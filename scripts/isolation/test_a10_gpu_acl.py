#!/usr/bin/env python3
"""A10 / OPS-04 —— GPU 服务端权限边界的隔离环境验证。

用例矩阵与判定口径的唯一家是
[当前运行边界](README.md)。
Redis/ACL 来自 [`deploy/redis/users.acl.template`](../../deploy/redis/users.acl.template)，
GPU 侧的 broker 设置来自 [`gpu-worker/gpu_worker/broker_settings.py`](../../gpu-worker/gpu_worker/broker_settings.py)
与 `gpu-worker/gpu_worker/celery_app.py`（真实 worker 与桩 worker 共用）。

运行（Windows，Docker 在 WSL 里）：

    PYTHONUTF8=1 backend/.venv/Scripts/python.exe scripts/isolation/test_a10_gpu_acl.py

每个用例记录命令与原始输出；结果写 `tmp/isolation/a10-<今天>.json`。
T9（SSH 隧道限制）在当前隔离环境无法执行：隔离栈没有 sshd，D6 又禁止引入新镜像；
脚本会以 SKIP 记录并输出生产宿主的配置清单，不作为通过。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shlex
import subprocess
import sys
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
GPU_DIR = REPO_ROOT / "gpu-worker"
STUB_WORKER = REPO_ROOT / "scripts" / "isolation" / "gpu_stub_worker.py"
COMPOSE_FILE = REPO_ROOT / "docker-compose.isolation.yml"

PROJECT = "seeword-isolation"
REDIS_CONTAINER = "seeword-isolation-redis"
PG_CONTAINER = "seeword-isolation-pg"
REDIS_HOST = "127.0.0.1"
REDIS_PORT = int(os.environ.get("A10_REDIS_PORT", "16379"))
REDIS_PASSWORD = os.environ.get("ISOLATION_REDIS_PASSWORD", "isolation-only")
GPU_PASSWORD = os.environ.get("ISOLATION_REDIS_GPU_PASSWORD", "isolation-gpu-only")
PG_HOST = "127.0.0.1"
PG_PORT = int(os.environ.get("A10_PG_PORT", "15432"))
PG_USER = "seeword"
PG_PASSWORD = os.environ.get("ISOLATION_PG_PASSWORD", "isolation-only")
PG_DB = "seeword_isolation"

REDIS_VOLUME = f"{PROJECT}_redisdata"
ACL_OUT = REPO_ROOT / "deploy" / "redis" / "users.acl.generated"

QUEUE = "transcription_gpu"
TASK_NAME = "app.tasks.video_processing.transcribe_video_gpu"
UNACKED_KEY = "gpu_unacked"
UNACKED_INDEX_KEY = "gpu_unacked_index"
UNACKED_MUTEX_KEY = "gpu_unacked_mutex"
HEARTBEAT_KEY = "worker:gpu:heartbeat"
HEARTBEAT_TTL_SECONDS = 90

CALLBACK_HOST = "127.0.0.1"
CALLBACK_PORT = int(os.environ.get("A10_CALLBACK_PORT", "18081"))
CALLBACK_SECRET = os.environ.get("A10_CALLBACK_SECRET", "a10-isolation-callback-secret")

# App settings for T10; set before any `import app.*` (which happens inside T10).
os.environ["ENV"] = "development"
os.environ["JWT_SECRET"] = "a10-isolation-secret-at-least-32-characters"
os.environ["DATABASE_URL"] = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
os.environ["REDIS_URL"] = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
os.environ["TRANSCRIPTION_CALLBACK_SECRET"] = CALLBACK_SECRET
os.environ["HEALTH_MONITOR_ENABLED"] = "false"

WORKERS: list[subprocess.Popen] = []


class SkippedCaseError(Exception):
    """A case the environment cannot execute (recorded as SKIP, not PASS)."""


# ---------------------------------------------------------------------------
# Docker plumbing (same shape as the A07 drill)
# ---------------------------------------------------------------------------


def _docker_prefix() -> list[str]:
    override = os.environ.get("A10_DOCKER")
    if override:
        return shlex.split(override)
    if os.name == "nt":
        return ["wsl", "-d", os.environ.get("A10_WSL_DISTRO", "Ubuntu-24.04"), "--", "docker"]
    return ["docker"]


def _wsl_path(path: Path) -> str:
    if os.name != "nt":
        return str(path)
    drive, rest = os.path.splitdrive(str(path))
    return f"/mnt/{drive.rstrip(':').lower()}{rest.replace(os.sep, '/')}"


def _compose_env() -> dict[str, str]:
    return {
        **os.environ,
        "ISOLATION_REDIS_PASSWORD": REDIS_PASSWORD,
        "ISOLATION_REDIS_GPU_PASSWORD": GPU_PASSWORD,
        "ISOLATION_PG_PASSWORD": PG_PASSWORD,
        "REDIS_PASSWORD": REDIS_PASSWORD,
        "REDIS_GPU_PASSWORD": GPU_PASSWORD,
    }


def _run(args: list[str], *, check: bool, timeout: int = 300) -> tuple[int, str, str]:
    proc = subprocess.run(args, capture_output=True, timeout=timeout, env=_compose_env())
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(args)}\nstdout:\n{out}\nstderr:\n{err}")
    return proc.returncode, out, err


def compose(*args: str, check: bool = True, timeout: int = 300) -> tuple[int, str, str]:
    if os.name == "nt":
        base = [
            *_docker_prefix(),
            "compose",
            "-p",
            PROJECT,
            "--project-directory",
            _wsl_path(REPO_ROOT),
            "-f",
            _wsl_path(COMPOSE_FILE),
        ]
    else:
        base = [*_docker_prefix(), "compose", "-p", PROJECT, "-f", str(COMPOSE_FILE)]
    return _run([*base, *args], check=check, timeout=timeout)


class CaseLog:
    def __init__(self) -> None:
        self.commands: list[dict] = []
        self.notes: list[str] = []

    def docker(self, *args: str, check: bool = True) -> tuple[int, str, str]:
        rc, out, err = _run([*_docker_prefix(), *args], check=False)
        self.commands.append({"cmd": "docker " + " ".join(args), "rc": rc, "out": out[-4000:], "err": err[-2000:]})
        if check and rc != 0:
            raise RuntimeError(f"docker {' '.join(args)} failed ({rc})\n{out}\n{err}")
        return rc, out, err

    def compose(self, *args: str, check: bool = True) -> tuple[int, str, str]:
        rc, out, err = compose(*args, check=False)
        self.commands.append(
            {"cmd": "docker compose " + " ".join(args), "rc": rc, "out": out[-4000:], "err": err[-2000:]}
        )
        if check and rc != 0:
            raise RuntimeError(f"docker compose {' '.join(args)} failed ({rc})\n{out}\n{err}")
        return rc, out, err

    def note(self, text: str) -> None:
        self.notes.append(text)


# ---------------------------------------------------------------------------
# Redis / PG / worker helpers
# ---------------------------------------------------------------------------


def render_acl() -> None:
    script = REPO_ROOT / "scripts" / "isolation" / "render_redis_acl.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--out", str(ACL_OUT)],
        capture_output=True,
        timeout=60,
        env=_compose_env(),
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ACL render failed:\n{proc.stdout.decode('utf-8', 'replace')}\n{proc.stderr.decode('utf-8', 'replace')}"
        )


def redis_client(username: str | None = None, *, socket_timeout: float = 10):
    import redis

    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        username=username,
        password=REDIS_PASSWORD if username in (None, "cloud", "default") else GPU_PASSWORD,
        decode_responses=True,
        socket_timeout=socket_timeout,
        socket_connect_timeout=5,
    )


def wait_redis(client, timeout: float = 60.0):
    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            if client.ping():
                return client
        except Exception as exc:
            last = exc
        time.sleep(0.3)
    raise TimeoutError(f"Redis identity {client.connection_pool.connection_kwargs.get('username')} 未就绪: {last}")


def wait_pg(timeout: float = 90.0) -> None:
    import socket

    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            with socket.create_connection((PG_HOST, PG_PORT), timeout=2):
                time.sleep(0.5)
                return
        except OSError as exc:
            last = exc
            time.sleep(0.5)
    raise TimeoutError(f"Postgres 未就绪: {last}")


def _prepare_app() -> None:
    for path in (BACKEND_DIR, GPU_DIR):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def start_worker(log: CaseLog, work_seconds: float = 0.0, visibility_timeout: float = 3600.0) -> subprocess.Popen:
    redis_url = f"redis://gpu:{GPU_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    cmd = [
        sys.executable,
        str(STUB_WORKER),
        "--redis-url",
        redis_url,
        "--queue",
        QUEUE,
        "--callback-url",
        f"http://{CALLBACK_HOST}:{CALLBACK_PORT}/callback",
        "--secret",
        CALLBACK_SECRET,
        "--work-seconds",
        str(work_seconds),
        "--visibility-timeout",
        str(visibility_timeout),
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    WORKERS.append(proc)
    safe_cmd = " ".join(cmd).replace(GPU_PASSWORD, "***")
    log.commands.append({"cmd": safe_cmd, "rc": None, "out": "", "err": ""})
    return proc


def stop_worker(proc: subprocess.Popen) -> str:
    if proc.poll() is None:
        proc.kill()
    try:
        output, _ = proc.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        output, _ = proc.communicate()
    if proc in WORKERS:
        WORKERS.remove(proc)
    return output or ""


def wait_heartbeat(cloud, timeout: float = 60.0) -> float:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if cloud.exists(HEARTBEAT_KEY):
            return cloud.ttl(HEARTBEAT_KEY)
        time.sleep(0.3)
    raise TimeoutError("桩 worker 没有写出心跳键")


def send_task(video_id: str) -> None:
    from celery import Celery

    producer = Celery("a10-producer", broker=f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0")
    producer.send_task(TASK_NAME, args=[video_id, "https://example.com/a10-drill.mp4", "youtube"], queue=QUEUE)


def acl_log(cloud, count: int = 50) -> list[dict]:
    raw = cloud.execute_command("ACL", "LOG", str(count))
    entries: list[dict] = []
    for item in raw or []:
        pairs: dict[str, str] = {}
        iterator = iter(item)
        for key, value in zip(iterator, iterator, strict=False):
            pairs[str(key)] = str(value)
        entries.append(pairs)
    return entries


def gpu_denials(cloud) -> list[dict]:
    return [entry for entry in acl_log(cloud) if entry.get("username") == "gpu"]


class CallbackServer:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.event = threading.Event()
        self._server: ThreadingHTTPServer | None = None

    def start(self) -> None:
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length).decode("utf-8", "replace")
                outer.requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
                outer.event.set()

            def log_message(self, *_args) -> None:
                pass

        self._server = ThreadingHTTPServer((CALLBACK_HOST, CALLBACK_PORT), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def reset(self) -> None:
        self.requests.clear()
        self.event.clear()

    def wait(self, timeout: float) -> bool:
        return self.event.wait(timeout)

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()


def expect_denied(gpu, command: str, *args: str) -> str:
    import redis

    try:
        gpu.execute_command(command, *args)
    except redis.exceptions.ResponseError as exc:
        message = str(exc)
        lower = message.lower()
        # Redis 7.4 phrases these as "User gpu has no permissions to run the
        # 'get' command" / "No permissions to access a key" (the NOPERM prefix
        # is only in RESP error codes, which redis-py strips).
        if any(word in lower for word in ("noperm", "no permissions", "unknown command", "command not allowed")):
            return message
        raise AssertionError(f"{command} 返回了非权限错误: {message}") from exc
    raise AssertionError(f"{command} 被允许，越权面未关闭")


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


def t1_cloud_identity(log: CaseLog) -> tuple[str, dict]:
    cloud = wait_redis(redis_client("cloud"))
    checks = {
        "set_blacklist": cloud.set("token_blacklist:a10:t1", "1", ex=600),
        "exists_blacklist": cloud.exists("token_blacklist:a10:t1"),
        "set_sms_cooldown": cloud.set("sms:cooldown:13800000000", "1", ex=60),
        "incr_rate_limit": cloud.incr("ratelimit:a10:t1"),
        "lpush_cloud_queue": cloud.lpush("celery", '{"task":"a10"}'),
        "sadd_binding": cloud.sadd("_kombu.binding.celery", "a10"),
        "set_cache": cloud.set("ai_cache:a10:t1", "x", ex=60),
    }
    whoami = cloud.execute_command("ACL", "WHOAMI")
    cloud.delete(
        "token_blacklist:a10:t1",
        "sms:cooldown:13800000000",
        "ratelimit:a10:t1",
        "ai_cache:a10:t1",
    )
    cloud.lrem("celery", 0, '{"task":"a10"}')
    cloud.srem("_kombu.binding.celery", "a10")
    ok = all(checks.values()) and whoami == "cloud"
    detail = f"cloud 身份全路径写入：{checks}；whoami={whoami}"
    if not ok:
        raise AssertionError(detail)
    return detail, {"checks": checks, "whoami": whoami}


def t2_gpu_consumption(log: CaseLog, cb: CallbackServer) -> tuple[str, dict]:
    cloud = wait_redis(redis_client("cloud"))
    cloud.delete(QUEUE, UNACKED_KEY, UNACKED_INDEX_KEY, UNACKED_MUTEX_KEY, HEARTBEAT_KEY)
    cloud.execute_command("ACL", "LOG", "RESET")
    cb.reset()

    proc = start_worker(log, 1.0)
    ttl_at_start = wait_heartbeat(cloud)
    video_id = str(uuid.uuid4())
    send_task(video_id)
    received = cb.wait(90)
    if not received:
        stop_worker(proc)
        raise AssertionError("桩 worker 没有在 90s 内回调")

    deadline = time.time() + 30
    while time.time() < deadline:
        if cloud.hlen(UNACKED_KEY) == 0 and cloud.llen(QUEUE) == 0:
            break
        time.sleep(0.5)

    ttl = cloud.ttl(HEARTBEAT_KEY)
    result_keys = cloud.keys("celery-task-meta-*")
    pidbox = cloud.execute_command("PUBSUB", "NUMSUB", "celery.pidbox")
    worker_output = stop_worker(proc)
    denials = gpu_denials(cloud)
    request = cb.requests[0] if cb.requests else {}

    checks = {
        "callback_received": received,
        "callback_secret_ok": str(request.get("headers", {}).get("X-Callback-Secret")) == CALLBACK_SECRET,
        "callback_video_id": video_id in str(request.get("body", "")),
        "heartbeat_ttl_within_contract": 0 < ttl <= HEARTBEAT_TTL_SECONDS,
        "unacked_drained": cloud.hlen(UNACKED_KEY) == 0,
        "queue_drained": cloud.llen(QUEUE) == 0,
        "no_result_keys": result_keys == [],
        "no_pidbox_subscriber": int(pidbox[1]) == 0 if len(pidbox) > 1 else False,
        "no_noperm_on_normal_path": denials == [],
    }
    failed = [name for name, ok in checks.items() if not ok]
    detail = (
        f"gpu 身份消费 1 条任务并回调；心跳 TTL={ttl}s；"
        f"结果键={len(result_keys)}；pidbox 订阅={pidbox[1] if len(pidbox) > 1 else '?'}；"
        f"正常路径 ACL LOG 拒绝 {len(denials)} 条"
    )
    if failed:
        raise AssertionError(f"{failed} / {detail} / worker={worker_output[-1500:]}")
    return detail, {
        "checks": checks,
        "heartbeat_ttl_at_start": ttl_at_start,
        "heartbeat_ttl": ttl,
        "callback": request,
        "acl_denials": denials,
        "worker_output": worker_output[-3000:],
    }


def t3_unacked_isolation(log: CaseLog, cb: CallbackServer) -> tuple[str, dict]:
    cloud = wait_redis(redis_client("cloud"))
    cloud.delete(QUEUE, UNACKED_KEY, UNACKED_INDEX_KEY, UNACKED_MUTEX_KEY)
    cloud.execute_command("ACL", "LOG", "RESET")
    cb.reset()

    # Default visibility_timeout (3600s) on purpose: recovery must come from
    # the worker's startup orphan restore, not from a compressed kombu window.
    proc = start_worker(log, 8.0)
    wait_heartbeat(cloud)
    video_id = str(uuid.uuid4())
    send_task(video_id)

    deadline = time.time() + 60
    while time.time() < deadline:
        if cloud.hlen(UNACKED_KEY) >= 1:
            break
        time.sleep(0.5)
    unacked_while_running = cloud.hlen(UNACKED_KEY)
    if unacked_while_running < 1:
        stop_worker(proc)
        raise AssertionError("任务没有进入 gpu_unacked（消费路径未走通）")

    stop_worker(proc)  # SIGKILL-equivalent on Windows
    time.sleep(1.0)
    after_kill = {
        "gpu_unacked": cloud.hlen(UNACKED_KEY),
        "cloud_unacked": cloud.hlen("unacked"),
        "queue": cloud.llen(QUEUE),
    }

    proc2 = start_worker(log, 0.0)
    wait_heartbeat(cloud)
    restored = cb.wait(90)
    if not restored:
        stop_worker(proc2)
        raise AssertionError("重启后未确认消息没有恢复投递")

    deadline = time.time() + 30
    while time.time() < deadline:
        if cloud.hlen(UNACKED_KEY) == 0 and cloud.llen(QUEUE) == 0:
            break
        time.sleep(0.5)
    worker_output = stop_worker(proc2)
    denials = gpu_denials(cloud)

    checks = {
        "message_was_unacked": unacked_while_running >= 1,
        "gpu_unacked_survived_kill": after_kill["gpu_unacked"] == 1,
        "cloud_unacked_untouched": after_kill["cloud_unacked"] == 0,
        "queue_empty_after_kill": after_kill["queue"] == 0,
        "redelivered_after_restart": restored,
        "unacked_drained_after_restart": cloud.hlen(UNACKED_KEY) == 0,
        "no_noperm_on_restore_path": denials == [],
    }
    failed = [name for name, ok in checks.items() if not ok]
    detail = (
        f"消费中被杀：gpu_unacked={after_kill['gpu_unacked']}、云 unacked={after_kill['cloud_unacked']}、"
        f"队列={after_kill['queue']}；重启后恢复回调={restored}，最终 unacked={cloud.hlen(UNACKED_KEY)}"
    )
    if failed:
        raise AssertionError(f"{failed} / {detail} / worker={worker_output[-1500:]}")
    return detail, {
        "checks": checks,
        "after_kill": after_kill,
        "redelivered": restored,
        "acl_denials": denials,
    }


def t4_blacklist_denied(log: CaseLog) -> tuple[str, dict]:
    gpu = wait_redis(redis_client("gpu"))
    denied = {
        "GET token_blacklist": expect_denied(gpu, "GET", "token_blacklist:a10"),
        "SET token_blacklist": expect_denied(gpu, "SET", "token_blacklist:a10", "1"),
        "EXISTS token_blacklist": expect_denied(gpu, "EXISTS", "token_blacklist:a10"),
    }
    detail = f"读/写撤销状态全部被拒：{list(denied)}"
    return detail, {"denied": denied}


def t5_cloud_queue_denied(log: CaseLog) -> tuple[str, dict]:
    gpu = wait_redis(redis_client("gpu"))
    denied = {
        "LPUSH celery": expect_denied(gpu, "LPUSH", "celery", "{}"),
        "SADD _kombu.binding.celery": expect_denied(gpu, "SADD", "_kombu.binding.celery", "a10"),
    }
    detail = f"向云端队列写任务被拒：{list(denied)}"
    return detail, {"denied": denied}


def t6_dangerous_denied(log: CaseLog) -> tuple[str, dict]:
    cloud = wait_redis(redis_client("cloud"))
    gpu = wait_redis(redis_client("gpu", socket_timeout=5))
    denied = {
        "FLUSHALL": expect_denied(gpu, "FLUSHALL"),
        "FLUSHDB": expect_denied(gpu, "FLUSHDB"),
        "CONFIG GET": expect_denied(gpu, "CONFIG", "GET", "appendonly"),
        "CONFIG SET": expect_denied(gpu, "CONFIG", "SET", "appendonly", "no"),
        "DEBUG SLEEP": expect_denied(gpu, "DEBUG", "SLEEP", "0"),
        "MONITOR": expect_denied(gpu, "MONITOR"),
        "CLIENT KILL": expect_denied(gpu, "CLIENT", "KILL", "ID", "1"),
        "ACL SETUSER": expect_denied(gpu, "ACL", "SETUSER", "gpu", "on"),
        "ACL LIST": expect_denied(gpu, "ACL", "LIST"),
        "KEYS *": expect_denied(gpu, "KEYS", "*"),
        "SCAN 0": expect_denied(gpu, "SCAN", "0"),
        "SHUTDOWN": expect_denied(gpu, "SHUTDOWN"),
    }
    if not cloud.ping():
        raise AssertionError("危险命令用例后 Redis 不再可用（越权写已生效）")
    detail = f"清库/配置/管理/枚举类命令全部被拒（{len(denied)} 条）"
    return detail, {"denied": denied}


def t7_other_keys_denied(log: CaseLog) -> tuple[str, dict]:
    gpu = wait_redis(redis_client("gpu"))
    denied = {
        "SET ai_cache": expect_denied(gpu, "SET", "ai_cache:a10", "x"),
        "SET cache": expect_denied(gpu, "SET", "cache:a10", "x"),
        "SET worker:gpu:other": expect_denied(gpu, "SET", "worker:gpu:other", "x"),
    }
    detail = f"其它命名空间的键被拒：{list(denied)}"
    return detail, {"denied": denied}


def t8_result_and_pubsub_closed(log: CaseLog, cb: CallbackServer) -> tuple[str, dict]:
    cloud = wait_redis(redis_client("cloud"))
    gpu = wait_redis(redis_client("gpu", socket_timeout=5))
    denied = {
        "SUBSCRIBE": expect_denied(gpu, "SUBSCRIBE", "a10"),
        "PSUBSCRIBE": expect_denied(gpu, "PSUBSCRIBE", "*"),
        "PUBLISH": expect_denied(gpu, "PUBLISH", "a10", "x"),
        "PUBSUB NUMSUB": expect_denied(gpu, "PUBSUB", "NUMSUB", "celery.pidbox"),
    }
    result_keys = cloud.keys("celery-task-meta-*")
    pidbox = cloud.execute_command("PUBSUB", "NUMSUB", "celery.pidbox")
    checks = {
        "no_result_keys": result_keys == [],
        "no_pidbox_subscriber": int(pidbox[1]) == 0 if len(pidbox) > 1 else False,
    }
    failed = [name for name, ok in checks.items() if not ok]
    detail = f"pubsub 全部被拒；结果键={len(result_keys)}；pidbox 订阅={pidbox[1] if len(pidbox) > 1 else '?'}"
    if failed:
        raise AssertionError(f"{failed} / {detail}")
    return detail, {"denied": denied, "checks": checks, "result_keys": result_keys, "pidbox": pidbox}


def t10_callback_secret(log: CaseLog) -> tuple[str, dict]:
    log.compose("--profile", "pg", "up", "-d", "pg")
    wait_pg()
    _prepare_app()

    import httpx

    import app.models  # noqa: F401 - fill Base.metadata
    from app.core.config import get_settings
    from app.core.database import Base, get_engine
    from app.main import create_app

    async def scenario() -> dict:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        application = create_app()
        transport = httpx.ASGITransport(app=application)
        url = "/api/v1/internal/transcription/callback"
        payload = {"video_id": str(uuid.uuid4()), "status": "ok", "segments": [], "audio_duration": 1.0}

        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            missing = await client.post(url, json=payload)
            wrong = await client.post(url, json=payload, headers={"X-Callback-Secret": "wrong-secret"})
            right = await client.post(url, json=payload, headers={"X-Callback-Secret": CALLBACK_SECRET})
            # Raw non-ASCII header bytes (httpx refuses to encode str headers as non-ASCII;
            # the server decodes header bytes as latin-1, which used to crash
            # secrets.compare_digest on str and turn 401 into 500).
            non_ascii = await client.post(url, json=payload, headers={"X-Callback-Secret": "é".encode("latin-1")})

            get_settings.cache_clear()
            os.environ["TRANSCRIPTION_CALLBACK_SECRET"] = "a10-rotated-secret"
            try:
                old_after_rotation = await client.post(
                    url, json=payload, headers={"X-Callback-Secret": CALLBACK_SECRET}
                )
                new_after_rotation = await client.post(
                    url, json=payload, headers={"X-Callback-Secret": "a10-rotated-secret"}
                )
            finally:
                os.environ["TRANSCRIPTION_CALLBACK_SECRET"] = CALLBACK_SECRET
                get_settings.cache_clear()

        await engine.dispose()
        return {
            "missing": missing.status_code,
            "wrong": wrong.status_code,
            "right": right.status_code,
            "right_body": right.json(),
            "non_ascii": non_ascii.status_code,
            "old_after_rotation": old_after_rotation.status_code,
            "new_after_rotation": new_after_rotation.status_code,
        }

    result = asyncio.run(scenario())
    checks = {
        "missing_secret_401": result["missing"] == 401,
        "wrong_secret_401": result["wrong"] == 401,
        "right_secret_200": result["right"] == 200 and result["right_body"].get("acknowledged") is True,
        "non_ascii_401_not_500": result["non_ascii"] == 401,
        "old_secret_rejected_after_rotation": result["old_after_rotation"] == 401,
        "new_secret_accepted_after_rotation": result["new_after_rotation"] == 200,
    }
    failed = [name for name, ok in checks.items() if not ok]
    detail = (
        f"缺失/错误 secret→401，正确→200；非 ASCII→{result['non_ascii']}；"
        f"轮换后旧={result['old_after_rotation']}、新={result['new_after_rotation']}"
    )
    if failed:
        raise AssertionError(f"{failed} / {detail}")
    return detail, {"checks": checks, **result}


SSH_CHECKLIST = {
    "where": "生产宿主的 sshd（不是隔离容器）",
    "authorized_keys": 'restrict,port-forwarding,permitopen="127.0.0.1:6379" ssh-ed25519 AAAA... gpu-tunnel',
    "sshd_config": [
        "PermitOpen 127.0.0.1:6379",
        "AllowTcpForwarding local",
        "PermitTTY no",
        "X11Forwarding no",
        "PermitTunnel no",
    ],
    "verify": [
        "ssh -i gpu_key -p 22 -N -L 16379:127.0.0.1:6379 tunnel@host   # 应成功",
        "ssh -i gpu_key -p 22 -N -L 15432:127.0.0.1:5432 tunnel@host   # 应被 permitopen 拒绝",
        "ssh -i gpu_key -p 22 tunnel@host id                          # 应无 shell（restrict）",
        "ssh -i gpu_key -p 22 -D 1080 tunnel@host                      # 动态转发应被拒绝",
        "ssh -i gpu_key -p 22 -R 6379:127.0.0.1:6379 tunnel@host       # 反向转发应被拒绝",
    ],
    "reason_skipped": "隔离栈没有 sshd；D6 禁止引入新镜像，且宿主机 sshd 不属于隔离边界。",
}


def t9_ssh_tunnel(log: CaseLog) -> tuple[str, dict]:
    raise SkippedCaseError("T9 需要生产宿主的 sshd；隔离环境无法替代，见 checklist")


CASES = [
    ("A10-T1", "云身份不受 ACL 影响", t1_cloud_identity),
    ("A10-T2", "GPU 正常消费、心跳与回调", t2_gpu_consumption),
    ("A10-T3", "未确认消息隔离与重启恢复", t3_unacked_isolation),
    ("A10-T4", "读/写撤销状态被拒", t4_blacklist_denied),
    ("A10-T5", "向云端队列写任务被拒", t5_cloud_queue_denied),
    ("A10-T6", "清库/配置/管理命令被拒", t6_dangerous_denied),
    ("A10-T7", "其它键被拒", t7_other_keys_denied),
    ("A10-T8", "结果与遥控通道关闭", t8_result_and_pubsub_closed),
    ("A10-T9", "SSH 隧道与账户限制", t9_ssh_tunnel),
    ("A10-T10", "回调密钥边界与轮换", t10_callback_secret),
]

# Cases that need the callback receiver.
NEEDS_CALLBACK = {"A10-T2", "A10-T3", "A10-T8"}


def _today() -> str:
    return time.strftime("%Y-%m-%d")


def main() -> int:
    parser = argparse.ArgumentParser(description="A10 GPU permission-boundary drill (isolated stack)")
    parser.add_argument("--out", default=str(REPO_ROOT / "tmp" / "isolation" / f"a10-{_today()}.json"))
    parser.add_argument("--cases", default="", help="逗号分隔，如 A10-T4,A10-T6（默认全部）")
    parser.add_argument("--keep", action="store_true", help="结束后不 down -v，保留现场")
    args = parser.parse_args()

    selected = {item.strip() for item in args.cases.split(",") if item.strip()}

    render_acl()
    compose("--profile", "pg", "down", "-v", check=False)
    compose("up", "-d", "redis")
    cloud = wait_redis(redis_client("cloud"))
    cloud.execute_command("ACL", "LOG", "RESET")

    callback = CallbackServer()
    callback.start()

    results = []
    started_all = time.time()
    try:
        for case_id, title, fn in CASES:
            if selected and case_id not in selected:
                continue
            log = CaseLog()
            start = time.time()
            record = {"id": case_id, "title": title, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            try:
                if case_id in NEEDS_CALLBACK:
                    detail, evidence = fn(log, callback)
                else:
                    detail, evidence = fn(log)
                record.update(status="PASS", detail=detail, evidence=evidence)
                print(f"PASS {case_id} {title} — {detail}")
            except SkippedCaseError as exc:
                record.update(status="SKIP", detail=str(exc), evidence=SSH_CHECKLIST)
                print(f"SKIP {case_id} {title} — {exc}")
            except Exception as exc:
                record.update(
                    status="FAIL",
                    detail=f"{exc.__class__.__name__}: {exc}",
                    traceback=traceback.format_exc(),
                    evidence={},
                )
                print(f"FAIL {case_id} {title} — {exc.__class__.__name__}: {exc}")
            record["duration_seconds"] = round(time.time() - start, 3)
            record["commands"] = log.commands
            record["notes"] = log.notes
            results.append(record)
    finally:
        for proc in list(WORKERS):
            stop_worker(proc)
        callback.stop()
        if not args.keep:
            compose("--profile", "pg", "down", "-v", check=False)

    summary = {
        "task": "A10 / OPS-04 GPU server-side permission boundary",
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "environment": {
            "isolation_project": PROJECT,
            "redis": f"{REDIS_HOST}:{REDIS_PORT}",
            "postgres": f"{PG_HOST}:{PG_PORT}/{PG_DB}",
            "compose_file": "docker-compose.isolation.yml",
            "acl_template": "deploy/redis/users.acl.template",
            "acl_rendered": str(ACL_OUT.relative_to(REPO_ROOT)),
            "gpu_broker_settings": "gpu-worker/gpu_worker/broker_settings.py",
        },
        "duration_seconds": round(time.time() - started_all, 1),
        "cases": results,
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "failed": sum(1 for r in results if r["status"] == "FAIL"),
        "skipped": sum(1 for r in results if r["status"] == "SKIP"),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{summary['passed']} passed / {summary['failed']} failed / {summary['skipped']} skipped — {out}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
