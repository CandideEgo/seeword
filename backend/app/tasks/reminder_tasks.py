"""Celery beat tasks for study reminders (产品设计规划-2026-08 §4-D6).

Two reminder families, all delivered as in-app notifications via
``notification_service.create_notification`` + ``commit_and_push``:

- ``send_hourly_reminders``: hourly sweep. Sends the vocabulary-review
  reminder when the user's local clock hits their ``vocabulary_reminder_time``
  hour and they have due words. The former streak-at-risk warning was
  retired; ``sent["streak_warning"]`` stays at 0 for compatibility.

The former ``send_pro_expiring_reminders`` sweep was removed with the retired
paid-membership chain (2026-11).

Timezone handling comes from the single authority in
``app.services.local_time`` (BUG-16 / DEC-079): the user's
``reminder_timezone`` preference, defaulting to ``Asia/Shanghai`` — the same
basis the daily counters and rounds use, so 「昨天」means the same thing here
as it does in the streak/profile numbers.

Deduplication: a per-user per-day Redis key (``SET NX EX 86400``) blocks
re-sends within the same local day. Redis outage is fail-open — the send
proceeds and ``create_notification``'s unread-dedup (same user/type/url)
is the fallback. Task bodies accept an optional aware-UTC ``now`` as a
test seam; beat always invokes them with no arguments.
"""

from datetime import UTC, datetime

import structlog

from app.services.local_time import resolve_user_timezone
from app.tasks.async_helpers import run_async
from app.tasks.celery_app import celery_app

logger = structlog.get_logger()


def _to_local(now_utc: datetime, tz_name: str | None) -> datetime:
    """Convert aware UTC to the user's local wall-clock time."""
    return now_utc.astimezone(resolve_user_timezone(tz_name))


def _merged_prefs(prefs) -> dict:
    """Merge stored notification_preferences over the defaults (same rule
    as GET /notifications/preferences)."""
    from app.models.preferences import DEFAULT_NOTIFICATION_PREFS

    merged = DEFAULT_NOTIFICATION_PREFS.copy()
    if prefs is not None and isinstance(prefs.notification_preferences, dict):
        merged.update(prefs.notification_preferences)
    return merged


async def _claim_daily_slot(key: str) -> bool:
    """SET NX one-per-day guard. Fail-open: any Redis error lets the send
    proceed (create_notification's unread-dedup is the fallback)."""
    try:
        from app.core.redis import get_redis

        ok = await get_redis().set(key, "1", nx=True, ex=86400)
        return bool(ok)
    except Exception:
        logger.warning("reminder_redis_fail_open", key=key)
        return True


async def _count_due_words(db, user_id: str, now_utc: datetime) -> int:
    from sqlalchemy import func, select

    from app.models.learning import Vocabulary

    result = await db.execute(
        select(func.count(Vocabulary.id)).where(
            Vocabulary.user_id == user_id,
            (Vocabulary.next_review_at.is_(None)) | (Vocabulary.next_review_at <= now_utc),
            # Mastered words exited review (tri-state semantics) — no reminder.
            Vocabulary.mastery_level != "mastered",
        )
    )
    return result.scalar() or 0


@celery_app.task
def send_hourly_reminders(now: datetime | None = None):
    """Hourly sweep: vocabulary-review reminder + streak-at-risk warning.

    Runs on a Celery beat schedule (crontab minute=0). Each user is matched
    against their own local time so a single sweep covers all timezones.
    """
    from app.core.database import async_session

    async def _process():
        from sqlalchemy import select

        from app.models.preferences import UserPreferences
        from app.models.user import User
        from app.services.notification_service import commit_and_push, create_notification

        now_utc = now or datetime.now(UTC)
        sent = {"vocabulary_reminder": 0, "streak_warning": 0}

        async with async_session() as db:
            rows = (
                await db.execute(
                    select(User, UserPreferences).outerjoin(UserPreferences, UserPreferences.user_id == User.id)
                )
            ).all()

            notifications = []
            for user, prefs in rows:
                nprefs = _merged_prefs(prefs)
                local_now = _to_local(now_utc, prefs.reminder_timezone if prefs else None)

                # ── Vocabulary review reminder (user's chosen hour) ──
                if nprefs.get("vocabulary_reminder", False):
                    reminder_time = (
                        (prefs.reminder_time if prefs else None) or nprefs.get("vocabulary_reminder_time") or "20:00"
                    )
                    try:
                        reminder_hour = int(str(reminder_time).split(":")[0])
                    except ValueError:
                        reminder_hour = 20
                    if local_now.hour == reminder_hour:
                        due = await _count_due_words(db, user.id, now_utc)
                        if due > 0:
                            key = f"reminder:vocabulary_reminder:{user.id}:{local_now.date().isoformat()}"
                            if await _claim_daily_slot(key):
                                notifications.append(
                                    await create_notification(
                                        user_id=user.id,
                                        type="vocabulary_reminder",
                                        title="词汇复习提醒",
                                        message=f"你有 {due} 个单词待复习，2 分钟搞定",
                                        db=db,
                                        related_url="/vocabulary",
                                    )
                                )
                                sent["vocabulary_reminder"] += 1

            if sent["vocabulary_reminder"] or sent["streak_warning"]:
                await commit_and_push(db, notifications)
            logger.info("hourly_reminders_sent", **sent)
            return sent

    try:
        return run_async(_process())
    except Exception:
        logger.exception("send_hourly_reminders failed")
        return {"vocabulary_reminder": 0, "streak_warning": 0}
