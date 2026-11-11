"""Authenticated learner operations on published course occurrences."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.limiter import rate_limit
from app.models.user import User
from app.schemas.teaching_dialogue import DialoguePage
from app.services import lesson_learning, teaching_runs
from app.services.teaching import dialogue
from app.services.teaching.principal import Principal

router = APIRouter(tags=["lesson learning"])

Slug = Annotated[str, StringConstraints(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")]


class OccurrenceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: str = Field(min_length=1, max_length=36)
    segment_id: Slug
    token_ids: list[Slug] = Field(min_length=1, max_length=128)


class LessonTurn(OccurrenceRef):
    request_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=36)


@router.post("/lessons/{lesson_id}/vocabulary")
@rate_limit("30/minute")
async def save_vocabulary_source(
    request: Request,
    response: Response,
    lesson_id: Slug,
    body: OccurrenceRef,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await lesson_learning.save_source(
        db, user.id, lesson_id, body.revision_id, body.segment_id, body.token_ids
    )
    await db.commit()
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/vocabulary/{word_id}/sources")
@rate_limit("60/minute")
async def vocabulary_sources(
    request: Request,
    response: Response,
    word_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    return await lesson_learning.list_sources(db, user.id, word_id)


@router.post("/lessons/{lesson_id}/tutor", status_code=202)
@rate_limit("20/minute")
async def start_tutor_turn(
    request: Request,
    response: Response,
    lesson_id: Slug,
    body: LessonTurn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await teaching_runs.start_lesson_turn(db, Principal(user.id), lesson_id, body)
    await db.commit()
    if result["status"] == "queued":
        teaching_runs.dispatch_run(result["run_id"])
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/lessons/{lesson_id}/tutor/{conversation_id}/messages", response_model=DialoguePage)
@rate_limit("60/minute")
async def tutor_history(
    request: Request,
    response: Response,
    lesson_id: Slug,
    conversation_id: str,
    after: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    return await dialogue.page_lesson(db, Principal(user.id), lesson_id, conversation_id, after=after, limit=limit)
