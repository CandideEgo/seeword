"""Explicit resource grants and minimal transactional delegated-learning receipts."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.v2_runtime import new_id, now


class ExternalLearningGrant(Base):
    __tablename__ = "external_learning_grants"

    connection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("external_connections.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resource_limits: Mapped[dict] = mapped_column(JSON, nullable=False)


class ExternalLearningOperation(Base):
    __tablename__ = "external_learning_operations"
    __table_args__ = (
        UniqueConstraint("user_id", "connection_id", "operation_id", name="uq_external_learning_operation"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    connection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("external_connections.id", ondelete="CASCADE"), index=True
    )
    operation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    resource: Mapped[dict] = mapped_column(JSON, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ExternalLearningIntent(Base):
    __tablename__ = "external_learning_intents"
    __table_args__ = (
        UniqueConstraint("user_id", "connection_id", "operation_id", name="uq_external_learning_intent"),
        Index("ix_external_learning_intents_expiry", "expires_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    connection_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("external_connections.id", ondelete="CASCADE"), index=True
    )
    operation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
