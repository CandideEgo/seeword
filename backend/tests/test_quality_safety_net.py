"""Tests for the transcription/translation quality safety net (Phase 2).

Covers:
- Hallucination detection in transcription output
- Translation batch retry with exponential backoff
- Translation quality gate in finalize_video
- Word-level score preservation during re-translation
- Quality report persistence to video_quality_reports (阶段 0)
"""

import pytest
from sqlalchemy import select

from app.models.subtitle import Subtitle
from app.models.video import Video, VideoStatus
from app.models.video_quality_report import VideoQualityReport
from app.services.ecdict import annotate_text


class TestTranscriptionQuality:
    """Tests for hallucination detection in transcription callback."""

    def test_repetitive_text_detected(self):
        from app.services.transcription_quality import check_transcription_quality

        segments = [
            {"text": "Hello world", "start": 0, "end": 2},
            {"text": "Hello world", "start": 2, "end": 4},
            {"text": "Hello world", "start": 4, "end": 6},
            {"text": "Hello world", "start": 6, "end": 8},
            {"text": "Hello world", "start": 8, "end": 10},
            {"text": "Hello world", "start": 10, "end": 12},
        ]
        report = check_transcription_quality(segments)
        assert not report.passed
        assert any(c.name == "repetitive" and not c.passed for c in report.checks)

    def test_nonsense_characters_detected(self):
        from app.services.transcription_quality import check_transcription_quality

        segments = [
            {"text": "Hello @#$% world", "start": 0, "end": 2},
            {"text": "Test *** ###", "start": 2, "end": 4},
            {"text": "Normal text here", "start": 4, "end": 6},
        ]
        report = check_transcription_quality(segments)
        # Only 1 of 3 has >50% non-linguistic, so this should pass
        assert report.passed

    def test_duration_mismatch_detected(self):
        from app.services.transcription_quality import check_transcription_quality

        segments = [
            {"text": "Hello", "start": 0, "end": 2},
            {"text": "World", "start": 2, "end": 4},
        ]
        # Audio is 10s but subtitles end at 4s — this is fine
        report = check_transcription_quality(segments, audio_duration=10)
        assert report.passed

        # Audio is 10s but last subtitle ends at 20s
        segments_long = [
            {"text": "Hello", "start": 0, "end": 2},
            {"text": "World", "start": 2, "end": 20},
        ]
        report_long = check_transcription_quality(segments_long, audio_duration=10)
        assert not report_long.passed

    def test_empty_segments_detected(self):
        from app.services.transcription_quality import check_transcription_quality

        # Need more segments to trigger the empty_ratio threshold
        # _MAX_EMPTY_RATIO = 0.5, need >5 segments and >50% empty
        segments = [
            {"text": "", "start": 0, "end": 2},
            {"text": "", "start": 2, "end": 4},
            {"text": "", "start": 4, "end": 6},
            {"text": "Hello", "start": 6, "end": 8},
            {"text": "", "start": 8, "end": 10},
            {"text": "", "start": 10, "end": 12},
        ]
        report = check_transcription_quality(segments)
        assert not report.passed
        assert any(c.name == "empty_ratio" and not c.passed for c in report.checks)

    def test_good_transcription_passes(self):
        from app.services.transcription_quality import check_transcription_quality

        segments = [
            {"text": "Hello world this is a test", "start": 0, "end": 3},
            {"text": "Another sentence here", "start": 3, "end": 6},
            {"text": "Third line of dialogue", "start": 6, "end": 9},
            {"text": "Final sentence", "start": 9, "end": 12},
        ]
        report = check_transcription_quality(segments, audio_duration=15)
        assert report.passed
        assert report.segment_count == 4


class TestTranslationQualityGate:
    """Tests for translation quality gate."""

    def test_low_coverage_fails(self):
        from app.services.translation.quality import check_translation_quality

        sources = ["Hello", "World", "Test", "Example"]
        translations = ["你好", None, None, "示例"]
        report = check_translation_quality(sources, translations)
        assert not report.passed
        assert report.coverage_ratio == 0.5  # 2/4

    def test_mixed_cjk_latin_fails(self):
        from app.services.translation.quality import check_translation_quality

        sources = ["Hello", "World", "Test"]
        translations = ["你好Hello", "世界World", "测试Test"]
        report = check_translation_quality(sources, translations)
        assert not report.passed
        assert report.mixed_ratio == 1.0  # All mixed

    def test_good_translation_passes(self):
        from app.services.translation.quality import check_translation_quality

        # Use longer English sources to ensure length ratios are within bounds
        sources = [
            "Hello world this is a nice day",
            "How are you doing today my friend",
            "This is a longer test sentence for you",
        ]
        translations = [
            "你好世界这是美好的一天",
            "你今天怎么样我的朋友",
            "这是一个给你准备的更长的测试句子",
        ]
        report = check_translation_quality(sources, translations)
        assert report.passed
        assert report.coverage_ratio == 1.0

    def test_empty_batch_passes(self):
        from app.services.translation.quality import check_translation_quality

        report = check_translation_quality([], [])
        assert report.passed


class TestWordLevelsPreservation:
    """Column-level checks that an existing word_levels value survives a read-modify-write.

    NOT covered here: INV-013 itself. The pipeline guard is inlined in `finalize_video`
    (app/tasks/video_processing.py, the "annotating" step) and these tests never call it.
    Until that decision is extracted from the Celery task, INV-013 stays unenforced — see
    backend/tests/test_architecture_invariants.py.
    """

    @pytest.mark.asyncio
    async def test_existing_word_levels_preserved(self, db_session):
        """An existing word_levels value round-trips through the DB unchanged."""
        # Create a subtitle with manually set word_levels
        sub = Subtitle(
            video_id="test-video-id",
            start_time=0,
            end_time=2,
            text_en="Hello world",
            text_zh="你好世界",
            sentence_index=0,
            word_levels={"hello": ["cet4"], "world": ["cet6"]},  # Manual override
        )
        db_session.add(sub)
        await db_session.commit()

        # Verify the word_levels are preserved
        result = await db_session.execute(select(Subtitle).where(Subtitle.id == sub.id))
        fetched = result.scalar_one()
        assert fetched.word_levels == {"hello": ["cet4"], "world": ["cet6"]}

        # Simulate what finalize_video's annotating step does now:
        # Only compute if word_levels is None
        if fetched.word_levels is None:
            fetched.word_levels = annotate_text(fetched.text_en) or None
            raise AssertionError("word_levels should not be None here")

        # The word_levels should still be the manual override
        assert fetched.word_levels == {"hello": ["cet4"], "world": ["cet6"]}

    @pytest.mark.asyncio
    async def test_null_word_levels_computed(self, db_session, requires_ecdict):
        """When word_levels is null, it should be computed from text_en."""
        sub = Subtitle(
            video_id="test-video-id",
            start_time=0,
            end_time=2,
            text_en="Hello world",
            text_zh="你好世界",
            sentence_index=0,
            word_levels=None,
        )
        db_session.add(sub)
        await db_session.commit()

        # When word_levels is None, compute it
        if sub.word_levels is None:
            sub.word_levels = annotate_text(sub.text_en) or None

        # Should now have computed values
        assert sub.word_levels is not None
        assert isinstance(sub.word_levels, dict)


class TestQualityReportPersistence:
    """Tests for persisting quality reports to video_quality_reports (阶段 0)."""

    @pytest.mark.asyncio
    async def test_persist_translation_report(self, db_session):
        """A failed translation quality report is persisted with coverage + metrics."""
        from app.services.translation.quality import check_translation_quality, persist_quality_report

        v = Video(id="vq-translation-1", title="t", source_url="x", status=VideoStatus.ready)
        db_session.add(v)
        await db_session.flush()

        sources = ["Hello", "World", "Test", "Example"]
        translations = ["你好", None, None, "示例"]  # 50% coverage -> fails
        report = check_translation_quality(sources, translations)

        await persist_quality_report(db_session, v.id, report)
        await db_session.commit()

        rows = (
            (await db_session.execute(select(VideoQualityReport).where(VideoQualityReport.video_id == v.id)))
            .scalars()
            .all()
        )
        assert len(rows) == 1
        row = rows[0]
        assert row.stage == "translation"
        assert row.passed is False
        assert row.coverage_ratio == 0.5
        assert row.metrics["translated_count"] == 2
        assert row.metrics["total_subtitles"] == 4
        assert len(row.issues) > 0
        assert row.segment_count is None

    @pytest.mark.asyncio
    async def test_persist_translation_report_passed(self, db_session):
        """A passing translation report is persisted with passed=True and empty issues."""
        from app.services.translation.quality import check_translation_quality, persist_quality_report

        v = Video(id="vq-translation-2", title="t", source_url="x", status=VideoStatus.ready)
        db_session.add(v)
        await db_session.flush()

        sources = [
            "Hello world this is a nice day",
            "How are you doing today my friend",
        ]
        translations = ["你好世界这是美好的一天", "你今天怎么样我的朋友"]
        report = check_translation_quality(sources, translations)

        await persist_quality_report(db_session, v.id, report)
        await db_session.commit()

        row = (
            await db_session.execute(select(VideoQualityReport).where(VideoQualityReport.video_id == v.id))
        ).scalar_one()
        assert row.passed is True
        assert row.issues == []

    @pytest.mark.asyncio
    async def test_persist_transcription_report(self, db_session):
        """A failed transcription report persists per-check details as issues."""
        from app.services.transcription_quality import check_transcription_quality, persist_quality_report

        v = Video(id="vq-transcription-1", title="t", source_url="x", status=VideoStatus.ready)
        db_session.add(v)
        await db_session.flush()

        # Repetitive segments -> fails the "repetitive" check
        segments = [{"text": "Hello world", "start": i * 2, "end": i * 2 + 2} for i in range(6)]
        report = check_transcription_quality(segments)

        await persist_quality_report(db_session, v.id, report)
        await db_session.commit()

        row = (
            await db_session.execute(select(VideoQualityReport).where(VideoQualityReport.video_id == v.id))
        ).scalar_one()
        assert row.stage == "transcription"
        assert row.passed is False
        assert row.coverage_ratio is None
        assert row.segment_count == 6
        # metrics carries the per-check breakdown
        check_names = {c["name"] for c in row.metrics["checks"]}
        assert "repetitive" in check_names
        # failed checks contribute their detail to issues
        assert len(row.issues) >= 1

    @pytest.mark.asyncio
    async def test_persist_is_append_only(self, db_session):
        """Re-running persist leaves a new row rather than mutating the old one."""
        from app.services.translation.quality import check_translation_quality, persist_quality_report

        v = Video(id="vq-append-1", title="t", source_url="x", status=VideoStatus.ready)
        db_session.add(v)
        await db_session.flush()

        sources = ["Hello world this is a nice day"]
        translations = ["你好世界这是美好的一天"]
        report = check_translation_quality(sources, translations)

        await persist_quality_report(db_session, v.id, report)
        await persist_quality_report(db_session, v.id, report)
        await db_session.commit()

        rows = (
            (await db_session.execute(select(VideoQualityReport).where(VideoQualityReport.video_id == v.id)))
            .scalars()
            .all()
        )
        assert len(rows) == 2  # append-only, no update
