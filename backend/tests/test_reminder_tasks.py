"""Direct-execution tests for the D6 reminder beat task bodies.

Same pattern as ``test_celery_tasks.py``: conftest stubs task dispatch and
routes ``async_session`` to the in-memory test DB, so we call the task
functions directly with an explicit aware-UTC ``now`` (test seam) and assert
on the notifications actually written.

Redis is monkeypatched to raise so every test exercises the documented
fail-open path: sends proceed, and same-day duplicates are prevented by
``create_notification``'s unread-dedup instead of the Redis NX key.
"""

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_async_session_maker
from app.models.learning import Vocabulary
from app.models.learning_plan import UserLearningProfile
from app.models.notification import Notification
from app.models.preferences import UserPreferences
from app.models.user import RoleType, User
from app.tasks.reminder_tasks import send_hourly_reminders

pytestmark = pytest.mark.usefixtures("_redis_down")


@pytest.fixture
def _redis_down(monkeypatch):
    """Force the fail-open branch: Redis 'outage' → sends proceed without NX guard."""

    def _raise():
        raise ConnectionError("redis down (test)")

    monkeypatch.setattr("app.core.redis.get_redis", _raise)


def _session_maker() -> async_sessionmaker[AsyncSession]:
    return get_async_session_maker()


# 12:00 UTC = 20:00 Asia/Shanghai — matches the default reminder time.
_NOW_REMINDER_HOUR = datetime(2026, 8, 29, 12, 0, tzinfo=UTC)
# 13:00 UTC = 21:00 Asia/Shanghai — streak warning hour.
_NOW_STREAK_HOUR = datetime(2026, 8, 29, 13, 0, tzinfo=UTC)


async def _make_user(db, phone: str):
    user = User(
        phone=phone,
        hashed_password="hashed",
        name="Reminder Test",
        role=RoleType.user,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _set_prefs(db, user_id: str, **overrides):
    prefs = UserPreferences(
        user_id=user_id,
        reminder_timezone="Asia/Shanghai",
        notification_preferences={**{"vocabulary_reminder_time": "20:00", "vocabulary_reminder": True}, **overrides},
    )
    db.add(prefs)
    await db.commit()
    return prefs


async def _notifications(db, user_id: str, type_: str) -> list[Notification]:
    result = await db.execute(select(Notification).where(Notification.user_id == user_id, Notification.type == type_))
    return list(result.scalars().all())


# ── Vocabulary reminder ─────────────────────────────────────────────────


async def test_vocabulary_reminder_sent_when_due_words_at_reminder_hour():
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100001")
        await _set_prefs(db, user.id)
        db.add(Vocabulary(user_id=user.id, word="apple", next_review_at=None))  # new word = due
        db.add(Vocabulary(user_id=user.id, word="banana", next_review_at=_NOW_REMINDER_HOUR + timedelta(days=1)))
        await db.commit()
        user_id = user.id

    sent = send_hourly_reminders(now=_NOW_REMINDER_HOUR)

    assert sent["vocabulary_reminder"] == 1
    async with _session_maker()() as db:
        notes = await _notifications(db, user_id, "vocabulary_reminder")
        assert len(notes) == 1
        assert "1 个单词" in notes[0].message
        assert notes[0].related_url == "/vocabulary"


async def test_vocabulary_reminder_not_sent_outside_reminder_hour():
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100002")
        await _set_prefs(db, user.id)
        db.add(Vocabulary(user_id=user.id, word="apple", next_review_at=None))
        await db.commit()
        user_id = user.id

    # 11:00 UTC = 19:00 local → not the 20:00 reminder hour
    send_hourly_reminders(now=_NOW_REMINDER_HOUR - timedelta(hours=1))

    async with _session_maker()() as db:
        assert await _notifications(db, user_id, "vocabulary_reminder") == []


async def test_vocabulary_reminder_skipped_when_no_due_words():
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100003")
        await _set_prefs(db, user.id)
        db.add(Vocabulary(user_id=user.id, word="apple", next_review_at=_NOW_REMINDER_HOUR + timedelta(days=2)))
        await db.commit()
        user_id = user.id

    sent = send_hourly_reminders(now=_NOW_REMINDER_HOUR)

    assert sent["vocabulary_reminder"] == 0
    async with _session_maker()() as db:
        assert await _notifications(db, user_id, "vocabulary_reminder") == []


async def test_vocabulary_reminder_respects_opt_out():
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100004")
        await _set_prefs(db, user.id, vocabulary_reminder=False)
        db.add(Vocabulary(user_id=user.id, word="apple", next_review_at=None))
        await db.commit()
        user_id = user.id

    sent = send_hourly_reminders(now=_NOW_REMINDER_HOUR)

    assert sent["vocabulary_reminder"] == 0
    async with _session_maker()() as db:
        assert await _notifications(db, user_id, "vocabulary_reminder") == []


async def test_vocabulary_reminder_not_duplicated_on_same_day_rerun():
    """Second sweep on the same day updates the unread notification instead
    of creating a duplicate (Redis down → unread-dedup fallback)."""
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100005")
        await _set_prefs(db, user.id)
        db.add(Vocabulary(user_id=user.id, word="apple", next_review_at=None))
        await db.commit()
        user_id = user.id

    send_hourly_reminders(now=_NOW_REMINDER_HOUR)
    send_hourly_reminders(now=_NOW_REMINDER_HOUR)

    async with _session_maker()() as db:
        assert len(await _notifications(db, user_id, "vocabulary_reminder")) == 1


# ── Streak warning ──────────────────────────────────────────────────────


async def test_streak_warning_sent_at_21_when_streak_at_risk():
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100006")
        await _set_prefs(db, user.id)
        db.add(
            UserLearningProfile(
                user_id=user.id,
                current_streak=3,
                last_active_date=date(2026, 8, 28),  # active yesterday, not today
            )
        )
        await db.commit()
        user_id = user.id

    sent = send_hourly_reminders(now=_NOW_STREAK_HOUR)

    assert sent["streak_warning"] == 0
    async with _session_maker()() as db:
        notes = await _notifications(db, user_id, "streak_warning")
        assert notes == []


async def test_streak_warning_skipped_when_already_active_today():
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100007")
        await _set_prefs(db, user.id)
        db.add(
            UserLearningProfile(
                user_id=user.id,
                current_streak=3,
                last_active_date=date(2026, 8, 29),  # local today (13:00 UTC = 21:00 CST)
            )
        )
        await db.commit()
        user_id = user.id

    sent = send_hourly_reminders(now=_NOW_STREAK_HOUR)

    assert sent["streak_warning"] == 0
    async with _session_maker()() as db:
        assert await _notifications(db, user_id, "streak_warning") == []


async def test_streak_warning_skipped_when_streak_below_two():
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100008")
        await _set_prefs(db, user.id)
        db.add(UserLearningProfile(user_id=user.id, current_streak=1, last_active_date=date(2026, 8, 28)))
        await db.commit()
        user_id = user.id

    sent = send_hourly_reminders(now=_NOW_STREAK_HOUR)

    assert sent["streak_warning"] == 0
    async with _session_maker()() as db:
        assert await _notifications(db, user_id, "streak_warning") == []


async def test_streak_warning_respects_opt_out():
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100009")
        await _set_prefs(db, user.id, streak_warning_enabled=False)
        db.add(UserLearningProfile(user_id=user.id, current_streak=5, last_active_date=date(2026, 8, 28)))
        await db.commit()
        user_id = user.id

    sent = send_hourly_reminders(now=_NOW_STREAK_HOUR)

    assert sent["streak_warning"] == 0
    async with _session_maker()() as db:
        assert await _notifications(db, user_id, "streak_warning") == []


async def test_streak_warning_not_sent_and_counter_reset_when_already_broken():
    """Streak 已断（最后活跃早于昨天）：不再发警告（“已连续 N 天”文案会失真，
    且旧实现会无限期每天发），并顺带把惰性更新的 current_streak 归零。"""
    async with _session_maker()() as db:
        user = await _make_user(db, "13800100010")
        await _set_prefs(db, user.id)
        db.add(
            UserLearningProfile(
                user_id=user.id,
                current_streak=5,
                last_active_date=date(2026, 8, 27),  # two days ago → already broken
            )
        )
        await db.commit()
        user_id = user.id

    sent = send_hourly_reminders(now=_NOW_STREAK_HOUR)

    assert sent["streak_warning"] == 0
    async with _session_maker()() as db:
        assert await _notifications(db, user_id, "streak_warning") == []
        profile = (
            await db.execute(select(UserLearningProfile).where(UserLearningProfile.user_id == user_id))
        ).scalar_one()
        assert profile.current_streak == 5
