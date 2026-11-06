"""Tests for the browse feed's sort values (GET /api/v1/browse/feed).

Covers the two favorites sorts the homepage filter bar needs (design doc §2.2):

- ``favorite`` — all-time ``Video.favorite_count``, the denormalized counter.
- ``weekly_favorite`` — favorites created since Monday 00:00 Asia/Shanghai, the
  same window ``/videos/rankings?scope=weekly_favorites`` uses, so the feed and
  the leaderboard cannot drift on what 「本周」 means.

Also pins the two properties the split task's acceptance calls out: pagination
stability of the new sorts (ties on the metric are constant, so the ordering
needs a unique last key) and the ``{sort}`` cache-key segment (the feed is
wrapped in ``@cached``, and a collision would serve one sort's order for the
other).

The pre-existing feed-sort tests (``hot`` ordering, 422 on an unknown value)
live in test_channels_api.py next to the channel-slug coverage; this file holds
the favorites coverage.
"""

from datetime import UTC, datetime, timedelta

from app.models.favorite import UserFavorite
from app.models.user import RoleType, User
from app.models.video import Video, VideoReviewStatus, VideoStatus
from app.services.ranking_service import current_week_start_utc
from app.services.video_card import CARD_SHAPE_VERSION

_FEED = "/api/v1/browse/feed"


def _in_window(hours: float = 1.0) -> datetime:
    """A timestamp inside the current calendar week (Monday 00:00 CST + hours)."""
    return current_week_start_utc() + timedelta(hours=hours)


def _before_window(hours: float = 1.0) -> datetime:
    """A timestamp just before this week started — excluded by the weekly sort."""
    return current_week_start_utc() - timedelta(hours=hours)


async def _make_user(db, phone: str) -> User:
    u = User(phone=phone, hashed_password="hashed", name="Feed Sort", role=RoleType.user)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


async def _make_users(db, count: int) -> list[User]:
    """``count`` distinct users in one commit (a favorite needs a distinct user)."""
    users = [
        User(
            phone=f"1380013{1000 + i}",
            hashed_password="hashed",
            name="Feed Sort",
            role=RoleType.user,
        )
        for i in range(count)
    ]
    db.add_all(users)
    await db.commit()
    for u in users:
        await db.refresh(u)
    return users


async def _make_video(
    db,
    *,
    title: str,
    created_at: datetime | None = None,
    favorite_count: int = 0,
    view_count: int = 0,
    status: VideoStatus = VideoStatus.ready,
    is_official: bool = True,
    is_published: bool = True,
    topic_tags: str = "tech",
    difficulty_level: str = "B1",
    duration: float = 120.0,
) -> Video:
    v = Video(
        title=title,
        source_url=f"https://feed.test/{title}",
        video_source="imported",
        status=status,
        is_official=is_official,
        is_published=is_published,
        review_status=VideoReviewStatus.published.value,
        topic_tags=topic_tags,
        difficulty_level=difficulty_level,
        duration=duration,
        favorite_count=favorite_count,
        view_count=view_count,
        video_url_720p=f"/media/{title}.mp4",
    )
    if created_at is not None:
        v.created_at = created_at
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v


def _favorite(db, *, user_id: str, video_id: str, created_at: datetime) -> None:
    """Queue a favorite (caller commits — the seeding loops add hundreds)."""
    db.add(UserFavorite(user_id=user_id, video_id=video_id, created_at=created_at))


def _ids(resp) -> list[str]:
    return [i["id"] for i in resp.json()["items"]]


class TestFavoriteSort:
    async def test_orders_by_all_time_favorite_count_desc(self, client, db_session):
        cold = await _make_video(db_session, title="cold", favorite_count=1)
        hot = await _make_video(db_session, title="hot", favorite_count=99)
        warm = await _make_video(db_session, title="warm", favorite_count=10)

        resp = await client.get(_FEED, params={"sort": "favorite", "page_size": 4})
        assert resp.status_code == 200
        assert _ids(resp) == [hot.id, warm.id, cold.id]
        assert resp.json()["total"] == 3

    async def test_composes_with_category_and_level_filters(self, client, db_session):
        await _make_video(db_session, title="biz", favorite_count=50, topic_tags="business")
        tech = await _make_video(db_session, title="tech", favorite_count=10, topic_tags="tech")
        sci = await _make_video(db_session, title="sci", favorite_count=5, topic_tags="science", difficulty_level="B2")

        resp = await client.get(_FEED, params={"sort": "favorite", "category": "tech"})
        assert resp.status_code == 200
        assert _ids(resp) == [tech.id]
        assert resp.json()["total"] == 1

        resp = await client.get(_FEED, params={"sort": "favorite", "category": "science", "level": "B2"})
        assert _ids(resp) == [sci.id]
        assert resp.json()["total"] == 1

        resp = await client.get(_FEED, params={"sort": "favorite", "category": "all"})
        assert [i["title"] for i in resp.json()["items"]] == ["biz", "tech", "sci"]


class TestWeeklyFavoriteSort:
    async def test_counts_only_favorites_created_this_week(self, client, db_session):
        """In-window favorites set the order; a video whose favorites are all from
        last week sorts with the empty ones — even though its denormalized
        ``favorite_count`` is the highest on the page (that is the difference
        between ``favorite`` and ``weekly_favorite``)."""
        users = await _make_users(db_session, 4)
        base = datetime(2026, 1, 1, tzinfo=UTC)
        hot = await _make_video(db_session, title="hot", created_at=base, favorite_count=2)
        warm = await _make_video(db_session, title="warm", created_at=base + timedelta(seconds=1), favorite_count=1)
        stale = await _make_video(db_session, title="stale", created_at=base + timedelta(seconds=2), favorite_count=50)
        idle = await _make_video(db_session, title="idle", created_at=base + timedelta(seconds=3), favorite_count=0)

        _favorite(db_session, user_id=users[0].id, video_id=hot.id, created_at=_in_window(1))
        _favorite(db_session, user_id=users[1].id, video_id=hot.id, created_at=_in_window(2))
        _favorite(db_session, user_id=users[2].id, video_id=warm.id, created_at=_in_window(3))
        for hours in (1, 2, 3):  # three favorites, all from last week
            _favorite(db_session, user_id=users[hours].id, video_id=stale.id, created_at=_before_window(hours))
        await db_session.commit()

        resp = await client.get(_FEED, params={"sort": "weekly_favorite", "page_size": 4})
        assert resp.status_code == 200
        assert _ids(resp) == [hot.id, warm.id, idle.id, stale.id]
        assert resp.json()["total"] == 4

    async def test_video_with_no_favorites_this_week_still_appears(self, client, db_session):
        """LEFT JOIN, not INNER: the feed is a browsable list, so the tail after
        the ranked videos must stay reachable."""
        users = await _make_users(db_session, 1)
        ranked = await _make_video(db_session, title="ranked")
        unranked = await _make_video(db_session, title="unranked")
        _favorite(db_session, user_id=users[0].id, video_id=ranked.id, created_at=_in_window(1))
        await db_session.commit()

        resp = await client.get(_FEED, params={"sort": "weekly_favorite"})
        assert _ids(resp) == [ranked.id, unranked.id]
        assert resp.json()["total"] == 2

    async def test_visibility_triple_excludes_hidden_videos(self, client, db_session):
        users = await _make_users(db_session, 1)
        hidden = [
            await _make_video(db_session, title="unpublished", is_published=False),
            await _make_video(db_session, title="ugc", is_official=False),
            await _make_video(db_session, title="processing", status=VideoStatus.processing),
        ]
        visible = await _make_video(db_session, title="visible")
        for v in [*hidden, visible]:
            _favorite(db_session, user_id=users[0].id, video_id=v.id, created_at=_in_window(1))
        await db_session.commit()

        resp = await client.get(_FEED, params={"sort": "weekly_favorite"})
        assert _ids(resp) == [visible.id]
        assert resp.json()["total"] == 1


class TestWeeklyFavoriteMatchesRankings:
    async def test_top_20_agrees_with_the_weekly_favorites_leaderboard(self, client, db_session):
        """The planner's acceptance: same instant, same window → the feed's first
        page and the leaderboard must list the same videos in the same order."""
        users = await _make_users(db_session, 21)
        base = datetime(2026, 1, 1, tzinfo=UTC)
        for i in range(21):  # video i gets i+1 favorites this week → distinct metrics
            v = await _make_video(db_session, title=f"v{i:02d}", created_at=base + timedelta(seconds=i))
            for u in users[: i + 1]:
                _favorite(db_session, user_id=u.id, video_id=v.id, created_at=_in_window(1))
        await db_session.commit()

        feed = await client.get(_FEED, params={"sort": "weekly_favorite", "page_size": 20})
        rankings = await client.get("/api/v1/videos/rankings?scope=weekly_favorites")
        assert feed.status_code == 200
        assert rankings.status_code == 200
        assert len(feed.json()["items"]) == 20
        assert _ids(feed) == [i["id"] for i in rankings.json()]
        assert feed.json()["total"] == 21  # the feed pages past the leaderboard's cap


class TestNewSortPagination:
    async def test_pages_do_not_repeat_or_skip_when_every_row_ties(self, client, db_session):
        """Ten videos sharing favorite_count *and* created_at: the ordering is
        decided entirely by the unique last key, and the three pages must
        reconstruct the full list exactly once."""
        same = datetime(2026, 1, 1, tzinfo=UTC)
        videos = [await _make_video(db_session, title=f"v{i}", created_at=same, favorite_count=5) for i in range(10)]
        expected = sorted((v.id for v in videos), reverse=True)

        seen: list[str] = []
        for page in (1, 2, 3):
            resp = await client.get(_FEED, params={"sort": "favorite", "page_size": 4, "page": page})
            assert resp.status_code == 200
            assert resp.json()["total"] == 10
            assert resp.json()["page"] == page
            seen += _ids(resp)

        assert seen == expected  # deterministic, no repeats, nothing dropped

    async def test_weekly_favorite_pages_do_not_repeat_or_skip(self, client, db_session):
        users = await _make_users(db_session, 2)
        same = datetime(2026, 1, 1, tzinfo=UTC)
        videos = [await _make_video(db_session, title=f"v{i}", created_at=same) for i in range(8)]
        for v in videos:
            _favorite(db_session, user_id=users[0].id, video_id=v.id, created_at=_in_window(1))
            _favorite(db_session, user_id=users[1].id, video_id=v.id, created_at=_in_window(2))
        await db_session.commit()

        seen: list[str] = []
        for page in (1, 2):
            resp = await client.get(_FEED, params={"sort": "weekly_favorite", "page_size": 4, "page": page})
            assert resp.json()["total"] == 8
            seen += _ids(resp)

        assert seen == sorted((v.id for v in videos), reverse=True)


class TestSortCacheKeys:
    async def test_sort_values_get_distinct_cache_entries(self, client, db_session, fake_redis):
        """``browse:feed:…:{sort}:…`` must keep the two favorites sorts apart —
        the same filters with a different sort must not serve the other's order."""
        users = await _make_users(db_session, 1)
        all_time = await _make_video(db_session, title="all-time", favorite_count=50)
        this_week = await _make_video(db_session, title="this-week", favorite_count=5)
        _favorite(db_session, user_id=users[0].id, video_id=this_week.id, created_at=_in_window(1))
        await db_session.commit()

        by_count = await client.get(_FEED, params={"sort": "favorite"})
        by_week = await client.get(_FEED, params={"sort": "weekly_favorite"})

        assert _ids(by_count) == [all_time.id, this_week.id]
        assert _ids(by_week) == [this_week.id, all_time.id]

        keys = set(fake_redis._store)
        # 键名带上卡片形状版本号，从常量拼出来，免得下次改形状时这里跟着一起改
        # （改形状就该换版本号，见 services/video_card.CARD_SHAPE_VERSION）。
        v = f"v{CARD_SHAPE_VERSION}"
        assert f"browse:feed:{v}:all:all:favorite:all:1:20" in keys
        assert f"browse:feed:{v}:all:all:weekly_favorite:all:1:20" in keys

    async def test_every_sort_value_returns_200(self, client, db_session):
        users = await _make_users(db_session, 1)
        v = await _make_video(db_session, title="v", favorite_count=1, view_count=1)
        _favorite(db_session, user_id=users[0].id, video_id=v.id, created_at=_in_window(1))
        await db_session.commit()

        for sort in ("latest", "hot", "favorite", "weekly_favorite"):
            resp = await client.get(_FEED, params={"sort": sort})
            assert resp.status_code == 200, sort
            assert _ids(resp) == [v.id], sort


class TestDurationFilter:
    async def test_duration_buckets_compose_with_filters(self, client, db_session):
        short = await _make_video(db_session, title="short", duration=120.0)
        medium = await _make_video(db_session, title="medium", duration=600.0)
        long = await _make_video(db_session, title="long", duration=1200.0)

        resp = await client.get(_FEED, params={"duration_max": 300})
        assert _ids(resp) == [short.id]

        resp = await client.get(_FEED, params={"duration_min": 301, "duration_max": 900})
        assert _ids(resp) == [medium.id]

        resp = await client.get(_FEED, params={"duration_min": 901})
        assert _ids(resp) == [long.id]

        resp = await client.get(_FEED, params={"duration_min": 301, "level": "B1", "sort": "hot"})
        assert resp.status_code == 200

    async def test_invalid_range_is_400(self, client):
        resp = await client.get(_FEED, params={"duration_min": 900, "duration_max": 300})
        assert resp.status_code == 400

    async def test_videos_without_duration_drop_out(self, client, db_session):
        no_duration = await _make_video(db_session, title="unknown", duration=0.0)
        no_duration.duration = None
        await db_session.commit()
        resp = await client.get(_FEED, params={"duration_min": 1})
        assert no_duration.id not in _ids(resp)
