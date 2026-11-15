"""Run with the isolated MCP SDK runtime; do not silently upgrade cloud dependencies."""

import json

import pytest
from httpx import ASGITransport, AsyncClient

pytest.importorskip("mcp", reason="MCP SDK is isolated until its dependency gate passes")

from app.integrations.mcp import server
from app.services import external_connection_service as connections
from app.services import v2_access
from app.services.teaching import service as core
from tests.teaching_fixtures import seed_original_content
from tests.test_v2_runtime import enable


async def setup(db, monkeypatch, *, scopes=None):
    user, revision, _question, _candidate = await seed_original_content(db)
    settings = enable(monkeypatch, user.id)
    settings.mcp_allowed_hosts = "testserver"
    settings.mcp_allowed_origins = "https://allowed.example"
    monkeypatch.setattr(server, "get_settings", lambda: settings)
    monkeypatch.setattr(v2_access, "get_settings", lambda: settings)
    state = await core.create_session(
        db,
        core.Principal(user.id),
        {
            "operation_id": "mcp-session",
            "content_revision_id": revision.id,
        },
    )
    issued = await connections.create(db, user.id, "SDK protocol test", scopes or ["teaching:read"])
    await db.commit()
    return user, state, issued


def headers(token, protocol="2025-11-25"):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": protocol,
    }


async def call(client, token, name, arguments=None, request_id=2, protocol="2025-11-25"):
    request_headers = headers(token, protocol)
    params = {"name": name, "arguments": arguments or {}}
    if protocol == "2026-07-28":
        request_headers.update({"Mcp-Method": "tools/call", "Mcp-Name": name})
        params["_meta"] = {
            "io.modelcontextprotocol/protocolVersion": protocol,
            "io.modelcontextprotocol/clientCapabilities": {},
        }
    return await client.post(
        "/",
        headers=request_headers,
        json={
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": params,
        },
    )


def result(response):
    assert response.status_code == 200, response.text
    data = response.json()
    assert "result" in data, data
    value = data["result"]
    if value.get("isError"):
        return value
    if "structuredContent" in value:
        return value["structuredContent"]
    return json.loads(value["content"][0]["text"])


@pytest.mark.parametrize("protocol", ["2025-11-25", "2026-07-28"])
async def test_protocol_auth_host_origin_and_read_scope(db_session, monkeypatch, protocol):
    _user, state, issued = await setup(db_session, monkeypatch)
    app = server.create_mcp_app()
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            denied = await client.post("/", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
            assert denied.status_code == 401 and "Bearer" in denied.headers["www-authenticate"]
            bad_origin = await client.post(
                "/", headers={**headers(issued["token"], protocol), "Origin": "https://evil.example"}, json={}
            )
            assert bad_origin.status_code == 403
            if protocol == "2026-07-28":
                # The installed SDK's modern protocol uses discovery and a
                # per-request envelope, rather than the legacy initialize.
                init_body = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "server/discover",
                    "params": {
                        "_meta": {
                            "io.modelcontextprotocol/protocolVersion": protocol,
                            "io.modelcontextprotocol/clientCapabilities": {},
                        }
                    },
                }
                init_headers = {**headers(issued["token"], protocol), "Mcp-Method": "server/discover"}
                malformed = await client.post(
                    "/",
                    headers=headers(issued["token"], protocol),
                    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                )
                assert malformed.status_code == 400 and "_meta" in malformed.text
            else:
                init_body = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": protocol,
                        "capabilities": {},
                        "clientInfo": {"name": "isolated-test", "version": "1"},
                    },
                }
                init_headers = headers(issued["token"], protocol)
            init = await client.post("/", headers=init_headers, json=init_body)
            assert init.status_code == 200, init.text
            discovered = init.json()["result"]
            if protocol == "2026-07-28":
                assert protocol in discovered["supportedVersions"]
                assert discovered["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "SeeWord"
            else:
                assert discovered["serverInfo"]["name"] == "SeeWord"
            restored = result(
                await call(
                    client, issued["token"], "get_teaching_session", {"session_id": state["id"]}, protocol=protocol
                )
            )
            assert restored["id"] == state["id"] and "correct_answer" not in str(restored)
            context = result(
                await call(
                    client, issued["token"], "get_learning_context", {"session_id": state["id"]}, protocol=protocol
                )
            )
            assert context["schema_version"] == 1 and context["audience"] == "external"
            assert context["task"]["session_id"] == state["id"] and context["allowed_actions"] == []
            assert "correct_answer" not in str(context) and "user_id" not in context
            denied_write = result(
                await call(
                    client,
                    issued["token"],
                    "submit_answer",
                    {
                        "session_id": state["id"],
                        "item_id": state["current_item_id"],
                        "answer": "B",
                        "operation_id": "denied",
                        "expected_revision": state["revision"],
                    },
                    protocol=protocol,
                )
            )
            assert denied_write["isError"] is True and "INSUFFICIENT_SCOPE" in str(denied_write)


@pytest.mark.parametrize("protocol", ["2025-11-25", "2026-07-28"])
async def test_auxiliary_submit_web_restore_replay_and_revocation(db_session, monkeypatch, protocol):
    user, state, issued = await setup(db_session, monkeypatch, scopes=["teaching:read", "teaching:attempts:submit"])
    user_id = user.id
    app = server.create_mcp_app()
    args = {
        "session_id": state["id"],
        "item_id": state["current_item_id"],
        "answer": "B",
        "operation_id": "external-first",
        "expected_revision": state["revision"],
    }
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            submitted = result(await call(client, issued["token"], "submit_answer", args, protocol=protocol))
            assert submitted["answer_origin"] == "external_reported"
            assert submitted["independence"] == "unverified" and submitted["counts_toward_mastery"] is False
            replay = result(await call(client, issued["token"], "submit_answer", args, request_id=3, protocol=protocol))
            assert replay["attempt_id"] == submitted["attempt_id"]
            db_session.expire_all()
            restored = await core.get_session(db_session, core.Principal(user_id), state["id"])
            assert len(restored["attempts"]) == 1 and restored["attempts"][0]["answer_origin"] == "external_reported"
            context = result(
                await call(
                    client, issued["token"], "get_learning_context", {"session_id": state["id"]}, protocol=protocol
                )
            )
            assert context["progress"]["recent_attempts"][0]["answer_origin"] == "external_reported"
            assert context["task"]["state_version"] == restored["revision"]
            await connections.revoke(db_session, user_id, issued["connection"]["id"])
            await db_session.commit()
            denied = await call(
                client, issued["token"], "get_teaching_session", {"session_id": state["id"]}, protocol=protocol
            )
            assert denied.status_code == 401
            denied_context = await call(
                client, issued["token"], "get_learning_context", {"session_id": state["id"]}, protocol=protocol
            )
            assert denied_context.status_code == 401


@pytest.mark.parametrize("protocol", ["2025-11-25", "2026-07-28"])
async def test_learning_tools_shared_grants_model_uses_and_confirmed_execution(db_session, monkeypatch, protocol):
    from sqlalchemy import func, select

    from app.core.config import get_settings
    from app.models.lesson_learning import VocabularyReviewLog
    from app.schemas.delegated_learning import ResourceLimits
    from app.services import delegated_learning
    from tests.open_learning_fixtures import add_revision, fixed_reference

    user, _state, _legacy = await setup(db_session, monkeypatch)
    monkeypatch.setattr(get_settings(), "slcs_lessons_enabled", True)
    monkeypatch.setattr(get_settings(), "slcs_vocabulary_enabled", True)
    monkeypatch.setattr("app.services.ecdict.lookup", lambda _word: None)
    revision = await add_revision(db_session)
    restricted = await add_revision(db_session, "site-only-model", "Not for models", model=False)
    issued = await connections.create(
        db_session,
        user.id,
        "Learning SDK",
        [
            "materials:read",
            "learning:vocabulary:write",
            "review:read",
            "review:write",
        ],
        ResourceLimits(lesson_ids=[revision.lesson_id, restricted.lesson_id]),
    )
    await db_session.commit()
    application = await connections.create(
        db_session,
        user.id,
        "Application-only SDK check",
        ["materials:read", "teaching:read", "learning:profile:read"],
        ResourceLimits(lesson_ids=[revision.lesson_id]),
        audience="application",
    )
    await db_session.commit()
    app = server.create_mcp_app()
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            blocked_audience = result(await call(client, application["token"], "search_materials", protocol=protocol))
            assert blocked_audience["isError"] is True and "INSUFFICIENT_SCOPE" in str(blocked_audience)
            blocked_profile = result(
                await call(client, application["token"], "get_learning_profile", protocol=protocol)
            )
            assert blocked_profile["isError"] is True and "INSUFFICIENT_SCOPE" in str(blocked_profile)
            materials = result(await call(client, issued["token"], "search_materials", protocol=protocol))
            assert materials["total"] == 1 and materials["items"][0]["lesson_id"] == revision.lesson_id
            denied = result(
                await call(
                    client,
                    issued["token"],
                    "get_context",
                    {"reference": fixed_reference(restricted)},
                    protocol=protocol,
                )
            )
            assert denied["isError"] is True and "LESSON_USE_NOT_ALLOWED" in str(denied)
            saved = result(
                await call(
                    client,
                    issued["token"],
                    "save_vocabulary",
                    {
                        "operation_id": "save",
                        "reference": fixed_reference(revision),
                    },
                    protocol=protocol,
                )
            )
            pending = result(
                await call(
                    client,
                    issued["token"],
                    "prepare_learning_intent",
                    {
                        "parameters": {
                            "operation_id": "review",
                            "action": "review",
                            "word_id": saved["word_id"],
                            "quality": 5,
                        }
                    },
                    protocol=protocol,
                )
            )
            denied = result(
                await call(
                    client, issued["token"], "execute_learning_intent", {"intent_id": pending["id"]}, protocol=protocol
                )
            )
            assert denied["isError"] is True and "CONFIRMATION_REQUIRED" in str(denied)
            await delegated_learning.confirm_intent(db_session, user.id, pending["id"])
            await db_session.commit()
            first = result(
                await call(
                    client, issued["token"], "execute_learning_intent", {"intent_id": pending["id"]}, protocol=protocol
                )
            )
            replay = result(
                await call(
                    client,
                    issued["token"],
                    "execute_learning_intent",
                    {"intent_id": pending["id"]},
                    request_id=3,
                    protocol=protocol,
                )
            )
            assert first == replay and first["review_count"] == 1
            assert await db_session.scalar(select(func.count()).select_from(VocabularyReviewLog)) == 1
