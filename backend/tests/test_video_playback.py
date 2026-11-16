"""Playback artifacts, supported fallback and durable localization outcomes."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from app.core.errors import BadRequestError
from app.core.redis import get_redis
from app.models.pipeline_dispatch import PipelineDispatch
from app.models.video import Video, VideoSource, VideoStatus
from app.services import pipeline_dispatch, video_media, video_playback
from app.services.video_publish import _publish_video
from app.tasks import video_processing as vp
from app.tasks.pipeline_helpers import PipelineCtx
from tests.conftest import TestSessionLocal

YOUTUBE = "https://www.youtube.com/watch?v=abcdefghijk"


@pytest.fixture
def media_root(tmp_path, monkeypatch):
    monkeypatch.setattr(video_media.get_settings(), "local_media_path", str(tmp_path))
    monkeypatch.setattr(video_media, "get_video_height", AsyncMock(return_value=720))
    return tmp_path


async def seed(db, *, source="imported", url=YOUTUBE, status=VideoStatus.ready_subtitles, **kwargs):
    row = Video(title="Playback", source_url=url, video_source=source, status=status, is_official=True, **kwargs)
    db.add(row)
    await db.commit()
    return row


def artifact(root, name):
    (root / name).write_bytes(b"fixture with a mocked video stream probe")
    return f"/media/{name}"


@pytest.mark.parametrize(
    "url,source,offline,expected",
    [
        (YOUTUBE, "imported", False, True),
        ("https://youtu.be/abcdefghijk", "imported", False, True),
        ("https://www.youtube.com/shorts/abcdefghijk", "imported", False, True),
        ("https://www.bilibili.com/video/BV1234567890", "imported", False, False),
        ("https://youtube.com.evil.test/watch?v=abcdefghijk", "imported", False, False),
        ("https://youtube.com/watch?v=short", "imported", False, False),
        (YOUTUBE, "local", False, False),
        (YOUTUBE, "imported", True, False),
    ],
)
def test_fallback_matches_only_supported_player_sources(url, source, offline, expected):
    video = Video(source_url=url, video_source=source, storage_mode="offline" if offline else "local")
    assert video_playback.can_embed(video) is expected


async def test_upload_without_valid_output_cannot_complete_or_invent_url(db_session, media_root, monkeypatch):
    video = await seed(db_session, source="local", url="upload.webm")
    ctx = PipelineCtx(db_session, video, video.id, video_path="upload.webm")
    monkeypatch.setattr(vp, "_transcode_video", AsyncMock(return_value={}))
    progress = AsyncMock()
    monkeypatch.setattr(vp, "update_progress", progress)
    with pytest.raises(video_playback.PlaybackUnavailableError):
        await vp._run_transcoding(ctx)
    assert video.video_url_720p is None and not video.is_published
    progress.assert_not_called()
    with pytest.raises(video_playback.PlaybackUnavailableError):
        await vp._run_done(ctx)
    assert video.status == VideoStatus.ready_subtitles


async def test_youtube_fallback_is_playable_and_records_localization_retry(db_session, media_root, monkeypatch):
    video = await seed(db_session, auto_publish=True)
    ctx = PipelineCtx(db_session, video, video.id)
    monkeypatch.setattr(vp, "_download_video", AsyncMock(return_value=None))
    progress = AsyncMock()
    monkeypatch.setattr(vp, "update_progress", progress)
    await vp._run_downloading(ctx)
    await vp._run_transcoding(ctx)
    await vp._run_done(ctx)
    assert video.status == VideoStatus.ready and video.is_published
    assert video.video_url_720p is None
    assert video.download_fail_count == 1 and video.download_failed_at is not None
    assert "transcoding" not in [call.args[1] for call in progress.await_args_list]


async def test_unsupported_import_without_file_never_reaches_ready(db_session, media_root, monkeypatch):
    video = await seed(db_session, url="https://www.bilibili.com/video/BV1234567890", auto_publish=True)
    monkeypatch.setattr(vp, "_download_video", AsyncMock(return_value=None))
    with pytest.raises(video_playback.PlaybackUnavailableError):
        await vp._run_downloading(PipelineCtx(db_session, video, video.id))
    assert video.status != VideoStatus.ready and not video.is_published


@pytest.mark.parametrize("source", [VideoSource.local, VideoSource.imported])
async def test_resume_restores_the_real_raw_path_for_both_sources(db_session, media_root, monkeypatch, source):
    video = await seed(db_session, source=source)
    raw = media_root / f"{video.id}_raw.webm"
    raw.write_bytes(b"raw")
    download = AsyncMock()
    monkeypatch.setattr(vp, "_download_video", download)
    ctx = PipelineCtx(db_session, video, video.id)
    await vp._skip_downloading(ctx)
    # Windows may report the temp directory with different casing
    # (pytest-of-fuwei vs pytest-of-Fuwei); compare resolved paths.
    assert Path(ctx.video_path).resolve() == raw.resolve()
    download.assert_not_called()


async def test_stale_transcode_marker_requires_real_output(db_session, media_root, monkeypatch):
    video = await seed(db_session, source="local", url="raw.mp4", video_url_720p="/media/missing.mp4")
    produced = artifact(media_root, "new.mp4")
    renderer = AsyncMock(return_value={"720p": produced})
    monkeypatch.setattr(vp, "_transcode_video", renderer)
    ctx = PipelineCtx(db_session, video, video.id, video_path="raw.mp4")
    await vp._skip_transcoding(ctx)
    renderer.assert_awaited_once()
    assert video.video_url_720p == produced


async def test_localization_failure_preserves_old_playable_file_and_records_attempt(
    db_session, media_root, monkeypatch
):
    old = artifact(media_root, "old.mp4")
    video = await seed(db_session, status=VideoStatus.processing, video_url_720p=old)
    vid = video.id
    monkeypatch.setattr(vp, "acquire_lock", lambda _: True)
    monkeypatch.setattr(vp, "_find_local_raw", lambda _: "existing_raw.mp4")
    monkeypatch.setattr(vp, "_transcode_video", AsyncMock(return_value={}))
    task = MagicMock()
    await vp._run_localize(task, vid, force=True)
    task.retry.assert_not_called()
    await db_session.refresh(video)
    assert video.status == VideoStatus.ready and video.video_url_720p == old
    assert video.download_fail_count == 1 and video.error_message
    assert (media_root / "old.mp4").read_bytes().startswith(b"fixture")


async def test_successful_localization_resets_failures_and_reuses_raw_file(db_session, media_root, monkeypatch):
    video = await seed(db_session, status=VideoStatus.processing, download_fail_count=3, error_message="prior failure")
    produced = artifact(media_root, "replacement.mp4")
    monkeypatch.setattr(vp, "acquire_lock", lambda _: True)
    monkeypatch.setattr(vp, "_find_local_raw", lambda _: "cached_raw.mp4")
    download = AsyncMock()
    monkeypatch.setattr(vp, "_download_video", download)
    monkeypatch.setattr(vp, "_transcode_video", AsyncMock(return_value={"720p": produced}))
    redis = get_redis()
    await redis.set(f"video:detail:{video.id}", "old playback")
    await redis.set("video:detail:unrelated", "other video")
    await redis.set("browse:feed:cached", "old card")
    await vp._run_localize(MagicMock(), video.id, force=True)
    await db_session.refresh(video)
    assert video.video_url_720p == produced and video.status == VideoStatus.ready
    assert video.download_fail_count == 0 and video.download_failed_at is None and video.error_message is None
    download.assert_not_called()
    assert await redis.get(f"video:detail:{video.id}") is None
    assert await redis.get("browse:feed:cached") is None
    assert await redis.get("video:detail:unrelated") == "other video"


async def test_publish_rejects_missing_media_and_offline_material(db_session, media_root):
    video = await seed(db_session, source="local", url="upload.mp4", status=VideoStatus.ready)
    with pytest.raises(BadRequestError):
        await _publish_video(db_session, video)
    assert not video.is_published
    video.video_url_720p = artifact(media_root, "publish.mp4")
    await _publish_video(db_session, video)
    assert video.is_published
    video.storage_mode = "offline"
    with pytest.raises(BadRequestError):
        await _publish_video(db_session, video)


async def test_broker_failure_keeps_localization_intent_and_previous_media(
    client, admin_headers, media_root, monkeypatch
):
    async with TestSessionLocal() as db:
        video = await seed(db, status=VideoStatus.ready, video_url_720p=artifact(media_root, "previous.mp4"))
        vid = video.id
    with monkeypatch.context() as patch:
        patch.setattr(pipeline_dispatch, "_send", AsyncMock(side_effect=ConnectionError("broker unavailable")))
        response = await client.post(f"/api/v1/videos/admin/{vid}/localize", headers=admin_headers)
    assert response.status_code == 200, response.text
    async with TestSessionLocal() as db:
        row = await db.get(Video, vid)
        intent = await db.scalar(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))
        assert row.status == VideoStatus.processing and row.video_url_720p == "/media/previous.mp4"
        assert row.processing_generation is not None and row.step_started_at is not None
        expected_args = [vid, True, row.processing_generation]
        assert intent.processing_generation == row.processing_generation
        assert intent.status == "pending" and intent.args == expected_args
        intent.next_attempt_at = None
        await db.commit()
        sender = AsyncMock()
        monkeypatch.setattr(pipeline_dispatch, "_send", sender)
        assert (await pipeline_dispatch.dispatch_pending(db)).sent == 1
        sender.assert_awaited_once_with(pipeline_dispatch.LOCALIZE_VIDEO_TASK, expected_args, None)


async def test_enqueue_failure_rolls_back_localization_claim(client, admin_headers, monkeypatch):
    async with TestSessionLocal() as db:
        video = await seed(db, status=VideoStatus.ready, video_url_720p="/media/original.mp4")
        vid = video.id
    monkeypatch.setattr(pipeline_dispatch, "enqueue", AsyncMock(side_effect=RuntimeError("intent storage unavailable")))
    with pytest.raises(RuntimeError, match="intent storage unavailable"):
        await client.post(f"/api/v1/videos/admin/{vid}/localize", headers=admin_headers)
    async with TestSessionLocal() as db:
        row = await db.get(Video, vid)
        assert row.status == VideoStatus.ready and row.video_url_720p == "/media/original.mp4"
        assert row.processing_generation is None and row.step_started_at is None
        assert await db.scalar(select(PipelineDispatch).where(PipelineDispatch.video_id == vid)) is None


@pytest.mark.parametrize(
    "status,source,storage,expected",
    [
        (VideoStatus.ready_subtitles, "imported", "local", 409),
        (VideoStatus.ready, "local", "local", 400),
        (VideoStatus.ready, "imported", "offline", 400),
    ],
)
async def test_localization_cannot_interrupt_full_pipeline_or_revive_offline_video(
    client, admin_headers, status, source, storage, expected
):
    async with TestSessionLocal() as db:
        video = await seed(db, status=status, source=source, storage_mode=storage)
        vid = video.id
    response = await client.post(f"/api/v1/videos/admin/{vid}/localize", headers=admin_headers)
    assert response.status_code == expected


@pytest.mark.parametrize("force", [True, False])
async def test_localization_claim_and_intent_share_fresh_generation(db_session, monkeypatch, force):
    from datetime import UTC, datetime, timedelta
    from uuid import UUID, uuid4

    from app.services.video_service import localize_video_admin

    old_generation = str(uuid4())
    old_started_at = datetime.now(UTC) - timedelta(days=1)
    video = await seed(
        db_session,
        status=VideoStatus.ready,
        processing_generation=old_generation,
        step_started_at=old_started_at,
        video_url_720p="/media/keep.mp4",
    )
    original_enqueue = pipeline_dispatch.enqueue
    seen = []

    async def enqueue(db, **kwargs):
        generation, started_at = (
            await db.execute(select(Video.processing_generation, Video.step_started_at).where(Video.id == video.id))
        ).one()
        assert generation != old_generation and UUID(generation).version == 4
        assert started_at.replace(tzinfo=UTC) > old_started_at
        seen.append(generation)
        return await original_enqueue(db, **kwargs)

    sender = AsyncMock()
    monkeypatch.setattr(pipeline_dispatch, "enqueue", enqueue)
    monkeypatch.setattr(pipeline_dispatch, "_send", sender)
    result = await localize_video_admin(db_session, video.id, force=force)
    intent = await db_session.scalar(select(PipelineDispatch).where(PipelineDispatch.video_id == video.id))
    assert result.status == VideoStatus.processing
    assert video.processing_generation == intent.processing_generation == seen[0]
    assert video.video_url_720p == "/media/keep.mp4"
    assert intent.args == [video.id, force, seen[0]]
    sender.assert_awaited_once_with(pipeline_dispatch.LOCALIZE_VIDEO_TASK, [video.id, force, seen[0]], None)
