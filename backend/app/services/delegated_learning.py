"""Transactional learning use cases for opaque-token HTTP and MCP adapters.

The connection fence is always acquired first, then lesson/revision and learner
rows. Callers commit once: facts, the operation receipt and intent consumption
are deliberately not separate transactions. Receipts contain identifiers and
schedule metadata only; every returned word or title is projected afresh.
"""

import hashlib
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.delegated_learning import ExternalLearningGrant, ExternalLearningIntent, ExternalLearningOperation
from app.models.learning import Vocabulary
from app.models.lesson import Lesson, LessonRevision
from app.models.lesson_learning import LessonVocabularySource
from app.models.user import User
from app.models.v2_runtime import ExternalConnection
from app.schemas.delegated_learning import PrepareIntent, SaveProgress, SaveVocabulary
from app.schemas.lesson import RecordLessonActivity, SaveLessonProgress
from app.services import external_connection_service as connections
from app.services import lesson_catalog, lesson_learning, lesson_progress, lessons, vocabulary_service
from app.services.learning_authorization import require_lesson, required_uses
from app.services.teaching.principal import Principal, require_scope
from app.services.v2_access import require_access
from app.services.v2_schema import existing_tables, has_tables
from slcs.material import stable_hash

TABLES = (
    ExternalLearningGrant.__tablename__,
    ExternalLearningIntent.__tablename__,
    ExternalLearningOperation.__tablename__,
)
CONFIRM_URL = "/profile?tab=account#learning-intents"


def _missing() -> AppError:
    return AppError(404, "NOT_FOUND", "学习资源不存在或未获授权")


def _conflict() -> AppError:
    return AppError(409, "IDEMPOTENCY_CONFLICT", "操作编号已用于其他学习参数")


async def require_ready(db: AsyncSession) -> None:
    if not await has_tables(db, TABLES):
        raise AppError(503, "SERVICE_UNAVAILABLE", "委托学习尚未迁移")


async def _external(db: AsyncSession, principal: Principal, scope: str, *, write: bool = False) -> Principal:
    if principal.actor != "external_agent" or principal.connection_id is None:
        raise AppError(403, "INSUFFICIENT_SCOPE", "此入口仅供获委托连接使用")
    row = await connections.owned(db, principal.user_id, principal.connection_id)
    user = await db.get(User, principal.user_id, populate_existing=True)
    if (
        row.revoked_at is not None
        or connections.utc(row.expires_at) <= datetime.now(UTC)
        or user is None
        or user.is_banned
        or user.deletion_requested_at
        or (
            user.password_changed_at
            and principal.credential_issued_at
            and connections.utc(principal.credential_issued_at) < connections.utc(user.password_changed_at)
        )
    ):
        raise AppError(401, "EXTERNAL_TOKEN_INVALID", "外部凭据无效或已过期")
    await require_access(db, principal.user_id, "mcp_write_enabled" if write else "mcp_read_enabled")
    limits, audience = await connections.learning_policy(db, row)
    fresh = replace(
        principal,
        granted_scopes=frozenset(row.granted_scopes),
        resource_limits=limits,
        disclosure_audience=audience,
    )
    require_scope(fresh, scope, write=write)
    return fresh


async def _revision(
    db: AsyncSession,
    principal: Principal,
    lesson_id: str,
    revision_id: str | None,
    *,
    scope: str,
    model: bool = False,
) -> LessonRevision:
    require_lesson(principal, lesson_id, scope=scope)
    await lessons.require_lessons_ready(db)
    # Match publication's Lesson -> Revision lock order, including old links.
    lesson = await db.get(Lesson, lesson_id, with_for_update={"read": True}, populate_existing=True)
    if lesson is None:
        raise _missing()
    revision = await lessons.get_visible_revision(db, lesson_id, revision_id, lock=True)
    uses = (revision.review or {}).get("uses", {})
    if not all(uses.get(use, {}).get("approved") is True for use in required_uses(principal, model=model)):
        raise AppError(403, "LESSON_USE_NOT_ALLOWED", "课程材料未获准用于此用途")
    return revision


async def _visible_words(db: AsyncSession, principal: Principal, words: list[Vocabulary], *, model: bool) -> set[str]:
    """Grant bare owned words, never definitions, contexts or unrelated sources.

    Course-derived words additionally need a currently permitted source. An
    explicit word grant permits its headword, not its course's other content;
    a lesson grant permits only words actually anchored to that lesson.
    """
    required_uses(principal, model=model)
    explicit = set(principal.resource_limits.get("word_ids", []))
    lesson_ids = set(principal.resource_limits.get("lesson_ids", []))
    candidates = {word.id for word in words if word.user_id == principal.user_id}
    if not candidates:
        return set()
    if not await has_tables(db, ("lesson_vocabulary_sources", "lesson_revisions", "lessons")):
        return candidates & explicit
    sources = list(
        await db.execute(
            select(LessonVocabularySource, LessonRevision.lesson_id)
            .join(LessonRevision, LessonRevision.id == LessonVocabularySource.revision_id)
            .where(LessonVocabularySource.vocabulary_id.in_(candidates))
            .order_by(LessonRevision.lesson_id, LessonRevision.id, LessonVocabularySource.id)
        )
    )
    sourced = {source.vocabulary_id for source, _ in sources}
    visible = (candidates & explicit) - sourced
    checked: dict[str, bool] = {}
    # Stable lesson locks before revision checks. No word lock has been taken.
    relevant_lessons = sorted({lid for source, lid in sources if lid in lesson_ids or source.vocabulary_id in explicit})
    if relevant_lessons:
        await db.execute(
            select(Lesson.id).where(Lesson.id.in_(relevant_lessons)).order_by(Lesson.id).with_for_update(read=True)
        )
    for source, lesson_id in sources:
        if lesson_id not in lesson_ids and source.vocabulary_id not in explicit:
            continue
        if source.revision_id not in checked:
            revision = await db.get(LessonRevision, source.revision_id, populate_existing=True)
            uses = ((revision.review or {}).get("uses", {})) if revision is not None else {}
            checked[source.revision_id] = bool(
                revision
                and revision.status == "published"
                and all(uses.get(use, {}).get("approved") is True for use in required_uses(principal, model=model))
            )
        if checked[source.revision_id]:
            visible.add(source.vocabulary_id)
    return visible


async def _word(db: AsyncSession, principal: Principal, word_id: str, *, model: bool = False) -> Vocabulary:
    word = await db.scalar(select(Vocabulary).where(Vocabulary.id == word_id, Vocabulary.user_id == principal.user_id))
    if word is None or word.id not in await _visible_words(db, principal, [word], model=model):
        raise _missing()
    return word


async def review_tasks(
    db: AsyncSession,
    principal: Principal,
    *,
    offset: int = 0,
    limit: int = 20,
    model: bool = False,
) -> dict:
    principal = await _external(db, principal, "review:read")
    if type(offset) is not int or type(limit) is not int or offset < 0 or not 1 <= limit <= 100:
        raise AppError(422, "VALIDATION_ERROR", "分页参数无效")
    if not principal.resource_limits:
        return {"items": [], "total": 0, "offset": offset, "limit": limit}
    query = await vocabulary_service.due_query(db, principal.user_id)
    words = list(await db.scalars(query))
    allowed = await _visible_words(db, principal, words, model=model)
    words = [word for word in words if word.id in allowed]
    return {
        "items": [
            {
                "id": word.id,
                "word": word.word,
                "next_review_at": word.next_review_at,
                "resume_url": "/vocabulary/review",
            }
            for word in words[offset : offset + limit]
        ],
        "total": len(words),
        "offset": offset,
        "limit": limit,
    }


def _hash(action: str, parameters: dict) -> str:
    return stable_hash({"action": action, "parameters": parameters})


async def _prior(
    db: AsyncSession,
    principal: Principal,
    operation_id: str,
    digest: str,
) -> ExternalLearningOperation | None:
    await require_ready(db)
    prior = await db.scalar(
        select(ExternalLearningOperation).where(
            ExternalLearningOperation.user_id == principal.user_id,
            ExternalLearningOperation.connection_id == principal.connection_id,
            ExternalLearningOperation.operation_id == operation_id,
        )
    )
    pending = await db.scalar(
        select(ExternalLearningIntent).where(
            ExternalLearningIntent.user_id == principal.user_id,
            ExternalLearningIntent.connection_id == principal.connection_id,
            ExternalLearningIntent.operation_id == operation_id,
        )
    )
    if (prior is not None and prior.payload_hash != digest) or (pending is not None and pending.payload_hash != digest):
        raise _conflict()
    return prior


def _receipt(
    db: AsyncSession,
    principal: Principal,
    operation_id: str,
    action: str,
    parameters: dict,
    resource: dict,
    result: dict,
) -> None:
    db.add(
        ExternalLearningOperation(
            user_id=principal.user_id,
            connection_id=principal.connection_id,
            operation_id=operation_id,
            action=action,
            payload_hash=_hash(action, parameters),
            resource=resource,
            result=result,
        )
    )


def _fact_id(principal: Principal, operation_id: str) -> str:
    # Separate connection namespace also for existing user-wide fact APIs.
    return "ext:" + hashlib.sha256(f"{principal.connection_id}:{operation_id}".encode()).hexdigest()[:60]


async def save_vocabulary(db: AsyncSession, principal: Principal, body: SaveVocabulary, *, model: bool = False) -> dict:
    principal = await _external(db, principal, "learning:vocabulary:write", write=True)
    parameters = body.reference.model_dump()
    previous = await _prior(db, principal, body.operation_id, _hash("vocabulary", parameters))
    # Live scope, fixed reference and all content uses are checked on replay.
    resolved = await lesson_catalog.resolve_reference(db, principal, body.reference, model=model)
    reference = resolved["reference"]
    if previous is not None:
        word = await db.scalar(
            select(Vocabulary).where(
                Vocabulary.id == previous.result["word_id"],
                Vocabulary.user_id == principal.user_id,
            )
        )
        if word is None:
            raise _missing()
        revision = await db.get(LessonRevision, reference["revision_id"])
        if revision is None:
            raise _missing()
        occurrence = lesson_learning.resolve_occurrence(
            lessons.material_for_revision(revision), reference["segment_id"], reference["token_ids"]
        )
        return {
            "word_id": word.id,
            "word": word.word,
            "source": lesson_learning.source_view(
                reference["lesson_id"], revision.id, reference["segment_id"], reference["token_ids"], occurrence
            ),
        }
    result = await lesson_learning.save_source(
        db,
        principal.user_id,
        reference["lesson_id"],
        reference["revision_id"],
        reference["segment_id"],
        reference["token_ids"],
    )
    _receipt(db, principal, body.operation_id, "vocabulary", parameters, reference, {"word_id": result["word_id"]})
    await db.flush()
    return result


async def read_progress(db: AsyncSession, principal: Principal, lesson_id: str, *, model: bool = False) -> dict:
    principal = await _external(db, principal, "learning:progress:read")
    require_lesson(principal, lesson_id, scope="learning:progress:read")
    await lessons.require_lessons_ready(db)
    # Fence publication before reading the pointer, then validate precisely the
    # returned revision (a first-party save may have moved it meanwhile).
    await db.get(Lesson, lesson_id, with_for_update={"read": True}, populate_existing=True)
    result = await lesson_progress.read_progress(db, principal.user_id, lesson_id)
    await _revision(db, principal, lesson_id, result["revision_id"], scope="learning:progress:read", model=model)
    return result


async def save_progress(
    db: AsyncSession,
    principal: Principal,
    lesson_id: str,
    body: SaveProgress,
    *,
    model: bool = False,
) -> dict:
    principal = await _external(db, principal, "learning:progress:write", write=True)
    require_scope(principal, "learning:progress:read")
    parameters = {"lesson_id": lesson_id, **body.model_dump(exclude={"operation_id"})}
    previous = await _prior(db, principal, body.operation_id, _hash("progress", parameters))
    await _revision(db, principal, lesson_id, body.revision_id, scope="learning:progress:write", model=model)
    if previous is not None:
        return previous.result
    result = await lesson_progress.save_progress(
        db,
        principal.user_id,
        lesson_id,
        SaveLessonProgress(revision_id=body.revision_id, position_ms=body.position_ms),
        expected_version=body.expected_version,
    )
    _receipt(
        db,
        principal,
        body.operation_id,
        "progress",
        parameters,
        {"lesson_id": lesson_id, "revision_id": body.revision_id},
        result,
    )
    await db.flush()
    return result


async def _validate_intent(db: AsyncSession, principal: Principal, body: PrepareIntent, *, model: bool) -> dict:
    if body.action == "review":
        if body.word_id is None or body.quality is None:
            raise AppError(422, "VALIDATION_ERROR", "复习操作需要明确词条和结果")
        require_scope(principal, "review:read")
        require_scope(principal, "review:write", write=True)
        word = await _word(db, principal, body.word_id, model=model)
        return {"word_id": word.id, "word": word.word, "available": True}
    if body.lesson_id is None or body.revision_id is None:
        raise AppError(422, "VALIDATION_ERROR", "完成操作需要固定课程修订")
    require_scope(principal, "learning:progress:read")
    require_scope(principal, "learning:progress:write", write=True)
    revision = await _revision(
        db, principal, body.lesson_id, body.revision_id, scope="learning:progress:write", model=model
    )
    return {"lesson_id": revision.lesson_id, "revision_id": revision.id, "title": revision.title, "available": True}


def _intent_status(row: ExternalLearningIntent) -> str:
    if row.consumed_at is not None:
        return "consumed"
    if connections.utc(row.expires_at) <= datetime.now(UTC):
        return "expired"
    return "approved" if row.approved_at is not None else "pending"


def _intent_view(row: ExternalLearningIntent, host_label: str, resource: dict, *, status: str | None = None) -> dict:
    return {
        "id": row.id,
        "connection_id": row.connection_id,
        "host_label": host_label,
        "operation_id": row.operation_id,
        "action": row.action,
        "resource": resource,
        "quality": row.parameters.get("quality"),
        "expires_at": row.expires_at,
        "status": status or _intent_status(row),
        "confirmation_url": CONFIRM_URL,
    }


async def prepare_intent(db: AsyncSession, principal: Principal, body: PrepareIntent, *, model: bool = False) -> dict:
    scope = "review:write" if body.action == "review" else "learning:progress:write"
    principal = await _external(db, principal, scope, write=True)
    parameters = body.model_dump(exclude={"operation_id", "action"}, exclude_none=True)
    digest = _hash(body.action, parameters)
    previous = await _prior(db, principal, body.operation_id, digest)
    resource = await _validate_intent(db, principal, body, model=model)
    intent = await db.scalar(
        select(ExternalLearningIntent).where(
            ExternalLearningIntent.user_id == principal.user_id,
            ExternalLearningIntent.connection_id == principal.connection_id,
            ExternalLearningIntent.operation_id == body.operation_id,
        )
    )
    if intent is None:
        if previous is not None:
            raise AppError(409, "CONFLICT", "操作已执行，确认意图已清理")
        intent = ExternalLearningIntent(
            user_id=principal.user_id,
            connection_id=principal.connection_id,
            operation_id=body.operation_id,
            action=body.action,
            parameters=parameters,
            payload_hash=digest,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        db.add(intent)
        await db.flush()
    connection = await db.get(ExternalConnection, principal.connection_id)
    if connection is None:
        raise _missing()
    return _intent_view(intent, connection.host_label, resource)


async def _owned_intent(
    db: AsyncSession, user_id: str, intent_id: str
) -> tuple[ExternalLearningIntent, ExternalConnection]:
    await require_ready(db)
    # Read identity only before the connection fence; never lock an intent and
    # then its connection (execute and account purge take the opposite order).
    connection_id = await db.scalar(
        select(ExternalLearningIntent.connection_id).where(
            ExternalLearningIntent.id == intent_id, ExternalLearningIntent.user_id == user_id
        )
    )
    if connection_id is None:
        raise _missing()
    connection = await connections.owned(db, user_id, connection_id)
    intent = await db.scalar(
        select(ExternalLearningIntent)
        .where(
            ExternalLearningIntent.id == intent_id,
            ExternalLearningIntent.user_id == user_id,
            ExternalLearningIntent.connection_id == connection.id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if intent is None:
        raise _missing()
    return intent, connection


async def list_intents(db: AsyncSession, user_id: str) -> dict:
    if not await has_tables(db, TABLES):
        return {"items": []}
    ids = list(
        await db.scalars(
            select(ExternalLearningIntent.id)
            .where(ExternalLearningIntent.user_id == user_id, ExternalLearningIntent.consumed_at.is_(None))
            .order_by(
                ExternalLearningIntent.connection_id, ExternalLearningIntent.created_at, ExternalLearningIntent.id
            )
        )
    )
    items = []
    for intent_id in ids:
        try:
            intent, connection = await _owned_intent(db, user_id, intent_id)
        except AppError as exc:
            # Expiry cleanup may remove an ID after enumeration but before its
            # connection fence is acquired. Other pending intents remain usable.
            if exc.status_code == 404:
                continue
            raise
        principal = Principal(user_id, actor="external_agent", connection_id=connection.id)
        try:
            principal = await _external(
                db, principal, "review:write" if intent.action == "review" else "learning:progress:write", write=True
            )
            resource = await _validate_intent(
                db,
                principal,
                PrepareIntent.model_validate(
                    {"operation_id": intent.operation_id, "action": intent.action, **intent.parameters}
                ),
                model=False,
            )
            status = _intent_status(intent)
        except AppError as exc:
            if exc.status_code not in {401, 403, 404, 410, 503}:
                raise
            resource = {
                key: value for key, value in intent.parameters.items() if key in {"word_id", "lesson_id", "revision_id"}
            }
            resource["available"] = False
            status = "unavailable"
        items.append(_intent_view(intent, connection.host_label, resource, status=status))
    return {"items": items}


async def confirm_intent(db: AsyncSession, user_id: str, intent_id: str) -> dict:
    intent, connection = await _owned_intent(db, user_id, intent_id)
    if _intent_status(intent) not in {"pending", "approved"}:
        raise AppError(409, "CONFLICT", "操作意图已过期或已执行")
    principal = Principal(user_id, actor="external_agent", connection_id=connection.id)
    principal = await _external(
        db, principal, "review:write" if intent.action == "review" else "learning:progress:write", write=True
    )
    resource = await _validate_intent(
        db,
        principal,
        PrepareIntent.model_validate(
            {"operation_id": intent.operation_id, "action": intent.action, **intent.parameters}
        ),
        model=False,
    )
    intent.approved_at = intent.approved_at or datetime.now(UTC)
    await db.flush()
    return _intent_view(intent, connection.host_label, resource)


async def execute_intent(db: AsyncSession, principal: Principal, intent_id: str, *, model: bool = False) -> dict:
    # Authentication already fenced the connection. Hide foreign intent IDs
    # without ever taking another connection lock.
    await require_ready(db)
    if principal.actor != "external_agent" or principal.connection_id is None:
        raise AppError(403, "INSUFFICIENT_SCOPE", "此入口仅供获委托连接使用")
    intent = await db.scalar(
        select(ExternalLearningIntent).where(
            ExternalLearningIntent.id == intent_id,
            ExternalLearningIntent.user_id == principal.user_id,
            ExternalLearningIntent.connection_id == principal.connection_id,
        )
    )
    if intent is None:
        raise _missing()
    principal = await _external(
        db, principal, "review:write" if intent.action == "review" else "learning:progress:write", write=True
    )
    await db.refresh(intent)
    body = PrepareIntent.model_validate(
        {"operation_id": intent.operation_id, "action": intent.action, **intent.parameters}
    )
    if intent.payload_hash != _hash(intent.action, intent.parameters):
        raise _conflict()
    resource = await _validate_intent(db, principal, body, model=model)
    previous = await _prior(db, principal, intent.operation_id, intent.payload_hash)
    if intent.consumed_at is not None:
        if previous is None:
            raise AppError(409, "CONFLICT", "操作意图已执行")
        return {**previous.result, "resource": resource}
    if intent.approved_at is None or connections.utc(intent.expires_at) <= datetime.now(UTC):
        raise AppError(409, "CONFIRMATION_REQUIRED", "请先在网站确认尚未过期的操作意图")
    if previous is not None:
        raise AppError(409, "CONFLICT", "操作已执行")
    if body.action == "review":
        if body.word_id is None or body.quality is None:
            raise AppError(422, "VALIDATION_ERROR", "复习操作需要明确词条和结果")
        result = await vocabulary_service.record_idempotent_review(
            db,
            principal.user_id,
            body.word_id,
            body.quality,
            _fact_id(principal, intent.operation_id),
            source="external_confirmed",
        )
        if result is None:
            raise _missing()
        # The legacy helper returns the live word; do not freeze it in a receipt.
        result = {key: value for key, value in result.items() if key != "word"}
    else:
        if body.lesson_id is None or body.revision_id is None:
            raise AppError(422, "VALIDATION_ERROR", "完成操作需要固定课程修订")
        result = await lesson_progress.record_activity(
            db,
            principal.user_id,
            body.lesson_id,
            RecordLessonActivity(
                revision_id=body.revision_id, event_type="complete", event_id=_fact_id(principal, intent.operation_id)
            ),
        )
    safe_resource = {key: value for key, value in resource.items() if key in {"word_id", "lesson_id", "revision_id"}}
    _receipt(db, principal, intent.operation_id, intent.action, intent.parameters, safe_resource, result)
    intent.consumed_at = datetime.now(UTC)
    await db.flush()
    return {**result, "resource": resource}


async def cleanup_expired_intents(db: AsyncSession, *, now: datetime | None = None) -> int:
    if not await has_tables(db, (ExternalLearningIntent.__tablename__,)):
        return 0
    # Consumed rows are minimal replay tombstones (IDs and bounded action
    # parameters, never content or credentials), retained with their receipt
    # until account deletion. Only unconsumed confirmations expire out of storage.
    cutoff = now or datetime.now(UTC)
    expired = (ExternalLearningIntent.expires_at <= cutoff) & ExternalLearningIntent.consumed_at.is_(None)
    expired_connections = select(ExternalLearningIntent.connection_id).where(expired)
    # Match execute/confirm/purge lock order, rather than deleting an intent
    # under a concurrent executor before it writes its receipt.
    await db.execute(
        select(ExternalConnection.id)
        .where(ExternalConnection.id.in_(expired_connections))
        .order_by(ExternalConnection.id)
        .with_for_update()
    )
    result = await db.execute(
        delete(ExternalLearningIntent).where(expired).execution_options(synchronize_session="fetch")
    )
    return int(getattr(result, "rowcount", 0) or 0)


async def export_sections(db: AsyncSession, user_id: str) -> dict:
    from app.services.account_data import row_to_dict

    tables = await existing_tables(db)
    result = {}
    for model in (ExternalLearningGrant, ExternalLearningOperation, ExternalLearningIntent):
        result[model.__tablename__] = (
            [
                row_to_dict(row, exclude=frozenset({"payload_hash"}))
                for row in await db.scalars(select(model).where(model.user_id == user_id))
            ]
            if model.__tablename__ in tables
            else []
        )
    return result


async def purge_facts(db: AsyncSession, user_id: str) -> None:
    tables = await existing_tables(db)
    for model in (ExternalLearningIntent, ExternalLearningOperation, ExternalLearningGrant):
        if model.__tablename__ in tables:
            await db.execute(delete(model).where(model.user_id == user_id))
