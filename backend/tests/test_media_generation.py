"""Attempt-specific media paths, authorization and admin generation fences.

All database writes use the default in-memory SQLite/fake Redis fixtures. These
checks inspect the row-lock statement, not PostgreSQL lock scheduling itself.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.api.v1 import media
from app.core.config import get_settings
from app.core.security import create_token
from app.models.pipeline_dispatch import PipelineDispatch
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.services import pipeline_dispatch, thumbnail_service, video_media, video_service
from app.services.processing_generation import StaleProcessingGenerationError, artifact_identity, fence_session
from tests.conftest import TestSessionLocal

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


@pytest.fixture
def media_root(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "local_media_path", str(tmp_path))
    media._VIDEO_ACCESS_CACHE.clear()
    yield tmp_path
    media._VIDEO_ACCESS_CACHE.clear()


@pytest.mark.parametrize("generation", [None, str(uuid4())])
async def test_upload_never_moves_another_attempts_raw(media_root, monkeypatch, generation):
    vid = str(uuid4())
    other_artifact = artifact_identity(vid, str(uuid4()))
    source = media_root / f"{other_artifact}_raw.webm"
    source.write_bytes(b"other attempt input")
    video = SimpleNamespace(id=vid, processing_generation=generation, source_url=str(source))
    upload = AsyncMock(return_value=None)
    monkeypatch.setattr("app.services.oss_service.upload_file", upload)

    gpu_source, key = await video_media.stage_local_upload(video)

    artifact = artifact_identity(vid, generation)
    expected = media_root / f"{artifact}_raw.webm"
    assert Path(gpu_source).resolve() == expected.resolve()
    assert Path(video.source_url).resolve() == expected.resolve()
    assert key == ""
    assert source.read_bytes() == expected.read_bytes() == b"other attempt input"
    upload.assert_awaited_once_with(str(expected.resolve()), f"{get_settings().oss_raw_prefix}/{artifact}.webm")
    assert video_media.find_local_raw(artifact) == str(expected.resolve())
    assert not list(media_root.glob("*.part"))


async def test_upload_private_oss_source_uses_attempt_key(media_root, monkeypatch):
    vid, generation = str(uuid4()), str(uuid4())
    source = media_root / "original.mp4"
    source.write_bytes(b"upload")
    video = SimpleNamespace(id=vid, processing_generation=generation, source_url=str(source))
    monkeypatch.setattr(get_settings(), "oss_raw_bucket_public", False)
    monkeypatch.setattr("app.services.oss_service.upload_file", AsyncMock(return_value="https://cdn.example/raw"))
    signed = []

    def sign(key, **kwargs):
        signed.append(key)
        return "https://signed.example/raw"

    monkeypatch.setattr("app.services.oss_service.get_signed_url", sign)
    gpu_source, key = await video_media.stage_local_upload(video)
    expected = f"{get_settings().oss_raw_prefix}/{artifact_identity(vid, generation)}.mp4"
    assert key == expected and signed == [expected]
    assert gpu_source == "https://signed.example/raw"
    assert source.read_bytes() == b"upload"


async def test_failed_raw_copy_keeps_existing_files_and_cleans_partial(media_root, monkeypatch):
    vid, generation = str(uuid4()), str(uuid4())
    source = media_root / "original.mp4"
    source.write_bytes(b"source")
    target = media_root / f"{artifact_identity(vid, generation)}_raw.mp4"
    target.write_bytes(b"previous usable raw")
    video = SimpleNamespace(id=vid, processing_generation=generation, source_url=str(source))

    def fail_copy(src, dest):
        assert Path(dest).suffix not in media._SERVE_EXT_ALLOWLIST
        Path(dest).write_bytes(b"partial")
        raise OSError("disk full")

    monkeypatch.setattr(video_media.shutil, "copy2", fail_copy)
    upload = AsyncMock()
    monkeypatch.setattr("app.services.oss_service.upload_file", upload)
    with pytest.raises(OSError, match="disk full"):
        await video_media.stage_local_upload(video)
    assert source.read_bytes() == b"source"
    assert target.read_bytes() == b"previous usable raw"
    assert video.source_url == str(source)
    assert not list(media_root.glob("*.part"))
    upload.assert_not_awaited()


@pytest.mark.parametrize("use_frame", [False, True])
async def test_thumbnail_probe_output_and_frame_source_are_attempt_scoped(media_root, monkeypatch, use_frame):
    vid = str(uuid4())
    artifact = artifact_identity(vid, str(uuid4()))
    previous = media_root / f"{vid}_thumb.jpg"
    previous.write_bytes(b"legacy cover")
    (media_root / f"{vid}_720p.mp4").write_bytes(b"legacy video")
    own_video = media_root / f"{artifact}_raw.webm"
    own_video.write_bytes(b"attempt video")
    probes, frames = [], []

    async def download(url, dest, proxy=None):
        probes.append(dest)
        if use_frame:
            return False
        dest.write_bytes(PNG)
        return True

    async def frame(source, dest):
        frames.append(source)
        dest.write_bytes(PNG)
        return True

    monkeypatch.setattr(thumbnail_service, "download_thumbnail", download)
    monkeypatch.setattr(thumbnail_service, "extract_frame_thumbnail", frame)
    video = SimpleNamespace(id=vid, thumbnail_url="https://i.ytimg.com/vi/test/cover.jpg")
    assert await thumbnail_service.localize_video_thumbnail(video, artifact_id=artifact)
    assert probes == [media_root.resolve() / f"{artifact}_thumb.probe"]
    assert frames == ([own_video.resolve()] if use_frame else [])
    assert video.thumbnail_url == f"/media/{artifact}_thumb.png"
    assert previous.read_bytes() == b"legacy cover"
    assert (media_root / f"{artifact}_thumb.png").read_bytes() == PNG
    assert not (media_root / f"{artifact}_thumb.probe").exists()


async def test_thumbnail_does_not_fall_back_to_another_generation_video(media_root, monkeypatch):
    vid = str(uuid4())
    artifact = artifact_identity(vid, str(uuid4()))
    (media_root / f"{vid}_720p.mp4").write_bytes(b"not this attempt")
    monkeypatch.setattr(thumbnail_service, "download_thumbnail", AsyncMock(return_value=False))
    frame = AsyncMock()
    monkeypatch.setattr(thumbnail_service, "extract_frame_thumbnail", frame)
    url = "https://i.ytimg.com/vi/test/cover.jpg"
    video = SimpleNamespace(id=vid, thumbnail_url=url)
    assert not await thumbnail_service.localize_video_thumbnail(video, artifact_id=artifact)
    assert video.thumbnail_url == url
    frame.assert_not_awaited()


async def test_thumbnail_reuses_only_own_generation_cover(media_root, monkeypatch):
    vid = str(uuid4())
    artifact = artifact_identity(vid, str(uuid4()))
    own = media_root / f"{artifact}_thumb.png"
    own.write_bytes(PNG)
    download = AsyncMock()
    monkeypatch.setattr(thumbnail_service, "download_thumbnail", download)
    video = SimpleNamespace(id=vid, thumbnail_url="https://i.ytimg.com/vi/test/cover.jpg")
    assert await thumbnail_service.localize_video_thumbnail(video, artifact_id=artifact)
    assert video.thumbnail_url == f"/media/{artifact}_thumb.png"
    download.assert_not_awaited()


@pytest.mark.parametrize("suffix", ["", "_raw", "_480p", "_720p", "_1080p"])
@pytest.mark.parametrize("method", ["GET", "HEAD"])
async def test_generation_files_keep_owner_publish_and_login_gates(client, db_session, media_root, suffix, method):
    owner = User(phone="13600009701", name="Owner", hashed_password="x")
    other = User(phone="13600009702", name="Other", hashed_password="x")
    db_session.add_all([owner, other])
    await db_session.flush()
    video = Video(
        title="Private attempt",
        source_url="upload.mp4",
        video_source="local",
        status=VideoStatus.ready,
        is_official=False,
        review_status="draft",
        user_id=owner.id,
    )
    db_session.add(video)
    await db_session.commit()
    artifact = artifact_identity(video.id, str(uuid4()))
    name = f"{artifact}{suffix}.mp4"
    (media_root / name).write_bytes(b"private media")
    url = f"/media/{name}"

    assert (await client.request(method, url)).status_code == 404
    response = await client.request(method, url, params={"token": create_token(owner.id)})
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert (await client.request(method, url, params={"token": create_token(other.id)})).status_code == 404
    assert (await client.request(method, url)).status_code == 404

    video.is_official = True
    await db_session.commit()
    media._VIDEO_ACCESS_CACHE.clear()
    assert (await client.request(method, url)).status_code == 403
    assert (await client.request(method, url, params={"token": create_token(other.id)})).status_code == 200

    video.storage_mode = "offline"
    await db_session.commit()
    media._VIDEO_ACCESS_CACHE.clear()
    assert (await client.request(method, url, params={"token": create_token(owner.id)})).status_code == 404


async def test_generation_file_for_unknown_video_is_not_public(client, media_root):
    name = f"{artifact_identity(str(uuid4()), str(uuid4()))}_raw.webm"
    (media_root / name).write_bytes(b"orphan attempt")
    assert (await client.get(f"/media/{name}")).status_code == 404


@pytest.mark.parametrize("trailer", ["_g0", "_g" + "f" * 31, "_g" + "f" * 33, "_g" + "z" * 32, "_thumb"])
def test_video_gate_pattern_does_not_overmatch_noncanonical_artifacts(trailer):
    vid = str(uuid4())
    assert media._VIDEO_FILE_RE.fullmatch(vid + trailer) is None
    assert media._VIDEO_FILE_RE.fullmatch(artifact_identity(vid, str(uuid4())) + "_720p").group("vid") == vid


def test_deletion_cleans_exact_video_all_generations_but_not_covers_or_neighbors(media_root):
    vid = str(uuid4())
    artifacts = [vid, artifact_identity(vid, str(uuid4())), artifact_identity(vid, str(uuid4()))]
    removed = [
        media_root / f"{artifact}{suffix}"
        for artifact in artifacts
        for suffix in (
            ".mp4",
            "_raw.mp4",
            "_raw.webm",
            "_480p.mp4",
            "_720p.mp4",
            "_1080p.mp4",
            f"_720p.{uuid4().hex}.part.mp4",
        )
    ]
    kept = [media_root / f"{artifact}_thumb.jpg" for artifact in artifacts] + [
        media_root / f"{vid}x_720p.mp4",
        media_root / f"{vid}_g{'f' * 31}_raw.mp4",
        media_root / f"{vid}_g{'f' * 33}_720p.mp4",
        media_root / f"{vid}_g{'z' * 32}_720p.mp4",
        media_root / f"{uuid4()}_720p.mp4",
        media_root / f"{vid}_720p.mp4.backup",
    ]
    for path in removed + kept:
        path.write_bytes(b"test-owned fixture")
    nested = media_root / "nested"
    nested.mkdir()
    (nested / f"{vid}_raw.mp4").write_bytes(b"nested source")
    video_service._delete_media_files(vid)
    assert not any(path.exists() for path in removed)
    assert all(path.exists() for path in kept)
    assert (nested / f"{vid}_raw.mp4").exists()
    # Non-UUID and glob-like ids cannot widen the deletion boundary.
    video_service._delete_media_files("*")
    assert all(path.exists() for path in kept)


async def test_localize_claim_rotates_generation_and_timestamp_in_intent_transaction(db_session, monkeypatch):
    old_generation = str(uuid4())
    video = Video(
        title="Localize",
        source_url="https://youtube.com/watch?v=abcdefghijk",
        video_source="imported",
        status=VideoStatus.ready,
        processing_generation=old_generation,
        step_started_at=datetime.now(UTC) - timedelta(days=1),
        video_url_720p="/media/previous.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    sender = AsyncMock()
    monkeypatch.setattr(pipeline_dispatch, "_send", sender)
    started = datetime.now(UTC)
    await video_service.localize_video_admin(db_session, video.id)
    async with TestSessionLocal() as db:
        row = await db.get(Video, video.id)
        intent = await db.scalar(select(PipelineDispatch).where(PipelineDispatch.video_id == video.id))
        assert UUID(row.processing_generation).version == 4 and row.processing_generation != old_generation
        assert row.step_started_at.replace(tzinfo=UTC) >= started
        assert row.status == VideoStatus.processing and row.video_url_720p == "/media/previous.mp4"
        assert intent.processing_generation == row.processing_generation
        assert intent.args == [video.id, True, row.processing_generation]
        sender.assert_awaited_once_with(pipeline_dispatch.LOCALIZE_VIDEO_TASK, intent.args, None)


async def test_takedown_refreshes_under_row_lock_and_fences_old_worker(db_session, media_root, monkeypatch):
    generation = str(uuid4())
    video = Video(
        title="Takedown",
        source_url="upload.mp4",
        video_source="local",
        status=VideoStatus.processing,
        processing_generation=generation,
        is_published=True,
        auto_publish=True,
        video_url_480p="/media/a.mp4",
        video_url_720p="/media/b.mp4",
        video_url_1080p="/media/c.mp4",
    )
    db_session.add(video)
    await db_session.commit()
    vid = video.id
    scalar = db_session.scalar
    locked = []

    async def capture(statement, *args, **kwargs):
        locked.append(
            statement._for_update_arg is not None and statement.get_execution_options().get("populate_existing")
        )
        return await scalar(statement, *args, **kwargs)

    monkeypatch.setattr(db_session, "scalar", capture)
    async with TestSessionLocal() as worker:
        stale = await worker.get(Video, vid)
        await video_service.takedown_video(db_session, vid)
        assert locked == [True]
        assert video.processing_generation != generation
        assert UUID(video.processing_generation).version == 4
        assert video.storage_mode == "offline" and not video.is_published and not video.auto_publish
        assert not any((video.video_url_480p, video.video_url_720p, video.video_url_1080p))
        with fence_session(worker, vid, generation):
            stale.is_published = True
            with pytest.raises(StaleProcessingGenerationError):
                await worker.commit()
        await worker.rollback()
    async with TestSessionLocal() as db:
        row = await db.get(Video, vid)
        assert row.storage_mode == "offline" and not row.is_published and not row.auto_publish


@pytest.mark.parametrize("method", ["GET", "HEAD"])
async def test_positive_media_cache_cannot_reopen_a_late_artifact_after_takedown(
    client, db_session, media_root, method
):
    user = User(phone="13600009703", name="Viewer", hashed_password="x")
    video = Video(
        title="Late artifact",
        source_url="upload.mp4",
        video_source="local",
        status=VideoStatus.ready,
        is_official=True,
        is_published=True,
        is_demo=True,
        processing_generation=str(uuid4()),
    )
    db_session.add_all([user, video])
    await db_session.commit()
    file = media_root / f"{artifact_identity(video.id, video.processing_generation)}_720p.mp4"
    file.write_bytes(b"published rendition")
    url = f"/media/{file.name}"
    assert (await client.request(method, url, params={"token": create_token(user.id)})).status_code == 200
    assert media._VIDEO_ACCESS_CACHE[video.id][1] is True

    await video_service.takedown_video(db_session, video.id)
    assert not file.exists()
    # Another process may still be finishing its old ffmpeg output after the
    # unlink. No process-local cache flush can revoke every process's verdict.
    media._cache_access_decision(video.id, True)
    file.write_bytes(b"late old-worker output")
    assert (await client.request(method, url, params={"token": create_token(user.id)})).status_code == 404
    media._cache_access_decision(video.id, True)
    assert (await client.request(method, url)).status_code == 404
