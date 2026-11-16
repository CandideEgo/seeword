"""Web-process health monitor + off-site alerts (A09/OPS-05).

The web process is the right place for this loop: it outlives individual
worker/beat restarts, it is replaced by the external uptime check if it dies,
and the alert channel it uses (``alert_service.send_alert`` → webhook) does not
need the database — a DB outage is one of the things being reported.

What it watches, each check isolated from the others so one failure still lets
the rest alert:

- cloud worker / beat heartbeats (``app/tasks/health_tasks.py`` writes them);
- the cloud queue depth and the GPU queue when the GPU worker is offline;
- free disk on the media path;
- the DB itself and the pipeline failure rate inside a time window.

Every probe is throttled per problem kind in Redis (``SET NX EX``), so a
persistent outage yields one alert per window instead of one per interval. If
Redis is the thing that is down, the throttle cannot be read and the alert is
sent anyway — that is exactly when it matters.
"""

from __future__ import annotations

import asyncio
import shutil
import time
import uuid
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.heartbeat import (
    BEAT_HEARTBEAT_KEY,
    GPU_HEARTBEAT_KEY,
    WORKER_HEARTBEAT_KEY,
    age_seconds,
)
from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger(__name__)

#: The cloud worker's default queue (``backend/app/tasks/celery_app.py``:
#: ``task_default_queue="celery"``). A literal, not an import, so importing the
#: monitor does not drag the whole task graph into the API process.
CLOUD_QUEUE = "celery"


@dataclass(frozen=True)
class HealthProblem:
    """One alertable finding. ``kind`` doubles as the throttle key."""

    kind: str
    severity: str  # "warning" | "critical"
    title: str
    detail: str


def _stale(age: float | None, limit: int) -> bool:
    return age is None or age > limit


async def _redis_problems(redis, settings) -> list[HealthProblem]:
    problems: list[HealthProblem] = []
    now = time.time()

    worker_age = age_seconds(await redis.get(WORKER_HEARTBEAT_KEY), now=now)
    if _stale(worker_age, settings.health_worker_stale_seconds):
        problems.append(
            HealthProblem(
                kind="cloud_worker_stale",
                severity="critical",
                title="云端 Celery worker 心跳丢失",
                detail=f"worker heartbeat age={worker_age}s (limit {settings.health_worker_stale_seconds}s); "
                "队列任务不会被消费，检查 worker 进程与 broker 连接。",
            )
        )

    beat_age = age_seconds(await redis.get(BEAT_HEARTBEAT_KEY), now=now)
    if _stale(beat_age, settings.health_beat_stale_seconds):
        problems.append(
            HealthProblem(
                kind="beat_stale",
                severity="critical",
                title="Celery beat 心跳丢失",
                detail=f"beat heartbeat age={beat_age}s (limit {settings.health_beat_stale_seconds}s); "
                "定时任务（管线看门狗、派发补发、订单对账等）已停摆。",
            )
        )

    queue_depth = int(await redis.llen(CLOUD_QUEUE))
    if queue_depth > settings.health_queue_backlog_threshold:
        problems.append(
            HealthProblem(
                kind="cloud_queue_backlog",
                severity="warning",
                title="云端任务队列积压",
                detail=f"queue={CLOUD_QUEUE} depth={queue_depth} "
                f"(threshold {settings.health_queue_backlog_threshold})。",
            )
        )

    gpu_queue_depth = int(await redis.llen(settings.transcription_gpu_queue_name))
    gpu_online = bool(await redis.exists(GPU_HEARTBEAT_KEY))
    if gpu_queue_depth and not gpu_online:
        problems.append(
            HealthProblem(
                kind="gpu_worker_offline_with_backlog",
                severity="warning",
                title="GPU worker 离线且有积压转录任务",
                detail=f"queue={settings.transcription_gpu_queue_name} depth={gpu_queue_depth}, "
                "gpu heartbeat missing；转录任务不会被消费。",
            )
        )
    return problems


def _disk_problems(settings) -> list[HealthProblem]:
    try:
        usage = shutil.disk_usage(settings.local_media_path)
    except OSError:
        usage = shutil.disk_usage(".")
    percent = usage.used / usage.total * 100 if usage.total else 0.0
    if percent < settings.health_disk_percent_threshold:
        return []
    return [
        HealthProblem(
            kind="disk_usage_high",
            severity="critical" if percent >= 95 else "warning",
            title="磁盘使用率过高",
            detail=f"path={settings.local_media_path} used={percent:.1f}% "
            f"(threshold {settings.health_disk_percent_threshold}%) "
            f"free={usage.free // (1024 * 1024)}MB。",
        )
    ]


async def _database_problems(settings) -> list[HealthProblem]:
    """DB reachability. Failure here must not stop the other checks — it only
    produces its own alert."""
    from sqlalchemy import select

    from app.core.database import get_async_session_maker

    try:
        async with get_async_session_maker()() as db:
            await db.execute(select(1))
            if getattr(settings, "slcs_lessons_enabled", False):
                from app.services.lessons import LESSON_ALL_TABLES
                from app.services.v2_schema import missing_tables

                missing = await missing_tables(db, LESSON_ALL_TABLES)
                if missing:
                    return [
                        HealthProblem(
                            kind="lesson_schema_missing",
                            severity="warning",
                            title="课程试点迁移未完成",
                            detail=f"课程试点已启用，尚缺数据表：{', '.join(missing)}。",
                        )
                    ]
    except Exception as exc:
        return [
            HealthProblem(
                kind="database_unreachable",
                severity="critical",
                title="数据库不可用（健康检查）",
                detail=f"健康检查无法查询数据库：{type(exc).__name__}: {exc}。站外通道不依赖数据库，本告警仍会投递。",
            )
        ]
    return []


async def _pipeline_failure_problems(redis, settings) -> list[HealthProblem]:
    """A failure-rate signal from ``pipeline_alerting``'s Redis list (see there
    for why the DB cannot answer this)."""
    from app.services.pipeline_alerting import read_pipeline_failures

    failures = await read_pipeline_failures(settings.health_pipeline_failure_window_minutes, redis=redis)
    if len(failures) <= settings.health_pipeline_failure_threshold:
        return []
    ids = ", ".join(str(entry.get("video_id")) for entry in failures[:5]) or "n/a"
    steps = {str(entry.get("step")) for entry in failures if entry.get("step")}
    return [
        HealthProblem(
            kind="pipeline_failure_rate",
            severity="warning",
            title="管线失败率超阈值",
            detail=f"最近 {settings.health_pipeline_failure_window_minutes} 分钟有 {len(failures)} 次视频失败 "
            f"(threshold {settings.health_pipeline_failure_threshold})；"
            f"recent video_id: {ids}；steps: {', '.join(sorted(steps)) or 'n/a'}。",
        )
    ]


async def collect_problems(*, redis=None, settings=None) -> list[HealthProblem]:
    """Run every check independently; return all alertable findings."""
    settings = settings or get_settings()
    redis = redis if redis is not None else get_redis()

    problems: list[HealthProblem] = []
    for label, check in (
        ("redis", lambda: _redis_problems(redis, settings)),
        ("pipeline", lambda: _pipeline_failure_problems(redis, settings)),
        ("database", lambda: _database_problems(settings)),
    ):
        try:
            problems.extend(await check())
        except Exception as exc:
            problems.append(
                HealthProblem(
                    kind=f"health_check_{label}_failed",
                    severity="warning",
                    title=f"健康检查自身失败（{label}）",
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
    try:
        problems.extend(_disk_problems(settings))
    except Exception as exc:
        problems.append(
            HealthProblem(
                kind="health_check_disk_failed",
                severity="warning",
                title="健康检查自身失败（disk）",
                detail=f"{type(exc).__name__}: {exc}",
            )
        )
    return problems


async def _dispatch(problem: HealthProblem, *, probe_id: str, redis) -> bool:
    from app.services.alert_service import send_alert

    settings = get_settings()
    key = f"system:health:alert:{problem.kind}"
    allowed = True
    try:
        allowed = bool(await redis.set(key, probe_id, nx=True, ex=settings.health_alert_throttle_seconds))
    except Exception:
        # Redis down: no throttle, but never swallow the alert.
        logger.warning("health alert throttle unavailable", kind=problem.kind, exc_info=True)

    if not allowed:
        logger.info("health problem suppressed by throttle", kind=problem.kind)
        return False

    try:
        sent = await send_alert(problem.title, f"{problem.detail}\nprobe={probe_id}", severity=problem.severity)
    except Exception:
        logger.warning("health alert delivery failed", kind=problem.kind, exc_info=True)
        return False
    logger.info("health alert", kind=problem.kind, severity=problem.severity, delivered=sent, probe=probe_id)
    return sent


async def check_once(*, redis=None) -> list[HealthProblem]:
    """One monitoring pass: collect, then alert on each new problem."""
    redis = redis if redis is not None else get_redis()
    probe_id = uuid.uuid4().hex[:12]
    problems = await collect_problems(redis=redis)
    for problem in problems:
        await _dispatch(problem, probe_id=probe_id, redis=redis)
    if problems:
        logger.warning("health checks reported problems", probe=probe_id, kinds=[p.kind for p in problems])
    return problems


async def run_health_monitor(stop_event: asyncio.Event) -> None:
    settings = get_settings()
    while not stop_event.is_set():
        try:
            await check_once()
        except Exception:
            logger.warning("health monitor pass failed", exc_info=True)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=settings.health_monitor_interval_seconds)
        except TimeoutError:
            continue


def start_health_monitor() -> asyncio.Task | None:
    """Start the loop in the web process (skipped in tests/off in settings).

    The caller owns the task and cancels it on shutdown; the loop's own
    ``stop_event`` is cancelled through that.
    """
    settings = get_settings()
    if settings.env == "testing" or not settings.health_monitor_enabled:
        return None
    stop_event = asyncio.Event()

    async def _runner() -> None:
        await run_health_monitor(stop_event)

    return asyncio.create_task(_runner(), name="health-monitor")
