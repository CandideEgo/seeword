"""Expire transient confirmations; durable operation receipts are not pruned."""

from app.tasks.async_helpers import run_async
from app.tasks.celery_app import celery_app


async def _cleanup() -> int:
    from app.core.database import get_async_session_maker
    from app.services.delegated_learning import cleanup_expired_intents

    async with get_async_session_maker()() as db:
        count = await cleanup_expired_intents(db)
        await db.commit()
        return count


@celery_app.task
def cleanup_learning_intents():
    return run_async(_cleanup())
