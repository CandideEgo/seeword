"""Tests for translation quality block/warn + admin re-translate (阶段 2)."""

from typing import ClassVar
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy import select

from app.models.subtitle import Subtitle
from app.models.video import Video, VideoStatus
from tests.conftest import TestSessionLocal


class TestTranslationQualityDecision:
    """Unit tests for the coverage -> quality_flag decision (no pipeline run)."""

    # Effective gate defaults mirror env: block enabled @ 0.60, warn @ 0.80.
    GATE: ClassVar[dict[str, object]] = dict(block_enabled=True, block_coverage=0.60, warn_coverage=0.80)

    def test_blocked(self):
        from app.tasks.video_processing import _translation_quality_decision

        assert _translation_quality_decision(0.5, **self.GATE) == "quality_blocked"

    def test_warning(self):
        from app.tasks.video_processing import _translation_quality_decision

        assert _translation_quality_decision(0.7, **self.GATE) == "quality_warning"

    def test_passed(self):
        from app.tasks.video_processing import _translation_quality_decision

        assert _translation_quality_decision(0.9, **self.GATE) is None

    def test_boundary_block_threshold_is_warning(self):
        # coverage == block_threshold (0.60) is NOT blocked (< is strict)
        from app.tasks.video_processing import _translation_quality_decision

        assert _translation_quality_decision(0.60, **self.GATE) == "quality_warning"

    def test_boundary_warn_threshold_is_passed(self):
        # coverage == warn_threshold (0.80) is passed (< is strict)
        from app.tasks.video_processing import _translation_quality_decision

        assert _translation_quality_decision(0.80, **self.GATE) is None

    def test_kill_switch_disables_block(self):
        from app.tasks.video_processing import _translation_quality_decision

        # 0.5 would block, but kill switch -> warning only
        gate = {**self.GATE, "block_enabled": False}
        assert _translation_quality_decision(0.5, **gate) == "quality_warning"

    def test_custom_thresholds_from_admin_settings(self):
        from app.tasks.video_processing import _translation_quality_decision

        # Admin row: block @ 0.70, warn @ 0.90
        gate = dict(block_enabled=True, block_coverage=0.70, warn_coverage=0.90)
        assert _translation_quality_decision(0.60, **gate) == "quality_blocked"
        assert _translation_quality_decision(0.75, **gate) == "quality_warning"
        assert _translation_quality_decision(0.95, **gate) is None


async def _assert_tail_intent(vid, engine, send):
    from app.models.pipeline_dispatch import PipelineDispatch
    from app.services.pipeline_dispatch import FINALIZE_VIDEO_TASK

    async with TestSessionLocal() as db:
        video = await db.get(Video, vid)
        intent = await db.scalar(select(PipelineDispatch).where(PipelineDispatch.video_id == vid))
        assert video.processing_generation is not None
        assert intent.processing_generation == video.processing_generation
        assert intent.args == [vid, engine, video.processing_generation]
        send.assert_called_once_with(FINALIZE_VIDEO_TASK, intent.args, None)


class TestRetranslateEndpoint:
    """POST /admin/{id}/retranslate clears text_zh + quality_flag, dispatches finalize."""

    async def test_retranslate_clears_and_dispatches_with_engine(self, client: AsyncClient, admin_headers: dict):
        async with TestSessionLocal() as db:
            v = Video(
                title="blocked",
                source_url="x",
                status=VideoStatus.error,
                quality_flag="quality_blocked",
                error_message="Translation coverage 50% below block",
                processing_step=None,
                is_official=True,
                is_published=False,
            )
            db.add(v)
            await db.flush()
            for i in range(3):
                db.add(
                    Subtitle(
                        video_id=v.id,
                        start_time=float(i),
                        end_time=float(i + 1),
                        text_en=f"line {i}",
                        text_zh=f"旧翻译 {i}",
                        sentence_index=i,
                    )
                )
            await db.commit()
            vid = v.id

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retranslate?engine=glm", headers=admin_headers)

        assert resp.status_code == 200
        # finalize_video.delay called with the video id + engine override
        await _assert_tail_intent(vid, "glm", mock_fin)

        async with TestSessionLocal() as db:
            fetched = (await db.execute(select(Video).where(Video.id == vid))).scalar_one()
            assert fetched.status == VideoStatus.ready_subtitles
            assert fetched.quality_flag is None
            assert fetched.error_message is None
            subs = (await db.execute(select(Subtitle).where(Subtitle.video_id == vid))).scalars().all()
            assert all(s.text_zh is None for s in subs)

    async def test_retranslate_no_engine_uses_default(self, client: AsyncClient, admin_headers: dict):
        """Without ?engine=, finalize is dispatched with engine=None (configured default)."""
        async with TestSessionLocal() as db:
            v = Video(
                title="warned",
                source_url="x",
                status=VideoStatus.ready,
                quality_flag="quality_warning",
                is_official=True,
                is_published=False,
            )
            db.add(v)
            await db.flush()
            db.add(Subtitle(video_id=v.id, start_time=0, end_time=1, text_en="hello", sentence_index=0))
            await db.commit()
            vid = v.id

        with patch("app.services.pipeline_dispatch._send_task") as mock_fin:
            resp = await client.post(f"/api/v1/videos/admin/{vid}/retranslate", headers=admin_headers)

        assert resp.status_code == 200
        await _assert_tail_intent(vid, None, mock_fin)

    async def test_retranslate_no_subtitles_400(self, client: AsyncClient, admin_headers: dict):
        async with TestSessionLocal() as db:
            v = Video(
                title="no subs",
                source_url="x",
                status=VideoStatus.error,
                quality_flag="quality_blocked",
            )
            db.add(v)
            await db.commit()
            vid = v.id

        resp = await client.post(f"/api/v1/videos/admin/{vid}/retranslate", headers=admin_headers)
        assert resp.status_code == 400

    async def test_retranslate_not_found(self, client: AsyncClient, admin_headers: dict):
        resp = await client.post("/api/v1/videos/admin/nonexistent/retranslate", headers=admin_headers)
        assert resp.status_code == 404

    async def test_retranslate_requires_admin(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post("/api/v1/videos/admin/some-id/retranslate", headers=auth_headers)
        assert resp.status_code == 403
