"""管理员 retry 的智能续跑：字幕保留、generation 隔离与持久 tail 派发。

有字幕的 error 视频直接续跑 tail；无字幕的 error 视频只回到
pending_processing，仍需显式 start-processing。broker 失败不丢已提交意图。
"""

from datetime import UTC, timedelta
from unittest.mock import patch
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy import select

from app.models.pipeline_dispatch import DISPATCH_STATUS_DISPATCHED, DISPATCH_STATUS_PENDING, PipelineDispatch
from app.models.subtitle import Subtitle
from app.models.user import User
from app.models.video import Video, VideoReviewStatus, VideoStatus
from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK, dispatch_pending, enqueue
from tests.conftest import TestSessionLocal


async def _owner_id(db) -> str:
    user = (await db.execute(select(User).where(User.phone == "13800138000"))).scalar_one()
    return user.id


async def _make_error_video(db, *, owner_id: str, with_subtitles: bool) -> Video:
    """Create an errored generation with optional persisted bilingual subtitles."""
    v = Video(
        title="Errored Pipeline",
        source_url="https://www.youtube.com/watch?v=resume_test",
        video_source="imported",
        status=VideoStatus.error,
        error_message="simulated transcription boom",
        processing_step=None,
        processing_progress=0,
        processing_generation=str(uuid4()),
        is_official=False,
        is_published=False,
        review_status=VideoReviewStatus.draft.value,
        user_id=owner_id,
        auto_publish=False,
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    if with_subtitles:
        for i in range(3):
            db.add(
                Subtitle(
                    video_id=v.id,
                    start_time=float(i),
                    end_time=float(i + 1),
                    text_en=f"line {i}",
                    text_zh=f"译文 {i}",
                    sentence_index=i,
                )
            )
        await db.commit()
    return v


class TestRetrySmartResume:
    async def test_retry_with_subtitles_dispatches_finalize(
        self, client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        async with TestSessionLocal() as db:
            v = await _make_error_video(db, owner_id=await _owner_id(db), with_subtitles=True)
            vid, old_generation = v.id, v.processing_generation
            old_subs = list((await db.scalars(select(Subtitle).where(Subtitle.video_id == vid))).all())
            # 已有旧代 tail 行应重置为新代意图，而非新增一行或发送旧代参数。
            dispatch_id = await enqueue(db, video_id=vid, task_name=FINALIZE_VIDEO_TASK, args=[vid, "glm"])
            old_dispatch = await db.get(PipelineDispatch, dispatch_id)
            old_dispatch.status = DISPATCH_STATUS_DISPATCHED
            old_dispatch.attempts = 4
            await db.commit()

        with patch("app.services.pipeline_dispatch._send_task") as send:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retry", headers=admin_headers)
            repeated = await client.post(f"/api/v1/videos/admin/{vid}/retry", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "ready_subtitles"
        assert resp.json()["error_message"] is None
        assert repeated.status_code == 400, repeated.text

        async with TestSessionLocal() as db:
            v = await db.get(Video, vid)
            assert v.status == VideoStatus.ready_subtitles
            assert v.processing_step == "translating"
            assert v.processing_progress == 70
            assert v.processing_generation and v.processing_generation != old_generation
            (row,) = (await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))).all()
            assert row.id == dispatch_id
            assert row.task_name == FINALIZE_VIDEO_TASK
            assert row.processing_generation == v.processing_generation
            assert row.args == [vid, None, v.processing_generation]
            assert row.queue is None
            assert row.status == DISPATCH_STATUS_DISPATCHED
            assert row.attempts == 1
            assert row.last_error is None
            assert row.dispatched_at is not None
            send.assert_called_once_with(FINALIZE_VIDEO_TASK, row.args, None)
            subs = list((await db.scalars(select(Subtitle).where(Subtitle.video_id == vid))).all())
            assert sorted((s.id, s.text_en, s.text_zh) for s in subs) == sorted(
                (s.id, s.text_en, s.text_zh) for s in old_subs
            )

    async def test_retry_without_subtitles_resets_to_pending(
        self, client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        async with TestSessionLocal() as db:
            v = await _make_error_video(db, owner_id=await _owner_id(db), with_subtitles=False)
            vid, old_generation = v.id, v.processing_generation

        with patch("app.services.pipeline_dispatch._send_task") as send:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retry", headers=admin_headers)

        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "pending_processing"
        # 无字幕 retry 不绕过显式启动和 worker-online 检查。
        send.assert_not_called()
        async with TestSessionLocal() as db:
            v = await db.get(Video, vid)
            assert v.status == VideoStatus.pending_processing
            assert v.processing_step is None
            assert v.processing_progress == 0
            assert v.error_message is None
            assert v.processing_generation and v.processing_generation != old_generation
            assert (await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))).all() == []

    async def test_retry_broker_failure_preserves_subtitles_and_resends_pending_tail(
        self, client: AsyncClient, auth_headers: dict, admin_headers: dict
    ):
        async with TestSessionLocal() as db:
            v = await _make_error_video(db, owner_id=await _owner_id(db), with_subtitles=True)
            vid, old_generation = v.id, v.processing_generation

        with patch("app.services.pipeline_dispatch._send_task", side_effect=RuntimeError("broker down")) as send:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retry", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        async with TestSessionLocal() as db:
            v = await db.get(Video, vid)
            assert v.status == VideoStatus.ready_subtitles
            assert v.error_message is None
            assert v.processing_generation and v.processing_generation != old_generation
            (row,) = (await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))).all()
            assert row.status == DISPATCH_STATUS_PENDING
            assert row.task_name == FINALIZE_VIDEO_TASK
            assert row.processing_generation == v.processing_generation
            assert row.args == [vid, None, v.processing_generation]
            assert row.attempts == 1
            assert row.last_error == "broker down"
            assert row.dispatched_at is None
            assert row.next_attempt_at is not None
            send.assert_called_once_with(FINALIZE_VIDEO_TASK, row.args, None)
            due = row.next_attempt_at.replace(tzinfo=UTC) + timedelta(seconds=1)
            dispatch_id, args = row.id, row.args

        with (
            patch("app.services.pipeline_dispatch._utcnow", return_value=due),
            patch("app.services.pipeline_dispatch._send_task") as resend,
        ):
            async with TestSessionLocal() as db:
                result = await dispatch_pending(db)
        assert result.scanned == result.sent == 1
        assert result.failed == result.abandoned == 0
        resend.assert_called_once_with(FINALIZE_VIDEO_TASK, args, None)
        async with TestSessionLocal() as db:
            (row,) = (await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))).all()
            assert row.id == dispatch_id
            assert row.args == args
            assert row.processing_generation == args[-1]
            assert row.status == DISPATCH_STATUS_DISPATCHED
            assert row.attempts == 2
            assert row.last_error is None
            assert row.next_attempt_at is None
            assert row.dispatched_at is not None
            subs = (
                await db.scalars(select(Subtitle).where(Subtitle.video_id == vid).order_by(Subtitle.sentence_index))
            ).all()
            assert [sub.text_zh for sub in subs] == ["译文 0", "译文 1", "译文 2"]

    async def test_retry_rejects_non_error_video(self, client: AsyncClient, auth_headers: dict, admin_headers: dict):
        async with TestSessionLocal() as db:
            v = Video(
                title="Not Error",
                source_url="https://example.com/processing.mp4",
                video_source="local",
                status=VideoStatus.processing,
                is_official=False,
                is_published=False,
                review_status=VideoReviewStatus.draft.value,
                user_id=await _owner_id(db),
            )
            db.add(v)
            await db.commit()
            vid = v.id

        with patch("app.services.pipeline_dispatch._send_task") as send:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retry", headers=admin_headers)
        assert resp.status_code == 400, resp.text
        send.assert_not_called()
        async with TestSessionLocal() as db:
            assert (await db.get(Video, vid)).status == VideoStatus.processing
            assert (await db.scalars(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))).all() == []

    async def test_retry_not_found(self, client: AsyncClient, admin_headers: dict):
        with patch("app.services.pipeline_dispatch._send_task") as send:
            resp = await client.post("/api/v1/videos/admin/nonexistent-id/retry", headers=admin_headers)
        assert resp.status_code == 404, resp.text
        send.assert_not_called()
