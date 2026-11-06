"""Retired product capabilities; historical records remain intact."""

from typing import NoReturn

from app.core.errors import AppError, ErrorCode

RETIRED_NOTIFICATION_TYPES = frozenset(
    {
        "achievement",
        "achievement_unlocked",
        "milestone",
        "weekly_report",
        "streak_warning",
        "streak_reminder",
        "speaking_feedback",
        "pro_expiring",
    }
)
RETIRED_NOTIFICATION_PREFS = frozenset({*RETIRED_NOTIFICATION_TYPES, "streak_warning_enabled"})


def feature_gone() -> NoReturn:
    raise AppError(410, ErrorCode.FEATURE_RETIRED, "功能已下线")


def sanitize_notification_preferences(values: dict) -> dict:
    return {**values, **dict.fromkeys(RETIRED_NOTIFICATION_PREFS, False)}
