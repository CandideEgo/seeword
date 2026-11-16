"""add subtitle_change_proposals + subtitle_mergeable_updates

Revision ID: w4x5y6z7a8b9
Revises: v3w4x5y6z7a8
Create Date: 2026-07-03 10:00:00.000000

Adds Phase 3e PR + propagation tables:
- subtitle_change_proposals: fork→standard propose-back PRs (batch, per-line
  diff, lifecycle pending→merged|rejected+withdrawn per 决议 8).
- subtitle_mergeable_updates: per-fork-per-line markers for conflicts when a
  PR merge propagates to a fork that has edited the same line (决议 2).

SubtitleRevision.scope gains the "sync" value (no schema change — it's a plain
String column; only the model comment + writer logic change).

See backend/app/services/subtitle_edit_service.py Phase 3e.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "w4x5y6z7a8b9"
down_revision: str | None = "v3w4x5y6z7a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subtitle_change_proposals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "standard_video_id",
            sa.String(36),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_url", sa.String(2000), nullable=False),
        sa.Column(
            "submitted_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("changes", sa.JSON, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "reviewed_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scp_standard_video_id", "subtitle_change_proposals", ["standard_video_id"])
    op.create_index("ix_scp_status", "subtitle_change_proposals", ["status"])
    op.create_index("ix_scp_submitted_by", "subtitle_change_proposals", ["submitted_by"])
    op.create_index("ix_scp_created_at", "subtitle_change_proposals", ["created_at"])

    op.create_table(
        "subtitle_mergeable_updates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "fork_video_id",
            sa.String(36),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fork_subtitle_id",
            sa.String(36),
            sa.ForeignKey("subtitles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sentence_index", sa.Integer, nullable=False),
        sa.Column(
            "standard_revision_id",
            sa.String(36),
            sa.ForeignKey("subtitle_revisions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "proposal_id",
            sa.String(36),
            sa.ForeignKey("subtitle_change_proposals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fork_video_id", "fork_subtitle_id", name="uq_mergeable_fork_subtitle"),
    )
    op.create_index("ix_smu_fork_video_id", "subtitle_mergeable_updates", ["fork_video_id"])


def downgrade() -> None:
    op.drop_index("ix_smu_fork_video_id", table_name="subtitle_mergeable_updates")
    op.drop_table("subtitle_mergeable_updates")
    op.drop_index("ix_scp_created_at", table_name="subtitle_change_proposals")
    op.drop_index("ix_scp_submitted_by", table_name="subtitle_change_proposals")
    op.drop_index("ix_scp_status", table_name="subtitle_change_proposals")
    op.drop_index("ix_scp_standard_video_id", table_name="subtitle_change_proposals")
    op.drop_table("subtitle_change_proposals")
