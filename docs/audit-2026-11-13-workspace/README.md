# 全仓缺陷巡检：已修 / 待你决定

日期：2026-11-13（北京时间）。范围：整个仓库（backend、frontend、gpu-worker、CI、
compose/nginx、scripts、文档）。方法：14 个维度的并行扫描 + 逐条对抗式核验，
外加我自己独立跑的确定性检查（AST 反查死模块、Settings↔`.env.example`↔compose
三方对比、Alembic 链、markdown 链接、mypy 基线对比、前端两条门禁、bandit、pip-audit）。

下面分三部分：**A. 已修（未提交）**、**B. 确认有问题但我没动，等你决定**、
**C. 已核实为「不是问题」**。每条都给了可复核的位置。

---

## A. 已修（工作区未提交）

### A1 真实缺陷（会出错、会误导、或有安全隐患）

| # | 位置 | 问题 | 修法 |
|---|---|---|---|
| 1 | `docker-compose.prod.yml` SMS 段 | `${VAR:-}` 把 `ALIYUN_SMS_SIGN_NAME` / 三个模板 ID 注入成空串；pydantic 把空串当有效值，生产丢掉 `config.py` 的非空默认值 → 配了 AK/SK 也发不出短信（实测复现） | 把同一份默认值写进 `${VAR:-...}` |
| 2 | `docker-compose.prod.yml` 翻译引擎 | 引擎凭据（`TRANSLATION_QWEN_API_KEY` / `HYMT2` / `GLM_*` / `CUSTOM_*` / `PREWARM_ENGINES`）不在白名单里，宿主 `.env` 配了也进不了容器；celery 才是真正跑翻译的 | 在 backend 与 celery 两个服务补全 |
| 3 | `frontend/.../HomeContentDraftForm.tsx:151,280` | 组件曾从不随响应下发的 `subtitle.video_id` 取视频 ID；但当前两处 `SubtitleQuote` 都是 compact 模式，不渲染定位链接，因此没有可点击的 `/watch/undefined` 故障 | 改为把上层 `videoId` 透传进 `ExpressionRow` / `ScenarioRow`，避免读取缺失字段 |
| 4 | `backend/app/services/video_service.py` | 详情端点构造 `SubtitleResponse` 时漏了 `words`，管理端精确断句永远退化成按字数比例切 | 新增 `include_word_timings` 参数（仅 admin 详情传 True，且该响应不入缓存） |
| 5 | `backend/app/services/admin_service.py:196` | 管理员 PUT 显式传 `null` 阈值 → `float(None)` → 500 | 显式 `None` 当「不修改」，并补了一条回归测试 |
| 6 | `backend/app/services/ai_service.py:82` | `_get_engine_client` 只捕 `ValueError`，而 `ServiceUnavailableError` 不是 `ValueError` → 未配置引擎时逃成未处理异常 | 同时捕 `AppError` |
| 7 | `gpu-worker/gpu_worker/tasks.py:75` | 回调 `audio_duration` 取「最后一句 end」，云端再用它比字幕 → 时长幻觉检查恒真 | 用 ffprobe 实测时长（`TranscriptionService.last_audio_duration`），补了投递契约测试 |
| 8 | `backend/slcs/stdio.py:23` | camelCase 关键字触发 mypy 新增错误，CI 的基线门会红 | 改成 pydantic 字段名 snake_case（实测 alias 两种都在运行时有效） |
| 9 | `frontend/src/components/common/ErrorState.tsx:65` | `(main)` 壳内 `fullPage` 再渲染一个 `<main>`，与壳层唯一 main 嵌套 | 加 `landmark` 开关，只有壳层之上的两个 error boundary 打开 |
| 10 | `frontend/src/app/user-ui.css:149` | 全局 `:focus-visible { border-radius: 4px }` 未分层，压掉所有 `rounded-pill` / 圆形按钮的圆角 | 删掉那行（outline 本就跟随元素圆角） |
| 11 | `docker-compose.yml` celery | 与 backend 都没设 `RUN_MIGRATIONS=0` → 两个容器并发 `alembic upgrade head`（`entrypoint.sh` 注释里写明的竞争） | 给 celery 补 `RUN_MIGRATIONS: "0"` |
| 12 | `docker-compose.yml` frontend | dev 全栈里 frontend 也在容器内，`next.config.js` 的 dev 代理写死 `127.0.0.1:8000` → 指向自己，所有 `/api`、`/media` 502 | 代理目标改为 `BACKEND_PROXY_ORIGIN`（默认仍是 127.0.0.1），compose 里设成 `http://backend:8000` |
| 13 | `frontend/src/app/user-ui.css:2450` | `var(--brand-600)` 未定义（正确名是 `--color-brand-600`）→ 整条焦点描边失效 | 改对变量名 |
| 14 | `frontend/src/components/notifications/NotificationPreferences.tsx:122` | `role="switch"` 无可访问名（旁边的文本是兄弟节点） | 补 `aria-label={type.label}` |
| 15 | `.gitignore` | `nginx/ssl/`（生产私钥挂载点）与 `deploy/redis/users.acl` 都没有忽略规则，私钥可被提交 | 补规则，并确认不误伤已跟踪文件 |
| 16 | `backend/tests/test_learning.py` ↔ 环境 | 本机测试执行超时，不是本轮确认的代码缺陷：`test_empty_for_new_user` 在本机对照 clean HEAD 也超时；超时原因未能归结为机器负载或其他单一因素 | 未改；见 B3-7 |

### A2 契约 / 事实不一致

| # | 位置 | 问题 |
|---|---|---|
| 17 | `frontend/src/components/teaching/TeachingCatalog.tsx` | 把 `GET /teaching/sessions`（返回 `SessionSummary`）当成 `TeachingSession` 读 `session.items`，永远 undefined。新增 `TeachingSessionSummary` 类型并改用它 |
| 18 | `frontend/src/components/admin/GrowthTrendChart.tsx` | 后端每天下发 `vocabulary` 趋势，组件只画两条 Area，词汇被静默丢弃；顺带把颜色换成 `useChartTheme()`（原来硬编码 hex，暗色不变） |
| 19 | `frontend/src/lib/videoStatus.tsx` | `REVIEW_STATUS_CONFIG` / `VIDEO_STATUS_CONFIG` / `displayStatusOf` 零引用；两个 STEP_LABELS 里的 `splitting` 后端从不产生；`text-red` 不是已定义 token——整块删掉 |
| 20 | `frontend/src/components/channels/ChannelSubscribeButton.tsx` | 文件里藏着一份同名同义、无人引用的 `SubscribedChannels`（真正在用的是另一个文件）——删除 |
| 21 | `frontend/src/hooks/usePlatformFeed.ts` | `startLearning` 调 `POST /api/v1/videos`，该端点在 INV-003 后已不存在，且调用方从未使用它——删除 `startLearning` / `addingId` |
| 22 | `frontend/src/types/index.ts` | `Subtitle.video_id` 必填但后端不下发（改可选并注明）；`VocabSetCreateResponse.existed` 是 `number` 而后端是 `bool`；`video_id` 可为 null |
| 23 | `backend/app/models/preferences.py` / `schemas/notification.py` / `api/v1/notifications.py` | 两份 `DEFAULT_NOTIFICATION_PREFS` 键集几乎不相交，注释却说「不会漂移」。键集不同是**设计**（一份是存储默认、一份是 API 面），改成如实说明 |
| 24 | `backend/app/schemas/vocabulary.py` | 6 个 `Quiz*` schema 零引用（练习早已换成 `VocabPracticeSubmit*`）——删除 |
| 25 | `backend/app/services/video_publish.py` | 快照 `version` 只写不读，本地 `_SNAPSHOT_VERSION` 是死常量——删副本，说明 version 归 writer 所有 |
| 26 | `backend/app/services/teaching_runs.py` | 三个错误码（`CONTENT_RESTRICTED` / `EVENT_CURSOR_INVALID` / `EXECUTION_TIMEOUT`）以字面量散落，`ErrorCode` 里没有——补进 `ErrorCode` 并全部改引用常量 |
| 27 | `backend/app/models/video.py` / `learning_plan.py` / `milestone.py` | 退役功能留下的注释与事实相反（评论分析、跟读、每日计划的死列被描述成活的）——改成如实标注 |

### A3 配置 / 死设置（零读取）

| # | 位置 | 问题 |
|---|---|---|
| 28 | `backend/app/core/config.py` | `max_upload_file_size` / `upload_temp_dir` 零读取，注释指向已删除的 `upload_service`——删除字段 + `.env.example` 两行 + `media.py` 的失效注释 |
| 29 | `backend/app/core/config.py` | `teaching_usage_retention_days` 零读取（功能都没实现）——删除；`teaching_run_retention_hours` 保留并让 run-event cursor 过期与清理两处硬编码 24h 都读它。`TeachingFeedback` 的 24h 是独立实体保留期，未改 |
| 30 | `backend/app/core/config.py` | `v2_daily_budget_usd` / `v2_user_daily_budget_usd` 零读取，真实额度是 `bootstrap_gateway.py` 的常量——删字段，`.env.example` 改成说明 |
| 31 | `backend/app/core/exam_subjects.py` | 整模块零 import（前端那份是唯一事实源）——删除，并修正三处指向它的注释 |
| 32 | `backend/app/tasks/video_processing.py` | 管理端「翻译/下载步超时」两个旋钮没有消费者，页面却声称控制 Watchdog——让 watchdog 优先读 settings 行的这两列，补了测试 |
| 33 | `backend/.env.example` | SMTP/邮件重置整段（8 个键）、`ALIYUN_SMS_TEMPLATE_CODE`、`OSS_CLEANUP_LOCAL`、`UPLOAD_*` 全是死配置——替换为如实的说明 |
| 34 | `backend/requirements-dev.txt` | `playwright-stealth` 无人 import——删除 |

### A4 门禁 / 脚本 / 文档

| # | 位置 | 问题 |
|---|---|---|
| 35 | `.github/workflows/ci.yml` | e2e 失败时不上传报告与 trace——补一步 `upload-artifact` |
| 36 | `.github/workflows/ci.yml` | `bandit` 装进了 dev 依赖、文档也写了，但没有任何门禁跑它——加一步 `bandit -r app/ -ll`（实测本树 0 Medium/High） |
| 37 | `.github/workflows/slcs.yml` | push 没有 `branches` 过滤 → 同一提交在 PR 上跑两遍——补 `branches: [master, main]` |
| 38 | `.pre-commit-config.yaml` | prettier 钩子用 `npx` 拉「最新」版，注释却说「与 package.json 一致」；`files: ^frontend/` 覆盖了源码外的 `scripts/*.mjs` 而 `format:check` 不覆盖 | 修正注释、把范围收成 `^frontend/(src|e2e)/` |
| 39 | `nginx.conf` / `nginx.ssl.conf` | `upload` rate-limit zone 无人使用（上传功能已下线）；`api` zone 也未使用——删 upload，给 api 加说明 |
| 40 | `nginx.ssl.conf` | `Permissions-Policy` 与后端冲突（`microphone=(self)` vs `()`），且前端已无 `getUserMedia`——统一成 `()` |
| 41 | `scripts/backup/backup.sh` | 仍在统计已删除的 `orders` 表——移除 |
| 42 | `backend/scripts/prep_sms.sh` | 把备份文件名硬编码成 `.env.bak.20260805`，其它运行日是空操作——改成用刚生成的那个文件 |
| 43 | `backend/scripts/test_watch_mobile.py` | 起的临时 uvicorn 少了 `--timeout-keep-alive 120`（CI 与 playwright.config 都加了，理由相同）——补上 |
| 44 | `backend/migrations/env.py` | 手抄的模型导入子集已与 `app.models.__init__` 漂移，且 56 个 F401——改成一次 `import app.models`（实测 `alembic upgrade head --sql` 正常） |
| 45 | `.claude/skills/deploy/SKILL.md` | 迁移失败判据写的字符串在 `entrypoint.sh` 里不存在——改成真实的 `ERROR: alembic upgrade head failed` / `migrations OK` 两种输出与退出码语义 |
| 46 | `.github/workflows/deploy.yml.template` | 指向已删的 `backend/Dockerfile` 与 `knowledge/operations/RUNBOOK.md`——改写说明并指向 `/deploy` skill |
| 47 | `CLAUDE.md` | `/admin/lessons` 其实**也受** `SLCS_LESSONS_ENABLED` 约束（`_require_pilot`）；迁移数是 100 不是 94；`HTTPException` 约 90 处不是 110；`transcription_gpu` 不是随 V2 入库——逐条更正 |
| 48 | `refactor-blueprint/docs/review.md` | 指向已删的 `order_tasks.py` / `payments.py` 的相对链接与一条引用了已删测试文件的命令——标注为历史快照并修正命令 |
| 49 | `frontend/src/lib/examSubjects.ts` | 注释说「改这里同步改 backend/app/core/exam_subjects.py」，而那个文件本轮已删——改成「本文件即唯一事实源」 |
| 50 | `backend/tests/test_videos.py` | 断言一个已删除的 `/quiz` 路由 404（任何不存在路径都满足，永远不可能失败）——删除该用例 |
| 51 | `backend/tests/test_milestone_service.py` | docstring 与一个未使用的 helper 描述的是已下线的成就系统——改写并删 helper |
| 52 | `backend/tests/conftest.py` / `test_channels_api.py` | 指向已删 `wiki/problems/...` 的注释——改成自包含说明 |
| 53 | `.gitignore` | 补 `release/`（SLCS 发行树构建产物）、`/tmp/`（根目录一次性脚本）、去掉重复的 `.qoder/` |
| 54 | `deploy.sh` / `deploy-oneclick.sh` | 写已废弃的 `WHISPER_MODEL` / `NEXT_PUBLIC_API_URL` / `REDIS_URL`，并指向已删文档——改成当前真实变量（`NEXT_PUBLIC_SITE_URL`）并说明 GPU 配置在 gpu-worker |
| 55 | `country` 注释类失效指针（`sr_service.py` / `video_access.py` / `media.py` / 两个 model） | 指向已删除的 `docs/plans/`、`upload_service`、`knowledge/`、两个不存在的函数——逐条改成自包含描述 |

### 修完后跑过的检查

- `backend`: `ruff check app/ tests/` ✅ · `ruff format --check` ✅ · 定向 pytest **181 passed**
  （覆盖 admin_settings / notifications / videos / watchdog / milestone / words /
  architecture-invariants / video playback / subtitle edit；测试进程退出时仍出现 thread shutdown timeout，断言通过不代表进程无异常退出）
- `frontend`: `npm run lint` ✅ · `tsc --noEmit` ✅ · `node scripts/check-design-system.mjs` ✅ ·
  `check-session-writes` ✅ · `prettier --check` ✅ · 全量单测 **391 passed**
- `gpu-worker`: pytest **68 passed**
- `alembic upgrade head --sql` 已启动并产出 SQL；当时输出被截断，未确认完整生成结束
- **未执行**：`pip-audit`（本机 pip 缓存权限报错 `Errno 13`，与改动无关）；
  GPU 侧 `pip_audit_gate.py` 通过（14/14 命中、无新增）；`bandit` 已在本机跑过（0 Medium/High）；
  全量 backend 套件未跑完（`test_learning.py` 在本机与 clean HEAD 同样超时，见 C3）；
  CI 与浏览器 e2e 未跑。

---

## B. 确认有问题，但我没动，等你决定

### B1 需要你拍板的产品/设计取舍

1. **浅色模式下 `text-success` / `text-warning` 作正文小字对比度不足**
   `globals.css` 已定义 `--color-success-text` 等加深档并写明「文字用 `text-*-text`」，
   但站内仍有约 45 处 `text-success`、85 处 `text-error`、27 处 `text-warning` 用在小字上
   （浅色 success 3.3:1、warning 3.0:1，AA 要 4.5:1）。批量改会整体加深一点视觉，
   属设计取舍，我不擅自动。

2. **`user-ui.css` 里约 133 个 CSS 类名零使用**（其中 `home-editorial-*` 一族就有 52 个、约 670 行）。
   死样式不影响功能，但删 600+ 行是视觉回归风险，建议单独一次改动 + 截图验收。

3. **`frontend/scripts/*.mjs` 不在 prettier 门禁范围内**。要么把它们纳入 `format:check`
   并一次性 `prettier --write`，要么明确写「工具脚本不归格式门管」。我改成了后者（写明理由），
   但如果你希望纳入，那是另一件事。

### B2 需要迁移才能干净收尾

4. **`videos` 表的 `quiz_data` / `comment_count` / `comment_quality_score`**、
   `user_learning_profiles` 的 `total_shadowing_count` / `last_plan_generated_at`、
   `learning_records.speaking_attempts` 都是死列（无读写），但删列要一条迁移。
   本轮只把注释改成如实标注。`speaking_attempts` 还在 API 契约与前端类型里，
   一并删需要同时动 schema、前端和迁移。

5. **`backend/.pip-audit-ignore` 有 15 条当前云端依赖集不使用的历史豁免**。
   backend 门只审计 `requirements-cloud.txt`，扫描确认这些条目均为 stale；GPU 门单独使用
   `gpu-worker/.pip-audit-ignore`，14 条配置覆盖 15 个去重后的发现，且没有 NEW/STALE。
   `CVE-2026-80047` 是 `PYSEC-2026-4174` 的别名，`PYSEC-2026-3740` 已由 GPU 锁定版本修复，
   不应把它们描述成 GPU 门禁缺口。本轮保留了 backend 历史行；是否清理及同步调整其测试仍待决定。

6. **`backend/.mypy-baseline` 有 3 行在本机不再产出**（`admin_service.py:misc` 等）。
   但它可能只是 mypy 小版本/平台差异，删掉有让 CI 反向变红的风险，我不动。

### B3 需要单独排查的既有问题

7. **`test_learning.py::test_empty_for_new_user` 在本机必挂（执行超时）**。
   我在 clean HEAD 的临时 worktree 里复现了同样现象，**与本次改动无关**；
   同时本机 `import app.main` 需要 80 秒（大量并发 agent 抢 CPU）。建议在 CI 上确认它是否绿。

8. **`core.hooksPath` 指向不存在的目录**（`C:\Users\Administrator\Speaking\.git\hooks`），
   本机 pre-commit 钩子实际不生效。这是本机 git 配置，不是仓库文件；修法：
   `git config --unset core.hooksPath` 后重新 `pre-commit install`。

### B4 我判断「不该由我改」的

9. **`scripts/release.sh` 被自己的前置守卫永久堵死**（要求 `knowledge/CHANGELOG.md`，
   该文件 2026-10-15 已删）。根 `CLAUDE.md` 已把它记为「已知断链」——需要先决定 CHANGELOG 的新家。

10. **`backend/requirements-cloud.txt` 的钉版与本机 venv 不符**
    （文件 `starlette==1.6.0` / `uvicorn==0.29.0`，venv 是 `1.10.0` / `0.54.0`；
    文件头注释里 `fastapi<0.135` 的约束描述也已过期，实际 `fastapi 0.141.1` 要求
    `starlette>=0.46.0`）。改钉版会影响生产镜像，且需要重装 venv 才能验证，我不擅动。

11. **2026-07 的两个一次性 SQL 数据包**（`backend/scripts/update_*_20260707.sql.gz`，共 808KB）
    与 `backend/scripts/data/lr_learning_pool.json`（406KB）都被跟踪且无引用。
    删数据属不可逆，留给你判断。

---

## C. 已核实为「不是问题」（避免你重复怀疑）

1. **`docs/evidence/` 的 1092 个截图、`docs/prototypes/`、`designs/`** — 归档证据，不是垃圾。
2. **`backend/.mypy-baseline` 的 `slcs/stdio.py:call-arg`（本轮之前）** — 真实问题，已修（A1-8）。
3. **`test_learning.py` 的超时** — 见 B3-7，clean HEAD 同样复现。
4. **`docker-compose.prod.yml` 挂载 `deploy/redis/users.acl` 而仓库只有 `.generated`** —
   该文件是宿主渲染产物、本就不入库；compose 注释给出了正确的渲染命令，线上也已按此运行。
5. **`DROPPED_TABLES` 守卫「漏了 8 张表」** — 一次扫描把 downgrade 里的 `drop_table` 也算进去了，
   因而该扫描结果不能证明存在漏项；尚未完成对升级路径与守卫清单的逐表核验，不据此断言清单完整。
6. **`frontend/src/types/platform.ts` 的 `VideoItem` 有 `video_id` / `url` / `channel_title`** —
   这是 `/browse/feed` 的旧形状与 `homeVideoToItem` 映射的中间类型，仍在用（不是幽灵字段）。
7. **`hallucination_detection_enabled` 无消费者** — 管理端 UI 已用 `STORED_ONLY_NOTE`
   如实标注「仅登记，运行时未读取」，是刻意的中间态。
8. **`chat-theme.ts` 的 `brand: "var(--color-brand-500)"`** — 我用 Chromium 实测：
   SVG 的 `fill`/`stroke` 属性里 `var()` 能正常解析（`rgb(255,90,31)`），不是缺陷。
