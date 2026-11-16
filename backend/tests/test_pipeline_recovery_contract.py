"""Regression for same-attempt hand-off lock ownership and late ready-tail replay."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from app.models.subtitle import Subtitle
from app.models.video import Video, VideoStatus
from app.services.processing_generation import run_identity
from tests.conftest import TestSessionLocal

GENERATION = "e1c66a92-06ef-45c7-ab4f-b7df076b5f59"


async def seed(generation, status):
    async with TestSessionLocal() as db:
        video = Video(
            title="Recovery fixture",
            source_url="https://www.youtube.com/watch?v=abcdefghijk",
            video_source="imported",
            status=status,
            processing_generation=generation,
            is_official=True,
            auto_publish=True,
            is_published=False,
        )
        db.add(video)
        await db.flush()
        db.add(Subtitle(video_id=video.id, start_time=0, end_time=1, text_en="A fixture.", sentence_index=0))
        await db.commit()
        return video.id


def capture_task(monkeypatch, vp):
    pending = []
    monkeypatch.setattr(vp, "run_pipeline_task", pending.append)
    return pending


@pytest.mark.parametrize("generation", [None, GENERATION])
async def test_head_exit_does_not_delete_tail_lock_acquired_during_dispatch(monkeypatch, generation):
    from app.services import pipeline_dispatch
    from app.tasks import pipeline_helpers
    from app.tasks import video_processing as vp

    vid = await seed(generation, VideoStatus.processing)
    key = run_identity(vid, generation)
    owners = {}

    def acquire(run_key):
        assert run_key == key
        owners[run_key] = "head"
        return True

    def release(run_key):
        owners.pop(run_key, None)

    def send(task_name, args, queue):
        assert task_name == pipeline_dispatch.FINALIZE_VIDEO_TASK
        assert key not in owners
        assert args == ([vid, None, generation] if generation else [vid])
        # The successor acquires the lock before dispatch_now returns to head.
        owners[key] = "tail"

    monkeypatch.setattr(vp, "acquire_lock", acquire)
    monkeypatch.setattr(vp, "release_lock", release)
    monkeypatch.setattr(pipeline_helpers, "release_lock", release)
    monkeypatch.setattr(pipeline_dispatch, "_send_task", send)
    pending = capture_task(monkeypatch, vp)
    vp.process_video.run(vid, generation)
    assert len(pending) == 1
    await pending[0]
    assert owners == {key: "tail"}
    async with TestSessionLocal() as db:
        assert (await db.get(Video, vid)).status == VideoStatus.ready_subtitles


@pytest.mark.parametrize("generation", [None, GENERATION])
async def test_ready_tail_replay_finishes_publication_without_translation_or_transcode(monkeypatch, generation):
    from app.services import difficulty_service, subtitle_metrics_service, video_publish
    from app.tasks import scoring_tasks
    from app.tasks import video_processing as vp

    vid = await seed(generation, VideoStatus.ready)
    key = run_identity(vid, generation)
    held = set()
    published_under_lock = []
    original_publish = video_publish._publish_video

    def acquire(run_key):
        assert run_key == key
        assert run_key not in held
        held.add(run_key)
        return True

    async def publish(db, video, **kwargs):
        published_under_lock.append(key in held)
        await original_publish(db, video, **kwargs)

    monkeypatch.setattr(vp, "acquire_lock", acquire)
    monkeypatch.setattr(vp, "release_lock_and_steps", held.remove)
    monkeypatch.setattr(vp, "require_playback", AsyncMock())
    monkeypatch.setattr(video_publish, "require_publishable", AsyncMock())
    monkeypatch.setattr(video_publish, "_publish_video", publish)
    monkeypatch.setattr(vp, "_register_standard", AsyncMock())
    monkeypatch.setattr(vp, "update_progress", AsyncMock())
    monkeypatch.setattr(scoring_tasks.compute_video_score_task, "delay", MagicMock())
    monkeypatch.setattr(difficulty_service, "compute_video_difficulty", AsyncMock())
    monkeypatch.setattr(subtitle_metrics_service, "compute_video_speech_metrics", AsyncMock())
    steps = AsyncMock()
    monkeypatch.setattr(vp, "run_steps", steps)
    pending = capture_task(monkeypatch, vp)
    # This is a redelivery of the same generation after ready was committed.
    vp.finalize_video.run(vid, None, generation)
    await pending.pop()
    assert published_under_lock == [True]
    assert held == set()
    steps.assert_not_awaited()
    async with TestSessionLocal() as db:
        video = await db.get(Video, vid)
        assert video.status == VideoStatus.ready
        assert video.is_published is True
        assert video.reviewed_by == "system:auto_publish"
        assert (await db.scalar(select(Subtitle).where(Subtitle.video_id == vid))).text_en == "A fixture."
    # A further duplicate remains idempotent for publication and expensive steps.
    vp.finalize_video.run(vid, None, generation)
    await pending.pop()
    assert published_under_lock == [True]
    steps.assert_not_awaited()
