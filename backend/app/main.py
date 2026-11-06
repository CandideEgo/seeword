import asyncio
import uuid
from contextlib import AsyncExitStack, asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1 import (
    admin,
    admin_home_content,
    admin_teaching_content,
    auth,
    behavior,
    browse,
    catalog,
    channels,
    discovery,
    exam_pdfs,
    exams,
    external_connections,
    favorites,
    feedback,
    home_editorial,
    internal,
    learning,
    learning_plan,
    media,
    notes,
    notifications,
    payments,
    presence,
    recommendations,
    shadowing,
    teaching,
    teaching_runs,
    users,
    videos,
    vocab_sets,
    vocabulary,
    words,
)
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode, format_validation_errors, json_safe_non_finite
from app.core.limiter import limiter
from app.core.logging import configure_logging, get_logger
from app.services.ai_service import AIServiceError

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

# Initialize Sentry (web process role; the Celery app does the same for
# worker/beat). Missing DSN is a no-op, not an error.
from app.core.observability import init_sentry

init_sentry("web")


async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"code": ErrorCode.RATE_LIMITED, "message": "请求过于频繁，请稍后再试"},
    )


async def _ai_service_error_handler(request: Request, exc: AIServiceError) -> JSONResponse:
    """Surface AI/LLM failures as 502 instead of letting them become 500s or,
    worse, silent fake-zero scores. Keeps the message safe to return to clients."""
    logger.warning("ai_service_error path=%s detail=%s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={"code": ErrorCode.AI_SERVICE_UNAVAILABLE, "message": "AI 服务暂不可用，请稍后重试"},
    )


async def _app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    """业务异常 -> 统一 envelope {code, message, detail?}."""
    body: dict = {"code": exc.code, "message": exc.message}
    if exc.detail is not None:
        body["detail"] = jsonable_encoder(exc.detail)
    return JSONResponse(status_code=exc.status_code, content=body)


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """存量 HTTPException 兜底转 envelope。code = HTTP_{status}。

    保留 detail 字段以向后兼容前端旧解析（422 数组 / 字符串）。
    """
    detail = exc.detail
    if isinstance(detail, str):
        body: dict = {"code": f"HTTP_{exc.status_code}", "message": detail, "detail": detail}
    elif isinstance(detail, list):
        enc = jsonable_encoder(detail)
        body = {
            "code": ErrorCode.VALIDATION_ERROR,
            "message": format_validation_errors(enc),
            "detail": enc,
        }
    else:
        body = {"code": f"HTTP_{exc.status_code}", "message": str(detail) if detail is not None else ""}
        if detail is not None:
            body["detail"] = jsonable_encoder(detail)
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


async def _validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 422 校验错误 -> envelope {code: VALIDATION_ERROR, message, detail}."""
    # 回显的 input 可能是非有限浮点数（body 里的裸 NaN/Infinity），直接放进响应会
    # 让 json.dumps(allow_nan=False) 抛错，把 422 变成 500。
    errors = json_safe_non_finite(jsonable_encoder(exc.errors()))
    return JSONResponse(
        status_code=422,
        content={
            "code": ErrorCode.VALIDATION_ERROR,
            "message": format_validation_errors(errors),
            "detail": errors,
        },
    )


def _security_headers() -> dict[str, str]:
    """Headers every response should carry, including error responses.

    The middleware only decorates responses that travel back through it; a
    response produced by the catch-all exception handler bypasses ``call_next``
    and used to miss them.
    """
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }
    if settings.env == "production":
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        connect_src = f"'self' {settings.csp_connect_domains}" if settings.csp_connect_domains else "'self'"
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            # YouTube IFrame player (no-local-file fallback) needs its own
            # script + frame + connect sources.
            "script-src 'self' https://www.youtube.com https://s.ytimg.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "media-src 'self' https:; "
            "frame-src https://www.youtube.com https://www.youtube-nocookie.com; "
            f"connect-src {connect_src} https://www.youtube.com; "
            "object-src 'none'; "
            "base-uri 'self'"
        )
    return headers


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底：任何没被上面 5 个 handler 接住的异常 -> 500 + INTERNAL_ERROR。

    在它存在之前，服务层抛出的 `ValueError` 只要路由层没认出来（`api/v1/
    videos.py` 那 16 处 `if "not found" in msg.lower()` 式的子串匹配），就会
    穿过所有 handler，变成**没有响应体的裸 500** —— 没有 code、没有
    correlation id，客户端无从分支，只能当"服务器炸了"。

    领域失败现在走 `core/errors.py::DomainError` 家族（服务层抛，自带状态码，
    由上面的 AppError handler 接住）。所以这一层**不再是正常的错误路径**：
    它一旦被触发，就是真的没有分类过的异常，值得看一眼日志。

    只把 message 写进日志，不回给客户端——原始消息里可能有内部细节。
    Starlette 在 handler 返回后仍会重新抛出该异常，所以 ASGI 服务器自身的错误
    日志行为不变。
    """
    logger.error(
        "unhandled_exception path=%s method=%s request_id=%s exc=%s: %s",
        request.url.path,
        request.method,
        getattr(request.state, "request_id", "-"),
        type(exc).__name__,
        exc,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"code": ErrorCode.INTERNAL_ERROR, "message": "服务器内部错误，请稍后重试"},
        headers=_security_headers(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup/shutdown lifecycle.

    - Startup: services initialise lazily (Redis singleton, DB engine pool).
    - Shutdown: dispose DB engine pool and close Redis connection.
    """
    # Production safety net: without real SMS credentials the auth flow
    # would (previously) silently degrade to the fixed dev code "1234".
    # Now dev-fake is production-blocked, so a misconfigured box fails
    # closed — but surface the misconfiguration loudly at startup.
    if settings.env == "production" and not (
        settings.sms_login_enabled and settings.aliyun_sms_access_key and settings.aliyun_sms_secret_key
    ):
        logger.warning(
            "SMS credentials missing in production — phone login/register/reset "
            "will fail closed (send-code 502, verify always rejected). "
            "Set SMS_LOGIN_ENABLED=true + ALIYUN_SMS_ACCESS_KEY/SECRET_KEY."
        )
    if settings.env == "production" and not settings.alert_webhook_url:
        logger.warning(
            "ALERT_WEBHOOK_URL is not configured in production — external alerts "
            "fall back to in-app admin notifications only (best-effort, and lost "
            "if the DB is unavailable). Set it to receive pipeline failures off-site."
        )
    # ECDICT builds its in-process index lazily on first lookup (~0.7s for
    # 14k words, synchronous SQLite reads). Without prewarming, the first
    # word-card/search request after every deploy blocks its worker's event
    # loop for that whole build. Pay it once at startup instead.
    if settings.env != "testing":
        from app.services import ecdict

        if ecdict.is_available():
            try:
                await asyncio.to_thread(ecdict.get_index)
                logger.info("ecdict_index_warmed")
            except Exception:
                logger.warning("ecdict index prewarm failed; first lookup will build it", exc_info=True)
    # Cross-worker notification fan-out. Tests drive the subscriber directly
    # with a fake pubsub instead of starting a real connection.
    if settings.env != "testing":
        from app.services.notification_transport import start_notification_subscriber

        start_notification_subscriber()
    # A09/OPS-05: worker/beat/queue/disk/pipeline-failure watchdog that alerts
    # off-site. Runs here rather than in beat because it must survive the
    # processes it watches; the external uptime check covers this process.
    from app.services.health_monitor import start_health_monitor

    health_monitor_task = start_health_monitor()
    async with AsyncExitStack() as stack:
        mcp_app = getattr(app.state, "mcp_app", None)
        if mcp_app is not None:
            await stack.enter_async_context(mcp_app.router.lifespan_context(mcp_app))
        yield
    # --- Shutdown ---
    if health_monitor_task is not None:
        health_monitor_task.cancel()
        try:
            await health_monitor_task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.warning("health monitor shutdown failed", exc_info=True)
    if settings.env != "testing":
        from app.services.notification_transport import stop_notification_subscriber

        await stop_notification_subscriber()

    from app.core.database import engine as db_engine

    await db_engine.dispose()
    logger.info("database_engine_disposed")

    from app.core.redis import close_redis

    await close_redis()

    from app.api.v1.media import close_proxy_client

    await close_proxy_client()


def create_app() -> FastAPI:
    # Import all models so SQLAlchemy registers them on Base.metadata before
    # any create_all (e.g. conftest in tests) or Alembic autogenerate runs.
    from app import models  # noqa: F401  (import registers every model on Base.metadata)

    # Defence in depth: the public docs/schema (and the metrics endpoint) are
    # useful in dev but are not part of the public surface. Production nginx
    # happens to route only /api/, /media/ and /health to the backend, but a
    # future proxy change must not be the only thing hiding them.
    is_production = settings.env == "production"
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )
    Instrumentator().instrument(app).expose(app, endpoint="/internal/metrics" if is_production else "/metrics")

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_exception_handler(AIServiceError, _ai_service_error_handler)
    app.add_exception_handler(AppError, _app_exception_handler)
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    # Catch-all last: anything reaching the ASGI server unhandled becomes a
    # typed 500 envelope instead of a body-less one. See the handler's docstring
    # — its main job right now is to enumerate what is still leaking.
    app.add_exception_handler(Exception, _unhandled_exception_handler)

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        response = await call_next(request)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            request_id=getattr(request.state, "request_id", "-"),
        )
        return response

    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update(_security_headers())
        return response

    allowed_origins = (
        ["http://localhost:3000", "http://127.0.0.1:3000"] if settings.env == "development" else [settings.frontend_url]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    media_path = Path(settings.local_media_path).resolve()
    media_path.mkdir(parents=True, exist_ok=True)
    # Range-aware media serving (Starlette StaticFiles ignores Range headers,
    # which breaks <video> seeking). See app/api/v1/media.py.
    app.include_router(media.router)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(videos.router, prefix="/api/v1")
    app.include_router(favorites.router, prefix="/api/v1")
    app.include_router(presence.router, prefix="/api/v1")
    app.include_router(payments.router, prefix="/api/v1")
    if settings.env in ("development", "testing"):
        from app.api.v1 import mock_payments

        app.include_router(mock_payments.router, prefix="/api/v1")
    app.include_router(vocabulary.router, prefix="/api/v1")
    app.include_router(vocab_sets.router, prefix="/api/v1")
    app.include_router(words.router, prefix="/api/v1")
    app.include_router(browse.router, prefix="/api/v1")
    # 首页编辑内容：公共读取（无缓存，见 services.home_content_service.resolve_public_page）
    app.include_router(home_editorial.router, prefix="/api/v1")
    app.include_router(recommendations.router, prefix="/api/v1")
    app.include_router(channels.router, prefix="/api/v1")
    app.include_router(discovery.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(admin_teaching_content.router, prefix="/api/v1")
    # 管理员首页编辑内容（草稿/生成/发布/布局）；鉴权在路由内用 get_admin_user。
    app.include_router(admin_home_content.router, prefix="/api/v1")
    app.include_router(catalog.router, prefix="/api/v1")
    app.include_router(feedback.router, prefix="/api/v1")
    app.include_router(feedback.admin_router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(notes.router, prefix="/api/v1")
    app.include_router(learning.router, prefix="/api/v1")
    app.include_router(learning_plan.router, prefix="/api/v1")
    app.include_router(shadowing.router, prefix="/api/v1")
    app.include_router(behavior.router, prefix="/api/v1")
    from app.api.v1 import listening

    app.include_router(listening.router, prefix="/api/v1")
    app.include_router(exams.router, prefix="/api/v1")
    app.include_router(teaching.router, prefix="/api/v1")
    app.include_router(teaching_runs.router, prefix="/api/v1")
    app.include_router(external_connections.router, prefix="/api/v1")
    mcp_app = None
    if settings.mcp_sdk_enabled:
        try:
            from app.integrations.mcp.server import create_mcp_app

            mcp_app = create_mcp_app()
        except ImportError:
            # The MCP SDK is deliberately absent from the cloud dependency set
            # (it conflicts with the pinned Uvicorn). A switch alone must not
            # take the whole API down: degrade to the same 503 as "disabled".
            logger.warning("MCP_SDK_ENABLED is set but the MCP SDK is not installed; serving 503")
    if mcp_app is not None:
        app.state.mcp_app = mcp_app
        app.mount("/api/v1/mcp", mcp_app)
    else:

        @app.api_route("/api/v1/mcp/", methods=["GET", "POST", "DELETE"], include_in_schema=False)
        async def unavailable_mcp():
            raise AppError(503, ErrorCode.SERVICE_UNAVAILABLE, "MCP 接入尚未通过运行环境与宿主验收")

    # 原卷 PDF 单独一个 router：exams 的末尾 catch-all GET /{paper_id} 会把
    # /exams/pdfs 当 paper_id 吃掉。
    app.include_router(exam_pdfs.router, prefix="/api/v1")
    app.include_router(internal.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        checks = {}
        all_healthy = True

        # --- Database connectivity check ---
        try:
            from app.core.database import engine as db_engine

            async with db_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = {"status": "ok"}
        except Exception as exc:
            all_healthy = False
            checks["database"] = {"status": "error", "detail": type(exc).__name__}

        # --- Redis connectivity check (using shared client) ---
        try:
            from app.core.redis import get_redis

            redis_client = get_redis()
            await redis_client.ping()
            checks["redis"] = {"status": "ok"}
        except Exception as exc:
            all_healthy = False
            checks["redis"] = {"status": "error", "detail": type(exc).__name__}

        payload = {
            "status": "ok" if all_healthy else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "environment": settings.env,
            "components": checks,
        }

        status_code = 200 if all_healthy else 503
        return JSONResponse(content=payload, status_code=status_code)

    @app.get("/health/heartbeats")
    async def health_heartbeats():
        """Worker/beat liveness for an external uptime checker (A09/OPS-05).

        ``/health`` stays as the compose probe (DB + Redis only) because making
        it 503 on a stale worker would restart the *backend* and fix nothing.
        This endpoint is meant for an off-site monitor: 503 when the cloud
        worker or beat heartbeat is missing/stale, 200 otherwise. The GPU
        worker is reported but does not fail the check — it may be offline on
        purpose (embed playback is the fallback), and its backlog is alerted by
        the in-process monitor instead.
        """
        from app.core.heartbeat import (
            BEAT_HEARTBEAT_KEY,
            GPU_HEARTBEAT_KEY,
            WORKER_HEARTBEAT_KEY,
            age_seconds,
        )
        from app.core.redis import get_redis

        components: dict = {}
        healthy = True
        try:
            redis_client = get_redis()
            worker_age = age_seconds(await redis_client.get(WORKER_HEARTBEAT_KEY))
            beat_age = age_seconds(await redis_client.get(BEAT_HEARTBEAT_KEY))
            gpu_online = bool(await redis_client.exists(GPU_HEARTBEAT_KEY))
        except Exception as exc:
            healthy = False
            components["redis"] = {"status": "error", "detail": type(exc).__name__}
        else:
            worker_ok = worker_age is not None and worker_age <= settings.health_worker_stale_seconds
            beat_ok = beat_age is not None and beat_age <= settings.health_beat_stale_seconds
            healthy = worker_ok and beat_ok
            components["cloud_worker"] = {
                "status": "ok" if worker_ok else "stale",
                "age_seconds": worker_age,
            }
            components["beat"] = {"status": "ok" if beat_ok else "stale", "age_seconds": beat_age}
            components["gpu_worker"] = {"status": "online" if gpu_online else "offline"}

        return JSONResponse(
            content={
                "status": "ok" if healthy else "degraded",
                "timestamp": datetime.now(UTC).isoformat(),
                "components": components,
            },
            status_code=200 if healthy else 503,
        )

    return app


app = create_app()
