"""内容三态与半自动下线（需求 §5.1 / §5.3）。

Covers:
- ``videos.storage_mode`` 默认 local；迁移回填
- POST /videos/admin/{id}/takedown：is_published=False + storage_mode=offline +
  清空 video_url_* + 删除本地媒体文件（缩略图保留），幂等
- 下线后：feed/browse/推荐/搜索/排行 自动隐藏（复用 is_published 过滤）
- 下线后：媒体流不再可读（403/404），管理员仍可预览复核
- 收藏夹保留入口并下发 storage_mode（前端标注「已下架」）
- 学习记录不断链：字幕与词汇本词行保留
- GET /videos/admin/takedown-suggestions：阈值规则 + 仅管理员可访问
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import TestSessionLocal


@pytest.fixture(autouse=True)
def _isolated_media_root(tmp_path, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "local_media_path", str(tmp_path))
    return tmp_path


async def _seed_video(
    db,
    *,
    title: str = "Takedown Test",
    view_count: int = 0,
    favorite_count: int = 0,
    age_days: int = 0,
    with_subtitle: bool = True,
):
    """官方已发布 ready 视频；可指定热度与上线天数。"""
    from app.models.subtitle import Subtitle
    from app.models.video import Video, VideoReviewStatus, VideoStatus

    created = datetime.now(UTC) - timedelta(days=age_days)
    video = Video(
        title=title,
        source_url=f"https://www.youtube.com/watch?v={abs(hash(title)) % 10**11:011d}",
        video_source="imported",
        status=VideoStatus.ready,
        is_official=True,
        is_published=True,
        review_status=VideoReviewStatus.published.value,
        created_at=created,
        published_at=created,
        view_count=view_count,
        favorite_count=favorite_count,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # 媒体文件名用真实 id —— /media 门控正则要求 UUID 前缀。
    from app.core.config import get_settings

    media_dir = Path(get_settings().local_media_path).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "raw": media_dir / f"{video.id}_raw.mp4",
        "bare": media_dir / f"{video.id}.mp4",
        "720": media_dir / f"{video.id}_720p.mp4",
        "thumb": media_dir / f"{video.id}_thumb.jpg",
    }
    for path in files.values():
        path.write_bytes(b"payload")
    video.video_url_720p = f"/media/{video.id}_720p.mp4"
    video.thumbnail_url = f"/media/{video.id}_thumb.jpg"
    await db.commit()

    if with_subtitle:
        db.add(
            Subtitle(
                video_id=video.id,
                start_time=0.0,
                end_time=2.0,
                text_en="Takedown check",
                text_zh="下线验证",
                sentence_index=0,
                word_levels={"check": ["cet4"]},
            )
        )
        await db.commit()
    return video, files


class TestStorageMode:
    async def test_defaults_to_local(self, db_session):
        video, _ = await _seed_video(db_session, title="ModeDefault")
        assert video.storage_mode == "local"

    async def test_takedown_is_idempotent(self, client: AsyncClient, admin_headers: dict, db_session):
        video, _ = await _seed_video(db_session, title="IdemDown")
        first = await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)
        assert first.status_code == 200, first.text
        second = await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)
        assert second.status_code == 200
        assert second.json()["storage_mode"] == "offline"

    async def test_takedown_unknown_video_404(self, client: AsyncClient, admin_headers: dict):
        resp = await client.post("/api/v1/videos/admin/does-not-exist/takedown", headers=admin_headers)
        assert resp.status_code == 404

    async def test_takedown_requires_admin(self, client: AsyncClient, auth_headers: dict, db_session):
        video, _ = await _seed_video(db_session, title="NotAdmin")
        resp = await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=auth_headers)
        assert resp.status_code == 403


class TestTakedownEffects:
    async def test_takedown_hides_and_clears_urls(self, client: AsyncClient, admin_headers: dict, db_session):
        video, _ = await _seed_video(db_session, title="Hidden", with_subtitle=False)
        resp = await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["storage_mode"] == "offline"
        assert body["is_published"] is False

        async with TestSessionLocal() as db:
            from app.models.video import Video

            fresh = (await db.execute(select(Video).where(Video.id == video.id))).scalar_one()
            # video 行保留 dormant（不断链），但播放 URL 已清空。
            assert fresh is not None
            assert fresh.storage_mode == "offline"
            assert fresh.is_published is False
            assert fresh.video_url_480p is None
            assert fresh.video_url_720p is None
            assert fresh.video_url_1080p is None

    async def test_takedown_deletes_media_but_keeps_thumbnail(self, admin_headers, db_session, client):
        video, files = await _seed_video(db_session, title="FilesGone", with_subtitle=False)
        assert all(p.exists() for p in files.values())

        await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)

        # 视频媒体（raw / 裸 mp4 / 720p）已删；缩略图保留（收藏夹仍要渲染卡片）。
        assert not files["raw"].exists()
        assert not files["bare"].exists()
        assert not files["720"].exists()
        assert files["thumb"].exists()

    async def test_takedown_hides_from_feed_and_rankings(self, client: AsyncClient, admin_headers: dict, db_session):
        video, _ = await _seed_video(db_session, title="FeedGone", with_subtitle=False)
        before = await client.get("/api/v1/browse/feed?page=1&page_size=50")
        assert any(i["id"] == video.id for i in before.json()["items"])

        await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)

        after = await client.get("/api/v1/browse/feed?page=1&page_size=50")
        assert not any(i["id"] == video.id for i in after.json()["items"])
        latest = await client.get("/api/v1/videos/rankings?scope=latest")
        assert not any(i["id"] == video.id for i in latest.json())

    async def test_takedown_blocks_media_stream(
        self, client: AsyncClient, admin_headers: dict, auth_headers: dict, db_session
    ):
        video, _ = await _seed_video(db_session, title="StreamGone", with_subtitle=False)
        from app.core.security import create_token

        admin_id = None
        async with TestSessionLocal() as db:
            from app.models.user import User

            admin = (await db.execute(select(User).where(User.role == "admin"))).scalars().first()
            admin_id = admin.id if admin else None

        await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)

        # 普通登录用户：媒体不可读。
        async with TestSessionLocal() as db:
            from app.models.user import User

            user = (await db.execute(select(User).where(User.phone == "13800138000"))).scalar_one()
            user_token = create_token(user.id)
        resp = await client.get(f"/media/{video.id}_720p.mp4?token={user_token}")
        assert resp.status_code in (403, 404), resp.status_code

        # 管理员仍可预览复核（门控放行；文件虽已删故 404 是文件系统层）。
        if admin_id:
            admin_resp = await client.get(f"/media/{video.id}_720p.mp4?token={create_token(admin_id)}")
            assert admin_resp.status_code != 403

    async def test_favorites_keep_offline_entry_with_flag(
        self, client: AsyncClient, admin_headers: dict, auth_headers: dict, db_session
    ):
        """需求 §5.3：收藏夹保留入口并标注「已下架」。"""
        from app.models.favorite import UserFavorite
        from app.models.user import User

        video, _ = await _seed_video(db_session, title="FavKept", with_subtitle=False)
        async with TestSessionLocal() as db:
            user = (await db.execute(select(User).where(User.phone == "13800138000"))).scalar_one()
            db.add(UserFavorite(user_id=user.id, video_id=video.id))
            await db.commit()

        favs = (await client.get("/api/v1/videos/favorites", headers=auth_headers)).json()
        item = next(i for i in favs["items"] if i["id"] == video.id)
        assert item["storage_mode"] == "local"

        await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)

        favs = (await client.get("/api/v1/videos/favorites", headers=auth_headers)).json()
        item = next(i for i in favs["items"] if i["id"] == video.id)
        assert item["storage_mode"] == "offline"  # 仍在收藏夹，带已下架标注

    async def test_learning_records_survive_takedown(
        self, client: AsyncClient, admin_headers: dict, auth_headers: dict, db_session
    ):
        """学习记录不断链（§5.3）：字幕与词汇本词行保留，详情仍带字幕。"""
        from app.models.learning import Vocabulary
        from app.models.user import User

        video, _ = await _seed_video(db_session, title="KeepLearning")
        async with TestSessionLocal() as db:
            user = (await db.execute(select(User).where(User.phone == "13800138000"))).scalar_one()
            db.add(
                Vocabulary(
                    user_id=user.id,
                    word="check",
                    video_id=video.id,
                    mastery_level="mastered",
                )
            )
            await db.commit()

        await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)

        detail = (await client.get(f"/api/v1/videos/{video.id}", headers=auth_headers)).json()
        assert detail["storage_mode"] == "offline"
        assert detail["video_url_720p"] is None  # 不可播
        assert len(detail["subtitles"]) == 1  # 字幕/词标注保留（点词仍可用）

        async with TestSessionLocal() as db:
            words = (await db.execute(select(Vocabulary).where(Vocabulary.video_id == video.id))).scalars().all()
            assert len(words) == 1 and words[0].mastery_level == "mastered"


class TestTakedownSuggestions:
    async def test_suggestions_require_admin(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/v1/videos/admin/takedown-suggestions", headers=auth_headers)
        assert resp.status_code == 403

    async def test_suggestions_select_cold_and_old(self, client: AsyncClient, admin_headers: dict, db_session):
        # 冷门 + 超龄 → 入选
        cold, _ = await _seed_video(db_session, title="ColdOld", age_days=60, view_count=3, favorite_count=0)
        # 热门 → 不入选
        hot, _ = await _seed_video(db_session, title="HotOld", age_days=60, view_count=9999, favorite_count=500)
        # 新品（未超龄）→ 不入选
        new, _ = await _seed_video(db_session, title="ColdNew", age_days=1, view_count=0, favorite_count=0)

        resp = await client.get("/api/v1/videos/admin/takedown-suggestions", headers=admin_headers)
        assert resp.status_code == 200
        ids = [i["id"] for i in resp.json()["items"]]
        assert cold.id in ids
        assert hot.id not in ids
        assert new.id not in ids

    async def test_suggestions_exclude_already_offline(self, client: AsyncClient, admin_headers: dict, db_session):
        video, _ = await _seed_video(db_session, title="AlreadyDown", age_days=60, view_count=1)
        await client.post(f"/api/v1/videos/admin/{video.id}/takedown", headers=admin_headers)
        resp = await client.get("/api/v1/videos/admin/takedown-suggestions", headers=admin_headers)
        assert video.id not in [i["id"] for i in resp.json()["items"]]


@pytest.mark.parametrize("generation", [None, "22222222-2222-4222-8222-222222222222"])
async def test_takedown_replaces_generation_and_fences_old_session(db_session, generation):
    from app.models.video import Video
    from app.services.processing_generation import StaleProcessingGenerationError, fence_session
    from app.services.video_service import takedown_video

    video, _ = await _seed_video(db_session, title="Fenced", with_subtitle=False)
    video.processing_generation = generation
    video.auto_publish = True
    await db_session.commit()
    async with TestSessionLocal() as worker:
        stale = await worker.get(Video, video.id)
        await takedown_video(db_session, video.id)
        assert video.processing_generation != generation
        assert UUID(video.processing_generation).version == 4
        assert not video.is_published and not video.auto_publish
        with fence_session(worker, video.id, generation):
            stale.title = "must not overwrite taken-down row"
            with pytest.raises(StaleProcessingGenerationError):
                await worker.commit()
            await worker.rollback()
    async with TestSessionLocal() as reader:
        fresh = await reader.get(Video, video.id)
        assert fresh.title == "Fenced" and fresh.storage_mode == "offline"
        assert fresh.video_url_720p is None and not fresh.is_published


async def test_takedown_locks_live_row_before_changing_generation(db_session):
    from sqlalchemy import event

    from app.services.video_service import takedown_video

    video, _ = await _seed_video(db_session, title="Locked", with_subtitle=False)
    seen = []

    def capture(state):
        if state.is_select:
            statement = state.statement
            if statement._for_update_arg is not None:
                seen.append(statement.get_execution_options())

    event.listen(db_session.sync_session, "do_orm_execute", capture)
    try:
        await takedown_video(db_session, video.id)
    finally:
        event.remove(db_session.sync_session, "do_orm_execute", capture)
    assert seen and seen[0].get("populate_existing") is True


def test_delete_media_removes_exact_video_generations_only(_isolated_media_root):
    from app.services.processing_generation import artifact_identity
    from app.services.video_service import _delete_media_files

    root = _isolated_media_root
    video_id = str(uuid4())
    other_id = str(uuid4())
    ids = [video_id, artifact_identity(video_id, str(uuid4())), artifact_identity(video_id, str(uuid4()))]
    removed = []
    kept = [f"{other_id}_raw.webm", f"{other_id}_720p.mp4", f"{video_id}_g{'a' * 31}_720p.mp4"]
    kept += [f"{video_id}_g{'b' * 33}_raw.mp4", f"{video_id}extra_720p.mp4", f"{video_id}_720p.mp4.bak"]
    for identity in ids:
        removed += [
            f"{identity}.mp4",
            f"{identity}_raw.mp4",
            f"{identity}_raw.webm",
            f"{identity}_raw.{uuid4().hex}.part.mp4",
            f"{identity}_480p.mp4",
            f"{identity}_720p.mp4",
            f"{identity}_1080p.mp4",
            f"{identity}_720p.{uuid4().hex}.part.mp4",
        ]
        kept += [f"{identity}_thumb.jpg", f"{identity}_thumb.probe", f"{identity}_thumb.png.part"]
    for name in removed + kept:
        (root / name).write_bytes(b"test-owned file")
    nested = root / "avatars" / f"{video_id}_720p.mp4"
    nested.parent.mkdir()
    nested.write_bytes(b"nested unrelated file")
    _delete_media_files(video_id)
    assert all(not (root / name).exists() for name in removed)
    assert all((root / name).read_bytes() == b"test-owned file" for name in kept)
    assert nested.read_bytes() == b"nested unrelated file"
    _delete_media_files("*")
    assert all((root / name).exists() for name in kept)
