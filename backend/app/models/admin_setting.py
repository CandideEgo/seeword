"""Admin platform settings model — singleton row of admin-console settings.

Backs the admin "系统设置" page (prototype 32-admin-settings):
通用配置 / 质量门禁 / 视频管线. The table holds at most one row with the
fixed primary key ``global``; missing rows fall back to the column defaults.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

#: Fixed primary key of the singleton settings row.
SETTINGS_ROW_ID = "global"


class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=SETTINGS_ROW_ID)

    # --- 通用配置 ---
    site_name: Mapped[str] = mapped_column(String(100), default="SeeWord", nullable=False)
    registration_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- 质量门禁 ---
    quality_block_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    quality_block_threshold: Mapped[float] = mapped_column(
        Numeric(4, 2), default=0.60, nullable=False, comment="覆盖率低于此值 -> quality_blocked"
    )
    quality_warn_threshold: Mapped[float] = mapped_column(
        Numeric(4, 2), default=0.80, nullable=False, comment="覆盖率低于此值 -> quality_warning"
    )
    hallucination_detection_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- 视频管线 ---
    translate_timeout_sec: Mapped[int] = mapped_column(Integer, default=1800, nullable=False)
    download_timeout_sec: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    download_auto_retry_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    watchdog_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
