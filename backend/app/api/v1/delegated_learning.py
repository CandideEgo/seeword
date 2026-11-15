"""Opaque-token adapters; first-party JWTs are never accepted here."""

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import AppError
from app.schemas.delegated_learning import PrepareIntent, SaveProgress, SaveVocabulary
from app.schemas.lesson_catalog import FixedReference, MaterialIdentity
from app.services import delegated_learning as service
from app.services import lesson_catalog
from app.services.external_connection_service import authenticate
from app.services.teaching.principal import Principal


def no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "private, no-store"


router = APIRouter(prefix="/external-learning", tags=["external-learning"], dependencies=[Depends(no_store)])


async def _principal(db: AsyncSession, authorization: str | None, *, write: bool) -> Principal:
    parts = (authorization or "").split(" ", 1)
    token = parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else ""
    return await authenticate(db, token, write=write)


async def read_principal(db: AsyncSession = Depends(get_db), authorization: str | None = Header(None)) -> Principal:
    return await _principal(db, authorization, write=False)


async def write_principal(db: AsyncSession = Depends(get_db), authorization: str | None = Header(None)) -> Principal:
    return await _principal(db, authorization, write=True)


@router.get("/materials")
async def materials(
    q: str = Query("", max_length=200),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(read_principal),
):
    result = await lesson_catalog.search_materials(db, principal, q, offset=offset, limit=limit)
    await db.commit()
    return result


@router.get("/occurrences")
async def occurrences(
    headword: str = Query(..., min_length=1, max_length=200),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(read_principal),
):
    result = await lesson_catalog.search_occurrences(db, principal, headword, offset=offset, limit=limit)
    await db.commit()
    return result


@router.post("/resolve")
async def resolve(
    body: FixedReference, db: AsyncSession = Depends(get_db), principal: Principal = Depends(read_principal)
):
    result = await lesson_catalog.resolve_reference(db, principal, body)
    await db.commit()
    return result


@router.post("/context")
async def context(
    body: FixedReference, db: AsyncSession = Depends(get_db), principal: Principal = Depends(read_principal)
):
    result = await lesson_catalog.get_context(db, principal, body)
    await db.commit()
    return result


@router.post("/reference-state")
async def reference_state(
    body: MaterialIdentity, db: AsyncSession = Depends(get_db), principal: Principal = Depends(read_principal)
):
    result = await lesson_catalog.get_state(db, principal, body)
    await db.commit()
    return result


@router.get("/review-tasks")
async def review_tasks(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(read_principal),
):
    result = await service.review_tasks(db, principal, offset=offset, limit=limit)
    await db.commit()
    return result


@router.post("/vocabulary")
async def save_vocabulary(
    body: SaveVocabulary, db: AsyncSession = Depends(get_db), principal: Principal = Depends(write_principal)
):
    result = await service.save_vocabulary(db, principal, body)
    await db.commit()
    return result


@router.get("/lessons/{lesson_id}/progress")
async def read_progress(
    lesson_id: str, db: AsyncSession = Depends(get_db), principal: Principal = Depends(read_principal)
):
    result = await service.read_progress(db, principal, lesson_id)
    await db.commit()
    return result


@router.put("/lessons/{lesson_id}/progress")
async def save_progress(
    lesson_id: str,
    body: SaveProgress,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(write_principal),
):
    result = await service.save_progress(db, principal, lesson_id, body)
    await db.commit()
    return result


@router.post("/intents", status_code=201)
async def prepare_intent(
    body: PrepareIntent, db: AsyncSession = Depends(get_db), principal: Principal = Depends(write_principal)
):
    result = await service.prepare_intent(db, principal, body)
    await db.commit()
    return result


@router.post("/intents/{intent_id}/execute")
async def execute_intent(
    intent_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    principal: Principal = Depends(write_principal),
):
    if await request.body():
        raise AppError(422, "VALIDATION_ERROR", "执行意图不接受自由参数")
    result = await service.execute_intent(db, principal, intent_id)
    await db.commit()
    return result
