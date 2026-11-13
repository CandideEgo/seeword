"""Milestone and mastery snapshot models (Sprint 4 — E4 掌握度可视化 + 成就系统).

UserMilestone — historical achievement rows. The achievement feature is retired
(``check_and_award`` awards nothing, ``/plan/milestones`` answers 410); the table
is kept only so that history is not destroyed.

MasterySnapshot — daily snapshot of mastery_by_level for trend visualization.
Still live: ``/plan/mastery-trend`` reads it via milestone_service.
"""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# UserMilestone
# ---------------------------------------------------------------------------

# Milestone type keys. The achievement system is retired (check_and_award never
# awards; /plan/milestones answers 410), so nothing reads these constants — the
# column still stores the old values on historical rows. Kept as documentation
# of what that column can contain; delete together with the table if it ever goes.
# Valid milestone types
MILESTONE_VOCAB_50 = "vocab_50"
MILESTONE_MASTERED_100 = "mastered_100_words"
MILESTONE_VOCAB_200 = "vocab_200"
MILESTONE_STREAK_7 = "streak_7_days"
MILESTONE_STREAK_30 = "streak_30_days"
MILESTONE_COMPLETED_10_VIDEOS = "completed_10_videos"
MILESTONE_FIRST_SHADOWING = "first_shadowing"
MILESTONE_FIRST_REVIEW = "first_review"

ALL_MILESTONE_TYPES = {
    MILESTONE_VOCAB_50,
    MILESTONE_MASTERED_100,
    MILESTONE_VOCAB_200,
    MILESTONE_STREAK_7,
    MILESTONE_STREAK_30,
    MILESTONE_COMPLETED_10_VIDEOS,
    MILESTONE_FIRST_SHADOWING,
    MILESTONE_FIRST_REVIEW,
}


class UserMilestone(Base):
    """A one-time achievement awarded when a user meets a milestone rule.

    Each (user_id, milestone_type) pair is unique — a milestone can only be
    achieved once per user.
    """

    __tablename__ = "user_milestones"
    __table_args__ = (UniqueConstraint("user_id", "milestone_type", name="uq_milestone_user_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Milestone type identifier (see ALL_MILESTONE_TYPES)
    milestone_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # When the milestone was achieved
    achieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # Optional metadata (e.g. {"word_count": 105} at time of achievement)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # relationships
    user = relationship("User", backref="milestones")


# ---------------------------------------------------------------------------
# MasterySnapshot
# ---------------------------------------------------------------------------


class MasterySnapshot(Base):
    """Daily snapshot of a user's mastery_by_level for trend visualization.

    Written once per day on the first LearningEvent emission. The mastery_json
    format matches UserLearningProfile.mastery_by_level:
    {"cet4": {"new": 5, "learning": 3, "mastered": 10, ...}, ...}
    """

    __tablename__ = "mastery_snapshots"
    __table_args__ = (UniqueConstraint("user_id", "snapshot_date", name="uq_snapshot_user_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # The date this snapshot represents
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Mastery breakdown JSON (same format as UserLearningProfile.mastery_by_level)
    mastery_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # relationships
    user = relationship("User", backref="mastery_snapshots")
