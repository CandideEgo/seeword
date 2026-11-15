"""管理员首页编辑内容 API（全部 ``get_admin_user``）。

契约：``backend/app/schemas/home_content.py``。这一层只做参数
解析与 service 调用——校验、乐观锁、事务、状态机都在
``app.services.home_content_service``。
"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_admin_user
from app.core.database import get_db
from app.core.errors import AppError, ErrorCode
from app.core.limiter import rate_limit
from app.models.user import User
from app.schemas.home_content import (
    HomeContentDraftSaveRequest,
    HomeContentGenerateRequest,
    HomeContentGenerationEnvelope,
    HomeContentGenerationResponse,
    HomeContentPublishRequest,
    HomeContentPublishResponse,
    HomeContentRestoreDraftRequest,
    HomeContentVideoState,
    HomeLayoutDraftSaveRequest,
    HomeLayoutPreview,
    HomeLayoutPublishRequest,
    HomeLayoutPublishResponse,
    HomeLayoutState,
)
from app.services import home_content_service

router = APIRouter(prefix="/admin/home-content", tags=["admin-home-content"])


# ---------------------------------------------------------------------------
# 单视频：草稿 / 生成 / 发布 / 恢复 / 预览
# ---------------------------------------------------------------------------


@router.get("/videos/{video_id}", response_model=HomeContentVideoState)
@rate_limit("60/minute")
async def get_video_content_state(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """草稿、生成任务状态、历史版本、当前位置；管理员鉴权。"""
    return await home_content_service.get_video_state(db, video_id)


@router.post("/videos/{video_id}/generate", response_model=HomeContentGenerationResponse, status_code=202)
@rate_limit("10/minute")
async def generate_content(
    request: Request,
    video_id: str,
    payload: HomeContentGenerateRequest,
    response: Response,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """入队生成任务：202 + generation；已有有效任务时 200 + reused=true（不重复计费）。"""
    claim = await home_content_service.claim_generation(
        db,
        video_id,
        current_user.id,
        expected_revision=payload.expected_revision,
        overwrite=payload.overwrite,
    )
    if not claim.reused:
        await home_content_service.enqueue_generation(db, claim)
    else:
        response.status_code = 200
    generation = await home_content_service.get_generation_state(db, video_id)
    if generation is None:  # claim 成功却读不到状态只可能是并发被清理，视为内部错误
        raise AppError(500, ErrorCode.INTERNAL_ERROR, "生成任务状态缺失，请重试")
    return HomeContentGenerationResponse(generation=generation, reused=claim.reused)


@router.get("/videos/{video_id}/generation", response_model=HomeContentGenerationEnvelope)
@rate_limit("60/minute")
async def get_generation_state(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """轻量轮询：最近一次生成任务（顺手做超时恢复）。"""
    return HomeContentGenerationEnvelope(generation=await home_content_service.get_generation_state(db, video_id))


@router.put("/videos/{video_id}/draft", response_model=HomeContentVideoState)
@rate_limit("30/minute")
async def save_draft(
    request: Request,
    video_id: str,
    payload: HomeContentDraftSaveRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """保存草稿（乐观锁 expected_revision；冲突 409）。"""
    return await home_content_service.save_draft(
        db, video_id, payload.payload, payload.expected_revision, current_user.id
    )


@router.post("/videos/{video_id}/publish", response_model=HomeContentPublishResponse)
@rate_limit("10/minute")
async def publish_content(
    request: Request,
    video_id: str,
    payload: HomeContentPublishRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """校验并创建不可变版本；``place`` 可在同事务内替换主推/次推位置。"""
    return await home_content_service.publish_content(
        db, video_id, payload.expected_revision, payload.place, current_user.id
    )


@router.post("/videos/{video_id}/restore-draft", response_model=HomeContentVideoState)
@rate_limit("10/minute")
async def restore_draft(
    request: Request,
    video_id: str,
    payload: HomeContentRestoreDraftRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """把指定历史版本复制为新草稿（不影响线上内容）。"""
    return await home_content_service.restore_draft(
        db, video_id, payload.revision_id, payload.expected_revision, current_user.id
    )


@router.get("/videos/{video_id}/preview", response_model=HomeLayoutPreview)
@rate_limit("60/minute")
async def preview_video(
    request: Request,
    video_id: str,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """草稿预览：与首页同形的 page + 发布会被拒绝的字段级 issues。"""
    return await home_content_service.preview_video(db, video_id)


# ---------------------------------------------------------------------------
# 首页编排（布局）
# ---------------------------------------------------------------------------


@router.get("/layout", response_model=HomeLayoutState)
@rate_limit("60/minute")
async def get_layout(
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """布局草稿 / 当前发布布局 / 上一版 / 候选池 / 字段级问题。"""
    return await home_content_service.get_layout_state(db)


@router.put("/layout/draft", response_model=HomeLayoutState)
@rate_limit("30/minute")
async def save_layout_draft(
    request: Request,
    payload: HomeLayoutDraftSaveRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """保存编排草稿（乐观锁；未排好的草稿允许保存，问题在发布时拦截）。"""
    return await home_content_service.save_layout_draft(db, payload.layout, payload.expected_revision, current_user.id)


@router.post("/layout/publish", response_model=HomeLayoutPublishResponse, response_model_exclude_none=True)
@rate_limit("10/minute")
async def publish_layout(
    request: Request,
    payload: HomeLayoutPublishRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """校验并原子发布整版布局。"""
    return await home_content_service.publish_layout(db, payload.expected_revision, current_user.id)


@router.post("/layout/rollback", response_model=HomeLayoutPublishResponse, response_model_exclude_none=True)
@rate_limit("10/minute")
async def rollback_layout(
    request: Request,
    payload: HomeLayoutPublishRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """恢复上一发布布局；没有上一版时原子清空并回到旧兜底（cleared=true）。

    上一版引用已下线/来源变更时仍 409 HOME_CONTENT_ROLLBACK_INVALID，不回滚。
    """
    return await home_content_service.rollback_layout(db, payload.expected_revision, current_user.id)


@router.get("/layout/preview", response_model=HomeLayoutPreview)
@rate_limit("60/minute")
async def preview_layout(
    request: Request,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """整版预览：用 draft_layout 构造 page；issues 为发布会被拒绝的问题。"""
    return await home_content_service.preview_layout(db)
