"""管理端仪表盘的读模型（A15 业务边界拆分）。

原先这些聚合与用户管理、设置、支付读写同住 admin_service（900+ 行）。
它们只读、只服务 GET /admin/stats，失败面与写路径无关，因此单独成模块；
路由、响应模型与缓存键都不变。
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select

from app.core.time_utils import iso_or_none
from app.models.learning import LearningRecord, Vocabulary
from app.models.learning_plan import LearningEvent
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.services.event_contract import MEANINGFUL_EVENT_TYPES

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def _count_online() -> int:
    """Count currently-online users via Redis ``presence:*`` keys (DEV-FLOW B2).

    Each heartbeat sets ``presence:{uid}`` with a 5-min TTL, so the key count
    is the real-time online number. Fails open to 0 if Redis is unavailable.
    """
    try:
        from app.core.redis import get_redis

        redis = get_redis()
        count = 0
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor=cursor, match="presence:*", count=1000)
            count += len(keys)
            if cursor == 0:
                break
        return count
    except Exception:
        return 0


async def _gpu_queue_depth() -> int:
    """Depth of the ``transcription_gpu`` Celery queue (pending GPU work).

    Celery's Redis broker stores pending tasks in a list keyed by the queue
    name, so ``LLEN`` gives the backlog. Fails open to 0 if Redis is
    unavailable.
    """
    try:
        from app.core.config import get_settings
        from app.core.redis import get_redis

        redis = get_redis()
        # redis 客户端的类型把同步/异步两种调用方式并成一个联合类型；admin 侧
        # 用的始终是异步客户端，显式收敛后再 await。
        return int(await cast("Awaitable[int]", redis.llen(get_settings().transcription_gpu_queue_name)))
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Stats dashboard
# ---------------------------------------------------------------------------

# The dashboard is polled by admins every 60s; recomputing ~15 aggregates per
# hit is wasteful. Cache the whole payload in Redis for a short TTL — fresh
# enough for an ops dashboard, cheap enough to serve many admins at once.
_STATS_CACHE_TTL = 30  # seconds


async def get_admin_stats(db: AsyncSession, days: int = 30) -> dict:
    """Aggregate dashboard KPIs, trend data, distributions, and recent activity.

    Wraps :func:`_compute_admin_stats` with a short-lived Redis cache
    (fails open — a Redis outage just means no caching).
    """
    cache_key = f"cache:admin_stats:{days}"
    try:
        from app.core.redis import get_redis

        cached = await get_redis().get(cache_key)
        if cached:
            parsed = json.loads(cached)
            if isinstance(parsed, dict):
                return parsed
    except Exception:
        logger.debug("admin_stats cache read failed — computing fresh", exc_info=True)

    result = await _compute_admin_stats(db, days)

    try:
        from app.core.redis import get_redis

        await get_redis().set(cache_key, json.dumps(jsonable_encoder(result)), ex=_STATS_CACHE_TTL)
    except Exception:
        logger.debug("admin_stats cache write failed", exc_info=True)

    return result


async def _compute_admin_stats(db: AsyncSession, days: int = 30) -> dict:
    """Compute the dashboard payload from scratch (see get_admin_stats)."""

    now = datetime.now(UTC)
    ago_7d = now - timedelta(days=7)
    ago_nd = now - timedelta(days=days)
    today = now.date()

    # --- KPI counts ---
    # All user-level counters in ONE scan via conditional aggregation
    # (previously 7 separate COUNT queries).
    #
    (
        total_users,
        new_users_7d,
        active_users_today,
        active_users_7d,
        signups_today,
    ) = (
        await db.execute(
            select(
                func.count(User.id),
                func.count(User.id).filter(User.created_at >= ago_7d),
                func.count(User.id).filter(func.date(User.last_active_at) == today),
                func.count(User.id).filter(User.last_active_at >= ago_7d),
                func.count(User.id).filter(func.date(User.created_at) == today),
            )
        )
    ).one()

    # Vocabulary KPI — replaces the retired speaking-attempts count (ADR-0003):
    # speaking progress tracking is gone; vocabulary is the active learning metric.
    total_vocabulary = (await db.execute(select(func.count(Vocabulary.id)))).scalar_one()

    # --- Real-time / today KPIs (DEV-FLOW 2026-07 Phase B2) ---
    online_now = await _count_online()
    gpu_queue_depth = await _gpu_queue_depth()

    # --- Trend data ---
    # Signup trend: count users created per day
    signup_rows = (
        await db.execute(
            select(func.date(User.created_at).label("d"), func.count(User.id).label("c"))
            .where(User.created_at >= ago_nd)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
        )
    ).all()
    signup_map = {r.d: r.c for r in signup_rows}

    # Vocabulary trend: new words added per day (SM-2 vocabulary table). Replaces
    # the retired speaking-attempts trend (ADR-0003) — vocabulary is the active
    # learning metric now that AI speaking scoring is removed.
    vocab_rows = (
        await db.execute(
            select(func.date(Vocabulary.created_at).label("d"), func.count(Vocabulary.id).label("c"))
            .where(Vocabulary.created_at >= ago_nd)
            .group_by(func.date(Vocabulary.created_at))
            .order_by(func.date(Vocabulary.created_at))
        )
    ).all()
    vocab_map = {r.d: r.c or 0 for r in vocab_rows}

    # 活跃用户趋势只认不可变的学习事件（MET-01）。旧实现按
    # ``LearningRecord.last_accessed_at`` 分日——那是一行「用户/视频」的最后访问
    # 时间，今天重看去年的视频会把去年的人数搬走，历史日活因此是可变的，
    # 也完全看不到纯词汇/听写/真题的学习者。``LearningEvent.event_date`` 在写入
    # 时就定死，覆盖所有语义学习行为；只看视频的用户由 behavior_service 每天
    # 补一条 watched_video。
    active_rows = (
        await db.execute(
            select(
                LearningEvent.event_date.label("d"),
                func.count(func.distinct(LearningEvent.user_id)).label("c"),
            )
            .where(LearningEvent.event_date >= ago_nd.date(), LearningEvent.event_type.in_(MEANINGFUL_EVENT_TYPES))
            .group_by(LearningEvent.event_date)
            .order_by(LearningEvent.event_date)
        )
    ).all()
    active_map = {r.d: r.c for r in active_rows}

    dates_list: list[str] = []
    signups_list: list[int] = []
    vocab_list: list[int] = []
    active_list: list[int] = []
    for i in range(days - 1, -1, -1):
        d = (now - timedelta(days=i)).date()
        dates_list.append(d.isoformat())
        signups_list.append(signup_map.get(d, 0))
        vocab_list.append(vocab_map.get(d, 0))
        active_list.append(active_map.get(d, 0))

    # --- Distributions ---
    # One GROUP BY replaces three queries (total / ready / error counts are
    # derived from the per-status rows).
    videos_by_status_rows = (await db.execute(select(Video.status, func.count(Video.id)).group_by(Video.status))).all()
    videos_by_status = [{"status": r[0], "count": r[1]} for r in videos_by_status_rows]
    status_counts = {r[0]: r[1] for r in videos_by_status_rows}
    total_videos = sum(status_counts.values())
    videos_ready = status_counts.get(VideoStatus.ready, 0)
    videos_error_count = status_counts.get(VideoStatus.error, 0)

    # --- Video topic distribution (prototype 31: 视频分类分布) ---
    # topic_tags is a comma-separated string column; aggregate in Python.
    topic_rows = (await db.execute(select(Video.topic_tags).where(Video.is_published.is_(True)))).scalars().all()
    topic_counts: dict[str, int] = {}
    for tags in topic_rows:
        if not tags:
            continue
        for tag in tags.split(","):
            tag = tag.strip()
            if tag:
                topic_counts[tag] = topic_counts.get(tag, 0) + 1
    videos_by_topic = [
        {"topic": t, "count": c} for t, c in sorted(topic_counts.items(), key=lambda kv: kv[1], reverse=True)[:8]
    ]

    # --- Cumulative behavior distribution ---
    # 这三个数字**互相独立**（不同 cohort、无时间窗、无步骤顺序），不是漏斗。
    # 真实 cohort 漏斗见 ``measurement_service.learning_metrics``。
    watched_users = (await db.execute(select(func.count(func.distinct(LearningRecord.user_id))))).scalar_one()
    vocab_users = (await db.execute(select(func.count(func.distinct(Vocabulary.user_id))))).scalar_one()
    funnel = {
        "registered": total_users,
        "watched": int(watched_users or 0),
        "vocab_saved": int(vocab_users or 0),
    }

    # --- Recent activity ---
    recent: list[dict] = []

    # Signups
    for u in (await db.execute(select(User).order_by(User.created_at.desc()).limit(8))).scalars().all():
        recent.append(
            {
                "id": f"signup-{u.id}",
                "type": "signup",
                "summary": f"新用户 {u.name or u.phone} 注册",
                "created_at": iso_or_none(u.created_at),
            }
        )

    # (Speaking-attempts activity source removed per ADR-0003 — AI speaking
    # scoring is gone, so "完成口语评测" entries would only ever describe a
    # dead feature.)

    # (Payment activity source removed with the retired paid-membership chain.)

    # Sort all by created_at desc and take top 8
    recent.sort(key=lambda x: x["created_at"] or "", reverse=True)
    recent = recent[:8]

    return {
        "total_users": total_users,
        "new_users_7d": new_users_7d,
        "total_videos": total_videos,
        "videos_ready": videos_ready,
        "total_vocabulary": total_vocabulary,
        "active_users_today": active_users_today,
        "active_users_7d": active_users_7d,
        "online_now": online_now,
        "gpu_queue_depth": gpu_queue_depth,
        "videos_error_count": videos_error_count,
        "signups_today": signups_today,
        "trend": {
            "dates": dates_list,
            "signups": signups_list,
            "vocabulary": vocab_list,
            "active_users": active_list,
        },
        "videos_by_status": videos_by_status,
        "recent_activity": recent,
        "funnel": funnel,
        "videos_by_topic": videos_by_topic,
    }
