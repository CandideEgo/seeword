"""Shared read-only, permission-projected material discovery and fixed references.

The caller owns the transaction. Lesson locks precede revision reads and remain
held until that transaction ends, matching publication/withdrawal lock order.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.core.errors import AppError, ErrorCode
from app.models.lesson import Lesson, LessonRevision
from app.schemas.lesson_catalog import FixedReference, MaterialIdentity
from app.services import lessons
from app.services.learning_authorization import allowed_lesson_ids, require_lesson, required_uses
from app.services.teaching.principal import Principal, require_scope
from slcs import FINGERPRINT_VERSION, VideoLearningMaterial, resolve_anchor, resolve_vocabulary


def _invalid(message: str) -> AppError:
    return AppError(422, ErrorCode.VALIDATION_ERROR, message)


def _missing() -> AppError:
    return AppError(404, ErrorCode.NOT_FOUND, "学习资源不存在或未获授权")


def _page(offset: int, limit: int) -> None:
    if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 100:
        raise _invalid("分页需要非负 offset 和 1–100 的 limit")


def _query(value: str, *, nonempty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > 200 or "\x00" in value:
        raise _invalid("查询必须为不超过 200 字符的文本")
    result = value.strip().casefold()
    if nonempty and not result:
        raise _invalid("词条不能为空")
    return result


def _summary(revision: LessonRevision) -> dict:
    return {
        "lesson_id": revision.lesson_id,
        "revision_id": revision.id,
        "title": revision.title,
        "fingerprint_version": revision.fingerprint_version,
        "fingerprint": revision.fingerprint,
    }


def _uses_allowed(revision: LessonRevision, principal: Principal, *, model: bool) -> bool:
    uses = (revision.review or {}).get("uses", {})
    return revision.status == "published" and all(
        uses.get(use, {}).get("approved") is True for use in required_uses(principal, model=model)
    )


async def _current_revisions(
    db: AsyncSession, principal: Principal, *, model: bool, with_pack: bool, delegable_only: bool = False
) -> list[LessonRevision]:
    require_scope(principal, "materials:read")
    required_uses(principal, model=model)
    await lessons.require_lessons_ready(db)
    allowed = allowed_lesson_ids(principal)
    if allowed is not None and not allowed:
        return []
    query = select(Lesson).order_by(Lesson.id).with_for_update(read=True)
    if allowed is not None:
        query = query.where(Lesson.id.in_(allowed))
    # Lock in the same stable order for every search. Never lock a revision and
    # then its Lesson: publication takes the Lesson first. Do not LIMIT this
    # scan, since permissions and word matches must precede counts/pagination.
    catalog = list(await db.scalars(query.execution_options(populate_existing=True)))
    revision_ids = [lesson.current_revision_id for lesson in catalog if lesson.current_revision_id is not None]
    if not revision_ids:
        return []
    revisions = select(LessonRevision).where(LessonRevision.id.in_(revision_ids)).order_by(LessonRevision.lesson_id)
    if not with_pack:
        revisions = revisions.options(defer(LessonRevision.pack))
    result = await db.scalars(revisions.execution_options(populate_existing=True))
    current = {lesson.id: lesson.current_revision_id for lesson in catalog}
    return [
        revision
        for revision in result
        if current.get(revision.lesson_id) == revision.id
        and revision.fingerprint_version == FINGERPRINT_VERSION
        and _uses_allowed(revision, principal, model=model)
        and (
            not delegable_only
            or (revision.review or {}).get("uses", {}).get("external_redistribution", {}).get("approved") is True
        )
    ]


async def search_materials(
    db: AsyncSession,
    principal: Principal,
    q: str = "",
    *,
    offset: int = 0,
    limit: int = 20,
    model: bool = False,
    delegable_only: bool = False,
) -> dict:
    """Casefolded title/ID search; the AI picker additionally requires both disclosure uses."""
    _page(offset, limit)
    query = _query(q)
    revisions = await _current_revisions(
        db, principal, model=model or delegable_only, with_pack=False, delegable_only=delegable_only
    )
    items = [
        _summary(revision)
        for revision in revisions
        if query in revision.title.casefold() or query in revision.lesson_id.casefold()
    ]
    return {"items": items[offset : offset + limit], "total": len(items), "offset": offset, "limit": limit}


def _reference(revision: LessonRevision, segment_id: str, token_ids: list[str]) -> dict:
    return FixedReference(
        **{key: value for key, value in _summary(revision).items() if key != "title"},
        segment_id=segment_id,
        token_ids=token_ids,
    ).model_dump()


async def search_occurrences(
    db: AsyncSession,
    principal: Principal,
    headword: str,
    *,
    offset: int = 0,
    limit: int = 20,
    model: bool = False,
) -> dict:
    """Exact strip+casefold headword/phrase matches, in lesson then pack order."""
    _page(offset, limit)
    query = _query(headword, nonempty=True)
    revisions = await _current_revisions(db, principal, model=model, with_pack=True)
    items = []
    for revision in revisions:
        material = _material(revision)
        segments = {segment.id: segment for segment in material.segments}
        for occurrence in resolve_vocabulary(material, query):
            segment = segments[occurrence.segment_id]
            items.append(
                {
                    "reference": _reference(revision, segment.id, list(occurrence.token_ids)),
                    "title": revision.title,
                    "headword": occurrence.headword,
                    "gloss": occurrence.gloss,
                    "text": occurrence.text,
                    "sentence": segment.text,
                    "translation": segment.translation,
                    "start_ms": occurrence.start_ms,
                    "end_ms": occurrence.end_ms,
                }
            )
    return {"items": items[offset : offset + limit], "total": len(items), "offset": offset, "limit": limit}


async def _fixed_revision(
    db: AsyncSession, principal: Principal, identity: MaterialIdentity, *, model: bool
) -> tuple[LessonRevision, Lesson]:
    require_lesson(principal, identity.lesson_id)
    required_uses(principal, model=model)
    await lessons.require_lessons_ready(db)
    if identity.fingerprint_version != FINGERPRINT_VERSION:
        raise _invalid("不支持的课程指纹版本")
    lesson = await db.get(Lesson, identity.lesson_id, with_for_update={"read": True}, populate_existing=True)
    if lesson is None:
        raise _missing()
    revision_id = identity.revision_id
    if revision_id is None:
        revision_id = await db.scalar(
            select(LessonRevision.id).where(
                LessonRevision.lesson_id == identity.lesson_id,
                LessonRevision.fingerprint_version == identity.fingerprint_version,
                LessonRevision.fingerprint == identity.fingerprint,
            )
        )
        if revision_id is None:
            raise _missing()
    # Reuse the established candidate/withdrawal/use error contract, but always
    # pass a fixed revision ID: this path must never resolve "current" instead.
    revision = await lessons.get_visible_revision(db, identity.lesson_id, revision_id)
    if not _uses_allowed(revision, principal, model=model):
        raise AppError(403, ErrorCode.LESSON_USE_NOT_ALLOWED, "课程材料未获准用于此用途")
    if (revision.fingerprint_version, revision.fingerprint) != (identity.fingerprint_version, identity.fingerprint):
        raise AppError(409, ErrorCode.CONTENT_REVISION_MISMATCH, "修订 ID 与固定课程指纹不一致")
    return revision, lesson


def _material(revision: LessonRevision) -> VideoLearningMaterial:
    material = lessons.material_for_revision(revision)
    if material.lesson_id != revision.lesson_id or material.source_fingerprint != revision.fingerprint:
        raise AppError(409, ErrorCode.CONTENT_REVISION_MISMATCH, "课程包身份与修订记录不一致")
    return material


async def resolve_reference(
    db: AsyncSession, principal: Principal, reference: FixedReference, *, model: bool = False
) -> dict:
    """Resolve only the named immutable pack and consecutive, text-ordered tokens."""
    revision, _ = await _fixed_revision(db, principal, reference, model=model)
    material = _material(revision)
    segment = next((segment for segment in material.segments if segment.id == reference.segment_id), None)
    if segment is None:
        raise _invalid("固定引用的段锚点不存在")
    try:
        text, start_ms, end_ms = resolve_anchor(segment, reference.token_ids)
    except ValueError:
        raise _invalid("固定引用的词锚点不存在、不连续或顺序不匹配") from None
    return {
        "reference": _reference(revision, segment.id, reference.token_ids),
        "title": revision.title,
        "text": text,
        "sentence": segment.text,
        "translation": segment.translation,
        "start_ms": start_ms,
        "end_ms": end_ms,
        "vocabulary": [
            {"headword": entry.headword, "gloss": entry.gloss}
            for entry in material.vocabulary
            if entry.segment_id == segment.id and list(entry.token_ids) == reference.token_ids
        ],
    }


async def get_context(
    db: AsyncSession, principal: Principal, reference: FixedReference, *, model: bool = False
) -> dict:
    """Return the requested sentence only, never implicitly disclose neighbours."""
    return await resolve_reference(db, principal, reference, model=model)


async def get_state(db: AsyncSession, principal: Principal, identity: MaterialIdentity, *, model: bool = False) -> dict:
    """Revalidate a fixed identity without returning any pack text or title."""
    revision, lesson = await _fixed_revision(db, principal, identity, model=model)
    return {
        "lesson_id": revision.lesson_id,
        "revision_id": revision.id,
        "fingerprint_version": revision.fingerprint_version,
        "fingerprint": revision.fingerprint,
        "available": True,
        "current": lesson.current_revision_id == revision.id,
    }
