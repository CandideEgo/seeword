"""GPU transcription task + cloud callback delivery.

Moved out of ``backend/app/tasks/video_processing.py`` (the GPU segment of the
head / GPU / tail split) with the logic unchanged. What differs is only the
import surface: settings/logging/source-enum/cookies now come from
``gpu_worker.*`` instead of ``app.*``, and there is no database, no OSS and no
pipeline state here by design.

The task runs on the desktop GPU machine, consumes the ``transcription_gpu``
queue, transcribes with WhisperX (faster-whisper fallback) and POSTs the
subtitles back to the cloud callback endpoint. Its only output channel is that
HTTP callback.
"""

import asyncio
import time

from gpu_worker.alerts import send_alert
from gpu_worker.celery_app import celery_app
from gpu_worker.config import get_settings
from gpu_worker.contracts import CALLBACK_SECRET_HEADER, TASK_NAME
from gpu_worker.logging import get_logger
from gpu_worker.sources import VideoSource

logger = get_logger(__name__)

# Re-exported for callers/tests that refer to ``gpu_worker.tasks.TASK_NAME``.
# The value itself lives in ``gpu_worker.contracts`` (one fact, one home).
__all__ = ["TASK_NAME", "transcribe_video_gpu"]


def _post_transcription_callback(
    video_id: str,
    status: str,
    segments: list[dict] | None = None,
    error: str | None = None,
    audio_duration: float | None = None,
) -> bool:
    """POST transcription results to the cloud callback endpoint.

    Retries 5xx / 408 / 425 / 429 and transport errors with exponential
    backoff. Other 4xx responses are permanent client-side problems (bad
    secret, deleted video, invalid payload) and are not retried. Returns True
    on acknowledged delivery. Used by the GPU worker, which has no database
    access.

    The callback endpoint itself rate-limits at 30/min, so 429 is transient and
    must be retried — treating every 4xx as permanent used to drop a finished
    GPU transcription on the floor.
    """
    import httpx

    settings = get_settings()
    url = settings.transcription_callback_url
    if not url:
        logger.error("TRANSCRIPTION_CALLBACK_URL not set; cannot deliver transcription for %s", video_id)
        return False

    payload = {
        "video_id": video_id,
        "status": status,
        "segments": (
            [
                {
                    "start": s["start"],
                    "end": s["end"],
                    "text": s["text"],
                    # Forward word-level timestamps so the cloud can persist
                    # them for precise split/merge + re-segmentation.
                    "words": s.get("words"),
                }
                for s in segments
            ]
            if status == "ok" and segments
            else None
        ),
        "error": error,
        # Phase 2: forward the REAL audio duration for hallucination detection.
        # It used to be ``segments[-1]["end"]``, which is derived from the same
        # subtitles the cloud compares it against — `last_end > duration * 1.5`
        # then can never fire, so the duration check silently passed always.
        # The value now comes from ffprobe in ``_sync_transcribe``.
        "audio_duration": audio_duration if status == "ok" else None,
    }
    headers = {CALLBACK_SECRET_HEADER: settings.transcription_callback_secret}
    max_retries = settings.transcription_callback_max_retries
    timeout = settings.transcription_callback_timeout
    transient_4xx = {408, 425, 429}

    for attempt in range(max_retries + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, json=payload, headers=headers)
            if 200 <= resp.status_code < 300:
                logger.info("Transcription callback delivered", video_id=video_id, status=status, attempt=attempt)
                return True
            if 400 <= resp.status_code < 500 and resp.status_code not in transient_4xx:
                logger.error(
                    "Transcription callback rejected (permanent 4xx, not retrying)",
                    video_id=video_id,
                    code=resp.status_code,
                    body=resp.text[:200],
                )
                return False
            # 5xx and transient 4xx (rate limit / timeout / too early) → retry
            logger.warning(
                "Transcription callback transient failure",
                video_id=video_id,
                code=resp.status_code,
                attempt=attempt,
            )
        except httpx.HTTPError as e:
            logger.warning("Transcription callback error", video_id=video_id, attempt=attempt, error=str(e))
        if attempt < max_retries:
            time.sleep(min(2**attempt, 30))
    logger.error("Transcription callback exhausted retries", video_id=video_id, status=status)
    return False


def _send_alert_sync(title: str, message: str, *, severity: str = "critical") -> None:
    """Fire an alert from a synchronous Celery task (best effort).

    ``send_alert`` is async because the webhook uses httpx; the GPU task is
    synchronous and runs in a prefork worker with no event loop, so a fresh
    loop is safe here. Never let alerting break the task itself.
    """
    try:
        asyncio.run(send_alert(title, message, severity=severity))
    except Exception:
        logger.warning("GPU task alert delivery failed", exc_info=True)


# The task name is a compatibility contract, NOT this module's dotted path:
# the cloud enqueues ``app.tasks.video_processing.transcribe_video_gpu`` and a
# rename would orphan messages already sitting in the transcription_gpu queue.
# Keep the old name even though this code lives in ``gpu_worker`` now.
@celery_app.task(bind=True, max_retries=3, name=TASK_NAME)
def transcribe_video_gpu(self, video_id: str, source: str, platform: str, language: str | None = None):
    """Transcribe a video on the GPU worker and POST subtitles back to the cloud.

    Runs on a remote machine (``transcription_gpu`` queue). Does NOT touch the
    database — results are delivered via HTTP callback so the worker needs no
    ``DATABASE_URL``. ``language`` is reserved for future use (v1 relies on the
    worker's ``WHISPER_LANGUAGE`` setting).
    """
    from gpu_worker.transcription import TranscriptionService

    try:
        svc = TranscriptionService()
        segments = svc._sync_transcribe(source, VideoSource(platform))
        audio_duration = getattr(svc, "last_audio_duration", None)
    except Exception as e:
        logger.exception("GPU transcription failed for video %s", video_id)
        if self.request.retries >= self.max_retries:
            # Let the cloud know transcription is unrecoverable so it can mark
            # the video failed instead of waiting for the watchdog.
            _post_transcription_callback(video_id, status="error", error=str(e))
            _send_alert_sync(
                "GPU 转录最终失败",
                f"video {video_id}: {e}",
            )
            raise
        raise self.retry(exc=e, countdown=60) from e

    if not _post_transcription_callback(video_id, status="ok", segments=segments, audio_duration=audio_duration):
        # The transcription itself succeeded; only delivery failed (e.g.
        # rate limit / network). Retrying re-runs the transcription, but that
        # is cheaper than leaving the video stuck in ``processing`` with a
        # silently "successful" Celery task.
        logger.error("GPU transcription callback delivery failed; retrying task for %s", video_id)
        if self.request.retries >= self.max_retries:
            _send_alert_sync(
                "GPU 转录回调投递最终失败",
                f"video {video_id}: callback still undeliverable after {self.max_retries} retries",
            )
        raise self.retry(
            exc=RuntimeError(f"transcription callback delivery failed for {video_id}"),
            countdown=60,
        )
