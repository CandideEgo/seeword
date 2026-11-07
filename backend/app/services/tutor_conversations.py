"""Standalone tutor chats. Every turn is executed by the shared run engine."""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.v2_runtime import (
    AgentRun,
    AgentRunEvent,
    AgentStep,
    TeachingMessage,
    TeachingMessageBlock,
    TutorConversation,
    TutorConversationTask,
    now,
)
from app.services.external_connection_service import utc
from app.services.teaching import dialogue
from app.services.teaching.principal import Principal
from app.services.v2_access import require_access
from app.services.v2_schema import require_conversation_schema


async def require_capability(db: AsyncSession, user_id: str) -> None:
    # Flags first (503 before any table read), then the schema. A standalone
    # chat is a new capability: it needs an existing teaching account, not
    # only the dialogue flag. The legacy per-session chat keeps its gates.
    await require_access(db, user_id, "teaching_enabled")
    await require_access(db, user_id, "teaching_conversations_enabled")
    await require_conversation_schema(db)


def _view(row: TutorConversation, tasks: list[dict]) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "status": row.status,
        "kind": row.kind,
        "created_at": utc(row.created_at),
        "updated_at": utc(row.updated_at),
        "tasks": tasks,
    }


async def create(db: AsyncSession, principal: Principal, body) -> dict:
    await require_capability(db, principal.user_id)
    row = TutorConversation(user_id=principal.user_id, title=body.title.strip(), kind="chat")
    db.add(row)
    await db.flush()
    return _view(row, [])


async def list_page(db: AsyncSession, principal: Principal, *, page: int, page_size: int) -> dict:
    await require_capability(db, principal.user_id)
    total = await db.scalar(
        select(func.count())
        .select_from(TutorConversation)
        .where(TutorConversation.user_id == principal.user_id, TutorConversation.kind == "chat")
    )
    rows = list(
        (
            await db.execute(
                select(TutorConversation)
                .where(TutorConversation.user_id == principal.user_id, TutorConversation.kind == "chat")
                .order_by(TutorConversation.updated_at.desc(), TutorConversation.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars()
    )
    tasks = await dialogue.task_views(db, [row.id for row in rows])
    total = total or 0
    return {
        "items": [_view(row, tasks.get(row.id, [])) for row in rows],
        "page": page,
        "page_size": page_size,
        "has_more": total > page * page_size,
    }


async def detail(db: AsyncSession, principal: Principal, conversation_id: str) -> dict:
    await require_capability(db, principal.user_id)
    row = await dialogue.owned_chat(db, principal, conversation_id)
    tasks = (await dialogue.task_views(db, [row.id])).get(row.id, [])
    return _view(row, tasks)


async def patch(db: AsyncSession, principal: Principal, conversation_id: str, body) -> dict:
    await require_capability(db, principal.user_id)
    row = await dialogue.owned_chat(db, principal, conversation_id, lock=True)
    if body.title is not None:
        row.title = body.title.strip()[:120]
    if body.status is not None:
        row.status = body.status
    row.updated_at = now()
    tasks = (await dialogue.task_views(db, [row.id])).get(row.id, [])
    return _view(row, tasks)


async def delete_chat(db: AsyncSession, principal: Principal, conversation_id: str) -> None:
    """Delete one chat and its execution logs; task facts stay untouched."""
    await require_capability(db, principal.user_id)
    row = await dialogue.owned_chat(db, principal, conversation_id, lock=True)
    message_ids = select(TeachingMessage.id).where(TeachingMessage.conversation_id == row.id)
    run_ids = select(AgentRun.id).where(AgentRun.conversation_id == row.id)
    await db.execute(delete(TeachingMessageBlock).where(TeachingMessageBlock.message_id.in_(message_ids)))
    await db.execute(delete(TeachingMessage).where(TeachingMessage.conversation_id == row.id))
    await db.execute(delete(AgentRunEvent).where(AgentRunEvent.run_id.in_(run_ids)))
    await db.execute(delete(AgentStep).where(AgentStep.run_id.in_(run_ids)))
    await db.execute(delete(AgentRun).where(AgentRun.conversation_id == row.id))
    await db.execute(delete(TutorConversationTask).where(TutorConversationTask.conversation_id == row.id))
    await db.delete(row)
