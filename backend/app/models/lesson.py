"""Site-owned lesson publication, revision history and progress."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    event,
    inspect,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid.uuid4())


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    current_revision_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("lesson_revisions.id", name="fk_lessons_current_revision", use_alter=True, ondelete="RESTRICT"),
    )


class LessonRevision(Base):
    __tablename__ = "lesson_revisions"
    __table_args__ = (
        UniqueConstraint("lesson_id", "fingerprint_version", "fingerprint", name="uq_lesson_revision_fingerprint"),
        CheckConstraint("status IN ('candidate', 'published', 'withdrawn')", name="ck_lesson_revision_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lesson_id: Mapped[str] = mapped_column(String(100), ForeignKey("lessons.id", ondelete="RESTRICT"), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint_version: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    access_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    pack: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="candidate")
    review: Mapped[dict | None] = mapped_column(JSON)
    reviewer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class LessonOperation(Base):
    __tablename__ = "lesson_operations"
    __table_args__ = (
        UniqueConstraint("actor_id", "operation_id", name="uq_lesson_operation_actor_operation"),
        UniqueConstraint("receipt_id", name="uq_lesson_operation_receipt"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    operation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(12), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    revision_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("lesson_revisions.id", ondelete="RESTRICT"), index=True
    )
    receipt_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(100), ForeignKey("lessons.id", ondelete="RESTRICT"), primary_key=True)
    # The revision the resume pointer currently belongs to. A learner following an
    # old deep link keeps writing there without disturbing anything else.
    revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lesson_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    position_ms: Mapped[int | None] = mapped_column(BigInteger)
    # Completion is a lesson-level fact: it is never cleared by a later position
    # save, and a re-published revision is delivered to a finished learner as
    # completed too.
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    watch_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class LessonActivity(Base):
    __tablename__ = "lesson_activities"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_lesson_activity_user_event"),
        Index("ix_lesson_activities_user_time", "user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lesson_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(12), nullable=False)
    delta_s: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


@event.listens_for(LessonRevision, "before_update")
def _immutable_pack(_mapper, _connection, revision: LessonRevision) -> None:
    attributes = inspect(revision).attrs
    mutable = {"status", "review", "reviewer_id"}
    if any(attribute.history.has_changes() for key, attribute in attributes.items() if key not in mutable):
        raise ValueError("Lesson revision content is immutable")
