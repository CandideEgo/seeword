"""Notification route handlers — REST API + WebSocket for real-time push."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.database import commit_refresh, get_async_session_maker, get_db
from app.core.limiter import rate_limit
from app.models.notification import Notification
from app.models.preferences import UserPreferences
from app.models.user import User
from app.schemas.notification import (
    DEFAULT_NOTIFICATION_PREFS,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams, paginated

# Compatibility exports for existing consumers; transport owns the singleton.
from app.services.notification_transport import (
    _INSTANCE_ID as _INSTANCE_ID,
)
from app.services.notification_transport import (
    NOTIFICATIONS_CHANNEL as NOTIFICATIONS_CHANNEL,
)
from app.services.notification_transport import (
    ConnectionManager as ConnectionManager,
)
from app.services.notification_transport import (
    _notification_subscriber_loop as _notification_subscriber_loop,
)
from app.services.notification_transport import (
    push_to_user as push_to_user,
)
from app.services.notification_transport import (
    start_notification_subscriber as start_notification_subscriber,
)
from app.services.notification_transport import (
    stop_notification_subscriber as stop_notification_subscriber,
)
from app.services.notification_transport import (
    ws_manager as ws_manager,
)
from app.services.retired_features import RETIRED_NOTIFICATION_TYPES, sanitize_notification_preferences

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = structlog.get_logger(__name__)

# ── WebSocket endpoint ────────────────────────────────────────────────

# The browser sends the JWT as a WebSocket subprotocol — `["bearer", <token>]`
# — instead of a query parameter, because query strings end up in proxy and
# uvicorn access logs. RFC 6455 requires the server to echo one of the
# client's requested subprotocols, so the handshake echoes the generic
# ``bearer`` marker and never the token itself.
BEARER_SUBPROTOCOL = "bearer"

# The frontend mirrors its access token into this cookie (see frontend
# src/lib/authHelpers.ts, AUTH_COOKIE_NAME) as a fallback for proxies that
# drop the Sec-WebSocket-Protocol header.
AUTH_COOKIE_NAME = "seeword_token"


def _requested_subprotocols(websocket: WebSocket) -> list[str]:
    header = websocket.headers.get("sec-websocket-protocol", "")
    return [part.strip() for part in header.split(",") if part.strip()]


def _ws_token(websocket: WebSocket) -> str | None:
    """Extract the access token from the handshake: subprotocol first, then cookie."""
    protocols = _requested_subprotocols(websocket)
    if BEARER_SUBPROTOCOL in protocols:
        index = protocols.index(BEARER_SUBPROTOCOL)
        if index + 1 < len(protocols):
            return protocols[index + 1]
    return websocket.cookies.get(AUTH_COOKIE_NAME)


@router.websocket("/ws")
async def notification_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time notifications.

    Authenticates on the JWT carried in the ``bearer`` subprotocol (or the
    auth cookie) and then pushes notification events as JSON messages.
    """
    protocols = _requested_subprotocols(websocket)
    token = _ws_token(websocket)
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Same auth chain as HTTP (token type, blacklist, password-change
    # revocation, user existence, ban) — the WS handshake used to duplicate a
    # weaker subset and let tokens issued before a password change stay alive.
    from app.api.dependencies import resolve_token_user

    async with get_async_session_maker()() as db:
        ws_user = await resolve_token_user(token, db)
    if ws_user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user_id = ws_user.id

    await ws_manager.connect(
        user_id,
        websocket,
        subprotocol=BEARER_SUBPROTOCOL if BEARER_SUBPROTOCOL in protocols else None,
    )
    try:
        # Send initial unread count
        # (We can't easily get a db session here in WebSocket,
        #  so we just keep the connection alive and push events)
        while True:
            # Keep connection alive — wait for any client message (ping/pong)
            data = await websocket.receive_text()
            # Client can send "ping" for keepalive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        # Unconditional: an error other than a clean disconnect (a socket the
        # push loop dropped, or cancellation on shutdown) must not leave the
        # socket registered in _connections.
        ws_manager.disconnect(user_id, websocket)


# ── REST API endpoints ────────────────────────────────────────────────


@router.get("", response_model=PaginatedResponse[NotificationResponse])
@rate_limit("30/minute")
async def list_notifications(
    request: Request,
    type_filter: str | None = Query(None, alias="type", description="Filter by notification type"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's notifications, newest first, optionally by type."""
    filters = [Notification.user_id == current_user.id, Notification.type.not_in(RETIRED_NOTIFICATION_TYPES)]
    if type_filter:
        filters.append(Notification.type == type_filter)
    total = (await db.execute(select(func.count()).where(*filters))).scalar() or 0

    result = await db.execute(
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    return paginated(result.scalars().all(), pagination, total=total)


@router.get("/unread-count", response_model=UnreadCountResponse)
@rate_limit("30/minute")
async def unread_count(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the number of unread notifications for the current user."""
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
            Notification.type.not_in(RETIRED_NOTIFICATION_TYPES),
        )
    )
    count = result.scalar() or 0
    return UnreadCountResponse(count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
@rate_limit("30/minute")
async def mark_as_read(
    request: Request,
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification as read. Only the owner can do this."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()
    if not notification:
        # Same convention as the rest of the API: "not visible" == "not found",
        # so a probe cannot distinguish someone else's id from a missing one.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.is_read = True
    await commit_refresh(db, notification)
    return notification


@router.patch("/read-all", response_model=UnreadCountResponse)
@rate_limit("10/minute")
async def mark_all_as_read(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all of the current user's notifications as read."""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    await db.commit()
    return UnreadCountResponse(count=0)


# ── Notification preferences ──────────────────────────────────────────

# Two default dicts, deliberately different, and they are NOT mirrors:
#   * ``app.schemas.notification.DEFAULT_NOTIFICATION_PREFS`` — the API-facing
#     key set (what NotificationPreferencesResponse exposes and validates).
#     Imported below and used as the merge base for this router.
#   * ``app.models.preferences.DEFAULT_NOTIFICATION_PREFS`` — the storage
#     default written into the ``notification_preferences`` JSON column. It
#     additionally carries internal keys the API never returns, notably
#     ``vocabulary_reminder_time``, which ``reminder_tasks`` reads.
# A key belongs in the storage dict when a task must see it with no user input;
# it belongs in the schema dict when a client may set it. Adding a key to one
# therefore does not imply adding it to the other.


@router.get("/preferences", response_model=NotificationPreferencesResponse)
@rate_limit("20/minute")
async def get_notification_preferences(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's notification preferences."""
    result = await db.execute(select(UserPreferences).where(UserPreferences.user_id == current_user.id))
    pref = result.scalar_one_or_none()

    if not pref or not pref.notification_preferences:
        return sanitize_notification_preferences(DEFAULT_NOTIFICATION_PREFS.copy())

    # Merge with defaults (in case new keys were added)
    merged = DEFAULT_NOTIFICATION_PREFS.copy()
    if isinstance(pref.notification_preferences, dict):
        merged.update(pref.notification_preferences)
    return sanitize_notification_preferences(merged)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
@rate_limit("10/minute")
async def update_notification_preferences(
    request: Request,
    data: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's notification preferences (upsert)."""
    result = await db.execute(select(UserPreferences).where(UserPreferences.user_id == current_user.id))
    pref = result.scalar_one_or_none()

    if not pref:
        pref = UserPreferences(user_id=current_user.id, notification_preferences=DEFAULT_NOTIFICATION_PREFS.copy())
        db.add(pref)

    # Merge updates into existing preferences
    current = pref.notification_preferences or DEFAULT_NOTIFICATION_PREFS.copy()
    if not isinstance(current, dict):
        current = DEFAULT_NOTIFICATION_PREFS.copy()
    update_data = data.model_dump(exclude_none=True)
    current.update(update_data)
    current = sanitize_notification_preferences(current)
    pref.notification_preferences = current

    await commit_refresh(db, pref)

    return current
