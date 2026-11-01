"""Aggregated "my learning" overview for the profile / discover rail.

The profile page used to fan out to five endpoints (users/me, plan/profile,
vocabulary/stats, learning/records, exams/stats) and still could not answer
"累计学了几天 / 一共多少分钟". One read model keeps those numbers consistent
and lets the client render the overview in a single round trip.

All figures are facts, not predictions: streak comes from the cached
``UserLearningProfile``, this week's minutes from ``behavior_events`` watch_time
bucketed by the user's local day (``study_time_service``), the all-time total
from the cumulative ``LearningRecord.time_spent_seconds`` counter (it cannot be
sliced by day), and the exam block reuses ``exam_service.exam_stats``.
"""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from app.models.exam_test import ExamAnswer, ExamSession
from app.models.favorite import UserFavorite, UserNote
from app.models.learning import LearningRecord
from app.models.learning_plan import LearningEvent, UserLearningProfile
from app.models.user_content import SentenceFavorite
from app.services import exam_service, vocabulary_service
from app.services.local_time import get_user_local_now, local_zone
from app.services.study_time_service import watch_seconds_by_local_day
from app.services.unlock_service import is_active_pro

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User


async def build_overview(db: AsyncSession, user: User) -> dict:
    local_now = await get_user_local_now(db, user.id)
    tz = local_zone(local_now)
    # 本周从**用户本地日**的周一起算：按 UTC 切周时，Asia/Shanghai 的用户
    # 周一 00:00–08:00 的学习会被算进上一周。
    this_monday = local_now.date() - timedelta(days=local_now.date().weekday())
    # 周窗换算成 UTC 交给事件聚合，分桶仍在本地日做（study_time_service）。
    week_start_utc = datetime.combine(this_monday, time.min, tzinfo=tz).astimezone(UTC)
    seconds_by_day = await watch_seconds_by_local_day(
        db,
        user.id,
        start=week_start_utc,
        end=datetime.now(UTC) + timedelta(minutes=1),
        tz=tz,
    )

    profile = (
        await db.execute(select(UserLearningProfile).where(UserLearningProfile.user_id == user.id))
    ).scalar_one_or_none()

    # 学过几天只认不可变的学习事件日期。旧实现还把
    # ``LearningRecord.last_accessed_at`` 与 ``created_at`` 并进来：前者会随
    # 每次观看移动（今天重看去年的视频就把那天记成今天），后者是「第一次打开
    # 这个视频」的日子，都不等于「那天学过」。因此历史用户的天数可能变少——
    # 这是真实值，不是回退，也不靠累计时长伪造缺失的日期。
    event_date_rows = (
        (await db.execute(select(LearningEvent.event_date).where(LearningEvent.user_id == user.id).distinct()))
        .scalars()
        .all()
    )
    days_studied = len(event_date_rows)

    # One aggregate for the whole "my videos" block: rows started, rows
    # completed and the cumulative watched-seconds counter.
    started_videos, completed_videos, total_seconds = (
        await db.execute(
            select(
                func.count(LearningRecord.id),
                func.count(LearningRecord.id).filter(LearningRecord.completed.is_(True)),
                func.coalesce(func.sum(LearningRecord.time_spent_seconds), 0),
            ).where(LearningRecord.user_id == user.id)
        )
    ).one()
    total_minutes = int(total_seconds or 0) // 60

    week_event_dates = {day for day in event_date_rows if day >= this_monday}
    daily: list[dict[str, Any]] = []
    for i in range(7):
        day_date = this_monday + timedelta(days=i)
        minutes = seconds_by_day.get(day_date, 0) // 60
        # 做卷子、背词会写 LearningEvent 但不记观看时长。只按分钟判断的话，
        # 同一个卡片会出现「连续学习 1 天」和「有学习的天数 0/7」。
        daily.append(
            {
                "date": day_date.isoformat(),
                "minutes": minutes,
                "active": minutes > 0 or day_date in week_event_dates,
            }
        )
    week_minutes = sum(item["minutes"] for item in daily)
    week_active_days = sum(1 for item in daily if item["active"])

    words = await vocabulary_service.get_stats(db, user.id)
    exam_summary = await exam_service.exam_stats(db, user.id)

    # Exam counters and library counters in one round trip. These used to be
    # seven separate ``SELECT count(*)`` / ``max()`` statements; as correlated
    # scalar subqueries they still use the same user_id indexes but cost one
    # network round trip instead of seven.
    submitted = ExamSession.submitted_at.is_not(None)
    attempt_count_sq = (
        select(func.count(ExamSession.id)).where(ExamSession.user_id == user.id, submitted).scalar_subquery()
    )
    answered_sq = (
        select(func.count(ExamAnswer.id))
        .join(ExamSession, ExamAnswer.session_id == ExamSession.id)
        .where(ExamSession.user_id == user.id, ExamAnswer.correct.is_not(None))
        .scalar_subquery()
    )
    correct_sq = (
        select(func.count(ExamAnswer.id))
        .join(ExamSession, ExamAnswer.session_id == ExamSession.id)
        .where(ExamSession.user_id == user.id, ExamAnswer.correct.is_(True))
        .scalar_subquery()
    )
    last_submitted_sq = (
        select(func.max(ExamSession.submitted_at)).where(ExamSession.user_id == user.id, submitted).scalar_subquery()
    )
    favorite_videos_sq = select(func.count(UserFavorite.id)).where(UserFavorite.user_id == user.id).scalar_subquery()
    favorite_sentences_sq = (
        select(func.count(SentenceFavorite.id)).where(SentenceFavorite.user_id == user.id).scalar_subquery()
    )
    note_count_sq = select(func.count(UserNote.id)).where(UserNote.user_id == user.id).scalar_subquery()

    (
        attempt_count,
        answered,
        correct,
        last_submitted,
        favorite_videos,
        favorite_sentences,
        note_count,
    ) = (
        await db.execute(
            select(
                attempt_count_sq,
                answered_sq,
                correct_sq,
                last_submitted_sq,
                favorite_videos_sq,
                favorite_sentences_sq,
                note_count_sq,
            )
        )
    ).one()

    membership_expires = user.plan_expires_at
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "plan": user.plan.value if hasattr(user.plan, "value") else str(user.plan),
            "plan_expires_at": membership_expires,
            "created_at": user.created_at,
        },
        "streak": {
            "current": profile.current_streak if profile else 0,
            "longest": profile.longest_streak if profile else 0,
            "last_active_date": profile.last_active_date if profile else None,
        },
        "learning": {
            "days_studied": days_studied,
            "total_minutes": total_minutes,
            "estimated_level": profile.estimated_level if profile else None,
        },
        "this_week": {
            "start_date": this_monday.isoformat(),
            "minutes": week_minutes,
            "days_active": week_active_days,
            "daily": daily,
        },
        "words": words,
        "videos": {"started": started_videos, "completed": completed_videos},
        "exams": {
            "attempts": attempt_count,
            "month_completed": exam_summary["month_completed"],
            "avg_score": exam_summary["avg_score"],
            "answered": answered,
            "correct": correct,
            "last_submitted_at": last_submitted,
        },
        "library": {
            "favorite_videos": favorite_videos,
            "favorite_sentences": favorite_sentences,
            "notes": note_count,
        },
        "membership": {
            "is_pro": is_active_pro(user),
            "expires_at": membership_expires,
        },
    }
