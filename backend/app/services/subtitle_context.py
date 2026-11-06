"""Resolve a word's source against the subtitles the viewer may actually see."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ErrorCode, NotFoundError
from app.models.subtitle import Subtitle
from app.models.user import User
from app.models.video import Video
from app.services.video_access import check_video_access, should_use_snapshot


async def resolve_context(db: AsyncSession, user: User, video_id: str | None, subtitle_id: str) -> str:
    if not video_id:
        raise AppError(422, ErrorCode.VALIDATION_ERROR, "字幕来源需要视频 ID")
    video = await db.get(Video, video_id)
    if video is None or not check_video_access(video, user):
        raise NotFoundError("原句不存在或不可访问")
    if should_use_snapshot(video, user):
        from app.services.video_publish import subtitles_from_snapshot

        snapshot_sub = next((s for s in subtitles_from_snapshot(video.published_snapshot) if s.id == subtitle_id), None)
        text = snapshot_sub.text_en if snapshot_sub else None
    else:
        sub = (
            await db.execute(select(Subtitle).where(Subtitle.id == subtitle_id, Subtitle.video_id == video_id))
        ).scalar_one_or_none()
        text = sub.text_en if sub else None
    if text is None:
        raise AppError(409, ErrorCode.CONFLICT, "原句位置已变化，请重新选择字幕")
    return text
