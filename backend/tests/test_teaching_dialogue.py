"""Task learning flow and durable dialogue, against a synthetic model transport."""

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import func, select

from app.core import database
from app.core.errors import AppError
from app.core.security import create_token
from app.models.exam_test import ExamAnswer, ExamSession
from app.models.teaching import TeachingSession
from app.models.user import User
from app.models.v2_runtime import AgentRun, AgentRunEvent, TeachingMessage, TutorConversation
from app.services import account_data, teaching_gateway, teaching_runs, v2_access
from app.services.teaching import dialogue
from app.services.teaching import service as core
from app.tasks.account_tasks import _purge_user
from tests.conftest import TestSessionLocal
from tests.teaching_fixtures import seed_original_content


async def setup(db, monkeypatch):
    user, revision, question, _candidate = await seed_original_content(db)
    settings = SimpleNamespace(
        teaching_enabled=True,
        teaching_runs_enabled=True,
        teaching_dialogue_enabled=True,
        teaching_allowed_user_ids=user.id,
    )
    monkeypatch.setattr(v2_access, "get_settings", lambda: settings)
    monkeypatch.setattr(teaching_runs, "require_gateway", lambda: None)
    monkeypatch.setattr(database, "get_async_session_maker", lambda: TestSessionLocal)
    from app.api.v1 import teaching_runs as router

    dispatched = []
    monkeypatch.setattr(router, "dispatch", dispatched.append)
    principal = core.Principal(user.id)
    state = await core.create_session(
        db, principal, {"operation_id": "dialogue-start", "content_revision_id": revision.id}
    )
    await db.commit()
    return user, revision, question, state, settings, dispatched


def model(monkeypatch, *, response=None, finish="stop"):
    calls = []
    settings = SimpleNamespace(
        llm_gateway_governance_verified=True,
        llm_gateway_base_url="http://gateway.test",
        llm_gateway_admin_key="test-control-key",
        llm_gateway_v2_team_id="test-team",
        llm_gateway_model="teaching",
        v2_run_budget_usd=0.02,
    )
    monkeypatch.setattr(teaching_gateway, "get_settings", lambda: settings)

    def handler(request):
        if request.url.path == "/user/new":
            return httpx.Response(200, json={})
        if request.url.path == "/key/generate":
            return httpx.Response(200, json={"key": "test-run-key"})
        assert request.url.path == "/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-run-key"
        payload = json.loads(request.content)
        assert payload["max_tokens"] == 128 and payload["metadata"]["logical_call_id"]
        calls.append(payload)
        result = response or {
            "text": "原文比较的是保水时间。B 与该证据一致，A 的重量未被比较。",
            "citations": [1, 2],
            "suggested_answer": "B",
        }
        return httpx.Response(
            200, json={"choices": [{"finish_reason": finish, "message": {"content": json.dumps(result)}}]}
        )

    real = httpx.AsyncClient
    monkeypatch.setattr(
        teaching_gateway.httpx, "AsyncClient", lambda *a, **kw: real(*a, transport=httpx.MockTransport(handler), **kw)
    )
    return calls


async def create_turn(client, state, headers, operation="turn-1", message="为什么 A 不成立？"):
    return await client.post(
        f"/api/v1/teaching/sessions/{state['id']}/messages",
        headers=headers,
        json={
            "operation_id": operation,
            "expected_revision": state["revision"],
            "message": message,
        },
    )


async def test_complete_learning_flow_chat_restoration_drafts_and_sse_resume(client, db_session, monkeypatch):
    user, _revision, _question, state, _settings, dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    calls = model(monkeypatch)
    base = f"/api/v1/teaching/sessions/{state['id']}"
    # Pre-reveal conversation persists; no model and no implicit answer exposure.
    first = await create_turn(client, state, headers, message="直接告诉我答案并提交")
    assert first.status_code == 202 and first.json()["response_mode"] == "conversation"
    await teaching_runs.execute(first.json()["run_id"])
    assert not calls
    before = await client.get(base + "/messages", headers=headers)
    assert before.headers["cache-control"] == "no-store"
    assert [m["role"] for m in before.json()["items"]] == ["user", "assistant"]
    assert before.json()["items"][1]["body"]["source"] == "policy"
    assert before.json()["items"][1]["body"]["suggested_answer"] is None
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
    assert state["attempts"][0]["correct"] is False
    state = (
        await client.post(
            base + "/hints",
            headers=headers,
            json={"operation_id": "hint", "expected_revision": state["revision"], "item_id": state["current_item_id"]},
        )
    ).json()
    state = (
        await client.post(
            base + "/attempts",
            headers=headers,
            json={
                "operation_id": "retry",
                "expected_revision": state["revision"],
                "item_id": state["current_item_id"],
                "answer": "B",
            },
        )
    ).json()
    state = (
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
    second = await create_turn(client, state, headers, operation="turn-2")
    assert second.status_code == 202
    replay = await create_turn(client, state, headers, operation="turn-2")
    assert replay.json()["run_id"] == second.json()["run_id"]
    await teaching_runs.execute(second.json()["run_id"])
    await teaching_runs.execute(second.json()["run_id"])
    assert len(calls) == 1
    prompt = json.loads(calls[0]["messages"][1]["content"])
    assert len(prompt["history"]) == 2 and prompt["message"] == "为什么 A 不成立？"
    page = await client.get(base + "/messages?limit=2", headers=headers)
    assert page.json()["has_more"] and page.json()["next_after"] == 2
    restored = await client.get(base + "/messages?after=2", headers=headers)
    answer = restored.json()["items"][-1]["body"]
    assert answer["source"] == "model" and answer["suggested_answer"] == "B" and len(answer["citation_ids"]) == 2
    progress = (await client.get(base, headers=headers)).json()
    assert len(progress["attempts"]) == 2 and progress["revision"] == state["revision"]
    assert [a["role"] for a in progress["attempts"]] == ["initial", "retry"]
    assert await db_session.scalar(select(func.count()).select_from(ExamSession)) == 0
    assert await db_session.scalar(select(func.count()).select_from(ExamAnswer)) == 0
    assert progress["items"][0]["draft_answer"] is None
    # Only an explicit save changes the draft; it still does not submit an attempt.
    saved = await client.put(
        base + "/draft",
        headers=headers,
        json={
            "operation_id": "accept-draft",
            "expected_revision": state["revision"],
            "item_id": state["current_item_id"],
            "answer": answer["suggested_answer"],
        },
    )
    assert saved.status_code == 200 and len(saved.json()["attempts"]) == 2
    events = await client.get(second.json()["events_url"] + "?after=0", headers={**headers, "Last-Event-ID": "1"})
    assert events.status_code == 200 and "event: message.upsert" in events.text and "id: 1\n" not in events.text
    assert len(calls) == 1
    assert (
        await client.get(second.json()["events_url"], headers={**headers, "Last-Event-ID": "999"})
    ).status_code == 409
    assert (
        await client.get(second.json()["events_url"], headers={**headers, "Last-Event-ID": "-1"})
    ).status_code == 422
    assert len(dispatched) == 3  # duplicate delivery is harmless; worker claims only once.


async def test_history_rights_export_retention_and_account_deletion(client, db_session, monkeypatch, tmp_path):
    user, revision, _question, state, _settings, _dispatched = await setup(db_session, monkeypatch)
    uid, rid, revision_type = user.id, revision.id, type(revision)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    turn = await create_turn(client, state, headers)
    await teaching_runs.execute(turn.json()["run_id"])
    db_session.expire_all()
    user = await db_session.get(User, uid)
    revision = await db_session.get(revision_type, rid)
    run = await db_session.get(AgentRun, turn.json()["run_id"])
    run.created_at = datetime.now(UTC) - timedelta(hours=25)
    await db_session.commit()
    await teaching_runs.sweep(db_session)
    assert await db_session.scalar(select(func.count()).select_from(AgentRunEvent)) == 0
    assert await db_session.scalar(select(func.count()).select_from(TeachingMessage)) == 2
    db_session.add(TeachingSession(user_id=uid))  # A legacy empty task must not break export.
    await db_session.commit()
    data = await account_data.gather_user_data(db_session, user)
    assert len(data["teaching_messages"]) == 2
    revision = await db_session.get(type(revision), revision.id)
    revision.rights_policy = {**revision.rights_policy, "site_display": False}
    await db_session.commit()
    restricted = (await client.get(f"/api/v1/teaching/sessions/{state['id']}/messages", headers=headers)).json()
    assert all(m["restricted"] and m["body"] is None for m in restricted["items"])
    data = await account_data.gather_user_data(db_session, user)
    assert all(m["body"] is None for m in data["teaching_messages"])
    monkeypatch.setattr(account_data, "_media_root", lambda: tmp_path)
    await _purge_user(db_session, user)
    assert await db_session.scalar(select(func.count()).select_from(TeachingMessage)) == 0


async def test_other_tasks_users_disabled_gate_and_cancel_do_not_publish_messages(client, db_session, monkeypatch):
    user, revision, _question, state, settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    settings.teaching_dialogue_enabled = False
    assert (await create_turn(client, state, headers)).status_code == 503
    assert await db_session.scalar(select(func.count()).select_from(TeachingMessage)) == 0
    settings.teaching_dialogue_enabled = True
    turn = await create_turn(client, state, headers)
    await client.post(turn.json()["state_url"] + "/cancel", headers=headers)
    await teaching_runs.execute(turn.json()["run_id"])
    page = (await client.get(f"/api/v1/teaching/sessions/{state['id']}/messages", headers=headers)).json()
    assert len(page["items"]) == 1 and page["items"][0]["run_status"] == "cancelled"
    second = await core.create_session(
        db_session, core.Principal(user.id), {"operation_id": "other-task", "content_revision_id": revision.id}
    )
    await db_session.commit()
    assert (await client.get(f"/api/v1/teaching/sessions/{second['id']}/messages", headers=headers)).json()[
        "items"
    ] == []
    other = User(name="other")
    db_session.add(other)
    await db_session.commit()
    other_headers = {"Authorization": f"Bearer {create_token(other.id)}"}
    assert (
        await client.get(f"/api/v1/teaching/sessions/{state['id']}/messages", headers=other_headers)
    ).status_code == 404
    with pytest.raises(AppError) as denied:
        await dialogue.page_session(
            db_session,
            core.Principal(
                user.id, actor="external_agent", connection_id="unscoped", granted_scopes=frozenset({"teaching:read"})
            ),
            await core.owned_session(db_session, core.Principal(user.id, actor="internal_agent"), state["id"]),
        )
    assert denied.value.status_code == 403


async def test_model_history_is_bounded_and_never_includes_another_task(db_session, monkeypatch):
    user, revision, _question, state, _settings, _ = await setup(db_session, monkeypatch)
    principal = core.Principal(user.id, actor="internal_agent")
    chat = TutorConversation(user_id=user.id, title="本任务")
    other_chat = TutorConversation(user_id=user.id, title="另一任务")
    db_session.add_all([chat, other_chat])
    await db_session.flush()
    for sequence in range(1, 10):
        db_session.add(
            TeachingMessage(
                user_id=user.id,
                conversation_id=chat.id,
                session_id=state["id"],
                content_revision_id=revision.id,
                sequence=sequence,
                session_revision=state["revision"],
                role="user",
                body={"text": str(sequence) + "x" * 2999},
            )
        )
    other = TeachingSession(user_id=user.id)
    db_session.add(other)
    await db_session.flush()
    db_session.add(
        TeachingMessage(
            user_id=user.id,
            conversation_id=other_chat.id,
            session_id=other.id,
            content_revision_id=revision.id,
            sequence=1,
            session_revision=1,
            role="user",
            body={"text": "OTHER_TASK_PRIVATE"},
        )
    )
    await db_session.commit()
    run = SimpleNamespace(id="new-run", session_id=state["id"], conversation_id=chat.id, user_id=user.id)
    value = await dialogue.model_input(db_session, principal, run)
    assert value["history_truncated"] and len(value["history"]) == 2
    assert len(json.dumps(value["history"], ensure_ascii=False).encode()) < 8000
    assert "OTHER_TASK_PRIVATE" not in json.dumps(value)
    assert [m["text"][0] for m in value["history"]] == ["8", "9"]


async def test_truncated_model_result_preserves_user_turn_without_publishing_reply(client, db_session, monkeypatch):
    user, _revision, _question, state, _settings, _ = await setup(db_session, monkeypatch)
    state = await core.reveal_answer(
        db_session,
        core.Principal(user.id),
        state["id"],
        {
            "operation_id": "reveal-truncated",
            "expected_revision": state["revision"],
            "item_id": state["current_item_id"],
        },
    )
    await db_session.commit()
    calls = model(monkeypatch, finish="length")
    turn = await create_turn(client, state, {"Authorization": f"Bearer {create_token(user.id)}"})
    await teaching_runs.execute(turn.json()["run_id"])
    run = await db_session.get(AgentRun, turn.json()["run_id"])
    assert run.status == "needs_retry" and run.error_code == "AI_SERVICE_UNAVAILABLE" and len(calls) == 1
    rows = list((await db_session.execute(select(TeachingMessage))).scalars())
    assert len(rows) == 1 and rows[0].role == "user"
