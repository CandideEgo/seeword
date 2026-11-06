"""Postgres integration tests for the concurrent-promote races (catalog).

The default suite runs on in-memory SQLite, where ``with_for_update`` is
silently ignored (see ``tests/conftest.py``), so it cannot express whether two
concurrent promotes of the same catalog item serialize. Against a real
Postgres, two parallel POSTs used to both read the item before either had
written ``promoted_video_id``, both called ``seed_video``, and the URL ended up
with two ``Video`` rows and two GPU runs.

Two ``seed_video`` stubs, because the concurrency has two regimes:

* :func:`test_concurrent_promote_seeds_once_and_creates_one_video` uses a stub
  that does **not** write through the request's session. That isolates the row
  lock: the loser's ``SELECT ... FOR UPDATE`` blocks until the winner commits,
  then re-reads the row (READ COMMITTED re-evaluation) and reuses the winner's
  video. Drop ``with_for_update()`` from ``catalog_service.get_item`` and it
  fails with two awaited seeds.
* :func:`test_concurrent_first_promote_seeds_once_with_committing_seed` uses a
  stub shaped like the real ``seed_video``: it inserts a ``Video`` and commits.
  That commit releases the item row lock at the very moment its video becomes
  visible to other transactions, so for a *first-ever* promote the lock alone
  cannot help — the loser reads ``promoted_video_id IS NULL``. What closes that
  window is ``promote_item``'s URL-scoped reuse lookup, which finds the
  freshly committed official video for the item's ``source_url``. This test is
  the regression guard for that lookup.

Marked ``integration`` (see pytest.ini). Locally:

    PG_TEST_URL=postgresql+asyncpg://seeword:seeword_dev@localhost:5432/speaking_test \\
        pytest tests/test_catalog_pg.py -v

The target database must be a dedicated/clean one: the integration branch of
conftest drops and recreates every table. CI's backend job points
``DATABASE_URL`` at its Postgres service, so these run there too; without a
reachable Postgres they skip loudly.
"""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_async_session_maker, get_db
from app.core.security import create_token
from app.main import create_app
from app.models.catalog import CatalogItem, CatalogStatus
from app.models.user import RoleType, User
from app.models.video import Video, VideoSource, VideoStatus

pytestmark = pytest.mark.integration


async def _seed_admin_and_item() -> tuple[dict, str, str]:
    """Insert an admin user + one catalog item; return (headers, item id, url)."""
    source_url = f"https://www.youtube.com/watch?v={uuid.uuid4().hex[:11]}"
    async with get_async_session_maker()() as db:
        admin = User(
            phone="13611136002",
            hashed_password="hashed",
            name="Catalog Race",
            role=RoleType.admin,
        )
        item = CatalogItem(
            source="languagereactor",
            upstream_id=f"yt_{uuid.uuid4().hex[:10]}",
            source_url=source_url,
            title="Promote Race Candidate",
            status=CatalogStatus.new.value,
        )
        db.add_all([admin, item])
        await db.commit()
        return {"Authorization": f"Bearer {create_token(admin.id)}"}, item.id, source_url


async def _seed_promoted_video(source_url: str) -> Video:
    """The ``Video`` row a (stubbed) seed hands back, pre-created and committed.

    Pre-created rather than inserted by the stub because an uncommitted INSERT
    is only flushed when ``promote_item`` writes ``promoted_video_id``, and
    SQLAlchemy's flush puts the ``catalog_items`` UPDATE ahead of the ``videos``
    INSERT — the ``catalog_items_promoted_video_id_fkey`` check then fails.
    """
    async with get_async_session_maker()() as db:
        video = Video(
            id=str(uuid.uuid4()),
            title="Processing...",
            source_url=source_url,
            video_source=VideoSource.imported,
            status=VideoStatus.processing,
            is_official=True,
            is_published=False,
        )
        db.add(video)
        await db.commit()
        return video


@pytest_asyncio.fixture
async def pg_client() -> AsyncGenerator[AsyncClient, None]:
    """App client whose request sessions read/write the Postgres test DB.

    conftest's ``client`` fixture is bound to the SQLite engine; the row lock
    under test only exists on Postgres, so this test needs the app routes wired
    to the Postgres session maker (resolved per request, after conftest's
    ``_async_setup`` monkeypatches ``async_session``).
    """

    async def _override_get_db():
        async with get_async_session_maker()() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    # raise_app_exceptions=False: an uncaught DB error must surface as the 500
    # the user sees, not as a re-raised exception in the test.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_concurrent_promote_seeds_once_and_creates_one_video(pg_client: AsyncClient):
    """The item row lock alone serializes two promotes of the same item.

    The stub's video deliberately lives on a *different* ``source_url`` than the
    item, so the URL-scoped reuse lookup cannot rescue the loser: only the
    recorded ``promoted_video_id`` can, and reading it under the lock is what a
    blocked request does. Drop ``with_for_update()`` from
    ``catalog_service.get_item`` and this fails with two awaited seeds.

    See :func:`test_concurrent_first_promote_seeds_once_with_committing_seed`
    for the complementary case — a stub shaped like the real ``seed_video``
    (same URL, commits mid-flight), where the URL-scoped lookup is what saves
    the loser.
    """
    headers, item_id, source_url = await _seed_admin_and_item()
    # A URL the item's own lookup can never match, so only the lock counts.
    stub_url = f"https://www.youtube.com/watch?v={uuid.uuid4().hex[:11]}"
    video = await _seed_promoted_video(stub_url)

    # seed_video is imported inside promote_item, so patching the module
    # attribute covers the call site.
    with patch(
        "app.services.video_seed_service.seed_video",
        new=AsyncMock(return_value=SimpleNamespace(id=video.id, is_published=False)),
    ) as mock_seed:
        first, second = await asyncio.gather(
            pg_client.post(f"/api/v1/admin/catalog/{item_id}/promote", headers=headers, json={}),
            pg_client.post(f"/api/v1/admin/catalog/{item_id}/promote", headers=headers, json={}),
        )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    # The loser blocks on the winner's row lock, then observes its
    # promoted_video_id and reuses that video instead of seeding again.
    assert mock_seed.await_count == 1

    async with get_async_session_maker()() as db:
        videos = (await db.execute(select(Video).where(Video.source_url == stub_url))).scalars().all()
        item_url_rows = (await db.execute(select(Video).where(Video.source_url == source_url))).scalars().all()
    assert len(videos) == 1
    assert item_url_rows == []
    assert source_url != stub_url

    # The item records that single video; both responses agree on it.
    assert first.json()["promoted_video_id"] == video.id
    assert second.json()["promoted_video_id"] == video.id
    assert first.json()["status"] == CatalogStatus.processing.value
    assert second.json()["status"] == CatalogStatus.processing.value


async def test_concurrent_first_promote_seeds_once_with_committing_seed(pg_client: AsyncClient):
    """Two concurrent first promotes of a brand-new item must seed only once.

    The stub is shaped like the real ``seed_video``: it inserts a ``Video`` and
    commits on the request's own session. That commit releases the item row lock
    at the same instant the new video becomes visible, so the loser can (and
    here does) read ``promoted_video_id IS NULL`` and pass the recorded-video
    check. The URL-scoped reuse lookup is what saves it: the loser finds the
    winner's just-committed official video for the same ``source_url``.
    """
    headers, item_id, source_url = await _seed_admin_and_item()

    async def _fake_seed_video(db, url: str, auto_publish: bool = False):
        video = Video(
            id=str(uuid.uuid4()),
            title="Processing...",
            source_url=url,
            video_source=VideoSource.imported,
            status=VideoStatus.processing,
            is_official=True,
            is_published=False,
        )
        db.add(video)
        await db.commit()
        return SimpleNamespace(id=video.id, is_published=False)

    with patch(
        "app.services.video_seed_service.seed_video",
        new=AsyncMock(side_effect=_fake_seed_video),
    ) as mock_seed:
        first, second = await asyncio.gather(
            pg_client.post(f"/api/v1/admin/catalog/{item_id}/promote", headers=headers, json={}),
            pg_client.post(f"/api/v1/admin/catalog/{item_id}/promote", headers=headers, json={}),
        )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert mock_seed.await_count == 1

    async with get_async_session_maker()() as db:
        videos = (await db.execute(select(Video).where(Video.source_url == source_url))).scalars().all()
    assert len(videos) == 1

    # Both responses point at the single seeded video: the loser adopted it.
    assert first.json()["promoted_video_id"] == videos[0].id
    assert second.json()["promoted_video_id"] == videos[0].id
