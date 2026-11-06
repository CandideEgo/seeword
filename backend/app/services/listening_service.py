"""Listening practice built from real, playable videos and frozen subtitle cues."""

import re
import unicodedata
from datetime import UTC, datetime
from difflib import SequenceMatcher

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import UnprocessableEntityError
from app.models.listening import ListeningSession
from app.models.subtitle import Subtitle
from app.models.user import User
from app.models.video import Video
from app.services.discovery_service import public_video_filters
from app.services.video_card import video_card_payload

MAX_QUESTIONS = 10
MAX_ANSWER_LENGTH = 2000


def iso_utc(value):
    if value is None:
        return None
    return (value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)).isoformat()


def cue_filters():
    return (
        func.length(Subtitle.text_en).between(12, 220),
        Subtitle.end_time > Subtitle.start_time,
        Subtitle.end_time - Subtitle.start_time <= 20,
        Subtitle.start_time >= 0,
    )


def playable_filters():
    return (
        *public_video_filters(),
        Video.storage_mode != "offline",
        (Video.video_url_480p.is_not(None) | Video.video_url_720p.is_not(None) | Video.video_url_1080p.is_not(None)),
    )


async def catalog(db: AsyncSession, page: int, page_size: int):
    counts = (
        select(Subtitle.video_id, func.count().label("cue_count"))
        .where(*cue_filters())
        .group_by(Subtitle.video_id)
        .subquery()
    )
    stmt = select(Video, counts.c.cue_count).join(counts, counts.c.video_id == Video.id).where(*playable_filters())
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = (
        await db.execute(
            stmt.order_by(Video.published_at.desc().nullslast(), Video.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    from app.services.channel_service import channel_slugs_for

    slugs = await channel_slugs_for(db, [v for v, _ in rows])
    return {
        "items": [{"video": video_card_payload(v, slugs.get(v.channel_ref)), "question_count": n} for v, n in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": page * page_size < total,
    }


async def playable_video(db: AsyncSession, video_id: str, user: User):
    video = (await db.execute(select(Video).where(Video.id == video_id, *playable_filters()))).scalar_one_or_none()
    if not video:
        raise HTTPException(404, "视频暂不可用于听力练习，请选择其他素材")
    return video


async def owned_session(db: AsyncSession, session_id: str, user_id: str, *, lock: bool = False) -> ListeningSession:
    stmt = select(ListeningSession).where(ListeningSession.id == session_id, ListeningSession.user_id == user_id)
    if lock:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    session = (await db.execute(stmt)).scalar_one_or_none()
    if not session:
        raise HTTPException(404, "练习记录不存在")
    return session


async def start(db: AsyncSession, user: User, video_id: str, count: int, restart: bool):
    if not 1 <= count <= MAX_QUESTIONS:
        raise UnprocessableEntityError(f"每次练习题数须为 1 至 {MAX_QUESTIONS}")
    video = await playable_video(db, video_id, user)
    # Serialize same-account starts without blocking FK key-share locks taken
    # by a concurrent submission's learning event. PostgreSQL compiles this to
    # FOR NO KEY UPDATE: the account's primary key is not being changed.
    await db.execute(select(User.id).where(User.id == user.id).with_for_update(key_share=True))
    pending = (
        (
            await db.execute(
                select(ListeningSession)
                .where(
                    ListeningSession.user_id == user.id,
                    ListeningSession.video_id == video.id,
                    ListeningSession.submitted_at.is_(None),
                )
                .order_by(ListeningSession.started_at.desc())
                .limit(1)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .first()
    )
    if pending:
        if not restart:
            return pending
        # Restart must not accumulate orphan pending sessions: one user/video
        # used to be able to create unbounded unsubmitted rows via restart=true.
        await db.delete(pending)
    cues = list(
        (
            await db.execute(
                select(Subtitle).where(Subtitle.video_id == video.id, *cue_filters()).order_by(Subtitle.sentence_index)
            )
        ).scalars()
    )
    cues = [c for c in cues if 3 <= len(c.text_en.split()) <= 35 and re.search(r"[a-zA-Z]", c.text_en)]
    if not cues:
        raise UnprocessableEntityError("这段视频还没有可用听力题目，请选择其他素材")
    # Spread excerpts through the lesson instead of only testing its introduction.
    size = min(count, len(cues))
    chosen = [cues[min(len(cues) - 1, int((i + 0.5) * len(cues) / size))] for i in range(size)]
    session = ListeningSession(
        user_id=user.id,
        video_id=video.id,
        title=video.title,
        questions=[
            {
                "id": c.id,
                "start": c.start_time,
                "end": c.end_time,
                "text_en": c.text_en,
                "text_zh": c.text_zh,
                "grammar_note": c.grammar_note,
            }
            for c in chosen
        ],
        answers={},
        current_index=0,
    )
    db.add(session)
    await db.flush()
    return session


async def payload(db: AsyncSession, session: ListeningSession, user: User):
    submitted = session.submitted_at is not None
    video = None
    if session.video_id:
        try:
            video = await playable_video(db, session.video_id, user)
        except HTTPException:
            pass
    return {
        "id": session.id,
        "video_id": session.video_id,
        "title": session.title,
        "video": video_card_payload(video) if video else None,
        "questions": [
            {k: v for k, v in q.items() if submitted or k not in ("text_en", "text_zh", "grammar_note")}
            for q in session.questions
        ],
        "answers": session.answers,
        "results": session.results if submitted else None,
        "correct_count": session.correct_count,
        "total": len(session.questions),
        "current_index": session.current_index,
        "started_at": iso_utc(session.started_at),
        "updated_at": iso_utc(session.updated_at),
        "submitted_at": iso_utc(session.submitted_at) if submitted else None,
    }


def normalized_words(text: str):
    text = unicodedata.normalize("NFKC", text).lower().replace("’", "'")
    return re.findall(r"[a-z0-9]+", text.replace("'", ""))


def grade(expected: str, actual: str):
    reference, answer = normalized_words(expected), normalized_words(actual)
    matcher = SequenceMatcher(a=reference, b=answer, autojunk=False)
    matching = sum(block.size for block in matcher.get_matching_blocks())
    return {
        "correct": bool(reference) and reference == answer,
        "accuracy": round(100 * matching / max(len(reference), len(answer), 1)),
        "diff": [
            {"kind": tag, "expected": " ".join(reference[a:b]), "actual": " ".join(answer[c:d])}
            for tag, a, b, c, d in matcher.get_opcodes()
        ],
    }


async def save(
    db: AsyncSession, session_id: str, user_id: str, answers: dict[str, str], index: int
) -> ListeningSession:
    """Lock and save an owned draft; caller commits the unit of work."""
    session = await owned_session(db, session_id, user_id, lock=True)
    if session.submitted_at:
        raise HTTPException(409, "这次练习已经提交，请开始新一轮练习")
    valid = {q["id"] for q in session.questions}
    if not set(answers).issubset(valid):
        raise UnprocessableEntityError("答案包含不属于本次练习的题目")
    if len(answers) > MAX_QUESTIONS:
        raise UnprocessableEntityError(f"每次最多保存 {MAX_QUESTIONS} 句")
    if any(len(answer) > MAX_ANSWER_LENGTH for answer in answers.values()):
        raise UnprocessableEntityError(f"每句答案最多 {MAX_ANSWER_LENGTH} 个字符")
    if index < 0 or index >= len(session.questions):
        raise UnprocessableEntityError("题目位置超出范围")
    session.answers = {**(session.answers or {}), **answers}
    session.current_index = index
    session.updated_at = datetime.now(UTC)
    await db.flush()
    return session


async def submit(db: AsyncSession, session_id: str, user_id: str) -> ListeningSession:
    """Grade the persisted draft once, together with its required learning fact.

    Lock/reload belongs here so every adapter follows the same state machine.
    A retry returns the committed result; the caller owns commit or rollback.
    """
    session = await owned_session(db, session_id, user_id, lock=True)
    if session.submitted_at:
        return session  # A retry cannot double-count learning activity.
    results = []
    for q in session.questions:
        answer = (session.answers or {}).get(q["id"], "")
        results.append({"id": q["id"], "answer": answer, **grade(q["text_en"], answer)})
    session.results = results
    session.correct_count = sum(r["correct"] for r in results)
    session.submitted_at = session.updated_at = datetime.now(UTC)
    from app.services.learning_event_service import EVENT_PRACTICED_ITEMS, record_event

    await record_event(
        db,
        session.user_id,
        EVENT_PRACTICED_ITEMS,
        len(results),
        video_id=session.video_id,
        flow_id=session.id,
        source="listening",
    )
    await db.flush()
    return session
