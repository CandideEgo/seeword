"""V2 execution metadata. Provider usage/cost remains owned by the gateway."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    inspect,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def new_id() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class TeachingAccessGrant(Base):
    __tablename__ = "teaching_access_grants"
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ExternalConnection(Base):
    __tablename__ = "external_connections"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    host_label: Mapped[str] = mapped_column(String(100))
    granted_scopes: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ExternalCredential(Base):
    __tablename__ = "external_credentials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    connection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("external_connections.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        UniqueConstraint("user_id", "operation_id", name="uq_agent_run_user_operation"),
        Index(
            "uq_agent_run_active_session",
            "session_id",
            unique=True,
            postgresql_where=text("status IN ('queued','running')"),
            sqlite_where=text("status IN ('queued','running')"),
        ),
        Index(
            "uq_agent_run_active_user",
            "user_id",
            unique=True,
            postgresql_where=text("status IN ('queued','running')"),
            sqlite_where=text("status IN ('queued','running')"),
        ),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teaching_sessions.id", ondelete="CASCADE"), index=True
    )
    operation_id: Mapped[str] = mapped_column(String(100))
    request_hash: Mapped[str] = mapped_column(String(64))
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_mode: Mapped[str] = mapped_column(String(20), default="cards", server_default="cards")
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    bound_session_revision: Mapped[int] = mapped_column(Integer)
    lease_epoch: Mapped[int] = mapped_column(Integer, default=0)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sequence: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    queue_deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    execution_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentStep(Base):
    __tablename__ = "agent_steps"
    __table_args__ = (UniqueConstraint("run_id", "seq", name="uq_agent_step_run_seq"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    lease_epoch: Mapped[int] = mapped_column(Integer)
    logical_call_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    safe_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AgentRunEvent(Base):
    __tablename__ = "agent_run_events"
    __table_args__ = (UniqueConstraint("run_id", "sequence", name="uq_agent_event_sequence"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(40))
    session_revision: Mapped[int] = mapped_column(Integer)
    safe_payload: Mapped[dict] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TeachingMessage(Base):
    """Task conversation survives short-lived execution logs; never a grading fact."""

    __tablename__ = "teaching_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_teaching_message_sequence"),
        UniqueConstraint("run_id", "role", name="uq_teaching_message_run_role"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teaching_sessions.id", ondelete="CASCADE"), index=True
    )
    content_revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("exam_analysis_revisions.id", ondelete="RESTRICT")
    )
    run_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    session_revision: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(20))
    body: Mapped[dict] = mapped_column(JSON)
    requires_reveal: Mapped[bool] = mapped_column(Boolean, default=False)
    # complete | streaming | interrupted. Only the final projection changes;
    # the text itself lives in immutable blocks (P02.2).
    status: Mapped[str] = mapped_column(String(20), default="complete", server_default="complete")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TeachingMessageBlock(Base):
    """One immutable piece of streamed reply text; published when committed."""

    __tablename__ = "teaching_message_blocks"
    # The unique constraint's leading column also serves message_id lookups
    # (page, export, model history, purge); no separate index is needed.
    __table_args__ = (UniqueConstraint("message_id", "ordinal", name="uq_teaching_message_block_ordinal"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("teaching_messages.id", ondelete="CASCADE"))
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


@event.listens_for(TeachingMessageBlock, "before_update")
def _immutable_block(_mapper, _connection, target):
    for attr in inspect(target).attrs:
        if attr.history.has_changes():
            raise ValueError("Teaching message blocks are append-only")


class GatewayLifecycleIntent(Base):
    """Survives account deletion until the remote idempotent operation is acknowledged."""

    __tablename__ = "gateway_lifecycle_intents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    subject_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    receipt: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
