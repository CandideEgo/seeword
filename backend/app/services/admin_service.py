"""Admin service — business logic for the admin panel endpoints.

All functions receive an ``AsyncSession`` and return plain dicts or model
instances that the route handler serialises via Pydantic schemas.
"""

import logging
from enum import Enum

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import commit_refresh
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.core.time_utils import iso_or_none
from app.models.admin_setting import SETTINGS_ROW_ID, AdminSetting
from app.models.learning import LearningRecord, Vocabulary
from app.models.user import RoleType, User
from app.schemas.pagination import paginated

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


#: 管理列表 keyword 的长度上限（ADM-11：避免把整段文本当 LIKE 模式拖慢全表扫描）。
_ADMIN_KEYWORD_MAX_LEN = 100


def _like_escape(value: str) -> str:
    """Escape LIKE metacharacters (``%`` / ``_``) and the escape char itself.

    Same approach as ``video_service``: pass ``escape="\\"`` to every LIKE and
    escape the user input first. Without this, searching for ``%`` matches the
    whole table (ADM-11).
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _parse_enum_filter(value: str, enum_cls: type[Enum], label: str):
    """Turn a raw filter string into an enum member, 400 on unknown values.

    The routes already validate via ``Literal`` (422); this is the defensive
    service-layer guard for direct callers, and it replaces the old
    ``except ValueError: pass`` that silently returned the unfiltered list.
    """
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = "/".join(str(member.value) for member in enum_cls)
        raise BadRequestError(f"无效的{label}过滤值：{value}（可选 {allowed}）") from exc


async def list_admin_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    role: str | None = None,
    keyword: str | None = None,
) -> dict:
    """List users with aggregated stats, filtered by role/keyword.

    Filter values are validated instead of silently ignored (ADM-11), the
    keyword is LIKE-escaped and length-capped, and ordering carries an ``id``
    tiebreaker so OFFSET pagination cannot duplicate/skip rows with equal
    ``created_at`` timestamps (ADM-10).
    """

    # Subqueries for aggregated counts.
    # Note: speaking-attempt counts are intentionally omitted — AI speaking
    # scoring was removed (ADR-0002/0003), so a per-user speaking count is
    # dead data.
    vw_count = (
        select(func.count(LearningRecord.id)).where(LearningRecord.user_id == User.id).correlate(User).scalar_subquery()
    )
    lw_count = select(func.count(Vocabulary.id)).where(Vocabulary.user_id == User.id).correlate(User).scalar_subquery()

    stmt = select(
        User,
        vw_count.label("videos_watched"),
        lw_count.label("learned_words"),
    )

    def _apply_filters(s):
        if role:
            s = s.where(User.role == _parse_enum_filter(role, RoleType, "角色"))
        if keyword and keyword.strip():
            k = keyword.strip().lower()
            if len(k) > _ADMIN_KEYWORD_MAX_LEN:
                raise BadRequestError(f"搜索关键词最长 {_ADMIN_KEYWORD_MAX_LEN} 个字符")
            pattern = f"%{_like_escape(k)}%"
            s = s.where(func.lower(User.name).like(pattern, escape="\\") | User.phone.like(pattern, escape="\\"))
        return s

    stmt = _apply_filters(stmt)

    # Count total for has_more
    count_stmt = _apply_filters(select(func.count(User.id)))
    total = (await db.execute(count_stmt)).scalar_one()

    # Paginate. ``User.id`` is the deterministic tiebreaker (ADM-10).
    stmt = stmt.order_by(User.created_at.desc(), User.id).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).all()

    items = []
    for row in rows:
        user: User = row[0]
        items.append(
            {
                "id": user.id,
                "phone": user.phone,
                "name": user.name,
                "bio": user.bio,
                "avatar_url": user.avatar_url,
                "gender": user.gender,
                "level": user.level,
                "timezone": user.timezone,
                "role": user.role.value if user.role else "user",
                "is_banned": user.is_banned,
                "created_at": iso_or_none(user.created_at),
                "last_active_at": iso_or_none(user.last_active_at),
                "videos_watched": int(row[1] or 0),
                "learned_words": int(row[2] or 0),
            }
        )

    return paginated(items, page=page, page_size=page_size, total=total)


# ---------------------------------------------------------------------------
# Admin settings (prototype 32 系统设置)
# ---------------------------------------------------------------------------


#: 首次创建设置单例各尝试几次（并发首建撞主键后重读）。
_SETTINGS_INSERT_ATTEMPTS = 3


async def _select_admin_settings(db: AsyncSession) -> AdminSetting | None:
    result = await db.execute(select(AdminSetting).where(AdminSetting.id == SETTINGS_ROW_ID))
    return result.scalar_one_or_none()


async def get_admin_settings(db: AsyncSession) -> AdminSetting:
    """Return the singleton settings row, creating it with defaults if absent.

    ADM-14: two concurrent first visits (fresh deploy, or two admins hitting
    the settings page before anyone saved it) used to race the plain
    ``add + commit`` into a primary-key ``IntegrityError`` → 500. The insert is
    now wrapped in a SAVEPOINT: the loser re-reads the winner's row instead of
    aborting the whole transaction (same pattern as
    ``home_content_service._get_or_create_*``).
    """
    settings = await _select_admin_settings(db)
    if settings is not None:
        return settings
    for _ in range(_SETTINGS_INSERT_ATTEMPTS):
        candidate = AdminSetting(id=SETTINGS_ROW_ID)
        try:
            async with db.begin_nested():
                db.add(candidate)
                await db.flush()
        except IntegrityError:
            # SAVEPOINT rollback leaves the (never-persisted) candidate attached.
            if candidate in db:
                db.expunge(candidate)
            settings = await _select_admin_settings(db)
            if settings is not None:
                return settings
            continue
        await db.commit()
        await db.refresh(candidate)
        return candidate
    raise ConflictError("系统设置初始化冲突，请重试")


async def update_admin_settings(db: AsyncSession, patch: dict) -> AdminSetting:
    """Apply a partial update to the singleton settings row.

    Cross-field validation happens **before** mutating the ORM object (ADM-14):
    a rejected patch must not leave half-applied attributes on the session
    (a later request on the same session would see them, and ``rollback`` is
    not called by the error handler).

    Raises ``BadRequestError`` if the thresholds are inconsistent
    (warn threshold must be >= block threshold).
    """
    settings = await get_admin_settings(db)

    # Merge the patch with the current values on plain python floats, then
    # validate — only after that touch the instance.
    block_t = float(patch.get("quality_block_threshold", settings.quality_block_threshold))
    warn_t = float(patch.get("quality_warn_threshold", settings.quality_warn_threshold))
    if warn_t < block_t:
        raise BadRequestError("警告阈值不能低于阻塞阈值")

    for key, value in patch.items():
        if value is not None:
            setattr(settings, key, value)
    await commit_refresh(db, settings)
    return settings


async def list_admin_accounts(db: AsyncSession) -> list[dict]:
    """All accounts with role=admin (settings page 管理员账户 list)."""
    rows = (
        (await db.execute(select(User).where(User.role == RoleType.admin).order_by(User.created_at.asc())))
        .scalars()
        .all()
    )
    return [
        {
            "id": u.id,
            "name": u.name,
            "phone": u.phone,
            "last_active_at": iso_or_none(u.last_active_at),
        }
        for u in rows
    ]


# ---------------------------------------------------------------------------
# User actions (ban / role)
# ---------------------------------------------------------------------------


async def _get_user_or_raise(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    return user


async def _lock_admin_rows(db: AsyncSession) -> list[User]:
    """Lock every admin row (stable ``id`` order) and return the fresh state.

    ADM-09 last-admin protection needs a serialisation point: two admins
    banning/demoting each other can both pass a plain "is there another admin"
    read under READ COMMITTED and commit into zero usable admins. Locking all
    admin rows in one deterministic order turns those transactions into a
    queue (no deadlock, one waits), and ``populate_existing`` makes the waiter
    re-read the state committed by the transaction it just waited for.
    """
    result = await db.execute(
        select(User)
        .where(User.role == RoleType.admin)
        .order_by(User.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    return list(result.scalars().all())


def _assert_not_last_admin(admins: list[User], user_id: str) -> None:
    """409 when removing ``user_id`` would leave zero usable admins.

    ``admins`` is the locked admin set; usable = not banned. Called only for
    actions that actually remove admin usability (ban / demote).
    """
    target = next((a for a in admins if a.id == user_id), None)
    if target is None or target.is_banned:
        return  # Not an active admin → nothing to lose.
    others = sum(1 for a in admins if a.id != user_id and not a.is_banned)
    if others == 0:
        raise ConflictError("不能移除最后一名可用管理员：请先授予其他账号管理员权限")


async def ban_user(db: AsyncSession, user_id: str, is_banned: bool, admin_user_id: str) -> User:
    if user_id == admin_user_id:
        raise BadRequestError("Cannot ban yourself")
    user = await _get_user_or_raise(db, user_id)
    if is_banned and user.role == RoleType.admin:
        # Lock all admin rows *before* deciding — see _lock_admin_rows.
        admins = await _lock_admin_rows(db)
        _assert_not_last_admin(admins, user_id)
    user.is_banned = is_banned
    await commit_refresh(db, user)
    logger.info("admin_action ban_user actor=%s target=%s banned=%s", admin_user_id, user_id, is_banned)
    return user


async def change_user_role(db: AsyncSession, user_id: str, role: str, admin_user_id: str) -> User:
    if user_id == admin_user_id:
        raise BadRequestError("Cannot change your own role")
    new_role = _parse_enum_filter(role, RoleType, "角色")
    user = await _get_user_or_raise(db, user_id)
    if new_role == RoleType.user and user.role == RoleType.admin:
        # Demotion is the other way to remove the last usable admin (ADM-09).
        admins = await _lock_admin_rows(db)
        _assert_not_last_admin(admins, user_id)
    user.role = new_role
    await commit_refresh(db, user)
    logger.info("admin_action change_user_role actor=%s target=%s role=%s", admin_user_id, user_id, role)
    return user
