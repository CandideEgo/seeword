"""Default-off deployments must not depend on the V2 tables existing."""

from types import SimpleNamespace

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.errors import AppError
from app.models.user import User
from app.services import account_data, v2_access
from app.services.v2_schema import V2_TABLES, schema_ready
from app.tasks import account_tasks, teaching_tasks


async def _bare_engine():
    """A database that has only the tables a default-off deployment needs."""
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as connection:
        await connection.run_sync(lambda sync: User.__table__.create(sync))
    return engine


async def test_schema_ready_detects_absent_and_present_v2_tables(db_session):
    assert await schema_ready(db_session) is True

    engine = await _bare_engine()
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        assert await schema_ready(db) is False
    await engine.dispose()


async def test_closed_feature_is_503_without_reading_the_grant_table(db_session, monkeypatch):
    # The bare database has no teaching_access_grants: a flag check that ran
    # after the grant lookup would raise OperationalError instead of 503.
    engine = await _bare_engine()
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as db:
        db.add(User(phone="13900000001", hashed_password="x"))
        await db.commit()
        user = (await db.execute(__import__("sqlalchemy").select(User))).scalar_one()
        monkeypatch.setattr(
            v2_access,
            "get_settings",
            lambda: SimpleNamespace(teaching_allowed_user_ids="", teaching_runs_enabled=False),
        )
        with pytest.raises(AppError) as exc:
            await v2_access.require_access(db, user.id, "teaching_runs_enabled")
        assert exc.value.status_code == 503
    await engine.dispose()


async def test_sweep_is_a_noop_without_the_v2_schema(monkeypatch):
    calls = []
    monkeypatch.setattr("app.services.v2_schema.has_tables", _never_ready)
    monkeypatch.setattr(teaching_tasks, "get_async_session_maker", _maker)
    result = await teaching_tasks._sweep()
    assert result == {"queued": 0, "skipped": "v2_schema_absent"}
    assert calls == []


async def test_export_omits_teaching_sections_without_the_v2_schema(monkeypatch):
    monkeypatch.setattr("app.services.v2_schema.has_tables", _never_ready)
    assert await account_data._gather_teaching_data(object(), "user-1") == {}


async def test_account_cleanup_is_a_noop_without_the_v2_schema(monkeypatch):
    monkeypatch.setattr("app.services.v2_schema.existing_tables", _no_tables)
    await account_tasks._prepare_v2_removal(object(), "user-1")
    await account_tasks._delete_v2_children(object(), "user-1")


async def _no_tables(_db):
    return frozenset()


async def _never_ready(_db, _names):
    return False


def _maker():
    return _EmptySessionFactory()


class _EmptySessionFactory:
    def __call__(self):
        return _EmptySession()


class _EmptySession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False


def test_v2_table_list_matches_every_v2_model():
    """A new V2 model must not be forgotten by the readiness check."""
    import app.models.content_publication as publication
    import app.models.question_exposure as exposure
    import app.models.teaching as teaching
    import app.models.v2_runtime as runtime

    names = set()
    for module in (teaching, runtime, publication, exposure):
        for value in vars(module).values():
            table = getattr(value, "__table__", None)
            if table is not None and getattr(value, "__module__", "") == module.__name__:
                names.add(table.name)
    assert names == set(V2_TABLES)
