"""Durable dispatch of the pipeline's cross-process task hand-offs (A05/BE-01).

These hand-offs cross the DB→broker gap:

1. head → GPU transcription (``GPU_TRANSCRIBE_TASK`` on ``transcription_gpu``)
2. head resume → tail (``finalize_video``, subtitles already present)
3. GPU callback → tail (``finalize_video``, the P1 case the audit reproduced)
4. admin localization claim → download/transcode (``localize_video``)

``enqueue`` records "this task must run for this video" **inside the caller's
transaction**, so a crash after commit cannot lose it. The caller commits, then
calls ``dispatch_now`` for a best-effort immediate send; whatever is left
pending is picked up by ``dispatch_pipeline_tasks`` (beat), which also alerts
when the backlog grows. Delivery may repeat; workers retain their processing
lock and artifact/state checks. This is not an exactly-once guarantee, nor does
it fence an old worker after its Redis lock expires.

The task must still make sense when it finally goes out — a video that the
watchdog moved to ``error`` meanwhile is not worth a GPU slot or a translate
run, so the intent is abandoned (kept as a row, with the reason) instead.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.capabilities import require_content_production
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.pipeline_dispatch import (
    DISPATCH_STATUS_ABANDONED,
    DISPATCH_STATUS_DISPATCHED,
    DISPATCH_STATUS_PENDING,
    PipelineDispatch,
)
from app.models.video import Video, VideoStatus
from app.tasks.celery_app import GPU_TRANSCRIBE_TASK

if TYPE_CHECKING:
    from sqlalchemy.engine import CursorResult
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

#: Cloud task name for the pipeline tail. Kept as a literal (not an import) so
#: the API layer does not pull in ``uvicorn``'s opposite — the task module
#: imports services, and services are imported by the API.
FINALIZE_VIDEO_TASK = "app.tasks.video_processing.finalize_video"
LOCALIZE_VIDEO_TASK = "app.tasks.video_processing.localize_video"

#: Task name → the video status the task is still meaningful in. A video that
#: left this state is either already past the step (watchdog error, manual
#: retrigger, delete) or never reached it.
_REQUIRED_STATUS: dict[str, frozenset[str]] = {
    GPU_TRANSCRIBE_TASK: frozenset({VideoStatus.processing.value}),
    FINALIZE_VIDEO_TASK: frozenset({VideoStatus.ready_subtitles.value}),
    LOCALIZE_VIDEO_TASK: frozenset({VideoStatus.processing.value}),
}

#: Send-failure backoff: 10s doubling, capped at 5 minutes. The beat scan runs
#: every minute, so the first retry lands on the next scan at worst.
_MAX_BACKOFF_SECONDS = 300
_MAX_ATTEMPT_ROWS = 200


def _backoff_seconds(attempts: int) -> int:
    return min(_MAX_BACKOFF_SECONDS, 10 * int(2 ** max(0, attempts - 1)))


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; Postgres returns aware ones."""
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _send_task(task_name: str, args: list, queue: str | None) -> None:
    """The single broker seam — tests monkeypatch this, not Celery internals."""
    from app.tasks.celery_app import celery_app

    options: dict = {"queue": queue} if queue else {}
    celery_app.send_task(task_name, args=list(args), **options)


async def _send(task_name: str, args: list, queue: str | None) -> None:
    # Broker I/O is blocking; keep it off the event loop (this is called from
    # async endpoints and from Celery's shared loop).
    await asyncio.to_thread(_send_task, task_name, args, queue)


async def enqueue(
    db: AsyncSession,
    *,
    video_id: str,
    task_name: str,
    args: list | tuple,
    queue: str | None = None,
) -> str:
    """Record the intent to run ``task_name`` for ``video_id``. Caller commits.

    Upsert on ``(video_id, task_name)``: a repeated callback / resumed head
    re-arms the existing row with the new args instead of creating a second
    intent, so the task cannot be queued twice by two callers that both believe
    it is missing.
    """
    require_content_production(model=task_name != LOCALIZE_VIDEO_TASK)
    now = _utcnow()
    values = {
        "id": str(uuid.uuid4()),
        "video_id": video_id,
        "task_name": task_name,
        "queue": queue,
        "args": list(args),
        "status": DISPATCH_STATUS_PENDING,
        "attempts": 0,
        "last_error": None,
        "next_attempt_at": None,
        "dispatched_at": None,
        "created_at": now,
        "updated_at": now,
    }
    dialect = db.bind.dialect.name if db.bind is not None else ""
    insert_stmt = (pg_insert if dialect == "postgresql" else sqlite_insert)(PipelineDispatch).values(**values)
    rearm = {
        key: values[key]
        for key in (
            "queue",
            "args",
            "status",
            "attempts",
            "last_error",
            "next_attempt_at",
            "dispatched_at",
            "updated_at",
        )
    }
    await db.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=["video_id", "task_name"],
            set_=rearm,
        )
    )
    row_id = await db.scalar(
        select(PipelineDispatch.id).where(
            PipelineDispatch.video_id == video_id,
            PipelineDispatch.task_name == task_name,
        )
    )
    if row_id is None:  # pragma: no cover - the upsert above guarantees the row
        raise RuntimeError(f"pipeline dispatch upsert produced no row for {video_id}/{task_name}")
    return row_id


async def dispatch_now(db: AsyncSession, dispatch_id: str) -> bool:
    """Try to send one intent immediately (best-effort, after the caller's commit).

    Returns True when the task reached the broker. A send failure leaves the row
    pending with a backoff — the caller should not treat it as an error, the
    dispatcher will retry.
    """
    row = await db.get(PipelineDispatch, dispatch_id)
    if row is None or row.status != DISPATCH_STATUS_PENDING:
        return False
    return await _attempt(db, row)


async def _attempt(db: AsyncSession, row: PipelineDispatch) -> bool:
    # Keep durable intents pending while an operator disables a capability;
    # do not send, abandon, consume attempts or change transaction ownership.
    settings = get_settings()
    if not settings.content_production_enabled or (row.task_name != LOCALIZE_VIDEO_TASK and not settings.llm_enabled):
        return False
    required = _REQUIRED_STATUS.get(row.task_name)
    if required is not None:
        status = await db.scalar(select(Video.status).where(Video.id == row.video_id))
        current = status.value if status is not None else None
        if current not in required:
            row.status = DISPATCH_STATUS_ABANDONED
            row.last_error = f"video no longer in {', '.join(sorted(required))} (now: {current or 'deleted'})"
            row.updated_at = _utcnow()
            await db.commit()
            logger.info(
                "pipeline_dispatch_abandoned",
                video_id=row.video_id,
                task=row.task_name,
                video_status=current,
            )
            return False

    try:
        await _send(row.task_name, list(row.args or []), row.queue)
    except Exception as exc:
        row.attempts += 1
        row.last_error = (str(exc) or exc.__class__.__name__)[:1000]
        row.next_attempt_at = _utcnow() + timedelta(seconds=_backoff_seconds(row.attempts))
        row.updated_at = _utcnow()
        await db.commit()
        logger.warning(
            "pipeline_dispatch_send_failed",
            video_id=row.video_id,
            task=row.task_name,
            attempts=row.attempts,
            exc_info=True,
        )
        return False

    row.status = DISPATCH_STATUS_DISPATCHED
    row.attempts += 1
    row.dispatched_at = _utcnow()
    row.last_error = None
    row.next_attempt_at = None
    row.updated_at = _utcnow()
    await db.commit()
    logger.info("pipeline_dispatch_sent", video_id=row.video_id, task=row.task_name, attempts=row.attempts)
    return True


@dataclass
class DispatchSweep:
    scanned: int = 0
    sent: int = 0
    failed: int = 0
    abandoned: int = 0
    pruned: int = 0


async def dispatch_pending(db: AsyncSession, *, limit: int = _MAX_ATTEMPT_ROWS) -> DispatchSweep:
    """Send every pending intent whose backoff has elapsed (beat entry point)."""
    now = _utcnow()
    rows = (
        (
            await db.execute(
                select(PipelineDispatch)
                .where(PipelineDispatch.status == DISPATCH_STATUS_PENDING)
                .order_by(PipelineDispatch.created_at)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    sweep = DispatchSweep()
    for row in rows:
        sweep.scanned += 1
        due_at = _as_utc(row.next_attempt_at)
        if due_at is not None and due_at > now:
            continue
        before = row.status
        sent = await _attempt(db, row)
        if row.status == DISPATCH_STATUS_ABANDONED and before != DISPATCH_STATUS_ABANDONED:
            sweep.abandoned += 1
        elif sent:
            sweep.sent += 1
        else:
            sweep.failed += 1
    return sweep


async def prune_settled(db: AsyncSession, *, retention_hours: int) -> int:
    """Delete dispatched/abandoned rows older than the retention window."""
    cutoff = _utcnow() - timedelta(hours=retention_hours)
    result = await db.execute(
        delete(PipelineDispatch).where(
            PipelineDispatch.status.in_([DISPATCH_STATUS_DISPATCHED, DISPATCH_STATUS_ABANDONED]),
            PipelineDispatch.updated_at < cutoff,
        )
    )
    await db.commit()
    return int(cast("CursorResult[Any]", result).rowcount or 0)


@dataclass
class DispatchBacklog:
    pending: int
    oldest_age_seconds: int | None


async def backlog(db: AsyncSession) -> DispatchBacklog:
    """Count undelivered intents and how long the oldest has waited."""
    count, oldest = (
        await db.execute(
            select(func.count(PipelineDispatch.id), func.min(PipelineDispatch.created_at)).where(
                PipelineDispatch.status == DISPATCH_STATUS_PENDING
            )
        )
    ).one()
    oldest_at = _as_utc(oldest)
    age = None if oldest_at is None else max(0, int((_utcnow() - oldest_at).total_seconds()))
    return DispatchBacklog(pending=int(count or 0), oldest_age_seconds=age)


async def pending_video_ids(db: AsyncSession, video_ids: list[str]) -> set[str]:
    """Videos with an undelivered pipeline intent (the watchdog must not kill them).

    Backoff does not matter here: an intent that is waiting out its retry
    schedule is still being worked on, not stuck, so the video is not failed
    while the dispatcher keeps trying (a permanently broken broker is surfaced
    by the backlog alert instead).
    """
    if not video_ids:
        return set()
    rows = await db.execute(
        select(PipelineDispatch.video_id).where(
            PipelineDispatch.video_id.in_(video_ids),
            PipelineDispatch.status == DISPATCH_STATUS_PENDING,
        )
    )
    return set(rows.scalars().all())
