"""Durable chat transcripts, projected with current material permissions.

A ``TutorConversation`` owns the transcript. Messages that talk about a
teaching task also carry ``session_id``/``content_revision_id`` and are
projected through that task's current rights; standalone messages are visible
to their owner only. The legacy per-session endpoint maps to one ``task``
conversation so its transcript, order and IDs are unchanged.

No commit, model call or second set of teaching rules lives here. Callers own
the transaction and hold the conversation lock while appending.
"""

import copy
import json
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import Row, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.teaching import TeachingItem, TeachingSession
from app.models.v2_runtime import (
    AgentRun,
    TeachingMessage,
    TeachingMessageBlock,
    TutorConversation,
    TutorConversationTask,
)
from app.schemas.teaching_dialogue import TutorReply
from app.services.external_connection_service import utc
from app.services.teaching.context import get_learning_context
from app.services.teaching.principal import Principal


def _allowed(principal: Principal) -> None:
    if principal.actor not in {"user_ui", "internal_agent"}:
        raise AppError(403, "INSUFFICIENT_SCOPE", "此入口未授权读取任务对话")


def sources(context: dict) -> list[dict]:
    return [card for card in context["cards"] if card["kind"] in {"question", "analysis", "evidence"}]


# --- conversations -----------------------------------------------------------


async def owned(db: AsyncSession, principal: Principal, conversation_id: str, *, lock=False) -> TutorConversation:
    """The owner's conversation; every writer takes ``lock`` before appending."""
    query = select(TutorConversation).where(
        TutorConversation.id == conversation_id, TutorConversation.user_id == principal.user_id
    )
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        raise AppError(404, "NOT_FOUND", "对话不存在")
    return row


async def owned_chat(db: AsyncSession, principal: Principal, conversation_id: str, *, lock=False) -> TutorConversation:
    """The new chat API only manages standalone chats, never task transcripts."""
    row = await owned(db, principal, conversation_id, lock=lock)
    if row.kind != "chat":
        raise AppError(404, "NOT_FOUND", "对话不存在")
    return row


async def task_conversation_id(db: AsyncSession, principal: Principal, session_id: str) -> str | None:
    """Read-only lookup used when projecting events of a pre-P02.3 run."""
    value = await db.scalar(
        select(TutorConversation.id).where(
            TutorConversation.user_id == principal.user_id,
            TutorConversation.task_session_id == session_id,
        )
    )
    return str(value) if value is not None else None


async def task_revision_id(db: AsyncSession, principal: Principal, session_id: str) -> str:
    """The task's current content revision; a session has one item today."""
    item = (
        await db.execute(
            select(TeachingItem).where(TeachingItem.session_id == session_id).order_by(TeachingItem.ordinal).limit(1)
        )
    ).scalar_one_or_none()
    if item is None:
        raise AppError(409, "TEACHING_STATE_CONFLICT", "当前教学题目不可用")
    return item.content_revision_id


async def task_conversation(db: AsyncSession, principal: Principal, session_id: str) -> TutorConversation:
    """The legacy per-session chat; created lazily and unique per session.

    Callers use this *before* taking the session lock, so the global lock
    order (conversation → session → run) holds on every write path.
    """
    query = (
        select(TutorConversation)
        .where(
            TutorConversation.user_id == principal.user_id,
            TutorConversation.task_session_id == session_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    row = (await db.execute(query)).scalar_one_or_none()
    if row is None:
        row = TutorConversation(
            user_id=principal.user_id,
            title="任务对话",
            kind="task",
            task_session_id=session_id,
        )
        try:
            async with db.begin_nested():
                db.add(row)
                await db.flush()
        except IntegrityError:
            # A concurrent request created it; our row is rolled back.
            row = (await db.execute(query)).scalar_one()
    await associate(db, row.id, session_id)
    return row


async def associate(db: AsyncSession, conversation_id: str, session_id: str) -> None:
    exists = await db.scalar(
        select(TutorConversationTask.id).where(
            TutorConversationTask.conversation_id == conversation_id,
            TutorConversationTask.session_id == session_id,
        )
    )
    if exists is not None:
        return
    try:
        async with db.begin_nested():
            db.add(TutorConversationTask(conversation_id=conversation_id, session_id=session_id))
            await db.flush()
    except IntegrityError:
        pass  # Same association created concurrently.


async def task_views(db: AsyncSession, conversation_ids: list[str]) -> dict[str, list[dict]]:
    if not conversation_ids:
        return {}
    rows = (
        await db.execute(
            select(TutorConversationTask, TeachingSession.status)
            .join(TeachingSession, TeachingSession.id == TutorConversationTask.session_id)
            .where(TutorConversationTask.conversation_id.in_(conversation_ids))
            .order_by(TutorConversationTask.created_at, TutorConversationTask.session_id)
        )
    ).all()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for task, status in rows:
        grouped[task.conversation_id].append(
            {
                "session_id": task.session_id,
                "status": status,
                "created_at": utc(task.created_at),
            }
        )
    return grouped


def touch(conversation: TutorConversation, text: str) -> None:
    conversation.updated_at = datetime.now(UTC)
    if not conversation.title.strip():
        conversation.title = text.strip()[:40]


# --- projection --------------------------------------------------------------


def _block_view(block: TeachingMessageBlock) -> dict:
    return {"id": block.id, "ordinal": block.ordinal, "text": block.text}


def project(
    row: TeachingMessage, context: dict | None, run_status: str | None, blocks: list[TeachingMessageBlock]
) -> dict:
    """A task message is restricted by that task's *current* rights.

    ``context is None`` means the message never bound a task (or its task can
    no longer be projected); only the former is visible.
    """
    if row.session_id is None:
        restricted = False
    elif context is None:
        restricted = True
    else:
        current = {card["card_id"] for card in sources(context)}
        restricted = (
            context["material"]["restricted"]
            or row.content_revision_id != context["material"]["content_revision_id"]
            or (row.requires_reveal and not any(card["kind"] == "analysis" for card in context["cards"]))
            or not set(row.body.get("citation_ids", [])).issubset(current)
        )
    return {
        "id": row.id,
        "conversation_id": row.conversation_id,
        "session_id": row.session_id,
        "sequence": row.sequence,
        "session_revision": row.session_revision,
        "run_id": row.run_id,
        "run_status": run_status,
        "role": row.role,
        "status": row.status,
        "body": None if restricted else copy.deepcopy(row.body),
        "blocks": [] if restricted else [_block_view(block) for block in blocks],
        "restricted": bool(restricted),
        "created_at": utc(row.created_at).isoformat(),
    }


async def _blocks_for(db: AsyncSession, message_ids: list[str]) -> dict[str, list[TeachingMessageBlock]]:
    if not message_ids:
        return {}
    rows = (
        await db.execute(
            select(TeachingMessageBlock)
            .where(TeachingMessageBlock.message_id.in_(message_ids))
            .order_by(TeachingMessageBlock.message_id, TeachingMessageBlock.ordinal)
        )
    ).scalars()
    grouped: dict[str, list[TeachingMessageBlock]] = defaultdict(list)
    for row in rows:
        grouped[row.message_id].append(row)
    return grouped


async def _contexts_for(db: AsyncSession, principal: Principal, session_ids: set[str]) -> dict[str, dict | None]:
    """Project each task once; a vanished/restricted task hides its messages."""
    contexts: dict[str, dict | None] = {}
    for session_id in sorted(session_ids):
        try:
            contexts[session_id] = (await get_learning_context(db, principal, session_id)).model_dump(mode="json")
        except AppError:
            contexts[session_id] = None
    return contexts


async def _page_rows(
    db: AsyncSession, principal: Principal, where, after: int, limit: int
) -> tuple[list[Row], bool, dict[str, dict | None], dict[str, list[TeachingMessageBlock]]]:
    rows = (
        await db.execute(
            select(TeachingMessage, AgentRun.status)
            .outerjoin(AgentRun, AgentRun.id == TeachingMessage.run_id)
            .where(*where, TeachingMessage.sequence > after)
            .order_by(TeachingMessage.sequence)
            .limit(limit + 1)
        )
    ).all()
    visible: list[Row] = list(rows[:limit])
    contexts = await _contexts_for(db, principal, {row.session_id for row, _ in visible if row.session_id})
    blocks = await _blocks_for(db, [row.id for row, _ in visible])
    return visible, len(rows) > limit, contexts, blocks


def _page(visible: list, truncated: bool, contexts: dict, blocks: dict, after: int) -> dict:
    return {
        "items": [
            project(row, contexts.get(row.session_id) if row.session_id else None, status, blocks.get(row.id, []))
            for row, status in visible
        ],
        "next_after": visible[-1][0].sequence if visible else after,
        "has_more": truncated,
    }


async def page_conversation(db: AsyncSession, principal: Principal, conversation_id: str, *, after=0, limit=50) -> dict:
    """Chat messages are read through the chat API only for ``kind='chat'``."""
    _allowed(principal)
    await owned_chat(db, principal, conversation_id)
    visible, truncated, contexts, blocks = await _page_rows(
        db,
        principal,
        (TeachingMessage.conversation_id == conversation_id, TeachingMessage.user_id == principal.user_id),
        after,
        limit,
    )
    return _page(visible, truncated, contexts, blocks, after)


async def page_session(db: AsyncSession, principal: Principal, session: TeachingSession, *, after=0, limit=50) -> dict:
    """Legacy endpoint: the task chat keeps its own transcript and cursor.

    A read never creates the chat; an empty task simply has no messages yet.
    """
    _allowed(principal)
    conversation = await db.scalar(
        select(TutorConversation).where(
            TutorConversation.user_id == principal.user_id,
            TutorConversation.task_session_id == session.id,
        )
    )
    if conversation is None:
        return {"items": [], "next_after": after, "has_more": False}
    visible, truncated, contexts, blocks = await _page_rows(
        db,
        principal,
        (
            TeachingMessage.conversation_id == conversation.id,
            TeachingMessage.user_id == principal.user_id,
        ),
        after,
        limit,
    )
    return _page(visible, truncated, contexts, blocks, after)


async def export_all(db: AsyncSession, principal: Principal) -> tuple[list[dict], list[dict]]:
    """Every conversation and message the owner may read, task-less included.

    Export never holds the per-session write lock: it projects from the same
    site view the user could read a moment later.
    """
    _allowed(principal)
    conversations = list(
        (
            await db.execute(
                select(TutorConversation)
                .where(TutorConversation.user_id == principal.user_id)
                .order_by(TutorConversation.created_at, TutorConversation.id)
            )
        ).scalars()
    )
    tasks = await task_views(db, [row.id for row in conversations])
    conversation_rows = [
        {
            "id": row.id,
            "title": row.title,
            "status": row.status,
            "kind": row.kind,
            "tasks": tasks.get(row.id, []),
            "created_at": utc(row.created_at).isoformat(),
            "updated_at": utc(row.updated_at).isoformat(),
        }
        for row in conversations
    ]
    rows = (
        await db.execute(
            select(TeachingMessage, AgentRun.status)
            .outerjoin(AgentRun, AgentRun.id == TeachingMessage.run_id)
            .where(TeachingMessage.user_id == principal.user_id)
            .order_by(TeachingMessage.conversation_id, TeachingMessage.sequence)
        )
    ).all()
    contexts = await _contexts_for(db, principal, {row.session_id for row, _ in rows if row.session_id})
    blocks = await _blocks_for(db, [row.id for row, _ in rows])
    messages = [
        project(row, contexts.get(row.session_id) if row.session_id else None, status, blocks.get(row.id, []))
        for row, status in rows
    ]
    return conversation_rows, messages


async def event_message(db: AsyncSession, principal: Principal, conversation_id: str, message_id: str) -> dict | None:
    _allowed(principal)
    row = await db.scalar(
        select(TeachingMessage).where(
            TeachingMessage.id == message_id,
            TeachingMessage.conversation_id == conversation_id,
            TeachingMessage.user_id == principal.user_id,
        )
    )
    if row is None:
        return None
    contexts = await _contexts_for(db, principal, {row.session_id} if row.session_id else set())
    blocks = (await _blocks_for(db, [row.id])).get(row.id, [])
    return project(row, contexts.get(row.session_id) if row.session_id else None, None, blocks)


async def event_block(
    db: AsyncSession, principal: Principal, conversation_id: str, message_id: str, block_id: str
) -> dict | None:
    """Project one published block with the current rights, never the stored snapshot."""
    _allowed(principal)
    row = await db.scalar(
        select(TeachingMessage).where(
            TeachingMessage.id == message_id,
            TeachingMessage.conversation_id == conversation_id,
            TeachingMessage.user_id == principal.user_id,
        )
    )
    if row is None:
        return None
    block = await db.scalar(
        select(TeachingMessageBlock).where(
            TeachingMessageBlock.id == block_id, TeachingMessageBlock.message_id == message_id
        )
    )
    if block is None:
        return None
    contexts = await _contexts_for(db, principal, {row.session_id} if row.session_id else set())
    projected = project(row, contexts.get(row.session_id) if row.session_id else None, None, [block])
    if projected["restricted"] or not projected["blocks"]:
        return None
    return {"message_id": row.id, "message_status": row.status, "block": projected["blocks"][0]}


# --- writes ------------------------------------------------------------------


async def append(
    db: AsyncSession,
    run: AgentRun,
    context: dict | None,
    role: str,
    body: dict,
    *,
    requires_reveal=False,
) -> TeachingMessage:
    """Caller holds the conversation write lock; message and run outcome commit together."""
    sequence = (
        await db.scalar(
            select(func.max(TeachingMessage.sequence)).where(TeachingMessage.conversation_id == run.conversation_id)
        )
        or 0
    ) + 1
    row = TeachingMessage(
        user_id=run.user_id,
        conversation_id=run.conversation_id,
        session_id=run.session_id,
        run_id=run.id,
        content_revision_id=context["material"]["content_revision_id"] if context else None,
        sequence=sequence,
        session_revision=run.bound_session_revision,
        role=role,
        body=copy.deepcopy(body),
        requires_reveal=requires_reveal,
        status="complete",
    )
    db.add(row)
    await db.flush()
    return row


async def append_streaming(
    db: AsyncSession, run: AgentRun, context: dict | None, *, requires_reveal=True
) -> TeachingMessage:
    """Create the assistant message that blocks are published under (P02.2)."""
    sequence = (
        await db.scalar(
            select(func.max(TeachingMessage.sequence)).where(TeachingMessage.conversation_id == run.conversation_id)
        )
        or 0
    ) + 1
    row = TeachingMessage(
        user_id=run.user_id,
        conversation_id=run.conversation_id,
        session_id=run.session_id,
        run_id=run.id,
        content_revision_id=context["material"]["content_revision_id"] if context else None,
        sequence=sequence,
        session_revision=run.bound_session_revision,
        role="assistant",
        body={"text": "", "citation_ids": [], "suggested_answer": None},
        requires_reveal=requires_reveal,
        status="streaming",
    )
    db.add(row)
    await db.flush()
    return row


async def append_block(db: AsyncSession, message: TeachingMessage, ordinal: int, text: str) -> TeachingMessageBlock:
    block = TeachingMessageBlock(message_id=message.id, ordinal=ordinal, text=text)
    db.add(block)
    await db.flush()
    return block


def finalize(message: TeachingMessage, body: dict, status: str) -> None:
    message.body = copy.deepcopy(body)
    message.status = status


# --- model input -------------------------------------------------------------


async def model_input(db: AsyncSession, principal: Principal, run: AgentRun) -> dict:
    """Bounded, permission-projected history plus the run's task, if any.

    History is scoped to the run's own task (or to task-less turns of the same
    chat). A chat can hold both, and a task-less turn must never receive task
    material — not even the user's own wording of it.
    """
    context = None
    if run.session_id is not None:
        context = (await get_learning_context(db, principal, run.session_id)).model_dump(mode="json")
    rows = list(
        (
            await db.execute(
                select(TeachingMessage)
                .where(
                    TeachingMessage.conversation_id == run.conversation_id,
                    TeachingMessage.user_id == principal.user_id,
                    or_(TeachingMessage.run_id != run.id, TeachingMessage.run_id.is_(None)),
                    (
                        TeachingMessage.session_id.is_(None)
                        if run.session_id is None
                        else TeachingMessage.session_id == run.session_id
                    ),
                )
                .order_by(TeachingMessage.sequence.desc())
                .limit(7)
            )
        ).scalars()
    )
    blocks = await _blocks_for(db, [row.id for row in rows[:6]])
    history, size = [], 0
    for row in rows[:6]:
        projected = project(row, context, None, blocks.get(row.id, []))
        if projected["restricted"]:
            continue
        text = row.body.get("text") or ""
        if not text.strip():
            # An interrupted stream may have blocks but no final body yet.
            text = "".join(block.text for block in blocks.get(row.id, []))
        if not text.strip():
            continue
        message = {"role": row.role, "text": text}
        added = len(json.dumps(message, ensure_ascii=False).encode())
        if size + added > 8000:
            break
        history.append(message)
        size += added
    history.reverse()
    return {"learning_context": context, "history": history, "history_truncated": len(history) < len(rows)}


def validate_reply(reply: TutorReply, context: dict | None) -> None:
    """A task reply must cite its revealed sources; a general reply must not."""
    if context is None:
        if not reply.text.strip() or reply.citation_ids or reply.suggested_answer is not None:
            raise AppError(502, "AI_SERVICE_UNAVAILABLE", "导师回复未通过当前上下文校验")
        return
    ids = {card["card_id"] for card in sources(context)}
    revealed = any(card["kind"] == "analysis" for card in context["cards"])
    if (
        not reply.text.strip()
        or not set(reply.citation_ids).issubset(ids)
        or (reply.source == "model" and (not revealed or not reply.citation_ids))
        or (reply.suggested_answer is not None and not revealed)
    ):
        raise AppError(502, "AI_SERVICE_UNAVAILABLE", "导师回复未通过当前上下文校验")


def before_reveal() -> TutorReply:
    return TutorReply(
        text="先在题面保存或提交你的判断。需要帮助时可选择分级提示；揭晓后，我会结合原文证据解释你的问题。聊天不会替你提交答案。",
        source="policy",
    )
