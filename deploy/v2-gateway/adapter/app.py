"""Thin gateway adapter for SeeWord V2.

Two stateless relays around LiteLLM, so LiteLLM stays the single usage/cost
ledger:

* ``app`` (inbound, port 4000): drop-in proxy in front of LiteLLM. It rejects a
  request whose ``max_tokens`` exceeds the verified cap for its model, and when
  the caller disconnects it keeps the LiteLLM request running to completion so
  LiteLLM settles instead of releasing the reservation on cancellation.
  SSE completions are relayed incrementally; JSON responses stay buffered.
* ``shim_app`` (outbound, port 4100): LiteLLM's provider ``api_base`` points
  here. It forwards to the real provider and, when the provider omits a
  ``usage`` block, injects the conservative upper bound (estimated prompt
  tokens + requested output cap) so LiteLLM charges it through its normal
  settlement path. SSE streams are relayed line by line so the usage chunk is
  appended at the end without buffering the turn.

No provider keys, budgets, or cost rows are stored here.
"""

import asyncio
import json
import math
import os
from typing import Any

import content_receipts
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

LITELLM_BASE = os.environ.get("LITELLM_BASE_URL", "http://gateway:4000").rstrip("/")
UPSTREAM_BASE = os.environ.get("UPSTREAM_BASE_URL", "http://synthetic-provider:4010/v1").rstrip("/")
MODEL_MAX_OUTPUT_TOKENS = int(os.environ.get("MODEL_MAX_OUTPUT_TOKENS", "128"))
ADAPTER_TIMEOUT_SECONDS = float(os.environ.get("ADAPTER_TIMEOUT_SECONDS", "60"))

_HOP_HEADERS = {
    "host",
    "content-length",
    "connection",
    "keep-alive",
    "transfer-encoding",
    "upgrade",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
}

# Keep drained requests alive after the caller is gone.
_background: set[asyncio.Task[Any]] = set()


def _forward_headers(request: Request) -> dict[str, str]:
    return {key: value for key, value in request.headers.items() if key.lower() not in _HOP_HEADERS}


def _response_headers(headers: httpx.Headers) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in _HOP_HEADERS and key.lower() != "content-encoding"
    }


def _estimate_prompt_tokens(body: bytes) -> int:
    """Deliberately conservative upper bound, not a tokenizer claim.

    Two bytes per token over-counts English and covers CJK UTF-8 at roughly one
    token per character; unknown-usage charging should err high.
    """
    return max(1, math.ceil(len(body) / 2) + 8)


def _requested_output(payload: dict[str, Any]) -> int:
    value = payload.get("max_tokens", payload.get("max_completion_tokens"))
    if value is None:
        raise ValueError("max_tokens is required")
    tokens = int(value)
    if tokens <= 0:
        raise ValueError("max_tokens must be positive")
    return tokens


def model_output_caps() -> dict[str, int]:
    """Per-model verified caps; unlisted models keep the legacy single cap.

    The streamed tutor needs a wider envelope than the 128-token cards /
    content-verification turn. A single global number would either loosen the
    narrow path or reject the tutor, so the cap is keyed by the gateway model
    alias: a deployment that verified a model raises only that entry. Invalid
    configuration falls back to the default cap (fail closed).
    """
    raw = os.environ.get("ADAPTER_MODEL_OUTPUT_CAPS", "").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except ValueError:
        return {}
    if not isinstance(value, dict):
        return {}
    caps: dict[str, int] = {}
    for model, cap in value.items():
        if isinstance(model, str) and isinstance(cap, int) and not isinstance(cap, bool) and 0 < cap <= 65536:
            caps[model] = cap
    return caps


def _model_cap(payload: dict[str, Any]) -> int:
    model = payload.get("model")
    if isinstance(model, str):
        cap = model_output_caps().get(model)
        if cap is not None:
            return cap
    return MODEL_MAX_OUTPUT_TOKENS


def _conservative_cap(payload: dict[str, Any]) -> int:
    """Shim-side upper bound.

    LiteLLM sends the *provider* model name to the shim, not the routing alias,
    so a caps map keyed by alias may not match. Under-counting a missing usage
    block is worse than over-counting, so fall back to the widest configured
    cap rather than the legacy default.
    """
    caps = model_output_caps()
    model = payload.get("model")
    if isinstance(model, str) and model in caps:
        return caps[model]
    return max([MODEL_MAX_OUTPUT_TOKENS, *caps.values()])


def _wants_stream(payload: dict[str, Any]) -> bool:
    return payload.get("stream") is True


def _error(status: int, error_type: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"message": message, "type": error_type}}, status_code=status)


def _keep_running(task: asyncio.Task[Any]) -> None:
    _background.add(task)
    task.add_done_callback(_background.discard)


async def _call(url: str, method: str, headers: dict[str, str], body: bytes) -> tuple[int, dict[str, str], bytes]:
    async with httpx.AsyncClient(timeout=ADAPTER_TIMEOUT_SECONDS) as client:
        response = await client.request(method, url, headers=headers, content=body)
        return (
            response.status_code,
            _response_headers(response.headers),
            response.content,
        )


app = FastAPI(title="SeeWord V2 gateway adapter")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _drained_call(
    url: str, method: str, headers: dict[str, str], body: bytes
) -> tuple[int, dict[str, str], bytes]:
    task = asyncio.create_task(_call(url, method, headers, body))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        _keep_running(task)
        raise


async def _drain_stream(client: httpx.AsyncClient, response: httpx.Response) -> None:
    """Finish the upstream body after the caller is gone so the ledger settles."""
    try:
        async for _ in response.aiter_bytes():
            pass
    except Exception:
        pass
    finally:
        try:
            await response.aclose()
        finally:
            await client.aclose()


async def _stream_proxy(request: Request, url: str, body: bytes) -> Response:
    """Relay an SSE completion incrementally instead of buffering the whole turn."""
    client = httpx.AsyncClient(timeout=ADAPTER_TIMEOUT_SECONDS)
    headers = _forward_headers(request)
    # The relay forwards decoded bytes and drops content-encoding, so the
    # upstream must not compress. The outbound shim already does the same.
    headers.pop("accept-encoding", None)
    upstream = client.build_request(request.method, url, headers=headers, content=body)
    try:
        response = await client.send(upstream, stream=True)
    except httpx.HTTPError:
        await client.aclose()
        raise
    out_headers = _response_headers(response.headers)
    if "text/event-stream" not in out_headers.get("content-type", ""):
        # An error body or a provider that ignored `stream`: behave as before.
        try:
            content = await response.aread()
        finally:
            await response.aclose()
            await client.aclose()
        return Response(content=content, status_code=response.status_code, headers=out_headers)

    # A dedicated pump owns the upstream iterator. The response generator only
    # consumes a queue, so a client disconnect cannot abandon (and close) the
    # upstream stream: the pump keeps reading until LiteLLM has settled.
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()

    async def pump() -> None:
        try:
            async for chunk in response.aiter_bytes():
                queue.put_nowait(chunk)
        except Exception:
            pass
        finally:
            queue.put_nowait(None)
            try:
                await response.aclose()
            finally:
                await client.aclose()

    _keep_running(asyncio.create_task(pump()))

    async def relay():
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    return StreamingResponse(relay(), status_code=response.status_code, headers=out_headers)


@app.post("/content-verification/{kind}")
async def verify_content(request: Request, kind: str) -> Response:
    if not request.headers.get("authorization", "").lower().startswith("bearer "):
        return _error(401, "authentication_error", "A gateway credential is required")
    body = await request.body()
    if len(body) > 131072:
        return _error(413, "verification_input_too_large", "Verification input exceeds 128 KiB")
    try:
        payload = json.loads(body)
        completion, receipt_input = content_receipts.completion_request(kind, payload, MODEL_MAX_OUTPUT_TOKENS)
    except (ValueError, TypeError, KeyError, AttributeError):
        return _error(422, "verification_input_invalid", "Invalid verification input")
    try:
        signer = content_receipts.signer()
    except content_receipts.ReceiptConfigurationError:
        return _error(503, "verification_unavailable", "Content receipt signing is not configured")
    try:
        status, _, response = await _drained_call(
            f"{LITELLM_BASE}/chat/completions",
            "POST",
            _forward_headers(request),
            json.dumps(completion, ensure_ascii=False, allow_nan=False).encode(),
        )
    except httpx.HTTPError:
        return _error(502, "verification_upstream_error", "Gateway verification request failed")
    if status != 200:
        return _error(
            status if 400 <= status < 600 else 502,
            "verification_upstream_error",
            "Gateway rejected verification",
        )
    try:
        data = json.loads(response)
        if not isinstance(data, dict):
            raise ValueError("Invalid gateway response")
        return JSONResponse(
            content_receipts.issue(kind, receipt_input, data, signer),
            headers={"Cache-Control": "no-store"},
        )
    except (ValueError, TypeError, KeyError, AttributeError):
        return _error(
            502,
            "verification_response_invalid",
            "No valid verification receipt was produced",
        )


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(request: Request, path: str) -> Response:
    body = await request.body()
    query = request.url.query
    target = f"{LITELLM_BASE}/{path}" + (f"?{query}" if query else "")
    is_completion = path.rstrip("/") in {"chat/completions", "v1/chat/completions"}
    stream = False
    if is_completion:
        try:
            payload = json.loads(body or b"{}")
            output_tokens = _requested_output(payload)
            cap = _model_cap(payload)
        except (ValueError, TypeError) as exc:
            return _error(422, "adapter_error", str(exc))
        if output_tokens > cap:
            return _error(
                422,
                "output_cap_exceeded",
                f"max_tokens {output_tokens} exceeds the verified model output cap {cap}",
            )
        stream = _wants_stream(payload)

    if stream:
        try:
            return await _stream_proxy(request, target, body)
        except httpx.HTTPError:
            return _error(502, "gateway_upstream_error", "Gateway streaming request failed")

    status, headers, content = await _drained_call(target, request.method, _forward_headers(request), body)
    return Response(content=content, status_code=status, headers=headers)


shim_app = FastAPI(title="SeeWord V2 provider usage shim")


@shim_app.get("/health")
async def shim_health() -> dict[str, str]:
    return {"status": "ok"}


async def _forward_upstream(request: Request, body: bytes) -> tuple[int, dict[str, str], bytes]:
    headers = _forward_headers(request)
    headers.pop("accept-encoding", None)
    if os.environ.get("ADAPTER_DEBUG_HEADERS") == "1":
        safe = {
            key: (f"<{len(value)} chars>" if key.lower() == "authorization" else value)
            for key, value in headers.items()
        }
        print(f"upstream headers: {safe}", flush=True)
    async with httpx.AsyncClient(timeout=ADAPTER_TIMEOUT_SECONDS) as client:
        response = await client.post(f"{UPSTREAM_BASE}/chat/completions", headers=headers, content=body)
        return (
            response.status_code,
            _response_headers(response.headers),
            response.content,
        )


def _conservative_usage(body: bytes, payload: dict[str, Any]) -> dict[str, Any]:
    requested = payload.get("max_tokens", payload.get("max_completion_tokens"))
    cap = _conservative_cap(payload)
    output_cap = cap if requested is None else min(int(requested), cap)
    prompt = _estimate_prompt_tokens(body)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": output_cap,
        "total_tokens": prompt + output_cap,
    }


def _usage_chunk(payload: dict[str, Any], body: bytes) -> bytes:
    chunk = json.dumps(
        {
            "id": "adapter-usage",
            "object": "chat.completion.chunk",
            "choices": [],
            "usage": _conservative_usage(body, payload),
        },
        ensure_ascii=False,
    )
    return f"data: {chunk}\n\n".encode()


def _line_has_usage(line: bytes) -> bool:
    """True only for a well-formed usage object; ``null`` or garbage is not usage."""
    data = line.strip()
    if not data.startswith(b"data:"):
        return False
    try:
        value = json.loads(data[5:].strip())
    except ValueError:
        return False
    return isinstance(value, dict) and isinstance(value.get("usage"), dict)


async def _stream_shim(request: Request, body: bytes, payload: dict[str, Any]) -> Response:
    """Relay the provider SSE incrementally; append conservative usage at the end."""
    client = httpx.AsyncClient(timeout=ADAPTER_TIMEOUT_SECONDS)
    headers = _forward_headers(request)
    headers.pop("accept-encoding", None)
    upstream = client.build_request("POST", f"{UPSTREAM_BASE}/chat/completions", headers=headers, content=body)
    try:
        response = await client.send(upstream, stream=True)
    except httpx.HTTPError:
        await client.aclose()
        raise
    out_headers = _response_headers(response.headers)
    if response.status_code >= 300 or "text/event-stream" not in out_headers.get("content-type", ""):
        try:
            content = await response.aread()
        finally:
            await response.aclose()
            await client.aclose()
        return Response(content=content, status_code=response.status_code, headers=out_headers)

    async def relay():
        buffer = b""
        held_done = b""
        usage_seen = False
        try:
            async for chunk in response.aiter_bytes():
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line += b"\n"
                    if b"[DONE]" in line and line.strip().startswith(b"data:"):
                        held_done = line
                        continue
                    if _line_has_usage(line):
                        usage_seen = True
                    yield line
            if buffer:
                yield buffer
            if not usage_seen:
                yield _usage_chunk(payload, body)
            if held_done:
                yield held_done
            else:
                yield b"data: [DONE]\n\n"
        finally:
            _keep_running(asyncio.create_task(_drain_stream(client, response)))

    return StreamingResponse(relay(), status_code=response.status_code, headers=out_headers)


@shim_app.api_route("/{path:path}", methods=["POST"])
async def shim(request: Request, path: str) -> Response:
    body = await request.body()
    try:
        payload = json.loads(body or b"{}")
    except ValueError:
        return _error(400, "adapter_error", "invalid json")
    if _wants_stream(payload):
        try:
            return await _stream_shim(request, body, payload)
        except httpx.HTTPError:
            return _error(502, "adapter_error", "provider streaming request failed")
    status, headers, content = await _forward_upstream(request, body)
    if status >= 300:
        return Response(content=content, status_code=status, headers=headers)

    content_type = headers.get("content-type", "")
    if "text/event-stream" in content_type:
        # A streamed body without a `stream:true` request is still relayed;
        # parsing only complete lines keeps the usage decision structured.
        text = content.decode("utf-8", "replace")
        if not any(_line_has_usage(line.encode()) for line in text.splitlines()):
            usage = json.dumps(
                {
                    "id": "adapter-usage",
                    "object": "chat.completion.chunk",
                    "choices": [],
                    "usage": _conservative_usage(body, payload),
                },
                ensure_ascii=False,
            )
            marker = "data: [DONE]"
            if marker in text:
                text = text.replace(marker, f"data: {usage}\n\n{marker}", 1)
            else:
                text = f"{text.rstrip()}\n\ndata: {usage}\n\ndata: [DONE]\n\n"
        return Response(content=text.encode(), status_code=status, headers=headers)

    try:
        data = json.loads(content)
    except ValueError:
        return Response(content=content, status_code=status, headers=headers)
    if isinstance(data, dict) and not data.get("usage"):
        data["usage"] = _conservative_usage(body, payload)
    return JSONResponse(data, status_code=status)
