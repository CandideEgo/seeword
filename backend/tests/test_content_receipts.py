"""Gateway evidence authentication. Test-generated keys never leave the fixture."""

import copy
import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.core.config import Settings
from app.services import teaching_gateway
from app.services.teaching.content_receipts import AUDIENCE, TOKEN_TYPE, verify_receipt
from tests.teaching_fixtures import original_candidate


@pytest.fixture
def signing_key():
    private = Ed25519PrivateKey.generate()
    public = (
        private.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    return private, public


def signed(private, *, review=False, claims_change=None, header_change=None):
    candidate = original_candidate()
    record = copy.deepcopy(candidate["verification_report"]["teaching_checks" if review else "blind_answers"][0])
    record["logical_call_id"] = "content-call-test"
    kind = "teaching-review-v1" if review else "blind-answer-v1"
    now = int(time.time())
    claims = {
        "iss": "test-gateway",
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + 3600,
        "jti": "test-observed-call",
        "v": 1,
        "kind": kind,
        "prompt_version": kind,
        "receipt": copy.deepcopy(record),
    }
    if claims_change:
        claims.update(claims_change)
    headers = {"kid": "test-1", "typ": TOKEN_TYPE, **(header_change or {})}
    return {**record, "gateway_receipt": jwt.encode(claims, private, algorithm="EdDSA", headers=headers)}


def verify(value, public, **overrides):
    options = {"keys": {"test-1": public}, "issuer": "test-gateway", "max_age_seconds": 86400, **overrides}
    return verify_receipt(value, **options)


@pytest.mark.parametrize("review", [False, True])
def test_public_key_authenticates_exact_observed_result(signing_key, review):
    private, public = signing_key
    value = signed(private, review=review)
    assert verify(value, public)
    assert "PRIVATE KEY" not in public


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "forged-model"),
        ("model_family", "forged-family"),
        ("provider_attempt_id", "other-attempt"),
        ("logical_call_id", "other-call"),
        ("input_sha256", "0" * 64),
        ("selected_position", 0),
        ("option_order", list("ABCD")),
    ],
)
def test_changed_claim_cannot_reuse_a_valid_signature(signing_key, field, value):
    private, public = signing_key
    record = signed(private)
    assert record[field] != value
    record[field] = value
    assert not verify(record, public)


@pytest.mark.parametrize(
    "change",
    [
        {"exp": lambda: int(time.time()) - 1},
        {"iat": lambda: int(time.time()) + 1000},
        {"exp": lambda: int(time.time()) + 90000},
        {"iss": "another-issuer"},
        {"aud": "login"},
        {"v": True},
        {"kind": "other-purpose"},
        {"prompt_version": "unreviewed-prompt"},
        {"jti": ""},
    ],
)
def test_expiry_audience_and_policy_are_not_optional(signing_key, change):
    private, public = signing_key
    # Long full-suite runs may reach this test after the collection-time future
    # has already passed. Keep the same negative cases relative to execution.
    current_change = {key: value() if callable(value) else value for key, value in change.items()}
    assert not verify(signed(private, claims_change=current_change), public)


def test_unknown_key_wrong_signature_and_jose_headers_fail_closed(signing_key):
    private, public = signing_key
    assert not verify(signed(private, header_change={"kid": "unknown"}), public)
    assert not verify(signed(Ed25519PrivateKey.generate()), public)
    assert not verify(signed(private, header_change={"jku": "https://untrusted.example/key"}), public)
    assert not verify(signed(private, header_change={"typ": "JWT"}), public)
    value = signed(private)
    value["gateway_receipt"] = jwt.encode(
        {"aud": AUDIENCE}, "synthetic-secret-at-least-32-characters", algorithm="HS256"
    )
    assert not verify(value, public)


def test_boolean_position_and_modified_review_result_are_rejected(signing_key):
    private, public = signing_key
    value = signed(private)
    value["selected_position"] = True
    assert not verify(value, public)
    review = signed(private, review=True)
    review["checks"]["one_correct_option"] = False
    assert not verify(review, public)
    review = signed(private, review=True)
    review["unexpected"] = "not an authenticated field"
    assert not verify(review, public)


@pytest.mark.parametrize("token", [None, "not.a.receipt", "x" * 16385])
def test_missing_or_unbounded_tokens_do_not_pass(signing_key, token):
    private, public = signing_key
    value = signed(private)
    value["gateway_receipt"] = token
    assert not verify(value, public)


def settings(**overrides):
    return Settings(
        _env_file=None,
        env="testing",
        jwt_secret="test_secret_for_receipts_at_least_32_chars",
        database_url="sqlite+aiosqlite:///:memory:",
        **overrides,
    )


def test_receipt_feature_requires_valid_public_key_configuration(signing_key):
    _, public = signing_key
    assert not settings().content_receipts_enabled
    valid = settings(content_receipts_enabled=True, content_receipt_public_keys={"test-1": public})
    assert valid.content_receipts_enabled
    for keys in ({}, {"bad key": public}, {"test-1": "invalid pem"}):
        with pytest.raises(RuntimeError):
            settings(content_receipts_enabled=True, content_receipt_public_keys=keys)


async def test_configured_gateway_verifier_uses_no_provider_or_network(signing_key, monkeypatch):
    private, public = signing_key
    configured = settings(
        content_receipts_enabled=True,
        content_receipt_public_keys={"test-1": public},
        content_receipt_issuer="test-gateway",
    )
    monkeypatch.setattr(teaching_gateway, "get_settings", lambda: configured)
    callback = teaching_gateway.content_receipt_verifier()
    assert callback is not None and await callback(signed(private))
    monkeypatch.setattr(teaching_gateway, "get_settings", lambda: settings())
    assert teaching_gateway.content_receipt_verifier() is None
