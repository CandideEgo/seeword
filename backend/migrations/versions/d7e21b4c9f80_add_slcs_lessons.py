"""Add independent SLCS publication, history and progress tables.

Revision ID: d7e21b4c9f80
Revises: c9d0e1f2a3b4
"""

import sqlalchemy as sa
from alembic import op

revision = "d7e21b4c9f80"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lessons",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("current_revision_id", sa.String(36)),
    )
    op.create_table(
        "lesson_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("lesson_id", sa.String(100), sa.ForeignKey("lessons.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("fingerprint_version", sa.String(32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("access_mode", sa.String(20), nullable=False),
        sa.Column("pack", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("review", sa.JSON()),
        sa.Column("reviewer_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("lesson_id", "fingerprint_version", "fingerprint", name="uq_lesson_revision_fingerprint"),
        sa.CheckConstraint("status IN ('candidate', 'published', 'withdrawn')", name="ck_lesson_revision_status"),
    )
    op.create_foreign_key(
        "fk_lessons_current_revision",
        "lessons",
        "lesson_revisions",
        ["current_revision_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_table(
        "lesson_operations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("operation_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(12), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("revision_id", sa.String(36), sa.ForeignKey("lesson_revisions.id", ondelete="RESTRICT")),
        sa.Column("receipt_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("actor_id", "operation_id", name="uq_lesson_operation_actor_operation"),
        sa.UniqueConstraint("receipt_id", name="uq_lesson_operation_receipt"),
    )
    op.create_index("ix_lesson_operations_actor_id", "lesson_operations", ["actor_id"])
    op.create_index("ix_lesson_operations_revision_id", "lesson_operations", ["revision_id"])
    op.create_table(
        "lesson_progress",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("lesson_id", sa.String(100), sa.ForeignKey("lessons.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column(
            "revision_id", sa.String(36), sa.ForeignKey("lesson_revisions.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("position_ms", sa.BigInteger()),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("watch_seconds", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "lesson_activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "revision_id", sa.String(36), sa.ForeignKey("lesson_revisions.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("event_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(12), nullable=False),
        sa.Column("delta_s", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "event_id", name="uq_lesson_activity_user_event"),
    )
    op.create_index("ix_lesson_activities_user_time", "lesson_activities", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("lesson_activities")
    op.drop_table("lesson_progress")
    op.drop_table("lesson_operations")
    op.drop_constraint("fk_lessons_current_revision", "lessons", type_="foreignkey")
    op.drop_table("lesson_revisions")
    op.drop_table("lessons")
