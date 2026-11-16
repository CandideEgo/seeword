"""add video_standards table + videos.forked_from

Revision ID: u2v3w4x5y6z7
Revises: 1af3205308d9
Create Date: 2026-07-03 06:00:00.000000

Adds the Phase 2 "standard version" registry and fork lineage:

- ``video_standards(source_url PK, canonical_video_id FK, created_at)`` —
  one canonical video per source_url. The first video to reach ``ready`` for
  a URL becomes its standard; subsequent submissions fork from it instead of
  re-running the GPU pipeline. PK on source_url prevents concurrent finalize
  races from creating two standards for the same URL.
- ``videos.forked_from`` — points to the source Video a fork was copied from
  (扩展 A4). SET NULL on delete so forks survive their source being removed.
- ``ix_videos_source_url`` — index for standard-lookup and dedup queries.

See backend/app/services/subtitle_edit_service.py Phase 2 and ADR-0006.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "u2v3w4x5y6z7"
down_revision: str | None = "1af3205308d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "video_standards",
        sa.Column("source_url", sa.String(2000), primary_key=True),
        sa.Column(
            "canonical_video_id",
            sa.String(36),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_video_standards_canonical_video_id", "video_standards", ["canonical_video_id"])

    op.add_column(
        "videos",
        sa.Column(
            "forked_from",
            sa.String(36),
            sa.ForeignKey("videos.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_videos_forked_from", "videos", ["forked_from"])
    op.create_index("ix_videos_source_url", "videos", ["source_url"])


def downgrade() -> None:
    op.drop_index("ix_videos_source_url", table_name="videos")
    op.drop_index("ix_videos_forked_from", table_name="videos")
    op.drop_column("videos", "forked_from")
    op.drop_index("ix_video_standards_canonical_video_id", table_name="video_standards")
    op.drop_table("video_standards")
