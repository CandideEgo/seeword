"""Fence a pipeline transaction to its server-issued video processing attempt.

The fence is attached only to a worker's own SQLAlchemy session, not globally.
Synchronous Session events run inside AsyncSession's SQLAlchemy greenlet: they
can lock/check the owning row before an ORM flush, explicit DML or commit.
This covers existing step helpers without changing their commit ownership.
"""

from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from typing import Any
from uuid import UUID

from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import ORMExecuteState, Session

from app.models.video import Video


class StaleProcessingGenerationError(Exception):
    """A replaced or deleted run must roll back, not fail the current video."""


def run_identity(video_id: str, generation: str | None) -> str:
    """Redis namespaces keep a stale worker away from the new run's locks/steps."""
    return f"{video_id}:{generation}" if generation else video_id


def artifact_identity(video_id: str, generation: str | None) -> str:
    """Generated files are immutable between attempts; legacy paths stay valid."""
    if generation is None:
        return video_id
    return f"{video_id}_g{UUID(generation).hex}"


@contextmanager
def fence_session(db: AsyncSession, video_id: str, generation: str | None) -> Iterator[None]:
    """Lock/check before every write, using the same transaction as that write.

    No cached ORM value may authorize a write. A concurrent admin reset also
    locks Video before changing the generation, so exactly one side commits
    first. An old message with no generation matches only a legacy NULL row.
    """
    session = db.sync_session

    def check(sync: Session) -> None:
        column = Video.__table__.c.processing_generation
        row = (
            sync.connection().execute(select(column).where(Video.__table__.c.id == video_id).with_for_update()).first()
        )
        if row is None or row[0] != generation:
            raise StaleProcessingGenerationError("Video processing attempt was replaced or deleted")

    def before_flush(sync: Session, _context, _instances) -> None:
        check(sync)

    def before_execute(state: ORMExecuteState) -> None:
        if state.is_insert or state.is_update or state.is_delete:
            check(state.session)

    event.listen(session, "before_flush", before_flush)
    event.listen(session, "before_commit", check)
    event.listen(session, "do_orm_execute", before_execute)
    try:
        yield
    finally:
        event.remove(session, "before_flush", before_flush)
        event.remove(session, "before_commit", check)
        event.remove(session, "do_orm_execute", before_execute)


@asynccontextmanager
async def processing_session(
    factory: Callable[[], Any], video_id: str, generation: str | None
) -> AsyncIterator[AsyncSession]:
    """Own a task session and silently discard a replaced attempt, not its successor."""
    from app.core.logging import get_logger

    async with factory() as db:
        try:
            with fence_session(db, video_id, generation):
                yield db
        except StaleProcessingGenerationError:
            await db.rollback()
            get_logger(__name__).info("stale_pipeline_attempt_ignored", video_id=video_id)
            # Only a replaced attempt may be cleaned up here. Normal task
            # hand-offs explicitly release their lock before enqueueing the
            # successor; a second DEL on normal exit could delete its lock.
            from app.tasks.pipeline_helpers import release_lock

            release_lock(run_identity(video_id, generation))
