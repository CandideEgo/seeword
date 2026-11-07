"""P02.3 chat concurrency under real PG locks: one run, one message, clean delete."""

import asyncio
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.database import get_async_session_maker
from app.models.v2_runtime import AgentRun, AgentRunEvent, AgentStep, TeachingMessage, TutorConversation
from app.services import teaching_runs, tutor_conversations, v2_access
from app.services.teaching import service as core
from tests.test_v2_runtime_pg import seed

pytestmark = pytest.mark.integration


async def prepare(monkeypatch):
    user_id, _revision, _state = await seed(monkeypatch)
    settings = v2_access.get_settings()
    settings.teaching_enabled = True
    settings.teaching_runs_enabled = True
    settings.teaching_dialogue_enabled = True
    settings.teaching_conversations_enabled = True
    settings.teaching_allowed_user_ids = user_id
    settings.teaching_streaming_enabled = False
    async with get_async_session_maker()() as db:
        created = await tutor_conversations.create(db, core.Principal(user_id), SimpleNamespace(title="并发"))
        await db.commit()
    return user_id, created["id"]


async def test_two_creators_share_one_chat_run_and_one_user_message(monkeypatch):
    user_id, conversation_id = await prepare(monkeypatch)
    body = SimpleNamespace(
        operation_id="same-chat-turn", message="affect 和 effect", session_id=None, expected_revision=None
    )
    barrier = asyncio.Barrier(2)

    async def create():
        async with get_async_session_maker()() as db:
            await barrier.wait()
            result = await teaching_runs.start_conversation_turn(db, core.Principal(user_id), conversation_id, body)
            await db.commit()
            return result

    a, b = await asyncio.gather(create(), create())
    assert a["run_id"] == b["run_id"]
    async with get_async_session_maker()() as db:
        assert await db.scalar(select(func.count()).select_from(AgentRun)) == 1
        assert await db.scalar(select(func.count()).select_from(TeachingMessage)) == 1


async def test_deleting_a_chat_mid_run_settles_without_crashing(monkeypatch):
    user_id, conversation_id = await prepare(monkeypatch)
    principal = core.Principal(user_id)
    async with get_async_session_maker()() as db:
        created = await teaching_runs.start_conversation_turn(
            db,
            principal,
            conversation_id,
            SimpleNamespace(
                operation_id="deleted-mid-run", message="这是什么", session_id=None, expected_revision=None
            ),
        )
        await db.commit()
    ready, finish = asyncio.Event(), asyncio.Event()

    async def controlled(_user, _run, _logical, _message, _context, _deadline, *, before_dispatch):
        await before_dispatch()
        ready.set()
        await finish.wait()
        raise teaching_runs.AppError(502, "AI_SERVICE_UNAVAILABLE", "synthetic")

    monkeypatch.setattr(teaching_runs, "tutor_reply", controlled)
    worker = asyncio.create_task(teaching_runs.execute(created["run_id"]))
    await asyncio.wait_for(ready.wait(), 5)
    async with get_async_session_maker()() as db:
        await tutor_conversations.delete_chat(db, principal, conversation_id)
        await db.commit()
    finish.set()
    await asyncio.wait_for(worker, 10)
    async with get_async_session_maker()() as db:
        assert await db.scalar(select(func.count()).select_from(TutorConversation)) == 0
        assert await db.scalar(select(func.count()).select_from(AgentRun)) == 0
        assert await db.scalar(select(func.count()).select_from(AgentRunEvent)) == 0
        assert await db.scalar(select(func.count()).select_from(AgentStep)) == 0
        assert await db.scalar(select(func.count()).select_from(TeachingMessage)) == 0
