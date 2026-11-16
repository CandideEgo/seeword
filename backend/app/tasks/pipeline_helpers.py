"""Shared infrastructure for the video processing pipeline.

Provides the "lock + step recovery + error commit" skeleton that all three
pipeline tasks (process_video, finalize_video, localize_video) previously
duplicated.  Each task now declares its steps and delegates the plumbing
here — including the step loop itself (``run_steps``), so that "in which
order", "which steps exist" and "what each may take" are one declaration
instead of a declaration plus a hand-written if-sequence.

Design goals (deep-module philosophy):
- **Leverage**: callers get lock/step/error semantics from a single import.
- **Locality**: the "what happens on failure" contract lives in one place.
- **Testability**: ``commit_error_state`` is a single seam for testing
  "any step throws → DB state is consistent".
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.tasks.async_helpers import run_async

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Pipeline steps — single source of truth
# ---------------------------------------------------------------------------

#: Terminal step. Nothing is left running under it, so it budgets no time.
TERMINAL_STEP = "done"

#: A step body: reads and writes the run's blackboard, owes nothing back.
StepBody = Callable[["PipelineCtx"], Awaitable[None]]


@dataclass(frozen=True)
class Step:
    """One pipeline step: resume name, progress percent, watchdog budget, body.

    **Order in ``STEPS`` is the pipeline order** (extracting → … → done). The
    two maps below are views of this tuple, so "what steps exist", "in which
    order" and "what each is allowed to take" cannot drift apart — previously
    the order lived only in ``finalize_video``'s if-sequence, a hundred lines
    away from the two maps that had to agree with it.

    ``timeout_attr`` names the ``Settings`` field holding the budget in
    seconds; ``None`` means "no budget" (the terminal step). It is a name and
    not a value because the watchdog reads settings at call time — an admin
    setting is re-read per run, a module-level constant would freeze it.

    ``run`` is the body. The canonical tuple here leaves it ``None``: bodies
    live with the task that owns them (the tail's bodies call
    ``video_processing``'s helpers), and the task attaches them by name via
    ``dataclasses.replace`` — so the order stays declared here while the code
    stays where its collaborators are.

    ``skip_run`` is for the rare step that still owes something to *later*
    steps when a resume skips it: ``downloading`` must re-derive the local file
    path for ``transcoding`` even when the download already happened.

    ``resumable=False`` marks the terminal step. It is never consulted against
    the completed-step set (there is nothing after it to resume into) and it is
    not stamped as the failure attribution — a failure there belongs to the
    last step that actually did work.
    """

    name: str
    progress: int
    timeout_attr: str | None = None
    run: StepBody | None = None
    skip_run: StepBody | None = None
    resumable: bool = True


STEPS: tuple[Step, ...] = (
    Step("extracting", 10, "pipeline_step_timeout_extracting"),
    Step("transcribing", 30, "video_transcribe_timeout"),  # GPU gap is long
    Step("translating", 70, "pipeline_step_timeout_translating"),
    Step("annotating", 72, "pipeline_step_timeout_annotating"),
    Step("prewarm_notes", 74, "pipeline_step_timeout_prewarm_notes"),
    Step("classifying", 74, "pipeline_step_timeout_classifying"),
    Step("downloading", 75, "pipeline_step_timeout_downloading"),
    Step("transcoding", 90, "pipeline_step_timeout_transcoding"),
    Step(TERMINAL_STEP, 100, resumable=False),
)

# Step name = percent complete for ``Video.processing_progress``. A plain dict
# because that is what the tasks and the status endpoint read.
STEP_PROGRESS: dict[str, int] = {step.name: step.progress for step in STEPS}


def get_step_timeouts() -> dict[str, int]:
    """Per-step watchdog budget in seconds, keyed by ``Video.processing_step``.

    Steps declared without a ``timeout_attr`` (the terminal one) are absent
    here; the watchdog falls back to ``settings.pipeline_step_timeout_default``
    for those.
    """
    settings = get_settings()
    budgets: dict[str, int] = {}
    for step in STEPS:
        timeout_attr = step.timeout_attr
        if timeout_attr:
            budgets[step.name] = getattr(settings, timeout_attr)
    return budgets


@dataclass
class PipelineCtx:
    """Mutable blackboard for one pipeline run.

    Three things travel between steps and cannot be arguments: ``current_step``
    (the attribution ``commit_error_state`` stamps), ``video_path``
    (``downloading`` → ``transcoding``), and a step's right to end the chain
    early — ``stop()``.  Early termination is a first-class outcome, not an
    exception: the error branch stays reserved for "something broke", which is
    what the watchdog and the admin UI read.  Today the only such step is
    ``translating`` on a quality block (``quality_flag = quality_blocked``).
    """

    db: Any
    video: Any
    video_id: str
    engine: str | None = None
    video_path: str | None = None
    current_step: str | None = None
    stopped: bool = False
    processing_generation: str | None = None

    @property
    def run_key(self) -> str:
        from app.services.processing_generation import run_identity

        return run_identity(self.video_id, self.processing_generation)

    @property
    def artifact_key(self) -> str:
        from app.services.processing_generation import artifact_identity

        return artifact_identity(self.video_id, self.processing_generation)

    def stop(self) -> None:
        """End the chain after the current step; no later step runs."""
        self.stopped = True


async def run_steps(ctx: PipelineCtx, steps: tuple[Step, ...]) -> None:
    """Run ``steps`` in order: resume-skip, failure attribution, early stop.

    This is the sequence each task used to re-implement as hand-written
    ``if not await is_step_done(...)`` blocks — eight of them in
    ``finalize_video`` alone, each free to disagree with the declared order.

    Contract:

    - the attribution moves to each resumable step **before** it is looked up,
      matching the blocks this replaces (they assigned the name above their
      guard): a failure after a skipped step is named by that step, and a body
      that raises is never blamed on its predecessor;
    - a resumable step already recorded in Redis is skipped, logged with the
      same wording as before, and its ``skip_run`` (if any) still runs;
    - a body calling ``ctx.stop()`` ends the chain immediately — the terminal
      step included;
    - steps whose ``run`` is ``None`` are declared here but run by another
      task's file (the GPU-side steps), and are passed over;
    - exceptions are **not** caught here: ``commit_error_state`` needs the
      video row and the session, which belong to the caller.
    """
    for step in steps:
        body = step.run
        if body is None:
            continue
        # Keep the processing lock alive across long pipelines: the lock TTL
        # covers the declared budgets, but a run near the limit (or settings
        # changed mid-run) should still hold it through every step boundary.
        refresh_lock(ctx.run_key)
        if step.resumable:
            ctx.current_step = step.name
            if await is_step_done(ctx.run_key, step.name):
                logger.info("Video %s: skipping %s (already done)", ctx.video_id, step.name)
                if step.skip_run is not None:
                    await step.skip_run(ctx)
                continue
        await body(ctx)
        if ctx.stopped:
            return


# ---------------------------------------------------------------------------
# Redis key TTLs
# ---------------------------------------------------------------------------


def lock_ttl_seconds() -> int:
    """Lock TTL long enough to cover the whole tail, plus a cushion.

    The old fixed 60-minute TTL was shorter than the watchdog budgets of the
    steps it protects (translating 30 + prewarm_notes 30 + downloading 60 +
    transcoding 30 = 150+ minutes), so a legitimate long run could lose its
    lock mid-flight and let a second trigger start the same steps. The TTL is
    now the sum of every step budget plus 10 minutes (minimum 60 minutes).
    ``run_steps`` also refreshes the TTL at each step boundary.
    """
    return max(60 * 60, sum(get_step_timeouts().values()) + 10 * 60)


STEPS_TTL_SECONDS = 3 * 60 * 60  # 3 hours (long videos need more time)

# ---------------------------------------------------------------------------
# Module-level sync Redis singleton
# ---------------------------------------------------------------------------

_sync_redis = None


def get_pipeline_redis():
    """Get a shared sync Redis client (module-level singleton).

    Celery tasks are synchronous so we use the sync redis client, sharing
    one connection across the module.
    """
    global _sync_redis
    if _sync_redis is None:
        import redis as redis_lib

        settings = get_settings()
        _sync_redis = redis_lib.from_url(settings.redis_url, decode_responses=True)
    return _sync_redis


# ---------------------------------------------------------------------------
# Progress tracking
# ---------------------------------------------------------------------------


async def update_progress(video_id: str, step: str, extra: dict | None = None) -> None:
    """Record a completed step in Redis.

    - Adds step name to Redis set ``video:steps:{video_id}`` (used for resume)
    - Sets TTL on the step-set

    Note: the DB ``processing_step``/``processing_progress`` fields (which the
    public ``/status`` endpoint reads) are written separately by each task.
    The orphan pub-sub channel (``video:progress:{id}``) was removed — the
    frontend polls the DB status endpoint instead.
    """
    try:
        r = get_pipeline_redis()
        steps_key = f"video:steps:{video_id}"
        r.sadd(steps_key, step)
        r.expire(steps_key, STEPS_TTL_SECONDS)
    except Exception:
        logger.warning("Failed to update progress for video %s step %s", video_id, step, exc_info=True)


async def is_step_done(video_id: str, step: str) -> bool:
    """Check if a step has already been completed (for resume).

    On Redis failure, returns False (fail-closed): we re-run the step rather
    than skipping it.  All pipeline steps are idempotent (translation
    overwrites, annotation overwrites, downloading is a no-op if the file
    exists, transcoding overwrites), so re-execution is safe.  The previous
    fail-open (return True) could skip steps that were never actually
    completed, producing videos marked "ready" with missing
    translations/annotations/transcodes.
    """
    try:
        r = get_pipeline_redis()
        return r.sismember(f"video:steps:{video_id}", step)
    except Exception:
        logger.warning(
            "Redis unavailable when checking step %s for video %s; assuming NOT done (will re-run the step)",
            step,
            video_id,
            exc_info=True,
        )
        return False


# ---------------------------------------------------------------------------
# Distributed lock
# ---------------------------------------------------------------------------


def acquire_lock(video_id: str) -> bool:
    """Try to acquire a Redis lock for processing this video.

    Returns True if acquired.  On Redis failure, returns False (fail-closed):
    we refuse to start processing rather than risking duplicate concurrent
    workers.  The task will be retried by Celery after Redis recovers.
    """
    try:
        r = get_pipeline_redis()
        lock_key = f"video:processing:{video_id}"
        acquired = r.set(lock_key, "1", nx=True, ex=lock_ttl_seconds())
        return bool(acquired)
    except Exception:
        logger.warning(
            "Redis unavailable when acquiring lock for video %s; refusing to process", video_id, exc_info=True
        )
        return False


def release_lock(video_id: str) -> None:
    """Release the processing lock, keeping the completed-step set intact.

    Used by the pipeline head after enqueuing remote transcription: the lock
    is not held across the head→GPU→tail gap, so cross-task coordination
    relies on DB ``status``/``processing_step`` instead.
    """
    try:
        r = get_pipeline_redis()
        r.delete(f"video:processing:{video_id}")
    except Exception:
        logger.warning("Failed to release lock for video %s", video_id, exc_info=True)


def release_lock_and_steps(video_id: str) -> None:
    """Release the processing lock and clear completed steps."""
    try:
        r = get_pipeline_redis()
        r.delete(f"video:processing:{video_id}", f"video:steps:{video_id}")
    except Exception:
        logger.warning("Failed to release lock/steps for video %s", video_id, exc_info=True)


# ---------------------------------------------------------------------------
# Step-started timestamp - per-step watchdog timing
# ---------------------------------------------------------------------------


def touch_step_started_at(video) -> None:
    """Stamp ``video.step_started_at = now``.

    Called at each pipeline step boundary (extracting/transcribing/translating/
    annotating/prewarm_notes/classifying/downloading/transcoding) so the watchdog
    can detect a single stuck step rather than measuring the whole pipeline from
    ``processing_started_at``. Only mutates the in-memory object; the caller
    commits it alongside its other step-state writes.
    """
    from datetime import UTC, datetime

    video.step_started_at = datetime.now(UTC)


def refresh_lock(video_id: str) -> None:
    """Extend the processing lock's TTL at a step boundary (best-effort).

    Only extends an existing key — if the lock is already gone this is a no-op
    (the step will fail/be recovered rather than resurrecting a lost lock).
    """
    try:
        r = get_pipeline_redis()
        r.expire(f"video:processing:{video_id}", lock_ttl_seconds())
    except Exception:
        logger.warning("Failed to refresh lock for video %s", video_id, exc_info=True)


def is_lock_held(video_id: str) -> bool:
    """Check whether the processing lock is currently held (a worker is active).

    Non-mutating (unlike ``acquire_lock``). Used by the watchdog to skip videos
    whose worker is alive but in Celery retry backoff - killing those would
    abort a recovery in progress. On Redis failure, returns False (fail-safe:
    assume not held so a genuinely stuck video isn't stranded forever; worst
    case a mid-retry video is marked error and re-triggered).
    """
    try:
        r = get_pipeline_redis()
        return bool(r.exists(f"video:processing:{video_id}"))
    except Exception:
        logger.warning(
            "Redis unavailable when checking lock for video %s; assuming not held",
            video_id,
            exc_info=True,
        )
        return False


# ---------------------------------------------------------------------------
# Error-state commit — single seam for "any step throws → DB is consistent"
# ---------------------------------------------------------------------------


async def commit_error_state(video, db, error: Exception, *, step: str | None = None) -> None:
    """Set video to error status and commit.  Safe to call from an except block.

    If the commit itself fails, attempts a rollback.  This is the single
    implementation of the error-commit contract — previously duplicated in
    process_video, finalize_video, and localize_video.

    If ``step`` is given, also stamps it onto ``video.processing_step`` so the
    admin UI shows the step that actually failed. Without it the field keeps
    the last successfully-committed step name — which names the step *before*
    the one that broke, since each step only writes its own name after it
    succeeds.
    """
    try:
        video.status = "error"
        video.error_message = str(error)
        if step:
            video.processing_step = step
        await db.commit()
        # A09: keep a time-windowed failure signal for the health monitor.
        # Best-effort — this helper's contract is "never break the pipeline".
        from app.services.pipeline_alerting import record_pipeline_failure

        await record_pipeline_failure(video.id, step=step or video.processing_step, reason=str(error))
    except Exception as exc:
        from app.services.processing_generation import StaleProcessingGenerationError

        if isinstance(exc, StaleProcessingGenerationError):
            raise
        logger.exception("Failed to commit error state for video %s", video.id)
        try:
            await db.rollback()
        except Exception:
            logger.exception("Rollback also failed for video %s", video.id)


# ---------------------------------------------------------------------------
# Task runner — wraps run_async without the forbidden RuntimeError fallback
# ---------------------------------------------------------------------------


def run_pipeline_task(coro) -> None:
    """Run an async pipeline coroutine via the shared event loop.

    If ``run_async`` raises RuntimeError (shared loop thread died), the task
    should fail and let Celery retry — we do NOT create a new event loop
    (that would violate the project convention and break AsyncOpenAI clients
    that cache loop references).
    """
    run_async(coro)
