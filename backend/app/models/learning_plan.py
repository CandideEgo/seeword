"""Learning profile models — the user aggregation and the semantic events
feeding it.

Key concepts:
  UserLearningProfile — aggregated learning profile (streak, mastery breakdown,
      daily goal tracking). One-to-one with User.
  LearningEvent — structured semantic learning events (distinct from raw
      BehaviorEvent). Feeds profile aggregation and recommendation system.

The daily-plan half of ADR-0012 Decision 3 was cut on 2026-08-27: the
``learning_plans`` / ``learning_plan_items`` models and tables, the ``plan_id``
reference on ``LearningEvent``, and the endpoints that served them are gone
(dropped in ``d1e2f3a4b5c6``). The module keeps its name because the profile is
what the plan was for.
"""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# UserLearningProfile
# ---------------------------------------------------------------------------


class UserLearningProfile(Base):
    """Aggregated learning profile for a user. One-to-one with User.

    Contains cached aggregations (mastery_by_level, streak) and daily
    progress counters (today_words_learned, today_minutes_spent) that are
    incrementally updated via LearningEvent emission.
    """

    __tablename__ = "user_learning_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_learning_profile_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # Estimated CEFR level, derived from vocabulary mastery distribution
    estimated_level: Mapped[str | None] = mapped_column(String(10), nullable=True)  # A1-C2

    # Weekly cycle tracking (north-star metric per ADR-0012)
    weekly_cycles_completed: Mapped[int] = mapped_column(Integer, default=0)
    weekly_cycles_started: Mapped[int] = mapped_column(Integer, default=0)
    current_week_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Streak tracking (replaces dropped User.streak_count / longest_streak)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Per-exam-level mastery breakdown (cached aggregation from Vocabulary)
    # {"cet4": {"new": 5, "learning": 3, "reviewing": 2, "mastered": 10, "due": 1}, ...}
    mastery_by_level: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Strengths/weaknesses (cached from practice accuracy)
    # {"strong": ["cet4"], "weak": ["cet6"]}
    strengths: Mapped[list | None] = mapped_column(JSON, nullable=True)
    weaknesses: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Daily training quota (DEC-053). Global per user — one setting, not one per
    # video — because the round is a day-sized dose, and a per-video quota would
    # make "today's 10 new words" ambiguous. ``daily_new_target`` is the new-word
    # quota (default 10); review words are taken separately and capped by
    # ``daily_review_target``. Bounds (5..100) are enforced in the API layer,
    # same convention as ``users.gender`` — no DB-level constraint.
    daily_new_target: Mapped[int] = mapped_column(Integer, default=10)
    daily_review_target: Mapped[int] = mapped_column(Integer, default=20)

    # Daily goal tracking (current day snapshot, incrementally updated)
    today_words_learned: Mapped[int] = mapped_column(Integer, default=0)
    today_minutes_spent: Mapped[int] = mapped_column(Integer, default=0)
    today_goal_met: Mapped[bool] = mapped_column(Boolean, default=False)
    today_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # 两条退役功能留下的死列，代码里已无任何读写：
    #   total_shadowing_count   —— 跟读（shadowing）已下线（410 兼容壳）
    #   last_plan_generated_at  —— 每日计划（ADR-0012）已在 d1e2f3a4b5c6 删除
    # 保留只为避免一次纯删列的迁移；下次动这张表时一并 drop。
    total_shadowing_count: Mapped[int] = mapped_column(Integer, default=0)

    last_plan_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
    )

    # relationships
    user = relationship("User", back_populates="learning_profile")


# ---------------------------------------------------------------------------
# LearningEvent
# ---------------------------------------------------------------------------


class LearningEvent(Base):
    """Structured semantic learning event — distinct from raw BehaviorEvent.

    BehaviorEvent captures raw interactions (click, play, pause, seek, etc.)
    for analytics and debugging. LearningEvent captures high-level learning
    actions (completed_video, learned_words, practiced_items, reviewed_words)
    that feed the learning profile, daily goal tracking, and the recommendation
    system (ADR-0011 behavior_events P0 blocker).

    event_date is the user's local date (computed server-side from UTC +
    timezone), used for daily aggregation and streak computation.
    """

    __tablename__ = "learning_events"
    __table_args__ = (
        Index("ix_learning_events_user_date", "user_id", "event_date"),
        Index("ix_learning_events_user_type", "user_id", "event_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Semantic event types
    # "completed_video" | "learned_words" | "practiced_items" | "reviewed_words"
    # "met_daily_goal"
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # Quantified value (e.g. 5 words learned, 10 items practiced)
    event_value: Mapped[int] = mapped_column(Integer, default=1)

    # Optional reference to source entity
    video_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("videos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Additional context
    event_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # A12 学习 flow 关联：一次学习流程的服务端 id 与路径（listening / exam /
    # practice / vocabulary / video）。客户端同 id 的 ``flow_result`` 意图事件
    # 落在 behavior_events，两者对齐才能算丢失率与重复率。
    flow_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # 按哪一版契约理解这行；历史行按 v1 回填（见迁移 b7c8d9e0f1a2）。
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    # User's local date for daily aggregation
    event_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    # relationships
    user = relationship("User", back_populates="learning_events")
