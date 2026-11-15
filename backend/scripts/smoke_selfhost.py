"""Localhost production smoke for the model-free self-host stack.

Explicitly opt in with --confirm-isolated-stack. Builds images and migrates ONLY
an automatically named, disposable Docker project. Never accepts an existing DB,
project, env file or remote URL. Uses synthetic content, not a private dictionary.
Requires Docker Compose and the backend Python dependencies; no server is started
by importing this module. The stack and its named volumes are removed in finally.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import ipaddress
import json
import os
import secrets
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import uuid
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))


def synthetic_pack() -> dict:
    """Self-authored test material, with no actual remote media fetch."""
    rights = {
        "attribution": "SeeWord smoke synthetic fixture",
        "basis": "自创合成测试内容；仅工程演练，不是真实内容权利验收",
        "evidence_url": "https://example.invalid/selfhost-smoke-evidence",
    }
    return {
        "schema_version": "0.1.0",
        "lesson_id": "selfhost-smoke",
        "title": "Synthetic smoke lesson",
        "source_language": "en",
        "translation_language": "zh-CN",
        "media": {
            "source_url": "https://example.invalid/synthetic.webm",
            "duration_ms": 2000,
            "access_mode": "external_link",
        },
        "segments": [
            {
                "id": "s1",
                "start_ms": 0,
                "end_ms": 2000,
                "text": "Read safely.",
                "translation": "安全阅读。",
                "tokens": [
                    {"id": "w1", "start_char": 0, "end_char": 4, "timing": {"start_ms": 0, "end_ms": 900}},
                    {"id": "w2", "start_char": 5, "end_char": 11, "timing": {"start_ms": 900, "end_ms": 1900}},
                ],
            }
        ],
        "vocabulary": [{"headword": "safely", "gloss": "安全地", "segment_id": "s1", "token_ids": ["w2"]}],
        "provenance": {kind: dict(rights) for kind in ("media", "transcript", "translation", "vocabulary")},
    }


def _ensure_smoke() -> None:
    from sqlalchemy.engine import make_url

    from app.core.config import get_settings

    settings = get_settings()
    identifier = os.environ.get("SELFHOST_SMOKE_ID", "")
    url = make_url(settings.database_url)
    if not (
        identifier.startswith("selfhost_smoke_")
        and len(identifier) == len("selfhost_smoke_") + 12
        and all(c in "0123456789abcdef" for c in identifier[-12:])
        and url.database == identifier
        and url.host == "db"
        and settings.env == "production"
        and not settings.llm_enabled
        and not settings.content_production_enabled
        and not settings.sms_dev_fake_enabled
    ):
        raise RuntimeError("Refusing a non-isolated or non-production smoke target")


async def _inside(action: str) -> None:
    _ensure_smoke()
    from sqlalchemy import select

    from app.core.database import get_async_session_maker
    from app.models.user import RoleType, User

    if action == "bootstrap":
        from scripts.create_admin import _create_or_promote

        data = json.load(sys.stdin)
        for phone, role in (("13900000001", RoleType.admin), ("13900000002", RoleType.user)):
            await _create_or_promote(phone, data["password"], False, role=role)
    elif action == "expire":
        async with get_async_session_maker()() as db:
            learner = await db.scalar(select(User).where(User.phone == "13900000002"))
            if learner is None or learner.deletion_requested_at is None:
                raise RuntimeError("Synthetic learner must request deletion through HTTP first")
            # Accelerate this fixture only; never change the product's 30-day policy.
            learner.deletion_scheduled_at = datetime.now(UTC) - timedelta(seconds=1)
            await db.commit()
    elif action == "check-purged":
        async with get_async_session_maker()() as db:
            if await db.scalar(select(User.id).where(User.phone == "13900000002")) is not None:
                raise RuntimeError("Synthetic learner has not been purged by beat/worker")
            if await db.scalar(select(User.id).where(User.phone == "13900000001")) is None:
                raise RuntimeError("Another account was incorrectly purged")
    elif action == "heartbeats":
        from app.core.heartbeat import BEAT_HEARTBEAT_KEY, WORKER_HEARTBEAT_KEY, age_seconds
        from app.core.redis import close_redis, get_redis

        redis = await get_redis()
        for key in (BEAT_HEARTBEAT_KEY, WORKER_HEARTBEAT_KEY):
            age = age_seconds(await redis.get(key), now=time.time())
            if age is None or age > 60:
                raise RuntimeError(f"Missing/stale process heartbeat: {key}")
        await close_redis()


def _certificate(directory: Path) -> Path:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=2))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    (directory / "privkey.pem").write_bytes(
        key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    )
    path = directory / "fullchain.pem"
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return path


def _docker_environment() -> dict[str, str]:
    # Do not inherit official credentials or Compose override variables. Docker
    # context is checked before any build/up; DOCKER_HOST is intentionally absent.
    allowed = {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "USERPROFILE",
        "HOME",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMFILES",
        "TEMP",
        "TMP",
        "DOCKER_CONFIG",
    }
    return {k: v for k, v in os.environ.items() if k.upper() in allowed} | {"PYTHONUTF8": "1"}


def host_smoke(port: int) -> int:
    import httpx
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from scripts.sign_lesson_receipt import public_pem, sign_receipt

    # Prefer the native executable on Windows. A PATH docker.cmd wrapper may
    # enter WSL, where this process's Windows temp/Compose paths are not valid.
    docker = shutil.which("docker.exe" if os.name == "nt" else "docker")
    if docker is None:
        raise RuntimeError("Docker CLI is required")
    child_env = _docker_environment()
    context = subprocess.run(
        [docker, "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
        env=child_env,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()
    if not (context.startswith("npipe://") or context.startswith("unix://")):
        raise RuntimeError("Refusing a non-local Docker context")
    suffix = uuid.uuid4().hex[:12]
    identifier = f"selfhost_smoke_{suffix}"
    project = f"seeword-selfhost-smoke-{suffix}"
    private_key = Ed25519PrivateKey.generate()
    password = f"Aa1-{secrets.token_hex(16)}"
    with tempfile.TemporaryDirectory(prefix="seeword-selfhost-smoke-") as temp:
        directory = Path(temp)
        cert = _certificate(directory)
        values = {
            "COMPOSE_PROJECT_NAME": project,
            "SELFHOST_IMAGE_PREFIX": project,
            "DB_NAME": identifier,
            "DB_PASSWORD": secrets.token_hex(32),
            "REDIS_PASSWORD": secrets.token_hex(32),
            "JWT_SECRET": secrets.token_hex(32),
            "SITE_URL": f"https://localhost:{port}",
            "HTTPS_PORT": str(port),
            "SSL_CERT_DIR": directory.as_posix(),
            "LLM_ENABLED": "false",
            "CONTENT_PRODUCTION_ENABLED": "false",
            "SLCS_LESSONS_ENABLED": "true",
            "SLCS_VOCABULARY_ENABLED": "true",
            "SLCS_LESSON_RECEIPT_ISSUER": "selfhost-smoke",
            "SLCS_LESSON_RECEIPT_PUBLIC_KEYS": json.dumps({"smoke": public_pem(private_key)}),
        }
        env_file = directory / "smoke.env"
        env_file.write_text("\n".join(f"{k}='{v}'" for k, v in values.items()), encoding="utf-8")
        # Smoke-only accelerated cadence; executes the real beat and real purge
        # task, not eager mode or a direct call to the task body.
        override = directory / "smoke.compose.json"
        override.write_text(
            json.dumps(
                {
                    "services": {
                        "beat": {
                            "command": ["python", "scripts/smoke_selfhost.py", "--inside", "beat"],
                            "environment": {"SELFHOST_SMOKE_ID": identifier},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        compose = [
            docker,
            "compose",
            "--env-file",
            str(env_file),
            "--project-name",
            project,
            "-f",
            str(ROOT / "docker-compose.selfhost.yml"),
            "-f",
            str(override),
        ]

        def run(*args: str, payload: dict | None = None) -> None:
            result = subprocess.run(
                compose + list(args),
                env=child_env,
                cwd=ROOT,
                input=json.dumps(payload) if payload is not None else None,
                text=True,
                capture_output=True,
                timeout=1800,
            )
            if result.returncode:
                from app.core.redaction import redact

                output = result.stderr or result.stdout
                for secret in (password, values["DB_PASSWORD"], values["REDIS_PASSWORD"], values["JWT_SECRET"]):
                    output = output.replace(secret, "***")
                raise RuntimeError(f"Compose {args[0]} failed (exit {result.returncode}): {redact(output)[-2000:]}")

        def inside(action: str, payload: dict | None = None) -> None:
            run(
                "exec",
                "-T",
                "-e",
                f"SELFHOST_SMOKE_ID={identifier}",
                "backend",
                "python",
                "scripts/smoke_selfhost.py",
                "--inside",
                action,
                payload=payload,
            )

        try:
            print(f"Isolated project: {project}; localhost:{port}; ENV=production", flush=True)
            # These two images are independent but memory-heavy. Build them
            # serially so a low-memory local host does not run two builders at once.
            run("build", "backend")
            run("build", "frontend")
            run("up", "-d", "--wait", "--wait-timeout", "240")
            run("exec", "-T", "backend", "python", "scripts/check_schema_revision.py")
            inside("bootstrap", {"password": password})
            tls = ssl.create_default_context(cafile=str(cert))
            with httpx.Client(base_url=values["SITE_URL"], verify=tls, trust_env=False, timeout=30) as client:

                def request(method: str, path: str, *, token: str | None = None, expected: int = 200, **kwargs):
                    response = client.request(
                        method, path, headers={"Authorization": f"Bearer {token}"} if token else {}, **kwargs
                    )
                    if response.status_code != expected:
                        raise RuntimeError(
                            f"HTTP {method} {path.split('?')[0]}: expected {expected}, got {response.status_code}"
                        )
                    return response

                admin = request(
                    "POST", "/api/v1/auth/phone-login", json={"phone": "13900000001", "password": password}
                ).json()["token"]
                learner = request(
                    "POST", "/api/v1/auth/phone-login", json={"phone": "13900000002", "password": password}
                ).json()["token"]
                learner_id = request("GET", "/api/v1/users/me", token=learner).json()["id"]
                request("GET", "/api/v1/users/me", expected=401)
                request(
                    "POST",
                    "/api/v1/videos/seed-full",
                    token=admin,
                    expected=503,
                    json={"source_url": "https://www.youtube.com/watch?v=abcdefghijk"},
                )
                request(
                    "POST", "/api/v1/auth/sms/send-code", expected=502, json={"phone": "13900000002", "purpose": "auth"}
                )
                request("POST", "/api/v1/auth/sms/login", expected=400, json={"phone": "13900000002", "code": "1234"})
                detail = request(
                    "POST",
                    "/api/v1/admin/lessons/import",
                    token=admin,
                    json={
                        "operation_id": "smoke-import",
                        "pack_json": json.dumps(synthetic_pack(), ensure_ascii=False),
                    },
                ).json()
                revision = detail["revision_id"]
                prefix = f"/api/v1/admin/lessons/selfhost-smoke/revisions/{revision}"
                detail = request(
                    "POST",
                    prefix + "/review",
                    token=admin,
                    json={
                        "operation_id": "smoke-review",
                        "source_commit": "0" * 40,
                        "uses": {
                            kind: {"approved": kind == "site_display", "evidence": "仅自创合成测试夹具，非真实内容验收"}
                            for kind in ("site_display", "model_processing", "external_redistribution")
                        },
                    },
                ).json()
                claims = {k: detail[k] for k in ("lesson_id", "revision_id", "fingerprint", "fingerprint_version")}
                claims["review_sha256"] = detail["review"]["review_sha256"]
                receipt = sign_receipt(claims, private_key, issuer="selfhost-smoke", kid="smoke", ttl=600)
                request(
                    "POST",
                    prefix + "/publish",
                    token=admin,
                    json={"operation_id": "smoke-publish", "expected_current_revision_id": None, "receipt": receipt},
                )
                body = request("GET", f"/api/v1/lessons/selfhost-smoke/revisions/{revision}", token=learner).json()
                if body["pack"]["segments"][0]["text"] != "Read safely.":
                    raise RuntimeError("Fixed revision read returned different text")
                request(
                    "PUT",
                    "/api/v1/lessons/selfhost-smoke/progress",
                    token=learner,
                    json={"revision_id": revision, "position_ms": 500},
                )
                task_id = request("GET", "/api/v1/users/me/export", token=learner).json()["task_id"]
                deadline = time.monotonic() + 90
                while True:
                    export = request("GET", f"/api/v1/users/me/export/{task_id}", token=learner).json()
                    if export["status"] == "failed":
                        raise RuntimeError("Lifecycle worker failed export")
                    if export["status"] == "ready":
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Lifecycle worker did not finish export")
                    time.sleep(3)
                archive = request("GET", export["download_url"], token=learner)
                with zipfile.ZipFile(io.BytesIO(archive.content)) as bundle:
                    if json.loads(bundle.read("profile.json"))["id"] != learner_id:
                        raise RuntimeError("Export does not belong to the learner")
                    if json.loads(bundle.read("lesson_progress.json"))[0]["revision_id"] != revision:
                        raise RuntimeError("Export lost fixed revision progress")
                request("GET", export["download_url"], token=learner, expected=410)
                inside("heartbeats")
                request(
                    "POST",
                    "/api/v1/users/me/deletion",
                    token=learner,
                    json={"confirm": True, "reason": "synthetic selfhost smoke"},
                )
                inside("expire")
                deadline = time.monotonic() + 60
                while True:
                    status = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {learner}"}).status_code
                    if status == 401:
                        break
                    if status != 200 or time.monotonic() >= deadline:
                        raise RuntimeError("Beat/worker did not purge expired synthetic learner")
                    time.sleep(3)
                inside("check-purged")
                request("GET", "/api/v1/users/me", token=admin)
            print(
                "PASS: production guards, fixed reading/progress, real worker export, independent beat expiry purge",
                flush=True,
            )
            return 0
        except Exception:
            # Preserve the actual failing worker/beat evidence before removing
            # this disposable project. Never dump credentials or request tokens.
            from app.core.redaction import redact

            logs = subprocess.run(
                [*compose, "logs", "--no-color", "--tail", "80", "worker", "beat", "backend"],
                env=child_env,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            diagnostic = logs.stdout + logs.stderr
            for secret in (password, values["DB_PASSWORD"], values["REDIS_PASSWORD"], values["JWT_SECRET"]):
                diagnostic = diagnostic.replace(secret, "***")
            print("Isolated smoke diagnostics:\n" + str(redact(diagnostic))[-8000:], file=sys.stderr, flush=True)
            raise
        finally:
            # Exactly this generated project only; never use the operator's stack.
            run("down", "--volumes", "--remove-orphans")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-isolated-stack", action="store_true")
    parser.add_argument("--port", type=int, default=19443)
    parser.add_argument(
        "--inside", choices=["bootstrap", "expire", "check-purged", "heartbeats", "beat"], help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    if args.inside == "beat":
        _ensure_smoke()
        from app.tasks.celery_app import celery_app

        celery_app.conf.beat_schedule["purge-deleted-accounts"]["schedule"] = 5
        celery_app.start(["beat", "--schedule=/app/media/celerybeat-smoke", "--loglevel=warning"])
        return 0
    if args.inside:
        asyncio.run(_inside(args.inside))
        return 0
    if not args.confirm_isolated_stack:
        parser.error("必须显式 --confirm-isolated-stack；此命令会构建镜像并迁移新的可丢弃库")
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    try:
        return host_smoke(args.port)
    except Exception as exc:
        print(f"FAIL ({type(exc).__name__}): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
