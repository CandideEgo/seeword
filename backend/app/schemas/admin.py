"""Admin-specific Pydantic schemas for request/response validation.

These schemas are separate from the user-facing schemas because admin responses
include extra fields (aggregated counts, cross-entity joins, admin-only flags)
that don't belong in the public API contract.
"""

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class AdminUserBanRequest(BaseModel):
    is_banned: bool


class AdminUserRoleRequest(BaseModel):
    role: Literal["user", "admin"]


class AdminSettingsUpdate(BaseModel):
    """Partial update of the singleton admin settings row (prototype 32)."""

    # 通用配置
    site_name: str | None = Field(default=None, max_length=100)
    registration_enabled: bool | None = None
    # 质量门禁
    quality_block_enabled: bool | None = None
    quality_block_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    quality_warn_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    hallucination_detection_enabled: bool | None = None
    # 视频管线
    translate_timeout_sec: int | None = Field(default=None, ge=60, le=86400)
    download_timeout_sec: int | None = Field(default=None, ge=60, le=86400)
    download_auto_retry_enabled: bool | None = None
    watchdog_enabled: bool | None = None


# ---------------------------------------------------------------------------
# Response schemas (BE-07: admin lists must not degrade to untyped items)
# ---------------------------------------------------------------------------


class AdminUserRow(BaseModel):
    id: str
    phone: str | None = None
    name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    gender: str | None = None
    level: str | None = None
    timezone: str | None = None
    role: str
    is_banned: bool = False
    created_at: str | None = None
    last_active_at: str | None = None
    videos_watched: int = 0
    learned_words: int = 0


class AdminSettingsResponse(BaseModel):
    site_name: str | None = None
    registration_enabled: bool
    quality_block_enabled: bool
    quality_block_threshold: float
    quality_warn_threshold: float
    hallucination_detection_enabled: bool
    translate_timeout_sec: int
    download_timeout_sec: int
    download_auto_retry_enabled: bool
    watchdog_enabled: bool
    updated_at: str | None = None


class WorkerStatusResponse(BaseModel):
    worker_online: bool


class AdminStatsTrend(BaseModel):
    dates: list[str]
    signups: list[int]
    vocabulary: list[int]
    active_users: list[int]


class AdminStatsCount(BaseModel):
    count: int


class AdminStatsVideoStatus(AdminStatsCount):
    status: str


class AdminStatsVideoTopic(AdminStatsCount):
    topic: str


class AdminStatsRecentActivity(BaseModel):
    id: str
    type: str
    summary: str
    created_at: str | None = None


class AdminStatsFunnel(BaseModel):
    registered: int
    watched: int
    vocab_saved: int


class AdminStatsResponse(BaseModel):
    total_users: int
    new_users_7d: int
    total_videos: int
    videos_ready: int
    total_vocabulary: int
    active_users_today: int
    active_users_7d: int
    online_now: int
    gpu_queue_depth: int
    videos_error_count: int
    signups_today: int
    trend: AdminStatsTrend
    videos_by_status: list[AdminStatsVideoStatus]
    recent_activity: list[AdminStatsRecentActivity]
    funnel: AdminStatsFunnel
    videos_by_topic: list[AdminStatsVideoTopic]


class AdminAccountItem(BaseModel):
    id: str
    name: str | None = None
    phone: str | None = None
    last_active_at: str | None = None


class AdminUserBanResponse(BaseModel):
    id: str
    is_banned: bool


class AdminUserRoleResponse(BaseModel):
    id: str
    role: str


# ---------------------------------------------------------------------------
# A12 学习测量（激活/留存、事件质量、性能基线）
# ---------------------------------------------------------------------------


class AdminActivationMetrics(BaseModel):
    window_registered: int
    activated_within_24h: int
    rate: float | None = None


class AdminCohortRow(BaseModel):
    cohort_date: str
    size: int
    d1_eligible: bool
    d1_retained: int | None = None
    d1_rate: float | None = None
    d7_eligible: bool
    d7_retained: int | None = None
    d7_rate: float | None = None


class AdminWeeklyVolume(BaseModel):
    active_7d: int
    multi_day_7d: int
    volume_rate: float | None = None


class AdminEventTypeQuality(BaseModel):
    event_type: str
    events: int
    with_event_id: int
    versions: dict[str, int]
    missing_event_id_rate: float | None = None


class AdminFlowReconciliation(BaseModel):
    path: str
    client_results: int
    client_distinct_flows: int
    server_facts: int
    matched: int
    client_only: int
    server_only: int
    duplicate_intents: int
    loss_rate: float | None = None


class AdminEventQuality(BaseModel):
    by_type: list[AdminEventTypeQuality]
    flows: list[AdminFlowReconciliation]


class AdminVitalMetric(BaseModel):
    p75: float | None = None
    samples: int


class AdminFirstPlayMetric(BaseModel):
    p75_ms: float | None = None
    samples: int


class AdminPipelineBacklog(BaseModel):
    pending_dispatches: int
    oldest_pending_age_s: int | None = None


class AdminPerformanceMetrics(BaseModel):
    web_vitals: dict[str, AdminVitalMetric]
    first_play: AdminFirstPlayMetric
    pipeline_backlog: AdminPipelineBacklog
    schema_version: int


class AdminLearningMetricsResponse(BaseModel):
    days: int
    definitions: dict[str, str]
    activation: AdminActivationMetrics
    cohorts: list[AdminCohortRow]
    weekly: AdminWeeklyVolume
    event_quality: AdminEventQuality
    performance: AdminPerformanceMetrics
