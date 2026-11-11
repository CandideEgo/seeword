"""有效学习时长的聚合读模型（A02 / BE-06 / MET-01）。

使用视频与课程各自的 ``watch_time`` 事件，按用户本地日分桶。

为什么不再用 ``LearningRecord.time_spent_seconds``：那是一个**累计计数器**，
一行一个用户/视频。拿 ``last_accessed_at`` 给它切片，会把这条记录的全部历史
时长记到最近一次访问的那天——今天重看一个去年看过的视频，去年那一周凭空多出
几百分钟。个人页（overview）与周统计（learning/stats/weekly）必须用同一个
函数，否则两个页面会给出互相矛盾的「本周学了多久」。

口径本身（什么算有效学习秒数）在 ``lib/watchTime.ts``（前端）与本模块的
docstring 里各写一次：播放中且页面可见的墙钟秒数。2026-10-29 之前的
watch_time 数据来自 v1 的位置差算法，与新口径不可比。
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import func, inspect, select

from app.models.behavior import BehaviorEvent
from app.models.lesson import LessonActivity

if TYPE_CHECKING:
    from zoneinfo import ZoneInfo

    from sqlalchemy.ext.asyncio import AsyncSession

EVENT_WATCH_TIME = "watch_time"


async def watch_seconds_by_local_day(
    db: AsyncSession,
    user_id: str,
    *,
    start: datetime,
    end: datetime,
    tz: ZoneInfo,
) -> dict[date, int]:
    """按用户本地日汇总 ``[start, end)`` 内的有效学习秒数。

    ``start`` / ``end`` 是 aware UTC 时刻。分桶必须落在**用户本地日**：
    ``func.date(server_ts)`` 只会换到数据库时区（UTC），对 Asia/Shanghai 的
    用户来说 00:00–08:00 会被算进前一天。

    On Postgres the bucketing and the sum both happen in SQL (``timezone(tz,
    server_ts)`` → local wall clock), so a busy week returns at most one row per
    day instead of every ``watch_time`` event. The in-memory SQLite used by the
    test suite has no ``timezone()`` function, so it keeps the row-walking path;
    both paths produce the same dictionary.
    """
    filters = (
        BehaviorEvent.user_id == user_id,
        BehaviorEvent.event_type == EVENT_WATCH_TIME,
        BehaviorEvent.server_ts >= start,
        BehaviorEvent.server_ts < end,
    )
    events = select(
        BehaviorEvent.server_ts.label("recorded_at"),
        BehaviorEvent.event_payload["delta_s"].as_float().label("seconds"),
    ).where(*filters)
    connection = await db.connection()
    if await connection.run_sync(lambda sync: inspect(sync).has_table(LessonActivity.__tablename__)):
        samples = events.union_all(
            select(LessonActivity.created_at, LessonActivity.delta_s).where(
                LessonActivity.user_id == user_id,
                LessonActivity.event_type == EVENT_WATCH_TIME,
                LessonActivity.created_at >= start,
                LessonActivity.created_at < end,
            )
        ).subquery()
    else:
        samples = events.subquery()

    if db.get_bind().dialect.name == "postgresql":
        local_day = func.date(func.timezone(tz.key, samples.c.recorded_at))
        rows = (
            await db.execute(
                select(local_day.label("day"), func.sum(samples.c.seconds).label("seconds")).group_by(local_day)
            )
        ).all()
        return {day: int(seconds) for day, seconds in rows if day is not None and seconds is not None}

    rows = (await db.execute(select(samples.c.recorded_at, samples.c.seconds))).all()

    totals: dict[date, float] = {}
    for server_ts, delta in rows:
        if server_ts is None or delta is None:
            continue
        if server_ts.tzinfo is None:
            server_ts = server_ts.replace(tzinfo=UTC)
        day = server_ts.astimezone(tz).date()
        totals[day] = totals.get(day, 0.0) + float(delta)

    return {day: int(seconds) for day, seconds in totals.items()}


def week_start_local(local_now: datetime) -> date:
    """本地日视角下本周的周一（含）。"""
    return local_now.date() - timedelta(days=local_now.date().weekday())
