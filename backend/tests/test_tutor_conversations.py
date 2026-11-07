"""P02.3: standalone chats, multi-task association and legacy transcript parity."""

import json
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import func, select

from app.core import database
from app.core.security import create_token
from app.models.v2_runtime import AgentRun, TeachingMessage, TutorConversation, TutorConversationTask
from app.services import account_data, teaching_gateway, teaching_runs, v2_access
from app.tasks.account_tasks import _purge_user
from tests.conftest import TestSessionLocal
from tests.teaching_fixtures import seed_original_content

_REAL_CLIENT = httpx.AsyncClient


async def setup(db, monkeypatch):
    user, revision, question, _candidate = await seed_original_content(db)
    settings = SimpleNamespace(
        teaching_enabled=True,
        teaching_runs_enabled=True,
        teaching_dialogue_enabled=True,
        teaching_conversations_enabled=True,
        teaching_allowed_user_ids=user.id,
    )
    monkeypatch.setattr(v2_access, "get_settings", lambda: settings)
    monkeypatch.setattr(teaching_runs, "require_gateway", lambda: None)
    monkeypatch.setattr(database, "get_async_session_maker", lambda: TestSessionLocal)
    from app.api.v1 import teaching_runs as router
    from app.api.v1 import tutor as tutor_router

    dispatched = []
    monkeypatch.setattr(router, "dispatch", dispatched.append)
    monkeypatch.setattr(tutor_router, "dispatch", dispatched.append)
    await db.commit()
    return user, revision, question, settings, dispatched


def model(monkeypatch, *, response=None, finish="stop"):
    calls = []
    settings = SimpleNamespace(
        llm_gateway_governance_verified=True,
        llm_gateway_base_url="http://gateway.test",
        llm_gateway_admin_key="test-control-key",
        llm_gateway_v2_team_id="test-team",
        llm_gateway_model="teaching",
        llm_gateway_tutor_model="tutor",
        llm_gateway_tutor_max_tokens=1024,
        v2_run_budget_usd=0.02,
    )
    monkeypatch.setattr(teaching_gateway, "get_settings", lambda: settings)

    def handler(request):
        if request.url.path == "/user/new":
            return httpx.Response(200, json={})
        if request.url.path == "/key/generate":
            return httpx.Response(200, json={"key": "test-run-key"})
        assert request.url.path == "/chat/completions"
        payload = json.loads(request.content)
        calls.append(payload)
        result = response or {
            "text": "一般英语问答。",
            "citations": [],
            "suggested_answer": None,
        }
        return httpx.Response(
            200, json={"choices": [{"finish_reason": finish, "message": {"content": json.dumps(result)}}]}
        )

    monkeypatch.setattr(
        teaching_gateway.httpx,
        "AsyncClient",
        lambda *a, **kw: _REAL_CLIENT(*a, transport=httpx.MockTransport(handler), **kw),
    )
    return calls


async def test_chat_lifecycle_and_taskless_turn(client, db_session, monkeypatch):
    user, _revision, _question, _settings, dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    calls = model(monkeypatch)
    created = await client.post("/api/v1/tutor/conversations", headers=headers, json={"title": "随便问问"})
    assert created.status_code == 201, created.text
    conversation = created.json()
    assert conversation["kind"] == "chat" and conversation["title"] == "随便问问" and conversation["tasks"] == []

    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "chat-1", "message": "affect 和 effect 有什么区别？"},
    )
    assert turn.status_code == 202, turn.text
    assert turn.json()["session_id"] is None and turn.json()["conversation_id"] == conversation["id"]
    replay = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "chat-1", "message": "affect 和 effect 有什么区别？"},
    )
    assert replay.json()["run_id"] == turn.json()["run_id"]
    await teaching_runs.execute(turn.json()["run_id"])
    # A task-less turn still reaches the model, with the wider tutor alias.
    assert len(calls) == 1 and calls[0]["model"] == "tutor" and calls[0]["max_tokens"] == 1024
    prompt = json.loads(calls[0]["messages"][1]["content"])
    assert "sources" not in prompt and prompt["message"].startswith("affect")

    page = await client.get(f"/api/v1/tutor/conversations/{conversation['id']}/messages", headers=headers)
    items = page.json()["items"]
    assert [m["role"] for m in items] == ["user", "assistant"]
    assert items[0]["session_id"] is None and items[1]["body"]["citation_ids"] == []
    assert not any(m["restricted"] for m in items)
    assert page.headers["cache-control"] == "no-store"

    events = await client.get(turn.json()["events_url"], headers=headers)
    assert "event: message.upsert" in events.text and "event: run.completed" in events.text

    listed = await client.get("/api/v1/tutor/conversations", headers=headers)
    assert [row["id"] for row in listed.json()["items"]] == [conversation["id"]]
    assert listed.json()["has_more"] is False

    renamed = await client.patch(
        f"/api/v1/tutor/conversations/{conversation['id']}", headers=headers, json={"title": "词汇"}
    )
    assert renamed.json()["title"] == "词汇"
    archived = await client.patch(
        f"/api/v1/tutor/conversations/{conversation['id']}", headers=headers, json={"status": "archived"}
    )
    assert archived.json()["status"] == "archived"
    blocked = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "chat-2", "message": "还在吗？"},
    )
    assert blocked.status_code == 409

    # A replayed turn is dispatched again; the worker claims it only once.
    assert len(dispatched) == 2
    deleted = await client.delete(f"/api/v1/tutor/conversations/{conversation['id']}", headers=headers)
    assert deleted.status_code == 204
    assert await db_session.scalar(select(func.count()).select_from(TutorConversation)) == 0
    assert await db_session.scalar(select(func.count()).select_from(TeachingMessage)) == 0
    assert await db_session.scalar(select(func.count()).select_from(AgentRun)) == 0


async def test_general_reply_may_not_cite_or_suggest(client, db_session, monkeypatch):
    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    model(monkeypatch, response={"text": "回答", "citations": [0], "suggested_answer": "B"})
    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "chat-cite", "message": "这是什么意思"},
    )
    await teaching_runs.execute(turn.json()["run_id"])
    run = await db_session.get(AgentRun, turn.json()["run_id"])
    assert run.status == "needs_retry" and run.error_code == "AI_SERVICE_UNAVAILABLE"
    rows = list((await db_session.execute(select(TeachingMessage))).scalars())
    assert len(rows) == 1 and rows[0].role == "user"


async def test_task_turn_inside_a_chat_and_cross_task_isolation(client, db_session, monkeypatch):
    user, revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    from app.services.teaching import service as core

    principal = core.Principal(user.id)
    first = await core.create_session(
        db_session, principal, {"operation_id": "task-1", "content_revision_id": revision.id}
    )
    second = await core.create_session(
        db_session, principal, {"operation_id": "task-2", "content_revision_id": revision.id}
    )
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    calls = model(monkeypatch)
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()

    missing_revision = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "t-1", "message": "帮我看看", "session_id": first["id"]},
    )
    assert missing_revision.status_code == 422
    stray_revision = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "t-2", "message": "帮我看看", "expected_revision": 1},
    )
    assert stray_revision.status_code == 422

    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "operation_id": "t-3",
            "message": "这题的解析",
            "session_id": first["id"],
            "expected_revision": first["revision"],
        },
    )
    assert turn.status_code == 202, turn.text
    detail = (await client.get(f"/api/v1/tutor/conversations/{conversation['id']}", headers=headers)).json()
    assert [t["session_id"] for t in detail["tasks"]] == [first["id"]]
    await teaching_runs.execute(turn.json()["run_id"])
    page = (await client.get(f"/api/v1/tutor/conversations/{conversation['id']}/messages", headers=headers)).json()
    assert page["items"][0]["session_id"] == first["id"]
    # Before reveal the trusted policy text is used and no answer is disclosed.
    assert page["items"][1]["body"]["source"] == "policy" and not calls

    revealed = await client.post(
        f"/api/v1/teaching/sessions/{first['id']}/reveal",
        headers=headers,
        json={
            "operation_id": "reveal-1",
            "expected_revision": first["revision"],
            "item_id": first["current_item_id"],
        },
    )
    assert revealed.status_code == 200, revealed.text
    revealed_task = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "operation_id": "t-3b",
            "message": "这题的解析",
            "session_id": first["id"],
            "expected_revision": revealed.json()["revision"],
        },
    )
    assert revealed_task.status_code == 202, revealed_task.text
    await teaching_runs.execute(revealed_task.json()["run_id"])
    # A chat task turn keeps the verified 128-token teaching envelope.
    assert len(calls) == 1 and calls[0]["model"] == "teaching" and calls[0]["max_tokens"] == 128

    second_turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "operation_id": "t-4",
            "message": "另一题",
            "session_id": second["id"],
            "expected_revision": second["revision"],
        },
    )
    assert second_turn.status_code == 202
    detail = (await client.get(f"/api/v1/tutor/conversations/{conversation['id']}", headers=headers)).json()
    assert sorted(t["session_id"] for t in detail["tasks"]) == sorted([first["id"], second["id"]])


async def test_legacy_task_endpoint_keeps_its_transcript(client, db_session, monkeypatch):
    from tests.test_teaching_dialogue import model as legacy_model
    from tests.test_teaching_dialogue import setup as legacy_setup

    user, revision, _question, state, settings, _ = await legacy_setup(db_session, monkeypatch)
    settings.teaching_conversations_enabled = True
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    legacy_model(monkeypatch)
    turn = await client.post(
        f"/api/v1/teaching/sessions/{state['id']}/messages",
        headers=headers,
        json={"operation_id": "legacy-1", "expected_revision": state["revision"], "message": "为什么 A 不成立？"},
    )
    await teaching_runs.execute(turn.json()["run_id"])
    page = (await client.get(f"/api/v1/teaching/sessions/{state['id']}/messages", headers=headers)).json()
    assert [m["role"] for m in page["items"]] == ["user", "assistant"]
    conversation_id = page["items"][0]["conversation_id"]
    assert all(m["conversation_id"] == conversation_id for m in page["items"])
    chat = await db_session.get(TutorConversation, conversation_id)
    assert chat is not None and chat.kind == "task" and chat.task_session_id == state["id"]
    # The standalone chat API never manages a task transcript.
    assert (await client.get(f"/api/v1/tutor/conversations/{conversation_id}", headers=headers)).status_code == 404
    assert (await client.delete(f"/api/v1/tutor/conversations/{conversation_id}", headers=headers)).status_code == 404
    # Reading a task with no transcript is empty, and never creates a chat.
    from app.services.teaching import service as core_again

    other = await core_again.create_session(
        db_session, core_again.Principal(user.id), {"operation_id": "empty-task", "content_revision_id": revision.id}
    )
    await db_session.commit()
    empty = (await client.get(f"/api/v1/teaching/sessions/{other['id']}/messages", headers=headers)).json()
    assert empty == {"items": [], "next_after": 0, "has_more": False}
    assert await db_session.scalar(select(func.count()).select_from(TutorConversation)) == 1


async def test_export_and_purge_cover_taskless_chats(client, db_session, monkeypatch, tmp_path):
    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    model(monkeypatch)
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={"title": "导出"})).json()
    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "export-1", "message": "记住我喜欢先看原句"},
    )
    await teaching_runs.execute(turn.json()["run_id"])
    from app.models.user import User

    current = await db_session.get(User, user.id)
    data = await account_data.gather_user_data(db_session, current)
    assert [c["kind"] for c in data["tutor_conversations"]] == ["chat"]
    assert len(data["teaching_messages"]) == 2
    assert all(m["session_id"] is None for m in data["teaching_messages"])

    monkeypatch.setattr(account_data, "_media_root", lambda: tmp_path)
    await _purge_user(db_session, current)
    assert await db_session.scalar(select(func.count()).select_from(TutorConversation)) == 0
    assert await db_session.scalar(select(func.count()).select_from(TutorConversationTask)) == 0
    assert await db_session.scalar(select(func.count()).select_from(TeachingMessage)) == 0


async def test_conversation_runs_are_gated_and_scoped(client, db_session, monkeypatch):
    user, _revision, _question, settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    from app.models.user import User

    other_user = User(name="someone-else", phone="13900000009")
    db_session.add(other_user)
    await db_session.commit()
    settings.teaching_conversations_enabled = False
    assert (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).status_code == 503
    settings.teaching_conversations_enabled = True
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    other_headers = {"Authorization": f"Bearer {create_token(other_user.id)}"}
    # The feature is closed for an account outside the allowlist, like every
    # other V2 entry point; it never leaks whether the chat exists.
    assert (
        await client.get(f"/api/v1/tutor/conversations/{conversation['id']}", headers=other_headers)
    ).status_code == 503

    allowed_user = User(name="allowed-other", phone="13900000010")
    db_session.add(allowed_user)
    await db_session.commit()
    settings.teaching_allowed_user_ids = f"{user.id},{allowed_user.id}"
    allowed_headers = {"Authorization": f"Bearer {create_token(allowed_user.id)}"}
    assert (
        await client.get(f"/api/v1/tutor/conversations/{conversation['id']}", headers=allowed_headers)
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/tutor/conversations/{conversation['id']}/messages",
            headers=allowed_headers,
            json={"operation_id": "spoof", "message": "hi"},
        )
    ).status_code == 404
    assert (await client.get("/api/v1/tutor/conversations")).status_code == 401


async def test_conversation_schema_gate_returns_503(db_session, monkeypatch):
    from app.core.errors import AppError
    from app.services.v2_schema import require_conversation_schema

    async def _never(_db, _names):
        return False

    monkeypatch.setattr("app.services.v2_schema.has_tables", _never)
    with pytest.raises(AppError) as denied:
        await require_conversation_schema(db_session)
    assert denied.value.status_code == 503


async def test_taskless_chat_streams_plain_text_without_citations(client, db_session, monkeypatch):
    from app.models.v2_runtime import AgentStep, TeachingMessageBlock
    from app.services.teaching.streaming import CitationStream
    from tests.conftest import TestSessionLocal
    from tests.test_teaching_streaming import enable_streaming, stream_model

    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    # A stray marker in a source-less chat is dropped, not treated as a citation.
    stream_model(monkeypatch, ["affect 是动词[1]。", "effect 多作名词。"])
    enable_streaming(monkeypatch)
    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "stream-chat", "message": "区别是什么"},
    )
    assert turn.status_code == 202, turn.text
    await teaching_runs.execute(turn.json()["run_id"])
    async with TestSessionLocal() as db:
        stored = (await db.execute(select(AgentRun).where(AgentRun.id == turn.json()["run_id"]))).scalars().one()
        message = (
            (await db.execute(select(TeachingMessage).where(TeachingMessage.run_id == turn.json()["run_id"])))
            .scalars()
            .all()
        )
        blocks = (await db.execute(select(TeachingMessageBlock))).scalars().all()
        step = (await db.execute(select(AgentStep).where(AgentStep.run_id == turn.json()["run_id"]))).scalars().one()
    assert stored.status == "succeeded"
    assistant = next(row for row in message if row.role == "assistant")
    assert assistant.status == "complete" and assistant.session_id is None
    assert assistant.body["citation_ids"] == []
    assert "[" not in assistant.body["text"]
    assert [b.ordinal for b in blocks] == [1, 2]
    assert step.safe_result["streamed"] is True and step.safe_result["usage_status"] == "reported"
    source_free = CitationStream(0, general=True)
    assert source_free.feed("[1][2] 文本，") == []
    assert source_free.finish() == [" 文本，"]
    assert source_free.citations == [] and "[" not in source_free.text


async def test_archived_chat_stays_readable_and_delete_keeps_task_facts(client, db_session, monkeypatch):
    user, revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    from app.models.teaching import TeachingSession
    from app.services.teaching import service as core

    task = await core.create_session(
        db_session, core.Principal(user.id), {"operation_id": "keep-task", "content_revision_id": revision.id}
    )
    await db_session.commit()
    model(monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "operation_id": "keep-1",
            "message": "这道题怎么看",
            "session_id": task["id"],
            "expected_revision": task["revision"],
        },
    )
    await teaching_runs.execute(turn.json()["run_id"])
    await client.patch(
        f"/api/v1/tutor/conversations/{conversation['id']}", headers=headers, json={"status": "archived"}
    )
    page = await client.get(f"/api/v1/tutor/conversations/{conversation['id']}/messages", headers=headers)
    assert page.status_code == 200 and len(page.json()["items"]) == 2
    assert (
        await client.delete(f"/api/v1/tutor/conversations/{conversation['id']}", headers=headers)
    ).status_code == 204
    # Deleting the chat never touches the task or its learning facts.
    assert await db_session.get(TeachingSession, task["id"]) is not None


async def test_cancelled_taskless_run_publishes_nothing(client, db_session, monkeypatch):
    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    model(monkeypatch)
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "cancel-chat", "message": "先别答"},
    )
    cancelled = await client.post(turn.json()["state_url"] + "/cancel", headers=headers)
    assert cancelled.status_code == 200
    await teaching_runs.execute(turn.json()["run_id"])
    rows = list((await db_session.execute(select(TeachingMessage))).scalars())
    assert len(rows) == 1 and rows[0].role == "user"
    run = await db_session.get(AgentRun, turn.json()["run_id"])
    assert run.status == "cancelled"


async def test_conversation_list_paginates_and_orders_by_update(client, db_session, monkeypatch):
    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    ids = []
    for index in range(3):
        created = await client.post("/api/v1/tutor/conversations", headers=headers, json={"title": f"c{index}"})
        ids.append(created.json()["id"])
    first = await client.get("/api/v1/tutor/conversations?page=1&page_size=2", headers=headers)
    second = await client.get("/api/v1/tutor/conversations?page=2&page_size=2", headers=headers)
    assert first.json()["has_more"] is True and len(first.json()["items"]) == 2
    assert second.json()["has_more"] is False and len(second.json()["items"]) == 1
    assert {row["id"] for row in first.json()["items"] + second.json()["items"]} == set(ids)
    # Renaming moves a chat to the top without changing its id.
    await client.patch(f"/api/v1/tutor/conversations/{ids[0]}", headers=headers, json={"title": "最新"})
    top = await client.get("/api/v1/tutor/conversations?page=1&page_size=1", headers=headers)
    assert top.json()["items"][0]["id"] == ids[0]


async def test_export_restricts_task_messages_after_rights_withdrawal(client, db_session, monkeypatch):
    user, revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    from app.models.teaching import ExamAnalysisRevision
    from app.models.user import User
    from app.services.teaching import service as core

    task = await core.create_session(
        db_session, core.Principal(user.id), {"operation_id": "export-task", "content_revision_id": revision.id}
    )
    await db_session.commit()
    model(monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "operation_id": "export-task-turn",
            "message": "看看这题",
            "session_id": task["id"],
            "expected_revision": task["revision"],
        },
    )
    row = await db_session.get(ExamAnalysisRevision, revision.id)
    row.rights_policy = {**row.rights_policy, "site_display": False}
    await db_session.commit()
    data = await account_data.gather_user_data(db_session, await db_session.get(User, user.id))
    task_messages = [m for m in data["teaching_messages"] if m["session_id"] == task["id"]]
    assert task_messages and all(m["restricted"] and m["body"] is None for m in task_messages)


async def test_chat_reads_close_with_the_capability(client, db_session, monkeypatch):
    user, _revision, _question, settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    settings.teaching_conversations_enabled = False
    assert (
        await client.get(f"/api/v1/tutor/conversations/{conversation['id']}/messages", headers=headers)
    ).status_code == 503
    assert (await client.get("/api/v1/tutor/conversations", headers=headers)).status_code == 503


async def test_vanished_chat_settles_the_queued_run(client, db_session, monkeypatch):
    """Deleting the chat between queue and execute must settle, not crash the worker."""
    from sqlalchemy import update as sql_update

    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    model(monkeypatch)
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "vanished", "message": "还在吗"},
    )
    run_id = turn.json()["run_id"]
    # Delete the chat row without going through the API, so the run survives.
    await db_session.execute(sql_update(AgentRun).where(AgentRun.id == run_id).values(conversation_id=None))
    await db_session.commit()
    await teaching_runs.execute(run_id)
    run = await db_session.get(AgentRun, run_id)
    assert run.status in {"failed", "needs_retry"}, run.status


async def test_taskless_run_never_sends_task_history_to_the_model(client, db_session, monkeypatch):
    """A chat may hold task turns; a task-less turn gets only its own history."""
    from app.services.teaching import service as core

    user, revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    task = await core.create_session(
        db_session, core.Principal(user.id), {"operation_id": "mix-task", "content_revision_id": revision.id}
    )
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    calls = model(monkeypatch)
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    task_turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "operation_id": "mix-1",
            "message": "TASK_SECRET_QUESTION",
            "session_id": task["id"],
            "expected_revision": task["revision"],
        },
    )
    await teaching_runs.execute(task_turn.json()["run_id"])
    chat_turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"operation_id": "mix-2", "message": "普通问题"},
    )
    await teaching_runs.execute(chat_turn.json()["run_id"])
    assert len(calls) == 1  # only the general turn reached the model
    sent = json.loads(calls[0]["messages"][1]["content"])
    assert "TASK_SECRET_QUESTION" not in json.dumps(sent, ensure_ascii=False)


async def test_same_operation_id_with_another_message_conflicts(client, db_session, monkeypatch):
    """A chat's receipt binds the message too; a different text is not a replay."""
    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    model(monkeypatch)
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    base = f"/api/v1/tutor/conversations/{conversation['id']}/messages"
    first = await client.post(base, headers=headers, json={"operation_id": "same-id", "message": "第一句"})
    assert first.status_code == 202
    other = await client.post(base, headers=headers, json={"operation_id": "same-id", "message": "第二句"})
    assert other.status_code == 409 and other.json()["code"] == "IDEMPOTENCY_CONFLICT"


async def test_new_turn_titles_and_surfaces_the_chat(client, db_session, monkeypatch):
    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    model(monkeypatch)
    first = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    second = (await client.post("/api/v1/tutor/conversations", headers=headers, json={"title": "已有标题"})).json()
    await client.post(
        f"/api/v1/tutor/conversations/{first['id']}/messages",
        headers=headers,
        json={"operation_id": "title-me", "message": "请解释虚拟语气"},
    )
    listed = (await client.get("/api/v1/tutor/conversations", headers=headers)).json()["items"]
    assert listed[0]["id"] == first["id"]
    assert listed[0]["title"].startswith("请解释虚拟语气")
    assert next(row for row in listed if row["id"] == second["id"])["title"] == "已有标题"


async def test_cross_chat_read_isolation(client, db_session, monkeypatch):
    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    model(monkeypatch)
    mine = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    neighbours = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    await client.post(
        f"/api/v1/tutor/conversations/{mine['id']}/messages",
        headers=headers,
        json={"operation_id": "k1", "message": "只属于我"},
    )
    page = (await client.get(f"/api/v1/tutor/conversations/{neighbours['id']}/messages", headers=headers)).json()
    assert page["items"] == []


async def test_capability_gate_checks_schema_after_the_switches(db_session, monkeypatch):
    """Flags open but the tables missing must still be 503, not a 500."""
    from app.core.errors import AppError
    from app.services.tutor_conversations import require_capability

    user, _revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    monkeypatch.setattr("app.services.v2_schema.has_tables", _never)
    with pytest.raises(AppError) as denied:
        await require_capability(db_session, user.id)
    assert denied.value.status_code == 503


async def _never(_db, _names):
    return False


async def test_purge_clears_a_task_bound_chat_and_its_associations_only(client, db_session, monkeypatch, tmp_path):
    """Purge must delete the chat's messages/associations, never the task facts."""
    from app.models.teaching import TeachingAttempt, TeachingSession
    from app.models.user import User
    from app.services.teaching import service as core

    user, revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    task = await core.create_session(
        db_session, core.Principal(user.id), {"operation_id": "purge-task", "content_revision_id": revision.id}
    )
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    model(monkeypatch)
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    turn = await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "operation_id": "purge-1",
            "message": "看看这题",
            "session_id": task["id"],
            "expected_revision": task["revision"],
        },
    )
    await teaching_runs.execute(turn.json()["run_id"])
    assert await db_session.scalar(select(func.count()).select_from(TutorConversationTask)) == 1
    monkeypatch.setattr(account_data, "_media_root", lambda: tmp_path)
    await _purge_user(db_session, await db_session.get(User, user.id))
    assert await db_session.scalar(select(func.count()).select_from(TutorConversation)) == 0
    assert await db_session.scalar(select(func.count()).select_from(TutorConversationTask)) == 0
    assert await db_session.scalar(select(func.count()).select_from(TeachingMessage)) == 0
    # The user row is gone, so the task rows go with it through the normal
    # account sweep; what this asserts is that no orphan association remains.
    assert await db_session.scalar(select(func.count()).select_from(TeachingSession)) == 0
    assert await db_session.scalar(select(func.count()).select_from(TeachingAttempt)) == 0


async def test_delete_chat_leaves_the_task_chat_transcript_untouched(client, db_session, monkeypatch):
    """A user's chat delete never reaches the legacy task transcript."""
    from tests.test_teaching_dialogue import model as legacy_model
    from tests.test_teaching_dialogue import setup as legacy_setup

    user, _revision, _question, state, settings, _ = await legacy_setup(db_session, monkeypatch)
    settings.teaching_conversations_enabled = True
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    legacy_model(monkeypatch)
    legacy_turn = await client.post(
        f"/api/v1/teaching/sessions/{state['id']}/messages",
        headers=headers,
        json={"operation_id": "legacy-keep", "expected_revision": state["revision"], "message": "为什么"},
    )
    await teaching_runs.execute(legacy_turn.json()["run_id"])
    task_page = (await client.get(f"/api/v1/teaching/sessions/{state['id']}/messages", headers=headers)).json()
    assert len(task_page["items"]) == 2
    chat = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    assert (await client.delete(f"/api/v1/tutor/conversations/{chat['id']}", headers=headers)).status_code == 204
    still_there = (await client.get(f"/api/v1/teaching/sessions/{state['id']}/messages", headers=headers)).json()
    assert len(still_there["items"]) == 2


async def test_export_order_lists_the_new_section():
    from app.services.account_data import EXPORT_ORDER

    assert "tutor_conversations" in EXPORT_ORDER
    assert EXPORT_ORDER.index("tutor_conversations") < EXPORT_ORDER.index("teaching_messages")


async def test_task_transcript_is_hidden_when_the_task_context_vanishes(client, db_session, monkeypatch):
    """A task message whose task can no longer be projected must be restricted."""
    from app.core.errors import AppError
    from app.services.teaching import service as core

    user, revision, _question, _settings, _dispatched = await setup(db_session, monkeypatch)
    task = await core.create_session(
        db_session, core.Principal(user.id), {"operation_id": "vanished-task", "content_revision_id": revision.id}
    )
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    model(monkeypatch)
    conversation = (await client.post("/api/v1/tutor/conversations", headers=headers, json={})).json()
    await client.post(
        f"/api/v1/tutor/conversations/{conversation['id']}/messages",
        headers=headers,
        json={
            "operation_id": "vanished-1",
            "message": "这题答案",
            "session_id": task["id"],
            "expected_revision": task["revision"],
        },
    )
    before = (await client.get(f"/api/v1/tutor/conversations/{conversation['id']}/messages", headers=headers)).json()
    assert before["items"] and not before["items"][0]["restricted"]

    async def _gone(*_a, **_kw):
        raise AppError(404, "NOT_FOUND", "教学会话不存在")

    monkeypatch.setattr("app.services.teaching.dialogue.get_learning_context", _gone)
    after = (await client.get(f"/api/v1/tutor/conversations/{conversation['id']}/messages", headers=headers)).json()
    assert after["items"] and all(m["restricted"] and m["body"] is None for m in after["items"])


async def test_list_excludes_the_legacy_task_chat(client, db_session, monkeypatch):
    from tests.test_teaching_dialogue import model as legacy_model
    from tests.test_teaching_dialogue import setup as legacy_setup

    user, _revision, _question, state, settings, _ = await legacy_setup(db_session, monkeypatch)
    settings.teaching_conversations_enabled = True
    headers = {"Authorization": f"Bearer {create_token(user.id)}"}
    legacy_model(monkeypatch)
    turn = await client.post(
        f"/api/v1/teaching/sessions/{state['id']}/messages",
        headers=headers,
        json={"operation_id": "legacy-list", "expected_revision": state["revision"], "message": "为什么"},
    )
    await teaching_runs.execute(turn.json()["run_id"])
    assert await db_session.scalar(select(func.count()).select_from(TutorConversation)) == 1
    listed = (await client.get("/api/v1/tutor/conversations", headers=headers)).json()
    assert listed["items"] == []


def test_migration_backfill_creates_one_task_chat_per_session(monkeypatch):
    """The migration's backfill is the only thing CI never runs; pin its shape."""
    import importlib.util
    from pathlib import Path

    import sqlalchemy as sa
    from alembic import op

    path = Path(__file__).resolve().parent.parent / "migrations/versions/c4a1b2c3d4e5_tutor_conversations.py"
    spec = importlib.util.spec_from_file_location("p023_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE teaching_sessions (id TEXT PRIMARY KEY, user_id TEXT NOT NULL)")
        connection.exec_driver_sql(
            "CREATE TABLE teaching_messages (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, session_id TEXT, "
            "conversation_id TEXT, sequence INTEGER NOT NULL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE tutor_conversations (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, title TEXT NOT NULL, "
            "status TEXT NOT NULL, kind TEXT NOT NULL, task_session_id TEXT, created_at TEXT NOT NULL, "
            "updated_at TEXT NOT NULL)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE tutor_conversation_tasks (id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, "
            "session_id TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        # Two sessions of different users, plus a stray message whose session row
        # is gone (must not create an orphan chat).
        connection.exec_driver_sql("INSERT INTO teaching_sessions (id, user_id) VALUES ('s-1','u-1'), ('s-2','u-2')")
        connection.exec_driver_sql(
            "INSERT INTO teaching_messages (id, user_id, session_id, sequence) VALUES "
            "('m-1','u-1','s-1',1), ('m-2','u-1','s-1',2), ('m-3','u-2','s-2',1), ('m-4','u-1','gone',1)"
        )
        monkeypatch.setattr(op, "get_bind", lambda: connection)
        module._backfill_task_chats()
        rows = connection.exec_driver_sql(
            "SELECT c.task_session_id, c.user_id, c.kind FROM tutor_conversations c ORDER BY c.task_session_id"
        ).fetchall()
        assert rows == [("s-1", "u-1", "task"), ("s-2", "u-2", "task")]
        links = connection.exec_driver_sql(
            "SELECT conversation_id, session_id FROM tutor_conversation_tasks"
        ).fetchall()
        assert len(links) == 2
        per_message = connection.exec_driver_sql(
            "SELECT session_id, conversation_id FROM teaching_messages WHERE session_id IN ('s-1','s-2') "
            "ORDER BY session_id, sequence"
        ).fetchall()
        assert len({row[1] for row in per_message[:2]}) == 1  # s-1's two messages share one chat
        assert per_message[2][1] != per_message[0][1]  # s-2 gets its own chat
        stray = connection.exec_driver_sql("SELECT conversation_id FROM teaching_messages WHERE id = 'm-4'").scalar()
        assert stray is None  # a message whose session row is gone is never adopted
        assert len(module._conversation_id("s-1")) == 36
