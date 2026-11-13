# gpu-worker — SeeWord GPU 转录 worker（独立组件）

本目录是 SeeWord/Speaking 的 **GPU 转录 worker**，从 `backend/` 拆出来的独立可运行组件。

它只做一件事：消费云端 Celery 的 `transcription_gpu` 队列 → 用 WhisperX（失败回退 faster-whisper）把视频转成带逐词时间戳的字幕 → POST 回云端回调接口。它**没有数据库、没有 OSS、没有 Web 接口**，唯一输出通道是那个 HTTP 回调。

```
gpu-worker/
├── gpu_worker/                  # 包
│   ├── config.py                # GPU worker 专属 Settings（pydantic-settings，读 .env.gpu-worker）
│   ├── contracts.py             # 与云端的契约常量：TASK_NAME / 心跳 key / 回调头
│   ├── celery_app.py            # Celery("gpu-worker")，只声明 transcription_gpu 队列 + 任务路由
│   ├── tasks.py                 # transcribe_video_gpu + 回调投递 + 告警
│   ├── alerts.py                # send_alert()：DingTalk/通用 webhook 签名 POST
│   ├── logging.py               # configure_logging() / get_logger()（structlog + request_id）
│   ├── broker_recovery.py       # 启动时恢复 gpu_unacked 孤儿消息
│   ├── broker_settings.py       # GPU 私有 broker 键与 ACL 身份配置
│   ├── sources.py               # VideoSource 枚举（复制自 backend 模型，值即协议）
│   ├── ytdlp_cookies.py         # disposable_cookiefile()（复制自 backend cookies 服务）
│   └── transcription/           # 转录业务逻辑（从 backend 原样搬出，只改 import）
├── scripts/
│   ├── run_gpu_worker.ps1        # 入口：加载 .env.gpu-worker → 用本目录 .venv 启动 worker
│   ├── start_gpu_worker.py       # 安全闸 + Redis 心跳 + celery worker_main
│   └── gpu_worker_tunnel.ps1     # SSH 隧道 keepalive：本机 16379 → 云端 Redis
├── tests/                       # pytest（不装 whisperx 模型、不连 Redis）
│   ├── test_contracts.py        # 任务名/队列/心跳/回调头等跨机契约
│   ├── test_broker_settings.py  # 私有 broker 键 / ACL 身份
│   ├── test_security_guard.py   # 无 DB/OSS 凭据边界（子进程断言 exit code）
│   ├── test_callback_delivery.py
│   ├── test_whisperx_oom_retry.py
│   └── test_whisperx_segmentation.py
├── requirements.txt             # 运行依赖（无 web 栈，含 whisperx/GPU 栈）
├── requirements.lock.txt        # 完整传递闭包锁（审计与 SBOM 的唯一输入，A11）
├── .pip-audit-ignore            # GPU 依赖豁免（带复核日期，过期即失败）
├── requirements-dev.txt         # 本地开发：pytest / pytest-asyncio / ruff
├── requirements-ci.txt          # CI 最小依赖子集（无 torch/whisperx）
├── pyproject.toml               # ruff 口径（line-length=120 / py312）
├── pytest.ini                   # testpaths / --timeout / pythonpath
└── .env.gpu-worker(.example)    # 本机配置；真实文件含密钥且被 .gitignore
```

## 1. 它和云端怎么配合

云端是「head / GPU / tail」三段切分里的 head 与 tail，本组件只跑中间那段：

```
云端 process_video（yt-dlp 元信息 / 本地文件先 stage 到 OSS）
  └─ celery_app.send_task(TASK_NAME, args=[video_id, source, platform], queue="transcription_gpu")
        │  （通过 Redis broker，本机经 SSH 隧道连云端 Redis）
        ▼
本组件 transcribe_video_gpu
  ├─ platform == "imported" → yt-dlp 拉音频（source 是原始 URL）
  ├─ platform == "local"    → httpx 下载 source（云端给的 OSS 签名 URL）→ ffmpeg
  ├─ WhisperX：VAD → 批量 ASR → 标点恢复 → wav2vec2 强制对齐（OOM 时按 batch ladder 重试）
  │             （WhisperX 不可用/失败 → faster-whisper 回退 + 重新断句）
  └─ POST 回 TRANSCRIPTION_CALLBACK_URL
        ▼
云端 /api/v1/internal/transcription/callback → 验共享密钥 + Redis 去重锁 → 写 Subtitle → 入队 tail
```

### 任务契约（**不要改**）

| 项 | 值 |
| --- | --- |
| 任务名 | `app.tasks.video_processing.transcribe_video_gpu`（**故意保留旧名**） |
| 队列 | `transcription_gpu`（本组件只消费这一个队列） |
| 参数 | `args=[video_id, source, platform]`，可选第 4 个 `language`（预留） |
| `platform` | `"local"`（source 是 OSS 签名 URL）或 `"imported"`（source 是原始视频 URL） |

任务名仍是 `app.*` 前缀：云端按这个名字 `send_task`，队列里可能还有在途消息，改名会让它们变成 unregistered task。**这是兼容契约，不是模块路径。** 常量集中在 `gpu_worker/contracts.py`。

任务本身 `bind=True, max_retries=3`：转录失败按 60s 重试；只有最后一次失败才回调 `status="error"` 并告警。回调投递失败也会重跑整个任务（宁可重转录，也不让云端视频卡在 `processing` 等 watchdog）。

### 回调契约

- 方法/地址：`POST {TRANSCRIPTION_CALLBACK_URL}`（云端 `POST /api/v1/internal/transcription/callback`）
- 认证头：`X-Callback-Secret: {TRANSCRIPTION_CALLBACK_SECRET}`（共享密钥，不走 JWT）
- body：

```json
{
  "video_id": "uuid",
  "status": "ok",
  "segments": [{"start": 0.0, "end": 2.4, "text": "...", "words": [{"word": "...", "start": 0.0, "end": 0.3}]}],
  "error": null,
  "audio_duration": 123.4
}
```

- `status="error"` 时 `segments=null`，`error` 是失败原因；`audio_duration` 取最后一段的 `end`（云端用它做幻觉检测）。
- 重试：5xx、408/425/429、网络错误按 `2^attempt`（上限 30s）退避，最多 `TRANSCRIPTION_CALLBACK_MAX_RETRIES` 次；其它 4xx 视为永久客户端错误不重试（回调接口自身限速 30/min，所以 429 必须重试）。

### 心跳契约

`start_gpu_worker.py` 每 60s 向 Redis 写 `worker:gpu:heartbeat = "1"`，TTL 90s；退出时删 key。云端 `video_seed_service.is_gpu_worker_online()` 就是 `EXISTS worker:gpu:heartbeat`，管理后台的「GPU Worker 在线/离线」和「开始处理」按钮的前置检查都依赖它。

## 2. 配置：`.env.gpu-worker`

真实文件 `.env.gpu-worker` 含密钥，**不要提交**（已在 `.gitignore`）。新机器从 `.env.gpu-worker.example` 复制。`scripts/run_gpu_worker.ps1` 会把文件里的 key=value 灌进进程环境，`gpu_worker.config.Settings` 也会从**当前工作目录**读同一个文件（两者等价，环境变量优先）。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `ENV` | `development` | `production` 时 structlog 输出 JSON |
| `LOG_LEVEL` | `INFO` | 根 logger 级别 |
| `REDIS_URL` | `redis://localhost:6379/0` | **云端 Redis**，经 SSH 隧道：`redis://:<password>@127.0.0.1:16379/0` |
| `TRANSCRIPTION_GPU_QUEUE_NAME` | `transcription_gpu` | 队列名（与云端一致） |
| `TRANSCRIPTION_CALLBACK_URL` | 空 | 云端回调地址，如 `https://seeword.top/api/v1/internal/transcription/callback` |
| `TRANSCRIPTION_CALLBACK_SECRET` | 空 | 与云端 `TRANSCRIPTION_CALLBACK_SECRET` 相同 |
| `TRANSCRIPTION_CALLBACK_TIMEOUT` | `30` | 单次回调超时（秒） |
| `TRANSCRIPTION_CALLBACK_MAX_RETRIES` | `5` | 回调重试次数 |
| `WHISPER_ENGINE` | `whisperx` | `whisperx` 或 `faster_whisper` |
| `WHISPER_MODEL_PATH` | `base` | **本机 CTranslate2 模型目录**（见下），不要填 HF 名称 |
| `WHISPERX_MODEL` | 空 | 空 = 复用 `WHISPER_MODEL_PATH` |
| `WHISPER_DEVICE` | `auto` | `auto` / `cuda` / `cpu` |
| `WHISPER_COMPUTE_TYPE` | `int8` | GPU 一般 `float16` |
| `WHISPERX_COMPUTE_TYPE` | 空 | 空 = 由 device 推导（cuda→float16，cpu→int8） |
| `WHISPER_LANGUAGE` | 空 | 空 = 自动检测；`en` = 强制英语并跳过检测 |
| `WHISPERX_VAD_METHOD` | `silero` | `silero` / `pyannote` |
| `WHISPERX_ALIGN_MODEL` | 空 | 覆盖 wav2vec2 对齐模型（默认按语言自动选） |
| `WHISPERX_BATCH_SIZE` | `8` | ASR 批大小；8GB 显存 OOM 时调小 |
| `WHISPER_PUNCTUATION_RESTORE` | `true` | 对齐前恢复标点（base/small 模型必需；turbo 可关掉省时间） |
| `WHISPER_CHUNK_DURATION` | `600.0` | 超过该时长（秒）的视频分块转录 |
| `WHISPER_MAX_CONCURRENT_CHUNKS` | `2` | 分块并发上限 |
| `TRANSCRIPTION_TEMP_DIR` | `./media/transcription_temp` | 临时音频目录 |
| `HTTP_PROXY` | 空 | yt-dlp / 下载 / Ping 用的代理 |
| `YOUTUBE_COOKIES_PATH` | 空 | yt-dlp cookies 文件（本机路径） |
| `YOUTUBE_POT_BASE_URL` | `http://127.0.0.1:4416` | bgutil POT provider（解 YouTube n-challenge）；显式给值，避免插件走 loopback 默认后经 `http_proxy` 不可达 |
| `ALERT_WEBHOOK_URL` | 空 | 告警 webhook；空则只写日志（**无 DB fallback**） |
| `ALERT_WEBHOOK_SECRET` | 空 | DingTalk 签名密钥 |

> 本文件里还可以有 `HF_HOME` / `TORCH_HOME` 这类非 Settings 字段：`Settings` 用 `extra="ignore"`，它们只会作为进程环境变量被 torch/transformers 使用。服务以 SYSTEM 账户跑时这两个必须显式指向缓存目录。

### SSH 隧道（`scripts/gpu_worker_tunnel.ps1`）

云端 Redis 不对公网开放；本机用 `ssh -L 16379:127.0.0.1:6379 admin@<云端IP>` 把云端 Redis 映射到本地 `16379`（不是 6379，避免和本地 docker-compose 的 dev Redis 撞端口）。脚本是 `while($true)` keepalive，断了 5s 后重连；注册成 NSSM 服务后随开机启动。

`REDIS_URL` 里带云端 Redis 的 `requirepass`，`start_gpu_worker.py` 打印配置时会把密码打码成 `redis://:***@127.0.0.1:16379/0`（NSSM 日志不可泄露密钥）。

## 3. 启动

前提：本机（RTX 3060 Ti 桌面机）装好 ffmpeg/ffprobe、node（yt-dlp 解 n-challenge 用）、以及 CUDA 版 torch。

```powershell
# 1) 建 venv（与主仓 backend/.venv 是两套；这里只装 worker 需要的依赖）
cd C:\Users\Administrator\Speaking\gpu-worker
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install -r requirements-dev.txt

# 2) CUDA 版 torch（whisperx 会拉 torch，但 PyPI 默认是 CPU wheel；本机验证的是 2.8.0+cu128）
.venv\Scripts\pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128

# 3) 配置
Copy-Item .env.gpu-worker.example .env.gpu-worker   # 然后填 REDIS_URL / TRANSCRIPTION_CALLBACK_SECRET
# WHISPER_MODEL_PATH=C:/Users/Administrator/local-model/Whisper-large-v3-turbo

# 4) 隧道（单独一个窗口/服务）
powershell -File scripts\gpu_worker_tunnel.ps1

# 5) 启动 worker
powershell -File scripts\run_gpu_worker.ps1
```

`run_gpu_worker.ps1` 的行为：`$rootDir` = 本目录（脚本目录的父目录）→ 读 `$rootDir\.env.gpu-worker` 灌入环境 → 用 `$rootDir\.venv\Scripts\python.exe` 跑 `scripts\start_gpu_worker.py`；venv 不存在时直接报错并提示 `python -m venv .venv && .venv\Scripts\pip install -r requirements.txt`。

**模型路径**：`WHISPER_MODEL_PATH` 必须是**本机已有的 CTranslate2 模型目录**（本机是 `C:/Users/Administrator/local-model/Whisper-large-v3-turbo`），WhisperX 与 faster-whisper 共用它。**不要填 `large-v3` 这种 HF 名称**——HF 缓存残缺时会触发联网下载失败。对齐模型（wav2vec2，~360MB）首次会自动下载到 `HF_HOME`。

**NSSM 服务**（Windows 服务，随开机启动、崩溃自动重启）：

| 服务名（NSSM / Windows 服务名） | 程序 | 说明 |
| --- | --- | --- |
| `SeeWordGpuWorker` | `powershell -ExecutionPolicy Bypass -File <gpu-worker>\scripts\run_gpu_worker.ps1` | Celery `--pool=solo --concurrency=1`，一次一个任务 |
| `SeeWordGpuTunnel` | `powershell -ExecutionPolicy Bypass -File <gpu-worker>\scripts\gpu_worker_tunnel.ps1` | SSH 隧道 keepalive |

> 注意 NSSM 的**服务名**是 `SeeWordGpuWorker` / `SeeWordGpuTunnel`（无空格，`nssm set/get` 和 `Get-Service` 都用它），DisplayName 同样是这两个名字。日志：worker → `<gpu-worker>\logs\gpu-worker.log`，隧道 → `<gpu-worker>\logs\gpu-tunnel.log`。

两个服务都跑在 SYSTEM 账户下（没有用户 PATH/profile），所以：ffmpeg/node/ssh 要用绝对路径或机器级 PATH；`HF_HOME`/`TORCH_HOME` 要在 `.env.gpu-worker` 里显式给；隧道脚本里用 IP 而不是 SSH alias。

## 4. 安全边界

`start_gpu_worker.py` 启动前执行 `_security_guard()`，**发现以下任何一个环境变量就退出（exit 1）**：

- `DATABASE_URL`
- `OSS_ACCESS_KEY`
- `OSS_SECRET_KEY`

原因是权限模型：本组件只需要 ① 连 Redis 拿任务 ② 连公共网络拉媒体 ③ 带共享密钥回调云端。它拿不到数据库和对象存储凭据，所以即使这台机器被拿下，也读不到用户数据、写不了 OSS。

其余边界：

- 只声明、只消费 `transcription_gpu` 队列（`celery_app.conf.task_default_queue` 也是它），不会误处理云端 `celery` 队列的任务。
- 不看 JWT、不碰 API：入站只有一个共享密钥回调头，出站只有 webhook 告警。
- `.env.gpu-worker` 含密钥，被 `.gitignore` 忽略；日志里 Redis 密码打码。

## 5. 检查与 CI

从本目录执行（Windows 中文环境必须 `PYTHONUTF8=1`，否则读 UTF-8 的 `.env` 会 GBK 解码失败）：

```powershell
$env:PYTHONUTF8=1; $env:PUNCTUATION_MODEL_DISABLED=1
# 模块可 import、任务已注册
.venv\Scripts\python.exe -c "import gpu_worker.celery_app as c; print(sorted(t for t in c.celery_app.tasks if t.startswith('app.')))"
# 单测（不需要 GPU / Redis / 真实模型）
.venv\Scripts\python.exe -m pytest tests -q
# lint + 格式（口径同主仓：line-length=120，target-version=py312）
.venv\Scripts\ruff.exe check gpu_worker/ tests/ scripts/
.venv\Scripts\ruff.exe format --check gpu_worker/ tests/ scripts/
```

测试用 monkeypatch 把模型、httpx、设置替换掉，`PUNCTUATION_MODEL_DISABLED=1` 避免加载标点模型；**不要**在此目录启动真实 Celery worker 或连真实 Redis 做测试。

### CI（`.github/workflows/ci.yml` 的 `gpu-worker` job）

CI 在 `ubuntu-latest` + Python 3.12 上跑，工作目录固定 `gpu-worker/`（审计与 SBOM 两步在 `backend/`），门依次是：

1. `pip install -r gpu-worker/requirements-ci.txt` — **只装最小依赖子集**（celery/redis/httpx/pydantic-settings/structlog + pytest/ruff），**不装 torch / whisperx / faster-whisper**。测试里这些引擎都被 mock，装 GPU 栈只会让 job 多花几个 GB 和十几分钟。
2. `ruff check gpu_worker/ tests/ scripts/`
3. `ruff format --check gpu_worker/ tests/ scripts/`（口径来自本目录 `pyproject.toml`）
4. `pytest tests -q`，env 带 `PUNCTUATION_MODEL_DISABLED=1`（不让测试下载标点模型）
5. `pip_audit_gate.py -r ../gpu-worker/requirements.lock.txt --ignore-file ../gpu-worker/.pip-audit-ignore --no-deps`（GPU 运行栈的依赖审计；只读锁文件，不装 CUDA 轮子）
6. `cyclonedx-py requirements gpu-worker/requirements.lock.txt` 生成 SBOM
7. 上传 `gpu-sbom` artifact

三个 requirements 文件的分工，别装错：

| 文件 | 给谁 |
| --- | --- |
| `requirements.txt` | **真正的 GPU 机器**：运行 worker（含 whisperx / faster-whisper / yt-dlp，torch/torchaudio 由 whisperx 拉取，CUDA 版需自行按 CUDA 版本装） |
| `requirements-dev.txt` | 本机开发/调试（在 `requirements.txt` 之上加 pytest-asyncio 等） |
| `requirements-ci.txt` | **CI 与无 GPU 环境**：只够跑 `pytest` + `ruff` |

### GPU 依赖的安全审计与 SBOM（A11 / OPS-07 起有门）

- **锁定**：`requirements.lock.txt` 是 `requirements.txt` 的完整传递闭包（128 个包），由
  `python gpu-worker/scripts/lock_requirements.py` 用 `pip --dry-run --report` 生成。
  文件头写明生成平台（当前是 Windows x86_64 / CPython 3.12 = 本机 GPU worker 的部署平台）。
  **换平台必须重新生成**，跨平台复用锁等于没锁。
- **审计**：CI 的 `gpu-worker` job 跑
  `python backend/scripts/pip_audit_gate.py -r ../gpu-worker/requirements.lock.txt --ignore-file ../gpu-worker/.pip-audit-ignore --no-deps`。
  用 `--no-deps` 是因为锁已钉死全部版本，再让 pip-audit 解析 torch/whisperx 只会多花几分钟和几 GB。
  豁免与云端一样带**复核日期**，过期即失败；上游修好后该行会被打印成 stale，必须删。
- **SBOM**：同一个 job 用 `cyclonedx-py requirements gpu-worker/requirements.lock.txt -o gpu-sbom.json`
  生成 CycloneDX SBOM 并作为 artifact 上传；只读锁文件，不安装 GPU 栈、不下载模型。
- **Dependabot** 已覆盖 `/gpu-worker`（`yt-dlp` 保持不钉，抽取器经常失效）。
- 当前接受的 14 条公告全部在 torch 2.8.0 / transformers 4.57.6：whisperx 3.8.6 的元数据是
  `torch~=2.8.0`，升级 torch 等于换掉整个转录栈，必须先做 GPU 侧回归；逐条不可达理由与
  2026-11-30 复核期限写在 `.pip-audit-ignore` 里。**不要**为让门变绿而往豁免里加没有论证的行。

## 6. 迁移说明

拆分原因：项目其余部分（`backend/`、`frontend/`、部署）要迁到另一台笔记本，而 GPU 转录只能跑在这台带 RTX 3060 Ti 的桌面机上。

- **本目录跟着桌面机走**：`gpu-worker/` 是自包含的（自己的 venv、自己的 `.env.gpu-worker`、自己的 requirements、不 import `app.*`），迁移时**不需要**把 `backend/` 留在本机。
- 桌面机要继续跑的服务：`SeeWordGpuWorker` + `SeeWordGpuTunnel`；`.env.gpu-worker` 的 `REDIS_URL` 指向迁移后云端的 Redis（隧道目标 IP 若变化，改 `gpu_worker_tunnel.ps1`）。
- 反方向约束：`backend/` 里不应再 import `gpu_worker.*`。云端只知道 Celery 任务名和回调 URL，没有代码依赖。
- 历史包袱：任务名保留 `app.tasks.video_processing.transcribe_video_gpu`（见上），所以 grep 到这个名字不代表还有 `app.*` 依赖。
