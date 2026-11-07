# 后端重构实施记录

本页只登记实际落地的切片；整体目标、接口标准和 AC 定义分别引用其他文档。审查原始证据保留在[审查结论](review.md)，不把历史审查结论改写成当前代码。当前切片已提交在 HEAD（`2a07e571`），但不代表生产部署版本。

## B02.1 · 支付结算、通知事务与依赖方向

日期：2026-11-04。用户已授权开始重构。基于审查时 HEAD `e3f5ecba635ad93d3ab28f0230716010e4e7ebca` 和现有工作树实施；V2 试做仍待取舍（代码已入库，但未部署、未验收），本批没有新增教学、网关或前端能力，没有新增表、迁移、配置、依赖或部署改动。

### 最终行为与问题对应

| 审查项 | 本批行为 | 验证范围与局限 |
| --- | --- | --- |
| REV01 | 本地 expired 仍可由真实成功回调或供应商 paid 查询结算；cancelled 不发放，paid 重放不再续期 | 自动化替身验证迟到/金额不符/重复通知；未使用真实收款 |
| REV02 | 单笔结算在共享服务内重新锁定并刷新 Order→User；仅 flush，由入口提交。补单分页读取候选，关闭会话后查询供应商，再按单开启结算事务 | 真实 PG 验证同订单竞争只加一次、不同订单同用户准确累计；不再以批次持有的旧 ORM 对象结算 |
| REV03 | 创建/更新通知仅 flush；原提交点使用显式 commit_and_push，提交失败或回滚不推送 | 推送失败不影响已持久通知；实时推送仍为 best-effort，未增加可靠投递 outbox |
| REV05 | Celery 调用 order_service；通知传输归 notification_transport，HTTP 与 main 生命周期复用同一单例 | 新架构检查禁止 services/tasks（包括函数内 import）反向导入 app.api；旧通知 import 保留兼容导出 |

REV04（词汇事实与学习事件的可丢失窗口）、REV06（V2 表依赖及清理）、REV07（教学产品能力）未在本批解决。AC02、AC05、AC10 只有下列切片证据，均未宣布整项通过。

### 文件、消费者与事务拥有者

路径相对 `backend/`；已有 V2 修改没有整体恢复，尤其 `main.py` 与 `account_tasks.py` 只变更本批涉及的通知调用。

| 落点 | 职责与消费者 | 提交点 |
| --- | --- | --- |
| `app/services/order_service.py::settle_paid_order` | 支付回调、开发 mock 与补单共用结算；校验可付款状态与已知套餐，锁 Order 后锁 User，刷新 identity map | 不提交，仅 flush；订单和会员同一事务 |
| `app/api/v1/payments.py`、`mock_payments.py` | HTTP 适配；保留开关、验签、金额校验、响应及开发环境限制 | 回调/mock 显式 commit；开发 mock 仍只接受 pending |
| `app/services/order_service.py::reconcile_pending_orders` | 每页最多 100 个候选；查询期间无服务持有的数据库会话；单笔异常留待下轮，不撤销其他成功单 | 每笔重新取锁、验证状态、提交 |
| `app/tasks/order_tasks.py` | 保留原有两个 Celery 任务名、beat 调度及计数/异常返回约定 | 调用服务拥有的独立会话 |
| `app/services/notification_service.py` | 创建/去重更新、显式提交后推送；管理员通知及公告 | commit_and_push 是明确的应用提交边界，不是隐藏在 create_notification 内的提交；公告原有提交后派发保持不变 |
| `app/services/notification_transport.py` | WebSocket 连接单例、Redis 跨 worker Pub/Sub、启动/关闭订阅 | 不写业务表；不反向依赖路由 |
| `app/api/v1/notifications.py`、`app/main.py` | HTTP/WS 鉴权和生命周期；旧通知模块导出同一连接管理器与原有传输入口 | HTTP 与传输协议/认证语义不变 |
| `app/services/alert_service.py`、`app/tasks/reminder_tasks.py`、`account_tasks.py` | 管理员告警、复习/到期提醒、导出完成/失败通知；已核对全部生产 create_notification 调用点 | 在原 commit 点收集本次通知并 commit_and_push |

金数据沿用 `jinshuju_service.py` 的独立收款与发放流程，不把两套订单模型硬合并。公开 URL、DTO、错误 envelope、表名、GPU 任务及模型注册均未因本批变化。删除旧私有 `_process_successful_payment` 前已核对仓库调用者并全部迁到共享服务。

### 必要回归与实际检查

全部命令在 `backend/` 使用现有 `.venv/Scripts/python.exe`，设置 `PYTHONUTF8=1`。快速回归用既有 SQLite/fake Redis/派发替身；PG 验证使用本批创建的独立临时 PostgreSQL 16 容器与一次性数据库，不连接业务数据库。表结构由测试 fixture create/drop，不是 Alembic 迁移验证。

| 检查 | 结果 | 说明 |
| --- | --- | --- |
| 受影响回归 | 已执行通过：182 passed、13 warnings | 支付、订单任务、通知、提醒/告警、账号导出/注销、V2 账号、后台收款/金数据及已有架构检查；222.73 秒 |
| PG 结算/订单任务与新增依赖检查 | 已执行通过：7 passed、无 skip | 新结算 2 项、原订单任务 PG 4 项、反向依赖检查 1 项；39.47 秒 |
| ruff check / format --check | 已执行通过 | app/ tests/ 全目录；376 个 Python 文件格式符合要求 |
| mypy baseline | 已执行通过：无新增 file:code | 原始 mypy exit 1，有 56 条存量错误、36 组 file:code；按 CI 口径比较并将 Windows 路径分隔符标准化，无新增项；未改 baseline |
| pip-audit gate | 已执行通过：exit 0，无新增公告 | 首轮旧用户 pip cache 的 oss2 wheel 读取权限报错；仅换独立临时 PIP_CACHE_DIR 重跑成功。15 条旧接受项均已不再报出；未改 requirements 或豁免 |
| 文档与差异检查 | 已执行通过 | 8 份蓝图文档、32 个本地链接有效；app Python AST 可解析；git diff --check 通过 |
| 原有金数据 PG 扩展回归 | 已执行失败：60 秒超时 | 详细复核结果见下文；不计为通过，不放宽 timeout |
| 全后端套件与覆盖率、真实 Redis/WS、真实支付、迁移、生产 smoke | 未执行 | 本批不能视为完整 CI 或上线验收 |

已有 182 项回归中的 warnings 为 structlog 的 `format_exc_info` 提示；未修改配置消除提示。新增测试的前期 15 项快速验证是上述回归的重复样本，不另加算覆盖数。

可复跑命令：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m pytest -m 'not integration' tests/test_order_service.py tests/test_notification_transactions.py tests/test_payments.py tests/test_celery_tasks.py tests/test_notifications.py tests/test_quality_alert.py tests/test_alert_service.py tests/test_reminder_tasks.py tests/test_account_data.py tests/test_account_deletion.py tests/test_v2_account_data.py tests/test_architecture_invariants.py tests/test_admin_payments.py tests/test_jinshuju.py -q
# 只可指向一次性 PG 测试库；fixture 会重建整个 schema。
$env:PG_TEST_URL = '<一次性隔离测试库 URL>'
.venv/Scripts/python.exe -m pytest tests/test_order_settlement_pg.py tests/test_celery_tasks_pg.py tests/test_architecture_invariants.py::test_services_and_tasks_do_not_import_http_adapters -q -rs
.venv/Scripts/python.exe -m ruff check app/ tests/
.venv/Scripts/python.exe -m ruff format --check app/ tests/
.venv/Scripts/python.exe -m mypy app/ --ignore-missing-imports
# mypy 需按 .github/workflows/ci.yml 的 file:code baseline 比较，不能将原始 exit 1 当作通过。
.venv/Scripts/python.exe scripts/pip_audit_gate.py
```

新增依赖检查在 182 项回归之后补入，所以上面快速回归命令当前会收集 183 项，其中 1 项与随后 PG 命令中的静态检查重复。mypy 的原始输出和 baseline 必须一起评估。

金数据 PG 复核：同测的结算/订单测试已独立复跑通过。`test_jinshuju_pg_concurrency.py` 单独复跑仍在首项测试通过断言后的 fixture `Base.metadata.drop_all` 阶段触发原有 60 秒门，未达到整模块通过。随后用 HEAD 临时副本、同一解释器和另建的全新一次性 PG 数据库对照，同样在首项通过断言后的 fixture 清理阶段超时、exit 1，确认当前环境下 HEAD 基线也能复现。不能由此断言所有环境/CI 都失败，也没有降低轮数或放宽超时掩盖它。

HEAD 对照第一次误用了工作区测试残留 schema，在 setup 遇到 V2 外键依赖而 exit 1；该次不构成有效基线对照。之后重新建立独立空库才得到上述有效的超时证据。本批未修改该测试、conftest 或金数据服务；完整清理耗时和 Windows 异步测试环境仍待单独排查。

测试结束已删除本批临时 PG 容器及其 tmpfs 数据，并将为测试启动的 Docker Desktop 停回原始关闭状态；未修改已有网关容器定义或数据卷。尝试下载的临时 PG 压缩包残片也已移除。

### 回退与剩余边界

- 本批无数据迁移，不需要 downgrade。回退须成组恢复上述支付/通知服务、路由、main 生命周期与调用者；有原 V2 差异的文件按 hunk 恢复，不能整文件覆盖或 reset 工作区。
- 回退前保留已发放会员/已支付状态；绝不能把 paid 改回 pending 重放。回退代码会恢复旧实现的漏补单、批次锁和提前推送风险，应在隔离验证后决定是否暂停旧支付入口/补单。
- 旧 Order 不记录 provider，query_order 只返回状态，补单仍依赖当前配置供应商；本批不能证明供应商切换后的归属、金额凭证、退款、历史余额或真实对账正确。正式收费前先补来源与支付凭证契约，或者明确退役该支路。
- 本地过期订单会继续被补单查询；分页限制单批内存，不限制全部历史查询总量。需要按真实订单量评估供应商 QPS、保留窗口与调度策略，不能擅自裁掉可能已付款的历史记录。
- 通知提交后进程退出仍可能丢实时提醒，REST 中已提交数据保留；需要可靠送达的业务另做持久意图，不把实时 Pub/Sub 当可靠队列。提醒的既有 Redis 日配额与数据库提交仍非原子，本批不承诺消除所有漏提醒。
- B01 的部署版本、真实消费者、迁移状态与 V2 数据/凭据尚未核对。原试做没有继续堆叠，也没有被误记为本批产物；清理前按[工作区分组](review.md)成组处理。

B02.1 交付后的首个后续切片为下文 B02.2。全局迁目录、重做教学和上线均未在本批完成。

## B02.2 · 词汇进度与学习事实原子提交

日期：2026-11-04。承接持续重构目标。产品要求是一次成功作答能同时恢复词汇进度、训练轮次和对应学习记录；数据库或必要投影写入失败时，不能返回已保存的假象。对应 REV04，以及 AC02、AC03、AC05 的部分证据。没有新增表、迁移、队列、依赖、前端或部署改动，原 V2 接线仍待取舍。

### 变化与消费者

| 用例/落点（相对 backend/） | 最终行为 | 事务拥有者 |
| --- | --- | --- |
| `services/learning_event_service.py` | 抽出严格的 record_event，写事件、每日计数、连续学习和快照；不提交、不吞异常。旧 emit_event 复用它并保留 savepoint 容错；未知类型、已退役类型及教学专用入口的限制不放宽 | 调用用例 |
| `services/vocabulary_service.py` / `api/v1/vocabulary.py` | 复习和一键掌握下沉为应用服务；按用户范围锁定并刷新词汇，再记录必达事实。重复掌握不重复计数，未拥有的词仍返回 404 | HTTP 一次 commit；下层只 flush |
| `services/study_session_service.py::submit_answer` | 轮次、item、词汇及该词首次作答事件一起提交；重复答同词继续计算连对，但学习词数仍只计一次。先锁轮次再锁词汇，结束轮次共用轮次锁 | 保留服务作为完整用例的提交点，去掉第二次 commit |
| `services/practice_service.py::submit_practice_results` | 批次内已有词按 ID 顺序取锁；所有词汇变化、答对计数及 practiced_items/learned_words 事件一起提交。移除事后二次查询并补写答对计数的循环，修复同词在一次批次跨状态后漏计答对的问题 | 保留服务提交点，改为一次 commit |
| `services/vocab_set_service.py` | 过筛/标记已学/取消掌握先锁词集再锁词汇。词集首次闭环事件失败会向上抛出，禁止静默丢失。SQL 只查该词集的历史完成事实，兼容缺少 flow_id 的旧 metadata | 保留 vocab_sets HTTP 提交点；服务只 flush |

复习间隔、错词阶梯、质量阈值、题面与成绩、学习日时区、事件类型/版本/source 及公开 DTO 保持原口径。未把练习端客户端 correct 升格为正式服务端考试成绩。

### 验证与局限

新增 `tests/test_vocabulary_transactions.py`：调用者回滚、必要投影失败、HTTP commit 失败均不能留下局部成功；批次第二条事件失败回滚整批（含自动新增词）；重复掌握/越权/旧事件兼容、旧 emitter 失败不影响独立业务写入均有断言。新增 PG 文件使用独立一次性 PostgreSQL 16 数据库，验证真实锁与事务，不能用 SQLite 结果代替。

| 检查 | 实际结果 | 说明 |
| --- | --- | --- |
| 词汇/轮次/词集/学习周统计/退役事件原有回归 | 已执行通过：85 passed，146.20 秒 | 首轮验证；词集 SQL 查重优化之后又纳入扩展回归 |
| 新增故障与事务回归 | 已执行通过：16 passed、2 warnings，15.71 秒 | warnings 为既有 structlog 异常格式提示；本轮不修改检查配置 |
| PostgreSQL 并发与回滚 | 已执行通过：7 passed、无 skip，46.97 秒 | 同词并发掌握；同轮同词/不同词；同词集同词/不同词收尾；反序重叠批次；词汇与事件共同回滚 |
| 扩展回归 | 已执行通过：185 passed、2 warnings，257.55 秒 | 档案、学习/继续学习、行为摄入、本地时区、快照、听力判分、考试 API/快照、架构、最终词集 SQL 与新增事务测试 |
| ruff check / format --check | 已执行通过 | app/ tests/ 全目录；378 个 Python 文件格式符合要求 |
| mypy baseline | 已执行通过：无新增 file:code | 原始 exit 1，56 条存量错误、36 组 file:code；按 CI 口径标准化 Windows 路径后比较，未改 baseline |
| 文档与差异检查 | 已执行通过 | 8 份蓝图文档、31 个本地链接有效；app/test Python AST 可解析；git diff --check 通过 |
| 安全依赖门、完整后端套件/覆盖率 | 未执行 | 依赖与豁免未变；B02.1 的安全门证据保留，不将前一轮结果冒充本轮重跑 |

上述数量包含重复运行，不能直接相加：85 项与 185 项共享 32 项词集测试，独立的 16 项故障测试已全部纳入 185 项；共 238 项不同的快速回归与 7 项 PG 验证。临时 PG 容器及 tmpfs 数据已移除，Docker Desktop 已停回测试前的关闭状态，已有网关定义和数据卷未修改。

可复跑命令（工作目录 backend/，解释器、UTF-8 与安全要求沿用仓库规则）：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m pytest tests/test_vocabulary_mastered.py tests/test_vocabulary_quiz.py tests/test_study_sessions.py tests/test_vocab_sets.py tests/test_learning_weekly_stats.py tests/test_retired_learning_events.py -q
.venv/Scripts/python.exe -m pytest tests/test_vocabulary_transactions.py -q
.venv/Scripts/python.exe -m pytest tests/test_profile.py tests/test_learning.py tests/test_learning_continue.py tests/test_behavior_api.py tests/test_local_time.py tests/test_milestone_service.py tests/test_listening_grading.py tests/test_exams_api.py tests/test_exam_snapshots.py tests/test_architecture_invariants.py tests/test_vocab_sets.py tests/test_vocabulary_transactions.py -q -m 'not integration'
# 只可指向一次性 PG 测试库；fixture 会重建整个 schema。
$env:PG_TEST_URL = '<一次性隔离测试库 URL>'
.venv/Scripts/python.exe -m pytest tests/test_vocabulary_transactions_pg.py -q -rs
```

回退无需 downgrade；词汇路由、四个词汇业务服务和学习事件写入口须成组恢复，保留原 V2 差异。回退代码会恢复丢失学习事件的窗口，不能删学习记录或手动回滚用户已完成的复习来“匹配”旧代码。

### 下一步与未完成项

- 本批采用业务事实及必要投影同事务的方式；必要写入失败会使这次学习保存失败。当前投影都在同一业务数据库内，没有引入新补偿队列。若将来异步化投影，需要与事实同事务写入持久派发意图并证明可重建，不能恢复静默吞错。
- 锁与首次转换去重不等于请求级幂等。复习/批量练习没有独立请求回执；相同 payload 的重传与真实第二次作答目前无法区分。后续明确 operation_id 与异请求冲突契约后再迁移，不能按 payload 哈希误删用户的真实复习。
- 同时创建一个此前不存在的 Vocabulary 仍可能竞争唯一约束，失败事务需要重试；本批证明了已有词的重叠批次，不宣称所有词汇消费者、删除/导入或新建竞争已完成治理。
- B02.2 交付时，考试与听力仍调用旧 emit_event，即使业务成绩已成功也可能缺少派生学习记录；后续迁移与验证见下文 B02.3。视频行为摄入继续沿用 best-effort，不全局替换 emitter。
- 全后端套件/覆盖率、完整迁移、真实端到端与生产验证未执行。B01、B02、真实上线与盈利目标均未宣布完成，长期重构目标保持进行中。

## B02.3 · 考试/听力交卷、学习事实与重放

日期：2026-11-04。产品要求是交卷成功后成绩、学习事实和相应披露一起持久化；失败保留可重试状态，响应丢失后的重传回到同一个结果。对应 AC02–AC05 的局部证据。本批没有新增表、迁移、依赖、队列、前端或部署改动，也没有把原 V2 接线整体恢复或扩建。

### 边界与最终行为

| 落点（相对 backend/） | 最终职责与行为 | 提交点 |
| --- | --- | --- |
| `services/exam_service.py::submit_answers` | 保留条件 UPDATE 认领交卷、冻结题面判分和首次结果重放；将认领本身也纳入错误回滚范围。严格写入 practiced_items，失败回滚认领、答案、成绩和曝光 | 服务拥有一次 commit，失败 rollback |
| `services/listening_service.py::save/submit` | 改为接受 session_id/user_id，由服务校验本人、取锁并刷新 identity map；不再要求 HTTP 调用者先锁 ORM 对象。草稿合并、交卷后的 409、判分与重放共用状态机 | 服务只 flush，听力 HTTP 一次 commit |
| `services/listening_service.py::start` | 账号串行锁改用 PG FOR NO KEY UPDATE，与学习事件外键所需 KEY SHARE 兼容；仅查/锁最新一条待完成会话并刷新。等待交卷完成后不删除已提交历史，另建新的待作答会话 | 保留听力 HTTP 提交点 |
| `services/listening_service.py` / `api/v1/listening.py` | 题数与答案长度上限由服务常量拥有，API schema 引用；服务自身也限制题数、题目归属、索引和长度，其他适配器不能绕过 | 校验失败不写入草稿或成绩 |

全部仓库消费者已核对并迁移：听力 save/submit 的原调用者仅在 listening HTTP 模块；GET 详情继续使用只读 owned_session。公开 URL、响应形状、200/404/409/422 语义、听写归一化算法、正式成绩与辅助教学的区分均保持不变。考试使用原有服务提交拥有者，不在此批顺便改变所有服务的事务约定。

重放的定义仍为“首个成功交卷结果优先”：考试并发的不同答案不会覆盖首次成绩，听力交卷后不能修改草稿；同一会话的重试不重新判分、不追加学习事件。新严格事件写入失败会使本次交卷失败，不把未保存完整的结果返回为成功。

### 实际验证

| 检查 | 实际结果 | 范围与局限 |
| --- | --- | --- |
| 考试/听力正常回归 | 已执行通过：60 passed，44.57 秒 | listening_api、listening_grading、exams_api、exam_snapshots |
| 扩展回归 | 已执行通过：101 passed、11 warnings，99.22 秒 | 当时新增的 12 项事务测试、词汇事务、学习/档案、导出、V2 导出、推荐索引、overview、架构 |
| 最终听力边界与故障回归 | 已执行通过：30 passed、6 warnings，26.30 秒 | listening_api 11 项 + assessment_transactions 最终 19 项（含新加的 7 项服务输入边界）；部分与上两行重复 |
| PostgreSQL 并发 | 已执行通过：13 passed、无 skip，69.39 秒 | 新听力 7 项 + 原考试 PG 6 项；独立一次性 PostgreSQL 16 库，不使用业务数据库 |
| mypy baseline | 已执行通过：无新增 file:code | 原始 exit 1，56 条存量错误、36 组 file:code；标准化 Windows 路径后按 CI 比较，未改 baseline |
| ruff check / format --check | 已执行通过 | app/ tests/ 全目录；380 个 Python 文件格式符合要求 |
| 文档与差异检查 | 已执行通过 | 8 份蓝图文档、31 个本地链接有效；app/test Python AST 可解析；git diff --check 通过 |
| 依赖/安全门、全后端套件/覆盖率、迁移与真实端到端 | 未执行 | requirements/豁免不变，不把前几批结果冒充本轮重跑或上线验收 |

正常/扩展/最终回归去重后为 168 项快速测试，另有 13 项 PG；单独运行的首轮 12 项故障测试均已包含，不另加算。warnings 仍为 structlog 异常格式提示。第一次扩展回归命令误写不存在的 test_daily_recommendation.py，收集 0 项失败，修正为实际 test_daily_recommendation_index.py 后取得上表结果；该失败命令不计为通过。

故障测试覆盖考试与听力的必要投影失败、commit 前失败、数据库已经提交但响应确认丢失、重试及再次重试；考试三个模式另有失败后认领/成绩/曝光回滚验证。PG 听力覆盖两个旧 identity map 同时交卷、两个不重叠草稿合并、先存后交/先交后存、重开或恢复等待交卷、双标签开始同一会话。重开竞争通过实际 SQL 完成账号取锁的事件控制交错，不用 SQLite 或随意延时推断行锁行为。

类型门首轮暴露了新声明的 ListeningSession 返回类型依赖未标注 owned_session 所产生的 no-any-return；已补齐真实返回类型并重跑完整 app baseline 门，无新增错误，未添加 ignore 或放宽检查器。

可复跑命令（工作目录 backend/）：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m pytest tests/test_listening_api.py tests/test_listening_grading.py tests/test_exams_api.py tests/test_exam_snapshots.py -q
.venv/Scripts/python.exe -m pytest tests/test_assessment_transactions.py tests/test_vocabulary_transactions.py tests/test_learning.py tests/test_profile.py tests/test_account_data.py tests/test_v2_account_data.py tests/test_daily_recommendation_index.py tests/test_user_overview.py tests/test_architecture_invariants.py -q -m 'not integration'
# 上一条命令当前多收集最终追加的 7 项输入边界测试，不是历史的 101 项。
.venv/Scripts/python.exe -m pytest tests/test_listening_api.py tests/test_assessment_transactions.py -q
$env:PG_TEST_URL = '<一次性隔离测试库 URL；fixture 将重建整个 schema>'
.venv/Scripts/python.exe -m pytest tests/test_listening_pg.py tests/test_exams_pg.py -q -rs
```

测试用的临时 PG 容器及 tmpfs 数据已移除，Docker Desktop 已恢复测试前的关闭状态；未更改已有网关容器定义、数据卷或业务数据库。回退无需 downgrade；听力服务与路由的新内部调用签名须成组回退；exam_service 只回退本批 hunk，保留已有 V2 差异。回退代码会重新引入可丢失学习事实的契约，不能通过删成绩或事件“回退”用户事实。

### 剩余范围

- 未回填历史上已交卷却缺失学习事件的记录；重试不会把缺失的历史事件按今天重新记账。历史修复需要单独确认原学习日期、已有重复事件与对账证据。
- 学习事实和必要投影仍为同库事务；投影故障会使交卷保存失败。异步化时必须有持久意图与可重建证据，不重新采用静默丢失。
- 草稿合并支持不相交题目的并发写；同题并发修改仍为锁顺序下的后写优先，没有引入 revision/expected_version 或编辑冲突 UI。
- 账号注销/撤权、视频下架、跨模式统计语义和完整生产链仍需整体审查；本批锁测试不代表所有生命周期交错都已验证。
- 下一切片 B02.4 转向视频/字幕大模块：先审清消费者、事务和重试，再拆分编排、外部 I/O 与规则。词汇请求幂等、新词创建竞争、B01 环境证据及全量门仍保留，不将切片完成当成整个重构完成。

## B02.4 · 媒体 I/O 与字幕规则分离

日期：2026-11-04。已核对任务、回调、派发 outbox、维护脚本和字幕替换的消费者。此批整理存量大模块，不建设新队列或通用工作流，不新增表/迁移/依赖，不改 GPU worker、任务名、URL 或部署配置。对应 AC02、AC04、AC05 的部分回归证据，不构成完整管线验收。

### 归属与行为

| 落点（相对 backend/） | 本批职责与变化 |
| --- | --- |
| `services/video_media.py` | 从 video_processing 提取源信息、原文件定位、上传暂存/清理、yt-dlp 下载、ffmpeg 转码和 ffprobe。拥有文件/进程 I/O，不拥有业务事务或派发。转码自行创建输出目录 |
| `tasks/video_processing.py` | 保留 head/tail、状态提交、质量门、发布、重试和 watchdog；已使用的旧私有 helper import 保留兼容别名，既有调用/测试仍能接入。主文件 1538→1199 行 |
| `scripts/rebackfill_video_quality.py` | 已知维护消费者改从媒体服务导入 download_video；仅修改 import/调用名，没有执行脚本或访问生产 |
| `services/subtitle_resegment_rules.py` | 提取纯分段、时间映射、收藏去重计划、计数和 v1/v2 快照兼容；不读取数据库、提交、删除或清缓存 |
| `services/subtitle_edit_service.py` | 保留字幕 CRUD/审计、用户数据捕获、数据库替换/恢复和原提交点，旧规则 helper 保留兼容别名。主文件 1445→1225 行 |

两个原主文件合计减少 559 行，代码迁入单一职责模块；不是宣称全项目总代码减少 559 行。媒体文档指针同步到 external_meta；没有复制第三套分段算法，仍调用既有 subtitle_segmentation，GPU 格式化规则未修改。

新增两个必要行为修复：

1. 媒体子进程 communicate 被取消或异常中断时，先终止并排空管道/回收进程，再传播原取消；此前只取消 Python 等待不会停止 ffmpeg/ffprobe。没有为 yt-dlp 执行线程承诺同样的即时取消，也没有调整任务/检查超时。
2. 同一视频混合“带逐词时间戳”和“无逐词时间戳”的字幕时，旧重断句只采集前者，遗漏手工/旧字幕。新规则保留未对齐文本，并仅在其原句时间范围估算用于切分的内部时间；含估算词的结果不发布伪造的逐词对齐，纯真实对齐的段保持原词时间。原全无时间戳的历史算法与快照版本保持不变。

### 实际验证

| 检查 | 实际结果 | 范围与局限 |
| --- | --- | --- |
| 原管线/字幕回归 | 已执行通过：117 passed、10 warnings，94.45 秒 | 恢复、锁 TTL、watchdog、步骤、转录回调、持久派发、下载重试、翻译质量、字幕重断句/拆合/审计/增删改 |
| 扩展与最终规则回归 | 已执行通过：132 passed、4 warnings，84.88 秒 | 后台字幕管线、待处理入口、架构、质量安全、外部元信息/语速、封面、媒体服务、新混合字幕与重断句 |
| 媒体输出目录调整后复验 | 已执行通过：12 passed、1 warning，6.26 秒 | 复用上行 12 项媒体测试，不另计独立覆盖 |
| 真实 Windows 子进程取消 | 已执行通过 | 在独立 ping.exe 子进程上调用媒体 communicate，取消后验证已终止/回收且 CancelledError 继续传播；不是 ffmpeg 编码验收 |
| 提交/编排未漂移的源对照 | 已执行通过 | 对照 HEAD，剩余 21 个视频任务函数及 24 个字幕服务函数/类 AST 均未改变；只移动依赖实现，未改它们的事务/派发控制流 |
| mypy baseline | 已执行通过：无新增 file:code | 原始 exit 1，55 条存量错误、35 组 file:code；修复了原视频提取函数的返回类型，删除已消失的 video_processing:no-any-return 一项，基线 39→38；未增加接受项 |
| ruff check / format --check | 已执行通过 | app/ tests/ 与本批维护脚本，共 385 个 Python 文件格式符合要求；提取后残留的空段注释清理并格式化 |
| 文档与差异检查 | 已执行通过 | 8 份蓝图文档、31 个本地链接有效；app/test/本批脚本 AST 可解析；git diff --check 通过 |
| PG/迁移、真实 yt-dlp/OSS/GPU/ffmpeg、完整后端套件/覆盖率、依赖安全门 | 未执行 | 本批没有 SQL/锁/表结构变化，未启动 Docker；网络与进程替身不等于完整媒体交付，依赖与豁免未变 |

两批主要回归共享 12 项重断句用例，去重后为 237 项；单独的媒体/混合字幕测试运行均是其中的重复样本。warnings 仍为 structlog 格式提示。首轮新媒体测试把真实契约的 channel_name 误写成 external_channel_name，已按 parse_external_meta 的代码修正测试并复跑；没有修改业务字段迎合错误断言。

类型门在移动代码后暴露了原来留在 task 基线中的 Any 返回；通过标注同步提取/下载的真实返回类型修复，再降低原基线。backend/CLAUDE.md 不再复制易过期的基线数量，数量以基线文件为准，没有放宽检查或豁免。

可复跑命令（工作目录 backend/）：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m pytest tests/test_pipeline_resume.py tests/test_pipeline_lock_ttl.py tests/test_pipeline_watchdog.py tests/test_pipeline_steps.py tests/test_internal_callback.py tests/test_pipeline_dispatch.py tests/test_download_retry.py tests/test_translation_quality_block.py tests/test_subtitle_resegment.py tests/test_subtitle_split_merge.py tests/test_subtitle_revisions.py tests/test_subtitle_reorder_create_delete.py tests/test_subtitle_edit.py -q -m 'not integration'
.venv/Scripts/python.exe -m pytest tests/test_admin_subtitle_pipeline.py tests/test_pending_processing.py tests/test_architecture_invariants.py tests/test_quality_safety_net.py tests/test_external_meta_and_speech_metrics.py tests/test_thumbnail_service.py tests/test_video_media.py tests/test_subtitle_resegment.py tests/test_subtitle_resegment_mixed.py -q -m 'not integration'
.venv/Scripts/python.exe -m ruff check app/ tests/ scripts/rebackfill_video_quality.py
.venv/Scripts/python.exe -m ruff format --check app/ tests/ scripts/rebackfill_video_quality.py
```

无数据迁移，回退须成组恢复两个主模块、新服务模块、维护脚本 import 和元信息说明；回滚代码会重新带回混合字幕漏文本与未清理媒体进程的行为。对已生成的字幕/快照不自动回滚或删数据。

### B02.4 结束时的管线问题（历史交接）

- 当时 `_run_transcoding`、`_run_localize` 在空转码结果时使用猜测的本地 URL；这项与导入恢复时遗漏原文件的问题已由下方 B02.5 处理。B02.4 的模块提取本身不代表播放可用性验收。
- 字幕批量替换与其他编辑入口没有在本批统一加锁；保留原事务不等于已证明并发替换安全。派发竞争、回调/worker 过期写回、账号生命周期和真实运行证据仍需审查。
- 需要更细的切片继续降低两个主模块的职责混杂；目标模块化单体、B01 环境核查、其他未完成项和上线门均仍在范围内，长期目标保持进行中。

## B02.5 · 真实播放产物、共享发布门与本地化持久派发

日期：2026-11-04。本批接续 B02.4 的管线问题，消费者覆盖云端 tail、本地化任务、后台 PATCH/发布服务、已有派发补发与当前前端播放器。没有新表、迁移、队列、依赖或部署配置；没有改 GPU worker、任务名或公开响应 schema。对应 AC02、AC04、AC05 的部分证据，B02 整包仍未完成。

### 最终行为与归属

| 落点（相对 backend/） | 职责与变化 |
| --- | --- |
| `services/video_media.py` | 转码输出到本次调用独有的临时文件，返回码成功、文件非空且 ffprobe 能探测视频流后才原子替换正式文件；失败或取消清临时文件，保留旧产物。媒体路径必须留在配置根目录内；ffprobe 等待上限 15 秒，超时终止并回收子进程 |
| `services/video_playback.py` | 唯一维护本地产物校验、当前播放器支持的 YouTube 嵌入来源、发布资格与本地化失败字段；不提交事务。本地 `/media/` 指针必须有实际视频流；新转码结果仅接受受支持分辨率和可信本地文件 |
| `tasks/video_processing.py` | 不再为下载/转码空结果编造 raw/mp4 URL。上传及不支持嵌入的导入必须有可播放产物；有效 YouTube 来源可保留嵌入回退并记录本地化失败。恢复时重新定位原文件，Redis 步骤标记不能替代实际产物，缺产物则重新执行。ready 前统一校验 |
| `services/video_publish.py`、`video_service.py` | 自动/人工发布与后台 PATCH 使用同一 ready + 播放资格门。本地化只认领 ready/error、imported、非 offline 视频，保留原播放指针；认领和 `LOCALIZE_VIDEO_TASK` 意图同事务提交，提交后尽力派发 |
| `services/pipeline_dispatch.py` | 本地化复用既有 outbox、补发和退避；只在 processing 状态发送本地化意图，状态不符则 abandoned。没有增加第二套任务系统，也没有改既有派发竞争算法 |
| `services/video_cache.py` | ready/新产物或保留回退的本地化状态提交后，使本视频详情和公共列表缓存失效。复用既有 best-effort 失效链，不修改其他视频详情缓存 |

兼容与操作语义：

- 仍使用既有 `/media/{id}_720p.mp4` 产物地址；不再把未经验证的原始文件当成最终 rendition。有效旧文件在失败重试后仍可播放。
- `download_failed_at` / `download_fail_count` 为保留的字段名，本批用于本地媒体准备失败（下载或转码）；成功后清零。ready 且缺 720p 的导入沿用既有有限次数 beat 重试，有旧有效 720p 的失败不因此自动重做；人工 force 可绕过次数上限。
- 当前前端 `useVideoPlayer.ts::youtubeId` 仅支持对应路径中的 11 字符 YouTube ID；Bilibili 等导入不能凭链接降级 ready。没有增加前端原型或宣称国内嵌入播放可用。
- 后台发布缺播放产物返回 400，非 ready 仍拒绝。后台本地化对 local/offline 返回 400，处理中或其他不允许状态返回 409，missing 返回 404。消费者为现有管理员页面及 API 调用者，无字段变化。
- 本地化 HTTP 200 表示已认领 processing，不能解释为已完成转码。broker 故障后保留 pending 意图，由既有 beat 补发；意图写入失败时认领一并回滚。已知媒体失败若仍有旧产物或支持的嵌入来源则保留 ready 并记录失败，否则进入原有 error/retry 路径。

### 实际验证

| 检查 | 实际结果 | 范围与局限 |
| --- | --- | --- |
| 最终相关快速回归 | 已执行通过：236 passed、16 warnings，189.09 秒 | 播放/媒体、恢复、锁、watchdog、回调、派发、后台字幕、播种、响应契约、架构及视频 API；包括新产物提交后的缓存失效断言。SQLite/fake Redis 不替代 PG 行锁证据 |
| 独立媒体/播放故障回归 | 已执行通过：41 passed、3 warnings，27.51 秒 | 含空产物、进程失败、不可探测输出、取消、路径越界、探测超时、重试保旧文件；最终命令涵盖同一批用例，不重复累计 |
| 隔离 PostgreSQL 本地化 | 已执行通过：3 passed、1 warning，16.90 秒 | HTTP 并发认领只产生一次派发、意图失败回滚、晚到意图遇 ready_subtitles 放弃；真实 PG 16，独立 tmpfs 数据，不使用业务数据库 |
| 真实 FFmpeg/ffprobe | 已执行通过 | 缓存后端镜像内真实运行：720p remux、1080p→720p scale，输出非空且可探测；坏输入返回空结果，旧文件字节不变、无临时产物。只读挂载当前代码，禁网，不挂业务媒体或 .env |
| ruff check / format --check | 已执行通过 | app/、tests/ 与新媒体检查脚本，388 个文件格式符合要求 |
| mypy baseline | 已执行通过：无新增 file:code | 原始 exit 1，55 条存量错误、35 组 file:code，基线未变；不是无错检查通过 |
| 文档与差异检查 | 已执行通过 | 8 份蓝图、32 个本地链接有效；app/tests/新检查脚本 AST 可解析；git diff --check 通过 |
| 全量后端/覆盖率、依赖安全门、真实 yt-dlp/OSS/GPU/CDN、生产发布 | 未执行 | 依赖与安全豁免未改；不把脚本或 mock 结果当成完整媒体上线证据 |

本批去重后为 236 项快速回归，另有 3 项 PG；41 项独立媒体/播放回归和更早的 85 项回归均被最终命令涵盖，不叠加计数。先前 235 项扩展命令的最终终端输出未取回，确认该进程已退出后才执行本表 236 项最终回归，不将未确认的旧运行另记为通过。

新增 `tests/test_video_playback.py`、`test_video_localization_pg.py`；扩充媒体测试。首次旧回归 7 项失败源于不受支持的假 YouTube URL、旧直接 delay 的断言及旧状态 SQL 形状，已按实际消费者契约修正 fixture/预期并复验；没有删除功能断言或放宽检查器。状态门断言改为检查允许状态的 IN 条件，避免误把 storage_mode 的不等条件识别为状态保护。warnings 为既有 structlog 格式提示。

可复跑命令（工作目录 backend/）：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m pytest tests/test_video_playback.py tests/test_video_media.py tests/test_download_retry.py tests/test_pipeline_resume.py tests/test_pipeline_steps.py tests/test_pipeline_lock_ttl.py tests/test_pipeline_watchdog.py tests/test_internal_callback.py tests/test_pipeline_dispatch.py tests/test_admin_subtitle_pipeline.py tests/test_seed_full.py tests/test_response_contract.py tests/test_architecture_invariants.py tests/test_videos.py -q -m 'not integration'
$env:PG_TEST_URL = '<一次性隔离测试库 URL；fixture 将重建整个 schema>'
.venv/Scripts/python.exe -m pytest tests/test_video_localization_pg.py -q -rs
# 具有 ffmpeg/ffprobe 的隔离环境；使用 testing 配置时还需有效测试 JWT_SECRET 和 DATABASE_URL。
.venv/Scripts/python.exe scripts/check_video_media.py
.venv/Scripts/python.exe -m ruff check app/ tests/ scripts/check_video_media.py
.venv/Scripts/python.exe -m ruff format --check app/ tests/ scripts/check_video_media.py
```

真实媒体检查代码见 [check_video_media.py](../../backend/scripts/check_video_media.py)。本机没有 PATH ffmpeg，实际使用已有 `speaking-backend:latest` 镜像执行该脚本（不是新构建镜像）；测试 ENV 导入仍遵循原配置校验，使用内存 SQLite 哨兵 URL，不连接数据库。临时 PG 容器、媒体测试容器及临时文件均已移除，Docker Desktop 已恢复测试前的关闭状态；已有网关容器定义/卷未修改。

### 局限、回退与下一切片

- 配置为 HTTP(S) 的远程 rendition 仅验证 URL 有主机名，没有联网验证 CDN 可达性；YouTube 来源支持仅与播放器语法匹配，不证明地区可达、内容授权或能完成解码。现有 ready/published 历史数据未全量扫描修复。
- 文件通过当前探测并不保证未来不会被删除或替换；本批不提供跨文件系统/数据库事务。旧产物被替换后不自动留历史副本。yt-dlp 线程取消、完整转码超时和资源上限仍需后续治理。
- 已有 Redis 锁没有 worker 代次 fencing；outbox 补发可能重复，状态门不能阻止所有新旧流水线交错。同视频过期 worker、派发并发和字幕替换/编辑互斥尚未完整验证，不宣称 exactly-once。
- 回退无需 downgrade；应成组回退播放服务消费者、媒体写入、任务与本地化 outbox 接线，保留已经生成的文件和派发行。若恢复到不认识本地化意图的旧代码，须先排空/处置此任务名的 pending 意图，不能只回退 HTTP 入口；不要删用户事实或业务媒体。回退会重新带入猜测 URL 与直接派发丢任务风险。
- 下一切片 B02.6 先审查上述锁/派发/字幕写入的具体交错并选定可验证范围。B01 环境、词汇请求幂等/新词竞争、V2 取舍及全量上线门继续保留，整体重构仍进行中，未部署。

## 2026-11-05 · 按 V2 设计校正实施主线

用户暂停持续执行后补充“按 v2 的设计”。本轮核对本机 V2.0 产品原稿、仓库技术设计和方向对齐文档，以及当前 reading 题面 schema、内容资格门、run 创建和模型 intent 实现；仅调整蓝图，不修改业务代码、迁移或运行服务。此前 B02.1–B02.5 的代码与验证保留，不能因此认定 V2 教学能力已完成。

目标依据和 V201–V207 仅维护在[目标框架 §0](architecture.md)，顺序仅维护在[当前实施主线](execution.md)。原 B02.6“下一切片”的顺序被本次校正取代：恢复后从 P01 可信材料与共同学习内核开始，旧派发/字幕风险保留并按依赖处理。补齐 AC14 的完整学习接力与 AC15 的多语境/逐次复习证据，显式保留 V2 的 FSRS 目标与算法分歧处理，未切换算法。

本轮文档检查已执行通过：8 份蓝图、41 个本地链接有效；V201–V207、P01–P06、AC01–AC15 编号齐全，旧的整包前置依赖已移除。业务测试、模型/宿主调用、迁移和部署均未执行，不复用历史测试数字作为本轮通过。持续执行保持暂停。

## P01.1 · 共同学习上下文 v1 与单题恢复

日期：2026-11-05。用户已恢复持续执行，本批推进 V201–V202 的内容/学习内核，并为 V203/V206 提供统一输入。实现范围为已有阅读单题，既有教学状态机继续使用；没有实施新数据表、迁移、独立前端或生产发布。新增上下文是已实现接口，其余 V2 目标仍按实际证据逐项推进。

### 当前契约与取舍

| 当前落点 | V2 要求 | 本批决定与边界 |
| --- | --- | --- |
| `teaching/content.py` 的 revision、来源指纹与权利投影 | 可信材料、版本和三档披露 | 复用现有结构与 fail-closed 发布门，未声称真实内容已完成核验。authenticated receipt verifier 的正式接线仍缺失，CLI 不会因 manifest 字段完整就发布 |
| `teaching/service.py` 的初答/复答、提示、揭晓、草稿、幂等和 outbox | 同一学习任务可恢复，正式成绩与辅助学习分开 | 保留已验证的确定性写入，不调用旧整卷提交，也不新增另一套答题状态机；合成旅程与原 PG 并发用例复验 |
| 网页 `get_session`、模型临时 cards dict、MCP 各自拼接 | 服务端构造最小、版本化的共同上下文 | 新建 `schemas/learning_context.py` 与 `teaching/context.py`，复用服务的内容/答案披露规则；运行时改用 v1，HTTP/MCP 新增同名能力 |
| 无正式 memory/多材料适配/持久对话 | V2.1 学习资产与完整导师 | 本批不填造假的空数据，不把三选一 intent 讲解当成完整老师；仍在后续范围 |

### 产物、消费者与事务

- 新增 HTTP `GET /api/v1/teaching/sessions/{session_id}/context` 与 MCP `get_learning_context(session_id)`；schema/语义统一见[CTX02](contracts.md)，不在此复制字段规则。现有 SessionResponse、任务名和写 API 均保留，HTTP 新接口禁止缓存。
- 新上下文通过已有 `project_session` 做内容与答案披露；新增可选近期作答查询限制，旧 session detail 默认仍返回原历史。共享 audience/答案历史规则，不另建第二套投影政策。MCP 列表与新上下文共用恢复地址构造函数。
- 平台 `teaching_runs.execute` 的初始模型输入和真正请求前重检都使用同一上下文服务。before_dispatch 事务退出后才执行模型网络 I/O，继续沿用原 lease/取消/预算边界；没有因此开放外部托管 run。
- 上下文是只读服务，调用者拥有 commit/rollback。PG 共享锁固定本任务 state_version 和内容权利，两个读取互不阻塞；写操作必须等待投影事务结束。外部工具仍逐调用认证并锁连接，撤权后新上下文调用同样失效。
- 不改变已经部署的 schema；候选 V2 表是否已在各环境应用仍需 B01 核验。无新依赖、开关、额外成本账本、模型调用或真实素材写入。

### 实际验证

| 检查 | 实际结果 | 证据与局限 |
| --- | --- | --- |
| 最终相关快速回归 | 已执行通过：127 passed、3 warnings，59.50 秒 | 上下文、教学、运行时、网关替身、内容 CLI、考试快照、导出/注销、响应与架构；模型仍用替身，warnings 为既有 structlog 格式提示 |
| 新增上下文回归 | 已执行通过：11 passed，9.68 秒 | HTTP 初答→提示→复答→揭晓→独立会话恢复，草稿/任务隔离，近期作答截断，三档权利、只读 scope、当前动作、撤回后旧上下文无写权限及模型请求前重投影 |
| 隔离 PG 回归 | 已执行通过：6 passed，29.72 秒 | 3 项新增测试使用 pg_blocking_pids 观察实际等待：并发草稿不能混入旧版本、撤回等待已有投影完成、两个共享读取互不阻塞；另复验原 3 项教学并发（同幂等创建、旧版本双答、跨 session 初答资格） |
| 隔离 MCP SDK | 已执行通过：4 passed，5.03 秒，无 skipped | 真实已安装 SDK + ASGI 协议调用，两个协议形态分别测鉴权、上下文只读、辅助提交/恢复/重放/撤权；不是四宿主真实兼容，也不是生产依赖门通过 |
| ruff check / format --check | 已执行通过 | app/ tests/，391 个文件符合格式 |
| mypy baseline | 已执行通过：无新增 file:code | 原始 exit 1，55 条存量错误、35 组 file:code，237 个源文件；未扩大基线/豁免 |
| 文档与差异检查 | 已执行通过 | 8 份蓝图、43 个本地链接有效；app/tests AST 可解析；蓝图无行尾空白/冲突标记。本批代码在未跟踪的 V2 候选文件上继续修改，Python 格式以上方 ruff 门验证，不靠空 git diff 推断无改动 |
| 全量后端/覆盖率、安全/依赖门、真实网关/宿主、真实素材核验与部署 | 未执行 | 云端依赖集没有安装或升级 MCP SDK；合成原创材料不冒充真实考题或内容授权证据 |

本批去重后 127 项快速回归，另有 6 项 PG 与隔离 SDK 的 4 项协议测试；基础 38 项与单独 11 项上下文回归均被最终命令涵盖，不重复累计。

首轮基础 38 项通过，追加结束状态测试后的扩展出现 1 failed / 126 passed：新测试误将 item_id 传给不接受该字段的 CompleteSession。按现有 schema 修正测试输入后，新上下文 11 项全部通过，再执行最终扩展命令并全部通过；没有放宽 extra=forbid。MCP 首轮的新版协议测试缺少 SDK 要求的每请求 envelope；对照隔离 SDK 源码，补请求元数据/路由头、使用 discover 与其真实 camelCase 响应字段，并保留缺元数据拒绝的负控，最终两种形态全部通过。没有为测试改服务端协议校验。

可复跑命令（工作目录 backend/）：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m pytest tests/test_learning_context.py tests/test_teaching.py tests/test_v2_runtime.py tests/test_teaching_gateway.py tests/test_teaching_content_cli.py tests/test_exam_snapshots.py tests/test_v2_account_data.py tests/test_account_data.py tests/test_response_contract.py tests/test_architecture_invariants.py -q -m 'not integration'
$env:PG_TEST_URL = '<一次性隔离测试库 URL；fixture 将重建整个 schema>'
$env:DATABASE_URL = $env:PG_TEST_URL
.venv/Scripts/python.exe -m pytest tests/test_learning_context_pg.py tests/test_teaching_pg.py -q -rs
```

MCP 使用仓库已有 `backend/.venv/mcp-runtime/` 的隔离安装，需按其 Windows 运行约束将 runtime、win32、win32/lib、pywin32_system32 加入 PYTHONPATH 并把 pywin32_system32 加入 PATH，再执行 `python -m pytest tests/test_mcp_adapter.py -q -rs`。未修改该运行时或云端 requirements；这不是生产 SDK 选型结论。具体 SDK 版本/依赖兼容仍须锁版治理，不能因协议测试成功自动启用生产 MCP。

隔离 PG 使用本轮创建的带标签 tmpfs 容器与随机 loopback 端口，测试完已移除；Docker Desktop 已停回原来的关闭状态。没有操作业务数据库、媒体或已有网关容器定义/数据卷。

### 下一步和回退

- P01 未整体完成：真实核验素材、可信收据验证器与发布/撤回操作尚需补齐。下一切片先落实正式核验输入/发布流程、来源可用性与后台消费者，保留未通过者不发布的边界；不能为做演示绕过当前发布门。
- 当前 v1 只覆盖阅读单题，档案/记忆检索、判断/听力/视频/词汇适配和完整任务对话待实现；当前运行时仍是有限 intent 卡片。四宿主、外部托管、公开授权、算法决策、商业与上线证据均继续保留。
- 共享行锁只保护遵循当前事务边界的投影与写入，不赋予上下文永久一致性；下一次动作必须重新鉴权/查权限/校验版本。跨任务帮助记录改变不会自动推进本任务 revision，后续需为导师运行补更完整的上下文失效约定。
- 无数据库 downgrade。回退时先将模型运行时恢复到原上下文构造，再成组回退新增 API/MCP 工具、schema/context 模块及可选投影参数；已有教学任务、作答和曝光事实保留。新接口如已有消费者需保留过渡响应/版本，而不是直接删入口。整体目标保持进行中，未部署。

## P01.2 · 内容发布操作、审计与迁移演练

日期：2026-11-05。本批推进 V201/V202/V207，将原内部出版函数接成可由后台和服务器 CLI 调用的内容生命周期。没有调用真实模型、获取新素材授权或部署；正式核验收据验证器仍缺失，发布默认关闭。接口操作可运行与真实内容已验收分别记录，不以测试替身解锁正式发布。

### 归属、消费者与最终行为

| 落点（相对 backend/） | 职责与变化 |
| --- | --- |
| `models/content_publication.py`、`schemas/content_publication.py` | 内容候选草稿、版本、发布引用与管理员操作回执；外层请求禁止自填 actor/核验开关，manifest 限 128 KiB |
| `services/teaching/publication.py` | 草稿/摘要列表/预检、分离核验与写事务、发布、单版本撤回、幂等和操作查询。复用既有内容核验/披露，不复制教学状态机或成本账本 |
| `api/v1/admin_teaching_content.py` | 管理 API，当前管理员鉴权、限流、输入/响应和最终提交；发布读取事务先结束，再验证收据，写入时再次检查管理员状态 |
| `services/teaching/content.py` | 统一把畸形候选转为校验错误；发布要求当前题库锚点。题目和所属试卷取锁后重新比较来源，修正原先“先比较、后取锁”的竞争窗口 |
| `scripts/qualify_teaching_content.py` | inventory/check 继续只读；import 改用同一草稿/发布服务，新增管理员 actor 与批次 operation 参数，批次原子提交和内容绑定的重放，不直接写 revision |
| `app/main.py`、`models/__init__.py` | 仅追加管理路由与两个模型注册，保留已有 V2 试做装配和其余工作区差异 |
| `migrations/versions/e0f1a2b3c4d5_content_publication.py` | 在候选 d9e0f1a2b3c4 后追加两张表、唯一键、FK 与索引；只在一次性隔离库执行 |

具体 wire/状态契约统一见 [CTX08](contracts.md)，不在此复制字段。管理员详情/编辑、预检、发布和撤回均有 API 入口，但本次不设计前端页面。列表用摘要 join，不把完整 manifest 逐项载入列表。草稿不完整时可以保存，预检通过不代表真实收据已认证。

单次写事务按管理员共享锁→操作回执认领→目标草稿/内容取锁→来源复查→新 revision/状态→成功回执完成；HTTP 或 CLI 拥有最终提交。网络核验在事务外；核验期间草稿、题库或管理员授权变化会在实际写入时拒绝。回执包含操作者、动作、目标、请求摘要、结果引用及撤回原因，不是模型用量账本或全站不可篡改审计。

同操作重试不会创建第二个版本；同编号不同请求/批次内容冲突。草稿/版本/回执一起回滚，撤回不改变历史判分。旧发布/导入重放按当前状态返回 withdrawn，不复活已撤回内容。CLI 依赖服务器操作权限并校验所指管理员，不把 actor ID 当作外部认证。

### 实际验证

| 检查 | 实际结果 | 范围与局限 |
| --- | --- | --- |
| 最终相关快速回归 | 已执行通过：126 passed、1 warning，76.79 秒 | 管理发布 14 项、内容 CLI 5 项，及共享上下文、教学、run、V2 导出、响应契约、架构；warning 为既有 structlog 格式提示 |
| 隔离 PG 并发 | 已执行通过：9 passed，48.19 秒，无 skipped | 6 项发布用例：同操作/异操作双击、两个草稿 revision 编号、核验期间修改草稿、取锁前题库修改、核验期间管理员降权；另复验 3 项上下文锁用例 |
| 全新 PG 迁移链 | 已执行通过 | 当前仓库 initial→e0f1a2b3c4d5 在独立空数据库完整 upgrade head；不是 metadata.create_all 代替迁移，也不代表生产 schema 已核对 |
| 新表 schema 与 ORM | 已执行通过 | 对照列集合、PostgreSQL 方言类型/时区、nullable、FK/ondelete、唯一键、索引；在真实迁移生成的库执行最终管理员草稿/回执写入 |
| 隔离回退与重升 | 已执行通过 | 仅将新 revision 降到 d9，再升至 e0；新两表移除/重建，已有合成 User 和内容 revision 在回退时保留。随后额外验证管理员删除触发 SET NULL，内容和操作回执仍保留；不是完整注销流程验收 |
| ruff / format | 已执行通过 | app/ tests/、内容 CLI 与新迁移，共 399 个 Python 文件符合格式；未改检查配置 |
| mypy baseline | 已执行通过：无新增 file:code | 原始 exit 1，55 条存量错误、35 组 file:code，241 个源文件；基线与豁免本批未变 |
| CLI 命令入口 | 已执行通过 | 实际运行 import-manifest --help，新增 actor/operation 参数可解析；未向业务库执行导入 |
| 文档与差异检查 | 已执行通过 | 8 份蓝图、45 个本地链接有效；app/tests/内容 CLI/新迁移 AST 可解析；蓝图无行尾空白/冲突，跟踪文件 diff --check 通过，新文件格式由 ruff 门验证 |
| 全量后端/覆盖率、依赖安全门、真实收据/内容授权、网关/宿主、生产迁移与部署 | 未执行 | 依赖未变；合成原创候选、模拟 verifier 与隔离数据库不冒充真实教学内容或上线证据 |

本批去重后 126 项快速回归，另有 9 项 PG；首轮 37、扩展 123 和单独 18 项均被最终命令覆盖，不重复累计。最初 lint 暴露新增 import 顺序/未用项，已修正；类型检查发现 SQLAlchemy `of=[ORM 类]` 不符合声明类型，改成对应列，实际 PG 锁行为用并发用例验证，未增加 ignore。新表检查第一轮把 generic DateTime 的字符串与 PG TIMESTAMP 字符串直接比较而失败；改用 PG 方言编译类型，并另查 timezone 后通过，未减少字段/FK/唯一/索引检查或修改 DDL 迎合检查。

迁移库与并发测试库是本轮同一专用 tmpfs PG 容器中的不同数据库，使用随机 loopback 端口；没有复用业务 PG。容器在核对任务标签后已删除，Docker Desktop 已恢复原关闭状态，已有网关定义和卷未修改。

可复跑命令（工作目录 backend/）：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m pytest tests/test_content_publication.py tests/test_learning_context.py tests/test_teaching.py tests/test_teaching_content_cli.py tests/test_v2_runtime.py tests/test_v2_account_data.py tests/test_response_contract.py tests/test_architecture_invariants.py -q -m 'not integration'
$env:PG_TEST_URL = '<一次性隔离测试库 URL；fixture 将重建整个 schema>'
$env:DATABASE_URL = $env:PG_TEST_URL
.venv/Scripts/python.exe -m pytest tests/test_content_publication_pg.py tests/test_learning_context_pg.py -q -rs
.venv/Scripts/python.exe -m ruff check app/ tests/ scripts/qualify_teaching_content.py migrations/versions/e0f1a2b3c4d5_content_publication.py
.venv/Scripts/python.exe -m ruff format --check app/ tests/ scripts/qualify_teaching_content.py migrations/versions/e0f1a2b3c4d5_content_publication.py
# 以下仅针对另一个独立空迁移测试库，不与上方 fixture 或业务库混用。
$env:DATABASE_URL = '<一次性空迁移测试库 URL>'
.venv/Scripts/python.exe -m alembic upgrade head
# 本次另有 schema/合成数据检查和隔离 downgrade d9→upgrade head，不是生产回退操作。
```

真实服务器导入的新调用形状为 `python scripts/qualify_teaching_content.py import-manifest candidate.json --actor-id <有效管理员ID> --operation-id <稳定批次ID>`。它仍需真实核验适配器；没有适配器时不会写库。check-manifest 不需要 actor 参数且不认证上游收据。

### 剩余范围与回退

- P01 尚未完成：`verify_content_receipt` 正式适配器没有实现，也没有对真实来源与许可给出核验结论。下一切片必须建立可信调用证据与其输入/输出绑定，再验证实际材料，不能用管理员勾选、同名来源字符串或测试 True 回调代替。
- 当前发布门限阅读单题，其他材料和题型仍待适配。撤回当前只针对一个 revision；整来源批量权利撤回、失败操作持久审计、运营保留期与发布质量指标仍需后续设计和验证。
- 新迁移已随 `2a07e571` 入库，但业务库尚未执行；业务环境实际 revision/数据/消费者未核验，不部署或自动清理旧候选。完整账号生命周期、P02–P06 和 B01/B02 遗留继续保留。
- 代码回退应关闭新管理入口/CLI import 并成组恢复服务、模型注册和兼容消费者，保留已经写入的候选与操作事实。真实环境默认采用保留新增表的前向兼容回退；本次 downgrade 会删除两张新表，仅用于一次性库演练，不能作为保留生产发布审计的回退方案。全目标继续进行中，未部署。

## P01.3 · 可信核验收据与后端验签

日期：2026-11-05。本批推进 V201/V202/V207，补上上一批尚未实现的正式签发/验签适配。固定提示的网关调用产出签名凭据，业务发布验证公钥和输入/输出绑定；管理员填写 verified、伪造模型族或普通收据 ID 均不能代替。能力默认关闭，没有配置真实密钥、调用真实供应商、认定素材使用权或部署。P01 继续进行中。

### 归属、消费者与边界

| 落点 | 职责与影响 |
| --- | --- |
| `deploy/v2-gateway/adapter/content_receipts.py` | 网关固定盲答/教学审查提示、重排、规范化输入摘要、实际响应身份检查、专用 Ed25519 签发；不保存材料或复制费用账本 |
| 同目录 `app.py` | 新内部 content-verification 入口复用 LiteLLM Bearer、模型和预算约束；鉴权/预算/不完整响应拒绝签名。共享排空调用使用 asyncio.shield，修正调用者取消会取消被等待子任务的问题 |
| `backend/app/services/teaching/content_receipts.py` | 纯公钥验签：固定算法、用途、kid、签发方、有效期、提示版本及字段完整绑定；不访问网络或数据库 |
| `backend/app/services/teaching_gateway.py`、`teaching/publication.py` | 按服务端配置装配真实验证器；关闭时保持不可发布，核验与写事务分离，原来源/许可/两模型族/证据发布门继续生效 |
| `backend/app/core/config.py`、`.env.example`、`requirements-cloud.txt` | 独立默认关闭开关、公钥环/issuer/期限校验；明确声明 cryptography 运行依赖，不使用登录 JWT 密钥 |
| adapter `Dockerfile`、`requirements-runtime.txt`；两份 gateway compose | sidecar 改为固定基础镜像/直接依赖的非 root 轻量运行时，LiteLLM 本身仍用原锁版；host 的签发配置默认关闭且不默认挂载私钥。仅本地构建，未应用到已有 host |

协议及配置唯一说明见[网关收据说明](../../deploy/v2-gateway/adapter/README.md#内容核验收据)，发布契约见 [CTX08](contracts.md#ctx08-内容草稿发布与撤回)。logical_call_id 同时写入调用 metadata 与签名凭据，供关联既有 LiteLLM 账本，不新增费用表。响应 id 仅代表实际观察到的供应商响应标识，不能当作已核对账单。模型族由网关受信配置确定，真实独立性仍需操作证据；签名不提供素材版权或教学正确性保证。

本批没有表结构或迁移变化。未重复运行 PostgreSQL/迁移检查，上一批隔离迁移与锁回归只代表 P01.2 的执行记录。没有改真实 .env、业务 DB 或媒体，未清理工作区无关试做。

### 实际验证

| 检查 | 实际结果 | 范围与局限 |
| --- | --- | --- |
| 最终后端相关回归 | 已执行通过：176 passed、1 warning，144.46 秒 | 收据验签、真实签名→发布桥接、发布流程、上下文、教学、CLI、配置、V2 运行/导出、响应契约和架构；包含 25 项验签与 1 项桥接，不另行累计 |
| adapter 回归 | 已执行通过：21 passed | 原代理/usage shim、固定提示、签名、实际模型身份、未知身份/鉴权/429/禁用/非法响应、false 审查保留与取消排空；格式调整后最终复跑 1.99 秒 |
| 实际 loopback HTTP | Windows 与 Linux 轻量镜像均已执行通过 | 两个真实 HTTP 服务、临时 Ed25519 密钥、实际后端纯验签模块；有效凭据通过、模型族篡改和错误上游 key 拒绝。上游为合成服务，不调用供应商 |
| 镜像构建/运行 | 已执行通过 | 最新源码重建、构建时 pip check；Linux HTTP 在 non-root、network none、read-only、受限 tmpfs/CPU/内存下运行。直接依赖固定，不声称传递依赖全部锁定 |
| 原有合成预算回归 | 已执行：10 通过、1 未证明，probe exit 1 | 最新 sidecar 配合原 LiteLLM；跨日 late settle/member UTC day 仍未证明，governance=false。[报告和首次失败记录](../evidence/content-receipts/README.md)完整保留 |
| ruff / format | 已执行通过 | app/tests 400 个文件及 5 个 adapter Python 文件；最终统一使用 backend 的规则，共 405 个文件格式通过，未改检查配置 |
| mypy baseline | 已执行通过：无新增 file:code | 原始 exit 1，55 条存量错误、26 文件、35 组 file:code，检查 242 个源文件；本批基线未变 |
| 依赖安全硬门 | 两套需求均已执行通过 | cloud 全依赖与 adapter runtime 全依赖分别用现有 pip_audit_gate；无漏洞命中，15 条历史豁免均 stale、未使用；豁免文件未改，没有 --no-deps 或关闭证书校验 |
| 文档/差异/语法 | 已执行通过 | 10 份 Markdown、64 个本地链接、405 个 Python AST；文档无冲突/行尾空白，跟踪文件 diff --check 通过 |
| 全量后端/覆盖率、真实模型核验、真实材料权利、四宿主、生产部署 | 未执行 | 不以合成模型/临时签名/本地容器替代上线证据 |

首轮 audit 遇到旧 pip 缓存权限错误，改用独立临时缓存；随后直连 PyPI TLS 失败，使用本机既有代理后完整硬门通过，没有放宽安全门。HTTP 脚本首次外置挂载/从 backend 执行分别暴露 app 导入路径问题，已固定为优先脚本相邻 adapter、外置挂载则镜像工作目录；两平台最终命令均通过。最后统一 backend 格式规则发现旧 test_adapter.py 格式不同，按既有规则格式化后复验，未新增忽略。

合成治理首次就绪超时、之后引擎 API 500；Docker Desktop 正常停启恢复，不把故障认定为已证实 OOM。重试暂停本批启动 Docker 时自动恢复的旧 host 网关，只运行独立合成项目；检查完成清理该项目，恢复原 host 五个容器的运行状态后将 Desktop 停回原关闭状态。未修改其镜像、定义、restart policy 或数据卷。

复跑命令（工作目录 backend/，adapter HTTP 与预算探针的完整方法见各自说明）：

```powershell
$env:PYTHONUTF8 = '1'
.venv/Scripts/python.exe -m pytest tests/test_content_receipts.py tests/test_content_receipt_publication.py tests/test_content_publication.py tests/test_learning_context.py tests/test_teaching.py tests/test_teaching_content_cli.py tests/test_config_env_guard.py tests/test_v2_runtime.py tests/test_v2_account_data.py tests/test_response_contract.py tests/test_architecture_invariants.py -q -m 'not integration'
.venv/Scripts/python.exe -m pytest ../deploy/v2-gateway/adapter/test_adapter.py ../deploy/v2-gateway/adapter/test_content_receipts.py -q
.venv/Scripts/python.exe ../deploy/v2-gateway/adapter/check_receipts_http.py --backend-verifier app/services/teaching/content_receipts.py
.venv/Scripts/python.exe -m ruff check app/ tests/ ../deploy/v2-gateway/adapter/
.venv/Scripts/python.exe -m ruff format --check app/ tests/ ../deploy/v2-gateway/adapter/
# 网络及缓存按执行环境配置；必须完整解析依赖，不添加 --no-deps。
.venv/Scripts/python.exe scripts/pip_audit_gate.py
.venv/Scripts/python.exe scripts/pip_audit_gate.py -r ../deploy/v2-gateway/adapter/requirements-runtime.txt
```

### 下一切片与回退

- 补核验任务输入构造、受控调用/失败恢复及可审阅产物，不将人工拼写 manifest 当作长期生产流程；继续复用发布服务、预算和用量账本。先确定真实素材来源/许可依据，再调用获准处理的内容，核对实际模型族及账目。当前未收到首批来源/授权信息。
- P01 只推进了阅读单题的可信调用证据，真实来源质量、其他材料/题型、整来源权利撤回、失败操作持久审计及 P02–P06 继续保留。午夜 late settle 仍是治理未通过项，不能绕过。
- 回退先关闭签发及后端收据开关，阻断新发布；既有内容仍按当前权利/撤回规则读取。成组恢复 sidecar 镜像/接口、后端装配及新增依赖；如果使用旧收据消费者，保留版本过渡。不能为了回退撤销已发布学习事实、操作回执或业务数据。本批没有可供生产执行的 downgrade。

## P01.4 · 可续跑核验采集与发布交接

日期：2026-11-05。上一目标回合有实际代码/证据进展，本批继续推进 V201/V207，补齐原先需要手工构造调用和拼装收据的服务器操作路径。没有调用真实模型、认证素材使用权、修改真实环境或部署；原有治理未证明项继续保留，不以新增工具解锁生产。

### 归属与行为

| 落点（相对 backend/） | 职责与消费者 |
| --- | --- |
| `services/teaching/content.py` | 将材料/来源/证据检查从完整发布核验中提取，准备和发布复用；教学复核输入共用一个构造函数，保持原规范化摘要；发布仍要求全部收据、独立模型族、答案一致及语义检查 |
| `services/teaching/qualification.py` | 四步请求计划、当前步骤收据认证、结果判断和可导入 manifest 组装；不访问业务 DB，不签名、不直接发布 |
| `services/teaching_gateway.py`、`core/config.py` | 独立默认空的 content_verification_api_key；拒绝已配置 admin key，用现有网关准入和错误归一作单次无重试调用，并认证返回签名；不创建第二套预算/成本行 |
| `scripts/content_verification_job.py` | 操作者工作目录中的原子检查点、OS 文件锁、过程状态、断点续跑和签名响应恢复；不是通用任务平台或 Celery 替代品 |
| `scripts/qualify_teaching_content.py` | 新增 plan/run/recover-verification；既有管理员幂等导入继续最终验签/题库复查。CLI 错误只返回固定说明与代码，不转发原始 provider 错误；补齐原有 proofs 的类型声明 |
| `.env.example` | 仅新增专用虚拟 key 的说明，不写真实 key，不修改实际 .env |

操作/状态/权限/恢复唯一说明见[内容核验采集操作](content-verification.md)，契约入口见 [CTX09](contracts.md#ctx09-服务器内容核验采集)。计划前拒绝未获准模型处理的材料；已有候选收据清空，不能靠旧自填记录减少新计划核验。每次付费请求前写 running，签名/输入绑定通过后持久结果。断连/崩溃的在途结果标 uncertain 并停止，不自动重发；恢复必须提供原始有效签名响应。错答/false 检查保留并立即停止后续调用，不重试负面结论。

全部有效结果通过同一个发布质量门后才产出 manifest；采集始终 published=false，导入仍由现有管理员服务提交。受控 key 的真实预算、模型许可和过期配置需另行验证，工具不会根据字符串认定其额度已正确配置。当前签发器没有持久收据查回；丢失响应且拿不到有效签名时需要人工对账，不能将其当零费用重试。专用 key 只驻留配置/请求头，不写作业文件。

### 实际验证

| 检查 | 实际结果 | 覆盖与局限 |
| --- | --- | --- |
| 最终相关快速回归 | 已执行通过：198 passed、1 warning，106.03 秒 | 新作业 19 项；并复验验签/签名→发布、发布操作、上下文、教学、CLI、网关、配置、运行/导出、响应及架构。旧 structlog 格式提示仍为 warning |
| 新作业流程 | 已包含在上行 | 使用真实网关签发模块/Ed25519 密钥及后端验签，合成上游和 ASGI 传输；四步产物实际交管理员导入并重放，未注入 True 验证器。未调用真实供应商 |
| 恢复与负控 | 已包含在上行 | 第二次调用丢失响应、重复执行不重发、篡改签名无法恢复、签名恢复后只执行剩余步骤、遗留 running 转 uncertain、计划修改拒绝、错答/false 停止、同族别名不能合格、治理/空 key/master key/关闭验签拒绝 |
| OS 锁与子进程 | 已执行通过，包含在 19 项 | Windows 双写者互斥，真实子进程 os._exit 后可重新取得锁；实际 CLI 子进程在隔离工作目录验证关闭准入、无模型调用和待执行状态不变。Linux fcntl 分支未执行 |
| ruff / format | 已执行通过 | app/tests 402 个文件加两个内容 CLI 文件，共 404 个文件；没有放宽规则 |
| mypy baseline | 已执行通过：无新增 file:code | 额外检查两个脚本，共 245 个源文件；原始 exit 1，55 条存量错误、26 文件、35 组 file:code；基线未改 |
| 命令入口 | 已执行通过 | 实际运行 plan-verification 和 recover-verification --help，参数可解析；实际 run 子进程由上述负控覆盖 |
| 文档/差异/语法 | 已执行通过 | 11 份 Markdown、73 个本地链接、404 个 app/tests/相关脚本 Python AST；无文档冲突/行尾空白，跟踪文件 diff --check 通过 |
| 全量后端/覆盖率、PG/迁移、依赖安全门、真实网关/模型/授权、四宿主及部署 | 未执行 | 无新依赖、表或数据库事务变化，不复用上一批安全门/迁移/容器证据作为本批通过 |

首轮新流程/既有教学相关 45 项通过。扩展首轮为 197 passed、1 failed：新的真实 CLI 子进程继承本机 .env 的 teaching-runs 设置，却在测试中单独关闭治理，配置校验按设计拒绝启动；已将该子进程置于隔离临时工作目录并显式关闭其 teaching-runs，最终 198 项完整复跑通过，未改真实配置或放宽启动校验。类型检查先发现新服务 Any 返回和本次额外纳入检查的旧 CLI 列表推断问题，已给出实际布尔返回/字典类型和正确的 proof 列表声明；没有新增 ignore 或修改基线。

复跑命令（backend/，Windows 先设置 PYTHONUTF8=1）：

```powershell
.venv/Scripts/python.exe -m pytest tests/test_content_verification_job.py tests/test_content_receipts.py tests/test_content_receipt_publication.py tests/test_content_publication.py tests/test_learning_context.py tests/test_teaching.py tests/test_teaching_content_cli.py tests/test_teaching_gateway.py tests/test_config_env_guard.py tests/test_v2_runtime.py tests/test_v2_account_data.py tests/test_response_contract.py tests/test_architecture_invariants.py -q -m 'not integration'
.venv/Scripts/python.exe -m ruff check app/ tests/ scripts/content_verification_job.py scripts/qualify_teaching_content.py
.venv/Scripts/python.exe -m ruff format --check app/ tests/ scripts/content_verification_job.py scripts/qualify_teaching_content.py
.venv/Scripts/python.exe -m mypy app/ scripts/content_verification_job.py scripts/qualify_teaching_content.py --ignore-missing-imports
# mypy 原始 exit 1 仍须与原 baseline 比较；不能直接当通过。
```

### 剩余目标与回退

- P01 尚未完成，仍缺真实材料来源/使用权与真实模型族、实际预算证据。来源问题尚未获得用户答复；不因此停止独立实现。下一步固定完整单题初答→提示→复答→揭晓→恢复及权限/正式成绩边界的集成证据，继续 P02 的任务对话/运行契约，不将服务器工具完善作为 V2 学习产品交付终点。
- 当前是单材料服务器作业，不是管理后台核验队列、持久收据查回、全站不可篡改失败审计或跨机器文件锁；真实 Linux 运行与实际模型输入能力需另验。P02–P06、其他材料、记忆与四宿主继续保留。
- 回退先停用新增采集命令/专用 key，保留作业文件以核对在途工作；成组恢复提取的材料校验/输入函数及 CLI 消费者。无数据库 downgrade，已发布内容、学习事实和操作回执不能用删数据回退。当前既有前端及工作区无关试做均未动，本批未启动 Docker 或操作业务服务。

## P02.1 · 任务对话持久化、引用回复与学习闭环

日期：2026-11-05。上一目标回合已有实际进展；本批从服务器核验工具进入 V202/V203/V207 的学习体验切片。用户随后明确要求“完成一轮后暂停”：本轮完成验证和交接后停止，不自动开始下一批。P01/P02 及 V2.0–V2.2 的完整目标不缩减，也不宣布完成。未改前端、未调用真实模型、未执行业务库迁移或部署。

### 归属与消费者

| 落点（相对 backend/） | 职责与变化 |
| --- | --- |
| `models/v2_runtime.py`、`models/__init__.py`、`schemas/teaching_dialogue.py` | 持久任务消息及回复 schema；run 新增 response_mode，旧值和旧入口保持 cards；消息属于用户/会话/内容 revision，不属于费用或判分表 |
| `services/teaching/dialogue.py` | 追加消息、分页/事件/导出的当前权限投影、有限历史构造及回复校验；调用者拥有事务，追加时持有会话锁 |
| `services/teaching_runs.py` | 新 conversation 路径复用幂等、认领、租约、取消、完成及事件机制。用户消息与创建原子提交，助手消息与最终运行状态/事件原子提交；旧 cards 路径继续兼容 |
| `services/teaching_gateway.py` | 两种回复复用同一有界模型调用、成员关系/临时 key、预算和超时；新导师结构输出严格校验并将源索引映射到真实引用，不存隐藏推理或第二套 usage/cost |
| `api/v1/teaching_runs.py` | GET/POST messages 入口和 no-store，SSE 增 Last-Event-ID、游标校验和 message.upsert 当前权限投影；订阅仍不创建模型任务 |
| `services/account_data.py`、`tasks/account_tasks.py` | 新增对话导出及注销删除；导出复用已有站内状态，避免跨多个任务累积上下文共享锁；24 小时执行日志清理不删除长期对话 |
| `core/config.py`、`.env.example` | 新对话开关默认关闭，要求教学运行已启用；真实 .env 未改 |
| `migrations/versions/9f2c8a7d6b10_teaching_conversation.py` | 继承 e0，新增消息表和 run 模式列，旧 run server default=cards；仅在独立临时数据库演练 |

正式 wire、权限、历史边界和未完成能力只维护在 [CTX10](contracts.md#ctx10-任务对话与导师回复)。兼容路径与新对话共用同一 run 状态机，不建新的通用任务系统；历史请求摘要继续使用原算法。未揭晓解析前为标记明确的 policy 引导，揭晓后才运行带引用的简短模型回复，建议只在消息中保存，用户须明确调用原 draft/attempt 动作。当前不是完整工具导师或 token 级流式生成。

### 实际验证

| 检查 | 实际结果 | 范围与局限 |
| --- | --- | --- |
| 最终相关快速回归 | 已执行通过：212 passed、1 warning，102.19 秒 | 新对话 5 项、导师输出 9 项，以及既有核验/发布/上下文/教学/CLI/网关/配置/运行/导出/响应/架构；不和先前 11、12、14、210 项重复累计。warning 是原 structlog 格式提示 |
| 单题 HTTP 学习流程 | 已包含在上行 | 初答 A→提示→复答 B→显式揭晓→对话→历史分页恢复→明确保存建议为草稿；未新增正式考试记录，作答数/教学 revision 不被聊天隐式增加，初答与辅助复答角色保留 |
| 导师网关及历史负控 | 已包含在上行 | 成员/key/受预算出口经 MockTransport，模型回复为合成；错误/布尔/重复/空引用、额外动作、空正文/错误答案类型和截断拒绝。新鲜上下文替换旧源映射，历史最多 6 条且 8 KiB 内，不含其他任务 |
| 恢复/导出/生命周期 | 已包含在上行 | 未揭晓不请求模型、重复 worker 不重复输出、断线续读不重新执行、未来/非法游标拒绝；任务/用户隔离、未授权外部读取拒绝；旧事件清理后消息保留，材料撤权后正文限制，空历史任务不阻断导出，注销清除消息 |
| 隔离 PostgreSQL | 已执行通过：15 passed，84.54 秒，无 skipped | 新对话 5 项：并发同操作仅一 run/一用户消息，以及取消/epoch/会话 revision/模型权利变化阻止晚到助手消息；另复验 10 项既有运行/外部授权并发。模型调用均为事件控制替身 |
| 迁移与 ORM | 已执行通过 | 新独立空库完整 initial→e0→9f；在 e0 插入不含新字段的旧 run，升级后保持原消息且 mode=cards。对照新表列、PG 方言类型/时区、nullable、FK/ondelete、唯一键与索引，并实际写消息 |
| 隔离回退/重升 | 已执行通过 | 仅本次新迁移 downgrade e0→upgrade head；新增消息表删除/重建，旧 run 和默认模式/原消息保留。演练删除的新消息是合成记录，不是生产保数据回退 |
| ruff / format | 已执行通过 | app/tests 和新迁移，共 408 个文件格式通过；规则未变 |
| mypy baseline | 已执行通过：无新增 file:code | 245 个源文件，原始 exit 1，55 条存量错误、26 文件、35 组 file:code；本批基线未改 |
| 文档/语法/迁移编号 | 已执行通过 | 11 份 Markdown、75 个本地链接、408 个 Python AST；93 个迁移 revision 无重复，跟踪文件 diff --check 通过 |
| 全量后端/覆盖率、真实模型教学质量/预算、浏览器/四宿主、生产迁移/部署 | 未执行 | 未新增依赖，不重跑依赖安全门；本批为后端 API 切片，不修改/验收前端界面，不能将合成回复当真实老师验收 |

新流程首轮 14 项中导出测试因 fixture 的 expire_all 后直接读取过期 User 导致 MissingGreenlet，已改为显式异步重新加载；未改生产加载规则。导出接入另复查了长期读锁边界，改用已有站内投影，增加空历史任务覆盖，最终完整回归通过。

迁移最初选用的 f1 编号与历史媒体清理迁移重复，已将本次新 revision 更名为唯一 9f，不动历史迁移。演练 harness 先因多个 asyncio.run 共用 asyncpg 池而失败，修正为单一事件循环；随后类型检查把 generic TIMESTAMP 字符串与带方言编译的类型比较，已通过实际反射确认 timezone=true，改为两侧同方言编译并独立验证时区。唯一约束索引与普通索引分别核对；没有改 DDL、基线或检查要求迎合脚本。最终迁移、schema/ORM、降级与重升均实际通过。

本次独立 PG 容器有任务标签、tmpfs 和随机 loopback 端口，迁移与并发分属不同数据库。测试完核对标签后已清除容器；启动 Docker 时自动恢复的原 host 五个容器在测试期间暂停，之后恢复原运行状态，Docker Desktop 再关闭回最初状态。未重建原 host、操作业务库或使用真实 provider key。

复跑命令（backend/，Windows 设置 PYTHONUTF8=1）：

```powershell
.venv/Scripts/python.exe -m pytest tests/test_teaching_dialogue.py tests/test_tutor_gateway.py tests/test_content_verification_job.py tests/test_content_receipts.py tests/test_content_receipt_publication.py tests/test_content_publication.py tests/test_learning_context.py tests/test_teaching.py tests/test_teaching_content_cli.py tests/test_teaching_gateway.py tests/test_config_env_guard.py tests/test_v2_runtime.py tests/test_v2_account_data.py tests/test_response_contract.py tests/test_architecture_invariants.py -q -m 'not integration'
# 以下 fixture 会重建整个 schema，URL 只能指向一次性隔离测试库。
$env:PG_TEST_URL = '<一次性测试库 URL>'
$env:DATABASE_URL = $env:PG_TEST_URL
.venv/Scripts/python.exe -m pytest tests/test_teaching_dialogue_pg.py tests/test_v2_runtime_pg.py -q -rs
.venv/Scripts/python.exe -m ruff check app/ tests/ migrations/versions/9f2c8a7d6b10_teaching_conversation.py
.venv/Scripts/python.exe -m ruff format --check app/ tests/ migrations/versions/9f2c8a7d6b10_teaching_conversation.py
# 对另一个独立空迁移库执行过完整升级/合成旧行检查/schema 检查/隔离回退与重升。
```

### 暂停交接与回退

- 按用户指令，本轮完成后暂停。恢复需用户明确指令，不自动启动 P02.2。真实素材依据及真实网关/模型证据仍缺失；完整自由导师、工具循环、流式回复、重试体验、其他材料、记忆、四宿主和商业/上线目标全部保留。
- 当前只新增后端对话入口，已有前端仍使用兼容 cards 路径；不把后端消息 API 当作已交付用户端完整老师。默认关闭新开关，业务环境没有应用新迁移，恢复时先核查环境及真实消费者。
- 回退先关闭对话写开关并停止新模式派发，保留当前消息/运行事实供恢复与导出；成组恢复入口、服务、schema、注册和生命周期消费者。生产应保留新增列/表作前向兼容回退，本次 downgrade 会删除消息，仅适用于一次性测试库，不能删除生产对话作为回退。


## P02.2 · 流式导师回复、块发布与用量三态

日期：2026-11-06。承接[开工前准备](preparation.md)：先修默认全关时的 V2 表依赖与发布边界，再实现本切片。范围为「揭晓后」的单轮导师回复流式化；未揭晓仍返回 policy 引导，不请求模型。没有独立聊天/跨任务关联（P02.3）、工具循环、token 级 SSE 或前端；没有调用真实模型、迁移业务库或部署。

### 归属与消费者

| 落点（相对 `backend/`） | 职责与变化 |
| --- | --- |
| `services/teaching/streaming.py` | 纯解析器：剥掉 `[n]` 引用标记、按句末/120 字符切块、越界标记立即失败、1000 字符上限。无数据库、无时钟 |
| `models/v2_runtime.py`、`models/__init__.py` | 新表 `teaching_message_blocks`（`message_id`+`ordinal` 唯一，append-only 的 `before_update` 守卫）；`teaching_messages.status`（`complete/streaming/interrupted`） |
| `migrations/versions/b8e2f4a6c901_teaching_stream_blocks.py` | 继承 `9f2c8a7d6b10`；新表 + `status` 列，含 downgrade |
| `services/teaching_gateway.py::stream_tutor_reply` | 复用同一 run 凭据/预算/准入；`stream=true` + `include_usage`，纯文本提示；逐块产出 delta，结束时报告 `reported/missing/unknown`；截断、工具调用、异常状态均归一为可解释错误 |
| `services/teaching_runs.py::_stream_turn` | 每个块一个短事务：会话锁 → run 锁 → 状态/epoch/取消/revision/材料使用权复查 → 写块 + `message.block` 事件 → 提交；取消与撤权分别结算 |
| `services/teaching/dialogue.py` | 流式消息创建、块追加、最终投影；历史/分页/导出/事件都带 `status` 与 `blocks`，按当前权利投影 |
| `api/v1/teaching_runs.py` | `message.block` 事件投影；`GET /runs/{id}` 补 `no-store` |
| `schemas/teaching_dialogue.py` | `DialogueMessage.status`、`blocks` 与 `DialogueBlock` |
| `services/v2_access.py`、`services/v2_schema.py`、`services/teaching/service.py`、`account_data.py`、`tasks/account_tasks.py`、`tasks/teaching_tasks.py`、`api/v1/external_connections.py`、`services/external_connection_service.py` | 默认全关时的惰性边界：开关先于表读取；sweep/导出/注销/连接列表按实际存在的表决定是否执行 |
| `app/main.py` | `MCP_SDK_ENABLED=true` 但 SDK 缺失时降级 503，不再拖垮整个 API |
| `deploy/v2-gateway/adapter/app.py` | 入站代理对 `stream:true` 增量转发 SSE（断线后台排空）；shim 逐行转发并在流末补保守 usage；输出上限按模型查 `ADAPTER_MODEL_OUTPUT_CAPS` |
| `core/config.py`、`.env.example`、`docker-compose.prod.yml` | `TEACHING_STREAMING_ENABLED`（依赖 dialogue）、`LLM_GATEWAY_TUTOR_MODEL/MAX_TOKENS`；补齐生产 env 白名单与适配层上限变量 |

未揭晓时的 policy 回复、P02.1 的非流式 JSON 路径、`max_tokens=128` 的 cards/核验出口都保持原样；切换只看 `TEACHING_STREAMING_ENABLED`，关闭即回退。

wire、事件与用量语义只在 [CTX11](contracts.md#ctx11-流式导师回复与块发布p022)。1 基引用标记只属于流式路径，P02.1 的 JSON 索引仍是 0 基。

### 实际验证

| 检查 | 实际结果 | 范围与局限 |
| --- | --- | --- |
| 最终相关快速回归 | 已执行通过：214 passed、5 warnings | 教学/对话/导师网关/runtime/context/发布/核验/CLI/账号导出与注销/架构/配置/流式/惰性边界/celery 任务；warnings 仍是既有 structlog 格式提示 |
| 新增流式回归 | 已包含在上行 | 解析器切块与标记；增量 delta 与 done；`reported/null/missing` 三态；块与事件同事务；取消只保留已提交块且 body 不含未发布文本；撤权中止；截断/缺失 finish_reason 标 interrupted；受限块事件降级 |
| 新增惰性回归 | 已包含在上行 | 缺表时 sweep 不发 SQL、导出跳过 V2 段、注销照常、关闭功能 503 不读授权表 |
| 隔离 PostgreSQL 迁移 | 已执行通过 | 空库 `initial → b8e2f4a6c901`；`downgrade -1 → upgrade head` 删除/恢复块表与 status 列；列类型/可空性/FK CASCADE/唯一约束逐项核对 |
| 隔离 PostgreSQL 并发 | 已执行通过：6 passed | 流式取消后只保留已提交块、step=uncertain、run=cancelled；既有对话并发 5 项复验 |
| schema drift 门 | 已执行通过：0 已知、0 新增 | 迁移生成的库对照 ORM metadata |
| 适配层回归 | 已执行通过：27 passed | 按模型上限、非法上限配置回退、入站/出站 SSE 增量转发、usage 注入不重复 |
| ruff check / format | 已执行通过 | app/、tests/、新迁移、adapter |
| mypy baseline | 已执行通过：无新增 `file:code` | 原始 exit 1 仍为存量条目，未改基线 |
| 全后端套件/覆盖率、真实网关/模型/预算、前端与部署 | 未执行 | 合成上游与 MockTransport 不替代真实供应商能力、账目与质量 |

首轮实现暴露过三处真实问题：`/messages` 响应模型缺 `status/blocks` 导致 FastAPI 422；跨 delta 的半个引用标记被当成普通文本；`published` dict 让 mypy 推出 `int | None`。均已按实际契约修复，未放宽检查器。

独立审查又发现并已修复的有效问题：网关模板新增了未注册的 `${V2_TUTOR_MAX_OUTPUT_TOKENS}` 占位符（会让 gateway 容器启动失败）→ 改为字面量；受限投影下 `event_block` 因 `blocks[0]` 越界 → 改为返回受限；流式消息 body 曾写 `citations` 而非 `citation_ids`，绕过引用失效检查 → 统一键名；没有 `finish_reason` 的流被当成功 → 必须显式 `stop`；`interrupted` 的 body 混入未发布文本 → 只写已提交块；`asyncio.timeout` 放在生成器内会取消消费者 task → 移到 `_stream_turn` 包住整轮；入站代理 `aiter_raw` + 去掉 `content-encoding` → 改 `aiter_bytes`、禁止上游压缩，并用独立 pump 保证断线排空；shim 保守 usage 按供应商模型名查不到别名上限 → 未知时取最大配置上限；`sweep` 兜底把崩溃遗留的 `streaming` 消息标 `interrupted`；教学读门禁改用完整 V2 表检查；补了 V2 表清单/ORM 同步、受限事件、缺失 finish_reason 与事件 payload 形状断言。

### 复跑命令（工作目录 `backend/`，Windows 设置 `PYTHONUTF8=1`）

```powershell
.venv/Scripts/python.exe -m pytest tests/test_teaching_streaming.py tests/test_v2_schema_gating.py tests/test_teaching_dialogue.py tests/test_tutor_gateway.py tests/test_teaching.py tests/test_v2_runtime.py tests/test_learning_context.py tests/test_content_publication.py tests/test_content_receipts.py tests/test_content_receipt_publication.py tests/test_teaching_content_cli.py tests/test_content_verification_job.py tests/test_v2_account_data.py tests/test_account_data.py tests/test_account_deletion.py tests/test_architecture_invariants.py tests/test_config_env_guard.py tests/test_celery_tasks.py -q -m 'not integration'
$env:PG_TEST_URL = '<一次性隔离测试库 URL；fixture 会重建整个 schema>'
$env:DATABASE_URL = $env:PG_TEST_URL
.venv/Scripts/python.exe -m pytest tests/test_teaching_streaming_pg.py tests/test_teaching_dialogue_pg.py -q -rs
# 迁移演练使用另一个空库：
#   alembic upgrade head → downgrade -1 → upgrade head
.venv/Scripts/python.exe scripts/check_schema_drift.py
.venv/Scripts/python.exe -m pytest ../deploy/v2-gateway/adapter/test_adapter.py ../deploy/v2-gateway/adapter/test_content_receipts.py -q
```

### 回退与剩余边界

- 回退先关闭 `TEACHING_STREAMING_ENABLED`（回到 P02.1 非流式），再成组恢复 gateway/runs/dialogue/schema 与适配层；已写入的块与消息保留可读，不以删数据回退。生产保留新表/新列作前向兼容回退。
- 仍未实现：独立聊天与跨任务关联（P02.3）、统一 actions/学习组件（P02.4）、工具循环与 token 级流式、真实模型质量与预算实证；块级发布受数据库事务粒度限制，不是逐 token 推送。
- `TeachingAccessGrant` 仍无生产写入路径；真实网关的 1024 输出上限必须实测后再配置 `ADAPTER_MODEL_OUTPUT_CAPS`，否则适配层会按失败关闭返回 422。
- 全后端套件、真实供应商/网关账目、浏览器与部署均未执行；不能把合成流当作完整导师验收。

## P02.3 · 独立聊天、消息与任务关联

日期：2026-11-06。承接 P02.2 的块发布与用量三态：本切片把「聊天」从教学会话中拆出，使一段对话可无任务、可跨多个任务，同时保持旧消息入口同源。未改前端、未调用真实模型、未迁移业务库或部署；新增开关默认关闭。

### 归属与消费者

| 落点（相对 `backend/`） | 职责与变化 |
| --- | --- |
| `models/v2_runtime.py`、`models/__init__.py` | 新表 `tutor_conversations`（`kind=chat/task`，`task_session_id` 每会话唯一）与 `tutor_conversation_tasks`（聊天↔会话多对多）。`teaching_messages` 增加 `conversation_id`，`session_id`/`content_revision_id`/`session_revision` 改为可空，序号唯一键从 `(session_id, sequence)` 改为 `(conversation_id, sequence)`；`agent_runs` 增加 `conversation_id`、`session_id` 与 `bound_session_revision` 可空；`agent_run_events.session_revision` 可空 |
| `migrations/versions/c4a1b2c3d4e5_tutor_conversations.py` | 继承 `d4e5f6a7b8c9`：建两表、按 `session_id` 回填 `kind=task` 聊天与关联、迁移唯一键、放宽三处非空；`downgrade` 反向删除。仅在隔离库演练 |
| `services/teaching/dialogue.py` | 聊天归属与投影：`owned`/`owned_chat`/`task_conversation`/`task_revision_id`/`associate`/`task_views`/`touch`；`page_conversation` 与 `page_session`；`project` 对无任务消息只认所有权，对有任务消息沿用当前权利；`model_input` 返回可空 `learning_context`；`validate_reply` 增加无来源分支；`export_all` 输出聊天与消息 |
| `services/tutor_conversations.py` | 独立聊天 CRUD 与删除：创建、分页列表（仅 chat）、详情含任务、改名/归档、删除消息/块/执行日志但保留教学事实 |
| `services/teaching_runs.py` | `start_conversation_turn`（无任务或绑定任务、必须版本）、`dispatch_run`、锁序聊天→会话→运行、`_lock_target` 只按 `conversation_id` 解析聊天（`events` 对 P02.3 之前的运行另行按会话查任务聊天）、`get`/`events`/`cancel` 支持无会话运行、`_stream_turn` 支持无任务纯文本流并允许零引用 |
| `services/teaching_gateway.py` | `_model_completion` 支持按调用指定模型与上限；无任务聊天走 `LLM_GATEWAY_TUTOR_MODEL`/`LLM_GATEWAY_TUTOR_MAX_TOKENS` 的 JSON 与流式提示，服务端拒绝引用或 ABCD 建议；任务回复仍是原 128-token 出口 |
| `services/teaching/streaming.py` | `CitationStream(general=True)`：无来源聊天丢弃 `[n]` 标记而非报越界 |
| `services/v2_schema.py` | `V2_TABLES`/`EXPORT_TABLES`/`DELETE_TABLES` 新增两表；新增 `CONVERSATION_TABLES` 与 `require_conversation_schema`，缺表 503 |
| `api/v1/tutor.py`、`app/main.py` | 新 `/api/v1/tutor` 路由并注册；全部响应 `no-store`，删除返回 204 |
| `api/v1/teaching_runs.py` | 旧消息 GET 改用 `page_session`（读不建聊天）；`dispatch` 指向服务层 `dispatch_run` |
| `core/config.py`、`.env.example`、`docker-compose.prod.yml` | `TEACHING_CONVERSATIONS_ENABLED`（要求 dialogue 与 teaching），补生产 env 白名单 |
| `services/account_data.py`、`tasks/account_tasks.py` | 导出新增 `tutor_conversations` 并覆盖无任务消息；注销显式删除聊天与关联 |

未任务化的消息不伪造引用，也不写 `requires_reveal`；任务聊天仍只由旧入口与其任务聊天维护，`/tutor` 不管理 `kind='task'` 聊天（详情/删除均 404）。旧消息端点保持同一张表、同一投影与同一 ID/顺序。

### 实际验证

| 检查 | 实际结果 | 范围与局限 |
| --- | --- | --- |
| 新增 P02.3 回归 | 已执行通过：25 passed（`test_tutor_conversations.py`） | 聊天 CRUD/归档/删除且保留任务事实、无任务回合与宽上限、引用与 ABCD 拒绝、聊天内两任务切换、取消不发布、列表分页与排序、旧入口同源且不建空聊天、导出（含撤权后 restricted）/注销、开关与越权、关闭后读取也 503、schema 503、无任务流式块与零引用 |
| 既有教学/运行回归 | 已执行通过：39 passed | 教学对话、流式、V2 运行时、schema gating、V2 账号导出 |
| 宽回归 | 已执行通过：155 passed | 上列 + 教学服务、内容发布、学习上下文、账号导出/注销、架构、配置、celery |
| 隔离 PostgreSQL 迁移 | 已执行通过 | 空库 `head`、`downgrade -1 → upgrade head`；在旧库插入临时教学会话与两条消息后升级，回填出 1 个 `kind=task` 聊天 + 1 条任务关联，消息 ID/顺序/会话引用不变 |
| schema drift 门 | 已执行通过：0 已知、0 新增 | 迁移生成库对照 ORM metadata |
| ruff check / format | 已执行通过 | app/、tests/、新迁移；规则未变 |
| mypy baseline | 已执行通过：无新增 `file:code` | 用 baseline 对比，新增集合为空 |
| 隔离 PostgreSQL 并发 | 已执行通过：7 passed（`test_tutor_conversations_pg.py` + 既有对话并发） | 两个并发创建共享一个聊天/一个 run/一条用户消息；运行中删除聊天后 runner 正常结束、无残留 run/事件/步骤/消息 |
| 全后端套件 | 已执行通过：1689 passed、1 skipped（`-m 'not integration'`，21:58） | 跳过项为既有条件跳过；集成用例单独在隔离 PG 执行（本切片 2 项 + 既有对话/流式/运行时 16 项） |
| 隔离 PostgreSQL 全量 integration | 已执行：60 passed、1 skipped、2 failed | 2 项失败是 `test_listening_pg.py` 的既有测试顺序耦合（在 HEAD `bfd642d5` 的干净 worktree 上以同一隔离库、同序复现同样 2 项失败），与本切片无关；本切片涉及的 PG 用例全绿 |
| 真实网关/模型、前端与部署 | 未执行 | 合成上游不替代真实供应商能力、账目与质量 |

独立审查（维度评审 + 逐条对抗核实）发现并已修复的有效问题：

- `execute()` 在聊天/任务已消失的分支先 `db.rollback()` 再读 `found.user_id`，实例已过期 → `MissingGreenlet`，本应「结算排队运行」的路径每次都崩、只能等 sweep；改为回滚前取 owner id，并补回归。
- 无任务回合会把同一聊天里的**任务消息**喂进模型输入（违反跨任务隔离），且任务消息内容可能包含已揭晓答案；`model_input` 的历史查询改为按本 run 的 `session_id`（无任务时为 NULL）过滤，并补「任务历史不得进入无任务回合」回归。
- P02.3 给既有表加列后，表存在性门禁不再能证明 ORM 可查询：停在旧 head 的库上 beat `sweep-teaching-runs`（每 10 秒）与注销 `_prepare_v2_removal`/`_delete_v2_children` 会因缺列抛 `ProgrammingError` 并无限重试。新增 `conversation_columns_ready` / `existing_columns`，sweep 与注销按列决定是否触碰这三张表，并补对应回归。
- `tests/test_architecture_invariants.py` 的「下线支付路由不得复活」参数化测试被嵌套在另一个测试函数体内，从未被收集（27 项 → 之前从未执行）；移到 `TestCutFeaturesStayCut` 后收集 32 项并通过。
- `teaching_runs.get`/`events`/`cancel` 以及 cards 模式的 `create` 直接 `select(AgentRun)`，从不经过 schema 门；停在旧 head 的库上返回 500。现在它们先 `require_teaching_schema`，返回 503，并补回归。
- 迁移回填改为从 `teaching_sessions` 取 owner，而不是从消息行取，避免两个用户映射到同一个唯一的 `task_session_id`。

补齐的测试缺口（评审以变异测试证明原先「删掉实现也照样通过」）：任务聊天不可经 `/tutor` 读取、归档后可读、关闭开关后读写都 503、同 `operation_id` 换消息必须 409、新回合更新标题并置顶、跨聊天读取隔离、注销删除任务聊天及其关联但保留任务事实、删除聊天不影响旧任务聊天、导出顺序包含新段、任务上下文消失后消息必须 restricted、无任务回合不携带任务历史、旧任务聊天不出现在聊天列表、迁移回填（两个用户各得一个任务聊天、会话已消失的孤儿消息不被收编）。

首次实现暴露并修复的问题：`execute()` 曾把已构建的上下文变量重置为 `None`；旧消息 GET 曾通过 `page` 名称被删除；测试直接插入 `teaching_messages` 时缺少 `conversation_id`；`create()` 曾在绑定任务聊天时把聊天锁放到会话锁之后，已改为先解析/创建任务聊天再锁会话；`_lock_target` 只按 `conversation_id` 解析聊天，缺聊天列的旧运行按状态冲突结算，不现场创建 transcript。mypy 对 `str | None` 会话/聊天 ID 的窄化也已按真实类型修正，未改基线。

### 复跑命令（工作目录 `backend/`，Windows 设置 `PYTHONUTF8=1`）

```powershell
.venv/Scripts/python.exe -m pytest tests/test_tutor_conversations.py tests/test_teaching_dialogue.py tests/test_teaching_streaming.py tests/test_v2_runtime.py tests/test_v2_schema_gating.py tests/test_v2_account_data.py -q -m 'not integration'
$env:PG_TEST_URL = '<一次性隔离测试库 URL；fixture 会重建整个 schema>'
$env:DATABASE_URL = $env:PG_TEST_URL
.venv/Scripts/python.exe -m pytest tests/test_tutor_conversations_pg.py tests/test_teaching_dialogue_pg.py tests/test_teaching_streaming_pg.py tests/test_v2_runtime_pg.py -q -rs
# 迁移演练使用另一个空库：alembic upgrade head → downgrade -1 → upgrade head
.venv/Scripts/python.exe scripts/check_schema_drift.py
```

### 回退与剩余边界

- 回退先关闭 `TEACHING_CONVERSATIONS_ENABLED`（独立聊天 503，旧任务聊天不受影响），再成组恢复 `/tutor` 路由、聊天服务、模型出口分支、`v2_schema` 清单与迁移。生产保留新表/新列作前向兼容回退；`downgrade` 会删聊天与消息，只用于一次性测试库。
- 仍未实现：统一 actions 与学习组件（P02.4）、工具循环、跨任务长期记忆、外部宿主接力；聊天内的即时小测、记忆写入/纠错与跨材料恢复仍属后续切片。
- 同一用户仍只允许一个活跃运行（`uq_agent_run_active_user`），因此「切换任务」是串行恢复而非并发执行；是否放宽留待运行时治理单独决定。
- 读取端点（`GET /runs`、`/events`、`/messages`、旧 `/context`）仍沿用既有「不按功能开关关闭」的口径，只校验当前身份与资源权利；新增 `/tutor` 读取则按新能力开关关闭。此差异已记录，未在本切片统一。
- `TeachingAccessGrant` 仍无生产写入路径；真实网关的 1024 输出上限必须实测后才能配置 `ADAPTER_MODEL_OUTPUT_CAPS`。
