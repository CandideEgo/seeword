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
from app.schemas.delegated_learning import ResourceLimits
from app.services.teaching.principal import DisclosureAudience, Principal
from app.services.v2_access import require_access

LEARNING_SCOPES = frozenset(
    {"materials:read", "learning:vocabulary:write", "learning:progress:read", "learning:progress:write", "review:write"}
)

SCOPES = (
    frozenset(
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
    | LEARNING_SCOPES
)


async def learning_policy(
    db: AsyncSession, connection: ExternalConnection
) -> tuple[dict[str, list[str]], DisclosureAudience]:
    """Load immutable disclosure purpose with grants, independent of HTTP/MCP path."""
    from app.models.delegated_learning import ExternalLearningGrant, ExternalLearningIntent, ExternalLearningOperation
    from app.services.v2_schema import has_tables

    requires_learning = bool(set(connection.granted_scopes) & LEARNING_SCOPES)
    if not requires_learning and "review:read" not in connection.granted_scopes:
        return {}, "model"
    tables = (
        ExternalLearningGrant.__tablename__,
        ExternalLearningIntent.__tablename__,
        ExternalLearningOperation.__tablename__,
    )
    if not await has_tables(db, tables):
        if requires_learning:
            raise AppError(503, "SERVICE_UNAVAILABLE", "委托学习授权尚未迁移")
        return {}, "model"
    grant = await db.get(ExternalLearningGrant, connection.id, populate_existing=True)
    if grant is None or grant.user_id != connection.user_id:
        return {}, "model"
    raw = grant.resource_limits
    limits: dict[str, list[str]] = {}
    for field in ("lesson_ids", "word_ids"):
        value = raw.get(field, [])
        limits[field] = value if isinstance(value, list) and all(isinstance(item, str) for item in value) else []
    audience: DisclosureAudience = "application" if raw.get("disclosure_audience") == "application" else "model"
    return limits, audience


async def learning_limits(db: AsyncSession, connection: ExternalConnection) -> dict[str, list[str]]:
    limits, _ = await learning_policy(db, connection)
    return limits


async def connection_view(db: AsyncSession, connection: ExternalConnection) -> dict:
    limits, audience = await learning_policy(db, connection)
    return {**view(connection), "resource_limits": limits, "audience": audience}


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
    return {"connection": await connection_view(db, connection), "token": token, "expires_at": connection.expires_at}


async def create(
    db: AsyncSession,
    user_id: str,
    host_label: str,
    scopes: list[str],
    resource_limits: ResourceLimits | None = None,
    *,
    audience: DisclosureAudience = "model",
) -> dict:
    await require_access(db, user_id, "mcp_read_enabled")
    if audience not in {"model", "application"}:
        raise AppError(422, "VALIDATION_ERROR", "连接用途无效")
    requested = set(scopes)
    dependencies = {
        "learning:vocabulary:write": "materials:read",
        "learning:progress:write": "learning:progress:read",
        "review:write": "review:read",
    }
    teaching = {scope for scope in requested if scope.startswith("teaching:") or scope == "learning:feedback:write"}
    if (
        not requested
        or not requested <= SCOPES
        or (teaching and "teaching:read" not in requested)
        or any(scope in requested and read not in requested for scope, read in dependencies.items())
    ):
        raise AppError(422, "VALIDATION_ERROR", "连接权限无效，写入权限须同时授权相应读取权限")
    learning = bool(requested & LEARNING_SCOPES) or ("review:read" in requested and resource_limits is not None)
    if audience == "application" and not learning:
        raise AppError(422, "VALIDATION_ERROR", "应用用途连接须明确声明学习资源")
    if learning or resource_limits is not None:
        from app.models.delegated_learning import (
            ExternalLearningGrant,
            ExternalLearningIntent,
            ExternalLearningOperation,
        )
        from app.models.learning import Vocabulary
        from app.services.lessons import get_visible_revision, require_lessons_ready
        from app.services.v2_schema import has_tables

        if not learning or resource_limits is None:
            raise AppError(422, "VALIDATION_ERROR", "学习连接必须明确声明资源范围")
        if not await has_tables(
            db,
            (
                ExternalLearningGrant.__tablename__,
                ExternalLearningIntent.__tablename__,
                ExternalLearningOperation.__tablename__,
            ),
        ):
            raise AppError(503, "SERVICE_UNAVAILABLE", "委托学习授权尚未迁移")
        # Courses are site-owned; a user can delegate only currently readable
        # courses with third-party redistribution approval, never candidates.
        if resource_limits.lesson_ids:
            await require_lessons_ready(db)
        for lesson_id in sorted(resource_limits.lesson_ids):
            await get_visible_revision(db, lesson_id, use="external_redistribution", lock=True)
            await get_visible_revision(db, lesson_id, use="site_display")
        word_ids = resource_limits.word_ids
        owned_words = (
            set(
                await db.scalars(
                    select(Vocabulary.id).where(Vocabulary.user_id == user_id, Vocabulary.id.in_(word_ids))
                )
            )
            if word_ids
            else set()
        )
        if owned_words != set(word_ids):
            raise AppError(422, "VALIDATION_ERROR", "只能授权本人已有词条")
    row = ExternalConnection(
        user_id=user_id,
        host_label=host_label,
        granted_scopes=sorted(requested),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(row)
    await db.flush()
    if learning and resource_limits is not None:
        db.add(
            ExternalLearningGrant(
                connection_id=row.id,
                user_id=user_id,
                resource_limits={**resource_limits.model_dump(), "disclosure_audience": audience},
            )
        )
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


async def authenticate(db: AsyncSession, token: str, *, write: bool = False) -> Principal:
    """Hold the same connection lock as revoke until the tool transaction commits."""
    from app.services.v2_schema import has_tables

    if not await has_tables(db, ("external_connections", "external_credentials")):
        raise AppError(503, "SERVICE_UNAVAILABLE", "外部连接尚未迁移")
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
    limits, audience = await learning_policy(db, connection)
    return Principal(
        user_id=user.id,
        actor="external_agent",
        connection_id=connection.id,
        granted_scopes=frozenset(connection.granted_scopes),
        credential_issued_at=credential.issued_at,
        resource_limits=limits,
        disclosure_audience=audience,
    )
