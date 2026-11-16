"""Tests for the one-click seed-full admin endpoint."""

from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy import select

from app.models.pipeline_dispatch import DISPATCH_STATUS_DISPATCHED, DISPATCH_STATUS_PENDING, PipelineDispatch
from app.models.video import Video, VideoStatus
from app.services.pipeline_dispatch import PROCESS_VIDEO_TASK
from tests.conftest import TestSessionLocal


async def _ready_official(url: str) -> str:
    """Insert a ready official video for dedup tests; return its id."""
    async with TestSessionLocal() as db:
        v = Video(
            title="Existing",
            source_url=url,
            video_source="imported",
            status=VideoStatus.ready,
            is_official=True,
            is_published=True,
        )
        db.add(v)
        await db.commit()
        await db.refresh(v)
        return v.id


class TestSeedFull:
    async def test_requires_admin(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/v1/videos/seed-full",
            headers=auth_headers,
            json={"source_url": "https://www.youtube.com/watch?v=abcdefghijk"},
        )
        assert resp.status_code == 403

    async def test_cookies_need_manual_login_returns_423(self, client: AsyncClient, admin_headers: dict):
        with patch(
            "app.services.youtube_cookies_service.ensure_cookies",
            new=AsyncMock(return_value="need_manual_login"),
        ):
            resp = await client.post(
                "/api/v1/videos/seed-full",
                headers=admin_headers,
                json={"source_url": "https://www.youtube.com/watch?v=abcdefghijk"},
            )
        assert resp.status_code == 423
        assert "登录" in resp.json()["detail"]

    async def test_cookies_error_returns_502(self, client: AsyncClient, admin_headers: dict):
        with patch(
            "app.services.youtube_cookies_service.ensure_cookies",
            new=AsyncMock(return_value="error"),
        ):
            resp = await client.post(
                "/api/v1/videos/seed-full",
                headers=admin_headers,
                json={"source_url": "https://www.youtube.com/watch?v=abcdefghijk"},
            )
        assert resp.status_code == 502

    async def test_seeds_with_auto_publish_when_cookies_ok(self, client: AsyncClient, admin_headers: dict):
        """cookies ok -> seed with auto_publish=True; verify the flag is set on the row."""
        with (
            patch(
                "app.services.youtube_cookies_service.ensure_cookies",
                new=AsyncMock(return_value="ok"),
            ),
            patch("app.services.pipeline_dispatch._send_task") as send,
        ):
            resp = await client.post(
                "/api/v1/videos/seed-full",
                headers=admin_headers,
                json={"source_url": "https://www.youtube.com/watch?v=autopubtest001"},
            )
        assert resp.status_code == 201
        vid = resp.json()["id"]
        # auto_publish 与持久 head 意图同一事务落库。
        async with TestSessionLocal() as db:
            v = (await db.execute(select(Video).where(Video.id == vid))).scalar_one()
            assert v.is_official is True
            assert v.is_published is False  # draft until finalize publishes
            assert v.auto_publish is True
            assert v.status == VideoStatus.processing
            assert v.processing_generation
            (row,) = (await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))).all()
            assert row.task_name == PROCESS_VIDEO_TASK
            assert row.processing_generation == v.processing_generation
            assert row.args == [vid, v.processing_generation]
            assert row.queue is None
            assert row.status == DISPATCH_STATUS_DISPATCHED
            assert row.attempts == 1
            assert row.last_error is None
            assert row.next_attempt_at is None
            assert row.dispatched_at is not None
            send.assert_called_once_with(PROCESS_VIDEO_TASK, row.args, None)

    async def test_dedup_returns_existing_ready_video(self, client: AsyncClient, admin_headers: dict):
        """Re-seeding an already-ready URL returns the existing row (no new row, no re-process)."""
        url = "https://www.youtube.com/watch?v=deduptest0001"
        existing_id = await _ready_official(url)
        with (
            patch(
                "app.services.youtube_cookies_service.ensure_cookies",
                new=AsyncMock(return_value="ok"),
            ),
            patch("app.services.pipeline_dispatch._send_task") as send,
        ):
            resp = await client.post(
                "/api/v1/videos/seed-full",
                headers=admin_headers,
                json={"source_url": url},
            )
        assert resp.status_code == 201
        assert resp.json()["id"] == existing_id
        # No new processing dispatched — dedup hit.
        send.assert_not_called()
        async with TestSessionLocal() as db:
            assert (await db.scalars(select(Video).where(Video.source_url == url))).one().id == existing_id
            assert (
                await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == existing_id))
            ).all() == []

    async def test_broker_failure_keeps_auto_publish_and_pending_head(self, client: AsyncClient, admin_headers: dict):
        """cookies 已通过而 broker 失败时，201 + 持久意图，不回退成 error。"""
        with (
            patch("app.services.youtube_cookies_service.ensure_cookies", new=AsyncMock(return_value="ok")),
            patch("app.services.pipeline_dispatch._send_task", side_effect=RuntimeError("broker down")) as send,
        ):
            resp = await client.post(
                "/api/v1/videos/seed-full",
                headers=admin_headers,
                json={"source_url": "https://www.youtube.com/watch?v=brokerfail001"},
            )
        assert resp.status_code == 201, resp.text
        vid = resp.json()["id"]
        async with TestSessionLocal() as db:
            video = await db.get(Video, vid)
            assert video.status == VideoStatus.processing
            assert video.auto_publish is True
            assert video.is_official is True
            assert video.is_published is False
            assert video.error_message is None
            assert video.processing_generation
            (row,) = (await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))).all()
            assert row.task_name == PROCESS_VIDEO_TASK
            assert row.args == [vid, video.processing_generation]
            assert row.processing_generation == video.processing_generation
            assert row.queue is None
            assert row.status == DISPATCH_STATUS_PENDING
            assert row.attempts == 1
            assert row.last_error == "broker down"
            assert row.next_attempt_at is not None
            assert row.dispatched_at is None
            send.assert_called_once_with(PROCESS_VIDEO_TASK, row.args, None)
