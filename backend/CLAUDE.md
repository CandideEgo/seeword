# 后端工作规则

全局规则见 [根 CLAUDE.md](../CLAUDE.md)，架构见 [当前框架](../docs/project-audit/architecture.md)。本文件只管后端操作。

## 环境和依赖

- Python 3.12；中文 Windows 每个 Python 进程带 `PYTHONUTF8=1`，显式使用本目录 `.venv/Scripts/python.exe`，否则 UTF-8 `.env` 可能被 GBK 解码而启动失败。
- `requirements-cloud.txt` 是 API/云端 worker 运行集，`requirements-dev.txt` 是测试/检查工具；GPU 依赖属于独立 `gpu-worker/`，不可混进云端镜像。
- `Dockerfile.cloud` 配 `entrypoint.sh`。环境取 `app/core/config.py::Settings`，模板是 `.env.example`；Compose environment 不是自动把宿主全部变量传进去。

## 命令

以下命令工作目录均为 `backend/`。启动整体服务优先 `/dev`，下面是单项工具；迁移只对明确授权的目标库执行。

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000 --timeout-keep-alive 120
```

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m celery -A app.tasks.celery_app worker -Q celery --pool=solo --loglevel=info
```

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m celery -A app.tasks.celery_app beat
```

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m alembic upgrade head
```

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m pytest tests/ -v
```

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m ruff check app/ tests/
```

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m ruff format --check app/ tests/
```

## 测试与门禁

- pytest 配置只在 `pytest.ini`，不在 pyproject 同放一份；超时配置不能被另一份配置静默覆盖。
- 默认测试使用内存 SQLite 和 fake Redis；`integration` 真连专用 PostgreSQL。未指定测试库时不能拿业务库代替。SQLite 通过不证明 PG 行锁/索引/迁移通过。
- CI 运行 `app/ tests/` lint、format、mypy baseline、覆盖率 60%、pip-audit、bandit，并用独立服务跑集成测试。`scripts/` 不在常规 backend lint 命令中，新增/改脚本应另外检查。
- ruff 版本与根 pre-commit rev 同步；AI SDK 直接 import 由 TID251 约束，允许出口认 `pyproject.toml`，不要为新路径添加随意豁免。
- mypy 是不增加已知 `file:code` 对的 baseline 门，不是“没有类型问题”。修存量可降基线，不能抬基线掩盖新问题。
- pip-audit 豁免有到期日和理由；不能继承过期豁免。版本钉死的测试依赖不可无验证放开。
- SLCS 安装制品验证独立于普通 pytest，执行方式认 `.github/workflows/slcs.yml`。测试必须 import 安装的 wheel，不能把源码测试/skip 当发行验收。

## 事务与发布

- 请求使用 `get_db`，任务/脚本用 `get_async_session_maker`；engine/session maker 懒建。不要在模块 import 时随意连业务库。
- 模型集中注册、schema/前端 DTO 对齐、事务/幂等边界按全局规则保持。
- 迁移只有 backend 拥有，worker/beat 使用 `RUN_MIGRATIONS=0`。并发升级会竞争同一个 revision。
- `entrypoint.sh migrate-only` 迁移失败返回非零，是发布门；正常启动模式会记录错误并继续，`/health` 只证明连通，不能证明迁移完整。
- `ENV` 默认 development。生产必须核对实际 ENV、安全头与配置，不能只凭容器启动判断。
- 短信凭据缺失时生产 fail closed。测试固定码只在 development/testing 显式开启 `SMS_DEV_FAKE_ENABLED` 且先发码后有效，production 拒绝该开关。

## 人工脚本

脚本逐项职责、输入依赖和风险见 [后端逐文件索引](../docs/project-audit/catalog/backend.md)。`backfill`/`purge`/`seed`/`recover` 都可能改库或入队，不自动当成安全检查。签发课程收据的私钥必须在仓库外；内容核验工具可能调用真实模型，不以“检查”为名擅自执行。
