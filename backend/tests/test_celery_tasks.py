"""Direct-execution tests for Celery task bodies.

conftest stubs ``.delay`` / ``.apply_async`` so tasks never dispatch through a
broker; these tests call the task functions directly. The body runs through
``run_async`` on the shared celery-asyncio loop against the test database
(conftest routes ``async_session`` to the test session maker).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_async_session_maker
from app.models.video import Video, VideoSource, VideoStatus
from app.tasks.scoring_tasks import compute_top_scores


def _session_maker() -> async_sessionmaker[AsyncSession]:
    """Resolve the test-routed session maker via the shared seam.

    ``app.core.database.get_async_session_maker`` reads ``async_session`` at
    call time, so conftest's monkeypatch routes it to the in-memory test
    session maker; a module-level ``from app.core.database import
    async_session`` would instead capture the real engine at collection time.
    """
    return get_async_session_maker()


async def test_compute_top_scores_scores_ready_videos():
    async with _session_maker()() as db:
        video = Video(
            title="Score Me",
            source_url="https://example.com/v.mp4",
            video_source=VideoSource.imported,
            status=VideoStatus.ready,
            is_official=True,
            review_status="published",
        )
        db.add(video)
        await db.commit()
        vid = video.id

    compute_top_scores(limit=10)  # must not raise

    async with _session_maker()() as db:
        row = (await db.execute(select(Video).where(Video.id == vid))).scalars().first()
        assert row is not None
        assert row.score_updated_at is not None
