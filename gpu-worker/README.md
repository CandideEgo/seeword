# GPU 转录 worker

独立 Python 3.12 组件，只消费 `transcription_gpu`，转录后 HTTP 回调云端；不 import `app.*`，不持有数据库或 OSS 凭据。整体配合见 [当前框架](../docs/project-audit/architecture.md)，逐文件说明见 [运行组件索引](../docs/project-audit/catalog/runtime.md)。

## 入口与协议

- `scripts/run_gpu_worker.ps1`：加载本目录 `.env.gpu-worker`，用本目录 `.venv` 启动 `scripts/start_gpu_worker.py`。
- `scripts/start_gpu_worker.py`：启动安全闸、Redis 心跳、Celery worker。Windows 使用 solo、单并发；NSSM 服务名 `SeeWordGpuWorker`。
- `scripts/gpu_worker_tunnel.ps1`：SSH keepalive，服务名 `SeeWordGpuTunnel`。Redis 通过受限隧道连云端，不对公网开放；具体主机和密钥路径查仓库外 ACCESS 说明。
- 任务名/心跳键/回调头的权威是 `gpu_worker/contracts.py`。保留的 `app.tasks.video_processing.transcribe_video_gpu` 是消息兼容名，不是要 import 的模块。
- 参数为视频 ID、源地址、platform（local/imported），预留 language。local 接收签名下载 URL，不需要 OSS key。
- `tasks.py` 发送真实音频时长、字幕和词时间；共享回调密钥不是 JWT。回调投递失败可重跑整个转录，不能当低成本网络重试。
- Redis 的私有 unacked 命名空间认 `broker_settings.py`，与 `deploy/redis/users.acl.template` 一起改。

## 安装与配置

运行机需 ffmpeg/ffprobe、下载器所需 Node、合适 CUDA/torch 和模型。复制 `.env.gpu-worker.example`，变量和默认值认 `gpu_worker/config.py`，不把真实配置提交入库。

- `requirements.txt`：真实运行集；`requirements.lock.txt`：传递闭包审计/SBOM 输入；`requirements-dev.txt`：开发工具；`requirements-ci.txt`：无 GPU 的轻量测试集。
- 不默认假定某台机器已有 `.venv` 或某个 CUDA 版本。模型使用已确认的本地路径；SYSTEM 服务需要机器级 PATH、显式模型缓存目录。
- `start_gpu_worker.py` 拒绝环境中 `DATABASE_URL`、`OSS_ACCESS_KEY`、`OSS_SECRET_KEY`；这是权限收敛，不代表远程 broker 不存在其他风险。
- 日志中的连接串和下载签名 URL 要脱敏；长期凭据只留运行机。

在 `gpu-worker/` 执行：

```bash
powershell -File scripts/run_gpu_worker.ps1
```

```bash
PYTHONUTF8=1 PUNCTUATION_MODEL_DISABLED=1 .venv/Scripts/python.exe -m pytest tests -q
```

```bash
PYTHONUTF8=1 .venv/Scripts/python.exe -m ruff check gpu_worker tests scripts
```

测试 mock 模型/网络，不证明真实 GPU 精度、吞吐或云端隧道。无 GPU 环境可安装轻量 CI 集运行这些测试；不要启动真实 worker 来跑单测。依赖安全审计使用完整 lock 与带期限的 `.pip-audit-ignore`，不得放宽豁免。
