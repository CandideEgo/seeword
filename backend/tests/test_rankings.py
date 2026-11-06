"""Tests for the home rankings feature (GET /api/v1/videos/rankings).

Covers the three scopes (latest / weekly_views / weekly_favorites): the
visibility triple, the calendar-week windows (Monday 00:00 Asia/Shanghai),
the session_id anti-fraud dedup, the top-20 cap, the snapshot beat task, and
the endpoint's cache read-through. Reuses the test_recommendations.py fixture
pattern: auth_headers + TestSessionLocal + explicit BehaviorEvent ids
(BigInteger PK on SQLite).

async tests run under pytest-asyncio auto mode (no @mark needed), same as
test_recommendations.py.
"""

from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.cache import cache_get_json, cache_set_json
from app.models.behavior import BehaviorEvent
from app.models.favorite import UserFavorite
from app.models.user import RoleType, User
from app.models.video import Video, VideoReviewStatus, VideoStatus
from app.services.ranking_service import (
    RANKING_SCOPES,
    compute_rankings,
    current_week_start_utc,
    rankings_cache_key,
)
from app.tasks.ranking_tasks import snapshot_rankings
from tests.conftest import TestSessionLocal


def _in_window(hours: float = 1.0) -> datetime:
    """A timestamp inside the current calendar week (Monday 00:00 CST + hours)."""
    return current_week_start_utc() + timedelta(hours=hours)


def _before_window(hours: float = 1.0) -> datetime:
    """A timestamp just before this week started — excluded by weekly scopes."""
    return current_week_start_utc() - timedelta(hours=hours)


# SQLite only auto-increments INTEGER PRIMARY KEY; BehaviorEvent.id is
# BigInteger (Postgres serial), so tests assign explicit unique ids.
_event_id = 0


def _next_event_id() -> int:
    global _event_id
    _event_id += 1
    return _event_id


async def _owner(db) -> User:
    return (await db.execute(select(User).where(User.phone == "13800138000"))).scalar_one()


async def _make_user(db, phone: str) -> User:
    u = User(phone=phone, hashed_password="hashed", name="Rank Test", role=RoleType.user)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _make_video(
    db,
    *,
    title: str = "V",
    published_at: datetime | None = None,
    created_at: datetime | None = None,
    status: VideoStatus = VideoStatus.ready,
    is_official: bool = True,
    is_published: bool = True,
    view_count: int = 0,
    owner_id: str | None = None,
) -> Video:
    v = Video(
        title=title,
        source_url=f"https://x.test/{abs(hash(title)) % 1000000}",
        video_source="imported",
        status=status,
        is_official=is_official,
        is_published=is_published,
        review_status=VideoReviewStatus.published.value,
        user_id=owner_id,
        topic_tags="tech",
        difficulty_level="B1",
        duration=120.0,
        view_count=view_count,
        video_url_720p=f"/media/{abs(hash(title)) % 1000000}.mp4",
    )
    if published_at is not None:
        v.published_at = published_at
    if created_at is not None:
        v.created_at = created_at
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v


async def _event(
    db,
    *,
    video_id: str,
    event_type: str = "play",
    session_id: str | None = None,
    server_ts: datetime | None = None,
    user_id: str | None = None,
) -> None:
    e = BehaviorEvent(
        id=_next_event_id(),
        user_id=user_id,
        video_id=video_id,
        event_type=event_type,
        session_id=session_id,
    )
    if server_ts is not None:
        e.server_ts = server_ts
    db.add(e)
    await db.commit()


async def _favorite(db, *, user_id: str, video_id: str, created_at: datetime | None = None) -> None:
    f = UserFavorite(user_id=user_id, video_id=video_id)
    if created_at is not None:
        f.created_at = created_at
    db.add(f)
    await db.commit()


class TestLatestRankings:
    async def test_orders_by_published_at_desc_nulls_last(self, auth_headers):
        now = datetime.now(UTC)
        async with TestSessionLocal() as db:
            user = await _owner(db)
            oldest = await _make_video(db, title="oldest", published_at=now - timedelta(days=3), owner_id=user.id)
            newest = await _make_video(db, title="newest", published_at=now - timedelta(days=1), owner_id=user.id)
            null_pub = await _make_video(db, title="nullpub", published_at=None, owner_id=user.id)
            middle = await _make_video(db, title="middle", published_at=now - timedelta(days=2), owner_id=user.id)
            items = await compute_rankings(db, "latest")
        assert [i["id"] for i in items] == [newest.id, middle.id, oldest.id, null_pub.id]
        assert all(i["metric"] is None for i in items)
        assert all(i["published_at"] is not None for i in items[:3])
        assert items[-1]["published_at"] is None

    async def test_visibility_filtering(self, auth_headers):
        """Unpublished / non-official / not-ready videos never rank."""
        now = datetime.now(UTC)
        async with TestSessionLocal() as db:
            user = await _owner(db)
            await _make_video(db, title="unpublished", published_at=now, is_published=False, owner_id=user.id)
            await _make_video(db, title="ugc", published_at=now, is_official=False, owner_id=user.id)
            await _make_video(db, title="processing", published_at=now, status=VideoStatus.processing, owner_id=user.id)
            visible = await _make_video(db, title="visible", published_at=now, owner_id=user.id)
            items = await compute_rankings(db, "latest")
        assert [i["id"] for i in items] == [visible.id]

    async def test_card_fields_include_view_count(self, auth_headers):
        async with TestSessionLocal() as db:
            user = await _owner(db)
            await _make_video(db, title="v", published_at=datetime.now(UTC), view_count=42, owner_id=user.id)
            items = await compute_rankings(db, "latest")
        assert items[0]["view_count"] == 42
        assert set(items[0]) >= {
            "id",
            "title",
            "thumbnail_url",
            "duration",
            "difficulty_level",
            "topic_tags",
            "is_official",
            "video_source",
            "channel_name",
            "channel_slug",
            "like_count",
            "favorite_count",
            "status",
            "created_at",
            "view_count",
            "published_at",
            "metric",
        }


class TestWeeklyViewsRankings:
    async def test_session_dedup_counts_each_session_once(self, auth_headers):
        """Anti-fraud rule: same session many plays = 1; distinct sessions add up;
        session-less events count individually ('row:'||id fallback)."""
        async with TestSessionLocal() as db:
            user = await _owner(db)
            hot = await _make_video(db, title="hot", owner_id=user.id)
            warm = await _make_video(db, title="warm", owner_id=user.id)
            cold = await _make_video(db, title="cold", owner_id=user.id)
            for _ in range(5):  # same session → 1
                await _event(db, video_id=hot.id, event_type="play", session_id="s-1", server_ts=_in_window(1))
            for s in ("s-2", "s-3", "s-4"):  # three distinct sessions → 3
                await _event(db, video_id=warm.id, event_type="complete", session_id=s, server_ts=_in_window(2))
            for _ in range(2):  # no session_id → each row counts → 2
                await _event(db, video_id=cold.id, event_type="play", session_id=None, server_ts=_in_window(3))
            items = await compute_rankings(db, "weekly_views")
        assert [i["id"] for i in items] == [warm.id, cold.id, hot.id]
        by_id = {i["id"]: i["metric"] for i in items}
        assert by_id[warm.id] == 3
        assert by_id[cold.id] == 2
        assert by_id[hot.id] == 1

    async def test_window_cutoff_excludes_events_before_this_week(self, auth_headers):
        """Calendar-week window: anything before Monday 00:00 CST is excluded,
        no matter how high its volume; events this week count."""
        async with TestSessionLocal() as db:
            user = await _owner(db)
            stale = await _make_video(db, title="stale", owner_id=user.id)
            fresh = await _make_video(db, title="fresh", owner_id=user.id)
            for _ in range(10):  # high volume but last week → out of window
                await _event(db, video_id=stale.id, event_type="play", session_id=None, server_ts=_before_window(1))
            await _event(db, video_id=fresh.id, event_type="play", session_id="s-9", server_ts=_in_window(1))
            items = await compute_rankings(db, "weekly_views")
        assert [i["id"] for i in items] == [fresh.id]
        assert items[0]["metric"] == 1

    async def test_only_play_and_complete_events_count(self, auth_headers):
        async with TestSessionLocal() as db:
            user = await _owner(db)
            clicked = await _make_video(db, title="clicked", owner_id=user.id)
            played = await _make_video(db, title="played", owner_id=user.id)
            for _ in range(4):
                await _event(db, video_id=clicked.id, event_type="click", session_id=None, server_ts=_in_window(1))
            await _event(db, video_id=played.id, event_type="play", session_id=None, server_ts=_in_window(2))
            items = await compute_rankings(db, "weekly_views")
        assert [i["id"] for i in items] == [played.id]

    async def test_visibility_join_excludes_hidden_videos(self, auth_headers):
        async with TestSessionLocal() as db:
            user = await _owner(db)
            hidden = await _make_video(db, title="hidden", is_published=False, owner_id=user.id)
            await _event(db, video_id=hidden.id, event_type="play", session_id=None, server_ts=_in_window(1))
            items = await compute_rankings(db, "weekly_views")
        assert items == []

    async def test_top_20_cap(self, auth_headers):
        async with TestSessionLocal() as db:
            user = await _owner(db)
            for i in range(25):
                v = await _make_video(db, title=f"v{i}", owner_id=user.id)
                for j in range(i + 1):  # distinct sessions → metric = i + 1
                    await _event(
                        db,
                        video_id=v.id,
                        event_type="play",
                        session_id=f"s-{v.id}-{j}",
                        server_ts=_in_window(1),
                    )
            items = await compute_rankings(db, "weekly_views")
        assert len(items) == 20
        metrics = [i["metric"] for i in items]
        assert metrics == sorted(metrics, reverse=True)
        assert metrics[0] == 25  # v24 with 25 plays leads


class TestWeeklyFavoritesRankings:
    async def test_counts_favorites_in_window_only(self, auth_headers):
        async with TestSessionLocal() as db:
            user = await _owner(db)
            other = await _make_user(db, "13800000021")
            hot = await _make_video(db, title="hot", owner_id=user.id)
            warm = await _make_video(db, title="warm", owner_id=user.id)
            cold = await _make_video(db, title="cold", owner_id=user.id)
            await _favorite(db, user_id=user.id, video_id=hot.id, created_at=_in_window(1))
            await _favorite(db, user_id=other.id, video_id=hot.id, created_at=_in_window(2))
            await _favorite(db, user_id=user.id, video_id=warm.id, created_at=_in_window(3))
            await _favorite(db, user_id=user.id, video_id=cold.id, created_at=_before_window(1))
            items = await compute_rankings(db, "weekly_favorites")
        assert [i["id"] for i in items] == [hot.id, warm.id]
        by_id = {i["id"]: i["metric"] for i in items}
        assert by_id[hot.id] == 2
        assert by_id[warm.id] == 1

    async def test_visibility_join_excludes_hidden_videos(self, auth_headers):
        async with TestSessionLocal() as db:
            user = await _owner(db)
            hidden = await _make_video(db, title="hidden", is_official=False, owner_id=user.id)
            await _favorite(db, user_id=user.id, video_id=hidden.id, created_at=_in_window(1))
            items = await compute_rankings(db, "weekly_favorites")
        assert items == []


class TestWeekBoundary:
    def test_week_start_is_monday_midnight_cst_for_any_day(self):
        """The window lower bound is always Monday 00:00 Asia/Shanghai, and the
        given instant lies within [week_start, week_start+7d)."""
        cst = timezone(timedelta(hours=8))
        anchor = datetime.now(UTC)
        for d in range(-7, 8):
            now = anchor + timedelta(days=d)
            ws = current_week_start_utc(now).astimezone(cst)
            assert ws.weekday() == 0  # Monday
            assert (ws.hour, ws.minute, ws.second, ws.microsecond) == (0, 0, 0, 0)
            now_cst = now.astimezone(cst)
            assert ws <= now_cst < ws + timedelta(days=7)


class TestSnapshotRankingsTask:
    async def test_writes_three_cache_keys_in_expected_shape(self, fake_redis, auth_headers):
        """Direct task-body call (conftest no-ops .delay): all three snapshot
        keys land in Redis with the ranking-item shape, TTL recorded."""
        now = datetime.now(UTC)
        async with TestSessionLocal() as db:
            user = await _owner(db)
            v = await _make_video(db, title="hot", published_at=now, owner_id=user.id)
            await _event(db, video_id=v.id, event_type="play", session_id="s-1", server_ts=now)
            await _favorite(db, user_id=user.id, video_id=v.id, created_at=now)

        snapshot_rankings()

        latest = await cache_get_json(rankings_cache_key("latest"))
        views = await cache_get_json(rankings_cache_key("weekly_views"))
        favs = await cache_get_json(rankings_cache_key("weekly_favorites"))
        for data in (latest, views, favs):
            assert isinstance(data, list) and len(data) == 1
            assert data[0]["id"] == v.id
            assert "metric" in data[0] and "published_at" in data[0] and "view_count" in data[0]
        assert latest[0]["metric"] is None  # latest scope carries no metric
        assert views[0]["metric"] == 1
        assert favs[0]["metric"] == 1
        for scope in RANKING_SCOPES:  # TTL recorded for every snapshot key
            assert rankings_cache_key(scope) in fake_redis._expires


class TestRankingsEndpoint:
    async def test_each_scope_returns_200_card_list(self, client, auth_headers):
        now = datetime.now(UTC)
        async with TestSessionLocal() as db:
            user = await _owner(db)
            v = await _make_video(db, title="v1", published_at=now, owner_id=user.id)
            await _event(db, video_id=v.id, event_type="play", session_id="s-1", server_ts=now)
            await _favorite(db, user_id=user.id, video_id=v.id, created_at=now)
        for scope in RANKING_SCOPES:
            resp = await client.get(f"/api/v1/videos/rankings?scope={scope}")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) == 1
            item = data[0]
            assert item["title"] == "v1"
            for key in (
                "id",
                "title",
                "thumbnail_url",
                "duration",
                "difficulty_level",
                "topic_tags",
                "is_official",
                "video_source",
                "channel_name",
                "channel_slug",
                "like_count",
                "favorite_count",
                "status",
                "created_at",
                "view_count",
                "published_at",
                "metric",
            ):
                assert key in item, f"{scope} item missing {key}"
        assert resp.json()[0]["metric"] == 1  # weekly_favorites (last scope) carries int metric

    async def test_default_scope_is_latest(self, client, auth_headers):
        async with TestSessionLocal() as db:
            user = await _owner(db)
            await _make_video(db, title="latest-v", published_at=datetime.now(UTC), owner_id=user.id)
        resp = await client.get("/api/v1/videos/rankings")
        assert resp.status_code == 200
        assert [i["title"] for i in resp.json()] == ["latest-v"]
        assert resp.json()[0]["metric"] is None

    async def test_invalid_scope_returns_422(self, client, auth_headers):
        resp = await client.get("/api/v1/videos/rankings?scope=bogus")
        assert resp.status_code == 422

    async def test_cache_hit_serves_snapshot_without_touching_db(self, client, fake_redis, auth_headers):
        """A snapshot written by one request is served by the next, DB or not.

        The payload is never spelled out by hand here — it is whatever
        ``ranking_service._serialize`` actually wrote on the first (cache-miss)
        request. That is deliberate: this test then cannot go stale when the
        card shape changes, so a shape change has to show up somewhere else
        (``tests/test_response_contract.py`` pins the shape itself).

        The play event is deleted between the two requests, so recomputing
        ``weekly_views`` would return an empty list. Getting the video back is
        proof the snapshot was read.
        """
        now = datetime.now(UTC)
        async with TestSessionLocal() as db:
            user = await _owner(db)
            v = await _make_video(db, title="cached-v", published_at=now, owner_id=user.id)
            await _event(db, video_id=v.id, event_type="play", session_id="s-cache", server_ts=now)

        first = await client.get("/api/v1/videos/rankings?scope=weekly_views")
        assert first.status_code == 200
        assert [i["title"] for i in first.json()] == ["cached-v"]

        async with TestSessionLocal() as db:
            await db.execute(delete(BehaviorEvent).where(BehaviorEvent.video_id == v.id))
            await db.commit()

        second = await client.get("/api/v1/videos/rankings?scope=weekly_views")
        assert second.status_code == 200
        assert second.json() == first.json()

    async def test_snapshot_written_before_the_shape_change_is_unreachable(self, client, fake_redis, auth_headers):
        """缓存键里带形状版本号 —— 这条测的是那个部署窗口。

        批 2 把四份手写卡片合并成一份 44 键形状。Redis 里还躺着按旧形状写的快照
        （rankings 的 TTL 是 48h），而路由现在拿 ``response_model`` 校验读到的
        dict：旧形状没有 ``source_url``，校验失败就是 500，不是「少几个字段」。
        所以旧键必须够不着 —— 版本号进键名，旧条目只能自然过期。
        """
        now = datetime.now(UTC)
        async with TestSessionLocal() as db:
            user = await _owner(db)
            await _make_video(db, title="real-v", published_at=now, owner_id=user.id)

        # 批 2 之前这个接口写出来的形状（17 键，没有 source_url）
        legacy = [
            {
                "id": "snap-1",
                "title": "from cache",
                "thumbnail_url": None,
                "duration": None,
                "difficulty_level": None,
                "topic_tags": None,
                "is_official": True,
                "video_source": "local",
                "channel_name": None,
                "channel_slug": None,
                "like_count": 0,
                "favorite_count": 0,
                "status": "ready",
                "created_at": "2026-09-19T00:00:00+00:00",
                "view_count": 0,
                "published_at": None,
                "metric": 7,
            }
        ]
        assert rankings_cache_key("latest") != "rankings:snapshot:latest"  # 版本号在位
        await cache_set_json("rankings:snapshot:latest", legacy, ttl=300)

        resp = await client.get("/api/v1/videos/rankings?scope=latest")
        assert resp.status_code == 200
        assert [i["title"] for i in resp.json()] == ["real-v"]
