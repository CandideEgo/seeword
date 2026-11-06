"""Unit tests for the thin gateway adapter.

Run from this directory with:
  python -m pytest test_adapter.py -q
The integration behaviour (drain on disconnect, LiteLLM settlement) is covered
by backend/scripts/check_v2_gateway.py against the synthetic Compose stack.
"""

import json

import httpx
import pytest

import app as adapter

# Captured before any test replaces it: adapter code and this helper share the module.
_REAL_CLIENT = httpx.AsyncClient


@pytest.fixture(autouse=True)
def restore_env(monkeypatch):
    monkeypatch.setattr(adapter, "MODEL_MAX_OUTPUT_TOKENS", 128)
    monkeypatch.delenv("ADAPTER_MODEL_OUTPUT_CAPS", raising=False)
    yield


def use_transport(monkeypatch, handler):
    monkeypatch.setattr(
        adapter.httpx, "AsyncClient", lambda *a, **kw: _REAL_CLIENT(*a, transport=httpx.MockTransport(handler), **kw)
    )


def run(application, method, url, **kwargs):
    async def go():
        transport = httpx.ASGITransport(app=application)
        async with _REAL_CLIENT(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, url, **kwargs)

    return __import__("asyncio").run(go())


def test_rejects_output_above_cap(monkeypatch):
    async def boom(*_args, **_kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(adapter, "_call", boom)
    response = run(adapter.app, "POST", "/chat/completions", json={"max_tokens": 129})
    assert response.status_code == 422
    assert response.json()["error"]["type"] == "output_cap_exceeded"


def test_requires_max_tokens(monkeypatch):
    async def boom(*_args, **_kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(adapter, "_call", boom)
    response = run(adapter.app, "POST", "/v1/chat/completions", json={"messages": []})
    assert response.status_code == 422


def test_proxies_admin_query_string(monkeypatch):
    seen = {}

    async def fake_call(url, method, headers, body):
        seen["url"] = url
        return 200, {"content-type": "application/json"}, b'{"ok":true}'

    monkeypatch.setattr(adapter, "_call", fake_call)
    response = run(adapter.app, "GET", "/team/info?team_id=abc-123")
    assert response.status_code == 200
    assert seen["url"].endswith("/team/info?team_id=abc-123")


def test_shim_injects_conservative_usage(monkeypatch):
    async def fake_upstream(request, body):
        return (
            200,
            {"content-type": "application/json"},
            json.dumps({"id": "x", "choices": [{"message": {"role": "assistant", "content": "hi"}}]}).encode(),
        )

    monkeypatch.setattr(adapter, "_forward_upstream", fake_upstream)
    request_body = {"model": "m", "messages": [{"role": "user", "content": "hello"}], "max_tokens": 64}
    response = run(
        adapter.shim_app,
        "POST",
        "/v1/chat/completions",
        json=request_body,
        headers={"Authorization": "Bearer provider-key"},
    )
    assert response.status_code == 200
    usage = response.json()["usage"]
    assert usage["completion_tokens"] == 64
    assert usage["prompt_tokens"] > 0


def test_shim_keeps_provider_usage(monkeypatch):
    provider_usage = {"prompt_tokens": 7, "completion_tokens": 9, "total_tokens": 16}

    async def fake_upstream(request, body):
        return (
            200,
            {"content-type": "application/json"},
            json.dumps({"id": "x", "choices": [], "usage": provider_usage}).encode(),
        )

    monkeypatch.setattr(adapter, "_forward_upstream", fake_upstream)
    response = run(
        adapter.shim_app,
        "POST",
        "/v1/chat/completions",
        json={"model": "m", "messages": [], "max_tokens": 64},
    )
    assert response.json()["usage"] == provider_usage


def test_shim_defaults_to_model_cap_when_max_tokens_missing(monkeypatch):
    async def fake_upstream(request, body):
        return 200, {"content-type": "application/json"}, json.dumps({"id": "x", "choices": []}).encode()

    monkeypatch.setattr(adapter, "_forward_upstream", fake_upstream)
    response = run(adapter.shim_app, "POST", "/v1/chat/completions", json={"model": "m", "messages": []})
    assert response.json()["usage"]["completion_tokens"] == 128


def test_per_model_cap_only_widens_the_listed_model(monkeypatch):
    monkeypatch.setenv("ADAPTER_MODEL_OUTPUT_CAPS", '{"tutor": 1024}')

    async def boom(*_args, **_kwargs):
        raise AssertionError("upstream must not be called")

    monkeypatch.setattr(adapter, "_call", boom)
    too_wide = run(adapter.app, "POST", "/chat/completions", json={"model": "teaching", "max_tokens": 1024})
    assert too_wide.status_code == 422 and too_wide.json()["error"]["type"] == "output_cap_exceeded"
    assert adapter._model_cap({"model": "tutor"}) == 1024
    assert adapter._model_cap({"model": "unknown"}) == 128


def test_invalid_caps_configuration_falls_back_to_the_default(monkeypatch):
    monkeypatch.setenv("ADAPTER_MODEL_OUTPUT_CAPS", '{"tutor": "wide"}')
    assert adapter._model_cap({"model": "tutor"}) == 128


def test_inbound_proxy_relays_sse_incrementally(monkeypatch):
    async def handler(request):
        assert json.loads(request.content)["stream"] is True

        async def body():
            yield b'data: {"choices":[{"delta":{"content":"he"}}]}\n\n'
            yield b'data: {"choices":[{"delta":{"content":"llo"}}]}\n\n'
            yield b"data: [DONE]\n\n"

        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body())

    use_transport(monkeypatch, handler)
    response = run(
        adapter.app,
        "POST",
        "/v1/chat/completions",
        json={"model": "teaching", "max_tokens": 64, "stream": True},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text.count("data:") == 3
    assert "hello" not in response.text  # relayed verbatim, never assembled


def test_shim_streams_upstream_and_appends_conservative_usage(monkeypatch):
    async def handler(request):
        async def body():
            yield b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
            yield b"data: [DONE]\n\n"

        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body())

    use_transport(monkeypatch, handler)
    response = run(
        adapter.shim_app,
        "POST",
        "/v1/chat/completions",
        json={"model": "tutor", "max_tokens": 1024, "stream": True},
        headers={"Authorization": "Bearer provider-key"},
    )
    text = response.text
    assert '"usage"' in text and text.index('"usage"') < text.index("[DONE]")
    assert '"completion_tokens": 128' in text  # default cap without the per-model override


def test_shim_does_not_duplicate_provider_stream_usage(monkeypatch):
    async def handler(request):
        async def body():
            yield b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
            yield b'data: {"choices":[],"usage":{"prompt_tokens":1,"completion_tokens":2,"total_tokens":3}}\n\n'
            yield b"data: [DONE]\n\n"

        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body())

    use_transport(monkeypatch, handler)
    response = run(
        adapter.shim_app,
        "POST",
        "/v1/chat/completions",
        json={"model": "tutor", "max_tokens": 1024, "stream": True},
    )
    assert response.text.count('"usage"') == 1


def test_stream_relay_keeps_draining_after_client_disconnect(monkeypatch):
    """The pump owns the upstream iterator, so a disconnect still settles the call."""
    import asyncio

    from starlette.requests import Request

    release = asyncio.Event()
    upstream_finished = asyncio.Event()

    async def handler(request):
        async def body():
            yield b'data: {"a":1}\n\n'
            await release.wait()
            yield b'data: {"a":2}\n\n'
            yield b"data: [DONE]\n\n"
            upstream_finished.set()

        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body())

    use_transport(monkeypatch, handler)

    async def go():
        request = Request({"type": "http", "method": "POST", "path": "/chat/completions", "headers": []})
        response = await adapter._stream_proxy(
            request,
            "http://gateway.test/chat/completions",
            b'{"model": "tutor", "max_tokens": 1024, "stream": true}',
        )
        iterator = response.body_iterator
        first = await iterator.__anext__()
        assert b'"a":1' in first
        await iterator.aclose()  # the client goes away mid-stream
        release.set()
        await asyncio.wait_for(upstream_finished.wait(), 5)
        await asyncio.sleep(0)

    asyncio.run(go())
