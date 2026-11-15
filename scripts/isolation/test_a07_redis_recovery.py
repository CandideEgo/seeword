#!/usr/bin/env python3
"""A07 / OPS-03 —— Redis 恢复契约的隔离环境验证。

跑的是 [`docker-compose.isolation.yml`](../../docker-compose.isolation.yml) 里的
一次性 Redis（127.0.0.1:16379）与可选一次性 Postgres（15432），不碰开发栈
（6379/5432）与生产。用例矩阵与判定口径的唯一家是
[当前运行边界](README.md)。

用法（Windows，Docker 在 WSL 里）：

    PYTHONUTF8=1 backend/.venv/Scripts/python.exe scripts/isolation/test_a07_redis_recovery.py

脚本默认用 `wsl -d Ubuntu-24.04 -- docker` 驱动容器；Linux 上直接 `docker`。
可用 `A07_DOCKER` 覆盖（例如 `A07_DOCKER=docker`）。

每个用例独立记录命令与原始输出；最后写 JSON 到 `--out`（默认
`tmp/isolation/a07-<今天>.json`），有 FAIL 时退出码为 1。
演练结束默认 `down -v` 回收；`--keep` 保留现场。
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
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
COMPOSE_FILE = REPO_ROOT / "docker-compose.isolation.yml"

PROJECT = "seeword-isolation"
REDIS_CONTAINER = "seeword-isolation-redis"
PG_CONTAINER = "seeword-isolation-pg"
REDIS_HOST = "127.0.0.1"
REDIS_PORT = int(os.environ.get("A07_REDIS_PORT", "16379"))
REDIS_PASSWORD = os.environ.get("ISOLATION_REDIS_PASSWORD", "isolation-only")
GPU_PASSWORD = os.environ.get("ISOLATION_REDIS_GPU_PASSWORD", "isolation-gpu-only")
PG_HOST = "127.0.0.1"
PG_PORT = int(os.environ.get("A07_PG_PORT", "15432"))
PG_USER = "seeword"
PG_PASSWORD = os.environ.get("ISOLATION_PG_PASSWORD", "isolation-only")
PG_DB = "seeword_isolation"

# Compose prefixes named volumes with the project name.
REDIS_VOLUME = f"{PROJECT}_redisdata"
OLD_VOLUME = f"{PROJECT}_a07old"
OLD_CONTAINER = "seeword-isolation-a07old"
MIGRATE_CONTAINER = "seeword-isolation-a07migrate"
ACL_OUT = REPO_ROOT / "deploy" / "redis" / "users.acl.generated"

# App modules read settings at import time, so this must happen before the
# first `import app.*` (which only happens inside T6/T7).
os.environ["ENV"] = "development"
os.environ["JWT_SECRET"] = "a07-isolation-secret-at-least-32-characters"
os.environ["DATABASE_URL"] = f"postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
os.environ["REDIS_URL"] = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
os.environ["HEALTH_MONITOR_ENABLED"] = "false"


# ---------------------------------------------------------------------------
# Docker plumbing
# ---------------------------------------------------------------------------


def _docker_prefix() -> list[str]:
    override = os.environ.get("A07_DOCKER")
    if override:
        return shlex.split(override)
    if os.name == "nt":
        return ["wsl", "-d", os.environ.get("A07_WSL_DISTRO", "Ubuntu-24.04"), "--", "docker"]
    return ["docker"]


def _wsl_path(path: Path) -> str:
    """Turn C:\\Users\\... into /mnt/c/Users/... for the WSL docker CLI."""
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
    }


def render_acl() -> None:
    """Render the ACL file the isolation Redis starts from (added for A10).

    The file is git-ignored and carries both one-off passwords, so it is
    re-rendered on every run. `default` keeps the same password A07's client
    uses, which is why the recovery cases are unaffected by the ACL.
    """
    env = {**_compose_env(), "REDIS_PASSWORD": REDIS_PASSWORD, "REDIS_GPU_PASSWORD": GPU_PASSWORD}
    script = REPO_ROOT / "scripts" / "isolation" / "render_redis_acl.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--out", str(ACL_OUT)],
        capture_output=True,
        timeout=60,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"ACL render failed:\n{proc.stdout.decode('utf-8', 'replace')}\n{proc.stderr.decode('utf-8', 'replace')}"
        )


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
    """Records the commands a case ran and their raw output (evidence §7)."""

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
# Redis helpers
# ---------------------------------------------------------------------------


def redis_client():
    import redis

    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_timeout=10,
        socket_connect_timeout=5,
    )


def wait_redis(timeout: float = 60.0):
    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            client = redis_client()
            if client.ping():
                return client
        except Exception as exc:
            last = exc
        time.sleep(0.3)
    raise TimeoutError(f"Redis 在 {timeout}s 内没有就绪: {last}")


def wipe_redis(log: CaseLog) -> None:
    """Delete the container *and* the volume, then start an empty instance."""
    log.docker("rm", "-f", REDIS_CONTAINER, check=False)
    log.docker("volume", "rm", "-f", REDIS_VOLUME, check=False)
    log.compose("up", "-d", "redis")
    wait_redis()


def persistence_info(client) -> dict:
    raw = client.info("persistence")
    keys = (
        "aof_enabled",
        "aof_rewrite_in_progress",
        "aof_last_bgrewrite_status",
        "aof_last_write_status",
        "aof_current_size",
        "aof_base_size",
        "aof_pending_rewrite",
        "aof_last_cow_size",
        "rdb_last_bgsave_status",
    )
    return {key: raw.get(key) for key in keys}


def _parse_info(text: str) -> dict[str, str]:
    """Parse the plain-text `INFO` output returned by `redis-cli info`."""
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        parsed[key] = value
    return parsed


def wait_pg(timeout: float = 90.0) -> None:
    import socket

    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            with socket.create_connection((PG_HOST, PG_PORT), timeout=2):
                # The port is open; ask Redis-less psql? The port is enough for
                # the compose healthcheck to take over.
                time.sleep(0.5)
                return
        except OSError as exc:
            last = exc
            time.sleep(0.5)
    raise TimeoutError(f"Postgres 在 {timeout}s 内没有就绪: {last}")


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


def t1_restart(log: CaseLog) -> tuple[str, dict]:
    client = wait_redis()
    keys = [f"a07:t1:{i}" for i in range(100)]
    pipe = client.pipeline()
    for index, key in enumerate(keys):
        pipe.set(key, f"value-{index}", ex=600)
    pipe.execute()
    before = {key: client.ttl(key) for key in keys}
    if not all(0 < ttl <= 600 for ttl in before.values()):
        raise AssertionError(f"写入后 TTL 异常: {sorted(before.items())[:5]}")

    log.docker("restart", REDIS_CONTAINER)
    client = wait_redis()
    missing = [key for key in keys if not client.exists(key)]
    after = {key: client.ttl(key) for key in keys}
    reset = [key for key in keys if after[key] <= 0 or after[key] > before[key]]

    detail = f"100 键写入后 docker restart：缺失 {len(missing)} 个，TTL 被重置/过期 {len(reset)} 个"
    if missing or reset:
        raise AssertionError(f"missing={missing[:5]} reset={reset[:5]}")
    return detail, {
        "ttl_before_sample": {k: before[k] for k in keys[:5]},
        "ttl_after_sample": {k: after[k] for k in keys[:5]},
        "missing": missing,
        "ttl_reset": reset,
    }


def t2_recreate(log: CaseLog) -> tuple[str, dict]:
    client = wait_redis()
    keys = [f"a07:t1:{i}" for i in range(100)]
    before = {key: client.ttl(key) for key in keys}
    log.note("T2 复用 T1 的 100 个键，验证 down（不带 -v）后卷仍在")

    log.compose("down")
    log.compose("up", "-d", "redis")
    client = wait_redis()
    missing = [key for key in keys if not client.exists(key)]
    info = persistence_info(client)
    _rc, logs, logs_err = log.docker("logs", "--tail", "40", REDIS_CONTAINER)
    loaded_from_aof = "DB loaded from append only file" in (logs + logs_err)

    detail = (
        f"down/up 后缺失 {len(missing)} 个键；aof_enabled={info['aof_enabled']}；"
        f"启动日志显示从 AOF 加载={loaded_from_aof}"
    )
    if missing:
        raise AssertionError(f"重建容器后丢键: {missing[:10]}")
    if info.get("aof_enabled") != 1:
        raise AssertionError(f"AOF 未生效: {info}")
    if not loaded_from_aof:
        raise AssertionError("启动日志里没有『DB loaded from append only file』，无法证明走的是 AOF")
    return detail, {
        "missing": missing,
        "ttl_before_sample": {k: before[k] for k in keys[:5]},
        "persistence": info,
        "startup_log_loaded_from_aof": loaded_from_aof,
    }


def t3_kill(log: CaseLog) -> tuple[str, dict]:
    """Three SIGKILL rounds; the loss window is acknowledged-but-not-durable writes.

    ``everysec`` fsyncs once a second, so a single round can legitimately lose
    nothing (the kill lands just after an fsync). Three rounds give the contract
    a real chance to show its worst case; the reported value is the maximum.
    """
    client = wait_redis()
    rounds: list[dict] = []
    for round_index in range(3):
        wait_redis()
        written: list[float] = []
        stop = threading.Event()

        def writer(index: int = round_index, written: list[float] = written, stop: threading.Event = stop) -> None:
            own = redis_client()
            while not stop.is_set():
                ts = time.time()
                try:
                    own.set(f"a07:t3:{index}:{len(written)}", f"{ts:.6f}")
                except Exception:
                    return
                written.append(ts)
                time.sleep(0.01)

        thread = threading.Thread(target=writer, daemon=True)
        thread.start()
        time.sleep(2.5)
        log.docker("kill", REDIS_CONTAINER)
        stop.set()
        thread.join(timeout=10)

        log.docker("start", REDIS_CONTAINER)
        client = wait_redis()

        surviving: list[float] = []
        for key in client.scan_iter(f"a07:t3:{round_index}:*"):
            value = client.get(key)
            if value is not None:
                surviving.append(float(value))
        surviving.sort()
        if not written:
            raise AssertionError(f"第 {round_index + 1} 轮写入线程没有写出任何键，用例无效")
        if not surviving:
            raise AssertionError(f"第 {round_index + 1} 轮 SIGKILL 后一个键都没恢复，AOF 没有生效")

        # Only writes Redis *acknowledged* before dying count as lost; the
        # writer stops on the first failed SET (connection gone with the kill).
        lost_seconds = max(0.0, written[-1] - surviving[-1])
        gaps = [b - a for a, b in pairwise(surviving)]
        rounds.append(
            {
                "round": round_index + 1,
                "written": len(written),
                "surviving": len(surviving),
                "lost_seconds": round(lost_seconds, 3),
                "max_internal_gap_seconds": round(max(gaps) if gaps else 0.0, 3),
            }
        )

    max_loss = max(item["lost_seconds"] for item in rounds)

    # After a SIGKILL the AOF tail may be torn; Redis truncates it on restart
    # (aof-load-truncated yes). Checking *after* the restart is the contract.
    _rc, listing, _err = log.docker("exec", REDIS_CONTAINER, "sh", "-c", "ls -1 /data/appendonlydir")
    manifest = "/data/appendonlydir/appendonly.aof.manifest"
    check_rc, check_out, check_err = log.docker("exec", REDIS_CONTAINER, "redis-check-aof", manifest, check=False)
    aof_ok = check_rc == 0

    detail = (
        f"3 轮 SIGKILL：最大丢失窗口 {max_loss:.3f}s（判定上限 2.0s，进程级）；各轮丢失 "
        f"{[item['lost_seconds'] for item in rounds]}；redis-check-aof rc={check_rc}"
    )
    if max_loss > 2.0:
        raise AssertionError(f"丢失窗口 {max_loss:.3f}s 超过 2s 契约")
    if not aof_ok:
        raise AssertionError(f"redis-check-aof 未通过: {check_out}\n{check_err}")
    return detail, {
        "rounds": rounds,
        "max_lost_seconds_by_sigkill": max_loss,
        # SIGKILL 只杀进程：Redis 在每轮事件循环里已经把 AOF buffer write(2)
        # 进文件，掉的是 fsync 而不是数据，所以实测通常为 0。宿主内核/掉电
        # 才会暴露 everysec 的窗口——本演练不重启宿主，只能按配置语义给出
        # 上界（≤1s + 调度抖动，契约允许 2s）。见 evidence README 的边界说明。
        "host_crash_bound_seconds": 2.0,
        "host_crash_measured": False,
        "aof_files": listing.strip().splitlines(),
        "redis_check_aof_rc": check_rc,
        "redis_check_aof_output": (check_out + check_err).strip()[-2000:],
    }


def t4_config(log: CaseLog) -> tuple[str, dict]:
    client = wait_redis()
    appendonly = client.config_get("appendonly")
    appendfsync = client.config_get("appendfsync")
    save = client.config_get("save")
    maxmemory_policy = client.config_get("maxmemory-policy")
    info = persistence_info(client)
    detail = (
        f"appendonly={appendonly.get('appendonly')} appendfsync={appendfsync.get('appendfsync')} "
        f"save={save.get('save')!r} maxmemory-policy={maxmemory_policy.get('maxmemory-policy')} "
        f"aof_enabled={info['aof_enabled']} aof_last_write_status={info['aof_last_write_status']}"
    )
    if appendonly.get("appendonly") != "yes":
        raise AssertionError(f"appendonly 未开启: {appendonly}")
    if appendfsync.get("appendfsync") != "everysec":
        raise AssertionError(f"appendfsync 不是 everysec: {appendfsync}")
    if save.get("save") != "":
        raise AssertionError(f"RDB save 未关闭: {save}")
    if maxmemory_policy.get("maxmemory-policy") != "noeviction":
        raise AssertionError(f"淘汰策略不是 noeviction: {maxmemory_policy}")
    if info.get("aof_enabled") != 1 or info.get("aof_last_write_status") != "ok":
        raise AssertionError(f"INFO persistence 不符: {info}")
    return detail, {
        "config": {
            "appendonly": appendonly,
            "appendfsync": appendfsync,
            "save": save,
            "maxmemory-policy": maxmemory_policy,
        },
        "persistence": info,
    }


def t5_volume_loss(log: CaseLog) -> tuple[str, dict]:
    client = wait_redis()
    seeded = {
        "celery": lambda: client.rpush("celery", '{"task":"a07"}'),
        "transcription_gpu": lambda: client.rpush("transcription_gpu", '{"task":"a07"}'),
        "unacked": lambda: client.rpush("unacked", "message"),
        "unacked_index": lambda: client.zadd("unacked_index", {"message": time.time()}),
        "_kombu.binding.celery": lambda: client.sadd("_kombu.binding.celery", "a07"),
        "token_blacklist:drill": lambda: client.set("token_blacklist:drill", "1", ex=600),
        "sms:cooldown:13800000000": lambda: client.set("sms:cooldown:13800000000", "1", ex=60),
        "video:callback:drill": lambda: client.set("video:callback:drill", "1", ex=600),
        "ai_cache:drill": lambda: client.set("ai_cache:drill", "x", ex=60),
        "browse:home:drill": lambda: client.set("browse:home:drill", "x", ex=60),
        "worker:gpu:heartbeat": lambda: client.set("worker:gpu:heartbeat", str(time.time()), ex=90),
        "pipeline:failures:recent": lambda: client.lpush("pipeline:failures:recent", "{}"),
        "celery-task-meta-drill": lambda: client.set("celery-task-meta-drill", "{}", ex=60),
    }
    for seed in seeded.values():
        seed()
    before_dbsize = client.dbsize()

    wipe_redis(log)
    client = wait_redis()
    after_dbsize = client.dbsize()

    checks = {
        "celery": client.llen("celery"),
        "transcription_gpu": client.llen("transcription_gpu"),
        "unacked": client.llen("unacked"),
        "unacked_index": client.zcard("unacked_index"),
        "_kombu.binding.celery": client.scard("_kombu.binding.celery"),
        "token_blacklist:*": len(list(client.scan_iter("token_blacklist:*"))),
        "sms:cooldown:*": len(list(client.scan_iter("sms:cooldown:*"))),
        "video:callback:*": len(list(client.scan_iter("video:callback:*"))),
        "ai_cache:*": len(list(client.scan_iter("ai_cache:*"))),
        "browse:*": len(list(client.scan_iter("browse:*"))),
        "worker:gpu:heartbeat": client.exists("worker:gpu:heartbeat"),
        "pipeline:failures:recent": client.llen("pipeline:failures:recent"),
        "celery-task-meta-*": len(list(client.scan_iter("celery-task-meta-*"))),
    }
    leaked = {name: count for name, count in checks.items() if count}
    loss_table = {
        "celery / transcription_gpu / unacked": {
            "lost": True,
            "consequence": "队列与在途任务不执行",
            "compensation": "管线走 pipeline_dispatches outbox + 看门狗；订单走对账任务（A07-T6 实测补发）",
        },
        "token_blacklist:*": {
            "lost": True,
            "consequence": "已登出但未过期的 token 在窗口内重新可用",
            "compensation": "既有 fail-open 契约；封禁与改密仍按 DB 判定（A07-T7 实测）",
        },
        "video:callback:* 去重锁": {
            "lost": True,
            "consequence": "同一回调可能被重复处理",
            "compensation": "回调处理器状态守卫 + A05 去重（幂等）",
        },
        "sms:cooldown:* / 会话计数": {
            "lost": True,
            "consequence": "短时间内限流变宽",
            "compensation": "可接受；记录为已知窗口",
        },
        "ai_cache:* / browse:*": {
            "lost": True,
            "consequence": "缓存未命中，回源重算",
            "compensation": "无正确性影响",
        },
        "worker:gpu:heartbeat": {
            "lost": True,
            "consequence": "GPU 心跳缺失，健康监控可能误报",
            "compensation": "GPU 下一次心跳（30s 内）自动恢复；告警有节流",
        },
        "pipeline:failures:recent": {
            "lost": True,
            "consequence": "窗口内失败率统计归零",
            "compensation": "仅是速率信号；告警通道本身不依赖它",
        },
    }
    detail = (
        f"空卷重启前 dbsize={before_dbsize}，重启后 dbsize={after_dbsize}；"
        f"逐类核对 {'全部丢失' if not leaked else '仍有残留: ' + str(leaked)}"
    )
    if after_dbsize != 0 or leaked:
        raise AssertionError(f"空卷后仍有数据: dbsize={after_dbsize} leaked={leaked}")
    return detail, {
        "dbsize_before": before_dbsize,
        "dbsize_after": after_dbsize,
        "checks_after": checks,
        "loss_table": loss_table,
    }


def _prepare_app() -> None:
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))


def t6_db_compensation(log: CaseLog) -> tuple[str, dict]:
    log.compose("--profile", "pg", "up", "-d", "pg")
    wait_pg()

    _prepare_app()
    import app.models  # noqa: F401 - fill Base.metadata
    from app.core.config import get_settings
    from app.core.database import Base, get_async_session_maker, get_engine
    from app.models.pipeline_dispatch import DISPATCH_STATUS_DISPATCHED, PipelineDispatch
    from app.models.video import Video, VideoSource, VideoStatus
    from app.services.pipeline_dispatch import dispatch_pending, enqueue

    settings = get_settings()
    queue = settings.transcription_gpu_queue_name
    task_name = "app.tasks.video_processing.transcribe_video_gpu"
    video_id = str(uuid.uuid4())

    async def _body() -> dict:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        session_maker = get_async_session_maker()
        async with session_maker() as db:
            db.add(
                Video(
                    id=video_id,
                    title="A07-T6 broker loss drill",
                    source_url="https://example.com/a07-t6.mp4",
                    video_source=VideoSource.imported,
                    status=VideoStatus.processing,
                )
            )
            await db.flush()
            dispatch_id = await enqueue(
                db,
                video_id=video_id,
                task_name=task_name,
                args=[video_id, "https://example.com/a07-t6.mp4", "youtube"],
                queue=queue,
            )
            await db.commit()
            log.note(f"在 PG 中留下 pending 意图 {dispatch_id}（视频 {video_id}），随后清空 Redis")

        # Broker loss: container + volume gone, then a fresh empty instance.
        wipe_redis(log)

        client = wait_redis()
        queue_before = client.llen(queue)
        async with session_maker() as db:
            sweep = await dispatch_pending(db)
            row = await db.get(PipelineDispatch, dispatch_id)
            status = row.status if row is not None else None
            attempts = row.attempts if row is not None else None
            last_error = row.last_error if row is not None else None
        queue_after = client.llen(queue)
        default_queue = client.llen("celery")
        message = client.lindex(queue, 0)

        async with session_maker() as db:
            second = await dispatch_pending(db)
            row = await db.get(PipelineDispatch, dispatch_id)
            status_after_second = row.status if row is not None else None
        queue_after_second = client.llen(queue)

        return {
            "dispatch_id": dispatch_id,
            "video_id": video_id,
            "queue": queue,
            "redis_queue_before": queue_before,
            "sweep_1": sweep.__dict__,
            "status_after_sweep": status,
            "attempts": attempts,
            "last_error": last_error,
            "redis_queue_after": queue_after,
            "default_queue_after": default_queue,
            "message_contains_task": bool(message and task_name in message),
            "sweep_2": second.__dict__,
            "status_after_second": status_after_second,
            "redis_queue_after_second": queue_after_second,
        }

    async def scenario() -> dict:
        # asyncpg connections are loop-bound; dispose inside the same loop so
        # the next case's fresh asyncio.run does not inherit a dead pool.
        try:
            return await _body()
        finally:
            await get_engine().dispose()

    result = asyncio.run(scenario())
    detail = (
        f"清空 Redis 后 beat 扫描：第一次 sent={result['sweep_1']['sent']}、队列 {queue} "
        f"llen={result['redis_queue_after']}；第二次 sent={result['sweep_2']['sent']}、llen="
        f"{result['redis_queue_after_second']}（不重复补发）"
    )
    checks = {
        "queue_was_empty_before_sweep": result["redis_queue_before"] == 0,
        "first_sweep_sent_one": result["sweep_1"]["sent"] == 1,
        "row_dispatched": result["status_after_sweep"] == DISPATCH_STATUS_DISPATCHED,
        "one_message_on_gpu_queue": result["redis_queue_after"] == 1,
        "no_message_on_default_queue": result["default_queue_after"] == 0,
        "message_is_the_task": result["message_contains_task"],
        "second_sweep_sent_none": result["sweep_2"]["sent"] == 0,
        "queue_still_one": result["redis_queue_after_second"] == 1,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise AssertionError(f"DB 补偿不符合契约: {failed} {result}")
    return detail, {"checks": checks, **result}


def t7_revocation(log: CaseLog) -> tuple[str, dict]:
    log.compose("--profile", "pg", "up", "-d", "pg")
    wait_pg()
    _prepare_app()
    import app.models  # noqa: F401
    from app.api.dependencies import resolve_token_user
    from app.core.database import Base, get_async_session_maker, get_engine
    from app.core.security import create_token, decode_token
    from app.core.token_blacklist import blacklist_token, claim_token_once, is_token_blacklisted
    from app.models.user import User

    async def _body() -> dict:
        engine = get_engine()
        async with engine.begin() as conn:
            # T7 can run alone (`--cases A07-T7`); create_all is idempotent.
            await conn.run_sync(Base.metadata.create_all)
        session_maker = get_async_session_maker()
        async with session_maker() as db:
            user = User(phone=f"139{uuid.uuid4().int % 100000000:08d}", name="A07-T7", is_banned=False)
            db.add(user)
            await db.commit()
            await db.refresh(user)
            user_id = user.id

            token = create_token(user_id)
            payload = decode_token(token) or {}
            jti = payload.get("jti")
            if not jti:
                raise AssertionError("token 没有 jti，用例无法进行")

            await blacklist_token(jti, 600)
            blacklisted_before = await is_token_blacklisted(jti)
            user_before = await resolve_token_user(token, db)

            # Nuke the broker state (container + volume) — the A07-T5 loss.
            # Close the app's async singleton first: its pooled connections
            # would otherwise raise from the parser thread when the server dies.
            from app.core.redis import close_redis

            await close_redis()
            wipe_redis(log)
            client = wait_redis()
            log.note("已清空 Redis（含 token_blacklist:*）")

            blacklisted_after = await is_token_blacklisted(jti)
            user_after = await resolve_token_user(token, db)

            # The other guards live in the DB and must still hold. Run them
            # *before* claim_token_once, which would re-write the blacklist key
            # and make the token fail for the wrong reason.
            user_row = await db.get(User, user_id)
            assert user_row is not None
            user_row.is_banned = True
            await db.commit()
            user_banned = await resolve_token_user(token, db)
            user_row.is_banned = False
            from datetime import timedelta

            user_row.password_changed_at = datetime.now(UTC) + timedelta(seconds=10)
            await db.commit()
            user_password_changed = await resolve_token_user(token, db)
            user_row.password_changed_at = datetime.now(UTC) - timedelta(days=1)
            await db.commit()

            # Last: the single-use claim also fails open after the loss.
            claim_after = await claim_token_once(jti, 600)

            return {
                "jti": jti,
                "blacklisted_before_loss": blacklisted_before,
                "user_before_loss": user_before is not None,
                "redis_dbsize_after_loss": client.dbsize(),
                "blacklisted_after_loss": blacklisted_after,
                "user_after_loss": user_after is not None,
                "claim_token_once_after_loss": claim_after,
                "user_when_banned": user_banned is not None,
                "user_when_password_changed": user_password_changed is not None,
            }

    async def scenario() -> dict:
        try:
            return await _body()
        finally:
            await get_engine().dispose()

    result = asyncio.run(scenario())
    detail = (
        f"清空 Redis 前黑名单命中={result['blacklisted_before_loss']}（请求被拒）；"
        f"清空后黑名单命中={result['blacklisted_after_loss']}，同一 token 重新可用="
        f"{result['user_after_loss']}（fail-open）；封禁与改密仍拒绝={not result['user_when_banned'] and not result['user_when_password_changed']}"
    )
    checks = {
        "blacklisted_before": result["blacklisted_before_loss"] is True,
        "revoked_request_rejected_before": result["user_before_loss"] is False,
        "blacklist_gone_after": result["blacklisted_after_loss"] is False,
        "revoked_token_usable_after": result["user_after_loss"] is True,
        "claim_once_fails_open": result["claim_token_once_after_loss"] is True,
        "banned_still_rejected": result["user_when_banned"] is False,
        "password_change_still_rejected": result["user_when_password_changed"] is False,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise AssertionError(f"撤销/护栏契约不符: {failed} {result}")
    return detail, {"checks": checks, **result}


def t8_volume_migration(log: CaseLog) -> tuple[str, dict]:
    # Simulate the current production volume: RDB only, no AOF.
    log.docker("rm", "-f", OLD_CONTAINER, check=False)
    log.docker("volume", "rm", "-f", OLD_VOLUME, check=False)
    log.docker("rm", "-f", REDIS_CONTAINER, check=False)
    log.docker("volume", "rm", "-f", REDIS_VOLUME, check=False)

    log.docker(
        "run",
        "-d",
        "--name",
        OLD_CONTAINER,
        "-v",
        f"{OLD_VOLUME}:/data",
        "redis:7-alpine",
        "redis-server",
        "--appendonly",
        "no",
        "--save",
        "60",
        "1",
    )
    deadline = time.time() + 60
    while time.time() < deadline:
        rc, out, _err = log.docker("exec", OLD_CONTAINER, "redis-cli", "ping", check=False)
        if rc == 0 and "PONG" in out:
            break
        time.sleep(0.3)
    else:  # pragma: no cover - environment failure
        raise TimeoutError("旧配置 Redis 没有就绪")

    log.docker(
        "exec",
        OLD_CONTAINER,
        "redis-cli",
        "mset",
        "a07:t8:keep",
        "survives",
        "a07:t8:ttl",
        "survives-with-ttl",
    )
    log.docker("exec", OLD_CONTAINER, "redis-cli", "expire", "a07:t8:keep", "900")
    log.docker("exec", OLD_CONTAINER, "redis-cli", "expire", "a07:t8:ttl", "600")
    log.docker("exec", OLD_CONTAINER, "redis-cli", "rpush", "a07:t8:list", "a", "b", "c")
    _rc, ttl_out, _ = log.docker("exec", OLD_CONTAINER, "redis-cli", "ttl", "a07:t8:ttl")
    old_ttl = int(ttl_out.strip())
    log.docker("exec", OLD_CONTAINER, "redis-cli", "save")
    log.docker("stop", OLD_CONTAINER)
    log.docker("rm", "-f", OLD_CONTAINER, check=False)

    # Copy the old volume into the new named volume.
    log.docker("volume", "create", REDIS_VOLUME)
    log.docker(
        "run",
        "--rm",
        "-v",
        f"{OLD_VOLUME}:/from",
        "-v",
        f"{REDIS_VOLUME}:/to",
        "redis:7-alpine",
        "sh",
        "-c",
        "cp -a /from/. /to/",
    )

    # Measured in the first drill run: starting with the AOF config directly
    # does NOT load the copied RDB — Redis 7 with `appendonly yes` and no AOF
    # manifest creates an empty AOF base file and serves an empty dataset.
    # The working migration is the documented upgrade path: load the RDB with
    # AOF off, turn AOF on at runtime (rewrite from the live dataset), then
    # switch to the AOF config.
    log.docker("rm", "-f", MIGRATE_CONTAINER, check=False)
    log.docker(
        "run",
        "-d",
        "--name",
        MIGRATE_CONTAINER,
        "-v",
        f"{REDIS_VOLUME}:/data",
        "redis:7-alpine",
        "redis-server",
        "--appendonly",
        "no",
        "--save",
        "",
    )
    deadline = time.time() + 60
    while time.time() < deadline:
        rc, out, _err = log.docker("exec", MIGRATE_CONTAINER, "redis-cli", "ping", check=False)
        if rc == 0 and "PONG" in out:
            break
        time.sleep(0.3)
    else:  # pragma: no cover - environment failure
        raise TimeoutError("迁移用 Redis（appendonly no）没有就绪")

    _rc, loaded_before, _ = log.docker("exec", MIGRATE_CONTAINER, "redis-cli", "--raw", "get", "a07:t8:keep")
    log.docker("exec", MIGRATE_CONTAINER, "redis-cli", "config", "set", "appendonly", "yes")
    aof_info: dict[str, str] = {}
    deadline = time.time() + 60
    while time.time() < deadline:
        _rc, info_out, _ = log.docker("exec", MIGRATE_CONTAINER, "redis-cli", "info", "persistence", check=False)
        aof_info = _parse_info(info_out)
        try:
            base_size = int(aof_info.get("aof_base_size", "0"))
            rewrite_running = int(aof_info.get("aof_rewrite_in_progress", "0"))
        except ValueError:
            base_size, rewrite_running = 0, 1
        if (
            aof_info.get("aof_enabled") == "1"
            and rewrite_running == 0
            and aof_info.get("aof_last_bgrewrite_status") == "ok"
            and base_size > 0
        ):
            break
        time.sleep(0.3)
    else:  # pragma: no cover - environment failure
        raise TimeoutError(f"AOF 重写没有完成: {aof_info}")

    log.docker("stop", MIGRATE_CONTAINER)
    log.docker("rm", "-f", MIGRATE_CONTAINER, check=False)

    log.compose("up", "-d", "redis")
    client = wait_redis()

    keep = client.get("a07:t8:keep")
    ttl_value = client.get("a07:t8:ttl")
    new_ttl = client.ttl("a07:t8:ttl")
    list_values = client.lrange("a07:t8:list", 0, -1)
    info = persistence_info(client)
    _rc, logs, logs_err = log.docker("logs", "--tail", "60", REDIS_CONTAINER)
    log_text = logs + logs_err
    loaded_from_aof = "DB loaded from append only file" in log_text

    log.docker("rm", "-f", OLD_CONTAINER, check=False)
    log.docker("rm", "-f", MIGRATE_CONTAINER, check=False)
    log.docker("volume", "rm", "-f", OLD_VOLUME, check=False)

    detail = (
        f"旧卷（RDB，无 AOF）拷入命名卷 → appendonly no 加载（keep={loaded_before.strip()!r}）"
        f" → CONFIG SET appendonly yes 生成 AOF → 切到 AOF 配置启动：keep={keep!r} "
        f"ttl={ttl_value!r}（旧 TTL={old_ttl}s → 新 {new_ttl}s）；list={list_values}；"
        f"从 AOF 加载={loaded_from_aof}"
    )
    checks = {
        "rdb_loaded_before_switch": loaded_before.strip() == "survives",
        "keep_survived": keep == "survives",
        "ttl_key_survived": ttl_value == "survives-with-ttl",
        "ttl_preserved": 0 < new_ttl <= old_ttl,
        "list_survived": list_values == ["a", "b", "c"],
        "aof_enabled_after_migration": info.get("aof_enabled") == 1,
        "startup_loaded_from_aof": loaded_from_aof,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise AssertionError(f"卷迁移失败: {failed} detail={detail} log={log_text[-2000:]}")
    return detail, {
        "checks": checks,
        "old_ttl": old_ttl,
        "new_ttl": new_ttl,
        "persistence": info,
        "aof_rewrite_info": aof_info,
        "startup_log_excerpt": log_text[-2000:],
    }


CASES = [
    ("A07-T1", "容器重启后键与 TTL 不丢", t1_restart),
    ("A07-T2", "容器替换（同卷）后恢复，且从 AOF 加载", t2_recreate),
    ("A07-T3", "SIGKILL 异常停机的损失窗口 ≤ 2s", t3_kill),
    ("A07-T4", "AOF 启动参数与运行时状态", t4_config),
    ("A07-T5", "卷丢失（最坏情况）的丢失面与后果表", t5_volume_loss),
    ("A07-T6", "broker 全丢后按 DB outbox 补偿且不重复", t6_db_compensation),
    ("A07-T7", "撤销状态丢失的 fail-open 与其余护栏", t7_revocation),
    ("A07-T8", "旧卷（RDB）迁移到新命名卷 + AOF", t8_volume_migration),
]


def _today() -> str:
    return datetime.now(UTC).astimezone().strftime("%Y-%m-%d")


def main() -> int:
    parser = argparse.ArgumentParser(description="A07 Redis recovery drill (isolated stack)")
    parser.add_argument("--out", default=str(REPO_ROOT / "tmp" / "isolation" / f"a07-{_today()}.json"))
    parser.add_argument("--cases", default="", help="逗号分隔，如 A07-T1,A07-T3（默认全部）")
    parser.add_argument("--keep", action="store_true", help="结束后不 down -v，保留现场")
    args = parser.parse_args()

    selected = {item.strip() for item in args.cases.split(",") if item.strip()}

    # Rebuild from nothing so a previous failed run cannot poison T1.
    # `--profile pg` matters: a plain `down` leaves profiled services running.
    render_acl()
    compose("--profile", "pg", "down", "-v", check=False)
    compose("up", "-d", "redis")
    wait_redis()

    results = []
    started_all = time.time()
    for case_id, title, fn in CASES:
        if selected and case_id not in selected:
            continue
        log = CaseLog()
        start = time.time()
        record = {"id": case_id, "title": title, "started_at": datetime.now(UTC).isoformat()}
        try:
            detail, evidence = fn(log)
            record.update(status="PASS", detail=detail, evidence=evidence)
            print(f"PASS {case_id} {title} — {detail}")
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

    if not args.keep:
        compose("--profile", "pg", "down", "-v", check=False)

    summary = {
        "task": "A07 / OPS-03 Redis recovery contract",
        "date": datetime.now(UTC).isoformat(),
        "environment": {
            "isolation_project": PROJECT,
            "redis": f"{REDIS_HOST}:{REDIS_PORT}",
            "postgres": f"{PG_HOST}:{PG_PORT}/{PG_DB}"
            if any(r["id"].startswith(("A07-T6", "A07-T7")) for r in results)
            else None,
            "compose_file": "docker-compose.isolation.yml",
            "redis_conf": "deploy/redis/redis.conf",
            "allowed_loss_seconds": 2.0,
        },
        "duration_seconds": round(time.time() - started_all, 1),
        "cases": results,
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "failed": sum(1 for r in results if r["status"] == "FAIL"),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{summary['passed']} passed / {summary['failed']} failed — {out}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
