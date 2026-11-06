"""Postgres integration test for Celery task bodies (D2 follow-up).

The in-memory SQLite suite cannot express row-locking semantics, so
Postgres-specific scoring coverage lives here.

Marked ``integration`` (see pytest.ini). It skips when no Postgres is
reachable; CI's backend job provisions one (``DATABASE_URL`` points at the
service Postgres). Locally:

    docker compose -f docker-compose.dev.yml up -d db
    PG_TEST_URL=postgresql+asyncpg://seeword:seeword_dev@localhost:5432/seeword pytest tests/test_celery_tasks_pg.py -v

Notes:
- Task bodies execute on the shared celery-asyncio background loop via
  ``run_async``; the test body runs on the pytest loop. conftest's Postgres
  engine uses ``NullPool`` so every session opens a fresh loop-local
  connection (asyncpg connections are loop-bound).
"""

import pytest
from sqlalchemy import select

from app.core.database import get_async_session_maker
from app.models.video import Video, VideoSource, VideoStatus
from app.tasks.scoring_tasks import compute_top_scores

pytestmark = pytest.mark.integration


def _session_maker():
    """Resolve the Postgres-routed session maker via the shared seam.

    conftest's integration branch monkeypatches ``async_session`` to the
    Postgres session maker; ``get_async_session_maker`` reads it at call time.
    """
    return get_async_session_maker()


async def test_compute_top_scores_scores_ready_videos_on_pg():
    """Scoring sweep runs on PG (BigInteger view_count, JSON columns)."""
    async with _session_maker()() as db:
        video = Video(
            title="PG Score Me",
            source_url="https://example.com/pg.mp4",
            video_source=VideoSource.imported,
            status=VideoStatus.ready,
            is_official=True,
            review_status="published",
            view_count=5000,  # BigInteger column
            external_meta={"level": "CET-4"},  # JSON column
        )
        db.add(video)
        await db.commit()
        vid = video.id

    compute_top_scores(limit=10)  # must not raise on PG

    async with _session_maker()() as db:
        row = (await db.execute(select(Video).where(Video.id == vid))).scalars().first()
        assert row is not None
        assert row.score is not None
        assert row.score_updated_at is not None
