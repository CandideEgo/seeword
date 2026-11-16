"""首页编辑内容——三张表（草稿 / 不可变版本 / 单例布局）。

契约见 ``backend/app/schemas/home_content.py``；产品边界见
``backend/app/models/home_content.py``。三张表的分工是这个
功能的核心决定，改之前先读那两节：

- :class:`HomeContentDraft` —— 每条视频一份**可编辑**草稿，同时承载「生成任务」
  的状态机（idle/queued/running/succeeded/failed）。生成结果只有在
  generation ID、草稿 revision、来源指纹三者都与入队时一致时才允许写回
  （见 ``services/home_content_service.py::complete_generation``）。
- :class:`HomeContentRevision` —— **只追加**的已发布版本；公共接口只读它。
  重新生成/编辑草稿永远不影响线上，因此内容与位置可以分开管理。
- :class:`HomePageConfig` —— 单例布局，只引用已发布版本的 id（+ 稳定
  expression_id/scenario_id）。draft/published/previous 三份让「整版发布」与
  「恢复上一版」都是原子操作。

**来源指纹**（``source_fingerprint``）覆盖有序字幕 ID + sentence_index +
start/end（3 位小数）+ text_en + text_zh，sha256 十六进制。发布、公共读取、
生成写回都重算比对，所以字幕被改/被重排/被重新转写后，旧引用自动失效——
不依赖逐个字幕写入入口挂钩子。
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class HomeContentGenerationStatus:
    """生成任务状态机的取值（draft.status 列；纯字符串，不走原生 enum）。

    状态流转：``idle → queued → running → succeeded | failed``。结束（成功或
    失败）后 ``active_generation_id`` 必须清空，否则同一视频会永远无法再次
    生成；最近一次任务的身份留在 ``last_generation_id`` 里供后台轮询/展示。
    """

    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

    ACTIVE = (QUEUED, RUNNING)
    TERMINAL = (SUCCEEDED, FAILED)


class HomeContentDraft(Base):
    """每视频一份可编辑草稿 + 生成任务状态（``home_content_drafts``）。"""

    __tablename__ = "home_content_drafts"
    __table_args__ = (Index("uq_home_content_drafts_video_id", "video_id", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # 每视频一份。CASCADE：视频硬删除时草稿随之消失（正常情况下视频走下线而非删行）。
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)

    # ── 内容 ──
    # 经 Pydantic 校验的 HomeContentDraft；草稿允许不完整（null = 从未保存过）。
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # 乐观锁：每次保存/生成写回/复制历史版本都 +1。从未保存过草稿时为 0。
    revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 本 payload 依据的字幕指纹。与当前视频指纹不一致 → 后台显示「来源已变更」。
    source_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # ── 生成任务状态机（同一视频同一时刻只允许一个有效任务） ──
    status: Mapped[str] = mapped_column(String(20), default=HomeContentGenerationStatus.IDLE, nullable=False)
    # 正在跑的任务；非空即「占位」，原子 UPDATE 靠它去重。
    active_generation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    # 最近一次任务（无论成败），任务结束后 active 清空、它保留，供后台展示
    # 失败错误码与成功信息（契约要求 HomeContentVideoState.generation 在任务
    # 结束后仍能显示最近一次结果）。
    last_generation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    generation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generation_finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generation_error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    generation_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 入队时的草稿 revision / 字幕指纹：worker 写回前逐项比对，任一不符即冲突。
    generation_draft_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generation_source_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generation_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # AI 服务返回的真实 usage；服务没返回就是 null（不估算）。
    generation_usage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 实际提交给模型的字幕覆盖范围；旧任务与尚未生成的草稿为 null。
    generation_coverage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 实际 AI 调用次数（分段生成时 >1，可追踪成本）。
    generation_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    generated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    updated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class HomeContentRevision(Base):
    """不可变已发布内容版本（``home_content_revisions``）——只追加，永不原地改。"""

    __tablename__ = "home_content_revisions"
    __table_args__ = (
        UniqueConstraint("video_id", "version", name="uq_home_content_revisions_video_version"),
        Index("ix_home_content_revisions_video_id", "video_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    video_id: Mapped[str] = mapped_column(String(36), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    # 同一视频从 1 递增；发布时取 max+1，与唯一约束一起保证不重号。
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    source_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)

    # 生成信息（来自草稿；手写发布的版本可以全为 null）。
    generation_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_prompt_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    generated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    published_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)


class HomePageConfig(Base):
    """首页单例布局（``home_page_config``），只有一行 id="singleton"。"""

    __tablename__ = "home_page_config"

    id: Mapped[str] = mapped_column(String(16), primary_key=True, default=lambda: "singleton")
    # 三份布局的形状见 schemas.HomeLayoutPlacement；只引用已发布 revision id。
    draft_layout: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    published_layout: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    previous_published_layout: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 布局乐观锁：每次草稿保存/发布/回滚 +1。
    revision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    published_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)

    updated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now, nullable=True
    )
    published_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
