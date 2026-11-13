from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import commit_refresh, get_db
from app.core.limiter import rate_limit
from app.models.learning import Vocabulary
from app.models.user import User
from app.schemas.pagination import PaginatedResponse, PaginationParams, paginated
from app.schemas.vocabulary import (
    DailySessionResponse,
    LearningWordsResponse,
    StudySessionAnswerRequest,
    StudySessionAnswerResponse,
    StudySessionEnvelope,
    StudySessionItemResponse,
    StudySessionResponse,
    StudySessionStartRequest,
    TodayTrainingSummary,
    VocabularyAddResponse,
    VocabularyDeleteResponse,
    VocabularyEnrichResponse,
    VocabularyMasteredResponse,
    VocabularyPracticeResponse,
    VocabularyPreferencesResponse,
    VocabularyPreferencesUpdate,
    VocabularyResponse,
    VocabularyReviewResponse,
    VocabularyStatsResponse,
    WatchContextResponse,
    WatchContextVocabSet,
)
from app.services import ecdict, practice_service, study_session_service, vocabulary_service

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


# ---------------------------------------------------------------------------
# Schemas for unified practice submit
# ---------------------------------------------------------------------------


class VocabPracticeResultItem(BaseModel):
    word: str
    correct: bool


class VocabPracticeSubmitRequest(BaseModel):
    results: list[VocabPracticeResultItem]
    #: A12：本轮练习的客户端 flow id。服务端用它把这批结果写成一条带 flow_id
    #: 的学习事件，客户端同 id 的 flow_result 意图事件因此可对账（丢失率/重复率）。
    flow_id: str | None = Field(None, max_length=36)


class VocabPracticeSubmitResponse(BaseModel):
    updated: int
    auto_added: int


# ---------------------------------------------------------------------------
# Serialisation helpers for study rounds
# ---------------------------------------------------------------------------


def _session_response(
    session,
    rows,
) -> StudySessionResponse:
    """Build a round payload from its ORM row plus (item, word) pairs.

    Items whose vocabulary row is gone are dropped rather than rendered blank;
    they still count toward ``target_count`` (the quota snapshot), which is
    why ``done_count``/``target_count`` can legitimately disagree.
    """
    items = [
        StudySessionItemResponse(
            id=item.id,
            vocabulary_id=item.vocabulary_id,
            sort_order=item.sort_order,
            correct_streak=item.correct_streak,
            wrong_in_round=item.wrong_in_round,
            status=item.status,
            word=VocabularyResponse.model_validate(word),
        )
        for item, word in rows
    ]
    return StudySessionResponse(
        id=session.id,
        kind=session.kind,
        local_date=session.local_date,
        target_count=session.target_count,
        done_count=session.done_count,
        correct_count=session.correct_count,
        status=session.status,
        items=items,
    )


async def _today_summary(db: AsyncSession, user_id: str) -> TodayTrainingSummary:
    return TodayTrainingSummary(**await study_session_service.get_today_summary(db, user_id))


# ---------------------------------------------------------------------------
# Static-path routes (must come before /{word_id} to avoid path collision)
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=VocabularyStatsResponse)
@rate_limit("30/minute")
async def vocabulary_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get vocabulary statistics by mastery level."""
    return await vocabulary_service.get_stats(db, current_user.id)


@router.get("/daily-session", response_model=DailySessionResponse)
@rate_limit("30/minute")
async def get_daily_session(
    request: Request,
    new_count: int | None = Query(None, ge=1, le=100, description="Override the user's daily new-word quota"),
    review_count: int | None = Query(None, ge=1, le=100, description="Override the user's daily review quota"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """今日训练队列：新词（从未复习）+ 到期复习词，附总量统计。

    Powers the Baicizhan-style /vocabulary home + /vocabulary/drill two-phase
    flow (learn flashcards, then due review quiz).

    Queue sizes come from the user's daily quota (DEC-053) unless the caller
    overrides them explicitly. The response also carries ``preferences`` and
    ``today`` so the 今日 tab renders the quota picker and 今日已学 without a
    second round trip.
    """
    prefs = await study_session_service.get_preferences(db, current_user.id)
    session = await vocabulary_service.build_daily_session(
        db,
        current_user.id,
        new_count if new_count is not None else prefs["daily_new_target"],
        review_count if review_count is not None else prefs["daily_review_target"],
    )
    active_id, training_new = await study_session_service.preview_new_words(
        db, current_user.id, prefs["daily_new_target"]
    )
    active_word_ids = set()
    if active_id:
        active_word_ids = {word.id for _, word in await study_session_service.session_rows(db, active_id)}
    review_words = [w for w in session["review_words"] if w.id not in active_word_ids]
    return {
        "training_preview": {
            "active_session_id": active_id,
            "new_words": await vocabulary_service.attach_word_sources(db, training_new),
            "review_words": await vocabulary_service.attach_word_sources(db, review_words),
        },
        "new_words": await vocabulary_service.attach_word_sources(db, session["new_words"]),
        "review_words": await vocabulary_service.attach_word_sources(db, session["review_words"]),
        "totals": session["totals"],
        "preferences": VocabularyPreferencesResponse(
            **prefs,
            quota_min=study_session_service.QUOTA_MIN,
            quota_max=study_session_service.QUOTA_MAX,
        ),
        "today": await _today_summary(db, current_user.id),
    }


@router.get("/preferences", response_model=VocabularyPreferencesResponse)
@rate_limit("30/minute")
async def get_vocabulary_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """每日训练配额（全局一个设置，不是每个视频一个）。"""
    prefs = await study_session_service.get_preferences(db, current_user.id)
    return VocabularyPreferencesResponse(
        **prefs,
        quota_min=study_session_service.QUOTA_MIN,
        quota_max=study_session_service.QUOTA_MAX,
    )


@router.put("/preferences", response_model=VocabularyPreferencesResponse)
@rate_limit("20/minute")
async def update_vocabulary_preferences(
    request: Request,
    body: VocabularyPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set the daily quota (5~100). Omitted fields are left untouched.

    Only affects rounds started *after* the change: a round snapshots the
    quota it was created with, so raising the number mid-round does not
    silently resize a round the user is already working through.
    """
    prefs = await study_session_service.set_preferences(
        db,
        current_user.id,
        daily_new_target=body.daily_new_target,
        daily_review_target=body.daily_review_target,
    )
    return VocabularyPreferencesResponse(
        **prefs,
        quota_min=study_session_service.QUOTA_MIN,
        quota_max=study_session_service.QUOTA_MAX,
    )


@router.get("/sessions/current", response_model=StudySessionEnvelope)
@rate_limit("60/minute")
async def get_current_study_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """今日未完成的一轮训练，没有则 ``session`` 为 null。

    Read-only on purpose: the drill opens a round explicitly via POST so a
    page load never writes.
    """
    session = await study_session_service.get_active_session(db, current_user.id)
    rows = await study_session_service.session_rows(db, session.id) if session else []
    return StudySessionEnvelope(
        session=_session_response(session, rows) if session else None,
        today=await _today_summary(db, current_user.id),
    )


@router.post("/sessions", response_model=StudySessionEnvelope)
@rate_limit("20/minute")
async def start_study_session(
    request: Request,
    body: StudySessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取或建当前轮：有未完成的一轮就续上，否则按配额开新的一轮。

    ``kind=extra`` 是加练：同配额、再取 ``mastery_level = new`` 的词，计入今日
    累计但不计入今日目标。调用方必须先结束当前轮，否则拿到的是当前轮本身
    （幂等，防止重复挂载开出两轮）。
    """
    result = await study_session_service.start_session(db, current_user.id, body.kind)
    return StudySessionEnvelope(
        session=_session_response(result["session"], result["items"]) if result["session"] else None,
        today=await _today_summary(db, current_user.id),
    )


@router.post("/sessions/{session_id}/answer", response_model=StudySessionAnswerResponse)
@rate_limit("120/minute")
async def answer_study_session(
    request: Request,
    session_id: str,
    body: StudySessionAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """一轮里的一次作答：更新该词在本轮的连对计数 + 该词的 SM-2 状态。

    一次作答只写 1~2 行 UPDATE（词在本轮的行 + 词自身的行），并发出一次
    ``learned_words`` 学习事件（首次作答该词时），让今日累计真的长起来。
    """
    result = await study_session_service.submit_answer(
        db,
        current_user.id,
        session_id,
        body.vocabulary_id,
        body.correct,
    )

    item, word = (result["item"], None)
    rows = await study_session_service.session_rows(db, session_id)
    for row_item, row_word in rows:
        if row_item.id == item.id:
            word = row_word
            break

    return StudySessionAnswerResponse(
        item=StudySessionItemResponse(
            id=item.id,
            vocabulary_id=item.vocabulary_id,
            sort_order=item.sort_order,
            correct_streak=item.correct_streak,
            wrong_in_round=item.wrong_in_round,
            status=item.status,
            word=VocabularyResponse.model_validate(word) if word else None,
        ),
        session_id=result["session"].id,
        done_count=result["session"].done_count,
        correct_count=result["session"].correct_count,
        target_count=result["session"].target_count,
        session_status=result["session"].status,
        graduated=result["graduated"],
        today=await _today_summary(db, current_user.id),
    )


@router.post("/sessions/{session_id}/finish", response_model=StudySessionEnvelope)
@rate_limit("20/minute")
async def finish_study_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """结束一轮（总结页到达时调用）。顺带清理该用户 30 天前的轮次明细。"""
    session = await study_session_service.finish_session(db, current_user.id, session_id)

    rows = await study_session_service.session_rows(db, session.id)
    return StudySessionEnvelope(
        session=_session_response(session, rows),
        today=await _today_summary(db, current_user.id),
    )


@router.get("/practice", response_model=VocabularyPracticeResponse)
@rate_limit("10/minute")
async def get_vocabulary_practice(
    request: Request,
    level: str | None = Query(None, description="Target exam level key"),
    count: int = Query(10, ge=1, le=30),
    due_only: bool = Query(False, description="Only include words due for review"),
    video_id: str | None = Query(None, description="Restrict drill to words from this video (D3b)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate adaptive practice items from the user's vocabulary list.

    Item types are chosen based on each word's SM-2 mastery level.
    All grading is client-side. When ``video_id`` is set, the candidate pool
    is restricted to that video's words and each item carries
    ``video_id`` / ``subtitle_id`` / ``start_time`` for the EndScreen's
    "复习本视频生词" deep link.
    """
    items = await practice_service.build_vocabulary_drill(db, current_user.id, level, count, due_only, video_id)

    return {"items": items}


@router.post("/practice/submit", response_model=VocabPracticeSubmitResponse)
@rate_limit("10/minute")
async def submit_vocabulary_practice(
    request: Request,
    body: VocabPracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch-submit vocabulary practice results and update SM-2 for each word.

    Words not yet in the user's vocabulary are auto-added.
    """
    try:
        result = await practice_service.submit_practice_results(
            db,
            current_user.id,
            [r.model_dump() for r in body.results],
            video_id=None,
            flow_id=body.flow_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交失败：{e}") from e

    return VocabPracticeSubmitResponse(**result)


# ---------------------------------------------------------------------------
# Dynamic-path routes
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=VocabularyAddResponse)
@rate_limit("20/minute")
async def add_word(
    request: Request,
    word: str,
    context_sentence: str | None = None,
    video_id: str | None = None,
    subtitle_id: str | None = Query(None, description="Source subtitle for D3b 回看原句"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a word to personal vocabulary."""
    if subtitle_id:
        from app.services.subtitle_context import resolve_context

        context_sentence = await resolve_context(db, current_user, video_id, subtitle_id)
    existing = await db.execute(
        select(Vocabulary).where(
            Vocabulary.user_id == current_user.id,
            Vocabulary.word == word.strip().lower(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Word already in vocabulary")

    vocab = Vocabulary(
        user_id=current_user.id,
        word=word.strip().lower(),
        context_sentence=context_sentence,
        video_id=video_id,
        subtitle_id=subtitle_id,
    )
    # 收词时就把 ECDICT 的释义/音标/词性/级别写进去（与词单建档同口径）。
    # 不在这里填，词库卡片和训练题会一直是「释义待补充」——收词那一刻用户其实
    # 已经看过释义，丢掉它等于让词库变成一张只有拼写的表。
    entry = ecdict.lookup(vocab.word)
    if entry:
        vocabulary_service.apply_ecdict_fields(vocab, entry)
    db.add(vocab)
    await commit_refresh(db, vocab)

    return {
        "id": vocab.id,
        "word": vocab.word,
        "context_sentence": vocab.context_sentence,
        "video_id": vocab.video_id,
        "subtitle_id": vocab.subtitle_id,
        "created_at": vocab.created_at.isoformat(),
    }


@router.get("", response_model=PaginatedResponse[VocabularyResponse])
@rate_limit("30/minute")
async def list_vocabulary(
    request: Request,
    due_only: bool = Query(False, description="Only show words due for review"),
    mastery: str | None = Query(
        None,
        description="Comma-separated mastery levels to include (new/learning/reviewing/mastered)",
    ),
    q: str | None = Query(
        None,
        description="Search word/translation/definition (case-insensitive substring)",
    ),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List vocabulary words with server-side filters + pagination.

    Filters (due_only / mastery / q) compose; all apply to both the page
    query and the total count so the pager stays correct. Stats
    (total/due/mastery) live in ``GET /vocabulary/stats``.
    """
    now = datetime.now(UTC)
    # Mastered words have exited the review loop (tri-state semantics) and
    # never appear in due queues, whatever next_review_at says.
    due_filter = ((Vocabulary.next_review_at == None) | (Vocabulary.next_review_at <= now)) & (
        Vocabulary.mastery_level != "mastered"
    )

    stmt = select(Vocabulary).where(Vocabulary.user_id == current_user.id)
    count_stmt = select(func.count(Vocabulary.id)).where(Vocabulary.user_id == current_user.id)
    if due_only:
        stmt = stmt.where(due_filter)
        count_stmt = count_stmt.where(due_filter)
    if mastery:
        # Same comma-separated convention as GET /vocabulary/words.
        levels = [lv.strip() for lv in mastery.split(",") if lv.strip()]
        if levels:
            stmt = stmt.where(Vocabulary.mastery_level.in_(levels))
            count_stmt = count_stmt.where(Vocabulary.mastery_level.in_(levels))
    if q and q.strip():
        like = f"%{q.strip()}%"
        search_filter = or_(
            Vocabulary.word.ilike(like),
            Vocabulary.translation.ilike(like),
            Vocabulary.definition.ilike(like),
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(Vocabulary.created_at.desc()).offset(pagination.offset).limit(pagination.page_size)
    words = list((await db.execute(stmt)).scalars().all())

    items = await vocabulary_service.attach_word_sources(db, words)
    return paginated(items, pagination, total=total)


@router.get("/{word_id}/enrich", response_model=VocabularyEnrichResponse)
@rate_limit("5/minute")
async def enrich_word(
    request: Request,
    word_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI enrichment for a vocabulary word."""
    vocab = await vocabulary_service.enrich_word(db, word_id, current_user.id)
    if not vocab:
        raise HTTPException(status_code=404, detail="Word not found")
    if not vocab.definition:
        raise HTTPException(
            status_code=502,
            detail="AI enrichment failed — could not generate word data",
        )
    return vocab


@router.post("/{word_id}/review", response_model=VocabularyReviewResponse)
@rate_limit("20/minute")
async def review_word(
    request: Request,
    word_id: str,
    quality: int = Query(..., ge=0, le=5, description="Self-assessment 0-5"),
    operation_id: str | None = Query(None, min_length=1, max_length=100, pattern=r"^\S+$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a review of a word (error-count banded scheduling, DEC-057).

    ``quality >= 3`` counts as correct; a wrong answer bumps ``wrong_count``,
    stamps ``last_wrong_at`` and schedules 次日. Correct answers climb the
    clean ladder (3→7→16→35) or the error ladder (2→5→12→25, capped at 7 days
    once ``wrong_count >= 3``). ``ease_factor`` is no longer part of the math.
    """
    if operation_id is not None:
        result = await vocabulary_service.record_idempotent_review(db, current_user.id, word_id, quality, operation_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Word not found")
        await db.commit()
        return result

    review = await vocabulary_service.record_review(db, current_user.id, word_id, quality)
    if review is None:
        raise HTTPException(status_code=404, detail="Word not found")
    vocab, next_interval, next_review_at = review
    await db.commit()

    return {
        "id": vocab.id,
        "word": vocab.word,
        "next_review_at": next_review_at.isoformat(),
        "interval_days": next_interval,
        "review_count": vocab.review_count,
        "wrong_count": vocab.wrong_count,
        "last_wrong_at": vocab.last_wrong_at.isoformat() if vocab.last_wrong_at else None,
    }


@router.post("/{word_id}/mastered", response_model=VocabularyMasteredResponse)
@rate_limit("20/minute")
async def mark_word_mastered(
    request: Request,
    word_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """One-click 已掌握 from the word bank.

    Mastered words exit the review loop (tri-state semantics): the level is
    set directly (no SM-2 grading) and ``next_review_at`` is cleared so due
    queues never resurface the word.
    """
    vocab = await vocabulary_service.mark_mastered(db, current_user.id, word_id)
    if vocab is None:
        raise HTTPException(status_code=404, detail="Word not found")
    await db.commit()

    return {
        "id": vocab.id,
        "word": vocab.word,
        "mastery_level": vocab.mastery_level,
    }


@router.delete("/{word_id}", response_model=VocabularyDeleteResponse)
@rate_limit("20/minute")
async def remove_word(
    request: Request,
    word_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a word from vocabulary."""
    result = await db.execute(
        select(Vocabulary).where(
            Vocabulary.id == word_id,
            Vocabulary.user_id == current_user.id,
        )
    )
    vocab = result.scalar_one_or_none()
    if not vocab:
        raise HTTPException(status_code=404, detail="Word not found")

    await db.delete(vocab)
    await db.commit()
    return {"success": True}


@router.get("/words", response_model=LearningWordsResponse)
@rate_limit("30/minute")
async def list_learning_words(
    request: Request,
    mastery: str = Query(
        "learning,reviewing",
        description="Comma-separated mastery levels to include",
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lightweight endpoint returning just word strings for the user's vocabulary.

    Used by the watch page to highlight words the user is actively learning
    in subtitle text (Sprint 3 vocab recurrence UI). Returns only the word
    strings — no full Vocabulary objects — to minimize payload.
    """
    levels = [lv.strip() for lv in mastery.split(",") if lv.strip()]
    if not levels:
        levels = ["learning", "reviewing"]

    result = await db.execute(
        select(Vocabulary.word).where(
            Vocabulary.user_id == current_user.id,
            Vocabulary.mastery_level.in_(levels),
        )
    )
    words = [w.lower() for w in result.scalars().all()]
    return {"words": words}


@router.get("/watch-context", response_model=WatchContextResponse)
@rate_limit("60/minute")
async def get_watch_context(
    request: Request,
    video_id: str = Query(..., min_length=1, max_length=36),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """观看页的词汇状态：一次返回「正在学」「已掌握」与「本视频是否已建集合」。

    播放页以前要发三个请求（``/vocabulary/words?mastery=learning,reviewing``、
    ``?mastery=mastered``、``/vocab-sets``）才凑齐同一块 UI。这里合成一次：

    * 词表按 mastery 分两组，过滤条件与 ``/vocabulary/words`` 完全一致；
    * 集合只按 ``user_id + video_id`` 直接查，而不是走 ``/vocab-sets`` 的
      全量列表（那个会加载用户所有集合 + 词统计 + 视频行）。

    同一视频若有多个等级的集合，取最近活跃的那个——按钮只需要一个可打开的 id。
    """
    from app.models.vocab_set import VocabSet

    rows = (
        await db.execute(
            select(Vocabulary.word, Vocabulary.mastery_level).where(
                Vocabulary.user_id == current_user.id,
                Vocabulary.mastery_level.in_(("learning", "reviewing", "mastered")),
            )
        )
    ).all()
    learning_words = [word.lower() for word, level in rows if level in ("learning", "reviewing")]
    mastered_words = [word.lower() for word, level in rows if level == "mastered"]

    vocab_set = (
        await db.execute(
            select(VocabSet.id, VocabSet.video_id)
            .where(VocabSet.user_id == current_user.id, VocabSet.video_id == video_id)
            .order_by(VocabSet.last_activity_at.desc(), VocabSet.created_at.desc())
            .limit(1)
        )
    ).first()

    return WatchContextResponse(
        learning_words=learning_words,
        mastered_words=mastered_words,
        vocab_set=WatchContextVocabSet(id=vocab_set.id, video_id=vocab_set.video_id) if vocab_set else None,
    )
