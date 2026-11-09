"""Vocabulary enrichment and stats service.

Quiz functionality has been unified into practice_service.build_vocabulary_drill
and practice_service.submit_practice_results.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import commit_refresh
from app.core.exam_levels import max_level
from app.models.learning import Vocabulary
from app.models.preferences import UserPreferences
from app.schemas.vocabulary import VocabularyResponse
from app.services import learning_event_service
from app.services.ai_service import get_ai_service
from app.services.local_time import resolve_user_timezone
from app.services.sr_service import calculate_review_interval

logger = logging.getLogger(__name__)

# ECDICT's pos field carries frequency codes ("v:2/n:98") and can exceed the
# Vocabulary.part_of_speech column width — truncate defensively.
_POS_MAX_LEN = 20


def apply_ecdict_fields(vocab: Vocabulary, entry: dict) -> None:
    """Copy ECDICT fields onto a Vocabulary row.

    The single home for this mapping: 收词（观看页点词入库）、考试/视频词单建档
    两条路径都走它，否则同一个词在不同入口会拿到不同完整度的释义。

    ``exam_level`` takes the highest tagged level (a word tagged both cet4 and
    cet6 is a 六级 word — the question is "how hard is it", not "where did it
    first appear"). ``part_of_speech`` stores ECDICT's raw ``pos`` code
    (``n:100``); ``partOfSpeechLabel`` on the frontend renders the label.
    """
    vocab.definition = entry.get("definition")
    vocab.translation = entry.get("translation")
    pos = entry.get("pos")
    vocab.part_of_speech = pos[:_POS_MAX_LEN] if pos else None
    vocab.ipa = entry.get("phonetic")
    levels = entry.get("levels")
    if levels:
        vocab.exam_level = max_level(list(levels))
    if entry.get("example_sentences"):
        vocab.example_sentences = entry["example_sentences"]


def _get_ai():
    return get_ai_service()


# Mastery level thresholds
MASTERY_NEW = "new"
MASTERY_LEARNING = "learning"
MASTERY_REVIEWING = "reviewing"
MASTERY_MASTERED = "mastered"

# Binary-answer grading shared by the drill's session answers and the legacy
# review endpoint: quality >= 3 counts as correct.
QUALITY_CORRECT = 5
QUALITY_WRONG = 2

# "本轮内曾答错" without a dedicated column (DEC-057): a wrong answer inside
# this window keeps the word on the 次日 schedule even when the *current*
# answer is correct. Round answers land minutes apart, and a word answered
# wrong in a round is due a day later, so in the normal flow only the current
# round can produce a wrong inside 24h. A same-day re-review of a word that
# was wrong earlier today gets the same treatment — "错的还热乎，明天再见".
WRONG_RECENT_WINDOW = timedelta(hours=24)


async def _get_owned_word_for_update(db: AsyncSession, user_id: str, word_id: str) -> Vocabulary | None:
    return (
        await db.execute(
            select(Vocabulary)
            .where(Vocabulary.id == word_id, Vocabulary.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()


async def record_review(
    db: AsyncSession, user_id: str, word_id: str, quality: int
) -> tuple[Vocabulary, int, datetime] | None:
    """Mutate one review and record its required fact; caller commits both."""
    if not 0 <= quality <= 5:
        raise ValueError("Review quality must be between 0 and 5")
    vocab = await _get_owned_word_for_update(db, user_id, word_id)
    if vocab is None:
        return None
    interval, next_review = apply_review(vocab, quality)
    await learning_event_service.record_event(
        db, user_id, learning_event_service.EVENT_REVIEWED_WORDS, source="vocabulary"
    )
    return vocab, interval, next_review


async def mark_mastered(db: AsyncSession, user_id: str, word_id: str) -> Vocabulary | None:
    """Exit the review queue and count the first mastery transition atomically."""
    vocab = await _get_owned_word_for_update(db, user_id, word_id)
    if vocab is None:
        return None
    already_mastered = vocab.mastery_level == MASTERY_MASTERED
    vocab.mastery_level = MASTERY_MASTERED
    vocab.next_review_at = None
    vocab.last_reviewed_at = datetime.now(UTC)
    if not already_mastered:
        await learning_event_service.record_event(
            db, user_id, learning_event_service.EVENT_LEARNED_WORDS, source="vocabulary"
        )
    await db.flush()
    return vocab


def _mastery_from_review_count(review_count: int) -> str:
    """Determine mastery level from review count."""
    if review_count == 0:
        return MASTERY_NEW
    elif review_count <= 2:
        return MASTERY_LEARNING
    elif review_count <= 5:
        return MASTERY_REVIEWING
    else:
        return MASTERY_MASTERED


async def _utc_window_of_local_yesterday(db: AsyncSession, user_id: str) -> tuple[datetime, datetime]:
    """UTC bounds of *yesterday* on the user's local calendar.

    Day boundary from the single authority in ``app.services.local_time``
    (BUG-16 / DEC-079) — same basis as rounds and daily counters, so the
    queue's "昨天错过的优先" cannot drift from them.
    """
    tz_name = (
        await db.execute(select(UserPreferences.reminder_timezone).where(UserPreferences.user_id == user_id))
    ).scalar_one_or_none()
    tz = resolve_user_timezone(tz_name)
    now_local = datetime.now(tz)
    today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    return yesterday_start.astimezone(UTC), today_start.astimezone(UTC)


def apply_review(vocab: Vocabulary, quality: int, now: datetime | None = None) -> tuple[int, datetime]:
    """Apply one answer to ``vocab`` in place (error-count bands, DEC-057).

    Returns ``(interval_days, next_review_at)`` — the next review time is handed
    back rather than re-read off the model so callers get a non-optional value
    (the column is nullable for words that were never scheduled).

    The single place that mutates a word's review state, so the drill's
    persisted round and ``POST /vocabulary/{id}/review`` can never drift apart.
    Mutates only — the caller owns the commit.

    Scheduling is ``sr_service.calculate_review_interval`` (DEC-057): a wrong
    answer — or a correct answer following a wrong one inside the current
    round — schedules 次日; otherwise the interval climbs the clean ladder
    (3→7→16→35) for never-wrong words or the error ladder (2→5→12→25) for
    words with ``wrong_count >= 1``, capped at 7 days once ``wrong_count >= 3``.
    ``wrong_count`` / ``last_wrong_at`` are written here on a wrong answer;
    ``ease_factor`` is left untouched (compat/display only). ``review_count``
    only ever grows — a wrong review must land the word back in the *review*
    queue tomorrow (mastery stays >= learning), not reset it to a new word,
    and must never graduate it (a wrong answer caps mastery at reviewing:
    mastered words are excluded from every queue, so the just-scheduled
    next-day review would never be reachable).
    """
    now = now or datetime.now(UTC)
    correct = quality >= 3
    # Three-level self-rating: quality 5 = 认识, 3 = 模糊, 1 = 不认识.
    # The middle bucket is still "correct" for mastery/wrong_count purposes,
    # but schedules its own two-day interval instead of climbing the ladder.
    hard = quality == 3
    wrong_count = vocab.wrong_count or 0

    wrong_recent = False
    if vocab.last_wrong_at is not None:
        last_wrong = vocab.last_wrong_at
        # SQLite round-trips datetimes naive; wall-clock math needs a zone.
        if last_wrong.tzinfo is None:
            last_wrong = last_wrong.replace(tzinfo=UTC)
        wrong_recent = now - last_wrong < WRONG_RECENT_WINDOW

    interval_days = calculate_review_interval(
        correct=correct,
        wrong_count=wrong_count,
        interval_days=vocab.interval_days or 0,
        wrong_recent=wrong_recent,
        hard=hard,
    )
    next_review_at = now + timedelta(days=interval_days)

    vocab.review_count = (vocab.review_count or 0) + 1
    vocab.last_reviewed_at = now
    vocab.next_review_at = next_review_at
    vocab.interval_days = interval_days
    new_mastery = _mastery_from_review_count(vocab.review_count)
    if not correct and new_mastery == MASTERY_MASTERED:
        # 错词不得毕业：mastered 会被 build_daily_session 的复习队列排除，
        # 上面刚排好的「次日」永远轮不到，词会从训练队列里无声消失。
        new_mastery = MASTERY_REVIEWING
    vocab.mastery_level = new_mastery

    if correct:
        vocab.correct_count = (vocab.correct_count or 0) + 1
    else:
        vocab.wrong_count = wrong_count + 1
        vocab.last_wrong_at = now

    return interval_days, next_review_at


async def enrich_word(db: AsyncSession, vocabulary_id: str, user_id: str) -> Vocabulary | None:
    """Fetch a word from DB, call AI enrichment, persist results, return enriched word."""
    result = await db.execute(
        select(Vocabulary).where(
            Vocabulary.id == vocabulary_id,
            Vocabulary.user_id == user_id,
        )
    )
    vocab = result.scalar_one_or_none()
    if not vocab:
        return None

    enriched = await _get_ai().enrich_vocabulary_word(vocab.word, vocab.context_sentence)

    vocab.definition = enriched.get("definition", "")
    vocab.translation = enriched.get("translation", "")
    vocab.part_of_speech = enriched.get("part_of_speech", "")
    vocab.ipa = enriched.get("ipa", "")
    vocab.example_sentences = enriched.get("example_sentences", [])
    vocab.collocations = enriched.get("collocations", [])
    vocab.difficulty_level = enriched.get("difficulty_level", "B1")

    await commit_refresh(db, vocab)
    return vocab


async def get_stats(db: AsyncSession, user_id: str) -> dict:
    """Aggregate vocabulary statistics by mastery level."""
    now = datetime.now(UTC)

    stmt = (
        select(
            Vocabulary.mastery_level,
            func.count(Vocabulary.id),
        )
        .where(Vocabulary.user_id == user_id)
        .group_by(Vocabulary.mastery_level)
    )
    result = await db.execute(stmt)
    level_counts: dict[str, int] = {level: count for level, count in result.all()}

    # Mastered words have exited review (tri-state semantics) and don't
    # count toward the due queue.
    due_window = (Vocabulary.next_review_at.is_(None)) | (Vocabulary.next_review_at <= now)
    # Both due counters in one round trip: each is the same window with a
    # different mastery predicate, so aggregate FILTER expresses both without a
    # second statement. Same filters as build_daily_session's review queue —
    # new words are the learn queue, not review.
    due_count, due_review_count = (
        await db.execute(
            select(
                func.count(Vocabulary.id).filter(due_window, Vocabulary.mastery_level != MASTERY_MASTERED),
                func.count(Vocabulary.id).filter(
                    due_window,
                    Vocabulary.mastery_level != MASTERY_MASTERED,
                    Vocabulary.mastery_level != MASTERY_NEW,
                ),
            ).where(Vocabulary.user_id == user_id)
        )
    ).one()

    total = sum(level_counts.values())

    return {
        "total": total,
        "new_count": level_counts.get(MASTERY_NEW, 0),
        "learning_count": level_counts.get(MASTERY_LEARNING, 0),
        "reviewing_count": level_counts.get(MASTERY_REVIEWING, 0),
        "mastered_count": level_counts.get(MASTERY_MASTERED, 0),
        "due_count": due_count or 0,
        "due_review_count": due_review_count or 0,
    }


async def attach_word_sources(db: AsyncSession, words: list[Vocabulary]) -> list[dict]:
    """Serialize vocabulary rows with their video title and sentence time.

    The word table only stores ``video_id`` / ``subtitle_id``; the row wants
    "来源视频 · mm:ss". Two batch queries (no N+1) fill the display fields.
    Missing/deleted sources stay ``None`` — the UI shows the generic source
    link instead of inventing a title.
    """
    if not words:
        return []
    from app.models.subtitle import Subtitle
    from app.models.video import Video

    video_ids = {w.video_id for w in words if w.video_id}
    subtitle_ids = {w.subtitle_id for w in words if w.subtitle_id}
    titles: dict[str, str] = {}
    if video_ids:
        rows = (await db.execute(select(Video.id, Video.title, Video.title_zh).where(Video.id.in_(video_ids)))).all()
        titles = {vid: (zh or en or "") for vid, en, zh in rows}
    starts: dict[str, float] = {}
    if subtitle_ids:
        subtitle_rows = (
            await db.execute(select(Subtitle.id, Subtitle.start_time).where(Subtitle.id.in_(subtitle_ids)))
        ).all()
        starts = {sid: float(start) for sid, start in subtitle_rows}

    payloads: list[dict] = []
    for word in words:
        item = VocabularyResponse.model_validate(word).model_dump()
        item["video_title"] = titles.get(word.video_id or "")
        item["subtitle_start_time"] = starts.get(word.subtitle_id or "")
        payloads.append(item)
    return payloads


async def build_daily_session(
    db: AsyncSession,
    user_id: str,
    new_count: int,
    review_count: int,
) -> dict:
    """Compose the 今日训练 queue: new words (never reviewed) + due words.

    New words are ``mastery_level == new`` ordered oldest-first so words the
    user saved earliest get learned first. Due words follow the S6 priority
    (DEC-057): words whose last wrong answer was *yesterday* (user-local day)
    come first — 昨天错得最多的词第一屏出现 — then ``wrong_count`` descending,
    then ``next_review_at`` ascending. Mastered words never appear in the
    review queue (tri-state semantics, same as get_stats).

    Both counts are required: the caller resolves them from the user's daily
    quota (``UserLearningProfile.daily_new_target`` / ``daily_review_target``,
    DEC-053) and only overrides them when an explicit request asks for it.
    """
    now = datetime.now(UTC)

    new_stmt = (
        select(Vocabulary)
        .where(Vocabulary.user_id == user_id, Vocabulary.mastery_level == MASTERY_NEW)
        .order_by(Vocabulary.created_at.asc())
        .limit(new_count)
    )
    new_words = (await db.execute(new_stmt)).scalars().all()

    wrong_yesterday_start, wrong_yesterday_end = await _utc_window_of_local_yesterday(db, user_id)
    wrong_yesterday = (Vocabulary.last_wrong_at >= wrong_yesterday_start) & (
        Vocabulary.last_wrong_at < wrong_yesterday_end
    )
    review_stmt = (
        select(Vocabulary)
        .where(
            Vocabulary.user_id == user_id,
            (Vocabulary.next_review_at == None) | (Vocabulary.next_review_at <= now),
            Vocabulary.mastery_level != MASTERY_MASTERED,
            Vocabulary.mastery_level != MASTERY_NEW,
        )
        .order_by(
            case((wrong_yesterday, 0), else_=1).asc(),
            Vocabulary.wrong_count.desc(),
            Vocabulary.next_review_at.asc().nulls_first(),
        )
        .limit(review_count)
    )
    review_words = (await db.execute(review_stmt)).scalars().all()

    new_total = (
        await db.execute(
            select(func.count(Vocabulary.id)).where(
                Vocabulary.user_id == user_id,
                Vocabulary.mastery_level == MASTERY_NEW,
            )
        )
    ).scalar() or 0
    # Due total mirrors the review queue: new words are the *learn* queue, not
    # review (differs from stats.due_count, which folds new words into the
    # badge number).
    due_total = (
        await db.execute(
            select(func.count(Vocabulary.id)).where(
                Vocabulary.user_id == user_id,
                (Vocabulary.next_review_at == None) | (Vocabulary.next_review_at <= now),
                Vocabulary.mastery_level != MASTERY_MASTERED,
                Vocabulary.mastery_level != MASTERY_NEW,
            )
        )
    ).scalar() or 0

    return {
        "new_words": new_words,
        "review_words": review_words,
        "totals": {"new_total": new_total, "due_total": due_total},
    }
