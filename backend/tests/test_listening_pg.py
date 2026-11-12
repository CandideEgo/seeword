"""Real row-lock evidence for listening drafts, submission and restarts."""

import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import event, func, select

from app.core.database import get_async_session_maker
from app.models.learning_plan import LearningEvent
from app.models.listening import ListeningSession
from app.models.user import User
from app.services import listening_service
from tests.test_listening_api import seed as seed_video

pytestmark = pytest.mark.integration


async def _snapshot_lock_waits() -> list[str]:
    """Every ungranted lock request plus who holds the blocker.

    Taken *during* the race, not after it: by the time DeadlockDetectedError
    reaches us Postgres has already aborted one side, so a post-mortem snapshot
    shows no waits at all (verified on CI).
    """
    from sqlalchemy import text

    async with get_async_session_maker()() as db:
        if db.get_bind().dialect.name != "postgresql":
            return []
        rows = (
            await db.execute(
                text(
                    """
                    SELECT w.pid AS waiter, w.mode AS want, w.relation::regclass::text AS rel,
                           b.pid AS blocker, b.mode AS held
                    FROM pg_locks w
                    JOIN pg_locks b
                      ON b.locktype = w.locktype
                     AND b.database IS NOT DISTINCT FROM w.database
                     AND b.relation IS NOT DISTINCT FROM w.relation
                     AND b.page IS NOT DISTINCT FROM w.page
                     AND b.tuple IS NOT DISTINCT FROM w.tuple
                     AND b.virtualxid IS NOT DISTINCT FROM w.virtualxid
                     AND b.transactionid IS NOT DISTINCT FROM w.transactionid
                     AND b.classid IS NOT DISTINCT FROM w.classid
                     AND b.objid IS NOT DISTINCT FROM w.objid
                     AND b.objsubid IS NOT DISTINCT FROM w.objsubid
                     AND b.pid <> w.pid
                    WHERE NOT w.granted AND b.granted
                    """
                )
            )
        ).all()
    return [
        f"pid {waiter} wants {want} on {rel} <- pid {blocker} holds {held}" for waiter, want, rel, blocker, held in rows
    ]


async def _watch_lock_waits(sink: list[str], stop: asyncio.Event, interval: float = 0.01) -> None:
    """Poll pg_locks until ``stop`` is set, keeping the last non-empty snapshot.

    Best-effort throughout: a diagnostics failure must never change the test's
    own outcome.
    """
    while not stop.is_set():
        try:
            waits = await _snapshot_lock_waits()
        except Exception:  # pragma: no cover - pool may be busy while the race runs
            waits = []
        if waits:
            sink[:] = waits
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except TimeoutError:
            continue


async def seed(*, start=True):
    async with get_async_session_maker()() as db:
        user = User(phone="13800009854", name="Listening race")
        db.add(user)
        await db.commit()
        video = await seed_video(db)
        if not start:
            return user.id, video.id, None, {}
        session = await listening_service.start(db, user, video.id, 5, False)
        await db.commit()
        return user.id, video.id, session.id, {q["id"]: q["text_en"] for q in session.questions}


async def race(sid, action):
    barrier = asyncio.Barrier(2)

    async def run(index):
        async with get_async_session_maker()() as db:
            # Keep the old identity-map object alive across the competing write.
            stale = await db.get(ListeningSession, sid)
            assert stale.submitted_at is None
            await barrier.wait()
            result = await action(db, index)
            await db.commit()
            return result

    return await asyncio.wait_for(asyncio.gather(run(0), run(1)), timeout=20)


async def test_two_stale_submissions_grade_once_and_replay_identical_results():
    uid, _vid, sid, answers = await seed()
    async with get_async_session_maker()() as db:
        await listening_service.save(db, sid, uid, answers, 0)
        await db.commit()

    async def submit(db, index):
        row = await listening_service.submit(db, sid, uid)
        return row.results, row.submitted_at

    first, second = await race(sid, submit)
    assert first == second
    async with get_async_session_maker()() as db:
        row = await db.get(ListeningSession, sid)
        assert row.correct_count == len(answers)
        assert await db.scalar(select(func.count(LearningEvent.id))) == 1


async def test_disjoint_concurrent_drafts_merge_without_lost_answers():
    uid, _vid, sid, answers = await seed()
    parts = list(answers.items())

    async def save(db, index):
        key, value = parts[index]
        await listening_service.save(db, sid, uid, {key: value}, index)

    await race(sid, save)
    async with get_async_session_maker()() as db:
        row = await db.get(ListeningSession, sid)
        assert row.answers == answers and row.submitted_at is None
        assert await db.scalar(select(func.count(LearningEvent.id))) == 0


@pytest.mark.parametrize("save_first", [True, False])
async def test_draft_and_submission_obey_the_same_locked_state_transition(save_first):
    uid, _vid, sid, answers = await seed()
    locked = asyncio.Event()
    follower_ready = asyncio.Event()

    async def first():
        async with get_async_session_maker()() as db:
            await listening_service.owned_session(db, sid, uid, lock=True)
            locked.set()
            await asyncio.wait_for(follower_ready.wait(), timeout=5)
            if save_first:
                await listening_service.save(db, sid, uid, answers, 0)
            else:
                await listening_service.submit(db, sid, uid)
            await db.commit()

    async def second():
        await asyncio.wait_for(locked.wait(), timeout=5)
        async with get_async_session_maker()() as db:
            stale = await db.get(ListeningSession, sid)
            assert stale.submitted_at is None
            follower_ready.set()
            if save_first:
                await listening_service.submit(db, sid, uid)
                await db.commit()
            else:
                with pytest.raises(HTTPException) as caught:
                    await listening_service.save(db, sid, uid, answers, 0)
                assert caught.value.status_code == 409
                await db.rollback()

    await asyncio.wait_for(asyncio.gather(first(), second()), timeout=20)
    async with get_async_session_maker()() as db:
        row = await db.get(ListeningSession, sid)
        assert row.submitted_at is not None
        assert row.answers == (answers if save_first else {})
        assert row.correct_count == (len(answers) if save_first else 0)
        assert await db.scalar(select(func.count(LearningEvent.id))) == 1


@pytest.mark.parametrize("restart", [True, False])
async def test_start_waiting_for_submit_does_not_deadlock_or_delete_submitted_history(restart):
    uid, vid, sid, _answers = await seed()
    maker = get_async_session_maker()
    engine = maker.kw["bind"].sync_engine
    session_locked, account_locked = asyncio.Event(), asyncio.Event()

    def observe_account_lock(conn, cursor, statement, parameters, context, executemany):
        if "FROM users" in statement and ("FOR UPDATE" in statement or "FOR NO KEY UPDATE" in statement):
            account_locked.set()

    async def submit():
        async with maker() as db:
            await listening_service.owned_session(db, sid, uid, lock=True)
            session_locked.set()
            # start now holds its account lock and is about to wait for this
            # attempt. A learning-event FK must remain able to take KEY SHARE.
            await asyncio.wait_for(account_locked.wait(), timeout=5)
            await listening_service.submit(db, sid, uid)
            await db.commit()

    async def start():
        await asyncio.wait_for(session_locked.wait(), timeout=5)
        async with maker() as db:
            user = await db.get(User, uid)
            row = await listening_service.start(db, user, vid, 5, restart)
            await db.commit()
            return row.id

    event.listen(engine, "after_cursor_execute", observe_account_lock)
    observed_waits: list[str] = []
    watcher_stop = asyncio.Event()
    watcher = asyncio.create_task(_watch_lock_waits(observed_waits, watcher_stop))
    try:
        _, new_id = await asyncio.wait_for(asyncio.gather(submit(), start()), timeout=20)
    except Exception:
        # CI reproduces this deadlock on every run while a local Postgres does
        # not. Postgres' deadlock DETAIL names the two statements but not the
        # lock modes, and log_lock_waits stays silent (the victim is picked at
        # deadlock_timeout). The waits only exist while the race is in flight,
        # so they are sampled above and reported here.
        waits = "\n  ".join(observed_waits or ["(none observed)"])
        print(f"\n[pg_locks] start/submit race, last non-empty snapshot:\n  {waits}")
        raise
    finally:
        watcher_stop.set()
        watcher.cancel()
        event.remove(engine, "after_cursor_execute", observe_account_lock)
    assert new_id != sid
    async with maker() as db:
        old = await db.get(ListeningSession, sid)
        assert old is not None and old.submitted_at is not None
        new = await db.get(ListeningSession, new_id)
        assert new.submitted_at is None
        assert await db.scalar(select(func.count(ListeningSession.id))) == 2
        assert await db.scalar(select(func.count(LearningEvent.id))) == 1


async def test_two_starts_share_one_pending_session():
    uid, vid, _sid, _answers = await seed(start=False)
    barrier = asyncio.Barrier(2)

    async def start():
        async with get_async_session_maker()() as db:
            user = await db.get(User, uid)
            await barrier.wait()
            row = await listening_service.start(db, user, vid, 5, False)
            await db.commit()
            return row.id

    first, second = await asyncio.wait_for(asyncio.gather(start(), start()), timeout=20)
    assert first == second
    async with get_async_session_maker()() as db:
        assert await db.scalar(select(func.count(ListeningSession.id))) == 1
