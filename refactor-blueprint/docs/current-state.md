# 后端代码现状

核查日期：2026-11-05；本页登记代码落点，不代表实现已通过验收或必须保留。HEAD 已提交 V2 与生产部署状态的区别、处置建议见 [审查结论](review.md)；开始重构后的切片与验证见[实施记录](implementation.md)。本地 HEAD 不等于生产部署版本。

## 装配和运行组件

| 组件 | 代码入口 | 当前职责 |
| --- | --- | --- |
| HTTP API | `backend/app/main.py::create_app` | FastAPI 装配、统一错误、鉴权消费者、健康检查与观测 |
| 数据会话 | `backend/app/core/database.py` | 懒建 async engine/session maker；请求依赖与 worker 会话来源 |
| 默认 worker / beat | `backend/app/tasks/celery_app.py` | 默认 `celery` 队列、调度、视频 head/tail、运营与生命周期任务 |
| 教学 worker（已提交、默认关闭） | 同一 Celery 应用的 `teaching` 队列 | `execute_teaching_run`；run 巡检与恢复 |
| 独立 GPU worker | `gpu-worker/gpu_worker/` | 只消费转录队列，回调云端；不 import `app.*` |
| 模型网关（已提交候选、未验收） | `deploy/v2-gateway/`、`docker-compose.v2-gateway.yml` | 锁版 LiteLLM、薄适配、模板与验证工具；是否采用需重新评估 |
| 网关业务适配（已提交、默认关闭） | `backend/app/services/teaching_gateway.py` | 教学网关准入、控制面/数据面调用与错误归一 |

网关版本和镜像只引用 `deploy/v2-gateway/image-lock.json`，不在此复制数字。该锁文件的治理标记为 false；不能从模板或合成测试推断当前真实供应商、容量或生产治理已经通过。

## 业务模块地图

下表中的路径均相对 `backend/app/`；一组现有模型可由多个服务使用，不表示它们已经按目标域物理拆分。

| 能力 | 现有主要落点 | 数据/边界 |
| --- | --- | --- |
| 身份、账号与权限 | `api/dependencies.py`、`api/v1/auth.py`、`api/v1/users.py`、`core/security.py` | 手机号身份、JWT/黑名单/改密/封禁、用户/管理身份 |
| 视频与内容 | `api/v1/videos.py`、`catalog.py`、`browse.py`；`tasks/video_processing.py`、`services/video_media.py`、`video_playback.py`、`video_publish.py`、`pipeline_dispatch.py` | Video/Subtitle、入库、head→GPU→回调→tail；任务拥有状态提交，媒体服务拥有提取/下载/转码 I/O，播放服务校验产物与发布资格；后台本地化认领与既有 outbox 意图同事务提交 |
| 字幕编辑与重断句 | `services/subtitle_edit_service.py`、`subtitle_resegment_rules.py`、`subtitle_segmentation.py` | 编辑服务拥有数据库替换、用户数据捕获/恢复及提交；规则模块负责分段、映射计划和快照格式 |
| 首页编辑发布 | `services/home_content_service.py`、`home_content_content.py`、`home_content_layout.py` | 草稿、不可变 revision、布局、来源指纹和回退 |
| 词汇与复习 | `api/v1/vocabulary.py`、`vocab_sets.py`、`words.py`；`services/vocabulary_service.py`、`study_session_service.py`、`practice_service.py`、`vocab_set_service.py` | 单词、来源、词集、复习；B02.2 将词汇学习事实与业务进度同事务写入，保留现有调度算法 |
| 正式考试 | `api/v1/exams.py`、`services/exam_service.py`、`models/exam_test.py` | 冻结题面、单次交卷认领、服务端判分与结果重放；学习事实随成绩同事务提交 |
| 听力练习 | `api/v1/listening.py`、`services/listening_service.py` | 冻结题面；服务拥有草稿/交卷的本人校验、锁定和状态检查；学习事实随结果同事务提交 |
| 教学内容与事务 | `services/teaching/content.py`、`service.py`、`principal.py`、`events.py` | 内容核验/披露、session/item/attempt、幂等、学习 outbox |
| 统一学习上下文（P01.1） | `services/teaching/context.py`、`schemas/learning_context.py` | 阅读单题 v1：当前材料/版本、草稿/近期作答、帮助/暴露、允许动作和恢复地址；HTTP/MCP/模型运行时调用同一投影，无新表 |
| 教学内容发布（P01.2） | `api/v1/admin_teaching_content.py`、`services/teaching/publication.py`、`models/content_publication.py` | 候选草稿、预检、发布、撤回与操作回执；后台 API 和服务器 CLI 共用事务服务。新增两表，仅在隔离 PG 演练 |
| 核验调用凭据（P01.3） | `services/teaching/content_receipts.py`、`services/teaching_gateway.py`；网关 `deploy/v2-gateway/adapter/content_receipts.py` | 网关固定核验提示、Ed25519 签名及后端公钥验签；输入、实际响应模型/模型族、结果与 logical_call_id 绑定。默认关闭，尚未配置真实签发密钥或完成真实材料核验 |
| 服务器核验采集（P01.4） | `services/teaching/qualification.py`、`scripts/content_verification_job.py`、`scripts/qualify_teaching_content.py` | 材料预检→四步采集→签名/输入复核→可导入 manifest；本地检查点、OS 锁及签名结果恢复；不确定调用不重发，不直接发布。采集凭据默认空，非后台队列系统 |
| 教学运行时 | `services/teaching_runs.py`、`tasks/teaching_tasks.py`、`api/v1/teaching_runs.py` | AgentRun/Step/Event、租约、取消、事件恢复与队列派发 |
| 任务对话（P02.1） | `services/teaching/dialogue.py`、`schemas/teaching_dialogue.py`、`models/v2_runtime.py`、同一 run 服务 | 新 messages 入口复用既有运行机制；任务独立历史、当前权限投影、揭晓后带引用/草稿建议的模型回复；持久消息与短期执行日志分离。开关默认关闭，新迁移仅隔离演练 |
| 流式导师回复（P02.2） | `services/teaching/streaming.py`、`teaching_gateway.py::stream_tutor_reply`、`teaching_runs.py::_stream_turn`、`models/v2_runtime.py::TeachingMessageBlock` | 纯文本 `[n]` 引用 + 有序不可变块；每块独立短事务发布，`message.block` 事件；用量 `reported/missing/unknown`；默认关闭，关闭时回到 P02.1 非流式 |
| 独立聊天（P02.3） | `api/v1/tutor.py`、`services/tutor_conversations.py`、`services/teaching/dialogue.py`、`models/v2_runtime.py::TutorConversation` | `/api/v1/tutor/conversations` CRUD 与回合；聊天可无任务、可关联多个教学会话；旧 `/teaching/sessions/{id}/messages` 同源；无任务回复走导师别名且无引用；默认关闭 |
| 四题小测与命令层（P02.4） | `services/teaching/service.py::create_quiz`、`services/teaching/commands.py`、`api/v1/teaching.py` | 小测即同一 `TeachingSession` 的 4 个 `TeachingItem`，进度由 attempts 投影；`POST /teaching/quizzes` 与 `POST /teaching/sessions/{id}/actions` 是唯一写入口，只接受 `user_ui`；零新表、不调用模型；默认关闭 |
| 外部接入 | `integrations/mcp/server.py`、`services/external_connection_service.py` | opaque 凭据、scope、过期/轮换/撤销；共享教学服务 |
| V2 开放控制 | `services/v2_access.py`、`models/v2_runtime.py` | 功能开关、白名单、账号有效性；不是现成的商业会员准入 |
| 收款与会员 | **已下线（2026-11）** | 会员收费链路整体删除（端点/服务/任务/表/配置）；全站功能对登录用户免费，本表其余能力不受影响 |
| 个人资料与互动 | `api/v1/favorites.py`、`notes.py`、`channels.py`、`learning.py` | 收藏、笔记、订阅、观看/学习历史；不复制内容主体 |
| 运营与通知 | `api/v1/admin.py`、`feedback.py`、`notifications.py`、`services/notification_service.py`、`notification_transport.py`、后台 services/tasks | 通知创建与传输分离，调用者提交后推送；系统配置、反馈公告及人工操作 |
| 档案与统计 | `services/learning_event_service.py`、`event_contract.py`、`profile_service.py`、`admin_stats.py` | LearningEvent、用户聚合、后台读模型；record_event 供必达事实，emit_event 保留旧生产者的容错入口；不能反写正式成绩 |
| 导出与注销 | `services/account_data.py`、`tasks/account_tasks.py` | 个人数据披露、删除编排与网关生命周期意图 |

## V2 已提交试做与待补能力

已存在的内容模型包括 `ExamAnalysisRevision`、`ExamEvidence`；教学事实包括 `TeachingSession`、`TeachingItem`、`TeachingAttempt`、`UserQuestionDisclosure`、`TeachingOperation`、`TeachingFeedback` 和 `LearningEventOutbox`。定义见 `models/teaching.py`。

运行/接入模型包括 `TeachingAccessGrant`、`ExternalConnection`、`ExternalCredential`、`AgentRun`、`AgentStep`、`AgentRunEvent`、`GatewayLifecycleIntent`。定义见 `models/v2_runtime.py`。以上均已提交在 HEAD；仍可整体替换，不强制保留表和实现。如果存在已迁移数据库或外部消费者，先处理其数据与兼容，不并存两套同义事实源。

- 已有教学 HTTP、run 创建/查询/取消/SSE、外部连接管理与 MCP 工具代码；不能写成“尚无后端”。
- 当前教学题面 schema 的题型为 reading，不能把目录存在理解为听力/判断/视频教学均已支持。
- run 创建当前限制为 `user_ui`；双推理模式中的外部托管老师能力不能宣称现有接口已开放。
- 兼容 cards 路径仍由 `teaching_gateway._choose_intent` 选三种 intent；新增 conversation 路径使用受限文本和引用输出，并复用预算出口。尚无揭晓前自由教学、受控工具循环或 token 流式输出，不能认定完整导师目标已实现。
- P01.1 已把模型上下文从临时卡片 dict 切到共享 v1；没有因此新增自由对话、记忆、外部托管或真实内容发布能力。契约归属及验证见实施记录。
- P01.2 补齐发布操作流程、版本与审计，并复查题库来源的锁边界；尚未认证真实素材或网关收据，不能据此把内容记为已验收。CLI 不再绕过发布回执直接写内容 revision。
- P01.3 已补签发与验签，P01.4 已补服务器工具的计划/采集/恢复；真实模型族确认、预算和材料依据仍未核验，不能把合成上游链路当作真实素材合格。后台异步核验/收据查回仍待建设。
- 当前 MCP scope 没有个人记忆 CRUD；在 app/migrations 中未检索到 `personal_memories`/`memory_sources` 等实现。个人记忆仍需新增。
- 完整 CLI/Skill、公开授权和四宿主端到端能力需逐项验证；协议适配存在不等于真实兼容通过。
- 网关与旧 AI/翻译出口的统一迁移仍需消费者清单；不能假定所有历史调用已走网关。
- 跟读、周报等已退役端点保留 410 兼容壳，见 `services/retired_features.py`；精简不能把它们复活，也不能无消费者核查直接删除兼容入口。

## 已有验证落点

`backend/tests/test_architecture_invariants.py` 保护架构不变量；教学见 `test_teaching.py`、`test_teaching_pg.py`；运行时见 `test_v2_runtime.py`、`test_v2_runtime_pg.py`；流式与惰性边界见 `test_teaching_streaming.py`、`test_teaching_streaming_pg.py`、`test_v2_schema_gating.py`；独立聊天见 `test_tutor_conversations.py`；另有 `test_teaching_gateway.py`、`test_mcp_adapter.py`、`test_v2_account_data.py`、考试快照测试及 `backend/scripts/check_v2_gateway.py`。

审查期实际执行项见审查结论；重构期新增验证见实施记录。不复用之前原型的测试结论，也不将旧报告中的“通过”当成本轮通过。
