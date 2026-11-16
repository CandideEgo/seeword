"""Subtitle edit audit log — revision history for subtitle edits.

Every edit to a subtitle row (text / timing / grammar note / word_levels)
writes a ``SubtitleRevision`` capturing the before/after delta. This powers:
- the edit-history UI (``GET /admin/{video_id}/subtitles/revisions``),
- one-click rollback (``POST .../rollback/{revision_id}``),
- and the propose-back flow's lineage (Phase 3e PRs).

``scope`` distinguishes edits to a fork (private, ``scope="fork"`` — only
affects that user's copy) from edits to a standard version body (shared,
``scope="standard"`` — affects the baseline for all future forks of that URL).
The scope is decided by whether the edited video is the canonical standard for
its ``source_url`` (see ``_determine_edit_scope``).

``before`` / ``after`` store ONLY the fields that actually changed, as
``{field: old_value}`` / ``{field: new_value}`` — rollback writes ``before``
back. Word-level overrides are audited too (they are real edits).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Fields audited on every subtitle edit. Kept in sync with update_subtitle's
# edit loop and the rollback writer.
AUDITED_FIELDS = ("text_en", "text_zh", "start_time", "end_time", "grammar_note", "speaker", "word_levels")


class SubtitleRevision(Base):
    __tablename__ = "subtitle_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subtitle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subtitles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    video_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    edited_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # "fork" (private edit to a user's fork) | "standard" (edit to the URL's
    # canonical standard body — affects all future forks) | "sync" (a standard
    # version PR merge auto-propagated to an unedited fork line; edited_by=None).
    # "动过" detection for propagation keys off scope="fork" ONLY — a prior
    # "sync" does NOT count as the fork having edited the line.
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    # Only the fields that actually changed: {field: old_value} / {field: new_value}.
    before: Mapped[dict] = mapped_column(JSON, nullable=False)
    after: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
