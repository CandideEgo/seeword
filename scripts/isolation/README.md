# 基础设施隔离演练

本目录不是普通单测。A07/A10 脚本会重启/删除容器、删除独立命名卷、杀桩 worker、写专用 PG；**不能指向开发或生产栈**。

- 根 `docker-compose.isolation.yml` 定义独立项目、Redis 与可选 PG。
- `render_redis_acl.py` 从版本化 ACL 模板读取策略、从环境读一次性密码，写入被忽略的实际 ACL 文件；不能打印或提交密码。
- `gpu_stub_worker.py` 只模拟队列/回调，不加载 GPU 模型。
- `test_a07_redis_recovery.py`：验证 AOF、队列与重启恢复。
- `test_a10_gpu_acl.py`：验证云/GPU ACL 与私有 unacked 命名空间。SSH 宿主侧限制不由无 sshd 的容器测试证明。

脚本参数支持用例选择与 `--keep`；具体命令以 argparse 为准。默认 Docker 驱动有 Windows/WSL 分支，必要时用 `A07_DOCKER`/`A10_DOCKER` 指定。输出默认在本地忽略的 `tmp/isolation/`，不再把每次原始日志和截图累积进 docs。

根目录执行，必须先确认所有密码/端口/项目名均为隔离环境：

```bash
PYTHONUTF8=1 backend/.venv/Scripts/python.exe scripts/isolation/test_a07_redis_recovery.py
```

```bash
PYTHONUTF8=1 backend/.venv/Scripts/python.exe scripts/isolation/test_a10_gpu_acl.py
```

脚本退出码非零就有失败；SKIP/未证明不算通过。清理只能针对本次独立项目，不能用全局 prune。
