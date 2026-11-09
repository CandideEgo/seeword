import asyncio
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.media_probe import get_video_duration
from app.services import ecdict
from app.services.video_cache import invalidate_video_playback_cache

# Compatibility imports keep task helpers and maintenance consumers callable;
# media I/O has one owner in services.video_media.
from app.services.video_media import (
    TRANSCODE_PROFILES as TRANSCODE_PROFILES,
)
from app.services.video_media import (
    cleanup_oss_raw as _cleanup_oss_raw,
)
from app.services.video_media import (
    download_video as _download_video,
)
from app.services.video_media import (
    extract_video_info as _extract_video_info,
)
from app.services.video_media import (
    find_local_raw as _find_local_raw,
)
from app.services.video_media import (
    stage_local_upload as _stage_local_upload,
)
from app.services.video_media import (
    transcode_video as _transcode_video,
)
from app.services.video_playback import (
    PlaybackUnavailableError,
    accept_local_renditions,
    has_playback,
    has_renditions,
    record_localization_failure,
    require_playback,
)
from app.tasks.celery_app import GPU_TRANSCRIBE_TASK, celery_app
from app.tasks.pipeline_helpers import (
    STEP_PROGRESS,
    STEPS,
    TERMINAL_STEP,
    PipelineCtx,
    Step,
    StepBody,
    acquire_lock,
    commit_error_state,
    release_lock,
    release_lock_and_steps,
    run_pipeline_task,
    run_steps,
    touch_step_started_at,
    update_progress,
)

if TYPE_CHECKING:
    # Only for the annotation below: the quality module pulls in the
    # translation stack, which the GPU worker's import path must not pay for.
    from app.services.translation.quality import TranslationQualityReport

logger = get_logger(__name__)


async def _translate_subtitles(
    texts: list[str], video_id: str | None = None, engine: str | None = None
) -> tuple[list[str | None], "TranslationQualityReport | None"]:
    """Translate subtitle texts in batches using TranslationService.

    Uses the pluggable TranslationService (with engine selection + fallback)
    instead of AIService.translate_batch which has no fallback support.

    After the main batch pass, retries individual None entries with
    single-item batches to maximize fill rate.

    Phase 2: quality gate runs after translation to detect common issues
    (low coverage, mixed CJK/Latin, suspiciously short translations).

    Args:
        engine: force a specific engine (admin re-translate after a quality
            block). A fresh non-singleton instance is used so the override
            doesn't poison the shared service for other in-flight translations.

    Returns ``(results, quality_report)`` so the caller (finalize_video) can
    persist the report within its own transaction. ``quality_report`` is None
    when ``video_id`` is falsy (caller didn't request a report).
    """
    from app.services.translation import TranslationService, get_translation_service
    from app.services.translation.quality import check_translation_quality, log_translation_quality

    service = TranslationService(engine_override=engine) if engine else get_translation_service()
    results: list[str | None] = [None] * len(texts)

    # Batches run with bounded concurrency instead of strictly one after the
    # other. The old loop turned a 20-minute video into a long chain of LLM
    # round trips; the limit keeps the engine's rate limit respected. Results
    # are written by index, so order and length are unchanged.
    batch_size = service.effective_batch_size
    concurrency = max(1, get_settings().translation_batch_concurrency)
    semaphore = asyncio.Semaphore(concurrency)

    async def _translate_one_batch(offset: int, batch: list[str]) -> None:
        async with semaphore:
            translations = await service.translate_batch(batch)
        for j, t in enumerate(translations):
            results[offset + j] = t

    async with asyncio.TaskGroup() as group:
        for offset in range(0, len(texts), batch_size):
            group.create_task(_translate_one_batch(offset, texts[offset : offset + batch_size]))

    # Retry individual None entries.  Single-item batches eliminate
    # length-mismatch and sentence-merging risks, and each retry goes through
    # the full translate_batch path (benefiting from concurrent dual-engine
    # fan-out when configured). They are grouped under the same concurrency
    # limit rather than awaited one by one.
    none_indices = [i for i, r in enumerate(results) if r is None]
    if none_indices:
        logger.info(
            "Retrying %d untranslated subtitles",
            len(none_indices),
        )

        async def _retry_one(index: int) -> None:
            async with semaphore:
                retry = await service.translate_batch([texts[index]])
            if retry and retry[0] is not None:
                results[index] = retry[0]

        async with asyncio.TaskGroup() as group:
            for index in none_indices:
                group.create_task(_retry_one(index))

    # Phase 2: translation quality gate
    quality_report = None
    if video_id:
        quality_report = check_translation_quality(texts, results)
        log_translation_quality(video_id, quality_report)
        if not quality_report.passed:
            logger.warning(
                "Translation quality issues detected but continuing pipeline",
                video_id=video_id,
                issues=quality_report.issues,
            )

    return results, quality_report


def _translation_quality_decision(
    coverage: float,
    *,
    block_enabled: bool,
    block_coverage: float,
    warn_coverage: float,
) -> str | None:
    """Decide the quality_flag from translation coverage.

    Returns ``"quality_blocked"`` (below block threshold, kill switch on),
    ``"quality_warning"`` (between block and warn), or ``None`` (passed).
    Pure function over explicit thresholds so it is unit-testable without
    running the pipeline or touching settings; the caller resolves the
    effective values (admin settings row first, env as fallback).
    """
    if coverage < warn_coverage:
        if block_enabled and coverage < block_coverage:
            return "quality_blocked"
        return "quality_warning"
    return None


async def _effective_quality_gate(db) -> tuple[bool, float, float]:
    """Resolve the translation quality gate from the admin settings row.

    Falls back to env defaults when the row is absent (no admin panel use
    yet). Returns ``(block_enabled, block_coverage, warn_coverage)``.
    """
    from sqlalchemy import select

    from app.models.admin_setting import SETTINGS_ROW_ID, AdminSetting

    row = (await db.execute(select(AdminSetting).where(AdminSetting.id == SETTINGS_ROW_ID))).scalar_one_or_none()
    settings = get_settings()
    if row is None:
        return (
            settings.translation_quality_block_enabled,
            settings.translation_quality_block_coverage,
            settings.translation_quality_warn_coverage,
        )
    return (
        row.quality_block_enabled,
        float(row.quality_block_threshold),
        float(row.quality_warn_threshold),
    )


@celery_app.task(bind=True, max_retries=3)
def process_video(self, video_id: str):
    """Head of the video pipeline: extract metadata, stage media, enqueue GPU transcription.

    Transcription itself runs on a remote GPU worker (``transcription_gpu``
    queue); this task only prepares the job and hands it off. The tail
    (``finalize_video``) is triggered by the transcription callback endpoint
    once subtitles arrive. The lock is released before the gap — cross-task
    coordination uses DB ``status``/``processing_step``.
    """
    if not acquire_lock(video_id):
        logger.warning("Video %s is already being processed, skipping", video_id)
        return

    from sqlalchemy import select

    from app.core.database import async_session
    from app.models.video import Video, VideoSource, VideoStatus

    async def _process():
        async with async_session() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                logger.error("Video %s not found", video_id)
                release_lock_and_steps(video_id)
                return

            try:
                settings = get_settings()
                current_step = "extracting"  # head task's primary step; shown on error

                # --- Resume check: skip transcription if subtitles exist ---
                # If subtitles are already in the DB, a prior run's transcription
                # succeeded (the callback only inserts on status=ok). Re-enqueuing
                # GPU transcription would waste GPU time and risk clobbering good
                # subtitles. Jump straight to the tail; finalize_video's
                # is_step_done() checks then skip any steps that already finished.
                from app.services.video_service import count_subtitles

                subtitle_count = await count_subtitles(db, video.id)
                if subtitle_count > 0:
                    logger.info(
                        "Video %s: subtitles already exist (%d), skipping transcription",
                        video_id,
                        subtitle_count,
                    )
                    video.status = VideoStatus.ready_subtitles
                    video.processing_step = "translating"
                    touch_step_started_at(video)
                    video.processing_progress = 70
                    # Same durable hand-off as the callback: the row is written in
                    # this transaction, then sent (A05/BE-01).
                    from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK, dispatch_now, enqueue

                    dispatch_id = await enqueue(
                        db,
                        video_id=video.id,
                        task_name=FINALIZE_VIDEO_TASK,
                        args=[video_id],
                    )
                    await db.commit()
                    release_lock(video_id)
                    await dispatch_now(db, dispatch_id)
                    return

                # --- Pre-check: refresh YouTube cookies if needed ---
                if video.video_source == VideoSource.imported:
                    from app.services.youtube_cookies_service import ensure_cookies_for_pipeline

                    cookie_result = await ensure_cookies_for_pipeline(video.source_url)
                    if cookie_result.status == "ok":
                        logger.info("Video %s: cookies valid", video_id)
                    elif cookie_result.cookies_path:
                        logger.warning(
                            "Video %s: cookies %s — continuing with existing file",
                            video_id,
                            cookie_result.message,
                        )
                    else:
                        logger.info(
                            "Video %s: no cookies file — proceeding without cookies (%s)",
                            video_id,
                            cookie_result.message,
                        )

                # --- Step: extracting (metadata) ---
                if video.video_source == VideoSource.imported:
                    info = await _extract_video_info(video.source_url)
                    if info is None:
                        raise Exception(f"Failed to extract video info from {video.source_url}")
                    video.title = info.get("title") or video.title
                    video.thumbnail_url = info.get("thumbnail")
                    video.duration = info.get("duration")
                    # 封面本地化：外部 URL 在渲染期依赖 /media/proxy 出口，
                    # ingest 时下载到媒体卷，断掉这条运行时依赖（任务 3）。
                    # 失败不阻断管线：保留外部 URL，后续可用
                    # scripts/backfill_local_thumbnails.py 补。
                    if video.thumbnail_url:
                        from app.services.thumbnail_service import localize_video_thumbnail

                        await localize_video_thumbnail(
                            video,
                            fallback_urls=info.get("thumbnail_fallbacks") or [],
                        )
                    # 阶段 1: persist external (YouTube) metadata — channel,
                    # upload date, external view/like counts, extras blob.
                    if info.get("external"):
                        from app.services.external_meta import apply_external_meta

                        apply_external_meta(video, info["external"])
                        # ADR-0014: attach to a curated channel registered for
                        # this upstream channel id (no-op when none matches).
                        from app.services.channel_service import auto_attach_channel

                        await auto_attach_channel(db, video)
                else:  # local upload — yt-dlp can't read a local path; use ffprobe
                    video.duration = get_video_duration(video.source_url)
                    if not video.title:
                        video.title = Path(video.source_url).stem
                video.processing_step = "extracting"
                touch_step_started_at(video)
                video.processing_progress = 10
                await db.commit()
                await update_progress(video_id, "extracting")

                # --- Stage media for the GPU worker ---
                if video.video_source == VideoSource.imported:
                    # GPU worker streams audio from the source URL via yt-dlp.
                    gpu_source = video.source_url
                    gpu_platform = VideoSource.imported.value
                else:
                    # Local upload → OSS (signed URL) so the GPU worker can fetch it.
                    gpu_source, _raw_key = await _stage_local_upload(video)
                    gpu_platform = VideoSource.local.value

                # --- Enqueue remote transcription ---
                video.status = VideoStatus.processing
                video.processing_step = "transcribing"
                touch_step_started_at(video)
                video.processing_progress = 30

                # The transcription implementation lives in the standalone
                # ``gpu-worker/`` component (GPU machine). The cloud only knows
                # the Celery task name — it has no import path to the worker.
                #
                # A05/BE-01: record the hand-off in the same transaction as the
                # status change, then send. A broker outage no longer fails the
                # head (which used to mark the video error and retry the whole
                # extraction): the intent stays pending and the beat dispatcher
                # re-sends it.
                from app.services.pipeline_dispatch import dispatch_now, enqueue

                dispatch_id = await enqueue(
                    db,
                    video_id=video.id,
                    task_name=GPU_TRANSCRIBE_TASK,
                    args=[video.id, gpu_source, gpu_platform],
                    queue=settings.transcription_gpu_queue_name,
                )
                await db.commit()
                await update_progress(video_id, "transcribing")
                await dispatch_now(db, dispatch_id)
                logger.info("Video %s: GPU transcription handed off", video_id)

                # Release the lock but keep the step-set; the gap to the tail is
                # bridged by DB status, not a held lock.
                release_lock(video_id)

            except Exception as e:
                logger.exception("Video %s head processing failed", video_id)
                await commit_error_state(video, db, e, step=current_step)
                # Always release the lock so Celery's retry can re-acquire it.
                # Keep the completed-step set so a retry (automatic or manual)
                # resumes from the last successful step rather than re-running
                # everything from scratch.
                release_lock(video_id)
                raise self.retry(exc=e) from e

    run_pipeline_task(_process())


# ---------------------------------------------------------------------------
# Pipeline tail: translate → download → transcode → ready (triggered by callback)
# ---------------------------------------------------------------------------


async def _register_standard(db, video) -> None:
    """Register ``video`` as the standard version for its ``source_url``.

    First-ready-wins: if a standard already exists for this URL (a concurrent
    finalize on a duplicate submission, or a prior ready), the INSERT becomes
    a no-op. The ``video_standards.source_url`` PK is the race backstop — two
    finalizes cannot both register a standard for the same URL.

    Dialect-specific INSERT ... ON CONFLICT DO NOTHING (Postgres + SQLite both
    support it; tests run on SQLite, prod on Postgres). Failure here is
    non-fatal: the video is already ``ready``, and the standard can be
    backfilled later, so we log and continue rather than failing finalize.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    from app.models.video_standard import VideoStandard

    try:
        dialect = db.bind.dialect.name
        stmt = (
            (pg_insert(VideoStandard) if dialect == "postgresql" else sqlite_insert(VideoStandard))
            .values(source_url=video.source_url, canonical_video_id=video.id)
            .on_conflict_do_nothing(index_elements=["source_url"])
        )
        await db.execute(stmt)
        await db.commit()
    except Exception:
        logger.warning("Video %s: failed to register standard version (continuing)", video.id, exc_info=True)


async def _run_translating(ctx: PipelineCtx) -> None:
    """Translate every subtitle, then apply the coverage quality gate.

    A blocked video **ends the chain here** (``ctx.stop()``) rather than taking
    the error path: the same engine on the same input would reproduce the same
    low coverage and only burn LLM quota. The admin re-translates with another
    engine — or with the gate switched off — via ``POST /admin/{id}/retranslate``.
    """
    from sqlalchemy import select

    from app.models.subtitle import Subtitle
    from app.models.video import VideoStatus

    db, video, video_id = ctx.db, ctx.video, ctx.video_id
    # Stamp the translating step *before* the LLM work starts. The old code
    # only touched step_started_at after every subtitle was translated, so the
    # watchdog kept seeing the transcription start time while a long
    # translation was legitimately running and could mark the video error.
    video.processing_step = "translating"
    touch_step_started_at(video)
    video.processing_progress = STEP_PROGRESS["translating"]
    await db.commit()
    sub_result = await db.execute(
        select(Subtitle).where(Subtitle.video_id == video.id).order_by(Subtitle.sentence_index)
    )
    sub_rows = list(sub_result.scalars().all())
    # Preserve original row index when filtering out empty
    # text_en — translating a filtered list and writing back
    # with the same enumerate index shifts every translation
    # past the first empty row onto the wrong subtitle (the
    # root cause of "some subtitles translated, some not").
    indexed = [(i, s.text_en) for i, s in enumerate(sub_rows) if s.text_en]
    texts = [t for _, t in indexed]
    translated, quality_report = await _translate_subtitles(texts, video_id=video.id, engine=ctx.engine)
    for j, t in enumerate(translated):
        if t:
            sub_rows[indexed[j][0]].text_zh = t
    # Persist the translation quality report within this
    # transaction (best-effort; never fails the pipeline).
    if quality_report is not None:
        from app.services.translation.quality import persist_quality_report

        await persist_quality_report(db, video.id, quality_report)
        # 阶段 2: coverage-based block/warn decision. Blocked
        # videos stop the pipeline WITHOUT a Celery retry - the
        # same engine + same input would reproduce the low
        # coverage and waste LLM quota. Admin re-translates
        # (optionally with a different engine) via
        # POST /admin/{id}/retranslate. kill switch:
        # translation_quality_block_enabled=False reverts to
        # warn-only for a bad engine batch.
        coverage = quality_report.coverage_ratio
        block_enabled, block_coverage, warn_coverage = await _effective_quality_gate(db)
        decision = _translation_quality_decision(
            coverage,
            block_enabled=block_enabled,
            block_coverage=block_coverage,
            warn_coverage=warn_coverage,
        )
        if decision == "quality_blocked":
            video.quality_flag = "quality_blocked"
            video.status = VideoStatus.error
            video.error_message = f"Translation coverage {coverage:.0%} below block threshold {block_coverage:.0%}"
            video.processing_step = None
            video.step_started_at = None
            await db.commit()
            from app.services.pipeline_alerting import record_pipeline_failure

            await record_pipeline_failure(video_id, step="translating", reason=video.error_message)
            # 阶段 4: alert admins (best-effort; never fails pipeline)
            from app.services.notification_service import notify_admins

            await notify_admins(
                db,
                title="翻译质量阻塞",
                message=(f"视频 {video_id} 翻译覆盖率 {coverage:.0%}，已标记 error。可在管理后台换引擎重触发翻译。"),
                related_url=f"/admin/videos/{video_id}",
            )
            release_lock_and_steps(video_id)
            logger.warning(
                "Video %s translation blocked (coverage %.0f%%)",
                video_id,
                coverage * 100,
            )
            ctx.stop()
            return
        video.quality_flag = decision  # "quality_warning" or None

    # Best-effort Chinese title for every card surface. It runs inside the same
    # transaction as the subtitle translations but must never fail the step —
    # translate_video_title already swallows engine errors and returns None.
    if not video.title_zh:
        from app.services.video_title import translate_video_title

        video.title_zh = await translate_video_title(video.title, engine=ctx.engine)

    video.processing_progress = STEP_PROGRESS["translating"]
    await db.commit()
    await update_progress(video_id, "translating")


async def _run_annotating(ctx: PipelineCtx) -> None:
    """Tag subtitles with exam-level word keys — pure local ECDICT, no AI.

    ``Subtitle.word_levels`` maps lemma → exam level keys once, level-agnostic;
    the watch page filters by the reader's target exam at display time. An
    existing annotation wins (manual review override, or a re-run where
    ``text_en`` did not change but the pipeline re-ran).

    A missing ECDICT db is not a failure: the step records itself done and
    ``word_levels`` stays null.
    """
    from sqlalchemy import select

    from app.models.subtitle import Subtitle

    db, video, video_id = ctx.db, ctx.video, ctx.video_id
    if not ecdict.is_available():
        logger.warning(
            "Video %s: skipping annotating (ECDICT db missing at %s)",
            video_id,
            ecdict.DB_PATH,
        )
        await update_progress(video_id, "annotating")
        return

    ann_result = await db.execute(
        select(Subtitle).where(Subtitle.video_id == video.id).order_by(Subtitle.sentence_index)
    )
    annotated_count = 0
    preserved_count = 0
    for s in ann_result.scalars().all():
        if s.word_levels is not None:
            # Preserve existing annotation (manual override or prior compute)
            preserved_count += 1
            continue
        levels = ecdict.annotate_text(s.text_en)
        s.word_levels = levels or None
        annotated_count += 1
    if preserved_count > 0:
        logger.info(
            "Video %s: preserved %d existing word_levels, annotated %d new",
            video_id,
            preserved_count,
            annotated_count,
        )
    video.processing_step = "annotating"
    touch_step_started_at(video)
    video.processing_progress = STEP_PROGRESS["annotating"]
    await db.commit()
    await update_progress(video_id, "annotating")


async def _run_prewarm_notes(ctx: PipelineCtx) -> None:
    """Pre-generate AI learning notes for the video's exam-tagged words.

    Stored as ``video:{id}`` rows so the gloss endpoint answers in <10ms instead
    of calling the LLM on the reading path.

    An enhancement, not a dependency: with the LLM down — or no ECDICT db, hence
    no words to annotate — the step still records itself done and gloss falls
    back to live AI / global notes.
    """
    db, video, video_id = ctx.db, ctx.video, ctx.video_id
    if not ecdict.is_available():
        logger.info(
            "Video %s: skipping prewarm_notes (no ECDICT — no words to annotate)",
            video_id,
        )
        await update_progress(video_id, "prewarm_notes")
        return

    try:
        from app.services.word_notes import prewarm_video_notes

        await prewarm_video_notes(db, video.id)
        video.processing_step = "prewarm_notes"
        touch_step_started_at(video)
        video.processing_progress = STEP_PROGRESS["prewarm_notes"]
        await db.commit()
        await update_progress(video_id, "prewarm_notes")
    except Exception as exc:
        # Prewarm is an enhancement; don't fail the pipeline if the LLM is down.
        # The gloss endpoint will fall back to live AI / global notes.
        logger.warning("Video %s: prewarm_notes skipped (%s)", video_id, exc)
        await update_progress(video_id, "prewarm_notes")


async def _run_classifying(ctx: PipelineCtx) -> None:
    """Generate canonical topic tags — and a difficulty when it is still NULL.

    Feeds the browse category filter and the card chip; the post-ready
    subtitle-derived difficulty compute stays the fallback.

    Same best-effort contract as ``prewarm_notes``: a failure must not block
    publishing, and ``scripts/backfill_classification.py`` can retry later.
    """
    db, video, video_id = ctx.db, ctx.video, ctx.video_id
    try:
        from app.services.video_classification import classify_video_metadata

        await classify_video_metadata(db, video_id)
    except Exception as exc:
        logger.warning("Video %s: classifying skipped (%s)", video_id, exc)
    video.processing_step = "classifying"
    touch_step_started_at(video)
    video.processing_progress = STEP_PROGRESS["classifying"]
    await db.commit()
    await update_progress(video_id, "classifying")


async def _run_downloading(ctx: PipelineCtx) -> None:
    """Materialize the local file ``transcoding`` reads.

    An imported (YouTube) source may play via embed with no local file at all,
    so a failed download logs and continues; a local upload whose staged raw
    file is gone *is* an error — there would be nothing to transcode and
    nothing to serve.
    """
    from app.models.video import VideoSource

    db, video, video_id = ctx.db, ctx.video, ctx.video_id
    if video.video_source == VideoSource.imported:
        ctx.video_path = await _download_video(video.source_url, video.id)
        if not ctx.video_path:
            # Imported (YouTube) videos can be played via embed
            # without a local file.  Log and continue rather than
            # failing the entire pipeline.
            logger.warning(
                "Video %s: download failed — continuing without local file (embed playback)",
                video_id,
            )
            await require_playback(video)
    else:
        # Local upload: raw file already staged by the head.
        ctx.video_path = _find_local_raw(video.id)
        if not ctx.video_path:
            raise Exception(f"Raw video file not found for local upload {video_id}")
    video.processing_step = "downloading"
    touch_step_started_at(video)
    video.processing_progress = STEP_PROGRESS["downloading"]
    await db.commit()
    if ctx.video_path:
        await update_progress(video_id, "downloading")


async def _skip_downloading(ctx: PipelineCtx) -> None:
    """A resumed run still owes ``transcoding`` the path (``Step.skip_run``).

    Re-find the staged/downloaded raw file for both local and imported videos.
    A Redis completion marker alone cannot restore an in-memory path.
    """
    ctx.video_path = _find_local_raw(ctx.video_id)
    if not ctx.video_path and not await has_renditions(ctx.video):
        await _run_downloading(ctx)


async def _run_transcoding(ctx: PipelineCtx) -> None:
    """Produce the playable renditions from whatever ``downloading`` left.

    Only verified outputs complete the local-media step. A supported YouTube
    source may finish via embed, with a recorded, bounded localization retry.
    """
    db, video, video_id = ctx.db, ctx.video, ctx.video_id
    urls = await _transcode_video(ctx.video_path, video.id) if ctx.video_path else {}
    converted = await accept_local_renditions(video, urls)
    if not converted:
        reason = (
            "Local video conversion produced no usable rendition"
            if ctx.video_path
            else "Local video download unavailable"
        )
        record_localization_failure(video, reason)
        await require_playback(video)
        logger.warning("video_local_media_fallback", video_id=video_id, reason=reason)
    video.processing_step = "transcoding"
    touch_step_started_at(video)
    video.processing_progress = STEP_PROGRESS["transcoding"]
    await db.commit()
    if converted:
        await update_progress(video_id, "transcoding")


async def _skip_transcoding(ctx: PipelineCtx) -> None:
    """A completed Redis step cannot stand in for a missing media artifact."""
    if not await has_renditions(ctx.video):
        await _run_transcoding(ctx)


async def _run_done(ctx: PipelineCtx) -> None:
    """Declare the video ready, then do what only makes sense afterwards.

    Terminal step: the runner never asks whether it already ran (there is
    nothing after it to resume into) and never blames it for a failure — a
    crash in here is attributed to ``transcoding``, the last step that did work.

    The cover-localization retry is its first act rather than a step of its own,
    because it needs what download/transcode left behind (the first attempt ran
    at extraction, before any local file existed) and because it must happen
    before the video claims to be ready; it stays best-effort — a failure keeps
    the external URL for backfill.

    Everything after the flip to ``ready`` is best-effort by contract: register
    the standard version for this source, auto-publish when an official video
    asked for it, then score / difficulty / speech metrics and the OSS cleanup
    of the staged raw upload. None of them may fail a pipeline whose output is
    already playable.
    """
    from app.models.video import VideoSource, VideoStatus

    db, video, video_id = ctx.db, ctx.video, ctx.video_id
    await require_playback(video)

    # --- Cover localization retry ---
    # The first attempt ran at extraction (needs CDN egress). After
    # download/transcode the local file exists, so the ffmpeg frame
    # fallback can synthesize a cover even with the egress dead.
    # Non-blocking: failures keep the external URL for backfill.
    if (video.thumbnail_url or "").startswith("http"):
        from app.services.thumbnail_service import localize_video_thumbnail

        if await localize_video_thumbnail(video):
            await db.commit()

    video.status = VideoStatus.ready
    video.processing_step = None
    video.step_started_at = None
    video.processing_progress = 100
    await db.commit()
    await invalidate_video_playback_cache(video_id)
    await update_progress(video_id, "done")
    release_lock_and_steps(video_id)
    logger.info("Video %s finalized", video_id)

    # Phase 2: register as the standard version for this source_url
    # (first ready wins; no-op if a standard already exists).
    await _register_standard(db, video)

    # Auto-publish once ready. Only official videos with
    # auto_publish=True are published immediately; UGC videos
    # always stay in draft after processing so the creator can
    # edit subtitles/practice before submitting for admin review.
    if video.auto_publish and not video.is_published and video.is_official:
        from app.services.video_publish import _publish_video

        await _publish_video(db, video, reviewed_by="system:auto_publish")
        try:
            from app.services.video_cache import invalidate_browse_cache

            await invalidate_browse_cache()
        except Exception:
            logger.warning("auto_publish browse cache invalidation failed", video_id=video_id, exc_info=True)
        logger.info("Video %s auto-published (official)", video_id)

    # P1: schedule an initial learning_score computation. Best-effort
    # — scoring failure must never fail finalize. The beat jobs
    # re-score hourly/daily; this gives new videos an immediate
    # (metadata-baseline) score so they aren't buried at null.
    try:
        from app.tasks.scoring_tasks import compute_video_score_task

        compute_video_score_task.delay(video_id)
    except Exception:
        logger.warning("Video %s: failed to schedule scoring (continuing)", video_id, exc_info=True)

    # Sprint 3: auto-compute CEFR difficulty from subtitle word_levels.
    # Best-effort — never fails the pipeline.
    try:
        from app.services.difficulty_service import compute_video_difficulty

        await compute_video_difficulty(db, video_id)
    except Exception:
        logger.warning("Video %s: difficulty computation failed (continuing)", video_id, exc_info=True)

    # 阶段 3: subtitle-derived speech metrics (WPM / vocabulary
    # density), compute-on-null. Best-effort — never fails the pipeline.
    try:
        from app.services.subtitle_metrics_service import compute_video_speech_metrics

        await compute_video_speech_metrics(db, video_id)
    except Exception:
        logger.warning("Video %s: speech metrics computation failed (continuing)", video_id, exc_info=True)

    # Best-effort OSS cleanup of the staged raw upload.
    if video.video_source != VideoSource.imported:
        await _cleanup_oss_raw(video.id, video.source_url)


#: Step name → body, for the steps **this task** owns. The declaration (order,
#: progress, watchdog budget) stays in ``pipeline_helpers``; only the code lives
#: here, next to the helpers the bodies call and on the same side of the
#: import cycle the declaration has to stay clear of.
_TAIL_BODIES: dict[str, StepBody] = {
    "translating": _run_translating,
    "annotating": _run_annotating,
    "prewarm_notes": _run_prewarm_notes,
    "classifying": _run_classifying,
    "downloading": _run_downloading,
    "transcoding": _run_transcoding,
    TERMINAL_STEP: _run_done,
}

#: Bodies that run *instead* of the body above when a resume skips that step,
#: because the step left something behind the later steps still need.
_TAIL_SKIP_BODIES: dict[str, StepBody] = {
    "downloading": _skip_downloading,
    "transcoding": _skip_transcoding,
}


def finalize_steps() -> tuple[Step, ...]:
    """The tail's slice of the declared pipeline, with bodies attached.

    Assembled by name off ``STEPS`` so the order is never restated: adding a
    step to the declaration plus a body to ``_TAIL_BODIES`` is the whole change,
    and a body whose name is not declared simply never runs.
    """
    return tuple(
        replace(step, run=_TAIL_BODIES[step.name], skip_run=_TAIL_SKIP_BODIES.get(step.name))
        for step in STEPS
        if step.name in _TAIL_BODIES
    )


@celery_app.task(bind=True, max_retries=3, name="app.tasks.video_processing.finalize_video")
def finalize_video(self, video_id: str, engine: str | None = None):
    """Tail of the video pipeline: translate → download → transcode → ready.

    Triggered by the transcription callback endpoint once subtitles arrive from
    the GPU worker. Runs on the cloud (default ``celery`` queue).
    """
    if not acquire_lock(video_id):
        logger.warning("Video %s is already being processed, skipping finalize", video_id)
        return

    from sqlalchemy import select

    from app.core.database import async_session
    from app.models.video import Video

    async def _process():
        async with async_session() as db:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                logger.error("Video %s not found for finalize", video_id)
                release_lock_and_steps(video_id)
                return

            ctx = PipelineCtx(db=db, video=video, video_id=video_id, engine=engine)

            try:
                # The whole tail is the declared step sequence: order, resume-skip
                # and the failure attribution all come from pipeline_helpers.STEPS.
                await run_steps(ctx, finalize_steps())

            except Exception as e:
                logger.exception("Video %s finalize failed", video_id)
                await commit_error_state(video, db, e, step=ctx.current_step)
                # Always release the lock so Celery's retry can re-acquire it.
                # Keep the completed-step set so a retry (automatic or manual)
                # resumes from the last successful step rather than re-running
                # translate/annotate/prewarm needlessly.
                release_lock(video_id)
                raise self.retry(exc=e) from e

    run_pipeline_task(_process())


# ---------------------------------------------------------------------------
# Watchdog: fail videos stuck in any pipeline step (head or tail)
# ---------------------------------------------------------------------------


async def _run_watchdog_pipeline() -> None:
    """Mark videos stuck in any pipeline step as failed (worker offline/hung).

    Covers both phases:
    - ``processing`` (head: extracting / transcribing on the GPU worker)
    - ``ready_subtitles`` (tail: translating / annotating / prewarm_notes /
      downloading / transcoding on the cloud)

    The tail runs under ``status=ready_subtitles`` (not ``processing``), so the
    old transcribing-only watchdog missed any tail step that hung (dead LLM
    call, crashed ffmpeg) - the video sat in ``ready_subtitles`` forever. This
    watchdog queries both statuses.

    Per-step timeout keyed by ``processing_step``: a video is stuck when
    ``step_started_at`` is older than its step's timeout. Skips videos whose
    Redis lock is still held - the worker is alive but in Celery retry backoff,
    not stuck. Legacy rows with NULL ``step_started_at`` (predate the column)
    fall back to ``processing_started_at``/``created_at`` with the transcribe
    timeout.

    Module-level (not a nested closure) so it can be unit-tested directly with
    a patched ``async_session``, bypassing the Celery ``run_async`` thread loop.
    """
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import and_, or_, select

    from app.core.database import async_session
    from app.models.admin_setting import SETTINGS_ROW_ID, AdminSetting
    from app.models.video import Video, VideoStatus
    from app.tasks.pipeline_helpers import get_step_timeouts, is_lock_held

    # Admin kill switch (settings row; absent row -> enabled):
    # a disabled watchdog lets a stuck video sit while ops investigate
    # instead of auto-failing it.
    async with async_session() as gate_db:
        gate_row = (
            await gate_db.execute(select(AdminSetting).where(AdminSetting.id == SETTINGS_ROW_ID))
        ).scalar_one_or_none()
    if gate_row is not None and not gate_row.watchdog_enabled:
        logger.info("Watchdog disabled via admin settings; skipping stale-pipeline scan")
        return

    settings = get_settings()
    now = datetime.now(UTC)

    # Per-step timeout lookup (seconds) — see pipeline_helpers.get_step_timeouts,
    # which is also the "every step has a budget" invariant's test seam.
    step_timeouts = get_step_timeouts()
    default_timeout = settings.pipeline_step_timeout_default
    transcribe_timeout = settings.video_transcribe_timeout

    async with async_session() as db:
        # Phase 1: rows with step_started_at - per-step timeout.
        result = await db.execute(
            select(Video).where(
                Video.status.in_([VideoStatus.processing, VideoStatus.ready_subtitles]),
                Video.processing_step.is_not(None),
                Video.step_started_at.is_not(None),
            )
        )
        stuck: list = []
        for v in result.scalars().all():
            timeout = step_timeouts.get(v.processing_step, default_timeout)
            # SQLite returns naive datetimes; Postgres returns tz-aware. Normalize
            # to aware UTC so the comparison works across both (tests run SQLite,
            # prod runs Postgres).
            step_ts = v.step_started_at
            if step_ts.tzinfo is None:
                step_ts = step_ts.replace(tzinfo=UTC)
            if step_ts >= now - timedelta(seconds=timeout):
                continue  # within its step's budget
            if is_lock_held(v.id):
                continue  # worker alive, in retry backoff - not stuck
            stuck.append(v)

        # Phase 2: legacy rows with NULL step_started_at (predate the
        # column). Only transcribing had a watchdog before; preserve that
        # using processing_started_at / created_at fallback.
        legacy_cutoff = now - timedelta(seconds=transcribe_timeout)
        stuck_ids = {v.id for v in stuck}
        legacy_result = await db.execute(
            select(Video).where(
                Video.status == VideoStatus.processing,
                Video.processing_step == "transcribing",
                Video.step_started_at.is_(None),
                or_(
                    Video.processing_started_at < legacy_cutoff,
                    and_(
                        Video.processing_started_at.is_(None),
                        Video.created_at < legacy_cutoff,
                    ),
                ),
            )
        )
        for v in legacy_result.scalars().all():
            if v.id not in stuck_ids and not is_lock_held(v.id):
                stuck.append(v)
                stuck_ids.add(v.id)

        # A05/BE-01: a video whose pipeline hand-off never reached the broker is
        # waiting on the dispatcher, not stuck on a dead worker. Failing it here
        # would throw away a run that is about to start; the dispatch backlog
        # alert owns the "broker is down for good" case.
        if stuck:
            from app.services.pipeline_dispatch import pending_video_ids

            undelivered = await pending_video_ids(db, [v.id for v in stuck])
            if undelivered:
                logger.info(
                    "Watchdog: leaving videos with undelivered pipeline dispatches alone",
                    video_ids=sorted(undelivered),
                )
                stuck = [v for v in stuck if v.id not in undelivered]

        steps_by_video: dict[str, str | None] = {}
        for v in stuck:
            step = v.processing_step
            steps_by_video[v.id] = step
            v.status = VideoStatus.error
            v.error_message = f"Pipeline step '{step}' timed out (worker stuck or offline?)"
            v.processing_step = None
            v.step_started_at = None
            release_lock_and_steps(v.id)
            logger.warning(
                "Watchdog: marked stuck pipeline step as failed",
                video_id=v.id,
                step=step,
            )
        if stuck:
            # In-app fallback + out-of-band webhook: a timed-out pipeline used
            # to leave only a log line, so nobody noticed until an admin
            # happened to open the video list.
            from app.services.notification_service import notify_admins

            summary = ", ".join(f"{v.id}@{v.error_message}" for v in stuck[:10])
            await notify_admins(
                db,
                title="管线步骤超时",
                message=f"Watchdog 标记 {len(stuck)} 个视频失败：{summary}",
                related_url=None,
            )
            await db.commit()
            from app.services.pipeline_alerting import record_pipeline_failure

            for v in stuck:
                await record_pipeline_failure(v.id, step=steps_by_video.get(v.id), reason="watchdog step timeout")
            try:
                from app.services.alert_service import send_alert

                await send_alert(
                    "管线步骤超时",
                    f"Watchdog marked {len(stuck)} video(s) failed. {summary}",
                    severity="critical",
                )
            except Exception:
                logger.warning("watchdog alert delivery failed", exc_info=True)


@celery_app.task(name="app.tasks.video_processing.watchdog_stale_pipeline")
def watchdog_stale_pipeline():
    """Celery wrapper for ``_run_watchdog_pipeline`` (beat-scheduled every 10 min)."""
    run_pipeline_task(_run_watchdog_pipeline())


# ---------------------------------------------------------------------------
# Admin "搬运到本地" (download + transcode only; no transcription)
# ---------------------------------------------------------------------------


async def _run_localize(self, video_id: str, force: bool = False) -> None:
    """Download + transcode a video's source to local storage (admin).

    Module-level (not a nested closure) so it can be unit-tested directly with
    a patched ``async_session``, bypassing the Celery ``run_async`` thread loop.

    Args:
        force: bypass the download_fail_count strike limit. Admin manual
            trigger passes True; the beat retry task passes False (default).
    """
    if not acquire_lock(video_id):
        logger.warning("Video %s is already being processed, skipping localize", video_id)
        return

    from sqlalchemy import select

    from app.core.database import async_session
    from app.models.video import Video, VideoStatus

    async with async_session() as db:
        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()
        if not video:
            logger.error("Video %s not found for localize", video_id)
            release_lock_and_steps(video_id)
            return
        if (
            video.storage_mode == "offline"
            or video.video_source != "imported"
            or video.status not in (VideoStatus.ready, VideoStatus.processing, VideoStatus.error)
        ):
            release_lock_and_steps(video_id)
            return

        # Strike limit: skip if this video has failed download too many
        # times (permanent failure - region block / video removed). force
        # =True (admin manual trigger) bypasses so an admin can retry
        # regardless. The beat task passes force=False.
        if not force:
            settings = get_settings()
            if (video.download_fail_count or 0) >= settings.download_retry_max_attempts:
                logger.info(
                    "Video %s: skipping localize (download_fail_count %d >= max %d)",
                    video_id,
                    video.download_fail_count,
                    settings.download_retry_max_attempts,
                )
                release_lock_and_steps(video_id)
                return

        try:
            # Reuse a real raw file on retry, regardless of a stale Redis marker.
            current_step = "downloading"
            video_path = _find_local_raw(video.id)
            if not video_path:
                video_path = await _download_video(video.source_url, video.id)
            if not video_path:
                raise PlaybackUnavailableError("Local video download unavailable")
            await update_progress(video_id, "downloading")

            current_step = "transcoding"
            urls = await _transcode_video(video_path, video.id)
            if not await accept_local_renditions(video, urls):
                raise PlaybackUnavailableError("Local video conversion produced no usable rendition")
            await require_playback(video)
            await update_progress(video_id, "transcoding")
            video.status = VideoStatus.ready
            video.processing_step = None
            video.step_started_at = None
            video.processing_progress = 100
            await db.commit()
            await invalidate_video_playback_cache(video_id)
            await update_progress(video_id, "done")
            release_lock_and_steps(video_id)
            logger.info("Video %s localized to local storage", video_id)

        except PlaybackUnavailableError as e:
            record_localization_failure(video, str(e))
            if await has_playback(video):
                # A conversion failure must not remove a valid previous file
                # or supported embed. Keep the failure visible to admins/beat.
                video.status = VideoStatus.ready
                video.processing_step = None
                video.step_started_at = None
                video.processing_progress = 100
                await db.commit()
                await invalidate_video_playback_cache(video_id)
                release_lock_and_steps(video_id)
                logger.warning("video_localization_failed_playback_preserved", video_id=video_id, step=current_step)
                return
            await commit_error_state(video, db, e, step=current_step)
            release_lock(video_id)
            raise self.retry(exc=e) from e

        except Exception as e:
            logger.exception("Video %s localize failed", video_id)
            await commit_error_state(video, db, e, step=current_step)
            # Always release the lock so Celery's retry can re-acquire it.
            # Keep the completed-step set so a retry resumes from the last
            # successful step rather than re-downloading/re-transcoding.
            release_lock(video_id)
            raise self.retry(exc=e) from e


@celery_app.task(bind=True, max_retries=2)
def localize_video(self, video_id: str, force: bool = False):
    """Download + transcode a video's source to local storage (admin).

    Thin Celery wrapper for ``_run_localize``. See that function for behavior.
    """
    run_pipeline_task(_run_localize(self, video_id, force))


# ---------------------------------------------------------------------------
# Beat task: re-attempt failed YouTube downloads (daily)
# ---------------------------------------------------------------------------


async def _run_retry_failed_downloads() -> None:
    """Select ready imported videos whose download failed (under the strike
    limit), refresh YouTube cookies, and dispatch ``localize_video``.

    Cookie expiry is the leading cause of download failure, so cookies are
    refreshed before each retry - retrying without refresh would reproduce the
    failure. ``localize_video`` is dispatched with default ``force=False`` so
    the strike limit inside localize still applies.
    """
    from sqlalchemy import select

    from app.core.database import async_session
    from app.models.video import Video, VideoSource, VideoStatus
    from app.services.youtube_cookies_service import ensure_cookies_for_pipeline

    settings = get_settings()

    # Admin kill switch (settings row; absent row -> enabled):
    # download_auto_retry_enabled=False stops the daily retry loop without
    # touching the per-video strike counters.
    async with async_session() as gate_db:
        from app.models.admin_setting import SETTINGS_ROW_ID, AdminSetting

        gate_row = (
            await gate_db.execute(select(AdminSetting).where(AdminSetting.id == SETTINGS_ROW_ID))
        ).scalar_one_or_none()
    if gate_row is not None and not gate_row.download_auto_retry_enabled:
        logger.info("Download auto-retry disabled via admin settings; skipping retry scan")
        return

    async with async_session() as db:
        result = await db.execute(
            select(Video).where(
                Video.video_source == VideoSource.imported,
                Video.status == VideoStatus.ready,
                Video.video_url_720p.is_(None),
                Video.download_failed_at.is_not(None),
                Video.download_fail_count < settings.download_retry_max_attempts,
            )
        )
        candidates = list(result.scalars().all())

    for v in candidates:
        try:
            await ensure_cookies_for_pipeline(v.source_url)
        except Exception:
            logger.warning(
                "Cookie refresh failed for video %s; retrying download anyway",
                v.id,
                exc_info=True,
            )
        # force=False (default) - respects the strike limit inside localize.
        localize_video.delay(v.id)
        logger.info("Video %s: scheduled download retry", v.id)


@celery_app.task(name="app.tasks.video_processing.retry_failed_downloads")
def retry_failed_downloads():
    """Daily beat task: re-attempt failed YouTube downloads (阶段 3)."""
    run_pipeline_task(_run_retry_failed_downloads())
