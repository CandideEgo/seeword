"""Real row-lock evidence for listening drafts, submission and restarts."""

import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

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

    Also dumps *every* lock held by the blocked pids and by their blockers. The
    transactionid-level edge alone is ambiguous: it says "waits for that
    transaction", not which row lock formed the cycle, and the two sides may be
    waiting on different lock types entirely.
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
        lines = [f"pid {w} wants {want} on {rel} <- pid {b} holds {held}" for w, want, rel, b, held in rows]
        if not lines:
            return []
        pids = sorted({row[0] for row in rows} | {row[3] for row in rows})
        held_rows = (
            await db.execute(
                text(
                    """
                    SELECT l.pid, a.state, a.wait_event_type, a.wait_event,
                           l.locktype, l.mode, l.granted,
                           l.relation::regclass::text AS rel, l.transactionid,
                           left(a.query, 110) AS q
                    FROM pg_locks l
                    JOIN pg_stat_activity a ON a.pid = l.pid
                    WHERE l.pid = ANY(:pids)
                    ORDER BY l.pid, l.granted DESC, l.mode
                    """
                ),
                {"pids": pids},
            )
        ).all()
    lines.append("  held locks:")
    lines.extend(
        f"    pid {pid} state={state} wait={wet or '-'}/{we or '-'} {ltype} {mode} "
        f"granted={granted} rel={rel} xid={xid} :: {q}"
        for pid, state, wet, we, ltype, mode, granted, rel, xid, q in held_rows
    )
    return lines


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
    """A start that lands after a submit must not delete the submitted history.

    Both bodies call the service functions exactly the way the API endpoints
    do — no pre-held row lock, and no artificial barrier. An earlier version
    hand-locked the session row before calling ``submit()``; that interleaving
    is stricter than any request can produce and deadlocks *by construction*
    once both paths take the account lock first (the test's own lock holds the
    session row, so submit waits for the account while start holds the account
    and waits for session). The lock order the fix establishes — account first,
    session second — is what removes that cycle; this test pins the ordering
    that the history assertion actually needs.
    """
    uid, vid, sid, _answers = await seed()
    maker = get_async_session_maker()
    # Submit commits first, then start runs against the already-submitted row.
    # The order is pinned on purpose: with a bare racing barrier the outcome is
    # not a race at all but a coin flip between "submit won, start sees nothing
    # to delete" and "start won, deletes the pending row submit is about to
    # commit" — and only the first one is the production case this guards.
    # Neither side pre-takes a row lock here (an earlier version did, which
    # deadlocks by construction once both paths take the account lock first).
    submitted = asyncio.Event()

    async def submit():
        async with maker() as db:
            await listening_service.submit(db, sid, uid)
            await db.commit()
        submitted.set()

    async def start():
        await asyncio.wait_for(submitted.wait(), timeout=10)
        async with maker() as db:
            user = await db.get(User, uid)
            row = await listening_service.start(db, user, vid, 5, restart)
            await db.commit()
            return row.id

    observed_waits: list[str] = []
    watcher_stop = asyncio.Event()
    watcher = asyncio.create_task(_watch_lock_waits(observed_waits, watcher_stop))
    try:
        _, new_id = await asyncio.wait_for(asyncio.gather(submit(), start()), timeout=20)
    except Exception:
        # Postgres' deadlock DETAIL names the two statements but not the lock
        # modes, and log_lock_waits stays silent (the victim is picked at
        # deadlock_timeout). The waits only exist while the race is in flight,
        # so they are sampled above and reported here.
        waits = "\n  ".join(observed_waits or ["(none observed)"])
        print(f"\n[pg_locks] start/submit race, last non-empty snapshot:\n  {waits}")
        raise
    finally:
        watcher_stop.set()
        watcher.cancel()
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


async def test_concurrent_submit_and_start_do_not_deadlock():
    """The two paths must queue on the account lock, not cycle.

    This is the case that used to raise ``DeadlockDetectedError`` in CI: submit
    reaches the account row through the ``learning_events`` foreign key while
    start takes it explicitly, so with the two paths acquiring the session row
    and the account row in opposite orders they closed a wait cycle (see the
    pg_locks dump in ``docs/slcs/start-here.md`` §5). Both paths now take the
    account lock first.

    ``restart=False`` on purpose: with ``restart=True`` the outcome genuinely
    depends on which transaction commits first (start deletes the pending row
    it finds), so that variant cannot assert a single result. Here the only
    claim is that the overlap completes, both ways round.
    """
    uid, vid, sid, answers = await seed()
    async with get_async_session_maker()() as db:
        await listening_service.save(db, sid, uid, answers, 0)
        await db.commit()

    barrier = asyncio.Barrier(2)

    async def submit():
        async with get_async_session_maker()() as db:
            await barrier.wait()
            await listening_service.submit(db, sid, uid)
            await db.commit()

    async def start():
        async with get_async_session_maker()() as db:
            user = await db.get(User, uid)
            await barrier.wait()
            await listening_service.start(db, user, vid, 5, False)
            await db.commit()

    # A DeadlockDetectedError propagates out of gather and fails the test.
    await asyncio.wait_for(asyncio.gather(submit(), start()), timeout=20)
    async with get_async_session_maker()() as db:
        row = await db.get(ListeningSession, sid)
        assert row is not None and row.submitted_at is not None
        assert await db.scalar(select(func.count(LearningEvent.id))) == 1
