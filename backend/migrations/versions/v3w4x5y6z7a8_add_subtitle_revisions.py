"""add subtitle_revisions table

Revision ID: v3w4x5y6z7a8
Revises: u2v3w4x5y6z7
Create Date: 2026-07-03 08:00:00.000000

Adds ``subtitle_revisions`` for Phase 3 edit audit: one row per subtitle edit
(before/after delta + scope: fork|standard + edited_by + created_at). Powers
the edit-history UI, one-click rollback, and the propose-back flow's lineage.

See backend/app/services/subtitle_edit_service.py Phase 3.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "v3w4x5y6z7a8"
down_revision: str | None = "u2v3w4x5y6z7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subtitle_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "subtitle_id",
            sa.String(36),
            sa.ForeignKey("subtitles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "video_id",
            sa.String(36),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "edited_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("before", sa.JSON, nullable=False),
        sa.Column("after", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subtitle_revisions_subtitle_id", "subtitle_revisions", ["subtitle_id"])
    op.create_index("ix_subtitle_revisions_video_id", "subtitle_revisions", ["video_id"])
    op.create_index("ix_subtitle_revisions_created_at", "subtitle_revisions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_subtitle_revisions_created_at", table_name="subtitle_revisions")
    op.drop_index("ix_subtitle_revisions_video_id", table_name="subtitle_revisions")
    op.drop_index("ix_subtitle_revisions_subtitle_id", table_name="subtitle_revisions")
    op.drop_table("subtitle_revisions")
