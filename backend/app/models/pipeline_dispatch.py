"""Pipeline task outbox — durable "this task must run" intent (A05/BE-01).

The pipeline used to commit its DB state and then call ``.delay()``. Those are
two systems, so the window between them loses work: a broker hiccup or a crash
right after the commit leaves the video stranded. Re-calling the callback does
not help — the status guard acknowledges it as a duplicate — and the watchdog
only marks the video failed.

This table closes that window: the intent is written in the **same
transaction** as the state change, a best-effort inline attempt follows the
commit, and ``dispatch_pipeline_tasks`` (beat) re-sends anything still
pending. Delivery is at-least-once; both pipeline tasks are idempotent under
the Redis processing lock and the completed-step set, so a duplicate send is
harmless.

Rows are kept after dispatch for auditing (attempts, last error) and pruned by
the same beat task after the retention window.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

#: Waiting for (re)dispatch; the dispatcher scans these.
DISPATCH_STATUS_PENDING = "pending"
#: Handed to the broker at least once. Not proof the task ran — that is the
#: video's own state, which the watchdog still owns.
DISPATCH_STATUS_DISPATCHED = "dispatched"
#: The video moved past the state this task applies to, or was deleted.
DISPATCH_STATUS_ABANDONED = "abandoned"


class PipelineDispatch(Base):
    __tablename__ = "pipeline_dispatches"
    __table_args__ = (
        # One live intent per (video, task): a duplicate callback, a resumed head
        # and the dispatcher all address the same row instead of queuing the
        # task twice. Re-enqueuing re-arms the row (see pipeline_dispatch.enqueue).
        UniqueConstraint("video_id", "task_name", name="uq_pipeline_dispatches_video_task"),
        Index("ix_pipeline_dispatches_status_next", "status", "next_attempt_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Celery task name (the cloud only knows names — the GPU task is not
    # registered in this app).
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    # ``None`` = the default queue. The GPU task carries ``transcription_gpu``.
    queue: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Positional args for ``send_task``. Rewritten by every re-enqueue: a fresh
    # intent may carry a fresh signed URL, a retry of the same intent reuses it.
    args: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    processing_generation: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=DISPATCH_STATUS_PENDING)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    # Retry backoff for send failures; NULL means "due now".
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
