# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

后端（`backend/`）专属的**本机操作约束**与门禁口径。架构叙述在根 [`CLAUDE.md`](../CLAUDE.md)，本文件不重复——就近分层，只管「在这台机器上怎么把后端跑对、哪些门不能糊弄」。

## 本机环境（中文 Windows）

| 约束 | 原因 |
|---|---|
| 每个 Python 进程都要带 `PYTHONUTF8=1`（backend / celery / GPU worker） | Windows 上没显式传 `encoding` 的 `open()` 走 OS locale（中文 Windows 是 GBK），而本应用假设 UTF-8（生产跑 Linux）。缺了它后端**启动即崩**：slowapi 的 `Limiter` 会经 starlette 的 `Config` 按 locale 读 `.env`，撞上文件里的 UTF-8 em-dash 与中文 `ALIYUN_SMS_SIGN_NAME`，报 `UnicodeDecodeError: 'gbk' codec`。 |
| 显式用 `backend/.venv/Scripts/python.exe` | 云端后端/测试的依赖都装在这里；系统 Python 跑不起来不代表代码有问题。**GPU worker 已不共用**：它用自己的 `gpu-worker\.venv`（当前是 `backend\.venv` 的克隆，torch 2.8.0+cu128 / whisperx 3.8.6 可用），`PYTHONUTF8=1` 对 gpu-worker 同样适用。 |
| 解释器不可用时如实报告，不要换一个猜 | 跑不了的检查就写「未执行」，不写成通过。 |

## 测试与检查门

以下每条「约束」都有它存在的理由，别当风格偏好绕过。

| 约束 | 原因 |
|---|---|
| pytest 配置**只**写在 `backend/pytest.ini` | `pytest.ini` 优先于 `pyproject.toml`。两边同时存在时 pytest 只警告一句「ignoring pytest config in pyproject.toml」就**静默丢掉** `addopts`——`--timeout=60` 一丢，一个卡在断连 TCP 上的测试会烧掉整个 CI job 预算。真要挪回 `pyproject.toml`，就在同一次改动里删掉 `pytest.ini`。 |
| marker 只有 `unit`（快、无外部依赖）与 `integration`（真连 Postgres） | 默认套件跑在内存 SQLite + fake Redis 上；标了 `integration` 的（如 `test_celery_tasks_pg.py`）才真连库。 |
| ruff 口径 `line-length=120` / `target-version=py312`；AI 调用必须走 service 层 | `TID251` 的 banned-api 禁掉直接 `import openai`（**INV-005**）。白名单只有 `app/services/ai_service.py`、`app/services/translation/*` 与一个一次性运维脚本。 |
| **ruff 版本必须与 `.pre-commit-config.yaml` 的 rev 同步** | `requirements-dev.txt` 里钉了 `ruff==0.15.18`，与 pre-commit 的 rev 一致。ruff 的 formatter 输出会随小版本变，曾发生 CI 装 0.16.4 而 pre-commit 钉 0.15.18、两边格式判定打架。改一处就同时改另一处。 |
| mypy 是 **baseline 门，不是无错门** | CI 只拦 `backend/.mypy-baseline` 中 `file:code` 对之外的**新增**错误；数量以该文件为准。修掉存量要顺手把基线调低；**不要**为了让新错误过门往基线里加行。mypy 上界钉 `<2.4`，升版本须重估基线（曾出现 2.3.1 让错误数 53→77）。 |
| 覆盖率门 `--cov-fail-under=60` | 在 CI 的 backend job 里。 |
| `pip-audit` 是硬门，豁免要带复核日期 | 豁免写在 `backend/.pip-audit-ignore`，每行格式 `<ID> <review-by> <owner> <why>`；`review-by` 是期限不是备注，**过期即失败**，被接受的公告必须重新论证，不能继承。由 `backend/scripts/pip_audit_gate.py` 执行，它还只会打印已被上游修掉的陈旧行。 |
| `requirements-dev.txt` 里的钉版是**故意的** | 尤其 `aiosqlite==0.20.0`：0.22.1 的 worker 线程不带 daemon flag，而测试套件不关测试 engine，线程活过 session，解释器永远停在 `threading._shutdown()`。症状是 CI 报「746 passed, 0 failed」然后被 10 分钟超时杀掉。放开任何钉版都要在 CI 里重新验证，本地过不算。 |

## 依赖集与镜像的对应（易错）

backend 只剩两套 requirements（2026-10 拆分后 GPU 依赖集已随 worker 搬走）：

| 文件 | 给谁 |
|---|---|
| `backend/requirements-cloud.txt` | **云端唯一运行集**——公网服务器/容器；不含 torch，web 栈（fastapi/starlette/sentry-sdk）在已修版本上，且**没有任何 pip-audit 豁免** |
| `backend/requirements-dev.txt` | 测试与 lint（pytest / ruff / mypy / pip-audit / bandit / pre-commit） |

GPU 依赖集 `backend/requirements.txt` **已删除**，现在在 `gpu-worker/requirements.txt`（另有 `requirements-dev.txt` / `requirements-ci.txt`，分工见 [`gpu-worker/README.md`](../gpu-worker/README.md)）。镜像侧：GPU/一体化镜像 `backend/Dockerfile` 已删除，`docker-compose.yml` 的 backend / celery 服务改用 `backend/Dockerfile.cloud`（装 `requirements-cloud.txt`，带 `entrypoint.sh`）。CI 的 backend 与 e2e job 装 `requirements-cloud.txt` + `requirements-dev.txt`；新增的 `gpu-worker` job 只装 `gpu-worker/requirements-ci.txt`。`scripts/pip_audit_gate.py` 默认只审计 `requirements-cloud.txt`（GPU 栈不在 backend job 里安装，其审计口径见 gpu-worker README）。

## 迁移与部署

- **迁移只由 backend 容器跑**：`entrypoint.sh` 按 `RUN_MIGRATIONS` 门控，`celery` 与 `celery-beat` 都是 `RUN_MIGRATIONS=0`。三个容器并发 `alembic upgrade head` 会在同一 revision 上竞争，实测表现为 celery 容器里的唯一约束冲突（backfill INSERT 的 `duplicate key`），落败的容器只能走「继续启动」分支，留下迁移到一半的 schema。
- `entrypoint.sh` **不会**因为迁移失败而阻断启动（失败的迁移通常意味着 DB 不可达，gunicorn 会经 `/health` 暴露出来）。
- 生产 `ENV` 漏配即按 dev 形态运行：`ENV` 默认 `development`，意味着**没有 HSTS/CSP**、JSON 日志与限流按 dev 口径。部署后必须核对。
- 生产启动时若短信凭据缺失，`lifespan` 会打 warning 并**fail closed**（发码 502、校验一律拒绝）。固定的测试码 `1234` 不再自动回退：只有 `SMS_DEV_FAKE_ENABLED=true` 且 `ENV` 为 `development`/`testing` 才生效，production 启动即拒绝该开关；dev-fake 模式下也必须先发过码（Redis 有记录）才接受。

## 常用脚本（`backend/scripts/`）

`seed_e2e.py`（e2e 播种，不跑的话观看页 spec 会整片 skip）、`create_admin.py`、`grant_teaching_access.py`（授予/撤销 `teaching_access_grants`，V2 教学的唯一写入口）、`seed_teaching_quiz.py`（本机走查用：播种 4 道合成题目并授权，复用 `tests/teaching_fixtures.py`）、`pip_audit_gate.py`（`--ignore-file`/`--no-deps` 供 GPU 锁复用）、`production_preflight.py`（生产配置预检，不连库）、`sign_lesson_receipt.py`（SLCS 课程发布收据的签发方工具：`keygen`/`claims`/`sign`，私钥必须在仓库外，本文件不 import `app.*`）、`smoke_lesson_publication.py`（在真实库上跑完导入→审核→签收据→发布→撤回→恢复，把签发脚本当子进程调用）、`measure_baseline.py`（A12 可复现基线）、`inventory_orphan_media.py`（只读孤儿媒体盘点）、`download_ecdict.py`、`import_catalog.py`、`seed_official_videos.py`、`retranscribe_video.py`、`recover_video.py`，以及若干 `backfill_*.py` / `rebackfill_*.py`。

**GPU 不再在本地跑转录**：`retranscribe_video.py` / `reprocess_official_videos.py` / `seed_local_video.py` 已改写为「重置状态 + 入队 `process_video`（走 head → GPU → tail）」，不再在本地调 WhisperX；`reprocess_official_videos.py` 的 JSON 导出上传流程已退役（`upload_reprocessed.py` 早已不存在）。`backfill_video_duration.py` 改用 `app.core.media_probe.get_video_duration`。

Windows 服务与隧道是 PowerShell：`run_celery_worker.ps1`、`proxy_tunnel.ps1`、`setup_pot_proxy.ps1`、`run_batch_driver.ps1`；GPU worker 的 `run_gpu_worker.ps1` / `gpu_worker_tunnel.ps1` / `start_gpu_worker.py` 已移到 `gpu-worker/scripts/`（见 [`gpu-worker/README.md`](../gpu-worker/README.md)）。

## 与根文件的分工

规则、失效指针与跨域约定都在根 [`CLAUDE.md`](../CLAUDE.md)；本文件只承接后端专属的操作约束。源码里的 `INV-*` 注释是活规则，但那份带编号的清单文件已删——以代码（尤其 `backend/tests/test_architecture_invariants.py`）为准。
