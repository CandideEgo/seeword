"""Authenticated SLCS pilot and maintenance routes."""

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_admin_user, get_current_user
from app.core.database import get_db
from app.core.errors import AppError, ErrorCode
from app.core.limiter import rate_limit
from app.models.user import User
from app.schemas.lesson import (
    ImportLesson,
    PublishLesson,
    RecordLessonActivity,
    ReviewLesson,
    SaveLessonProgress,
    WithdrawLesson,
)
from app.services import lesson_progress, lessons


async def _require_pilot(db: AsyncSession = Depends(get_db)) -> None:
    await lessons.require_lessons_ready(db)


router = APIRouter(prefix="/lessons", tags=["lessons"], dependencies=[Depends(get_current_user)])
admin_router = APIRouter(
    prefix="/admin/lessons", tags=["admin lessons"], dependencies=[Depends(get_admin_user), Depends(_require_pilot)]
)
_REVISION = "/{lesson_id}/revisions/{revision_id}"
_PILOT_DEPENDENCY = [Depends(_require_pilot)]
_MAX_IMPORT_REQUEST_BYTES = 2 * lessons.MAX_PACK_BYTES


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


@router.get("/_status")
async def status(response: Response):
    _no_store(response)
    return {"enabled": lessons.lesson_router_enabled()}


@router.get("", dependencies=_PILOT_DEPENDENCY)
@rate_limit("60/minute")
async def index(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    _no_store(response)
    return {"lessons": await lessons.list_lessons(db)}


@router.get("/_history", dependencies=_PILOT_DEPENDENCY)
@rate_limit("60/minute")
async def history(
    request: Request,
    response: Response,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    return {"items": await lesson_progress.read_history(db, user.id, offset=offset, limit=limit)}


@router.get("/{lesson_id}", dependencies=_PILOT_DEPENDENCY)
@rate_limit("60/minute")
async def current(request: Request, response: Response, lesson_id: str, db: AsyncSession = Depends(get_db)):
    _no_store(response)
    return lessons.public_detail(await lessons.get_visible_revision(db, lesson_id))


@router.get(_REVISION, dependencies=_PILOT_DEPENDENCY)
@rate_limit("60/minute")
async def by_revision(
    request: Request, response: Response, lesson_id: str, revision_id: str, db: AsyncSession = Depends(get_db)
):
    _no_store(response)
    return lessons.public_detail(await lessons.get_visible_revision(db, lesson_id, revision_id))


@router.get("/{lesson_id}/_state", dependencies=_PILOT_DEPENDENCY)
@rate_limit("120/minute")
async def state(
    request: Request,
    response: Response,
    lesson_id: str,
    revision: str | None = Query(default=None, max_length=36),
    db: AsyncSession = Depends(get_db),
):
    """Cheap revalidation: what the reader polls instead of re-downloading the pack.

    A lesson pack carries every segment and every vocabulary anchor; polling it
    every 20 seconds is a large repeated download. This answer is a few hundred
    bytes and tells the page whether the pack it holds is still current and
    still publishable.
    """
    _no_store(response)
    return lessons.revision_state(await lessons.get_visible_revision(db, lesson_id, revision))


@router.get("/{lesson_id}/progress", dependencies=_PILOT_DEPENDENCY)
@rate_limit("60/minute")
async def progress(
    request: Request,
    response: Response,
    lesson_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    return await lesson_progress.read_progress(db, user.id, lesson_id)


@router.put("/{lesson_id}/progress", dependencies=_PILOT_DEPENDENCY)
@rate_limit("60/minute")
async def update_progress(
    request: Request,
    lesson_id: str,
    body: SaveLessonProgress,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await lesson_progress.save_progress(db, user.id, lesson_id, body)
    await db.commit()
    return result


@router.post("/{lesson_id}/activity", dependencies=_PILOT_DEPENDENCY)
@rate_limit("60/minute")
async def activity(
    request: Request,
    lesson_id: str,
    body: RecordLessonActivity,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await lesson_progress.record_activity(db, user.id, lesson_id, body)
    await db.commit()
    return result


@admin_router.get("")
@rate_limit("60/minute")
async def admin_index(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    _no_store(response)
    return {"lessons": await lessons.list_admin_lessons(db)}


async def _read_import(request: Request) -> ImportLesson:
    declared = request.headers.get("content-length", "")
    if declared.isdecimal() and (len(declared) > 20 or int(declared) > _MAX_IMPORT_REQUEST_BYTES):
        raise AppError(413, ErrorCode.BAD_REQUEST, "导入请求超过 8 MiB")
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > _MAX_IMPORT_REQUEST_BYTES:
            raise AppError(413, ErrorCode.BAD_REQUEST, "导入请求超过 8 MiB")
        data.extend(chunk)
    try:
        return ImportLesson.model_validate_json(data)
    except ValidationError:
        raise AppError(422, ErrorCode.VALIDATION_ERROR, "导入请求需要操作编号和学习包原始 JSON") from None


@admin_router.post("/import")
@rate_limit("10/minute")
async def import_pack(
    request: Request,
    response: Response,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    body = await _read_import(request)
    result = await lessons.import_lesson(db, user.id, body.operation_id, body.pack_json.encode("utf-8"))
    await db.commit()
    return result


@admin_router.get(_REVISION)
@rate_limit("60/minute")
async def admin_detail(
    request: Request, response: Response, lesson_id: str, revision_id: str, db: AsyncSession = Depends(get_db)
):
    _no_store(response)
    return await lessons.admin_detail(db, lesson_id, revision_id)


@admin_router.post(_REVISION + "/review")
@rate_limit("20/minute")
async def review(
    request: Request,
    response: Response,
    lesson_id: str,
    revision_id: str,
    body: ReviewLesson,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    result = await lessons.review_lesson(db, user.id, lesson_id, revision_id, body)
    await db.commit()
    return result


@admin_router.post(_REVISION + "/publish")
@rate_limit("10/minute")
async def publish(
    request: Request,
    response: Response,
    lesson_id: str,
    revision_id: str,
    body: PublishLesson,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    result = await lessons.publish_lesson(db, user.id, lesson_id, revision_id, body)
    await db.commit()
    return result


@admin_router.post(_REVISION + "/withdraw")
@rate_limit("20/minute")
async def withdraw(
    request: Request,
    response: Response,
    lesson_id: str,
    revision_id: str,
    body: WithdrawLesson,
    user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    result = await lessons.withdraw_lesson(db, user.id, lesson_id, revision_id, body)
    await db.commit()
    return result


@admin_router.get(_REVISION + "/operations")
@rate_limit("60/minute")
async def operations(
    request: Request,
    response: Response,
    lesson_id: str,
    revision_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    _no_store(response)
    return {"operations": await lessons.list_operations(db, lesson_id, revision_id, offset=offset, limit=limit)}
