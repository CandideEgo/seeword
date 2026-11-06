from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.v2_runtime import ExternalConnection
from app.services import external_connection_service as service

router = APIRouter(prefix="/external-connections", tags=["external-connections"])


class ConnectionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host_label: str = Field(min_length=1, max_length=100)
    granted_scopes: list[str] = Field(default_factory=lambda: ["teaching:read"], max_length=7)


@router.get("")
async def list_connections(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    from app.services.v2_schema import has_tables

    # The settings page renders this for every account; an unmigrated database
    # holds no connections, so answer empty instead of failing the request.
    if not await has_tables(db, ("external_connections",)):
        return {"items": [], "can_create": False}
    rows = (
        await db.execute(
            select(ExternalConnection)
            .where(ExternalConnection.user_id == user.id)
            .order_by(ExternalConnection.created_at.desc())
        )
    ).scalars()
    from app.core.errors import AppError
    from app.services.v2_access import require_access

    try:
        await require_access(db, user.id, "mcp_read_enabled")
        can_create = True
    except AppError:
        can_create = False
    return {"items": [service.view(row) for row in rows], "can_create": can_create}


@router.post("", status_code=201)
async def create_connection(
    body: ConnectionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    result = await service.create(db, user.id, body.host_label, body.granted_scopes)
    await db.commit()
    return result


@router.post("/{connection_id}/revoke")
async def revoke_connection(
    connection_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    result = await service.revoke(db, user.id, connection_id)
    await db.commit()
    return result


@router.post("/{connection_id}/rotate")
async def rotate_connection(
    connection_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    result = await service.rotate(db, user.id, connection_id)
    await db.commit()
    return result
