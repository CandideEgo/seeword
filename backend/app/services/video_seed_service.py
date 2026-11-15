"""Video seeding and processing control — create Video rows and dispatch Celery tasks.

- Admin seed (seed_video): creates video in "processing" status and immediately
  dispatches process_video.delay() — admin-seeded videos auto-process.
- start_processing(): admin triggers GPU processing for a pending video.
  Checks that the local GPU worker is online (via Redis heartbeat) before
  dispatching the Celery task.

There is no user-submit path (INV-003): everything here is admin/catalog
triggered, so the old UGC helpers (submit_video / seed_user_video /
fork_video) are gone.
"""

import hashlib
from datetime import UTC, datetime

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
# the admin out of recovery, and the Celery dispatch behind the guard fails
# closed anyway when the broker is unavailable.

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
        held = bool(await _get_redis().exists(f"video:processing:{video.id}"))
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


async def _clear_translating_marker(video_id: str) -> bool:
    """Drop the ``translating`` completed-step marker; return whether it was set.

    The boolean lets the dispatch-failure path put the marker back so a later
    resume does not skip a translation that never ran.
    """
    from app.core.redis import get_redis as _get_redis

    try:
        r = _get_redis()
        was_set = bool(await r.sismember(f"video:steps:{video_id}", "translating"))
        await r.srem(f"video:steps:{video_id}", "translating")
        return was_set
    except Exception as exc:
        # AttributeError = client without set commands (in-memory test double).
        logger.warning(
            "Redis unavailable while clearing translating marker for %s: %s",
            video_id,
            exc,
            exc_info=not isinstance(exc, AttributeError),
        )
        return False


async def _restore_translating_marker(video_id: str) -> None:
    from app.core.redis import get_redis as _get_redis

    try:
        await _get_redis().sadd(f"video:steps:{video_id}", "translating")
    except Exception:
        logger.warning("Redis unavailable while restoring translating marker for %s", video_id, exc_info=True)


async def seed_video(
    db: AsyncSession,
    source_url: str,
    auto_publish: bool = False,
) -> VideoResponse:
    """Seed an official video for the public homepage. Admin only.

    Dedup (ADM-04) covers every in-pipeline state for this URL
    (``pending_processing`` / ``processing`` / ``ready_subtitles`` / ``ready``):
    re-clicking the seed button while the first run is still going returns the
    existing row instead of inserting a second video and paying for a second GPU
    transcription. ``error`` is deliberately not deduped — a failed video must
    stay retryable.

    A URL-level Redis lock (``seed:{sha1(url)}``, 120s, ``SET NX``) serialises
    the check+create window so two concurrent requests cannot both miss the
    dedup query. The lock is always released in ``finally`` so a crash does not
    block the URL for the full TTL where avoidable.

    If Celery dispatch fails after the row is committed, the row is marked
    ``error`` (rather than left in ``processing`` with nothing queued) and the
    request answers 503.
    """
    require_content_production(model=True)
    await validate_video_url(source_url)
    lock_key = _seed_lock_key(source_url)
    if not await _acquire_single_flight(lock_key, _SEED_LOCK_TTL_SECONDS):
        raise ConflictError("该 URL 正在添加中（另一请求已在进行），请稍后刷新列表")
    try:
        # Dedup: an official video for this URL that already exists in any
        # pipeline state wins (`error` excluded — retry must be possible).
        # `.first()` rather than `.scalar_one_or_none()`: legacy duplicate rows
        # for the same URL predate this guard and must not raise.
        existing_result = await db.execute(
            select(Video).where(
                Video.source_url == source_url,
                Video.is_official == True,
                Video.status.in_(list(_SEED_DEDUP_STATUSES)),
            )
        )
        existing = existing_result.scalars().first()
        if existing is not None:
            return VideoResponse.model_validate(existing)

        platform = _detect_platform(source_url)

        video = Video(
            title="Processing...",
            source_url=source_url,
            video_source=platform,
            status=VideoStatus.processing,
            is_official=True,
            # Seeded as a draft: stays off the homepage until published. The
            # one-click flow sets auto_publish=True so finalize_video publishes it
            # automatically once ready; the manual flow leaves it False for review.
            is_published=False,
            auto_publish=auto_publish,
            processing_started_at=datetime.now(UTC),
        )
        db.add(video)
        await commit_refresh(db, video)

        from app.tasks.video_processing import process_video

        try:
            process_video.delay(video.id)
        except Exception as exc:
            # Never leave a row sitting in `processing` with no task queued.
            logger.exception("Failed to dispatch process_video for video %s", video.id)
            video.status = VideoStatus.error
            video.error_message = f"管线任务派发失败：{exc}"
            await commit_refresh(db, video)
            raise ServiceUnavailableError("视频已创建但管线任务派发失败，请稍后重试") from exc

        return VideoResponse.model_validate(video)
    finally:
        await _delete_redis_key(lock_key)


# ---------------------------------------------------------------------------
# Admin-triggered processing
# ---------------------------------------------------------------------------

_WORKER_HEARTBEAT_KEY = GPU_HEARTBEAT_KEY


async def is_gpu_worker_online() -> bool:
    """Check if the local GPU worker is online (heartbeat present in Redis)."""
    try:
        r = get_redis()
        return bool(await r.exists(_WORKER_HEARTBEAT_KEY))
    except Exception:
        return False


async def start_processing(db: AsyncSession, video_id: str) -> VideoResponse:
    """Admin triggers GPU processing for a pending_processing video.

    Only allowed when:
    - The video exists and is in ``pending_processing`` status.
    - The local GPU worker is confirmed online (Redis heartbeat key present).

    Raises:
        NotFound: If the video is not found.
        Invalid: If the video is not in pending_processing status.
        Unavailable: If the GPU worker is offline.
    """
    require_content_production(model=True)
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if video is None:
        raise NotFoundError("Video not found")
    if video.status != VideoStatus.pending_processing:
        raise BadRequestError(f"Video is not in pending_processing state (current: {video.status.value})")

    # Check GPU worker heartbeat
    worker_online = await is_gpu_worker_online()
    if not worker_online:
        raise ServiceUnavailableError("GPU worker is offline — please start the local processing service first")

    # Transition to processing and dispatch Celery task
    video.status = VideoStatus.processing
    video.processing_started_at = datetime.now(UTC)
    await commit_refresh(db, video)

    from app.tasks.video_processing import process_video

    process_video.delay(video.id)

    return VideoAdminResponse.model_validate(video)


async def recover_processing(db: AsyncSession, video_id: str) -> VideoAdminResponse:
    """Re-dispatch ``finalize_video`` for a video stuck mid-pipeline.

    When the cloud Celery worker dies during ``finalize_video`` (the most
    common cause of a stuck video), the ``video:processing:{id}`` Redis lock
    is left behind and ``finalize_video`` refuses to re-run ("already being
    processed, skipping"). This clears that stale lock and re-dispatches
    ``finalize_video``, which is resume-safe — each step checks
    ``_is_step_done()`` and skips completed work (translating / annotating /
    prewarm_notes / downloading).

    ADM-03: the lock is **not** deleted unconditionally any more. It is only
    cleared when it is provably stale (``step_started_at`` older than the
    current step's watchdog budget × 1.2). A live lock means a worker is still
    running; recovering then would let two finalize runs write the same
    subtitle rows, so the request answers 409 instead. A 60s single-flight key
    per video also collapses double clicks.

    Only allowed for the stuck statuses (``processing`` / ``ready_subtitles``).
    A video still pending GPU trigger should use ``start_processing``; a
    ``ready`` / ``error`` video needs no recovery. No worker-online gate:
    finalize runs on the ``celery`` queue (cloud worker), not the GPU worker,
    so the task simply queues until a cloud worker is up — standard Celery.

    Raises:
        NotFound: If the video is not found.
        Invalid: If the video is not in a recoverable status.
        Conflict: If the pipeline still holds a live lock, or a recover/retry
            for this video already ran in the last 60 seconds.
    """
    require_content_production(model=True)
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if video is None:
        raise NotFoundError("Video not found")
    if video.status not in (VideoStatus.processing, VideoStatus.ready_subtitles):
        raise BadRequestError(
            f"Video is not in a recoverable state (current: {video.status.value}). "
            f"Use start-processing for pending_processing; ready/error need no recovery."
        )

    lock_live, lock_detail = await _processing_lock_live(video)
    if lock_live:
        raise ConflictError(
            f"视频仍在处理中（{lock_detail}），无需恢复；请等待任务结束，确认卡死后再等步骤预算过期后重试"
        )
    if not await _acquire_single_flight(f"pipeline:resume:{video.id}", _RESUME_LOCK_TTL_SECONDS):
        raise ConflictError("该视频刚刚触发过恢复/重试，60 秒内请勿重复操作")

    # Stale (or absent) lock: clear it so finalize_video can re-acquire.
    await _delete_redis_key(f"video:processing:{video.id}")

    from app.tasks.video_processing import finalize_video

    try:
        finalize_video.delay(str(video.id))
    except Exception as exc:
        logger.exception("Failed to dispatch recover for video %s", video.id)
        # Release the 60s single-flight key so the admin can retry at once.
        await _delete_redis_key(f"pipeline:resume:{video.id}")
        raise ServiceUnavailableError("恢复任务派发失败，请稍后重试") from exc

    return VideoAdminResponse.model_validate(video)


async def retry_video(db: AsyncSession, video_id: str) -> VideoAdminResponse:
    """Resume an errored video from the last completed pipeline step.

    Unlike a blind reset, this preserves the Redis completed-step set so
    ``finalize_video``'s ``is_step_done()`` checks can skip work that already
    succeeded. The resume point is decided by the ground-truth presence of
    subtitles in the DB:

    * Subtitles exist -> transcription succeeded; jump straight to the tail
      (``finalize_video``), keeping the step set so translating/annotating/
      downloading/transcoding that already finished are skipped.
    * No subtitles -> transcription never produced output; reset to
      ``pending_processing`` and clear the step set so the admin can trigger
      a fresh full run via ``start_processing``.

    Only the processing lock is cleared in the subtitle-exists branch — the
    step set is intentionally kept. Compare ``recover_processing`` (re-dispatch
    finalize for videos stuck mid-pipeline without an error state).

    ADM-03: same live-lock rule as ``recover_processing`` — a lock inside the
    current step's watchdog budget is not deleted (409), and a 60s single-flight
    key per video collapses double clicks.

    Raises:
        NotFound: If the video is not found.
        Invalid: If the video is not in error status.
        Conflict: If a live pipeline lock is still held, or a recover/retry for
            this video already ran in the last 60 seconds.
    """
    require_content_production(model=True)
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if video is None:
        raise NotFoundError("Video not found")
    if video.status != VideoStatus.error:
        raise BadRequestError(
            f"Video is not in error state (current: {video.status.value}). "
            f"Use recover for processing/ready_subtitles; start-processing for pending_processing."
        )

    lock_live, lock_detail = await _processing_lock_live(video)
    if lock_live:
        raise ConflictError(f"视频仍有处理中的任务持锁（{lock_detail}），请等待其结束后再重试")
    if not await _acquire_single_flight(f"pipeline:resume:{video.id}", _RESUME_LOCK_TTL_SECONDS):
        raise ConflictError("该视频刚刚触发过恢复/重试，60 秒内请勿重复操作")

    from app.services.video_service import count_subtitles
    from app.tasks.video_processing import finalize_video

    # Subtitles in the DB are ground truth that transcription already
    # succeeded (the callback only inserts on status=ok). Decide the resume
    # point from this — not from processing_step, which error paths may have
    # already cleared.
    subtitle_count = await count_subtitles(db, video.id)

    # Release the (stale or absent) processing lock so the head/tail can
    # re-acquire it. The step set is kept in the resume branch (only cleared
    # when starting over).
    await _delete_redis_key(f"video:processing:{video.id}")

    if subtitle_count > 0:
        # Transcription succeeded before the failure — resume from the tail.
        # Keep video:steps so finalize_video skips already-completed steps.
        video.status = VideoStatus.ready_subtitles
        video.error_message = None
        video.processing_step = "translating"
        video.processing_progress = 70
        await commit_refresh(db, video)
        try:
            finalize_video.delay(str(video.id))
        except Exception as exc:
            logger.exception("Failed to dispatch retry for video %s", video.id)
            # Roll the resume bookkeeping back so the row stays retryable with
            # its original error state, and free the single-flight key.
            video.status = VideoStatus.error
            video.error_message = "任务派发失败，请稍后重试"
            video.processing_step = None
            video.processing_progress = 0
            try:
                await commit_refresh(db, video)
            except Exception:
                logger.exception("Failed to restore video %s after retry dispatch failure", video.id)
                await db.rollback()
            await _delete_redis_key(f"pipeline:resume:{video.id}")
            raise ServiceUnavailableError("重试任务派发失败，请稍后重试") from exc
    else:
        # No subtitles -> transcription never produced output; start over.
        # This is the only branch that clears the step set.
        video.status = VideoStatus.pending_processing
        video.error_message = None
        video.processing_step = None
        video.processing_progress = 0
        await _delete_redis_key(f"video:steps:{video.id}")
        await commit_refresh(db, video)

    return VideoAdminResponse.model_validate(video)


_RETRANSLATE_ALLOWED_STATUSES = (VideoStatus.error, VideoStatus.ready)


async def retranslate_video(db: AsyncSession, video_id: str, engine: str | None = None) -> VideoAdminResponse:
    """Re-run the translation step, optionally with a different engine.

    Used after a translation quality block (``quality_flag=quality_blocked``)
    or warning (``quality_flag=quality_warning``) to retry translation. The same
    engine + same input would reproduce the low coverage, so an admin can
    override the engine (e.g. ``glm``) to break out of a bad-engine loop.

    Clears existing ``text_zh`` so the re-run is clean (a partial new run
    wouldn't otherwise overwrite slots the new engine leaves None), resets
    ``quality_flag``, and re-dispatches ``finalize_video`` with the engine
    override. Only the ``translating`` completed-step marker is cleared -
    annotating/downloading/transcoding don't depend on ``text_zh`` and stay
    marked done so they're skipped.

    ADM-02 hardenings:

    * status guard — only ``error`` / ``ready`` are acceptable; a video in
      ``processing`` / ``ready_subtitles`` / ``pending_processing`` has a live
      pipeline and gets 409 (clearing its translations would race the run);
    * the ``engine`` value is validated against the translation registry (422
      for an unknown name, instead of failing later inside the Celery task);
    * a Redis single-flight key (300s) blocks double clicks;
    * if the Celery dispatch raises after the translations were cleared and
      committed, the pre-click ``text_zh`` values *and* the video state are
      restored before answering 503 — a video must never end up with all
      translations wiped and no task queued.

    Raises:
        NotFound: If the video is not found.
        Conflict: If the video is mid-pipeline or a retranslate is already queued.
        Invalid: If the video has no subtitles to translate.
        Unprocessable: If ``engine`` is not a known translation engine.
    """
    require_content_production(model=True)
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if video is None:
        raise NotFoundError("Video not found")

    # Validate the request before touching any state (422 / 409 ordering: an
    # unknown engine is always a client error, whatever the video's status).
    _validate_retranslate_engine(engine)

    if video.status not in _RETRANSLATE_ALLOWED_STATUSES:
        raise ConflictError(
            f"视频当前状态为 {video.status.value}，正在跑管线，不能重新翻译；"
            f"请等待任务结束，或用 recover/retry 处理卡住的状态"
        )

    from app.services.video_service import count_subtitles

    if await count_subtitles(db, video.id) == 0:
        raise BadRequestError("Video has no subtitles to translate")

    if not await _acquire_single_flight(f"retranslate:{video.id}", _RETRANSLATE_LOCK_TTL_SECONDS):
        raise ConflictError("该视频已有重新翻译任务在进行中，请勿重复点击")

    subs = list((await db.execute(select(Subtitle).where(Subtitle.video_id == video.id))).scalars().all())
    previous_zh = {s.id: s.text_zh for s in subs}
    # Typed locals (not a dict) so mypy keeps the ORM column types for the
    # restore below.
    prev_status = video.status
    prev_quality_flag = video.quality_flag
    prev_error_message = video.error_message
    prev_processing_step = video.processing_step
    prev_processing_progress = video.processing_progress

    # Clear existing translations so the re-run writes fresh text_zh everywhere.
    for s in subs:
        s.text_zh = None

    video.quality_flag = None
    video.status = VideoStatus.ready_subtitles
    video.error_message = None
    video.processing_step = "translating"
    video.processing_progress = 70

    # Clear only the translating marker so finalize re-runs it; keep other
    # steps' markers (they don't depend on text_zh).
    had_translating_marker = await _clear_translating_marker(str(video.id))
    # Release any stale processing lock so finalize can re-acquire it.
    await _delete_redis_key(f"video:processing:{video.id}")

    await commit_refresh(db, video)

    from app.tasks.video_processing import finalize_video

    try:
        finalize_video.delay(str(video.id), engine=engine)
    except Exception as exc:
        # The clear + status flip is already committed. Restore both from the
        # snapshot so the video is exactly where it was before the click: no
        # wiped-translation-with-no-task state (ADM-02).
        logger.exception("Failed to dispatch retranslate for video %s; restoring state", video.id)
        for s in subs:
            s.text_zh = previous_zh.get(s.id)
        video.status = prev_status
        video.quality_flag = prev_quality_flag
        video.error_message = prev_error_message
        video.processing_step = prev_processing_step
        video.processing_progress = prev_processing_progress
        if had_translating_marker:
            await _restore_translating_marker(str(video.id))
        try:
            await commit_refresh(db, video)
        except Exception:
            logger.exception("Failed to restore video %s after dispatch failure", video.id)
            await db.rollback()
        # Release the single-flight key: the admin must be able to retry
        # immediately after a transient broker failure.
        await _delete_redis_key(f"retranslate:{video.id}")
        raise ServiceUnavailableError("重新翻译任务派发失败，已恢复原有译文，请稍后重试") from exc

    return VideoAdminResponse.model_validate(video)
