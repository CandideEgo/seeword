"""Range-aware static media serving.

Starlette's ``StaticFiles`` / ``FileResponse`` do not honor HTTP ``Range``
requests — a long-standing limitation that breaks HTML5 ``<video>`` seeking:
the browser exposes an empty ``seekable`` range, so setting ``currentTime``
(e.g. when clicking a subtitle to jump) silently resets to 0 and the video
plays from the start.

This router serves files under the local media directory with full byte-range
support (``206 Partial Content`` + ``Accept-Ranges``), so the browser can seek
arbitrarily. Production fronts media with nginx (range-aware); this router is
mounted unconditionally but costs nothing there since nginx serves media first.
"""

import mimetypes
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, StreamingResponse

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.database import get_async_session_maker
from app.core.limiter import rate_limit
from app.core.media_hosts import host_allowed, referer_for
from app.models.user import User

router = APIRouter(prefix="/media", tags=["media"])

_CHUNK = 64 * 1024

# Only these extensions may ever be served from the media directory. Anything
# else (html, svg, json, ...) is a 404: a client-chosen filename extension must
# never become servable content on the trusted origin (stored-XSS defense).
# There is no upload-side counterpart any more — user submissions are gone
# (INV-003); every file in this tree is produced by the pipeline or by ops.
_SERVE_EXT_ALLOWLIST = {
    ".mp4",
    ".webm",
    ".mov",
    ".avi",
    ".mkv",
    ".mp3",
    ".wav",
    ".ogg",
    ".m4a",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
}

# ---------------------------------------------------------------------------
# Image proxy — bypasses CDN hotlink protection (Referer) and mixed-content
# (http:// thumbnails on an https site) for externally-hosted video thumbnails.
# YouTube/Bilibili/Douyin all serve thumbnails from CDN hosts that either
# hotlink-protect via Referer or serve over plain http; routing the <img> src
# through this endpoint makes them load reliably on any platform.
# ---------------------------------------------------------------------------

# The allowlist itself lives in ``app/core/media_hosts.py`` — the thumbnail
# service needs the same policy, and a service must not import the HTTP layer.
# Keep in sync with the frontend allowlist in frontend/src/lib/api.ts (mediaUrl).
# NOTE: aliyuncs.com is deliberately NOT in the list — OSS bucket domains are
# attacker-controllable ({bucket}.oss-{region}.aliyuncs.com), and with
# redirect-following disabled upstreams cannot jump to internal hosts anyway.
# OSS-hosted images should be served directly via signed/CDN URLs instead.

_PROXY_MAX_BYTES = 5 * 1024 * 1024  # 5 MB cap — thumbnails are tiny
_PROXY_TIMEOUT = 8.0

# Shared httpx client for the proxy endpoint. Creating a client per request
# (the old behaviour) paid a fresh connection/TLS handshake for every
# thumbnail on the homepage; a pooled singleton reuses upstream connections.
_proxy_client: httpx.AsyncClient | None = None


def _get_proxy_client() -> httpx.AsyncClient:
    global _proxy_client
    if _proxy_client is None or _proxy_client.is_closed:
        settings = get_settings()
        _proxy_client = httpx.AsyncClient(
            timeout=_PROXY_TIMEOUT,
            # Redirects must NOT be followed: the host allowlist is validated
            # only on the initial URL, so following a 3xx Location to an
            # arbitrary host would be an open SSRF (e.g. an OSS bucket 回源
            # rule redirecting to cloud metadata / internal services). A
            # redirect upstream now surfaces as a 502 "Upstream error".
            follow_redirects=False,
            proxy=settings.http_proxy or None,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _proxy_client


async def close_proxy_client() -> None:
    """Shutdown hook — called from the app lifespan."""
    global _proxy_client
    if _proxy_client is not None and not _proxy_client.is_closed:
        await _proxy_client.aclose()
    _proxy_client = None


def _host_allowed(host: str) -> bool:
    return host_allowed(host)


def _referer_for(host: str) -> str:
    return referer_for(host)


@router.get("/proxy")
@rate_limit("120/minute")
async def proxy_image(
    request: Request,
    url: str = Query(..., description="Absolute image URL to proxy"),
):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid URL")
    if not _host_allowed(parsed.hostname):
        raise HTTPException(status_code=400, detail="Host not allowed")

    headers = {
        "User-Agent": "Mozilla/5.0 SeeWord/1.0 (thumbnail proxy)",
        "Referer": _referer_for(parsed.hostname),
        "Accept": "image/*,*/*;q=0.8",
    }

    buf = bytearray()
    content_type = "image/jpeg"
    client = _get_proxy_client()
    try:
        async with client.stream("GET", url, headers=headers) as resp:
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Upstream error")
            # Cheap size guard before downloading: upstreams usually advertise
            # the length, so oversized images are rejected without bandwidth.
            declared = resp.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > _PROXY_MAX_BYTES:
                raise HTTPException(status_code=413, detail="Image too large")
            ct = resp.headers.get("content-type", "")
            if ct and ct.lower().startswith("image/"):
                content_type = ct.split(";")[0].strip()
            async for chunk in resp.aiter_bytes(_CHUNK):
                buf.extend(chunk)
                if len(buf) > _PROXY_MAX_BYTES:
                    raise HTTPException(status_code=413, detail="Image too large")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Upstream fetch failed") from None

    return Response(
        content=bytes(buf),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ---------------------------------------------------------------------------
# Retired recording upload compatibility route.
# Must be defined BEFORE the catch-all serve_media route.
# ---------------------------------------------------------------------------


@router.post("/shadowing-audio")
@rate_limit("30/minute")
async def upload_shadowing_audio(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Compatibility endpoint. Never reads or writes a recording blob."""
    from app.services.retired_features import feature_gone

    feature_gone()


async def _shadowing_token_ok(owner_user_id: str, request: Request) -> bool:
    """Validate the ``?token=`` JWT for a shadowing recording.

    The token must resolve to a live, non-banned user through the shared auth
    chain and its ``sub`` must match the owner id embedded in the media path.
    Returns False on any mismatch / malformed / revoked token (caller maps to
    404).
    """
    token = request.query_params.get("token", "")
    if not token:
        return False
    return (await _viewer_id_from_request(request)) == owner_user_id


# ---------------------------------------------------------------------------
# Publish-state gate for video media files.
#
# Pipeline-produced files are named ``{video_id}.mp4`` (720p fallback),
# ``{video_id}_480p.mp4`` / ``_720p`` / ``_1080p`` / ``_raw.<ext>``; fenced
# attempts insert ``_g{32 lowercase hex}`` between the UUID and that suffix.
# They must
# not be publicly downloadable while the video is unpublished (draft UGC
# content leaks before admin approval otherwise — the URL is derivable from
# the video id). Access follows the same rules as the API layer
# (services/video_access.py): official/published/snapshot videos are public,
# owners and admins may preview drafts via a JWT (?token= or Bearer).
# ---------------------------------------------------------------------------
_VIDEO_ARTIFACT_STEM = (
    r"(?P<vid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"(?:_g[0-9a-f]{32})?"
)
_VIDEO_FILE_RE = re.compile(rf"^{_VIDEO_ARTIFACT_STEM}(?:_raw|_480p|_720p|_1080p)?$")
# Atomic writers probe temporary bytes before replacing the final filename.
# Those UUID-named files are not playable artifacts, even for an admin/owner.
_VIDEO_TEMP_FILE_RE = re.compile(rf"^{_VIDEO_ARTIFACT_STEM}_(?:raw|480p|720p|1080p)\.[0-9a-f]{{32}}\.part$")

# Short-TTL cache of the viewer-independent access decision:
# {video_id: (expires_at, publicly_viewable)}. Only "is this video public" may
# live behind a video_id key — see ``_video_media_allowed``.
_VIDEO_ACCESS_CACHE: dict[str, tuple[float, bool]] = {}
_VIDEO_ACCESS_CACHE_TTL = 60.0
# Upper bound on cache entries: the TTL check on read only evicts entries that
# are re-accessed, so without a cap random-UUID requests against
# /media/{vid}.mp4 would grow the dict without limit.
_VIDEO_ACCESS_CACHE_MAX = 1024


def _cache_access_decision(video_id: str, public: bool) -> None:
    """Store a viewer-independent access decision, bounding the cache size.

    Evicts expired entries first, then the oldest live entries (dicts preserve
    insertion order) until the cap is satisfied.
    """
    now = time.monotonic()
    if len(_VIDEO_ACCESS_CACHE) >= _VIDEO_ACCESS_CACHE_MAX:
        for key, (expires_at, _) in list(_VIDEO_ACCESS_CACHE.items()):
            if expires_at <= now:
                _VIDEO_ACCESS_CACHE.pop(key, None)
        while len(_VIDEO_ACCESS_CACHE) >= _VIDEO_ACCESS_CACHE_MAX:
            _VIDEO_ACCESS_CACHE.pop(next(iter(_VIDEO_ACCESS_CACHE)), None)
    _VIDEO_ACCESS_CACHE[video_id] = (now + _VIDEO_ACCESS_CACHE_TTL, public)


async def _viewer_id_from_request(request: Request) -> str | None:
    """Resolve the viewer's user id from ``?token=`` or the Authorization
    header through the same auth chain as the API (blacklist / password change /
    banned). Returns None when absent or no longer valid (anonymous viewer)."""
    token = request.query_params.get("token", "")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        return None
    from app.api.dependencies import resolve_token_user

    async with get_async_session_maker()() as db:
        user = await resolve_token_user(token, db)
    return user.id if user is not None else None


async def _video_media_allowed(video_id: str, viewer_id: str | None) -> bool:
    """Publish-state gate for a pipeline-produced video media file.

    缓存只存与 viewer 无关的「公共判定」（official / published / snapshot，
    offline 一律视为不公共）；owner/admin 旁路每次请求实时判定。把带 viewer
    维度的结论按 video_id 缓存，会让 owner/admin 预览草稿时写入的允许值在
    TTL 内泄漏给任意其他 viewer，反向也会把 owner 误锁成 404。

    已下线（``storage_mode='offline'``）的视频一律不再提供媒体流：媒体文件
    此时已删除，且即使残留也不该被播放（需求 §5.3）。管理员仍可预览以复核。
    """
    now = time.monotonic()
    cached = _VIDEO_ACCESS_CACHE.get(video_id)
    # Only anonymous denials may be reused. Positive state must be read live:
    # a taken-down worker may finish writing an old artifact after local file
    # cleanup, and a cached public=True must not make those bytes playable.
    if cached is not None and cached[0] > now and not cached[1] and viewer_id is None:
        return False

    from app.models.video import Video
    from app.services.video_access import check_video_access_by_owner, is_admin

    async with get_async_session_maker()() as db:
        video = await db.get(Video, video_id)
        # offline 是内容状态而非 viewer 属性（ADR-0020：门控不依赖文件系统），
        # 所以它参与被缓存的那一半判定。
        public = video is not None and video.storage_mode != "offline" and check_video_access_by_owner(video, None)
        _cache_access_decision(video_id, public)
        if public:
            return True
        if video is None or viewer_id is None:
            return False

        viewer = await db.get(User, viewer_id)
        if video.storage_mode == "offline":
            return is_admin(viewer)
        # Admin preview bypass — the rule lives in video_access.is_admin
        # (role read from the DB-backed User row, not the JWT).
        return check_video_access_by_owner(video, viewer_id) or is_admin(viewer)


# ---------------------------------------------------------------------------
# Membership gate — DISABLED for the internal test (需求 §2.3 内测期免费开放).
#
# History: under the D0 unlock model this gate required active Pro or a
# permanent unlock row for Free viewers. The internal-test requirement is
# "免费开放全功能，不引入 Pro 概念", so every logged-in viewer may stream any
# video that passes the publish-state gate above. Anonymous viewers are still
# refused except for ``is_demo`` videos, whose open access is a deliberate
# carve-out for the (deferred) public landing page — the login wall sends
# everyone else to /login. The paid membership chain is gone for good: the
# orders / jinshuju_payments / user_video_unlocks tables and the users.plan*
# columns were dropped in migration d4e5f6a7b8c9, and
# tests/test_architecture_invariants.py::DROPPED_TABLES fails if any of them
# reappears in the metadata. The login wall is the only remaining boundary.
#
# Draft/unpublished protection is NOT this gate's job: ``_video_media_allowed``
# above still enforces owner/admin-only preview for those.
# ---------------------------------------------------------------------------


async def _video_unlock_allowed(video_id: str, viewer_id: str | None) -> bool:
    """Whether this viewer may stream the video's media.

    内测期：登录用户一律放行（免费开放）；匿名仅 ``is_demo`` 示范视频放行
    （落地页预留，见 FREE-TIER-ASSESSMENT §D 登录墙保留）。
    """
    if viewer_id is not None:
        return True
    from app.models.video import Video

    async with get_async_session_maker()() as db:
        video = await db.get(Video, video_id)
        return bool(video is not None and video.is_demo)


@router.get("/{file_path:path}")
@router.head("/{file_path:path}")
@rate_limit("60/minute")
async def serve_media(file_path: str, request: Request):
    base = Path(get_settings().local_media_path).resolve()
    # Resolve safely — reject paths that escape the media directory.
    full = (base / file_path).resolve()
    try:
        full.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=404) from None
    if not full.is_file():
        raise HTTPException(status_code=404)
    # Extension allowlist: non-media files (html/svg/json/...) are never
    # servable from the media directory (stored-XSS defense).
    if full.suffix.lower() not in _SERVE_EXT_ALLOWLIST:
        raise HTTPException(status_code=404)

    # Shadowing recordings are private per-user: require a valid JWT whose
    # subject matches the owner id in the path. The token travels as a query
    # param (?token=) because <audio src> cannot attach Authorization headers.
    # 404 (not 401) so non-owners cannot probe which recordings exist.
    #
    # Segments come from the resolved ``full`` (``full.is_file()`` above proves
    # it sits inside ``base``), never from the raw ``file_path``: any ``..``
    # segment that survives upstream normalization decouples the request path
    # from the file served, so `/media/x/../shadowing/{other}/rec.webm` skipped
    # this branch entirely (no gate at all) and
    # `/media/shadowing/{own}/../../{vid}.mp4` entered it, skipping the
    # publish-state gate below. The gate must follow the bytes that ship.
    rel = full.relative_to(base).parts
    if len(rel) == 1 and _VIDEO_TEMP_FILE_RE.fullmatch(full.stem) is not None:
        raise HTTPException(status_code=404)
    if rel[0] == "shadowing":
        if len(rel) < 2 or not await _shadowing_token_ok(rel[1], request):
            raise HTTPException(status_code=404)
    else:
        # Publish-state gate for pipeline-produced video files
        # ({video_id}.mp4 / _raw / _480p / _720p / _1080p). Uploads staged as
        # {uuid}.mp4 match too — they belong to no video row yet, so the
        # lookup fails and they 404, which also removes the source_url leak.
        # The gate is scoped to ROOT-level files only: pipeline output always
        # lands at the media root, while user content (avatars/{uuid}.jpg,
        # shadowing/…) lives in subdirectories — matching the stem alone
        # would 404 every avatar (users.py::upload_avatar stores bare-uuid
        # filenames under avatars/).
        m = _VIDEO_FILE_RE.match(full.stem)
        if m is not None and len(rel) == 1:
            vid = m.group("vid")
            viewer_id = await _viewer_id_from_request(request)
            if not await _video_media_allowed(vid, viewer_id):
                raise HTTPException(status_code=404)
            if not await _video_unlock_allowed(vid, viewer_id):
                # Membership gate (D0): 403 (not 404) so the player surfaces
                # "locked" distinctly — the frontend gates on the access field
                # before playback anyway.
                raise HTTPException(status_code=403, detail="Video locked")

    total = full.stat().st_size
    media_type = mimetypes.guess_type(full.name)[0] or "application/octet-stream"
    range_header = request.headers.get("range")

    # HEAD: advertise range support, no body.
    if request.method == "HEAD":
        return Response(
            status_code=200,
            media_type=media_type,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(total),
                "X-Content-Type-Options": "nosniff",
            },
        )

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(total),
        "Content-Type": media_type,
        # The main.py security-headers middleware skips /media paths (media
        # must stay cacheable/proxyable), so set nosniff here explicitly.
        "X-Content-Type-Options": "nosniff",
    }

    # No Range header → full file (200), still advertising range support.
    if not range_header:
        return StreamingResponse(_read(full, 0, total), media_type=media_type, headers=headers)

    # Parse "bytes=start-end" (single range only; end optional).
    try:
        unit, spec = range_header.split("=", 1)
        if unit.strip().lower() != "bytes" or "," in spec:
            raise ValueError
        start_s, _, end_s = spec.strip().partition("-")
        if not start_s:
            # Suffix range "bytes=-N": the final N bytes (RFC 7233 §2.1).
            suffix_len = int(end_s) if end_s else 0
            if suffix_len <= 0:
                raise ValueError
            start = max(total - suffix_len, 0)
            end = total - 1
        else:
            start = int(start_s)
            end = int(end_s) if end_s else total - 1
    except ValueError:
        raise HTTPException(status_code=416, detail="Unsupported Range") from None

    if start < 0 or start >= total or end >= total or start > end:
        return Response(
            status_code=416,
            media_type=media_type,
            headers={
                "Content-Range": f"bytes */{total}",
                "X-Content-Type-Options": "nosniff",
            },
        )

    length = end - start + 1
    headers["Content-Length"] = str(length)
    headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    return StreamingResponse(
        _read(full, start, length),
        status_code=206,
        media_type=media_type,
        headers=headers,
    )


def _read(path: Path, start: int, length: int):
    """Yield `length` bytes from `path` starting at `start` (sync iterator → threadpool)."""
    remaining = length
    with open(path, "rb") as f:
        f.seek(start)
        while remaining > 0:
            chunk = f.read(min(_CHUNK, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
