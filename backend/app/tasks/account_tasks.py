"""Account lifecycle tasks (P1-7 / A08): async data export + 30-day deletion purge.

Two families:

- ``build_user_export`` — assemble a ZIP for one ``DataExportTask``. The
  dataset inventory lives in :mod:`app.services.account_data` so it can be
  tested independently of Celery; it covers profile / preferences / vocabulary /
  learning records+events+profile / favorites / notes / sentence favorites /
  channel subscriptions / likes / vocab sets / study sessions / listening
  attempts / exam attempts+answers / notifications / feedback /
  mastery+milestone history / behavior events / uploaded videos, plus the
  on-disk originals (avatar, uploaded video files, historical shadowing audio). Failures retry a bounded number of times and
  notify the user once they give up.
- ``purge_deleted_accounts`` — daily sweep for accounts whose 30-day window
  elapsed. Deletes personal data, keeps official catalog videos, anonymizes
  behavior events, then deletes the user row
  (the moment the phone number is released). Disk cleanup is recorded in
  ``media_cleanup_tasks`` inside the same transaction and drained afterwards;
  ``retry_media_cleanup`` (beat, every 15 minutes) retries anything that failed,
  so a locked file cannot become a permanent leak.

Both tasks open their own sessions via ``async_session`` so they run on the
shared celery-asyncio loop (``run_async``). Task bodies accept an optional
aware-UTC ``now`` as a test seam.
"""

import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import structlog

from app.services import account_data
from app.tasks.async_helpers import run_async
from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


def _csv_bytes(rows: list[dict]) -> bytes:
    """Serialize rows to a BOM-prefixed UTF-8 CSV (Excel-friendly Chinese)."""
    if not rows:
        return "﻿".encode()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: (
                    ""
                    if value is None
                    else json.dumps(value, ensure_ascii=False)
                    if isinstance(value, (dict, list))
                    else value
                )
                for key, value in row.items()
            }
        )
    return buf.getvalue().encode("utf-8")


def _json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str).encode("utf-8")


_README = """SeeWord 数据导出包
=================

本包包含你在 SeeWord 的账号数据：
  profile.json                 账号资料（不含密码哈希）
  preferences.json             学习与通知偏好
  learning_profile.json        学习档案与连续天数
  vocabulary.*                 单词本
  learning_records.*           视频学习记录
  learning_events.*            学习事件（完成视频、学词、练习等）
  vocab_sets.json              词汇集与每个词的过筛状态
  study_sessions.json          词汇训练轮次与每题状态
  favorites.* / notes.*        收藏与笔记
  sentence_favorites.json      句子收藏
  channel_subscriptions.json   频道订阅
  video_likes.json             点赞记录
  listening_sessions.*         听力练习与判分结果
  exam_sessions.json           试卷作答（含逐题快照与你的答案）
  teaching_sessions.json / teaching_attempts.json  教学状态与作答（按当前内容权限投影）
  question_exposures.json / question_disclosures.json  提示与答案可见记录
  exposure_mapping_states.json 历史暴露映射资格
  teaching_feedbacks.json / teaching_operations.json  未过期教学反馈与动作回执
  external_connections.json / teaching_runs.json  外部连接与讲解任务安全摘要
  tutor_conversations.json  独立对话列表（含关联任务）
  teaching_messages.json  当前权限允许的对话消息
  videos.json                  你上传的视频元数据
  notifications.*              站内通知
  feedbacks.*                  你提交的反馈
  mastery_snapshots.json       掌握度历史快照
  user_milestones.json         成就记录
  behavior_events.*            观看与操作行为事件
  lesson_progress.json         课程学习进度（按课程与修订）
  lesson_activities.json       课程播放活动（逐次可观测学习操作）
  lesson_vocabulary_sources.json  从课程原句收录的词的定位锚点
  vocabulary_review_log.json   复习调度日志（评分、调度版本与前后状态）
  lesson_tutor_anchors.json    课程导师对话绑定的原句锚点
  media/                       头像、上传视频文件与历史跟读音频原件

说明：
- 导出由账号本人发起，只包含该账号自己的数据。
- 手机号与账号标识属于账号资料。
- 下载链接一次性、15 分钟内有效。
"""


async def _build_export(task_id: str) -> dict:
    """Build the ZIP for one export task. Raises on any failure (caller retries)."""
    import zipfile

    from app.core.config import get_settings
    from app.core.database import async_session
    from app.models.data_export import DataExportTask
    from app.models.user import User

    async with async_session() as db:
        task = await db.get(DataExportTask, task_id)
        if task is None:
            logger.warning("build_user_export_missing_task", task_id=task_id)
            return {"status": "missing"}
        task.status = "running"
        await db.commit()

        user = await db.get(User, task.user_id)
        if user is None:
            task.status = "failed"
            task.error = "用户不存在"
            await db.commit()
            return {"status": "failed"}

        data, media_entries = await account_data.gather_export(db, user)

        media_root = Path(get_settings().local_media_path).resolve()
        out_dir = media_root / "exports" / user.id
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = out_dir / f"{task.id}.zip"

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for key in account_data.EXPORT_ORDER:
                payload = data.get(key)
                zf.writestr(f"{key}.json", _json_bytes(payload))
                if key in account_data.CSV_SECTIONS and isinstance(payload, list):
                    zf.writestr(f"{key}.csv", _csv_bytes(payload))
            for source, arcname in media_entries:
                zf.write(source, arcname)
            zf.writestr("README.txt", _README)

        size = zip_path.stat().st_size
        # Relative to the media root — the download endpoint joins it back.
        task.file_path = zip_path.relative_to(media_root).as_posix()
        task.size_bytes = size
        task.status = "ready"
        task.error = None
        await db.commit()

        from app.services.notification_service import commit_and_push, create_notification

        notification = await create_notification(
            user_id=user.id,
            type="system",
            title="数据导出已完成",
            message="你的数据导出包已就绪，可在「我的 → 账号安全」下载（链接 15 分钟内有效）。",
            db=db,
            related_url="/profile?tab=settings",
        )
        await commit_and_push(db, [notification])
        logger.info("data_export_ready", export_task_id=task.id, size_bytes=size)
        return {"status": "ready", "size_bytes": size}


async def _mark_export_failure(task_id: str, error: str, *, final: bool) -> None:
    from app.core.database import async_session
    from app.models.data_export import DataExportTask

    async with async_session() as db:
        task = await db.get(DataExportTask, task_id)
        if task is None:
            return
        task.attempts = (task.attempts or 0) + 1
        task.error = error[:2000]
        if final:
            task.status = "failed"
        await db.commit()
        if final:
            from app.services.notification_service import commit_and_push, create_notification

            notification = await create_notification(
                user_id=task.user_id,
                type="system",
                title="数据导出失败",
                message="导出多次尝试后仍未成功，请稍后在「我的 → 账号安全」重试。",
                db=db,
                related_url="/profile?tab=settings",
            )
            await commit_and_push(db, [notification])


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def build_user_export(self, task_id: str):
    """Celery entry point for the async export (retries a few times)."""
    try:
        return run_async(_build_export(task_id))
    except Exception as exc:  # retry/notify boundary
        final = self.request.retries >= self.max_retries
        logger.exception("build_user_export_failed", export_task_id=task_id, final=final)
        run_async(_mark_export_failure(task_id, str(exc), final=final))
        if not final:
            raise self.retry(exc=exc) from exc
        return {"status": "failed"}


# ── 30-day deletion purge ───────────────────────────────────────────


async def _purge_user(db, user) -> None:
    """Delete one expired account; record media cleanup in the same transaction."""
    from sqlalchemy import delete as sa_delete
    from sqlalchemy import select
    from sqlalchemy import update as sa_update

    from app.core.database import Base
    from app.models.behavior import BehaviorEvent
    from app.models.data_export import DataExportTask
    from app.models.user import User as UserModel
    from app.models.video import Video

    await _prepare_v2_removal(db, user.id)

    # 1. Disk paths to delete, collected before the rows go away. The rows are
    #    written inside this transaction; if it rolls back, no cleanup happens.
    videos = (await db.execute(select(Video).where(Video.user_id == user.id))).scalars().all()
    export_paths = [
        fp
        for fp in (
            (await db.execute(select(DataExportTask.file_path).where(DataExportTask.user_id == user.id)))
            .scalars()
            .all()
        )
        if fp
    ]
    files, dirs = account_data.cleanup_paths(user, videos, list(export_paths))
    await account_data.enqueue_media_cleanup(db, user.id, files, dirs)

    # 2. Behavior events survive as aggregate stats, without the account link.
    await db.execute(sa_update(BehaviorEvent).where(BehaviorEvent.user_id == user.id).values(user_id=None))

    # 3. Official catalog videos are not the uploader's personal data — keep
    #    them, detach the account. User-uploaded (non-official) videos go with
    #    the account; their subtitles/dispatches cascade.
    official_ids = [video.id for video in videos if video.is_official]
    if official_ids:
        await db.execute(sa_update(Video).where(Video.id.in_(official_ids)).values(user_id=None))
    user_video_ids = [video.id for video in videos if not video.is_official]
    if user_video_ids:
        from app.services.lesson_learning import detach_lesson_words_from_videos

        await detach_lesson_words_from_videos(db, user_video_ids)
        await db.execute(sa_delete(Video).where(Video.id.in_(user_video_ids)))

    #    Course rows hang off a word row and a conversation, not a user column;
    #    Postgres cascades them but SQLite does not, so delete them here. This
    #    must run BEFORE the V2 children, because the anchor rows are found
    #    through their conversation and that sweep deletes the conversations.
    from app.services.lesson_learning import purge_learner_facts

    await purge_learner_facts(db, user.id)

    await _delete_v2_children(db, user.id)

    # 4. Every remaining table with a user_id FK to users.id, children before
    #    parents. The excluded ones were handled above; DB-level ON DELETE
    #    CASCADE covers nested rows (exam answers, study items, …).
    from app.services.v2_schema import existing_tables

    present = await existing_tables(db)
    user_scoped = [
        t
        for t in Base.metadata.sorted_tables
        if t.name not in account_data.PURGE_EXCLUDED_TABLES
        and t.name in present
        and "user_id" in t.columns
        and any(fk.target_fullname == "users.id" for fk in t.columns["user_id"].foreign_keys)
    ]
    for table in reversed(user_scoped):
        await db.execute(sa_delete(table).where(table.columns["user_id"] == user.id))

    # 5. Delete the user row — this is where the phone number is released.
    await db.execute(sa_delete(UserModel).where(UserModel.id == user.id))
    await db.commit()

    # 6. Drain the media queue now; failures stay pending for the beat retry.
    result = await account_data.process_media_cleanup(db, limit=500)
    logger.info(
        "account_purged",
        user_id=user.id,
        media_files=len(files),
        media_dirs=len(dirs),
        **result,
    )


async def _prepare_v2_removal(db, user_id: str) -> None:
    """Revoke access, fence execution, and retain a remote lifecycle intent atomically."""
    from app.services.v2_schema import existing_columns, existing_tables

    async def has_conversation_columns(db, table: str) -> bool:
        return "conversation_id" in await existing_columns(db, table)

    # Deletion must complete even when the V2 migration never ran: a missing
    # table means there is nothing to revoke or fence, not that the account
    # should stay alive past its 30-day promise. Alembic applies one revision
    # at a time, so each group is checked on its own instead of all-or-nothing.
    present = await existing_tables(db)
    if not present & {"external_connections", "teaching_sessions", "agent_runs", "gateway_lifecycle_intents"}:
        return

    from sqlalchemy import select

    from app.models.teaching import TeachingSession
    from app.models.v2_runtime import AgentRun, ExternalConnection, ExternalCredential, GatewayLifecycleIntent

    now = datetime.now(UTC)
    if "external_connections" in present:
        connections = (
            (
                await db.execute(
                    select(ExternalConnection)
                    .where(ExternalConnection.user_id == user_id)
                    .order_by(ExternalConnection.id)
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )
        for connection in connections:
            connection.revoked_at = connection.revoked_at or now
            if "external_credentials" not in present:
                continue
            credentials = (
                await db.execute(select(ExternalCredential).where(ExternalCredential.connection_id == connection.id))
            ).scalars()
            for credential in credentials:
                credential.revoked_at = credential.revoked_at or now
    if "teaching_sessions" in present:
        await db.execute(
            select(TeachingSession.id)
            .where(TeachingSession.user_id == user_id)
            .order_by(TeachingSession.id)
            .with_for_update()
        )
    # The ORM now selects ``agent_runs.conversation_id``; on a database
    # stopped before P02.3 this table has none of the conversation columns, so
    # touching it would break deletion instead of fencing it.
    if "agent_runs" in present and await has_conversation_columns(db, "agent_runs"):
        runs = (
            await db.execute(
                select(AgentRun)
                .where(AgentRun.user_id == user_id, AgentRun.status.in_(["queued", "running"]))
                .order_by(AgentRun.id)
                .with_for_update()
            )
        ).scalars()
        for run in runs:
            run.status = "cancelled"
            run.cancel_requested_at = now
            run.finished_at = now
            run.lease_epoch += 1
    if "gateway_lifecycle_intents" in present:
        existing = await db.scalar(
            select(GatewayLifecycleIntent.id)
            .where(GatewayLifecycleIntent.subject_ref == user_id, GatewayLifecycleIntent.status == "pending")
            .limit(1)
        )
        if existing is None:
            db.add(GatewayLifecycleIntent(subject_ref=user_id, status="pending"))
    await db.flush()


async def _delete_v2_children(db, user_id: str) -> None:
    """Explicitly erase nested private records, also on SQLite test databases."""
    from sqlalchemy import delete, select

    from app.services.v2_schema import existing_columns, existing_tables

    present = await existing_tables(db)

    async def has_column(table: str, column: str) -> bool:
        return column in await existing_columns(db, table)

    from app.models.teaching import LearningEventOutbox, TeachingAttempt, TeachingItem, TeachingSession
    from app.models.v2_runtime import (
        AgentRun,
        AgentRunEvent,
        AgentStep,
        ExternalConnection,
        ExternalCredential,
        TeachingMessage,
        TeachingMessageBlock,
        TutorConversation,
        TutorConversationTask,
    )

    # These three tables gained P02.3 columns; the ORM selects them, so a
    # pre-P02.3 database must not be queried through the model at all. The
    # generic per-table sweep later still clears them by ``user_id``.
    if "agent_runs" in present and await has_column("agent_runs", "conversation_id"):
        run_ids = select(AgentRun.id).where(AgentRun.user_id == user_id)
        if "agent_run_events" in present:
            await db.execute(delete(AgentRunEvent).where(AgentRunEvent.run_id.in_(run_ids)))
        if "agent_steps" in present:
            await db.execute(delete(AgentStep).where(AgentStep.run_id.in_(run_ids)))
    if "teaching_messages" in present and await has_column("teaching_messages", "conversation_id"):
        message_ids = select(TeachingMessage.id).where(TeachingMessage.user_id == user_id)
        if "teaching_message_blocks" in present:
            await db.execute(delete(TeachingMessageBlock).where(TeachingMessageBlock.message_id.in_(message_ids)))
        await db.execute(delete(TeachingMessage).where(TeachingMessage.user_id == user_id))
    if "tutor_conversations" in present:
        conversation_ids = select(TutorConversation.id).where(TutorConversation.user_id == user_id)
        if "tutor_conversation_tasks" in present:
            await db.execute(
                delete(TutorConversationTask).where(TutorConversationTask.conversation_id.in_(conversation_ids))
            )
        await db.execute(delete(TutorConversation).where(TutorConversation.user_id == user_id))
    if "external_connections" in present and "external_credentials" in present:
        connection_ids = select(ExternalConnection.id).where(ExternalConnection.user_id == user_id)
        await db.execute(delete(ExternalCredential).where(ExternalCredential.connection_id.in_(connection_ids)))
    if "learning_event_outbox" in present:
        await db.execute(delete(LearningEventOutbox).where(LearningEventOutbox.user_id == user_id))
    if "teaching_sessions" in present:
        session_ids = select(TeachingSession.id).where(TeachingSession.user_id == user_id)
        if "teaching_attempts" in present and "teaching_items" in present:
            item_ids = select(TeachingItem.id).where(TeachingItem.session_id.in_(session_ids))
            await db.execute(delete(TeachingAttempt).where(TeachingAttempt.item_id.in_(item_ids)))
        if "teaching_items" in present:
            await db.execute(delete(TeachingItem).where(TeachingItem.session_id.in_(session_ids)))


async def _purge_due(now: datetime | None = None) -> int:
    from sqlalchemy import select

    from app.core.database import async_session
    from app.models.user import User

    now_utc = now or datetime.now(UTC)
    purged = 0
    async with async_session() as db:
        users = (
            (
                await db.execute(
                    select(User).where(
                        User.deletion_scheduled_at.is_not(None),
                        User.deletion_scheduled_at <= now_utc,
                    )
                )
            )
            .scalars()
            .all()
        )
        for user in users:
            try:
                await _purge_user(db, user)
                purged += 1
            except Exception:
                await db.rollback()
                logger.exception("account_purge_failed", user_id=user.id)

        # Sweep anything a previous run could not delete (locked files, a host
        # restart mid-cleanup). This is what makes the cleanup retryable.
        try:
            await account_data.process_media_cleanup(db)
            await account_data.prune_media_cleanup(db)
        except Exception:
            await db.rollback()
            logger.exception("media_cleanup_sweep_failed")
    return purged


async def _drain_media_cleanup(limit: int) -> dict:
    from app.core.database import async_session

    async with async_session() as db:
        result = await account_data.process_media_cleanup(db, limit=limit)
        pruned = await account_data.prune_media_cleanup(db)
    return {**result, "pruned": pruned}


@celery_app.task
def retry_media_cleanup(limit: int = 200):
    """Beat: retry account-deletion media cleanup that failed (A08)."""
    try:
        return run_async(_drain_media_cleanup(limit))
    except Exception:
        logger.exception("retry_media_cleanup failed")
        return {"processed": 0, "done": 0, "failed": 0, "pruned": 0}


@celery_app.task
def purge_deleted_accounts(now: datetime | None = None):
    """Daily sweep: finalize every account whose 30-day window has elapsed."""
    try:
        return run_async(_purge_due(now))
    except Exception:
        logger.exception("purge_deleted_accounts failed")
        return 0
