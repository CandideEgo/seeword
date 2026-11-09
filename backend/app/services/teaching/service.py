"""Deterministic, transaction-owned single-item teaching operations.

Callers own commit/rollback. All receipts store references, and every response
is projected again under current rights/scopes, including idempotent replay.
"""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, NoReturn

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.errors import AppError
from app.models.exam_test import ExamAnswer, ExamPaper, ExamSession
from app.models.teaching import (
    ExamAnalysisRevision,
    LearningEventOutbox,
    TeachingAttempt,
    TeachingFeedback,
    TeachingItem,
    TeachingOperation,
    TeachingSession,
    UserQuestionDisclosure,
)
from app.models.user import User
from app.schemas.teaching import CompleteSession, CreateSession, DraftAnswer, Feedback, ItemAction, SubmitAttempt
from app.services.question_exposure_service import (
    ensure_exposure_mapping_state,
    lock_question_exposure,
    record_answer_available,
)
from app.services.teaching.content import current_revision_available, project_content, source_fingerprint
from app.services.teaching.principal import Principal, require_scope

if TYPE_CHECKING:
    from pydantic import BaseModel
    from sqlalchemy.ext.asyncio import AsyncSession


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return (value.replace(tzinfo=UTC) if value.tzinfo is None else value).isoformat()


def _body(body) -> dict:
    data = body.model_dump() if hasattr(body, "model_dump") else dict(body)
    if isinstance(data.get("answer"), str):
        data["answer"] = data["answer"].strip().upper()
    return data


def _error(code: str, message: str, status=409) -> NoReturn:
    raise AppError(status, code, message)


async def check_write_access(db: "AsyncSession", principal: Principal, operation: str) -> None:
    from app.services.v2_access import require_access

    scope = {
        "attempt": "teaching:attempts:submit",
        "reveal": "teaching:analysis:reveal",
        "feedback": "learning:feedback:write",
    }.get(operation, "teaching:read")
    require_scope(principal, scope, write=True)
    if principal.actor == "external_agent" and operation not in {"attempt", "reveal", "feedback"}:
        _error("INSUFFICIENT_SCOPE", "该动作只允许在网页明确执行", 403)
    await require_access(db, principal.user_id, "teaching_enabled")


async def owned_session(db: "AsyncSession", principal: Principal, session_id: str, *, lock=False) -> TeachingSession:
    from app.services.v2_schema import require_teaching_schema

    require_scope(principal, "teaching:read")
    await require_teaching_schema(db)
    query = (
        select(TeachingSession)
        .where(TeachingSession.id == session_id, TeachingSession.user_id == principal.user_id)
        .execution_options(populate_existing=True)
    )
    if lock:
        query = query.with_for_update()
    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        _error("NOT_FOUND", "教学会话不存在", 404)
    return row


def _request_hash(operation: str, target: str | None, body: dict) -> str:
    data = {"operation": operation, "target": target, "input": {k: v for k, v in body.items() if k != "operation_id"}}
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def _operation(
    db: "AsyncSession", principal: Principal, operation: str, target: str | None, body: dict
) -> tuple[TeachingOperation, bool]:
    """Claim the unique operation before effects, waiting for a concurrent winner."""
    import uuid

    request_hash = _request_hash(operation, target, body)
    values = {
        "id": str(uuid.uuid4()),
        "user_id": principal.user_id,
        "operation_namespace": principal.namespace,
        "operation_id": body["operation_id"],
        "operation_type": operation,
        "request_hash": request_hash,
        "status": "reserved",
        "result_refs": {},
        "created_at": _now(),
    }
    dialect_insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    result = await db.execute(
        dialect_insert(TeachingOperation)
        .values(**values)
        .on_conflict_do_nothing(index_elements=["user_id", "operation_namespace", "operation_id"])
        .returning(TeachingOperation.id)
    )
    inserted = result.scalar_one_or_none() is not None
    row = (
        await db.execute(
            select(TeachingOperation)
            .where(
                TeachingOperation.user_id == principal.user_id,
                TeachingOperation.operation_namespace == principal.namespace,
                TeachingOperation.operation_id == body["operation_id"],
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    if row.request_hash != request_hash:
        _error("IDEMPOTENCY_CONFLICT", "同一个操作标识不能用于不同内容")
    if not inserted and row.status != "completed":
        _error("TEACHING_STATE_CONFLICT", "该动作正在处理")
    return row, not inserted


async def _disclosure(db: "AsyncSession", principal: Principal, revision_id: str) -> UserQuestionDisclosure:
    dialect_insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    await db.execute(
        dialect_insert(UserQuestionDisclosure)
        .values(user_id=principal.user_id, content_revision_id=revision_id, reason="none")
        .on_conflict_do_nothing(index_elements=["user_id", "content_revision_id"])
    )
    return (
        await db.execute(
            select(UserQuestionDisclosure)
            .where(
                UserQuestionDisclosure.user_id == principal.user_id,
                UserQuestionDisclosure.content_revision_id == revision_id,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one()


def projection_target(principal: Principal) -> str:
    return (
        "external"
        if principal.actor == "external_agent"
        else "model"
        if principal.actor == "internal_agent"
        else "site"
    )


def answer_history_visible(principal: Principal, *, restricted: bool) -> bool:
    return not restricted and (
        principal.actor != "external_agent"
        or bool(principal.granted_scopes & {"teaching:attempts:submit", "teaching:analysis:read"})
    )


async def project_session(
    db: "AsyncSession",
    principal: Principal,
    session: TeachingSession,
    *,
    replayed=False,
    attempt_limit: int | None = None,
) -> dict:
    require_scope(principal, "teaching:read")
    if session.user_id != principal.user_id:
        _error("NOT_FOUND", "教学会话不存在", 404)
    items = list(
        (
            await db.execute(
                select(TeachingItem)
                .where(TeachingItem.session_id == session.id)
                .order_by(TeachingItem.ordinal)
                .execution_options(populate_existing=True)
            )
        ).scalars()
    )
    cards: list[dict] = []
    public_items: list[dict] = []
    attempts: list[dict] = []
    attempt_count = 0
    for item in items:
        revision = await db.get(ExamAnalysisRevision, item.content_revision_id, populate_existing=True)
        if revision is None:
            _error("NOT_FOUND", "教学内容不存在", 404)
        disclosure = await db.get(
            UserQuestionDisclosure, (principal.user_id, item.content_revision_id), populate_existing=True
        )
        disclosed = bool(disclosure and disclosure.analysis_revealed_at)
        target = projection_target(principal)
        content = await project_content(db, revision, principal, disclosed=disclosed, target=target)
        header = {
            "schema_version": 1,
            "session_id": session.id,
            "item_id": item.id,
            "session_revision": session.revision,
        }
        restricted = content.get("restricted", False)
        if restricted:
            cards.append(
                {
                    **header,
                    "card_id": f"{item.id}:restricted",
                    "kind": "status",
                    "payload": {"code": "CONTENT_RESTRICTED", "message": "该内容当前不允许在此入口展示"},
                }
            )
        else:
            cards.append(
                {
                    **header,
                    "card_id": f"{item.id}:question",
                    "kind": "question",
                    "payload": {
                        key: content[key]
                        for key in ("question_key", "question_type", "passage", "question", "options", "source_url")
                    },
                }
            )
            if item.hint_level and principal.actor != "external_agent":
                cards.append(
                    {
                        **header,
                        "card_id": f"{item.id}:hint:{item.hint_level}",
                        "kind": "hint",
                        "payload": {"level": item.hint_level, "text": revision.reviewed_hints[item.hint_level - 1]},
                    }
                )
            if "correct_answer" in content:
                cards.append(
                    {
                        **header,
                        "card_id": f"{item.id}:analysis",
                        "kind": "analysis",
                        "payload": {key: content[key] for key in ("correct_answer", "option_analyses", "analysis")},
                    }
                )
                cards.append(
                    {
                        **header,
                        "card_id": f"{item.id}:evidence",
                        "kind": "evidence",
                        "payload": {"quotes": content["quotes"]},
                    }
                )
        # Read-only external scopes must not infer the standard answer from an
        # earlier correct answer, even after the user revealed it in the web UI.
        may_read_answers = answer_history_visible(principal, restricted=restricted)
        # Quiz progress counts this item's own attempts. It is withheld with the
        # same rule as the answer history: a flip of ``correct`` across repeated
        # guesses would otherwise be an answer oracle. ``next_attempt_no`` is
        # bumped on every graded attempt, so it answers "was this answered"
        # without another query; the latest verdict comes from the attempt rows
        # read below (or a single-row lookup when they are limited).
        answered = may_read_answers and item.next_attempt_no > 1
        correct: bool | None = None
        public_items.append(
            {
                "id": item.id,
                "question_key": item.question_key,
                "content_revision_id": item.content_revision_id,
                "state": item.state,
                "draft_answer": item.draft_answer if may_read_answers else None,
                "draft_revision": item.draft_revision,
                "answered": answered,
                "correct": correct,
            }
        )
        if may_read_answers:
            query = select(TeachingAttempt).where(TeachingAttempt.item_id == item.id)
            query = (
                query.order_by(TeachingAttempt.attempt_no.desc()).limit(attempt_limit)
                if attempt_limit is not None
                else query.order_by(TeachingAttempt.attempt_no)
            )
            rows = list((await db.execute(query.execution_options(populate_existing=True))).scalars())
            attempt_count += len(rows) if attempt_limit is None else item.next_attempt_no - 1
            if attempt_limit is not None:
                # Rows are newest-first only to take the latest verdict; the
                # attempt list itself stays in ascending attempt order. A limited
                # read can still come back empty (the item was graded under a
                # scope that hides attempts), so the verdict stays unknown then.
                if rows:
                    correct = rows[0].correct
                rows.reverse()
            elif rows:
                correct = rows[-1].correct
            # ``public_items`` was appended above, before the attempt rows were
            # read; patch the verdict in place so the API still ships it.
            public_items[-1]["correct"] = correct
            attempts.extend(
                {
                    "id": a.id,
                    "item_id": a.item_id,
                    "attempt_no": a.attempt_no,
                    "answer": a.user_answer,
                    "correct": a.correct,
                    "role": a.role,
                    "answer_origin": a.answer_origin,
                    "server_graded": a.server_graded,
                    "assistance_snapshot": a.assistance_snapshot,
                    "occurred_at": _iso(a.occurred_at),
                }
                for a in rows
            )
    if session.status != "active" and items:
        cards.append(
            {
                "schema_version": 1,
                "card_id": f"{session.id}:summary",
                "session_id": session.id,
                "item_id": items[0].id,
                "session_revision": session.revision,
                "kind": "summary",
                "payload": {"attempt_count": attempt_count, "status": session.status},
            }
        )
    answered_count = sum(1 for row in public_items if row["answered"])
    if len(items) > 1:
        cards.append(
            {
                "schema_version": 1,
                "card_id": f"{session.id}:progress",
                "session_id": session.id,
                "item_id": items[0].id,
                "session_revision": session.revision,
                "kind": "progress",
                "payload": {
                    "answered": answered_count,
                    "correct": sum(1 for row in public_items if row["correct"] is True),
                    "total": len(items),
                    "item_ids": [row["id"] for row in public_items],
                },
            }
        )
    # The bound is derived from the session, not fixed at 8: a quiz has one
    # question card per item and each item may legitimately also carry a hint,
    # an analysis and an evidence card. A fixed cap turned the normal path
    # ("reveal two of four questions", then "finish") into a permanent 409 that
    # every retry reproduced — the session could never leave ``active``.
    limit = max(SINGLE_ITEM_CARD_LIMIT, PER_ITEM_CARDS * len(items) + 2)
    if len(cards) > limit or any(len(json.dumps(card, ensure_ascii=False).encode()) > 16384 for card in cards):
        _error("TEACHING_STATE_CONFLICT", "内容超过卡片展示上限")
    from app.models.v2_runtime import AgentRun

    latest = await db.scalar(
        select(AgentRun).where(AgentRun.session_id == session.id).order_by(AgentRun.created_at.desc()).limit(1)
    )
    latest_run = (
        {
            "id": latest.id,
            "run_id": latest.id,
            "session_id": session.id,
            "status": latest.status,
            "last_sequence": latest.last_sequence,
            "cards": [],
            "error_code": latest.error_code,
        }
        if latest
        else None
    )
    return {
        "id": session.id,
        "user_id": session.user_id,
        "status": session.status,
        "revision": session.revision,
        "current_item_id": session.current_item_id,
        "policy_version": session.policy_version,
        "items": public_items,
        "attempts": attempts,
        "cards": cards,
        "latest_run": latest_run,
        "operation_result": None,
        "replayed": replayed,
        "created_at": _iso(session.created_at),
        "updated_at": _iso(session.updated_at),
    }


async def get_session(db: "AsyncSession", principal: Principal, session_id: str) -> dict:
    return await project_session(db, principal, await owned_session(db, principal, session_id))


async def list_sessions(db: "AsyncSession", principal: Principal) -> dict:
    from app.services.v2_schema import require_teaching_schema

    require_scope(principal, "teaching:read")
    await require_teaching_schema(db)
    rows = (
        await db.execute(
            select(TeachingSession)
            .where(TeachingSession.user_id == principal.user_id)
            .order_by(TeachingSession.updated_at.desc())
            .limit(30)
        )
    ).scalars()
    return {
        "items": [
            {
                "id": s.id,
                "status": s.status,
                "revision": s.revision,
                "current_item_id": s.current_item_id,
                "updated_at": _iso(s.updated_at),
            }
            for s in rows
        ]
    }


async def content_catalog(db: "AsyncSession", principal: Principal, *, question_id=None, paper_id=None) -> dict:
    from app.services.v2_access import require_access

    require_scope(principal, "teaching:read")
    await require_access(db, principal.user_id, "teaching_enabled")
    query = (
        select(ExamAnalysisRevision)
        .where(ExamAnalysisRevision.status == "auto_verified")
        .order_by(ExamAnalysisRevision.revision_no.desc())
    )
    if question_id:
        query = query.where(ExamAnalysisRevision.question_id == question_id)
    rows = (await db.execute(query.limit(100))).scalars()
    result, seen = [], set()
    for revision in rows:
        if revision.question_key in seen or not await current_revision_available(db, revision):
            continue
        from app.models.exam_test import ExamQuestion

        question = await db.get(ExamQuestion, revision.question_id)
        if question is None:
            continue
        if paper_id and question.paper_id != paper_id:
            continue
        projected = await project_content(
            db, revision, principal, target="external" if principal.actor == "external_agent" else "site"
        )
        if projected.get("restricted"):
            continue
        paper = await db.get(ExamPaper, question.paper_id)
        if paper is None:
            continue
        result.append(
            {
                "id": revision.id,
                "question_key": revision.question_key,
                "question_id": revision.question_id,
                "status": revision.status,
                "paper_id": question.paper_id,
                "title": paper.title,
                "number": question.number,
                "level": paper.level,
            }
        )
        seen.add(revision.question_key)
    return {"items": result}


async def create_session(db: "AsyncSession", principal: Principal, body) -> dict:
    await check_write_access(db, principal, "create")
    data = _body(CreateSession.model_validate(body) if isinstance(body, dict) else body)
    # Starts have no session to lock. A user row serializes start receipts and
    # legacy-source reuse without committing a partial session on conflict.
    await db.execute(select(User.id).where(User.id == principal.user_id).with_for_update())
    operation, replayed = await _operation(db, principal, "create", None, data)
    if replayed:
        return await project_session(
            db, principal, await owned_session(db, principal, operation.result_refs["session_id"]), replayed=True
        )
    legacy_answer, legacy_session = None, None
    revision_id = data.get("content_revision_id")
    qid = data.get("question_id")
    if data.get("source_exam_answer_id"):
        row = (
            await db.execute(
                select(ExamAnswer, ExamSession)
                .join(ExamSession, ExamSession.id == ExamAnswer.session_id)
                .where(ExamAnswer.id == data["source_exam_answer_id"], ExamSession.user_id == principal.user_id)
            )
        ).one_or_none()
        if row is None:
            _error("NOT_FOUND", "考试作答不存在", 404)
        legacy_answer, legacy_session = row
        if not legacy_session.submitted_at:
            _error("TEACHING_STATE_CONFLICT", "请先提交原考试")
        existing = (
            await db.execute(
                select(TeachingSession).where(
                    TeachingSession.user_id == principal.user_id,
                    TeachingSession.source_exam_answer_id == legacy_answer.id,
                )
            )
        ).scalar_one_or_none()
        if existing:
            operation.status, operation.result_refs = "completed", {"session_id": existing.id}
            return await project_session(db, principal, existing, replayed=True)
        qid = legacy_answer.question_id
        if not qid:
            _error("CONTENT_REVISION_MISMATCH", "历史题面无法匹配当前核验版本")
    if not revision_id:
        revision_id = await db.scalar(
            select(ExamAnalysisRevision.id)
            .where(ExamAnalysisRevision.question_id == qid, ExamAnalysisRevision.status == "auto_verified")
            .order_by(ExamAnalysisRevision.revision_no.desc())
            .limit(1)
        )
    revision = (
        await db.execute(
            select(ExamAnalysisRevision)
            .where(ExamAnalysisRevision.id == revision_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if revision is None:
        _error("NOT_FOUND", "暂无可用于教学的自动核验内容", 404)
    if not await current_revision_available(db, revision):
        _error("CONTENT_REVISION_MISMATCH", "题目来源已变化，请重新选择核验版本")
    projected = await project_content(
        db, revision, principal, target="external" if principal.actor == "external_agent" else "site"
    )
    if projected.get("restricted"):
        _error("CONTENT_REVISION_MISMATCH", "该材料不允许在此入口使用")
    if legacy_answer:
        snapshot = legacy_answer.question
        frozen = {
            **revision.question_payload,
            **{key: snapshot[key] for key in ("passage", "question", "options", "question_type") if key in snapshot},
        }
        if source_fingerprint(frozen, snapshot.get("answer", "")) != revision.source_fingerprint:
            _error("CONTENT_REVISION_MISMATCH", "历史作答与当前核验版本不一致")
    await ensure_exposure_mapping_state(db, principal.user_id)
    await lock_question_exposure(db, principal.user_id, revision.question_key)
    session = TeachingSession(
        user_id=principal.user_id,
        source_exam_session_id=legacy_session.id if legacy_session else None,
        source_exam_answer_id=legacy_answer.id if legacy_answer else None,
    )
    db.add(session)
    await db.flush()
    item = TeachingItem(
        session_id=session.id,
        question_key=revision.question_key,
        content_revision_id=revision.id,
        source_exam_answer_id=legacy_answer.id if legacy_answer else None,
    )
    db.add(item)
    await db.flush()
    session.current_item_id = item.id
    if legacy_answer:
        attempt = TeachingAttempt(
            item_id=item.id,
            attempt_no=1,
            user_answer=legacy_answer.user_answer,
            correct=bool(legacy_answer.correct),
            grading_version="legacy_server_grading",
            role="legacy_exam",
            answer_origin="legacy_exam",
            assistance_snapshot={
                "initial_eligibility": "unknown",
                "independence": "unverified",
                "answer_available": True,
            },
            source_exam_answer_id=legacy_answer.id,
        )
        db.add(attempt)
        await db.flush()
        item.next_attempt_no, item.last_attempt_id, item.state = 2, attempt.id, "graded"
        await record_answer_available(
            db, principal.user_id, [item.question_key], origin="legacy_exam", occurred_at=_now()
        )
    operation.status, operation.result_refs = "completed", {"session_id": session.id}
    await db.flush()
    return await project_session(db, principal, session)


QUIZ_SIZE = 4
#: Cards one item may contribute: question, hint, analysis, evidence.
PER_ITEM_CARDS = 4
#: The pre-quiz bound, kept so a single-question session is never tightened.
SINGLE_ITEM_CARD_LIMIT = 8


async def _quiz_revisions(db: "AsyncSession", data: dict) -> list[ExamAnalysisRevision]:
    """Resolve exactly ``QUIZ_SIZE`` distinct, still-available verified revisions."""
    picked: list[ExamAnalysisRevision] = []
    if data.get("revision_ids"):
        for revision_id in data["revision_ids"]:
            revision = (
                await db.execute(
                    select(ExamAnalysisRevision)
                    .where(ExamAnalysisRevision.id == revision_id)
                    .execution_options(populate_existing=True)
                )
            ).scalar_one_or_none()
            if revision is None:
                _error("NOT_FOUND", "教学内容不存在", 404)
            picked.append(revision)
    else:
        from app.models.exam_test import ExamQuestion

        rows = (
            await db.execute(
                select(ExamAnalysisRevision)
                .join(ExamQuestion, ExamQuestion.id == ExamAnalysisRevision.question_id)
                .join(ExamPaper, ExamPaper.id == ExamQuestion.paper_id)
                .where(
                    ExamPaper.id == data["paper_id"],
                    ExamAnalysisRevision.status == "auto_verified",
                )
                # Paper order, not question_key order: the key is a string, so
                # "…:100" would sort before "…:46" and pick the wrong four.
                .order_by(ExamQuestion.number, ExamAnalysisRevision.revision_no.desc())
            )
        ).scalars()
        seen: set[str] = set()
        for revision in rows:
            if revision.question_key in seen:
                continue
            seen.add(revision.question_key)
            picked.append(revision)
    explicit = bool(data.get("revision_ids"))
    unique: list[ExamAnalysisRevision] = []
    keys: set[str] = set()
    for revision in picked:
        if revision.question_key in keys:
            _error("VALIDATION_ERROR", "一道题只能在一份小测里出现一次", 422)
        keys.add(revision.question_key)
        if revision.status != "auto_verified":
            # An explicit list is a promise about *which* questions, so a
            # withdrawn one is refused; a paper scan simply skips it and fills
            # the slot from the next question.
            if explicit:
                _error("CONTENT_REVISION_MISMATCH", "该内容未通过自动核验，不能组成小测")
            continue
        if not await current_revision_available(db, revision):
            if explicit:
                _error("CONTENT_REVISION_MISMATCH", "题目来源已变化，请重新选择核验版本")
            continue
        unique.append(revision)
        if not explicit and len(unique) == QUIZ_SIZE:
            break

    if len(unique) != QUIZ_SIZE:
        _error(
            "VALIDATION_ERROR",
            f"小测需要 {QUIZ_SIZE} 道可用的已核验题目，实际 {len(unique)} 道",
            422,
        )
    return unique


async def create_quiz(db: "AsyncSession", principal: Principal, body) -> dict:
    """Freeze a four-question quiz as four items in one teaching session.

    No new tables: the quiz *is* the session, its questions are the items, and
    its progress is projected from those items' attempts. The legacy
    one-question start shares this shape, so every action below works unchanged.
    """
    await check_write_access(db, principal, "create")
    from app.schemas.teaching import QuizCreate

    data = _body(QuizCreate.model_validate(body) if isinstance(body, dict) else body)
    await db.execute(select(User.id).where(User.id == principal.user_id).with_for_update())
    operation, replayed = await _operation(db, principal, "create_quiz", None, data)
    if replayed:
        return await project_session(
            db, principal, await owned_session(db, principal, operation.result_refs["session_id"]), replayed=True
        )

    revisions = await _quiz_revisions(db, data)
    session = TeachingSession(user_id=principal.user_id)
    db.add(session)
    await db.flush()
    first_item: TeachingItem | None = None
    for ordinal, revision in enumerate(revisions):
        projected = await project_content(db, revision, principal, target="site")
        if projected.get("restricted"):
            _error("CONTENT_REVISION_MISMATCH", "该材料不允许在此入口使用")
        await lock_question_exposure(db, principal.user_id, revision.question_key)
        item = TeachingItem(
            session_id=session.id,
            question_key=revision.question_key,
            content_revision_id=revision.id,
            ordinal=ordinal,
        )
        db.add(item)
        await db.flush()
        first_item = first_item or item
    await ensure_exposure_mapping_state(db, principal.user_id)
    session.current_item_id = first_item.id if first_item else None
    operation.status, operation.result_refs = "completed", {"session_id": session.id}
    await db.flush()
    return await project_session(db, principal, session)


async def _prepare(db: "AsyncSession", principal: Principal, session_id: str, body, kind: str):
    await check_write_access(db, principal, kind)
    schemas: dict[str, type[BaseModel]] = {
        "draft": DraftAnswer,
        "attempt": SubmitAttempt,
        "hint": ItemAction,
        "reveal": ItemAction,
        "feedback": Feedback,
        "complete": CompleteSession,
    }
    schema = schemas[kind]
    data = _body(schema.model_validate(body) if isinstance(body, dict) else body)
    session = await owned_session(db, principal, session_id, lock=True)
    item_id = data.get("item_id") or session.current_item_id
    item = (
        await db.execute(
            select(TeachingItem)
            .where(TeachingItem.id == item_id, TeachingItem.session_id == session.id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if item is None:
        _error("NOT_FOUND", "教学题目不存在", 404)
    revision = (
        await db.execute(
            select(ExamAnalysisRevision)
            .where(ExamAnalysisRevision.id == item.content_revision_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one()
    mapping = await ensure_exposure_mapping_state(db, principal.user_id)
    exposure = await lock_question_exposure(db, principal.user_id, item.question_key)
    disclosure = await _disclosure(db, principal, revision.id)
    await db.execute(select(TeachingItem.id).where(TeachingItem.id == item.id).with_for_update())
    operation, replayed = await _operation(db, principal, kind, session_id, data)
    if replayed:
        return session, item, revision, mapping, exposure, disclosure, operation, data, True
    if data["expected_revision"] != session.revision:
        _error("TEACHING_REVISION_CONFLICT", "教学状态已更新，请刷新后重试")
    if session.status != "active":
        _error("TEACHING_STATE_CONFLICT", "该教学会话已结束")
    target = "external" if principal.actor == "external_agent" else "site"
    if (await project_content(db, revision, principal, target=target)).get("restricted"):
        _error("CONTENT_REVISION_MISMATCH", "内容已撤回或不允许当前用途")
    return session, item, revision, mapping, exposure, disclosure, operation, data, False


async def _finish(db, principal, session, operation, *, replayed=False) -> dict:
    if not replayed:
        session.revision += 1
        session.updated_at = _now()
        operation.status = "completed"
        operation.result_refs = {**operation.result_refs, "session_id": session.id}
        await db.flush()
    result = await project_session(db, principal, session, replayed=replayed)
    result["operation_result"] = operation.result_refs
    return result


async def save_draft(db: "AsyncSession", principal: Principal, session_id: str, body) -> dict:
    session, item, revision, _mapping, _exposure, _disclosure_row, operation, data, replayed = await _prepare(
        db, principal, session_id, body, "draft"
    )
    if not replayed:
        answer = data.get("answer")
        answer = answer.strip().upper() if answer else None
        if answer is not None and answer not in revision.question_payload["options"]:
            _error("VALIDATION_ERROR", "答案必须是有效选项", 422)
        item.draft_answer, item.draft_revision = answer, item.draft_revision + 1
    return await _finish(db, principal, session, operation, replayed=replayed)


async def submit_attempt(db: "AsyncSession", principal: Principal, session_id: str, body) -> dict:
    session, item, revision, mapping, exposure, disclosure, operation, data, replayed = await _prepare(
        db, principal, session_id, body, "attempt"
    )
    if not replayed:
        answer = data["answer"].strip().upper()
        if answer not in revision.question_payload["options"]:
            _error("VALIDATION_ERROR", "答案必须是有效选项", 422)
        untouched = not (exposure.feedback_count or exposure.max_hint_level or exposure.first_answer_available_at)
        initial = untouched and mapping.status == "complete" and principal.actor == "user_ui"
        assistance = {
            "max_hint_level": exposure.max_hint_level,
            "feedback_count": exposure.feedback_count,
            "answer_available": exposure.first_answer_available_at is not None,
            "initial_eligibility": "eligible"
            if initial
            else "unknown"
            if mapping.status != "complete"
            else "ineligible",
            "independence": "unverified" if principal.actor == "external_agent" else "system_observed",
        }
        attempt = TeachingAttempt(
            item_id=item.id,
            attempt_no=item.next_attempt_no,
            user_answer=answer,
            correct=answer == revision.correct_answer,
            grading_version=revision.grading_version,
            role="initial" if initial else "retry",
            answer_origin="external_reported" if principal.actor == "external_agent" else "ui_explicit",
            assistance_snapshot=assistance,
        )
        db.add(attempt)
        await db.flush()
        operation.result_refs = {"attempt_id": attempt.id}
        item.next_attempt_no += 1
        item.last_attempt_id, item.draft_answer = attempt.id, None
        item.state = "answer_revealed" if disclosure.analysis_revealed_at else "graded"
        exposure.feedback_count += 1
        exposure.updated_at = _now()
        if attempt.correct:
            await record_answer_available(
                db, principal.user_id, [item.question_key], origin=attempt.answer_origin, occurred_at=_now()
            )
            disclosure.answer_confirmed_at = disclosure.answer_confirmed_at or _now()
            disclosure.reason = "correct_answer"
        from app.services.local_time import get_user_local_now

        local_now = await get_user_local_now(db, principal.user_id)
        db.add(
            LearningEventOutbox(
                user_id=principal.user_id,
                attempt_id=attempt.id,
                business_operation_key=f"{principal.namespace}:{data['operation_id']}",
                event_type="teaching_attempt",
                flow_id=session.id,
                actor=principal.actor,
                payload={
                    "answer_origin": attempt.answer_origin,
                    "verification_method": "server_graded",
                    "assistance": assistance,
                    "correct": attempt.correct,
                    "event_date": local_now.date().isoformat(),
                    "timezone": str(local_now.tzinfo),
                },
                occurred_at=attempt.occurred_at,
            )
        )
    return await _finish(db, principal, session, operation, replayed=replayed)


async def request_hint(db: "AsyncSession", principal: Principal, session_id: str, body) -> dict:
    session, item, revision, _mapping, exposure, _disclosure_row, operation, _data, replayed = await _prepare(
        db, principal, session_id, body, "hint"
    )
    if not replayed:
        item.hint_level = min(item.hint_level + 1, len(revision.reviewed_hints))
        exposure.max_hint_level = max(exposure.max_hint_level, item.hint_level)
        exposure.updated_at = _now()
        if item.state != "answer_revealed":
            item.state = "coaching"
    return await _finish(db, principal, session, operation, replayed=replayed)


async def reveal_answer(db: "AsyncSession", principal: Principal, session_id: str, body) -> dict:
    session, item, _revision, _mapping, _exposure, disclosure, operation, _data, replayed = await _prepare(
        db, principal, session_id, body, "reveal"
    )
    if not replayed:
        if principal.actor == "external_agent":
            require_scope(principal, "teaching:analysis:read")
        await record_answer_available(
            db, principal.user_id, [item.question_key], origin="explicit_reveal", occurred_at=_now()
        )
        disclosure.analysis_revealed_at = disclosure.analysis_revealed_at or _now()
        disclosure.reason, item.state = "explicit_reveal", "answer_revealed"
    return await _finish(db, principal, session, operation, replayed=replayed)


async def record_feedback(db: "AsyncSession", principal: Principal, session_id: str, body) -> dict:
    session, _item, _revision, _mapping, _exposure, _disclosure_row, operation, data, replayed = await _prepare(
        db, principal, session_id, body, "feedback"
    )
    if not replayed:
        if not data["content"].strip():
            _error("VALIDATION_ERROR", "反馈不能为空", 422)
        db.add(
            TeachingFeedback(
                user_id=principal.user_id,
                session_id=session.id,
                source_connection_id=principal.connection_id,
                operation_id=data["operation_id"],
                content=data["content"],
                source_kind=principal.actor,
                expires_at=_now() + timedelta(hours=24),
            )
        )
    return await _finish(db, principal, session, operation, replayed=replayed)


async def complete_session(db: "AsyncSession", principal: Principal, session_id: str, body) -> dict:
    session, item, _revision, _mapping, _exposure, _disclosure_row, operation, data, replayed = await _prepare(
        db, principal, session_id, body, "complete"
    )
    if not replayed:
        session.status = "abandoned" if data["action"] == "abandon" else "completed"
        item.state = "completed"
    return await _finish(db, principal, session, operation, replayed=replayed)
