from datetime import datetime

from pydantic import BaseModel

# API-facing default notification preferences (what the client GETs/PUTs and
# what NotificationPreferencesResponse exposes). This is deliberately a
# different key set from ``app.models.preferences.DEFAULT_NOTIFICATION_PREFS``,
# the row-level JSON default — see the comment there. Community-typed prefs
# (community_updates/new_follower/comment_reply) are dormant since ADR-0012 cut
# the community — kept for schema compat, OFF by default.
DEFAULT_NOTIFICATION_PREFS: dict[str, bool] = {
    "push_notifications": True,
    "vocabulary_reminder": False,
    "streak_reminder": False,
    "weekly_report": False,
    "community_updates": False,
    "new_follower": False,
    "comment_reply": False,
}


class NotificationResponse(BaseModel):
    """对外通知形状。**不含 `user_id`**：通知永远只返回给本人，让归属字段出现在
    响应里既无用又诱导前端拿它做客户端过滤（那是服务端的鉴权职责）。"""

    id: str
    type: str
    title: str
    message: str | None = None
    is_read: bool = False
    related_url: str | None = None
    data: str | None = None
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    count: int


class NotificationPreferencesResponse(BaseModel):
    push_notifications: bool = DEFAULT_NOTIFICATION_PREFS["push_notifications"]
    vocabulary_reminder: bool = DEFAULT_NOTIFICATION_PREFS["vocabulary_reminder"]
    streak_reminder: bool = DEFAULT_NOTIFICATION_PREFS["streak_reminder"]
    weekly_report: bool = DEFAULT_NOTIFICATION_PREFS["weekly_report"]
    # Community-typed prefs are dormant (ADR-0012) — OFF by default.
    community_updates: bool = DEFAULT_NOTIFICATION_PREFS["community_updates"]
    new_follower: bool = DEFAULT_NOTIFICATION_PREFS["new_follower"]
    comment_reply: bool = DEFAULT_NOTIFICATION_PREFS["comment_reply"]

    model_config = {"from_attributes": True}


class NotificationPreferencesUpdate(BaseModel):
    push_notifications: bool | None = None
    vocabulary_reminder: bool | None = None
    streak_reminder: bool | None = None
    weekly_report: bool | None = None
    community_updates: bool | None = None
    new_follower: bool | None = None
    comment_reply: bool | None = None
