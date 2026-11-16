"""Video seeding and processing control — create Video rows and dispatch Celery tasks.

- Admin seed (seed_video): atomically creates a processing video and durable head intent.
- start_processing(): claims a new attempt for a pending video after checking
  the GPU heartbeat; broker outages leave a pending intent for beat.

There is no user-submit path (INV-003): everything here is admin/catalog
triggered, so the old UGC helpers (submit_video / seed_user_video /
fork_video) are gone.
"""

import hashlib
from collections.abc import Awaitable
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capabilities import require_content_production
from app.core.database import commit_refresh
from app.core.errors import (
    BadRequestError,
    ConflictError,
    NotFoundError,
    ServiceUnavailableError,
    UnprocessableEntityError,
)
from app.core.heartbeat import GPU_HEARTBEAT_KEY
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.models.subtitle import Subtitle
from app.models.video import Video, VideoSource, VideoStatus
from app.schemas.video import VideoAdminResponse, VideoResponse
from app.services.video_url_guard import validate_video_url

logger = get_logger(__name__)


def _detect_platform(source_url: str) -> VideoSource:
    """Determine video source from source URL.

    HTTP/HTTPS URLs are treated as imported (YouTube, etc.).
    Local file paths are treated as local.
    """
    if source_url.startswith(("http://", "https://")):
        return VideoSource.imported
    return VideoSource.local


# ---------------------------------------------------------------------------
# Single-flight guards (ADM-02/03/04)
# ---------------------------------------------------------------------------
#
# Every admin pipeline action used to be a plain "check then act": double clicks
# and concurrent admins could create duplicate videos / dispatch the same task
# twice. A Redis ``SET NX EX`` key per action is the cheap fix; all guards are
# best effort (fail-open on Redis errors) because Redis being down must not lock
# the admin out of recovery. Durable dispatch preserves the committed intent
# across broker failures; DB row locks serialize updates to an existing video.

_SEED_LOCK_TTL_SECONDS = 120
_RETRANSLATE_LOCK_TTL_SECONDS = 300
_RESUME_LOCK_TTL_SECONDS = 60

# Statuses meaning "this URL is already in the pipeline". A second seed click
# must reuse that row instead of inserting a duplicate video + GPU run.
# ``error`` is intentionally absent — a failed video stays retryable.
_SEED_DEDUP_STATUSES = (
    VideoStatus.pending_processing,
    VideoStatus.processing,
    VideoStatus.ready_subtitles,
    VideoStatus.ready,
)


def _seed_lock_key(source_url: str) -> str:
    """URL-level lock key; sha1 keeps long URLs out of Redis key size limits."""
    return f"seed:{hashlib.sha1(source_url.encode('utf-8'), usedforsecurity=False).hexdigest()}"


async def _acquire_single_flight(key: str, ttl: int) -> bool:
    """Take ``SET key 1 NX EX ttl``; True when the caller may proceed.

    False means another request holds the key (a real conflict). Redis errors
    are fail-open: without Redis we cannot coordinate, but blocking a genuinely
    needed recover/seed would be worse than losing the duplicate protection.
    The import is deliberately inside the function so tests can swap
    ``app.core.redis.get_redis`` for an in-memory double.
    """
    from app.core.redis import get_redis as _get_redis

    try:
        return bool(await _get_redis().set(key, "1", nx=True, ex=ttl))
    except Exception as exc:
        # TypeError / AttributeError means the client lacks the API (in-memory
        # test doubles) rather than a real Redis failure: log without a
        # traceback for those, keep it for connectivity errors.
        logger.warning(
            "Redis unavailable while acquiring single-flight %s: %s; proceeding",
            key,
            exc,
            exc_info=not isinstance(exc, (TypeError, AttributeError)),
        )
        return True


async def _delete_redis_key(key: str) -> None:
    """Best-effort Redis DEL (used to release locks and stale pipeline state)."""
    from app.core.redis import get_redis as _get_redis

    try:
        await _get_redis().delete(key)
    except Exception:
        logger.warning("Redis delete failed for %s", key, exc_info=True)


def _step_budget_seconds(video: Video) -> int:
    """Watchdog budget (seconds) for the step the video is currently on.

    Reads the same declaration the pipeline and the watchdog use
    (``pipeline_helpers.STEPS``) so the "is this lock still alive?" decision
    cannot drift from the actual per-step timeouts.
    """
    from app.core.config import get_settings
    from app.tasks.pipeline_helpers import get_step_timeouts

    budgets = get_step_timeouts()
    step = video.processing_step
    if step and step in budgets:
        return budgets[step]
    if video.status == VideoStatus.processing:
        # No step stamped yet: the head is still in extracting (metadata fetch
        # can take a while before it writes processing_step).
        return budgets.get("extracting") or get_settings().pipeline_step_timeout_extracting
    return get_settings().pipeline_step_timeout_default


async def _processing_lock_live(video: Video) -> tuple[bool, str]:
    """Is ``video:processing:{id}`` held by a run that is still within budget?

    ADM-03: ``recover``/``retry`` used to delete that key unconditionally, which
    could kill the lock of a perfectly healthy finalize and let a second run
    write the same subtitle rows. The lock is only treated as live when it is
    held **and** ``step_started_at`` (falling back to ``processing_started_at``)
    is younger than the current step's watchdog budget × 1.2 grace. Anything
    older — or a lock with no timestamp at all, which no live worker leaves
    behind — is stale and may be cleared.

    On Redis failure the lock cannot be observed; report "not live" so an admin
    can still recover a stuck video (finalize's own ``acquire_lock`` is the
    fail-closed gate).
    """
    from app.core.redis import get_redis as _get_redis

    try:
        from app.services.processing_generation import run_identity

        held = bool(
            await _get_redis().exists(f"video:processing:{run_identity(video.id, video.processing_generation)}")
        )
    except Exception:
        logger.warning("Redis unavailable while checking lock for video %s", video.id, exc_info=True)
        return False, ""
    if not held:
        return False, ""

    started = video.step_started_at or video.processing_started_at
    if started is None:
        return False, ""
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    age = (datetime.now(UTC) - started).total_seconds()
    budget = _step_budget_seconds(video) * 1.2
    if age <= budget:
        step = video.processing_step or "extracting"
        return True, f"当前步骤 {step} 已运行 {int(age)}s，预算 {int(budget)}s"
    return False, ""


def _allowed_retranslate_engines() -> tuple[str, ...]:
    """Engine names accepted by ``retranslate`` (single source: the registry)."""
    from app.services.translation.engines import BUILTIN_ENGINES

    return tuple(sorted(BUILTIN_ENGINES))


def _validate_retranslate_engine(engine: str | None) -> None:
    """Reject unknown engines with 422 before any state is touched (ADM-02)."""
    if engine is None:
        return
    allowed = _allowed_retranslate_engines()
    if engine not in allowed:
        raise UnprocessableEntityError(f"未知的翻译引擎 {engine!r}，可用引擎：{', '.join(allowed)}")


async def _renew_generation(
    video: Video, *, carry_steps: bool = False, omit_steps: frozenset[str] = frozenset()
) -> None:
    """New DB-owned attempt; Redis markers are only an optional resume hint."""
    from uuid import uuid4

    from app.services.processing_generation import run_identity
    from app.tasks.pipeline_helpers import STEPS_TTL_SECONDS

    previous = run_identity(video.id, video.processing_generation)
    video.processing_generation = str(uuid4())
    current = run_identity(video.id, video.processing_generation)
    if carry_steps:
        try:
            redis = get_redis()
            completed = set(await cast("Awaitable[set[str]]", redis.smembers(f"video:steps:{previous}"))) - omit_steps
            if completed:
                await cast("Awaitable[int]", redis.sadd(f"video:steps:{current}", *completed))
                await redis.expire(f"video:steps:{current}", STEPS_TTL_SECONDS)
        except Exception:
            # Re-running an idempotent step is safe. Guessing a completed one is not.
            logger.warning("Processing resume hints unavailable", video_id=video.id)


async def _queue_run(db: AsyncSession, video: Video, task_name: str, *, engine: str | None = None) -> None:
    """State and durable intent commit together; immediate delivery is best effort."""
    from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK, dispatch_now, enqueue

    args = [video.id, engine] if task_name == FINALIZE_VIDEO_TASK else [video.id]
    dispatch_id = await enqueue(db, video_id=video.id, task_name=task_name, args=args)
    await commit_refresh(db, video)
    await dispatch_now(db, dispatch_id)


async def seed_video(db: AsyncSession, source_url: str, auto_publish: bool = False) -> VideoResponse:
    """Admin/catalog seed: commit a new video and its head intent atomically.

    Broker outage leaves a pending intent for beat, never an unqueued terminal
    error. The URL-level guard retains the established duplicate-click policy.
    """
    from uuid import uuid4

    from app.services.pipeline_dispatch import PROCESS_VIDEO_TASK

    require_content_production(model=True)
    await validate_video_url(source_url)
    lock_key = _seed_lock_key(source_url)
    if not await _acquire_single_flight(lock_key, _SEED_LOCK_TTL_SECONDS):
        raise ConflictError("该 URL 正在添加中（另一请求已在进行），请稍后刷新列表")
    try:
        existing = (
            await db.scalars(
                select(Video).where(
                    Video.source_url == source_url,
                    Video.is_official.is_(True),
                    Video.status.in_(list(_SEED_DEDUP_STATUSES)),
                )
            )
        ).first()
        if existing is not None:
            return VideoResponse.model_validate(existing)
        video = Video(
            title="Processing...",
            source_url=source_url,
            video_source=_detect_platform(source_url),
            status=VideoStatus.processing,
            is_official=True,
            is_published=False,
            auto_publish=auto_publish,
            processing_started_at=datetime.now(UTC),
            step_started_at=datetime.now(UTC),
            processing_step="extracting",
            processing_generation=str(uuid4()),
        )
        db.add(video)
        await db.flush()
        await _queue_run(db, video, PROCESS_VIDEO_TASK)
        return VideoResponse.model_validate(video)
    finally:
        await _delete_redis_key(lock_key)


_WORKER_HEARTBEAT_KEY = GPU_HEARTBEAT_KEY


async def is_gpu_worker_online() -> bool:
    try:
        return bool(await get_redis().exists(_WORKER_HEARTBEAT_KEY))
    except Exception:
        return False


async def _locked_video(db: AsyncSession, video_id: str) -> Video:
    video = await db.scalar(
        select(Video).where(Video.id == video_id).with_for_update().execution_options(populate_existing=True)
    )
    if video is None:
        raise NotFoundError("Video not found")
    return video


async def start_processing(db: AsyncSession, video_id: str) -> VideoResponse:
    from app.services.pipeline_dispatch import PROCESS_VIDEO_TASK

    require_content_production(model=True)
    video = await _locked_video(db, video_id)
    if video.status != VideoStatus.pending_processing:
        raise BadRequestError(f"Video is not in pending_processing state (current: {video.status.value})")
    if not await is_gpu_worker_online():
        raise ServiceUnavailableError("GPU worker is offline — please start the local processing service first")
    await _renew_generation(video)
    video.status = VideoStatus.processing
    video.processing_started_at = datetime.now(UTC)
    video.step_started_at = datetime.now(UTC)
    video.processing_step = "extracting"
    await _queue_run(db, video, PROCESS_VIDEO_TASK)
    return VideoAdminResponse.model_validate(video)


async def _require_recoverable(video: Video) -> None:
    lock_live, lock_detail = await _processing_lock_live(video)
    if lock_live:
        raise ConflictError(f"视频仍在处理中（{lock_detail}），请等待任务结束或步骤预算过期后重试")
    if not await _acquire_single_flight(f"pipeline:resume:{video.id}", _RESUME_LOCK_TTL_SECONDS):
        raise ConflictError("该视频刚刚触发过恢复/重试，60 秒内请勿重复操作")


async def recover_processing(db: AsyncSession, video_id: str) -> VideoAdminResponse:
    """Replace a provably stale run; old messages can no longer write its state."""
    from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK, PROCESS_VIDEO_TASK
    from app.services.video_service import count_subtitles

    require_content_production(model=True)
    video = await _locked_video(db, video_id)
    if video.status not in (VideoStatus.processing, VideoStatus.ready_subtitles):
        raise BadRequestError(f"Video is not in a recoverable state (current: {video.status.value})")
    await _require_recoverable(video)
    has_subtitles = await count_subtitles(db, video.id) > 0
    await _renew_generation(video, carry_steps=has_subtitles)
    video.status = VideoStatus.ready_subtitles if has_subtitles else VideoStatus.processing
    video.processing_step = "translating" if has_subtitles else "extracting"
    video.processing_progress = 70 if has_subtitles else 0
    video.error_message = None
    video.step_started_at = datetime.now(UTC)
    await _queue_run(db, video, FINALIZE_VIDEO_TASK if has_subtitles else PROCESS_VIDEO_TASK)
    return VideoAdminResponse.model_validate(video)


async def retry_video(db: AsyncSession, video_id: str) -> VideoAdminResponse:
    """Preserve subtitle facts; every retry fences old successes and failures."""
    from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK
    from app.services.video_service import count_subtitles

    require_content_production(model=True)
    video = await _locked_video(db, video_id)
    if video.status != VideoStatus.error:
        raise BadRequestError(f"Video is not in error state (current: {video.status.value})")
    await _require_recoverable(video)
    has_subtitles = await count_subtitles(db, video.id) > 0
    await _renew_generation(video, carry_steps=has_subtitles)
    video.error_message = None
    video.processing_step = "translating" if has_subtitles else None
    video.processing_progress = 70 if has_subtitles else 0
    video.step_started_at = datetime.now(UTC) if has_subtitles else None
    if has_subtitles:
        video.status = VideoStatus.ready_subtitles
        await _queue_run(db, video, FINALIZE_VIDEO_TASK)
    else:
        # Still requires the explicit start action/worker-online check.
        video.status = VideoStatus.pending_processing
        await commit_refresh(db, video)
    return VideoAdminResponse.model_validate(video)


_RETRANSLATE_ALLOWED_STATUSES = (VideoStatus.error, VideoStatus.ready)


async def retranslate_video(db: AsyncSession, video_id: str, engine: str | None = None) -> VideoAdminResponse:
    """Translation reset and durable tail intent are one transaction.

    A broker failure no longer needs to restore committed translations: the
    intent remains pending and beat retries delivery. A DB failure rolls back
    the whole reset, rather than losing state between two commits.
    """
    from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK
    from app.services.video_service import count_subtitles

    require_content_production(model=True)
    video = await _locked_video(db, video_id)
    _validate_retranslate_engine(engine)
    if video.status not in _RETRANSLATE_ALLOWED_STATUSES:
        raise ConflictError(f"视频当前状态为 {video.status.value}，请等待任务结束后再重新翻译")
    if await count_subtitles(db, video.id) == 0:
        raise BadRequestError("Video has no subtitles to translate")
    if not await _acquire_single_flight(f"retranslate:{video.id}", _RETRANSLATE_LOCK_TTL_SECONDS):
        raise ConflictError("该视频已有重新翻译任务在进行中，请勿重复点击")
    await _renew_generation(video, carry_steps=True, omit_steps=frozenset({"translating"}))
    for sub in await db.scalars(select(Subtitle).where(Subtitle.video_id == video.id)):
        sub.text_zh = None
    video.quality_flag = None
    video.status = VideoStatus.ready_subtitles
    video.error_message = None
    video.processing_step = "translating"
    video.processing_progress = 70
    video.step_started_at = datetime.now(UTC)
    await _queue_run(db, video, FINALIZE_VIDEO_TASK, engine=engine)
    return VideoAdminResponse.model_validate(video)
