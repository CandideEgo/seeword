"""Postgres integration tests for the note-write races (H3).

The default suite runs on in-memory SQLite, where ``with_for_update`` is
silently ignored (see ``tests/conftest.py``), so it cannot express whether two
concurrent note writes serialize. Against a real Postgres, two parallel PUTs
from the same user previously both saw "no note", both INSERTed, and the second
one failed with the uncaught ``IntegrityError`` from
``uq_user_note_user_video`` — a 500 that also threw the note away. Two parallel
DELETEs both loaded the same row, so the loser's DELETE matched zero rows
(SQLAlchemy's rowcount check flags it; a versioned mapper would raise
``StaleDataError``). And a DELETE racing a PUT used to break the PUT: its
UPDATE matched the row the DELETE had just removed —
``StaleDataError: UPDATE statement on table 'user_notes' expected to update
1 row(s); 0 were matched`` — the 500 that put the video row lock in
``delete_note``.

Marked ``integration`` (see pytest.ini). Locally:

    PG_TEST_URL=postgresql+asyncpg://seeword:seeword_dev@localhost:5432/<clean-db> \\
        pytest tests/test_favorites_pg.py -v

The target database must be a dedicated/clean one: the integration branch of
conftest drops and recreates every table. CI's backend job points
``DATABASE_URL`` at its Postgres service, so these run there too; without a
reachable Postgres they skip loudly.
"""

import asyncio
import uuid
import warnings
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session_maker, get_db
from app.core.security import create_token
from app.main import create_app
from app.models.favorite import UserNote
from app.models.user import RoleType, User
from app.models.video import Video, VideoStatus

pytestmark = pytest.mark.integration

# How long the writers are paced apart, in seconds, to hold the read→write
# window open (see ``_hold_note_write_window_open``).
RACE_WINDOW_S = 0.3
RACE_HEADSTART_S = 0.05


async def _seed_user_and_video() -> tuple[dict, str]:
    """Insert a user + ready video on Postgres; return (auth headers, video id)."""
    async with get_async_session_maker()() as db:
        user = User(
            phone="13611136001",
            hashed_password="hashed",
            name="Note Race",
            role=RoleType.user,
        )
        video = Video(
            id=str(uuid.uuid4()),
            title="Note Race Video",
            source_url="https://example.com/note-race.mp4",
            status=VideoStatus.ready,
        )
        db.add_all([user, video])
        await db.commit()
        return {"Authorization": f"Bearer {create_token(user.id)}"}, video.id


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
    # raise_app_exceptions=False: an uncaught IntegrityError must surface as the
    # 500 the user sees, not as a re-raised exception in the test.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_concurrent_note_upserts_both_succeed(pg_client: AsyncClient):
    headers, video_id = await _seed_user_and_video()
    url = f"/api/v1/videos/{video_id}/note"

    first, second = await asyncio.gather(
        pg_client.put(url, headers=headers, json={"content": "first writer"}),
        pg_client.put(url, headers=headers, json={"content": "second writer"}),
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == {"content": "first writer"}
    assert second.json() == {"content": "second writer"}

    # Exactly one row survives the race, holding one of the two payloads.
    async with get_async_session_maker()() as db:
        contents = (await db.execute(select(UserNote.content).where(UserNote.video_id == video_id))).scalars().all()
    assert contents in (["first writer"], ["second writer"])


async def test_concurrent_note_deletes_both_succeed(pg_client: AsyncClient):
    headers, video_id = await _seed_user_and_video()
    url = f"/api/v1/videos/{video_id}/note"
    assert (await pg_client.put(url, headers=headers, json={"content": "to be deleted"})).status_code == 200

    # A zero-row DELETE is the fingerprint of the unlocked race: both requests
    # loaded the same note row, so the slower one deletes a row that is already
    # gone. SQLAlchemy reports that as this warning (and raises StaleDataError
    # for a versioned mapper), so surface it as a failure instead of letting it
    # pass as background noise.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        first, second = await asyncio.gather(
            pg_client.delete(url, headers=headers),
            pg_client.delete(url, headers=headers),
        )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == {"content": ""}
    assert second.json() == {"content": ""}
    zero_row_deletes = [str(w.message) for w in caught if "user_notes" in str(w.message)]
    assert zero_row_deletes == [], zero_row_deletes

    async with get_async_session_maker()() as db:
        remaining = (await db.execute(select(UserNote).where(UserNote.video_id == video_id))).scalars().all()
    assert remaining == []

    # Replaying the idempotent delete after the row is gone stays a 200.
    replay = await pg_client.delete(url, headers=headers)
    assert replay.status_code == 200, replay.text
    assert replay.json() == {"content": ""}


def _hold_note_write_window_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pace both writers so the PUT/DELETE race interleaves every time.

    Both endpoints touch the row in back-to-back round trips, so on this stack
    the race normally resolves before either writer can interfere: measured
    against the unlocked code, 25/25 rounds ended with the DELETE committing
    before the PUT's read and the PUT re-inserting the note — no 500, nothing
    for the test to catch. This pins the interleaving that used to break
    ``upsert_note``: the DELETE commits inside the window between the PUT's
    read of the note and the flush of its UPDATE. The DELETE gets a small head
    start so it cannot finish before the PUT has read; the PUT's flush is
    paused for longer so the DELETE is guaranteed to land in that window.
    """
    original_commit, original_delete = AsyncSession.commit, AsyncSession.delete

    async def _paused_commit(self: AsyncSession) -> None:
        # ``Session.dirty`` holds modified rows only — never deleted ones — so
        # this pauses the PUT's flush and leaves the DELETE's commit alone.
        if any(isinstance(obj, UserNote) for obj in self.dirty):
            await asyncio.sleep(RACE_WINDOW_S)
        await original_commit(self)

    async def _delayed_delete(self: AsyncSession, instance: object) -> None:
        if isinstance(instance, UserNote):
            await asyncio.sleep(RACE_HEADSTART_S)
        await original_delete(self, instance)

    monkeypatch.setattr(AsyncSession, "commit", _paused_commit)
    monkeypatch.setattr(AsyncSession, "delete", _delayed_delete)


async def _note_contents(video_id: str) -> list[str]:
    async with get_async_session_maker()() as db:
        return (await db.execute(select(UserNote.content).where(UserNote.video_id == video_id))).scalars().all()


async def test_concurrent_note_put_and_delete_never_fails(pg_client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    """A PUT racing a DELETE: neither 500s, and one consistent state survives.

    The PUT used to lose this race with ``StaleDataError`` (its UPDATE matched
    the row the DELETE had already removed); the DELETE used to win it by
    wiping a note the PUT had just written.
    """
    headers, video_id = await _seed_user_and_video()
    url = f"/api/v1/videos/{video_id}/note"
    assert (await pg_client.put(url, headers=headers, json={"content": "initial"})).status_code == 200

    _hold_note_write_window_open(monkeypatch)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        put_resp, delete_resp = await asyncio.gather(
            pg_client.put(url, headers=headers, json={"content": "typed by the user"}),
            pg_client.delete(url, headers=headers),
        )

    assert put_resp.status_code == 200, put_resp.text
    assert delete_resp.status_code == 200, delete_resp.text
    assert delete_resp.json() == {"content": ""}
    assert [str(w.message) for w in caught if "user_notes" in str(w.message)] == []
    # Serialized on the video row lock, so one writer ran last: the PUT's
    # payload survived, or the note is gone. Anything else is a lost write
    # (payload written, then still a stale row) or a half-applied pair.
    assert await _note_contents(video_id) in ([], ["typed by the user"])


async def test_concurrent_note_delete_and_put_never_fails(pg_client: AsyncClient):
    """The same pair with the DELETE issued first (the other interleaving)."""
    headers, video_id = await _seed_user_and_video()
    url = f"/api/v1/videos/{video_id}/note"
    assert (await pg_client.put(url, headers=headers, json={"content": "initial"})).status_code == 200

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        delete_resp, put_resp = await asyncio.gather(
            pg_client.delete(url, headers=headers),
            pg_client.put(url, headers=headers, json={"content": "typed by the user"}),
        )

    assert put_resp.status_code == 200, put_resp.text
    assert delete_resp.status_code == 200, delete_resp.text
    assert delete_resp.json() == {"content": ""}
    assert [str(w.message) for w in caught if "user_notes" in str(w.message)] == []
    assert await _note_contents(video_id) in ([], ["typed by the user"])
