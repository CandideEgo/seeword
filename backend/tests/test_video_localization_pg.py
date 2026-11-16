"""PostgreSQL evidence for localization claim + existing dispatch outbox."""

import asyncio
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.database import get_async_session_maker, get_db
from app.core.security import create_token
from app.main import create_app
from app.models.pipeline_dispatch import PipelineDispatch
from app.models.user import RoleType, User
from app.models.video import Video, VideoStatus
from app.services import pipeline_dispatch

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def pg_client():
    async def sessions():
        async with get_async_session_maker()() as db:
            yield db

    app = create_app()
    app.dependency_overrides[get_db] = sessions
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


async def seed():
    async with get_async_session_maker()() as db:
        user = User(phone="13800009861", name="Localization admin", role=RoleType.admin)
        video = Video(
            title="PG localization",
            source_url="https://youtube.com/watch?v=abcdefghijk",
            video_source="imported",
            status=VideoStatus.ready,
            is_official=True,
            video_url_720p="/media/previous.mp4",
        )
        db.add_all([user, video])
        await db.commit()
        return video.id, {"Authorization": f"Bearer {create_token(user.id)}"}


async def test_concurrent_localization_claims_create_and_send_one_intent(pg_client, monkeypatch):
    vid, headers = await seed()
    sender = AsyncMock()
    monkeypatch.setattr(pipeline_dispatch, "_send", sender)
    url = f"/api/v1/videos/admin/{vid}/localize"
    responses = await asyncio.wait_for(
        asyncio.gather(pg_client.post(url, headers=headers), pg_client.post(url, headers=headers)), timeout=15
    )
    assert sorted(response.status_code for response in responses) == [200, 409]
    async with get_async_session_maker()() as db:
        assert await db.scalar(select(func.count(PipelineDispatch.id))) == 1
        video = await db.get(Video, vid)
        assert video.status == VideoStatus.processing and video.video_url_720p == "/media/previous.mp4"
        assert video.processing_generation is not None and video.step_started_at is not None
        sender.assert_awaited_once_with(
            pipeline_dispatch.LOCALIZE_VIDEO_TASK, [vid, True, video.processing_generation], None
        )


async def test_failed_intent_insert_rolls_back_processing_claim(pg_client, monkeypatch):
    vid, headers = await seed()
    monkeypatch.setattr(pipeline_dispatch, "enqueue", AsyncMock(side_effect=RuntimeError("intent unavailable")))
    response = await pg_client.post(f"/api/v1/videos/admin/{vid}/localize", headers=headers)
    assert response.status_code == 500
    async with get_async_session_maker()() as db:
        assert (await db.get(Video, vid)).status == VideoStatus.ready
        assert await db.scalar(select(func.count(PipelineDispatch.id))) == 0


async def test_delayed_intent_is_abandoned_if_full_pipeline_has_taken_over(monkeypatch):
    vid, _headers = await seed()
    sender = AsyncMock()
    monkeypatch.setattr(pipeline_dispatch, "_send", sender)
    async with get_async_session_maker()() as db:
        await pipeline_dispatch.enqueue(
            db, video_id=vid, task_name=pipeline_dispatch.LOCALIZE_VIDEO_TASK, args=[vid, True]
        )
        video = await db.get(Video, vid)
        video.status = VideoStatus.ready_subtitles
        await db.commit()
        result = await pipeline_dispatch.dispatch_pending(db)
        assert result.abandoned == 1 and result.sent == 0
        sender.assert_not_called()
