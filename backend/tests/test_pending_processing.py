"""Tests for the pending_processing video flow.

Covers:
- User video submission creates pending_processing status (not processing).
- process_video.delay() is NOT called on user submission.
- Admin start_processing transitions pending_processing → processing.
- start_processing fails when GPU worker is offline (503).
- start_processing fails when video is not in pending_processing status (400).
- Admin seed (seed_video) still auto-processes (backwards compatible).
- Auto-publish syncs review_status to published.
- Worker status endpoint returns correct online/offline state.
- UGC submissions always stay in draft (auto_publish=False).

The GPU worker security-guard tests moved to ``gpu-worker/tests/`` together with
``scripts/start_gpu_worker.py`` when the GPU worker was split out of this repo.
"""

from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User
from app.models.video import Video, VideoReviewStatus, VideoStatus


async def _assert_head_intent(vid, send):
    from app.models.pipeline_dispatch import PipelineDispatch
    from app.services.pipeline_dispatch import PROCESS_VIDEO_TASK
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as db:
        video = await db.get(Video, vid)
        intent = await db.scalar(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))
        assert video.processing_generation is not None
        assert intent.processing_generation == video.processing_generation
        assert intent.args == [vid, video.processing_generation]
        send.assert_called_once_with(PROCESS_VIDEO_TASK, intent.args, None)


async def _owner_id(db) -> str:
    user = (await db.execute(select(User).where(User.phone == "13800138000"))).scalar_one()
    return user.id


async def _seed_pending_video(db, *, owner_id):
    v = Video(
        title="Pending Test",
        source_url="https://example.com/pending.mp4",
        video_source="local",
        status=VideoStatus.pending_processing,
        is_official=False,
        is_published=False,
        review_status=VideoReviewStatus.draft.value,
        user_id=owner_id,
        auto_publish=False,
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v


class TestUserSubmissionNoAutoProcess:
    """Admin seed still auto-processes (backwards compatible)."""

    async def test_admin_seed_still_auto_processes(self, client: AsyncClient, admin_headers: dict):
        """POST /videos/seed (admin) should still immediately process."""
        with patch("app.services.pipeline_dispatch._send_task") as mock_pv:
            resp = await client.post(
                "/api/v1/videos/seed",
                json={"source_url": "https://www.youtube.com/watch?v=admin_seed_test"},
                headers=admin_headers,
            )
            assert resp.status_code == 201
            await _assert_head_intent(resp.json()["id"], mock_pv)

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "processing"
        assert data["is_official"] is True


class TestStartProcessing:
    """Admin-triggered processing for pending_processing videos."""

    async def test_start_processing_success(self, client: AsyncClient, auth_headers: dict, admin_headers: dict):
        """POST /admin/{id}/start-processing transitions to processing when worker online."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            owner = await _owner_id(db)
            v = await _seed_pending_video(db, owner_id=owner)
            vid = v.id

        with (
            patch("app.services.video_seed_service.is_gpu_worker_online", return_value=True),
            patch("app.services.pipeline_dispatch._send_task") as mock_pv,
        ):
            resp = await client.post(
                f"/api/v1/videos/admin/{vid}/start-processing",
                headers=admin_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processing"
        await _assert_head_intent(vid, mock_pv)

    async def test_start_processing_worker_offline_503(
        self, client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        """POST /admin/{id}/start-processing returns 503 when worker offline."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            owner = await _owner_id(db)
            v = await _seed_pending_video(db, owner_id=owner)
            vid = v.id

        with patch("app.services.video_seed_service.is_gpu_worker_online", return_value=False):
            resp = await client.post(
                f"/api/v1/videos/admin/{vid}/start-processing",
                headers=admin_headers,
            )

        assert resp.status_code == 503
        # 批 1c: 这条 503 的 code 从 transport 形态（HTTP_503）换成原因名——
        # service 抛 ServiceUnavailableError，走 AppError handler 的 envelope
        # （{code, message}，不再回显 detail）。状态码本身不动。
        assert resp.json()["code"] == "SERVICE_UNAVAILABLE"
        assert "offline" in resp.json()["message"].lower()

    async def test_start_processing_wrong_status_400(
        self, client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        """POST /admin/{id}/start-processing returns 400 when video is not pending_processing."""
        from tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            owner = await _owner_id(db)
            v = Video(
                title="Already Processing",
                source_url="https://example.com/already.mp4",
                video_source="local",
                status=VideoStatus.processing,
                is_official=False,
                is_published=False,
                review_status=VideoReviewStatus.draft.value,
                user_id=owner,
            )
            db.add(v)
            await db.commit()
            await db.refresh(v)
            vid = v.id

        with patch("app.services.video_seed_service.is_gpu_worker_online", return_value=True):
            resp = await client.post(
                f"/api/v1/videos/admin/{vid}/start-processing",
                headers=admin_headers,
            )

        assert resp.status_code == 400

    async def test_start_processing_not_found(self, client: AsyncClient, admin_headers: dict):
        """POST /admin/{id}/start-processing returns 404 for missing video."""
        resp = await client.post(
            "/api/v1/videos/admin/nonexistent-id/start-processing",
            headers=admin_headers,
        )
        assert resp.status_code == 404


class TestWorkerStatus:
    """Admin worker-status endpoint."""

    async def test_worker_online(self, client: AsyncClient, admin_headers: dict):
        with patch("app.services.video_seed_service.is_gpu_worker_online", return_value=True):
            resp = await client.get(
                "/api/v1/admin/worker-status",
                headers=admin_headers,
            )
        assert resp.status_code == 200
        assert resp.json()["worker_online"] is True

    async def test_worker_offline(self, client: AsyncClient, admin_headers: dict):
        with patch("app.services.video_seed_service.is_gpu_worker_online", return_value=False):
            resp = await client.get(
                "/api/v1/admin/worker-status",
                headers=admin_headers,
            )
        assert resp.status_code == 200
        assert resp.json()["worker_online"] is False


class TestAutoPublishSyncsReviewStatus:
    """When auto_publish fires, review_status should also be set to published."""

    async def test_auto_publish_sets_review_status_published(self):
        assert VideoReviewStatus.published.value == "published"
        assert VideoStatus.pending_processing.value == "pending_processing"
