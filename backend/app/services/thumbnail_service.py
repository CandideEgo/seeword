"""Localize externally-hosted video thumbnails into the local media volume.

External thumbnail URLs (ytimg/hdslb/…) depend on the ``/media/proxy`` fetch
path at render time; when that egress dies (the HK relay expiring, a stale
HTTP_PROXY address) every cover on the site breaks at once. Localizing the
image at ingest/backfill time removes the runtime dependency: the cover
becomes a plain local static file served by nginx/backend like any media.

Host allowlist and Referer spoofing rules are shared with the proxy endpoint
via ``app.core.media_hosts`` so both surfaces stay in sync — and so this
service does not have to import the HTTP layer to get them.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.media_hosts import host_allowed, referer_for

logger = get_logger(__name__)

_MAX_BYTES = 5 * 1024 * 1024  # thumbnails are tiny; match the proxy cap
_TIMEOUT = 15.0

# Content-type → local extension. The media router serves with nosniff, so
# the extension must agree with the real payload type.
_EXT_BY_CONTENT_TYPE = (
    ("image/webp", ".webp"),
    ("image/png", ".png"),
    ("image/gif", ".gif"),
    ("image/jpeg", ".jpg"),
)


def _ext_for_content_type(content_type: str) -> str:
    ct = (content_type or "").lower()
    for needle, ext in _EXT_BY_CONTENT_TYPE:
        if needle in ct:
            return ext
    return ".jpg"


def local_thumbnail_stems(video_id: str) -> list[Path]:
    """Existing local thumbnail files for a video (any supported extension)."""
    base = Path(get_settings().local_media_path).resolve()
    return sorted(base.glob(f"{video_id}_thumb.*"))


def find_local_video_file(video_id: str) -> Path | None:
    """Locally-staged video file for frame extraction (transcode first, then raw)."""
    base = Path(get_settings().local_media_path).resolve()
    for name in (f"{video_id}_720p.mp4", f"{video_id}_480p.mp4", f"{video_id}_raw.mp4"):
        cand = base / name
        if cand.exists():
            return cand
    for f in base.glob(f"{video_id}_raw.*"):
        return f
    return None


async def extract_frame_thumbnail(video_path: Path, dest: Path) -> bool:
    """ffmpeg: grab one frame (~2s in) as a JPEG cover.

    Last-resort cover source when the CDN download fails (egress dead): a real
    frame from the local file beats a broken-image placeholder. Never raises.
    """
    tmp = dest.with_name(dest.name + ".part")
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-y",
            "-ss",
            "2",
            "-i",
            str(video_path),
            # -f/-update: dest has a probe/part extension ffmpeg can't infer;
            # single-image output regardless of filename.
            "-frames:v",
            "1",
            "-q:v",
            "3",
            "-f",
            "image2",
            "-update",
            "1",
            str(tmp),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=30)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        logger.warning("Frame extraction timed out for %s", video_path.name)
        tmp.unlink(missing_ok=True)
        return False
    except OSError as e:
        logger.warning("Frame extraction unavailable for %s: %s", video_path.name, str(e)[:120])
        return False
    if proc.returncode != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        logger.warning("Frame extraction failed for %s (rc=%s)", video_path.name, proc.returncode)
        tmp.unlink(missing_ok=True)
        return False
    tmp.replace(dest)
    return True


async def download_thumbnail(url: str, dest: Path, proxy: str | None = None) -> bool:
    """Download ``url`` to ``dest`` honoring the proxy host allowlist.

    Returns True on success, False on any failure (never raises) — callers
    decide the fallback. Redirects are followed: unlike the user-facing
    ``/media/proxy`` endpoint this runs in a trusted ingest/backfill context,
    and CDNs (ytimg/hdslb) occasionally redirect between edge hosts.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    if not host_allowed(parsed.hostname):
        logger.warning("Thumbnail host not in allowlist: %s", parsed.hostname)
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 SeeWord/1.0 (thumbnail fetch)",
        "Referer": referer_for(parsed.hostname),
        "Accept": "image/*,*/*;q=0.8",
    }
    settings = get_settings()
    try:
        async with httpx.AsyncClient(
            timeout=_TIMEOUT,
            proxy=proxy if proxy is not None else (settings.http_proxy or None),
            follow_redirects=True,
        ) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.warning("Thumbnail fetch %s -> HTTP %s", url[:80], resp.status_code)
            return False
        data = resp.content
        if not data or len(data) > _MAX_BYTES:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        tmp.write_bytes(data)
        tmp.replace(dest)
        return True
    except httpx.HTTPError as e:
        logger.warning("Thumbnail fetch failed for %s: %s", url[:80], str(e)[:200])
        return False


async def localize_video_thumbnail(
    video,
    proxy: str | None = None,
    fallback_urls: list[str] | None = None,
    *,
    artifact_id: str | None = None,
) -> bool:
    """Download ``video.thumbnail_url`` into the media volume, rewrite to local.

    Idempotent: already-local or missing URLs are left untouched (True); a
    failed download keeps the external URL (False) so nothing regresses.

    ``fallback_urls`` — when the primary URL fails (e.g. YouTube maxresdefault
    404), each fallback is tried in order before resorting to ffmpeg frame
    extraction.  This preserves the author's chosen cover at a lower
    resolution instead of replacing it with an arbitrary video frame.

    ``artifact_id`` isolates a pipeline attempt's probe, cover and frame source.
    Omitted by legacy/backfill callers, it preserves the video-id filenames.
    """
    artifact_id = artifact_id if artifact_id is not None else video.id
    url = video.thumbnail_url
    if not url or not url.startswith("http"):
        return True

    # A worker supplies its attempt identity; scripts and legacy callers keep
    # their original filenames. Never reuse another attempt's thumb/probe/raw.
    existing = local_thumbnail_stems(artifact_id)
    if existing:
        video.thumbnail_url = f"/media/{existing[0].name}"
        return True

    settings = get_settings()
    base = Path(settings.local_media_path).resolve()
    probe = base / f"{artifact_id}_thumb.probe"
    ok = await download_thumbnail(url, probe, proxy=proxy)
    # Primary URL failed — try fallbacks before giving up.
    if not ok and fallback_urls:
        for fb_url in fallback_urls:
            if fb_url == url:
                continue
            logger.info("Thumbnail fallback for %s: trying %s", video.id[:8], fb_url[:80])
            if await download_thumbnail(fb_url, probe, proxy=proxy):
                ok = True
                break
    if not ok:
        # CDN unreachable (egress dead): synthesize a cover from the local
        # video file when it exists — no runtime network dependency.
        local_video = find_local_video_file(artifact_id)
        if local_video is not None:
            ok = await extract_frame_thumbnail(local_video, probe)
    if not ok:
        return False
    # Extension from the actual payload (headers can lie; nosniff serving
    # requires the extension to match).
    ext = _ext_for_content_type(_sniff(probe))
    dest = base / f"{artifact_id}_thumb{ext}"
    probe.replace(dest)
    video.thumbnail_url = f"/media/{dest.name}"
    return True


def _sniff(path: Path) -> str:
    """Cheap magic-byte content type sniff (payload may disagree with headers)."""
    head = path.read_bytes()[:16]
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "image/jpeg"
