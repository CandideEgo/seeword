"""Media access control — shadowing recordings are owner-only (?token= JWT)."""

from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_token
from app.models.video import Video, VideoReviewStatus, VideoSource, VideoStatus


@pytest_asyncio.fixture
async def media_dir(tmp_path, monkeypatch, db_session):
    """Point local_media_path at a temp dir with a shadowing recording + a
    public media file. Creates the two users the tokens below refer to, because
    media auth now goes through the full chain (user must exist)."""
    from app.models.user import User

    settings = get_settings()
    monkeypatch.setattr(settings, "local_media_path", str(tmp_path))
    (tmp_path / "shadowing" / "userA").mkdir(parents=True)
    (tmp_path / "shadowing" / "userA" / "rec.webm").write_bytes(b"fake audio")
    (tmp_path / "public.mp4").write_bytes(b"fake video")
    db_session.add_all(
        [
            User(id="userA", phone="13600000001", hashed_password="x", name="User A"),
            User(id="userB", phone="13600000002", hashed_password="x", name="User B"),
        ]
    )
    await db_session.commit()
    return tmp_path


async def test_shadowing_without_token_404(client, media_dir):
    resp = await client.get("/media/shadowing/userA/rec.webm")
    assert resp.status_code == 404


async def test_shadowing_owner_token_200(client, media_dir):
    token = create_token("userA")
    resp = await client.get(f"/media/shadowing/userA/rec.webm?token={token}")
    assert resp.status_code == 200
    assert resp.content == b"fake audio"


async def test_shadowing_other_user_token_404(client, media_dir):
    token = create_token("userB")
    resp = await client.get(f"/media/shadowing/userA/rec.webm?token={token}")
    assert resp.status_code == 404


async def test_shadowing_garbage_token_404(client, media_dir):
    resp = await client.get("/media/shadowing/userA/rec.webm?token=not-a-jwt")
    assert resp.status_code == 404


async def test_shadowing_refresh_token_rejected(client, media_dir):
    refresh = create_token("userA", token_type="refresh")
    resp = await client.get(f"/media/shadowing/userA/rec.webm?token={refresh}")
    assert resp.status_code == 404


async def test_shadowing_other_user_dir_404_even_with_owner_token(client, media_dir):
    # token matches userA, but the path belongs to another user dir
    token = create_token("userA")
    resp = await client.get(f"/media/shadowing/userB/rec.webm?token={token}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Path-gate coupling: the gate must branch on the same path that is served
# (`full`), not on the raw request path. `..` segments in the latter decouple
# the two — the resolved file lands in a private dir while the raw prefix looks
# harmless.
#
# The dots are percent-encoded on purpose: httpx normalizes a literal `..` away
# before sending, so `%2e%2e` is the only way to hand the ASGI app the raw
# segment a non-normalizing client/proxy would. Resource-wise `x/` need not
# exist — resolution never touches it.
# ---------------------------------------------------------------------------


async def test_shadowing_dotdot_prefix_does_not_skip_token_gate(client, media_dir):
    """`/media/x/../shadowing/{owner}/rec.webm` must still demand the token."""
    resp = await client.get("/media/x/%2e%2e/shadowing/userA/rec.webm")
    assert resp.status_code == 404


async def test_shadowing_dotdot_cannot_reach_other_user_with_own_token(client, media_dir):
    """A caller's own token must not unlock a sibling's recording via `..`."""
    other = media_dir / "shadowing" / "userB"
    other.mkdir(parents=True)
    (other / "rec.webm").write_bytes(b"userB private audio")
    token = create_token("userA")
    resp = await client.get(f"/media/shadowing/userA/%2e%2e/userB/rec.webm?token={token}")
    assert resp.status_code == 404


async def test_public_media_no_token_ok(client, media_dir):
    resp = await client.get("/media/public.mp4")
    assert resp.status_code == 200
    assert resp.content == b"fake video"


# ---------------------------------------------------------------------------
# Stored-XSS defense: uploaded extension is server-derived, and the media
# directory only ever serves allowlisted extensions with nosniff.
# ---------------------------------------------------------------------------


async def test_serve_media_rejects_non_media_extension(client, media_dir):
    """Planting a non-media file must not make it servable (stored-XSS)."""
    (media_dir / "evil.html").write_bytes(b"<script>alert(1)</script>")
    (media_dir / "evil.svg").write_bytes(b'<svg onload="alert(1)"></svg>')
    for name in ("evil.html", "evil.svg"):
        resp = await client.get(f"/media/{name}")
        assert resp.status_code == 404, name


async def test_public_media_has_nosniff(client, media_dir):
    resp = await client.get("/media/public.mp4")
    assert resp.status_code == 200
    assert resp.headers.get("x-content-type-options") == "nosniff"


# ---------------------------------------------------------------------------
# User content in subdirectories (avatars/) uses bare-uuid filenames and must
# NOT hit the video publish-state gate, which is scoped to pipeline-produced
# files at the media ROOT. Regression: avatars 404'd because the gate regex
# matched the uuid stem and found no Video row.
# ---------------------------------------------------------------------------


async def test_nested_uuid_named_image_not_treated_as_video(client, media_dir):
    """avatars/{uuid}.png must be served, not gated (was 404 before the fix)."""
    avatar = media_dir / "avatars" / f"{uuid4()}.png"
    avatar.parent.mkdir(parents=True)
    avatar.write_bytes(b"fake png")
    resp = await client.get(f"/media/avatars/{avatar.name}")
    assert resp.status_code == 200
    assert resp.content == b"fake png"


async def test_nested_video_uuid_still_not_gated(client, media_dir, db_session):
    """Even a subdirectory file whose stem equals a real video id is user
    content: the publish-state gate only applies to ROOT-level pipeline
    files, so this must be served without any Video lookup."""
    video = await _make_video(db_session, is_official=False, review_status="draft", user_id="owner-1")
    avatar = media_dir / "avatars" / f"{video.id}.png"
    avatar.parent.mkdir(parents=True)
    avatar.write_bytes(b"fake png")
    resp = await client.get(f"/media/avatars/{avatar.name}")
    assert resp.status_code == 200
    assert resp.content == b"fake png"


# ---------------------------------------------------------------------------
# /media/proxy — SSRF defense: allowlist is validated on the initial URL only,
# so redirects must not be followed and attacker-controllable OSS domains are
# excluded from the allowlist.
# ---------------------------------------------------------------------------


async def test_proxy_rejects_aliyuncs_host(client):
    resp = await client.get("/media/proxy", params={"url": "https://evil.oss-cn-beijing.aliyuncs.com/x.jpg"})
    assert resp.status_code == 400


async def test_proxy_rejects_internal_ip_url(client):
    resp = await client.get("/media/proxy", params={"url": "http://100.100.100.200/latest/meta-data/"})
    assert resp.status_code == 400


async def test_proxy_does_not_follow_redirects(client, monkeypatch):
    """A 3xx upstream must surface as an error, never be fetched to the
    redirect target (SSRF via OSS 回源-style redirect rules)."""

    async def handler(request):
        return httpx.Response(302, headers={"location": "http://100.100.100.200/latest/meta-data/"})

    from app.api.v1 import media as media_module

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(media_module, "_proxy_client", httpx.AsyncClient(transport=transport, follow_redirects=False))
    resp = await client.get("/media/proxy", params={"url": "https://ytimg.com/x.jpg"})
    assert resp.status_code == 502


async def test_proxy_success(client, monkeypatch):
    async def handler(request):
        return httpx.Response(200, content=b"img", headers={"content-type": "image/jpeg"})

    from app.api.v1 import media as media_module

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(media_module, "_proxy_client", httpx.AsyncClient(transport=transport))
    resp = await client.get("/media/proxy", params={"url": "https://ytimg.com/x.jpg"})
    assert resp.status_code == 200
    assert resp.content == b"img"
    assert resp.headers["content-type"] == "image/jpeg"


# ---------------------------------------------------------------------------
# Publish-state gate for pipeline-produced video media files
# ({video_id}.mp4 / _raw / _480p / _720p / _1080p). Draft/unpublished UGC media
# must not be publicly downloadable; owners and admins preview via ?token=.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_video_access_cache():
    """The access-decision cache is module-global with a 60s TTL — clear it per
    test so decisions from one test never leak into the next.

    The unlock-gate cache was removed when the membership gate was opened for
    the internal test (需求 §2.3); only the publish-state cache remains.
    """
    from app.api.v1 import media as media_module

    media_module._VIDEO_ACCESS_CACHE.clear()
    yield
    media_module._VIDEO_ACCESS_CACHE.clear()


async def _make_video(
    db: AsyncSession,
    *,
    is_official: bool = False,
    review_status: str = "draft",
    user_id: str | None = None,
    snapshot: dict | None = None,
) -> Video:
    video = Video(
        title="Test Video",
        source_url="https://example.com/source.mp4",
        video_source=VideoSource.imported,
        status=VideoStatus.ready,
        is_official=is_official,
        review_status=VideoReviewStatus(review_status).value,
        user_id=user_id,
        published_snapshot=snapshot,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


@pytest_asyncio.fixture
async def video_media_dir(tmp_path, monkeypatch, db_session):
    """Media dir with pipeline-produced files for videos in various states."""
    from app.models.user import User

    settings = get_settings()
    monkeypatch.setattr(settings, "local_media_path", str(tmp_path))

    # Owners referenced by the UGC videos below; media auth resolves the token
    # through the real user table, so these rows must exist.
    db_session.add_all(
        [
            User(id="owner-1", phone="13600000011", hashed_password="x", name="Owner 1"),
            User(id="owner-2", phone="13600000012", hashed_password="x", name="Owner 2"),
            User(id="owner-3", phone="13600000013", hashed_password="x", name="Owner 3"),
        ]
    )
    await db_session.commit()

    official = await _make_video(db_session, is_official=True, review_status="published")
    (tmp_path / f"{official.id}.mp4").write_bytes(b"official video")
    (tmp_path / f"{official.id}_720p.mp4").write_bytes(b"official 720p")

    ugc_draft = await _make_video(db_session, is_official=False, review_status="draft", user_id="owner-1")
    (tmp_path / f"{ugc_draft.id}_720p.mp4").write_bytes(b"draft video")

    ugc_published = await _make_video(db_session, is_official=False, review_status="published", user_id="owner-2")
    (tmp_path / f"{ugc_published.id}_480p.mp4").write_bytes(b"published ugc")

    snapshot_video = await _make_video(
        db_session,
        is_official=False,
        review_status="pending_review",
        user_id="owner-3",
        snapshot={"subtitles": []},
    )
    (tmp_path / f"{snapshot_video.id}_720p.mp4").write_bytes(b"snapshot video")

    # A staged-upload style file whose uuid matches no video row.
    (tmp_path / "12345678-1234-1234-1234-123456789012.mp4").write_bytes(b"staged upload")

    return {"official": official, "ugc_draft": ugc_draft, "ugc_published": ugc_published, "snapshot": snapshot_video}


async def _make_user(
    db: AsyncSession,
    *,
    phone: str,
    role: str = "user",
):
    from app.models.user import RoleType, User

    user = User(
        phone=phone,
        hashed_password="x",
        name=f"User {phone[-4:]}",
        role=RoleType(role),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def test_official_video_media_locked_for_anonymous(client, video_media_dir):
    """D0 membership gate: publish state passes, but anonymous viewers hold
    neither Pro nor an unlock — the stream is refused (403, not 404)."""
    v = video_media_dir["official"]
    for name in (f"{v.id}.mp4", f"{v.id}_720p.mp4"):
        resp = await client.get(f"/media/{name}")
        assert resp.status_code == 403, name


async def test_official_video_media_logged_in_ok(client, video_media_dir, db_session):
    """Any logged-in account can stream official media — there is no membership gate."""
    v = video_media_dir["official"]
    user = await _make_user(db_session, phone="13700000001")
    resp = await client.get(f"/media/{v.id}.mp4?token={create_token(user.id)}")
    assert resp.status_code == 200
    assert resp.content == b"official video"


async def test_demo_video_media_open_to_anonymous(client, video_media_dir, db_session):
    v = video_media_dir["official"]
    v.is_demo = True
    await db_session.commit()
    resp = await client.get(f"/media/{v.id}.mp4")
    assert resp.status_code == 200


async def test_published_ugc_media_locked_for_anonymous(client, video_media_dir):
    v = video_media_dir["ugc_published"]
    resp = await client.get(f"/media/{v.id}_480p.mp4")
    assert resp.status_code == 403


async def test_snapshot_video_media_locked_for_anonymous(client, video_media_dir):
    """Pending-re-review with a frozen snapshot stays *viewable* for viewers
    with access, but anonymous streaming still needs membership (D0)."""
    v = video_media_dir["snapshot"]
    resp = await client.get(f"/media/{v.id}_720p.mp4")
    assert resp.status_code == 403


async def test_draft_ugc_media_private_without_token(client, video_media_dir):
    v = video_media_dir["ugc_draft"]
    resp = await client.get(f"/media/{v.id}_720p.mp4")
    assert resp.status_code == 404


async def test_draft_ugc_media_owner_token_ok(client, video_media_dir):
    v = video_media_dir["ugc_draft"]
    token = create_token("owner-1")
    resp = await client.get(f"/media/{v.id}_720p.mp4?token={token}")
    assert resp.status_code == 200
    assert resp.content == b"draft video"


async def test_draft_ugc_media_other_user_token_404(client, video_media_dir):
    v = video_media_dir["ugc_draft"]
    token = create_token("someone-else")
    resp = await client.get(f"/media/{v.id}_720p.mp4?token={token}")
    assert resp.status_code == 404


async def test_draft_ugc_media_admin_token_ok(client, video_media_dir, db_session):
    from app.models.user import RoleType, User

    admin = User(
        phone="13911112222",
        hashed_password="x",
        name="Admin 2",
        role=RoleType.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    v = video_media_dir["ugc_draft"]
    token = create_token(admin.id)
    resp = await client.get(f"/media/{v.id}_720p.mp4?token={token}")
    assert resp.status_code == 200


async def test_unknown_video_media_404(client, video_media_dir):
    resp = await client.get(f"/media/{'0' * 36}_720p.mp4")
    assert resp.status_code == 404


async def test_staged_upload_file_not_servable(client, video_media_dir):
    """A staged upload uuid that maps to no video row must 404 (removes the
    source_url leak surface)."""
    resp = await client.get("/media/12345678-1234-1234-1234-123456789012.mp4")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# The access-decision cache must never carry a viewer-dependent verdict: the
# owner/admin preview bypass is evaluated per request, so one viewer's outcome
# can neither publish a draft to others nor lock its owner out.
# ---------------------------------------------------------------------------


async def test_draft_media_not_leaked_after_owner_preview(client, video_media_dir):
    """The owner's allowed preview must not cache a green light for everyone
    else (the draft URL is derivable from the video id)."""
    v = video_media_dir["ugc_draft"]
    owner = await client.get(f"/media/{v.id}_720p.mp4?token={create_token('owner-1')}")
    assert owner.status_code == 200

    other = await client.get(f"/media/{v.id}_720p.mp4?token={create_token('someone-else')}")
    assert other.status_code == 404
    anonymous = await client.get(f"/media/{v.id}_720p.mp4")
    assert anonymous.status_code == 404


async def test_owner_preview_not_blocked_by_anonymous_denial(client, video_media_dir):
    """Reverse direction: an anonymous 404 must not cache a denial that 404s
    the owner for the rest of the TTL."""
    v = video_media_dir["ugc_draft"]
    anonymous = await client.get(f"/media/{v.id}_720p.mp4")
    assert anonymous.status_code == 404

    owner = await client.get(f"/media/{v.id}_720p.mp4?token={create_token('owner-1')}")
    assert owner.status_code == 200
    assert owner.content == b"draft video"


async def test_banned_owner_token_cannot_preview_draft(client, video_media_dir, db_session):
    """Media auth must honour the same ban rule as the API auth chain."""
    from app.models.user import User

    owner = await db_session.get(User, "owner-1")
    assert owner is not None
    owner.is_banned = True
    await db_session.commit()

    v = video_media_dir["ugc_draft"]
    resp = await client.get(f"/media/{v.id}_720p.mp4?token={create_token('owner-1')}")
    assert resp.status_code == 404


async def test_stale_password_token_cannot_preview_draft(client, video_media_dir, db_session):
    """A token issued before a password change must fail on media too."""
    from datetime import timedelta

    from app.models.user import User

    owner = await db_session.get(User, "owner-1")
    assert owner is not None
    owner.password_changed_at = datetime.now(UTC) + timedelta(hours=1)
    await db_session.commit()

    v = video_media_dir["ugc_draft"]
    resp = await client.get(f"/media/{v.id}_720p.mp4?token={create_token('owner-1')}")
    assert resp.status_code == 404


async def test_banned_shadowing_owner_token_404(client, media_dir, db_session):
    """Shadowing recordings use the same chain: a banned owner loses access."""
    from app.models.user import User

    owner = await db_session.get(User, "userA")
    assert owner is not None
    owner.is_banned = True
    await db_session.commit()

    resp = await client.get(f"/media/shadowing/userA/rec.webm?token={create_token('userA')}")
    assert resp.status_code == 404


async def test_shadowing_dotdot_cannot_bypass_publish_gate(client, video_media_dir):
    """`/media/shadowing/{own}/../../{vid}.mp4` resolves to a root pipeline file:
    it must hit the publish-state gate, not the shadowing branch (whose token
    check the caller trivially satisfies with their own token)."""
    v = video_media_dir["ugc_draft"]
    token = create_token("attacker")
    bypass = await client.get(f"/media/shadowing/attacker/%2e%2e/%2e%2e/{v.id}_720p.mp4?token={token}")
    assert bypass.status_code == 404
    # Same verdict as the equivalent direct request — the gate follows the
    # resolved file, so the two URL spellings cannot disagree.
    direct = await client.get(f"/media/{v.id}_720p.mp4?token={token}")
    assert direct.status_code == 404
