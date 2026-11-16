"""JWT token blacklist backed by Redis.

When a user logs out (or an admin revokes a token), the token's JTI is stored
in Redis with a TTL equal to the token's remaining lifetime. On every request,
the auth dependency checks whether the JTI is blacklisted.

Design choices:
  - Ordinary access-token reads retain their documented fail-open policy.
  - Refresh consumption and revocation writes fail closed: a Redis outage is
    unavailable, never proof that a single-use claim or revocation succeeded.
  - **Key format**: ``token_blacklist:{jti}`` — simple, O(1) lookup.
  - **TTL**: set to the token's remaining validity so keys auto-expire
    when the token would have expired anyway.
"""

import structlog

from app.core.errors import ServiceUnavailableError

logger = structlog.get_logger(__name__)


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a token JTI to the blacklist.

    Args:
        jti: The JWT ID claim (unique per token).
        ttl_seconds: How long to keep the key — should equal the
                     token's remaining validity (exp - now).
    """
    if ttl_seconds <= 0:
        # Token already expired — nothing to blacklist.
        return

    try:
        from app.core.redis import get_redis

        r = get_redis()
        acknowledged = await r.set(f"token_blacklist:{jti}", "1", ex=ttl_seconds)
        if not acknowledged:
            raise ServiceUnavailableError("暂时无法确认会话撤销，请稍后重试")
        logger.debug("token_blacklisted", jti=jti, ttl=ttl_seconds)
    except ServiceUnavailableError:
        raise
    except Exception as exc:
        logger.warning("token_blacklist_redis_error", jti=jti, exc_info=True)
        raise ServiceUnavailableError("暂时无法确认会话撤销，请稍后重试") from exc


async def claim_token_once(jti: str | None, ttl_seconds: int) -> bool:
    """Atomically consume a single-use token.

    Returns True when this caller won the claim (and may therefore mint a
    successor), False when the jti was already claimed or blacklisted.

    This replaces the old "read the blacklist, then write to it" pair used by
    the refresh endpoint. Two concurrent refreshes could both observe "not yet
    revoked" and both rotate, minting two successor chains from one refresh
    token. ``SET NX`` makes the claim atomic, and because it reuses the
    ``token_blacklist:{jti}`` key, winning the claim *is* revoking the old
    token — there is no second write to lose.

    Redis outage raises ServiceUnavailableError: callers must not mint a
    successor or mistake temporary unavailability for a revoked credential.
    Legacy refresh tokens without a JTI cannot prove single-use consumption
    and require a fresh login.
    """
    if not jti:
        return False
    if ttl_seconds <= 0:
        return False

    try:
        from app.core.redis import get_redis

        r = get_redis()
        return bool(await r.set(f"token_blacklist:{jti}", "1", nx=True, ex=ttl_seconds))
    except Exception as exc:
        logger.warning("token_blacklist_claim_redis_error", jti=jti, exc_info=True)
        raise ServiceUnavailableError("暂时无法确认会话续期，请稍后重试") from exc


async def is_token_blacklisted(jti: str | None) -> bool:
    """Check whether a token JTI has been blacklisted.

    Returns False if:
      - jti is None (tokens issued before the blacklist feature was added)
      - Redis is unavailable (fail-open)
      - The key does not exist in Redis
    """
    if jti is None:
        return False

    try:
        from app.core.redis import get_redis

        r = get_redis()
        return bool(await r.exists(f"token_blacklist:{jti}"))
    except Exception:
        # Fail open — if Redis is down, allow the request through.
        logger.warning("token_blacklist_check_redis_error", jti=jti, exc_info=True)
        return False
