"""Shared test fixtures for Speaking backend tests.

Test database: in-memory SQLite (aiosqlite), isolated from the real Postgres.
Redis: an in-memory fake is injected via ``app.core.redis`` so that
quiz/notification flows can be tested without a live Redis server.

IMPORTANT: the async autouse fixtures (``_async_setup``) are scoped to async
tests only. Applying an async autouse fixture to a plain sync test makes
pytest-asyncio hang, which is why the suite previously deadlocked when sync
files (test_whisperx_segmentation, test_sr_service) were collected alongside
async files.
"""

import os
import time
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Set env before any app imports so limiter/config pick up "testing"
os.environ["ENV"] = "testing"
# Was DATABASE_URL provided by the caller (CI/dev) rather than defaulted below?
# Integration tests only auto-target it when explicit — the conftest fallback
# below is the production URL, never a safe test target.
_db_url_explicit = "DATABASE_URL" in os.environ
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://speaking:speaking_dev@localhost:5432/speaking")
os.environ.setdefault("JWT_SECRET", "test_secret_for_pytest_at_least_32_chars")
# The fixed-code dev fake is opt-in (BE-06); tests exercise phone flows with it.
os.environ.setdefault("SMS_DEV_FAKE_ENABLED", "true")
# The punctuation restoration model imports `transformers` (5.x), whose import
# hangs indefinitely on this platform. Disable it in tests — the module falls
# back to no-punctuation mode, and the dedicated tests assert graceful fallback.
os.environ.setdefault("PUNCTUATION_MODEL_DISABLED", "1")

# Force-register all ORM models on Base.metadata so the autouse
# _async_setup fixture can create_all() them, including models added
# after the ``create_app`` import above. (create_app does the same import
# but only when called; this conftest fixture runs before any test
# invokes create_app.)
from app import models  # noqa: F401  (import registers every model on Base.metadata)
from app.core import redis as redis_module
from app.core.database import Base, get_db
from app.core.security import create_token, hash_password
from app.main import create_app

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Postgres integration-test support (marker: integration)
# ---------------------------------------------------------------------------
# The default suite runs on in-memory SQLite, where ``with_for_update`` /
# ``skip_locked`` are silently ignored and JSON / ILIKE / BigInteger semantics
# differ from production. Tests marked ``integration`` (see
# test_celery_tasks_pg.py) instead run against a real Postgres so the Celery
# task bodies' row-lock ordering is actually exercised.
#
# URL resolution: ``PG_TEST_URL`` wins; otherwise the configured
# ``DATABASE_URL`` when it points at Postgres (CI's backend job sets it to its
# Postgres service). When no Postgres is reachable the tests skip loudly —
# CI always provisions one, so they run for real there; locally point
# ``PG_TEST_URL`` at any Postgres (e.g. ``docker compose -f
# docker-compose.dev.yml up -d db``).
#
# The engine uses ``NullPool`` on purpose: task bodies execute on the shared
# celery-asyncio background loop (``run_async``), while the test body runs on
# the pytest loop. asyncpg connections are loop-bound, so connections must
# never be pooled across loops — NullPool opens a fresh loop-local connection
# per session and closes it on release.

PG_TEST_URL = os.environ.get("PG_TEST_URL") or (
    os.environ["DATABASE_URL"]
    if _db_url_explicit and os.environ.get("DATABASE_URL", "").startswith("postgresql")
    else ""
)

_pg_engine: AsyncEngine | None = None


async def _pg_engine_or_skip() -> AsyncEngine:
    """Return the cached Postgres test engine, skipping when unreachable."""
    global _pg_engine
    if _pg_engine is not None:
        return _pg_engine
    if not PG_TEST_URL:
        pytest.skip("integration tests need PG_TEST_URL or a postgresql DATABASE_URL")
    probe = create_async_engine(PG_TEST_URL, poolclass=NullPool, connect_args={"timeout": 3})
    try:
        async with probe.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:  # any failure -> skip with reason
        await probe.dispose()
        pytest.skip(f"Postgres unreachable at {PG_TEST_URL!r}: {exc}")
    await probe.dispose()
    _pg_engine = create_async_engine(PG_TEST_URL, poolclass=NullPool, connect_args={"timeout": 5})
    return _pg_engine


class _FakeRedis:
    """Minimal in-memory async Redis substitute used in tests.

    Implements only the subset of commands the app relies on:
    get/set/setex/delete/exists/ping/aclose.

    TTL semantics: ``setex``/``set(ex=...)`` record an expiry; ``get`` /
    ``exists`` purge expired keys so cooldown/expiry logic is testable.
    ``_store`` remains a plain ``dict[str, str]`` (tests inspect it directly);
    expiry lives in a parallel ``_expires`` map keyed by monotonic timestamps.
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._expires: dict[str, float] = {}

    def __await__(self):
        """Awaiting the client resolves to the client itself, mirroring
        redis-py 5.0.0's ``Redis.__await__`` (``self.initialize()``). Production
        call sites write ``redis = await get_redis()``; without this the
        ``await`` raises TypeError *inside* their fail-open ``try/except``, so
        detail-cache invalidation silently no-ops in tests — the same blindspot
        as the missing ``scan_iter`` below. See
        ``wiki/problems/cache-invalidation-and-media-gate-blindspots.md``.
        """

        async def _self() -> "_FakeRedis":
            return self

        return _self().__await__()

    def _purge(self, key: str) -> None:
        exp = self._expires.get(key)
        if exp is not None and exp <= time.monotonic():
            self._store.pop(key, None)
            self._expires.pop(key, None)

    async def get(self, key: str) -> str | None:
        self._purge(key)
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> str | None:
        if nx:
            self._purge(key)
            if key in self._store:
                return None
        self._store[key] = value
        if ex is not None:
            self._expires[key] = time.monotonic() + ex
        else:
            self._expires.pop(key, None)
        return "OK"

    async def setex(self, key: str, ttl: int, value: str) -> str | None:
        self._store[key] = value
        self._expires[key] = time.monotonic() + ttl
        return "OK"

    async def delete(self, key: str) -> int:
        existed = key in self._store
        self._store.pop(key, None)
        self._expires.pop(key, None)
        return 1 if existed else 0

    async def exists(self, key: str) -> bool:
        self._purge(key)
        return key in self._store

    async def ping(self) -> bool:
        return True

    async def scan(self, cursor: int = 0, match: str | None = None, count: int | None = None):
        """SCAN: return (0, matching keys) in one page (fake has no cursor)."""
        import fnmatch

        keys = list(self._store.keys())
        if match:
            keys = [k for k in keys if fnmatch.fnmatch(k, match)]
        return (0, keys)

    def scan_iter(self, match: str | None = None, count: int | None = None):
        """Async generator mirroring redis-py's ``scan_iter`` (used by
        ``cache_delete``). Without it, cache invalidation silently no-ops in
        tests (fail-open swallows the AttributeError), which would hide stale
        cache reads — e.g. a taken-down video still showing in the feed.
        """
        import fnmatch

        async def _gen():
            for key in list(self._store.keys()):
                if match is None or fnmatch.fnmatch(key, match):
                    yield key

        return _gen()

    async def llen(self, key: str) -> int:
        """LLEN: Celery broker lists aren't modelled; tests don't enqueue real tasks."""
        return 0

    async def aclose(self) -> None:
        return None


def _is_async_test(request: pytest.FixtureRequest) -> bool:
    """Return True if the requesting test runs on an asyncio event loop.

    We detect this by checking for any async-detectable signal: the test node
    being a coroutine function, or any async fixtures in its argnames. This
    keeps the async autouse fixtures from being activated for plain sync tests.
    """
    node = request.node
    # pytest-asyncio marks coroutine tests; their fixtures appear in argnames.
    testfunc = getattr(node, "function", None)
    if testfunc is not None and hasattr(testfunc, "__code__") and testfunc.__code__.co_flags & 0x100:  # CO_COROUTINE
        return True
    # Fall back: an asyncio marker was applied.
    if node.get_closest_marker("asyncio") is not None:
        return True
    return False


@pytest.fixture(autouse=True)
def _mock_celery(monkeypatch):
    """Stub out Celery task dispatch so tests never block on the broker.

    ``process_video.delay(...)`` (and any other task) would otherwise try to
    reach the Redis broker at ``settings.redis_url`` and hang forever in the
    test environment (no broker running). We replace ``.delay`` / ``.apply_async``
    on every registered Celery task with no-ops that record their args, so tests
    that submit videos/orders still pass but no background work runs.
    """
    from app.tasks.celery_app import celery_app

    calls: list[tuple[str, tuple, dict]] = []

    class _FakeAsyncResult:
        """Minimal stand-in for celery's AsyncResult."""

        def __init__(self, task_id: str = "fake-task-id") -> None:
            self.id = task_id
            self.state = "PENDING"

        def get(self, timeout=None):
            return None

        def ready(self) -> bool:
            return False

        def successful(self) -> bool:
            return False

    def _make_noop(task_name: str):
        def _delay(*args, **kwargs):
            calls.append((task_name, args, kwargs))
            return _FakeAsyncResult()

        def _apply_async(*args, **kwargs):
            calls.append((task_name, args, kwargs))
            return _FakeAsyncResult()

        return _delay, _apply_async

    for task_name in list(celery_app.tasks):
        # Skip Celery's own built-in tasks (celery.*)
        if task_name.startswith("celery."):
            continue
        task = celery_app.tasks[task_name]
        delay_fn, apply_fn = _make_noop(task_name)
        monkeypatch.setattr(task, "delay", delay_fn)
        monkeypatch.setattr(task, "apply_async", apply_fn)

    # ``send_task`` is the name-based dispatch path (and the seam the pipeline
    # outbox uses — the GPU task is not registered in this app, only known by
    # name). Recording it here keeps every dispatch testable without a broker.
    def _send_task(name, args=None, kwargs=None, **options):
        calls.append((name, tuple(args or ()), options))
        return _FakeAsyncResult()

    monkeypatch.setattr(celery_app, "send_task", _send_task)

    # Expose recorded calls for tests that want to assert dispatch happened.
    monkeypatch._celery_calls = calls  # type: ignore[attr-defined]
    yield calls


class _SocketShim:
    """A stand-in for the ``socket`` module with ``getaddrinfo`` replaced.

    Patching ``socket.getaddrinfo`` itself would be process-wide: every library
    that does ``import socket`` resolves through the same module object, so a
    fake resolver here would also hijack redis-py's and asyncpg's hostname
    resolution. Rebinding the *name* ``socket`` inside ``video_url_guard``
    confines the fake to the one module that wants it.
    """

    def __init__(self, real, getaddrinfo) -> None:
        self._real = real
        self.getaddrinfo = getaddrinfo

    def __getattr__(self, name):
        return getattr(self._real, name)


@pytest.fixture(autouse=True)
def _mock_dns_lookup(request: pytest.FixtureRequest, monkeypatch):
    """Stub DNS lookups for the SSRF guard so tests never hit real DNS.

    Default resolution returns a public IP (the guard's domain-allowlist
    logic stays exercised); test_video_url_guard.py overrides this per-test
    to simulate private-IP / rebinding scenarios.

    The fake is scoped to ``video_url_guard`` via ``_SocketShim`` rather than
    written onto the ``socket`` module, so it cannot leak into unrelated
    resolution — a leak here previously made the sync Redis client in
    ``pipeline_helpers`` dial the fake IP (and hang until the CI test-step
    timeout). Postgres integration tests still skip the mock so they resolve
    the Postgres hostname for real; the shim makes that belt-and-braces
    rather than a requirement.
    """
    if request.node.get_closest_marker("integration") is not None:
        return  # real DNS — asyncpg must resolve the Postgres hostname
    import app.services.video_url_guard as guard

    def fake_getaddrinfo(host, port=None, *args, **kwargs):
        return [(2, 1, 6, "", ("93.184.216.34", 0))]

    monkeypatch.setattr(guard, "socket", _SocketShim(guard.socket, fake_getaddrinfo))


@pytest.fixture
def requires_ecdict():
    """Skip a test that asserts ECDICT-derived values when the DB is absent.

    ``backend/data/ecdict.db`` is gitignored (851MB) and CI does not vendor it;
    ``ecdict`` documents that callers degrade gracefully in that case
    (``is_available()`` False, ``lookup`` None). Tests asserting computed
    glosses/levels must therefore skip rather than fail — run
    ``python scripts/download_ecdict.py`` to make them run.
    """
    from app.services import ecdict

    if not ecdict.is_available():
        pytest.skip("ecdict.db absent (run scripts/download_ecdict.py)")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Dump every thread's stack if the interpreter does not exit after the session.

    Only the Linux CI runner hangs here: the suite prints its result
    (746 passed, 0 failed) and then the process stays alive until the step's
    10-minute timeout kills it, failing the job. Aligning the runner's pytest
    dependencies with the verified local stack did not change it, so arm
    faulthandler to print where it is stuck instead of guessing further.
    Remove this once the cause is known — it is a diagnostic, not a fix.
    """
    import faulthandler

    try:
        faulthandler.dump_traceback_later(90, exit=False)
    except (AttributeError, RuntimeError, ValueError):
        pass  # not supported on this platform — nothing to diagnose locally


@pytest_asyncio.fixture
async def fake_redis(request: pytest.FixtureRequest, monkeypatch):
    """An in-memory fake Redis, injected into ``app.core.redis``.

    Request this fixture in tests that need to inspect or assert on the Redis
    store (e.g. AI cache, vocab quiz staging). It is also installed implicitly
    by ``_async_setup`` for every async test, so async tests that don't need
    direct access can ignore it.

    Late ``from app.core.redis import get_redis`` imports resolve the name at
    call time, so patching the module attribute covers every caller.
    """
    fake = _FakeRedis()

    def _get_redis():
        return fake

    monkeypatch.setattr(redis_module, "get_redis", _get_redis)
    monkeypatch.setattr(redis_module, "_redis", fake)
    redis_module._test_fake_installed = True  # type: ignore[attr-defined]
    yield fake
    redis_module._test_fake_installed = False  # type: ignore[attr-defined]


@pytest_asyncio.fixture(autouse=True)
async def _async_setup(request: pytest.FixtureRequest, monkeypatch):
    """Create tables + inject fake Redis — but only for async tests.

    Runs ``create_all``/``drop_all`` around each async test and patches
    ``app.core.redis`` with an in-memory fake so Redis-backed features (token
    blacklist, vocab quiz staging) work without a live Redis. If a test already
    requested the ``fake_redis`` fixture, that same instance is reused (the
    fixture does the patching); otherwise we install a fresh one here.

    Tests marked ``integration`` instead run against a real Postgres (see
    ``_pg_engine_or_skip``): the schema is created/dropped on Postgres and
    ``app.core.database.async_session`` is routed to the Postgres session
    maker, so Celery task bodies (which open their own sessions on the shared
    celery-asyncio loop) see the same test data the test body wrote.
    """
    if not _is_async_test(request):
        # Plain sync test (e.g. pure unit tests) — skip DB/Redis setup entirely.
        yield
        return

    # --- Database tables ---
    import app.core.database as database_module

    if request.node.get_closest_marker("integration") is not None:
        engine = await _pg_engine_or_skip()
        pg_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            # The models declare the pg_trgm GIN indexes that migration
            # ``c9d0e1f2a3b4`` installs (so the drift gate stays at zero), and
            # ``create_all`` emits them verbatim — the operator class only
            # exists once the extension does, exactly as on a migrated DB.
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
            await conn.run_sync(Base.metadata.create_all)
        monkeypatch.setattr(database_module, "async_session", pg_maker)
    else:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # --- Route `async_session` to the test session maker ---
        # app.core.database resolves `async_session` lazily to the REAL engine
        # (settings.database_url) unless it is patched here. Code that opens its
        # own sessions (media publish-state gate, Celery task bodies) must see the
        # test DB, not the configured Postgres.
        monkeypatch.setattr(database_module, "async_session", TestSessionLocal)

    # --- Fake Redis (only if the test didn't already install one) ---
    if not getattr(redis_module, "_test_fake_installed", False):
        # No fake installed yet — install one for this test.
        fake = _FakeRedis()

        def _get_redis():
            return fake

        monkeypatch.setattr(redis_module, "get_redis", _get_redis)
        monkeypatch.setattr(redis_module, "_redis", fake)
        redis_module._test_fake_installed = True  # type: ignore[attr-defined]

    yield

    redis_module._test_fake_installed = False  # type: ignore[attr-defined]
    if request.node.get_closest_marker("integration") is not None:
        # Best-effort cleanup: when a test fails, pytest-asyncio closes the
        # event loop before running async fixture teardown, so drop_all may
        # not be able to connect — don't mask the real failure with a
        # secondary teardown ERROR.
        engine = _pg_engine
        if engine is not None:
            try:
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.drop_all)
            except Exception:  # cleanup is best-effort
                pass
    else:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client with test database + fake redis overrides."""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Raw database session for direct model manipulation."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def test_password() -> str:
    return "Testpass123!"


@pytest.fixture
def test_user_data() -> dict:
    return {
        "phone": "13800138000",
        "password": "Testpass123!",
        "name": "Test User",
    }


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user_data: dict, test_password: str) -> dict:
    """Create a test user, return Authorization headers with JWT."""
    from app.models.user import RoleType, User

    async with TestSessionLocal() as db:
        user = User(
            phone=test_user_data["phone"],
            hashed_password=hash_password(test_password),
            name=test_user_data["name"],
            role=RoleType.user,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        token = create_token(user.id)
        return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict:
    """Create an admin user, return Authorization headers."""
    from app.models.user import RoleType, User

    async with TestSessionLocal() as db:
        user = User(
            phone="13900139000",
            hashed_password=hash_password("Adminpass1!"),
            name="Admin",
            role=RoleType.admin,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        token = create_token(user.id)
        return {"Authorization": f"Bearer {token}"}
