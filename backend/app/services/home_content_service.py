"""首页编辑内容服务——草稿 / 不可变版本 / 生成状态机（A15 业务边界拆分后）。

契约：``backend/app/schemas/home_content.py``。API 路由只做解析与
调用，所有规则收敛在首页内容这一族模块里。A15 按业务边界拆成三层：

- ``home_content_content``：常量、来源指纹、字段级 issues、展示 DTO（不碰布局与写入）；
- ``home_content_layout``：布局写入、布局校验、公共读取 ``resolve_public_page``；
- 本模块：视频侧的草稿与不可变版本（保存/发布/恢复/预览）＋ 生成任务状态机。

对外仍然只认 ``app.services.home_content_service``——路由、Celery 任务与测试都按模块
属性访问；下面把另外两层的公开名字重新导入，保证 ``home_content_service.<name>`` 不变。

四条不可破坏的不变量（改代码前先读）：

1. **内容与位置分开**：布局只存 ``content_revision_id``（+ 稳定
   expression_id/scenario_id），所以重新生成/编辑草稿永远不影响线上。
2. **已发布版本只追加**：发布产生新的 ``HomeContentRevision``，从不原地修改；
   草稿坏了可以靠历史版本恢复，线上内容也不会被写坏。
3. **来源指纹**：见 ``home_content_content.compute_source_fingerprint``；发布、公共
   读取、生成写回都重算比对，字幕被改/重排/重新转写后旧引用自动失效。
4. **公共接口不缓存**：见 ``home_content_layout.resolve_public_page``；旧兜底
   （``browse/featured``）继续走它自己的缓存与既有失效链路。

生成任务（Celery，``app/tasks/home_content_tasks.py``）通过这些钩子与本模块交互；
它们**自己 commit**，调用方不要再包事务：

    claim = await claim_generation(db, video_id, actor_id, expected_revision=..., overwrite=...)
    await enqueue_generation(db, claim)          # 入队失败会置 failed 并抛 503
    # worker 侧：
    ctx = await load_generation_context(db, generation_id)   # None = 已被取代/取消
    if ctx is None: return
    ... 生成 payload ...
    await complete_generation(db, generation_id, payload, model=..., prompt_version=...,
                              usage=..., calls=...)
    # 失败：await fail_generation(db, generation_id, code, message)
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import TYPE_CHECKING

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ErrorCode
from app.models.home_content import (
    HomeContentDraft,
    HomeContentGenerationStatus,
    HomeContentRevision,
    HomePageConfig,
)
from app.models.video import Video
from app.schemas.home_content import (
    HomeContentDraft as HomeContentDraftSchema,
)
from app.schemas.home_content import (
    HomeContentGeneration,
    HomeContentGenerationCoverage,
    HomeContentGenerationUsage,
    HomeContentSlotPosition,
    HomeContentVideoState,
    HomeEditorialExpressionSlot,
    HomeEditorialPage,
    HomeEditorialScenarioSlot,
    HomeEditorialVideoSlot,
    HomeLayoutPreview,
)
from app.services.home_content_content import (
    _INSERT_ATTEMPTS,
    _VERSION_ALLOC_ATTEMPTS,
    CONTENT_SCHEMA_VERSION,
    GENERATION_STALE_SECONDS,
    LAYOUT_SINGLETON_ID,
    MAX_SCENARIOS,
    MAX_SECONDARY,
    _as_utc,
    _cas_update,
    _content_dto,
    _iso,
    _issue,
    _load_subtitles,
    _now,
    _parse_draft,
    _revision_conflict,
    _try_parse_draft,
    collect_issues,
    compute_source_fingerprint,
    current_source_fingerprint,
    empty_layout,
    resolve_clip,
    resolve_sentences,
)
from app.services.home_content_layout import (
    _get_config,
    _get_or_create_config,
    _get_video,
    _is_publicly_visible,
    _layout_revision_ids,
    _parse_layout,
    _positions_map,
    _revision_summaries,
    _sorted_positions,
    _video_cards,
    get_layout_state,
    preview_layout,
    publish_layout,
    resolve_public_page,
    rollback_layout,
    save_layout_draft,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.subtitle import Subtitle

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 管理员：视频状态 / 草稿 / 发布 / 恢复 / 预览
# ---------------------------------------------------------------------------


async def _get_draft(db: AsyncSession, video_id: str) -> HomeContentDraft | None:
    return (
        await db.execute(select(HomeContentDraft).where(HomeContentDraft.video_id == video_id))
    ).scalar_one_or_none()


async def _get_or_create_draft(db: AsyncSession, video_id: str) -> HomeContentDraft:
    """取草稿；没有就建一行（每视频一份）。

    并发建行会撞唯一约束（``video_id``）：输的那笔重读对方建好的行，不把
    ``IntegrityError`` 泄成 500。先查后插的窗口用 SAVEPOINT 包住，撞了只回滚
    这一段插入，不动整个事务。
    """
    draft = await _get_draft(db, video_id)
    if draft is not None:
        return draft
    for _ in range(_INSERT_ATTEMPTS):
        candidate = HomeContentDraft(
            video_id=video_id,
            payload=None,
            schema_version=CONTENT_SCHEMA_VERSION,
            revision=0,
            status=HomeContentGenerationStatus.IDLE,
            generation_calls=0,
        )
        try:
            async with db.begin_nested():
                db.add(candidate)
                await db.flush()
            return candidate
        except IntegrityError:
            if candidate in db:  # SAVEPOINT 回滚后仍挂在 session 上的残留对象
                db.expunge(candidate)
            existing = await _get_draft(db, video_id)
            if existing is not None:
                return existing
            # 对方还没提交：重试（INSERT 会等到对方提交后再判定唯一约束）。
    raise AppError(409, ErrorCode.CONFLICT, "草稿初始化冲突，请重试")


def _stale_generation(draft: HomeContentDraft) -> bool:
    started = draft.generation_started_at
    if started is None:
        return False
    return _now() - _as_utc(started) > timedelta(seconds=GENERATION_STALE_SECONDS)


def _expire_stale_generation(draft: HomeContentDraft) -> bool:
    """把超时的 queued/running 标 failed TIMEOUT；返回是否改动（调用方 commit）。"""
    if draft.status not in HomeContentGenerationStatus.ACTIVE:
        return False
    if not _stale_generation(draft):
        return False
    draft.status = HomeContentGenerationStatus.FAILED
    draft.active_generation_id = None
    draft.generation_error_code = ErrorCode.HOME_CONTENT_TIMEOUT
    draft.generation_error_message = "生成任务超时，请重试"
    draft.generation_finished_at = _now()
    return True


def _generation_dto(draft: HomeContentDraft | None) -> HomeContentGeneration | None:
    if draft is None:
        return None
    generation_id = draft.active_generation_id or draft.last_generation_id
    if not generation_id:
        return None
    status = draft.status
    if status not in HomeContentGenerationStatus.ACTIVE and status not in HomeContentGenerationStatus.TERMINAL:
        status = HomeContentGenerationStatus.IDLE
    usage = None
    if isinstance(draft.generation_usage, dict):
        usage = HomeContentGenerationUsage(
            prompt_tokens=draft.generation_usage.get("prompt_tokens"),
            completion_tokens=draft.generation_usage.get("completion_tokens"),
        )
    return HomeContentGeneration(
        generation_id=generation_id,
        status=status,  # type: ignore[arg-type]
        started_at=_iso(draft.generation_started_at),
        finished_at=_iso(draft.generation_finished_at),
        error_code=draft.generation_error_code,
        error_message=draft.generation_error_message,
        model=draft.generation_model,
        prompt_version=draft.generation_prompt_version,
        usage=usage,
        coverage=(
            HomeContentGenerationCoverage.model_validate(draft.generation_coverage)
            if isinstance(draft.generation_coverage, dict)
            else None
        ),
    )


async def get_video_state(db: AsyncSession, video_id: str) -> HomeContentVideoState:
    """后台视频详情：草稿、最近生成、历史版本、当前位置（契约 §4 表）。"""
    video = await _get_video(db, video_id)
    fingerprint, _ = await current_source_fingerprint(db, video_id)
    draft = await _get_draft(db, video_id)
    if draft is not None and _expire_stale_generation(draft):
        await db.commit()
    config = await _get_config(db)
    published_layout = _parse_layout(config.published_layout) if config is not None else None
    position_map = await _positions_map(db, published_layout)
    revision_summaries = await _revision_summaries(db, video, fingerprint, position_map)
    draft_payload = _try_parse_draft(draft.payload) if draft is not None else None
    positions: list[HomeContentSlotPosition] = []
    for summary in revision_summaries:
        for position in summary.positions:
            if position not in positions:
                positions.append(position)
    return HomeContentVideoState(
        video_id=video.id,
        video_title=video.title,
        publicly_visible=await _is_publicly_visible(db, video.id),
        source_fingerprint=fingerprint,
        draft=draft_payload,
        draft_revision=draft.revision if draft is not None else 0,
        source_changed=bool(draft is not None and draft.source_fingerprint and draft.source_fingerprint != fingerprint),
        generation=_generation_dto(draft),
        revisions=revision_summaries,
        positions=_sorted_positions(positions),
    )


async def get_generation_state(db: AsyncSession, video_id: str) -> HomeContentGeneration | None:
    """轻量轮询接口：只读最近一次生成任务，并顺手做超时恢复。"""
    await _get_video(db, video_id)
    draft = await _get_draft(db, video_id)
    if draft is not None and _expire_stale_generation(draft):
        await db.commit()
    return _generation_dto(draft)


async def save_draft(
    db: AsyncSession,
    video_id: str,
    payload: HomeContentDraftSchema,
    expected_revision: int,
    actor_id: str | None,
) -> HomeContentVideoState:
    """保存草稿（乐观锁）。逻辑上不改变已发布内容。"""
    await _get_video(db, video_id)
    fingerprint, subtitles = await current_source_fingerprint(db, video_id)
    if not subtitles:
        raise AppError(422, ErrorCode.HOME_CONTENT_NO_SUBTITLES, "该视频没有字幕，无法制作首页内容")
    draft = await _get_or_create_draft(db, video_id)
    if draft.revision != expected_revision:
        raise _revision_conflict("内容已在别处修改，请刷新后重试")
    issues = collect_issues(payload, subtitles, strict=False)
    if issues:
        raise AppError(
            422,
            ErrorCode.HOME_CONTENT_INVALID,
            "草稿内容校验失败",
            detail=[issue.model_dump() for issue in issues],
        )
    # 乐观锁的原子判定：条件 UPDATE（WHERE revision = expected_revision）。
    # 上面读到的 draft.revision 可能已经过期（另一个管理员刚保存过），所以判定
    # 必须落在写入这条语句上，而不是靠内存里那份快照。
    await _cas_update(
        db,
        update(HomeContentDraft)
        .where(
            HomeContentDraft.id == draft.id,
            HomeContentDraft.revision == expected_revision,
        )
        .values(
            payload=payload.model_dump(mode="json"),
            schema_version=CONTENT_SCHEMA_VERSION,
            revision=expected_revision + 1,
            source_fingerprint=fingerprint,
            updated_by=actor_id,
            updated_at=_now(),
        ),
        "内容已在别处修改，请刷新后重试",
    )
    # Core UPDATE 不经过 ORM：identity map 里还是旧 payload / 旧 revision，
    # 不显式重读的话后面的 get_video_state 会读到旧值。
    await db.refresh(draft)
    await db.commit()
    return await get_video_state(db, video_id)


async def publish_content(
    db: AsyncSession,
    video_id: str,
    expected_revision: int,
    place: str | None,
    actor_id: str | None,
) -> dict:
    """校验并创建不可变版本；可选在同事务内替换首页位置（「发布并替换主推」）。"""
    video = await _get_video(db, video_id)
    # 布局乐观锁的基准：请求开始时编排的 revision。发布期间别人改过编排
    # （保存草稿/发布/回滚），下面的布局条件 UPDATE 就会失配 → 409。
    config_snapshot = await _get_config(db)
    expected_config_revision = config_snapshot.revision if config_snapshot is not None else 0
    fingerprint, subtitles = await current_source_fingerprint(db, video_id)
    if not subtitles:
        raise AppError(422, ErrorCode.HOME_CONTENT_NO_SUBTITLES, "该视频没有字幕，无法发布首页内容")
    draft = await _get_draft(db, video_id)
    if draft is None or draft.payload is None:
        raise AppError(422, ErrorCode.HOME_CONTENT_INVALID, "该视频还没有草稿，无法发布")
    if draft.revision != expected_revision:
        raise _revision_conflict("内容已在别处修改，请刷新后重试")
    if draft.source_fingerprint != fingerprint:
        raise AppError(
            422,
            ErrorCode.HOME_CONTENT_SOURCE_CHANGED,
            "视频字幕已变更，请重新核对内容后再发布",
            detail=[_issue("source_fingerprint", "SOURCE_CHANGED", "草稿依据的字幕已变化").model_dump()],
        )
    payload = _parse_draft(draft.payload)
    issues = collect_issues(payload, subtitles, strict=True)
    if issues:
        raise AppError(
            422,
            ErrorCode.HOME_CONTENT_INVALID,
            "发布校验失败",
            detail=[issue.model_dump() for issue in issues],
        )
    if not await _is_publicly_visible(db, video.id):
        raise AppError(
            422,
            ErrorCode.HOME_CONTENT_VIDEO_NOT_PUBLIC,
            "视频当前不满足公共可见条件，不能发布到首页（可先完成发布/上线）",
            detail=[_issue("video_id", "VIDEO_NOT_PUBLIC", "视频未公开或已下线").model_dump()],
        )

    # 草稿乐观锁的原子判定：条件 UPDATE（WHERE revision = expected_revision）。
    # 顺带把同一视频的并发发布串行化（行锁持有到提交），后面的版本号分配因此
    # 不会撞唯一约束。revision 自赋值 = 不改草稿内容，只做判定 + 取行锁；
    # updated_at 显式写出（该列有 onupdate 默认值）。
    await _cas_update(
        db,
        update(HomeContentDraft)
        .where(
            HomeContentDraft.id == draft.id,
            HomeContentDraft.revision == expected_revision,
        )
        .values(revision=expected_revision, updated_at=_now()),
        "内容已在别处修改，请刷新后重试",
    )
    revision = await _allocate_revision(
        db,
        video_id=video.id,
        payload=payload,
        fingerprint=fingerprint,
        draft=draft,
        actor_id=actor_id,
    )

    layout_revision: int | None = None
    if place in ("lead", "secondary"):
        layout_revision = await _place_content(  # type: ignore[arg-type]
            db,
            revision,
            video.id,
            place,
            actor_id,
            expected_config_revision=expected_config_revision,
        )
    await db.commit()
    return {"revision_id": revision.id, "version": revision.version, "layout_revision": layout_revision}


async def _next_version(db: AsyncSession, video_id: str) -> int:
    """下一个可用版本号（同一视频从 1 递增）。"""
    latest_version = (
        await db.execute(
            select(HomeContentRevision.version)
            .where(HomeContentRevision.video_id == video_id)
            .order_by(HomeContentRevision.version.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return (latest_version or 0) + 1


async def _allocate_revision(
    db: AsyncSession,
    *,
    video_id: str,
    payload: HomeContentDraftSchema,
    fingerprint: str,
    draft: HomeContentDraft,
    actor_id: str | None,
) -> HomeContentRevision:
    """分配版本号并插入不可变版本（已发布版本只追加）。

    版本号取 ``max(version)+1``：没有行锁时两个并发发布会算到同一个号，撞唯一
    约束 ``(video_id, version)``。这里用 SAVEPOINT 包住 INSERT，撞了就重算重试；
    重试仍失败则 409——绝不把 ``IntegrityError`` 泄成 500 ``INTERNAL_ERROR``。
    """
    for _ in range(_VERSION_ALLOC_ATTEMPTS):
        revision = HomeContentRevision(
            video_id=video_id,
            version=await _next_version(db, video_id),
            payload=payload.model_dump(mode="json"),
            schema_version=CONTENT_SCHEMA_VERSION,
            source_fingerprint=fingerprint,
            generation_model=draft.generation_model,
            generation_prompt_version=draft.generation_prompt_version,
            generated_by=draft.generated_by,
            generated_at=draft.generated_at,
            published_by=actor_id,
            published_at=_now(),
        )
        try:
            async with db.begin_nested():
                db.add(revision)
                await db.flush()
            return revision
        except IntegrityError:
            if revision in db:  # SAVEPOINT 回滚后仍挂在 session 上的残留对象
                db.expunge(revision)
    raise _revision_conflict("发布冲突，请刷新后重试")


async def _revision_video_map(db: AsyncSession, revision_ids: Iterable[str]) -> dict[str, str]:
    ids = list(dict.fromkeys(revision_ids))
    if not ids:
        return {}
    rows = (
        await db.execute(
            select(HomeContentRevision.id, HomeContentRevision.video_id).where(HomeContentRevision.id.in_(ids))
        )
    ).all()
    return {row[0]: row[1] for row in rows}


def _layout_without_video(layout: dict, video_id: str, video_by_revision: dict[str, str]) -> dict:
    """去掉布局里属于 ``video_id`` 的位置（主次不重复），返回新 dict。"""
    cleaned = dict(layout)
    lead = cleaned.get("lead")
    if isinstance(lead, dict) and video_by_revision.get(lead.get("content_revision_id", "")) == video_id:
        cleaned["lead"] = None
    cleaned["secondary"] = [
        ref
        for ref in cleaned.get("secondary") or []
        if video_by_revision.get(ref.get("content_revision_id", "")) != video_id
    ]
    return cleaned


async def _place_content(
    db: AsyncSession,
    revision: HomeContentRevision,
    video_id: str,
    place: str,
    actor_id: str | None,
    *,
    expected_config_revision: int | None = None,
) -> int:
    """把已发布版本放进首页位置（主推/次推）。

    布局乐观锁：配置行也走条件 UPDATE（``WHERE revision = 读到的 revision``），
    与 :func:`publish_layout` 同一套标准——别人刚改过编排时返回 409，而不是
    静默覆盖别人的编排草稿。``expected_config_revision`` 由调用方在请求开始
    时取好（``publish_content``），这样「请求期间编排被改过」也能被发现。
    """
    config = await _get_or_create_config(db)
    expected_revision = config.revision if expected_config_revision is None else expected_config_revision
    published = config.published_layout or empty_layout()
    draft_layout = config.draft_layout or empty_layout()
    all_revision_ids = set(_layout_revision_ids(_parse_layout(published)))
    all_revision_ids.add(revision.id)
    video_by_revision = await _revision_video_map(db, all_revision_ids)
    video_by_revision[revision.id] = video_id

    published = _layout_without_video(published, video_id, video_by_revision)
    draft_layout = _layout_without_video(draft_layout, video_id, video_by_revision)
    if place == "lead":
        published["lead"] = {"content_revision_id": revision.id}
        draft_layout["lead"] = {"content_revision_id": revision.id}
    else:
        secondary = published.get("secondary") or []
        if len(secondary) >= MAX_SECONDARY:
            raise AppError(
                422,
                ErrorCode.HOME_CONTENT_LAYOUT_INVALID,
                f"次推位置已满（最多 {MAX_SECONDARY} 条），请先在首页编排里调整",
                detail=[_issue("secondary", "POSITION_FULL", "次推位置已满").model_dump()],
            )
        published["secondary"] = [*secondary, {"content_revision_id": revision.id}]
        draft_secondary = [ref for ref in (draft_layout.get("secondary") or [])]
        # 草稿布局与线上保持一致；替换/去重已在上面做过。
        draft_layout["secondary"] = [*draft_secondary, {"content_revision_id": revision.id}]
    now = _now()
    new_revision = expected_revision + 1
    await _cas_update(
        db,
        update(HomePageConfig)
        .where(
            HomePageConfig.id == LAYOUT_SINGLETON_ID,
            HomePageConfig.revision == expected_revision,
        )
        .values(
            previous_published_layout=config.published_layout,
            published_layout=published,
            draft_layout=draft_layout,
            revision=new_revision,
            published_revision=new_revision,
            updated_by=actor_id,
            updated_at=now,
            published_by=actor_id,
            published_at=now,
        ),
        "首页编排已在别处修改，请刷新后重试",
    )
    return new_revision


async def restore_draft(
    db: AsyncSession,
    video_id: str,
    revision_id: str,
    expected_revision: int,
    actor_id: str | None,
) -> HomeContentVideoState:
    """把指定历史版本复制为新草稿（不改变线上内容）。"""
    await _get_video(db, video_id)
    _, subtitles = await current_source_fingerprint(db, video_id)
    if not subtitles:
        raise AppError(422, ErrorCode.HOME_CONTENT_NO_SUBTITLES, "该视频没有字幕，无法制作首页内容")
    draft = await _get_or_create_draft(db, video_id)
    if draft.revision != expected_revision:
        raise _revision_conflict("内容已在别处修改，请刷新后重试")
    revision = (
        await db.execute(
            select(HomeContentRevision).where(
                HomeContentRevision.id == revision_id,
                HomeContentRevision.video_id == video_id,
            )
        )
    ).scalar_one_or_none()
    if revision is None:
        raise AppError(404, ErrorCode.NOT_FOUND, "指定的历史版本不存在")
    payload = _try_parse_draft(revision.payload)
    if payload is None:
        raise AppError(422, ErrorCode.HOME_CONTENT_INVALID, "该历史版本内容与当前结构不兼容，无法复制")
    # 乐观锁的原子判定：条件 UPDATE（WHERE revision = expected_revision）。
    await _cas_update(
        db,
        update(HomeContentDraft)
        .where(
            HomeContentDraft.id == draft.id,
            HomeContentDraft.revision == expected_revision,
        )
        .values(
            payload=revision.payload,
            schema_version=revision.schema_version or CONTENT_SCHEMA_VERSION,
            # 保留历史版本的来源指纹：字幕若已变化，后台会显示「来源已变更」并阻止发布，
            # 直到管理员重新核对保存或重新生成（任务文档 §8）。
            source_fingerprint=revision.source_fingerprint,
            revision=expected_revision + 1,
            updated_by=actor_id,
            updated_at=_now(),
        ),
        "内容已在别处修改，请刷新后重试",
    )
    await db.refresh(draft)
    await db.commit()
    return await get_video_state(db, video_id)


async def preview_video(db: AsyncSession, video_id: str) -> HomeLayoutPreview:
    """草稿预览：返回与公共接口同形的 page；issues 是发布会被拒绝的问题。"""
    video = await _get_video(db, video_id)
    _, subtitles = await current_source_fingerprint(db, video_id)
    draft = await _get_draft(db, video_id)
    payload = _try_parse_draft(draft.payload) if draft is not None else None
    if payload is None:
        return HomeLayoutPreview(
            page=None,
            issues=[_issue("payload", "DRAFT_EMPTY", "该视频还没有草稿，生成或手动保存后即可预览")],
        )
    issues = collect_issues(payload, subtitles, strict=True)
    cards, labels = await _video_cards(db, [video])
    content = _content_dto(
        payload=payload,
        revision_id=f"draft-{video.id}",
        video_id=video.id,
        version=0,
        published_at=None,
        source_label=labels.get(video.id),
        subtitles=subtitles,
    )
    expression_slot = None
    if content.expressions:
        expression_slot = HomeEditorialExpressionSlot(
            content_revision_id=content.content_revision_id,
            expression_id=content.expressions[0].id,
            headline=content.headline,
            topic_label=content.topic_label,
            video=cards[video.id],
            expression=content.expressions[0],
        )
    scenario_slots = [
        HomeEditorialScenarioSlot(
            content_revision_id=content.content_revision_id,
            scenario_id=scenario.id,
            video=cards[video.id],
            scenario=scenario,
        )
        for scenario in content.scenarios[:MAX_SCENARIOS]
    ]
    page = HomeEditorialPage(
        layout_revision=0,
        published_at=None,
        lead=HomeEditorialVideoSlot(content=content, video=cards[video.id]),
        secondary=[],
        expression=expression_slot,
        scenarios=scenario_slots,
    )
    return HomeLayoutPreview(page=page, issues=issues)


# ---------------------------------------------------------------------------
# 生成任务状态机（Celery 侧钩子；这些函数自己 commit）
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class GenerationClaim:
    """``claim_generation`` 的结果：要么新建任务，要么复用既有有效任务。"""

    generation_id: str
    video_id: str
    reused: bool
    draft_revision: int
    source_fingerprint: str


@dataclass(slots=True)
class GenerationContext:
    """worker 生成所需的一切；``subtitles`` 是按 sentence_index 排序的 ORM 行。"""

    generation_id: str
    video_id: str
    video_title: str
    draft_revision: int
    source_fingerprint: str
    subtitles: list[Subtitle] = field(default_factory=list)
    existing_payload: dict | None = None


async def claim_generation(
    db: AsyncSession,
    video_id: str,
    actor_id: str | None,
    *,
    expected_revision: int | None = None,
    overwrite: bool = False,
    model: str | None = None,
    prompt_version: str | None = None,
) -> GenerationClaim:
    """原子占位一个生成任务；有有效任务时返回 ``reused=True``（不重复计费）。

    - 乐观锁：传了 ``expected_revision`` 就必须等于当前草稿 revision（409）。
    - 已有草稿且未确认覆盖 → 409 HOME_CONTENT_OVERWRITE_CONFIRM（先保留旧内容）。
    - 卡死的 queued/running（超过 ``GENERATION_STALE_SECONDS``）先标 failed TIMEOUT
      再重新占位，任务不会永久卡在 generating。
    """
    from app.core.capabilities import require_content_production

    require_content_production(model=True)
    await _get_video(db, video_id)
    fingerprint, subtitles = await current_source_fingerprint(db, video_id)
    if not subtitles:
        raise AppError(422, ErrorCode.HOME_CONTENT_NO_SUBTITLES, "该视频没有字幕，无法生成首页内容")
    draft = await _get_or_create_draft(db, video_id)
    if expected_revision is not None and draft.revision != expected_revision:
        raise AppError(409, ErrorCode.HOME_CONTENT_REVISION_CONFLICT, "内容已在别处修改，请刷新后重试")

    if draft.active_generation_id:
        stale = _expire_stale_generation(draft)
        if not stale:
            if draft.generation_source_fingerprint is None:
                # 兼容历史行：没有指纹就按当前值补上，任务仍可继续。
                draft.generation_source_fingerprint = fingerprint
                draft.generation_draft_revision = draft.generation_draft_revision or draft.revision
                await db.commit()
            return GenerationClaim(
                generation_id=draft.active_generation_id,
                video_id=video_id,
                reused=True,
                draft_revision=draft.generation_draft_revision or draft.revision,
                source_fingerprint=draft.generation_source_fingerprint or fingerprint,
            )
        await db.commit()

    if draft.payload is not None and not overwrite:
        raise AppError(
            409,
            ErrorCode.HOME_CONTENT_OVERWRITE_CONFIRM,
            "该视频已有草稿，重新生成会覆盖现有内容；确认后请带 overwrite=true 重试",
            detail=[_issue("payload", "OVERWRITE_CONFIRM", "已有草稿，需要确认覆盖").model_dump()],
        )

    generation_id = str(uuid.uuid4())
    now = _now()
    values = {
        "active_generation_id": generation_id,
        "last_generation_id": generation_id,
        "status": HomeContentGenerationStatus.QUEUED,
        "generation_started_at": now,
        "generation_finished_at": None,
        "generation_error_code": None,
        "generation_error_message": None,
        "generation_draft_revision": draft.revision,
        "generation_source_fingerprint": fingerprint,
        "generation_model": model,
        "generation_prompt_version": prompt_version,
        "generation_usage": None,
        "generation_coverage": None,
        "generation_calls": 0,
        "generated_by": actor_id,
        "generated_at": now,
    }
    result = await db.execute(
        update(HomeContentDraft)
        .where(
            HomeContentDraft.video_id == video_id,
            HomeContentDraft.active_generation_id.is_(None),
        )
        .values(**values)
    )
    if result.rowcount == 0:
        # 并发落败：另一个请求刚占了位，按既有任务返回（不重复生成）。
        await db.rollback()
        current = await _get_draft(db, video_id)
        if current is not None and current.active_generation_id:
            return GenerationClaim(
                generation_id=current.active_generation_id,
                video_id=video_id,
                reused=True,
                draft_revision=current.generation_draft_revision or current.revision,
                source_fingerprint=current.generation_source_fingerprint or fingerprint,
            )
        raise AppError(409, ErrorCode.CONFLICT, "生成任务占位失败，请重试")
    # Core UPDATE 不经过 ORM，identity map 里还是旧值：commit 前刷新，避免调用方
    # 在同一 session 里读到 active_generation_id=None 的陈旧草稿。
    await db.refresh(draft)
    await db.commit()
    return GenerationClaim(
        generation_id=generation_id,
        video_id=video_id,
        reused=False,
        draft_revision=draft.revision,
        source_fingerprint=fingerprint,
    )


async def enqueue_generation(db: AsyncSession, claim: GenerationClaim) -> None:
    """把任务投到云端 Celery 队列；入队失败必须可见、可重试（503 + failed 状态）。"""
    from app.core.capabilities import require_content_production

    require_content_production(model=True)
    try:
        from app.tasks.home_content_tasks import generate_home_content_draft

        generate_home_content_draft.apply_async(args=[claim.generation_id], task_id=claim.generation_id)
    except Exception as exc:
        logger.warning("home_content enqueue failed generation=%s exc=%s", claim.generation_id, exc)
        await fail_generation(
            db,
            claim.generation_id,
            ErrorCode.HOME_CONTENT_ENQUEUE_FAILED,
            "生成任务入队失败，请稍后重试",
        )
        raise AppError(
            503,
            ErrorCode.HOME_CONTENT_ENQUEUE_FAILED,
            "生成任务入队失败，请稍后重试",
        ) from exc


async def load_generation_context(
    db: AsyncSession, generation_id: str, *, mark_running: bool = True
) -> GenerationContext | None:
    """worker 读取生成上下文；返回 None 表示该任务已被取代/取消，应直接退出。"""
    draft = (
        await db.execute(select(HomeContentDraft).where(HomeContentDraft.active_generation_id == generation_id))
    ).scalar_one_or_none()
    if draft is None:
        return None
    video = (await db.execute(select(Video).where(Video.id == draft.video_id))).scalar_one_or_none()
    if video is None:
        await fail_generation(db, generation_id, ErrorCode.NOT_FOUND, "视频已不存在")
        return None
    subtitles = await _load_subtitles(db, draft.video_id)
    if mark_running and draft.status == HomeContentGenerationStatus.QUEUED:
        draft.status = HomeContentGenerationStatus.RUNNING
        await db.commit()
    return GenerationContext(
        generation_id=generation_id,
        video_id=video.id,
        video_title=video.title,
        draft_revision=draft.generation_draft_revision or draft.revision,
        source_fingerprint=draft.generation_source_fingerprint or compute_source_fingerprint(subtitles),
        subtitles=subtitles,
        existing_payload=draft.payload,
    )


async def complete_generation(
    db: AsyncSession,
    generation_id: str,
    payload: HomeContentDraftSchema | dict,
    *,
    model: str | None = None,
    prompt_version: str | None = None,
    usage: dict | None = None,
    coverage: dict | None = None,
    calls: int = 0,
) -> bool:
    """worker 成功写回：三重断言（任务 ID / 草稿 revision / 来源指纹）后才替换 payload。

    写回是**条件 UPDATE**（``WHERE id AND active_generation_id AND revision``）：
    判定与写入在同一条语句里，管理员在本函数读到草稿之后、提交之前保存草稿，
    也不会被 AI 结果盖掉（rowcount == 0 → 判冲突）。

    返回 True = 已写回；False = 有冲突或输出非法，此时草稿已被标 failed 并保留旧
    内容（调用方不需要再调 ``fail_generation``）。绝不覆盖管理员的新修改。
    """
    draft = (
        await db.execute(select(HomeContentDraft).where(HomeContentDraft.active_generation_id == generation_id))
    ).scalar_one_or_none()
    if draft is None:
        return False
    try:
        parsed = _parse_draft(payload)
        issues = collect_issues(parsed, await _load_subtitles(db, draft.video_id), strict=True)
    except ValidationError as exc:
        message = "; ".join(
            f"{'.'.join(str(part) for part in error.get('loc', ()))}: {error.get('msg', 'invalid')}"
            for error in exc.errors()
        )
        await fail_generation(db, generation_id, ErrorCode.HOME_CONTENT_AI_INVALID, f"AI 输出结构非法：{message}")
        return False
    if issues:
        await fail_generation(
            db,
            generation_id,
            ErrorCode.HOME_CONTENT_AI_INVALID,
            "AI 输出未通过校验：" + issues[0].message,
        )
        return False

    fingerprint = compute_source_fingerprint(await _load_subtitles(db, draft.video_id))
    if draft.generation_draft_revision is not None and draft.revision != draft.generation_draft_revision:
        await fail_generation(
            db,
            generation_id,
            ErrorCode.HOME_CONTENT_CONFLICT,
            "生成期间草稿已被修改，结果未写回",
        )
        return False
    if draft.generation_source_fingerprint and fingerprint != draft.generation_source_fingerprint:
        await fail_generation(
            db,
            generation_id,
            ErrorCode.HOME_CONTENT_SOURCE_CHANGED,
            "生成期间视频字幕已变更，结果未写回",
        )
        return False

    now = _now()
    values: dict[str, object] = {
        "payload": parsed.model_dump(mode="json"),
        "schema_version": CONTENT_SCHEMA_VERSION,
        "revision": draft.revision + 1,
        "source_fingerprint": fingerprint,
        "status": HomeContentGenerationStatus.SUCCEEDED,
        "active_generation_id": None,
        "last_generation_id": generation_id,
        "generation_finished_at": now,
        "generation_error_code": None,
        "generation_error_message": None,
        "generation_usage": usage,
        "generation_coverage": coverage,
        "generation_calls": max(int(calls or 0), 0),
        "updated_by": draft.generated_by,
        "updated_at": now,
    }
    if model is not None:
        values["generation_model"] = model
    if prompt_version is not None:
        values["generation_prompt_version"] = prompt_version
    # 写回用**条件 UPDATE**：判定与写入是同一条语句，SELECT 之后管理员再保存草稿
    # 也不会被覆盖（rowcount == 0 = 期间草稿变了 → 冲突）。这里校验的 revision 是
    # 本函数读到的那个快照值——它可能已经过期，正因如此才要把判定写进 WHERE。
    result = await db.execute(
        update(HomeContentDraft)
        .where(
            HomeContentDraft.id == draft.id,
            HomeContentDraft.active_generation_id == generation_id,
            HomeContentDraft.revision == draft.revision,
        )
        .values(**values)
    )
    if result.rowcount == 0:
        # 草稿在生成期间被改过：保留管理员的内容，把任务标成冲突失败。
        await db.rollback()
        await fail_generation(
            db,
            generation_id,
            ErrorCode.HOME_CONTENT_CONFLICT,
            "生成期间草稿已被修改，结果未写回",
        )
        return False
    await db.commit()
    return True


async def fail_generation(db: AsyncSession, generation_id: str, code: str, message: str) -> bool:
    """把当前任务标 failed（保留旧 payload / revision）；不是当前任务则返回 False。

    条件 UPDATE（``WHERE active_generation_id = generation_id``）：占位已经被
    换成新任务时，这一笔不会把新任务误标成失败。
    """
    result = await db.execute(
        update(HomeContentDraft)
        .where(HomeContentDraft.active_generation_id == generation_id)
        .values(
            status=HomeContentGenerationStatus.FAILED,
            last_generation_id=generation_id,
            active_generation_id=None,
            generation_error_code=(code or "UNKNOWN")[:40],
            generation_error_message=(message or "生成失败")[:500],
            generation_finished_at=_now(),
        )
    )
    if result.rowcount == 0:
        return False
    await db.commit()
    return True


async def sweep_stale_generations(db: AsyncSession | None = None) -> int:
    """巡检兜底：把超过 ``GENERATION_STALE_SECONDS`` 的 queued/running 标 failed TIMEOUT。

    Celery beat 调用时不传 ``db``（自己开 session）；返回处理条数。
    """
    if db is None:
        from app.core.database import get_async_session_maker

        maker = get_async_session_maker()
        async with maker() as session:
            return await sweep_stale_generations(session)
    drafts = (
        (
            await db.execute(
                select(HomeContentDraft).where(HomeContentDraft.status.in_(list(HomeContentGenerationStatus.ACTIVE)))
            )
        )
        .scalars()
        .all()
    )
    swept = 0
    for draft in drafts:
        if _expire_stale_generation(draft):
            swept += 1
    if swept:
        await db.commit()
    return swept


__all__ = [
    "CONTENT_SCHEMA_VERSION",
    "GENERATION_STALE_SECONDS",
    "LAYOUT_SINGLETON_ID",
    "GenerationClaim",
    "GenerationContext",
    "claim_generation",
    "collect_issues",
    "complete_generation",
    "compute_source_fingerprint",
    "current_source_fingerprint",
    "empty_layout",
    "enqueue_generation",
    "fail_generation",
    "get_generation_state",
    "get_layout_state",
    "get_video_state",
    "load_generation_context",
    "preview_layout",
    "preview_video",
    "publish_content",
    "publish_layout",
    "resolve_clip",
    "resolve_public_page",
    "resolve_sentences",
    "restore_draft",
    "rollback_layout",
    "save_draft",
    "save_layout_draft",
    "sweep_stale_generations",
]
