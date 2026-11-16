"""公告广播 Celery 任务（ADM-07）。

审计问题：``POST /admin/announcements`` 曾在一个 HTTP 事务里对全表用户逐条
``create_notification``（每人一次 SELECT 去重 + INSERT + WS 推送），耗时随用户数
线性增长，超过反向代理默认 60s 就会 504，客户端断开后事务还可能被取消（一半人
收到、一半没收到）。

现在的切分：

- 请求路径只做「数人 + 入队」，返回 ``{queued: true, notified_count, title, message}``；
- 扇出在本任务里按 ``ANNOUNCEMENT_CHUNK_SIZE``（500）分页 keyset 遍历用户，每页
  一条多值 ``insert()``、每页提交后再 best-effort 推送 WebSocket。

去重语义与旧实现一致（见 ``notification_service.fan_out_announcement``）：

- 带 ``related_url``：同一 (user, announcement, related_url) 的**未读**通知原地
  更新，不新增行 —— 重发同一条公告是刷新而不是刷屏；
- 不带 ``related_url``：每次广播新增一行 —— 新公告必须能盖过旧未读公告。

已知残留风险（写进 backend/app/services/notification_service.py 的
deferred/风险节）：分页提交意味着任务若在**中途**被 worker 杀掉并重投，
``related_url=None`` 的广播会给已处理用户再插一行。要根治需要公告实体表 +
``broadcast_id`` 唯一键（本轮 deferred）。
"""

from __future__ import annotations

from app.core.database import get_async_session_maker
from app.core.logging import get_logger
from app.services.notification_service import (
    ANNOUNCEMENT_CHUNK_SIZE,
    fan_out_announcement,
)
from app.tasks.async_helpers import run_async
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)

BROADCAST_ANNOUNCEMENT_TASK_NAME = "app.tasks.notification_tasks.broadcast_announcement"


async def _broadcast_announcement_async(
    title: str,
    message: str,
    related_url: str | None = None,
    chunk_size: int = ANNOUNCEMENT_CHUNK_SIZE,
) -> int:
    """任务体的异步实现（测试直接 await 它，不经过 Celery 序列化）。"""
    async with get_async_session_maker()() as db:
        processed = await fan_out_announcement(
            db,
            title=title,
            message=message,
            related_url=related_url,
            chunk_size=chunk_size,
        )
    logger.info(
        "announcement fan-out finished",
        title=title,
        related_url=related_url,
        notified=processed,
    )
    return processed


@celery_app.task(
    name=BROADCAST_ANNOUNCEMENT_TASK_NAME,
    soft_time_limit=280,
    time_limit=300,
)
def broadcast_announcement(title: str, message: str, related_url: str | None = None) -> int:
    """把公告扇出到全表用户（云端默认 ``celery`` 队列，不路由到 GPU 队列）。"""
    return run_async(_broadcast_announcement_async(title, message, related_url))
