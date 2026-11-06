"""Streamed tutor replies: immutable text blocks and a message lifecycle status.

Revision ID: b8e2f4a6c901
Revises: 9f2c8a7d6b10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8e2f4a6c901"
down_revision: str | None = "9f2c8a7d6b10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "teaching_messages",
        sa.Column("status", sa.String(20), nullable=False, server_default="complete"),
    )
    op.create_table(
        "teaching_message_blocks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("message_id", sa.String(36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["teaching_messages.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("message_id", "ordinal", name="uq_teaching_message_block_ordinal"),
    )


def downgrade() -> None:
    op.drop_table("teaching_message_blocks")
    op.drop_column("teaching_messages", "status")
