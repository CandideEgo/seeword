"""Issue the externally signed publication receipt for one reviewed lesson revision.

``POST /admin/lessons/{lesson_id}/revisions/{revision_id}/publish`` refuses to run
without a JWT signed by a key whose public half the site only *verifies*. Nothing
in the product could produce one, so a first lesson could be imported and reviewed
but never published. This is that missing half.

Three publish paths need a receipt, and all three must be signable or the
operator sees a form they cannot complete: a first publication (candidate), a
restore of a withdrawn revision, and a rollback to a superseded one (the older
revision is still ``published`` but no longer current). A revision that *is* the
current one needs no receipt and is refused here.

The signer is deliberately a separate role from the web process:

- it holds the Ed25519 **private** key, which never enters `backend/.env` or the
  repository — the site is configured with ``SLCS_LESSON_RECEIPT_PUBLIC_KEYS``
  (``{"<kid>": "<public key PEM>"}``) and ``SLCS_LESSON_RECEIPT_ISSUER`` only;
- it reads exactly five columns from the revision it is asked about and signs
  them; it does not import ``app.*``, share the app's configuration, or write
  anything back;
- it prints the claims it is about to sign (`stderr`) so the operator can compare
  them with what ``/admin/lessons`` showed before approving the review.

Usage (working directory ``backend/``, Windows needs ``PYTHONUTF8=1``)::

    # Once per signing key. Writes the private key outside the repository.
    python scripts/sign_lesson_receipt.py keygen --out ~/.seeword/slcs-receipt-key.pem

    # The claims the site will accept for a revision (read-only query).
    python scripts/sign_lesson_receipt.py claims --database-url "$DB" \
        --lesson-id welcome-to-wikisource --revision-id 570f8301-...

    # Emit the token: stdout is the JWT alone, the claims summary goes to stderr,
    # so `> receipt.jwt` keeps the file pasteable.
    python scripts/sign_lesson_receipt.py sign --database-url "$DB" \
        --private-key ~/.seeword/slcs-receipt-key.pem --kid release-2026 \
        --lesson-id welcome-to-wikisource --revision-id 570f8301-...

``--database-url`` may be omitted when ``DATABASE_URL`` is set; keeping the DSN
in the environment rather than in argv keeps it out of ``ps`` and shell history.

Exit codes: 0 signed, 1 usage / lookup / state error.

Two rules this script cannot enforce and does not pretend to:

1. **Sign only what you reviewed.** The receipt is the operator's attestation
   that this fingerprint and this review hash are the ones they approved.
   Compare the printed ``fingerprint`` / ``review_sha256`` with the values in
   ``/admin/lessons`` before publishing.
2. **The receipt is short-lived on purpose.** ``--ttl`` defaults to 600 s and the
   site rejects anything longer than ``SLCS_LESSON_RECEIPT_MAX_AGE_SECONDS``
   (900 s by default). Sign right before publishing; a stale receipt is a 422,
   never a silent acceptance.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

#: Must match ``app.services.lesson_receipts``. Duplicated on purpose: the signer
#: is not allowed to import the verifier, and a drift here fails loudly at the
#: first publish (the site answers 422) rather than silently accepting a token.
AUDIENCE = "seeword-slcs-lesson-publication"
TOKEN_TYPE = "seeword-slcs-lesson-receipt+jwt"
CLAIM_KEYS = ("lesson_id", "revision_id", "fingerprint", "fingerprint_version", "review_sha256")

DEFAULT_MAX_AGE = 600
_SLUG = re.compile(r"[A-Za-z0-9_-]{1,64}")
_SHA256 = re.compile(r"[a-f0-9]{64}")
#: ``scheme://user:password@host`` — the password half, for redacting a DSN the
#: driver refused before SQLAlchemy could parse it.
_USERINFO = re.compile(r"://[^:/@]+:([^@/]+)@")

_REVISION_QUERY = """
    SELECT r.id, r.lesson_id, r.fingerprint, r.fingerprint_version, r.status, r.review,
           l.current_revision_id
    FROM lesson_revisions r
    JOIN lessons l ON l.id = r.lesson_id
    WHERE r.lesson_id = :lesson_id
"""


class SignerError(RuntimeError):
    """A usage, lookup or state problem; printed as one line and exit 1."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _redact(exc: BaseException, database_url: str | None) -> str:
    """One line for the operator, never the password.

    SQLAlchemy and asyncpg errors quote the URL verbatim, so a mistyped DSN would
    otherwise put the database password into shell history, CI logs and whatever
    collected stderr. Every occurrence is replaced, not just the first.

    ``make_url`` handles a well-formed DSN; a malformed one is exactly the case
    that raises, so fall back to finding the ``user:password@`` segment by regex.
    """
    message = f"{type(exc).__name__}: {exc}"
    if database_url:
        password = None
        try:
            from sqlalchemy.engine import make_url

            password = make_url(database_url).password
        except Exception:
            secret = _USERINFO.findall(database_url)
            password = secret[0] if len(secret) == 1 else None
        if password:
            message = message.replace(password, "***")
    return " ".join(message.split())[:600]


def load_private_key(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SignerError(f"{path} 不是 Ed25519 私钥（课程发布收据只接受 EdDSA）")
    return key


def public_pem(key: Ed25519PrivateKey) -> str:
    return (
        key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )


def build_claims(row: dict) -> dict:
    """Return only the claims the site compares, in the shape it compares them."""
    return {
        "lesson_id": row["lesson_id"],
        "revision_id": row["id"],
        "fingerprint": row["fingerprint"],
        "fingerprint_version": row["fingerprint_version"],
        "review_sha256": _review_hash(row),
    }


#: ``verify_lesson_receipt`` passes no ``leeway`` to PyJWT, so an ``iat`` even
#: one second ahead of the site's clock is ImmatureSignatureError — a 422 that
#: says "收据无效" and points at nothing. Backdate by this much so ordinary NTP
#: drift between the operator's laptop and the server is harmless. It costs
#: nothing: the window is still ``ttl`` long, just shifted.
CLOCK_SKEW_SECONDS = 30


def sign_receipt(receipt: dict, key: Ed25519PrivateKey, *, issuer: str, kid: str, ttl: int) -> str:
    if not _SLUG.fullmatch(kid):
        raise SignerError(f"kid {kid!r} 只能由 1–64 个 A-Z a-z 0-9 _ - 组成")
    if not issuer.strip():
        raise SignerError("签发方（--issuer）不能为空")
    if not 0 < ttl <= 86_400:
        raise SignerError("--ttl 必须在 1–86400 秒之间；默认 600，站点上限 900")
    now = int(datetime.now(UTC).timestamp())
    issued = now - CLOCK_SKEW_SECONDS
    payload = {
        "iss": issuer,
        "aud": AUDIENCE,
        "iat": issued,
        "exp": issued + ttl,
        "jti": uuid.uuid4().hex,
        "v": 1,
        "receipt": {name: receipt[name] for name in CLAIM_KEYS},
    }
    return jwt.encode(payload, key, algorithm="EdDSA", headers={"kid": kid, "typ": TOKEN_TYPE})


def _review_hash(row: dict) -> str:
    review = row["review"]
    if isinstance(review, str):
        try:
            review = json.loads(review)
        except ValueError:
            raise SignerError(f"修订 {row['id']} 的审核记录无法解析") from None
    if not isinstance(review, dict):
        raise SignerError(f"修订 {row['id']} 还没有审核记录；先在 /admin/lessons 保存审核再签收据")
    value = review.get("review_sha256")
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise SignerError(f"修订 {row['id']} 的审核记录里没有 review_sha256；重新保存一次审核")
    return value


async def read_revision(database_url: str, lesson_id: str, revision_id: str | None) -> dict:
    """Read one revision in a read-only transaction; never touches the site's session."""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            # Postgres only: SQLite (used by the tests) has no such statement, and
            # on a read-only replica the session is already read-only.
            if connection.dialect.name == "postgresql":
                await connection.execute(text("SET TRANSACTION READ ONLY"))
            if revision_id:
                statement = _REVISION_QUERY + " AND r.id = :revision_id"
                params = {"lesson_id": lesson_id, "revision_id": revision_id}
            else:
                # Three publish paths need a receipt, and all three have to be
                # signable or the operator sees a form they cannot complete:
                # a first publication (candidate), a restore of a withdrawn
                # revision, and a rollback to a superseded one. A revision that
                # *is* the current one needs no receipt, so it is excluded here.
                statement = _REVISION_QUERY + " AND r.id IS DISTINCT FROM l.current_revision_id"
                params = {"lesson_id": lesson_id}
            rows = [dict(row._mapping) for row in (await connection.execute(text(statement), params))]
    finally:
        await engine.dispose()

    if not rows:
        where = f"修订 {revision_id}" if revision_id else "待发布的修订"
        raise SignerError(f"找不到课程 {lesson_id} 的{where}")
    if len(rows) > 1:
        listed = "、".join(f"{row['id']}（{row['status']}）" for row in rows)
        raise SignerError(f"{lesson_id} 有多个可发布的修订：{listed}；用 --revision-id 指定一个")

    row = rows[0]
    if revision_id and row["id"] == row["current_revision_id"]:
        # ``publish_lesson`` answers 409 here, so a receipt would be wasted work
        # and an unclear error later.
        raise SignerError(f"修订 {row['id']} 已是当前版；发布当前版不需要收据")
    return {**row, "review_sha256": _review_hash(row)}


def _summarise(row: dict, receipt: dict) -> str:
    return "\n".join(
        [
            f"课程      {receipt['lesson_id']}",
            f"修订      {receipt['revision_id']}  状态 {row['status']}",
            f"指纹      {receipt['fingerprint']}",
            f"指纹版本  {receipt['fingerprint_version']}",
            f"审核哈希  {receipt['review_sha256']}",
        ]
    )


def _cmd_keygen(args: argparse.Namespace) -> int:
    out: Path = args.out.expanduser().resolve()
    if out.exists() and not args.force:
        raise SignerError(f"{out} 已存在；换一个路径，或加 --force 覆盖（旧密钥签的收据将无法再验签）")
    if _repo_root() in out.parents:
        raise SignerError(f"{out} 在仓库里；私钥不能入库（本仓库不保存任何私钥）")
    key = Ed25519PrivateKey.generate()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    try:
        os.chmod(out, 0o600)
    except OSError:  # Windows has no meaningful POSIX mode; the directory ACL governs.
        pass
    print(f"私钥已写入 {out}，别入库、别进镜像。", file=sys.stderr)
    print("\n站点侧配置（backend/.env 或生产 compose 环境白名单）：\n", file=sys.stderr)
    print(f"SLCS_LESSON_RECEIPT_ISSUER={args.issuer}", file=sys.stderr)
    print(f"SLCS_LESSON_RECEIPT_PUBLIC_KEYS={json.dumps({args.kid: public_pem(key)})}", file=sys.stderr)
    print(
        "\n同一课程可以有多个 kid：换钥时把新公钥加进这个 JSON，"
        "等所有旧收据过期后再删掉旧的——删早了，历史上用旧钥签的收据就再也验不过。",
        file=sys.stderr,
    )
    return 0


def _cmd_claims(args: argparse.Namespace) -> int:
    row = asyncio.run(read_revision(args.database_url, args.lesson_id, args.revision_id))
    receipt = build_claims(row)
    print(_summarise(row, receipt), file=sys.stderr)
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _cmd_sign(args: argparse.Namespace) -> int:
    key = load_private_key(args.private_key.expanduser().resolve())
    row = asyncio.run(read_revision(args.database_url, args.lesson_id, args.revision_id))
    receipt = build_claims(row)
    token = sign_receipt(receipt, key, issuer=args.issuer, kid=args.kid, ttl=args.ttl)
    print(_summarise(row, receipt), file=sys.stderr)
    print(f"签发方    {args.issuer}  kid {args.kid}  有效期 {args.ttl}s", file=sys.stderr)
    print("\n把下面这一行（只这一行）粘进 /admin/lessons 的「签名发布收据」。", file=sys.stderr)
    print(token)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SLCS 课程发布收据的签发方工具")
    sub = parser.add_subparsers(dest="command", required=True)

    keygen = sub.add_parser("keygen", help="生成一对 Ed25519 密钥，打印站点侧配置")
    keygen.add_argument("--out", type=Path, required=True, help="私钥输出路径（必须在仓库之外）")
    keygen.add_argument("--issuer", default="seeword-slcs-editorial", help="签发方标识；站点要配成同一个值")
    keygen.add_argument("--kid", default="release-2026", help="密钥编号，站点公钥表里的键")
    keygen.add_argument("--force", action="store_true", help="覆盖已存在的私钥文件")
    keygen.set_defaults(handler=_cmd_keygen)

    for name, handler, help_text in (
        ("claims", _cmd_claims, "只读打印某修订的收据声明，供人工核对"),
        ("sign", _cmd_sign, "签发收据，JWT 写 stdout"),
    ):
        command = sub.add_parser(name, help=help_text)
        command.add_argument(
            "--database-url",
            default=None,
            help="只读查询用的库地址（postgresql+asyncpg://…）；省略时读环境变量 DATABASE_URL",
        )
        command.add_argument("--lesson-id", required=True)
        command.add_argument(
            "--revision-id",
            default=None,
            help="省略时要求该课程只有一个可发布的修订（候选、已撤回待恢复，或已发布但被新版本取代）",
        )
        if name == "sign":
            command.add_argument("--private-key", type=Path, required=True)
            command.add_argument("--issuer", default="seeword-slcs-editorial")
            command.add_argument("--kid", default="release-2026")
            command.add_argument("--ttl", type=int, default=DEFAULT_MAX_AGE, help="有效期秒数，默认 600，站点上限 900")
        command.set_defaults(handler=handler)

    args = parser.parse_args(argv)
    if getattr(args, "database_url", None) is None:
        args.database_url = os.environ.get("DATABASE_URL", "").strip() or None
    if args.command in {"claims", "sign"} and not args.database_url:
        print("错误：需要 --database-url，或先设好环境变量 DATABASE_URL", file=sys.stderr)
        return 1
    try:
        result = args.handler(args)
    except SignerError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # A raw traceback from the driver is how a DSN reaches a log file: the
        # SQLAlchemy and asyncpg messages quote the URL, password included. One
        # line, with the password stripped, keeps exit code 1 without the leak.
        print(f"错误：{_redact(exc, args.database_url)}", file=sys.stderr)
        return 1
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
