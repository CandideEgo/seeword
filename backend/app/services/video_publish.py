"""Shared video publish + subtitle-snapshot helpers.

Extracted from `video_review_service.py` (ADR-0012) so the UGC review lifecycle
can be deleted without breaking the pipeline's auto_publish path or the
public-snapshot subtitle serving. Both the admin approval flow (until removed)
and `finalize_video`'s auto_publish call `_publish_video`; `video_service`
serves a frozen approved snapshot via `subtitles_from_snapshot`.
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import commit_refresh
from app.models.video import Video, VideoReviewStatus
from app.schemas.video import SubtitleResponse
from app.services.video_cache import invalidate_video_detail_cache
from app.services.video_playback import require_publishable


def subtitles_from_snapshot(snapshot: dict | None) -> list[SubtitleResponse]:
    """Build SubtitleResponse list from a frozen published_snapshot.

    The snapshot is written by ``video_review_service`` (which owns its
    ``version`` field); this side only reads the subtitles array. There used to
    be a second ``_SNAPSHOT_VERSION`` constant here that nobody read — two
    copies of a version number that only one writer maintains.
    """
    if not snapshot:
        return []
    raw = snapshot.get("subtitles") or []
    out: list[SubtitleResponse] = []
    for s in raw:
        out.append(
            SubtitleResponse(
                id=s.get("id", ""),
                start_time=s.get("start_time", 0.0),
                end_time=s.get("end_time", 0.0),
                text_en=s.get("text_en", ""),
                text_zh=s.get("text_zh"),
                sentence_index=s.get("sentence_index", 0),
                grammar_note=s.get("grammar_note"),
                speaker=s.get("speaker"),
                word_levels=s.get("word_levels"),
            )
        )
    return out


async def _publish_video(
    db: AsyncSession,
    video: Video,
    reviewed_by: str | None = None,
) -> None:
    """Shared publish helper: sets is_published, review_status, reviewed_by, reviewed_at.

    This is the single source of truth for publishing a video. Both admin approval
    and auto_publish call this to ensure consistent data.
    """
    await require_publishable(video)
    video.is_published = True
    video.review_status = VideoReviewStatus.published.value
    video.reviewed_by = reviewed_by
    now = datetime.now(UTC)
    video.reviewed_at = now
    if video.published_at is None:
        # First publish only — later re-review cycles must not move the
        # original publish timestamp (homepage 「最新」 ranking sort key).
        video.published_at = now
    video.rejection_reason = None
    await commit_refresh(db, video)
    await invalidate_video_detail_cache(video.id)
