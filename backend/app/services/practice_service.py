"""Vocabulary practice service — adaptive drill from the user's wordbook.

Generates practice items from the user's personal vocabulary list, with
adaptive difficulty based on SM-2 mastery level. All grading is client-side;
this service only generates items and accepts batch review submissions
(review-line words via the DEC-057 banded algorithm, new/auto-added words
via the frozen SM-2 update).

Question types by mastery:
  new / unknown → recognition  (listen_choose_meaning, see_word_choose_meaning)
  learning      → production   (see_meaning_spell_word, listen_spell_word)
  reviewing / mastered → context (sentence_repeat with the saved context)

Note: the video-scoped practice engine (build_unified_drill / context-fill
generation) was removed when the 试题功能 was taken offline (2026-08); the
video practice endpoints no longer exist. Only the vocabulary drill remains.
"""

import logging
import random
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.core.exam_levels import should_display
from app.models.learning import Vocabulary
from app.models.subtitle import Subtitle
from app.services import ecdict
from app.services.sr_service import calculate_next_review
from app.services.vocabulary_service import MASTERY_LEARNING, MASTERY_REVIEWING, apply_logged_review

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Mastery → category mapping
MASTERY_TO_CATEGORY = {
    "new": "recognition",
    "learning": "production",
    "reviewing": "context",
    "mastered": "context",
}

# Category → possible types (randomly selected)
CATEGORY_TYPES = {
    "recognition": ["listen_choose_meaning", "see_word_choose_meaning"],
    "production": ["see_meaning_spell_word", "listen_spell_word"],
    "context": ["context_fill"],
}


def shuffle_options(options: list[str]) -> None:
    """Shuffle options in place so the correct answer position is random."""
    if len(options) < 2:
        return
    random.shuffle(options)


# ---------------------------------------------------------------------------
# Distractor selection (S4, 设计文档 §8)
# ---------------------------------------------------------------------------

# Options are fixed at 4 (1 correct + DISTRACTOR_COUNT distractors). A question
# with fewer than 2 usable distractors is emitted with options=None instead.
DISTRACTOR_COUNT = 3

# Priority-2 candidates (wordbook-wide) must sit 2~4 edits from the target
# word — close enough to confuse (affect/effect), far enough not to be it (§8.2).
EDIT_DISTANCE_MIN = 2
EDIT_DISTANCE_MAX = 4

# ECDICT pos codes and full-word POS spellings → canonical token. Both sides of
# a comparison go through the same normalizer, so the exact choice is invisible.
_POS_ALIASES = {
    "noun": "n",
    "verb": "v",
    "adjective": "a",
    "adj": "a",
    "adverb": "ad",
    "adv": "ad",
    "preposition": "prep",
    "prep": "prep",
    "conjunction": "conj",
    "conj": "conj",
    "pronoun": "pron",
    "pron": "pron",
    "interjection": "int",
    "interj": "int",
    "numeral": "num",
    "num": "num",
}


@dataclass
class DistractorCandidate:
    """One distractor source word, normalized for selection."""

    word: str
    translation: str  # concise (single-line) display translation
    pos: frozenset[str] = frozenset()
    levels: frozenset[str] = frozenset()
    video_id: str | None = None
    bnc: int = 0  # BNC frequency rank; lower = more common (0 = unknown)


def _pos_tokens(pos: str | None) -> frozenset[str]:
    """Parse ECDICT-style pos ("n:46/v:32") or full words ("noun/verb") into tokens."""
    if not pos:
        return frozenset()
    tokens: set[str] = set()
    for tok in re.split(r"[/\s,;，；、]+", pos):
        tok = tok.strip().lower().rstrip(".")
        if not tok:
            continue
        head = tok.split(":", 1)[0] if ":" in tok else tok
        if head:
            tokens.add(_POS_ALIASES.get(head, head))
    return frozenset(tokens)


def _concise_translation(translation: str | None) -> str:
    """First line of a (possibly multi-line, multi-POS) translation string."""
    if not translation:
        return ""
    lines = [ln.strip() for ln in translation.strip().splitlines() if ln.strip()]
    return lines[0] if lines else ""


def _translation_key(translation: str) -> str:
    """Normalization for equality/containment checks between translations.

    Compares the CJK content when present (options are Chinese meanings), so
    POS markers and punctuation cannot mask duplicates; falls back to a stripped
    lowercase form otherwise.
    """
    cjk = "".join(ch for ch in translation if "\u4e00" <= ch <= "\u9fff")
    if cjk:
        return cjk
    return re.sub(r"[\W_]+", "", translation, flags=re.UNICODE).lower()


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if abs(len(a) - len(b)) > EDIT_DISTANCE_MAX:
        return EDIT_DISTANCE_MAX + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _matches_pos_level(
    target_word: str,
    target_pos: frozenset[str],
    target_levels: frozenset[str],
    cand: DistractorCandidate,
) -> bool:
    """§8.2 quality gate: same POS (or, when POS is unknown on both sides, the
    same length bucket) and same exam level. Unknown data on exactly one side
    stays lenient — the candidate remains eligible and relies on pool priority."""
    if target_pos and cand.pos:
        if not (target_pos & cand.pos):
            return False
    elif not target_pos and not cand.pos:
        if abs(len(target_word) - len(cand.word)) > 2:
            return False
    if target_levels and cand.levels and not (target_levels & cand.levels):
        return False
    return True


def select_distractors(
    target_word: str,
    correct_translation: str,
    same_video: list[DistractorCandidate],
    vocab_rest: list[DistractorCandidate],
    ecdict_pool: list[DistractorCandidate] | None = None,
    target_pos: frozenset[str] = frozenset(),
    target_levels: frozenset[str] = frozenset(),
) -> list[str]:
    """Pick up to ``DISTRACTOR_COUNT`` distractor translations for one question.

    Priority ladder (设计文档 §8.2):
      1. same video + same level + same POS, from the user's wordbook;
      2. wordbook-wide, same level + POS, edit distance 2~4;
      3. ECDICT exam words, same level + POS, high-frequency (low BNC) first;
      4. relaxation pass without POS/level/edit-distance constraints so the
         question can still be built.

    Hard constraints (§8.3): candidates equal to the target word are dropped,
    translations are deduped, and anything equal to or overlapping the correct
    translation (synonym/containment) is excluded. Returns at most 3 concise
    translation strings; the caller combines them with the correct answer.
    """
    correct_key = _translation_key(correct_translation)
    if not correct_key:
        return []
    seen: set[str] = {correct_key}
    distractors: list[str] = []
    target_lower = target_word.lower()

    def take(pool: list[DistractorCandidate], *, check_pos_level: bool, check_edit: bool, sort_by_bnc: bool) -> None:
        if len(distractors) >= DISTRACTOR_COUNT:
            return
        matches = [c for c in pool if c.translation and c.word.lower() != target_lower]
        if check_edit:
            matches = [
                c
                for c in matches
                if EDIT_DISTANCE_MIN <= _levenshtein(c.word.lower(), target_lower) <= EDIT_DISTANCE_MAX
            ]
        if check_pos_level:
            matches = [c for c in matches if _matches_pos_level(target_word, target_pos, target_levels, c)]
        # Shuffle first so equal-priority candidates rotate between questions;
        # the stable bnc sort then only orders across frequency tiers.
        random.shuffle(matches)
        if sort_by_bnc:
            matches.sort(key=lambda c: c.bnc)
        for cand in matches:
            if len(distractors) >= DISTRACTOR_COUNT:
                break
            key = _translation_key(cand.translation)
            if not key or key in seen:
                continue
            if correct_key in key or key in correct_key:
                continue
            seen.add(key)
            distractors.append(cand.translation)

    take(same_video, check_pos_level=True, check_edit=False, sort_by_bnc=False)
    take(vocab_rest, check_pos_level=True, check_edit=True, sort_by_bnc=False)
    take(ecdict_pool or [], check_pos_level=True, check_edit=False, sort_by_bnc=True)
    take([*same_video, *vocab_rest, *(ecdict_pool or [])], check_pos_level=False, check_edit=False, sort_by_bnc=False)
    return distractors


async def _load_distractor_candidates(
    db: AsyncSession, user_id: str, video_id: str | None
) -> tuple[list[DistractorCandidate], list[DistractorCandidate]]:
    """Build the wordbook-wide distractor pools: ``(same_video, rest)``.

    Levels/POS prefer the ECDICT entry (authoritative exam tags); rows the
    dictionary does not know fall back to the stored ``part_of_speech``.
    """
    rows = (
        await db.execute(
            select(Vocabulary.word, Vocabulary.translation, Vocabulary.part_of_speech, Vocabulary.video_id).where(
                Vocabulary.user_id == user_id
            )
        )
    ).all()
    same_video: list[DistractorCandidate] = []
    rest: list[DistractorCandidate] = []
    for word, translation, pos, vid in rows:
        entry = ecdict.lookup(word)
        cand = DistractorCandidate(
            word=word,
            translation=_concise_translation(translation),
            pos=_pos_tokens(entry.get("pos")) if entry else _pos_tokens(pos),
            levels=frozenset(entry.get("levels") or []) if entry else frozenset(),
            video_id=vid,
            bnc=entry["bnc"] if entry and isinstance(entry.get("bnc"), int) else 0,
        )
        if not cand.translation:
            continue
        if video_id and vid == video_id:
            same_video.append(cand)
        else:
            rest.append(cand)
    return same_video, rest


def _ecdict_candidates(target_levels: frozenset[str]) -> list[DistractorCandidate]:
    """ECDICT fallback pool (priority 3): exam words only, level-filtered when
    the drill's target words carry known levels. Empty when ECDICT is absent."""
    pool: list[DistractorCandidate] = []
    for entry in ecdict.entries():
        levels = frozenset(entry["levels"])
        if target_levels and levels and not (levels & target_levels):
            continue
        translation = _concise_translation(entry["translation"])
        if not translation:
            continue
        pool.append(
            DistractorCandidate(
                word=entry["lemma"],
                translation=translation,
                pos=_pos_tokens(entry["pos"]),
                levels=levels,
                bnc=entry["bnc"] if isinstance(entry.get("bnc"), int) else 0,
            )
        )
    return pool


# ---------------------------------------------------------------------------
# Item builders (one per category)
# ---------------------------------------------------------------------------


def _build_recognition_item(word: str, translation: str, phonetic: str, distractors: list[str]) -> dict:
    """Build a recognition item (listen_choose_meaning or see_word_choose_meaning)."""
    item_type = random.choice(CATEGORY_TYPES["recognition"])

    # Options carry the concise (single-line) translation strings; the answer is
    # the exact option string so client-side grading compares like with like.
    concise = _concise_translation(translation)
    options = None
    if concise and len(distractors) >= 2:
        options = [*distractors, concise]
        shuffle_options(options)

    return {
        "word": word,
        "category": "recognition",
        "type": item_type,
        "translation": translation,
        "options": options,
        "answer": concise or translation,
        "phonetic": phonetic,
    }


def _build_production_item(word: str, translation: str, phonetic: str) -> dict:
    """Build a production item (see_meaning_spell_word or listen_spell_word)."""
    item_type = random.choice(CATEGORY_TYPES["production"])

    return {
        "word": word,
        "category": "production",
        "type": item_type,
        "translation": translation,
        "options": None,
        "answer": word,
        "phonetic": phonetic,
    }


def _build_context_item(
    word: str,
    translation: str,
    phonetic: str,
    full_sentence: str,
    start_time: float | None,
    end_time: float | None,
) -> dict:
    """Build a spelling question from the saved source sentence."""
    if not re.search(r"\b" + re.escape(word) + r"\b", full_sentence, flags=re.IGNORECASE):
        return _build_production_item(word, translation, phonetic)
    return {
        "word": word,
        "category": "context",
        "type": "context_fill",
        "sentence_template": re.sub(r"\b" + re.escape(word) + r"\b", "___", full_sentence, flags=re.IGNORECASE),
        "translation": translation,
        "options": None,
        "answer": word,
        "full_sentence": full_sentence,
        "start_time": start_time,
        "end_time": end_time,
        "phonetic": phonetic,
    }


# ---------------------------------------------------------------------------
# Core: build vocabulary-scoped drill (for /vocabulary page)
# ---------------------------------------------------------------------------


async def build_vocabulary_drill(
    db: AsyncSession,
    user_id: str,
    target_level: str | None = None,
    count: int = 10,
    due_only: bool = False,
    video_id: str | None = None,
) -> list[dict]:
    """Build adaptive practice items from the user's personal vocabulary list.

    Item types are chosen based on each word's SM-2 mastery level.
    All grading is client-side.

    When ``video_id`` is provided, the candidate pool is restricted to words
    the user added while watching that video, and each emitted item carries
    ``video_id`` / ``subtitle_id`` / ``start_time`` so the frontend can build
    a "回看原句" deep link (D3b). Words without a subtitle source still appear,
    just without those fields.

    Raises:
        ValueError: no vocabulary words available
    """
    now = datetime.now(UTC)
    stmt = select(Vocabulary).where(Vocabulary.user_id == user_id)

    if due_only:
        # Mastered words exited the review loop (tri-state semantics) — due
        # drills must not resurrect them.
        stmt = stmt.where(
            ((Vocabulary.next_review_at == None) | (Vocabulary.next_review_at <= now)),
            Vocabulary.mastery_level != "mastered",
        )

    if video_id:
        stmt = stmt.where(Vocabulary.video_id == video_id)

    stmt = stmt.order_by(Vocabulary.created_at.desc()).limit(count * 3)
    result = await db.execute(stmt)
    words = result.scalars().all()

    if not words:
        # 409 是既有线上行为（router 层过去把这两条 ValueError 一律映射成 409），
        # 批 1c 只搬「谁决定状态码」，不动状态码本身；语义上 400 也说得通，但改
        # 它是另一次改动（契约变更），不夹在重构里做。
        if video_id:
            raise ConflictError("该视频还没有生词，去看视频时点击字幕里的单词就能加入词汇本")
        raise ConflictError("词汇本为空，请先在学习中添加词汇")

    # Filter by target exam level when requested. Words whose ECDICT lookup
    # levels pass should_display() are preferred; if too few match we top up
    # from non-matches so practice still works (e.g. words missing from ECDICT
    # or a level the user hasn't annotated for). Without this the vocabulary
    # drill ignored `target_level` entirely — every level saw the same words.
    if target_level and ecdict.is_available():
        matches: list = []
        misses: list = []
        for w in words:
            entry = ecdict.lookup(w.word)
            levels = entry["levels"] if entry else []
            (matches if should_display(levels, target_level) else misses).append(w)
        if matches:
            # Enough level matches → restrict to them; only top up with misses
            # when matches alone can't fill the requested count.
            words = matches if len(matches) >= count else matches + misses

    # Prefer enriched words
    enriched = [w for w in words if w.definition and w.translation]
    if len(enriched) >= count:
        selected = enriched[:count]
    else:
        unenriched = [w for w in words if not (w.definition and w.translation)]
        selected = (enriched + unenriched)[:count]

    # Distractor pools (S4): priority 1/2 come from the user's wordbook
    # (same-video first), priority 3 from ECDICT exam words. Built once per
    # drill; per-word filtering happens in select_distractors.
    same_video_pool, vocab_pool = await _load_distractor_candidates(db, user_id, video_id)
    drill_target_levels = frozenset(
        level for w in selected for level in ((ecdict.lookup(w.word) or {}).get("levels") or [])
    )
    ecdict_pool = _ecdict_candidates(drill_target_levels)

    # Phase 1 D3b: when video_id is set, batch-join Subtitle for the
    # start_time so items can deep-link "回看原句" back to the source cue.
    subtitle_starts: dict[str, float] = {}
    if video_id:
        sub_ids = [w.subtitle_id for w in selected if w.subtitle_id]
        if sub_ids:
            sub_rows = (await db.execute(select(Subtitle).where(Subtitle.id.in_(sub_ids)))).scalars().all()
            subtitle_starts = {s.id: s.start_time for s in sub_rows}

    items: list[dict] = []
    for w in selected:
        word = w.word
        translation = w.translation or ""
        phonetic = w.ipa or ""
        mastery = w.mastery_level or "new"
        category = MASTERY_TO_CATEGORY.get(mastery, "recognition")

        if category == "recognition":
            entry = ecdict.lookup(word)
            item = _build_recognition_item(
                word,
                translation,
                phonetic,
                select_distractors(
                    target_word=word,
                    correct_translation=translation,
                    same_video=same_video_pool,
                    vocab_rest=vocab_pool,
                    ecdict_pool=ecdict_pool,
                    target_pos=_pos_tokens(entry.get("pos")) if entry else _pos_tokens(w.part_of_speech),
                    target_levels=frozenset(entry.get("levels") or []) if entry else frozenset(),
                ),
            )
        elif category == "production":
            item = _build_production_item(word, translation, phonetic)
        elif category == "context":
            # For vocabulary page, use sentence_repeat with context_sentence if available
            if w.context_sentence:
                start = subtitle_starts.get(w.subtitle_id) if w.subtitle_id else None
                item = _build_context_item(
                    word=word,
                    translation=translation,
                    phonetic=phonetic,
                    full_sentence=w.context_sentence,
                    start_time=start,
                    end_time=None,
                )
            else:
                # Fall back to production (spelling)
                item = _build_production_item(word, translation, phonetic)
        else:
            continue

        # Phase 1 D3b: attach source metadata for "回看原句" deep linking.
        if video_id and w.subtitle_id:
            start = subtitle_starts.get(w.subtitle_id)
            item["video_id"] = w.video_id or video_id
            item["subtitle_id"] = w.subtitle_id
            if start is not None:
                item["start_time"] = float(start)
        items.append(item)

    return items


# ---------------------------------------------------------------------------
# Core: submit practice results → review-state update
# ---------------------------------------------------------------------------


async def submit_practice_results(
    db: AsyncSession,
    user_id: str,
    results: list[dict],
    video_id: str | None = None,
    flow_id: str | None = None,
) -> dict:
    """Batch-submit practice results and update each word's review state.

    For each {word, correct}:
      1. Look up Vocabulary row. If not found, auto-add.
      2. quality = 5 if correct, 2 if wrong.
      3. Review-line words (``mastery_level`` learning/reviewing — the due
         words the drill's merged loop submits here, S5) go through
         ``vocabulary_service.apply_logged_review``: error-count banded scheduling
         plus ``wrong_count`` / ``last_wrong_at`` bookkeeping (DEC-057).
      4. Everything else — auto-added and still-``new`` words from the
         video-scoped drill — keeps the frozen SM-2 update below.

    Returns:
        {"updated": N, "auto_added": M}
    """
    now = datetime.now(UTC)
    updated = 0
    auto_added = 0
    # Lock existing words in a stable order before mutating the batch. A
    # concurrent batch submitted in reverse order must not invert row locks.
    await db.execute(
        select(Vocabulary)
        .where(Vocabulary.user_id == user_id, Vocabulary.word.in_([r["word"] for r in results]))
        .order_by(Vocabulary.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )

    for r in results:
        word = r["word"]
        correct = r["correct"]
        quality = 5 if correct else 2

        # Look up existing vocabulary row
        result = await db.execute(
            select(Vocabulary).where(
                Vocabulary.user_id == user_id,
                Vocabulary.word == word,
            )
        )
        vocab = result.scalar_one_or_none()

        if not vocab:
            # Auto-add word to vocabulary. ecdict's ``pos`` can be a long
            # multi-tag string (e.g. "i:10/n:1/r:87/j:1/v:1") that exceeds the
            # String(20) column, so truncate to fit and avoid a flush error.
            entry = ecdict.lookup(word)
            raw_pos = entry.get("pos", "") if entry else ""
            vocab = Vocabulary(
                user_id=user_id,
                word=word[:100],
                translation=(entry["translation"] if entry else "")[:500],
                definition=entry.get("definition", "") if entry else "",
                part_of_speech=raw_pos[:20],
                ipa=(entry.get("phonetic", "") if entry else "")[:100],
                video_id=video_id,
                mastery_level="new",
                review_count=0,
                ease_factor=2.5,
                interval_days=0,
            )
            db.add(vocab)
            await db.flush()
            auto_added += 1

        if vocab.mastery_level in (MASTERY_LEARNING, MASTERY_REVIEWING):
            # 到期复习词：错误次数分档（DEC-057）。wrong_count / last_wrong_at
            # 由复习服务统一落库；caller owns the commit（循环尾统一 commit）。
            await apply_logged_review(db, vocab, quality, source="practice", now=now)
            updated += 1
            continue

        # Update SM-2 (frozen legacy path: new / auto-added words outside study rounds)
        current_ef = vocab.ease_factor if vocab.ease_factor else 2.5

        if vocab.review_count > 0:
            if vocab.interval_days and vocab.interval_days > 0:
                interval_days = vocab.interval_days
            elif vocab.last_reviewed_at and vocab.next_review_at:
                interval_days = max((vocab.next_review_at - vocab.last_reviewed_at).days, 1)
            else:
                interval_days = 0
        else:
            interval_days = 0

        next_interval, new_ef, new_review_count = calculate_next_review(
            quality, vocab.review_count, current_ef, interval_days
        )

        vocab.review_count = new_review_count
        vocab.last_reviewed_at = now
        vocab.next_review_at = now + timedelta(days=next_interval)
        vocab.ease_factor = new_ef
        vocab.interval_days = next_interval
        # Mastered words left the review loop (tri-state); a later practice
        # answer must not re-derive (and demote) their level.
        if vocab.mastery_level != "mastered":
            vocab.mastery_level = _mastery_from_review_count(new_review_count)
        if correct:
            vocab.correct_count = (vocab.correct_count or 0) + 1
        updated += 1

    from app.services.learning_event_service import EVENT_LEARNED_WORDS, EVENT_PRACTICED_ITEMS, record_event

    correct_count = sum(1 for r in results if r.get("correct"))
    await record_event(
        db, user_id, EVENT_PRACTICED_ITEMS, len(results), video_id=video_id, flow_id=flow_id, source="practice"
    )
    if correct_count > 0:
        await record_event(
            db, user_id, EVENT_LEARNED_WORDS, correct_count, video_id=video_id, flow_id=flow_id, source="practice"
        )
    await db.commit()

    return {"updated": updated, "auto_added": auto_added}


def _mastery_from_review_count(review_count: int) -> str:
    """Determine mastery level from review count."""
    if review_count == 0:
        return "new"
    elif review_count <= 2:
        return "learning"
    elif review_count <= 5:
        return "reviewing"
    else:
        return "mastered"
