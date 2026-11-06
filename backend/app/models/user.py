import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RoleType(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # Partial unique index: allow multiple NULLs while still enforcing
        # uniqueness among non-NULL phone values.
        Index(
            "uq_users_phone_partial",
            "phone",
            unique=True,
            postgresql_where=text("phone IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[str | None] = mapped_column(String(10), nullable=True)  # A1-C2
    role: Mapped[RoleType] = mapped_column(SAEnum(RoleType, name="roletype"), default=RoleType.user, nullable=False)
    # Timestamp of the last password change/reset. Tokens issued before this
    # moment are rejected by the auth dependency, effectively invalidating all
    # active sessions when a user changes or resets their password.
    password_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    native_language: Mapped[str] = mapped_column(String(10), default="zh")
    avatar_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # The user's own gender: "male" | "female", NULL = not filled in. It decides
    # which built-in default illustration is shown when there is no upload; while
    # it is NULL the client falls back to a seed-derived provisional face. See
    # DEC-048.
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(300), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 30 天可撤回注销（P1-7）：申请时间与到期时间成对出现；撤销时一起清空。
    # 冷静期内**允许登录**，登录不会自动取消 —— 只有显式撤销才清字段。
    deletion_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deletion_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 用户填写的注销原因，可选；删除完成后随用户行一起消失。
    deletion_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # relationships
    # foreign_keys is required because videos has TWO FKs to users (user_id +
    # reviewed_by); this relationship tracks ownership via user_id.
    videos = relationship("Video", foreign_keys="Video.user_id", back_populates="user")
    learning_records = relationship("LearningRecord", back_populates="user")
    vocabulary = relationship("Vocabulary", back_populates="user")
    notifications = relationship("Notification", back_populates="user", order_by="Notification.created_at.desc()")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("UserNote", back_populates="user", cascade="all, delete-orphan")
    learning_profile = relationship("UserLearningProfile", back_populates="user", uselist=False)
    learning_events = relationship("LearningEvent", back_populates="user", cascade="all, delete-orphan")

    @property
    def has_password(self) -> bool:
        """Whether a login password has been set (phone-only accounts don't).

        Additive read-only field for the API contract: the set-password page
        uses it to tell "first setup" (no current password needed) from
        "change password" (current password required) before the user types
        anything and hits a 400.
        """
        return bool(self.hashed_password)
