"""首页编辑内容 —— AI 草稿生成 Celery 任务（T2）。

契约见 ``backend/app/schemas/home_content.py``「生成状态机」：

- 任务名 ``app.tasks.home_content_tasks.generate_home_content_draft``，默认 ``celery``
  队列（不路由到 GPU 队列），``soft_time_limit=420`` / ``time_limit=480``；由服务层
  以 ``task_id = generation_id`` 入队，同一 generation 被重复投递必须幂等。
- 任务体只做三件事：读上下文 → 调 ``home_content_generation.generate_draft`` →
  通过 ``home_content_service.complete_generation`` 写回。**写回前的三重断言**
  （generation_id / 入队时草稿 revision / 入队时来源指纹）与 strict 校验由服务层在
  事务里做：返回 False 即「有冲突或输出非法，草稿已标 failed，旧 payload 保持原样」，
  任务不再调 ``fail_generation``（否则会把错误码盖掉）。
- 失败绝不伪装成功：AI 不可用 / 输出非法 / 超时 / 冲突都落 ``status=failed`` +
  明确错误码，可重试；「成功」只在服务层真正写回后返回。
- 覆盖范围（送了几段、覆盖了哪些句）落结构化日志 + 任务返回值，便于回溯
  「是否只读了开头」——数据库 schema 没有 coverage 列，不另造字段。

另一个任务 ``sweep_home_content_generations`` 由 beat 每 600s 调一次，把卡在
queued/running 超过阈值的生成标为 failed TIMEOUT（GET 状态接口也会顺手处理，
这里是兜底）。
"""

from __future__ import annotations

from typing import Any

from celery.exceptions import SoftTimeLimitExceeded
from sqlalchemy import select

from app.core.database import get_async_session_maker
from app.core.logging import get_logger
from app.models.home_content import HomeContentDraft
from app.services.home_content_generation import (
    GENERATION_ERROR_CONFLICT,
    GENERATION_ERROR_INTERNAL,
    GENERATION_ERROR_TIMEOUT,
    DraftGenerationError,
    generate_draft,
)
from app.services.home_content_service import (
    complete_generation,
    fail_generation,
    load_generation_context,
    sweep_stale_generations,
)
from app.tasks.async_helpers import run_async
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)

GENERATION_TASK_NAME = "app.tasks.home_content_tasks.generate_home_content_draft"
SWEEP_TASK_NAME = "app.tasks.home_content_tasks.sweep_home_content_generations"

_STATUS_SUCCEEDED = "succeeded"
_STATUS_FAILED = "failed"


async def _fail_generation(generation_id: str, code: str, message: str) -> bool:
    """把当前任务标 failed（保留旧 payload/revision）；记录本身再失败只打日志。"""
    async with get_async_session_maker()() as db:
        try:
            return await fail_generation(db, generation_id, code, message)
        except Exception:
            logger.exception("home_content fail_generation failed", generation_id=generation_id, code=code)
            return False


async def _read_generation_error_code(generation_id: str) -> str | None:
    """写回被服务层拒绝后，读回它落的具体错误码（AI_INVALID/CONFLICT/SOURCE_CHANGED）。"""
    try:
        async with get_async_session_maker()() as db:
            code = (
                await db.execute(
                    select(HomeContentDraft.generation_error_code).where(
                        HomeContentDraft.last_generation_id == generation_id
                    )
                )
            ).scalar_one_or_none()
        return str(code) if code else None
    except Exception:
        logger.exception("home_content read generation error code failed", generation_id=generation_id)
        return None


async def _generate_async(generation_id: str) -> dict[str, Any]:
    """任务体的异步实现（测试直接 await 它，不经过 Celery 序列化）。"""
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.content_production_enabled or not settings.llm_enabled:
        await _fail_generation(generation_id, "SERVICE_UNAVAILABLE", "模型或内容生产能力已关闭")
        return {
            "generation_id": generation_id,
            "status": _STATUS_FAILED,
            "error_code": "SERVICE_UNAVAILABLE",
            "ai_calls": 0,
        }
    # 1) 读上下文。服务层顺手把 queued → running；返回 None = 任务已被取代/取消/已结束。
    async with get_async_session_maker()() as db:
        context = await load_generation_context(db, generation_id)
    if context is None:
        # 幂等：同一 generation 重复执行（worker 重投/重试）时这里直接退出，
        # 不会再写一次成功；被新任务取代时同样不碰任何数据。
        logger.info("home_content generation has no active context; skipping", generation_id=generation_id)
        return {"generation_id": generation_id, "status": "skipped", "reason": "no_active_context"}

    # 2) 生成（AI 调用期间不持有 DB 会话/连接）。
    try:
        result = await generate_draft(video_title=context.video_title, subtitles=context.subtitles)
    except DraftGenerationError as exc:
        logger.warning(
            "home_content generation failed",
            generation_id=generation_id,
            video_id=context.video_id,
            code=exc.code,
            message=exc.message,
            ai_calls=exc.calls,
        )
        await _fail_generation(generation_id, exc.code, exc.message)
        return {
            "generation_id": generation_id,
            "status": _STATUS_FAILED,
            "error_code": exc.code,
            "error_message": exc.message,
            "ai_calls": exc.calls,
        }
    except Exception:
        logger.exception("home_content generation crashed", generation_id=generation_id)
        await _fail_generation(generation_id, GENERATION_ERROR_INTERNAL, "生成任务内部错误，请重试")
        return {
            "generation_id": generation_id,
            "status": _STATUS_FAILED,
            "error_code": GENERATION_ERROR_INTERNAL,
            "ai_calls": 0,
        }

    # 3) 写回。服务层在同一事务里重做 strict 校验 + 三重断言；False = 已标 failed。
    async with get_async_session_maker()() as db:
        try:
            written = await complete_generation(
                db,
                generation_id,
                result.payload,
                model=result.model,
                prompt_version=result.prompt_version,
                usage=result.usage,
                coverage=result.coverage,
                calls=result.calls,
            )
        except Exception:
            logger.exception("home_content complete_generation crashed", generation_id=generation_id)
            await _fail_generation(generation_id, GENERATION_ERROR_INTERNAL, "生成结果写回失败，请重试")
            return {
                "generation_id": generation_id,
                "status": _STATUS_FAILED,
                "error_code": GENERATION_ERROR_INTERNAL,
                "ai_calls": result.calls,
            }

    if not written:
        error_code = await _read_generation_error_code(generation_id) or GENERATION_ERROR_CONFLICT
        logger.warning(
            "home_content generation rejected on write-back",
            generation_id=generation_id,
            video_id=context.video_id,
            code=error_code,
            ai_calls=result.calls,
        )
        return {
            "generation_id": generation_id,
            "status": _STATUS_FAILED,
            "error_code": error_code,
            "ai_calls": result.calls,
        }

    logger.info(
        "home_content generation succeeded",
        generation_id=generation_id,
        video_id=context.video_id,
        ai_calls=result.calls,
        model=result.model,
        prompt_version=result.prompt_version,
        coverage=result.coverage,
    )
    return {
        "generation_id": generation_id,
        "status": _STATUS_SUCCEEDED,
        "ai_calls": result.calls,
        "coverage": result.coverage,
        "model": result.model,
        "prompt_version": result.prompt_version,
    }


async def _sweep_async() -> int:
    """beat 巡检：把超时未结束的生成任务标 failed TIMEOUT（服务层自己开 session/commit）。"""
    count = int(await sweep_stale_generations() or 0)
    if count:
        logger.info("home_content swept stale generations", count=count)
    return count


# ---------------------------------------------------------------------------
# Celery 任务
# ---------------------------------------------------------------------------


@celery_app.task(
    name=GENERATION_TASK_NAME,
    soft_time_limit=420,
    time_limit=480,
)
def generate_home_content_draft(generation_id: str) -> dict[str, Any]:
    """生成首页内容草稿（云端默认队列；task_id = generation_id）。"""
    try:
        return run_async(_generate_async(generation_id))
    except SoftTimeLimitExceeded:
        # 软超时后有 60s 宽限（time_limit=480 才硬杀）：把状态落成可见的 TIMEOUT。
        logger.warning("home_content generation soft timeout", generation_id=generation_id)
        run_async(_fail_generation(generation_id, GENERATION_ERROR_TIMEOUT, "生成任务超时（超过 420 秒），请重试"))
        return {"generation_id": generation_id, "status": _STATUS_FAILED, "error_code": GENERATION_ERROR_TIMEOUT}


@celery_app.task(name=SWEEP_TASK_NAME)
def sweep_home_content_generations() -> int:
    """把卡在 queued/running 的生成任务标 failed TIMEOUT（beat 每 10 分钟）。"""
    return run_async(_sweep_async())
