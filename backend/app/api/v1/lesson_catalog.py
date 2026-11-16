"""First-party read-only learning catalog; declared before dynamic lesson paths."""

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.limiter import rate_limit
from app.models.user import User
from app.schemas.lesson_catalog import FixedReference, MaterialIdentity
from app.services import lesson_catalog, lessons
from app.services.teaching.principal import Principal


async def _ready(db: AsyncSession = Depends(get_db)) -> None:
    await lessons.require_lessons_ready(db)


router = APIRouter(prefix="/lessons", tags=["lesson catalog"], dependencies=[Depends(_ready)])


def _private(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


@router.get("/_search")
@rate_limit("60/minute")
async def search(
    request: Request,
    response: Response,
    q: str = Query("", max_length=200),
    delegable_only: bool = Query(False),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _private(response)
    return await lesson_catalog.search_materials(
        db, Principal(user.id), q, offset=offset, limit=limit, delegable_only=delegable_only
    )


@router.get("/_occurrences")
@rate_limit("60/minute")
async def occurrences(
    request: Request,
    response: Response,
    headword: str = Query(min_length=1, max_length=200),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _private(response)
    return await lesson_catalog.search_occurrences(db, Principal(user.id), headword, offset=offset, limit=limit)


@router.post("/_resolve")
@rate_limit("60/minute")
async def resolve(
    request: Request,
    response: Response,
    body: FixedReference,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _private(response)
    return await lesson_catalog.resolve_reference(db, Principal(user.id), body)


@router.post("/_context")
@rate_limit("60/minute")
async def context(
    request: Request,
    response: Response,
    body: FixedReference,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _private(response)
    return await lesson_catalog.get_context(db, Principal(user.id), body)


@router.get("/_reference-state")
@rate_limit("60/minute")
async def reference_state(
    request: Request,
    response: Response,
    lesson_id: str = Query(min_length=1, max_length=100),
    fingerprint_version: str = Query(min_length=1, max_length=32),
    fingerprint: str = Query(pattern=r"^[0-9a-f]{64}$"),
    revision_id: str | None = Query(None, min_length=1, max_length=36),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _private(response)
    identity = MaterialIdentity(
        lesson_id=lesson_id,
        fingerprint_version=fingerprint_version,
        fingerprint=fingerprint,
        revision_id=revision_id,
    )
    return await lesson_catalog.get_state(db, Principal(user.id), identity)
