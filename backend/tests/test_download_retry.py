"""Tests for failed-download retry + localize strike logic (阶段 3)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from app.models.video import Video, VideoStatus
from tests.conftest import TestSessionLocal


async def _patch_async_session(monkeypatch):
    """Point app.core.database.async_session at the test SQLite engine."""
    import app.core.database as db_mod

    monkeypatch.setattr(db_mod, "async_session", TestSessionLocal)


class TestRetryFailedDownloads:
    """_run_retry_failed_downloads selects only ready imported videos under the strike limit."""

    @pytest.mark.asyncio
    async def test_selects_under_strike_limit(self, db_session, monkeypatch):
        await _patch_async_session(monkeypatch)
        from app.services import pipeline_dispatch

        send = MagicMock()
        monkeypatch.setattr(pipeline_dispatch, "_send_task", send)
        monkeypatch.setattr(
            "app.services.youtube_cookies_service.ensure_cookies_for_pipeline",
            AsyncMock(),
        )
        from app.tasks.video_processing import _run_retry_failed_downloads

        v1 = Video(  # under limit -> candidate
            title="r1",
            source_url="https://youtube.com/1",
            video_source="imported",
            status=VideoStatus.ready,
            video_url_720p=None,
            download_failed_at=datetime.now(UTC),
            download_fail_count=1,
        )
        v2 = Video(  # at limit -> skipped
            title="r2",
            source_url="https://youtube.com/2",
            video_source="imported",
            status=VideoStatus.ready,
            video_url_720p=None,
            download_failed_at=datetime.now(UTC),
            download_fail_count=3,
        )
        v3 = Video(  # no failure recorded -> skipped
            title="r3",
            source_url="https://youtube.com/3",
            video_source="imported",
            status=VideoStatus.ready,
            video_url_720p=None,
            download_failed_at=None,
            download_fail_count=0,
        )
        db_session.add_all([v1, v2, v3])
        await db_session.commit()

        await _run_retry_failed_downloads()

        from app.models.pipeline_dispatch import PipelineDispatch
        from app.services.pipeline_dispatch import LOCALIZE_VIDEO_TASK

        async with TestSessionLocal() as db:
            video = await db.get(Video, v1.id)
            intents = list((await db.scalars(select(PipelineDispatch))).all())
            assert len(intents) == 1
            assert intents[0].video_id == v1.id
            assert video.processing_generation is not None
            assert intents[0].processing_generation == video.processing_generation
            assert intents[0].args == [v1.id, False, video.processing_generation]
            assert intents[0].status == "dispatched"
            send.assert_called_once_with(LOCALIZE_VIDEO_TASK, intents[0].args, None)
            assert (await db.get(Video, v2.id)).status == VideoStatus.ready
            assert (await db.get(Video, v3.id)).status == VideoStatus.ready

    @pytest.mark.asyncio
    async def test_refreshes_cookies_before_dispatch(self, db_session, monkeypatch):
        await _patch_async_session(monkeypatch)
        from app.services import pipeline_dispatch

        events = []
        monkeypatch.setattr(pipeline_dispatch, "_send_task", lambda *args: events.append("send"))
        cookie_mock = AsyncMock(side_effect=lambda *args: events.append("cookies"))
        monkeypatch.setattr(
            "app.services.youtube_cookies_service.ensure_cookies_for_pipeline",
            cookie_mock,
        )
        from app.tasks.video_processing import _run_retry_failed_downloads

        v = Video(
            title="cookie",
            source_url="https://youtube.com/c",
            video_source="imported",
            status=VideoStatus.ready,
            video_url_720p=None,
            download_failed_at=datetime.now(UTC),
            download_fail_count=0,
        )
        db_session.add(v)
        await db_session.commit()

        await _run_retry_failed_downloads()

        cookie_mock.assert_awaited_once_with(v.source_url)
        assert events == ["cookies", "send"]


class TestLocalizeDownloadFailure:
    """_run_localize records download failures and respects the strike limit."""

    @pytest.mark.asyncio
    async def test_download_failure_records_and_stays_ready(self, db_session, monkeypatch):
        await _patch_async_session(monkeypatch)
        import app.tasks.video_processing as vp

        monkeypatch.setattr(vp, "acquire_lock", lambda vid: True)
        monkeypatch.setattr(vp, "_download_video", AsyncMock(return_value=None))
        from app.tasks.video_processing import _run_localize

        v = Video(
            title="dl",
            source_url="https://youtube.com/watch?v=abcdefghijk",
            video_source="imported",
            status=VideoStatus.processing,
            video_url_720p=None,
            download_fail_count=0,
        )
        db_session.add(v)
        await db_session.commit()
        vid = v.id

        await _run_localize(MagicMock(), vid, force=False)

        async with TestSessionLocal() as db:
            fetched = (await db.execute(select(Video).where(Video.id == vid))).scalar_one()
            assert fetched.status == VideoStatus.ready  # stayed playable
            assert fetched.download_failed_at is not None
            assert fetched.download_fail_count == 1

    @pytest.mark.asyncio
    async def test_strike_skips_localize(self, db_session, monkeypatch):
        await _patch_async_session(monkeypatch)
        import app.tasks.video_processing as vp

        monkeypatch.setattr(vp, "acquire_lock", lambda vid: True)
        mock_dl = AsyncMock(return_value="/fake/path")
        monkeypatch.setattr(vp, "_download_video", mock_dl)
        from app.tasks.video_processing import _run_localize

        v = Video(
            title="strike",
            source_url="https://youtube.com/watch?v=abcdefghijk",
            video_source="imported",
            status=VideoStatus.ready,
            video_url_720p=None,
            download_fail_count=3,
        )
        db_session.add(v)
        await db_session.commit()

        await _run_localize(MagicMock(), v.id, force=False)

        mock_dl.assert_not_called()  # strike -> skip before download

    @pytest.mark.asyncio
    async def test_force_bypasses_strike(self, db_session, monkeypatch):
        await _patch_async_session(monkeypatch)
        import app.tasks.video_processing as vp

        monkeypatch.setattr(vp, "acquire_lock", lambda vid: True)
        mock_dl = AsyncMock(return_value=None)
        monkeypatch.setattr(vp, "_download_video", mock_dl)
        from app.tasks.video_processing import _run_localize

        v = Video(
            title="force",
            source_url="https://youtube.com/watch?v=abcdefghijk",
            video_source="imported",
            status=VideoStatus.processing,
            video_url_720p=None,
            download_fail_count=3,
        )
        db_session.add(v)
        await db_session.commit()

        await _run_localize(MagicMock(), v.id, force=True)

        mock_dl.assert_called_once()  # force bypassed the strike limit
