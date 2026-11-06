"""全站免费开放 — 访问行为（2026-11 下线会员收费链路之后）。

Covers:
- 注册不再赠 Pro：新账号没有会员字段（UserResponse 不含 plan/plan_expires_at）
- 登录用户对已发布视频直接可看：详情带字幕/URL
- 匿名只能拿元信息：不下发字幕/播放地址（登录墙语义保留）
- 示范视频 is_demo 对匿名只放媒体流，详情仍按登录墙
- 已退役的解锁/收费端点全部 404
"""

from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import TestSessionLocal


async def _seed_ready_video(db, *, title: str = "Free Access", is_demo: bool = False, with_subtitle: bool = True):
    """Insert an official, published, ready video (optionally with 1 subtitle)."""
    from app.models.subtitle import Subtitle
    from app.models.video import Video, VideoReviewStatus, VideoStatus

    video = Video(
        title=title,
        source_url=f"https://www.youtube.com/watch?v={abs(hash(title)) % 10**11:011d}",
        video_source="imported",
        status=VideoStatus.ready,
        is_official=True,
        is_published=True,
        review_status=VideoReviewStatus.published.value,
        video_url_720p=f"/media/video-{title}.mp4",
        is_demo=is_demo,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    if with_subtitle:
        db.add(
            Subtitle(
                video_id=video.id,
                start_time=0.0,
                end_time=2.0,
                text_en="Hello world",
                text_zh="你好世界",
                sentence_index=0,
            )
        )
        await db.commit()
    return video


class TestNoMembershipOnSignup:
    async def test_register_returns_no_plan_fields(self, client: AsyncClient):
        import app.services.sms_service as sms_svc

        # Dev-fake SMS mode (code "1234").
        original = sms_svc._dev_fake_enabled
        sms_svc._dev_fake_enabled = lambda: True
        try:
            await client.post("/api/v1/auth/sms/send-code", json={"phone": "13600136000", "purpose": "register"})
            resp = await client.post(
                "/api/v1/auth/sms/register",
                json={"phone": "13600136000", "code": "1234", "password": "Testpass123!"},
            )
        finally:
            sms_svc._dev_fake_enabled = original
        assert resp.status_code == 201, resp.text
        user_payload = resp.json()["user"]
        assert "plan" not in user_payload
        assert "plan_expires_at" not in user_payload

        from app.models.user import User

        async with TestSessionLocal() as db:
            user = (await db.execute(select(User).where(User.phone == "13600136000"))).scalar_one()
            assert not hasattr(user, "plan_expires_at")


class TestFreeDetail:
    async def test_logged_in_detail_serves_subtitles_and_urls(
        self, client: AsyncClient, auth_headers: dict, db_session
    ):
        """免费开放：登录用户无需解锁即可拿到字幕与可播放 URL。"""
        video = await _seed_ready_video(db_session, title="OneVideo")
        resp = await client.get(f"/api/v1/videos/{video.id}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["title"] == "OneVideo"
        assert len(data["subtitles"]) == 1
        assert data["video_url_720p"] == "/media/video-OneVideo.mp4"
        assert "access" not in data

    async def test_anonymous_detail_is_metadata_only(self, client: AsyncClient, db_session):
        """匿名只能拿元信息：字幕/播放地址不下发（登录墙）。"""
        video = await _seed_ready_video(db_session, title="AnonWall")
        resp = await client.get(f"/api/v1/videos/{video.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "AnonWall"
        assert data["subtitles"] == []
        assert data["video_url_720p"] is None

    async def test_demo_video_detail_same_as_any_video(self, client: AsyncClient, auth_headers: dict, db_session):
        video = await _seed_ready_video(db_session, title="DemoVid", is_demo=True)
        resp = await client.get(f"/api/v1/videos/{video.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["subtitles"]) == 1


class TestAdminDetail:
    """管理员后台详情（skip_access_check）不受登录墙的空载荷影响。"""

    async def test_admin_detail_still_serves_subtitles_and_urls(
        self, client: AsyncClient, admin_headers: dict, db_session
    ):
        video = await _seed_ready_video(db_session, title="AdminDetail")
        resp = await client.get(f"/api/v1/videos/admin/{video.id}/detail", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["subtitles"]) == 1
        assert data["video_url_720p"] == "/media/video-AdminDetail.mp4"


class TestRetiredPaymentSurface:
    """会员收费链路已整体下线：解锁与收款端点都不再存在。"""

    async def test_unlock_endpoint_is_gone(self, client: AsyncClient, auth_headers: dict, db_session):
        video = await _seed_ready_video(db_session, title="GoneUnlock")
        assert (await client.post(f"/api/v1/videos/{video.id}/unlock", headers=auth_headers)).status_code == 404

    async def test_unlocked_lists_are_gone(self, client: AsyncClient, auth_headers: dict):
        assert (await client.get("/api/v1/videos/unlocked", headers=auth_headers)).status_code == 404
        assert (await client.get("/api/v1/videos/unlocked-ids", headers=auth_headers)).status_code == 404

    async def test_payment_endpoints_are_gone(self, client: AsyncClient, auth_headers: dict):
        assert (await client.get("/api/v1/payments/status", headers=auth_headers)).status_code == 404
        assert (await client.get("/api/v1/payments/jinshuju/purchase-link", headers=auth_headers)).status_code == 404


class TestShadowingSentencesGate:
    """EndScreen 跟读重点句端点：跟读功能本身已退役（410）。"""

    async def test_logged_in_user_gets_410(self, client: AsyncClient, auth_headers: dict, db_session):
        video = await _seed_ready_video(db_session, title="SentencesGone")
        resp = await client.get(f"/api/v1/videos/{video.id}/shadowing-sentences", headers=auth_headers)
        assert resp.status_code == 410
        assert resp.json()["code"] == "FEATURE_RETIRED"

    async def test_anonymous_requires_auth(self, client: AsyncClient, db_session):
        video = await _seed_ready_video(db_session, title="AnonSentences")
        resp = await client.get(f"/api/v1/videos/{video.id}/shadowing-sentences")
        assert resp.status_code == 401
