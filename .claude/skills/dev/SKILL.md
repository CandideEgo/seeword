---
name: dev
description: Start the Speaking dev stack on Windows — backend :8000, cloud Celery worker, GPU transcription worker, Next.js frontend :3000, and the Docker Postgres/Redis containers. Use on /dev, or when the user asks to start the dev services or says 重启服务 / "restart services".
---

# Speaking Dev — start & restart

Brings up four native Windows services plus the Docker infra:

| Service | What it is |
|---|---|
| Backend | FastAPI via uvicorn on :8000 |
| Cloud Celery | worker (pool=solo) on the `celery` queue — video head/tail, localize, watchdog |
| GPU Worker | Celery worker (pool=solo, concurrency=1) on the `transcription_gpu` queue — WhisperX on the local GPU, with a Redis heartbeat |
| Frontend | Next.js dev server on :3000 |
| Infra | PostgreSQL + Redis as Docker containers (`speaking-db-1`, `speaking-redis-1`) |

**Restart is this same run.** 重启服务 / "restart services" is not a separate procedure: step 1 kills
every service already on 8000/3000/3001 and step 7 clears the `.next` cache, so just run the steps
below as written. Docker containers stay up either way — only `/dev-stop --infra` takes those down.

## Steps

All paths below are resolved from the repository root at runtime with
`$(git rev-parse --show-toplevel)` (shell state does not persist between tool calls, so every block
inlines it) — never hardcode a machine path; this checkout moved machines once already.

1. **Free the app ports.** Read and run
   `$(git rev-parse --show-toplevel)/.claude/reference/kill-ports.md` — no exceptions, no skipping.
   Done when its last line printed `all app ports free`.

2. **Check prerequisites** — is Docker Desktop running?
   ```bash
   docker info > /dev/null 2>&1 && echo "Docker OK" || echo "Docker not running"
   ```

3. **Start infra** (DB + Redis):
   ```bash
   cd "$(git rev-parse --show-toplevel)"
   docker start speaking-db-1 speaking-redis-1 2>/dev/null || docker compose -f docker-compose.dev.yml up -d
   ```

4. **Run migrations** (idempotent):
   ```bash
   cd "$(git rev-parse --show-toplevel)/backend" && PYTHONUTF8=1 .venv/Scripts/python.exe -m alembic upgrade head
   ```

5. **Start the backend** (uvicorn on :8000) — background:
   ```bash
   cd "$(git rev-parse --show-toplevel)/backend" && PYTHONUTF8=1 .venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --timeout-keep-alive 120
   ```
   `--timeout-keep-alive 120` 不是可选项：uvicorn 默认 5s，Next dev 代理复用的空闲连接会被它在同一时刻关掉 → ECONNRESET → 代理回 500。本机全量 e2e 里表现为随机页面接口 500（不是应用 bug，换短超时后必现）。

6. **Start the cloud Celery worker** — background:
   ```bash
   cd "$(git rev-parse --show-toplevel)/backend" && PYTHONUTF8=1 .venv/Scripts/python.exe -m celery -A app.tasks.celery_app worker --pool=solo -Q celery --loglevel=info
   ```

7. **Start the GPU worker** — background, **only on the machine that has a GPU worker venv + `.env.gpu-worker` + an NVIDIA GPU**:
   ```bash
   cd "$(git rev-parse --show-toplevel)/gpu-worker" && PYTHONUTF8=1 .venv/Scripts/python.exe scripts/start_gpu_worker.py
   ```
   Skip this step on a checkout without `gpu-worker/.venv/Scripts/python.exe` or `gpu-worker/.env.gpu-worker` (the laptop has neither) — and say so in the final report instead of silently omitting it.
   This reads `gpu-worker/.env.gpu-worker` (cloud Redis via the 16379 SSH tunnel + cloud callback URL).
   For an all-local dev run (local Redis + local backend callback) override the two env vars before
   starting: `REDIS_URL=redis://localhost:6379/0` and
   `TRANSCRIPTION_CALLBACK_URL=http://localhost:8000/api/v1/internal/transcription/callback`.

8. **Start the frontend** — background:
   ```bash
   rm -rf "$(git rev-parse --show-toplevel)/frontend/.next"
   cd "$(git rev-parse --show-toplevel)/frontend" && npm run dev
   ```

9. **Verify.** Wait ~8 seconds, then:
   ```bash
   curl -s http://localhost:8000/health | head -1
   curl -s http://localhost:3000 | head -1
   ```
   Backend must return `{"status":"ok"}` and the frontend must return HTML. Then read the two worker
   startup logs: the cloud worker registered the `celery` queue only, the GPU worker registered
   `transcription_gpu` and printed `[heartbeat] started`. The cloud registers its five pipeline
   tasks; the standalone GPU worker registers only the remote transcription task name.
   A service that is up but failed one of these checks is **not** started — report it.

10. **Report status**:
    ```
    === Speaking — all services started ===
      Backend    → http://localhost:8000/docs
      Frontend   → http://localhost:3000
      Cloud Cel  → pool=solo, queue: celery (head/tail/localize/watchdog)
      GPU Worker → queue: transcription_gpu, heartbeat → admin shows 在线
    ```

## Notes

- **`PYTHONUTF8=1` on every Python service.** Windows Python defaults to the OS locale codec (GBK on
  a Chinese Windows) for `open()` calls without an explicit encoding, while the app assumes UTF-8
  (it runs on Linux in prod). Without it the backend crashes at startup: slowapi's `Limiter` reads
  `.env` through starlette `Config` with the locale codec and hits `UnicodeDecodeError: 'gbk' codec`
  on the UTF-8 em-dash in a comment and the Chinese `ALIYUN_SMS_SIGN_NAME` value. Celery and the GPU
  worker do not import `app.core.limiter` and so do not crash, but all three set it for consistency.
- **The queue split is load-bearing.** The cloud worker takes `-Q celery` only; the GPU worker takes
  `transcription_gpu` only. This mirrors production (`docker-compose.prod.yml`: cloud worker `-Q
  celery`, remote GPU worker on `transcription_gpu`). Locally both run on one machine but never
  contend for a task. Do not widen the cloud worker to both queues — it has no GPU and would steal
  transcription tasks, falling back to slow CPU Whisper.
- **The GPU worker is what makes transcription happen.** It runs WhisperX on the local GPU (RTX
  3060 Ti) and writes a Redis heartbeat every 60s (key `worker:gpu:heartbeat`, TTL 90s) so the admin
  VideoManager page shows 在线. With it down, transcription tasks sit in `transcription_gpu` forever
  and that page shows 离线. Since the 2026-10 split it is a standalone component (`gpu-worker/`) with
  its own venv (`gpu-worker/.venv/Scripts/python.exe`; verify it exists on the GPU machine) and its
  own `app`-free package — do not start it from `backend/` anymore.
- `--pool=solo` is required for Celery on Windows; prefork is unsupported.
- Everything above runs natively on Windows. Only Postgres + Redis are in Docker.

## Stop signals

Stop and ask the user instead of pressing on:

- A service fails for a reason that is **not** one of the known Windows traps (locale codec, port
  conflict, orphaned `--reload` reloader). Report the real error rather than restarting until it
  merely looks fine — a green `/health` over a failed worker is the failure this skill exists to
  surface.
- You are about to touch production (the deploy scripts, the remote host). That is not a local-dev
  action and needs explicit authorization.
- Irreversible steps: dropping tables, deleting media, deleting the `_raw` masters (with no OSS
  configured, `_raw` is the only copy), or changing file permissions.
