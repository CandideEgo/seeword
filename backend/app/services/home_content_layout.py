"""首页编排的布局读写与公共读取（A15 业务边界拆分）。

契约见 ``backend/app/schemas/home_content.py``。这一层管
「哪些内容版本放在哪四个位置」以及「线上首页现在长什么样」：

- ``HomePageConfig`` 单例行（draft / published / previous 三份布局）、版本号与 CAS；
- 布局字段级校验（``_validate_layout``）与展示页构造（``_build_page``）；
- 公共读取 ``resolve_public_page``——**不缓存**，每次读库，发布/下线立即生效；
- 布局引用的数据快照 ``_LayoutData``：revision / 公共视频 / 卡片 / 字幕 / 指纹。

内容是否成立（指纹、字段 issues）由 ``home_content_content`` 判定，这里只消费；
草稿与版本的写入仍在 ``home_content_service``。这条方向是单向的：布局依赖内容，
内容不依赖布局。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ErrorCode
from app.models.channel import Channel
from app.models.home_content import HomeContentRevision, HomePageConfig
from app.models.subtitle import Subtitle
from app.models.user import User
from app.models.video import Video
from app.schemas.home_content import (
    HomeContentCandidate,
    HomeContentRevisionSummary,
    HomeContentSlotPosition,
    HomeEditorialExpressionSlot,
    HomeEditorialPage,
    HomeEditorialScenarioSlot,
    HomeEditorialVideoSlot,
    HomeLayoutIssue,
    HomeLayoutPlacement,
    HomeLayoutPreview,
    HomeLayoutState,
)
from app.schemas.home_content import (
    HomeContentDraft as HomeContentDraftSchema,
)
from app.services.discovery_service import public_video_filters
from app.services.home_content_content import (
    _INSERT_ATTEMPTS,
    DEFAULT_SOURCE_LABEL,
    LAYOUT_SINGLETON_ID,
    MAX_SCENARIOS,
    MAX_SECONDARY,
    POSITION_ORDER,
    _cas_update,
    _content_dto,
    _iso,
    _issue,
    _now,
    _resolve_expressions,
    _resolve_scenarios,
    _revision_conflict,
    _try_parse_draft,
    compute_source_fingerprint,
    empty_layout,
)
from app.services.video_card import serialize_video_card

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.schemas.video import VideoResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 数据加载（管理员读取 / 公共读取共用）
# ---------------------------------------------------------------------------


async def _get_video(db: AsyncSession, video_id: str) -> Video:
    video = (await db.execute(select(Video).where(Video.id == video_id))).scalar_one_or_none()
    if video is None:
        raise AppError(404, ErrorCode.NOT_FOUND, "视频不存在")
    return video


async def _public_video_ids(db: AsyncSession, video_ids: Iterable[str]) -> set[str]:
    ids = list(dict.fromkeys(video_ids))
    if not ids:
        return set()
    result = await db.execute(select(Video.id).where(Video.id.in_(ids), *public_video_filters()))
    return set(result.scalars().all())


async def _is_publicly_visible(db: AsyncSession, video_id: str) -> bool:
    """复用 discovery_service.public_video_filters()（契约 §1.5，不另抄 SQL 条件）。"""
    return bool(await _public_video_ids(db, [video_id]))


async def _video_cards(db: AsyncSession, videos: Sequence[Video]) -> tuple[dict[str, VideoResponse], dict[str, str]]:
    """批量得到 (video_id → 卡片, video_id → 来源标签)。"""
    if not videos:
        return {}, {}
    # 惰性 import：channel_service 顶层 import 了 api.v1.browse。
    from app.services.channel_service import channel_slugs_for

    slug_map = await channel_slugs_for(db, videos)
    channel_ids = {video.channel_ref for video in videos if video.channel_ref}
    channel_names: dict[str, str] = {}
    if channel_ids:
        rows = (await db.execute(select(Channel.id, Channel.name).where(Channel.id.in_(channel_ids)))).all()
        channel_names = {row[0]: row[1] for row in rows}
    cards: dict[str, VideoResponse] = {}
    labels: dict[str, str] = {}
    for video in videos:
        cards[video.id] = serialize_video_card(
            video,
            scope="feed",
            channel_slug=slug_map.get(video.channel_ref) if video.channel_ref else None,
        )
        labels[video.id] = (channel_names.get(video.channel_ref) if video.channel_ref else None) or DEFAULT_SOURCE_LABEL
    return cards, labels


async def _subtitles_by_video(db: AsyncSession, video_ids: Iterable[str]) -> dict[str, list[Subtitle]]:
    ids = list(dict.fromkeys(video_ids))
    if not ids:
        return {}
    result = await db.execute(
        select(Subtitle)
        .where(Subtitle.video_id.in_(ids))
        .order_by(Subtitle.video_id, Subtitle.sentence_index, Subtitle.id)
    )
    grouped: dict[str, list[Subtitle]] = {video_id: [] for video_id in ids}
    for subtitle in result.scalars().all():
        grouped.setdefault(subtitle.video_id, []).append(subtitle)
    return grouped


def _layout_revision_ids(layout: HomeLayoutPlacement) -> list[str]:
    ids: list[str] = []
    if layout.lead is not None:
        ids.append(layout.lead.content_revision_id)
    ids.extend(ref.content_revision_id for ref in layout.secondary)
    if layout.expression is not None:
        ids.append(layout.expression.content_revision_id)
    ids.extend(ref.content_revision_id for ref in layout.scenarios)
    return list(dict.fromkeys(ids))


async def _load_layout_data(db: AsyncSession, layout: HomeLayoutPlacement) -> _LayoutData:
    revision_ids = _layout_revision_ids(layout)
    data = _LayoutData()
    if not revision_ids:
        return data
    revisions = (
        (await db.execute(select(HomeContentRevision).where(HomeContentRevision.id.in_(revision_ids)))).scalars().all()
    )
    data.revisions = {revision.id: revision for revision in revisions}
    video_ids = list(dict.fromkeys(revision.video_id for revision in revisions))
    public = await db.execute(select(Video).where(Video.id.in_(video_ids), *public_video_filters()))
    public_videos = list(public.scalars().all())
    data.public_videos = {video.id: video for video in public_videos}
    data.cards, data.labels = await _video_cards(db, public_videos)
    data.subtitles = await _subtitles_by_video(db, video_ids)
    data.fingerprints = {video_id: compute_source_fingerprint(subs) for video_id, subs in data.subtitles.items()}
    return data


class _LayoutData:
    """布局引用的数据快照（revision / 公共视频 / 卡片 / 字幕 / 指纹 / 来源标签）。"""

    __slots__ = ("cards", "fingerprints", "labels", "public_videos", "revisions", "subtitles")

    def __init__(self) -> None:
        self.revisions: dict[str, HomeContentRevision] = {}
        self.public_videos: dict[str, Video] = {}
        self.cards: dict[str, VideoResponse] = {}
        self.subtitles: dict[str, list[Subtitle]] = {}
        self.fingerprints: dict[str, str] = {}
        self.labels: dict[str, str] = {}

    def is_valid(self, revision: HomeContentRevision) -> bool:
        """来源指纹一致 + 视频当前公共可见（否则该版本暂时失效）。"""
        if revision.video_id not in self.public_videos:
            return False
        return self.fingerprints.get(revision.video_id) == revision.source_fingerprint

    def payload(self, revision: HomeContentRevision) -> HomeContentDraftSchema | None:
        return _try_parse_draft(revision.payload)


async def _get_config(db: AsyncSession) -> HomePageConfig | None:
    return (
        await db.execute(select(HomePageConfig).where(HomePageConfig.id == LAYOUT_SINGLETON_ID))
    ).scalar_one_or_none()


async def _get_or_create_config(db: AsyncSession) -> HomePageConfig:
    """取布局单例行；没有就建（``id='singleton'``，主键即天然去重）。

    并发建行撞主键时重读对方建好的行（同 :func:`_get_or_create_draft`）。
    """
    config = await _get_config(db)
    if config is not None:
        return config
    for _ in range(_INSERT_ATTEMPTS):
        candidate = HomePageConfig(id=LAYOUT_SINGLETON_ID, revision=0, draft_layout=empty_layout())
        try:
            async with db.begin_nested():
                db.add(candidate)
                await db.flush()
            return candidate
        except IntegrityError:
            if candidate in db:
                db.expunge(candidate)
            existing = await _get_config(db)
            if existing is not None:
                return existing
    raise AppError(409, ErrorCode.CONFLICT, "首页编排初始化冲突，请重试")


def _parse_layout(raw: object) -> HomeLayoutPlacement:
    if raw is None:
        return HomeLayoutPlacement()
    try:
        return HomeLayoutPlacement.model_validate(raw)
    except ValidationError:
        return HomeLayoutPlacement()


async def _positions_map(db: AsyncSession, layout: HomeLayoutPlacement | None) -> dict[str, list[str]]:
    """已发布布局里 revision_id → 位置列表（用于后台展示「当前在哪些位置」）。"""
    if layout is None:
        return {}
    positions: dict[str, list[str]] = {}

    def add(revision_id: str | None, position: HomeContentSlotPosition) -> None:
        if revision_id is None:
            return
        bucket = positions.setdefault(revision_id, [])
        if position not in bucket:
            bucket.append(position)

    if layout.lead is not None:
        add(layout.lead.content_revision_id, "lead")
    for secondary_ref in layout.secondary:
        add(secondary_ref.content_revision_id, "secondary")
    if layout.expression is not None:
        add(layout.expression.content_revision_id, "expression")
    for scenario_ref in layout.scenarios:
        add(scenario_ref.content_revision_id, "scenario")
    return positions


def _sorted_positions(positions: Iterable[str]) -> list[HomeContentSlotPosition]:
    known = [position for position in POSITION_ORDER if position in positions]
    return known  # type: ignore[return-value]


async def _user_names(db: AsyncSession, user_ids: Iterable[str | None]) -> dict[str, str]:
    ids = [user_id for user_id in dict.fromkeys(user_ids) if user_id]
    if not ids:
        return {}
    rows = (await db.execute(select(User.id, User.name).where(User.id.in_(ids)))).all()
    return {row[0]: row[1] for row in rows if row[0]}


async def _revision_summaries(
    db: AsyncSession,
    video: Video,
    fingerprint: str,
    position_map: dict[str, list[str]],
) -> list[HomeContentRevisionSummary]:
    revisions = (
        (
            await db.execute(
                select(HomeContentRevision)
                .where(HomeContentRevision.video_id == video.id)
                .order_by(HomeContentRevision.version.desc())
            )
        )
        .scalars()
        .all()
    )
    names = await _user_names(db, (revision.published_by for revision in revisions))
    summaries: list[HomeContentRevisionSummary] = []
    for revision in revisions:
        payload = _try_parse_draft(revision.payload)
        summaries.append(
            HomeContentRevisionSummary(
                id=revision.id,
                version=revision.version,
                headline=payload.headline if payload is not None else "",
                dek=payload.dek if payload is not None else "",
                published_at=_iso(revision.published_at),
                published_by_name=names.get(revision.published_by) if revision.published_by else None,
                source_changed=revision.source_fingerprint != fingerprint,
                positions=_sorted_positions(position_map.get(revision.id, [])),
                expression_ids=[expression.id for expression in payload.expressions] if payload else [],
                scenario_ids=[scenario.id for scenario in payload.scenarios] if payload else [],
            )
        )
    return summaries


# ---------------------------------------------------------------------------
# 管理员：首页布局
# ---------------------------------------------------------------------------


async def _validate_layout(db: AsyncSession, layout: HomeLayoutPlacement) -> list[HomeLayoutIssue]:
    """布局字段级校验：引用存在、来源未变、视频公共可见、主次不重复。"""
    revision_ids = _layout_revision_ids(layout)
    issues: list[HomeLayoutIssue] = []
    if not revision_ids:
        return issues
    data = await _load_layout_data(db, layout)
    video_ids = [revision.video_id for revision in data.revisions.values()]
    public_ids = await _public_video_ids(db, video_ids)

    def check(field_name: str, revision_id: str) -> HomeContentRevision | None:
        revision = data.revisions.get(revision_id)
        if revision is None:
            issues.append(_issue(field_name, "REVISION_NOT_FOUND", "引用的内容版本不存在"))
            return None
        if revision.video_id not in public_ids:
            issues.append(_issue(field_name, "VIDEO_NOT_PUBLIC", "视频当前不可公开展示（未公开或已下线）"))
            return revision
        if data.fingerprints.get(revision.video_id) != revision.source_fingerprint:
            issues.append(_issue(field_name, "SOURCE_CHANGED", "内容版本依据的字幕已变更，请重新核对后发布"))
        return revision

    lead_revision = None
    if layout.lead is not None:
        lead_revision = check("lead", layout.lead.content_revision_id)

    seen_videos: set[str] = set()
    if lead_revision is not None:
        seen_videos.add(lead_revision.video_id)
    for index, secondary_ref in enumerate(layout.secondary):
        field_name = f"secondary[{index}]"
        if index >= MAX_SECONDARY:
            issues.append(_issue(field_name, "TOO_MANY", f"次推最多 {MAX_SECONDARY} 条"))
            continue
        revision = check(field_name, secondary_ref.content_revision_id)
        if revision is None:
            continue
        if revision.video_id in seen_videos:
            issues.append(_issue(field_name, "DUPLICATE_VIDEO", "主推与次推不能是同一视频"))
            continue
        seen_videos.add(revision.video_id)

    if layout.expression is not None:
        expression_revision = check("expression", layout.expression.content_revision_id)
        if expression_revision is not None:
            expression_payload = data.payload(expression_revision)
            expression_ids = (
                {expression.id for expression in expression_payload.expressions} if expression_payload else set()
            )
            if layout.expression.expression_id not in expression_ids:
                issues.append(_issue("expression", "EXPRESSION_NOT_FOUND", "该内容版本里没有这条表达"))

    for index, scenario_ref in enumerate(layout.scenarios):
        field_name = f"scenarios[{index}]"
        if index >= MAX_SCENARIOS:
            issues.append(_issue(field_name, "TOO_MANY", f"场景最多 {MAX_SCENARIOS} 条"))
            continue
        revision = check(field_name, scenario_ref.content_revision_id)
        if revision is not None:
            scenario_payload = data.payload(revision)
            scenario_ids = {scenario.id for scenario in scenario_payload.scenarios} if scenario_payload else set()
            if scenario_ref.scenario_id not in scenario_ids:
                issues.append(_issue(field_name, "SCENARIO_NOT_FOUND", "该内容版本里没有这个场景"))
    return issues


async def _build_page(
    layout: HomeLayoutPlacement,
    data: _LayoutData,
    *,
    layout_revision: int,
    published_at: str | None,
) -> HomeEditorialPage | None:
    """按布局 + 数据快照构造展示页（主推缺失时次推可提升，全失效返回 None）。"""
    ordered_revisions: list[HomeContentRevision] = []
    seen_videos: set[str] = set()
    candidates = []
    if layout.lead is not None:
        candidates.append(layout.lead.content_revision_id)
    candidates.extend(ref.content_revision_id for ref in layout.secondary)
    for revision_id in candidates:
        revision = data.revisions.get(revision_id)
        if revision is None or not data.is_valid(revision):
            continue
        if revision.video_id in seen_videos:
            continue
        if data.payload(revision) is None:
            continue
        seen_videos.add(revision.video_id)
        ordered_revisions.append(revision)
    if not ordered_revisions:
        return None

    def video_slot(revision: HomeContentRevision) -> HomeEditorialVideoSlot | None:
        video = data.public_videos.get(revision.video_id)
        card = data.cards.get(revision.video_id)
        payload = data.payload(revision)
        if video is None or card is None or payload is None:
            return None
        content = _content_dto(
            payload=payload,
            revision_id=revision.id,
            video_id=revision.video_id,
            version=revision.version,
            published_at=_iso(revision.published_at),
            source_label=data.labels.get(revision.video_id),
            subtitles=data.subtitles.get(revision.video_id, []),
        )
        return HomeEditorialVideoSlot(content=content, video=card)

    lead_slot = video_slot(ordered_revisions[0])
    if lead_slot is None:
        return None
    secondary_slots: list[HomeEditorialVideoSlot] = []
    for revision in ordered_revisions[1 : 1 + MAX_SECONDARY]:
        slot = video_slot(revision)
        if slot is not None:
            secondary_slots.append(slot)

    expression_slot = None
    if layout.expression is not None:
        expression_revision = data.revisions.get(layout.expression.content_revision_id)
        if expression_revision is not None and data.is_valid(expression_revision):
            expression_payload = data.payload(expression_revision)
            expression_card = data.cards.get(expression_revision.video_id)
            if expression_payload is not None and expression_card is not None:
                expression = next(
                    (
                        item
                        for item in _resolve_expressions(
                            expression_payload, data.subtitles.get(expression_revision.video_id, [])
                        )
                        if item.id == layout.expression.expression_id
                    ),
                    None,
                )
                if expression is not None:
                    expression_slot = HomeEditorialExpressionSlot(
                        content_revision_id=expression_revision.id,
                        expression_id=expression.id,
                        headline=expression_payload.headline,
                        topic_label=expression_payload.topic_label,
                        video=expression_card,
                        expression=expression,
                    )

    scenario_slots: list[HomeEditorialScenarioSlot] = []
    for scenario_ref in layout.scenarios:
        if len(scenario_slots) >= MAX_SCENARIOS:
            break
        scenario_revision = data.revisions.get(scenario_ref.content_revision_id)
        if scenario_revision is None or not data.is_valid(scenario_revision):
            continue
        scenario_payload = data.payload(scenario_revision)
        scenario_card = data.cards.get(scenario_revision.video_id)
        if scenario_payload is None or scenario_card is None:
            continue
        scenario = next(
            (
                item
                for item in _resolve_scenarios(scenario_payload, data.subtitles.get(scenario_revision.video_id, []))
                if item.id == scenario_ref.scenario_id
            ),
            None,
        )
        if scenario is None:
            continue
        scenario_slots.append(
            HomeEditorialScenarioSlot(
                content_revision_id=scenario_revision.id,
                scenario_id=scenario.id,
                video=scenario_card,
                scenario=scenario,
            )
        )

    return HomeEditorialPage(
        layout_revision=layout_revision,
        published_at=published_at,
        lead=lead_slot,
        secondary=secondary_slots,
        expression=expression_slot,
        scenarios=scenario_slots,
    )


async def resolve_public_page(db: AsyncSession) -> HomeEditorialPage | None:
    """公共读取：每次读库、不缓存；无有效主推时返回 None（首页走旧兜底）。"""
    config = await _get_config(db)
    if config is None:
        return None
    layout = _parse_layout(config.published_layout)
    if layout.lead is None:
        return None
    data = await _load_layout_data(db, layout)
    return await _build_page(
        layout,
        data,
        layout_revision=config.published_revision or config.revision,
        published_at=_iso(config.published_at),
    )


async def _candidate_pool(db: AsyncSession, position_map: dict[str, list[str]]) -> list[HomeContentCandidate]:
    revisions = (
        (
            await db.execute(
                select(HomeContentRevision).order_by(
                    HomeContentRevision.published_at.desc(), HomeContentRevision.version.desc()
                )
            )
        )
        .scalars()
        .all()
    )
    if not revisions:
        return []
    video_ids = list(dict.fromkeys(revision.video_id for revision in revisions))
    videos = (await db.execute(select(Video).where(Video.id.in_(video_ids)))).scalars().all()
    video_map = {video.id: video for video in videos}
    public_ids = await _public_video_ids(db, video_ids)
    subtitles = await _subtitles_by_video(db, video_ids)
    fingerprints = {video_id: compute_source_fingerprint(subs) for video_id, subs in subtitles.items()}
    candidates: list[HomeContentCandidate] = []
    for revision in revisions:
        video = video_map.get(revision.video_id)
        payload = _try_parse_draft(revision.payload)
        candidates.append(
            HomeContentCandidate(
                content_revision_id=revision.id,
                video_id=revision.video_id,
                video_title=video.title if video is not None else "",
                thumbnail_url=video.thumbnail_url if video is not None else None,
                duration=video.duration if video is not None else None,
                difficulty_level=video.difficulty_level if video is not None else None,
                topic_label=payload.topic_label if payload is not None else None,
                headline=payload.headline if payload is not None else "",
                dek=payload.dek if payload is not None else "",
                published_at=_iso(revision.published_at),
                source_changed=fingerprints.get(revision.video_id) != revision.source_fingerprint,
                publicly_visible=revision.video_id in public_ids,
                expression_ids=[expression.id for expression in payload.expressions] if payload else [],
                scenario_ids=[scenario.id for scenario in payload.scenarios] if payload else [],
                positions=_sorted_positions(position_map.get(revision.id, [])),
            )
        )
    return candidates


async def get_layout_state(db: AsyncSession) -> HomeLayoutState:
    config = await _get_config(db)
    draft_layout = _parse_layout(config.draft_layout) if config is not None else HomeLayoutPlacement()
    # 未发布/无上一版时必须是 None（TS 契约 HomeLayoutState.published_layout 可空），
    # 不能把 None 摊平成空布局——否则前端无法区分「空编排」与「从未发布」。
    published_layout = (
        _parse_layout(config.published_layout) if config is not None and config.published_layout is not None else None
    )
    previous_layout = (
        _parse_layout(config.previous_published_layout)
        if config is not None and config.previous_published_layout is not None
        else None
    )
    position_map = await _positions_map(db, published_layout)
    issues = await _validate_layout(db, draft_layout)
    page = None
    if published_layout is not None and published_layout.lead is not None:
        data = await _load_layout_data(db, published_layout)
        page = await _build_page(
            published_layout,
            data,
            layout_revision=0,
            published_at=None,
        )
    return HomeLayoutState(
        draft_layout=draft_layout,
        published_layout=published_layout,
        previous_published_layout=previous_layout,
        revision=config.revision if config is not None else 0,
        published_revision=config.published_revision if config is not None else None,
        published_active=page is not None,
        updated_at=_iso(config.updated_at) if config is not None else None,
        published_at=_iso(config.published_at) if config is not None else None,
        candidates=await _candidate_pool(db, position_map),
        issues=issues,
    )


async def save_layout_draft(
    db: AsyncSession,
    layout: HomeLayoutPlacement,
    expected_revision: int,
    actor_id: str | None,
) -> HomeLayoutState:
    """保存布局草稿（乐观锁）。允许保存「还没排好」的草稿，问题在发布时拦截。"""
    config = await _get_or_create_config(db)
    if config.revision != expected_revision:
        raise _revision_conflict("布局已在别处修改，请刷新后重试")
    # 乐观锁的原子判定：条件 UPDATE（WHERE revision = expected_revision）。
    await _cas_update(
        db,
        update(HomePageConfig)
        .where(
            HomePageConfig.id == LAYOUT_SINGLETON_ID,
            HomePageConfig.revision == expected_revision,
        )
        .values(
            draft_layout=layout.model_dump(mode="json"),
            revision=expected_revision + 1,
            updated_by=actor_id,
            updated_at=_now(),
        ),
        "布局已在别处修改，请刷新后重试",
    )
    await db.refresh(config)
    await db.commit()
    return await get_layout_state(db)


async def publish_layout(db: AsyncSession, expected_revision: int, actor_id: str | None) -> dict:
    """校验并原子发布整版布局（不暴露半套内容）。"""
    config = await _get_or_create_config(db)
    if config.revision != expected_revision:
        raise _revision_conflict("布局已在别处修改，请刷新后重试")
    layout = _parse_layout(config.draft_layout)
    issues = await _validate_layout(db, layout)
    if issues:
        raise AppError(
            422,
            ErrorCode.HOME_CONTENT_LAYOUT_INVALID,
            "布局校验失败",
            detail=[issue.model_dump() for issue in issues],
        )
    now = _now()
    new_revision = expected_revision + 1
    # 乐观锁的原子判定：条件 UPDATE（WHERE revision = expected_revision）。
    await _cas_update(
        db,
        update(HomePageConfig)
        .where(
            HomePageConfig.id == LAYOUT_SINGLETON_ID,
            HomePageConfig.revision == expected_revision,
        )
        .values(
            previous_published_layout=config.published_layout,
            published_layout=layout.model_dump(mode="json"),
            revision=new_revision,
            published_revision=new_revision,
            published_by=actor_id,
            published_at=now,
            updated_by=actor_id,
            updated_at=now,
        ),
        "布局已在别处修改，请刷新后重试",
    )
    await db.refresh(config)
    await db.commit()
    return {"layout_revision": new_revision}


async def rollback_layout(db: AsyncSession, expected_revision: int, actor_id: str | None) -> dict:
    """恢复上一发布布局。

    - ``previous_published_layout`` 为 null = 「没有上一版」，不是「上一版已失效」：
      允许原子地清空发布布局、回到旧首页兜底（``published_layout=null``），并把当前
      发布布局存进 previous 以便再次「前进」。返回 ``cleared=true``。
    - 有上一版时重新检查来源与可见性；引用已失效则 409 拒绝，不暴露半套内容。
    """
    config = await _get_or_create_config(db)
    if config.revision != expected_revision:
        raise _revision_conflict("布局已在别处修改，请刷新后重试")

    if config.previous_published_layout is None:
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
                published_layout=None,
                revision=new_revision,
                published_revision=new_revision,
                published_by=actor_id,
                published_at=now,
                updated_by=actor_id,
                updated_at=now,
            ),
            "布局已在别处修改，请刷新后重试",
        )
        await db.refresh(config)
        await db.commit()
        return {"layout_revision": new_revision, "cleared": True}

    previous = _parse_layout(config.previous_published_layout)
    issues = await _validate_layout(db, previous)
    if issues:
        raise AppError(
            409,
            ErrorCode.HOME_CONTENT_ROLLBACK_INVALID,
            "上一版布局已不可恢复：内容来源或视频可见性发生变化，请重新编排",
            detail=[issue.model_dump() for issue in issues],
        )
    now = _now()
    new_revision = expected_revision + 1
    # 乐观锁的原子判定：条件 UPDATE（WHERE revision = expected_revision）。
    await _cas_update(
        db,
        update(HomePageConfig)
        .where(
            HomePageConfig.id == LAYOUT_SINGLETON_ID,
            HomePageConfig.revision == expected_revision,
        )
        .values(
            previous_published_layout=config.published_layout,
            published_layout=previous.model_dump(mode="json"),
            revision=new_revision,
            published_revision=new_revision,
            published_by=actor_id,
            published_at=now,
            updated_by=actor_id,
            updated_at=now,
        ),
        "布局已在别处修改，请刷新后重试",
    )
    await db.refresh(config)
    await db.commit()
    return {"layout_revision": new_revision, "cleared": False}


async def preview_layout(db: AsyncSession) -> HomeLayoutPreview:
    """整版预览：用 draft_layout 尽力构造 page，issues 是发布会被拒绝的问题。"""
    config = await _get_config(db)
    layout = _parse_layout(config.draft_layout) if config is not None else HomeLayoutPlacement()
    issues = await _validate_layout(db, layout)
    data = await _load_layout_data(db, layout)
    page = await _build_page(layout, data, layout_revision=0, published_at=None)
    return HomeLayoutPreview(page=page, issues=issues)
