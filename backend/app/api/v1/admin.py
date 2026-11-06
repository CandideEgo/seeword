"""Admin API router — all admin-only endpoints under /api/v1/admin.

This router consolidates the admin management endpoints that don't belong
in existing domain routers (videos, users). Those keep their admin
routes in-place; this file adds the missing ones:

  - Dashboard stats
  - User management (list, ban, role change)
"""

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_admin_user
from app.core.database import get_db
from app.core.limiter import rate_limit
from app.models.user import User
from app.schemas.admin import (
    AdminAccountItem,
    AdminLearningMetricsResponse,
    AdminSettingsResponse,
    AdminSettingsUpdate,
    AdminStatsResponse,
    AdminUserBanRequest,
    AdminUserBanResponse,
    AdminUserRoleRequest,
    AdminUserRoleResponse,
    AdminUserRow,
    WorkerStatusResponse,
)
from app.schemas.pagination import PaginatedResponse
from app.services import admin_service, admin_stats

router = APIRouter(prefix="/admin", tags=["admin"])

#: Admin user-list filters are validated by FastAPI (422 instead of silently
#: ignoring unknown values, ADM-11).
AdminRoleFilter = Literal["user", "admin"]


# ---------------------------------------------------------------------------
# GPU worker status
# ---------------------------------------------------------------------------


@router.get("/worker-status", response_model=WorkerStatusResponse)
@rate_limit("30/minute")
async def get_worker_status(
    request: Request,
    current_user: User = Depends(get_admin_user),
):
    """Check if the local GPU worker is online (heartbeat present in Redis)."""
    from app.services.video_seed_service import is_gpu_worker_online

    online = await is_gpu_worker_online()
    return {"worker_online": online}


# ---------------------------------------------------------------------------
# Stats dashboard
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=AdminStatsResponse)
@rate_limit("30/minute")
async def get_admin_stats(
    request: Request,
    days: int = Query(30, ge=7, le=90, description="Trend window in days"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Dashboard KPIs, trend data, distributions, and recent activity."""
    return await admin_stats.get_admin_stats(db, days=days)


@router.get("/metrics/learning", response_model=AdminLearningMetricsResponse)
@rate_limit("20/minute")
async def get_learning_metrics(
    request: Request,
    days: int = Query(30, ge=7, le=90, description="Cohort / event window in days"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """激活/留存、事件质量与性能基线（A12）。

    口径（分母、时间边界、成熟判定）随响应一起返回在 ``definitions`` 里——
    看数字的人必须先看到它，避免把累计人数读成漏斗、把未成熟 cohort 补进分母。
    """
    from app.services.measurement_service import learning_metrics

    return await learning_metrics(db, days=days)


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


@router.get("/users", response_model=PaginatedResponse[AdminUserRow])
@rate_limit("30/minute")
async def list_admin_users(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: AdminRoleFilter | None = Query(None, description="Filter by role: user / admin"),
    keyword: str | None = Query(None, max_length=100, description="Search name or phone"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List users with aggregated stats. Admin only."""
    return await admin_service.list_admin_users(db, page=page, page_size=page_size, role=role, keyword=keyword)


@router.patch("/users/{user_id}/ban", response_model=AdminUserBanResponse)
@rate_limit("10/minute")
async def ban_user(
    request: Request,
    user_id: str,
    payload: AdminUserBanRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Ban or unban a user. Admin only (cannot ban self)."""
    user = await admin_service.ban_user(db, user_id, payload.is_banned, current_user.id)
    return {
        "id": user.id,
        "is_banned": user.is_banned,
    }


@router.patch("/users/{user_id}/role", response_model=AdminUserRoleResponse)
@rate_limit("10/minute")
async def change_user_role(
    request: Request,
    user_id: str,
    payload: AdminUserRoleRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user role (admin/user). Admin only (cannot change own role)."""
    user = await admin_service.change_user_role(db, user_id, payload.role, current_user.id)
    return {
        "id": user.id,
        "role": user.role.value,
    }


# ---------------------------------------------------------------------------
# Platform settings (prototype 32 系统设置)
# ---------------------------------------------------------------------------


@router.get("/settings", response_model=AdminSettingsResponse)
@rate_limit("30/minute")
async def get_settings(
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the singleton admin settings row (defaults if absent)."""
    settings = await admin_service.get_admin_settings(db)
    return {
        "site_name": settings.site_name,
        "registration_enabled": settings.registration_enabled,
        "quality_block_enabled": settings.quality_block_enabled,
        "quality_block_threshold": float(settings.quality_block_threshold),
        "quality_warn_threshold": float(settings.quality_warn_threshold),
        "hallucination_detection_enabled": settings.hallucination_detection_enabled,
        "translate_timeout_sec": settings.translate_timeout_sec,
        "download_timeout_sec": settings.download_timeout_sec,
        "download_auto_retry_enabled": settings.download_auto_retry_enabled,
        "watchdog_enabled": settings.watchdog_enabled,
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
    }


@router.put("/settings", response_model=AdminSettingsResponse)
@rate_limit("10/minute")
async def update_settings(
    request: Request,
    payload: AdminSettingsUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Partially update the singleton admin settings row. Admin only."""
    settings = await admin_service.update_admin_settings(db, payload.model_dump(exclude_unset=True))
    return {
        "site_name": settings.site_name,
        "registration_enabled": settings.registration_enabled,
        "quality_block_enabled": settings.quality_block_enabled,
        "quality_block_threshold": float(settings.quality_block_threshold),
        "quality_warn_threshold": float(settings.quality_warn_threshold),
        "hallucination_detection_enabled": settings.hallucination_detection_enabled,
        "translate_timeout_sec": settings.translate_timeout_sec,
        "download_timeout_sec": settings.download_timeout_sec,
        "download_auto_retry_enabled": settings.download_auto_retry_enabled,
        "watchdog_enabled": settings.watchdog_enabled,
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None,
    }


@router.get("/admins", response_model=list[AdminAccountItem])
@rate_limit("30/minute")
async def list_admin_accounts(
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List accounts with admin role (settings page 管理员账户). Admin only."""
    return await admin_service.list_admin_accounts(db)
