"""The receipt signer and the site's verifier must agree, byte for byte.

The signer exists outside the app on purpose (it holds the private key), so
nothing type-checks the two halves against each other. These tests are that
check: a token from ``scripts/sign_lesson_receipt.py`` must pass
``verify_lesson_receipt`` under the settings the site would have, and the claims
it reads must be the ones ``publish_lesson`` compares.
"""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

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


def test_claims_match_what_publish_lesson_compares():
    """Pin the claim set against the *server*, not against a copy of itself.

    ``publish_lesson`` builds the expected dict; if it grew a sixth field the
    signer would silently keep signing five and every publish would 422. Reading
    the source is the only way to assert that without running a publish here —
    ``test_a_signed_receipt_is_accepted_by_the_site`` covers the runtime side.
    """
    source = (Path(__file__).resolve().parents[1] / "app" / "services" / "lessons.py").read_text(encoding="utf-8")
    start = source.index("claims = {", source.index("async def publish_lesson"))
    block = source[start : source.index("}", start)]
    for name in ("lesson_id", "revision_id", "review_sha256"):
        assert f'"{name}"' in block, f"publish_lesson no longer asks for {name}"
    # The fingerprint pair arrives through ``**_fingerprint_fields``; assert both
    # that the expander is still used and what it expands to.
    assert "_fingerprint_fields(revision)" in block
    helper = source[source.index("def _fingerprint_fields") :]
    helper = helper[: helper.index("}")]
    for name in ("fingerprint", "fingerprint_version"):
        assert f'"{name}"' in helper, f"_fingerprint_fields no longer yields {name}"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lesson_id", "another-lesson"),
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


def test_a_receipt_from_a_different_key_with_a_known_kid_is_rejected(site_key):
    """Unknown-kid fails at lookup; this one must fail at signature verification."""
    receipt = signer.build_claims(_row())
    token = signer.sign_receipt(
        receipt, Ed25519PrivateKey.generate(), issuer="seeword-slcs-editorial", kid="release-2026", ttl=600
    )
    with pytest.raises(AppError):
        verify_lesson_receipt(token, receipt)


def test_iat_is_backdated_so_clock_skew_does_not_break_publishing(site_key):
    """PyJWT validates ``iat`` with zero leeway; a laptop 2 s ahead must still work."""
    receipt = signer.build_claims(_row())
    token = signer.sign_receipt(receipt, site_key, issuer="seeword-slcs-editorial", kid="release-2026", ttl=600)
    claims = jwt.decode(token, options={"verify_signature": False})
    assert claims["iat"] <= int(datetime.now(UTC).timestamp())
    assert claims["exp"] - claims["iat"] == 600
    verify_lesson_receipt(token, receipt)  # the verifier's own iat check passes


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


def _seed_sqlite(tmp_path, rows: list[dict], *, current_revision_id: str | None, name: str) -> str:
    """A minimal two-table fixture: the signer joins lessons.current_revision_id."""
    import asyncio

    import sqlalchemy
    from sqlalchemy.ext.asyncio import create_async_engine

    url = f"sqlite+aiosqlite:///{(tmp_path / name).as_posix()}"

    async def prepare():
        engine = create_async_engine(url)
        async with engine.begin() as connection:
            await connection.execute(
                sqlalchemy.text("CREATE TABLE lessons (id TEXT PRIMARY KEY, current_revision_id TEXT)")
            )
            await connection.execute(
                sqlalchemy.text(
                    "CREATE TABLE lesson_revisions (id TEXT, lesson_id TEXT, fingerprint TEXT,"
                    " fingerprint_version TEXT, status TEXT, review TEXT)"
                )
            )
            await connection.execute(
                sqlalchemy.text("INSERT INTO lessons VALUES (:id, :current_revision_id)"),
                {"id": rows[0]["lesson_id"], "current_revision_id": current_revision_id},
            )
            for row in rows:
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


def _pending_row(status: str = "candidate") -> dict:
    return {**_row(), "status": status, "review": json.dumps({"review_sha256": "a" * 64})}


def test_the_current_revision_needs_no_receipt(tmp_path):
    """``publish_lesson`` answers 409 for the current revision, so minting a token wastes work."""
    import asyncio

    row = _pending_row("published")
    url = _seed_sqlite(tmp_path, [row], current_revision_id=row["id"], name="current.db")

    with pytest.raises(signer.SignerError) as refused:
        asyncio.run(signer.read_revision(url, row["lesson_id"], row["id"]))
    assert "已是当前版" in str(refused.value)


@pytest.mark.parametrize("status", ["candidate", "withdrawn", "published"])
def test_every_publish_path_that_needs_a_receipt_can_be_signed(tmp_path, status):
    """candidate = first publication, withdrawn = restore, published-but-superseded = rollback.

    The last one matters: ``publish_lesson`` only refuses the *current* revision,
    and ``/admin/lessons`` renders the publish form for a superseded one. If the
    signer refused it, the operator would see a button no tool can complete.
    """
    import asyncio

    row = _pending_row(status)
    newer = {**row, "id": str(uuid.uuid4())}
    url = _seed_sqlite(tmp_path, [row, newer], current_revision_id=newer["id"], name=f"{status}.db")

    loaded = asyncio.run(signer.read_revision(url, row["lesson_id"], row["id"]))
    assert loaded["review_sha256"] == "a" * 64


def test_omitting_the_revision_id_refuses_when_several_are_publishable(tmp_path):
    """The shortcut must list the candidates, not silently pick one."""
    import asyncio

    first, second = (
        _pending_row("candidate"),
        {**_row(), "id": str(uuid.uuid4()), "review": json.dumps({"review_sha256": "a" * 64})},
    )
    url = _seed_sqlite(tmp_path, [first, second], current_revision_id=None, name="ambiguous.db")

    with pytest.raises(signer.SignerError) as refused:
        asyncio.run(signer.read_revision(url, first["lesson_id"], None))
    message = str(refused.value)
    assert first["id"] in message and second["id"] in message


def test_a_bad_database_url_does_not_echo_the_password(capsys):
    """A traceback from the driver is how a DSN reaches a log file."""
    secret = "SUPERSECRETPASSWORD"
    exit_code = signer.main(
        [
            "claims",
            "--database-url",
            f"not-a-url://user:{secret}@host/db",
            "--lesson-id",
            "welcome-to-wikisource",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert secret not in captured.err
    assert secret not in captured.out
    assert captured.err.startswith("错误：")


def test_database_url_falls_back_to_the_environment(monkeypatch, capsys):
    """Keeping the DSN out of argv keeps it out of `ps` and shell history."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@127.0.0.1:1/nonexistent")
    exit_code = signer.main(["claims", "--lesson-id", "welcome-to-wikisource"])
    assert exit_code == 1
    assert "错误：" in capsys.readouterr().err
