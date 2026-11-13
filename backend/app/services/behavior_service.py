"""Behavior collection service — ingest user interaction events (ADR-0011 P0).

Writes to the behavior_events table AND mirrors side-effects onto
LearningRecord (time_spent_seconds, completed) and Video.view_count. This
dual-write closes the long-standing LearningRecord gap — previously
time_spent_seconds / completed had no write path at all (position /
progress_percentage go through the existing /learning/progress endpoint,
which the frontend now calls for resume + periodic position saves).

Not a recommendation engine — just the data channel. Ranking/scoring live in
scoring_service / recommendation_service (P1/P2).
"""

import math
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior import BehaviorEvent
from app.models.learning import LearningRecord
from app.models.video import Video

# Dialect-specific INSERT constructors for the event_id dedup. Typed as
# ``Callable[..., Any]`` on purpose: ``on_conflict_do_nothing`` lives on the
# dialect copies, not on the generic ``Insert`` both of them subclass.
_DIALECT_INSERTS: dict[str, Callable[..., Any]] = {
    "postgresql": pg_insert,
    "sqlite": sqlite_insert,
}

# Event types that carry LearningRecord/Video side-effects beyond the raw log.
EVENT_WATCH_TIME = "watch_time"
EVENT_COMPLETE = "complete"

# One play-completion per user/video/playback-session. The frontend can emit
# the same `complete` twice (retry, double flush, two tabs) and each repeat
# used to bump Video.view_count and emit another completed_video learning
# event; it also ran the full browse-cache invalidation on every repeat, which
# made the cache trivially easy to cold-start on purpose. Redis is a cache
# here, so a Redis outage fails open (analytics must never break playback).
COMPLETE_DEDUP_TTL_SECONDS = 6 * 60 * 60

# Upper bound on a single watch_time delta. The client reports roughly every 10
# seconds and settles tails on pause/hide, so anything past two minutes means a
# broken or spoofed client: the row is kept for diagnosis but the side effect is
# dropped rather than letting one event move a user's total by an hour.
MAX_WATCH_TIME_DELTA_S = 120


async def _insert_event(db: AsyncSession, event: dict, user_id: str | None) -> bool:
    """Append the raw event; return False when its ``event_id`` was already stored.

    The unique index on ``behavior_events.event_id`` is the idempotency
    guarantee: ``ON CONFLICT DO NOTHING`` makes a re-delivered batch a no-op,
    and the absence of a returned row is how the caller learns to skip the
    side effects. Events without an id (older clients, server-side callers) are
    inserted the plain way.
    """
    values = {
        "user_id": user_id,
        "video_id": event.get("video_id"),
        "event_type": event.get("event_type"),
        "event_payload": event.get("event_payload") or {},
        "session_id": event.get("session_id"),
        "flow_id": event.get("flow_id"),
        "schema_version": event.get("schema_version") or 1,
        "client_ts": event.get("client_ts"),
        "event_id": event.get("event_id"),
    }
    if not values["event_id"]:
        db.add(BehaviorEvent(**values))
        return True

    insert = _DIALECT_INSERTS.get(db.get_bind().dialect.name)
    if insert is None:  # pragma: no cover - only Postgres/SQLite are supported
        db.add(BehaviorEvent(**values))
        return True

    statement = (
        insert(BehaviorEvent)
        .values(**values)
        .on_conflict_do_nothing(index_elements=["event_id"])
        .returning(BehaviorEvent.id)
    )
    return (await db.execute(statement)).first() is not None


async def ingest_event(db: AsyncSession, event: dict, user_id: str | None) -> bool:
    """Ingest one event: append to behavior_events + mirror side-effects.

    Returns True when a LearningRecord/Video side-effect was actually applied
    (callers use it to decide whether browse caches must be invalidated).
    Does not commit — the caller (batch endpoint or single endpoint) commits.
    """
    video_id = event.get("video_id")
    event_type = event.get("event_type")
    payload = event.get("event_payload") or {}

    if not await _insert_event(db, event, user_id):
        # Duplicate delivery: the row already exists, so every side effect it
        # would have caused has already happened.
        return False

    # Side-effects only for logged-in users on a video-scoped event.
    if user_id and video_id and isinstance(event_type, str):
        return await _mirror_to_learning_record(db, user_id, video_id, event_type, payload, event.get("session_id"))
    return False


async def ingest_batch(db: AsyncSession, events: list[dict], user_id: str | None) -> tuple[int, bool]:
    """Ingest a batch of events (frontend flush).

    Returns ``(ingested_count, complete_side_effect_applied)``. The second flag
    stays False for a replayed `complete`, so the endpoint does not needlessly
    cold-start the browse/rankings caches.
    """
    complete_applied = False
    for ev in events:
        if await ingest_event(db, ev, user_id) and ev.get("event_type") == EVENT_COMPLETE:
            complete_applied = True
    await db.commit()
    return len(events), complete_applied


async def _complete_already_counted(user_id: str, video_id: str, session_id: str | None) -> bool:
    """Claim one play-completion; True means "already counted".

    Best-effort rather than strictly atomic (EXISTS + SETEX): a duplicate pair
    racing in the same millisecond may both pass, which is acceptable for a
    plays counter. Redis is a cache here, so an outage fails open (returns
    False): the analytics path must never break playback. The TTL bounds the
    claim to one playback session, not forever.
    """
    try:
        from app.core.redis import get_redis

        redis = get_redis()
        key = f"behavior:complete:{user_id}:{video_id}:{session_id or 'no-session'}"
        if await redis.exists(key):
            return True
        await redis.setex(key, COMPLETE_DEDUP_TTL_SECONDS, "1")
    except Exception:  # pragma: no cover - Redis outage
        return False
    return False


async def _claim_watch_day(db: AsyncSession, user_id: str, video_id: str, session_id: str | None = None) -> None:
    """Emit at most one ``watched_video`` learning event per user per UTC day.

    Why this exists: ``LearningEvent`` is the immutable daily fact that the
    personal "days studied" figure and the admin activity trend read (MET-01).
    Watching alone used to produce no learning event at all, so a user who only
    re-watched videos was invisible on both. One row per day is enough to place
    them on the timeline; per-event rows would be 6 writes a minute per viewer.

    The claim itself lives in ``learning_event_service.claim_watch_day`` so the
    course path shares one dedupe with playback. When Redis is down the claim
    fails open and a duplicate row may appear — harmless, because every consumer
    groups by distinct date.
    """
    from app.services.learning_event_service import EVENT_WATCHED_VIDEO, claim_watch_day, emit_event

    if not await claim_watch_day(db, user_id):
        return
    try:
        await emit_event(db, user_id, EVENT_WATCHED_VIDEO, 1, video_id=video_id, flow_id=session_id, source="video")
    except Exception:  # pragma: no cover - event emission must not break playback
        pass


async def drop_unknown_video_ids(db: AsyncSession, events: list[dict]) -> list[dict]:
    """Blank out video_ids that have no row in `videos`.

    behavior_events.video_id is a FK to videos.id, so an id for a video deleted
    between page load and the analytics flush aborts the INSERT with an
    IntegrityError. These are analytics events: the whole batch would be lost
    and the client has no way to learn the video is gone, so the id is dropped
    (video_id NULL) and the event is kept — see BehaviorEvent.video_id, which
    is nullable for exactly this reason.

    Resolves the whole batch in one query; per-event lookups would cost N
    round-trips on every flush.
    """
    ids = {ev.get("video_id") for ev in events if ev.get("video_id")}
    if not ids:
        return events
    known = set((await db.execute(select(Video.id).where(Video.id.in_(ids)))).scalars().all())
    unknown = ids - known
    if not unknown:
        return events
    return [ev if ev.get("video_id") not in unknown else {**ev, "video_id": None} for ev in events]


async def _mirror_to_learning_record(
    db: AsyncSession,
    user_id: str,
    video_id: str,
    event_type: str,
    payload: dict,
    session_id: str | None,
) -> bool:
    """Update LearningRecord.time_spent_seconds / completed + Video.view_count.

    The LearningRecord row is created by video_service on first video open;
    we only update it if it exists (no upsert here — avoids a second creation
    path racing the unique constraint). Returns True only when a side-effect
    was actually applied.
    """
    if event_type == EVENT_WATCH_TIME:
        try:
            delta = float(payload.get("delta_s", 0) or 0)
        except (TypeError, ValueError, OverflowError):
            return False
        if not math.isfinite(delta) or delta <= 0 or delta > MAX_WATCH_TIME_DELTA_S:
            return False
        # Round rather than truncate: the client settles tails as small as 0.5s,
        # and int(0.6) would silently drop them.
        seconds = math.floor(delta + 0.5)
        if seconds <= 0:
            return False
        # Atomic SQL increment. The previous read-modify-write in Python lost
        # one increment whenever two tabs (or a retry racing its original)
        # updated the same record.
        result = await db.execute(
            update(LearningRecord)
            .where(
                LearningRecord.user_id == user_id,
                LearningRecord.video_id == video_id,
            )
            .values(
                time_spent_seconds=func.coalesce(LearningRecord.time_spent_seconds, 0) + seconds,
                last_accessed_at=datetime.now(UTC),
            )
        )
        if not result.rowcount:
            return False
        await _claim_watch_day(db, user_id, video_id, session_id)
        return True

    elif event_type == EVENT_COMPLETE:
        record_result = await db.execute(
            select(LearningRecord).where(
                LearningRecord.user_id == user_id,
                LearningRecord.video_id == video_id,
            )
        )
        record = record_result.scalar_one_or_none()
        if not record:
            return False
        # Idempotency: a replayed `complete` (retry / duplicate flush / two
        # tabs) must not bump view_count, emit a second completed_video event,
        # or force another browse-cache invalidation.
        if await _complete_already_counted(user_id, video_id, session_id):
            return False
        record.completed = True
        record.progress_percentage = 100.0
        # view_count increments per play-completion (not per unique user) —
        # matches the ADR's "播放完成次数" semantics. Inside `if record:` on
        # purpose: without the open-video marker any client could POST a bare
        # `complete` event and inflate the counter.
        await db.execute(update(Video).where(Video.id == video_id).values(view_count=Video.view_count + 1))

        # Emit learning event (ADR-0012 learning plan integration). Gated on
        # `record` like the counter above: a bare `complete` event from a user
        # who never opened the video must not manufacture a completed_video
        # event (and the daily counters / streak / milestone awards it drives).
        try:
            from app.services.learning_event_service import EVENT_COMPLETED_VIDEO, emit_event

            await emit_event(
                db, user_id, EVENT_COMPLETED_VIDEO, 1, video_id=video_id, flow_id=session_id, source="video"
            )
        except Exception:
            pass  # Non-blocking — event emission must not disrupt behavior ingestion
        return True
    return False
