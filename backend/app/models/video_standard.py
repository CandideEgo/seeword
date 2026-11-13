"""Standard Version registry — one canonical video per source_url.

A "standard version" is the shared baseline for a ``source_url``: the first
video to reach ``ready`` for that URL becomes its standard, and all subsequent
submissions fork from it (copying subtitles + practice + metadata) instead of
re-running the GPU pipeline. See ADR-0006.

``source_url`` is the PK → the DB enforces "one URL, one standard" and
prevents concurrent finalize races from creating two standards. Replacing a
standard (Grilling 决议 7) is an atomic repoint of ``canonical_video_id``;
the old standard video demotes to a plain Video (its media kept if forks
exist). The standard is a *role*, not an intrinsic property of a Video row,
which is why it lives in a separate table rather than a flag on ``videos``.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VideoStandard(Base):
    __tablename__ = "video_standards"

    # PK = source_url → "one URL, one standard" enforced at the DB layer.
    source_url: Mapped[str] = mapped_column(String(2000), primary_key=True)
    canonical_video_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # The canonical Video for this URL. Single-direction (no back_populates on
    # Video) to keep the Video model free of standard-version concerns.
    canonical_video = relationship("Video", foreign_keys=[canonical_video_id])
