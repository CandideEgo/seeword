"""Streamed blocks under real PostgreSQL locks: cancellation fences publication."""

import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import func, select

from app.core.database import get_async_session_maker
from app.models.v2_runtime import AgentRun, AgentStep, TeachingMessage, TeachingMessageBlock
from app.services import teaching_gateway, teaching_runs, v2_access
from app.services.teaching import service as core
from tests.test_v2_runtime_pg import seed

pytestmark = pytest.mark.integration

_REAL_CLIENT = httpx.AsyncClient


def install_stream(monkeypatch, chunks, gate):
    settings = SimpleNamespace(
        llm_gateway_governance_verified=True,
        llm_gateway_base_url="http://gateway.test",
        llm_gateway_admin_key="admin-key",
        llm_gateway_v2_team_id="team",
        llm_gateway_tutor_model="tutor",
        llm_gateway_tutor_max_tokens=1024,
        v2_run_budget_usd=0.02,
    )
    monkeypatch.setattr(teaching_gateway, "get_settings", lambda: settings)

    def handler(request: httpx.Request):
        if request.url.path == "/user/new":
            return httpx.Response(200, json={})
        if request.url.path == "/key/generate":
            return httpx.Response(200, json={"key": "run-key"})

        async def body():
            for index, text in enumerate(chunks):
                if index == 1:
                    await gate()
                yield f"data: {json.dumps({'choices': [{'delta': {'content': text}}]})}\n\n".encode()
            yield b'data: {"choices": [{"delta": {}, "finish_reason": "stop"}]}\n\n'
            yield b'data: {"choices": [], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}\n\n'
            yield b"data: [DONE]\n\n"

        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body())

    monkeypatch.setattr(
        teaching_gateway.httpx,
        "AsyncClient",
        lambda *a, **kw: _REAL_CLIENT(*a, transport=httpx.MockTransport(handler), **kw),
    )


async def test_cancel_mid_stream_keeps_only_committed_blocks(monkeypatch):
    user_id, _revision_id, state = await seed(monkeypatch, revealed=True)
    v2_access.get_settings().teaching_dialogue_enabled = True
    monkeypatch.setattr("app.core.config.get_settings", lambda: SimpleNamespace(teaching_streaming_enabled=True))
    principal = core.Principal(user_id)
    async with get_async_session_maker()() as db:
        created = await teaching_runs.create(
            db,
            principal,
            state["id"],
            SimpleNamespace(operation_id="stream-pg", expected_revision=state["revision"], message="Explain"),
            response_mode="conversation",
        )
        await db.commit()

    first, release = asyncio.Event(), asyncio.Event()

    async def gate():
        first.set()
        await release.wait()

    install_stream(monkeypatch, ["原文支持[1]。", "第二段[1]。"], gate)
    worker = asyncio.create_task(teaching_runs.execute(created["run_id"]))
    await asyncio.wait_for(first.wait(), 10)
    async with get_async_session_maker()() as db:
        await teaching_runs.cancel(db, principal, created["run_id"])
        await db.commit()
    release.set()
    await asyncio.wait_for(worker, 10)

    async with get_async_session_maker()() as db:
        message = (
            (
                await db.execute(
                    select(TeachingMessage).where(
                        TeachingMessage.run_id == created["run_id"], TeachingMessage.role == "assistant"
                    )
                )
            )
            .scalars()
            .one()
        )
        blocks = (
            (await db.execute(select(TeachingMessageBlock).where(TeachingMessageBlock.message_id == message.id)))
            .scalars()
            .all()
        )
        step = (await db.execute(select(AgentStep).where(AgentStep.run_id == created["run_id"]))).scalars().one()
        run = (await db.execute(select(AgentRun).where(AgentRun.id == created["run_id"]))).scalars().one()
        users = await db.scalar(select(func.count()).select_from(TeachingMessage))
    assert run.status == "cancelled"
    assert message.status == "interrupted"
    assert [block.text for block in blocks] == ["原文支持。"]
    assert step.status == "uncertain"
    assert users == 2  # the user's own turn plus the interrupted assistant message
