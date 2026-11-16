# 当前框架与关键链路

审计起点：`a93979c34dab7b8fb7a5493f76b63a28e58d48ac`，2026-11-14（北京时间）。这是**本地代码现状**，不是生产部署证明，也不是新大纲的目标架构。具体文件职责和直接依赖见 [文件索引](file-catalog.md)，风险见 [审计结论](README.md)。2026-11-16 已按当前未提交工程更新处理代次、认证故障策略和用户壳；本轮验证边界认[验收卡第 5 节](../evidence/open-learning/acceptance-cards.md#5-前端重设计与后端补齐--2026-11-15)。

## 1. 先用一张文字地图理解它

```text
学习者浏览器
  └─ Next.js 页面（frontend/src/app）
       ├─ 用户/管理员各自的会话与 API 客户端
       ├─ 页面 → 组件 → Hook / Zustand → /api/v1
       └─ /media、/api：开发时 Next 转发，生产时 nginx 转发
                     ↓
FastAPI（backend/app/main.py）
  ├─ api/v1：身份、输入与输出；services：业务规则
  ├─ schemas：接口格式；models：数据库中的表
  ├─ PostgreSQL：内容、个人记录、草稿/修订、持久派发意图
  ├─ Redis：缓存、限流、令牌撤销、通知、Celery 消息与结果
  └─ Celery 云端 worker / beat：后台执行与周期调度
        ├─ celery：视频首尾、首页生成、通知、导出、清理
        ├─ teaching：默认不启动的教学运行 worker
        └─ transcription_gpu → 独立 GPU 机 → HTTP 回调云端

独立离线线：SLCS JSON 包 → backend/slcs 读取器 → CLI / 可选 stdio MCP
可选模型线：教学服务 → 薄适配层 → LiteLLM → usage shim → 供应商
旧内容生成线：AIService / TranslationService → 当前配置的兼容供应商
```

这里没有微服务注册中心，也没有 React Query/SWR。GPU worker 是真正独立的运行组件；`backend/slcs` 是真正可以单独打包的 Python 库；V2 的很多目录仍在同一后端进程、同一个业务数据库里。

## 2. 技术栈与入口

| 部分                       | 代码事实源                                                                                                                                             | 初学者的理解                                                                     |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| Python 3.12 / FastAPI      | [main.py](../../backend/app/main.py)、[requirements-cloud.txt](../../backend/requirements-cloud.txt)                                                   | API 收请求、返回 JSON；不是整个程序只跑一个文件                                  |
| SQLAlchemy async / Alembic | [database.py](../../backend/app/core/database.py)、[迁移目录](../../backend/migrations/env.py)                                                         | 前者读写数据库，后者按版本改变表结构                                             |
| PostgreSQL 16 / Redis 7    | [生产 Compose](../../docker-compose.prod.yml)                                                                                                          | PostgreSQL 保存长期事实；Redis 既有缓存又有不能当临时缓存随意清空的队列/撤销状态 |
| Celery                     | [celery_app.py](../../backend/app/tasks/celery_app.py)                                                                                                 | worker 干活；beat 定时发活；只启动 worker 不会自动有定时任务                     |
| Next.js 16 / React 19 / TS | [package.json](../../frontend/package.json)、[next.config.js](../../frontend/next.config.js)                                                           | App Router 按目录组织网址，`proxy.ts` 是登录墙                                   |
| Tailwind v4 / Zustand      | [globals.css](../../frontend/src/app/globals.css)、[user-ui.css](../../frontend/src/app/user-ui.css)、[stores](../../frontend/src/stores/authStore.ts) | CSS 变量负责主题；store 管理客户端共享状态                                       |
| Astryx / StyleX            | [AstryxProvider](../../frontend/src/components/common/AstryxProvider.tsx)、[用户壳](../../frontend/src/app/%28main%29/MainLayoutInner.tsx)             | 用户壳统一提供主题；词汇与课程搜索渐进接入，后台共享控件没有整体替换             |
| WhisperX / faster-whisper  | [独立转录实现](../../gpu-worker/gpu_worker/transcription/__init__.py)                                                                                  | 前者逐词对齐，失败可回退；API 镜像不安装 GPU 栈                                  |
| SLCS                       | [包元数据](../../backend/slcs/pyproject.toml)、[最小规范](../slcs/README.md)                                                                           | 一份可离线读取的学习材料契约；不是网站全部数据格式                               |
| nginx / Docker Compose     | [nginx.ssl.conf](../../nginx.ssl.conf)、[生产 Compose](../../docker-compose.prod.yml)                                                                  | 对外入口、转发、静态文件与多进程装配                                             |

版本请读清单与锁文件，不把报告里的“大版本”当锁。`frontend/package.json` 有版本范围，实际安装取 `package-lock.json`。

## 3. 目录分工与依赖方向

### 后端

- `api/`：HTTP 身份和参数边界。**不是所有路由都只剩薄壳**；`videos.py` 等仍有大量操作编排。
- `schemas/`：Pydantic 请求/响应模型，决定浏览器看得见哪些字段；改这里要追前端 DTO。
- `services/`：用例和纯规则混合存在。多个服务仍会自行提交，不能假设“service 永不 commit”。
- `models/`：映射表集中注册于 `models/__init__.py`；不能删 import 后指望 Alembic 仍识别该表。
- `tasks/`：持久工作和定时调度的入口。任务名字符串是跨进程契约，不一定等于当前模块路径。
- `core/`：配置、连接、错误、安全、日志等共用基础。`config.py` 中有启用收据时的惰性服务导入，不是严格无上层依赖的纯基础层。
- `migrations/versions/`：有序迁移包含旧功能的建表和后来的删表，旧迁移不是“旧功能死代码”。本轮新增 nullable 视频／派发处理代次列，单 head 为 `d7e21b4c9f84`；运行目标仍须以实际 `alembic heads/current` 核对。
- `scripts/`：人工维护、导入、播种、签名、审计工具，不会自动随 API 启动。运行前先看是否会写库/发消息/调用模型。
- `slcs/` 与 `slcs_tests/`：独立库和安装制品测试。`app/slcs`、`video_learning_material.py` 是兼容导入层，不是第二个读取器。

### 前端

- `src/app/(main)`：普通用户的页面和共享导航壳；括号不出现在 URL。
- `src/app/(admin)`：管理会话及后台；登录页不在管理工作台壳里。
- `page.tsx` 是页面，`layout.tsx` 是套在子页面外的壳或 metadata/provider；不能因为 layout 没 UI 就删。
- `[id]`、`[slug]`、`[lessonId]` 是动态参数，不是真实文件名占位。
- `components/`：页面拼装块；`hooks/`：有状态交互逻辑；`lib/`：API、格式化、规则与纯函数；`types/`：DTO；`stores/`：共享状态。
- `*.test.ts` 是 Vitest 单测；`e2e/*.spec.ts` 是 Playwright 实际浏览器回归。两者不能相互代替。
- `public/`、`src/app/favicon.ico`、`icon.png`、`apple-icon.png`：公开资源或 Next metadata 约定入口，不要求显式 import。`icon-192.png`/`icon-512.png` 目前只是备用导出；当前未接 manifest，Next 不自动识别这种命名，不能把所有 icon 文件都算已接线。

### 基础设施与工具

- `deploy/redis`：Redis 持久化和云端/GPU ACL 模板，实际密码文件不入库。
- `deploy/v2-gateway`：候选网关、适配器、供应商桩、反向隧道、运行模板和本地合成演练。镜像与治理状态读 `image-lock.json`，不是凭目录存在就已经开放。
- `scripts/backup`：备份/恢复；恢复参数可以删库，绝非普通检查脚本。
- `scripts/isolation`：带容器重建和卷删除的独立演练，不能指向业务环境。
- `.github`：CI 与依赖更新；`.claude`：本地启动/停止/部署技能和预览配置，不属于产品接口。

## 4. 数据不是一大坨 JSON

| 领域      | 主体事实                                                 | 派生/关系                                                  | 重构时别混淆                                                 |
| --------- | -------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| 用户      | `users`、`user_preferences`                              | 角色、封禁、改密时间、注销请求                             | 用户和管理员是同一个用户模型、两套浏览器会话                 |
| 视频      | `videos`、`subtitles`                                    | 标准版本、修订、质量/评分、派发 outbox                     | 源视频、可播放媒体、字幕、已发布状态不等同                   |
| 个人学习  | `vocabulary`、`study_sessions/items`、`learning_records` | 词集、收藏、笔记、订阅                                     | 单词掌握状态不是课程正文，播放进度不是掌握                   |
| 事件/统计 | `behavior_events`、`learning_events`                     | 学习档案、streak、mastery 快照、后台指标                   | 原始点击与服务端学习结果不同；聚合可重建，成绩不能被统计反写 |
| 考试      | `exam_papers/questions/sessions/answers`                 | 题面冻结快照、题目暴露事实                                 | 当前题库可变，不得用新答案重判历史                           |
| 词句语料  | `exam_sentences/words/freq`                              | 词卡例句与频次                                             | 与正式试卷作答是两套用途                                     |
| 听力      | `listening_sessions`                                     | 字幕句冻结、草稿、逐词 diff                                | 视频删除不应抹掉冻结历史，媒体不可用仍可能无法重听           |
| 首页编辑  | 草稿、不可变 revision、单例布局三张表                    | 来源指纹、前一版、生成占位                                 | 保存草稿不是发布；位置不是内容本身                           |
| 课程      | `lessons/revisions/operations/progress/activities`       | 词汇来源锚点、复习事实、导师锚点                           | 不建在 `videos` 行上；引用要固定修订和段/词                  |
| 教学 V2   | 内容修订、evidence、session/item/attempt、disclosure     | 幂等 operation、outbox、run/step/event、chat/message/block | 模型建议不是正式作答；一次执行不是一份长期聊天               |
| 生命周期  | 导出任务、媒体清理队列、gateway 意图                     | 文件与外部凭据的后续动作                                   | 删用户行不等于删完文件或外部数据                             |

完整表名、外键和各文件对应关系在 [机器清单](inventory.json)。外键只是结构引用，不代表每一条业务权限都由数据库自动保证。

## 5. 关键链路：从按钮到数据

### 5.1 登录、续签与媒体

`login/register` → `authStore` → `lib/api` → `auth.py` → SMS/密码校验 → JWT → `authHelpers.setSession` 同写 localStorage 与 cookie。普通请求带 Bearer；`proxy.ts` 只看 cookie 是否非空，因此**通过登录墙不等于后端已授权**。

后端 `dependencies._authenticate` 共用 token 类型、撤销、改密、账号存在和封禁校验；媒体/PDF/通知握手通过 `resolve_token_user` 复用。媒体 URL 的 query token 必须脱敏；日志不能记整条查询串。JWT 支持的 HMAC 算法由配置约束，并非永远硬编码 HS256。

续签使用 Redis `SET NX` 原子消费旧 refresh；Redis 故障返回明确 503，不签发后继 token。撤销写入也必须得到确认；客户端立即清本机会话，但服务端未确认时在登录页保留警告。禁用黑名单或缺少 JTI 不伪称远端撤销成功。普通 access 黑名单读取仍保留 fail-open；改密／封禁等 DB 校验不变。用户和管理端 API 的 GET 缓存按 client、token、URL 隔离，异步刷新与退出导航按会话 epoch 防止旧请求复活或覆盖新登录。

### 5.2 视频生产

管理员/catalog → `video_seed_service` → `process_video`（云端 head）→ 元信息/本地源 stage → `pipeline_dispatch.enqueue` 与视频状态同事务 → Redis GPU 队列 → 独立 GPU 转录 → `internal.transcription_callback` → 共享密钥、锁、质量门 → 字幕与 tail 意图同事务 → `finalize_video`。

Tail 顺序由 `finalize_steps` 定义：翻译、注释、词注预热、分类、下载、转码、完成/发布及衍生指标。下载失败可以走受支持的原站嵌入回退，并非“没下载文件就一定不能发布”。看门狗负责超时标错；beat 的 outbox 补发负责未发出的任务，两者不能相互代替。

派发是**至少一次**而非 exactly-once。首次生产、开始、恢复、重试／重译和自动下载重试均复用 outbox；视频状态与意图同事务，broker 故障保留待派发，不靠第二次提交补偿已清译文。服务端 `processing_generation` 贯穿 head、GPU 原任务名消息、回调、tail 与 outbox；旧缺代次消息仅能匹配 legacy NULL 行，不能默认认领新轮次。worker 自己的 session 在 ORM flush、显式 DML 与 commit 前锁视频并校验数据库代次；超时、重试、下架会使旧轮次失效。Redis 锁／完成标志与媒体 raw／转码／封面按代次隔离；媒体路径仍提取原视频 UUID 做实时权限检查，临时产物不对外服务。代次不是课程修订或内容指纹，也不把 Redis 锁当 exactly-once。正常任务的锁由任务显式交接，session 退出不重复释放；已提交 ready 的 tail 重投只补终态／自动发布，不重新翻译或转码。上线切换仍须先停旧二进制 worker、核对迁移并同步 GPU 协议；新代码兼容旧消息不意味着未加 fence 的旧进程也会被自动保护。

### 5.3 看视频、点词、保存、复习

观看页 → `useVideoPlayer`（本地视频/YouTube）→ `watchStore` 当前句、播放器与字幕跟随 → `useWordLookup` → `/words` 静态 ECDICT 与预生成注释/真题例句 → 收词写 `Vocabulary` → `vocab_set_service`/`study_session_service` 形成可恢复轮次 → `vocabulary_service` 统一更新复习状态 → 必达 `LearningEvent` 同事务。

播放位置由 `watch_progress_service` 保存；可见且播放中的墙钟学习时长由客户端事件产生，聚合读 `study_time_service`。不要把历史累计计数按最后访问日切成“本周学习时长”。

复习主要是错误次数分档算法；SM-2 仍作为旧练习支路存在。改变算法之前先盘各调用点和历史状态，而不是按 `sr_service` 文件名判断全站都用 SM-2。

### 5.4 考试与听力

考试：创建 session 时冻结题面 → 交卷条件 UPDATE 原子认领 → 服务端按冻结题判分 → 成绩和学习事实同事务 → 重复交卷重放首次结果。

听力：只选已发布可播放视频的合适字幕句 → 冻结题目 → 提交前去掉原句/译文/解析 → 存草稿 → 先账号锁再 session 锁 → 服务端归一化和逐词 diff → 结果与学习事实同事务。锁顺序是为防并发死锁，不是无用的繁琐代码。

词汇练习的客户端自评另见 R04，不能照搬为考试判分。

### 5.5 首页内容发布

管理员选视频 → 草稿状态机原子占位 → Celery 生成 → schema 与来源校验 → generation id/草稿 revision/字幕指纹三重比较 → 保存候选 → 显式发布不可变 revision → 布局引用该 revision → 公共读取每次重算有效性，失效则提升次推或回旧首页兜底。没有公开的 draft 绕过入口。

### 5.6 SLCS 与课程发布

离线包先由 `slcs.contract` 校验，再由 `slcs.material` 投影；CLI/MCP 复用读取器。站内课程导入是新域，不是直接“把 JSON 写到 videos”。管理审核分别记录站内展示/模型用途等权限；发布需要外部 Ed25519 收据。后端只持公钥，签发脚本私钥在仓库外。

课程当前版与固定修订读取不同；撤回立即挡住后续正文读取，保留学习事实和引用，不声称能收回下载包。课程收据与教学内容核验收据的 audience/配置不同，不能互换。撤回操作将本轮撤回 ID 写入审核元数据；恢复必须重新审核，审核哈希绑定本轮撤回及唯一审核操作，撤回前未用收据也不能恢复。普通旧版回退继续用原 CAS 发布。管理端 `lesson_diff` 按稳定段／词 ID 显示正文、译文、时间、来源和词汇差异，不修改包。

`lesson_catalog` 是课程只读用例的唯一实现：站内 HTTP、外部 HTTP 与 MCP 共用按当前用途和身份投影的检索／固定引用解析。线上修订与包指纹映射已有唯一约束；查询当前版和解析固定引用不同，不自动跨修订重定位。具体输入／输出和在线支持边界认[接口契约](../open-learning/api.md)。

### 5.7 教学、聊天、MCP

HTTP、CLI、MCP 的身份由服务器推导，进入同一教学规则。作答/提示/揭晓等确定性动作有 operation 幂等回执；模型只能建议。对话持久化在 conversation/message，执行恢复在 run/step/event，流式正文在不可变 block。

开关默认关闭；课程开关与 V2 访问白名单不是同一道门。`/admin/teaching-content` 只有管理员鉴权，不受用户 V2 开关控制；`/admin/lessons` 同时受课程门限制。关功能不等于 ORM 可以运行在旧 schema 上。

新 `/external-learning` 和对应 MCP 工具复用 `delegated_learning`：独立 opaque token 与连接行锁、明确资源 grant、按连接 namespace 的幂等回执；连接用途随 grant 绑定，默认模型用途，不能靠改走 REST 降级；本人显式创建的应用用途连接禁止用于模型披露。复习／完成须第一方确认短期参数绑定，不能相信模型自述。新增 grant／intent／operation 独立表各自做 schema 检查，不往旧连接新增必读列。收词和进度仍复用原服务，复习仍用原 S6；位置冲突版本来自单调更新的 UTC 时间戳。未消费意图由独立 beat 清理，已消费最小墓碑与回执保留至账号注销，重放重新检查当前权限。

网关账本属于 LiteLLM；旧翻译/注释/首页生成仍有直接兼容 provider 路径，尚未统一成一个模型出口。真实模型质量、账单/跨午夜治理与宿主兼容不能从 mock 测试推断。

### 5.8 导出与注销

`users.py` 建导出任务 → Celery 收集本人数据 → 受控投影 → ZIP → 短期/单次下载。请求注销保留冷静期，beat 到期清理用户关系；媒体清理意图和删用户在同一事务写入，文件删除失败可重试。外部 gateway 凭据有生命周期意图，不能靠删本地连接行当作远端已经撤销。

## 6. 如何跑，如何别误跑

仓库根没有 package.json/Makefile。启动整体服务使用 `.claude/skills/dev`；轻量 API/前端入口仍是 `Start-Redesign.ps1`。本机 Python 必须 `PYTHONUTF8=1`。详细命令与本机限制分别集中在 [后端规则](../../backend/CLAUDE.md)、[前端规则](../../frontend/CLAUDE.md)、[GPU 运行说明](../../gpu-worker/README.md)。

| 装配文件                        | 实际用途                                                                         | 不是什么                                                   |
| ------------------------------- | -------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `docker-compose.yml`            | 开发全栈；teaching 为 profile                                                    | 不带 beat/GPU 的完整生产拓扑                               |
| `docker-compose.dev.yml`        | 只起开发 DB/Redis                                                                | 不启动 API                                                 |
| `docker-compose.prod.yml`       | 单机生产应用及可选 gateway/teaching profile                                      | 不包含独立 GPU worker                                      |
| `docker-compose.selfhost.yml`   | 无官方模型／GPU 凭据的 production 基础装配，含 worker／独立 beat／失败即停迁移门 | 不附官方语料、不开生产短信 fake；不是现有生产站部署授权    |
| `docker-compose.smoke.yml`      | 旧 testing 配置的生产镜像/HTTPS 隔离 smoke                                       | 不能证明无模型 production 基础模式，也不能指向远程生产账号 |
| `docker-compose.isolation.yml`  | Redis ACL/恢复与专用 PG 演练                                                     | 不能当可删的开发库                                         |
| `docker-compose.v2-gateway.yml` | 合成 provider 的网关验证                                                         | 不是生产模型治理已放行                                     |

生产是 standalone Next + nginx，开发代理只在 next dev 生效。生产 `.env` 的值必须列在 Compose environment 中才会透传；`NEXT_PUBLIC_*` 在前端构建期固定。

正常 entrypoint 的迁移失败会记错后继续启动；发布必须先用 `migrate-only` 非零即停，并核对 revision。健康检查主要探 DB/Redis 连通，不能替代 schema/worker/beat/完整产品验证。发布只走当前 deploy skill；数据库破坏性迁移后不能只回退镜像就假设兼容。

源码自托管的唯一操作说明是[自托管安装与升级](../self-hosting.md)。基础配置显式关闭 `LLM_ENABLED`／`CONTENT_PRODUCTION_ENABLED`，相关模型出口、生产派发与回调失败关闭；能力默认值仍保留既有开启路径的安全要求。JWT、显式 DB/Redis、生产短信 fake 禁止不随之放宽。基础栈仍需真实 worker 与独立 beat 执行本人导出、到期注销和意图清理，不能以“页面能读”代替生命周期。

## 7. 当前不应恢复的东西

- 跟读/周报/热力图/成就/里程碑等旧入口有 410 兼容壳；历史录音文件与历史 milestone 数据不等于功能仍开放。
- 收费、会员、订单、购买/升级/解锁、人工付费管理链路已整套删除；不要从旧迁移的建表语句“恢复功能”。
- `/weekly-report` 是兼容跳转；`usePlan`/`learning_plan` 这些名字主要指档案，不意味着每日计划功能仍在。
- 无普通用户视频投稿链路；管理/catalog 才能生产视频。

## 8. 重构时必须一起看的组合

| 想改哪里      | 最小一起检查的消费者                                                       |
| ------------- | -------------------------------------------------------------------------- |
| 错误格式      | `core/errors.py`、`main.py`、`createApiClient.ts`、契约测试                |
| 登录/权限     | dependencies、auth、媒体/PDF/WS、proxy、双 store、authHelpers              |
| 视频状态/任务 | head、GPU contracts/tasks、callback、tail、outbox、watchdog、后台轮询      |
| 字幕 ID/分段  | 编辑服务、重映射快照、收藏/词汇/笔记、首页指纹、播放器深链                 |
| 复习事实      | vocabulary、study_session、practice、sr、LearningEvent、overview/导出/注销 |
| SLCS 契约     | reader、schema、参考包/负例、指纹、发行器、安装制品测试                    |
| V2 表或列     | models、迁移、考试 exposure、导出/注销、beat、MCP/网关/前端入口            |
| 前端 UI       | 用户作用域 token、现有公共组件、Astryx 作用域、响应式/键盘/e2e             |

不要先建一层全新的同义系统，再把旧系统“慢慢迁过去”；优先用一个端到端用例确定事务、权限和事实归属。
