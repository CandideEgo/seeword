"""Fence video processing and durable dispatch to a server-issued generation."""

import sqlalchemy as sa
from alembic import op

revision = "d7e21b4c9f84"
down_revision = "d7e21b4c9f83"
branch_labels = None
depends_on = None


def upgrade():
    # Existing in-flight rows remain legacy NULL; never guess which new run an
    # old untagged GPU callback belongs to.
    op.add_column("videos", sa.Column("processing_generation", sa.String(36), nullable=True))
    op.add_column("pipeline_dispatches", sa.Column("processing_generation", sa.String(36), nullable=True))


def downgrade():
    op.drop_column("pipeline_dispatches", "processing_generation")
    op.drop_column("videos", "processing_generation")
