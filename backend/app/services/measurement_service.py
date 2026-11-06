"""A12 学习测量服务——激活/留存、事件质量与性能基线。

这个模块是「测量」的唯一正文：口径（分母、边界、窗口）、实现与样本量都在
这里，管理端只是把结果画出来。三个原则：

1. **分母写死并随结果一起返回**。激活率的分母是「窗口内注册的非管理员账号」，
   D1/D7 的分母是「该激活日 cohort 的去重用户」，而不是「今天还在的人」。
   没成熟的 cohort 返回 ``eligible=False``，不拿后来的用户补分母。
2. **性能数字必须带样本量**。p75 用最近秩法（nearest-rank），样本 <20 时
   只作参考；没有样本就返回 ``None``，不返回 0 冒充「很快」。

时间边界：注册/激活用 UTC 时间戳；学习日与 D1/D7 用
``LearningEvent.event_date``（用户本地日，写入时冻结，事后改时区不回写历史）。
两者混用会在 ±1 天上保守（成熟判定用 UTC 日期，可能晚一天），这是刻意选择：
宁可晚一天出数，也不让分母随用户时区变化漂移。
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from app.models.behavior import BehaviorEvent
from app.models.learning_plan import LearningEvent
from app.models.pipeline_dispatch import DISPATCH_STATUS_PENDING, PipelineDispatch
from app.models.user import RoleType, User
from app.services.event_contract import (
    CLIENT_FIRST_PLAY,
    CLIENT_FLOW_RESULT,
    CLIENT_WEB_VITAL,
    LEARNING_EVENT_SCHEMA_VERSION,
    MEANINGFUL_EVENT_TYPES,
    WEB_VITAL_METRICS,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

#: 口径版本：改分母、边界或分档时必须 +1，并在 evidence 里写明生效日。
METRICS_DEFINITION_VERSION = 1

#: 只读最近这段时间的原始行做聚合；再久的数据请走离线导出，不在请求里扫全表。
MAX_EVENT_ROWS = 50_000

ACTIVATION_WINDOW = timedelta(hours=24)

DEFINITIONS: dict[str, str] = {
    "version": str(METRICS_DEFINITION_VERSION),
    "meaningful_learning": "当天有任一有效学习事件（完成视频/学会词/练习/复习/当天看过视频）的用户本地日",
    "activation": "注册后 24 小时内出现首个有效学习事件；分母 = 窗口内注册的非管理员账号",
    "cohort": "激活日 cohort（首次有效学习所在的用户本地日）；分母 = 该日首次学习的去重用户",
    "d1_d7": "激活日后第 1/7 个本地日仍有有效学习；只统计已成熟 cohort，不用后来的用户补分母",
    "percentile": "p75 最近秩法；返回样本量，样本 <20 时仅作参考",
    "boundary": "注册/激活用 UTC 时间戳；学习日与 D1/D7 用 LearningEvent.event_date（用户本地日，写入时冻结）",
}


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile. Returns None for an empty sample."""
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(p * len(ordered)))
    return ordered[rank - 1]


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _payload_number(payload: dict | None, key: str) -> float | None:
    if not isinstance(payload, dict):
        return None
    raw = payload.get(key)
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, (int, float, str)):
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        return value if math.isfinite(value) else None
    return None


async def _activation(db: AsyncSession, window_start: datetime) -> dict[str, Any]:
    """注册后 24h 内首次学习 = 激活。分母固定为窗口内注册的非管理员账号。"""
    registered = (
        await db.execute(
            select(User.id, User.created_at).where(
                User.created_at >= window_start,
                User.role != RoleType.admin,
            )
        )
    ).all()
    if not registered:
        return {"window_registered": 0, "activated_within_24h": 0, "rate": None}

    ids = [row[0] for row in registered]
    first_rows = (
        await db.execute(
            select(LearningEvent.user_id, func.min(LearningEvent.created_at))
            .where(LearningEvent.user_id.in_(ids), LearningEvent.event_type.in_(MEANINGFUL_EVENT_TYPES))
            .group_by(LearningEvent.user_id)
        )
    ).all()
    first_events: dict[str, datetime] = {}
    for event_user_id, first_seen in first_rows:
        if first_seen is not None:
            first_events[event_user_id] = first_seen

    activated = 0
    for user_id, created_at in registered:
        first = first_events.get(user_id)
        if first is None or created_at is None:
            continue
        if first - created_at <= ACTIVATION_WINDOW:
            activated += 1
    return {
        "window_registered": len(registered),
        "activated_within_24h": activated,
        "rate": _rate(activated, len(registered)),
    }


async def _cohorts(db: AsyncSession, first_date: date, today: date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """激活日 cohort 的 D1/D7。只返回窗口内的 cohort，成熟前 eligible=False。"""
    # 管理员/内部测试账号不进 cohort 分母：他们对「用户留存」没有解释力，
    # 混进去只会让早期小 cohort 的留存率虚高。
    first_rows = (
        select(LearningEvent.user_id, func.min(LearningEvent.event_date).label("first_date"))
        .join(User, User.id == LearningEvent.user_id)
        .where(LearningEvent.event_type.in_(MEANINGFUL_EVENT_TYPES), User.role != RoleType.admin)
        .group_by(LearningEvent.user_id)
        .subquery()
    )
    cohort_rows = (
        await db.execute(
            select(first_rows.c.user_id, first_rows.c.first_date).where(first_rows.c.first_date >= first_date)
        )
    ).all()
    if not cohort_rows:
        return [], {"active_7d": 0, "multi_day_7d": 0, "volume_rate": None}

    cohort_sizes: dict[date, int] = defaultdict(int)
    user_first: dict[str, date] = {}
    for user_id, activation_date in cohort_rows:
        cohort_sizes[activation_date] += 1
        user_first[user_id] = activation_date

    active_days: dict[str, set[date]] = defaultdict(set)
    day_rows = (
        await db.execute(
            select(LearningEvent.user_id, LearningEvent.event_date)
            .where(
                LearningEvent.user_id.in_(list(user_first)),
                LearningEvent.event_date >= first_date,
                LearningEvent.event_type.in_(MEANINGFUL_EVENT_TYPES),
            )
            .distinct()
        )
    ).all()
    for user_id, event_date in day_rows:
        active_days[user_id].add(event_date)

    d1: dict[date, int] = defaultdict(int)
    d7: dict[date, int] = defaultdict(int)
    for user_id, activation_date in user_first.items():
        days = active_days.get(user_id, set())
        if activation_date + timedelta(days=1) in days:
            d1[activation_date] += 1
        if activation_date + timedelta(days=7) in days:
            d7[activation_date] += 1

    cohorts: list[dict[str, Any]] = []
    for activation_date in sorted(cohort_sizes):
        size = cohort_sizes[activation_date]
        d1_eligible = activation_date + timedelta(days=1) <= today
        d7_eligible = activation_date + timedelta(days=7) <= today
        cohorts.append(
            {
                "cohort_date": activation_date.isoformat(),
                "size": size,
                "d1_eligible": d1_eligible,
                "d1_retained": d1[activation_date] if d1_eligible else None,
                "d1_rate": _rate(d1[activation_date], size) if d1_eligible else None,
                "d7_eligible": d7_eligible,
                "d7_retained": d7[activation_date] if d7_eligible else None,
                "d7_rate": _rate(d7[activation_date], size) if d7_eligible else None,
            }
        )

    active_7d = sum(1 for days in active_days.values() if len(days) >= 1)
    multi_day_7d = sum(1 for days in active_days.values() if len(days) >= 2)
    return cohorts, {
        "active_7d": active_7d,
        "multi_day_7d": multi_day_7d,
        # MET 字典的主指标：每周至少 2 个有效学习日的人占「至少 1 天」的比例。
        "volume_rate": _rate(multi_day_7d, active_7d),
    }


async def _event_quality(db: AsyncSession, window_start: datetime) -> dict[str, Any]:
    """事件质量：版本、缺失率、以及 client 意图 vs 服务端事实的对账。"""
    type_rows = (
        await db.execute(
            select(
                BehaviorEvent.event_type,
                BehaviorEvent.schema_version,
                func.count(BehaviorEvent.id),
                func.count(BehaviorEvent.event_id),
            )
            .where(BehaviorEvent.server_ts >= window_start)
            .group_by(BehaviorEvent.event_type, BehaviorEvent.schema_version)
        )
    ).all()

    by_type: dict[str, dict[str, Any]] = {}
    for event_type, schema_version, total, with_id in type_rows:
        entry = by_type.setdefault(
            event_type,
            {"event_type": event_type, "events": 0, "with_event_id": 0, "versions": {}},
        )
        entry["events"] += int(total or 0)
        entry["with_event_id"] += int(with_id or 0)
        entry["versions"][str(schema_version)] = entry["versions"].get(str(schema_version), 0) + int(total or 0)
    for entry in by_type.values():
        entry["missing_event_id_rate"] = _rate(entry["events"] - entry["with_event_id"], entry["events"])

    client_rows = (
        await db.execute(
            select(BehaviorEvent.flow_id, BehaviorEvent.event_payload)
            .where(
                BehaviorEvent.event_type == CLIENT_FLOW_RESULT,
                BehaviorEvent.server_ts >= window_start,
                BehaviorEvent.flow_id.is_not(None),
            )
            .limit(MAX_EVENT_ROWS)
        )
    ).all()
    client_by_path: dict[str, list[str]] = defaultdict(list)
    for flow_id, payload in client_rows:
        path = (payload or {}).get("path") if isinstance(payload, dict) else None
        client_by_path[str(path or "unknown")].append(str(flow_id))

    server_rows = (
        await db.execute(
            select(LearningEvent.flow_id, LearningEvent.source)
            .where(
                LearningEvent.flow_id.is_not(None),
                LearningEvent.created_at >= window_start,
            )
            .limit(MAX_EVENT_ROWS)
        )
    ).all()
    server_by_path: dict[str, set[str]] = defaultdict(set)
    for flow_id, source in server_rows:
        server_by_path[str(source or "unknown")].add(str(flow_id))

    flows: list[dict[str, Any]] = []
    for path in sorted(set(client_by_path) | set(server_by_path)):
        client_ids = client_by_path.get(path, [])
        server_ids = server_by_path.get(path, set())
        matched = len(set(client_ids) & server_ids)
        client_only = len(set(client_ids) - server_ids)
        server_only = len(server_ids - set(client_ids))
        flows.append(
            {
                "path": path,
                "client_results": len(client_ids),
                "client_distinct_flows": len(set(client_ids)),
                "server_facts": len(server_ids),
                "matched": matched,
                # 客户端说完成了、服务端没有事实：可能是请求失败，也可能是重试。
                "client_only": client_only,
                # 服务端有事实、客户端没发意图：埋点漏发或客户端版本过旧。
                "server_only": server_only,
                "duplicate_intents": len(client_ids) - len(set(client_ids)),
                "loss_rate": _rate(client_only, len(set(client_ids))) if client_ids else None,
            }
        )

    return {
        "by_type": sorted(by_type.values(), key=lambda e: (-e["events"], e["event_type"])),
        "flows": flows,
    }


async def _performance(db: AsyncSession, window_start: datetime, now: datetime) -> dict[str, Any]:
    """RUM（LCP/INP/CLS）、首播耗时与管线派发积压年龄。"""
    vital_rows = (
        await db.execute(
            select(BehaviorEvent.event_payload)
            .where(
                BehaviorEvent.event_type == CLIENT_WEB_VITAL,
                BehaviorEvent.server_ts >= window_start,
            )
            .limit(MAX_EVENT_ROWS)
        )
    ).scalars()
    vital_samples: dict[str, list[float]] = defaultdict(list)
    for payload in vital_rows:
        metric = payload.get("metric") if isinstance(payload, dict) else None
        if metric not in WEB_VITAL_METRICS:
            continue
        value = _payload_number(payload, "value")
        if value is not None:
            vital_samples[str(metric)].append(value)

    first_play_rows = (
        await db.execute(
            select(BehaviorEvent.event_payload)
            .where(
                BehaviorEvent.event_type == CLIENT_FIRST_PLAY,
                BehaviorEvent.server_ts >= window_start,
            )
            .limit(MAX_EVENT_ROWS)
        )
    ).scalars()
    first_play = [v for v in (_payload_number(p, "ms") for p in first_play_rows) if v is not None]

    pending = (
        await db.execute(
            select(func.count(PipelineDispatch.id)).where(PipelineDispatch.status == DISPATCH_STATUS_PENDING)
        )
    ).scalar_one()
    oldest_pending = (
        await db.execute(
            select(func.min(PipelineDispatch.created_at)).where(PipelineDispatch.status == DISPATCH_STATUS_PENDING)
        )
    ).scalar_one()

    oldest_age = None
    if oldest_pending is not None:
        if oldest_pending.tzinfo is None:  # SQLite returns naive datetimes
            oldest_pending = oldest_pending.replace(tzinfo=UTC)
        oldest_age = int((now - oldest_pending).total_seconds())

    return {
        "web_vitals": {
            metric: {
                "p75": percentile(vital_samples[metric], 0.75),
                "samples": len(vital_samples[metric]),
            }
            for metric in sorted(WEB_VITAL_METRICS)
        },
        "first_play": {"p75_ms": percentile(first_play, 0.75), "samples": len(first_play)},
        "pipeline_backlog": {
            "pending_dispatches": int(pending or 0),
            "oldest_pending_age_s": oldest_age,
        },
        "schema_version": LEARNING_EVENT_SCHEMA_VERSION,
    }


async def learning_metrics(db: AsyncSession, days: int = 30) -> dict[str, Any]:
    """一次性返回管理端需要的全部测量结果（一次读取，一个响应）。"""
    now = datetime.now(UTC)
    window_start = now - timedelta(days=days)
    today = now.date()

    activation = await _activation(db, window_start)
    cohorts, weekly = await _cohorts(db, window_start.date(), today)
    event_quality = await _event_quality(db, window_start)
    performance = await _performance(db, window_start, now)

    return {
        "days": days,
        "definitions": DEFINITIONS,
        "activation": activation,
        "cohorts": cohorts,
        "weekly": weekly,
        "event_quality": event_quality,
        "performance": performance,
    }
