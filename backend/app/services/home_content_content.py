"""首页编辑内容的内容层——常量、来源指纹、字段校验与展示 DTO（A15 业务边界拆分）。

这是从 ``home_content_service`` 拆出的第一层：只读字幕与草稿 payload，回答两件事——
「这份内容现在是否还成立」（来源指纹、字段级 issues）与「它渲染成什么样」
（``_content_dto``）。它不碰布局、发布与生成状态机：那些留在
``home_content_service``，布局与公共读取在 ``home_content_layout``。

四条不变量里的第 3 条（来源指纹）在本模块实现；服务层与布局层都从这里取，
不各写一份。契约见 ``backend/app/schemas/home_content.py``。
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol

from pydantic import ValidationError
from sqlalchemy import Update, select

from app.core.errors import AppError, ErrorCode
from app.models.subtitle import Subtitle
from app.schemas.home_content import (
    HomeContentDraft as HomeContentDraftSchema,
)
from app.schemas.home_content import (
    HomeContentSlotPosition,
    HomeEditorialClip,
    HomeEditorialContent,
    HomeEditorialExpression,
    HomeEditorialInteraction,
    HomeEditorialInteractionOption,
    HomeEditorialScenario,
    HomeEditorialSentence,
    HomeLayoutIssue,
)
from app.services import ecdict

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    class SubtitleLike(Protocol):
        """``collect_issues`` 需要的最小字幕形状（ORM ``Subtitle`` 与生成侧只读行都满足）。

        frozen dataclass 的属性是只读的，所以这里用只读 property 声明——否则生成侧
        的 ``SubtitleLine``（frozen dataclass）无法通过结构化类型检查。
        """

        @property
        def id(self) -> str: ...

        @property
        def sentence_index(self) -> int: ...

        @property
        def start_time(self) -> float: ...

        @property
        def end_time(self) -> float: ...

        @property
        def text_en(self) -> str: ...

        @property
        def text_zh(self) -> str | None: ...


logger = logging.getLogger(__name__)

#: queued/running 超过这个秒数视为卡死，标 failed TIMEOUT（可重试）。
GENERATION_STALE_SECONDS = 900
#: 布局单例行主键。
LAYOUT_SINGLETON_ID = "singleton"
#: 布局里最多几条次推。
MAX_SECONDARY = 2
#: 场景卡最多几条。
MAX_SCENARIOS = 3
#: 草稿/版本 payload 的 schema 版本。
CONTENT_SCHEMA_VERSION = 1
#: 发布时若没取到来源标签的缺省值。
DEFAULT_SOURCE_LABEL = "SeeWord"

#: 位置在展示顺序上的先后（用于把 revision 的多个位置稳定排序）。
POSITION_ORDER: tuple[HomeContentSlotPosition, ...] = ("lead", "secondary", "expression", "scenario")

#: 词边界匹配用的字符类：英文 + 数字 + 撇号/连字符都算词内字符。
_WORD_CHAR = "A-Za-z0-9'’"

#: 「先查后插」撞唯一约束时的重试次数（并发建草稿/建布局单例行）。
_INSERT_ATTEMPTS = 3
#: 版本号分配撞唯一约束时的重试次数（并发发布抢到同一个 version）。
_VERSION_ALLOC_ATTEMPTS = 3


def empty_layout() -> dict:
    """空布局常量（与契约 §2 一致）。"""
    return {"lead": None, "secondary": [], "expression": None, "scenarios": []}


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    """SQLite 读回的是 naive datetime，统一按 UTC 处理后再比较。"""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _issue(field_name: str, code: str, message: str) -> HomeLayoutIssue:
    return HomeLayoutIssue(field=field_name, code=code, message=message)


# ---------------------------------------------------------------------------
# 并发控制：乐观锁的统一出口
# ---------------------------------------------------------------------------
#
# 本模块所有「读-改-写」都走**条件 UPDATE + rowcount 判定**（和 ``claim_generation``
# 的生成占位去重同一套写法）：
#
# - 判定与写入是**同一条语句**，所以「读到旧值 → 校验通过 → 写回」之间不再有窗口；
#   两个管理员同时保存不可能都成功，后到的那个拿到 409，而不是静默覆盖对方。
# - 不用 ``SELECT ... FOR UPDATE``：本项目的默认测试库是内存 SQLite，``FOR UPDATE``
#   在那里被静默忽略（见 tests/conftest.py），条件 UPDATE 在两种库上都真的生效，
#   也更容易被测试钉住。
# - 不用「先 SELECT 再 UPDATE」的两段式：判定必须落在写入的那条语句上，否则
#   TOCTOU 窗口照旧存在。


def _revision_conflict(message: str) -> AppError:
    """乐观锁冲突 → 409 + ``HOME_CONTENT_REVISION_CONFLICT``（前端按 code 分支）。"""
    return AppError(409, ErrorCode.HOME_CONTENT_REVISION_CONFLICT, message)


async def _cas_update(db: AsyncSession, statement: Update, message: str) -> None:
    """执行条件 UPDATE；命中 0 行 = 期间被别处改过 → 409。

    冲突时**先回滚本次事务**再抛错：调用方可能已经写了别的行（例如发布路径上的
    版本插入），留着半套写入比直接失败更危险。
    """
    result = await db.execute(statement)
    if result.rowcount == 0:
        await db.rollback()
        raise _revision_conflict(message)


# ---------------------------------------------------------------------------
# 来源指纹
# ---------------------------------------------------------------------------


def compute_source_fingerprint(subtitles: Iterable[Subtitle]) -> str:
    """sha256(有序字幕 ID + sentence_index + 起止 3 位小数 + 中英文原文)。

    契约 §1.3：这个指纹是「内容版本仍然对得上字幕」的唯一判据。时间取 3 位
    小数是为了忽略浮点尾差（0.1ms 级的重新量化不应该让整个发布失效），同时保留
    所有影响引用正确性的信息。返回 64 位十六进制字符串。
    """
    ordered = sorted(subtitles, key=lambda item: (item.sentence_index, item.id))
    lines = [
        "|".join(
            (
                subtitle.id,
                str(subtitle.sentence_index),
                f"{float(subtitle.start_time):.3f}",
                f"{float(subtitle.end_time):.3f}",
                subtitle.text_en or "",
                subtitle.text_zh or "",
            )
        )
        for subtitle in ordered
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


async def _load_subtitles(db: AsyncSession, video_id: str) -> list[Subtitle]:
    result = await db.execute(
        select(Subtitle).where(Subtitle.video_id == video_id).order_by(Subtitle.sentence_index, Subtitle.id)
    )
    return list(result.scalars().all())


async def current_source_fingerprint(db: AsyncSession, video_id: str) -> tuple[str, list[Subtitle]]:
    """当前视频字幕指纹 + 有序字幕行（一次查询，调用方两样都要）。"""
    subtitles = await _load_subtitles(db, video_id)
    return compute_source_fingerprint(subtitles), subtitles


# ---------------------------------------------------------------------------
# 草稿结构 / 引用校验（草稿宽松、发布严格）
# ---------------------------------------------------------------------------


def _parse_draft(payload: object) -> HomeContentDraftSchema:
    """把 DB 里的 dict / 请求里的模型统一成 HomeContentDraft；非法抛 ValidationError。"""
    if isinstance(payload, HomeContentDraftSchema):
        return payload
    return HomeContentDraftSchema.model_validate(payload)


def _try_parse_draft(payload: object) -> HomeContentDraftSchema | None:
    """宽松解析：DB 里的历史 payload 若与当前 schema 不兼容，返回 None 而不是 500。"""
    if payload is None:
        return None
    try:
        return _parse_draft(payload)
    except ValidationError:
        return None


def _normalize_text(text: str) -> str:
    return " ".join(text.split())


def _phrase_present(phrase: str, text: str) -> bool:
    """大小写不敏感、按词边界判断 phrase 是否真实出现在字幕原文里。"""
    needle = re.escape(_normalize_text(phrase))
    if not needle:
        return False
    pattern = rf"(?<![{_WORD_CHAR}]){needle}(?![{_WORD_CHAR}])"
    return re.search(pattern, _normalize_text(text), re.IGNORECASE) is not None


def _word_of_phrase(word: str, phrase: str) -> bool:
    """``word`` 必须等于 phrase 本身，或是 phrase 里的单个词。"""
    word_norm = _normalize_text(word).lower()
    phrase_norm = _normalize_text(phrase).lower()
    if word_norm == phrase_norm:
        return True
    tokens = re.findall(rf"[{_WORD_CHAR}]+", phrase_norm)
    return word_norm in tokens


def collect_issues(
    payload: HomeContentDraftSchema | dict | None,
    subtitles: Sequence[SubtitleLike],
    strict: bool,
) -> list[HomeLayoutIssue]:
    """草稿/发布校验，返回字段级问题列表（空 = 通过）。

    ``strict=False``（保存草稿）：结构与长度已在 Pydantic 层校验；这里只查
    「引用是否真属于该视频、短语是否真在字幕里、片段顺序是否合法」。
    ``strict=True``（发布 / AI 写回）：额外要求 headline/dek 非空、clip 非空、
    1–3 条表达、互动 2–3 个选项。
    """
    if payload is None:
        if strict:
            return [_issue("payload", "REQUIRED", "尚未保存草稿内容")]
        return []
    if isinstance(payload, dict):
        try:
            draft = _parse_draft(payload)
        except ValidationError as exc:
            return [
                _issue(
                    ".".join(str(part) for part in error.get("loc", ())), "SCHEMA_INVALID", error.get("msg", "结构非法")
                )
                for error in exc.errors()
            ]
    else:
        draft = payload

    issues: list[HomeLayoutIssue] = []
    subtitle_map = {subtitle.id: subtitle for subtitle in subtitles}

    for index, subtitle_id in enumerate(draft.evidence_subtitle_ids):
        if subtitle_id not in subtitle_map:
            issues.append(_issue(f"evidence_subtitle_ids[{index}]", "SUBTITLE_NOT_IN_VIDEO", "引用的字幕不属于该视频"))

    if draft.clip is not None:
        start = subtitle_map.get(draft.clip.start_subtitle_id)
        end = subtitle_map.get(draft.clip.end_subtitle_id)
        if start is None or end is None:
            issues.append(_issue("clip", "SUBTITLE_NOT_IN_VIDEO", "片段起止字幕不属于该视频"))
        elif start.sentence_index > end.sentence_index or float(end.end_time) <= float(start.start_time):
            issues.append(
                _issue("clip", "CLIP_ORDER_INVALID", "片段起始句必须早于或等于结束句，且结束时间大于开始时间")
            )

    for index, expression in enumerate(draft.expressions):
        field_name = f"expressions[{index}]"
        subtitle = subtitle_map.get(expression.subtitle_id)
        if subtitle is None:
            issues.append(_issue(f"{field_name}.subtitle_id", "SUBTITLE_NOT_IN_VIDEO", "表达引用的字幕不属于该视频"))
            continue
        if not _phrase_present(expression.phrase, subtitle.text_en or ""):
            issues.append(_issue(f"{field_name}.phrase", "PHRASE_NOT_IN_SUBTITLE", "短语没有真实出现在该句字幕原文里"))
        if expression.word is not None and not _word_of_phrase(expression.word, expression.phrase):
            issues.append(
                _issue(f"{field_name}.word", "WORD_NOT_IN_PHRASE", "收词 word 必须是 phrase 的单个词或 phrase 本身")
            )

    if draft.interaction is not None:
        if strict and not 2 <= len(draft.interaction.options) <= 3:
            issues.append(_issue("interaction.options", "OPTIONS_COUNT", "互动需要 2–3 个选项"))
        if strict and not draft.interaction.question.strip():  # 已被 schema 保证，防御式保留
            issues.append(_issue("interaction.question", "REQUIRED", "互动问题不能为空"))

    for index, scenario in enumerate(draft.scenarios):
        if scenario.subtitle_id is not None and scenario.subtitle_id not in subtitle_map:
            issues.append(
                _issue(f"scenarios[{index}].subtitle_id", "SUBTITLE_NOT_IN_VIDEO", "场景锚定的字幕不属于该视频")
            )

    if strict:
        if not draft.headline.strip():
            issues.append(_issue("headline", "REQUIRED", "发布需要编辑标题"))
        if not draft.dek.strip():
            issues.append(_issue("dek", "REQUIRED", "发布需要推荐理由"))
        if draft.clip is None:
            issues.append(_issue("clip", "REQUIRED", "发布需要选择真实片段"))
        if not 1 <= len(draft.expressions) <= 3:
            issues.append(_issue("expressions", "REQUIRED", "发布需要 1–3 条表达"))
        if len(draft.scenarios) > MAX_SCENARIOS:
            issues.append(_issue("scenarios", "TOO_MANY", f"场景最多 {MAX_SCENARIOS} 条"))

    return issues


# ---------------------------------------------------------------------------
# 展示 DTO 解析（公共接口与后台预览共用）
# ---------------------------------------------------------------------------


def _sentence_dto(subtitle: Subtitle) -> HomeEditorialSentence:
    return HomeEditorialSentence(
        subtitle_id=subtitle.id,
        sentence_index=int(subtitle.sentence_index),
        text_en=subtitle.text_en or "",
        text_zh=subtitle.text_zh,
        start_time=float(subtitle.start_time),
        end_time=float(subtitle.end_time),
    )


def resolve_sentences(
    payload: HomeContentDraftSchema | dict | None, subtitles: Sequence[Subtitle]
) -> list[HomeEditorialSentence]:
    """该内容版本引用到的全部字幕：依据 + 片段范围 + 表达句 + 场景锚定句。"""
    draft = _try_parse_draft(payload) if not isinstance(payload, HomeContentDraftSchema) else payload
    subtitle_map = {subtitle.id: subtitle for subtitle in subtitles}
    wanted: set[str] = set()
    if draft is not None:
        wanted.update(draft.evidence_subtitle_ids)
        if draft.clip is not None:
            start = subtitle_map.get(draft.clip.start_subtitle_id)
            end = subtitle_map.get(draft.clip.end_subtitle_id)
            if start is not None and end is not None:
                low, high = sorted((start.sentence_index, end.sentence_index))
                wanted.update(subtitle.id for subtitle in subtitles if low <= subtitle.sentence_index <= high)
        wanted.update(expression.subtitle_id for expression in draft.expressions)
        wanted.update(scenario.subtitle_id for scenario in draft.scenarios if scenario.subtitle_id)
    selected = [subtitle for subtitle in subtitles if subtitle.id in wanted]
    selected.sort(key=lambda item: (item.sentence_index, item.id))
    return [_sentence_dto(subtitle) for subtitle in selected]


def resolve_clip(
    payload: HomeContentDraftSchema | dict | None, subtitles: Sequence[Subtitle]
) -> HomeEditorialClip | None:
    """按字幕 ID 解析片段时间；引用不合法（顺序/缺失）时返回 None。"""
    draft = _try_parse_draft(payload) if not isinstance(payload, HomeContentDraftSchema) else payload
    if draft is None or draft.clip is None:
        return None
    subtitle_map = {subtitle.id: subtitle for subtitle in subtitles}
    start = subtitle_map.get(draft.clip.start_subtitle_id)
    end = subtitle_map.get(draft.clip.end_subtitle_id)
    if start is None or end is None:
        return None
    if start.sentence_index > end.sentence_index or float(end.end_time) <= float(start.start_time):
        return None
    return HomeEditorialClip(
        start_subtitle_id=start.id,
        end_subtitle_id=end.id,
        start_time=float(start.start_time),
        end_time=float(end.end_time),
        duration=round(float(end.end_time) - float(start.start_time), 3),
    )


def _word_timing(words: Iterable[dict] | None, token: str) -> tuple[float | None, float | None]:
    """在 WhisperX 词级时间戳里找 ``token``；找不到返回 (None, None)（不显示「听这个词」）。"""
    if not words or not token:
        return None, None
    target = re.sub(rf"[^ {_WORD_CHAR}]", "", token.lower())
    for entry in words:
        if not isinstance(entry, dict):
            continue
        word = re.sub(rf"[^ {_WORD_CHAR}]", "", str(entry.get("word", "")).lower())
        if word and word == target:
            try:
                return float(entry["start"]), float(entry["end"])
            except (KeyError, TypeError, ValueError):
                return None, None
    return None, None


def _dictionary_fields(word: str | None) -> tuple[str | None, str | None]:
    """词典里的 (音标, 中文释义)；没有词典/查不到就 (None, None)，绝不伪造。"""
    if not word:
        return None, None
    entry = ecdict.lookup(word) if ecdict.is_available() else None
    if not entry:
        return None, None
    phonetic = entry.get("phonetic") or None
    translation = (entry.get("translation") or "").strip() or None
    return phonetic, translation


def _resolve_expressions(
    payload: HomeContentDraftSchema | dict | None, subtitles: Sequence[Subtitle]
) -> list[HomeEditorialExpression]:
    draft = _try_parse_draft(payload) if not isinstance(payload, HomeContentDraftSchema) else payload
    if draft is None:
        return []
    subtitle_map = {subtitle.id: subtitle for subtitle in subtitles}
    resolved: list[HomeEditorialExpression] = []
    for expression in draft.expressions:
        subtitle = subtitle_map.get(expression.subtitle_id)
        if subtitle is None:
            continue
        lookup_key = expression.word or (
            _normalize_text(expression.phrase) if " " not in _normalize_text(expression.phrase) else None
        )
        phonetic, dictionary_gloss = _dictionary_fields(lookup_key)
        word_start, word_end = _word_timing(subtitle.words, expression.word or expression.phrase)
        resolved.append(
            HomeEditorialExpression(
                id=expression.id,
                subtitle_id=expression.subtitle_id,
                phrase=expression.phrase,
                word=expression.word,
                gloss_zh=expression.gloss_zh or dictionary_gloss,
                note_zh=expression.note_zh,
                phonetic=phonetic,
                word_start_time=word_start,
                word_end_time=word_end,
                sentence=_sentence_dto(subtitle),
            )
        )
    return resolved


def _resolve_interaction(payload: HomeContentDraftSchema | dict | None) -> HomeEditorialInteraction | None:
    draft = _try_parse_draft(payload) if not isinstance(payload, HomeContentDraftSchema) else payload
    if draft is None or draft.interaction is None:
        return None
    return HomeEditorialInteraction(
        id=draft.interaction.id,
        question=draft.interaction.question,
        options=[
            HomeEditorialInteractionOption(id=option.id, label=option.label, feedback=option.feedback)
            for option in draft.interaction.options
        ],
    )


def _resolve_scenarios(
    payload: HomeContentDraftSchema | dict | None, subtitles: Sequence[Subtitle]
) -> list[HomeEditorialScenario]:
    draft = _try_parse_draft(payload) if not isinstance(payload, HomeContentDraftSchema) else payload
    if draft is None:
        return []
    subtitle_map = {subtitle.id: subtitle for subtitle in subtitles}
    resolved: list[HomeEditorialScenario] = []
    for scenario in draft.scenarios:
        anchor = subtitle_map.get(scenario.subtitle_id) if scenario.subtitle_id else None
        resolved.append(
            HomeEditorialScenario(
                id=scenario.id,
                situation_zh=scenario.situation_zh,
                prompt_zh=scenario.prompt_zh,
                reply_en=scenario.reply_en,
                reply_zh=scenario.reply_zh,
                sentence=_sentence_dto(anchor) if anchor is not None else None,
            )
        )
    return resolved


def _content_dto(
    *,
    payload: HomeContentDraftSchema,
    revision_id: str,
    video_id: str,
    version: int,
    published_at: str | None,
    source_label: str | None,
    subtitles: Sequence[Subtitle],
) -> HomeEditorialContent:
    return HomeEditorialContent(
        content_revision_id=revision_id,
        video_id=video_id,
        version=version,
        headline=payload.headline,
        dek=payload.dek,
        topic_label=payload.topic_label,
        source_label=source_label or DEFAULT_SOURCE_LABEL,
        published_at=published_at,
        clip=resolve_clip(payload, subtitles),
        expressions=_resolve_expressions(payload, subtitles),
        interaction=_resolve_interaction(payload),
        scenarios=_resolve_scenarios(payload, subtitles),
        sentences=resolve_sentences(payload, subtitles),
    )
