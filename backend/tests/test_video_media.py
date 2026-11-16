"""Media adapter failure/cancellation and format decisions, without network I/O."""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import yt_dlp

from app.services import video_media


@pytest.fixture
def media_config(tmp_path, monkeypatch):
    settings = SimpleNamespace(
        local_media_path=str(tmp_path / "media"),
        http_proxy=None,
        youtube_cookies_path=None,
        youtube_pot_base_url=None,
        video_max_height=720,
        oss_raw_prefix="raw",
        oss_raw_bucket_public=False,
        oss_signed_url_expiry=600,
    )
    monkeypatch.setattr(video_media, "get_settings", lambda: settings)
    return settings


class Process:
    def __init__(self, code=0, stdout=b"", stderr=b""):
        self.returncode = code
        self.stdout = stdout
        self.stderr = stderr

    async def communicate(self):
        return self.stdout, self.stderr


@pytest.mark.parametrize("height,scaled", [(720, False), (1080, True)])
async def test_transcode_remuxes_without_loss_or_scales_only_when_needed(
    tmp_path, media_config, monkeypatch, height, scaled
):
    source = tmp_path / "source.mp4"
    source.touch()
    commands = []

    async def spawn(*cmd, **kwargs):
        commands.append(cmd)
        if cmd[0] == "ffprobe":
            return Process(stdout=f"{height}\n".encode())
        Path(cmd[-1]).write_bytes(b"probeable test fixture")
        return Process()

    monkeypatch.setattr(video_media.asyncio, "create_subprocess_exec", spawn)
    assert await video_media.transcode_video(str(source), "video1") == {"720p": "/media/video1_720p.mp4"}
    ffmpeg = next(cmd for cmd in commands if cmd[0] == "ffmpeg")
    assert ffmpeg[0] == "ffmpeg"
    assert ("scale=-2:720" in ffmpeg) == scaled
    assert ("copy" in ffmpeg) != scaled
    assert "+faststart" in ffmpeg


@pytest.mark.parametrize("unavailable", [True, False])
async def test_missing_or_failed_ffmpeg_never_returns_success_urls(tmp_path, media_config, monkeypatch, unavailable):
    source = tmp_path / "source.mp4"
    source.touch()
    monkeypatch.setattr(video_media, "get_video_height", AsyncMock(return_value=720))

    async def spawn(*cmd, **kwargs):
        if unavailable:
            raise FileNotFoundError("ffmpeg")
        return Process(code=1, stderr=b"invalid input")

    monkeypatch.setattr(video_media.asyncio, "create_subprocess_exec", spawn)
    assert await video_media.transcode_video(str(source), "video1") == {}


@pytest.mark.parametrize("operation", ["probe", "transcode"])
@pytest.mark.parametrize("exit_during_kill", [False, True])
async def test_cancellation_kills_and_reaps_child_then_propagates(
    tmp_path, media_config, monkeypatch, operation, exit_during_kill
):
    entered = asyncio.Event()

    class HangingProcess:
        returncode = None
        calls = 0
        killed = False
        reaped = False

        async def communicate(self):
            self.calls += 1
            if self.calls == 1:
                entered.set()
                await asyncio.Future()
            self.reaped = True
            return b"", b""

        def kill(self):
            self.killed = True
            self.returncode = 0 if exit_during_kill else -9
            if exit_during_kill:
                raise ProcessLookupError("already exited")

    proc = HangingProcess()
    published = Path(media_config.local_media_path) / "video1_720p.mp4"
    published.parent.mkdir(parents=True, exist_ok=True)
    published.write_bytes(b"previous rendition")

    async def spawn(*args, **kwargs):
        if args[0] == "ffmpeg":
            Path(args[-1]).write_bytes(b"incomplete replacement")
        return proc

    source = tmp_path / "source.mp4"
    source.touch()
    monkeypatch.setattr(video_media.asyncio, "create_subprocess_exec", spawn)
    if operation == "probe":
        work = video_media.get_video_height(str(source))
    else:
        monkeypatch.setattr(video_media, "get_video_height", AsyncMock(return_value=720))
        work = video_media.transcode_video(str(source), "video1")
    task = asyncio.create_task(work)
    await asyncio.wait_for(entered.wait(), timeout=3)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(task, timeout=3)
    assert proc.killed and proc.reaped and proc.calls == 2
    assert proc.returncode is not None
    assert published.read_bytes() == b"previous rendition"
    assert list(published.parent.glob("*.part.mp4")) == []


@pytest.mark.parametrize("failure", ["empty", "failed", "unprobeable"])
async def test_unsuccessful_output_never_replaces_previous_rendition(tmp_path, media_config, monkeypatch, failure):
    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    published = Path(media_config.local_media_path) / "video1_720p.mp4"
    published.parent.mkdir(parents=True)
    published.write_bytes(b"previous usable rendition")

    async def height(path):
        return None if failure == "unprobeable" and path.endswith(".part.mp4") else 720

    async def spawn(*args, **kwargs):
        Path(args[-1]).write_bytes(b"" if failure == "empty" else b"partial")
        return Process(code=1 if failure == "failed" else 0)

    monkeypatch.setattr(video_media, "get_video_height", height)
    monkeypatch.setattr(video_media.asyncio, "create_subprocess_exec", spawn)
    assert await video_media.transcode_video(str(source), "video1") == {}
    assert published.read_bytes() == b"previous usable rendition"
    assert list(published.parent.glob("*.part.mp4")) == []


@pytest.mark.parametrize(
    "url", ["/media/../outside.mp4", "/media/%2e%2e/outside.mp4", "https://example.com/media/a.mp4"]
)
async def test_local_artifact_validation_stays_inside_media_root(tmp_path, media_config, monkeypatch, url):
    (tmp_path / "outside.mp4").write_bytes(b"not an owned media artifact")
    probe = AsyncMock(return_value=720)
    monkeypatch.setattr(video_media, "get_video_height", probe)
    assert not await video_media.is_usable_local_url(url)
    probe.assert_not_called()


async def test_probe_timeout_kills_child_and_returns_unavailable(media_config, monkeypatch):
    class HangingProbe:
        returncode = None
        calls = 0

        async def communicate(self):
            self.calls += 1
            if self.calls == 1:
                await asyncio.Future()
            return b"", b""

        def kill(self):
            self.returncode = -9

    proc = HangingProbe()
    monkeypatch.setattr(video_media.asyncio, "create_subprocess_exec", AsyncMock(return_value=proc))
    monkeypatch.setattr(video_media, "MEDIA_PROBE_TIMEOUT_SECONDS", 0.01)
    assert await video_media.get_video_height("fixture.mp4") is None
    assert proc.returncode == -9 and proc.calls == 2


async def test_metadata_retry_keeps_external_fields_and_thumbnail_fallbacks(media_config, monkeypatch):
    attempts = []

    class Downloader:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def extract_info(self, url, download):
            attempts.append(url)
            assert download is False
            assert self.options["extractor_args"]["youtube"]["player_client"][0] == "web_safari"
            if len(attempts) < 3:
                raise RuntimeError("temporary upstream failure")
            return {"id": "abc123", "title": "Lesson", "duration": 42, "channel": "Teacher"}

    monkeypatch.setattr(yt_dlp, "YoutubeDL", Downloader)
    monkeypatch.setattr(video_media, "_EXTRACT_RETRY_BASE_DELAY", 0)
    info = await video_media.extract_video_info("https://youtube.com/watch?v=abc123")
    assert len(attempts) == 3
    assert info["title"] == "Lesson" and info["duration"] == 42
    assert info["external"]["channel_name"] == "Teacher"
    assert "https://i.ytimg.com/vi/abc123/hqdefault.jpg" in info["thumbnail_fallbacks"]


async def test_download_preserves_actual_raw_extension(media_config, monkeypatch):
    class Downloader:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def download(self, urls):
            Path(self.options["outtmpl"].replace("%(ext)s", "webm")).touch()

    monkeypatch.setattr(yt_dlp, "YoutubeDL", Downloader)
    result = await video_media.download_video("https://example.com/video", "video1")
    assert result == str(Path(media_config.local_media_path).resolve() / "video1_raw.webm")
    assert video_media.find_local_raw("video1") == result


@pytest.mark.parametrize("signed", [True, False])
async def test_private_upload_uses_signed_source_and_keeps_canonical_path(tmp_path, media_config, monkeypatch, signed):
    source = tmp_path / "upload.mp4"
    source.write_bytes(b"test-owned raw file")
    video = SimpleNamespace(id="video1", source_url=str(source))
    monkeypatch.setattr("app.services.oss_service.upload_file", AsyncMock(return_value="https://cdn.example.com/raw"))
    monkeypatch.setattr(
        "app.services.oss_service.get_signed_url", lambda *a, **k: "https://signed.example.com/raw" if signed else None
    )
    if signed:
        gpu_source, key = await video_media.stage_local_upload(video)
        assert gpu_source == "https://signed.example.com/raw" and key == "raw/video1.mp4"
    else:
        with pytest.raises(Exception, match="signed URL generation failed"):
            await video_media.stage_local_upload(video)
    assert video.source_url.endswith("video1_raw.mp4")
    assert video_media.find_local_raw("video1") == video.source_url


@pytest.mark.parametrize("generation", [None, "22222222-2222-4222-8222-222222222222"])
async def test_upload_staging_never_moves_another_generations_source(tmp_path, media_config, monkeypatch, generation):
    from app.services.processing_generation import artifact_identity

    video_id = "11111111-1111-4111-8111-111111111111"
    other_generation = "33333333-3333-4333-8333-333333333333"
    other_id = artifact_identity(video_id, other_generation)
    media_dir = Path(media_config.local_media_path).resolve()
    media_dir.mkdir()
    source = media_dir / f"{other_id}_raw.webm"
    source.write_bytes(b"another attempt still needs these bytes")
    video = SimpleNamespace(id=video_id, source_url=str(source), processing_generation=generation)
    upload = AsyncMock(return_value="https://cdn.example.com/raw")
    monkeypatch.setattr("app.services.oss_service.upload_file", upload)
    monkeypatch.setattr("app.services.oss_service.get_signed_url", lambda *a, **k: "https://signed.example.com/raw")

    gpu_source, key = await video_media.stage_local_upload(video)
    artifact_id = artifact_identity(video_id, generation)
    expected = media_dir / f"{artifact_id}_raw.webm"
    assert gpu_source == "https://signed.example.com/raw"
    assert key == f"raw/{artifact_id}.webm"
    upload.assert_awaited_once_with(str(expected), key)
    assert Path(video.source_url) == expected
    assert expected.read_bytes() == source.read_bytes() == b"another attempt still needs these bytes"
    assert video_media.find_local_raw(artifact_id) == str(expected)
    # A retry reuses only this attempt's own canonical path.
    await video_media.stage_local_upload(video)
    assert source.exists() and expected.exists()
    assert list(media_dir.glob("*.part*")) == []


async def test_generation_upload_without_oss_keeps_local_source(tmp_path, media_config, monkeypatch):
    from app.services.processing_generation import artifact_identity

    source = tmp_path / "upload.mp4"
    source.write_bytes(b"local upload")
    video = SimpleNamespace(
        id="11111111-1111-4111-8111-111111111111",
        source_url=str(source),
        processing_generation="22222222-2222-4222-8222-222222222222",
    )
    monkeypatch.setattr("app.services.oss_service.upload_file", AsyncMock(return_value=None))
    local, key = await video_media.stage_local_upload(video)
    artifact_id = artifact_identity(video.id, video.processing_generation)
    assert Path(local).name == f"{artifact_id}_raw.mp4"
    assert key == "" and video.source_url == local
    assert source.read_bytes() == Path(local).read_bytes() == b"local upload"


async def test_failed_staging_copy_preserves_source_and_previous_raw(tmp_path, media_config, monkeypatch):
    media_dir = Path(media_config.local_media_path).resolve()
    media_dir.mkdir()
    source = tmp_path / "upload.mp4"
    source.write_bytes(b"source")
    previous = media_dir / "video1_raw.mp4"
    previous.write_bytes(b"previous raw")
    video = SimpleNamespace(id="video1", source_url=str(source))

    def fail_copy(src, dest):
        dest.write_bytes(b"partial copy")
        raise OSError("disk full")

    monkeypatch.setattr(video_media.shutil, "copy2", fail_copy)
    upload = AsyncMock()
    monkeypatch.setattr("app.services.oss_service.upload_file", upload)
    with pytest.raises(OSError, match="disk full"):
        await video_media.stage_local_upload(video)
    assert source.read_bytes() == b"source" and previous.read_bytes() == b"previous raw"
    assert video.source_url == str(source)
    assert list(media_dir.glob("*.part*")) == []
    upload.assert_not_called()
