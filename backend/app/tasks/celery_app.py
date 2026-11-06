from celery import Celery
from celery.schedules import crontab
from kombu import Queue

from app.core.config import get_settings
from app.core.observability import celery_role, init_sentry

# Celery task name for the transcription step. The *implementation* now lives in
# the standalone ``gpu-worker/`` component (the GPU machine consumes the
# ``transcription_gpu`` queue); the cloud enqueues it by name with
# ``celery_app.send_task`` and has no import path to the worker. The literal is
# kept for compatibility with already-queued messages and the documented
# head/GPU/tail contract — do not rename without draining the queue.
GPU_TRANSCRIBE_TASK = "app.tasks.video_processing.transcribe_video_gpu"

settings = get_settings()

# A09/OPS-05: worker and beat exceptions now reach Sentry with the same
# scrubbing as the web process (previously only main.py initialised it).
init_sentry(celery_role())

celery_app = Celery(
    "speaking",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Queue topology: the cloud worker consumes the default ``celery`` queue;
    # the remote GPU worker (the standalone ``gpu-worker/`` component) consumes
    # ``transcription_gpu`` exclusively. Only the transcription task is routed
    # off the default queue — everything else (video pipeline head/tail,
    # localize) runs on the cloud.
    task_default_queue="celery",
    task_queues=(Queue("celery"), Queue(settings.transcription_gpu_queue_name), Queue("teaching")),
    task_routes={
        GPU_TRANSCRIBE_TASK: {"queue": settings.transcription_gpu_queue_name},
        "app.tasks.teaching_tasks.execute_teaching_run": {"queue": "teaching"},
    },
    beat_schedule={
        "sweep-teaching-runs": {
            "task": "app.tasks.teaching_tasks.sweep_teaching_runs",
            "schedule": 10,
        },
        # Mark videos stuck in any pipeline step (translating/downloading/
        # transcoding/...) as failed when the worker is offline or hung longer
        # than the step's per-step timeout. Covers both ``processing`` (head)
        # and ``ready_subtitles`` (tail) phases.
        "watchdog-stale-pipeline": {
            "task": "app.tasks.video_processing.watchdog_stale_pipeline",
            "schedule": 600,  # every 10 minutes
        },
        # A05/BE-01: re-send pipeline hand-offs whose DB state committed but
        # whose Celery message never reached the broker (broker down / crash in
        # the gap). Runs every minute so the recovery window stays short; also
        # prunes settled rows and alerts on a backlog that will not drain.
        "dispatch-pipeline-tasks": {
            "task": "app.tasks.pipeline_dispatch_tasks.dispatch_pipeline_tasks",
            "schedule": 60,
        },
        # Re-attempt failed YouTube downloads for ready videos that fell back
        # to embed playback (阶段 3). Daily; refreshes cookies first, respects
        # the 3-strike limit via localize_video's force=False path.
        "retry-failed-downloads": {
            "task": "app.tasks.video_processing.retry_failed_downloads",
            "schedule": 86400,  # every 24 hours
        },
        # P1 scoring: refresh hot videos hourly, all videos daily. New videos
        # are also scored immediately at the end of finalize_video.
        "score-videos-hourly": {
            "task": "app.tasks.scoring_tasks.compute_top_scores",
            "schedule": 3600,  # every hour — Top 200 by view_count
        },
        "score-videos-daily": {
            "task": "app.tasks.scoring_tasks.compute_all_scores",
            "schedule": 86400,  # every day — full recompute
        },
        # 首页排行榜快照：每日 16:30 UTC（= 北京次日 00:30）重算三个榜单
        # （latest / weekly_views / weekly_favorites）并覆写 Redis 快照；
        # GET /videos/rankings 读穿缓存，Redis 故障时 fail-open 直接查库。
        # 周榜按北京自然周（周一 00:00）切分，排在 00:30 刷新让周一换榜最多滞后半小时。
        "snapshot-rankings": {
            "task": "app.tasks.ranking_tasks.snapshot_rankings",
            "schedule": crontab(minute=30, hour=16),
        },
        # 首页编辑内容：把卡在 queued/running 超过 900s 的生成任务标为 failed TIMEOUT
        # （GET 状态时也会顺手处理，本巡检是兜底）。生成任务本身走默认 celery 队列。
        "sweep-home-content-generations": {
            "task": "app.tasks.home_content_tasks.sweep_home_content_generations",
            "schedule": 600,  # every 10 minutes
        },
        # D6 学习提醒：每小时扫一次，按用户本地时间匹配词汇复习提醒点（断签警告已退役）。
        "send-hourly-reminders": {
            "task": "app.tasks.reminder_tasks.send_hourly_reminders",
            "schedule": crontab(minute=0),  # every hour on the hour
        },
        # P1-7 注销：每日清理已到期（30 天冷静期结束）的账号。
        "purge-deleted-accounts": {
            "task": "app.tasks.account_tasks.purge_deleted_accounts",
            "schedule": crontab(minute=30, hour=18),
        },
        # A08/BE-04：注销后媒体删除失败（文件被占用、主机重启）时重试。
        # 清理队列在删除用户的同一事务里写入，失败行带退避，永不静默丢失。
        "retry-media-cleanup": {
            "task": "app.tasks.account_tasks.retry_media_cleanup",
            "schedule": 900,  # every 15 minutes
        },
    },
)

# Ensure all models are loaded before importing task modules (SQLAlchemy relationship resolution)
# Register the task_prerun signal that binds request_id (task_id) into
# structlog context vars so every log line emitted during a Celery task
# automatically includes request_id for traceability.
import app.core.logging
import app.models
import app.tasks.account_tasks
import app.tasks.health_tasks
import app.tasks.home_content_tasks
import app.tasks.notification_tasks
import app.tasks.pipeline_dispatch_tasks  # A05: beat re-dispatches pending pipeline intents
import app.tasks.ranking_tasks
import app.tasks.reminder_tasks
import app.tasks.scoring_tasks
import app.tasks.teaching_tasks
import app.tasks.video_processing  # noqa: F401  (import registers the tasks with this app)
