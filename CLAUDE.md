# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目速览

**SeeWord** — 视频 + 字幕逐词点读的英语学习站。用户看视频、点单词查义、重听原句、做词汇复习与四六级试卷。

- 后端：FastAPI(Python 3.12) + SQLAlchemy 2.0 async + Celery + Alembic，源码在 `backend/`
- GPU 转录 worker：已从 backend 拆成**独立组件** `gpu-worker/`（自带 `.venv`、`.env.gpu-worker`、requirements 与 NSSM 服务，不 import `app.*`），只消费 `transcription_gpu` 队列并回调云端
- 前端：Next.js 16 App Router + React 19 + Tailwind v4 + Zustand，源码在 `frontend/`
- 基础设施：Postgres 16 + Redis 7（Celery 的 broker 和 result backend 都用它）
- 部署：单机 docker compose + nginx 反代；转写另跑在一台无 DB 的 GPU 机器上（就是 `gpu-worker/`）

**仓库根没有 `package.json`，也没有 Makefile。** 所有命令都要先进 `backend/`、`frontend/` 或 `gpu-worker/`。子包各自的约定见 [`backend/CLAUDE.md`](backend/CLAUDE.md) 与 [`frontend/CLAUDE.md`](frontend/CLAUDE.md)；GPU worker 读 [`gpu-worker/README.md`](gpu-worker/README.md)。

## 命令速查

| 目的                | 命令                                                                                   | 工作目录    |
| ------------------- | -------------------------------------------------------------------------------------- | ----------- |
| compose dev 栈      | `docker compose up -d`（db/redis/backend/celery/frontend；无 beat、无 GPU worker；V2 教学 worker 只在 `--profile teaching` 下起） | 根          |
| 轻量本地启动        | `.\Start-Redesign.ps1`（只起 API+前端+DB/Redis，无 Celery/GPU）                        | 根          |
| 只起 DB + Redis     | `docker compose -f docker-compose.dev.yml up -d`                                       | 根          |
| 后端 API            | `uvicorn app.main:app --reload --port 8000`                                            | `backend/`  |
| Celery worker       | `celery -A app.tasks.celery_app worker --loglevel=info`                                | `backend/`  |
| Celery beat         | `celery -A app.tasks.celery_app beat`                                                  | `backend/`  |
| GPU worker（GPU 机） | `powershell -File scripts\run_gpu_worker.ps1`（加载 `.env.gpu-worker` 后用本目录 `.venv` 启动） | `gpu-worker/` |
| 跑迁移              | `alembic upgrade head`                                                                 | `backend/`  |
| 后端测试            | `pytest tests/ -v`                                                                     | `backend/`  |
| 跑单条后端测试      | `pytest tests/test_auth.py::TestUserProfile::test_get_me_without_token_returns_401 -v` | `backend/`  |
| 后端 lint / 格式    | `ruff check app/ tests/` · `ruff format app/ tests/`                                   | `backend/`  |
| GPU worker 测试     | `.venv/Scripts/python.exe -m pytest tests -q`                                          | `gpu-worker/` |
| GPU worker lint     | `.venv/Scripts/ruff.exe check gpu_worker/ tests/ scripts/`                             | `gpu-worker/` |
| 前端 dev            | `npm run dev`                                                                          | `frontend/` |
| 前端单测            | `npm run test:unit`                                                                    | `frontend/` |
| 跑单个前端单测      | `npx vitest run src/lib/createApiClient.test.ts`                                       | `frontend/` |
| e2e                 | `npx playwright test`                                                                  | `frontend/` |
| 跑单个 e2e          | `npx playwright test e2e/watch.spec.ts`（或 `-g "标题关键词"`）                        | `frontend/` |
| 前端门禁            | `npm run check`                                                                        | `frontend/` |
| e2e 数据播种        | `python scripts/seed_e2e.py`                                                           | `backend/`  |

`npm run check` = design-system 检查 + 会话写入检查 + `tsc --noEmit` + ESLint + Prettier `--check`。后两个检查器都是「机器执行的不变量」，见 [`frontend/CLAUDE.md`](frontend/CLAUDE.md)。

`.\Start-Redesign.ps1` 是改版交付的轻量启动入口：复用已跑的端口，只拉起 backend :8000 + Next :3000 + Docker 的 DB/Redis，**不拉 Celery/GPU worker**；需要转写或定时任务时仍用 `/dev`。

> 本机是中文 Windows：启动任何后端 Python 进程都要带 `PYTHONUTF8=1`（云端用 `backend/.venv/Scripts/python.exe`，GPU worker 用 `gpu-worker/.venv/Scripts/python.exe`），否则读取 UTF-8 的 `.env` 会直接 `UnicodeDecodeError: 'gbk' codec` 启动失败。原因与其余本机坑见 [`backend/CLAUDE.md`](backend/CLAUDE.md)，GPU worker 侧见 [`gpu-worker/README.md`](gpu-worker/README.md)。`/dev` skill 已内置。

### 优先用 skill，别照上表手敲

`.claude/skills/` 里三个 skill **已入库**，本机（中文 Windows + NSSM 服务）的坑都在里面，别自己重新踩：

| skill       | 干什么                                                                                                                                                                          |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/dev`      | 起／重启本地全栈：uvicorn :8000 + 云端 Celery worker + GPU worker + Next :3000 + Docker 的 DB/Redis。用户说「重启服务」就是它——它会先清端口、清 `.next`，**重启不是另一套流程** |
| `/dev-stop` | 停本地 dev（加 `--infra` 才连 Postgres/Redis 容器一起停）                                                                                                                       |
| `/deploy`   | 发生产：本机构建 amd64 镜像 → 上传校验 → 迁移 → 切容器 → 核验；回滚点、nginx reload、脏树停机等约束都在里面                                                                     |

上面那张表是「只起一件东西」或排查时用的原始命令，不是推荐入口。前端相关的运行方式与 `dev` 代理前提见 [`frontend/CLAUDE.md`](frontend/CLAUDE.md)。

**部署与主机访问**：生产机与 GPU 机怎么连、某个 secret 放在哪台机的哪个文件、迭代证据分别在哪个目录，
写在本机 `~/.seeword/ACCESS.md`（仓库外，含路径不含凭据）。本仓库不保存任何密码或私钥。

## 架构大图

以下都是读多个文件才能拼出来的部分；单个文件的结构直接打开看即可。

### 后端装配与错误契约

`backend/app/main.py::create_app()` 是唯一入口，模块底部 `app = create_app()`（认符号别认行号，行号会漂）。三个自定义 `@app.middleware("http")`：request-id 注入、请求日志、安全头（生产才加 HSTS 与 CSP）。Prometheus 走 `Instrumentator`，`/health` 会真探 DB 与 Redis 并在任一不健康时返回 503。

**所有错误响应都是统一 envelope** `{code, message, detail?}`：

- 业务代码抛 `AppError(status_code, code, message, detail?)`，`code` 取 `backend/app/core/errors.py::ErrorCode`
- 存量 `HTTPException`（约 110 处 `raise`）由全局 handler 兜底转 envelope，`code = HTTP_{status}`
- 422 校验错误 → `code = VALIDATION_ERROR`，`detail` 是 pydantic errors 数组
- `AIServiceError` → 502 + `AI_SERVICE_UNAVAILABLE`，绝不退化成 500 或静默假分值

前端 `lib/createApiClient.ts` 就是按这个 envelope 解析的，改 envelope 就同时改了前端。

### 路由

全部在 `backend/app/api/v1/*.py`，注册时统一加 `prefix="/api/v1"`。**唯一例外**是 `media.router` 挂在根——它是 Range-aware 的视频服务，因为 Starlette 的 `StaticFiles` 会吞掉 Range 头，导致 `<video>` 无法拖进度。

**已下线功能不是死代码**：跟读/成就/热力图/周报/里程碑与旧录音上传的后端入口统一由 `app/services/retired_features.py::feature_gone` 返回 410 `FEATURE_RETIRED`（`api/v1/shadowing.py`、`learning.py` 的 heatmap/weekly-reports、`learning_plan.py` 的 milestones、`media.py` 的 shadowing-audio），前端 `/weekly-report` 则重定向到个人页进度 tab；这些都是兼容壳，不要「恢复」这些端点。**退役功能的用户数据表已在 2026-10-26 的清理迁移 `c3d4e5f6a7b8` 中删除**（`shadowing_attempts` / `weekly_reports` / `speaking_attempts` / `speaking_rubrics` / `rubric_criteria` / `speaking_attempt_scores` / `video_practice_questions`，以及兑换码系统 `redeem_codes`），数据导出与注销清理不再包含这些数据集；存量 `/media/shadowing/` 音频文件仍在磁盘上（仅旧媒体路由可读），需要清理由运维单独执行。

**会员收费链路是更彻底的一种「下线」**（2026-11）：不是留 410 兼容壳，而是端点、页面、服务、任务、配置与数据表全部删除（含 `/upgrade`、`/pricing`、`/checkout`、`/payments/*`、`/videos/{id}/unlock`、`/videos/unlocked*`、`/admin/payments*`、后台人工开通会员；表在迁移 `d4e5f6a7b8c9` 中删除）。`tests/test_architecture_invariants.py` 的 `DROPPED_TABLES` 与 `REMOVED_PAYMENT_ROUTE_FRAGMENTS` 守着它不许复活。

`backend/app/api/dependencies.py` 提供鉴权依赖（见下）。

### 数据层

SQLAlchemy 2.0 async。`backend/app/core/database.py` 里有两点值得知道：

- engine 与 session maker 都 `@lru_cache` **懒建**，不在 import 时建。历史动因是让没有 `DATABASE_URL` 的 GPU worker 也能 import 这些模块；GPU 段已拆进独立组件 `gpu-worker/`（不再 import `app.*`），懒建继续服务脚本与测试。
- FastAPI 路由用 `get_db()` 依赖；Celery 任务等非依赖场景用 `get_async_session_maker()`——后者同时是测试 monkeypatch 的缝。

模型在 `backend/app/models/`，必须由 `app/models/__init__.py` 按依赖序 re-export（`create_app` 会先 import 它们，好让 SQLAlchemy 在任何 `create_all`／Alembic autogenerate 前把 `Base.metadata` 填全）。迁移在 `backend/migrations/versions/`：HEAD 上 94 个 revision（含 5 个 V2 迁移）。数量会漂，别把它当契约。

核心实体：`User` 拥有 `Video` / `Vocabulary` / `LearningRecord` / `UserFavorite` / `UserNote` / `Notification`；`Video` 拥有 `Subtitle`（按 `sentence_index` 排序，含 `text_en` / `text_zh` / 逐词时间戳 `words` / `word_levels`），并冗余 `like_count` / `favorite_count` / `view_count` / `score`，以及管线状态 `status` + `processing_step` + `step_started_at`。`ListeningSession` 保存听力练习的冻结题面、草稿答案与判分结果（见下）。

另有两组容易混淆的数据：`UserLearningProfile` + `LearningEvent`（结构化学习事件，喂学习档案/目标/推荐；`learning_event_service.py` 增量更新计数与 streak，`profile_service.py` 负责按需重算 mastery/CEFR。模块名仍叫 `learning_plan`，但 ADR-0012 的每日计划已在 `d1e2f3a4b5c6` 连同表一起删除）与真题语料/试卷（`ExamSentence` / `ExamSentenceWord` / `ExamWordFreq` 供例句与高频词，`ExamPaper` / `ExamQuestion` / `ExamSession` / `ExamAnswer` 供试卷作答；原卷 PDF 走 `exam_pdfs.py`）。

### 鉴权

另有一行密码契约：新密码 8 位起、**最多 72 个 UTF-8 字节**（bcrypt 只消费前 72 字节，bcrypt ≥ 5 对更长输入直接抛错）。`security.validate_password_strength` 统一校验、schema 转 422；`hash_password` 拒绝超长而**不截断**；`verify_password` 对历史 hash 按前 72 字节比对，让旧密码仍可登录。

手机号 + 短信验证码，**没有邮箱**。`app/core/security.py` 用 PyJWT HS256 签 token（access 30 分钟、refresh 7 天，带 `jti`/`type`）。`app/api/dependencies.py` 的 `get_current_user` 会解 token、校验类型、查 token 黑名单、拒绝早于 `password_changed_at` 的 token、拒绝被封禁用户。另有 `get_optional_user` / `get_admin_user`。**2026-11 起会员收费链路整体下线**：全站功能对登录用户免费，没有 `plan` / 解锁额度 / 收款端点 / 后台付费面板，`users.plan*`、`orders`、`jinshuju_payments`、`user_video_unlocks` 均在迁移 `d4e5f6a7b8c9` 中删除；未登录仍被登录墙挡住（后端匿名详情不下发字幕与媒体 URL）。

**不走 Bearer 的入口共用同一条校验链**：媒体 `?token=`、原卷 PDF、通知 WebSocket 握手都调 `dependencies.resolve_token_user()`，而不是各自解 token——黑名单、改密失效、封禁一条不落。新增这类入口（`<video>`/`<audio>`/WS/下载）必须走它。

**GPU worker 的回调不走 JWT**，走共享密钥（见下）。

### 视频管线：head / GPU / tail 三段切分

head 与 tail 在 `backend/app/tasks/video_processing.py`，**中间的 GPU 段已拆到独立组件** `gpu-worker/gpu_worker/tasks.py`。这个切分是整个仓库最需要先理解的东西——中间一段跑在**另一台机器**上。

1. **head** `process_video`：yt-dlp 取元信息，本地上传的素材先 stage 到 OSS，然后 `celery_app.send_task(GPU_TRANSCRIBE_TASK, args=[video_id, source, platform], queue=settings.transcription_gpu_queue_name)` 入队并释放锁——云端用任务名常量入队，不 import GPU 代码
2. **GPU 段** `transcribe_video_gpu`：任务名**故意保留旧名** `app.tasks.video_processing.transcribe_video_gpu`（兼容队列里已入队的消息），实现在 `gpu-worker/gpu_worker/tasks.py`：GPU 机器上的 Celery 只消费 `transcription_gpu` 队列，跑 `TranscriptionService._sync_transcribe`（WhisperX = VAD → 批量 ASR → wav2vec2 强制对齐，失败回退 faster-whisper），完事后 POST 回云端
3. **回调** `app/api/v1/internal.py::transcription_callback`：验共享密钥 + Redis 去重锁 → 质量门 → 写 `Subtitle` → 置 `ready_subtitles`，并在**同一事务**写入待派发意图（`pipeline_dispatches` outbox），提交后立即入队 tail；派发失败不丢意图，由 beat `dispatch_pipeline_tasks` 补发（A05/BE-01）
4. **tail** `finalize_video`：翻译（`TranslationService`）→ 质量门 → ECDICT 本地查词注释 → 预热词注 → 分类 → 下载 → 转码 → `ready`，随后注册标准、自动发布、评分、难度与语速指标

`watchdog_stale_pipeline` 每 10 分钟把卡过各步骤超时的视频标失败，覆盖 `processing` 与 `ready_subtitles` 两个相位。

### Celery

`backend/app/tasks/celery_app.py` 定义 `celery_app` 与常量 `GPU_TRANSCRIBE_TASK`（值是**保留的旧任务名** `app.tasks.video_processing.transcribe_video_gpu`，task_routes 用它），三个队列：云端默认的 `celery`、远端 `transcription_gpu` 与教学 `teaching`（后两者随 V2 提交入库；teaching 队列默认没有 worker，V2 开关默认关闭，但 beat 的 `sweep-teaching-runs` 每 10 秒无条件排程，见「V2 后端重构标准」）。**只有 `GPU_TRANSCRIBE_TASK` 路由到 GPU 队列**，其余（管线首尾、本地化等）都在云端跑。GPU 侧的 Celery 应用与任务在 `gpu-worker/gpu_worker/celery_app.py` / `tasks.py`，只声明、只消费 `transcription_gpu`。beat 里挂着管线看门狗（含首页草稿生成超时巡检）、**管线派发补发（每 60 秒，`app.services.pipeline_dispatch` 的 outbox）**、失败下载重试、评分（小时/天）、内容榜单快照、自愿开启的词汇复习提醒、注销账号清理。**Pro/兑换码 beat 与周报空任务壳已在 2026-10-26 清理中删除**；2026-11 会员收费链路下线时，订单过期/对账与金数据同步两条 beat、以及 `reminder_tasks.send_pro_expiring_reminders` 任务体也一并删除（已入队的旧消息会以 unregistered task 结束，影响面可忽略）。

Windows 上这些以 NSSM 服务托管：云端 worker 用 `backend/scripts/run_celery_worker.ps1`（该脚本只起 worker；仓库没有 beat 的 NSSM 脚本，本地/生产 beat 需单独启动或由 prod compose 的 `celery-beat` 服务托管）；GPU worker 用 `gpu-worker/scripts/run_gpu_worker.ps1`，隧道用 `gpu-worker/scripts/gpu_worker_tunnel.ps1`（服务名见 [`gpu-worker/README.md`](gpu-worker/README.md)）。

### 听力练习（`/api/v1/listening` + `/practice/listening`）

- **题库不是独立数据**：`listening_service.catalog()` 从已发布、可播放的视频里挑 12–220 字符、时长 ≤20s 的字幕句，建会话时把题目冻结进 `ListeningSession.questions`；`video_id` 是 `SET NULL`，视频下架不影响历史会话与结果。
- **判分只在服务端**：`POST /sessions` 建会话 → `PUT /sessions/{id}` 只存草稿（答案/当前题号）→ `POST /sessions/{id}/submit` 判分。提交前 `payload()` 会剥掉 `text_en` / `text_zh` / `grammar_note`，`results` 恒为 `null`；提交后再 `save` 返回 409，重复 `submit` 幂等直接返回，不会重复累计。判分归一化大小写、标点与空白，给出逐词 diff 与 accuracy，并向 `LearningEvent` 发 `practiced_items`。
- 前端列表与作答分别在 `(main)/practice/listening` 与 `[id]`，播放器是 `components/listening/ClipPlayer.tsx`，DTO 契约在 `types/listening.ts`。

### 首页编辑内容（选视频→AI 草稿→预览→发布替换→恢复上一版）

后端的唯一事实源是 `backend/app/services/home_content_service.py`（视频侧草稿 / 不可变版本 /
生成状态机）、同目录的 `home_content_content.py`（来源指纹、字段级 issues、展示 DTO）与
`home_content_layout.py`（布局写入与校验、公共读取）+ `backend/app/schemas/home_content.py`；
前端 DTO 的唯一契约是 `frontend/src/types/homeContent.ts`（前后端字段一一对应，页面不得自行解释任意 JSON）。

- **三张表、内容与位置分离**：`home_content_drafts`（每视频一份可编辑草稿 + 生成状态机）、
  `home_content_revisions`（**只追加**的不可变已发布版本）、`home_page_config`（单例布局，只引用
  revision id + 稳定 expression_id/scenario_id，另有 draft/published/previous 三份供整版发布与回退）。
  编辑或重新生成草稿永远不会影响线上，直到再次发布。
- **来源指纹是失效机制**：`compute_source_fingerprint` 覆盖有序字幕 ID + 句序 + 起止时间 + 英中文本；
  生成入队、生成落库、发布、公共读取都重算比对。因此字幕被改/重排/重新断句/重新转写后旧版本自动失效，
  **不需要也不应该在每个字幕写入入口挂钩子**。
- **公共读取不走缓存**：`GET /api/v1/browse/home-editorial`（`api/v1/home_editorial.py`）每次读库，用
  `discovery_service.public_video_filters()` 判可见性，主推失效时次推可提升，全部失效返回 `{"editorial":null}`
  让前端整块退回旧 `featured + learning metadata` 兜底（旧兜底仍用既有 browse 缓存与失效链路）。
- **生成走云端 Celery**：`app/tasks/home_content_tasks.py` 的 `generate_home_content_draft` 在默认 `celery` 队列，
  状态机 `idle→queued→running→succeeded|failed`，靠原子的 `active_generation_id` 占位去重；写回前校验
  generation id / 入队草稿 revision / 入队指纹三者，任一不符即冲突且不覆盖；900s 未结束由 GET 状态与
  beat `sweep-home-content-generations` 兜底标 TIMEOUT。
- **后台预览 = 首页组件**：两个管理员 preview 接口都返回 `{page, issues}`，前端用
  `HomeEditorialPreview` 渲染与首页同一套展示组件；公共接口没有 `?draft=true` 之类绕过发布边界的入口。
- 操作说明见 [`docs/home-content-operation-guide-2026-10.md`](docs/home-content-operation-guide-2026-10.md)，
  实施契约见 [`docs/home-editorial-content-implementation-2026-10.md`](docs/home-editorial-content-implementation-2026-10.md)。

### 前端装配

Next.js 16 App Router，源码在 `frontend/src`。路由组 `(main)`（用户壳，其下有 20+ 个子 `layout.tsx`）与 `(admin)`（管理壳），另有裸路由 `login` / `register` / `forgot-password` / `set-password` / `onboarding` / `terms` / `privacy`——其中前五个各有自己的 `layout.tsx`；`(main)/browse` 是 `route.ts` 307 重定向到 `/`。

**手写 fetch 封装，没有 React Query 也没有 SWR。** `frontend/src/lib/createApiClient.ts` 是工厂，提供：仅对 GET/HEAD 的 5xx 重试（1s/2s 退避）、发请求前的 JWT 过期预检、401 单次刷新、解析上面的错误 envelope、GET 在途去重与可选 `cacheTtlMs` TTL 缓存。用户端实例是 `lib/api.ts`，管理端是 `lib/adminApi.ts`——**两套 token、两套会话**。

**token 双重存放**：真身在 Zustand `authStore` 的 localStorage，请求时带 `Authorization: Bearer`；同时镜像到 cookie `seeword_token`，让 `frontend/src/proxy.ts`（Next 16 把 middleware 改名 proxy）的边缘登录墙能读到。**登录墙只查 cookie 是否存在**，不解析 JWT、不查库，所以它挡的是"完全未登录"，真正鉴权仍在后端。因为 `<video>`/`<audio>` 发不了请求头，`mediaUrl()` 用 `?token=` 附 token（媒体及受保护的历史音频走这条路）。

**样式**：Tailwind v4 CSS-first，**没有 `tailwind.config`**。token 定义在 `frontend/src/app/globals.css` 的 `@theme {}`，语义色（`--color-canvas` / `surface-*` / `ink` / `body` / `muted` / `hairline` / `brand-*`）靠 `:root` 与 `.dark` 两套变量切换，所以暗色模式是"换变量"而不是"改类名"。**用户端还有一层 `.user-ui` 作用域**（`src/app/user-ui.css`）：`(main)` 壳挂上它之后，`--color-brand-*` / `--color-action-primary` 被覆盖为蓝色并统一圆角与版式，管理端仍用橙色 brand。改用户端视觉改 `user-ui.css`，不要动 `globals.css` 的全站 token。`hooks/useTheme.ts` + `layout.tsx` 里的内联脚本负责防闪烁。取值与组件用法见 [`frontend/DESIGN.md`](frontend/DESIGN.md)，设计依据见根 [`DESIGN.md`](DESIGN.md)。

### 配置

`backend/app/core/config.py::Settings`（pydantic-settings，`get_settings()` 带 `@lru_cache`，读 `backend/.env`）。`model_post_init` **fail-closed**：`development` 给 localhost 与开发密钥默认值；其它环境强制要 `JWT_SECRET` + `DATABASE_URL`；`production` 还要 `REDIS_URL` + `TRANSCRIPTION_CALLBACK_SECRET`，且 `OPENAI_API_KEY`、`COMMANDCODE_API_KEY`、内部 LLM 网关（`LLM_GATEWAY_BASE_URL` + `LLM_GATEWAY_API_KEY`）三选一。

**GPU 转录配置已不在 backend**：`WHISPER_*` 与 `TRANSCRIPTION_TEMP_DIR` 已从 backend `Settings` 删除，改由 `gpu-worker/gpu_worker/config.py` 的独立 `Settings` 读 `.env.gpu-worker`（重叠字段的名字与默认值与云端保持一致）。backend 只保留云端侧的回调与队列旋钮：`TRANSCRIPTION_CALLBACK_URL` / `TRANSCRIPTION_CALLBACK_SECRET` / `TRANSCRIPTION_CALLBACK_TIMEOUT` / `TRANSCRIPTION_CALLBACK_MAX_RETRIES` / `TRANSCRIPTION_GPU_QUEUE_NAME`；`backend/.env.example` 也不再列 Whisper 变量。

**LLM 接入**：provider + 模型目录 + 「哪些模型免费」+ 任务路由的唯一事实源是 `backend/app/services/llm_provider.py`（形状照 pi 的 `models.json`，裁成 env 驱动）。默认 provider 是 Command Code（OpenAI 兼容），默认模型是免费模型；`AIService`（词注释/分类/练习题/首页草稿）与翻译的 `commandcode` 引擎都从这里取模型，`LLM_MODEL_<TASK>` 可按任务换模型，`OPENAI_*` 仅作后备。巡检 `python scripts/check_llm_provider.py --list|--test`；接入手册与免费模型口径见 [`docs/llm-provider-commandcode-integration-2026-10.md`](docs/llm-provider-commandcode-integration-2026-10.md)（外部事实/调研见同目录 `llm-provider-commandcode-research-2026-10.md`）。

运行时开关有两层：env 布尔（`sms_login_enabled`、`oss_upload_enabled`、`jwt_blacklist_enabled` 等）与 DB 里的单行 `AdminSetting`（看门狗、注册开关、质量门阈值等，任务里按调用时刻读 `_effective_*`）。

**会员收费链路已于 2026-11 整体下线**（全站功能免费开放）：站内 `payments` 路由、支付宝/微信/金数据 providers、订单与收款台账、后台付费面板、`/upgrade`、`/pricing`、`/checkout` 及全部 `PAYMENTS_*` / `JINSHUJU_*` / `ALIPAY_*` / `WECHAT_*` 配置都已删除，不要再恢复。历史实施记录见 [`docs/jinshuju-payment-integration-2026-10.md`](docs/jinshuju-payment-integration-2026-10.md)（已标注下线）。

## 改版（`redesign` 分支，2026-10）

改版主体已于 2026-10-28 合并进 `master`（`55da59f0`），后缀的 GPU worker 独立拆分与迭代 4 提交也已全部在 `master` 上：远端 `redesign` 分支已于 2026-10-31 删除（当时 tip `a507e5ca`，无独有提交），本节讲的"改版"现在就是 `master` 本身。分支领先/落后数会变，现查 `git log --oneline master..HEAD`，别信写死的数字。内容以表现层、真实统计口径、听力扩展与后端审计修补为主；不恢复已下线功能。相关文件都是活文档：

| 路径 | 作用 |
| --- | --- |
| [`DESIGN.md`](DESIGN.md) | 设计依据与验收口径：视觉规范、页面布局、YouTube 参考结论、390/1440 截图要求 |
| [`frontend/DESIGN.md`](frontend/DESIGN.md) | 设计系统的**用法**（token 去哪取、组件/版式原语、断点、验证命令）；数值只认 `globals.css` 与 `user-ui.css` |
| [`PROGRESS.md`](PROGRESS.md) | 改版工作项、决策、逐轮验证记录与遗留问题；很长，按阶段标题检索，别整篇读进上下文 |
| `Start-Redesign.ps1` / `designs/` | 轻量本地启动脚本 / 设计导出原件（只作视觉依据，不作数据来源） |
| `docs/audit-2026-10-24/` | 第二轮审计报告（前端视觉、前端功能/可访问性、后端架构 31 条发现） |
| `docs/admin-audit-2026-10-26/` | 后台管理面板专项审计与清理报告（前后端审计、兑换码/退役数据表清理、管线与列表页修复、金数据收款管理面） |
| `docs/evidence/` | 验收截图与 JSON 报告：`design-redo/`、`audit-2026-10-24/`、`home-design-refresh/` 等 |

页面截图与交互走查脚本在 `frontend/scripts/design-shots.mjs`（`--tag` / `--routes`），输出到 `docs/evidence/design-redo/`。

## 常驻规则

### V2 后端重构标准（2026-11-04）

后端框架与重构验收入口见 [`refactor-blueprint/README.md`](refactor-blueprint/README.md)，包括审查结论、代码现状、模块与数据归属、接口契约、迁移任务及验收条件。按用户最新要求已开始后端渐进重构，当前范围和实际验证统一见该目录的实施记录；V2 试做已提交在 HEAD，但仍不强制保留（可整体取舍），不保留交互原型和前端设计材料。具体标准只维护在该目录，其余现有事务、安全、退役功能与发布门继续有效；本地重构不代表已经部署。

**V2 代码已提交在 HEAD（`2a07e571`），但未部署生产、未对业务库执行迁移，不是已上线能力。** `teaching` / `teaching_runs` / `external_connections` / `admin_teaching_content` 路由、`models/teaching.py`、`v2_runtime.py`、`content_publication.py`、`question_exposure.py`、`services/teaching/`、`services/teaching_gateway.py`、`services/v2_access.py`、`integrations/mcp/` 与 4 个新迁移均已入库；`TEACHING_*` / `MCP_*` 开关默认全关，用户侧 HTTP 入口经 `v2_access.require_access` 返回 503（`/admin/teaching-content` 只走管理员鉴权，不看这组开关）；MCP 是 `/api/v1/mcp` 上的 mount，`MCP_SDK_ENABLED=false` 时同一路径返回 503。开关**不是 schema 隔离**：既有考试链路已映射 `c8d9e0f1a2b3` 给 `exam_sessions` 加的列与 exposure 表，HEAD 不能跑在 V2 迁移之前的库上——部署必须与迁移同批。后台路径已按「表是否存在」保持惰性（`sweep-teaching-runs`、导出、注销、外部连接列表在缺表时不访问 V2 表，REV06 已收口），但这不是可以跳过迁移的理由。改这批代码前先读 `refactor-blueprint/docs/current-state.md` 与 `review.md`，不要把「文件存在」当成契约或已验收。

- 与用户交流用中文。
- **代码是事实源。** 注释、文档、快照都可能过期；冲突时以代码为准。
- 先验证再下结论。跑不了的检查明确写「未执行」，不写成通过。
- **浏览器检查一律用 `ego-browser`，并且要真的把服务跑起来。** 任何要看页面、点交互、核对视觉／移动端／键盘行为的检查（走查、验收、复现、QA）都用 `ego-browser` skill，不用内置浏览器工具或其它浏览器；这类检查需要站点才能验证时，先按 `/dev`（或 `npm run dev` + 后端）把服务起起来，再实际打开、点击、读取页面。**不得以「Playwright 浏览器没装／沙箱限制」为由把这类检查记成「未执行」**——那是环境问题，不是跳过浏览器验证的理由。`npx playwright test` 仍是 CI 的自动化门禁，与 ego-browser 分工不同（自动跑回归 vs 真的看一眼），两者都不能被对方替代。
- **永不为让检查变绿而放宽检查器、基线或豁免。** 具体指 `backend/.mypy-baseline`、`backend/.pip-audit-ignore`、`frontend/scripts/check-design-system.mjs`。先处理真实违规。
- 一条事实只放一个家，不跨文件复制规则。
- 用户授权只覆盖当前任务，不自动延伸到生产、删除、发布或额外系统。
- 高影响改动（契约、迁移、部署配置、不可逆操作）先理清消费者与退路再动手。

### 工作原则（2026-11-06）

- 前端质感与丝滑动效是核心要求；涉及前端的改动可以多轮截图验收打磨。
- **不重复造轮子**：优先参考对应成熟项目的源代码，而不是从零手写。
- **不做过度开发**：以优雅为原则，以用户体验为第一性原理。

### 前端文案与信息密度

- 避免不必要的次要标签、说明文字、辅助文案、描述性文字与冗余微文案——让布局、视觉层级、间距和清晰的主操作自己完成解释。
- 优先用强视觉层级与自解释的结构，而不是用文字去解释。默认不加 slogan 式文字、教学段落，也不给每个区块配「帮助说明」；确实需要补充信息时用 info 图标 + tooltip，而不是常驻的次要文字。
- 保留必要的表单标签与可访问名称——界面清爽不能牺牲可访问性。
- 危险或不可逆操作（删除、支付、提交永久性变更）必须保留清晰的后果提示。
- 去掉说明文字后，第一次使用的人仍应能看懂下一步点哪里、点了会发生什么。
- 重写已有界面时先删冗余标签与说明；若清晰度下降，再优化布局与按钮文案。
- 本仓的具体落地形态见 [`frontend/DESIGN.md`](frontend/DESIGN.md) 第 6 节「状态与文案」；两处冲突时以本节的原则为准。

### 收尾

- 每轮涉及较大代码改动的会话，在最终交付前派一个**使用当前可用最强模型**的独立子代理做代码 review；随后由主代理接力修复有效问题并验证。一轮对话通常只 review 一次，确有必要才复审，避免重复迭代。
- 有实质进展时，在根目录 `progress.txt`（不存在则创建）追加一行：`YYYY-MM-DD HH:mm（北京时间）| 工作概要`，保持简短。

## 失效指针：这些路径已不存在

2026-10-15 的提交 `a7d9d45` / `ec9688e` / `c3cbed2` 删除了整个文档与知识层——`knowledge/`、`wiki/`、`.agent/`、`CONTEXT.md`、`README.md`、`CONTRIBUTING.md` 以及各子包的 `AGENTS.md`。**代码里仍有指向它们的引用，不要去找那些文件。** 具体地：

- `backend/tests/test_architecture_invariants.py` 的 docstring 指向 `.agent/invariants.md`（已删）。**那个测试文件本身是活权威**（比如 INV-003：视频处理只由管理员/catalog 触发，没有用户投稿路径）——以测试代码为准。
- `backend/pyproject.toml` 与 `app/**` 注释里的 `INV-005` 是**活规则**：AI 调用必须走 `app.services.ai_service` 或 `app.services.translation`，由 ruff 的 `TID251 banned-api` 强制。但那份带编号的清单文件已不存在。
- `.github/workflows/ci.yml` 开头提到的「本仓审查原则第 N 条」清单已删。
- `scripts/release.sh` 里指向 `knowledge/CHANGELOG.md` 的步骤现在是断的。
- `.mcp.json` 用 PATH 上的 `aoci` 与仓库相对路径 `--repo .`；该 server 已在 `.claude/settings.local.json` 里禁用。

改这些注释里的失效指针不属于当前任务；遇到时按上面说明处理即可。

**两个例外——这两个路径现在确实存在，别当成已删的：**

- **`docs/` 已回归**（2026-10-15 `0b85160` 入库）：里面是 2026-10 起的产品/架构计划、调研、代码与 UI 评审、实施契约和验证记录（如 `architecture-fix-plan-2026-10.md`、`product-review-2026-10.md`、`oss-reference-2026-10.md`、`code-review-2026-10-20.md`、`ui-review-2026-10-21.md`、`home-editorial-content-implementation-2026-10.md`），不是被删的那批知识层。可以读（改版新增的审计报告与截图见上一节）。
- **根 `AGENTS.md` 已重建**（2026-10-17），是指向本文件的纯入口、不含任何规则。规则的家：本文件、`backend/CLAUDE.md`、`frontend/CLAUDE.md`、`gpu-worker/README.md`。

另外 `.agents/`（复数）也真实存在，但它**不是规则源**：那是 Codex 的本地镜像（`.gitignore` 忽略），里面的 `skills/` 只是 `.claude/skills/` 的旧副本（路径还写着旧机器），以 `.claude/skills/` 为准。
