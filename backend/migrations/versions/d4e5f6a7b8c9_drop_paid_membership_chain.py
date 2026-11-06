"""Drop the retired paid-membership / payment chain.

2026-11 product decision: every feature is free, so the paid-membership chain
is taken down end to end (backend routers/services/tasks/models and the
frontend purchase surfaces were removed in the same change).

- ``orders`` + the Postgres enum ``orderstatus``: in-site order table. The
  admin orders surface was already gone; with the payment routers deleted
  nothing reads or writes this table.
- ``jinshuju_payments``: off-site (Jinshuju) payment ledger. The Jinshuju
  sync/webhook tasks, purchase-link endpoint and admin payment pages are all
  removed, so the ledger has no reader left.
- ``user_video_unlocks``: D0 free-tier unlock quota. The unlock endpoints
  were already compatibility shells; they are deleted now too.
- ``users.plan`` / ``users.plan_expires_at`` / ``users.plan_source`` + the
  Postgres enum ``plantype``: membership entitlement. No access rule read
  these columns (``video_access`` never did), so dropping them changes no
  permission behaviour.
- ``admin_settings.wechat_shop_url`` / ``admin_settings.payments_enabled``:
  the admin-console switches for the removed purchase entry points.

Data is intentionally dropped. ``downgrade`` recreates the tables/columns/
enums structurally so the revision chain stays reversible; it cannot restore
rows.

Revision ID: d4e5f6a7b8c9
Revises: b8e2f4a6c901
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "b8e2f4a6c901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ORDER_STATUS = ("pending", "paid", "expired", "cancelled")
_PLAN_TYPES = ("free", "pro")


def upgrade() -> None:
    # Children before parents. ``jinshuju_payments.user_id`` is SET NULL, so it
    # does not block; ``orders.user_id`` cascades.
    op.drop_index("ix_jinshuju_payments_status", table_name="jinshuju_payments")
    op.drop_index("ix_jinshuju_payments_phone", table_name="jinshuju_payments")
    op.drop_index("uq_jinshuju_payments_entry_token", table_name="jinshuju_payments")
    op.drop_table("jinshuju_payments")

    op.drop_index("ix_orders_order_number", table_name="orders")
    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_user_video_unlocks_user_unlocked_at", table_name="user_video_unlocks")
    op.drop_table("user_video_unlocks")

    op.drop_column("admin_settings", "payments_enabled")
    op.drop_column("admin_settings", "wechat_shop_url")

    op.drop_column("users", "plan_source")
    op.drop_column("users", "plan_expires_at")
    op.drop_column("users", "plan")

    # Enum types survive their columns on Postgres; drop them after the last
    # dependent column/table is gone.
    op.execute("DROP TYPE IF EXISTS plantype")
    op.execute("DROP TYPE IF EXISTS orderstatus")


def downgrade() -> None:
    # Enums must exist before the columns that use them are created.
    op.execute("CREATE TYPE plantype AS ENUM ('free', 'pro')")
    op.execute("CREATE TYPE orderstatus AS ENUM ('pending', 'paid', 'expired', 'cancelled')")

    plantype = postgresql.ENUM(*_PLAN_TYPES, name="plantype", create_type=False)
    orderstatus = postgresql.ENUM(*_ORDER_STATUS, name="orderstatus", create_type=False)

    op.add_column(
        "users",
        sa.Column("plan", plantype, nullable=False, server_default="free"),
    )
    op.add_column("users", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("plan_source", sa.String(20), nullable=True))

    op.add_column("admin_settings", sa.Column("wechat_shop_url", sa.String(length=500), nullable=True))
    op.add_column(
        "admin_settings",
        sa.Column("payments_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "user_video_unlocks",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("video_id", sa.String(36), sa.ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_user_video_unlocks_user_unlocked_at", "user_video_unlocks", ["user_id", "unlocked_at"])

    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("order_number", sa.String(length=64), nullable=False),
        sa.Column("plan", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", orderstatus, nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_orders_order_number", "orders", ["order_number"], unique=True)
    op.create_index("ix_orders_user_id", "orders", ["user_id"], unique=False)

    op.create_table(
        "jinshuju_payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entry_token", sa.String(64), nullable=False),
        sa.Column("serial_number", sa.Integer(), nullable=False),
        sa.Column("form_token", sa.String(32), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("tier_name", sa.String(20), nullable=True),
        sa.Column("amount_fen", sa.Integer(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("trade_status", sa.String(32), nullable=True),
        sa.Column("trade_no", sa.String(64), nullable=True),
        sa.Column("payment_method", sa.String(32), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("entry_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("uq_jinshuju_payments_entry_token", "jinshuju_payments", ["entry_token"], unique=True)
    op.create_index("ix_jinshuju_payments_phone", "jinshuju_payments", ["phone"])
    op.create_index("ix_jinshuju_payments_status", "jinshuju_payments", ["status"])
