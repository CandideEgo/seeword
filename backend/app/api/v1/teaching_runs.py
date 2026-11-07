import asyncio
import json
import time

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, resolve_token_user
from app.core.database import get_async_session_maker, get_db
from app.core.errors import AppError
from app.models.user import User
from app.schemas.teaching_dialogue import DialoguePage
from app.services import teaching_runs as service
from app.services.teaching import dialogue
from app.services.teaching import service as core
from app.services.teaching.service import Principal

router = APIRouter(prefix="/teaching", tags=["teaching-runs"])


class CreateRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: str = Field(min_length=1, max_length=64)
    expected_revision: int = Field(ge=1)
    message: str = Field(min_length=1, max_length=4000)


# The queued DB row is a durable dispatch intent; the sweep retries it.
dispatch = service.dispatch_run


@router.post("/sessions/{session_id}/runs", status_code=202)
async def create_run(
    session_id: str, body: CreateRun, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    result = await service.create(db, Principal(user.id), session_id, body)
    await db.commit()
    if result["status"] == "queued":
        dispatch(result["run_id"])
    return result


@router.post("/sessions/{session_id}/messages", status_code=202)
async def create_turn(
    session_id: str,
    body: CreateRun,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    response.headers["Cache-Control"] = "no-store"
    result = await service.create(db, Principal(user.id), session_id, body, response_mode="conversation")
    await db.commit()
    if result["status"] == "queued":
        dispatch(result["run_id"])
    return result


@router.get("/sessions/{session_id}/messages", response_model=DialoguePage)
async def messages(
    session_id: str,
    response: Response,
    after: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    response.headers["Cache-Control"] = "no-store"
    principal = Principal(user.id)
    session = await core.owned_session(db, principal, session_id)
    return await dialogue.page_session(db, principal, session, after=after, limit=limit)


def resume_cursor(after: int, last_event_id: str | None) -> int:
    if last_event_id is None:
        return after
    if not last_event_id.isascii() or not last_event_id.isdecimal() or len(last_event_id) > 10:
        raise AppError(422, "VALIDATION_ERROR", "Last-Event-ID 必须为非负事件序号")
    return max(after, int(last_event_id))


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    response.headers["Cache-Control"] = "no-store"
    return await service.get(db, Principal(user.id), run_id)


@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await service.cancel(db, Principal(user.id), run_id)
    await db.commit()
    return result


@router.get("/runs/{run_id}/events")
async def run_events(
    request: Request,
    run_id: str,
    after: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    principal = Principal(user.id)
    after = resume_cursor(after, request.headers.get("last-event-id"))
    await service.events(db, principal, run_id, after)  # HTTP errors before starting the stream.
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    await db.rollback()
    await db.close()  # No transaction or connection held by the subscription.

    async def stream():
        cursor, started, heartbeat = after, time.monotonic(), time.monotonic()
        yield ": connected\n\n"
        while time.monotonic() - started < 60 and not await request.is_disconnected():
            try:
                async with get_async_session_maker()() as read_db:
                    current_user = await resolve_token_user(token, read_db)
                    if current_user is None:
                        raise AppError(401, "UNAUTHORIZED", "登录状态已过期")
                    rows, status = await service.events(read_db, principal, run_id, cursor)
                for event in rows:
                    cursor = event["sequence"]
                    yield f"id: {cursor}\nevent: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
                if status in service.TERMINAL:
                    return
            except AppError as exc:
                # A transport/auth failure is not a persisted run event and
                # must not invent a sequence number or advance the cursor.
                yield "event: error\ndata: " + json.dumps({"code": exc.code, "message": exc.message}) + "\n\n"
                return
            if time.monotonic() - heartbeat >= 10:
                yield ": heartbeat\n\n"
                heartbeat = time.monotonic()
            await asyncio.sleep(1)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
    )
