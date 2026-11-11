"""The receipt signer and the site's verifier must agree, byte for byte.

The signer exists outside the app on purpose (it holds the private key), so
nothing type-checks the two halves against each other. These tests are that
check: a token from ``scripts/sign_lesson_receipt.py`` must pass
``verify_lesson_receipt`` under the settings the site would have, and the claims
it reads must be the ones ``publish_lesson`` compares.
"""

import json
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.core.config import get_settings
from app.core.errors import AppError
from app.services.lesson_receipts import verify_lesson_receipt
from scripts import sign_lesson_receipt as signer


def _row(**overrides):
    row = {
        "lesson_id": "welcome-to-wikisource",
        "id": str(uuid.uuid4()),
        "fingerprint": "d06cd8fa05b10e71d0030fb2e1a5569639c561d565117df91c14057f2f355ab4",
        "fingerprint_version": "slcs-pack-v1",
        "status": "candidate",
        "review": {"review_sha256": "a" * 64},
    }
    return {**row, **overrides}


@pytest.fixture
def site_key(monkeypatch):
    """Configure the site exactly as ``keygen`` prints, and hand back the private key."""
    key = Ed25519PrivateKey.generate()
    pem = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    settings = get_settings()
    monkeypatch.setattr(settings, "slcs_lesson_receipt_issuer", "seeword-slcs-editorial")
    monkeypatch.setattr(settings, "slcs_lesson_receipt_public_keys", {"release-2026": pem.decode()})
    monkeypatch.setattr(settings, "slcs_lesson_receipt_max_age_seconds", 900)
    return key


def test_a_signed_receipt_is_accepted_by_the_site(site_key):
    receipt = signer.build_claims(_row())
    token = signer.sign_receipt(receipt, site_key, issuer="seeword-slcs-editorial", kid="release-2026", ttl=600)
    assert verify_lesson_receipt(token, receipt) == jwt.decode(token, options={"verify_signature": False})["jti"]


def test_claims_use_exactly_the_keys_publish_compares():
    # ``publish_lesson`` builds the same dict from the row and the review.
    assert set(signer.CLAIM_KEYS) == {
        "lesson_id",
        "revision_id",
        "fingerprint",
        "fingerprint_version",
        "review_sha256",
    }
    row = _row()
    assert signer.build_claims(row)["revision_id"] == row["id"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fingerprint", "b" * 64),
        ("fingerprint_version", "slcs-pack-v2"),
        ("review_sha256", "c" * 64),
        ("revision_id", str(uuid.uuid4())),
    ],
)
def test_a_receipt_for_different_claims_is_rejected(site_key, field, value):
    receipt = signer.build_claims(_row())
    token = signer.sign_receipt(receipt, site_key, issuer="seeword-slcs-editorial", kid="release-2026", ttl=600)
    with pytest.raises(AppError) as rejected:
        verify_lesson_receipt(token, {**receipt, field: value})
    assert rejected.value.status_code == 422


def test_unknown_kid_is_rejected(site_key):
    receipt = signer.build_claims(_row())
    token = signer.sign_receipt(receipt, site_key, issuer="seeword-slcs-editorial", kid="other", ttl=600)
    with pytest.raises(AppError):
        verify_lesson_receipt(token, receipt)


def test_a_receipt_longer_than_the_site_max_age_is_rejected(site_key):
    receipt = signer.build_claims(_row())
    token = signer.sign_receipt(receipt, site_key, issuer="seeword-slcs-editorial", kid="release-2026", ttl=901)
    with pytest.raises(AppError):
        verify_lesson_receipt(token, receipt)


def test_a_receipt_from_another_issuer_is_rejected(site_key):
    receipt = signer.build_claims(_row())
    token = signer.sign_receipt(receipt, site_key, issuer="someone-else", kid="release-2026", ttl=600)
    with pytest.raises(AppError):
        verify_lesson_receipt(token, receipt)


def test_missing_review_hash_is_a_signer_error_not_a_bad_token():
    with pytest.raises(signer.SignerError) as refused:
        signer._review_hash(_row(review=None))
    assert "审核" in str(refused.value)


def test_keygen_refuses_a_path_inside_the_repository(tmp_path, capsys):
    exit_code = signer.main(["keygen", "--out", str(signer._repo_root() / "receipt-key.pem")])
    assert exit_code == 1
    assert "仓库里" in capsys.readouterr().err


def test_keygen_does_not_overwrite_a_key_without_force(tmp_path, capsys):
    out = tmp_path / "key.pem"
    assert signer.main(["keygen", "--out", str(out)]) == 0
    original = out.read_bytes()
    capsys.readouterr()

    assert signer.main(["keygen", "--out", str(out)]) == 1
    assert "已存在" in capsys.readouterr().err
    assert out.read_bytes() == original

    assert signer.main(["keygen", "--out", str(out), "--force"]) == 0
    assert out.read_bytes() != original
    printed = json.loads(capsys.readouterr().err.split("SLCS_LESSON_RECEIPT_PUBLIC_KEYS=")[1].split("\n")[0])
    assert list(printed) == ["release-2026"]


def _seed_sqlite(tmp_path, row: dict, *, name: str) -> str:
    import asyncio

    import sqlalchemy
    from sqlalchemy.ext.asyncio import create_async_engine

    url = f"sqlite+aiosqlite:///{(tmp_path / name).as_posix()}"

    async def prepare():
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.execute(
                sqlalchemy.text(
                    "CREATE TABLE lesson_revisions (id TEXT, lesson_id TEXT, fingerprint TEXT,"
                    " fingerprint_version TEXT, status TEXT, review TEXT)"
                )
            )
            await connection.execute(
                sqlalchemy.text(
                    "INSERT INTO lesson_revisions VALUES (:id, :lesson_id, :fingerprint,"
                    " :fingerprint_version, :status, :review)"
                ),
                row,
            )
        await engine.dispose()

    asyncio.run(prepare())
    return url


def test_a_published_revision_is_refused(tmp_path):
    """A live revision needs no receipt, so the signer must not mint one for it."""
    import asyncio

    row = {**_row(), "status": "published", "review": json.dumps({"review_sha256": "a" * 64})}
    url = _seed_sqlite(tmp_path, row, name="published.db")

    with pytest.raises(signer.SignerError) as refused:
        asyncio.run(signer.read_revision(url, row["lesson_id"], row["id"]))
    assert "published" in str(refused.value)


def test_every_pending_publish_path_can_be_signed(tmp_path):
    """First publication (candidate) and restore (withdrawn) both need receipts."""
    import asyncio

    for status in ("candidate", "withdrawn"):
        row = {**_row(), "status": status, "review": json.dumps({"review_sha256": "a" * 64})}
        url = _seed_sqlite(tmp_path, row, name=f"{status}.db")
        loaded = asyncio.run(signer.read_revision(url, row["lesson_id"], row["id"]))
        assert loaded["review_sha256"] == "a" * 64
        # Omitting --revision-id is safe when exactly one revision is pending.
        assert asyncio.run(signer.read_revision(url, row["lesson_id"], None))["id"] == row["id"]
