"""性能：搜索/列表索引（2026-11）。

三张热表上的 ``ILIKE '%q%'``（前导通配）与「按用户 + 状态 + 时间排序」目前都
走顺序扫描；字幕表随视频增长后，搜索与首页「待复习」计数的成本会线性上升。

Postgres 专用部分：

* ``pg_trgm`` 扩展 + GIN trigram 索引，让 ``ILIKE '%…%'`` 能用索引。这几个索引
  是**方言专用**的，因此只在本迁移里创建，不写进 model 的 ``__table_args__``
  （``create_all`` 在 SQLite 上会把它降级成一个没用的普通 btree）。人工
  autogenerate 时会把它们当成「模型里没有的索引」，这是刻意的。
* 扩展需要 ``CREATE EXTENSION`` 权限。执行账号没有权限时本迁移会直接失败并
  报出权限错误（不静默降级）——由运维用有权限的账号先 ``CREATE EXTENSION
  pg_trgm`` 后重跑，或把这三条 GIN 语句拆到单独的运维脚本。

跨方言部分：两条复合 btree（用户 + 状态 + 时间），两套数据库都能用。

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-11-01 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers
revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (index name, table, column) — all queried with ILIKE '%…%' or plain ILIKE.
_TRGM_INDEXES: tuple[tuple[str, str, str], ...] = (
    ("ix_subtitles_text_en_trgm", "subtitles", "text_en"),
    ("ix_subtitles_text_zh_trgm", "subtitles", "text_zh"),
    ("ix_videos_title_trgm", "videos", "title"),
    ("ix_videos_title_zh_trgm", "videos", "title_zh"),
    ("ix_videos_topic_tags_trgm", "videos", "topic_tags"),
    ("ix_channels_name_trgm", "channels", "name"),
)


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        for name, table, column in _TRGM_INDEXES:
            op.execute(f'CREATE INDEX IF NOT EXISTS {name} ON {table} USING gin ("{column}" gin_trgm_ops)')

    op.create_index(
        "ix_learning_records_user_completed_accessed",
        "learning_records",
        ["user_id", "completed", "last_accessed_at"],
    )
    op.create_index(
        "ix_vocabulary_user_mastery_review",
        "vocabulary",
        ["user_id", "mastery_level", "next_review_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_vocabulary_user_mastery_review", table_name="vocabulary")
    op.drop_index("ix_learning_records_user_completed_accessed", table_name="learning_records")

    if op.get_bind().dialect.name == "postgresql":
        for name, _table, _column in _TRGM_INDEXES:
            op.execute(f"DROP INDEX IF EXISTS {name}")
        # The extension is left installed: other objects may depend on it, and
        # dropping it would fail if they do. It is harmless when unused.
