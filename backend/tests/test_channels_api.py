"""Tests for the Channels API (ADR-0014, rev. 2026-08-30 full author pages)."""

from datetime import UTC, datetime

from app.models.channel import Channel
from app.models.learning import LearningRecord
from app.models.video import Video, VideoReviewStatus, VideoSource, VideoStatus
from app.services import channel_service
from app.services.channel_service import auto_attach_channel


async def _make_video(
    db, *, official=True, published=True, ready=True, channel_id=None, channel_name=None, channel_ref=None
) -> Video:
    video = Video(
        title="Channel Test Video",
        source_url="https://example.com/channel-test.mp4",
        video_source=VideoSource.imported,
        status=VideoStatus.ready if ready else VideoStatus.processing,
        review_status=VideoReviewStatus.published.value,
        is_official=official,
        is_published=published,
        channel_id=channel_id,
        channel_name=channel_name,
        channel_ref=channel_ref,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


async def _make_channel(db, **kw) -> Channel:
    defaults = dict(name="TED Talks", slug="ted-talks", sort_order=0, is_visible=True)
    defaults.update(kw)
    channel = Channel(**defaults)
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return channel


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


async def test_list_channels_shows_visible_only_with_counts(client, db_session):
    visible = await _make_channel(db_session, slug="visible-one", sort_order=1)
    await _make_channel(db_session, name="Hidden", slug="hidden-one", is_visible=False)
    await _make_video(db_session, channel_ref=visible.id)
    # Draft/unpublished videos must not count.
    await _make_video(db_session, channel_ref=visible.id, published=False)

    resp = await client.get("/api/v1/channels")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert [c["slug"] for c in items] == ["visible-one"]
    assert items[0]["video_count"] == 1


async def test_channel_detail_lists_published_videos(client, db_session):
    channel = await _make_channel(db_session, description="Curated talks")
    await _make_video(db_session, channel_ref=channel.id)
    await _make_video(db_session, channel_ref=channel.id, ready=False)  # not ready → excluded

    resp = await client.get(f"/api/v1/channels/{channel.slug}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["channel"]["slug"] == channel.slug
    assert data["channel"]["description"] == "Curated talks"
    assert data["videos"]["total"] == 1
    assert len(data["videos"]["items"]) == 1


async def test_channel_detail_unknown_slug_404(client):
    resp = await client.get("/api/v1/channels/does-not-exist")
    assert resp.status_code == 404


async def test_hidden_channel_detail_404(client, db_session):
    await _make_channel(db_session, slug="secret", is_visible=False)
    resp = await client.get("/api/v1/channels/secret")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


async def test_admin_create_channel_and_auto_attach_by_upstream_id(client, admin_headers, db_session):
    # Existing video scraped from an upstream channel, not yet curated.
    video = await _make_video(db_session, channel_id="UC12345")

    resp = await client.post(
        "/api/v1/channels/admin",
        json={"name": "TED", "slug": "ted", "upstream_channel_id": "UC12345"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    channel_id = resp.json()["id"]

    # Video auto-attached via upstream_channel_id match.
    await db_session.refresh(video)
    assert video.channel_ref == channel_id


async def test_admin_create_channel_slug_conflict_400(client, admin_headers, db_session):
    await _make_channel(db_session, slug="taken")
    resp = await client.post("/api/v1/channels/admin", json={"name": "Other", "slug": "taken"}, headers=admin_headers)
    assert resp.status_code == 400


async def test_admin_create_channel_invalid_slug_400(client, admin_headers):
    resp = await client.post(
        "/api/v1/channels/admin", json={"name": "Bad", "slug": "Not A Slug!"}, headers=admin_headers
    )
    assert resp.status_code == 400


async def test_admin_requires_admin_role(client, auth_headers):
    resp = await client.post("/api/v1/channels/admin", json={"name": "X"}, headers=auth_headers)
    assert resp.status_code == 403


async def test_admin_update_and_delete_channel(client, admin_headers, db_session):
    channel = await _make_channel(db_session)
    resp = await client.patch(
        f"/api/v1/channels/admin/{channel.id}",
        json={"name": "TED Talks 精选", "sort_order": 5, "is_visible": False},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "TED Talks 精选"
    await db_session.refresh(channel)
    assert channel.sort_order == 5
    assert channel.is_visible is False

    resp = await client.delete(f"/api/v1/channels/admin/{channel.id}", headers=admin_headers)
    assert resp.status_code == 204
    resp = await client.delete(f"/api/v1/channels/admin/{channel.id}", headers=admin_headers)
    assert resp.status_code == 404


async def test_admin_attach_videos_overwrites_assignment(client, admin_headers, db_session):
    a = await _make_channel(db_session, slug="chan-a")
    b = await _make_channel(db_session, slug="chan-b")
    video = await _make_video(db_session, channel_ref=a.id)

    resp = await client.post(
        f"/api/v1/channels/admin/{b.id}/videos",
        json={"video_ids": [video.id]},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["attached"] == 1
    await db_session.refresh(video)
    assert video.channel_ref == b.id


async def test_admin_attach_videos_reports_missing_and_only_counts_real_changes(client, admin_headers, db_session):
    """ADM-19: `attached` used to be the matched-row count (already-attached ids
    included) and nonexistent ids were silently dropped."""
    target = await _make_channel(db_session, slug="attach-target")
    other = await _make_channel(db_session, slug="attach-other")
    already = await _make_video(db_session, channel_ref=target.id)
    moved = await _make_video(db_session, channel_ref=other.id)

    resp = await client.post(
        f"/api/v1/channels/admin/{target.id}/videos",
        json={"video_ids": [already.id, moved.id, moved.id, "no-such-video"]},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    # Only `moved` actually changed; the duplicate id is de-duped and the
    # missing one is reported back instead of being ignored.
    assert resp.json() == {"attached": 1, "missing_ids": ["no-such-video"]}
    await db_session.refresh(moved)
    assert moved.channel_ref == target.id
    await db_session.refresh(already)
    assert already.channel_ref == target.id


async def test_admin_attach_videos_rejects_unbounded_batch(client, admin_headers, db_session):
    channel = await _make_channel(db_session, slug="attach-big")
    resp = await client.post(
        f"/api/v1/channels/admin/{channel.id}/videos",
        json={"video_ids": [f"video-{i}" for i in range(201)]},
        headers=admin_headers,
    )
    assert resp.status_code == 422


async def test_admin_create_channel_slug_race_returns_400_not_500(client, admin_headers, db_session, monkeypatch):
    """Two admins POST the same slug at once: both pass the pre-check, the loser
    hits the unique index. That must be a readable 400, not the 500 envelope."""
    await _make_channel(db_session, slug="raced-slug")

    async def _always_free(db, slug, *, exclude_id=None):
        return False

    monkeypatch.setattr(channel_service, "_slug_exists", _always_free)
    resp = await client.post(
        "/api/v1/channels/admin", json={"name": "Race", "slug": "raced-slug"}, headers=admin_headers
    )
    assert resp.status_code == 400, resp.text
    body = resp.json()
    assert body["code"] == "BAD_REQUEST"
    assert "slug 已存在" in body["message"]


async def test_admin_update_channel_slug_race_returns_400_not_500(client, admin_headers, db_session, monkeypatch):
    first = await _make_channel(db_session, slug="race-alpha")
    await _make_channel(db_session, slug="race-beta")

    async def _always_free(db, slug, *, exclude_id=None):
        return False

    monkeypatch.setattr(channel_service, "_slug_exists", _always_free)
    resp = await client.patch(f"/api/v1/channels/admin/{first.id}", json={"slug": "race-beta"}, headers=admin_headers)
    assert resp.status_code == 400, resp.text
    assert "slug 已存在" in resp.json()["message"]


async def test_admin_video_patch_sets_channel_ref(client, admin_headers, db_session):
    channel = await _make_channel(db_session)
    video = await _make_video(db_session)

    resp = await client.patch(
        f"/api/v1/videos/admin/{video.id}",
        json={"channel_ref": channel.id},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["channel_ref"] == channel.id

    # Empty string clears the assignment.
    resp = await client.patch(
        f"/api/v1/videos/admin/{video.id}",
        json={"channel_ref": ""},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["channel_ref"] is None


# ---------------------------------------------------------------------------
# Full author pages (ADR-0014 rev. 2026-08-30): auto-creation at ingest
# ---------------------------------------------------------------------------


async def test_auto_attach_creates_channel_for_unknown_upstream(db_session):
    video = await _make_video(db_session, channel_id="UCabc123", channel_name="某中文频道")

    await auto_attach_channel(db_session, video)
    await db_session.commit()

    assert video.channel_ref is not None
    channel = await db_session.get(Channel, video.channel_ref)
    assert channel is not None
    assert channel.is_auto is True
    assert channel.is_visible is True
    assert channel.name == "某中文频道"
    assert channel.upstream_channel_id == "UCabc123"
    # Chinese display name has no ASCII slug -> lowercased upstream id.
    assert channel.slug == "ucabc123"


async def test_auto_attach_ascii_name_slugifies(db_session):
    video = await _make_video(db_session, channel_id="UCxyz789", channel_name="TED Talks")

    await auto_attach_channel(db_session, video)
    await db_session.commit()

    channel = await db_session.get(Channel, video.channel_ref)
    assert channel.slug == "ted-talks"


async def test_auto_attach_slug_conflict_falls_back_to_upstream(db_session):
    # An unrelated curated channel already owns the slug an auto channel would want.
    await _make_channel(db_session, name="TED Talks 精选", slug="ted-talks")
    video = await _make_video(db_session, channel_id="UCxyz789", channel_name="TED Talks")

    await auto_attach_channel(db_session, video)
    await db_session.commit()

    channel = await db_session.get(Channel, video.channel_ref)
    assert channel.slug == "ucxyz789"


async def test_auto_attach_registered_channel_wins(db_session):
    curated = await _make_channel(db_session, name="TED", slug="ted", upstream_channel_id="UC12345")
    video = await _make_video(db_session, channel_id="UC12345", channel_name="TED")

    await auto_attach_channel(db_session, video)
    await db_session.commit()

    assert video.channel_ref == curated.id
    # No duplicate auto channel was created.
    from sqlalchemy import select

    assert len(list((await db_session.execute(select(Channel))).scalars())) == 1


async def test_auto_attach_noop_without_channel_id_or_when_attached(db_session):
    local_video = await _make_video(db_session, channel_id=None)
    await auto_attach_channel(db_session, local_video)
    assert local_video.channel_ref is None

    channel = await _make_channel(db_session)
    attached = await _make_video(db_session, channel_id="UC1", channel_ref=channel.id)
    await auto_attach_channel(db_session, attached)
    assert attached.channel_ref == channel.id


# ---------------------------------------------------------------------------
# Public list: ordering / empty-channel hiding / pagination / cover fallback
# ---------------------------------------------------------------------------


async def test_list_channels_curated_first_then_auto_by_count(client, db_session):
    await _make_channel(db_session, name="Empty curated", slug="empty-curated")  # no videos -> hidden
    curated = await _make_channel(db_session, name="Curated", slug="curated", sort_order=5)
    await _make_video(db_session, channel_ref=curated.id)

    small_auto = Channel(name="Small Author", slug="small-author", upstream_channel_id="UCsmall", is_auto=True)
    big_auto = Channel(name="Big Author", slug="big-author", upstream_channel_id="UCbig", is_auto=True)
    db_session.add_all([small_auto, big_auto])
    await db_session.commit()
    await _make_video(db_session, channel_id="UCbig", channel_ref=big_auto.id)
    await _make_video(db_session, channel_id="UCbig", channel_ref=big_auto.id)
    await _make_video(db_session, channel_id="UCsmall", channel_ref=small_auto.id)

    resp = await client.get("/api/v1/channels")
    assert resp.status_code == 200
    data = resp.json()
    slugs = [c["slug"] for c in data["items"]]
    # Curated leads regardless of count; auto rows follow by video count desc.
    assert slugs == ["curated", "big-author", "small-author"]
    assert data["total"] == 3
    assert data["has_more"] is False


async def test_list_channels_paginated(client, db_session):
    for i in range(5):
        ch = Channel(name=f"Author {i}", slug=f"author-{i}", upstream_channel_id=f"UC{i}", is_auto=True)
        db_session.add(ch)
        await db_session.flush()
        await _make_video(db_session, channel_id=f"UC{i}", channel_ref=ch.id)

    resp = await client.get("/api/v1/channels?page=1&page_size=4")
    data = resp.json()
    assert len(data["items"]) == 4
    assert data["has_more"] is True

    resp = await client.get("/api/v1/channels?page=2&page_size=4")
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["has_more"] is False


async def test_channel_detail_cover_falls_back_to_newest_video(client, db_session):
    from datetime import UTC, datetime, timedelta

    auto = Channel(name="Author", slug="author", upstream_channel_id="UCx", is_auto=True)
    db_session.add(auto)
    await db_session.commit()
    v1 = await _make_video(db_session, channel_id="UCx", channel_ref=auto.id)
    v1.thumbnail_url = "/media/old.jpg"
    v1.created_at = datetime.now(UTC) - timedelta(hours=1)
    v2 = await _make_video(db_session, channel_id="UCx", channel_ref=auto.id)
    v2.thumbnail_url = "/media/new.jpg"
    await db_session.commit()

    resp = await client.get("/api/v1/channels/author")
    assert resp.status_code == 200
    # Cover fallback = newest public video's thumbnail (cover_url itself empty).
    assert resp.json()["channel"]["cover_url"] == "/media/new.jpg"


async def test_channel_detail_carries_upstream_stats(client, db_session):
    """Author-page header data: follower count + verified flag from the newest
    video's scraped external_meta (snapshot at ingest time)."""
    auto = Channel(name="CNBC", slug="cnbc", upstream_channel_id="UCcn", is_auto=True)
    db_session.add(auto)
    await db_session.commit()
    v = await _make_video(db_session, channel_id="UCcn", channel_ref=auto.id)
    v.external_meta = {"channel": {"follower_count": 12_300_000, "is_verified": True}}
    await db_session.commit()

    resp = await client.get("/api/v1/channels/cnbc")
    assert resp.status_code == 200
    ch = resp.json()["channel"]
    assert ch["follower_count"] == 12_300_000
    assert ch["is_verified"] is True


async def test_channel_detail_upstream_stats_null_without_meta(client, db_session):
    channel = await _make_channel(db_session, slug="plain")
    await _make_video(db_session, channel_ref=channel.id)

    resp = await client.get("/api/v1/channels/plain")
    assert resp.status_code == 200
    ch = resp.json()["channel"]
    assert ch["follower_count"] is None
    assert ch["is_verified"] is None


async def test_browse_feed_items_carry_channel_name_and_slug(client, db_session):
    channel = await _make_channel(db_session, name="TED", slug="ted", upstream_channel_id="UC12345")
    video = await _make_video(db_session, channel_id="UC12345", channel_name="TED", channel_ref=channel.id)

    resp = await client.get("/api/v1/browse/feed")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "feed should contain the published video"
    item = next(i for i in items if i["id"] == video.id)
    assert item["channel_name"] == "TED"
    assert item["channel_slug"] == "ted"


async def test_browse_feed_sort_hot_orders_by_view_count(client, db_session):
    cold = await _make_video(db_session)
    cold.view_count = 1
    warm = await _make_video(db_session)
    warm.view_count = 10
    hot = await _make_video(db_session)
    hot.view_count = 99
    db_session.add_all([cold, warm, hot])
    await db_session.commit()

    resp = await client.get("/api/v1/browse/feed", params={"sort": "hot"})
    assert resp.status_code == 200
    ids = [v["id"] for v in resp.json()["items"]]
    pos = {vid: ids.index(vid) for vid in (cold.id, warm.id, hot.id)}
    assert pos[hot.id] < pos[warm.id] < pos[cold.id]


async def test_browse_feed_rejects_unknown_sort(client, db_session):
    resp = await client.get("/api/v1/browse/feed", params={"sort": "bogus"})
    assert resp.status_code == 422


async def test_home_feed_items_carry_channel_slug(client, db_session):
    channel = await _make_channel(db_session, name="TED", slug="ted", upstream_channel_id="UC12345")
    video = await _make_video(db_session, channel_id="UC12345", channel_ref=channel.id)
    await db_session.commit()

    resp = await client.get("/api/v1/recommendations/home")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert items, "home feed should contain the published video"
    item = next(i for i in items if i["id"] == video.id)
    assert item["channel_slug"] == "ted"


async def test_video_detail_carries_channel_name_and_slug(client, db_session):
    channel = await _make_channel(db_session, name="TED", slug="ted", upstream_channel_id="UC12345")
    video = await _make_video(db_session, channel_id="UC12345", channel_name="TED", channel_ref=channel.id)

    resp = await client.get(f"/api/v1/videos/{video.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["channel_name"] == "TED"
    assert data["channel_slug"] == "ted"


async def test_admin_list_channels_marks_is_auto(client, admin_headers, db_session):
    await _make_channel(db_session, name="Curated", slug="curated")
    auto = Channel(name="Author", slug="author", upstream_channel_id="UCx", is_auto=True)
    db_session.add(auto)
    await db_session.commit()

    resp = await client.get("/api/v1/channels/admin/all", headers=admin_headers)
    assert resp.status_code == 200
    by_slug = {c["slug"]: c for c in resp.json()["items"]}
    assert by_slug["curated"]["is_auto"] is False
    assert by_slug["author"]["is_auto"] is True


# ---------------------------------------------------------------------------
# Cache invalidation: feed cards and video detail embed the author-page link
# (`channel_slug`/`channel_name`), so a channel rename or delete must drop them
# — otherwise the stale link survives the TTL (browse 5min, rankings snapshot up
# to 48h) and points at a renamed or 404'd author page. Fail-open invalidation
# silently no-ops when the test double lacks the Redis command it calls, so the
# fake in conftest.py must implement every command production invalidation uses.
# ---------------------------------------------------------------------------


async def _warm_author_link_caches(client, headers, video, expected_slug: str) -> None:
    """Read the two caches that carry the author-page link (browse feed card +
    video detail). The detail cache is only written for a `can_watch` reader, so
    a logged-in user's headers are required for it to be warmed."""
    feed = await client.get("/api/v1/browse/feed")
    item = next(i for i in feed.json()["items"] if i["id"] == video.id)
    assert item["channel_slug"] == expected_slug

    detail = await client.get(f"/api/v1/videos/{video.id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["channel_slug"] == expected_slug


async def test_admin_update_channel_invalidates_author_link_caches(
    client, admin_headers, auth_headers, db_session, fake_redis
):
    channel = await _make_channel(db_session, name="TED", slug="ted")
    video = await _make_video(db_session, channel_ref=channel.id)
    await _warm_author_link_caches(client, auth_headers, video, "ted")
    assert f"video:detail:{video.id}" in fake_redis._store
    assert any(k.startswith("browse:feed:") for k in fake_redis._store)

    resp = await client.patch(
        f"/api/v1/channels/admin/{channel.id}",
        json={"name": "TED 精选", "slug": "ted-selected"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # The rename must drop both caches the stale link is served from.
    assert not any(k.startswith("browse:feed:") for k in fake_redis._store)
    assert f"video:detail:{video.id}" not in fake_redis._store

    feed = await client.get("/api/v1/browse/feed")
    item = next(i for i in feed.json()["items"] if i["id"] == video.id)
    assert item["channel_slug"] == "ted-selected"


async def test_admin_delete_channel_invalidates_author_link_caches(
    client, admin_headers, auth_headers, db_session, fake_redis, monkeypatch
):
    channel = await _make_channel(db_session, name="TED", slug="ted")
    video = await _make_video(db_session, channel_ref=channel.id)
    await _warm_author_link_caches(client, auth_headers, video, "ted")
    assert f"video:detail:{video.id}" in fake_redis._store

    # Postgres nulls videos.channel_ref as part of the DELETE (FK SET NULL); the
    # in-memory SQLite suite does not enforce that FK, so reproduce it here. With
    # the nulling in place, collecting the affected ids *after* the delete finds
    # nothing and the member video's detail cache keeps the dead link.
    from sqlalchemy import update

    real_delete = channel_service.delete_channel

    async def _delete_with_fk_set_null(db, channel_id):
        await db.execute(update(Video).where(Video.channel_ref == channel_id).values(channel_ref=None))
        return await real_delete(db, channel_id)

    monkeypatch.setattr(channel_service, "delete_channel", _delete_with_fk_set_null)

    resp = await client.delete(f"/api/v1/channels/admin/{channel.id}", headers=admin_headers)
    assert resp.status_code == 204

    assert not any(k.startswith("browse:feed:") for k in fake_redis._store)
    assert f"video:detail:{video.id}" not in fake_redis._store

    feed = await client.get("/api/v1/browse/feed")
    item = next(i for i in feed.json()["items"] if i["id"] == video.id)
    assert item["channel_slug"] is None


async def test_admin_video_patch_channel_ref_invalidates_browse_cache_only_on_change(client, admin_headers, db_session):
    """Changing ``channel_ref`` rewrites the author link embedded in the cached
    feed cards, so it must drop the browse caches — while an unrelated edit or a
    no-op re-send must not (invalidation is a full-scan delete)."""
    from unittest.mock import AsyncMock, patch

    channel = await _make_channel(db_session, slug="new-author")
    video = await _make_video(db_session)

    with patch("app.services.video_cache.invalidate_browse_cache", new=AsyncMock()) as invalidate:

        async def _patch(body: dict) -> None:
            resp = await client.patch(f"/api/v1/videos/admin/{video.id}", json=body, headers=admin_headers)
            assert resp.status_code == 200

        # Unrelated field: the cached cards are unchanged, so leave them alone.
        await _patch({"admin_notes": "internal note"})
        # Clearing an already-empty channel_ref normalizes to None -> no change.
        await _patch({"channel_ref": ""})
        invalidate.assert_not_awaited()

        # A title edit rewrites the text inside every cached card -> invalidate.
        await _patch({"title": "Renamed"})
        invalidate.assert_awaited_once()

        # A real assignment changes the cached author link -> invalidate again.
        await _patch({"channel_ref": channel.id})
        assert invalidate.await_count == 2

        # Re-sending the same value is a no-op (idempotent PATCH).
        await _patch({"channel_ref": channel.id})
        assert invalidate.await_count == 2


# ---------------------------------------------------------------------------
# Learning facts (2026-10 频道改版): position / directions / difficulty / start
# ---------------------------------------------------------------------------


async def test_channel_list_exposes_content_learning_facts(client, db_session):
    channel = await _make_channel(db_session, name="Rachel's English", slug="rachel-s-english")
    video = await _make_video(db_session, channel_ref=channel.id)
    video.title = "How to Pronounce SEX vs. SIX - American English"
    video.difficulty_level = "B2"
    # The old classifier put a wrong news tag on a pronunciation lesson;
    # the curated profile is authoritative for this channel.
    video.topic_tags = "news"
    await db_session.commit()

    resp = await client.get("/api/v1/channels")
    assert resp.status_code == 200
    item = next(c for c in resp.json()["items"] if c["slug"] == channel.slug)
    assert item["positioning_zh"] == "美式发音与口语训练"
    assert item["learning_directions"] == [{"id": "pronunciation", "label": "发音"}]
    assert item["difficulty_range"] == {"min": "B2", "max": "B2"}
    assert item["accent_label"] == "美式发音"
    assert item["video_titles"] == ["How to Pronounce SEX vs. SIX - American English"]
    assert item["latest_video"]["difficulty_level"] == "B2"


async def test_channel_detail_recommends_lowest_difficulty_and_falls_back_to_latest(client, db_session):
    channel = await _make_channel(db_session, slug="plain-start")
    hard = await _make_video(db_session, channel_ref=channel.id)
    hard.title = "Hard one"
    hard.difficulty_level = "B2"
    hard.duration = 100
    easy = await _make_video(db_session, channel_ref=channel.id)
    easy.title = "Easy one"
    easy.difficulty_level = "A2"
    easy.duration = 300
    await db_session.commit()

    data = (await client.get(f"/api/v1/channels/{channel.slug}")).json()
    assert data["channel"]["difficulty_range"] == {"min": "A2", "max": "B2"}
    assert data["recommended_start"]["basis"] == "lowest_difficulty"
    assert data["recommended_start"]["video"]["id"] == easy.id
    assert data["recommended_start"]["video"]["difficulty_level"] == "A2"

    no_level = await _make_channel(db_session, slug="plain-no-level")
    await _make_video(db_session, channel_ref=no_level.id)
    fallback = (await client.get(f"/api/v1/channels/{no_level.slug}")).json()
    assert fallback["channel"]["difficulty_range"] is None
    assert fallback["recommended_start"]["basis"] == "latest"
    assert fallback["recommended_start"]["video"]["id"] is not None


async def test_subscriptions_carry_continue_video_and_unlearned_count(client, auth_headers, db_session):
    uid = (await client.get("/api/v1/users/me", headers=auth_headers)).json()["id"]
    channel = await _make_channel(db_session, name="Sub Author", slug="sub-author")
    started = await _make_video(db_session, channel_ref=channel.id)
    started.title = "Started lesson"
    started.duration = 300
    started.difficulty_level = "A2"
    # Explicit timestamps: the "latest" query orders by created_at, and two
    # rows created in the same clock tick would fall back to a random UUID tie.
    started.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    untouched = await _make_video(db_session, channel_ref=channel.id)
    untouched.title = "Untouched lesson"
    untouched.duration = 200
    untouched.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    db_session.add(
        LearningRecord(
            user_id=uid,
            video_id=started.id,
            words_learned=0,
            speaking_attempts=0,
            completed=False,
            time_spent_seconds=60,
            progress_percentage=40.5,
            position_seconds=121.5,
        )
    )
    await db_session.commit()
    assert (
        await client.put(f"/api/v1/discovery/subscriptions/{channel.slug}", headers=auth_headers)
    ).status_code == 200

    rows = (await client.get("/api/v1/discovery/subscriptions", headers=auth_headers)).json()
    row = next(item for item in rows if item["slug"] == channel.slug)
    assert row["video_count"] == 2
    assert row["latest_video"]["title"] == "Untouched lesson"
    assert row["continue_video"]["title"] == "Started lesson"
    assert row["continue_video"]["progress_percentage"] == 40.5
    assert row["continue_video"]["position_seconds"] == 121.5
    assert row["unlearned_count"] == 1


async def test_channel_subscription_state_is_viewer_scoped(client, db_session, auth_headers):
    from app.models.user_content import ChannelSubscription

    me = (await client.get("/api/v1/users/me", headers=auth_headers)).json()
    channel = await _make_channel(db_session, name="Subscribed", slug="subscribed-one")
    await _make_video(db_session, channel_ref=channel.id)
    db_session.add(ChannelSubscription(user_id=me["id"], channel_id=channel.id))
    await db_session.commit()

    anonymous = (await client.get("/api/v1/channels")).json()["items"][0]
    assert anonymous["is_subscribed"] is False
    # Subscriber count is public; only the viewer-specific flag changes.
    assert anonymous["subscriber_count"] == 1

    signed_in = (await client.get("/api/v1/channels", headers=auth_headers)).json()["items"][0]
    assert signed_in["is_subscribed"] is True
    assert signed_in["subscriber_count"] == 1

    detail = (await client.get(f"/api/v1/channels/{channel.slug}", headers=auth_headers)).json()["channel"]
    assert detail["is_subscribed"] is True
    assert detail["subscriber_count"] == 1
    assert "latest_published_at" in detail
    assert "recent_video_count" in detail
