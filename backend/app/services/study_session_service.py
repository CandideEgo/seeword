"""Study session service — persisted training rounds, daily quota and 加练 (DEC-053).

The vocabulary drill's progress used to live in React state only, and its daily
volume was hardcoded in the route (15 new + 20 review). This module owns the
three things that replaced that (design §3.2 §3.3 §5.5):

1. **Rounds** — a round is a ``StudySession`` row with one ``StudySessionItem``
   per word. Repeated answers UPDATE the item, never append, so storage is
   bounded by words × rounds rather than by answers.
2. **Quota** — ``daily_new_target`` / ``daily_review_target`` on
   ``UserLearningProfile``, one global setting per user (5..100). A round
   snapshots the quota it was created with; raising the quota later must not
   rewrite a finished round's size.
3. **加练** — ``kind=extra``: the same quota again, taken from words still
   ``mastery_level = new``. It counts toward today's total
   (``today_words_learned``) but not toward today's goal.

Answering a word also emits ``learned_words`` so the profile's
``today_words_learned`` grows — that counter is what the 今日 tab reads, and
before this it only moved for practice-quiz submissions.

Retention: finishing a round sweeps that user's rounds older than
``SESSION_RETENTION_DAYS`` in the same transaction. Deliberately not a
scheduled job — a periodic task for a table that only grows when a user
studies is more moving parts than the problem needs.
"""

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.models.learning import Vocabulary
from app.models.study_session import StudySession, StudySessionItem
from app.services import learning_event_service
from app.services.learning_event_service import get_user_local_date
from app.services.profile_service import get_or_create_profile
from app.services.vocabulary_service import (
    MASTERY_NEW,
    QUALITY_CORRECT,
    QUALITY_WRONG,
    apply_logged_review,
)

# 每日配额（设计方案 §3.2）：全局一个设置，范围 5~100，新词默认 10。
QUOTA_MIN = 5
QUOTA_MAX = 100
DEFAULT_NEW_TARGET = 10
DEFAULT_REVIEW_TARGET = 20

# 连对 2 次毕业（设计方案 §5.1）。S3 只负责把计数落库，用它驱动出题循环是 S5。
GRADUATE_STREAK = 2

# 轮次明细保留期（天）。超过的轮次在下一轮完成时顺手删除。
SESSION_RETENTION_DAYS = 30

SESSION_ACTIVE = "active"
SESSION_FINISHED = "finished"
SESSION_ABANDONED = "abandoned"

ITEM_PENDING = "pending"
ITEM_LEARNING = "learning"
ITEM_GRADUATED = "graduated"

KIND_DAILY = "daily"

# 加练取词时，排除「近 N 天的轮次里已经排过的词」。主机制其实是答过的词会离开
# mastery_level = new 池；这层排除只为兜住「作答请求失败、词没被更新」的情况，
# 顺带跨过午夜边界。
_PICK_EXCLUDE_DAYS = 1


# ---------------------------------------------------------------------------
# Daily quota
# ---------------------------------------------------------------------------


def clamp_quota(value: int) -> int:
    """Clamp a quota into the allowed range."""
    return max(QUOTA_MIN, min(QUOTA_MAX, value))


async def get_preferences(db: AsyncSession, user_id: str) -> dict:
    """Read the user's daily training quota, with defaults for missing rows."""
    profile = await get_or_create_profile(db, user_id)
    return {
        "daily_new_target": profile.daily_new_target or DEFAULT_NEW_TARGET,
        "daily_review_target": profile.daily_review_target or DEFAULT_REVIEW_TARGET,
    }


async def set_preferences(
    db: AsyncSession,
    user_id: str,
    daily_new_target: int | None = None,
    daily_review_target: int | None = None,
) -> dict:
    """Update the daily training quota. ``None`` leaves a field untouched.

    Range enforcement lives in the request schema (5..100); this clamps as a
    second line of defence so a service-level caller cannot write a nonsense
    quota that would make every round either empty or absurd.
    """
    profile = await get_or_create_profile(db, user_id)
    if daily_new_target is not None:
        profile.daily_new_target = clamp_quota(daily_new_target)
    if daily_review_target is not None:
        profile.daily_review_target = clamp_quota(daily_review_target)
    await db.commit()
    return {
        "daily_new_target": profile.daily_new_target,
        "daily_review_target": profile.daily_review_target,
    }


# ---------------------------------------------------------------------------
# Today's counters
# ---------------------------------------------------------------------------


async def get_today_summary(db: AsyncSession, user_id: str) -> dict:
    """Today's 累计: words studied (incl. 加练) and how many rounds were started.

    Reads the profile counter without mutating it: a stale ``today_date``
    simply means zero words today, which is also what the next ``emit_event``
    will reset it to.
    """
    today = await get_user_local_date(db, user_id)
    profile = await get_or_create_profile(db, user_id)
    words_learned = profile.today_words_learned if profile.today_date == today else 0
    rounds = (
        await db.execute(
            select(func.count(StudySession.id)).where(
                StudySession.user_id == user_id,
                StudySession.local_date == today,
            )
        )
    ).scalar() or 0
    return {"words_learned": words_learned, "rounds": rounds}


# ---------------------------------------------------------------------------
# Rounds
# ---------------------------------------------------------------------------


async def get_active_session(db: AsyncSession, user_id: str) -> StudySession | None:
    """The user's resumable round, or ``None``.

    Only **today's** round resumes. A round left active yesterday is stale by
    definition — 今日训练 is a per-day dose, and resuming yesterday's queue
    would silently make today's quota disappear. Stale rows are marked
    abandoned when the next round is started.
    """
    today = await get_user_local_date(db, user_id)
    stmt = (
        select(StudySession)
        .where(
            StudySession.user_id == user_id,
            StudySession.status == SESSION_ACTIVE,
            StudySession.local_date == today,
        )
        .order_by(StudySession.started_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_owned_session(
    db: AsyncSession, user_id: str, session_id: str, *, for_update: bool = False
) -> StudySession | None:
    """Fetch a round by id, scoped to its owner."""
    stmt = select(StudySession).where(
        StudySession.id == session_id,
        StudySession.user_id == user_id,
    )
    if for_update:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    return (await db.execute(stmt)).scalar_one_or_none()


async def session_rows(db: AsyncSession, session_id: str) -> list[tuple[StudySessionItem, Vocabulary]]:
    """The round's items paired with their words, in round order.

    A left-join would be wrong here: a missing word means the vocabulary row
    was deleted, and the item is then dropped rather than rendered blank.
    """
    stmt = (
        select(StudySessionItem, Vocabulary)
        .join(Vocabulary, Vocabulary.id == StudySessionItem.vocabulary_id)
        .where(StudySessionItem.session_id == session_id)
        .order_by(StudySessionItem.sort_order.asc())
    )
    return [(item, word) for item, word in (await db.execute(stmt)).all()]


async def _recent_session_vocab_ids(db: AsyncSession, user_id: str, today: date) -> set[str]:
    """Vocabulary ids already queued in the user's recent rounds."""
    cutoff = today - timedelta(days=_PICK_EXCLUDE_DAYS)
    stmt = (
        select(StudySessionItem.vocabulary_id)
        .join(StudySession, StudySession.id == StudySessionItem.session_id)
        .where(StudySession.user_id == user_id, StudySession.local_date >= cutoff)
    )
    return set((await db.execute(stmt)).scalars().all())


async def _pick_new_words(
    db: AsyncSession,
    user_id: str,
    limit: int,
    exclude_ids: set[str],
) -> list[Vocabulary]:
    """Oldest-first ``mastery_level = new`` words, minus the excluded ids."""
    stmt = (
        select(Vocabulary)
        .where(Vocabulary.user_id == user_id, Vocabulary.mastery_level == MASTERY_NEW)
        .order_by(Vocabulary.created_at.asc())
        .limit(limit)
    )
    if exclude_ids:
        stmt = stmt.where(Vocabulary.id.notin_(exclude_ids))
    return list((await db.execute(stmt)).scalars().all())


async def preview_new_words(db: AsyncSession, user_id: str, limit: int) -> tuple[str | None, list[Vocabulary]]:
    """Read the next round without creating it or changing existing progress."""
    active = await get_active_session(db, user_id)
    if active is not None:
        rows = await session_rows(db, active.id)
        return active.id, [word for item, word in rows if item.status != ITEM_GRADUATED]
    today = await get_user_local_date(db, user_id)
    excluded = await _recent_session_vocab_ids(db, user_id, today)
    return None, await _pick_new_words(db, user_id, limit, excluded)


async def start_session(db: AsyncSession, user_id: str, kind: str = KIND_DAILY) -> dict:
    """Get the resumable round, or open a new one.

    Idempotent by design: if today's round is still active it is returned
    untouched, so a double-mounted effect (React StrictMode) cannot open two
    rounds or duplicate items. Callers that want 加练 must close the current
    round first — that is exactly the 总结页 flow.

    Returns ``{"session": StudySession | None, "items": [(item, word)]}``;
    ``session`` is ``None`` when the pool of unlearned words is empty (nothing
    to train), which is a normal state, not an error.
    """
    # 「取或建」必须对同一用户串行：两个并发 POST（StrictMode 双挂载、两个
    # 标签页、或前端两个 hook 同时首访）都会先读到「没有进行中的一轮」，
    # 然后各自开一轮，留下两条 active 记录。用事务级 advisory lock 把
    # check-then-create 变成临界区——不能锁 users 行：插入档案行时外键要拿
    # 该行的 KEY SHARE，会和 FOR UPDATE 互相等待成死锁。锁随本次事务提交
    # 释放；SQLite（单测）没有这把锁，也不需要。
    bind = db.get_bind() if hasattr(db, "get_bind") else getattr(db, "bind", None)
    if getattr(getattr(bind, "dialect", None), "name", "") == "postgresql":
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:uid, 0))"),
            {"uid": user_id},
        )

    today = await get_user_local_date(db, user_id)

    active = await get_active_session(db, user_id)
    if active is not None:
        return {"session": active, "items": await session_rows(db, active.id)}

    # Any still-active round from an earlier day is dead: mark it abandoned so
    # "active" keeps meaning "resumable".
    stale = (
        (
            await db.execute(
                select(StudySession).where(
                    StudySession.user_id == user_id,
                    StudySession.status == SESSION_ACTIVE,
                    StudySession.local_date < today,
                )
            )
        )
        .scalars()
        .all()
    )
    for old in stale:
        old.status = SESSION_ABANDONED
        old.finished_at = datetime.now(UTC)

    prefs = await get_preferences(db, user_id)
    excluded = await _recent_session_vocab_ids(db, user_id, today)
    words = await _pick_new_words(db, user_id, prefs["daily_new_target"], excluded)
    if not words:
        await db.commit()
        return {"session": None, "items": []}

    session = StudySession(
        user_id=user_id,
        local_date=today,
        kind=kind,
        target_count=len(words),
        done_count=0,
        correct_count=0,
        status=SESSION_ACTIVE,
    )
    db.add(session)
    await db.flush()

    items: list[tuple[StudySessionItem, Vocabulary]] = []
    for position, word in enumerate(words):
        item = StudySessionItem(
            session_id=session.id,
            vocabulary_id=word.id,
            sort_order=position,
            status=ITEM_PENDING,
        )
        db.add(item)
        items.append((item, word))

    await db.commit()
    return {"session": session, "items": items}


async def submit_answer(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    vocabulary_id: str,
    correct: bool,
) -> dict:
    """Record one answer inside a round. Raises ``LookupError`` / ``ValueError``.

    One answer costs one UPDATE on the item plus one on the word — the same
    write the drill already did per tap (it POSTed a review per 认识/不认识);
    the difference is that the round's own state now lands somewhere durable.
    """
    session = await get_owned_session(db, user_id, session_id, for_update=True)
    if session is None:
        raise NotFoundError("Round not found")
    if session.status != SESSION_ACTIVE:
        raise ConflictError("Round is closed")

    item = (
        await db.execute(
            select(StudySessionItem)
            .where(StudySessionItem.session_id == session_id, StudySessionItem.vocabulary_id == vocabulary_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if item is None:
        raise NotFoundError("Word is not part of this round")

    vocab = (
        await db.execute(
            select(Vocabulary)
            .where(Vocabulary.id == vocabulary_id, Vocabulary.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if vocab is None:
        raise NotFoundError("Word not found")

    was_pending = item.status == ITEM_PENDING

    await apply_logged_review(db, vocab, QUALITY_CORRECT if correct else QUALITY_WRONG, source="study")

    if correct:
        item.correct_streak = (item.correct_streak or 0) + 1
    else:
        item.correct_streak = 0
        item.wrong_in_round = True
    item.status = ITEM_GRADUATED if item.correct_streak >= GRADUATE_STREAK else ITEM_LEARNING

    if was_pending:
        session.done_count = (session.done_count or 0) + 1
    if correct:
        session.correct_count = (session.correct_count or 0) + 1

    # Emit once per word, not once per answer: ``today_words_learned`` counts
    # words met today, and a word answered twice is still one word. The round
    # lock serializes first-answer claims; fact and answer commit together.
    if was_pending:
        await learning_event_service.record_event(
            db, user_id, learning_event_service.EVENT_LEARNED_WORDS, flow_id=session_id, source="vocabulary"
        )
    await db.commit()

    return {
        "item": item,
        "session": session,
        "correct": correct,
        "graduated": item.status == ITEM_GRADUATED,
    }


async def finish_session(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    status: str = SESSION_FINISHED,
) -> StudySession:
    """Close a round and sweep the user's expired rounds in the same transaction."""
    if status not in {SESSION_FINISHED, SESSION_ABANDONED}:
        raise BadRequestError("Invalid round status")

    session = await get_owned_session(db, user_id, session_id, for_update=True)
    if session is None:
        raise NotFoundError("Round not found")

    session.status = status
    session.finished_at = datetime.now(UTC)

    today = await get_user_local_date(db, user_id)
    cutoff = today - timedelta(days=SESSION_RETENTION_DAYS)
    expired = select(StudySession.id).where(
        StudySession.user_id == user_id,
        StudySession.local_date < cutoff,
    )
    # Items first, explicitly: the test suite runs on SQLite, where FK
    # ON DELETE CASCADE is not enforced, and an orphan sweep is cheaper than a
    # pragma that would change the whole suite's semantics.
    await db.execute(delete(StudySessionItem).where(StudySessionItem.session_id.in_(expired)))
    await db.execute(
        delete(StudySession).where(
            StudySession.user_id == user_id,
            StudySession.local_date < cutoff,
        )
    )

    await db.commit()
    return session
