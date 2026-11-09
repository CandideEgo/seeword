"""Real PostgreSQL transactions for the P02.4 quiz surface.

The concurrency question a single-connection test cannot answer: two identical
clicks arriving at the same time must produce one attempt, because the receipt
(``TeachingOperation``) is claimed by a unique index before any effect, and the
loser waits on the row lock instead of inserting a second attempt.

Never point ``PG_TEST_URL`` at a development, UI, or production database.
"""

import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.database import get_async_session_maker
from app.core.errors import AppError
from app.models.teaching import TeachingAttempt
from app.services import v2_access
from app.services.teaching import commands, service
from app.services.teaching.principal import Principal
from app.schemas.teaching import SessionActionRequest
from tests.teaching_fixtures import seed_quiz_content

pytestmark = pytest.mark.integration


async def seed(monkeypatch):
    async with get_async_session_maker()() as db:
        user, paper, revisions = await seed_quiz_content(db)
        monkeypatch.setattr(
            v2_access, "get_settings", lambda: SimpleNamespace(teaching_enabled=True, teaching_allowed_user_ids=user.id)
        )
        return user.id, paper.id, [revision.id for revision in revisions]


async def start_quiz(user_id, paper_id, operation_id="quiz"):
    async with get_async_session_maker()() as db:
        result = await service.create_quiz(db, Principal(user_id), {"operation_id": operation_id, "paper_id": paper_id})
        await db.commit()
        return result


async def test_concurrent_click_on_one_action_creates_one_attempt(monkeypatch):
    user_id, paper_id, _revisions = await seed(monkeypatch)
    state = await start_quiz(user_id, paper_id)
    item_id, revision = state["items"][0]["id"], state["revision"]
    barrier = asyncio.Barrier(2)

    async def click():
        async with get_async_session_maker()() as db:
            body = SessionActionRequest(
                operation_id="click-once",
                expected_revision=revision,
                action="attempts",
                item_id=item_id,
                answer="B",
            )
            await barrier.wait()
            try:
                result = await commands.execute(db, Principal(user_id), state["id"], body)
                await db.commit()
                return result
            except AppError as exc:
                await db.rollback()
                return exc

    first, second = await asyncio.gather(click(), click())
    # The receipt is claimed before any effect: one call wins, the other either
    # replays the same result or reports the action as still in flight.
    errors = [row for row in (first, second) if isinstance(row, AppError)]
    assert all(isinstance(exc, AppError) and exc.code in {"TEACHING_STATE_CONFLICT"} for exc in errors)

    async with get_async_session_maker()() as db:
        attempts = await db.scalar(
            select(func.count()).select_from(TeachingAttempt).where(TeachingAttempt.item_id == item_id)
        )
        assert attempts == 1


async def test_concurrent_quiz_creation_with_one_operation_id(monkeypatch):
    user_id, paper_id, _revisions = await seed(monkeypatch)
    barrier = asyncio.Barrier(2)

    async def start():
        async with get_async_session_maker()() as db:
            await barrier.wait()
            try:
                result = await service.create_quiz(
                    db, Principal(user_id), {"operation_id": "quiz-once", "paper_id": paper_id}
                )
                await db.commit()
                return result
            except AppError as exc:
                await db.rollback()
                return exc

    first, second = await asyncio.gather(start(), start())
    ids = {row["id"] for row in (first, second) if isinstance(row, dict)}
    assert len(ids) == 1, "two clicks created two quizzes"

    async with get_async_session_maker()() as db:
        sessions = await db.scalar(select(func.count()).select_from(service.TeachingSession))
        assert sessions == 1
