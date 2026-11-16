"""Bind lesson chats to an immutable course revision and occurrence."""

import sqlalchemy as sa
from alembic import op

revision = "d7e21b4c9f81"
down_revision = "d7e21b4c9f80"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lesson_tutor_anchors",
        sa.Column(
            "conversation_id",
            sa.String(36),
            sa.ForeignKey("tutor_conversations.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "revision_id", sa.String(36), sa.ForeignKey("lesson_revisions.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("segment_id", sa.String(100), nullable=False),
        sa.Column("token_ids", sa.JSON(), nullable=False),
    )


def downgrade():
    op.drop_table("lesson_tutor_anchors")
