"""add home editorial content tables (drafts / revisions / page config)

Revision ID: m3n4o5p6q7r8
Revises: j1i2n3s4h5u6
Create Date: 2026-10-20 06:00:00.000000

首页编辑内容（管理员换主推）的三张表，契约见
``backend/app/schemas/home_content.py``：

- ``home_content_drafts``：每视频一份可编辑草稿 + 生成任务状态机
- ``home_content_revisions``：只追加的不可变已发布版本（公共接口只读它）
- ``home_page_config``：单例布局（draft / published / previous）

本迁移**只建表**：不回填、不调用 AI、不改动既有精选（任务文档 §9 阶段 A）。
之外依赖的唯一既有结构是 ``videos``（video_id FK）与 ``users``（操作者 FK）。
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "m3n4o5p6q7r8"
down_revision: str | None = "j1i2n3s4h5u6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "home_content_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "video_id",
            sa.String(36),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_fingerprint", sa.String(64), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="idle"),
        sa.Column("active_generation_id", sa.String(36), nullable=True),
        sa.Column("last_generation_id", sa.String(36), nullable=True),
        sa.Column("generation_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generation_finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generation_error_code", sa.String(40), nullable=True),
        sa.Column("generation_error_message", sa.Text(), nullable=True),
        sa.Column("generation_draft_revision", sa.Integer(), nullable=True),
        sa.Column("generation_source_fingerprint", sa.String(64), nullable=True),
        sa.Column("generation_model", sa.String(100), nullable=True),
        sa.Column("generation_prompt_version", sa.String(40), nullable=True),
        sa.Column("generation_usage", sa.JSON(), nullable=True),
        sa.Column("generation_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "generated_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("uq_home_content_drafts_video_id", "home_content_drafts", ["video_id"], unique=True)

    op.create_table(
        "home_content_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "video_id",
            sa.String(36),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_fingerprint", sa.String(64), nullable=False),
        sa.Column("generation_model", sa.String(100), nullable=True),
        sa.Column("generation_prompt_version", sa.String(40), nullable=True),
        sa.Column(
            "generated_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "published_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("video_id", "version", name="uq_home_content_revisions_video_version"),
    )
    op.create_index("ix_home_content_revisions_video_id", "home_content_revisions", ["video_id"])

    op.create_table(
        "home_page_config",
        sa.Column("id", sa.String(16), primary_key=True),
        sa.Column("draft_layout", sa.JSON(), nullable=True),
        sa.Column("published_layout", sa.JSON(), nullable=True),
        sa.Column("previous_published_layout", sa.JSON(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_revision", sa.Integer(), nullable=True),
        sa.Column(
            "updated_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "published_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("home_page_config")
    op.drop_index("ix_home_content_revisions_video_id", table_name="home_content_revisions")
    op.drop_table("home_content_revisions")
    op.drop_index("uq_home_content_drafts_video_id", table_name="home_content_drafts")
    op.drop_table("home_content_drafts")
