"""Learner-owned SLCS anchors and append-only review facts."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, event, inspect
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LessonVocabularySource(Base):
    __tablename__ = "lesson_vocabulary_sources"
    __table_args__ = (
        UniqueConstraint("vocabulary_id", "revision_id", "segment_id", "token_digest", name="uq_lesson_vocab_anchor"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    vocabulary_id: Mapped[str] = mapped_column(String(36), ForeignKey("vocabulary.id", ondelete="CASCADE"))
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("lesson_revisions.id", ondelete="RESTRICT"))
    segment_id: Mapped[str] = mapped_column(String(100))
    token_digest: Mapped[str] = mapped_column(String(64))
    token_ids: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class VocabularyReviewLog(Base):
    """One scheduling fact per review, kept even after its word is deleted.

    ``vocabulary_id`` is ``SET NULL`` and the headword is copied into the row:
    deleting a word removes the learner's current word list entry, not the
    history of what they studied. A cascade here would make "append-only
    review facts" false the moment the user taps delete.
    """

    __tablename__ = "vocabulary_review_log"
    __table_args__ = (
        UniqueConstraint("user_id", "operation_id", name="uq_vocab_review_operation"),
        CheckConstraint("quality BETWEEN 0 AND 5", name="ck_vocab_review_quality"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    vocabulary_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vocabulary.id", ondelete="SET NULL"), index=True
    )
    word: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    operation_id: Mapped[str] = mapped_column(String(100))
    quality: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(20))
    schedule_version: Mapped[str] = mapped_column(String(20))
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    before_state: Mapped[dict] = mapped_column(JSON)
    after_state: Mapped[dict] = mapped_column(JSON)


class LessonTutorAnchor(Base):
    __tablename__ = "lesson_tutor_anchors"

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tutor_conversations.id", ondelete="CASCADE"), primary_key=True
    )
    revision_id: Mapped[str] = mapped_column(String(36), ForeignKey("lesson_revisions.id", ondelete="RESTRICT"))
    segment_id: Mapped[str] = mapped_column(String(100))
    token_ids: Mapped[list[str]] = mapped_column(JSON)


@event.listens_for(LessonTutorAnchor, "before_update")
@event.listens_for(LessonVocabularySource, "before_update")
@event.listens_for(VocabularyReviewLog, "before_update")
def _immutable_fact(_mapper, _connection, target) -> None:
    if any(attribute.history.has_changes() for attribute in inspect(target).attrs):
        raise ValueError("Course learning facts are append-only")
