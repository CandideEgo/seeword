"""Drop the retired redeem-code system and the frozen user-data tables.

2026-10 backend cleanup (backend/tests/test_architecture_invariants.py). Every
table below is dormant: no active feature reads or writes it, and the
compatibility shells that used to keep them alive now answer 410
``FEATURE_RETIRED`` (or no longer exist at all).

- ``redeem_codes`` + the Postgres enums ``redeemstatus`` / ``revokedreason``:
  the redeem-code / Pro-grant system (ADR-0007). Pro is sold off-site via the
  Jinshuju payment page; no code path issues or redeems codes any more.
- ``speaking_attempts`` / ``speaking_rubrics`` / ``rubric_criteria`` /
  ``speaking_attempt_scores``: AI speaking scoring was removed in 2026-07
  (ADR-0002/0003); the tables were only kept so historical rows stayed
  exportable. That export path is gone with this cleanup.
- ``shadowing_attempts`` / ``weekly_reports``: retired features whose 410
  compatibility routes never touch storage again.
- ``video_practice_questions``: the model was already deleted; orphan table.

Data is intentionally dropped (the dev database was backed up to
``.tmp-diag/seeword-pre-cleanup-20261026.dump`` before this migration).
``downgrade`` recreates the tables and enums structurally equivalent so the
migration chain stays reversible; it cannot restore the dropped rows.

Revision ID: c3d4e5f6a7b8
Revises: q8r9s0t1u2v3
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c3d4e5f6a7b8"
down_revision = "q8r9s0t1u2v3"
branch_labels = None
depends_on = None

# Children before parents: speaking_attempt_scores -> speaking_attempts /
# rubric_criteria -> speaking_rubrics. The rest are independent leaves.
_DROP_ORDER = (
    "speaking_attempt_scores",
    "speaking_attempts",
    "rubric_criteria",
    "speaking_rubrics",
    "shadowing_attempts",
    "weekly_reports",
    "video_practice_questions",
    "redeem_codes",
)

_REDEEM_STATUS = ("unused", "redeemed", "revoked", "expired")
_REVOKED_REASON = ("leak", "error", "refund")


def upgrade() -> None:
    for table in _DROP_ORDER:
        op.drop_table(table)

    # The enum types belong to redeem_codes; drop them after the table that
    # used them is gone (Postgres refuses to drop a type that still has
    # dependents).
    op.execute("DROP TYPE IF EXISTS revokedreason")
    op.execute("DROP TYPE IF EXISTS redeemstatus")


def downgrade() -> None:
    # Enums must exist before the column that uses them is created.
    op.execute("CREATE TYPE redeemstatus AS ENUM ('unused', 'redeemed', 'revoked', 'expired')")
    op.execute("CREATE TYPE revokedreason AS ENUM ('leak', 'error', 'refund')")

    redeemstatus = postgresql.ENUM(*_REDEEM_STATUS, name="redeemstatus", create_type=False)
    revokedreason = postgresql.ENUM(*_REVOKED_REASON, name="revokedreason", create_type=False)

    op.create_table(
        "speaking_rubrics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rubric_criteria",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("rubric_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["rubric_id"], ["speaking_rubrics.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "speaking_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("subtitle_id", sa.String(length=36), nullable=True),
        sa.Column("audio_url", sa.String(length=2000), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("fluency", sa.Float(), nullable=True),
        sa.Column("completeness", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("word_scores", sa.JSON(), nullable=True),
        sa.Column("audio_duration", sa.Float(), nullable=True),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("rubric_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["rubric_id"], ["speaking_rubrics.id"]),
        sa.ForeignKeyConstraint(["subtitle_id"], ["subtitles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_speaking_attempts_user_id", "speaking_attempts", ["user_id"])
    op.create_table(
        "speaking_attempt_scores",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("speaking_attempt_id", sa.String(length=36), nullable=False),
        sa.Column("criterion_id", sa.String(length=36), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["criterion_id"], ["rubric_criteria.id"]),
        sa.ForeignKeyConstraint(["speaking_attempt_id"], ["speaking_attempts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_speaking_attempt_scores_speaking_attempt_id",
        "speaking_attempt_scores",
        ["speaking_attempt_id"],
    )
    op.create_table(
        "shadowing_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("subtitle_id", sa.String(length=36), nullable=True),
        sa.Column("audio_url", sa.String(length=2000), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("is_satisfied", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["subtitle_id"], ["subtitles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shadowing_attempts_user_id", "shadowing_attempts", ["user_id"])
    op.create_index("ix_shadowing_attempts_video_id", "shadowing_attempts", ["video_id"])
    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("study_days", sa.Integer(), nullable=False),
        sa.Column("total_minutes", sa.Integer(), nullable=False),
        sa.Column("new_words", sa.Integer(), nullable=False),
        sa.Column("reviewed_words", sa.Integer(), nullable=False),
        sa.Column("videos_completed", sa.Integer(), nullable=False),
        sa.Column("streak_at_week_end", sa.Integer(), nullable=False),
        sa.Column("delta_minutes_pct", sa.Float(), nullable=True),
        sa.Column("daily_minutes", sa.JSON(), nullable=True),
        sa.Column("daily_new_words", sa.JSON(), nullable=True),
        sa.Column("highlight", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "week_start", name="uq_weekly_report_user_week"),
    )
    op.create_index("ix_weekly_reports_user_id", "weekly_reports", ["user_id"])
    op.create_index("ix_weekly_reports_week_start", "weekly_reports", ["week_start"])
    op.create_table(
        "video_practice_questions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("video_id", sa.String(length=36), nullable=False),
        sa.Column("exam_level", sa.String(length=20), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("question_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["video_id"], ["videos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("video_id", "exam_level", name="uq_video_practice_video_level"),
    )
    op.create_index("ix_video_practice_questions_video_id", "video_practice_questions", ["video_id"])
    op.create_table(
        "redeem_codes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("batch_label", sa.String(length=100), nullable=True),
        sa.Column("used_by", sa.String(length=36), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", redeemstatus, server_default=sa.text("'unused'::redeemstatus"), nullable=False),
        sa.Column("revoked_reason", revokedreason, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["used_by"],
            ["users.id"],
            name="fk_redeem_codes_used_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_redeem_codes_code", "redeem_codes", ["code"], unique=True)
