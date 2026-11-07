"""Standalone tutor conversations, with legacy task chats backfilled.

Each existing teaching session that already has messages gets one
``kind="task"`` conversation, so the legacy per-session message endpoint keeps
the same transcript. New chats may reference several tasks; a message's
``session_id``/``content_revision_id`` stay set only while it is about a task.

Revision ID: c4a1b2c3d4e5
Revises: d4e5f6a7b8c9
"""

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "c4a1b2c3d4e5"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _conversation_id(session_id: str) -> str:
    return "conv-" + hashlib.md5(session_id.encode()).hexdigest()[:31]


def _backfill_task_chats() -> None:
    """One conversation per session that already has messages; ordered as before.

    The owner is taken from the session, not the message, so two users can
    never map onto one ``task_session_id`` (which is unique).
    """
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT DISTINCT s.id, s.user_id FROM teaching_sessions s "
            "WHERE EXISTS (SELECT 1 FROM teaching_messages m WHERE m.session_id = s.id)"
        )
    ).fetchall()
    now = datetime.now(UTC)
    for session_id, user_id in rows:
        conversation_id = _conversation_id(session_id)
        bind.execute(
            sa.text(
                "INSERT INTO tutor_conversations "
                "(id, user_id, title, status, kind, task_session_id, created_at, updated_at) "
                "VALUES (:id, :user_id, :title, :status, :kind, :task_session_id, :created_at, :updated_at)"
            ),
            {
                "id": conversation_id,
                "user_id": user_id,
                "title": "任务对话",
                "status": "active",
                "kind": "task",
                "task_session_id": session_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        bind.execute(
            sa.text(
                "INSERT INTO tutor_conversation_tasks (id, conversation_id, session_id, created_at) "
                "VALUES (:id, :conversation_id, :session_id, :created_at)"
            ),
            {
                "id": "ctk-" + hashlib.md5(session_id.encode()).hexdigest()[:31],
                "conversation_id": conversation_id,
                "session_id": session_id,
                "created_at": now,
            },
        )
        bind.execute(
            sa.text("UPDATE teaching_messages SET conversation_id = :id WHERE session_id = :session_id"),
            {"id": conversation_id, "session_id": session_id},
        )


def upgrade() -> None:
    op.create_table(
        "tutor_conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(120), nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("kind", sa.String(20), nullable=False, server_default="chat"),
        sa.Column("task_session_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_session_id"], ["teaching_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("task_session_id", name="uq_tutor_conversation_task_session"),
    )
    op.create_index("ix_tutor_conversation_user_updated", "tutor_conversations", ["user_id", "updated_at"])
    op.create_table(
        "tutor_conversation_tasks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["tutor_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["teaching_sessions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("conversation_id", "session_id", name="uq_tutor_conversation_task"),
    )
    op.create_index("ix_tutor_conversation_tasks_conversation_id", "tutor_conversation_tasks", ["conversation_id"])
    op.create_index("ix_tutor_conversation_tasks_session_id", "tutor_conversation_tasks", ["session_id"])

    op.add_column("teaching_messages", sa.Column("conversation_id", sa.String(36), nullable=True))
    _backfill_task_chats()
    op.alter_column("teaching_messages", "conversation_id", nullable=False)
    op.create_foreign_key(
        "fk_teaching_messages_conversation_id",
        "teaching_messages",
        "tutor_conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("teaching_messages", "session_id", existing_type=sa.String(36), nullable=True)
    op.alter_column("teaching_messages", "content_revision_id", existing_type=sa.String(36), nullable=True)
    op.alter_column("teaching_messages", "session_revision", existing_type=sa.Integer(), nullable=True)
    op.drop_constraint("uq_teaching_message_sequence", "teaching_messages", type_="unique")
    op.create_unique_constraint(
        "uq_teaching_message_conversation_sequence", "teaching_messages", ["conversation_id", "sequence"]
    )

    op.add_column("agent_runs", sa.Column("conversation_id", sa.String(36), nullable=True))
    op.create_foreign_key(
        "fk_agent_runs_conversation_id",
        "agent_runs",
        "tutor_conversations",
        ["conversation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_agent_runs_conversation_id", "agent_runs", ["conversation_id"])
    op.alter_column("agent_runs", "session_id", existing_type=sa.String(36), nullable=True)
    op.alter_column("agent_runs", "bound_session_revision", existing_type=sa.Integer(), nullable=True)

    op.alter_column("agent_run_events", "session_revision", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    op.alter_column("agent_run_events", "session_revision", existing_type=sa.Integer(), nullable=False)
    op.alter_column("agent_runs", "bound_session_revision", existing_type=sa.Integer(), nullable=False)
    op.alter_column("agent_runs", "session_id", existing_type=sa.String(36), nullable=False)
    op.drop_index("ix_agent_runs_conversation_id", table_name="agent_runs")
    op.drop_constraint("fk_agent_runs_conversation_id", "agent_runs", type_="foreignkey")
    op.drop_column("agent_runs", "conversation_id")

    op.drop_constraint("uq_teaching_message_conversation_sequence", "teaching_messages", type_="unique")
    op.create_unique_constraint("uq_teaching_message_sequence", "teaching_messages", ["session_id", "sequence"])
    op.alter_column("teaching_messages", "session_revision", existing_type=sa.Integer(), nullable=False)
    op.alter_column("teaching_messages", "content_revision_id", existing_type=sa.String(36), nullable=False)
    op.alter_column("teaching_messages", "session_id", existing_type=sa.String(36), nullable=False)
    op.drop_constraint("fk_teaching_messages_conversation_id", "teaching_messages", type_="foreignkey")
    op.drop_column("teaching_messages", "conversation_id")

    op.drop_index("ix_tutor_conversation_tasks_session_id", table_name="tutor_conversation_tasks")
    op.drop_index("ix_tutor_conversation_tasks_conversation_id", table_name="tutor_conversation_tasks")
    op.drop_table("tutor_conversation_tasks")
    op.drop_index("ix_tutor_conversation_user_updated", table_name="tutor_conversations")
    op.drop_table("tutor_conversations")
