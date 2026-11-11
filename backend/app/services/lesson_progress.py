"""Progress and idempotent activity keyed to SLCS lessons and their revisions.

Two ideas share one row and must not be confused:

* the **resume pointer** (``revision_id`` + ``position_ms``) follows the revision
  the learner is actually looking at, so an old deep link writes an old revision
  without disturbing anything else;
* **completion** is a lesson-level fact. It is never cleared by a later position
  save, a newer published revision is delivered to a finished learner as
  completed, and it feeds the learning profile's ``completed_video`` and
  ``watched_video`` facts so course learning reaches the streak, the "days
  studied" count and the weekly totals.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.core.errors import AppError, ErrorCode
from app.models.lesson import LessonActivity, LessonProgress, LessonRevision
from app.schemas.lesson import RecordLessonActivity, SaveLessonProgress
from app.services.learning_event_service import (
    EVENT_COMPLETED_VIDEO,
    EVENT_WATCHED_VIDEO,
    claim_watch_day,
    emit_event,
    record_event,
)
from app.services.lessons import get_visible_revision, insert_for, may_display_revision


def _progress(row: LessonProgress | None, *, pointer_available: bool = True) -> dict:
    # Withdrawal never erases learner state: the position and the completion stay
    # readable. ``pointer_available`` tells the page whether the revision the
    # pointer names can still be opened, so it does not offer a dead link.
    return {
        "revision_id": row.revision_id if row else None,
        "position_ms": row.position_ms if row else None,
        "completed": row.completed if row else False,
        "watch_seconds": row.watch_seconds if row else 0.0,
        "pointer_available": pointer_available,
    }


async def read_progress(db: AsyncSession, user_id: str, lesson_id: str) -> dict:
    row = await db.get(LessonProgress, (user_id, lesson_id), populate_existing=True)
    if row is None:
        await get_visible_revision(db, lesson_id)
        return _progress(None)
    # Only the status is needed to know whether the resume pointer can still be
    # opened; loading the whole revision would drag the pack along.
    status = await db.scalar(select(LessonRevision.status).where(LessonRevision.id == row.revision_id))
    return _progress(row, pointer_available=status == "published")


async def read_history(db: AsyncSession, user_id: str, *, offset: int, limit: int) -> list[dict]:
    rows = await db.execute(
        select(LessonProgress, LessonRevision)
        .join(LessonRevision, LessonRevision.id == LessonProgress.revision_id)
        .where(LessonProgress.user_id == user_id)
        .options(defer(LessonRevision.pack))
        .order_by(LessonProgress.updated_at.desc(), LessonProgress.lesson_id)
        .offset(offset)
        .limit(limit)
    )
    history = []
    for progress, revision in rows:
        available = may_display_revision(revision)
        history.append(
            {
                **_progress(progress, pointer_available=available),
                "lesson_id": progress.lesson_id,
                "title": revision.title if available else None,
                "available": available,
                "updated_at": progress.updated_at,
            }
        )
    return history


async def _ensure_row(
    db: AsyncSession, user_id: str, lesson_id: str, revision_id: str, now: datetime
) -> LessonProgress:
    """Return the learner's progress row, locked, creating it if this is the first write.

    The insert is the race-free gate: exactly one concurrent request creates the
    row, every other one takes the conflict path and blocks on the row lock.
    """
    await db.execute(
        insert_for(db, LessonProgress)
        .values(
            user_id=user_id,
            lesson_id=lesson_id,
            revision_id=revision_id,
            watch_seconds=0.0,
            updated_at=now,
        )
        .on_conflict_do_nothing(index_elements=["user_id", "lesson_id"])
    )
    row = await db.scalar(
        select(LessonProgress)
        .where(LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if row is None:  # pragma: no cover - the inserted row cannot be invisible inside the transaction
        raise AppError(409, ErrorCode.CONFLICT, "学习进度正在更新，请重试")
    return row


async def save_progress(db: AsyncSession, user_id: str, lesson_id: str, body: SaveLessonProgress) -> dict:
    revision = await get_visible_revision(db, lesson_id, body.revision_id, lock=True)
    if body.position_ms > revision.pack["media"]["duration_ms"]:
        raise AppError(422, ErrorCode.VALIDATION_ERROR, "播放位置超过课程时长")
    now = datetime.now(UTC)
    # Only the resume pointer moves. ``completed`` is never touched here: an old
    # tab or an old deep link saving its position must not clear a lesson the
    # learner already finished.
    row = await _ensure_row(db, user_id, lesson_id, revision.id, now)
    row.revision_id = revision.id
    row.position_ms = body.position_ms
    row.updated_at = now
    await db.flush()
    return _progress(row)


async def record_activity(db: AsyncSession, user_id: str, lesson_id: str, body: RecordLessonActivity) -> dict:
    revision = await get_visible_revision(db, lesson_id, body.revision_id, lock=True)
    if body.event_type == "watch_time" and revision.access_mode != "provider_embed":
        # An external link has no player clock, so elapsed playback cannot be
        # observed. Explicit learner actions stay recordable for it; only the
        # timer is refused.
        raise AppError(422, ErrorCode.VALIDATION_ERROR, "外链课程没有播放时钟，无法记录播放时长")
    event = await db.scalar(
        insert_for(db, LessonActivity)
        .values(user_id=user_id, **body.model_dump())
        .on_conflict_do_nothing(index_elements=["user_id", "event_id"])
        .returning(LessonActivity.id)
    )
    if event is None:
        previous = (
            await db.scalars(
                select(LessonActivity).where(
                    LessonActivity.user_id == user_id, LessonActivity.event_id == body.event_id
                )
            )
        ).one()
        if (previous.revision_id, previous.event_type, previous.delta_s) != (
            body.revision_id,
            body.event_type,
            body.delta_s,
        ):
            raise AppError(409, ErrorCode.IDEMPOTENCY_CONFLICT, "该事件编号已用于其他播放活动")
        return await read_progress(db, user_id, lesson_id)

    delta = body.delta_s or 0.0
    completing = body.event_type == "complete"
    now = datetime.now(UTC)
    row = await _ensure_row(db, user_id, lesson_id, revision.id, now)
    first_completion = completing and not row.completed
    row.watch_seconds += delta
    row.revision_id = revision.id
    row.completed = row.completed or completing
    row.updated_at = now
    await db.flush()

    metadata = {"lesson_id": lesson_id, "revision_id": revision.id}
    if completing:
        if first_completion:
            # Durable fact: the streak, "days studied" and the weekly completed
            # count must see course learning. One per learner per lesson, so a
            # re-published revision does not count the same lesson twice.
            await record_event(db, user_id, EVENT_COMPLETED_VIDEO, video_id=None, metadata=metadata, source="video")
    elif await claim_watch_day(db, user_id):
        # One "this user studied today" fact per UTC day, shared with the video
        # path so a course day cannot be double-counted.
        await emit_event(db, user_id, EVENT_WATCHED_VIDEO, video_id=None, metadata=metadata, source="video")
    return _progress(row)
