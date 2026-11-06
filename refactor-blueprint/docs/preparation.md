# V2 开工前准备：环境基线、惰性边界与 P02.2 契约

日期：2026-11-06。本文只记录**准备工作**：实际环境与代码基线、默认全关时的行为边界、遗留风险处置、P02.2 的契约冻结与迁移/回退。已落地切片的行为与验证仍以[实施记录](implementation.md)为准，wire 契约的唯一事实源是[接口契约](contracts.md)。

## 1 结论

| 门 | 结果 |
| --- | --- |
| 代码基线 | `master` `75387eaf`，工作树在本轮改动前干净且已推送；本地 HEAD 不等于生产部署版本 |
| 迁移链 | 93 个 revision、单一 head `9f2c8a7d6b10`（本轮新增 `b8e2f4a6c901` 后为 94）、单一根 `80e681bd554d`、无缺失父节点/环；V2 迁移（本轮前 4 个，新增后 5 个）线性追加在旧 head `b7c8d9e0f1a2` 之后 |
| V2 模型/迁移漂移 | 21 张表零漂移；新增 blocks 表与 `status` 列后 `scripts/check_schema_drift.py` 仍为 0 新漂移 |
| 生产部署版本与业务库 revision | **未读取**。只读 SSH 被权限分类器拒绝（`Production Reads`）；需用户授权或运维执行。建议命令见 §5 |
| 真实网关/模型/预算证据 | 未取得，沿用 P01/P02 记录；不要用合成替身代替 |
| 默认全关惰性 | 审计出 6 类会触碰 V2 表的路径，本轮修复 5 类；考试链路（`c8d9e0f1a2b3`）无法用开关隔离，改为「部署必须带上迁移」的硬契约 |
| P02.2 契约 | 已在 [CTX11](contracts.md#ctx11-流式导师回复与块发布p022) 冻结，按该契约实施 |

## 2 环境与基线

- **仓库**：`master`，`75387eaf`；根 `CLAUDE.md` 所述 README/PROGRESS 仍是活文档。
- **迁移图**：脚本解析 94 个迁移文件（本轮前 93）得到唯一 head。V2 链序：
  `b7c8d9e0f1a2 → c8d9e0f1a2b3 → d9e0f1a2b3c4 → e0f1a2b3c4d5 → 9f2c8a7d6b10 → b8e2f4a6c901`。
- **本机**：Docker 29.9.2 可用；隔离 PostgreSQL 16 容器用于迁移与并发验证（随机 loopback 端口、tmpfs），验证后已删除，未使用业务库。
- **生产**：本机 `~/.seeword/ACCESS.md` 记录了只读入口；本轮未连接。部署仍走 `/deploy`，`entrypoint.sh migrate-only` 是发布前迁移门。

## 3 审计发现与处置

只读审计覆盖装配/开关、迁移链、模型出口、运行与 SSE、账号生命周期、测试与门禁。级别按「默认全关部署是否会被破坏」判定。

| 编号 | 级别 | 事实 | 处置 |
| --- | --- | --- | --- |
| P1 | blocker | `_purge_user` 第一步与第 5 步无条件访问 V2 表；未迁移库上注销永久失败（PIPL 30 天承诺静默失效） | **已修**：`_prepare_v2_removal` / `_delete_v2_children` 先查表是否存在；第 5 步只删除**实际存在**的表 |
| P2 | blocker | 既有考试链路映射 `exam_sessions.snapshot_*` 与 `user_exposure_*`（迁移 `c8d9e0f1a2b3`），开关关不掉 | **决策**：HEAD 不能跑在 V2 迁移之前的 schema 上；「部署即必须迁移」写进发布契约（§5），不做条件映射 |
| P3 | high | 数据导出末尾无条件读 9 张 V2 表，未迁移库上整包导出失败 | **已修**：`_gather_teaching_data` 按表存在性早退，非 V2 数据仍正常导出 |
| P4 | high | `sweep-teaching-runs` 每 10 秒无条件查 5 张 V2 表 | **已修**：任务体先检查 `SWEEP_TABLES`；开关不用于跳过（已入队的 run 仍要回收） |
| P5 | high | `require_access` 先查 `teaching_access_grants` 再看开关，未迁移库返回 500 而非 503 | **已修**：开关先判，再查账号与授权表 |
| P6 | high | 教学读接口（`/teaching/sessions`、context）只查 scope，不查 schema；`/practice` 与设置页对全体用户请求 | **已修**：`owned_session` / `list_sessions` / `get_learning_context` 在表缺失时 503；外部连接列表在表缺失时返回空 |
| P7 | high | `MCP_SDK_ENABLED=true` 且镜像无 `mcp` 时整个 API 启动失败 | **已修**：捕获 `ImportError`，降级为与关闭态相同的 503 路由并告警 |
| P8 | high | 迁移失败不阻断启动、`/health` 只 `SELECT 1`，schema 漂移对编排不可见 | **保留为发布契约**：`/deploy` 的 migrate-only 是硬门；是否把 schema revision 纳入 `/health` 属于部署行为变更，需单独决定（§7） |
| P9 | medium | 生产 compose 的 env 白名单缺 `TEACHING_DIALOGUE_ENABLED`、`CONTENT_RECEIPT_*`、`CONTENT_VERIFICATION_API_KEY` 等，设了不生效 | **已修**：补齐 backend / teaching 服务白名单，并加入本轮新增开关 |
| P10 | medium | `gateway_lifecycle_intents` 只有写入，没有消费者；pending 行无限累积 | 保留（P05 运营闭环）；回执/清理任务不在本轮 |
| P11 | medium | `teaching_run_retention_hours` / `teaching_usage_retention_days` 从未被读取，保留期写死 24h | 保留（P05）；不伪造「可配置」语义 |
| P12 | medium | `create()` 一次读取全站活跃 run、常量 advisory 锁串行化全部创建；第 5 个并发用户可能被全站 429 | 保留（B02.6/P02 运行治理）；不属于 P02.2 |
| P13 | medium | SSE 每秒全量重投影会话；`/runs/{id}` 缺 `no-store` | 后者**已修**；前者保留（P02.3 读取路径优化） |
| P14 | medium | MCP 适配器测试在 CI 被 `importorskip` 整体跳过；V2 配置 fail-closed 无测试 | **已修测试缺口**：补齐 V2 开关联动、verified gateway 必填、streaming 依赖等 7 项；MCP 运行依赖仍不在云端 requirements |
| P15 | medium | 没有机器门禁「模型出口只在 `teaching_gateway`」 | **已修**：新增架构不变量，`app/` 内除该模块外不得出现 `/chat/completions` 字面量 |
| P16 | low | 事件序号是内存自增，发布必须持有 run 行锁 | 接受：块发布用短事务，锁窗口与事件写入同事务 |
| P17 | info | 前端对 V2 零覆盖（e2e 把 `/api/v1/teaching/*` 的 503 视为正常） | 记录：V2 目前是纯后端能力，前端门禁绿灯不代表 V2 可用 |

## 4 P02.2 契约冻结

wire 与运行语义只在 [CTX11](contracts.md#ctx11-流式导师回复与块发布p022)。以下是本轮确定、容易反复的取舍：

- 新增开关 `TEACHING_STREAMING_ENABLED`，默认 false，要求 `TEACHING_DIALOGUE_ENABLED`；关闭时完全走 P02.1 的非流式 JSON 路径，不触碰新表。
- 新表 `teaching_message_blocks` 与 `teaching_messages.status`（`complete | streaming | interrupted`）；块 append-only，ORM `before_update` 拒绝任何修改。
- 引用标记为 **1 基**（`[1]` = `sources()` 的第一个），与 P02.1 JSON 的 **0 基** 索引并存；两种模式各自的提示词和解析器都显式写明，不共用索引基准。
- 旧 `MODEL_MAX_OUTPUT_TOKENS=128` 不变；教练使用独立别名 `LLM_GATEWAY_TUTOR_MODEL`（默认 `teaching-tutor`）、`LLM_GATEWAY_TUTOR_MAX_TOKENS`（默认 1024）与 `ADAPTER_MODEL_OUTPUT_CAPS` 按模型放宽，避免把窄路径一起放宽。别名未在网关配置时调用失败关闭。
- 用量只记录不结算：`reported / missing / unknown` 写入 step 的 `safe_result`；`usage: null` 不等于 0。
- 取消/撤权：停止发布新块，但继续排空上游流让网关结算；已展示的文字保留，消息标 `interrupted`。

## 5 迁移与发布契约

- 本轮新增迁移 `b8e2f4a6c901`（blocks 表 + `status` 列），继承 `9f2c8a7d6b10`；在隔离 PG 上完成 `initial → head`、`downgrade -1 → upgrade head`、列/FK/唯一约束核对。
- **HEAD 与迁移必须同批上线**：`c8d9e0f1a2b3` 给既有 `exam_sessions` 加列，旧考试链路已映射这些列；只关开关无法回到旧 schema。发布前必须确认 `backend` 容器已完成 migrate-only 且 `alembic_version = head`。
- 只读核查生产（需用户授权/运维执行）：
  - `git -C /opt/speaking rev-parse HEAD`
  - `docker compose -f /opt/speaking/docker-compose.prod.yml exec -T db psql -U <user> -d <db> -tAc "select version_num from alembic_version"`
  - 只读 `.env` 中 V2 开关是否为 false（不要复制凭据）。
- 回退：关闭 `TEACHING_STREAMING_ENABLED` 即回到 P02.1 行为；数据库保留新表/新列（前向兼容回退）。`downgrade` 只用于一次性库演练，不作为生产回退手段。

## 6 本轮实际验证

命令在 `backend/` 使用 `.venv/Scripts/python.exe` 并设置 `PYTHONUTF8=1`。真实模型、真实网关预算、浏览器与部署均未执行。

| 检查 | 结果 |
| --- | --- |
| V2/账号/架构相关快速回归 | 214 passed（teaching、dialogue、tutor gateway、runtime、context、publication、receipts、CLI、account data/deletion、架构、配置、celery 任务） |
| 新增准备与流式回归 | 18 passed（schema gating 6 + streaming 12） |
| 配置与架构门 | 58 passed（含 7 项 V2 fail-closed、模型出口唯一性） |
| 适配层回归 | 27 passed（含按模型上限、入站/出站 SSE 增量转发） |
| 隔离 PostgreSQL | `alembic upgrade head` 成功；`downgrade -1` 删除 blocks/status 后 `upgrade head` 恢复；`check_schema_drift.py` 0 新漂移 |
| PostgreSQL 并发 | 6 passed（流式取消只保留已提交块；既有对话并发 5 项复验） |
| ruff check / format | 通过（app/、tests/、迁移、adapter） |
| mypy baseline | 无新增 `file:code`（原始 exit 1 仍为存量 39 组，未改基线） |
| 全后端套件/覆盖率、真实网关/模型、部署 | 未执行 |

临时 PG 容器（随机 loopback 端口 + tmpfs）与测试数据已删除；未连接业务库、未启动 GPU worker，未修改已有网关容器定义与数据卷。

## 7 未决事项（需要用户或运维）

1. **生产只读核查**：部署 commit、业务库 `alembic_version`、真实 V2 消费者。权限分类器拒绝了本轮 SSH 只读操作，需要显式授权。
2. **`/health` 是否纳入 schema revision**：当前迁移失败只影响功能不阻断启动；加入 `/health` 会改变编排行为（celery-beat 依赖 `service_healthy`），需单独决定。
3. **`TeachingAccessGrant` 无生产写入路径**：开放真实用户前需要管理员 API/CLI 或改用白名单 env。
4. **真实网关与模型能力**：`ADAPTER_MODEL_OUTPUT_CAPS` 的 1024 必须在真实供应商上验证后才能配置；否则适配层会 422 `output_cap_exceeded`（失败关闭）。
