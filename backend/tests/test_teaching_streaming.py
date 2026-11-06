"""P02.2: streamed tutor blocks, usage states, cancellation and rights loss."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import select

from app.core.errors import AppError
from app.core.security import create_token
from app.models.teaching import ExamAnalysisRevision
from app.models.v2_runtime import AgentRun, AgentRunEvent, AgentStep, TeachingMessage, TeachingMessageBlock
from app.services import teaching_gateway, teaching_runs
from app.services.teaching.streaming import CitationStream
from tests.conftest import TestSessionLocal
from tests.test_teaching_dialogue import create_turn, setup

# Captured before any test replaces the module attribute.
_REAL_CLIENT = httpx.AsyncClient


def context(summary: str = "analysis"):
    return {
        "learning_context": {
            "task": {"session_id": "one"},
            "progress": {},
            "cards": [
                {"kind": "question", "card_id": "one:question", "payload": {}},
                {"kind": "analysis", "card_id": "one:analysis", "payload": {"summary": summary}},
                {"kind": "evidence", "card_id": "one:evidence", "payload": {}},
            ],
        },
        "history": [],
        "history_truncated": False,
    }


def stream_model(monkeypatch, chunks, *, usage="reported", finish="stop", gate=None):
    """A gateway that streams SSE chunks; ``gate`` runs before the second chunk."""
    calls = []
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
        calls.append(json.loads(request.content))

        async def body():
            for index, text in enumerate(chunks):
                if index == 1 and gate is not None:
                    await gate()
                yield f"data: {json.dumps({'choices': [{'delta': {'content': text}}]})}\n\n".encode()
            yield (f"data: {json.dumps({'choices': [{'delta': {}, 'finish_reason': finish}]})}\n\n".encode())
            if usage == "reported":
                chunk = {"choices": [], "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7}}
                yield f"data: {json.dumps(chunk)}\n\n".encode()
            elif usage == "null":
                yield b'data: {"choices": [], "usage": null}\n\n'
            yield b"data: [DONE]\n\n"

        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body())

    monkeypatch.setattr(
        teaching_gateway.httpx,
        "AsyncClient",
        lambda *a, **kw: _REAL_CLIENT(*a, transport=httpx.MockTransport(handler), **kw),
    )
    return calls


def enable_streaming(monkeypatch):
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: SimpleNamespace(teaching_streaming_enabled=True),
    )


async def reveal(client, state, headers):
    base = f"/api/v1/teaching/sessions/{state['id']}"
    state = (
        await client.post(
            base + "/attempts",
            headers=headers,
            json={
                "operation_id": "initial",
                "expected_revision": state["revision"],
                "item_id": state["current_item_id"],
                "answer": "A",
            },
        )
    ).json()
    return (
        await client.post(
            base + "/reveal",
            headers=headers,
            json={
                "operation_id": "reveal",
                "expected_revision": state["revision"],
                "item_id": state["current_item_id"],
            },
        )
    ).json()


async def run_turn(client, db_session, monkeypatch, gate=None, chunks=None, **model_options):
    user, _revision, _question, state, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    state = await reveal(client, state, headers)
    calls = stream_model(monkeypatch, chunks or ["原文支持[1]。", "所以选 B。"], gate=gate, **model_options)
    enable_streaming(monkeypatch)
    turn = await create_turn(client, state, headers, operation="turn-stream")
    assert turn.status_code == 202
    return user, state, headers, calls, turn.json()


async def test_parser_strips_markers_splits_sentences_and_keeps_unknown_brackets():
    stream = CitationStream(2)
    assert stream.feed("原文支持[1]。") == ["原文支持。"]
    assert stream.feed("另一个[2]") == []
    assert stream.finish() == ["另一个"]
    assert stream.text == "原文支持。另一个"
    assert stream.citations == [1, 2]
    literal = CitationStream(1)
    assert literal.feed("[abc] 保留") == []
    assert literal.finish() == ["[abc] 保留"]


async def test_parser_holds_a_marker_split_across_deltas():
    stream = CitationStream(1)
    assert stream.feed("支持[") == []
    assert stream.feed("1") == []
    assert stream.feed("]。") == ["支持。"]
    assert stream.citations == [1]


async def test_parser_rejects_out_of_range_markers_and_oversized_text():
    with pytest.raises(AppError):
        CitationStream(2).feed("[3]")
    with pytest.raises(AppError):
        CitationStream(1, max_chars=3).feed("abcd")


async def test_parser_cuts_long_unpunctuated_text_at_the_block_limit():
    stream = CitationStream(1, block_chars=10)
    assert stream.feed("abcdefghijklm") == ["abcdefghij"]
    assert stream.finish() == ["klm"]


async def test_gateway_stream_reports_model_stream_and_usage(monkeypatch):
    calls = stream_model(monkeypatch, ["原文", "支持[1]。"])
    events = [
        event
        async for event in teaching_gateway.stream_tutor_reply(
            "u",
            "r",
            "call",
            "为什么选 B？",
            datetime.now(UTC) + timedelta(seconds=30),
            before_dispatch=lambda: _ctx(),
        )
    ]
    assert [event["text"] for event in events if event["type"] == "delta"] == ["原文", "支持[1]。"]
    assert events[-1]["type"] == "done"
    assert events[-1]["usage_status"] == "reported"
    payload = calls[0]
    assert payload["stream"] is True and payload["stream_options"] == {"include_usage": True}
    assert payload["model"] == "tutor" and payload["max_tokens"] == 1024
    assert "response_format" not in payload  # plain text markers, not JSON mode


async def _ctx():
    return context()


async def test_gateway_stream_distinguishes_null_from_missing_usage(monkeypatch):
    for mode, expected in (("null", "unknown"), ("missing", "missing")):
        stream_model(monkeypatch, ["原文[1]。"], usage=mode)
        events = [
            event
            async for event in teaching_gateway.stream_tutor_reply(
                "u", "r", "call", "问", datetime.now(UTC) + timedelta(seconds=30), before_dispatch=_ctx
            )
        ]
        assert events[-1]["usage_status"] == expected


async def test_streamed_turn_publishes_blocks_and_finalises_the_message(client, db_session, monkeypatch):
    _user, state, headers, _calls, run = await run_turn(client, db_session, monkeypatch)
    expected = next(card["card_id"] for card in state["cards"] if card["kind"] in {"question", "analysis", "evidence"})
    await teaching_runs.execute(run["run_id"])

    async with TestSessionLocal() as db:
        message = (
            (
                await db.execute(
                    select(TeachingMessage).where(
                        TeachingMessage.run_id == run["run_id"], TeachingMessage.role == "assistant"
                    )
                )
            )
            .scalars()
            .one()
        )
        blocks = (
            (
                await db.execute(
                    select(TeachingMessageBlock)
                    .where(TeachingMessageBlock.message_id == message.id)
                    .order_by(TeachingMessageBlock.ordinal)
                )
            )
            .scalars()
            .all()
        )
        step = (await db.execute(select(AgentStep).where(AgentStep.run_id == run["run_id"]))).scalars().one()
        stored = (await db.execute(select(AgentRun).where(AgentRun.id == run["run_id"]))).scalars().one()
        events = (
            (
                await db.execute(
                    select(AgentRunEvent).where(AgentRunEvent.run_id == run["run_id"]).order_by(AgentRunEvent.sequence)
                )
            )
            .scalars()
            .all()
        )

    assert stored.status == "succeeded"
    assert message.status == "complete"
    assert [block.text for block in blocks] == ["原文支持。", "所以选 B。"]
    assert message.body == {"text": "原文支持。所以选 B。", "citation_ids": [expected], "suggested_answer": None}
    assert step.safe_result == {
        "streamed": True,
        "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
        "usage_status": "reported",
    }
    kinds = [event.type for event in events]
    assert kinds.count("message.block") == 2
    assert kinds[-2:] == ["message.upsert", "run.completed"]

    page = await client.get(f"/api/v1/teaching/sessions/{state['id']}/messages", headers=headers)
    assistant = page.json()["items"][-1]
    assert assistant["status"] == "complete"
    assert [block["text"] for block in assistant["blocks"]] == ["原文支持。", "所以选 B。"]
    assert assistant["body"]["citation_ids"] == [expected]

    stream = await client.get(run["events_url"] + "?after=0", headers=headers)
    assert "event: message.block" in stream.text
    block_event = next(
        line.removeprefix("data: ")
        for line in stream.text.splitlines()
        if line.startswith("data: ") and '"message_status"' in line
    )
    event = json.loads(block_event)
    assert event["type"] == "message.block"
    assert event["payload"]["message_status"] == "complete"
    assert set(event["payload"]["block"]) == {"id", "ordinal", "text"}


async def test_cancel_mid_stream_keeps_published_blocks_and_stops(client, db_session, monkeypatch):
    first = asyncio.Event()
    release = asyncio.Event()

    async def gate():
        first.set()
        await release.wait()

    _user, _state, headers, _calls, run = await run_turn(
        client, db_session, monkeypatch, gate=gate, chunks=["原文支持[1]。", "未完成的半句"]
    )
    task = asyncio.create_task(teaching_runs.execute(run["run_id"]))
    await asyncio.wait_for(first.wait(), timeout=10)
    cancelled = await client.post(f"/api/v1/teaching/runs/{run['run_id']}/cancel", headers=headers)
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    release.set()
    await asyncio.wait_for(task, timeout=10)

    async with TestSessionLocal() as db:
        message = (
            (
                await db.execute(
                    select(TeachingMessage).where(
                        TeachingMessage.run_id == run["run_id"], TeachingMessage.role == "assistant"
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
        step = (await db.execute(select(AgentStep).where(AgentStep.run_id == run["run_id"]))).scalars().one()
        stored = (await db.execute(select(AgentRun).where(AgentRun.id == run["run_id"]))).scalars().one()
    assert stored.status == "cancelled"
    assert message.status == "interrupted"
    assert [block.text for block in blocks] == ["原文支持。"]
    # The un-published tail never enters the body.
    assert message.body["text"] == "原文支持。"
    assert step.status == "uncertain"


async def test_revoked_material_mid_stream_fails_the_run_without_new_blocks(client, db_session, monkeypatch):
    revision_id = {}

    async def withdraw():
        async with TestSessionLocal() as db:
            revision = await db.get(ExamAnalysisRevision, revision_id["id"])
            revision.rights_policy = {**revision.rights_policy, "model_processing": False}
            await db.commit()

    user, _revision, _question, state, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    state = await reveal(client, state, headers)
    revision_id["id"] = state["items"][0]["content_revision_id"]
    stream_model(monkeypatch, ["原文支持[1]。", "第二段[1]。"], gate=withdraw)
    enable_streaming(monkeypatch)
    turn = await create_turn(client, state, headers, operation="turn-rights")
    await teaching_runs.execute(turn.json()["run_id"])

    async with TestSessionLocal() as db:
        message = (
            (
                await db.execute(
                    select(TeachingMessage).where(
                        TeachingMessage.run_id == turn.json()["run_id"], TeachingMessage.role == "assistant"
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
        stored = (await db.execute(select(AgentRun).where(AgentRun.id == turn.json()["run_id"]))).scalars().one()
    assert stored.status == "needs_retry" and stored.error_code == "CONTENT_RESTRICTED"
    assert message.status == "interrupted"
    assert [block.text for block in blocks] == ["原文支持。"]


async def test_truncated_stream_is_not_published_as_a_complete_reply(client, db_session, monkeypatch):
    user, _revision, _question, state, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    state = await reveal(client, state, headers)
    stream_model(monkeypatch, ["原文支持[1]。"], finish="length")
    enable_streaming(monkeypatch)
    turn = await create_turn(client, state, headers, operation="turn-cut")
    await teaching_runs.execute(turn.json()["run_id"])

    async with TestSessionLocal() as db:
        message = (
            (
                await db.execute(
                    select(TeachingMessage).where(
                        TeachingMessage.run_id == turn.json()["run_id"], TeachingMessage.role == "assistant"
                    )
                )
            )
            .scalars()
            .one()
        )
        stored = (await db.execute(select(AgentRun).where(AgentRun.id == turn.json()["run_id"]))).scalars().one()
    assert stored.status == "needs_retry" and stored.error_code == "AI_SERVICE_UNAVAILABLE"
    assert message.status == "interrupted"


async def test_stream_without_finish_reason_is_not_success(client, db_session, monkeypatch):
    _user, _revision, _question, state, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(_user.id)}"}
    state = await reveal(client, state, headers)
    stream_model(monkeypatch, ["原文支持[1]。"], finish=None)
    enable_streaming(monkeypatch)
    turn = await create_turn(client, state, headers, operation="turn-nofinish")
    await teaching_runs.execute(turn.json()["run_id"])

    async with TestSessionLocal() as db:
        stored = (await db.execute(select(AgentRun).where(AgentRun.id == turn.json()["run_id"]))).scalars().one()
        message = (
            (
                await db.execute(
                    select(TeachingMessage).where(
                        TeachingMessage.run_id == turn.json()["run_id"], TeachingMessage.role == "assistant"
                    )
                )
            )
            .scalars()
            .one()
        )
    assert stored.status == "needs_retry" and stored.error_code == "AI_SERVICE_UNAVAILABLE"
    assert message.status == "interrupted"


async def test_restricted_block_events_do_not_raise(client, db_session, monkeypatch):
    _user, _revision, _question, state, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(_user.id)}"}
    state = await reveal(client, state, headers)
    stream_model(monkeypatch, ["原文支持[1]。"])
    enable_streaming(monkeypatch)
    turn = await create_turn(client, state, headers, operation="turn-restrict")
    await teaching_runs.execute(turn.json()["run_id"])

    async with TestSessionLocal() as db:
        revision = await db.get(ExamAnalysisRevision, state["items"][0]["content_revision_id"])
        revision.rights_policy = {**revision.rights_policy, "site_display": False}
        await db.commit()

    stream = await client.get(turn.json()["events_url"] + "?after=0", headers=headers)
    assert stream.status_code == 200
    assert "event: content.restricted" in stream.text
    assert "原文支持" not in stream.text
