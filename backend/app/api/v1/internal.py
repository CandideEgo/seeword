"""Internal API endpoints — not for public/frontend consumption.

Currently hosts the transcription callback: the remote GPU worker POSTs its
Whisper transcription results here so the cloud can persist subtitles and kick
off the pipeline tail. Authenticated by a shared secret (no JWT).
"""

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.capabilities import require_content_production
from app.core.config import get_settings
from app.core.database import get_db
from app.core.limiter import rate_limit
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.models.subtitle import Subtitle
from app.models.video import Video, VideoStatus
from app.schemas.common import AcknowledgedResponse
from app.schemas.video import TranscriptionCallbackRequest
from app.services.transcription_quality import check_transcription_quality, log_quality_report

router = APIRouter(prefix="/internal", tags=["internal"])

logger = get_logger(__name__)

# Redis-based dedup lock for the callback endpoint.  Two concurrent callbacks
# (e.g. a Celery retry that fires a second POST before the first commits) can
# both read ``status == processing`` and proceed, causing double subtitle
# insert + double ``finalize_video.delay()``.  The lock serialises them.
_CALLBACK_LOCK_TTL = 5 * 60  # 5 minutes — more than enough for the DB work


async def _acquire_callback_lock(video_id: str) -> bool:
    """Try to acquire a Redis SETNX lock for the callback.  Returns True if
    acquired, False if another callback is already in-flight **or Redis is
    down** (fail-closed).  When Redis is unavailable we reject the callback
    rather than allowing a concurrent double-insert / double-enqueue.  The
    GPU worker will retry after its own backoff.

    Uses the shared async Redis singleton (``app.core.redis.get_redis``) — the
    old implementation created a synchronous redis client per call inside this
    async endpoint, blocking the event loop and leaking a connection pool.
    """
    try:
        r = await get_redis()
        lock_key = f"video:callback:{video_id}"
        return bool(await r.set(lock_key, "1", nx=True, ex=_CALLBACK_LOCK_TTL))
    except Exception:
        # Fail-closed: refuse the callback so the GPU worker retries later.
        # The DB status check alone is insufficient — two concurrent
        # callbacks can both read status==processing before either commits.
        logger.warning(
            "Redis unavailable for callback lock on video %s; rejecting callback (GPU worker will retry)",
            video_id,
            exc_info=True,
        )
        return False


async def _release_callback_lock(video_id: str) -> None:
    """Release the callback lock after successful processing."""
    try:
        r = await get_redis()
        await r.delete(f"video:callback:{video_id}")
    except Exception:
        pass


@router.post("/transcription/callback", response_model=AcknowledgedResponse)
@rate_limit("30/minute")
async def transcription_callback(
    request: Request,
    payload: TranscriptionCallbackRequest,
    x_callback_secret: str = Header(default="", alias="X-Callback-Secret"),
    db: AsyncSession = Depends(get_db),
):
    """Receive transcription results from the remote GPU worker.

    Idempotency: the callback is only honored while the video is still in the
    ``processing`` state (i.e. waiting for transcription). Any later/duplicate
    callback (e.g. a Celery redelivery after the tail has already run) is
    acknowledged but ignored — this prevents both double-enqueuing the tail and
    wiping already-translated subtitles.
    """
    require_content_production(model=True)
    settings = get_settings()
    expected = settings.transcription_callback_secret
    # 常量时间比较必须比 **bytes**：``secrets.compare_digest`` 对非 ASCII 的
    # str 会抛 TypeError（"comparing strings with non-ASCII characters is not
    # supported"）。``x_callback_secret`` 来自 HTTP Header（latin-1 解码，
    # 任何字节都能进来），非 ASCII 时同样的 TypeError 会把 401 变成 500。
    # 先编成 UTF-8 字节再比：既保留常量时间语义，又不会抛异常。
    if not expected or not secrets.compare_digest(x_callback_secret.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid callback secret")

    result = await db.execute(select(Video).where(Video.id == payload.video_id).with_for_update())
    video = result.scalar_one_or_none()
    if not video:
        # Acknowledge so the GPU worker stops retrying a callback for a deleted video.
        return {"acknowledged": True}

    # Only act while transcription is still pending. Once the tail has started
    # (status != processing) the video is past this stage — ignore duplicates.
    if video.status != VideoStatus.processing or video.processing_generation != payload.processing_generation:
        return {"acknowledged": True}

    # Acquire a Redis dedup lock to prevent two concurrent callbacks from both
    # passing the status check and proceeding to double-insert subtitles.
    # If Redis is down (fail-closed), return 503 so the GPU worker retries.
    if not await _acquire_callback_lock(payload.video_id):
        raise HTTPException(
            status_code=503,
            detail="Callback lock unavailable; retry after Redis recovers",
        )

    # The lock serialises callbacks, it does not re-validate state: a previous
    # callback may have completed the tail between the status read above and
    # here, so re-read the row under the lock before acting on it.
    await db.refresh(video, with_for_update=True)
    if video.status != VideoStatus.processing or video.processing_generation != payload.processing_generation:
        await _release_callback_lock(payload.video_id)
        return {"acknowledged": True}

    try:
        if payload.status == "error":
            video.status = VideoStatus.error
            video.error_message = payload.error or "Transcription failed"
            video.processing_step = None
            await db.commit()
            from app.services.pipeline_alerting import record_pipeline_failure

            await record_pipeline_failure(payload.video_id, reason=video.error_message)
            return {"acknowledged": True}

        # status == "ok": insert subtitles and hand off to the tail.
        # Guard against re-inserting: if subtitles already exist (a duplicate
        # callback raced past the status guard, or a prior partial insert left
        # rows behind), keep the existing set rather than wiping them —
        # deleting would discard any already-translated rows.
        segments = payload.segments or []

        # --- Phase 2: hallucination detection ---
        # Run quality checks before persisting. If critical issues are found,
        # mark the video as error so an admin can re-trigger transcription.
        quality_report = check_transcription_quality(segments, audio_duration=payload.audio_duration)
        log_quality_report(payload.video_id, quality_report)
        # Persist the report (best-effort) so the admin panel can show the
        # failure reason - both on failure (why it was blocked) and on success
        # (per-check pass/detail for auditing).
        from app.services.transcription_quality import persist_quality_report

        await persist_quality_report(db, payload.video_id, quality_report)

        if not quality_report.passed:
            video.status = VideoStatus.error
            video.error_message = (
                f"Transcription quality check failed: {', '.join(c.detail for c in quality_report.failed_checks)}"
            )
            video.processing_step = None
            await db.commit()
            from app.services.pipeline_alerting import record_pipeline_failure

            await record_pipeline_failure(
                payload.video_id,
                reason=f"transcription quality: {', '.join(c.detail for c in quality_report.failed_checks)}",
            )
            # 阶段 4: alert admins (best-effort)
            from app.services.notification_service import notify_admins

            await notify_admins(
                db,
                title="转录质量失败",
                message=(f"视频 {payload.video_id} 转录质量检查未通过，已标记 error。可在管理后台重新触发转录。"),
                related_url=f"/admin/videos/{payload.video_id}",
            )
            return {"acknowledged": True, "quality_check": "failed"}

        existing = await db.scalar(
            select(func.count()).select_from(Subtitle).where(Subtitle.video_id == payload.video_id)
        )
        if existing:
            logger.info("Subtitles already exist for video %s, skipping insert", payload.video_id)
        else:
            for i, seg in enumerate(segments):
                db.add(
                    Subtitle(
                        video_id=video.id,
                        start_time=seg.start,
                        end_time=seg.end,
                        text_en=seg.text,
                        sentence_index=i,
                        # Persist word-level timestamps when the GPU worker
                        # sends them — enables precise split/merge + re-segment.
                        words=[w.model_dump() for w in seg.words] if seg.words else None,
                    )
                )
        video.status = VideoStatus.ready_subtitles
        video.processing_step = "translating"
        video.processing_progress = 70
        # A05/BE-01: the intent to run the tail is committed **in this same
        # transaction** as the status change. `delay()` after the commit lost
        # the tail whenever the broker was down or the process died in the gap
        # (and the callback's own retries were then acknowledged as duplicates).
        # The outbox row survives that gap; the beat dispatcher re-sends it, and
        # `dispatch_now` below is only the fast path.
        from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK, dispatch_now, enqueue

        dispatch_id = await enqueue(
            db,
            video_id=payload.video_id,
            task_name=FINALIZE_VIDEO_TASK,
            args=[payload.video_id],
        )
        await db.commit()
        await dispatch_now(db, dispatch_id)
    finally:
        # Release lock so a future retry (if needed) can proceed.
        await _release_callback_lock(payload.video_id)

    return {"acknowledged": True}
