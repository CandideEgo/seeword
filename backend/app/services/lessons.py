"""Transactional publication and revision visibility for SLCS lessons."""

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.models.lesson import Lesson, LessonOperation, LessonRevision
from app.schemas.lesson import LessonUse, PublishLesson, ReviewLesson, WithdrawLesson
from app.services.lesson_receipts import verify_lesson_receipt
from app.services.v2_schema import has_tables
from slcs import FINGERPRINT_VERSION, PackValidationError, fingerprint, load_pack, load_video_material
from slcs.material import stable_hash

MAX_PACK_BYTES = 4 * 1024 * 1024
# What the catalog and a lesson page need. Phases 3 and 4 add their own tables
# and gate on them separately, so a site migrated only to the first lesson
# revision still serves lessons; the health monitor reports the rest as a
# partial migration.
LESSON_TABLES = ("lessons", "lesson_revisions", "lesson_operations", "lesson_progress", "lesson_activities")
LESSON_ALL_TABLES = (*LESSON_TABLES, "lesson_tutor_anchors", "lesson_vocabulary_sources", "vocabulary_review_log")
_INSERT = {"postgresql": pg_insert, "sqlite": sqlite_insert}


def insert_for(db: AsyncSession, model):
    return _INSERT[db.get_bind().dialect.name](model)


def lesson_router_enabled() -> bool:
    return get_settings().slcs_lessons_enabled


async def require_lessons_ready(db: AsyncSession) -> None:
    if not lesson_router_enabled() or not await has_tables(db, LESSON_TABLES):
        raise AppError(503, ErrorCode.SERVICE_UNAVAILABLE, "课程试点暂未开放")


def _not_found() -> AppError:
    return AppError(404, ErrorCode.NOT_FOUND, "课程修订不存在")


def _conflict(message: str) -> AppError:
    return AppError(409, ErrorCode.CONTENT_REVISION_MISMATCH, message)


def _pack_error(path: str, message: str) -> AppError:
    return AppError(422, ErrorCode.VALIDATION_ERROR, "学习包校验失败", [{"path": path, "message": message}])


def _use_allowed(revision: LessonRevision, use: LessonUse) -> bool:
    return bool(revision.review and revision.review["uses"][use]["approved"] is True)


def may_display_revision(revision: LessonRevision) -> bool:
    return revision.status == "published" and _use_allowed(revision, "site_display")


def material_for_revision(revision: LessonRevision):
    return load_video_material(json.dumps(revision.pack, ensure_ascii=False).encode("utf-8"))


async def get_visible_revision(
    db: AsyncSession,
    lesson_id: str,
    revision_id: str | None = None,
    *,
    use: LessonUse = "site_display",
    lock: bool = False,
) -> LessonRevision:
    if revision_id is None:
        revision_id = await db.scalar(select(Lesson.current_revision_id).where(Lesson.id == lesson_id))
        if revision_id is None:
            was_withdrawn = await db.scalar(
                select(LessonRevision.id)
                .where(LessonRevision.lesson_id == lesson_id, LessonRevision.status == "withdrawn")
                .limit(1)
            )
            if was_withdrawn:
                raise AppError(410, ErrorCode.LESSON_WITHDRAWN, "课程材料已撤回")
            raise _not_found()

    query = select(LessonRevision).where(LessonRevision.id == revision_id, LessonRevision.lesson_id == lesson_id)
    if lock:
        query = query.with_for_update(read=True)
    revision = await db.scalar(query.execution_options(populate_existing=True))
    if revision is None or revision.status == "candidate":
        raise _not_found()
    if revision.status == "withdrawn":
        raise AppError(410, ErrorCode.LESSON_WITHDRAWN, "课程材料已撤回")
    if not _use_allowed(revision, use):
        raise AppError(403, ErrorCode.LESSON_USE_NOT_ALLOWED, "课程材料未获准用于此用途")
    return revision


def _summary(revision: LessonRevision) -> dict:
    return {
        "lesson_id": revision.lesson_id,
        "revision_id": revision.id,
        "title": revision.title,
        "access_mode": revision.access_mode,
    }


def _fingerprint_fields(revision: LessonRevision) -> dict:
    return {"fingerprint": revision.fingerprint, "fingerprint_version": revision.fingerprint_version}


def public_detail(revision: LessonRevision) -> dict:
    settings = get_settings()
    return {
        **_summary(revision),
        **_fingerprint_fields(revision),
        "pack": revision.pack,
        "permissions": _permissions(revision, settings),
    }


def _permissions(revision: LessonRevision, settings) -> dict:
    return {
        "model_processing": _use_allowed(revision, "model_processing"),
        "tutor_enabled": settings.slcs_tutor_enabled and settings.teaching_streaming_enabled,
        "vocabulary_enabled": settings.slcs_vocabulary_enabled,
    }


def revision_state(revision: LessonRevision) -> dict:
    """Everything a reader needs to revalidate the pack it already holds.

    Polled by the lesson page, so it must stay small: no segments, no vocabulary.
    """
    return {
        **_summary(revision),
        **_fingerprint_fields(revision),
        "permissions": _permissions(revision, get_settings()),
    }


async def list_lessons(db: AsyncSession) -> list[dict]:
    revisions = await db.scalars(
        select(LessonRevision)
        .join(Lesson, Lesson.current_revision_id == LessonRevision.id)
        .where(LessonRevision.status == "published")
        .options(defer(LessonRevision.pack))
        .order_by(LessonRevision.title, LessonRevision.lesson_id)
    )
    return [_summary(revision) for revision in revisions if may_display_revision(revision)]


def _admin_summary(revision: LessonRevision) -> dict:
    return {
        **_summary(revision),
        **_fingerprint_fields(revision),
        "status": revision.status,
        "review": {**revision.review, "reviewer_id": revision.reviewer_id} if revision.review else None,
    }


def _admin_detail(revision: LessonRevision, *, replayed: bool = False) -> dict:
    # The pack stays readable for withdrawn revisions: the maintainer has to see
    # what was published before deciding to restore it, and the review page has
    # no other way to reach the content. Public routes never touch this dict.
    return {
        **_admin_summary(revision),
        "pack": revision.pack,
        "replayed": replayed,
    }


async def list_admin_lessons(db: AsyncSession) -> list[dict]:
    rows = await db.execute(
        select(Lesson, LessonRevision)
        .join(LessonRevision, LessonRevision.lesson_id == Lesson.id)
        .options(defer(LessonRevision.pack))
        .order_by(Lesson.id, LessonRevision.created_at.desc(), LessonRevision.id)
    )
    lessons: dict[str, dict] = {}
    for lesson, revision in rows:
        row = lessons.setdefault(
            lesson.id, {"lesson_id": lesson.id, "current_revision_id": lesson.current_revision_id, "revisions": []}
        )
        row["revisions"].append(_admin_summary(revision))
    return list(lessons.values())


async def _revision(db: AsyncSession, lesson_id: str, revision_id: str) -> LessonRevision:
    revision = await db.get(LessonRevision, revision_id, populate_existing=True)
    if revision is None or revision.lesson_id != lesson_id:
        raise _not_found()
    return revision


async def admin_detail(db: AsyncSession, lesson_id: str, revision_id: str) -> dict:
    return _admin_detail(await _revision(db, lesson_id, revision_id))


async def list_operations(db: AsyncSession, lesson_id: str, revision_id: str, *, offset: int, limit: int) -> list[dict]:
    await _revision(db, lesson_id, revision_id)
    operations = await db.scalars(
        select(LessonOperation)
        .where(LessonOperation.revision_id == revision_id)
        .order_by(LessonOperation.created_at.desc(), LessonOperation.id)
        .offset(offset)
        .limit(limit)
    )
    return [
        {
            "actor_id": operation.actor_id,
            "operation_id": operation.operation_id,
            "action": operation.action,
            "created_at": operation.created_at,
            "result": operation.result,
        }
        for operation in operations
    ]


async def _claim(db: AsyncSession, actor_id: str, operation_id: str, action: str, values: dict):
    request_hash = stable_hash({"action": action, "values": values})
    statement = (
        insert_for(db, LessonOperation)
        .values(actor_id=actor_id, operation_id=operation_id, action=action, request_hash=request_hash)
        .on_conflict_do_nothing(index_elements=["actor_id", "operation_id"])
        .returning(LessonOperation)
    )
    operation = await db.scalar(statement)
    if operation is not None:
        return operation, False
    operation = (
        await db.scalars(
            select(LessonOperation).where(
                LessonOperation.actor_id == actor_id, LessonOperation.operation_id == operation_id
            )
        )
    ).one()
    if operation.request_hash != request_hash:
        raise AppError(409, ErrorCode.IDEMPOTENCY_CONFLICT, "操作编号已用于不同的课程请求")
    return operation, True


async def _replay(db: AsyncSession, operation: LessonOperation) -> dict:
    revision = await db.get(LessonRevision, operation.revision_id, populate_existing=True)
    if revision is None:
        raise _not_found()
    return _admin_detail(revision, replayed=True)


async def import_lesson(db: AsyncSession, actor_id: str, operation_id: str, payload: bytes) -> dict:
    if len(payload) > MAX_PACK_BYTES:
        raise AppError(413, ErrorCode.BAD_REQUEST, "学习包超过 4 MiB")
    try:
        pack = load_pack(payload)
    except PackValidationError as exc:
        raise _pack_error(exc.path, exc.message) from None
    if len(pack.lesson_id) > 100:
        raise _pack_error("/lesson_id", "站内课程 ID 最长为 100 个字符")
    if "\x00" in pack.title:
        raise _pack_error("/title", "站内课程标题不能包含空字符")
    digest = fingerprint(pack)
    operation, replayed = await _claim(
        db, actor_id, operation_id, "import", {"fingerprint": digest, "fingerprint_version": FINGERPRINT_VERSION}
    )
    if replayed:
        return await _replay(db, operation)
    await db.execute(insert_for(db, Lesson).values(id=pack.lesson_id).on_conflict_do_nothing(index_elements=["id"]))
    await db.get(Lesson, pack.lesson_id, with_for_update=True)
    revision = await db.scalar(
        select(LessonRevision).where(
            LessonRevision.lesson_id == pack.lesson_id,
            LessonRevision.fingerprint_version == FINGERPRINT_VERSION,
            LessonRevision.fingerprint == digest,
        )
    )
    if revision is None:
        revision = LessonRevision(
            lesson_id=pack.lesson_id,
            fingerprint=digest,
            fingerprint_version=FINGERPRINT_VERSION,
            title=pack.title,
            access_mode=pack.media.access_mode,
            pack=pack.model_dump(mode="json"),
        )
        db.add(revision)
        await db.flush()
    operation.revision_id = revision.id
    operation.result = {"lesson_id": pack.lesson_id}
    return _admin_detail(revision)


async def _claim_revision(db, actor_id, lesson_id, revision_id, action, body):
    # Replay first. A retried request must return its original result even if
    # the revision has since changed state (a retry that lands after a withdraw
    # is still the same operation and must not become an error).
    operation, replayed = await _claim(
        db,
        actor_id,
        body.operation_id,
        action,
        {"lesson_id": lesson_id, "revision_id": revision_id, **body.model_dump(exclude={"operation_id"})},
    )
    if replayed:
        return operation, None, None
    lesson = await db.get(Lesson, lesson_id, with_for_update=True, populate_existing=True)
    if lesson is None:
        raise _not_found()
    revision = await _revision(db, lesson_id, revision_id)
    operation.revision_id = revision.id
    return operation, lesson, revision


async def review_lesson(db: AsyncSession, actor_id: str, lesson_id: str, revision_id: str, body: ReviewLesson) -> dict:
    operation, _, revision = await _claim_revision(db, actor_id, lesson_id, revision_id, "review", body)
    if revision is None:
        return await _replay(db, operation)
    if revision.status != "candidate":
        raise _conflict("仅候选修订可更新审核")
    review = body.model_dump(exclude={"operation_id"})
    review["reviewed_at"] = datetime.now(UTC).isoformat()
    review["review_sha256"] = stable_hash({**review, "reviewer_id": actor_id, "revision_id": revision.id})
    revision.review, revision.reviewer_id = review, actor_id
    operation.result = review
    return _admin_detail(revision)


async def publish_lesson(
    db: AsyncSession, actor_id: str, lesson_id: str, revision_id: str, body: PublishLesson
) -> dict:
    operation, lesson, revision = await _claim_revision(db, actor_id, lesson_id, revision_id, "publish", body)
    if revision is None:
        return await _replay(db, operation)
    if lesson.current_revision_id == revision.id:
        raise _conflict("该修订已是当前版")
    if lesson.current_revision_id != body.expected_current_revision_id:
        raise _conflict("课程当前版已变化，请重新读取")
    if revision.review is None or not _use_allowed(revision, "site_display"):
        raise AppError(422, ErrorCode.VALIDATION_ERROR, "发布前需要完成站内展示用途审核")
    claims = {
        "lesson_id": lesson_id,
        "revision_id": revision.id,
        **_fingerprint_fields(revision),
        "review_sha256": revision.review["review_sha256"],
    }
    receipt_id = verify_lesson_receipt(body.receipt, claims)
    # The unique receipt ID also prevents a concurrent reuse across lessons, and
    # makes a restore (withdrawn -> published) need its own explicit signature.
    await db.flush()
    try:
        async with db.begin_nested():
            operation.receipt_id = receipt_id
            await db.flush()
    except IntegrityError:
        raise AppError(409, ErrorCode.IDEMPOTENCY_CONFLICT, "发布收据已使用") from None
    previous_status = revision.status
    lesson.current_revision_id = revision.id
    # Publishing a withdrawn revision is the explicit restore path: the review
    # and its evidence are unchanged, only a fresh signed receipt is required.
    revision.status = "published"
    operation.result = {
        **claims,
        "previous_revision_id": body.expected_current_revision_id,
        "previous_status": previous_status,
        "receipt_sha256": hashlib.sha256(body.receipt.encode("utf-8")).hexdigest(),
    }
    return _admin_detail(revision)


async def withdraw_lesson(
    db: AsyncSession, actor_id: str, lesson_id: str, revision_id: str, body: WithdrawLesson
) -> dict:
    operation, lesson, revision = await _claim_revision(db, actor_id, lesson_id, revision_id, "withdraw", body)
    if revision is None:
        return await _replay(db, operation)
    if revision.status != "published":
        raise _conflict("仅已发布修订可撤回")
    revision.status = "withdrawn"
    if lesson.current_revision_id == revision.id:
        lesson.current_revision_id = None
    operation.result = {"reason": body.reason, "status": "withdrawn"}
    return _admin_detail(revision)
