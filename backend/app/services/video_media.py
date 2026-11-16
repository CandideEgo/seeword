"""Media I/O used by cloud pipeline tasks and maintenance scripts.

Owns source metadata, staged files, downloads and playable renditions. It does
not enqueue tasks, own database transactions or import the GPU worker.
"""

import asyncio
import shutil
import uuid
from pathlib import Path
from urllib.parse import unquote, urlsplit

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Remux sources at or below the target; only scale genuinely taller sources.
TRANSCODE_PROFILES = {
    "720p": {"height": 720},
}
MEDIA_PROBE_TIMEOUT_SECONDS = 15


def find_local_raw(video_id: str) -> str | None:
    """Locate the staged raw file ``{video_id}_raw.*`` in the media directory."""
    media_dir = Path(get_settings().local_media_path).resolve()
    if not media_dir.exists():
        return None
    for f in media_dir.iterdir():
        if f.stem == f"{video_id}_raw":
            return str(f)
    return None


async def stage_local_upload(video) -> tuple[str, str]:
    """Copy a local upload to this attempt's raw path and stage it on OSS.

    Returns ``(gpu_source, remote_key)`` where ``gpu_source`` is a signed URL
    (private bucket) or CDN URL (public bucket) the GPU worker can fetch
    without OSS credentials. When OSS is not configured (dev, GPU worker on the
    same host), falls back to the local raw file path so the worker reads it
    directly — ``remote_key`` is empty in that case.
    """
    from app.services import oss_service
    from app.services.processing_generation import artifact_identity

    settings = get_settings()
    artifact_id = artifact_identity(video.id, getattr(video, "processing_generation", None))
    src = Path(video.source_url)
    if not src.exists():
        raise Exception(f"Local upload file not found: {video.source_url}")

    ext = src.suffix or ".mp4"
    media_dir = Path(settings.local_media_path).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    raw_path = media_dir / f"{artifact_id}_raw{ext}"
    if src.resolve() != raw_path.resolve():
        # A retry may inherit a prior attempt's source_url. Copy rather than
        # rename: neither a new attempt nor a late legacy worker may steal
        # another attempt's input. Publish the copy atomically for resumption.
        # A .part extension also keeps the unfinished copy outside the media
        # router's servable extension allowlist.
        staged = media_dir / f"{artifact_id}_raw.{uuid.uuid4().hex}{ext}.part"
        try:
            shutil.copy2(src, staged)
            staged.replace(raw_path)
        finally:
            staged.unlink(missing_ok=True)
    video.source_url = str(raw_path)

    remote_key = f"{settings.oss_raw_prefix}/{artifact_id}{ext}"
    cdn_url = await oss_service.upload_file(str(raw_path), remote_key)
    if cdn_url:
        if settings.oss_raw_bucket_public:
            gpu_source = cdn_url
        else:
            gpu_source = oss_service.get_signed_url(remote_key, expires=settings.oss_signed_url_expiry)
            if not gpu_source:
                raise Exception("OSS signed URL generation failed")
        return gpu_source, remote_key

    # OSS not configured (dev): when the GPU worker runs on the same host as
    # the cloud backend, it can read the local raw file directly — skip the
    # OSS round-trip. Production has OSS enabled and never hits this branch.
    logger.info("OSS not configured; GPU worker will read local raw file", video_id=video.id)
    return str(raw_path), ""


async def cleanup_oss_raw(video_id: str, source_url: str) -> None:
    """Best-effort deletion of the staged raw upload from OSS."""
    from app.services import oss_service

    ext = Path(source_url).suffix or ".mp4"
    remote_key = f"{get_settings().oss_raw_prefix}/{video_id}{ext}"
    await oss_service.delete_file(remote_key)


_EXTRACT_MAX_ATTEMPTS = 5
_EXTRACT_RETRY_BASE_DELAY = 8  # 秒；第 n 次重试等 n * base


def youtube_extractor_args(settings) -> dict:
    """yt-dlp ``extractor_args`` for YouTube: client choice + POT provider.

    - ``player_client``: web_safari first, then web+android as fallback.
      web_safari is required to unlock the adaptive high-res ladder:
      with only web/android, YouTube withholds all adaptive formats and
      returns just format 18 (360p), which was the root cause of the
      46×640x360 blurry videos (2026-09-16 实测). ``tv`` answers
      UNPLAYABLE / "The page needs to be reloaded" for many videos.
    - ``youtubepot-bgutilhttp.base_url``: the bgutil POT provider address. It has
      to be spelled out — otherwise the plugin's request to its own default
      (127.0.0.1:4416) is routed through ``http_proxy``, which cannot reach the
      host loopback, and every POT fetch dies on a 20s read timeout.
    """
    args: dict = {"youtube": {"player_client": ["web_safari", "web", "android"]}}
    if settings.youtube_pot_base_url:
        args["youtubepot-bgutilhttp"] = {"base_url": [settings.youtube_pot_base_url]}
    return args


async def extract_video_info(url: str) -> dict | None:
    """Extract video metadata via yt-dlp without downloading.

    Returns title/thumbnail/duration plus an ``external`` key carrying the
    parsed external-metadata fields (see ``services/external_meta.py``).
    """
    import yt_dlp

    settings = get_settings()
    loop = asyncio.get_event_loop()

    def _sync_extract() -> dict | None:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "remote_components": "ejs:github",
            # node 运行时：解 YouTube n-challenge 签名（无 JS 运行时只能拿到图片格式）
            "js_runtimes": {"node": {}},
        }
        if settings.http_proxy:
            opts["proxy"] = settings.http_proxy
        if settings.youtube_cookies_path:
            # 副本：yt-dlp 退出时会把 cookie jar 写回 cookiefile，YouTube 的 anti-bot
            # 响应里带清 auth 的 Set-Cookie，直接传原文件会把 LOGIN_INFO 洗掉
            from app.services.youtube_cookies_service import disposable_cookiefile

            ck = disposable_cookiefile(settings.youtube_cookies_path)
            if ck:
                opts["cookiefile"] = ck
        # tv/web/android client：默认 web client 常触发 anti-bot（"Sign in to confirm"），
        # 即便 cookies 有效；tv+android 通常放行（2026-09-08 batch 教训）
        opts["extractor_args"] = youtube_extractor_args(settings)
        opts["socket_timeout"] = 30
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

                from app.services.external_meta import parse_external_meta, pick_best_thumbnail

                # 从 thumbnails 列表选原视频作者设置的封面（而非自动截帧）
                best_thumb = pick_best_thumbnail(info)
                # 构造 fallback URLs：当最佳封面下载失败时尝试其他分辨率
                thumb_fallbacks = []
                yt_id = info.get("id")
                if yt_id and ("youtube.com" in url or "youtu.be" in url):
                    for qual in ("maxresdefault", "hqdefault", "sddefault", "default"):
                        fb = f"https://i.ytimg.com/vi/{yt_id}/{qual}.jpg"
                        if fb != best_thumb:
                            thumb_fallbacks.append(fb)

                return {
                    "title": info.get("title"),
                    "thumbnail": best_thumb,
                    "thumbnail_fallbacks": thumb_fallbacks,
                    "duration": info.get("duration"),
                    "youtube_video_id": yt_id,
                    "external": parse_external_meta(info),
                }
        except Exception:
            logger.exception("Failed to extract video info")
            return None

    # YouTube 的 anti-bot 是概率性的：同一 URL 同一 cookies 连续请求会有部分被
    # "Sign in to confirm you're not a bot" 拦下（实测 5 次里过 1 次）。这里退避重试，
    # 而不是让整条 pipeline 因一次拦截就 error。
    for attempt in range(_EXTRACT_MAX_ATTEMPTS):
        info = await loop.run_in_executor(None, _sync_extract)
        if info is not None:
            return info
        if attempt < _EXTRACT_MAX_ATTEMPTS - 1:
            delay = _EXTRACT_RETRY_BASE_DELAY * (attempt + 1)
            logger.info(
                "extract_video_info_retry",
                url=url,
                attempt=attempt + 1,
                max_attempts=_EXTRACT_MAX_ATTEMPTS,
                delay=delay,
            )
            await asyncio.sleep(delay)
    return None


async def download_video(url: str, video_id: str) -> str | None:
    """Download video from YouTube/Bilibili to local media storage.

    Returns the file path if successful, None otherwise.
    """
    import yt_dlp

    settings = get_settings()
    media_dir = Path(settings.local_media_path).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    output = str(media_dir / f"{video_id}_raw.%(ext)s")

    loop = asyncio.get_event_loop()

    def _sync_download() -> str | None:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "format": f"bestvideo[height<={settings.video_max_height}]+bestaudio/best[height<={settings.video_max_height}]/best",
            "outtmpl": output,
            "merge_output_format": "mp4",
            "remote_components": "ejs:github",
            # node 运行时：解 YouTube n-challenge 签名
            "js_runtimes": {"node": {}},
        }
        if settings.http_proxy:
            opts["proxy"] = settings.http_proxy
        if settings.youtube_cookies_path:
            # 副本：yt-dlp 退出时会把 cookie jar 写回 cookiefile，YouTube 的 anti-bot
            # 响应里带清 auth 的 Set-Cookie，直接传原文件会把 LOGIN_INFO 洗掉
            from app.services.youtube_cookies_service import disposable_cookiefile

            ck = disposable_cookiefile(settings.youtube_cookies_path)
            if ck:
                opts["cookiefile"] = ck
        # tv/web/android client：默认 web client 常触发 anti-bot（"Sign in to confirm"），
        # 即便 cookies 有效；tv+android 通常放行（2026-09-08 batch 教训）
        opts["extractor_args"] = youtube_extractor_args(settings)
        opts["socket_timeout"] = 30
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            raw_mp4 = media_dir / f"{video_id}_raw.mp4"
            if raw_mp4.exists():
                return str(raw_mp4)

            # yt-dlp may have used a different extension
            for f in media_dir.iterdir():
                if f.stem == f"{video_id}_raw" and f.suffix != ".mp4":
                    # Try renaming to mp4 if it's a supported format
                    return str(f)
            return None
        except Exception:
            logger.exception("Video download failed")
            return None

    return await loop.run_in_executor(None, _sync_download)


async def _communicate(proc: asyncio.subprocess.Process) -> tuple[bytes, bytes]:
    """Collect output, terminating/reaping a media child if its caller stops.

    Cancelling communicate alone leaves ffmpeg/ffprobe running. Drain the pipes
    after killing, so a full stderr buffer cannot keep process cleanup waiting.
    Cancellation still propagates to the pipeline owner.
    """
    try:
        return await proc.communicate()
    except BaseException:
        if proc.returncode is None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass  # The process exited between the state check and kill.
        await proc.communicate()
        raise


async def is_usable_media_file(path: Path) -> bool:
    """Require a nonempty regular file and a probeable video stream."""
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return False
    except OSError:
        return False
    height = await get_video_height(str(path))
    return height is not None and height > 0


async def is_usable_local_url(url: str) -> bool:
    """Validate an existing /media URL inside the configured media root."""
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/media/"):
        return False
    root = Path(get_settings().local_media_path).resolve()
    path = (root / unquote(parsed.path[len("/media/") :])).resolve()
    if not path.is_relative_to(root):
        return False
    return await is_usable_media_file(path)


async def transcode_video(source_path: str, video_id: str) -> dict[str, str]:
    """Produce the target-resolution variant of a downloaded source.

    The source is already a YouTube-encoded H.264 stream. When its height is
    at or below the target (TRANSCODE_PROFILES) we remux — stream-copy video
    and audio, add +faststart — instead of re-encoding. This is zero quality
    loss and near-zero CPU, which matters on the 2-core prod VPS (re-encoding
    1080p with libx264 there takes minutes per video and only adds loss).
    A genuinely-higher source (e.g. a 1080p download targeting 720p) gets
    scaled with libx264 at CRF 20.

    Returns a dict mapping resolution key to URL path.
    """
    settings = get_settings()
    media_dir = Path(settings.local_media_path).resolve()
    source = Path(source_path)

    if not source.exists():
        logger.error(f"Source video not found for transcoding: {source_path}")
        return {}

    media_dir.mkdir(parents=True, exist_ok=True)
    urls: dict[str, str] = {}
    source_res = await get_video_height(source_path)

    for label, profile in TRANSCODE_PROFILES.items():
        # Remux when the source is at or below the target height. Re-encoding
        # a 720p source to 720p is pure generation loss (same pixels, new loss).
        needs_scale = bool(source_res and source_res > profile["height"])

        out_name = f"{video_id}_{label}.mp4"
        out_path = media_dir / out_name
        if out_path.resolve().parent != media_dir:
            raise ValueError("Media output must stay in the media directory")
        # Only replace the published filename once ffmpeg and the output probe
        # succeed. A failed/cancelled retry must leave a good prior file intact.
        temp_path = media_dir / f"{video_id}_{label}.{uuid.uuid4().hex}.part.mp4"

        if needs_scale:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(source),
                "-vf",
                f"scale=-2:{profile['height']}",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "20",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(temp_path),
            ]
        else:
            # Stream copy both video and audio: no decode, no re-encode.
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(source),
                "-c",
                "copy",
                "-movflags",
                "+faststart",
                str(temp_path),
            ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await _communicate(proc)

            if proc.returncode == 0 and await is_usable_media_file(temp_path):
                temp_path.replace(out_path)
                urls[label] = f"/media/{out_name}"
                mode = "scaled" if needs_scale else "remuxed"
                logger.info(f"{mode.capitalize()} {label}: {out_name}")
            else:
                logger.error(f"FFmpeg {label} failed: {stderr.decode()[:200]}")
        except FileNotFoundError:
            logger.warning("FFmpeg not installed - skipping video transcoding")
            return {}
        except Exception:
            logger.exception(f"Transcoding {label} failed")
        finally:
            # This UUID-named file belongs only to this invocation, inside the
            # checked media root. Never remove the prior published rendition.
            temp_path.unlink(missing_ok=True)

    return urls


async def get_video_height(path: str) -> int | None:
    """Get video height using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=height",
        "-of",
        "csv=p=0",
        path,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        async with asyncio.timeout(MEDIA_PROBE_TIMEOUT_SECONDS):
            stdout, _ = await _communicate(proc)
        if proc.returncode != 0:
            return None
        height = stdout.decode().strip()
        return int(height) if height.isdigit() else None
    except Exception:
        return None
