"""Save and project learner anchors without storing licensed excerpts in word rows."""

from collections.abc import Sequence

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, NotFoundError
from app.models.learning import Vocabulary
from app.models.lesson import LessonRevision
from app.models.lesson_learning import LessonTutorAnchor, LessonVocabularySource, VocabularyReviewLog
from app.models.v2_runtime import TutorConversation
from app.services import ecdict, vocabulary_service
from app.services.lessons import get_visible_revision, insert_for, material_for_revision, require_lessons_ready
from app.services.v2_schema import existing_tables, has_tables
from app.services.video_learning_material import VideoLearningMaterial, VocabularyOccurrence
from slcs.material import stable_hash


async def require_vocabulary_pilot(db: AsyncSession) -> None:
    if not get_settings().slcs_vocabulary_enabled:
        raise AppError(503, "SERVICE_UNAVAILABLE", "课程收词暂未开放")
    await require_lessons_ready(db)
    if not await has_tables(db, (LessonVocabularySource.__tablename__,)):
        raise AppError(503, "SERVICE_UNAVAILABLE", "课程收词暂未开放")


def resolve_occurrence(
    material: VideoLearningMaterial, segment_id: str, token_ids: Sequence[str]
) -> VocabularyOccurrence:
    anchor = tuple(token_ids)
    for occurrence in material.vocabulary:
        if occurrence.segment_id == segment_id and occurrence.token_ids == anchor:
            return occurrence
    raise NotFoundError("该课程词汇锚点不可用")


def source_view(
    lesson_id: str, revision_id: str, segment_id: str, token_ids: Sequence[str], occurrence: VocabularyOccurrence | None
) -> dict:
    return {
        "lesson_id": lesson_id,
        "revision_id": revision_id,
        "segment_id": segment_id,
        "token_ids": list(token_ids),
        "start_ms": occurrence.start_ms if occurrence else None,
        "end_ms": occurrence.end_ms if occurrence else None,
        "available": occurrence is not None,
    }


async def save_source(
    db: AsyncSession, user_id: str, lesson_id: str, revision_id: str, segment_id: str, token_ids: list[str]
) -> dict:
    await require_vocabulary_pilot(db)
    revision = await get_visible_revision(db, lesson_id, revision_id, use="site_display", lock=True)
    occurrence = resolve_occurrence(material_for_revision(revision), segment_id, token_ids)
    word = occurrence.headword.strip().lower()
    if len(word) > 100:
        raise AppError(422, "VALIDATION_ERROR", "该词条超出收词长度上限")

    created_id = await db.scalar(
        insert_for(db, Vocabulary)
        .values(user_id=user_id, word=word)
        .on_conflict_do_nothing(index_elements=["user_id", "word"])
        .returning(Vocabulary.id)
    )
    vocab = (
        await db.execute(
            select(Vocabulary).where(Vocabulary.user_id == user_id, Vocabulary.word == word).with_for_update()
        )
    ).scalar_one()
    if created_id is not None:
        entry = ecdict.lookup(word)
        if entry:
            vocabulary_service.apply_ecdict_fields(vocab, entry)

    # One canonical-JSON hash implementation for the whole repo (shared with the
    # fingerprint and the teaching content digest).
    token_digest = stable_hash(list(token_ids))
    await db.execute(
        insert_for(db, LessonVocabularySource)
        .values(
            vocabulary_id=vocab.id,
            revision_id=revision.id,
            segment_id=segment_id,
            token_digest=token_digest,
            token_ids=token_ids,
        )
        .on_conflict_do_nothing(index_elements=["vocabulary_id", "revision_id", "segment_id", "token_digest"])
    )
    return {
        "word_id": vocab.id,
        "word": word,
        "source": source_view(lesson_id, revision.id, segment_id, token_ids, occurrence),
    }


async def list_sources(db: AsyncSession, user_id: str, word_id: str) -> dict:
    await require_vocabulary_pilot(db)
    owned = await db.scalar(select(Vocabulary.id).where(Vocabulary.user_id == user_id, Vocabulary.id == word_id))
    if owned is None:
        raise NotFoundError("词条不存在")
    rows = (
        await db.execute(
            select(LessonVocabularySource, LessonRevision.lesson_id)
            .join(LessonRevision, LessonRevision.id == LessonVocabularySource.revision_id)
            .where(LessonVocabularySource.vocabulary_id == owned)
            .order_by(LessonVocabularySource.created_at, LessonVocabularySource.id)
        )
    ).all()
    materials: dict[str, VideoLearningMaterial | None] = {}
    sources = []
    for source, lesson_id in rows:
        if source.revision_id not in materials:
            try:
                revision = await get_visible_revision(db, lesson_id, source.revision_id, use="site_display")
                materials[source.revision_id] = material_for_revision(revision)
            except AppError as exc:
                if exc.status_code not in {403, 404, 410}:
                    raise
                materials[source.revision_id] = None
        material = materials[source.revision_id]
        try:
            occurrence = resolve_occurrence(material, source.segment_id, source.token_ids) if material else None
        except NotFoundError:
            occurrence = None
        sources.append(source_view(lesson_id, source.revision_id, source.segment_id, source.token_ids, occurrence))
    return {"sources": sources}


async def detach_lesson_words_from_videos(db: AsyncSession, video_ids: Sequence[str]) -> None:
    """Deleting an old video must preserve words that also belong to a course."""
    if not video_ids or not await has_tables(db, (LessonVocabularySource.__tablename__,)):
        return
    await db.execute(
        update(Vocabulary)
        .where(
            Vocabulary.video_id.in_(video_ids),
            select(LessonVocabularySource.id).where(LessonVocabularySource.vocabulary_id == Vocabulary.id).exists(),
        )
        .values(video_id=None, subtitle_id=None, context_sentence=None)
    )


async def purge_learner_facts(db: AsyncSession, user_id: str) -> None:
    """Delete the course rows whose ownership hangs off a parent row.

    Account deletion sweeps tables with a ``user_id`` column;
    ``lesson_vocabulary_sources`` and ``lesson_tutor_anchors`` have none (their
    ownership is the vocabulary row and the conversation). Postgres cascades
    them, but the SQLite test database does not enforce foreign keys, so the
    purge has to delete them explicitly — otherwise a local test run leaves
    another user's anchors behind.

    A database stopped before the course migrations must not fail the whole
    deletion: the tables are checked first, and the anchors are deleted before
    the conversations they hang off (the conversation sweep runs earlier in the
    purge, so asking for them afterwards would find nothing and leave orphans).
    """
    tables = await existing_tables(db)
    if LessonVocabularySource.__tablename__ in tables:
        await db.execute(
            delete(LessonVocabularySource).where(
                LessonVocabularySource.vocabulary_id.in_(select(Vocabulary.id).where(Vocabulary.user_id == user_id))
            )
        )
    if LessonTutorAnchor.__tablename__ in tables and "tutor_conversations" in tables:
        await db.execute(
            delete(LessonTutorAnchor).where(
                LessonTutorAnchor.conversation_id.in_(
                    select(TutorConversation.id).where(TutorConversation.user_id == user_id)
                )
            )
        )


async def export_sections(db: AsyncSession, user_id: str) -> dict:
    """Return only learner facts and opaque anchors, including withdrawn anchors."""
    tables = await existing_tables(db)
    sections: dict[str, list[dict]] = {
        "lesson_vocabulary_sources": [],
        "vocabulary_review_log": [],
        "lesson_tutor_anchors": [],
    }
    if {"lesson_vocabulary_sources", "lesson_revisions"} <= tables:
        rows = await db.execute(
            select(LessonVocabularySource, LessonRevision.lesson_id)
            .join(Vocabulary, Vocabulary.id == LessonVocabularySource.vocabulary_id)
            .join(LessonRevision, LessonRevision.id == LessonVocabularySource.revision_id)
            .where(Vocabulary.user_id == user_id)
            .order_by(LessonVocabularySource.created_at, LessonVocabularySource.id)
        )
        sections["lesson_vocabulary_sources"] = [
            {
                "vocabulary_id": row.vocabulary_id,
                "lesson_id": lesson_id,
                "revision_id": row.revision_id,
                "segment_id": row.segment_id,
                "token_ids": row.token_ids,
                "created_at": row.created_at.isoformat(),
            }
            for row, lesson_id in rows
        ]
    if "vocabulary_review_log" in tables:
        logs = await db.scalars(
            select(VocabularyReviewLog)
            .where(VocabularyReviewLog.user_id == user_id)
            .order_by(VocabularyReviewLog.reviewed_at, VocabularyReviewLog.id)
        )
        sections["vocabulary_review_log"] = [
            {
                "vocabulary_id": log.vocabulary_id,
                "word": log.word,
                "operation_id": log.operation_id,
                "source": log.source,
                "quality": log.quality,
                "schedule_version": log.schedule_version,
                "reviewed_at": log.reviewed_at.isoformat(),
                "before_state": log.before_state,
                "after_state": log.after_state,
            }
            for log in logs
        ]
    if {"lesson_tutor_anchors", "lesson_revisions", "tutor_conversations"} <= tables:
        rows = await db.execute(
            select(LessonTutorAnchor, LessonRevision.lesson_id)
            .join(TutorConversation, TutorConversation.id == LessonTutorAnchor.conversation_id)
            .join(LessonRevision, LessonRevision.id == LessonTutorAnchor.revision_id)
            .where(TutorConversation.user_id == user_id)
            .order_by(TutorConversation.created_at, TutorConversation.id)
        )
        sections["lesson_tutor_anchors"] = [
            {
                "conversation_id": row.conversation_id,
                "lesson_id": lesson_id,
                "revision_id": row.revision_id,
                "segment_id": row.segment_id,
                "token_ids": row.token_ids,
            }
            for row, lesson_id in rows
        ]
    return sections
