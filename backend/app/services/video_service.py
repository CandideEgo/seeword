"""Business logic for video operations.

Route handlers in api/v1/videos.py delegate to these functions
so HTTP concerns (parsing, status codes) stay separate from
domain logic (queries, state transitions, side effects).
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import commit_refresh
from app.core.errors import BadRequestError, ConflictError, NotFoundError
from app.models.learning import LearningRecord
from app.models.user import User
from app.models.video import Video, VideoReviewStatus, VideoStatus
from app.schemas.pagination import PaginatedResponse, paginated
from app.schemas.video import (
    SubtitleResponse,
    VideoAdminResponse,
    VideoAdminUpdate,
    VideoDetailResponse,
    VideoResponse,
    VideoStatusResponse,
)
from app.services.video_access import (
    check_video_access,
    is_video_owner,
    should_use_snapshot,
)
from app.services.video_card import serialize_video_card
from app.services.video_title import normalize_title_zh


async def count_subtitles(db: AsyncSession, video_id: str) -> int:
    """Count persisted subtitle rows for a video.

    Used by the pipeline resume logic (``retry_video`` and the ``process_video``
    head) to decide whether transcription can be skipped. Subtitles in the DB
    are the ground-truth signal that the GPU stage already succeeded, since
    the transcription callback only inserts them on ``status == "ok"``.
    """
    from app.models.subtitle import Subtitle

    result = await db.scalar(select(func.count()).select_from(Subtitle).where(Subtitle.video_id == video_id))
    return result or 0


async def list_public_videos(db: AsyncSession, page: int = 1, page_size: int = 20) -> dict:
    """List official public videos for the homepage. Paginated."""
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size

    base = select(Video).where(
        Video.is_official == True,
        Video.is_published == True,
        Video.status.in_([VideoStatus.ready, VideoStatus.ready_subtitles]),
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

    # Sort by score desc (nulls last) with is_featured as a fallback tiebreaker
    # — featured curates the top until scores accumulate, then score dominates.
    result = await db.execute(
        base.order_by(
            Video.score.is_(None),
            Video.score.desc(),
            Video.is_featured.desc(),
            Video.created_at.desc(),
        )
        .offset(offset)
        .limit(page_size + 1)
    )
    rows = result.scalars().all()
    has_more = len(rows) > page_size
    items = [VideoResponse.model_validate(v) for v in rows[:page_size]]
    return paginated(items, page=page, page_size=page_size, has_more=has_more, total=total)


async def _invalidate_video_detail_cache(video_id: str) -> None:
    """Backward-compat wrapper — delegates to shared video_cache module.

    Retained for any external callers importing the private name; new code
    should import invalidate_video_detail_cache from app.services.video_cache.
    """
    from app.services.video_cache import invalidate_video_detail_cache

    await invalidate_video_detail_cache(video_id)


async def _ensure_learning_record(db: AsyncSession, user_id: str, video_id: str) -> None:
    """Create the first-view ``LearningRecord`` if it is absent, atomically.

    Replaces the previous ``SELECT … FOR UPDATE`` probe. That probe took a row
    lock on **every** watch-page load for an authenticated viewer, only to
    discover that the record usually already existed. The unique constraint
    ``uq_learning_record_user_video`` is the real arbiter, so a conditional
    ``INSERT … ON CONFLICT DO NOTHING`` answers the same question in one
    statement and never blocks a concurrent reader.

    Only an actual insert is committed — a no-op leaves the surrounding
    transaction untouched, exactly like the old "record exists" path.

    Every column is supplied explicitly: the model's defaults are Python-side
    (``default=``), not ``server_default``, so a Core insert would otherwise
    write NULL into the NOT NULL columns.
    """
    values = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "video_id": video_id,
        "words_learned": 0,
        "speaking_attempts": 0,
        "completed": False,
        "time_spent_seconds": 0,
        "progress_percentage": 0.0,
        "created_at": datetime.now(UTC),
    }
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    stmt = (
        insert(LearningRecord)
        .values(**values)
        .on_conflict_do_nothing(index_elements=["user_id", "video_id"])
        .returning(LearningRecord.id)
    )
    inserted = (await db.execute(stmt)).first()
    if inserted is not None:
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise


async def get_video_detail(
    db: AsyncSession,
    video_id: str,
    current_user: User | None,
    *,
    skip_access_check: bool = False,
) -> VideoDetailResponse:
    """Get video detail with subtitles. Creates a LearningRecord on first view.

    When *skip_access_check* is True the ``check_video_access`` gate is
    bypassed (used by the admin detail endpoint so admins can view UGC
    drafts they don't own).

    D0 membership gate: Free viewers who have not unlocked the video get the
    metadata (cover/title/difficulty) but empty subtitles and no media URLs —
    the watch page renders the unlock panel from the ``access`` field.
    """
    from app.core.cache import cache_get, cache_set
    from app.services.unlock_service import get_video_access_info

    # Metadata only — the subtitle rows are the payload's largest part and are
    # loaded below, *after* the cache lookup, so a detail-cache hit never pays
    # for reading them. This used to be a selectinload on this very query, which
    # made the Redis cache save only serialization, not the DB work.
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        return None

    # Access control: official videos are public; user-owned require auth.
    # Admin endpoints set skip_access_check=True so admins can view any video.
    if not skip_access_check and not check_video_access(video, current_user):
        return None

    # Membership gate (D0): admins (skip path) and Pro see everything; Free
    # viewers need an unlock (demo videos are always open).
    if skip_access_check:
        from app.core.config import get_settings

        access = {"unlocked": True, "remaining_this_month": None, "quota": get_settings().free_monthly_unlock_quota}
    else:
        access = await get_video_access_info(db, current_user, video)
    can_watch = bool(access["unlocked"])
    # 已下线（需求 §5.1 offline）：不再可播。字幕/词标注仍下发（学习记录不断链，
    # 收藏夹与集合页「回看原视频」落到一个显示「已下架」的 watch 页）。
    is_offline = video.storage_mode == "offline"
    playable = can_watch and not is_offline

    # Create LearningRecord on first view for authenticated viewers — only
    # once they can actually watch (locked panel views don't count). Runs
    # before the cache lookup: a cached payload must not skip view-history.
    if current_user and can_watch:
        await _ensure_learning_record(db, current_user.id, video_id)

    # 内测免费期：登录用户即放行（见 unlock_service.get_video_access_info）。
    # access 不再含 per-user 额度，故登录用户的响应可共用 key；但**匿名**响应
    # 是 locked 形状（空字幕/空 URL），绝不能缓存后回给登录用户，因此只有
    # can_watch 的响应才读写缓存。
    #
    # 安全前提显式化：缓存 payload 不含任何 viewer 相关字段。免费额度恢复后
    # `remaining_this_month` 会变成 per-user；那时不能再走共享 key（否则跨用户
    # 泄漏），下面的谓词会让这条详情直接不缓存，而不是悄悄复用旧缓存。
    viewer_independent = access.get("remaining_this_month") is None
    cache_key = f"video:detail:{video_id}"
    cacheable = can_watch and viewer_independent
    if cacheable:
        cached = await cache_get(cache_key)
        if cached:
            detail = VideoDetailResponse.model_validate_json(cached)
            # Subtitle caching must never freeze changing engagement counters.
            detail.like_count = video.like_count
            detail.favorite_count = video.favorite_count
            detail.view_count = video.view_count
            detail.upload_date = video.upload_date.isoformat() if video.upload_date else None
            detail.published_at = video.published_at.isoformat() if video.published_at else None
            return detail

    # Decide which subtitles the viewer sees. The owner always sees their live
    # (draft) subtitles. A non-owner viewing a UGC video under re-review
    # (pending/rejected) sees the frozen approved snapshot instead of the live
    # draft the owner is editing.
    use_snapshot = should_use_snapshot(video, current_user)

    if not can_watch:
        subtitle_responses: list[SubtitleResponse] = []
    elif use_snapshot:
        from app.services.video_publish import subtitles_from_snapshot

        subtitle_responses = subtitles_from_snapshot(video.published_snapshot)
    else:
        from app.models.subtitle import Subtitle

        subtitle_rows = (
            (await db.execute(select(Subtitle).where(Subtitle.video_id == video.id).order_by(Subtitle.sentence_index)))
            .scalars()
            .all()
        )
        subtitle_responses = [
            SubtitleResponse(
                id=s.id,
                start_time=s.start_time,
                end_time=s.end_time,
                text_en=s.text_en,
                text_zh=s.text_zh,
                sentence_index=s.sentence_index,
                grammar_note=s.grammar_note,
                speaker=s.speaker,
                word_levels=s.word_levels,
            )
            for s in subtitle_rows
        ]

    # Author page link (ADR-0014 rev.): channel slug + cover for the watch page.
    channel_slug = None
    channel_cover_url = None
    if video.channel_ref:
        from app.models.channel import Channel

        row = (
            await db.execute(select(Channel.slug, Channel.cover_url).where(Channel.id == video.channel_ref))
        ).one_or_none()
        if row:
            channel_slug, channel_cover_url = row

    detail = VideoDetailResponse(
        id=video.id,
        title=video.title,
        source_url=video.source_url,
        video_source=video.video_source.value,
        thumbnail_url=video.thumbnail_url,
        duration=video.duration,
        difficulty_level=video.difficulty_level,
        status=video.status.value,
        topic_tags=video.topic_tags,
        is_official=video.is_official,
        is_published=video.is_published,
        storage_mode=video.storage_mode,
        review_status=video.review_status,
        # Only the owner sees the rejection reason; a public/snapshot viewer
        # never learns why an unpublished draft was rejected.
        # Cached responses (anonymous/free) must never include it.
        rejection_reason=video.rejection_reason if is_video_owner(video, current_user) else None,
        # 播放 URL：锁定（匿名）或已下线时不下发。已下线的视频媒体文件已被
        # 删除，此处留空让前端渲染「已下架」态而不是一个必然 404 的播放器。
        video_url_480p=video.video_url_480p if playable else None,
        video_url_720p=video.video_url_720p if playable else None,
        video_url_1080p=video.video_url_1080p if playable else None,
        like_count=video.like_count,
        favorite_count=video.favorite_count,
        view_count=video.view_count,
        upload_date=video.upload_date.isoformat() if video.upload_date else None,
        published_at=video.published_at.isoformat() if video.published_at else None,
        # 详情页保留完整简介（列表卡片才截断到 CARD_DESCRIPTION_LIMIT）。
        description=video.description,
        processing_mode=video.processing_mode,
        processing_progress=video.processing_progress or 0,
        # Only the owner sees the error message; non-owners get null.
        error_message=video.error_message if is_video_owner(video, current_user) else None,
        created_at=video.created_at.isoformat(),
        channel_name=video.channel_name,
        channel_slug=channel_slug,
        channel_cover_url=channel_cover_url,
        subtitles=subtitle_responses,
        access=access,
    )

    # Cache official video details for 5 minutes.
    # Only cache if owner-only fields are None to prevent leaking them
    # to anonymous/free users via the shared cache.
    if cacheable and video.is_official and detail.rejection_reason is None and detail.error_message is None:
        await cache_set(cache_key, detail.model_dump_json(), ttl=300)

    return detail


async def get_video_status(
    db: AsyncSession,
    video_id: str,
    current_user: User | None,
    *,
    skip_access_check: bool = False,
) -> VideoStatusResponse | None:
    """Get processing status for a video. Returns None if not found / no access.

    When *skip_access_check* is True the ``check_video_access`` gate is
    bypassed (used by the admin status endpoint).
    """
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if not video:
        return None
    if not skip_access_check and not check_video_access(video, current_user):
        return None
    subtitle_count = await count_subtitles(db, video_id)
    # error_message can name internal pipeline paths/failures — owner (or the
    # admin status path) only, same rule as get_video_detail.
    can_see_error = skip_access_check or is_video_owner(video, current_user)
    return VideoStatusResponse(
        status=video.status.value,
        video_url_720p=video.video_url_720p,
        processing_step=video.processing_step,
        processing_progress=video.processing_progress,
        error_message=video.error_message if can_see_error else None,
        subtitle_count=subtitle_count,
    )


# ---------------------------------------------------------------------------
# Admin video content management
# ---------------------------------------------------------------------------


async def list_all_videos(
    db: AsyncSession,
    *,
    status: str | None = None,
    is_official: bool | None = None,
    is_featured: bool | None = None,
    review_status: str | None = None,
    keyword: str | None = None,
    quality: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[VideoAdminResponse]:
    """List every video (admin view) with filters.

    Unlike the public list, this returns videos in any status (including
    ``processing``/``error``). Keyword search uses ILIKE on title/topic_tags so
    it works on SQLite (tests) and Postgres alike — the public search path's
    PostgreSQL ``tsvector`` expression is not used here. ``review_status``
    filters the UGC review queue (e.g. ``pending_review``).
    """
    stmt = select(Video)
    if status:
        try:
            status_enum = VideoStatus(status)
        except ValueError:
            status_enum = None
        if status_enum is not None:
            stmt = stmt.where(Video.status == status_enum)
    if is_official is not None:
        stmt = stmt.where(Video.is_official == is_official)
    if is_featured is not None:
        stmt = stmt.where(Video.is_featured == is_featured)
    if review_status:
        stmt = stmt.where(Video.review_status == review_status)
    if keyword and keyword.strip():
        escaped_kw = keyword.strip().replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped_kw}%"
        stmt = stmt.where(or_(Video.title.ilike(pattern, escape="\\"), Video.topic_tags.ilike(pattern, escape="\\")))
    # 阶段 5: quality filter. quality_warning/quality_blocked read the denormalized
    # flag directly; low_coverage joins video_quality_reports for any translation
    # report under 90% (catches videos that passed the block but are still thin).
    if quality == "quality_warning":
        stmt = stmt.where(Video.quality_flag == "quality_warning")
    elif quality == "quality_blocked":
        stmt = stmt.where(Video.quality_flag == "quality_blocked")
    elif quality == "low_coverage":
        from app.models.video_quality_report import VideoQualityReport

        sub = select(VideoQualityReport.video_id).where(
            VideoQualityReport.stage == "translation",
            VideoQualityReport.coverage_ratio < 0.9,
        )
        stmt = stmt.where(Video.id.in_(sub))

    # total count for the paginated envelope's `total` (the admin table's
    # "共 N 条" and the has_more flag both come from it; ADM-10).
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # id tiebreaker: OFFSET paging over created_at alone can repeat/skip rows
    # when bulk-imported videos share a timestamp (ADM-10/15).
    stmt = stmt.order_by(Video.created_at.desc(), Video.id.desc()).limit(page_size).offset((page - 1) * page_size)
    rows = (await db.execute(stmt)).scalars().all()

    has_more = total > page * page_size
    items = [VideoAdminResponse.model_validate(v) for v in rows]
    return PaginatedResponse(items=items, page=page, page_size=page_size, has_more=has_more, total=total)


async def get_ugc_pending_counts(db: AsyncSession) -> dict:
    """Count UGC (non-official) videos awaiting admin action.

    Returns ``{pending_processing, pending_review, total}`` for the admin
    top-bar badge. ``pending_processing`` = waiting for admin to start GPU
    processing; ``pending_review`` = processed, waiting for admin approval.
    Both counts are scoped to user-submitted (``is_official=False``) videos.
    """
    pending_processing = (
        await db.execute(
            select(func.count()).where(
                Video.is_official == False,
                Video.status == VideoStatus.pending_processing,
            )
        )
    ).scalar_one()
    pending_review = (
        await db.execute(
            select(func.count()).where(
                Video.is_official == False,
                Video.review_status == VideoReviewStatus.pending_review.value,
            )
        )
    ).scalar_one()
    return {
        "pending_processing": pending_processing,
        "pending_review": pending_review,
        "total": pending_processing + pending_review,
    }


async def _get_video_or_404(db: AsyncSession, video_id: str) -> Video:
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    if video is None:
        raise NotFoundError("Video not found")
    return video


# Arbitrary stable int used as the Postgres transaction-scoped advisory lock key
# for the "exactly one is_demo video" grant. Must never change while rows exist.
_DEMO_ADVISORY_LOCK_KEY = 0x5EE0D3E3


async def _serialize_demo_grant(db: AsyncSession) -> None:
    """Serialize ``is_demo=True`` grants across concurrent admins (ADM-14).

    The single-demo invariant is enforced in application code, not by a DB
    constraint: two admins flipping different videos at the same time can both
    run "clear the previous holder" and both commit, leaving two demo rows.
    A row lock cannot guard "at most one row carries this flag", so on Postgres
    we take a transaction-scoped advisory lock — released by the same commit
    that writes the flag, so the second grant then sees the first one's row and
    clears it. SQLite (tests/local) serializes writers itself; no-op there.
    """
    bind = db.get_bind()
    if bind is None or bind.dialect.name != "postgresql":
        return
    await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": _DEMO_ADVISORY_LOCK_KEY})


async def update_video(
    db: AsyncSession,
    video_id: str,
    payload: VideoAdminUpdate,
) -> VideoAdminResponse:
    """Apply a partial admin update to a video (None fields are skipped)."""
    video = await _get_video_or_404(db, video_id)

    # Exactly one demo/first-lesson video is allowed globally. Flipping a
    # video on clears the previous holder in the same transaction; the advisory
    # lock serializes two concurrent grants so they cannot both leave a demo
    # row behind (ADM-14).
    demo_cleared = False
    if payload.is_demo is True and not video.is_demo:
        await _serialize_demo_grant(db)
        result = await db.execute(
            update(Video).where(Video.is_demo.is_(True), Video.id != video_id).values(is_demo=False)
        )
        demo_cleared = bool(result.rowcount)

    # Publish guard: only ready videos may be published.
    if payload.is_published is True and video.status != VideoStatus.ready:
        raise BadRequestError("只能发布 status=ready 的视频")

    publish_changed = payload.is_published is not None and payload.is_published != video.is_published
    # "" clears the assignment, so both sides normalize through `or None`.
    channel_changed = payload.channel_ref is not None and (payload.channel_ref or None) != video.channel_ref
    title_changed = payload.title is not None and payload.title != video.title
    next_title_zh = normalize_title_zh(payload.title_zh) if payload.title_zh is not None else None
    title_zh_changed = payload.title_zh is not None and next_title_zh != video.title_zh

    for field in (
        "title",
        "difficulty_level",
        "topic_tags",
        "is_official",
        "is_featured",
        "is_published",
        "show_on_homepage",
        "is_demo",
        "admin_notes",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(video, field, value)

    # Empty string clears a bad translation; the next pipeline run can refill it.
    if payload.title_zh is not None:
        video.title_zh = next_title_zh

    # ADR-0014 channel assignment — "" explicitly clears (the generic loop
    # skips None, so clearing needs its own branch).
    if payload.channel_ref is not None:
        video.channel_ref = payload.channel_ref or None

    # Keep review_status in sync with the admin publish toggle so the two
    # visibility gates never diverge (official videos are managed here; UGC
    # videos are managed via the dedicated approve/reject endpoints).
    if publish_changed:
        if video.is_published:
            video.review_status = VideoReviewStatus.published.value
        else:
            video.review_status = VideoReviewStatus.draft.value

    await commit_refresh(db, video)

    # Best-effort cache invalidation so the next read reflects new metadata.
    try:
        from app.core.redis import get_redis

        redis = await get_redis()
        await redis.delete(f"video:detail:{video_id}")
    except Exception:
        pass

    if demo_cleared:
        from app.services.video_cache import invalidate_browse_cache

        await invalidate_browse_cache()

    # Publish/unpublish changes which videos surface on the homepage/browse feed,
    # a channel_ref change rewrites the author link (`channel_slug`) embedded in
    # every cached browse card, and title/title_zh changes rewrite the cached
    # card text itself. (Subtitle edits don't need this; browse only caches video
    # metadata.) The detail cache above is dropped separately because it is
    # keyed per video.
    if publish_changed or channel_changed or title_changed or title_zh_changed:
        from app.services.video_cache import invalidate_browse_cache

        await invalidate_browse_cache()

    return VideoAdminResponse.model_validate(video)


async def get_demo_video(db: AsyncSession) -> VideoResponse:
    """Return the single first-lesson/demo video, or raise if none is marked.

    ``update_video`` guarantees at most one ``is_demo=True`` row globally;
    ordering by ``created_at`` keeps the response stable if that guarantee is
    ever temporarily violated by a direct DB edit.
    """
    result = await db.execute(select(Video).where(Video.is_demo.is_(True)).order_by(Video.created_at.desc()).limit(1))
    video = result.scalar_one_or_none()
    if video is None:
        # 用户可见文案（登录后的新用户流程会读它）；不是内部日志文本。
        raise NotFoundError("暂未配置第一课视频")
    return VideoResponse.model_validate(video)


async def delete_video(db: AsyncSession, video_id: str) -> bool:
    """Delete a video and all of its dependents + on-disk media files.

    Most FKs to ``videos.id`` have no DB-level ``ondelete`` clause, so we
    delete the child rows explicitly. Comments/comment_stats rely on their
    existing ``cascade="all, delete-orphan"`` / ``ondelete=CASCADE`` and are
    cleaned up via the ORM relationship cascade when the video row goes.
    """
    video = await _get_video_or_404(db, video_id)

    # Explicit child-row cleanup for tables lacking ondelete CASCADE.
    from app.models.learning import Vocabulary
    from app.models.subtitle import Subtitle

    await db.execute(delete(Subtitle).where(Subtitle.video_id == video_id))
    await db.execute(delete(LearningRecord).where(LearningRecord.video_id == video_id))
    await db.execute(delete(Vocabulary).where(Vocabulary.video_id == video_id))

    # Remove the video row (comments/comment_stats cascade via ORM).
    await db.delete(video)
    await db.commit()

    # Best-effort deletion of on-disk media files.
    _delete_media_files(video_id)

    # Best-effort cache invalidation.
    try:
        from app.core.redis import get_redis

        redis = await get_redis()
        await redis.delete(f"video:detail:{video_id}")
    except Exception:
        pass

    return True


def _delete_media_files(video_id: str) -> None:
    """Remove raw + transcoded media files for a video from local storage.

    Covers every variant the pipeline can produce, including the bare
    ``{video_id}.mp4`` 720p fallback. Thumbnails are intentionally kept: they
    are tiny, and the favorites list still renders a card for a taken-down
    video (需求 §5.3「收藏夹保留入口并标注已下架」).
    """
    try:
        from app.core.config import get_settings

        media_dir = Path(get_settings().local_media_path).resolve()  # type: ignore[name-defined]
    except Exception:
        return
    if not media_dir.exists():
        return
    import glob

    for pattern in (
        f"{video_id}.mp4",
        f"{video_id}_raw.*",
        f"{video_id}_480p.mp4",
        f"{video_id}_720p.mp4",
        f"{video_id}_1080p.mp4",
    ):
        for path in glob.glob(str(media_dir / pattern)):
            try:
                Path(path).unlink()
            except Exception:
                pass


# ── 内容三态：下线（需求 §5.3） ────────────────────────────────────────────
STORAGE_OFFLINE = "offline"


async def takedown_video(db: AsyncSession, video_id: str) -> VideoAdminResponse:
    """下线一个视频：隐藏 + 删本地媒体，保留 video 行与学习记录（§5.3）。

    幂等。动作：
      1. ``is_published=False`` —— 复用既有可见性过滤，feed/browse/推荐/搜索/
         频道/排行一次性全部隐藏，无需逐个改查询
      2. ``storage_mode='offline'`` —— 供媒体门控与前端「已下架」态判定
      3. 清空 ``video_url_*`` + 删除本地媒体文件（缩略图保留，收藏夹仍要渲染）
    字幕、word_levels、Vocabulary、VocabSetWord 与 LearningRecord 全部保留，
    收藏夹入口不断链，集合页「回看原视频」落到一个已下架的 watch 页。
    """
    video = await _get_video_or_404(db, video_id)

    was_offline = video.storage_mode == STORAGE_OFFLINE
    video.storage_mode = STORAGE_OFFLINE
    video.is_published = False
    video.video_url_480p = None
    video.video_url_720p = None
    video.video_url_1080p = None
    await commit_refresh(db, video)

    if not was_offline:
        _delete_media_files(video_id)

    await _invalidate_video_detail_cache(video_id)
    from app.services.video_cache import invalidate_browse_cache

    await invalidate_browse_cache()
    return VideoAdminResponse.model_validate(video)


async def takedown_suggestions(db: AsyncSession, *, limit: int = 20) -> list[VideoResponse]:
    """半自动下线的「建议下线」候选（需求 §5.3：阈值建议 + 管理员确认）。

    规则（全部由 config 控制）：已发布、上线超过 ``takedown_min_age_days``
    天、且 ``view_count`` / ``favorite_count`` 均低于阈值 —— 即冷启动期没有
    产生学习价值的视频。按热度升序（最冷门的排最前），仅建议，不自动执行。

    卡片来自共享 projector（services/video_card）—— 这是第四个、也是最后一个
    手写卡片 dict 的位置。管理员表格只读其中几列，但「建议下线」这一行的形状
    没有理由跟别的卡片长得不一样。
    """
    from datetime import timedelta

    from app.core.config import get_settings

    settings = get_settings()
    cutoff = datetime.now(UTC) - timedelta(days=settings.takedown_min_age_days)

    rows = (
        (
            await db.execute(
                select(Video)
                .where(
                    Video.is_published.is_(True),
                    Video.storage_mode != STORAGE_OFFLINE,
                    Video.created_at <= cutoff,
                    Video.view_count < settings.takedown_min_views,
                    Video.favorite_count < settings.takedown_min_favorites,
                    or_(Video.published_at.is_(None), Video.published_at <= cutoff),
                )
                .order_by(Video.view_count.asc(), Video.favorite_count.asc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return [serialize_video_card(v, scope="feed") for v in rows]


# Single source of truth: import from pipeline_helpers instead of
# maintaining a separate constant that can drift out of sync.
from app.tasks.pipeline_helpers import STEP_PROGRESS as _STEP_PROGRESS

STEP_PROGRESS_DOWNLOADING = _STEP_PROGRESS["downloading"]


async def localize_video_admin(db: AsyncSession, video_id: str) -> VideoAdminResponse:
    """Kick off local download+transcode for an imported video (admin).

    Clears any existing local URLs and flips the video to ``processing`` so
    the admin panel can poll progress. Raises ``Conflict`` (409) if the video
    is already being processed.

    The ``processing`` gate is a conditional UPDATE checked by ``rowcount``, not
    a ``read status -> if`` in Python: two concurrent clicks both pass the
    Python check, and both would dispatch ``localize_video`` (double transcode
    onto the same output files). Only the request whose UPDATE actually flipped
    the row dispatches (ADM-14).
    """
    result = await db.execute(
        update(Video)
        .where(Video.id == video_id, Video.status != VideoStatus.processing)
        .values(
            video_url_480p=None,
            video_url_720p=None,
            video_url_1080p=None,
            error_message=None,
            processing_step="downloading",
            processing_progress=STEP_PROGRESS_DOWNLOADING,
            status=VideoStatus.processing,
        )
        .execution_options(synchronize_session=False)
    )
    if not result.rowcount:
        # No row matched: either the video doesn't exist, or another request
        # already moved it to ``processing``. Roll back before probing so the
        # caller's session stays usable.
        await db.rollback()
        if await db.get(Video, video_id) is None:
            raise NotFoundError("Video not found")
        raise ConflictError("Video is already processing")

    await db.commit()
    video = await _get_video_or_404(db, video_id)

    from app.tasks.video_processing import localize_video

    localize_video.delay(video.id, force=True)
    return VideoAdminResponse.model_validate(video)
