"""Learning records API — list and detail endpoints for per-video learning progress."""

from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.limiter import rate_limit
from app.models.learning import LearningRecord
from app.models.learning_plan import LearningEvent
from app.models.user import User
from app.models.video import Video
from app.schemas.common import VideoBrief
from app.schemas.learning import (
    ContinueLearningResponse,
    EventDistributionItem,
    LearningRecordResponse,
    SaveProgressRequest,
    SaveProgressResponse,
    WatchProgressResponse,
    WeeklyStatsResponse,
)
from app.schemas.pagination import PaginatedResponse, paginated
from app.services.local_time import get_user_local_now, local_zone
from app.services.study_time_service import watch_seconds_by_local_day, week_start_local

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/records", response_model=PaginatedResponse[LearningRecordResponse])
@rate_limit("30/minute")
async def list_learning_records(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    completed: bool | None = Query(None, description="Filter by completion status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's per-video learning records with video info."""
    offset = (page - 1) * page_size

    # Build query
    stmt = (
        select(LearningRecord, Video)
        .join(Video, LearningRecord.video_id == Video.id)
        .where(LearningRecord.user_id == current_user.id)
        .order_by(LearningRecord.last_accessed_at.desc().nullslast(), LearningRecord.created_at.desc())
    )

    if completed is not None:
        stmt = stmt.where(LearningRecord.completed == completed)

    # Total count
    count_stmt = select(func.count(LearningRecord.id)).where(LearningRecord.user_id == current_user.id)
    if completed is not None:
        count_stmt = count_stmt.where(LearningRecord.completed == completed)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Fetch records with video info
    result = await db.execute(stmt.offset(offset).limit(page_size))

    records = []
    for lr, video in result.all():
        video_info = VideoBrief.model_validate(video)
        record_resp = LearningRecordResponse(
            id=lr.id,
            video_id=lr.video_id,
            words_learned=lr.words_learned,
            speaking_attempts=lr.speaking_attempts,
            quiz_score=lr.quiz_score,
            completed=lr.completed,
            time_spent_seconds=lr.time_spent_seconds,
            last_accessed_at=lr.last_accessed_at,
            progress_percentage=lr.progress_percentage,
            position_seconds=lr.position_seconds,
            created_at=lr.created_at,
            video=video_info,
        )
        records.append(record_resp)

    return paginated(records, page=page, page_size=page_size, total=total)


@router.get("/continue", response_model=ContinueLearningResponse)
@rate_limit("30/minute")
async def continue_learning(
    request: Request,
    limit: int = Query(1, ge=1, le=5),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """In-progress videos as feed cards, newest activity first.

    "Continue learning" needs the video card + resume position in one call;
    the generic records endpoint returns ``VideoBrief`` and makes the client
    join three more requests to render the strip. Only genuinely started
    (progress > 0) and still-unfinished records qualify.
    """
    from app.services.channel_service import channel_slugs_for
    from app.services.discovery_service import public_video_filters
    from app.services.video_card import video_card_payload

    rows = (
        await db.execute(
            select(LearningRecord, Video)
            .join(Video, LearningRecord.video_id == Video.id)
            .where(
                LearningRecord.user_id == current_user.id,
                LearningRecord.completed.is_(False),
                LearningRecord.progress_percentage > 0,
                *public_video_filters(),
            )
            .order_by(
                LearningRecord.last_accessed_at.desc().nullslast(),
                LearningRecord.created_at.desc(),
            )
            .limit(limit)
        )
    ).all()
    videos = [video for _, video in rows]
    slug_map = await channel_slugs_for(db, videos)
    items = []
    for record, video in rows:
        position = float(record.position_seconds or 0)
        duration = float(video.duration or 0)
        items.append(
            {
                "video": video_card_payload(video, slug_map.get(video.channel_ref) if video.channel_ref else None),
                "position_seconds": position,
                "progress_percentage": float(record.progress_percentage or 0),
                "remaining_seconds": max(0.0, round(duration - position, 1)) if duration else None,
                "last_accessed_at": record.last_accessed_at,
            }
        )
    return {"items": items, "total": len(items)}


@router.get("/records/{record_id}", response_model=LearningRecordResponse)
@rate_limit("30/minute")
async def get_learning_record(
    request: Request,
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single learning record detail."""
    result = await db.execute(
        select(LearningRecord).where(
            LearningRecord.id == record_id,
            LearningRecord.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Learning record not found")

    # Fetch associated video
    video_result = await db.execute(select(Video).where(Video.id == record.video_id))
    video = video_result.scalar_one_or_none()

    video_info = None
    if video:
        video_info = VideoBrief.model_validate(video)

    return LearningRecordResponse(
        id=record.id,
        video_id=record.video_id,
        words_learned=record.words_learned,
        speaking_attempts=record.speaking_attempts,
        quiz_score=record.quiz_score,
        completed=record.completed,
        time_spent_seconds=record.time_spent_seconds,
        last_accessed_at=record.last_accessed_at,
        progress_percentage=record.progress_percentage,
        position_seconds=record.position_seconds,
        created_at=record.created_at,
        video=video_info,
    )


@router.patch("/progress", response_model=SaveProgressResponse)
@rate_limit("30/minute")
async def save_watch_progress(
    request: Request,
    body: SaveProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save or update the user's watch progress for a video.

    Called periodically by the frontend (debounced) to persist the
    current playback position. Also updates progress_percentage
    based on position vs video duration.
    """
    from app.services.watch_progress_service import save_position

    record = await save_position(db, current_user.id, body.video_id, body.position_seconds)

    return SaveProgressResponse(
        position_seconds=record.position_seconds or 0.0,
        progress_percentage=record.progress_percentage or 0.0,
    )


@router.get("/progress/{video_id}", response_model=WatchProgressResponse)
@rate_limit("30/minute")
async def get_watch_progress(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's watch progress for a specific video.

    Returns the saved playback position so the frontend can
    resume from where the user left off.
    """
    result = await db.execute(
        select(LearningRecord).where(
            LearningRecord.user_id == current_user.id,
            LearningRecord.video_id == video_id,
        )
    )
    record = result.scalar_one_or_none()

    return {
        "video_id": video_id,
        "position_seconds": record.position_seconds if record else None,
        "progress_percentage": record.progress_percentage if record else 0.0,
    }


# ──────────────────────────────────────────────────────────────────────
# Phase 1 B0 — profile stats (D5 激励体系)
# ──────────────────────────────────────────────────────────────────────


@router.get("/stats/weekly", response_model=WeeklyStatsResponse)
@rate_limit("30/minute")
async def stats_weekly(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated weekly activity for the profile 学习进度 page.

    - this_week_minutes / last_week_minutes / daily_minutes: 有效学习秒数，来自
      视频的 ``behavior_events.watch_time`` 与课程的 ``lesson_activities``，
      按**用户本地日**分桶（study_time_service）。与个人页 overview 用同一个函数，
      两个页面不会给出互相矛盾的「本周学了多久」。
      旧实现按 UTC 切周、按 UTC 日分桶，Asia/Shanghai 的用户在周一 00:00–08:00
      的学习会被算进上一周。
    - week_delta_pct: 0.0 when last week is 0 (handle "first week" UI)
    - this_week_words/videos: counted from LearningEvent (learned_words /
      completed_video) so they reflect this calendar week
    """
    local_now = await get_user_local_now(db, current_user.id)
    tz = local_zone(local_now)
    this_monday = week_start_local(local_now)
    last_monday = this_monday - timedelta(days=7)

    def _utc_at(day: date) -> datetime:
        """本地某天 00:00 对应的 UTC 时刻。"""
        return datetime.combine(day, time.min, tzinfo=tz).astimezone(UTC)

    now_utc = datetime.now(UTC) + timedelta(minutes=1)
    this_week = await watch_seconds_by_local_day(db, current_user.id, start=_utc_at(this_monday), end=now_utc, tz=tz)
    last_week = await watch_seconds_by_local_day(
        db, current_user.id, start=_utc_at(last_monday), end=_utc_at(this_monday), tz=tz
    )

    # 逐日取整后再求和 —— 与 overview 的每日卡片同一算法，否则两边会因为
    # 「先求和再除 60」与「先除 60 再求和」差出几分钟。
    this_week_minutes = sum(this_week.get(this_monday + timedelta(days=i), 0) // 60 for i in range(7))
    last_week_minutes = sum(last_week.get(last_monday + timedelta(days=i), 0) // 60 for i in range(7))

    if last_week_minutes > 0:
        week_delta_pct = round((this_week_minutes - last_week_minutes) / last_week_minutes * 100, 1)
    else:
        week_delta_pct = None  # "first week" → UI shows no arrow

    async def _event_count(event_type: str, start: date) -> int:
        result = await db.execute(
            select(func.coalesce(func.sum(LearningEvent.event_value), 0)).where(
                LearningEvent.user_id == current_user.id,
                LearningEvent.event_type == event_type,
                LearningEvent.event_date >= start,
            )
        )
        return result.scalars().one()

    this_week_words = await _event_count("learned_words", this_monday)
    this_week_videos = await _event_count("completed_video", this_monday)

    # Daily minutes for the 7 days of this week, Mon→Sun, from the same
    # local-day buckets as the weekly totals above.
    daily_minutes: list[dict] = [
        {
            "date": (this_monday + timedelta(days=i)).isoformat(),
            "minutes": this_week.get(this_monday + timedelta(days=i), 0) // 60,
        }
        for i in range(7)
    ]

    return {
        "this_week_minutes": this_week_minutes,
        "last_week_minutes": last_week_minutes,
        "week_delta_pct": week_delta_pct,
        "this_week_words": this_week_words,
        "this_week_videos": this_week_videos,
        "daily_minutes": daily_minutes,
    }


@router.get("/stats/event-distribution", response_model=list[EventDistributionItem])
@rate_limit("30/minute")
async def stats_event_distribution(
    request: Request,
    days: int = Query(30, ge=1, le=180),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sum of LearningEvent.event_value grouped by event_type over the last N days.

    Used by the profile EventDistributionChart (D5). The frontend maps
    event_type → Chinese label and color.
    """
    cutoff = (datetime.now(UTC) - timedelta(days=days)).date()
    rows = (
        await db.execute(
            select(
                LearningEvent.event_type,
                func.coalesce(func.sum(LearningEvent.event_value), 0).label("total"),
            )
            .where(
                LearningEvent.user_id == current_user.id,
                LearningEvent.event_date >= cutoff,
            )
            .group_by(LearningEvent.event_type)
        )
    ).all()
    return [{"event_type": r.event_type, "count": int(r.total)} for r in rows]


@router.get("/stats/heatmap")
@rate_limit("30/minute")
async def stats_heatmap(
    request: Request,
    days: int = Query(90, ge=30, le=180),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.retired_features import feature_gone

    feature_gone()


@router.get("/weekly-reports")
@rate_limit("30/minute")
async def list_weekly_reports(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.retired_features import feature_gone

    feature_gone()


@router.get("/weekly-reports/latest")
@rate_limit("30/minute")
async def latest_weekly_report(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.retired_features import feature_gone

    feature_gone()
