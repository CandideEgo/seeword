"""Postgres integration tests for exam submission atomicity (A06 / BE-03).

The default suite runs on in-memory SQLite, where every request in a test shares
one database file and the interleavings that broke submission cannot be staged.
The defect was a read-then-write on ``exam_sessions.submitted_at``: two requests
each loaded the attempt while it was still unsubmitted, both graded, and a
three-question paper ended up with six answer rows plus two ``practiced_items``
LearningEvents.

The fix makes the write decide: ``exam_service._claim_submit`` runs a conditional
``UPDATE … WHERE submitted_at IS NULL``, and the losing request replays the
winner's settled result. On PostgreSQL the loser blocks on the row lock until
the winner commits and then re-evaluates the predicate against the committed row,
which is what these tests exercise — SQLite would serialise the whole thing and
prove nothing about the lock.

Locally (needs a dedicated, throwaway database — the fixture drops every table):

    PG_TEST_URL=postgresql+asyncpg://seeword:seeword_dev@localhost:5432/<clean-db> \\
        pytest tests/test_exams_pg.py -v

CI's backend job points ``DATABASE_URL`` at its Postgres service, so these run
there too; without a reachable Postgres they skip loudly.
"""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, update

from app.core.database import get_async_session_maker, get_db
from app.core.security import create_token
from app.main import create_app
from app.models.exam_test import ExamAnswer, ExamPaper, ExamQuestion, ExamSession
from app.models.learning_plan import LearningEvent
from app.models.user import RoleType, User
from app.services import exam_service

pytestmark = pytest.mark.integration

# Seconds the winner's grading commit is held open (see
# ``_hold_grading_commit_open``): long enough for the loser to reach its claim.
RACE_WINDOW_S = 0.4


async def _seed() -> tuple[str, dict, list[dict], str]:
    """Insert a user + a 3-question paper; return (user_id, headers, answers, paper_id)."""
    async with get_async_session_maker()() as db:
        user = User(
            phone="13611136201",
            hashed_password="hashed",
            name="Exam Race",
            role=RoleType.user,
        )
        paper = ExamPaper(
            level="cet4",
            year=2024,
            month=6,
            set_no=1,
            title="2024年6月真题（第1套）",
            source="test",
            total_questions=3,
        )
        db.add_all([user, paper])
        await db.flush()
        specs = [
            (26, "reading_A", "cloze", "B"),
            (27, "reading_C", "reading", "A"),
            (28, "reading_C", "reading", "C"),
        ]
        answers: list[dict] = []
        for number, section, qtype, answer in specs:
            question = ExamQuestion(
                paper_id=paper.id,
                section=section,
                number=number,
                question_type=qtype,
                passage="Passage.",
                question=f"Question {number}.",
                options={"A": "alpha", "B": "beta", "C": "gamma"},
                answer=answer,
            )
            db.add(question)
            await db.flush()
            answers.append({"question_id": question.id, "answer": answer})
        await db.commit()
        return user.id, {"Authorization": f"Bearer {create_token(user.id)}"}, answers, paper.id


async def _create_attempt(user_id: str, paper_id: str) -> str:
    async with get_async_session_maker()() as db:
        paper = await exam_service.get_paper_with_questions(db, paper_id)
        assert paper is not None
        attempt = await exam_service.create_paper_session(db, user_id, paper)
        await db.commit()
        return attempt.id


async def _stored_state(session_id: str, user_id: str) -> tuple[int, int, int]:
    """(answer rows, correct rows, practiced_items events) for one attempt."""
    async with get_async_session_maker()() as db:
        rows = (await db.execute(select(ExamAnswer).where(ExamAnswer.session_id == session_id))).scalars().all()
        events = (
            (
                await db.execute(
                    select(LearningEvent).where(
                        LearningEvent.user_id == user_id,
                        LearningEvent.event_type == "practiced_items",
                    )
                )
            )
            .scalars()
            .all()
        )
        return len(rows), sum(1 for row in rows if row.correct), len(events)


@pytest_asyncio.fixture
async def pg_client() -> AsyncGenerator[AsyncClient, None]:
    """App client whose request sessions read/write the Postgres test DB.

    conftest's ``client`` fixture is bound to the SQLite engine; the row lock
    under test only exists on Postgres, so the routes need the Postgres session
    maker (resolved per request, after conftest's ``_async_setup`` monkeypatches
    ``async_session``).
    """

    async def _override_get_db():
        async with get_async_session_maker()() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_two_preloaded_unsubmitted_attempts_grade_once():
    """The audit's deterministic sequence: both requests read first, then write.

    The barrier is what makes this the race and not an accident — both sessions
    hold ``submitted_at=None`` before either one claims, so the conditional
    UPDATE is the only thing that can pick a winner.
    """
    user_id, _headers, answers, paper_id = await _seed()
    session_id = await _create_attempt(user_id, paper_id)
    maker = get_async_session_maker()
    barrier = asyncio.Barrier(2)

    async def _submit_after_stale_read() -> dict:
        async with maker() as db:
            attempt = await exam_service.get_attempt_detail(db, session_id, user_id)
            assert attempt is not None
            assert attempt.submitted_at is None, "the attempt must still be unsubmitted at read time"
            await barrier.wait()
            return await exam_service.submit_answers(db, attempt, user_id, answers)

    first, second = await asyncio.gather(_submit_after_stale_read(), _submit_after_stale_read())

    # One grading, replayed to the other caller.
    assert first["score"] == second["score"] == 1.0
    assert first["correct_count"] == second["correct_count"] == 3
    assert first["total"] == second["total"] == 3
    assert first["results"] == second["results"]

    rows, correct, events = await _stored_state(session_id, user_id)
    assert (rows, correct) == (3, 3), "a second answer set means both requests graded"
    assert events == 1, "each submission grades once, so exactly one learning event"


async def test_concurrent_http_submits_return_one_result(pg_client: AsyncClient):
    """Same invariant through the endpoint two tabs would hit."""
    user_id, headers, answers, paper_id = await _seed()
    session_id = await _create_attempt(user_id, paper_id)
    url = f"/api/v1/exams/attempts/{session_id}/submit"

    first, second = await asyncio.gather(
        pg_client.post(url, headers=headers, json={"answers": answers}),
        pg_client.post(url, headers=headers, json={"answers": answers}),
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["score"] == second.json()["score"] == 1.0
    assert first.json()["results"] == second.json()["results"]

    rows, correct, events = await _stored_state(session_id, user_id)
    assert (rows, correct, events) == (3, 3, 1)

    async with get_async_session_maker()() as db:
        submitted = (await db.execute(select(ExamSession.submitted_at).where(ExamSession.id == session_id))).scalar()
    assert submitted is not None


def _hold_grading_commit_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pace the winner so the loser provably reaches its claim attempt.

    Pause after the conditional UPDATE wins, before grading. Placeholder rows
    already exist now, so inspecting ``self.new`` would miss the transaction.
    """
    original_claim = exam_service._claim_submit

    async def _paused_claim(db, session_id, user_id, now) -> bool:
        won = await original_claim(db, session_id, user_id, now)
        if won:
            await asyncio.sleep(RACE_WINDOW_S)
        return won

    monkeypatch.setattr(exam_service, "_claim_submit", _paused_claim)


async def test_racing_submits_with_different_payloads_keep_the_first(
    pg_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """The losers' answers never overwrite the submission of record.

    The two payloads disagree on purpose, so "both callers see one result" and
    "the later answers won" cannot be confused.
    """
    user_id, headers, answers, paper_id = await _seed()
    session_id = await _create_attempt(user_id, paper_id)
    url = f"/api/v1/exams/attempts/{session_id}/submit"
    wrong = [{"question_id": a["question_id"], "answer": "Z"} for a in answers]

    _hold_grading_commit_open(monkeypatch)

    first, second = await asyncio.gather(
        pg_client.post(url, headers=headers, json={"answers": answers}),
        pg_client.post(url, headers=headers, json={"answers": wrong}),
    )

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    payload = first.json()
    assert payload["correct_count"] in (0, 3), "one payload was graded, the other replayed"

    rows, correct, events = await _stored_state(session_id, user_id)
    assert rows == 3
    assert correct == payload["correct_count"]
    assert events == 1

    async with get_async_session_maker()() as db:
        stored_answers = sorted(
            (await db.execute(select(ExamAnswer.user_answer).where(ExamAnswer.session_id == session_id)))
            .scalars()
            .all()
        )
        score = (await db.execute(select(ExamSession.score).where(ExamSession.id == session_id))).scalar()
    assert stored_answers == sorted(r["user_answer"] for r in payload["results"])
    assert score == payload["score"]


@pytest.mark.parametrize("mode", ["paper_exam", "daily_check", "wrong_redo"])
async def test_postgres_deleting_source_paper_preserves_frozen_grading(mode):
    """Real CASCADE/SET NULL must not remove the grading identity or answers."""
    user_id, _headers, answers, paper_id = await _seed()
    maker = get_async_session_maker()
    if mode == "wrong_redo":
        previous_id = await _create_attempt(user_id, paper_id)
        async with maker() as db:
            previous = await exam_service.get_attempt_detail(db, previous_id, user_id)
            await exam_service.submit_answers(
                db, previous, user_id, [{"question_id": a["question_id"], "answer": "Z"} for a in answers]
            )
    async with maker() as db:
        if mode == "paper_exam":
            paper = await exam_service.get_paper_with_questions(db, paper_id)
            session = await exam_service.create_paper_session(db, user_id, paper)
        elif mode == "daily_check":
            session, _ = await exam_service.create_daily_session(db, user_id, "cet4", 3)
        else:
            session, _ = await exam_service.create_wrong_redo_session(db, user_id)
        session_id = session.id
        await db.commit()
    async with maker() as db:
        await db.execute(update(ExamQuestion).where(ExamQuestion.paper_id == paper_id).values(answer="Z"))
        await db.execute(delete(ExamPaper).where(ExamPaper.id == paper_id))
        await db.commit()
    async with maker() as db:
        session = await exam_service.get_attempt_detail(db, session_id, user_id)
        assert session.paper_id is None
        assert all(a.question_id is None for a in session.answers)
        result = await exam_service.submit_answers(db, session, user_id, answers)
        assert result["score"] == 1.0 and result["total"] == 3
    async with maker() as db:
        session = await exam_service.get_attempt_detail(db, session_id, user_id)
        assert await exam_service.submit_answers(db, session, user_id, []) == result
