"""Task-owned durable conversation, projected with current material permissions."""

import copy
import json
from collections import defaultdict

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models.v2_runtime import AgentRun, TeachingMessage, TeachingMessageBlock
from app.schemas.teaching_dialogue import TutorReply
from app.services.external_connection_service import utc
from app.services.teaching.context import get_learning_context
from app.services.teaching.principal import Principal


def _allowed(principal: Principal) -> None:
    if principal.actor not in {"user_ui", "internal_agent"}:
        raise AppError(403, "INSUFFICIENT_SCOPE", "此入口未授权读取任务对话")


def sources(context: dict) -> list[dict]:
    return [card for card in context["cards"] if card["kind"] in {"question", "analysis", "evidence"}]


def _block_view(block: TeachingMessageBlock) -> dict:
    return {"id": block.id, "ordinal": block.ordinal, "text": block.text}


def project(row: TeachingMessage, context: dict, run_status: str | None, blocks: list[TeachingMessageBlock]) -> dict:
    current = {card["card_id"] for card in sources(context)}
    restricted = (
        context["material"]["restricted"]
        or row.content_revision_id != context["material"]["content_revision_id"]
        or (row.requires_reveal and not any(card["kind"] == "analysis" for card in context["cards"]))
        or not set(row.body.get("citation_ids", [])).issubset(current)
    )
    return {
        "id": row.id,
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


async def append(
    db: AsyncSession, run: AgentRun, context: dict, role: str, body: dict, *, requires_reveal=False
) -> TeachingMessage:
    """Caller holds the session write lock; message and run outcome commit together."""
    sequence = (
        await db.scalar(select(func.max(TeachingMessage.sequence)).where(TeachingMessage.session_id == run.session_id))
        or 0
    ) + 1
    row = TeachingMessage(
        user_id=run.user_id,
        session_id=run.session_id,
        run_id=run.id,
        content_revision_id=context["material"]["content_revision_id"],
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


async def append_streaming(db: AsyncSession, run: AgentRun, context: dict) -> TeachingMessage:
    """Create the assistant message that blocks are published under (P02.2)."""
    sequence = (
        await db.scalar(select(func.max(TeachingMessage.sequence)).where(TeachingMessage.session_id == run.session_id))
        or 0
    ) + 1
    row = TeachingMessage(
        user_id=run.user_id,
        session_id=run.session_id,
        run_id=run.id,
        content_revision_id=context["material"]["content_revision_id"],
        sequence=sequence,
        session_revision=run.bound_session_revision,
        role="assistant",
        body={"text": "", "citation_ids": [], "suggested_answer": None},
        requires_reveal=True,
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


async def page(db: AsyncSession, principal: Principal, session_id: str, *, after=0, limit=50) -> dict:
    _allowed(principal)
    context = (await get_learning_context(db, principal, session_id)).model_dump(mode="json")
    rows = (
        await db.execute(
            select(TeachingMessage, AgentRun.status)
            .outerjoin(AgentRun, AgentRun.id == TeachingMessage.run_id)
            .where(
                TeachingMessage.session_id == session_id,
                TeachingMessage.user_id == principal.user_id,
                TeachingMessage.sequence > after,
            )
            .order_by(TeachingMessage.sequence)
            .limit(limit + 1)
        )
    ).all()
    visible = rows[:limit]
    blocks = await _blocks_for(db, [row.id for row, _ in visible])
    return {
        "items": [project(row, context, status, blocks.get(row.id, [])) for row, status in visible],
        "next_after": visible[-1][0].sequence if visible else after,
        "has_more": len(rows) > limit,
    }


async def export_messages(db: AsyncSession, principal: Principal, sessions: list[dict]) -> list[dict]:
    """Reuse the export's current site projection, without holding cross-task locks."""
    _allowed(principal)
    contexts = {}
    for state in sessions:
        item = next((i for i in state["items"] if i["id"] == state["current_item_id"]), None)
        contexts[state["id"]] = {
            "material": {
                "restricted": not any(c["kind"] == "question" for c in state["cards"]),
                "content_revision_id": item["content_revision_id"] if item else None,
            },
            "cards": state["cards"],
        }
    rows = (
        await db.execute(
            select(TeachingMessage, AgentRun.status)
            .outerjoin(AgentRun, AgentRun.id == TeachingMessage.run_id)
            .where(TeachingMessage.user_id == principal.user_id)
            .order_by(TeachingMessage.session_id, TeachingMessage.sequence)
        )
    ).all()
    visible = [row for row, _ in rows if row.session_id in contexts]
    blocks = await _blocks_for(db, [row.id for row in visible])
    return [
        project(row, contexts[row.session_id], status, blocks.get(row.id, []))
        for row, status in rows
        if row.session_id in contexts
    ]


async def event_message(db: AsyncSession, principal: Principal, session_id: str, message_id: str) -> dict | None:
    _allowed(principal)
    row = await db.scalar(
        select(TeachingMessage).where(
            TeachingMessage.id == message_id,
            TeachingMessage.session_id == session_id,
            TeachingMessage.user_id == principal.user_id,
        )
    )
    if row is None:
        return None
    context = (await get_learning_context(db, principal, session_id)).model_dump(mode="json")
    blocks = (await _blocks_for(db, [row.id])).get(row.id, [])
    return project(row, context, None, blocks)


async def event_block(
    db: AsyncSession, principal: Principal, session_id: str, message_id: str, block_id: str
) -> dict | None:
    """Project one published block with the current rights, never the stored snapshot."""
    _allowed(principal)
    row = await db.scalar(
        select(TeachingMessage).where(
            TeachingMessage.id == message_id,
            TeachingMessage.session_id == session_id,
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
    context = (await get_learning_context(db, principal, session_id)).model_dump(mode="json")
    projected = project(row, context, None, [block])
    if projected["restricted"] or not projected["blocks"]:
        return None
    return {"message_id": row.id, "message_status": row.status, "block": projected["blocks"][0]}


async def model_input(db: AsyncSession, principal: Principal, run: AgentRun) -> dict:
    context = (await get_learning_context(db, principal, run.session_id)).model_dump(mode="json")
    rows = list(
        (
            await db.execute(
                select(TeachingMessage)
                .where(
                    TeachingMessage.session_id == run.session_id,
                    TeachingMessage.user_id == principal.user_id,
                    or_(TeachingMessage.run_id != run.id, TeachingMessage.run_id.is_(None)),
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


def validate_reply(reply: TutorReply, context: dict) -> None:
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
