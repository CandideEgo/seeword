"""Revision-bound lesson context for the V2 tutor runtime."""

from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError
from app.models.lesson import LessonRevision
from app.models.lesson_learning import LessonTutorAnchor
from app.services.lesson_learning import resolve_occurrence, source_view
from app.services.lessons import get_visible_revision, material_for_revision
from app.services.v2_schema import has_tables

LESSON_CONVERSATION = "lesson"


def require_tutor() -> None:
    settings = get_settings()
    if not (settings.slcs_lessons_enabled and settings.slcs_tutor_enabled and settings.teaching_streaming_enabled):
        raise AppError(503, "SERVICE_UNAVAILABLE", "课程导师暂未开放")


async def require_anchor_schema(db: AsyncSession) -> None:
    if not await has_tables(db, (LessonTutorAnchor.__tablename__, LessonRevision.__tablename__)):
        raise AppError(503, "SERVICE_UNAVAILABLE", "课程导师暂未开放")


async def get_anchor(db: AsyncSession, conversation_id: str) -> tuple[LessonTutorAnchor, str]:
    await require_anchor_schema(db)
    row = (
        await db.execute(
            select(LessonTutorAnchor, LessonRevision.lesson_id)
            .join(LessonRevision, LessonRevision.id == LessonTutorAnchor.revision_id)
            .where(LessonTutorAnchor.conversation_id == conversation_id)
        )
    ).first()
    if row is None:
        raise NotFoundError("课程对话不存在")
    return row[0], row[1]


async def material_context(
    db: AsyncSession, lesson_id: str, revision_id: str, segment_id: str, token_ids: list[str], *, lock: bool = False
) -> dict:
    """Project the single approved segment and its canonical citation."""
    require_tutor()
    await get_visible_revision(db, lesson_id, revision_id, use="site_display", lock=lock)
    revision = await get_visible_revision(db, lesson_id, revision_id, use="model_processing", lock=lock)
    material = material_for_revision(revision)
    occurrence = resolve_occurrence(material, segment_id, token_ids)
    segment = next(segment for segment in material.segments if segment.id == segment_id)
    return {
        "source": {
            "text": segment.text,
            "translation": segment.translation,
            "headword": occurrence.headword,
            "gloss": occurrence.gloss,
        },
        "citation_id": f"lesson:{revision_id}:{segment_id}",
        "citation": source_view(lesson_id, revision_id, segment_id, token_ids, occurrence),
    }


async def model_context(db: AsyncSession, conversation_id: str, *, lock: bool = True) -> dict:
    require_tutor()
    anchor, lesson_id = await get_anchor(db, conversation_id)
    return await material_context(db, lesson_id, anchor.revision_id, anchor.segment_id, anchor.token_ids, lock=lock)


async def projection(db: AsyncSession, conversation_id: str) -> dict | Literal[False]:
    """All message surfaces use the same current rights, including exports."""
    try:
        return await model_context(db, conversation_id, lock=False)
    except AppError as exc:
        if exc.status_code not in {403, 404, 410, 503}:
            raise
        return False
