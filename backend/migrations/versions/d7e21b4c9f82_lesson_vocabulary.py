"""Add lesson vocabulary occurrences and versioned S6 review facts."""

import sqlalchemy as sa
from alembic import op

revision = "d7e21b4c9f82"
down_revision = "d7e21b4c9f81"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lesson_vocabulary_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("vocabulary_id", sa.String(36), sa.ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "revision_id", sa.String(36), sa.ForeignKey("lesson_revisions.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("segment_id", sa.String(100), nullable=False),
        sa.Column("token_digest", sa.String(64), nullable=False),
        sa.Column("token_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "vocabulary_id", "revision_id", "segment_id", "token_digest", name="uq_lesson_vocab_anchor"
        ),
    )
    op.create_table(
        "vocabulary_review_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        # SET NULL, not CASCADE: deleting a word from the list must not erase the
        # learner's review history. The headword is copied into the row.
        sa.Column("vocabulary_id", sa.String(36), sa.ForeignKey("vocabulary.id", ondelete="SET NULL")),
        sa.Column("word", sa.String(100), nullable=False, server_default=""),
        sa.Column("operation_id", sa.String(100), nullable=False),
        sa.Column("quality", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("schedule_version", sa.String(20), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=False),
        sa.Column("after_state", sa.JSON(), nullable=False),
        sa.UniqueConstraint("user_id", "operation_id", name="uq_vocab_review_operation"),
        sa.CheckConstraint("quality BETWEEN 0 AND 5", name="ck_vocab_review_quality"),
    )
    op.create_index("ix_vocabulary_review_log_vocabulary_id", "vocabulary_review_log", ["vocabulary_id"])


def downgrade():
    op.drop_table("vocabulary_review_log")
    op.drop_table("lesson_vocabulary_sources")
