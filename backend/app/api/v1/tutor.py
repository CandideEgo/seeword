"""Standalone tutor chats: lifecycle plus message turns on the shared engine."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.teaching_dialogue import DialoguePage
from app.schemas.tutor import ConversationCreate, ConversationPage, ConversationPatch, ConversationSummary, SendMessage
from app.services import teaching_runs as runs
from app.services import tutor_conversations as service
from app.services.teaching.principal import Principal

router = APIRouter(prefix="/tutor", tags=["tutor"])

# Replaced by tests; the queued DB row is the durable dispatch intent.
dispatch = runs.dispatch_run


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post("/conversations", status_code=201, response_model=ConversationSummary)
async def create_conversation(
    body: ConversationCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _no_store(response)
    created = await service.create(db, Principal(user.id), body)
    await db.commit()
    return created


@router.get("/conversations", response_model=ConversationPage)
async def list_conversations(
    response: Response,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _no_store(response)
    return await service.list_page(db, Principal(user.id), page=page, page_size=page_size)


@router.get("/conversations/{conversation_id}", response_model=ConversationSummary)
async def get_conversation(
    conversation_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _no_store(response)
    return await service.detail(db, Principal(user.id), conversation_id)


@router.patch("/conversations/{conversation_id}", response_model=ConversationSummary)
async def patch_conversation(
    conversation_id: str,
    body: ConversationPatch,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _no_store(response)
    updated = await service.patch(db, Principal(user.id), conversation_id, body)
    await db.commit()
    return updated


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await service.delete_chat(db, Principal(user.id), conversation_id)
    await db.commit()


@router.post("/conversations/{conversation_id}/messages", status_code=202)
async def create_turn(
    conversation_id: str,
    body: SendMessage,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _no_store(response)
    result = await runs.start_conversation_turn(db, Principal(user.id), conversation_id, body)
    await db.commit()
    if result["status"] == "queued":
        dispatch(result["run_id"])
    return result


@router.get("/conversations/{conversation_id}/messages", response_model=DialoguePage)
async def messages(
    conversation_id: str,
    response: Response,
    after: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _no_store(response)
    from app.services.teaching import dialogue

    principal = Principal(user.id)
    # Reads stay available after archival but not after the capability closes.
    await service.require_capability(db, user.id)
    return await dialogue.page_conversation(db, principal, conversation_id, after=after, limit=limit)
