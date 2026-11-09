"""Video channels - author pages (ADR-0014, rev. 2026-08-30).

Channels are the "content source" dimension, orthogonal to the topic-tag
dimension used by recommendations. Since the 2026-08-30 revision (full author
pages), every video ingested with a scraped upstream ``channel_id``
auto-creates a channel (``is_auto=True``) so each author has a browsable
home; admins curate rows by editing them (``is_auto=False`` marks rows
created by hand). The scraped upstream fields on Video
(``channel_id`` / ``channel_name``) stay as external metadata;
``Channel.upstream_channel_id`` bridges the two - videos are auto-attached
by matching their scraped ``channel_id``.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Channel(Base):
    __tablename__ = "channels"
    __table_args__ = (
        # pg_trgm GIN index from migration ``c9d0e1f2a3b4`` (PostgreSQL only).
        Index("ix_channels_name_trgm", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # Upstream (YouTube/Bilibili) channel id; registering it lets ingest and
    # the backfill script attach matching videos automatically.
    upstream_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # ADR-0014 rev. 2026-08-30 (full author pages): True when auto-created at
    # ingest from a scraped upstream channel id; False for admin-curated rows.
    is_auto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
