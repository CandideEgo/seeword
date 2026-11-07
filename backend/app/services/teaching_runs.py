"""Durable execution and independently reconnectable, permission-projected events.

A run belongs to a chat (``conversation_id``) and optionally to one teaching
task (``session_id``). Lock order is always conversation → session → run;
the lock-free periods are the model calls themselves.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError
from app.models.teaching import TeachingSession
from app.models.v2_runtime import AgentRun, AgentRunEvent, AgentStep, TutorConversation
from app.services.external_connection_service import utc
from app.services.teaching import dialogue
from app.services.teaching import service as core
from app.services.teaching.context import get_learning_context
from app.services.teaching_gateway import choose_intent, require_gateway, tutor_reply
from app.services.v2_access import require_access
from app.services.v2_schema import require_conversation_schema, require_teaching_schema

TERMINAL = {"succeeded", "failed", "cancelled", "needs_retry"}


def summary(run: AgentRun) -> dict:
    return {
        "id": run.id,
        "run_id": run.id,
        "session_id": run.session_id,
        "conversation_id": run.conversation_id,
        "status": run.status,
        "last_sequence": run.last_sequence,
        "cards": [],
        "error_code": run.error_code,
        "state_url": f"/api/v1/teaching/runs/{run.id}",
        "events_url": f"/api/v1/teaching/runs/{run.id}/events",
        "response_mode": run.response_mode,
    }


def projected_cards(run: AgentRun, state: dict) -> list[dict]:
    cards = list(state["cards"])
    if any(card["kind"] == "question" for card in cards):
        cards.append(
            {
                "schema_version": 1,
                "card_id": f"{run.id}:action",
                "session_id": state["id"],
                "item_id": state["current_item_id"],
                "session_revision": state["revision"],
                "kind": "status",
                "payload": {
                    "code": "TEACHING_ACTION_REQUIRED",
                    "message": "可以回到题面作答，或选择分级提示和揭晓解析。",
                },
            }
        )
    return cards


async def _owned(db: AsyncSession, user_id: str, run_id: str, *, lock: bool = False) -> AgentRun:
    query = select(AgentRun).where(AgentRun.id == run_id, AgentRun.user_id == user_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    run = (await db.execute(query)).scalar_one_or_none()
    if run is None:
        raise NotFoundError("讲解任务不存在")
    return run


def append_event(db: AsyncSession, run: AgentRun, kind: str, payload: dict | None = None) -> None:
    run.last_sequence += 1
    db.add(
        AgentRunEvent(
            run_id=run.id,
            sequence=run.last_sequence,
            type=kind,
            session_revision=run.bound_session_revision,
            safe_payload=payload or {},
        )
    )


async def _lock_target(
    db: AsyncSession, principal, run: AgentRun, *, lock: bool = True
) -> tuple[TutorConversation | None, TeachingSession | None]:
    """Conversation first, then session; both are optional for a plain chat.

    A run queued before P02.3 has no ``conversation_id``; execution settles it
    with TEACHING_STATE_CONFLICT rather than inventing a transcript owner. The
    events read path still resolves its session's task chat by lookup.
    """
    conversation = None
    if run.conversation_id is not None:
        conversation = await dialogue.owned(db, principal, run.conversation_id, lock=lock)
    session = None
    if run.session_id is not None:
        session = await core.owned_session(db, principal, run.session_id, lock=lock)
    return conversation, session


async def _require_run_switches(db: AsyncSession, run: AgentRun, conversation: TutorConversation | None) -> None:
    await require_access(db, run.user_id, "teaching_runs_enabled")
    if run.response_mode == "conversation":
        await require_access(db, run.user_id, "teaching_dialogue_enabled")
        if conversation is not None and conversation.kind == "chat":
            await require_access(db, run.user_id, "teaching_conversations_enabled")


def _request_digest(conversation, session_id: str | None, message: str, expected_revision, response_mode: str) -> str:
    if conversation is not None and conversation.kind == "chat":
        # Chat receipt namespace: the task is part of the request, so reusing an
        # operation id for another task is a conflict, not a silent replay.
        request = {
            "conversation_id": conversation.id,
            "session_id": session_id,
            "message": message,
            "response_mode": response_mode,
        }
    else:
        request = {"session_id": session_id, "message": message, "expected_revision": expected_revision}
        # Preserve the legacy cards digest so existing receipts still replay.
        if response_mode != "cards":
            request["response_mode"] = response_mode
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


async def _start_run(
    db: AsyncSession,
    principal,
    *,
    conversation: TutorConversation | None,
    session,
    message: str,
    operation_id: str,
    expected_revision: int | None,
    response_mode: str,
) -> dict:
    """Shared idempotent start; the caller already holds the conversation/session locks."""
    digest = _request_digest(conversation, session.id if session else None, message, expected_revision, response_mode)
    prior = (
        await db.execute(
            select(AgentRun).where(AgentRun.user_id == principal.user_id, AgentRun.operation_id == operation_id)
        )
    ).scalar_one_or_none()
    if prior:
        if prior.request_hash != digest:
            raise AppError(409, "IDEMPOTENCY_CONFLICT", "操作编号已用于不同请求")
        return summary(prior)
    if session is not None:
        if expected_revision != session.revision:
            raise AppError(409, "TEACHING_REVISION_CONFLICT", "教学状态已更新，请重新读取")
        if session.status != "active":
            raise AppError(409, "TEACHING_STATE_CONFLICT", "教学会话已结束")
    active = (await db.execute(select(AgentRun).where(AgentRun.status.in_(["queued", "running"])))).scalars().all()
    if any(row.user_id == principal.user_id for row in active) or len(active) >= 4:
        raise AppError(429, "CONCURRENCY_LIMITED", "讲解任务正在处理中，请稍后重试")
    now = datetime.now(UTC)
    run = AgentRun(
        user_id=principal.user_id,
        session_id=session.id if session else None,
        conversation_id=conversation.id if conversation else None,
        operation_id=operation_id,
        request_hash=digest,
        message=message,
        response_mode=response_mode,
        bound_session_revision=session.revision if session else None,
        queue_deadline_at=now + timedelta(seconds=60),
        last_sequence=0,
    )
    db.add(run)
    await db.flush()
    if response_mode == "conversation":
        if conversation is None:
            raise AppError(409, "TEACHING_STATE_CONFLICT", "对话不存在")
        context = await _conversation_context(db, principal, session)
        await dialogue.append(db, run, context, "user", {"text": message})
        if session is not None:
            await dialogue.associate(db, conversation.id, session.id)
        dialogue.touch(conversation, message)
    return summary(run)


async def _conversation_context(db: AsyncSession, principal, session) -> dict | None:
    if session is None:
        return None
    context = (await get_learning_context(db, principal, session.id)).model_dump(mode="json")
    if context["material"]["restricted"]:
        raise AppError(409, "CONTENT_RESTRICTED", "教学内容不可用")
    return context


def dispatch_run(run_id: str) -> None:
    """Queue the worker; the committed queued row is the durable intent."""
    from app.tasks.celery_app import celery_app

    try:
        celery_app.send_task("app.tasks.teaching_tasks.execute_teaching_run", args=[run_id], queue="teaching")
    except Exception:
        from app.core.logging import get_logger

        get_logger(__name__).warning("teaching_run_dispatch_deferred", run_id=run_id)


async def start_conversation_turn(db: AsyncSession, principal, conversation_id: str, body) -> dict:
    """A standalone chat turn; a task reference is optional and version-bound."""
    await require_access(db, principal.user_id, "teaching_runs_enabled")
    await require_access(db, principal.user_id, "teaching_dialogue_enabled")
    await require_access(db, principal.user_id, "teaching_conversations_enabled")
    await require_conversation_schema(db)
    require_gateway()
    if db.get_bind().dialect.name == "postgresql":
        await db.execute(select(func.pg_advisory_xact_lock(192837461)))
    conversation = await dialogue.owned_chat(db, principal, conversation_id, lock=True)
    if conversation.status != "active":
        raise AppError(409, "TEACHING_STATE_CONFLICT", "对话已归档")
    session = None
    if body.session_id is not None:
        if body.expected_revision is None:
            raise AppError(422, "VALIDATION_ERROR", "任务对话必须提供当前教学版本")
        session = await core.owned_session(db, principal, body.session_id, lock=True)
    elif body.expected_revision is not None:
        raise AppError(422, "VALIDATION_ERROR", "无任务对话不接受教学版本")
    return await _start_run(
        db,
        principal,
        conversation=conversation,
        session=session,
        message=body.message,
        operation_id=body.operation_id,
        expected_revision=body.expected_revision,
        response_mode="conversation",
    )


async def create(db: AsyncSession, principal, session_id: str, body, *, response_mode="cards") -> dict:
    if principal.actor != "user_ui":
        raise AppError(403, "INSUFFICIENT_SCOPE", "只能由网页明确创建讲解任务")
    await require_access(db, principal.user_id, "teaching_runs_enabled")
    # Every mode here selects ``AgentRun``, which now has conversation columns;
    # a database stopped before P02.3 must answer 503, not 500.
    await require_teaching_schema(db)
    if response_mode not in {"cards", "conversation"}:
        raise AppError(422, "VALIDATION_ERROR", "未知讲解模式")
    if response_mode == "conversation":
        await require_access(db, principal.user_id, "teaching_dialogue_enabled")
    require_gateway()
    # Serialize starts before reading receipts, including the same operation on
    # two different sessions. Other teaching writes do not acquire this lock.
    if db.get_bind().dialect.name == "postgresql":
        await db.execute(select(func.pg_advisory_xact_lock(192837461)))
    conversation = None
    if response_mode == "conversation":
        # Resolve/create the task chat first so the lock order is conversation → session.
        await core.owned_session(db, principal, session_id)
        conversation = await dialogue.task_conversation(db, principal, session_id)
    session = await core.owned_session(db, principal, session_id, lock=True)
    return await _start_run(
        db,
        principal,
        conversation=conversation,
        session=session,
        message=body.message,
        operation_id=body.operation_id,
        expected_revision=body.expected_revision,
        response_mode=response_mode,
    )


async def get(db: AsyncSession, principal, run_id: str) -> dict:
    await require_teaching_schema(db)
    run = await _owned(db, principal.user_id, run_id)
    result = summary(run)
    if run.session_id is None:
        return result
    state = await core.get_session(db, principal, run.session_id)
    if state["revision"] == run.bound_session_revision:
        references = (
            await db.execute(
                select(AgentRunEvent.safe_payload).where(
                    AgentRunEvent.run_id == run.id, AgentRunEvent.type == "card.upsert"
                )
            )
        ).scalars()
        ids = {value.get("card_id") for value in references}
        result["cards"] = [card for card in projected_cards(run, state) if card["card_id"] in ids]
    return result


async def events(db: AsyncSession, principal, run_id: str, after: int) -> tuple[list[dict], str]:
    await require_teaching_schema(db)
    run = await _owned(db, principal.user_id, run_id)
    if after > run.last_sequence:
        raise AppError(409, "EVENT_CURSOR_INVALID", "事件游标超出当前运行范围")
    if utc(run.created_at) < datetime.now(UTC) - timedelta(hours=24):
        raise AppError(410, "EVENT_CURSOR_EXPIRED", "运行事件已过期，请读取当前教学状态")
    conversation_id = run.conversation_id
    if conversation_id is None and run.response_mode == "conversation" and run.session_id is not None:
        # A conversation-mode run that predates P02.3 still points at its
        # session's task chat; resolve it without creating or locking.
        conversation_id = await dialogue.task_conversation_id(db, principal, run.session_id)
    current_cards: dict[str, dict] = {}
    state_revision = None
    if run.session_id is not None:
        state = await core.get_session(db, principal, run.session_id)
        current_cards = {card["card_id"]: card for card in projected_cards(run, state)}
        state_revision = state["revision"]
    rows = (
        await db.execute(
            select(AgentRunEvent)
            .where(AgentRunEvent.run_id == run_id, AgentRunEvent.sequence > after)
            .order_by(AgentRunEvent.sequence)
        )
    ).scalars()
    result = []
    for row in rows:
        kind, payload = row.type, row.safe_payload
        if kind == "card.upsert":
            card = current_cards.get(str(payload.get("card_id", "")))
            if card is None or state_revision != row.session_revision:
                kind, payload = "content.restricted", {"card_id": payload.get("card_id")}
            else:
                payload = {"card": card}
        elif kind == "message.upsert":
            message = await dialogue.event_message(db, principal, conversation_id or "", payload.get("message_id", ""))
            if message is None or message["restricted"]:
                kind, payload = "content.restricted", {"message_id": payload.get("message_id")}
            else:
                payload = {"message": message}
        elif kind == "message.block":
            projected = await dialogue.event_block(
                db,
                principal,
                conversation_id or "",
                payload.get("message_id", ""),
                payload.get("block_id", ""),
            )
            if projected is None:
                kind, payload = "content.restricted", {"message_id": payload.get("message_id")}
            else:
                payload = projected
        result.append(
            {
                "schema_version": 1,
                "run_id": run.id,
                "sequence": row.sequence,
                "session_revision": row.session_revision,
                "type": kind,
                "payload": payload,
            }
        )
    return result, run.status


async def cancel(db: AsyncSession, principal, run_id: str) -> dict:
    await require_teaching_schema(db)
    observed = await _owned(db, principal.user_id, run_id)
    await _lock_target(db, principal, observed, lock=True)
    run = await _owned(db, principal.user_id, run_id, lock=True)
    if run.status not in TERMINAL:
        run.cancel_requested_at = datetime.now(UTC)
        run.status, run.finished_at = "cancelled", datetime.now(UTC)
        append_event(db, run, "run.cancelled", {"status": "cancelled"})
    return summary(run)


async def _task_state(db: AsyncSession, principal, run: AgentRun, session):
    """Verify the task is still model-usable at model-dispatch and publish time."""
    from app.models.teaching import ExamAnalysisRevision
    from app.services.teaching.content import may_disclose

    if session is None:
        return None
    revision_id = await dialogue.task_revision_id(db, principal, session.id)
    revision = await db.get(ExamAnalysisRevision, revision_id, with_for_update=True)
    if revision is None or not may_disclose(revision, principal, "model"):
        raise AppError(409, "CONTENT_RESTRICTED", "材料当前不允许模型处理")
    return revision_id


async def execute(run_id: str) -> None:
    """Committed dispatch intent is never automatically repeated after uncertainty."""
    from app.core.database import get_async_session_maker

    maker = get_async_session_maker()
    async with maker() as db:
        found = await db.get(AgentRun, run_id)
        if found is None:
            return
        owner_id = found.user_id  # read before any rollback expires the instance
        principal = core.Principal(owner_id, actor="internal_agent")
        now = datetime.now(UTC)
        try:
            conversation, session = await _lock_target(db, principal, found, lock=True)
        except AppError as exc:
            # A vanished chat or task must settle the queued run instead of
            # leaving the worker to retry it until the sweep notices.
            await db.rollback()
            run = await _owned(db, owner_id, run_id, lock=True)
            if run.status == "queued":
                run.status, run.error_code, run.finished_at = "failed", exc.code, now
                append_event(db, run, "run.failed", {"error_code": exc.code})
                await db.commit()
            return
        run = await _owned(db, owner_id, run_id, lock=True)
        if run.status != "queued":
            return
        if utc(run.queue_deadline_at) < now:
            run.status, run.error_code, run.finished_at = "failed", "QUEUE_TIMEOUT", now
            append_event(db, run, "run.failed", {"error_code": run.error_code})
            await db.commit()
            return
        try:
            await _require_run_switches(db, run, conversation)
            state = None
            context = None
            if session is not None:
                state = await core.get_session(db, principal, session.id)
                if state["revision"] != run.bound_session_revision:
                    raise AppError(409, "TEACHING_CONTEXT_CHANGED", "教学状态已变化")
                await _task_state(db, principal, run, session)
            if run.response_mode == "conversation":
                if conversation is None:
                    # No chat means nothing can own the transcript; settle
                    # instead of failing the insert on a NOT NULL column.
                    raise AppError(409, "TEACHING_STATE_CONFLICT", "对话已不存在")
                context = await dialogue.model_input(db, principal, run)
            elif session is None:
                raise AppError(409, "TEACHING_STATE_CONFLICT", "讲解任务缺少教学会话")
            else:
                context = (await get_learning_context(db, principal, session.id)).model_dump(mode="json")
            if context is None:
                raise AppError(409, "TEACHING_STATE_CONFLICT", "讲解任务缺少上下文")
            dispatch_context: dict = context
            general = run.response_mode == "conversation" and dispatch_context["learning_context"] is None
            revealed = bool(state) and any(card["kind"] == "analysis" for card in (state or {}).get("cards", []))
            run.status = "running"
            run.lease_epoch += 1
            epoch = run.lease_epoch
            run.execution_deadline_at = now + timedelta(seconds=30)
            run.lease_expires_at = run.execution_deadline_at
            deadline = run.execution_deadline_at
            message = run.message or ""
            logical_call = str(uuid.uuid4())
            step = AgentStep(
                run_id=run.id,
                seq=1,
                kind="policy" if run.response_mode == "conversation" and not general and not revealed else "model",
                status="dispatched",
                lease_epoch=epoch,
                logical_call_id=logical_call,
            )
            db.add(step)
            append_event(db, run, "run.started", {"status": "running"})
            await db.commit()
        except AppError as exc:
            run.status, run.error_code, run.finished_at = "needs_retry", exc.code, now
            append_event(db, run, "run.failed", {"error_code": exc.code})
            await db.commit()
            return
        run_target = {
            "conversation_id": run.conversation_id,
            "session_id": run.session_id,
            "general": general,
            "revealed": revealed,
        }

    intent, error, reply = None, None, None

    async def validate_dispatch():
        # Key issuance is network I/O. Recheck after it, immediately before the
        # model request, with no database transaction held across that request.
        async with maker() as check_db:
            current = await _owned(check_db, principal.user_id, run_id)
            check_conversation, check_session = await _lock_target(check_db, principal, current, lock=True)
            checked = await _owned(check_db, principal.user_id, run_id, lock=True)
            await _require_run_switches(check_db, checked, check_conversation)
            if (
                checked.status != "running"
                or checked.lease_epoch != epoch
                or checked.cancel_requested_at
                or (check_session is not None and check_session.revision != checked.bound_session_revision)
            ):
                raise AppError(409, "TEACHING_CONTEXT_CHANGED", "教学状态已变化")
            if checked.session_id is not None:
                await _task_state(check_db, principal, checked, check_session)
            if checked.response_mode == "conversation":
                return await dialogue.model_input(check_db, principal, checked)
            return (await get_learning_context(check_db, principal, check_session.id)).model_dump(mode="json")

    from app.core.config import get_settings

    if (
        run.response_mode == "conversation"
        and get_settings().teaching_streaming_enabled
        and (run_target["general"] or run_target["revealed"])
    ):
        # P02.2: publish validated text blocks as the model writes them.
        await _stream_turn(maker, principal, run_id, epoch, deadline, message)
        return

    try:
        # Before reveal, only trusted hint/actions are displayed; no answer is sent to a model.
        if run.response_mode == "conversation":
            if run_target["general"] or run_target["revealed"]:
                reply = await tutor_reply(
                    principal.user_id,
                    run_id,
                    logical_call,
                    message,
                    context,
                    deadline,
                    before_dispatch=validate_dispatch,
                )
            else:
                reply = dialogue.before_reveal()
        elif run_target["revealed"]:
            intent = await choose_intent(
                principal.user_id, run_id, logical_call, message, context, deadline, before_dispatch=validate_dispatch
            )
        else:
            intent = "suggest_retry"
    except AppError as exc:
        error = exc.code
    async with maker() as db:
        try:
            current = await _owned(db, principal.user_id, run_id)
            conversation, session = await _lock_target(db, principal, current, lock=True)
            current = await _owned(db, principal.user_id, run_id, lock=True)
        except AppError:
            # The chat/run was deleted while the model was running; nothing is
            # left to publish and the execution log is already gone.
            return
        step = (await db.execute(select(AgentStep).where(AgentStep.run_id == run_id, AgentStep.seq == 1))).scalar_one()
        state = None
        # A cancelled or obsolete lease can settle usage in the gateway but cannot publish.
        if current.status != "running" or current.lease_epoch != epoch:
            step.status = "uncertain" if error else "completed"
            await db.commit()
            return
        try:
            await _require_run_switches(db, current, conversation)
            if session is not None:
                state = await core.get_session(db, principal, session.id)
                await _task_state(db, principal, current, session)
                if session.revision != current.bound_session_revision:
                    error = "TEACHING_CONTEXT_CHANGED"
            if datetime.now(UTC) > utc(deadline):
                error = error or "EXECUTION_TIMEOUT"
        except AppError as exc:
            error = exc.code
        if error:
            current.status, current.error_code = "needs_retry", error
            step.status = "uncertain"
            append_event(db, current, "run.failed", {"error_code": error})
        elif current.response_mode == "conversation":
            try:
                final_context = await dialogue.model_input(db, principal, current)
                if reply is None:
                    raise AppError(502, "AI_SERVICE_UNAVAILABLE", "导师回复缺失")
                if (final_context["learning_context"] is None) != run_target["general"]:
                    raise AppError(409, "TEACHING_CONTEXT_CHANGED", "对话任务状态已变化")
                dialogue.validate_reply(reply, final_context["learning_context"])
            except AppError as exc:
                current.status, current.error_code = "needs_retry", exc.code
                step.status = "uncertain"
                append_event(db, current, "run.failed", {"error_code": exc.code})
            else:
                response = await dialogue.append(
                    db,
                    current,
                    final_context["learning_context"],
                    "assistant",
                    reply.model_dump(),
                    requires_reveal=reply.source == "model" and final_context["learning_context"] is not None,
                )
                step.status, step.safe_result = "completed", {"message_id": response.id}
                current.status = "succeeded"
                append_event(db, current, "message.upsert", {"message_id": response.id})
                append_event(db, current, "run.completed", {"status": "succeeded"})
        else:
            kind = {"show_analysis": "analysis", "show_evidence": "evidence", "suggest_retry": "status"}[
                intent or "suggest_retry"
            ]
            assert state is not None
            cards = [card for card in projected_cards(current, state) if card["kind"] == kind]
            for card in cards:
                # Events persist references, not privileged response snapshots.
                append_event(db, current, "card.upsert", {"card_id": card["card_id"]})
            step.status, step.safe_result = "completed", {"intent": intent}
            current.status = "succeeded"
            append_event(db, current, "run.completed", {"status": "succeeded"})
        current.finished_at = datetime.now(UTC)
        await db.commit()


async def sweep(db: AsyncSession) -> list[str]:
    now = datetime.now(UTC)
    rows = (
        await db.execute(
            select(AgentRun).where(AgentRun.status.in_(["queued", "running"])).with_for_update(skip_locked=True)
        )
    ).scalars()
    dispatch, expired_runs = [], []
    for run in rows:
        deadline = run.queue_deadline_at if run.status == "queued" else run.lease_expires_at
        if deadline is None or utc(deadline) < now:
            run.status, run.error_code, run.finished_at = "needs_retry", "EXECUTION_UNCERTAIN", now
            append_event(db, run, "run.failed", {"error_code": run.error_code})
            expired_runs.append(run.id)
        elif run.status == "queued":
            dispatch.append(run.id)
    if expired_runs:
        from sqlalchemy import update

        from app.models.v2_runtime import TeachingMessage as _TeachingMessage
        from app.services.v2_schema import has_tables

        if await has_tables(db, ("teaching_messages",)):
            await db.execute(
                update(_TeachingMessage)
                .where(_TeachingMessage.run_id.in_(expired_runs), _TeachingMessage.status == "streaming")
                .values(status="interrupted")
            )
    old = select(AgentRun.id).where(AgentRun.created_at < now - timedelta(hours=24), AgentRun.status.in_(TERMINAL))
    await db.execute(delete(AgentRunEvent).where(AgentRunEvent.run_id.in_(old)))
    await db.execute(delete(AgentStep).where(AgentStep.run_id.in_(old)))
    from sqlalchemy import update

    await db.execute(update(AgentRun).where(AgentRun.id.in_(old)).values(message=None))
    from app.models.teaching import TeachingFeedback

    await db.execute(delete(TeachingFeedback).where(TeachingFeedback.expires_at <= now))
    await db.commit()
    return dispatch


class _StreamStoppedError(Exception):
    """Publication stopped mid-stream; ``reason`` decides how the run settles."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


async def _stream_turn(maker, principal, run_id: str, epoch: int, deadline, message: str) -> None:
    """Consume the model stream, publish committed blocks, then settle the run.

    Every block is its own short transaction under the conversation lock (then
    the session lock when the turn is about a task, then the run lock); the
    model request never holds any of them. A cancelled/fenced run stops
    publishing but the generator keeps draining upstream for settlement.
    """
    from app.models.teaching import ExamAnalysisRevision
    from app.models.v2_runtime import AgentStep, TeachingMessage
    from app.services.teaching.content import may_disclose
    from app.services.teaching.streaming import CitationStream
    from app.services.teaching_gateway import stream_tutor_reply

    held: dict = {"general": False, "content_revision_id": None, "source_ids": [], "text": "", "citations": []}
    message_id: str | None = None
    ordinal = 0
    published_text: list[str] = []

    async def dispatch_context():
        async with maker() as db:
            current = await _owned(db, principal.user_id, run_id)
            conversation, session = await _lock_target(db, principal, current, lock=True)
            checked = await _owned(db, principal.user_id, run_id, lock=True)
            await _require_run_switches(db, checked, conversation)
            if (
                checked.status != "running"
                or checked.lease_epoch != epoch
                or checked.cancel_requested_at
                or (session is not None and session.revision != checked.bound_session_revision)
            ):
                raise AppError(409, "TEACHING_CONTEXT_CHANGED", "教学状态已变化")
            if session is not None:
                revision_id = await dialogue.task_revision_id(db, principal, session.id)
                revision = await db.get(ExamAnalysisRevision, revision_id, with_for_update=True)
                if revision is None or not may_disclose(revision, principal, "model"):
                    raise AppError(409, "CONTENT_RESTRICTED", "材料当前不允许模型处理")
                held["content_revision_id"] = revision_id
            value = await dialogue.model_input(db, principal, checked)
            held["general"] = value["learning_context"] is None
            held["source_ids"] = (
                [card["card_id"] for card in dialogue.sources(value["learning_context"])]
                if value["learning_context"] is not None
                else []
            )
            return value

    async def publish(text: str) -> None:
        nonlocal message_id, ordinal
        async with maker() as db:
            # Same lock order as every other writer: conversation, session, run.
            try:
                current = await _owned(db, principal.user_id, run_id)
                conversation, session = await _lock_target(db, principal, current, lock=True)
                current = await _owned(db, principal.user_id, run_id, lock=True)
            except AppError:
                raise _StreamStoppedError("cancelled") from None
            if current.status != "running" or current.lease_epoch != epoch or current.cancel_requested_at:
                raise _StreamStoppedError("cancelled")
            await _require_run_switches(db, current, conversation)
            if session is not None:
                if session.revision != current.bound_session_revision:
                    raise _StreamStoppedError("rights")
                revision = await db.get(ExamAnalysisRevision, held["content_revision_id"])
                if revision is None or not may_disclose(revision, principal, "model"):
                    raise _StreamStoppedError("rights")
            if message_id is None:
                context = await dialogue.model_input(db, principal, current)
                row = await dialogue.append_streaming(
                    db, current, context["learning_context"], requires_reveal=session is not None
                )
                message_id = row.id
            else:
                row = await db.get(TeachingMessage, message_id)
            ordinal += 1
            block = await dialogue.append_block(db, row, ordinal, text)
            append_event(
                db,
                current,
                "message.block",
                {"message_id": row.id, "block_id": block.id, "ordinal": ordinal},
            )
            published_text.append(text)
            await db.commit()

    def remember_text(parser) -> None:
        if parser is None:
            return
        source_ids = held.get("source_ids") or []
        # Only text that was actually committed as blocks may appear in the
        # message body: a cancelled/failed tail was never published.
        held["text"] = "".join(published_text)
        if held["general"]:
            held["citations"] = []
        else:
            held["citations"] = [source_ids[index - 1] for index in parser.citations if 0 < index <= len(source_ids)]

    async def settle(error_code: str | None, done: dict | None, parser) -> None:
        remember_text(parser)
        async with maker() as db:
            try:
                current = await _owned(db, principal.user_id, run_id)
                conversation, session = await _lock_target(db, principal, current, lock=True)
                current = await _owned(db, principal.user_id, run_id, lock=True)
            except AppError:
                return
            step = (
                await db.execute(select(AgentStep).where(AgentStep.run_id == run_id, AgentStep.seq == 1))
            ).scalar_one()
            row = await db.get(TeachingMessage, message_id) if message_id else None

            def mark_interrupted() -> None:
                if row is not None and row.status == "streaming":
                    dialogue.finalize(
                        row,
                        {
                            "text": held.get("text", ""),
                            "citation_ids": held.get("citations", []),
                            "suggested_answer": None,
                        },
                        "interrupted",
                    )

            if current.status != "running" or current.lease_epoch != epoch:
                # Cancelled or superseded: publication stays stopped; the step
                # record is the only bookkeeping we may still write.
                mark_interrupted()
                step.status = "uncertain"
                await db.commit()
                return
            if error_code is None:
                # Re-check what the last block transaction checked: a user
                # action, a withdrawal or the deadline may have landed between
                # the final block and this commit.
                try:
                    await _require_run_switches(db, current, conversation)
                except AppError as exc:
                    error_code = exc.code
                if session is not None and error_code is None:
                    from app.services.teaching.content import may_disclose

                    revision = await db.get(ExamAnalysisRevision, held["content_revision_id"])
                    if session.revision != current.bound_session_revision:
                        error_code = "TEACHING_CONTEXT_CHANGED"
                    elif revision is None or not may_disclose(revision, principal, "model"):
                        error_code = "CONTENT_RESTRICTED"
                if datetime.now(UTC) > utc(deadline):
                    error_code = error_code or "EXECUTION_TIMEOUT"
            citations = held.get("citations") or []
            if error_code is not None:
                mark_interrupted()
                current.status, current.error_code = "needs_retry", error_code
                step.status = "uncertain"
                append_event(db, current, "run.failed", {"error_code": error_code})
            elif row is None or not (held.get("text") or "").strip() or (not held["general"] and not citations):
                mark_interrupted()
                current.status, current.error_code = "needs_retry", "AI_SERVICE_UNAVAILABLE"
                step.status = "uncertain"
                append_event(db, current, "run.failed", {"error_code": current.error_code})
            else:
                dialogue.finalize(
                    row,
                    {"text": held["text"], "citation_ids": citations, "suggested_answer": None},
                    "complete",
                )
                step.status = "completed"
                step.safe_result = {
                    "streamed": True,
                    "usage": (done or {}).get("usage"),
                    "usage_status": (done or {}).get("usage_status", "missing"),
                }
                current.status = "succeeded"
                append_event(db, current, "message.upsert", {"message_id": row.id})
                append_event(db, current, "run.completed", {"status": "succeeded"})
            current.finished_at = datetime.now(UTC)
            await db.commit()

    parser = None
    done = None
    error_code = None
    stopped = None
    try:
        # The whole turn — model stream and block commits — shares one budget.
        remaining = (deadline - datetime.now(UTC)).total_seconds()
        async with asyncio.timeout(max(0.001, remaining)):
            async for event in stream_tutor_reply(
                principal.user_id, run_id, str(uuid.uuid4()), message, deadline, before_dispatch=dispatch_context
            ):
                if event["type"] == "delta":
                    if parser is None:
                        parser = CitationStream(len(held["source_ids"]), general=held["general"])
                    for block in parser.feed(event["text"]):
                        await publish(block)
                elif event["type"] == "done":
                    done = event
    except TimeoutError:
        error_code = "EXECUTION_TIMEOUT"
    except _StreamStoppedError as exc:
        stopped = exc.reason
    except AppError as exc:
        error_code = exc.code
    except Exception:
        # A database/gateway fault must still settle, not leave the message
        # in ``streaming`` (the sweep is the crash-only safety net).
        error_code = "AI_SERVICE_UNAVAILABLE"

    if parser is not None and stopped is None:
        try:
            for block in parser.finish():
                await publish(block)
        except _StreamStoppedError as exc:
            stopped = exc.reason
        except AppError as exc:
            error_code = exc.code
    elif parser is None and error_code is None and stopped is None:
        error_code = "AI_SERVICE_UNAVAILABLE"

    if stopped == "cancelled":
        await settle(None, done, parser)
        return
    if stopped == "rights":
        error_code = error_code or "CONTENT_RESTRICTED"
    await settle(error_code, done, parser)
