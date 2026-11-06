from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.limiter import rate_limit
from app.core.logging import mask_phone
from app.core.redis import get_redis
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.core.token_blacklist import blacklist_token, claim_token_once
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    ChangePhoneRequest,
    LogoutRequest,
    MessageResponse,
    PhoneLoginRequest,
    RefreshRequest,
    RefreshResponse,
    SendSmsCodeRequest,
    SmsLoginRequest,
    SmsRegisterRequest,
    SmsResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.sms_service import send_verify_code
from app.services.sms_service import verify_code as verify_sms_code

logger = structlog.get_logger(__name__)
settings = get_settings()

security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/auth", tags=["auth"])


# Per-phone-per-purpose send cooldown (seconds). Redis key
# sms:cooldown:{phone}:{purpose} is set on send and its existence blocks
# resends. Aliyun also rate-limits server-side; this is a local first line
# of defense against billing abuse.
_SMS_COOLDOWN_SECONDS = 60

# New-account creation through /auth/sms/login keeps the registration
# risk-control budget (3/min/IP). Existing-account login stays at 10/min.
_SIGNUP_RATE_LIMIT = 3
_SIGNUP_RATE_WINDOW_SECONDS = 60


async def _verify_auth_code(phone: str, code: str) -> bool:
    """Verify a code issued for the canonical auth purpose or legacy register."""
    if await verify_sms_code(phone, code, purpose="auth"):
        return True
    return await verify_sms_code(phone, code, purpose="register")


async def _registration_enabled(db: AsyncSession) -> bool:
    """Admin kill switch: absent row means registration is enabled."""
    from app.models.admin_setting import SETTINGS_ROW_ID, AdminSetting

    row = (await db.execute(select(AdminSetting).where(AdminSetting.id == SETTINGS_ROW_ID))).scalar_one_or_none()
    return row is None or bool(row.registration_enabled)


async def _check_signup_rate_limit(request: Request) -> None:
    """Per-IP guard for accounts created by the combined login/register flow.

    Redis is not the source of truth: a blip must not block signup (INV-002),
    so storage failures fall through.
    """
    if settings.env == "testing":
        return
    redis = get_redis()
    client_host = request.client.host if request.client else "unknown"
    key = f"auth:signup_rate:{client_host}"
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, _SIGNUP_RATE_WINDOW_SECONDS)
        if count > _SIGNUP_RATE_LIMIT:
            raise HTTPException(status_code=429, detail="注册过于频繁，请稍后再试")
    except HTTPException:
        raise
    except Exception:
        logger.warning("signup_rate_limit_check_failed", client=client_host)


@router.post("/sms/send-code", response_model=MessageResponse)
@rate_limit("5/minute")
async def sms_send_code(request: Request, data: SendSmsCodeRequest):
    """Send an SMS verification code to the given phone number.

    A 60s per-phone-per-purpose cooldown (Redis) prevents rapid resends.
    In dev-fake mode (no Aliyun credentials) the code is logged instead of sent.
    """
    redis = get_redis()
    cooldown_key = f"sms:cooldown:{data.phone}:{data.purpose}"
    if await redis.exists(cooldown_key):
        raise HTTPException(status_code=429, detail="发送过于频繁，请稍后再试")

    try:
        await send_verify_code(data.phone, purpose=data.purpose)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # Set the cooldown only after a successful send.
    try:
        await redis.setex(cooldown_key, _SMS_COOLDOWN_SECONDS, "1")
    except Exception:
        # Fail-open: Redis outage must not block login. Aliyun's own rate
        # limit still protects us.
        logger.warning("sms_cooldown_set_failed", phone=mask_phone(data.phone), purpose=data.purpose)

    logger.info("sms_code_sent", phone=mask_phone(data.phone), purpose=data.purpose)
    return MessageResponse(message="验证码已发送")


@router.post("/sms/login", response_model=TokenResponse)
@rate_limit("10/minute")
async def sms_login(request: Request, data: SmsLoginRequest, db: AsyncSession = Depends(get_db)):
    """Log in or register with phone number + SMS code.

    Canonical passwordless entry point: a verified code logs into an existing
    account, or creates a phone-only account (``hashed_password`` NULL) when
    the phone is new. ``is_new_user`` tells the client to route into
    onboarding. Registration risk controls (``registration_enabled`` +
    per-IP 3/min) apply only on the create branch.
    """
    if not await _verify_auth_code(data.phone, data.code):
        raise HTTPException(status_code=400, detail="验证码错误或已失效")

    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()

    is_new_user = False
    if user is None:
        await _check_signup_rate_limit(request)
        if not await _registration_enabled(db):
            raise HTTPException(status_code=403, detail="注册功能暂未开放，请联系管理员")

        user = User(
            phone=data.phone,
            hashed_password=None,
            name=None,
            onboarding_completed=False,
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
            is_new_user = True
        except Exception as exc:
            # Concurrent first logins with the same phone race past the check
            # and hit the partial unique index — fall back to the winner's row.
            await db.rollback()
            if "uq_users_phone_partial" in str(exc) or "unique" in str(exc).lower():
                user = (await db.execute(select(User).where(User.phone == data.phone))).scalar_one_or_none()
                if user is None:
                    raise
            else:
                raise
    if user.is_banned:
        raise HTTPException(status_code=403, detail="账户已被封禁")

    token = create_token(user.id)
    refresh_token = create_token(user.id, token_type="refresh")
    logger.info("sms_login_success", user_id=user.id, phone=mask_phone(data.phone), is_new_user=is_new_user)
    return TokenResponse(
        token=token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        is_new_user=is_new_user,
    )


@router.post("/sms/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@rate_limit("3/minute")
async def sms_register(request: Request, data: SmsRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Deprecated compatibility registration endpoint.

    New clients use ``/auth/sms/login``. Kept for one release so old clients
    that still send a password keep working; ``password`` is now optional.
    """
    if not await _verify_auth_code(data.phone, data.code):
        raise HTTPException(status_code=400, detail="验证码错误或已失效")

    if not await _registration_enabled(db):
        raise HTTPException(status_code=403, detail="注册功能暂未开放，请联系管理员")

    existing = await db.execute(select(User).where(User.phone == data.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="该手机号已注册")

    user = User(
        phone=data.phone,
        hashed_password=hash_password(data.password) if data.password else None,
        name=data.name,
        onboarding_completed=False,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        # Concurrent registration with the same phone can race past the check
        # above and hit the partial unique index — convert to a clean 409.
        #
        # The test is "does this phone exist now?", not a match on the driver's
        # constraint name: whoever won the race has committed, so the re-query
        # is the ground truth. Matching `"unique" in str(exc)` made the status
        # code depend on driver prose — different driver wording, a translated
        # message, or a rename of the index would have silently turned this 409
        # back into a 500.
        await db.rollback()
        taken = (await db.execute(select(User.id).where(User.phone == data.phone))).scalar_one_or_none()
        if taken is None:
            raise
        raise HTTPException(status_code=409, detail="该手机号已注册") from exc
    await db.refresh(user)

    token = create_token(user.id)
    refresh_token = create_token(user.id, token_type="refresh")
    logger.info("sms_register_success", user_id=user.id, phone=mask_phone(data.phone))
    return TokenResponse(
        token=token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        is_new_user=True,
    )


@router.post("/phone-login", response_model=TokenResponse)
@rate_limit("5/minute")
async def phone_login(request: Request, data: PhoneLoginRequest, db: AsyncSession = Depends(get_db)):
    """Log in with phone + password (the password set at /auth/sms/register)."""
    result = await db.execute(select(User).where(User.phone == data.phone))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="手机号或密码错误")
    if user.is_banned:
        raise HTTPException(status_code=403, detail="账户已被封禁")

    token = create_token(user.id)
    refresh_token = create_token(user.id, token_type="refresh")
    return TokenResponse(token=token, refresh_token=refresh_token, user=UserResponse.model_validate(user))


@router.post("/refresh", response_model=RefreshResponse)
@rate_limit("20/minute")
async def refresh_token(request: Request, data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a valid refresh token for a new access token.

    The refresh token must have type='refresh' in its payload.
    Returns a new access token (and optionally a new refresh token).
    """
    payload = decode_token(data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Verify this is actually a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not a refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # 封禁必须终止 token 链：每个请求的 get_current_user 都会拒封禁用户，续签
    # 出来的是废票，但放任 refresh 继续铸新对只会让客户端攥着一串死 token。
    if user.is_banned:
        raise HTTPException(status_code=403, detail="账户已被封禁")

    # Reject refresh tokens issued before the last password change/reset, so a
    # compromised refresh token becomes useless once the user resets their password.
    from app.api.dependencies import _token_issued_before_password_change

    if _token_issued_before_password_change(payload, user):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired due to password change. Please log in again.",
        )

    # 单次消费（A03/BE-05）：把「这个 refresh 是否已被撤销」与「撤销它」合并成
    # 一个原子 claim。旧实现在最前面读黑名单、校验完再写黑名单，两个并发请求都能
    # 读到「尚未撤销」，于是同一个 refresh 铸出两条后继链；若旧 token 被盗，合法
    # 用户与攻击者可以同时续期。现在只有抢到 key 的那一个能继续，重放一律 401。
    # 放在其他校验之后：被封禁或改过密码的 token 不必再占一个键。
    if settings.jwt_blacklist_enabled:
        old_exp = payload.get("exp")
        if old_exp:
            remaining = int(old_exp - datetime.now(UTC).timestamp())
        else:
            remaining = settings.jwt_refresh_expire_days * 24 * 60 * 60  # refresh token TTL
        if not await claim_token_once(payload.get("jti"), max(remaining, 0)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

    new_token = create_token(user.id)
    new_refresh_token = create_token(user.id, token_type="refresh")
    return RefreshResponse(token=new_token, refresh_token=new_refresh_token)


@router.post("/sms/reset-password", response_model=MessageResponse)
@rate_limit("5/minute")
async def sms_reset_password(
    request: Request,
    data: SmsResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password via phone + SMS code.

    Returns the same message whether or not the phone is registered, to prevent
    enumeration.
    """
    if not await verify_sms_code(data.phone, data.code, purpose="reset_password"):
        raise HTTPException(status_code=400, detail="验证码错误或已失效")

    result = await db.execute(select(User).where(User.phone == data.phone).with_for_update())
    user = result.scalar_one_or_none()

    if user is not None:
        user.hashed_password = hash_password(data.new_password)
        # Invalidate all sessions issued before this moment (tokens with an
        # earlier ``iat`` are rejected by the auth dependency).
        user.password_changed_at = datetime.now(UTC)
        db.add(user)
        await db.commit()
        logger.info("sms_password_reset", user_id=user.id, phone=mask_phone(data.phone))

    return MessageResponse(message="如果该手机号已注册，密码已重置。")


@router.post("/sms/change-phone", response_model=UserResponse)
@rate_limit("5/minute")
async def change_phone(
    request: Request,
    data: ChangePhoneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change the current user's phone number.

    Requires: current password (re-authentication) + SMS code sent to the NEW
    phone (proves ownership of the new number).
    """
    # 1. Verify current password
    if not current_user.hashed_password or not verify_password(data.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="密码错误")

    # 2. Verify SMS code sent to the new phone
    if not await verify_sms_code(data.new_phone, data.code, purpose="change_phone"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="验证码错误或已失效")

    # 3. Check new phone is not already registered
    existing = await db.execute(select(User).where(User.phone == data.new_phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该手机号已被注册")

    # 4. Update phone number
    current_user.phone = data.new_phone
    await db.commit()
    await db.refresh(current_user)

    logger.info("phone_changed", user_id=current_user.id, new_phone=mask_phone(data.new_phone))
    return UserResponse.model_validate(current_user)


@router.post("/logout", response_model=MessageResponse)
@rate_limit("10/minute")
async def logout(
    request: Request,
    data: LogoutRequest = None,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Invalidate the current JWT by adding its JTI to the Redis blacklist.
    Optionally also blacklists the refresh token if provided in the request body.
    """
    if not settings.jwt_blacklist_enabled:
        return MessageResponse(message="Logged out successfully")

    payload = decode_token(credentials.credentials)
    if payload is None:
        return MessageResponse(message="Logged out successfully")

    jti = payload.get("jti")
    if jti is None:
        return MessageResponse(message="Logged out successfully")

    # Calculate remaining TTL from the exp claim.
    exp = payload.get("exp")
    if exp:
        remaining = int(exp - datetime.now(UTC).timestamp())
    else:
        remaining = settings.jwt_expire_minutes * 60

    await blacklist_token(jti, remaining)
    logger.info("user_logged_out", user_id=current_user.id, jti=jti)

    # Also blacklist the refresh token if provided
    if data and data.refresh_token:
        refresh_payload = decode_token(data.refresh_token)
        if refresh_payload:
            refresh_jti = refresh_payload.get("jti")
            if refresh_jti:
                refresh_exp = refresh_payload.get("exp")
                if refresh_exp:
                    refresh_remaining = int(refresh_exp - datetime.now(UTC).timestamp())
                else:
                    refresh_remaining = settings.jwt_refresh_expire_days * 24 * 60 * 60
                await blacklist_token(refresh_jti, max(refresh_remaining, 0))
                logger.info("refresh_token_blacklisted", user_id=current_user.id, jti=refresh_jti)

    return MessageResponse(message="Logged out successfully")


@router.post("/change-password", response_model=MessageResponse)
@rate_limit("5/minute")
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set a first password, or change an existing one.

    A phone-only account has ``hashed_password`` NULL: the authenticated
    session is enough to set the first password, and doing so must not
    invalidate that session (first setup is not a credential change). A real
    password change still requires the current password and bumps
    ``password_changed_at`` to revoke older sessions.
    """
    is_first_setup = not current_user.hashed_password
    if not is_first_setup:
        if not data.current_password or not verify_password(data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

    current_user.hashed_password = hash_password(data.new_password)
    if not is_first_setup:
        # Invalidate all sessions issued before this moment.
        current_user.password_changed_at = datetime.now(UTC)
    await db.commit()

    logger.info("password_changed", user_id=current_user.id, first_setup=is_first_setup)
    return MessageResponse(message="Password set successfully" if is_first_setup else "Password changed successfully")
