"""Authenticated deterministic teaching HTTP adapter."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.limiter import rate_limit
from app.models.user import User
from app.schemas.learning_context import LearningContext
from app.schemas.teaching import (
    CompleteSession,
    ContentCatalogResponse,
    CreateSession,
    DraftAnswer,
    Feedback,
    ItemAction,
    QuizCreate,
    SessionActionRequest,
    SessionListResponse,
    SessionResponse,
    SubmitAttempt,
)
from app.services.teaching import commands, service
from app.services.teaching.context import get_learning_context
from app.services.teaching.principal import Principal

router = APIRouter(prefix="/teaching", tags=["teaching"])


def _principal(user: User, request: Request) -> Principal:
    return Principal(user_id=user.id, request_id=getattr(request.state, "request_id", ""))


@router.get("/content", response_model=ContentCatalogResponse)
@rate_limit("60/minute")
async def content(
    request: Request,
    question_id: str | None = Query(None, max_length=36),
    paper_id: str | None = Query(None, max_length=36),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await service.content_catalog(db, _principal(user, request), question_id=question_id, paper_id=paper_id)


@router.get("/sessions", response_model=SessionListResponse)
@rate_limit("60/minute")
async def sessions(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await service.list_sessions(db, _principal(user, request))


@router.post("/sessions", response_model=SessionResponse, status_code=201)
@rate_limit("20/minute")
async def create(
    request: Request,
    response: Response,
    body: CreateSession,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.create_session(db, _principal(user, request), body)
    await db.commit()
    if result["replayed"]:
        response.status_code = 200
    return result


@router.post("/quizzes", response_model=SessionResponse, status_code=201)
@rate_limit("10/minute")
async def create_quiz(
    request: Request,
    response: Response,
    body: QuizCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.create_quiz(db, _principal(user, request), body)
    await db.commit()
    if result["replayed"]:
        response.status_code = 200
    return result


@router.post("/sessions/{session_id}/actions", response_model=SessionResponse)
@rate_limit("60/minute")
async def action(
    request: Request,
    response: Response,
    session_id: str,
    body: SessionActionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The single write entry for explicit user actions (quiz cards and page buttons)."""
    result = await commands.execute(db, _principal(user, request), session_id, body)
    await db.commit()
    if result["replayed"]:
        response.status_code = 200
    return result


@router.get("/sessions/{session_id}", response_model=SessionResponse)
@rate_limit("60/minute")
async def detail(
    request: Request, session_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await service.get_session(db, _principal(user, request), session_id)


@router.get("/sessions/{session_id}/context", response_model=LearningContext)
@rate_limit("60/minute")
async def context(
    request: Request,
    response: Response,
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    response.headers["Cache-Control"] = "no-store"
    return await get_learning_context(db, _principal(user, request), session_id)


@router.put("/sessions/{session_id}/draft", response_model=SessionResponse)
@rate_limit("60/minute")
async def draft(
    request: Request,
    session_id: str,
    body: DraftAnswer,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.save_draft(db, _principal(user, request), session_id, body)
    await db.commit()
    return result


@router.post("/sessions/{session_id}/attempts", response_model=SessionResponse, status_code=201)
@rate_limit("30/minute")
async def attempt(
    request: Request,
    response: Response,
    session_id: str,
    body: SubmitAttempt,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.submit_attempt(db, _principal(user, request), session_id, body)
    await db.commit()
    if result["replayed"]:
        response.status_code = 200
    return result


@router.post("/sessions/{session_id}/hints", response_model=SessionResponse)
@rate_limit("30/minute")
async def hint(
    request: Request,
    session_id: str,
    body: ItemAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.request_hint(db, _principal(user, request), session_id, body)
    await db.commit()
    return result


@router.post("/sessions/{session_id}/reveal", response_model=SessionResponse)
@rate_limit("30/minute")
async def reveal(
    request: Request,
    session_id: str,
    body: ItemAction,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.reveal_answer(db, _principal(user, request), session_id, body)
    await db.commit()
    return result


@router.post("/sessions/{session_id}/feedback", response_model=SessionResponse, status_code=201)
@rate_limit("20/minute")
async def feedback(
    request: Request,
    response: Response,
    session_id: str,
    body: Feedback,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.record_feedback(db, _principal(user, request), session_id, body)
    await db.commit()
    if result["replayed"]:
        response.status_code = 200
    return result


@router.post("/sessions/{session_id}/complete", response_model=SessionResponse)
@rate_limit("20/minute")
async def complete(
    request: Request,
    session_id: str,
    body: CompleteSession,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await service.complete_session(db, _principal(user, request), session_id, body)
    await db.commit()
    return result
