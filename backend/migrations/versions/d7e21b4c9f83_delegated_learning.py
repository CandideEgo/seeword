"""Explicit learning resource grants, transactional receipts and short-lived intents."""

import sqlalchemy as sa
from alembic import op

revision = "d7e21b4c9f83"
down_revision = "d7e21b4c9f82"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "external_learning_grants",
        sa.Column(
            "connection_id",
            sa.String(36),
            sa.ForeignKey("external_connections.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_limits", sa.JSON(), nullable=False),
    )
    op.create_index("ix_external_learning_grants_user_id", "external_learning_grants", ["user_id"])
    op.create_table(
        "external_learning_operations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "connection_id", sa.String(36), sa.ForeignKey("external_connections.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("operation_id", sa.String(64), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("resource", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "connection_id", "operation_id", name="uq_external_learning_operation"),
    )
    op.create_index("ix_external_learning_operations_user_id", "external_learning_operations", ["user_id"])
    op.create_index("ix_external_learning_operations_connection_id", "external_learning_operations", ["connection_id"])
    op.create_table(
        "external_learning_intents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "connection_id", sa.String(36), sa.ForeignKey("external_connections.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("operation_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "connection_id", "operation_id", name="uq_external_learning_intent"),
    )
    op.create_index("ix_external_learning_intents_user_id", "external_learning_intents", ["user_id"])
    op.create_index("ix_external_learning_intents_connection_id", "external_learning_intents", ["connection_id"])
    op.create_index("ix_external_learning_intents_expiry", "external_learning_intents", ["expires_at"])


def downgrade():
    op.drop_table("external_learning_intents")
    op.drop_table("external_learning_operations")
    op.drop_table("external_learning_grants")
