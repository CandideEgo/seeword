"""Tests for video endpoints."""

from httpx import AsyncClient


class TestPublicVideos:
    async def test_list_public_videos(self, client: AsyncClient):
        resp = await client.get("/api/v1/videos/public")
        assert resp.status_code == 200
        data = resp.json()
        # Paginated response shape: {items, page, page_size, has_more}
        assert isinstance(data, dict)
        assert "items" in data
        assert isinstance(data["items"], list)


class TestSeedVideo:
    async def test_seed_requires_admin(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/videos/seed",
            headers=auth_headers,
            json={"source_url": "https://www.youtube.com/watch?v=abcdefghijk"},
        )
        assert resp.status_code == 403  # regular user cannot seed

    async def test_seed_as_admin_succeeds(self, client: AsyncClient, admin_headers: dict):
        resp = await client.post(
            "/api/v1/videos/seed",
            headers=admin_headers,
            json={"source_url": "https://www.youtube.com/watch?v=abcdefghijk"},
        )
        assert resp.status_code == 201
        assert resp.json()["is_official"] is True


class TestGetVideo:
    async def test_get_nonexistent_video_returns_404(self, client: AsyncClient):
        resp = await client.get("/api/v1/videos/nonexistent-id")
        assert resp.status_code == 404


# The old ``GET /videos/{id}/quiz`` route and this module's TestVideoQuiz class
# are gone: the route was removed with the legacy per-video quiz feature. The
# class that used to live here asserted a 404 for that path, which any
# nonexistent URL satisfies — it could never fail, so it protected nothing.


# ---------------------------------------------------------------------------
# Admin video content management
# ---------------------------------------------------------------------------


async def _seed_video_rows(db, *, count=1, status="ready", is_official=True, is_featured=False, title=None):
    """Insert Video rows directly for admin-list tests."""
    from app.models.video import Video, VideoStatus

    videos = []
    for i in range(count):
        v = Video(
            title=title or f"Admin Test {i}",
            source_url=f"https://www.youtube.com/watch?v=vidid{i:06d}",
            video_source="imported",
            status=VideoStatus(status),
            is_official=is_official,
            is_featured=is_featured,
            video_url_720p=f"/media/vidid{i}.mp4" if status == "ready" else None,
        )
        db.add(v)
        videos.append(v)
    await db.commit()
    for v in videos:
        await db.refresh(v)
    return videos


class TestAdminListVideos:
    async def test_list_requires_admin(self, client: AsyncClient, auth_headers: dict):
        # Regular user is forbidden.
        resp = await client.get("/api/v1/videos/admin", headers=auth_headers)
        assert resp.status_code == 403

    async def test_list_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/videos/admin")
        assert resp.status_code == 401

    async def test_admin_lists_all_videos(self, client: AsyncClient, admin_headers: dict, db_session):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            await _seed_video_rows(db, count=3)

        resp = await client.get("/api/v1/videos/admin", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert "items" in data and "has_more" in data
        assert len(data["items"]) >= 3
        # Admin response exposes featured/notes/error/progress fields.
        item = data["items"][0]
        assert "is_featured" in item
        assert "admin_notes" in item
        assert "processing_progress" in item

    async def test_status_filter(self, client: AsyncClient, admin_headers: dict):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            await _seed_video_rows(db, count=2, status="processing", title="Proc")
            await _seed_video_rows(db, count=1, status="ready", title="Ready")

        resp = await client.get("/api/v1/videos/admin?status=processing", headers=admin_headers)
        assert resp.status_code == 200
        assert all(v["status"] == "processing" for v in resp.json()["items"])

    async def test_pagination_has_more(self, client: AsyncClient, admin_headers: dict):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            await _seed_video_rows(db, count=5)

        resp = await client.get("/api/v1/videos/admin?page=1&page_size=2", headers=admin_headers)
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["has_more"] is True

    async def test_list_reports_real_total(self, client: AsyncClient, admin_headers: dict):
        """ADM-10: the service already counted rows but never passed ``total`` on."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            await _seed_video_rows(db, count=3)

        resp = await client.get("/api/v1/videos/admin?page=1&page_size=2", headers=admin_headers)
        data = resp.json()
        assert data["total"] == 3
        assert data["has_more"] is True
        assert len(data["items"]) == 2

    async def test_list_order_has_id_tiebreaker(self, client: AsyncClient, admin_headers: dict):
        """Bulk-imported videos often share ``created_at``; OFFSET paging over a
        single timestamp column can then repeat or skip rows."""
        from datetime import UTC, datetime

        from tests.conftest import TestSessionLocal

        stamp = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
        async with TestSessionLocal() as db:
            videos = await _seed_video_rows(db, count=3)
            for video in videos:
                video.created_at = stamp
            await db.commit()
            seeded_ids = {video.id for video in videos}

        page1 = (await client.get("/api/v1/videos/admin?page=1&page_size=2", headers=admin_headers)).json()
        page2 = (await client.get("/api/v1/videos/admin?page=2&page_size=2", headers=admin_headers)).json()
        assert page1["total"] == page2["total"] == 3
        seen = [item["id"] for item in page1["items"] + page2["items"]]
        assert len(seen) == len(set(seen)) == 3
        assert set(seen) == seeded_ids


class TestAdminUpdateVideo:
    async def test_update_requires_admin(self, client: AsyncClient, auth_headers: dict, db_session):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1)

        resp = await client.patch(
            f"/api/v1/videos/admin/{v.id}",
            headers=auth_headers,
            json={"title": "New Title"},
        )
        assert resp.status_code == 403

    async def test_update_metadata(self, client: AsyncClient, admin_headers: dict):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1)

        resp = await client.patch(
            f"/api/v1/videos/admin/{v.id}",
            headers=admin_headers,
            json={"title": "Updated Title", "difficulty_level": "b2", "is_featured": True, "admin_notes": "note"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Title"
        assert data["difficulty_level"] == "B2"
        assert data["is_featured"] is True
        assert data["admin_notes"] == "note"

    async def test_update_title_zh_and_clear(self, client: AsyncClient, admin_headers: dict):
        """title_zh is editable; an empty string clears it for a re-translate."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1)

        resp = await client.patch(
            f"/api/v1/videos/admin/{v.id}",
            headers=admin_headers,
            json={"title_zh": "  如何成为好的倾听者  "},
        )
        assert resp.status_code == 200
        assert resp.json()["title_zh"] == "如何成为好的倾听者"

        resp = await client.patch(
            f"/api/v1/videos/admin/{v.id}",
            headers=admin_headers,
            json={"title_zh": ""},
        )
        assert resp.status_code == 200
        assert resp.json()["title_zh"] is None

    async def test_update_invalid_difficulty(self, client: AsyncClient, admin_headers: dict):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1)

        resp = await client.patch(
            f"/api/v1/videos/admin/{v.id}",
            headers=admin_headers,
            json={"difficulty_level": "X9"},
        )
        assert resp.status_code == 422

    async def test_update_nonexistent(self, client: AsyncClient, admin_headers: dict):
        resp = await client.patch(
            "/api/v1/videos/admin/nope",
            headers=admin_headers,
            json={"title": "x"},
        )
        assert resp.status_code == 404


class TestPublishGate:
    """is_published separates official source attribution from public visibility."""

    async def test_seed_creates_draft(self, client: AsyncClient, admin_headers: dict):
        """Newly seeded official videos are drafts — not yet published."""
        resp = await client.post(
            "/api/v1/videos/seed",
            headers=admin_headers,
            json={"source_url": "https://www.youtube.com/watch?v=seeddraft001"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["is_official"] is True
        assert data["is_published"] is False

    async def test_publish_requires_ready_status(self, client: AsyncClient, admin_headers: dict):
        """A non-ready video cannot be published (400, not 200)."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1, status="processing")

        resp = await client.patch(
            f"/api/v1/videos/admin/{v.id}",
            headers=admin_headers,
            json={"is_published": True},
        )
        assert resp.status_code == 400

    async def test_publish_ready_video_then_visible_on_homepage(self, client: AsyncClient, admin_headers: dict):
        """A published ready video appears on the public homepage; an unpublished one doesn't."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (published,) = await _seed_video_rows(db, count=1, title="Published")
            await _seed_video_rows(db, count=1, title="Draft")

        # Publish one of them.
        resp = await client.patch(
            f"/api/v1/videos/admin/{published.id}",
            headers=admin_headers,
            json={"is_published": True},
        )
        assert resp.status_code == 200
        assert resp.json()["is_published"] is True

        # Public homepage lists only the published one.
        public = (await client.get("/api/v1/videos/public")).json()
        # Paginated response shape: {items, page, page_size, has_more}
        titles = [item["title"] for item in public["items"]]
        assert "Published" in titles
        assert "Draft" not in titles

    async def test_admin_list_still_shows_drafts(self, client: AsyncClient, admin_headers: dict):
        """Admin list is not gated by is_published — admins see drafts to review them."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            await _seed_video_rows(db, count=1, title="Draft For Review")

        resp = await client.get("/api/v1/videos/admin", headers=admin_headers)
        assert resp.status_code == 200
        titles = [item["title"] for item in resp.json()["items"]]
        assert "Draft For Review" in titles


class TestAdminDeleteVideo:
    async def test_delete_requires_admin(self, client: AsyncClient, auth_headers: dict):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1)

        resp = await client.delete(f"/api/v1/videos/admin/{v.id}", headers=auth_headers)
        assert resp.status_code == 403

    async def test_delete_removes_video_and_subtitles(self, client: AsyncClient, admin_headers: dict):
        from sqlalchemy import select

        from app.models.subtitle import Subtitle
        from app.models.video import Video
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1)
            db.add(Subtitle(video_id=v.id, start_time=0.0, end_time=1.0, text_en="hi", sentence_index=0))
            await db.commit()
            vid = v.id

        resp = await client.delete(f"/api/v1/videos/admin/{vid}", headers=admin_headers)
        assert resp.status_code == 204

        # Verify the video and its subtitles are gone.
        async with TestSessionLocal() as db:
            assert (await db.execute(select(Video).where(Video.id == vid))).scalar_one_or_none() is None
            assert (await db.execute(select(Subtitle).where(Subtitle.video_id == vid))).scalars().all() == []

    async def test_delete_nonexistent(self, client: AsyncClient, admin_headers: dict):
        resp = await client.delete("/api/v1/videos/admin/nope", headers=admin_headers)
        assert resp.status_code == 404


class TestAdminLocalizeVideo:
    async def test_localize_requires_admin(self, client: AsyncClient, auth_headers: dict):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1)

        resp = await client.post(f"/api/v1/videos/admin/{v.id}/localize", headers=auth_headers)
        assert resp.status_code == 403

    async def test_localize_dispatches_task(self, client: AsyncClient, admin_headers: dict, monkeypatch):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1, status="ready")
            vid = v.id

        resp = await client.post(f"/api/v1/videos/admin/{vid}/localize", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processing"
        # The conftest _mock_celery fixture records dispatches on the request's
        # monkeypatch — assert localize_video was called.
        calls = getattr(monkeypatch, "_celery_calls", [])
        from app.models.video import Video

        async with TestSessionLocal() as db:
            generation = (await db.get(Video, vid)).processing_generation
        assert generation is not None
        assert any(name.endswith("localize_video") and args == (vid, True, generation) for name, args, _ in calls)

    async def test_localize_conflict_when_processing(self, client: AsyncClient, admin_headers: dict):
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1, status="processing")

        resp = await client.post(f"/api/v1/videos/admin/{v.id}/localize", headers=admin_headers)
        assert resp.status_code == 409

    async def test_localize_nonexistent_returns_404(self, client: AsyncClient, admin_headers: dict):
        resp = await client.post("/api/v1/videos/admin/does-not-exist/localize", headers=admin_headers)
        assert resp.status_code == 404

    async def test_localize_second_request_is_blocked_and_dispatches_once(
        self, client: AsyncClient, admin_headers: dict, monkeypatch
    ):
        """ADM-14: the second click must 409 without dispatching a second task."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1, status="ready")
            vid = v.id

        first = await client.post(f"/api/v1/videos/admin/{vid}/localize", headers=admin_headers)
        assert first.status_code == 200
        from app.models.video import Video

        async with TestSessionLocal() as db:
            generation = (await db.get(Video, vid)).processing_generation
        assert generation is not None

        def _localize_dispatches() -> list:
            return [
                call
                for call in getattr(monkeypatch, "_celery_calls", [])
                if call[0].endswith("localize_video") and call[1] == (vid, True, generation)
            ]

        assert len(_localize_dispatches()) == 1
        second = await client.post(f"/api/v1/videos/admin/{vid}/localize", headers=admin_headers)
        assert second.status_code == 409
        assert len(_localize_dispatches()) == 1

    async def test_localize_guard_is_a_conditional_update(self, client: AsyncClient, admin_headers: dict):
        """The double-dispatch guard is the UPDATE's rowcount, not a Python status
        read: the emitted statement must carry a ``status IN (ready, error)`` predicate,
        otherwise two requests that both read ``ready`` would both dispatch."""
        from sqlalchemy import event

        from tests.conftest import TestSessionLocal, test_engine

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1, status="ready")
            vid = v.id

        updates: list[str] = []

        def _capture(conn, cursor, statement, parameters, context, executemany):
            if statement.lstrip().upper().startswith("UPDATE VIDEOS"):
                updates.append(statement)

        event.listen(test_engine.sync_engine, "before_cursor_execute", _capture)
        try:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/localize", headers=admin_headers)
        finally:
            event.remove(test_engine.sync_engine, "before_cursor_execute", _capture)

        assert resp.status_code == 200, resp.text
        assert len(updates) == 1
        normalized = " ".join(updates[0].lower().split())
        assert " set " in normalized
        assert " where " in normalized
        assert "videos.status in (" in normalized


class TestAdminDemoVideoSerialization:
    async def test_demo_grant_takes_the_serialization_lock(self, client: AsyncClient, admin_headers: dict, monkeypatch):
        """ADM-14: granting ``is_demo`` goes through the cross-admin lock."""
        from unittest.mock import AsyncMock

        from app.services import video_service
        from tests.conftest import TestSessionLocal

        lock = AsyncMock()
        monkeypatch.setattr(video_service, "_serialize_demo_grant", lock)

        async with TestSessionLocal() as db:
            (v,) = await _seed_video_rows(db, count=1)
            vid = v.id

        resp = await client.patch(f"/api/v1/videos/admin/{vid}", headers=admin_headers, json={"is_demo": True})
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_demo"] is True
        lock.assert_awaited_once()

        # Non-demo updates don't contend for the single-demo invariant.
        lock.reset_mock()
        resp = await client.patch(
            f"/api/v1/videos/admin/{vid}", headers=admin_headers, json={"admin_notes": "internal"}
        )
        assert resp.status_code == 200
        lock.assert_not_awaited()

    async def test_serialization_lock_is_a_noop_off_postgres(self, db_session):
        """SQLite (tests/local) serializes writers itself; the helper must not
        emit PostgreSQL-only SQL there nor raise."""
        from app.services.video_service import _serialize_demo_grant

        await _serialize_demo_grant(db_session)  # no-op, no exception
