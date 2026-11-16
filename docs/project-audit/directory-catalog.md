# 每个目录的作用和关系

覆盖审计起点和当前交付的每个版本化目录；本机依赖/私密/生成树按明确边界登记，不展开第三方安装文件。

| 目录 | 作用与上下游 | 状态 |
| --- | --- | --- |
| `./` | 仓库根：装配多个组件、Compose/nginx/CI 与工作规则；没有根 package.json/Makefile，命令在对应组件运行。 | 保留/当前 |
| `.agents/` | 本地 agent 镜像及一次性输出，不是规则源；未确认内容不删。 | 保留/当前 |
| `.claude/` | 开发助手技能/预览配置；local settings、凭据和工作树被忽略。 | 保留/当前 |
| `.claude/reference/` | 技能消费的本机必要操作参考。 | 保留/当前 |
| `.claude/skills/` | 当前 dev/stop/deploy 操作技能，不是产品后台任务。 | 保留/当前 |
| `.claude/skills/deploy/` | 当前 dev/stop/deploy 操作技能，不是产品后台任务。 | 保留/当前 |
| `.claude/skills/deploy/scripts/` | 受授权发布流程调用的 SSH/SFTP 辅助，不保存密码。 | 保留/当前 |
| `.claude/skills/dev/` | 当前 dev/stop/deploy 操作技能，不是产品后台任务。 | 保留/当前 |
| `.claude/skills/dev-stop/` | 当前 dev/stop/deploy 操作技能，不是产品后台任务。 | 保留/当前 |
| `.git/` | Git 对象、分支和历史；不是源码；不清理。 | 保留/当前 |
| `.github/` | 仓库托管自动化与依赖更新配置。 | 保留/当前 |
| `.github/workflows/` | GitHub Actions 检查与交叉浏览器/独立发行验证，不自动部署。 | 保留/当前 |
| `.production-smoke/` | 本机生产 smoke 生成的配置/证书/临时状态，可能敏感；本轮未重建。 | 保留/当前 |
| `.pytest_cache/` | pytest 可重建缓存，不是业务数据；不作为源码逐项审计。 | 保留/当前 |
| `.references/` | 第三方源码/wheel/许可核对下载缓存；原件不发布，证据保留在 P0。 | 保留/当前 |
| `.ruff_cache/` | ruff 可重建缓存；不代表源码已通过检查。 | 保留/当前 |
| `backend/` | Python 云端 API/worker 根、依赖/检查/迁移入口，也容纳独立 slcs 包。 | 保留/当前 |
| `backend/.venv/` | 后端安装依赖与解释器，不是第一方源码。 | 保留/当前 |
| `backend/app/` | FastAPI 主应用；汇集 API、服务、ORM、任务，不是独立可发布读取器。 | 保留/当前 |
| `backend/app/api/` | HTTP 路由和鉴权依赖；上游是客户端，下游是业务服务。 | 保留/当前 |
| `backend/app/api/v1/` | HTTP 路由和鉴权依赖；上游是客户端，下游是业务服务。 | 保留/当前 |
| `backend/app/core/` | 配置、连接、安全、错误与可观测基础，被所有业务层使用。 | 保留/当前 |
| `backend/app/integrations/` | 可选外部协议适配；复用业务服务，不另造业务规则。 | 保留/当前 |
| `backend/app/integrations/mcp/` | 可选外部协议适配；复用业务服务，不另造业务规则。 | 保留/当前 |
| `backend/app/models/` | 持久实体和关系；被服务/迁移/导出注销消费，集中注册。 | 保留/当前 |
| `backend/app/schemas/` | HTTP 数据契约；约束输入输出，需与前端 DTO 配合。 | 保留/当前 |
| `backend/app/services/` | 业务用例/规则/读模型；模块之间有事务和外部 I/O 依赖，非自动独立领域。 | 保留/当前 |
| `backend/app/services/teaching/` | 确定性教学、内容核验/发布、对话和共享身份规则；HTTP/模型/MCP 共用。 | 保留/当前 |
| `backend/app/services/translation/` | 可切换字幕翻译引擎、清洗与质量门；由管线/维护工具调用。 | 保留/当前 |
| `backend/app/slcs/` | 旧 app.slcs 路径兼容转发到独立包。 | 保留/当前 |
| `backend/app/tasks/` | Celery 注册入口和视频/生命周期/通知等后台执行；beat 负责派发周期任务。 | 保留/当前 |
| `backend/data/` | 下载词典、原卷和题库参考数据，不在镜像/代码清单，生产只读挂载；需单独许可和备份审查。 | 保留/当前 |
| `backend/media/` | 后端工作目录下的真实媒体/导出；不按缓存删除。 | 保留/当前 |
| `backend/migrations/` | 数据库版本升级装配/模板；Alembic 消费模型 metadata。 | 保留/当前 |
| `backend/migrations/versions/` | 数据库历史升级图的 revision 文件；与 ORM/已迁移数据库和后续 revision 相连，不能按退役功能删。 | 保留/当前 |
| `backend/scripts/` | 显式维护/播种/签名/导入/检查工具；有些会写库或外部调用，不随 API 自动执行。 | 保留/当前 |
| `backend/scripts/data/` | 导入工具的候选目录数据；不是线上 Video 表，公开前仍核对来源许可。 | 保留/当前 |
| `backend/slcs/` | 独立 Apache-2.0 Python 读取库、CLI 和可选离线 MCP。 | 保留/当前 |
| `backend/slcs_tests/` | 独立 wheel/发行树一致性与 stdio 测试，不能被源码 import 替代。 | 保留/当前 |
| `backend/tests/` | 后端单元/API/PG 并发回归与合成素材，默认 SQLite、集成需专用 PG。 | 保留/当前 |
| `backend/tests/fixtures/` | 后端单元/API/PG 并发回归与合成素材，默认 SQLite、集成需专用 PG。 | 保留/当前 |
| `deploy/` | 部署所需资源和可选适配器，不是一次性报告输出目录。 | 保留/当前 |
| `deploy/redis/` | 持久化和最小权限策略模板，生产/隔离演练共同消费。 | 保留/当前 |
| `deploy/v2-gateway/` | 可选候选网关的合成/主机装配、模板、隧道和锁版治理状态。 | 保留/当前 |
| `deploy/v2-gateway/adapter/` | 模型网关入站/出站薄中继与可选签发，外部账本仍由 LiteLLM 拥有。 | 保留/当前 |
| `designs/` | 未入库设计导出，可能有唯一原件/嵌套工具状态；无业务运行引用，未确认唯一性，不永久删。 | 保留/当前 |
| `dist/` | 本地构建制品缓存，版本化源在组件目录；不等于已发布。 | 保留/当前 |
| `docs/` | 最新大纲/P0 证据、活 SLCS 契约与本轮审计，不再并存旧蓝图/历史方案库。 | 保留/当前 |
| `docs/admin-audit-2026-10-26/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/audit-2026-10-24/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/audit-2026-10-24/shots/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/audit-2026-11-13-workspace/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/comprehensive-audit-2026-10-29/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/comprehensive-audit-2026-10-29/evidence/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/comprehensive-audit-2026-10-29/evidence/entrypoint-stub/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/` | 仅保留最新 open-learning/Astryx 证据；普通运行产物默认放 tmp。 | 保留/当前 |
| `docs/evidence/admin-audit-2026-10-26/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/admin-audit-2026-10-26/fixes/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/admin-audit-2026-10-26/frontend-removal/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/astryx-integration/` | 保留的最新词汇 UI 试点证据，不是全站规范。 | 保留/当前 |
| `docs/evidence/audit-2026-10-24/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/brand-refresh-2026-10-31/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/auth-final/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/dark-breakpoints/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/final-home-register/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/final-pages/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/final-register/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/flows-final/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/listening-ui/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/other-pages/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/post-build-final/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/practice/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/subpage-recheck/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/design-redo/subpages-final/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-2026-10-26/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-2026-10-26/chromium/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-2026-10-26/firefox/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-2026-10-26/mobile-chrome/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-2026-10-26/mobile-iphone/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-v2-2026-10-26/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-v2-2026-10-26/firefox/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-chrome/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-iphone/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/discover-watch-v2-2026-10-26/visual/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/home-design-refresh/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/home-editorial/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/iteration-2/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/iteration-3/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/iteration-3/backup-restore/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/iteration-4/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/iteration-5/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/open-learning/` | 保留的最新 P0 原始证据，不重写旧结果。 | 保留/当前 |
| `docs/evidence/open-learning/p0/` | 保留的最新 P0 原始证据，不重写旧结果。 | 保留/当前 |
| `docs/evidence/perf-2026-11/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/slcs-2026-11-11/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-gateway-capacity-2026-11-04/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-gateway-host-2026-11-04/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-gateway-real-2026-11-03/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/bifrost-data/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-gateway-spike-2026-11-03/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-kernel-2026-11-03/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-mcp-spike-2026-11-03/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-p024-2026-11/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/v2-ui-2026-11-03/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/w0-merge-2026-11/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/evidence/watch-layout-refresh/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/open-learning/` | 保留的最新 P0 决策、许可和来源核对；与最新大纲相连。 | 保留/当前 |
| `docs/open-learning/p0/` | 保留的最新 P0 决策、许可和来源核对；与最新大纲相连。 | 保留/当前 |
| `docs/project-audit/` | 本轮新人审计交付与逐文件/目录索引；检查 JSON 为本轮证据。 | 保留/当前 |
| `docs/project-audit/catalog/` | 本轮新人审计交付与逐文件/目录索引；检查 JSON 为本轮证据。 | 保留/当前 |
| `docs/project-audit/checks/` | 本轮新人审计交付与逐文件/目录索引；检查 JSON 为本轮证据。 | 保留/当前 |
| `docs/prototypes/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/prototypes/home-direction-2026-10-20/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/prototypes/home-refresh-2026-10/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/prototypes/home-refresh-2026-10/assets/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/session-notes/` | 保留的最新提交会话验证边界。 | 保留/当前 |
| `docs/slcs/` | 最小 SLCS 规范/Schema/许可证与示例；旧愿景/路线/交接已清出。 | 保留/当前 |
| `docs/slcs/examples/` | 明确许可的参考包及离线读取示例，发行与测试实际消费。 | 保留/当前 |
| `docs/slcs/examples/invalid/` | 发行校验器必须拒绝的合成反例。 | 保留/当前 |
| `docs/ui-review-2026-10-21/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `docs/watch-baseline-2026-10-20/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `frontend/` | Next/npm 构建根，包含生产/开发镜像、测试与依赖锁。 | 保留/当前 |
| `frontend/.next/` | Next 可重建输出和类型，不是手写源码。 | 保留/当前 |
| `frontend/e2e/` | Playwright 浏览器回归，测试真实交互，不与 Vitest 混收集。 | 保留/当前 |
| `frontend/e2e/fixtures/` | 自产媒体/localhost 证书等浏览器夹具，不是用户内容或生产私钥。 | 保留/当前 |
| `frontend/e2e/production/` | 经本机 HTTPS nginx 的生产镜像回归。 | 保留/当前 |
| `frontend/node_modules/` | 第三方 npm 安装树，不逐项当自有代码；版本认 lock。 | 保留/当前 |
| `frontend/playwright-report/` | 浏览器回归报告生成物，不替代本轮测试结果。 | 保留/当前 |
| `frontend/public/` | 品牌/默认头像/公开资源，按 URL 引用而非必须 import。 | 保留/当前 |
| `frontend/scripts/` | 前端设计/会话硬门与可选截图/生产 smoke 工具。 | 保留/当前 |
| `frontend/src/` | 手写应用源码；页面、组件、Hook、工具、状态和类型相互装配。 | 保留/当前 |
| `frontend/src/app/` | Next 路由/布局约定目录；页面壳或参数子路由；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/` | Next 路由/布局约定目录；首页与继续学习；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/` | Next 路由/布局约定目录；管理概览；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/` | Next 路由/布局约定目录；管理概览；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/channels/` | Next 路由/布局约定目录；频道管理；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/feedback/` | Next 路由/布局约定目录；反馈管理；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/home-editorial/` | Next 路由/布局约定目录；首页编排管理；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/lessons/` | Next 路由/布局约定目录；课程发布管理；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/settings/` | Next 路由/布局约定目录；系统设置；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/stats/` | Next 路由/布局约定目录；后台学习/运营统计；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/users/` | Next 路由/布局约定目录；用户管理；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/videos/` | Next 路由/布局约定目录；视频管理；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/(shell)/videos/[id]/` | Next 路由/布局约定目录；视频详情/字幕维护；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(admin)/admin/login/` | Next 路由/布局约定目录；管理员登录；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/` | Next 路由/布局约定目录；首页与继续学习；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/browse/` | Next 路由/布局约定目录；页面壳或参数子路由；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/channels/` | Next 路由/布局约定目录；频道发现；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/channels/[slug]/` | Next 路由/布局约定目录；页面壳或参数子路由；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/contact/` | Next 路由/布局约定目录；联系与反馈；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/favorites/` | Next 路由/布局约定目录；个人收藏；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/history/` | Next 路由/布局约定目录；观看历史；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/lessons/` | Next 路由/布局约定目录；SLCS 课程；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/lessons/[lessonId]/` | Next 路由/布局约定目录；页面壳或参数子路由；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/notifications/` | Next 路由/布局约定目录；本人通知；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/` | Next 路由/布局约定目录；练习中心；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/daily/` | Next 路由/布局约定目录；每日检查；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/exams/` | Next 路由/布局约定目录；真题试卷；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/exams/[id]/` | Next 路由/布局约定目录；页面壳或参数子路由；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/exams/redo/` | Next 路由/布局约定目录；错题重做；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/exams/result/` | Next 路由/布局约定目录；页面壳或参数子路由；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/exams/result/[id]/` | Next 路由/布局约定目录；考试结果；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/listening/` | Next 路由/布局约定目录；听力练习；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/practice/listening/[id]/` | Next 路由/布局约定目录；页面壳或参数子路由；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/profile/` | Next 路由/布局约定目录；个人档案/设置；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/rankings/` | Next 路由/布局约定目录；学习视频榜单；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/search/` | Next 路由/布局约定目录；视频/原句搜索；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/vocabulary/` | Next 路由/布局约定目录；词汇本；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/vocabulary/drill/` | Next 路由/布局约定目录；单词训练；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/vocabulary/review/` | Next 路由/布局约定目录；复习入口；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/vocabulary/sets/` | Next 路由/布局约定目录；个人词集；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/vocabulary/sets/[id]/` | Next 路由/布局约定目录；词集详情；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/vocabulary/sets/[id]/sieve/` | Next 路由/布局约定目录；快速过筛；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/watch/` | Next 路由/布局约定目录；页面壳或参数子路由；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/watch/[id]/` | Next 路由/布局约定目录；视频逐句点词学习；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/watch/[id]/transcript/` | Next 路由/布局约定目录；视频整篇文稿；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/(main)/weekly-report/` | Next 路由/布局约定目录；退役周报兼容跳转；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/forgot-password/` | Next 路由/布局约定目录；短信重置密码；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/login/` | Next 路由/布局约定目录；登录；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/onboarding/` | Next 路由/布局约定目录；个人引导；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/privacy/` | Next 路由/布局约定目录；隐私政策；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/register/` | Next 路由/布局约定目录；注册；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/set-password/` | Next 路由/布局约定目录；首次设置密码；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/app/terms/` | Next 路由/布局约定目录；用户协议；由父布局到页面隐式装配。 | 保留/当前 |
| `frontend/src/components/` | UI 展示与交互组件；components业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/admin/` | UI 展示与交互组件；admin业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/admin/home/` | UI 展示与交互组件；home业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/admin/ui/` | UI 展示与交互组件；ui业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/auth/` | UI 展示与交互组件；auth业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/channels/` | UI 展示与交互组件；channels业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/common/` | UI 展示与交互组件；common业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/exam/` | UI 展示与交互组件；exam业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/home/` | UI 展示与交互组件；home业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/layout/` | UI 展示与交互组件；layout业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/legal/` | UI 展示与交互组件；legal业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/lessons/` | UI 展示与交互组件；lessons业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/listening/` | UI 展示与交互组件；listening业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/notifications/` | UI 展示与交互组件；notifications业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/practice/` | UI 展示与交互组件；practice业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/profile/` | UI 展示与交互组件；profile业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/rankings/` | UI 展示与交互组件；rankings业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/search/` | UI 展示与交互组件；search业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/subtitle/` | UI 展示与交互组件；subtitle业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/teaching/` | UI 展示与交互组件；teaching业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/transcript/` | UI 展示与交互组件；transcript业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/ui/` | UI 展示与交互组件；ui业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/video/` | UI 展示与交互组件；video业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/video-edit/` | UI 展示与交互组件；video-edit业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/vocabulary/` | UI 展示与交互组件；vocabulary业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/components/watch/` | UI 展示与交互组件；watch业务/控件分组；上游页面，下游 Hook/工具/API。 | 保留/当前 |
| `frontend/src/hooks/` | React 可复用状态/请求/媒体/布局生命周期；不是服务器事实源。 | 保留/当前 |
| `frontend/src/lib/` | 共享 API、纯规则、格式化与同目录 Vitest 单测。 | 保留/当前 |
| `frontend/src/stores/` | Zustand 跨组件状态和独立会话；与 API/持久化 helper 协作。 | 保留/当前 |
| `frontend/src/types/` | 前端 DTO/接口形状，与后端 schema 一一核对。 | 保留/当前 |
| `frontend/test-results/` | Playwright 运行产物，不是测试定义。 | 保留/当前 |
| `gpu-worker/` | 独立运行/依赖根，真实机器应有单独 venv 和专属环境。 | 保留/当前 |
| `gpu-worker/gpu_worker/` | 仅转录队列/共享密钥回调的独立包，无云端 app/DB/OSS key。 | 保留/当前 |
| `gpu-worker/gpu_worker/transcription/` | 独立 GPU 转录引擎、对齐/分段/标点/回退，模型成本和运行资源只在 worker 侧。 | 保留/当前 |
| `gpu-worker/scripts/` | GPU 启动、安全闸、心跳、依赖锁和受限隧道。 | 保留/当前 |
| `gpu-worker/tests/` | 无真实模型/网络的 GPU 契约与恢复回归；不证明真实精度和吞吐。 | 保留/当前 |
| `logs/` | 本地服务日志和运维状态，可能含凭据；除占位不纳入公开正文。 | 保留/当前 |
| `media/` | 本地实际视频/音频/头像/导出；可能是唯一副本和个人数据，不清理。 | 保留/当前 |
| `refactor-blueprint/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `refactor-blueprint/docs/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `refactor-blueprint/evidence/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `refactor-blueprint/evidence/content-receipts/` | 旧方案/原型/验收/实施材料目录；未证明为运行入口，已可恢复移出。 | 原目录已清出 |
| `release/` | SLCS 生成公开发行树；不在 Git，不自动同步外部仓库。 | 保留/当前 |
| `scripts/` | 仓库级可重复运维工具；不是根 npm 包。 | 保留/当前 |
| `scripts/backup/` | 显式备份/恢复工具，恢复可破坏数据；与发布前回退点不同。 | 保留/当前 |
| `scripts/isolation/` | 独立容器/卷的 ACL 与恢复演练，有删除专用卷的副作用。 | 保留/当前 |
| `tmp/` | 本地忽略的探针、构建和临时证据；本轮含审计恢复副本，不永久删除。 | 保留/当前 |

## 本地不应按无用删除的文件/目录

以下只登记用途，不读取/公开凭据正文：

- `.env`、`.env.gpu-worker`、本机 `.mcp.json`、`.claude/settings.local.json`、cookie/会话状态：机器绑定或凭据，排除公开清单。
- node_modules/.venv：第三方安装树，不是自有代码，依赖关系认清单/锁文件。
- data/media/数据库卷：参考材料或用户数据，不等于可重建缓存。
- `.git`：历史和回退依据，本轮不改写历史。
- `tmp/project-audit-recovery/`：本轮保留的旧材料原字节，不释放磁盘；未入库项只能从本机恢复，需保留到用户确认。
- `tmp/project-audit/`：本轮本地分析/日志/隔离 wheel 环境，报告只引用已脱敏结果。

未跟踪业务源码没有被静默混入/删除；本轮新增第一方文件均列入文件清单。
