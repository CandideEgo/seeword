import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_learning_record_user_video"),
        # Study-history pages filter by user (+ completed) and order by recency;
        # the count/first-page queries otherwise sort every record of the user.
        Index("ix_learning_records_user_completed_accessed", "user_id", "completed", "last_accessed_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    words_learned: Mapped[int] = mapped_column(Integer, default=0)
    speaking_attempts: Mapped[int] = mapped_column(Integer, default=0)
    quiz_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Enhanced tracking
    # Cumulative per record — never slice this by last_accessed_at. Daily /
    # weekly watched-minute aggregates come from behavior_events.watch_time
    # (see app/api/v1/learning.py::stats_weekly, BE-08).
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    progress_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    position_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="learning_records")
    video = relationship("Video", back_populates="learning_records")


class Vocabulary(Base):
    __tablename__ = "vocabulary"
    __table_args__ = (
        UniqueConstraint("user_id", "word", name="uq_vocabulary_user_word"),
        # Due-queue counts and the review list filter user + mastery + due time
        # together; without this the plan is an index scan per mastery level.
        Index("ix_vocabulary_user_mastery_review", "user_id", "mastery_level", "next_review_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word: Mapped[str] = mapped_column(String(100), nullable=False)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Chinese translation
    part_of_speech: Mapped[str | None] = mapped_column(String(20), nullable=True)  # noun/verb/adj/etc
    ipa: Mapped[str | None] = mapped_column(String(100), nullable=True)  # International Phonetic Alphabet
    example_sentences: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # list of example sentences
    collocations: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # list of common collocations
    difficulty_level: Mapped[str | None] = mapped_column(String(5), nullable=True)  # A1-C2
    mastery_level: Mapped[str] = mapped_column(String(20), default="new")  # new/learning/reviewing/mastered
    context_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Phase 1 D3b: drill "回看原句" needs the originating subtitle. Nullable
    # so old words without a source still display normally; SET NULL on
    # subtitle deletion preserves word history.
    subtitle_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("subtitles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # SM-2 algorithm fields
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)

    # Learning plan enhancement fields (ADR-0012)
    exam_level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "cet4"
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)

    # S3 (DEC-053): cumulative wrong answers and when the last one happened.
    # S6's review-interval algorithm reads these instead of SM-2's ease_factor
    # (a word answered wrong often must come back sooner, not later).
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    last_wrong_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="vocabulary")
    video = relationship("Video")
