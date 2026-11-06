"""Opaque external credentials, intentionally independent from first-party JWTs."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError
from app.models.user import User
from app.models.v2_runtime import ExternalConnection, ExternalCredential
from app.services.v2_access import require_access

SCOPES = frozenset(
    {
        "learning:profile:read",
        "teaching:read",
        "teaching:analysis:read",
        "teaching:analysis:reveal",
        "teaching:attempts:submit",
        "learning:feedback:write",
        "review:read",
    }
)


def utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def view(row: ExternalConnection) -> dict:
    return {
        key: getattr(row, key)
        for key in ("id", "host_label", "granted_scopes", "created_at", "expires_at", "revoked_at")
    }


async def owned(db: AsyncSession, user_id: str, connection_id: str) -> ExternalConnection:
    from app.services.v2_schema import has_tables

    # Revocation must stay reachable with the feature switched off, but on a
    # database without the V2 tables there is no connection to own.
    if not await has_tables(db, ("external_connections",)):
        raise NotFoundError("连接不存在")
    row = (
        await db.execute(
            select(ExternalConnection)
            .where(ExternalConnection.id == connection_id, ExternalConnection.user_id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("连接不存在")
    return row


async def issue(db: AsyncSession, connection: ExternalConnection) -> dict:
    token = "sw_ext_" + secrets.token_urlsafe(32)
    db.add(ExternalCredential(connection_id=connection.id, token_hash=hashlib.sha256(token.encode()).hexdigest()))
    await db.flush()
    return {"connection": view(connection), "token": token, "expires_at": connection.expires_at}


async def create(db: AsyncSession, user_id: str, host_label: str, scopes: list[str]) -> dict:
    await require_access(db, user_id, "mcp_read_enabled")
    if not set(scopes) <= SCOPES or "teaching:read" not in scopes:
        raise AppError(422, "VALIDATION_ERROR", "连接权限无效，至少需要 teaching:read")
    row = ExternalConnection(
        user_id=user_id,
        host_label=host_label,
        granted_scopes=sorted(set(scopes)),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(row)
    await db.flush()
    return await issue(db, row)


async def revoke(db: AsyncSession, user_id: str, connection_id: str) -> dict:
    row = await owned(db, user_id, connection_id)
    row.revoked_at = row.revoked_at or datetime.now(UTC)
    return view(row)


async def rotate(db: AsyncSession, user_id: str, connection_id: str) -> dict:
    await require_access(db, user_id, "mcp_read_enabled")
    row = await owned(db, user_id, connection_id)
    if row.revoked_at is not None or utc(row.expires_at) <= datetime.now(UTC):
        raise AppError(409, "CONFLICT", "连接已撤销或过期，请新建连接")
    credentials = (
        await db.execute(
            select(ExternalCredential).where(
                ExternalCredential.connection_id == row.id, ExternalCredential.revoked_at.is_(None)
            )
        )
    ).scalars()
    for credential in credentials:
        credential.revoked_at = datetime.now(UTC)
    return await issue(db, row)


async def authenticate(db: AsyncSession, token: str, *, write: bool = False):
    """Hold the same connection lock as revoke until the tool transaction commits."""
    from app.services.teaching.service import Principal

    digest = hashlib.sha256(token.encode()).hexdigest()
    credential = (
        await db.execute(select(ExternalCredential).where(ExternalCredential.token_hash == digest))
    ).scalar_one_or_none()
    invalid = AppError(401, "EXTERNAL_TOKEN_INVALID", "外部凭据无效或已过期")
    if credential is None or not hmac.compare_digest(credential.token_hash, digest):
        raise invalid
    connection = (
        await db.execute(
            select(ExternalConnection)
            .where(ExternalConnection.id == credential.connection_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    # Re-read after acquiring the connection lock; rotation may have committed while we waited.
    await db.refresh(credential)
    now = datetime.now(UTC)
    if connection is None or connection.revoked_at or credential.revoked_at or utc(connection.expires_at) <= now:
        raise invalid
    user = await db.get(User, connection.user_id)
    if user is None or user.is_banned or user.deletion_requested_at:
        raise invalid
    if user.password_changed_at and utc(credential.issued_at) < utc(user.password_changed_at):
        raise invalid
    await require_access(db, user.id, "mcp_write_enabled" if write else "mcp_read_enabled")
    return Principal(
        user_id=user.id,
        actor="external_agent",
        connection_id=connection.id,
        granted_scopes=frozenset(connection.granted_scopes),
        credential_issued_at=credential.issued_at,
    )
