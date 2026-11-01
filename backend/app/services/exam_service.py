"""真题测试 (past-paper exam) service — sessions, grading, daily check.

Owns the attempt lifecycle:
  * ``create_paper_session``   — start a full-paper attempt (mode=paper_exam)
  * ``create_daily_session``   — start a random daily check (mode=daily_check)
  * ``create_wrong_redo_session`` — start a wrong-book redo (mode=wrong_redo)
  * ``submit_answers``         — server-side grading, freezes question
    snapshots into exam_answers, computes score + per-section breakdown, and
    emits a LearningEvent (practiced_items) so the daily plan / profile
    pipelines see the activity. One submission per attempt: the conditional
    UPDATE in ``_claim_submit`` decides a concurrent race, and losers replay
    the winner's settled result instead of grading again.
  * ``list_wrong_questions``   — aggregated wrong-book view (derived query,
    no extra table)
  * ``exam_stats``             — practice-hub headline stats

Grading rule: user choice must exactly match the stored answer letter
(case-insensitive). Unanswered questions count as wrong.
"""

from __future__ import annotations

import logging
import random
import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.models.exam_test import ExamAnswer, ExamPaper, ExamQuestion, ExamSession
from app.models.preferences import UserPreferences

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

MODE_PAPER = "paper_exam"
MODE_DAILY = "daily_check"
MODE_WRONG = "wrong_redo"

# Section display order in results. **这也是一道丢弃门**：交卷时 part_scores 只保留
# 列在这里的 section（见 `submit_answers` 里的 `for sec in SECTION_ORDER if sec in part`），
# 新增 section 而不加进来会让成绩页整节消失、总分却仍然正确。考研卷用
# use_of_english / new_type，四级六级只有 reading_A/B/C。
SECTION_ORDER = ("use_of_english", "reading_A", "reading_B", "reading_C", "new_type")

DAILY_QUESTION_COUNT = 10


def _now() -> datetime:
    return datetime.now(UTC)


def _as_naive_utc(dt: datetime | None) -> datetime | None:
    """Normalize DB datetimes to naive UTC.

    PostgreSQL returns timezone-aware datetimes while the test SQLite returns
    naive ones; both must compare/sort consistently with the naive-UTC
    boundaries computed in this module.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


async def get_paper_with_questions(db: AsyncSession, paper_id: str) -> ExamPaper | None:
    stmt = select(ExamPaper).where(ExamPaper.id == paper_id).options(selectinload(ExamPaper.questions))
    return (await db.execute(stmt)).scalar_one_or_none()


def _question_public(q: ExamQuestion) -> dict:
    """Public question payload — deliberately excludes answer/explanation."""
    return {
        "id": q.id,
        "number": q.number,
        "section": q.section,
        "question_type": q.question_type,
        "passage": q.passage,
        "question": q.question,
        "options": q.options,
    }


def _snapshot_question(q: ExamQuestion) -> dict:
    """Frozen question snapshot stored on exam_answers (includes answer)."""
    return {
        "id": q.id,
        "number": q.number,
        "section": q.section,
        "question_type": q.question_type,
        "passage": q.passage,
        "question": q.question,
        "options": q.options,
        "answer": q.answer,
        "explanation": q.explanation,
    }


# Mirror of the frontend option-derivation rules (ExamRunner.deriveOptions).
# Section A / B questions store options=null; their answerable options come
# from the passage (word-bank appendix / paragraph letters). A question with
# neither stored options nor a derivable passage (e.g. xdf matching rows with
# passage=null) has nothing to click and must not enter an attempt.
_WORD_BANK_MARKER = "[word bank]"
_WORD_BANK_ENTRY_RE = re.compile(r"([A-O])\)")
# 段落字母放宽到 A-Z：CET 匹配题的文章段落数不止 15（实测四级到 P、六级到 R），
# 卡在 A-O 会让 P/Q/R 这三个字母的正确答案在界面上点不到。
_PARAGRAPH_LETTER_RE = re.compile(r"^([A-Z])\)", re.MULTILINE)


def is_answerable(q: ExamQuestion) -> bool:
    """True when the client can render at least one clickable option."""
    if q.options:
        return True
    passage = q.passage or ""
    if not passage:
        return False
    marker = passage.lower().find(_WORD_BANK_MARKER)
    if marker != -1:
        return bool(_WORD_BANK_ENTRY_RE.search(passage[marker + len(_WORD_BANK_MARKER) :]))
    if q.question_type == "matching":
        return len(set(_PARAGRAPH_LETTER_RE.findall(passage))) >= 2
    return False


def _answerable_questions(questions: list[ExamQuestion]) -> list[ExamQuestion]:
    return [q for q in questions if is_answerable(q)]


async def create_paper_session(db: AsyncSession, user_id: str, paper: ExamPaper) -> ExamSession:
    """Create a full-paper attempt session.

    ``question_count`` reflects only answerable questions — unanswerable rows
    (no stored options and no derivable passage) are excluded everywhere the
    question set is served, so the client's 已答/总题数 denominator matches.
    """
    session = ExamSession(
        user_id=user_id,
        mode=MODE_PAPER,
        exam_level=paper.level,
        paper_id=paper.id,
        question_count=len(_answerable_questions(list(paper.questions))),
        started_at=_now(),
    )
    db.add(session)
    await db.flush()
    return session


async def create_daily_session(
    db: AsyncSession, user_id: str, level: str | None, count: int = DAILY_QUESTION_COUNT
) -> tuple[ExamSession, list[ExamQuestion]]:
    """Create a daily-check session with random questions from the bank.

    ``level`` filters by the user's target exam when given; falls back to any
    available level otherwise. Random selection without repetition.
    """
    stmt = select(ExamQuestion)
    if level:
        stmt = stmt.join(ExamQuestion.paper).where(ExamPaper.level == level)
    # Draw a bounded random sample first so a large question bank is not fully
    # materialised on every daily-check start. If the sample is too sparse
    # (most rows unanswerable), fall back to the full pool — correctness first.
    sample_size = max(count * 5, count)
    pool = list((await db.execute(stmt.order_by(func.random()).limit(sample_size))).scalars())
    if not pool:
        # Level filter matched nothing (e.g. user target_exam has no bank yet):
        # fall back to any available question so the daily check still works.
        pool = list((await db.execute(select(ExamQuestion).order_by(func.random()).limit(sample_size))).scalars())
    # Never draw unanswerable questions (client would render no options).
    pool = _answerable_questions(pool)
    if len(pool) < count:
        fallback = (await db.execute(select(ExamQuestion))).scalars().all()
        pool = _answerable_questions(list(fallback))
    if not pool:
        raise NotFoundError("题库为空，请先导入真题")
    picked = random.sample(pool, min(count, len(pool)))
    # Keep paper grouping so the same paper's passages stay together for reading.
    picked.sort(key=lambda q: (q.paper_id, q.number))

    session = ExamSession(
        user_id=user_id,
        mode=MODE_DAILY,
        exam_level=level,
        paper_id=None,
        question_count=len(picked),
        started_at=_now(),
    )
    db.add(session)
    await db.flush()
    # Fix the session's question set NOW via placeholder ExamAnswer rows
    # (answered_at=None). Binding submission to exactly these questions is
    # required — otherwise a client could submit arbitrary question ids and
    # read the correct answers back from the grading response (answer
    # enumeration / score manipulation).
    for q in picked:
        db.add(
            ExamAnswer(
                session_id=session.id,
                question_id=q.id,
                question=_snapshot_question(q),
                answered_at=None,
            )
        )
    return session, picked


async def _latest_wrong_answers(db: AsyncSession, user_id: str) -> list[ExamAnswer]:
    """Latest graded answer per question, only where that answer is wrong.

    Uses a window function instead of loading the user's entire answer history
    into Python: the result is bounded by the number of distinct questions the
    user has answered, not by every attempt since signup.
    """
    ranked = (
        select(
            ExamAnswer.id.label("answer_id"),
            func.row_number()
            .over(
                partition_by=ExamAnswer.question_id,
                order_by=(ExamAnswer.answered_at.desc(), ExamAnswer.id.desc()),
            )
            .label("rank"),
        )
        .join(ExamSession, ExamAnswer.session_id == ExamSession.id)
        .where(
            ExamSession.user_id == user_id,
            ExamSession.submitted_at.is_not(None),
            ExamAnswer.user_answer.is_not(None),
            ExamAnswer.question_id.is_not(None),
        )
        .subquery()
    )
    rows = (
        await db.execute(
            select(ExamAnswer)
            .join(ranked, ExamAnswer.id == ranked.c.answer_id)
            .where(ranked.c.rank == 1, ExamAnswer.correct.is_(False))
            .order_by(ExamAnswer.answered_at.desc())
        )
    ).scalars()
    return list(rows)


async def _wrong_counts(db: AsyncSession, user_id: str) -> dict[str, int]:
    """How many times each question was answered wrong (SQL GROUP BY)."""
    rows = (
        await db.execute(
            select(ExamAnswer.question_id, func.count())
            .join(ExamSession, ExamAnswer.session_id == ExamSession.id)
            .where(
                ExamSession.user_id == user_id,
                ExamSession.submitted_at.is_not(None),
                ExamAnswer.user_answer.is_not(None),
                ExamAnswer.question_id.is_not(None),
                ExamAnswer.correct.is_(False),
            )
            .group_by(ExamAnswer.question_id)
        )
    ).all()
    return {qid: count for qid, count in rows if qid}


async def list_wrong_questions(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[dict], int]:
    """Aggregate the user's wrong book (derived query, no extra table).

    One row per question whose most recent graded answer is wrong, with
    ``wrong_count`` and the source paper's title/level. Only answered rows
    count; unanswered questions are excluded.
    """
    latest_rows = await _latest_wrong_answers(db, user_id)
    wrong_counts = await _wrong_counts(db, user_id)
    latest = {a.question_id: a for a in latest_rows if a.question_id}

    question_ids = list(latest.keys())
    papers: dict[str, ExamPaper] = {}
    if question_ids:
        paper_rows = (
            await db.execute(
                select(ExamQuestion.id, ExamPaper)
                .join(ExamPaper, ExamQuestion.paper_id == ExamPaper.id)
                .where(ExamQuestion.id.in_(question_ids))
            )
        ).all()
        papers = {qid: paper for qid, paper in paper_rows}

    items: list[dict] = []
    for qid, answer in latest.items():
        snap = answer.question or {}
        paper = papers.get(qid)
        items.append(
            {
                "question_id": qid,
                "number": snap.get("number"),
                "section": snap.get("section"),
                "question_type": snap.get("question_type"),
                "passage": snap.get("passage"),
                "question": snap.get("question"),
                "options": snap.get("options"),
                "wrong_count": wrong_counts.get(qid, 1),
                "last_wrong_at": answer.answered_at,
                "paper_id": paper.id if paper else None,
                "paper_title": paper.title if paper else None,
                "level": paper.level if paper else None,
                "year": paper.year if paper else None,
                "month": paper.month if paper else None,
            }
        )

    # Most recent wrong first, then by paper question number.
    items.sort(
        key=lambda x: (
            _as_naive_utc(x["last_wrong_at"]) or datetime.min,
            -(x["number"] or 0),
        ),
        reverse=True,
    )
    total = len(items)
    start = (page - 1) * page_size
    return items[start : start + page_size], total


async def create_wrong_redo_session(
    db: AsyncSession,
    user_id: str,
    question_ids: list[str] | None = None,
) -> tuple[ExamSession, list[ExamQuestion]]:
    """Start a wrong-book redo session over the user's wrong questions.

    ``question_ids`` restricts the set (e.g. retry one attempt's wrong
    questions); when omitted every aggregated wrong question is included.
    Mirrors ``create_daily_session``: question set locked via placeholder
    ExamAnswer rows so submissions can't enumerate arbitrary ids.
    """
    latest_rows = await _latest_wrong_answers(db, user_id)
    wrong_ids = sorted(a.question_id for a in latest_rows if a.question_id)
    if question_ids:
        allowed = set(question_ids)
        wrong_ids = [qid for qid in wrong_ids if qid in allowed]
    if not wrong_ids:
        raise NotFoundError("暂无错题可重做")

    questions = list((await db.execute(select(ExamQuestion).where(ExamQuestion.id.in_(wrong_ids)))).scalars())
    questions = _answerable_questions(questions)
    if not questions:
        raise NotFoundError("暂无错题可重做")
    questions.sort(key=lambda q: (q.paper_id, q.number))

    session = ExamSession(
        user_id=user_id,
        mode=MODE_WRONG,
        exam_level=None,
        paper_id=None,
        question_count=len(questions),
        started_at=_now(),
    )
    db.add(session)
    await db.flush()
    for q in questions:
        db.add(
            ExamAnswer(
                session_id=session.id,
                question_id=q.id,
                question=_snapshot_question(q),
                answered_at=None,
            )
        )
    return session, questions


async def exam_stats(db: AsyncSession, user_id: str) -> dict:
    """Practice-hub headline stats.

    ``month_completed`` / ``avg_score`` cover this calendar month's submitted
    attempts; ``last_daily_score`` / ``week_daily_count`` cover the daily
    check series (any time / last 7 days).
    """
    now = _as_naive_utc(_now())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    month_filter = (ExamSession.submitted_at.is_not(None), ExamSession.submitted_at >= month_start)
    daily_filter = (ExamSession.mode == MODE_DAILY, ExamSession.submitted_at.is_not(None))
    week_daily_filter = (*daily_filter, ExamSession.submitted_at >= week_start)

    # One round trip for all four figures. The "latest daily score" is a
    # correlated scalar subquery rather than a second statement; the two counts
    # use aggregate FILTER so no extra WHERE clause is needed.
    last_daily_score_sq = (
        select(ExamSession.score)
        .where(ExamSession.user_id == user_id, *daily_filter)
        .order_by(ExamSession.submitted_at.desc())
        .limit(1)
        .scalar_subquery()
    )
    month_completed, month_score_sum, week_daily_count, last_daily_score = (
        await db.execute(
            select(
                func.count(ExamSession.id).filter(*month_filter),
                func.coalesce(func.sum(ExamSession.score).filter(*month_filter), 0.0),
                func.count(ExamSession.id).filter(*week_daily_filter),
                last_daily_score_sq,
            ).where(ExamSession.user_id == user_id)
        )
    ).one()
    avg_score = round(float(month_score_sum) / month_completed, 4) if month_completed else None

    return {
        "month_completed": int(month_completed),
        "avg_score": avg_score,
        "last_daily_score": last_daily_score,
        "week_daily_count": int(week_daily_count or 0),
    }


async def _claim_submit(db: AsyncSession, session_id: str, user_id: str, now: datetime) -> bool:
    """Try to take this attempt's single submission slot.

    ``submitted_at`` doubles as the claim: a conditional ``UPDATE`` is the only
    write allowed to decide a concurrent submit, so two requests that both read
    ``submitted_at IS NULL`` still produce exactly one winner. On PostgreSQL
    the loser blocks on the row lock until the winner commits and then
    re-evaluates the predicate against the committed row (no match) — so a
    ``False`` here also means the winner's answers are already readable.
    Claim and grading share one transaction: a failure further down rolls the
    claim back, so an aborted submit never leaves the attempt looking submitted.
    """
    stmt = (
        update(ExamSession)
        .where(
            ExamSession.id == session_id,
            ExamSession.user_id == user_id,
            ExamSession.submitted_at.is_(None),
        )
        .values(submitted_at=now)
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    return bool(result.rowcount)


def _submitted_payload(settled: ExamSession) -> dict:
    """Grading payload rebuilt from a submitted attempt's frozen answer rows."""
    rows = sorted(
        (a for a in settled.answers if a.answered_at is not None),
        key=lambda a: (a.question or {}).get("number") or 0,
    )
    results = []
    for a in rows:
        snap = a.question or {}
        results.append(
            {
                # Legacy snapshot-only rows predate the question bank link and
                # only carry the id inside the frozen snapshot.
                "question_id": a.question_id or snap.get("id"),
                "number": int(snap.get("number") or 0),
                "section": str(snap.get("section") or ""),
                "question_type": snap.get("question_type"),
                "question": snap.get("question"),
                "options": snap.get("options"),
                "passage": snap.get("passage"),
                "user_answer": a.user_answer,
                "correct": bool(a.correct),
                "correct_answer": snap.get("answer"),
                "explanation": snap.get("explanation"),
            }
        )
    return {
        "session_id": settled.id,
        "mode": settled.mode,
        "score": settled.score or 0.0,
        "correct_count": sum(1 for a in rows if a.correct),
        "total": len(rows),
        "part_scores": settled.part_scores or {},
        "results": results,
    }


async def _settled_submit_payload(db: AsyncSession, session_id: str, user_id: str) -> dict:
    """Replay the result of the submission that won the race.

    A repeat submit is not an error: the first submission is the answer of
    record, so a client retry (double click, two tabs, a request that timed out
    after the server had already committed) lands on the same result page
    instead of a dead end. Nothing is re-graded and nothing is overwritten.
    """
    stmt = (
        select(ExamSession)
        .where(ExamSession.id == session_id, ExamSession.user_id == user_id)
        .options(selectinload(ExamSession.answers))
    )
    settled = (await db.execute(stmt)).scalar_one_or_none()
    if settled is None:
        raise NotFoundError("作答不存在")
    return _submitted_payload(settled)


async def submit_answers(
    db: AsyncSession,
    session: ExamSession,
    user_id: str,
    answers: list[dict],
) -> dict:
    """Grade a session's answers and freeze per-question snapshots.

    ``answers`` is a list of {question_id, answer}. The session must belong to
    ``user_id``. Exactly one submission per attempt is accepted: the winner
    grades and writes; every later or concurrent submit returns the winner's
    settled result without touching the stored answers. Returns the grading
    payload: {score, correct_count, total, part_scores, results}.
    """
    if session.user_id != user_id:
        raise ForbiddenError("不是本人的作答")

    # Read the id before any rollback: rollback expires the ORM object, and
    # touching an expired attribute here would attempt sync IO (MissingGreenlet).
    session_id = session.id
    now = _now()
    if not await _claim_submit(db, session_id, user_id, now):
        # Already submitted — by an earlier request, or by the concurrent one
        # this call just waited for. Roll back first so the replay cannot read
        # this request's pre-claim snapshot out of the identity map.
        await db.rollback()
        return await _settled_submit_payload(db, session_id, user_id)

    # Load the questions for this session (paper questions or daily picks).
    if session.paper_id is not None:
        paper = await get_paper_with_questions(db, session.paper_id)
        questions: list[ExamQuestion] = sorted(paper.questions, key=lambda q: q.number) if paper else []
        # Keep grading aligned with the answerable set served to the client —
        # excluded rows must not silently count as wrong.
        questions = _answerable_questions(questions)
    else:
        # Daily check: the question set was fixed at session creation via
        # placeholder ExamAnswer rows (answered_at=None). Recovering it from
        # the submitted payload instead would let a client submit arbitrary
        # question ids — extracting answers from the grading response and
        # manipulating scores. Require an exact match on the placeholder set.
        placeholders = {a.question_id: a for a in session.answers if a.question_id}
        submitted_ids = [a.get("question_id") for a in answers]
        if set(submitted_ids) != set(placeholders) or len(submitted_ids) != len(placeholders):
            raise ConflictError("作答题目与本次抽题不一致，请重新开始")
        questions = list((await db.execute(select(ExamQuestion).where(ExamQuestion.id.in_(submitted_ids)))).scalars())
        questions.sort(key=lambda q: q.number)

    if not questions:
        raise ConflictError("作答题目不存在")

    ans_map: dict[str, str] = {}
    for a in answers:
        qid = a.get("question_id") or ""
        val = str(a.get("answer") or "").strip().upper()
        if qid:
            ans_map[qid] = val

    results: list[dict] = []
    part: dict[str, dict[str, int]] = {}
    correct_count = 0

    for q in questions:
        user_answer = ans_map.get(q.id, "")
        is_correct = bool(user_answer) and user_answer == q.answer.upper()
        if is_correct:
            correct_count += 1
        part.setdefault(q.section, {"correct": 0, "total": 0})
        part[q.section]["total"] += 1
        if is_correct:
            part[q.section]["correct"] += 1

        if session.paper_id is not None:
            db.add(
                ExamAnswer(
                    session_id=session.id,
                    question_id=q.id,
                    question=_snapshot_question(q),
                    user_answer=user_answer or None,
                    correct=is_correct,
                    answered_at=now,
                )
            )
        else:
            # Daily check: fill in the pre-inserted placeholder row instead
            # of adding a new one (the placeholder IS the question-set lock).
            row = placeholders[q.id]
            row.user_answer = user_answer or None
            row.correct = is_correct
            row.answered_at = now
        results.append(
            {
                "question_id": q.id,
                "number": q.number,
                "section": q.section,
                "question_type": q.question_type,
                "question": q.question,
                "options": q.options,
                "passage": q.passage,
                "user_answer": user_answer or None,
                "correct": is_correct,
                "correct_answer": q.answer,
                "explanation": q.explanation,
            }
        )

    total = len(questions)
    score = round(correct_count / total, 4) if total else 0.0
    session.submitted_at = now
    session.score = score
    session.part_scores = {
        sec: {"correct": part[sec]["correct"], "total": part[sec]["total"]} for sec in SECTION_ORDER if sec in part
    }
    await db.flush()

    # Same transaction as the grading: the attempt and its practiced_items
    # event land together, so a committed submit can never be missing its
    # event, and a replay (which returns further up) can never emit a second
    # one. ``emit_event`` is itself non-blocking — it swallows its own failures
    # inside a savepoint — so the try/except is belt-and-braces.
    try:
        from app.services.learning_event_service import EVENT_PRACTICED_ITEMS, emit_event

        await emit_event(db, user_id, EVENT_PRACTICED_ITEMS, total, video_id=None, flow_id=session.id, source="exam")
    except Exception:
        logger.exception("Failed to emit learning event for exam session %s", session.id)
    await db.commit()

    return {
        "session_id": session.id,
        "mode": session.mode,
        "score": score,
        "correct_count": correct_count,
        "total": total,
        "part_scores": session.part_scores or {},
        "results": results,
    }


async def list_papers(
    db: AsyncSession,
    user_id: str,
    level: str | None = None,
    page: int = 1,
    page_size: int = 12,
    year: int | None = None,
    status: str = "all",
) -> tuple[list[dict], int]:
    """List papers (newest first) with the current user's attempt stats."""
    stmt = select(ExamPaper)
    count_stmt = select(func.count()).select_from(ExamPaper)
    if level:
        stmt = stmt.where(ExamPaper.level == level)
        count_stmt = count_stmt.where(ExamPaper.level == level)
    filters = []
    if year is not None:
        filters.append(ExamPaper.year == year)
    submitted = (
        select(ExamSession.id)
        .where(
            ExamSession.paper_id == ExamPaper.id,
            ExamSession.user_id == user_id,
            ExamSession.submitted_at.is_not(None),
        )
        .exists()
    )
    if status == "submitted":
        filters.append(submitted)
    elif status == "unsubmitted":
        filters.append(~submitted)
    stmt = stmt.where(*filters)
    count_stmt = count_stmt.where(*filters)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(ExamPaper.year.desc(), ExamPaper.month.desc(), ExamPaper.set_no.asc(), ExamPaper.id)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    papers = (await db.execute(stmt)).scalars().all()

    paper_ids = [p.id for p in papers]
    attempts: list[ExamSession] = []
    if paper_ids:
        attempts = list(
            (
                await db.execute(
                    select(ExamSession).where(
                        ExamSession.user_id == user_id,
                        ExamSession.paper_id.in_(paper_ids),
                        ExamSession.submitted_at.is_not(None),
                    )
                )
            ).scalars()
        )

    by_paper: dict[str, list[ExamSession]] = {}
    for a in attempts:
        by_paper.setdefault(a.paper_id or "", []).append(a)

    last_by_paper = {
        paper_id: max(mine, key=lambda a: (_as_naive_utc(a.submitted_at), a.id)) for paper_id, mine in by_paper.items()
    }
    correct_counts: dict[str, int] = {}
    if last_by_paper:
        rows = await db.execute(
            select(ExamAnswer.session_id, func.count(ExamAnswer.id))
            .where(
                ExamAnswer.session_id.in_([a.id for a in last_by_paper.values()]),
                ExamAnswer.correct.is_(True),
            )
            .group_by(ExamAnswer.session_id)
        )
        correct_counts = {session_id: count for session_id, count in rows.all()}

    # Paper composition for the practice-page cards: real section names and
    # question counts instead of a hard-coded "3 部分 / 30 题".
    sections_by_paper: dict[str, list[dict]] = {}
    if paper_ids:
        section_rows = (
            await db.execute(
                select(ExamQuestion.paper_id, ExamQuestion.section, func.count(ExamQuestion.id))
                .where(ExamQuestion.paper_id.in_(paper_ids))
                .group_by(ExamQuestion.paper_id, ExamQuestion.section)
                .order_by(ExamQuestion.paper_id, ExamQuestion.section)
            )
        ).all()
        for paper_id, section, count in section_rows:
            sections_by_paper.setdefault(paper_id, []).append({"section": section, "question_count": count})

    items: list[dict] = []
    for p in papers:
        mine = by_paper.get(p.id, [])
        last = last_by_paper.get(p.id)
        best = max((a.score or 0) for a in mine) if mine else None
        items.append(
            {
                "id": p.id,
                "level": p.level,
                "year": p.year,
                "month": p.month,
                "set_no": p.set_no,
                "title": p.title,
                "source": p.source,
                "total_questions": p.total_questions,
                "last_score": last.score if last else None,
                "last_submitted_at": last.submitted_at if last else None,
                "last_session_id": last.id if last else None,
                "last_correct_count": correct_counts.get(last.id, 0) if last else None,
                "last_question_count": last.question_count if last else None,
                "attempt_count": len(mine),
                "best_score": best,
                "sections": sections_by_paper.get(p.id, []),
            }
        )
    return items, total


async def paper_years(db: AsyncSession, level: str | None) -> list[int]:
    stmt = select(ExamPaper.year).distinct().order_by(ExamPaper.year.desc())
    if level:
        stmt = stmt.where(ExamPaper.level == level)
    return list((await db.execute(stmt)).scalars().all())


async def get_attempt_detail(db: AsyncSession, session_id: str, user_id: str) -> ExamSession | None:
    stmt = (
        select(ExamSession)
        .where(ExamSession.id == session_id, ExamSession.user_id == user_id)
        .options(selectinload(ExamSession.answers))
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_attempts(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[dict], int]:
    """List the user's attempts (newest first) with paper titles."""
    count_stmt = select(func.count()).select_from(ExamSession).where(ExamSession.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = (
        select(ExamSession)
        .where(ExamSession.user_id == user_id)
        .order_by(ExamSession.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    sessions = (await db.execute(stmt)).scalars().all()

    paper_ids = [s.paper_id for s in sessions if s.paper_id]
    titles: dict[str, str] = {}
    if paper_ids:
        rows = (await db.execute(select(ExamPaper.id, ExamPaper.title).where(ExamPaper.id.in_(paper_ids)))).all()
        titles = {r[0]: r[1] for r in rows}

    # Count correct answers from the frozen answer rows instead of reverse-
    # engineering them from ``score``: score is rounded to 4 decimals, so
    # int(score * question_count) truncates (1/3 → 0, 7/30 → 6) and the attempt
    # list disagrees with the result page for the very same attempt.
    submitted_ids = [s.id for s in sessions if s.submitted_at]
    correct_counts: dict[str, int] = {}
    if submitted_ids:
        correct_rows = (
            await db.execute(
                select(ExamAnswer.session_id, func.count())
                .where(ExamAnswer.session_id.in_(submitted_ids), ExamAnswer.correct.is_(True))
                .group_by(ExamAnswer.session_id)
            )
        ).all()
        correct_counts = {session_id: int(count) for session_id, count in correct_rows}

    items: list[dict] = []
    for s in sessions:
        duration = 0
        if s.submitted_at and s.started_at:
            duration = max(int((s.submitted_at - s.started_at).total_seconds()), 0)
        items.append(
            {
                "id": s.id,
                "mode": s.mode,
                "exam_level": s.exam_level,
                "paper_id": s.paper_id,
                "paper_title": titles.get(s.paper_id or "") if s.paper_id else None,
                "question_count": s.question_count,
                "score": s.score,
                "correct_count": correct_counts.get(s.id, 0) if s.submitted_at else None,
                "duration_sec": duration,
                "started_at": s.started_at,
                "submitted_at": s.submitted_at,
            }
        )
    return items, total


async def user_target_level(db: AsyncSession, user_id: str) -> str | None:
    """The user's target exam level from UserPreferences (no lazy-load)."""
    prefs = (await db.execute(select(UserPreferences).where(UserPreferences.user_id == user_id))).scalar_one_or_none()
    return prefs.target_exam if prefs and prefs.target_exam else None
