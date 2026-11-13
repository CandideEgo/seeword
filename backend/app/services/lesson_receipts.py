"""Verify the publisher's externally signed attestation for one reviewed lesson revision."""

import re

import jwt

from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.services.teaching.content_receipts import public_key

AUDIENCE = "seeword-slcs-lesson-publication"
TOKEN_TYPE = "seeword-slcs-lesson-receipt+jwt"


def verify_lesson_receipt(token: str, expected: dict[str, str]) -> str:
    settings = get_settings()
    keys = settings.slcs_lesson_receipt_public_keys
    issuer = settings.slcs_lesson_receipt_issuer
    if not keys or not issuer:
        raise AppError(503, ErrorCode.SERVICE_UNAVAILABLE, "尚未配置课程发布收据验签")

    try:
        header = jwt.get_unverified_header(token)
        if set(header) != {"alg", "kid", "typ"} or header["alg"] != "EdDSA" or header["typ"] != TOKEN_TYPE:
            raise ValueError("unexpected token header")
        key = keys[header["kid"]]
        claims = jwt.decode(
            token,
            public_key(key),
            algorithms=["EdDSA"],
            issuer=issuer,
            audience=AUDIENCE,
            options={"require": ["iss", "aud", "iat", "exp", "jti", "v", "receipt"], "strict_aud": True},
        )
        receipt_id = claims["jti"]
        if (
            type(claims["v"]) is not int
            or claims["v"] != 1
            or type(claims["iat"]) is not int
            or type(claims["exp"]) is not int
            or not 0 < claims["exp"] - claims["iat"] <= settings.slcs_lesson_receipt_max_age_seconds
            or not isinstance(receipt_id, str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", receipt_id) is None
            or claims["receipt"] != expected
        ):
            raise ValueError("unexpected receipt claims")
    except (jwt.PyJWTError, ValueError, TypeError, KeyError, AttributeError):
        raise AppError(422, ErrorCode.VALIDATION_ERROR, "发布收据无效或与当前审核不符") from None
    return receipt_id
