"""Video route handlers — thin HTTP layer only.

All business logic lives in app.services.video_service.
These handlers parse requests, call the service, and return responses.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_admin_user, get_current_user, get_optional_user
from app.core.database import get_db
from app.core.errors import UnprocessableEntityError
from app.core.limiter import rate_limit
from app.models.user import User
from app.models.video import Video
from app.schemas.pagination import PaginatedResponse, PaginationParams, paginated
from app.schemas.video import (
    HotSearchesResponse,
    PendingCountsResponse,
    QualityReportItem,
    RecomputeWordLevelsRequest,
    RecomputeWordLevelsResponse,
    ResegmentResult,
    ResegmentRollbackResult,
    ReviewRejectRequest,
    SearchSuggestionsResponse,
    SubtitleBatchUpdate,
    SubtitleCreate,
    SubtitleDeleteResult,
    SubtitleReorder,
    SubtitleResponse,
    SubtitleRevisionItem,
    SubtitleSearchResult,
    SubtitleSplit,
    SubtitleUpdate,
    TakedownSuggestionsResponse,
    VideoAdminResponse,
    VideoAdminStatusResponse,
    VideoAdminUpdate,
    VideoCreate,
    VideoDetailResponse,
    VideoLikeStatusResponse,
    VideoLikeToggleResponse,
    VideoResponse,
    VideoScoreResponse,
    VideoStatusResponse,
    VideoVocabularyItem,
    WordLevelsUpdate,
)
from app.services.search_service import (
    get_hot_searches as _get_hot_searches,
)
from app.services.search_service import (
    record_search_query as _record_search_query,
)
from app.services.search_service import (
    search_subtitles as _search_subtitles,
)
from app.services.search_service import (
    search_videos as _search_videos,
)
from app.services.search_service import (
    suggest_titles as _suggest_titles,
)
from app.services.subtitle_edit_service import (
    create_subtitle as _create_subtitle,
)
from app.services.subtitle_edit_service import (
    delete_subtitle as _delete_subtitle,
)
from app.services.subtitle_edit_service import (
    list_subtitle_revisions as _list_subtitle_revisions,
)
from app.services.subtitle_edit_service import (
    merge_subtitle as _merge_subtitle,
)
from app.services.subtitle_edit_service import (
    recompute_word_levels as _recompute_word_levels,
)
from app.services.subtitle_edit_service import (
    reorder_subtitles as _reorder_subtitles,
)
from app.services.subtitle_edit_service import (
    resegment_video as _resegment_video,
)
from app.services.subtitle_edit_service import (
    rollback_resegment as _rollback_resegment,
)
from app.services.subtitle_edit_service import (
    rollback_subtitle as _rollback_subtitle,
)
from app.services.subtitle_edit_service import (
    split_subtitle as _split_subtitle,
)
from app.services.subtitle_edit_service import (
    update_subtitle as _update_subtitle,
)
from app.services.subtitle_edit_service import (
    update_subtitles_batch as _update_subtitles_batch,
)
from app.services.subtitle_edit_service import (
    update_word_levels as _update_word_levels,
)
from app.services.video_card import (
    serialize_video_card as _serialize_video_card,
)
from app.services.video_like_service import (
    get_video_like_status as _get_video_like_status,
)
from app.services.video_like_service import (
    toggle_video_like as _toggle_video_like,
)
from app.services.video_review_service import (
    approve_review as _approve_review,
)
from app.services.video_review_service import (
    reject_review as _reject_review,
)
from app.services.video_seed_service import (
    seed_video as _seed_video,
)
from app.services.video_service import (
    delete_video as _delete_video,
)
from app.services.video_service import (
    get_demo_video as _get_demo_video,
)
from app.services.video_service import (
    get_ugc_pending_counts as _get_ugc_pending_counts,
)
from app.services.video_service import (
    get_video_detail as _get_video_detail,
)
from app.services.video_service import (
    get_video_status as _get_video_status,
)
from app.services.video_service import (
    list_all_videos as _list_all_videos,
)
from app.services.video_service import (
    list_public_videos as _list_public_videos,
)
from app.services.video_service import (
    localize_video_admin as _localize_video_admin,
)
from app.services.video_service import (
    update_video as _update_video,
)

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/public", response_model=PaginatedResponse[VideoResponse])
@rate_limit("30/minute")
async def list_public_videos(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await _list_public_videos(db, page=page, page_size=page_size)


@router.get("/demo", response_model=VideoResponse)
@rate_limit("30/minute")
async def get_demo_video(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the first-lesson video for the new-user flow (login required).

    404 means the operator has not marked a demo video yet; the client falls
    back to the home page rather than blocking onboarding.
    """
    return await _get_demo_video(db)


@router.get("/search", response_model=list[VideoResponse])
@rate_limit("30/minute")
async def search_videos(
    request: Request,
    q: str = "",
    limit: int = Query(20, ge=1, le=50),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Search videos by keyword across title and topic tags.

    Works for both authenticated and unauthenticated users.
    Authenticated users can also find their own non-official videos.

    Intentionally non-paginated (top-N by relevance); returns a bare list,
    not the PaginatedResponse envelope.
    """
    user_id = current_user.id if current_user else None
    results = await _search_videos(db, query=q, limit=limit, user_id=user_id)
    # D7: 搜索热度只记「搜到了内容」的词。搜不到的词（拼错、试玩、爬虫探测）
    # 挂上热搜栏只会让下一个人照着搜一遍空结果；Redis 故障仍然静默。
    if results:
        await _record_search_query(q)
    return results


@router.get("/search/suggest", response_model=SearchSuggestionsResponse)
@rate_limit("30/minute")
async def suggest_search(
    request: Request,
    q: str = "",
    limit: int = Query(8, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """D7 搜索建议：已发布视频标题，前缀匹配优先。公开（无需登录）。"""
    return {"suggestions": await _suggest_titles(db, q, limit)}


@router.get("/search/hot", response_model=HotSearchesResponse)
@rate_limit("30/minute")
async def hot_searches(request: Request):
    """D7 热门搜索：Redis ZSET Top 10（1h 缓存），故障时退回静态列表。"""
    return {"hot": await _get_hot_searches()}


@router.get("/search/subtitles", response_model=list[SubtitleSearchResult])
@rate_limit("20/minute")
async def search_subtitles(
    request: Request,
    q: str = "",
    limit: int = Query(10, ge=1, le=30),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Search subtitle text, return video + matching subtitle snippets.

    Intentionally non-paginated (top-N grouped by video); returns a bare
    list, not the PaginatedResponse envelope.
    """
    user_id = current_user.id if current_user else None
    return await _search_subtitles(db, query=q, limit=limit, user_id=user_id)


# ---------------------------------------------------------------------------
# Admin video content management
#
# NOTE: these static-path routes MUST be registered before the ``/{video_id}``
# catch-all below, otherwise ``GET /admin`` is shadowed by ``GET /{video_id}``.
# ---------------------------------------------------------------------------


@router.get("/admin", response_model=PaginatedResponse[VideoAdminResponse])
@rate_limit("30/minute")
async def list_admin_videos(
    request: Request,
    pagination: PaginationParams = Depends(),
    status: str | None = Query(None, description="Filter by processing status"),
    is_official: bool | None = Query(None, description="Filter official/user videos"),
    is_featured: bool | None = Query(None, description="Filter featured videos"),
    review_status: str | None = Query(
        None, description="Filter by UGC review status (draft/pending_review/published/rejected)"
    ),
    keyword: str | None = Query(None, description="Search title/topic_tags"),
    quality: str | None = Query(
        None, description="Filter by quality flag (quality_warning|quality_blocked|low_coverage)"
    ),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all videos (any status) with filters. Admin only."""
    return await _list_all_videos(
        db,
        status=status,
        is_official=is_official,
        is_featured=is_featured,
        review_status=review_status,
        keyword=keyword,
        quality=quality,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/admin/pending-count", response_model=PendingCountsResponse)
@rate_limit("30/minute")
async def get_admin_pending_count(
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Count UGC videos awaiting admin action (badge for the admin top bar).

    Returns ``{pending_processing, pending_review, total}`` for non-official
    videos waiting to be processed or reviewed.
    """
    return await _get_ugc_pending_counts(db)


@router.patch("/admin/{video_id}", response_model=VideoAdminResponse)
@rate_limit("30/minute")
async def update_admin_video(
    request: Request,
    video_id: str,
    payload: VideoAdminUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update video metadata (title, difficulty, tags, official/featured, published, notes). Admin only."""
    return await _update_video(db, video_id, payload)


@router.delete("/admin/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit("30/minute")
async def delete_admin_video(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a video and all of its dependents + media files. Admin only."""
    await _delete_video(db, video_id)

    return None


@router.post("/admin/{video_id}/start-processing", response_model=VideoAdminResponse)
@rate_limit("10/minute")
async def start_processing_video(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger GPU processing for a pending video. Admin only.

    The local GPU worker must be online (heartbeat present in Redis).
    Returns 503 if the worker is offline, 400 if the video is not in
    pending_processing status.
    """
    from app.services.video_seed_service import start_processing as _start_processing

    return await _start_processing(db, video_id)


@router.post("/admin/{video_id}/recover", response_model=VideoAdminResponse)
@rate_limit("10/minute")
async def recover_video(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-dispatch finalize_video for a video stuck mid-pipeline. Admin only.

    Clears the stale ``video:processing:{id}`` Redis lock left behind when the
    cloud worker died during finalize, then re-dispatches ``finalize_video``
    (resume-safe — skips completed steps). Use this for videos stuck in
    ``processing`` / ``ready_subtitles``; use ``start-processing`` for a fresh
    ``pending_processing`` video.

    A lock that is still inside its step's watchdog budget means a worker is
    running → 409 (the lock is not deleted). A recover for the same video is
    accepted at most once per 60 seconds.
    """
    from app.services.video_seed_service import recover_processing as _recover_processing

    return await _recover_processing(db, video_id)


@router.post("/admin/{video_id}/retry", response_model=VideoAdminResponse)
@rate_limit("10/minute")
async def retry_video(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a failed (error) video from the last completed pipeline step. Admin only.

    Preserves completed steps so finalize_video skips already-finished work.
    If subtitles exist, jumps straight to the tail (translating -> ... -> ready);
    otherwise resets to pending_processing for a fresh full run.

    Use ``recover`` for videos stuck mid-pipeline (processing/ready_subtitles)
    without an error state.
    """
    from app.services.video_seed_service import retry_video as _retry_video

    return await _retry_video(db, video_id)


@router.get("/admin/takedown-suggestions", response_model=TakedownSuggestionsResponse)
@rate_limit("30/minute")
async def list_takedown_suggestions(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """半自动下线的候选列表（需求 §5.3）：阈值建议 + 管理员确认。

    注册在 /admin/{video_id} 之前，避免 "takedown-suggestions" 被动态段吞掉。
    """
    from app.services.video_service import takedown_suggestions

    return {"items": await takedown_suggestions(db, limit=limit)}


@router.post("/admin/{video_id}/takedown", response_model=VideoAdminResponse)
@rate_limit("10/minute")
async def takedown_admin_video(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """下线视频：隐藏 + 删除本地媒体释放空间，保留 video 行与学习记录（§5.3）。

    幂等；缩略图保留以便收藏夹仍能渲染卡片。
    """
    from app.services.video_service import takedown_video

    return await takedown_video(db, video_id)


@router.post("/admin/{video_id}/localize", response_model=VideoAdminResponse)
@rate_limit("5/minute")
async def localize_admin_video(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Download + transcode an imported video's source to local storage. Admin only."""
    return await _localize_video_admin(db, video_id)


@router.post("/admin/{video_id}/retranslate", response_model=VideoAdminResponse)
@rate_limit("10/minute")
async def retranslate_video(
    request: Request,
    video_id: str,
    engine: str | None = Query(
        None,
        description="Override translation engine (registry keys, e.g. qwen|hy_mt2|glm|agnes|custom|commandcode)",
    ),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run translation, optionally with a different engine. Admin only.

    Use after a translation quality block (coverage below the block threshold)
    to retry with a different engine - the same engine + same input would
    reproduce the low coverage. Clears existing text_zh + quality_flag and
    re-dispatches finalize_video.

    Only allowed for ``error`` / ``ready`` videos: a video that is mid-pipeline
    (``processing`` / ``ready_subtitles`` / ``pending_processing``) answers 409.
    An unknown ``engine`` answers 422; a Redis single-flight guard blocks double
    clicks, and a dispatch failure restores the cleared translations (503).
    """
    from app.services.video_seed_service import retranslate_video as _retranslate

    return await _retranslate(db, video_id, engine=engine)


@router.get("/admin/{video_id}/quality-reports", response_model=list[QualityReportItem])
@rate_limit("30/minute")
async def get_video_quality_reports(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all quality reports for a video (transcription + translation history).

    Admin-only. Powers the video-detail quality panel: shows each stage's
    pass/fail, coverage, and per-check breakdown across re-runs.
    """
    from app.models.video_quality_report import VideoQualityReport

    rows = (
        (
            await db.execute(
                select(VideoQualityReport)
                .where(VideoQualityReport.video_id == video_id)
                .order_by(VideoQualityReport.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "id": r.id,
            "stage": r.stage,
            "passed": r.passed,
            "coverage_ratio": r.coverage_ratio,
            "metrics": r.metrics,
            "issues": r.issues,
            "segment_count": r.segment_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.patch("/admin/{video_id}/subtitles/{subtitle_id}", response_model=SubtitleResponse)
@rate_limit("60/minute")
async def update_admin_subtitle(
    request: Request,
    video_id: str,
    subtitle_id: str,
    payload: SubtitleUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit one subtitle's text/timing/grammar note. Editing text_en resets that
    line's word_levels to the ECDICT baseline. Admin only."""
    return await _update_subtitle(db, video_id, subtitle_id, payload, edited_by=current_user.id)


@router.patch("/admin/{video_id}/subtitles", response_model=list[SubtitleResponse])
@rate_limit("60/minute")
async def update_admin_subtitles_batch(
    request: Request,
    video_id: str,
    payload: SubtitleBatchUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply many subtitle edits in one transaction. All ids must belong to video_id. Admin only."""
    return await _update_subtitles_batch(db, video_id, payload, edited_by=current_user.id)


@router.post("/admin/{video_id}/subtitles", response_model=SubtitleResponse)
@rate_limit("60/minute")
async def create_admin_subtitle(
    request: Request,
    video_id: str,
    payload: SubtitleCreate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Append a new subtitle row at the end of the video (canvas editor).
    The English text may be empty initially; timing must not overlap existing
    rows. Admin only."""
    return await _create_subtitle(db, video_id, payload, edited_by=current_user.id)


@router.post(
    "/admin/{video_id}/subtitles/reorder",
    response_model=list[SubtitleResponse],
)
@rate_limit("30/minute")
async def reorder_admin_subtitles(
    request: Request,
    video_id: str,
    payload: SubtitleReorder,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Reassign sentence_index for every subtitle in one transaction (canvas
    editor drag-to-reorder). The payload must cover all current subtitles with
    a contiguous 0..N-1 index sequence; timing is re-validated against the new
    neighbor order. Admin only."""
    return await _reorder_subtitles(db, video_id, payload, edited_by=current_user.id)


@router.delete("/admin/{video_id}/subtitles/{subtitle_id}", response_model=SubtitleDeleteResult)
@rate_limit("60/minute")
async def delete_admin_subtitle(
    request: Request,
    video_id: str,
    subtitle_id: str,
    force: bool = Query(
        False,
        description="删除会级联清除该行的用户原句收藏与编辑历史；缺省 409 并返回影响计数，带 force=true 才执行",
    ),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete one subtitle and close the gap in sentence_index (canvas editor).

    Deleting one row also cascades to its sentence favorites and edit history,
    so a plain delete answers 409 with the affected counts; pass ``?force=true``
    only after reviewing them. Admin only.
    """
    return await _delete_subtitle(db, video_id, subtitle_id, edited_by=current_user.id, force=force)


@router.post(
    "/admin/{video_id}/subtitles/{subtitle_id}/split",
    response_model=list[SubtitleResponse],
)
@rate_limit("60/minute")
async def split_admin_subtitle(
    request: Request,
    video_id: str,
    subtitle_id: str,
    payload: SubtitleSplit,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Split one subtitle into two at split_time. Admin only."""
    return await _split_subtitle(db, video_id, subtitle_id, payload, edited_by=current_user.id)


@router.post(
    "/admin/{video_id}/subtitles/{subtitle_id}/merge",
    response_model=SubtitleResponse,
)
@rate_limit("60/minute")
async def merge_admin_subtitle(
    request: Request,
    video_id: str,
    subtitle_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Merge a subtitle with the next one. Admin only."""
    return await _merge_subtitle(db, video_id, subtitle_id, edited_by=current_user.id)


@router.post("/admin/{video_id}/subtitles/resegment", response_model=ResegmentResult)
@rate_limit("10/minute")
async def resegment_admin_subtitles(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-cut every subtitle into proper sentences (bulk). Snapshots first so
    the change is reversible via /resegment/rollback. Translations are cleared
    — segmentation changed, so the admin should re-trigger translation after.

    Sentence favorites, edit revisions and vocabulary source links are
    re-mapped onto the new segments by time overlap instead of being deleted by
    the FK cascades; the response reports the counts. Admin only."""
    return await _resegment_video(db, video_id, edited_by=current_user.id)


@router.post("/admin/{video_id}/subtitles/resegment/rollback", response_model=ResegmentRollbackResult)
@rate_limit("10/minute")
async def rollback_resegment_admin(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore subtitles from the latest re-segment snapshot.

    User data attached to the re-segmented rows is mapped back onto the
    restored rows, and rows the original re-segmentation had to drop are
    re-inserted from the snapshot payload. Admin only."""
    return await _rollback_resegment(db, video_id, edited_by=current_user.id)


@router.patch("/admin/{video_id}/subtitles/{subtitle_id}/word-levels", response_model=SubtitleResponse)
@rate_limit("60/minute")
async def update_admin_word_levels(
    request: Request,
    video_id: str,
    subtitle_id: str,
    payload: WordLevelsUpdate,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually override one subtitle's word-level annotations. Pass null to clear. Admin only."""
    return await _update_word_levels(db, video_id, subtitle_id, payload)


@router.post("/admin/{video_id}/subtitles/word-levels/recompute", response_model=RecomputeWordLevelsResponse)
@rate_limit("10/minute")
async def recompute_admin_word_levels(
    request: Request,
    video_id: str,
    payload: RecomputeWordLevelsRequest | None = None,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Recompute word_levels from ECDICT for selected subtitles (or the whole video). Admin only."""
    subtitle_ids = payload.subtitle_ids if payload else None
    return await _recompute_word_levels(db, video_id, subtitle_ids)


@router.post("/admin/{video_id}/subtitles/{subtitle_id}/rollback/{revision_id}", response_model=SubtitleResponse)
@rate_limit("30/minute")
async def rollback_admin_subtitle(
    request: Request,
    video_id: str,
    subtitle_id: str,
    revision_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Roll back a subtitle to the before-state of a prior edit. Admin only."""
    return await _rollback_subtitle(db, video_id, subtitle_id, revision_id, edited_by=current_user.id)


@router.get("/admin/{video_id}/subtitles/revisions", response_model=PaginatedResponse[SubtitleRevisionItem])
@rate_limit("30/minute")
async def list_admin_subtitle_revisions(
    request: Request,
    video_id: str,
    page: int = 1,
    page_size: int = 50,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all subtitle edit revisions for a video (newest first). Admin only."""
    return await _list_subtitle_revisions(db, video_id, page=page, page_size=page_size)


@router.get(
    "/admin/{video_id}/subtitles/{subtitle_id}/revisions", response_model=PaginatedResponse[SubtitleRevisionItem]
)
@rate_limit("30/minute")
async def list_admin_subtitle_revisions_for_one(
    request: Request,
    video_id: str,
    subtitle_id: str,
    page: int = 1,
    page_size: int = 50,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List edit revisions for one subtitle. Admin only."""
    return await _list_subtitle_revisions(db, video_id, subtitle_id=subtitle_id, page=page, page_size=page_size)


@router.post("/admin/{video_id}/review/approve", response_model=VideoAdminResponse)
@rate_limit("30/minute")
async def approve_admin_review(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a UGC video pending review: freezes live subtitles as the public
    version and marks it published. Admin only."""
    video = await _get_admin_video_or_404(db, video_id)
    return VideoAdminResponse.model_validate(await _approve_review(db, video, current_user))


@router.post("/admin/{video_id}/review/reject", response_model=VideoAdminResponse)
@rate_limit("30/minute")
async def reject_admin_review(
    request: Request,
    video_id: str,
    payload: ReviewRejectRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a UGC video pending review with a reason. The public keeps the
    last approved snapshot (if any); the owner can edit & resubmit. Admin only."""
    video = await _get_admin_video_or_404(db, video_id)
    return VideoAdminResponse.model_validate(await _reject_review(db, video, current_user, payload.reason))


async def _get_admin_video_or_404(db: AsyncSession, video_id: str):
    """Admin helper: fetch any video by id (no access gate — admin sees all)."""
    from app.services.video_service import _get_video_or_404

    return await _get_video_or_404(db, video_id)


@router.get("/admin/{video_id}/detail", response_model=VideoDetailResponse)
@rate_limit("30/minute")
async def get_admin_video_detail(
    request: Request,
    video_id: str,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin video detail — bypasses check_video_access so admins can view UGC drafts."""
    result = await _get_video_detail(db, video_id, current_user=None, skip_access_check=True)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return result


@router.get("/admin/{video_id}/status", response_model=VideoAdminStatusResponse)
@rate_limit("30/minute")
async def get_admin_video_status(
    request: Request,
    video_id: str,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin processing status — bypasses check_video_access + includes error_message."""
    result = await _get_video_status(db, video_id, current_user=None, skip_access_check=True)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return result


@router.get("/admin/{video_id}/score", response_model=VideoScoreResponse)
@rate_limit("30/minute")
async def get_admin_video_score(
    request: Request,
    video_id: str,
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin/debug: latest learning_score breakdown for a video (P1).

    Returns the per-factor values so the score is explainable, not just the
    total. Typed response (ADM-10); 404 if the video has never been scored.
    """
    from app.services.scoring_service import get_latest_score

    row = await get_latest_score(db, video_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No score computed yet")
    return {
        "video_id": video_id,
        "total_score": row.total_score,
        "factors": {
            "ctr": row.ctr,
            "retention": row.retention,
            "watch_time": row.watch_time,
            "topic_match": row.topic_match,
            "quality": row.quality,
            "viral": row.viral,
            "freshness": row.freshness,
            "bonus": row.bonus,
        },
        "computed_at": row.computed_at.isoformat() if row.computed_at else None,
    }


# Phase 1 B0 — list the current user's favorite videos. Declared before the
# /{video_id} dynamic route so the static "favorites" path wins the match
# (FastAPI's route ordering is registration order; the previous attempt got
# swallowed by the catch-all and returned 404).
@router.get("/favorites", response_model=PaginatedResponse[VideoResponse])
@rate_limit("30/minute")
async def list_user_favorites(
    request: Request,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Paginated list of the current user's favorited videos.

    Joins user_favorites → videos (LEFT user_notes for the excerpt). Cards come
    from the shared projector at ``scope="card"`` — same shape as every other
    card, plus the favorite/note annotations this list is the only one to carry.

    已下线（``storage_mode='offline'``）的视频**仍然出现在收藏夹**：需求 §5.3
    要求「收藏夹保留入口并标注已下架」。故此处刻意不加发布态过滤；``storage_mode``
    随卡片下发，由前端渲染「已下架」角标。
    """
    from app.models.favorite import UserFavorite, UserNote
    from app.services.channel_service import channel_slugs_for

    total = (
        await db.execute(select(func.count(UserFavorite.id)).where(UserFavorite.user_id == current_user.id))
    ).scalar_one()

    rows = (
        await db.execute(
            select(Video, UserFavorite.created_at, UserNote.content)
            .join(UserFavorite, UserFavorite.video_id == Video.id)
            .outerjoin(
                UserNote,
                (UserNote.video_id == Video.id) & (UserNote.user_id == current_user.id),
            )
            .where(UserFavorite.user_id == current_user.id)
            .order_by(UserFavorite.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
    ).all()

    slug_map = await channel_slugs_for(db, [v for v, _, _ in rows])
    items = [
        _serialize_video_card(
            v,
            scope="card",
            # The viewer here is the list's owner, so owner-only fields (their
            # own UGC draft's error/rejection notes) stay visible, and the
            # favorite/note annotations of this list are filled in.
            viewer=current_user,
            channel_slug=slug_map.get(v.channel_ref),
            # `note` is the third SELECT column — UserNote.content itself, not a
            # UserNote row. The pre-批 2 dict read `note.content` here and raised
            # AttributeError (→ 500) for every favorites list containing a note.
            note=note,
            favorited_at=fav_at,
        )
        for v, fav_at, note in rows
    ]
    return paginated(items, pagination, total=total)


# 首页排行榜 — static route registered before the /{video_id} dynamic route so
# the static "rankings" path wins the match (same ordering constraint as
# /favorites above). Optional auth: the lists are public; the dependency only
# mirrors the neighboring endpoints.
@router.get("/rankings", response_model=list[VideoResponse])
@rate_limit("30/minute")
async def list_video_rankings(
    request: Request,
    scope: str = Query("latest"),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """首页排行榜：最新发布 / 本周播放 / 本周收藏（自然周，北京周一 00:00 切周），
    各取前 20。

    scope 不合法返回 422。结果读穿 Redis 快照（fail-open，Redis 故障时直接
    查库）；快照由 snapshot-rankings beat 任务每日北京 00:30 刷新。周播放榜按
    session_id 去重计数（防刷规则，见 ranking_service）。
    """
    from app.services.ranking_service import RANKING_SCOPES, get_rankings

    if scope not in RANKING_SCOPES:
        raise UnprocessableEntityError(f"Invalid scope: {scope!r} (expected one of: {', '.join(RANKING_SCOPES)})")
    return await get_rankings(db, scope)


# Related videos for the watch page: same channel first, then the same first
# topic tag, then recent published videos. Public; excludes the current video.
@router.get("/{video_id}/related", response_model=dict)
@rate_limit("30/minute")
async def list_related_videos(
    request: Request,
    video_id: str,
    limit: int = Query(6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    source = await db.get(Video, video_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    from app.services.channel_service import channel_slugs_for
    from app.services.discovery_service import public_video_filters
    from app.services.video_card import video_card_payload

    picked: list[Video] = []
    seen = {video_id}

    async def _take(stmt) -> None:
        for video in (await db.execute(stmt.limit(limit))).scalars().all():
            if video.id not in seen and len(picked) < limit:
                seen.add(video.id)
                picked.append(video)

    base = (
        select(Video)
        .where(Video.id != video_id, *public_video_filters())
        .order_by(Video.favorite_count.desc().nullslast(), Video.created_at.desc(), Video.id.desc())
    )
    if source.channel_ref:
        await _take(base.where(Video.channel_ref == source.channel_ref))
    first_tag = next((tag.strip() for tag in (source.topic_tags or "").split(",") if tag.strip()), None)
    if first_tag and len(picked) < limit:
        await _take(base.where(Video.topic_tags.ilike(f"%{first_tag}%")))
    if len(picked) < limit:
        await _take(base)

    slug_map = await channel_slugs_for(db, picked)
    return {
        "items": [video_card_payload(v, slug_map.get(v.channel_ref) if v.channel_ref else None) for v in picked],
        "total": len(picked),
    }


# Phase 1 B0 — list the current user's vocabulary for a single video, used by
# the EndScreen "复习本视频生词" entry on the watch page.
@router.get("/{video_id}/vocabulary", response_model=PaginatedResponse[VideoVocabularyItem])
@rate_limit("30/minute")
async def list_video_vocabulary(
    request: Request,
    video_id: str,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's vocabulary rows for this video, newest first."""
    from app.models.learning import Vocabulary

    video = await db.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    total = (
        await db.execute(
            select(func.count(Vocabulary.id)).where(
                Vocabulary.user_id == current_user.id, Vocabulary.video_id == video_id
            )
        )
    ).scalar_one()

    rows = (
        (
            await db.execute(
                select(Vocabulary)
                .where(Vocabulary.user_id == current_user.id, Vocabulary.video_id == video_id)
                .order_by(Vocabulary.created_at.desc())
                .offset(pagination.offset)
                .limit(pagination.page_size)
            )
        )
        .scalars()
        .all()
    )

    items = [
        {
            "id": w.id,
            "word": w.word,
            "definition": w.definition,
            "translation": w.translation,
            "mastery_level": w.mastery_level,
            "context_sentence": w.context_sentence,
            "video_id": w.video_id,
            "subtitle_id": w.subtitle_id,
            "review_count": w.review_count,
            "next_review_at": w.next_review_at.isoformat() if w.next_review_at else None,
            "created_at": w.created_at.isoformat(),
        }
        for w in rows
    ]
    return paginated(items, pagination, total=total)


# Phase 1 B0 — return the top-N sentences with the highest exam-word density,
# used by the EndScreen "跟读重点句" entry. Falls back to the first N
# sentences when no exam words are tagged.
@router.get("/{video_id}/shadowing-sentences")
@rate_limit("30/minute")
async def list_shadowing_sentences(
    request: Request,
    video_id: str,
    limit: int = Query(3, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.retired_features import feature_gone

    feature_gone()


@router.get("/{video_id}", response_model=VideoDetailResponse)
@rate_limit("30/minute")
async def get_video(
    request: Request,
    video_id: str,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    result = await _get_video_detail(db, video_id, current_user)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return result


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
@rate_limit("30/minute")
async def get_video_status(
    request: Request,
    video_id: str,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    result = await _get_video_status(db, video_id, current_user)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return result


@router.post("/seed", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
@rate_limit("5/minute")
async def seed_video(
    request: Request,
    data: VideoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Seed an official video for the public homepage. Admin only.

    Re-seeding a URL that is already in the pipeline (any of
    pending_processing / processing / ready_subtitles / ready) returns the
    existing row instead of creating a duplicate + a second GPU run. A
    URL-level Redis lock turns a double click into 409 while the first request
    is still working. Only ``error`` rows stay retryable.
    """
    return await _seed_video(db, data.source_url)


async def _require_valid_cookies(source_url: str):
    """Ensure YouTube cookies are valid; raise HTTPException if not."""
    from app.services.youtube_cookies_service import ensure_cookies

    cookies_status = await ensure_cookies(source_url)
    if cookies_status == "need_manual_login":
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="YouTube cookies 需重新登录：请在服务器上运行 playwright-cli open "
            "https://www.youtube.com --persistent 并登录后重试",
        )
    if cookies_status == "error":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="cookies 探测/刷新失败，请检查网络或 yt-dlp 配置",
        )


@router.post("/seed-full", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
@rate_limit("3/minute")
async def seed_video_full(
    request: Request,
    data: VideoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """One-click seed: ensure cookies, seed, run the full pipeline, auto-publish.

    Probes yt-dlp cookies against the URL; if invalid, refreshes from the
    persistent playwright-cli browser session; if the session is logged out,
    returns 423 so the admin knows to re-login on the server. On success the
    video is seeded with auto_publish=True so finalize_video publishes it once
    ready — the frontend just polls /status.
    """
    await _require_valid_cookies(data.source_url)
    return await _seed_video(db, data.source_url, auto_publish=True)


@router.post("/{video_id}/like", response_model=VideoLikeToggleResponse)
@rate_limit("30/minute")
async def toggle_video_like(
    request: Request,
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle like on a video. Returns {"liked": bool}."""
    return await _toggle_video_like(db, current_user.id, video_id)


@router.get("/{video_id}/like-status", response_model=VideoLikeStatusResponse)
@rate_limit("30/minute")
async def video_like_status(
    request: Request,
    video_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if the current user has liked a video."""
    return await _get_video_like_status(db, current_user.id, video_id)
