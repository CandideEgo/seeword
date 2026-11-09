import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VideoStatus(str, enum.Enum):
    pending_processing = "pending_processing"  # waiting for admin to trigger GPU processing
    processing = "processing"
    ready_subtitles = "ready_subtitles"  # subtitles + AI done, video not yet downloaded
    ready = "ready"
    error = "error"


class VideoSource(str, enum.Enum):
    local = "local"
    imported = "imported"


class VideoReviewStatus(str, enum.Enum):
    """UGC review lifecycle for user-uploaded videos.

    - ``draft``: owner is still editing; not visible to the public.
    - ``pending_review``: owner submitted for review; admins see it in the queue.
      While pending, the public keeps watching the last approved version (if any)
      via ``published_snapshot``.
    - ``published``: admin approved; the live subtitles are the public version.
    - ``rejected``: admin rejected; owner can edit & resubmit. The public keeps
      watching the last approved snapshot (if any).

    Official (admin-seeded) videos are always publicly accessible regardless of
    this field (see ``check_video_access``); for them ``review_status`` mirrors
    ``is_published`` for consistency only.
    """

    draft = "draft"
    pending_review = "pending_review"
    published = "published"
    rejected = "rejected"


class Video(Base):
    __tablename__ = "videos"
    __table_args__ = (
        Index("ix_videos_homepage_status", "show_on_homepage", "is_published", "status"),
        # Public feed/ranking visibility triple (is_official, is_published,
        # status): the homepage-first index cannot serve it.
        Index("ix_videos_public", "is_official", "is_published", "status"),
        # Created by an older migration and still useful for source-URL dedup;
        # kept in the model so autogenerate does not see it as removable drift.
        Index("ix_videos_source_url", "source_url"),
        # pg_trgm GIN indexes from migration ``c9d0e1f2a3b4`` (PostgreSQL only);
        # declared so the drift gate sees no new removable-index diff.
        Index("ix_videos_title_trgm", "title", postgresql_using="gin", postgresql_ops={"title": "gin_trgm_ops"}),
        Index(
            "ix_videos_title_zh_trgm",
            "title_zh",
            postgresql_using="gin",
            postgresql_ops={"title_zh": "gin_trgm_ops"},
        ),
        Index(
            "ix_videos_topic_tags_trgm",
            "topic_tags",
            postgresql_using="gin",
            postgresql_ops={"topic_tags": "gin_trgm_ops"},
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    # Chinese display title (translated by the pipeline, editable by admins).
    # Kept separate from ``title`` so the original English title stays the
    # canonical source for search, dedup and standard-version matching.
    title_zh: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    video_source: Mapped[str] = mapped_column(
        SAEnum(VideoSource, name="videosource"), default=VideoSource.local, nullable=False
    )
    thumbnail_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_level: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[VideoStatus] = mapped_column(
        SAEnum(VideoStatus), default=VideoStatus.pending_processing, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    processing_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "lightweight" or "full"
    processing_step: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # CDN URLs
    video_url_480p: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    video_url_720p: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    video_url_1080p: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Metadata
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Public visibility gate — distinct from ``is_official`` (source attribution).
    # Official videos go through draft → review → publish; only published ones
    # appear on the homepage / browse feed / search. See list_public_videos and
    # the browse endpoints for the filtering.
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    # Set by the one-click "seed-full" admin flow: when finalize_video reaches
    # the ready step it auto-publishes (is_published=True) without a manual
    # PATCH. Default false preserves the existing review-then-publish flow.
    auto_publish: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    # Demo/tutorial video (D0): always watchable for Free users without
    # consuming the monthly unlock quota. Admin-toggled via the video manager.
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 内容存储三态（需求 §5.1）:
    #   local   — 本地精品：下载转码自托管，全功能（字幕/词标注/点词/收词）
    #   proxy   — 代理播放：不下载媒体，播放器走外部源；零存储，不可收词
    #              （需求 §5.4 优先级 3「远期/占位」，本期仅保留取值，不实现）
    #   offline — 已下线：从首页/推荐/排行隐藏（同时置 is_published=False，
    #              既有可见性过滤自动生效），媒体文件已删除释放空间；
    #              video 行保留 dormant，学习记录与词表不断链（§5.3）
    # 存字符串而非原生 enum：SQLite（测试）与 Postgres 迁移回填一致。
    storage_mode: Mapped[str] = mapped_column(
        String(10), default="local", server_default="local", nullable=False, index=True
    )

    # ── UGC review lifecycle (user-uploaded videos) ──
    # Stored as a plain string column (not a native enum) so migrations backfill
    # cleanly across SQLite (tests) and Postgres (prod). See VideoReviewStatus.
    review_status: Mapped[str] = mapped_column(
        String(20), default=VideoReviewStatus.draft.value, server_default="draft", nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Frozen copy of the last admin-approved subtitles (+ practice, added in 2B)
    # shown to the public while the owner edits a pending/rejected version. Null
    # until the video is first approved. Shape: {"subtitles": [...], "version": 1}.
    published_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    topic_tags: Mapped[str | None] = mapped_column(String(500), nullable=True)
    quiz_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processing_progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100 percentage

    # Comment-analysis denormalised fields (written by comment_service.analyze).
    # comment_count exists in the initial migration; comment_quality_score was
    # referenced by code but missing from the schema — added here + a migration.
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Denormalized social counts
    like_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    # Play-completion counter (distinct from like_count) — populated by
    # behavior_service on `complete` events. Used by scoring/recommendation (P1/P2).
    view_count: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0", nullable=False)

    # P1 learning_score (0-100) — denormalized current total for cheap list
    # sorting. Computed by scoring_service.compute_video_score (7-factor
    # weighted + bonus, 阶段 2 added viral/freshness) and refreshed by the
    # scoring beat tasks. Null until first computed (sorts last via
    # score.is_(None)). Full per-factor breakdown lives in video_scores rows.
    score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    score_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Admin-curated homepage visibility (distinct from is_featured which is auto-set)
    show_on_homepage: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # First-publish timestamp — set once by video_publish._publish_video (never
    # overwritten on later re-reviews). Pre-existing rows are backfilled as
    # COALESCE(reviewed_at, created_at) by the g2h3i4j5k6l7 migration. Sort key
    # for the homepage 「最新」 ranking (NULLs last). See app.services.ranking_service.
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # When processing actually started (set by start_processing or seed_video).
    # Used by the watchdog to detect stale transcriptions — more accurate than
    # created_at because admin may delay triggering start_processing.
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # When the *current* processing step started. Refreshed at each step boundary
    # (extracting/transcribing/translating/annotating/prewarm_notes/classifying/
    # downloading/transcoding) so the watchdog can detect a single stuck step
    # rather than measuring the whole pipeline from processing_started_at (which
    # would force an over-wide timeout and detect failures slowly). Cleared on
    # ready/error. See watchdog_stale_pipeline.
    step_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Translation quality flag set by finalize_video after the translation
    # quality gate. None = passed (>= warn threshold); "quality_warning" =
    # coverage between block and warn thresholds (video still goes ready, admin
    # sees a warning in the list); "quality_blocked" = below block threshold
    # (video marked error, admin re-translates - optionally with a different
    # engine via POST /admin/{id}/retranslate). See finalize_video.
    quality_flag: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Local-media retry tracking (legacy download_* names). Records download
    # or conversion failure so beat can re-attempt a supported embed video's
    # localization later. After ``download_fail_count``
    # reaches the max the beat task stops retrying (permanent failure - region
    # block / video removed); admin can still force via localize with force=True.
    download_failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    download_fail_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    # ── External (YouTube) metadata (阶段 1: 视频特征采集) ──
    # Captured by _extract_video_info at the pipeline's extracting step (and
    # backfilled by scripts/backfill_external_meta.py). Strictly separated from
    # the in-app counters above: ``ext_view_count`` is the YouTube view count,
    # ``view_count`` stays the in-app completion counter.
    yt_video_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # In-site curated channel (ADR-0014) — orthogonal to the scraped channel_id
    # above. SET NULL on delete so videos survive their channel being removed.
    channel_ref: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("channels.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # YouTube publication date (freshness signal for viral/views-per-day metrics).
    upload_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ext_view_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ext_like_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Non-queried extras: description, tags, categories, language, caption track
    # summary (has_caption/auto_generated/manual counts), channel stats
    # (channel_follower_count when available), fetched_at.
    external_meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    @property
    def description(self) -> str | None:
        """YouTube-side video description from ``external_meta``; None for
        local videos / before extraction / when the field is blank. List
        serializers truncate it (CARD_DESCRIPTION_LIMIT) to keep feeds small."""
        desc = (self.external_meta or {}).get("description")
        if isinstance(desc, str) and desc.strip():
            return desc.strip()
        return None

    # ── Subtitle-derived speech metrics (阶段 3, compute-on-null) ──
    # Written by subtitle_metrics_service at finalize tail; never overwritten.
    wpm: Mapped[float | None] = mapped_column(Float, nullable=True)  # words per minute
    vocabulary_density: Mapped[float | None] = mapped_column(Float, nullable=True)  # unique/total tokens

    # Fork lineage (扩展 A4): points to the source Video this was forked from
    # (a standard version or another fork). Null for original submissions.
    # Indexed for "find all forks of X" queries; SET NULL on delete so forks
    # survive their source being deleted.
    forked_from: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # relationships
    # foreign_keys disambiguates the two users FKs (user_id ownership vs
    # reviewed_by reviewer); this relationship tracks the owner.
    user = relationship("User", foreign_keys=[user_id], back_populates="videos")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    subtitles = relationship("Subtitle", back_populates="video", order_by="Subtitle.sentence_index")
    learning_records = relationship("LearningRecord", back_populates="video")
    favorites = relationship("UserFavorite", back_populates="video", cascade="all, delete-orphan")
    notes = relationship("UserNote", back_populates="video", cascade="all, delete-orphan")
    likes = relationship("VideoLike", back_populates="video", cascade="all, delete-orphan")
