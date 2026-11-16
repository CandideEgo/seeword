"""Attempt fencing: real ORM/explicit writes, legacy messages and outbox identity."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select, update

from app.models.pipeline_dispatch import PipelineDispatch
from app.models.subtitle import Subtitle
from app.models.video import Video, VideoStatus
from app.services import pipeline_dispatch as dispatch
from app.services.processing_generation import (
    StaleProcessingGenerationError,
    artifact_identity,
    fence_session,
    run_identity,
)


async def seed(factory, generation):
    async with factory() as db:
        video = Video(
            title="Generation fixture",
            source_url="https://example.com/fixture",
            video_source="imported",
            status=VideoStatus.processing,
            processing_generation=generation,
        )
        db.add(video)
        await db.flush()
        db.add(Subtitle(video_id=video.id, start_time=0, end_time=1, text_en="Original", sentence_index=0))
        await db.commit()
        return video.id


@pytest.mark.parametrize("backend", ["sqlite", pytest.param("postgres", marks=pytest.mark.integration)])
@pytest.mark.parametrize("write_kind", ["flush", "commit", "explicit"])
async def test_replaced_attempt_cannot_write(backend, write_kind):
    from app.core.database import async_session as factory

    old, new = str(uuid4()), str(uuid4())
    vid = await seed(factory, old)
    async with factory() as worker:
        video = await worker.get(Video, vid)
        sub = await worker.scalar(select(Subtitle).where(Subtitle.video_id == vid))
        # Leave stale objects in the identity map, but release the read transaction.
        await worker.commit()
        async with factory() as admin:
            await admin.execute(update(Video).where(Video.id == vid).values(processing_generation=new, title="New run"))
            await admin.commit()
        with fence_session(worker, vid, old):
            with pytest.raises(StaleProcessingGenerationError):
                if write_kind == "explicit":
                    await worker.execute(update(Subtitle).where(Subtitle.video_id == vid).values(text_zh="Stale"))
                else:
                    video.title = "Stale title"
                    sub.text_zh = "Stale translation"
                    await (worker.flush() if write_kind == "flush" else worker.commit())
            await worker.rollback()
    async with factory() as db:
        assert (await db.get(Video, vid)).title == "New run"
        assert (await db.scalar(select(Subtitle).where(Subtitle.video_id == vid))).text_zh is None


@pytest.mark.parametrize("backend", ["sqlite", pytest.param("postgres", marks=pytest.mark.integration)])
@pytest.mark.parametrize("generation", [None, "new"])
async def test_legacy_only_matches_null(backend, generation):
    from app.core.database import async_session as factory

    gen = str(uuid4()) if generation else None
    vid = await seed(factory, gen)
    async with factory() as db:
        with fence_session(db, vid, None):
            if gen:
                with pytest.raises(StaleProcessingGenerationError):
                    await db.execute(update(Video).where(Video.id == vid).values(title="Legacy"))
                await db.rollback()
            else:
                await db.execute(update(Video).where(Video.id == vid).values(title="Legacy"))
                await db.commit()
    async with factory() as db:
        assert (await db.get(Video, vid)).title == ("Generation fixture" if gen else "Legacy")


async def test_generation_args_and_old_intent_abandoned(monkeypatch):
    from app.core.database import async_session as factory

    old, new = str(uuid4()), str(uuid4())
    vid = await seed(factory, old)
    sent = []
    monkeypatch.setattr(dispatch, "_send_task", lambda *args: sent.append(args))
    async with factory() as db:
        row_id = await dispatch.enqueue(db, video_id=vid, task_name=dispatch.PROCESS_VIDEO_TASK, args=[vid])
        await db.commit()
        row = await db.get(PipelineDispatch, row_id)
        assert row.args == [vid, old]
        await db.execute(update(Video).where(Video.id == vid).values(processing_generation=new))
        await db.commit()
        assert await dispatch.pending_video_ids(db, [vid]) == set()
        assert await dispatch.dispatch_now(db, row_id) is False
        assert row.status == "abandoned"
        assert sent == []
        assert await dispatch.enqueue(db, video_id=vid, task_name=dispatch.PROCESS_VIDEO_TASK, args=[vid]) == row_id
        await db.commit()
        assert await dispatch.dispatch_now(db, row_id)
        assert sent[0][1] == [vid, new]


@pytest.mark.integration
async def test_waiting_old_write_checks_generation_after_row_lock():
    from app.core.database import async_session as factory

    old, new = str(uuid4()), str(uuid4())
    vid = await seed(factory, old)
    started = asyncio.Event()

    async def late_worker():
        async with factory() as db:
            with fence_session(db, vid, old):
                started.set()
                with pytest.raises(StaleProcessingGenerationError):
                    await db.execute(update(Subtitle).where(Subtitle.video_id == vid).values(text_zh="Too late"))
                await db.rollback()

    async with factory() as admin:
        video = await admin.scalar(select(Video).where(Video.id == vid).with_for_update())
        video.processing_generation = new
        await admin.flush()
        task = asyncio.create_task(late_worker())
        await started.wait()
        # Scheduling barrier proves the old writer has not bypassed the row lock.
        await asyncio.sleep(0.05)
        assert not task.done()
        await admin.commit()
    await asyncio.wait_for(task, timeout=10)
    async with factory() as db:
        assert (await db.scalar(select(Subtitle).where(Subtitle.video_id == vid))).text_zh is None


def test_attempt_identities_are_distinct_and_legacy_compatible():
    vid, generation = str(uuid4()), str(uuid4())
    assert run_identity(vid, None) == artifact_identity(vid, None) == vid
    assert run_identity(vid, generation) == f"{vid}:{generation}"
    assert artifact_identity(vid, generation) == f"{vid}_g{generation.replace('-', '')}"
    for task, args in [
        (dispatch.PROCESS_VIDEO_TASK, [vid]),
        (dispatch.FINALIZE_VIDEO_TASK, [vid, None]),
        (dispatch.LOCALIZE_VIDEO_TASK, [vid, False]),
        (dispatch.GPU_TRANSCRIBE_TASK, [vid, "source", "imported", None]),
    ]:
        assert dispatch._generation_args(task, args, generation) == [*args, generation]
        with pytest.raises(ValueError):
            dispatch._generation_args(task, [*args, str(uuid4())], generation)
