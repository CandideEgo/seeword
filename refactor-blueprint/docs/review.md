# 后端审查结论与工作区处置

日期：2026-11-04。本文保留开始重构前的审查快照，范围为本地代码、未提交差异、快速回归与隔离复现，不包含生产审计。文中的“当前”“本轮”指审查阶段；后续用户已授权开始重构，最新修复状态和验证见[实施记录](implementation.md)，不覆盖原问题证据。

## 1. 结论与代码基线

建议保留已提交业务底座，以业务事务和调用方向为单位逐步整理。未提交 V2 是可舍弃的试做，不是下一阶段必须沿用的系统，也不按已有文件数量计算产品进度。产品目标与实现取舍分开，舍弃代码不等于取消教学、记忆或外部接入需求。

审查基线 HEAD：`e3f5ecba635ad93d3ab28f0230716010e4e7ebca`。本轮另将 HEAD 的 `backend/` 通过 `git archive` 解包到系统临时目录做对照；没有切换当前分支或覆盖工作区。HEAD 是否就是线上版本未核验。

审查开始时有 36 个已跟踪文件修改：backend 19、frontend 7、docs 3、基础设施/脚本 6、根 CLAUDE.md 1。另有未跟踪文件：backend 35、frontend 10、网关与 compose 16、历史 V2 文档/证据 66，以及本蓝图文档 6。数量是审查起点快照，不含忽略文件，不代表全部是本次产生的。

本轮仅修改蓝图文档与根标准指针；上述业务代码和历史证据未删除、未恢复。用户已允许舍弃 V2，不再要求保护试做实现；暂不清理是为了先完成依赖、数据库状态与消费者的核对，不是等待用户再次批准同一项取舍。

## 2. 审查发现

优先级表示后续处理顺序。静态推断、隔离复现和生产现象分开记录；没有证据的线上故障不作结论。

### REV01 · P1 · 本地过期会把漏通知的已付订单排除出补单

- 来源：HEAD 旧站内 Order 支路，工作区未改这些代码。金数据使用独立收款模型，不能把本结论外推为金数据已发生同类故障。
- 位置（**本结论是历史快照**：`backend/app/tasks/order_tasks.py` 与 `backend/app/api/v1/payments.py` 已随 2026-11 会员收费链路下线删除，迁移 `d4e5f6a7b8c9` 删掉 `orders` / `jinshuju_payments` / `user_video_unlocks` 与 `users.plan*`。下面的行号指向审查时的 HEAD `e3f5ecba`）：`order_tasks.py` 的 `expire_pending_orders`（15）与 `reconcile_pending_orders`（57）；`payments.py` 的支付回调（186、228）；`celery_app.py` 的订单调度。
- 触发：订单已在供应商付款，通知丢失；本地订单超过 30 分钟先被过期任务改为 expired。补单只查 pending，回调也拒绝非 pending。
- 结果：之后即使供应商认定已付款，补单不会查询该订单，用户无法靠这条自动路径取得会员。过期巡检每 5 分钟、补单每 15 分钟，二者具有重叠窗口。
- 证据：HEAD 隔离 SQLite 复现，模拟供应商始终返回 paid；先过期再补单，补单计数 0、供应商查询次数 0、状态仍 expired。复现不涉及真实付款。
- 后续标准：区分本地订单超时和真实支付事实；以订单来源、支付凭证和幂等结算统一处理迟到通知/对账。若明确退役旧支路，保留所需兼容响应和历史财务数据，不默默留着一条看似可启用的收费路径。
- **现状**：收费链路已整体删除而非留壳，因此本条不再有可修的代码；保留它是为了记录「为什么不要恢复这条支路」的推理。

### REV02 · P1 · 批量补单调用内部 commit，提前释放后续订单的锁

- 来源：HEAD。位置同上（两个文件均已随 2026-11 收费链路下架删除），`order_tasks.reconcile_pending_orders` 与 `payments._process_successful_payment`（65–97）。
- 证据：任务一次 `FOR UPDATE SKIP LOCKED` 读出全部订单；循环调用的支付 helper 每次自行 commit，第一次成功就释放整个事务的行锁。session 使用 `expire_on_commit=False`，后续订单对象仍保留旧状态；helper 没有重新锁定并校验该订单。
- 推断：多个订单的批次与另一补单/回调交错时，后续订单可能被重复结算，重复延长会员。只有一笔订单的 happy path 测试不能证明批次安全。
- 状态：锁释放与提交位置已静态确认；并发重复发放尚未在 PostgreSQL 复现。本机 Docker engine 不可达，不能拿 SQLite 证明 PG 锁行为。
- 后续标准：结算进入共享应用服务，单笔订单在最终事务内重新锁定/刷新并以状态或唯一结算凭据幂等认领；禁止下层 commit 破坏上层批次事务。也不把远程供应商查询放在一个长批次锁事务里。

### REV03 · P2 · 通知先推送，再由调用者决定提交或回滚

- 来源：HEAD。位置：[notification_service.py](../../backend/app/services/notification_service.py) 的 `create_notification`（43–133），新增与更新去重通知都在 flush 后调用 `_push_notification`；函数约定调用者 commit。
- 触发：通知推送后，业务事务继续执行并失败/回滚。
- 结果：用户收到数据库中不存在或未更新成功的通知。重新读取列表、点击关联内容可能与刚收到的消息不一致。
- 证据：HEAD 隔离复现成功；捕获到通知推送后回滚，按通知 ID 再查库为空。捕获发送函数用于观察调用次序，不验证真实 WebSocket/Redis 网络。
- 后续标准：提交成功后才能推送；对需要可靠送达的通知，把派发意图与通知记录一同持久化，提交失败不发，派发失败可补偿。不让通知领域依赖 HTTP 路由模块。

### REV04 · P2 · 词汇事实与学习记录存在可丢失窗口

- 来源：HEAD。位置：[vocabulary.py](../../backend/app/api/v1/vocabulary.py) 的 `review_word`（511–556）、`mark_word_mastered`（561–603）；[learning_event_service.py](../../backend/app/services/learning_event_service.py) 的 `emit_event`。
- 证据：先 commit 词汇变化，再尝试发学习事件并第二次 commit；异常吞掉。事件服务本身也以 savepoint 和日志处理失败，没有这两条路径的持久重投意图。
- 推断：进程在两次提交之间退出或事件写失败时，复习已经生效，学习日/档案事件可能永久缺失。这是现有 best-effort 契约的局限，不是 V2 新增问题。
- 后续标准：先区分必须持久化的学习事实与允许丢失的行为埋点；前者与业务写入原子提交，聚合读模型允许异步重建。不能直接把所有现有 emit_event 改为抛异常，破坏旧调用者。
- 状态：静态确认；本轮未执行进程中断故障注入。

### REV05 · P2 · 应用服务与任务反向依赖 HTTP 层

- 来源：HEAD。位置：`order_tasks.py:107` 从 API 导入 `_process_successful_payment`（两者均已在收费链路下架时删除）；`notification_service.py:139` 从 API 导入 `push_to_user`（**这一处仍然存在**，是当前要处理的那半条）。
- 影响：批处理、HTTP 生命周期和业务提交规则相互绑定，难以单独测试或复用到外部接入；REV02、REV03 正是边界不清的具体表现。
- 后续标准：支付结算归 billing 应用服务；WebSocket 连接管理/Redis 推送归通知传输适配器。HTTP 与 Celery 都调用服务，不让服务反向导入 API。维持已有 URL、任务名和响应契约。
- 状态：静态 import 与 HEAD/工作区内容一致性已确认；当前测试通过不表示该边界已经合理。

### REV06 · P1（清理/发布前）· V2 开关不能隔离新表依赖

- 来源：未提交 V2。位置：[account_data.py](../../backend/app/services/account_data.py) 的新增 exposure sections（137–138）和 `_gather_teaching_data` 调用（224）；[account_tasks.py](../../backend/app/tasks/account_tasks.py) 的 `_prepare_v2_removal`（231）与 `_delete_v2_children`（265）；`models/__init__.py`、`main.py` 和 `exam_service.py` 的装配/快照改动。
- 证据：旧导出和注销路径无条件访问新增表；ORM 注册和考试字段也已变化。即便教学/MCP 开关关闭，也不能保证这批代码可在 HEAD schema 上运行。
- 推断：只删除教学目录、不恢复调用点会产生 import/查询错误；直接拿工作区部署到未迁移库也有 schema 风险。反过来删迁移文件也不等于撤销已经落库的变更。
- 状态：调用关系已确认；本地/生产 `alembic_version`、新表数据、在途任务与外部凭据均未读取，不能宣称已经安全退回。
- 后续标准：代码清理、数据库保留/迁移、队列清理、凭据撤销分别记录。先恢复或替换所有消费者再删候选模块，不自动 downgrade/drop 表。

### REV07 · P2 · V2 完成度不能等同于完整老师与外部学习闭环

- 来源：未提交 V2。位置：[teaching_gateway.py](../../backend/app/services/teaching_gateway.py) 的 `_choose_intent`（76–172）、[teaching_runs.py](../../backend/app/services/teaching_runs.py) 的 `create`（78）和 `execute`（189）、`schemas/teaching.py`、`scripts/qualify_teaching_content.py`。
- 证据：模型只返回 `show_analysis / show_evidence / suggest_retry`；run 再投影已有卡片。揭晓前不执行该模型推理。当前创建 run 仅允许 user_ui；教学限定 reading，记忆尚无对应实现；内容发布要求真实核验收据，但 CLI 仍为只读资格盘点。
- 影响：这是一批边界/安全试做，尚未形成完整导师对话、稳定可用的教学内容和跨宿主接力。测试大多验证规则/替身，不能证明产品教学效果。
- 后续标准：先选一个真实材料学习任务定义输入、可见上下文、输出质量和写回规则，再决定是否采用试做中的确定性判分、披露和幂等思路。完整老师需要单独的任务对话、持久消息与质量评估设计，不把 intent 选择包装成已实现的自由教学。

## 3. 当前后端应怎样划清边界

以下登记优先审清的调用链；逻辑领域和目录规范只在 [目标框架](architecture.md) 维护。

| 用例 | 当前写入/事务拥有者 | 已知消费者 | 下一阶段要统一的边界 |
| --- | --- | --- | --- |
| 身份与账号 | auth/users、dependencies、security | HTTP、媒体/PDF、WebSocket；试做外部连接 | 第一方身份继续复用，外部凭据单独解析，最终共享账号有效性规则 |
| 收款与权益 | payments API helper 自行 commit；金数据 service 自行编排 | HTTP 回调、order/payment tasks、管理员 | 先决定金数据主路径与旧 provider 支路取舍；billing 认定付款，entitlement 拥有会员字段写入 |
| 视频入库/发布 | video 服务、任务、内部回调，提交点随用例不同 | 管理 API、catalog、云端/GPU/beat | 保留 head/GPU/tail 与 pipeline outbox；不重建另一套全局任务框架 |
| 字幕编辑/重分段 | subtitle_edit_service | videos API、修订/回退入口、词汇/收藏/笔记引用 | 按单条编辑、结构编辑、重分段映射拆职责；同一视频锁/回退快照仍整体拥有 |
| 词汇与复习 | vocabulary 路由和 vocabulary/study_session services | 词库/复习 HTTP、词集、档案聚合 | 复习算法/事实由词汇域拥有；事件和聚合不能各自认定一次复习 |
| 正式考试/听力 | exam_service 提交判分事务；listening 路由/服务另一约定 | 考试/听力 API、每日推荐、历史、导出 | 各模式用自己的冻结材料和结果；学习事件不能改成绩，教学辅助另存 |
| 通知 | notification_service flush、调用者 commit、API 模块推送 | HTTP、管线、提醒、账号导出 worker | 通知存储与派发分离，提交后推送，可靠投递按需持久化 |
| 档案/统计 | LearningEvent 写入、profile/overview/admin 等投影 | 首页/个人页/后台、推荐、提醒 | 定义必达事实和可重建读模型，保留用户本地日期口径 |
| 导出/注销 | account_data + account_tasks 跨表编排 | users API、导出 worker、注销 beat | 各域提供安全导出/清理能力，跨系统删除有意图与回执，不能直接依赖教学网页投影的全部实现 |
| 教学/运行/连接/记忆 | 目前仅有部分工作区试做 | 试做网页、MCP、teaching worker | 需求继续保留，正式契约重新审定；不直接把试做视作底座 |

体积只是定位入口：HEAD 的 video_processing 1538 行、subtitle_edit_service 1445 行、videos 路由 1210 行、home_content_generation 1144 行、home_content_service 1024 行。这些大文件早于本轮 V2。不能仅靠删除 V2 或按行数拆文件解决整体臃肿；应沿编排、纯规则、外部 I/O、持久化职责拆分，并保留事务完整性。

## 4. 工作区分组与可舍弃范围

以下是后续清理候选，不是已执行删除。清单按消费者依赖分组，不使用整仓 `reset --hard` / `clean -fd`。

| 组 | 范围 | 建议处置与前置 |
| --- | --- | --- |
| W01 V2 新模块 | 未跟踪 teaching/external API；integrations/mcp；question_exposure/teaching/v2_runtime 模型；teaching schema；teaching、run、gateway、access、connection/exposure services；teaching tasks；对应新增脚本/测试 | 允许舍弃；先完成 W02 恢复/替换、确认没有数据/凭据/外部消费者。判分、披露、幂等的设计价值可保留，不要求复制代码 |
| W02 V2 旧模块接线 | backend 的 19 个跟踪修改：.env.example；exams API；config/errors/main；models/__init__/exam_test；exam schema；account_data/admin_stats/daily_recommendation/event_contract/exam_service/learning_event/overview；account_tasks/celery_app；exams_api/exams_pg 测试 | 差异已对照，以 V2 快照、暴露、教学统计、运行和账号接线为主；按 hunk 成组恢复。不要只删 W01 留悬空 import，也不要仅恢复统计过滤留下教学事件 |
| W03 迁移 | 未跟踪 `c8d9e0f1a2b3`、`d9e0f1a2b3c4` 两个 revision | 先查各环境实际 revision、数据和已发布制品；未应用且无消费者才可随试做移除文件；已应用时保留迁移链或制定后续修正迁移，不自动删表 |
| W04 网关/部署试做 | deploy/v2-gateway 15 文件、独立 gateway compose；两份主 compose、两份 nginx、Redis ACL 模板/render 脚本差异 | 可替换；先核对 gateway/worker 是否实际运行、是否有已发 key 和未结算用量。不改现有云端/GPU 拓扑和无关运行服务 |
| W05 前端接线 | 7 个跟踪修改：考试作答/结果/practice 入口、ExamRunner、privacy、AccountLifecycleSettings、SettingsTab；10 个新增文件：ExamAnswerOptions、ExternalConnections、teaching 组件及 lib/types | 仅登记后端消费者，本轮未审查视觉或前端实现。清理时与 W01/W02 配对，尤其 ExamAnswerOptions 被已有 ExamRunner 引用，不能只删新增文件 |
| W06 V2 历史材料 | 3 个修改计划、3 个新增 V2 文档及 63 个 evidence 文件 | 只作为历史研究，不作当前完成度/验收依据；后续可随试做清理。本轮没有再次验证其网关/容量结论 |
| W07 本次后端蓝图 | refactor-blueprint 与根 CLAUDE 标准指针 | 保留本轮审查和标准；不是 V2 试做运行代码，不随 W01–W06 误删 |

忽略文件、环境配置、已有数据库、Docker volumes、媒体、线上/本地服务不在“舍弃工作区 V2 代码”的自动清理范围。当前没有做归档、git stash、恢复或删除，避免把尚未检查的内容混入清理范围。

## 5. 本轮验证记录

命令使用后端既有 `.venv/Scripts/python.exe`，设置 `PYTHONUTF8=1`。工作区测试使用仓库现有内存 SQLite + fake Redis + Celery 派发替身；HEAD 对照使用临时目录内相同配置和同一个解释器，没有连接业务数据库。

| 检查 | 实际结果 | 解释 |
| --- | --- | --- |
| 工作区 `python -m ruff check app/ tests/` | 已执行通过 | 未修改检查配置或基线 |
| 工作区快速回归 A | 98 passed，1 skipped，3 warnings | 架构、考试/快照、教学、run、V2 账号、overview、account_data；MCP 整个模块因 SDK 不在云端环境而 skipped |
| 工作区快速回归 B | 78 passed，7 warnings | payments、celery_tasks、notifications、vocabulary_mastered、listening_grading |
| HEAD 对照 | 30 passed，3 warnings | exams_api、user_overview、account_data；不是全后端套件 |
| HEAD 临时诊断复现 | 2 个问题复现成功 | REV01、REV03；测试断言描述当前错误行为，不计作业务验收通过 |
| 文档与改动范围 | 已执行通过 | 7 份文档、22 个相对链接有效；app Python 全部可解析；git diff --check 通过；业务差异统计与审查开始时一致 |
| PostgreSQL 并发/迁移 | 未执行 | 本机 Docker Linux engine pipe 不存在，未启动 Docker Desktop；未尝试使用业务 PG 代替隔离测试库 |
| mypy baseline、依赖/安全门、完整后端套件 | 未执行 | 本轮无业务代码改动，审查不宣称完整 CI 通过 |
| 真实支付、网关/四宿主、WebSocket/SSE 网络、生产 smoke | 未执行 | 模拟与静态审查无法替代实际端到端证据 |

已执行测试中的 warnings 是 structlog `format_exc_info` 提示；未为消除提示改配置。两批工作区回归合计 176 passed，另有 MCP module skipped；HEAD 的 30 项是对照重复样本，不加算为独立覆盖。没有以这些通过数字否定上述事务问题。

可复跑命令（工作目录 `backend/`）：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m ruff check app/ tests/
.venv/Scripts/python.exe -m pytest -m 'not integration' tests/test_architecture_invariants.py tests/test_exams_api.py tests/test_exam_snapshots.py tests/test_teaching.py tests/test_v2_runtime.py tests/test_v2_account_data.py tests/test_mcp_adapter.py tests/test_user_overview.py tests/test_account_data.py -q
# test_payments.py 已随收费链路下架删除；下面这条是还存在的部分（2026-11 复核）。
.venv/Scripts/python.exe -m pytest -m 'not integration' tests/test_celery_tasks.py tests/test_notifications.py tests/test_vocabulary_mastered.py tests/test_listening_grading.py -q
```

隔离复现的最小操作顺序：

1. 在系统临时目录解包指定 HEAD 的 backend，使用现有解释器和该副本的 conftest，不复制 .env、不指向业务 PG。
2. REV03：测试库创建用户并提交；替换 `_push_notification` 为捕获函数；调用 `create_notification`，记 ID；回滚；验证捕获到一次发送但库里没有该 ID。
3. REV01：测试库创建超过两小时的 pending 订单；替换 provider 为记录调用并返回 paid；依次执行 expire 和 reconcile；验证 expired、reconcile=0、provider 从未被查询。
4. 这两项只证明相应执行路径，不证明真实供应商/WebSocket 或 PostgreSQL 并发；正式修复时须新增“期望行为”回归，不能照抄错误行为断言当作验收。

## 6. 下一步的门槛

先补齐 B01：只读核对实际部署 commit、各环境迁移状态、工作区试做是否产生数据/凭据/任务、旧接口与脚本是否有真实消费者，并给 W01–W06 标记最终取舍。读取配置只取必要状态，不把凭据写入报告。

之后的首个实际切片优先处理支付结算/通知事务和反向依赖，或明确退役无需运营的旧支付支路；其后再整理词汇事实与档案、视频/字幕等存量大模块。教学、记忆与外部接入应基于稳定业务边界重新实施，不从继续堆叠试做代码开始。

当前停在审查阶段。B01 未完成的环境证据不伪造，B02 尚未实施，未因“可以舍弃 V2”而删除数据库或改动运行服务。
