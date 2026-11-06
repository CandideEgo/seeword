"""Shared opt-in gate for HTTP, worker and external tools."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.user import User
from app.models.v2_runtime import TeachingAccessGrant


async def require_access(db: AsyncSession, user_id: str, flag: str) -> None:
    settings = get_settings()
    # The switch is checked before any V2 table is read: with every teaching
    # flag off (the default) this entry point must answer 503 on a database
    # whose V2 migrations never ran, not raise on a missing
    # ``teaching_access_grants`` table.  A closed feature is 503 regardless of
    # the account's state; the ban/lifecycle check applies once it opens.
    if not getattr(settings, flag, False):
        raise AppError(503, "SERVICE_UNAVAILABLE", "教学功能暂未开放")
    user = await db.get(User, user_id)
    if user is None or user.is_banned or user.deletion_requested_at:
        raise AppError(403, "FORBIDDEN", "账号暂不可使用教学功能")
    bootstrap = {value.strip() for value in settings.teaching_allowed_user_ids.split(",") if value.strip()}
    if user_id not in bootstrap and await db.get(TeachingAccessGrant, user_id) is None:
        raise AppError(503, "SERVICE_UNAVAILABLE", "教学功能暂未开放")
