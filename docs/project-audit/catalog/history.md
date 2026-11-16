# 已清出文件逐项索引

本分册 1338 项。每项来自实际文件、符号/表/路由和引用提取；关系未显示的其余项在 [完整机器清单](../inventory.json)。无 import 不等于无调用，动态入口/收集器/配置关系另列。

旧文件已移出原路径，原字节在本地忽略恢复区；Git 文件也可从基线提交恢复。JSON、截图、文本和一次性脚本逐项记录，不把旧通过结论当新证据。

| 原路径 | 原作用/关系 | 本轮处置原因 |
| --- | --- | --- |
| `.github/workflows/deploy.yml.template` | 未启用且正文标记不可直接启用的旧就地构建模板。 | 未启用且正文标记不可直接启用的旧就地构建模板；可恢复隔离 |
| `DESIGN.md` | 旧全站视觉说明；必要当前约束归入 frontend/CLAUDE.md，数值仍认 CSS。 | 旧全站视觉说明；必要当前约束归入 frontend/CLAUDE.md，数值仍认 CSS；可恢复隔离 |
| `PROGRESS.md` | 已结束的改版任务与旧验收快照；不再作为当前框架说明。 | 已结束的改版任务与旧验收快照；不再作为当前框架说明；可恢复隔离 |
| `backend/scripts/update_prewarm_practice_20260707.sql.gz` | 二进制静态资源：历史证据/生成素材；不是应用执行代码。 | 2026-07-07 固定字幕数据 UPDATE 导出，不是迁移；无脚本/构建/测试消费者；可恢复隔离 |
| `backend/scripts/update_subtitles_20260707.sql.gz` | 二进制静态资源：历史证据/生成素材；不是应用执行代码。 | 2026-07-07 固定字幕数据 UPDATE 导出，不是迁移；无脚本/构建/测试消费者；可恢复隔离 |
| `deploy-oneclick.sh` | 正文明确标记已失效；避免新人误执行旧全栈 down 与就地构建。 | 正文明确标记已失效；避免新人误执行旧全栈 down 与就地构建；可恢复隔离 |
| `deploy.sh` | 正文明确标记已失效；依赖生产机 git pull/就地构建，不是当前发布流程。 | 正文明确标记已失效；依赖生产机 git pull/就地构建，不是当前发布流程；可恢复隔离 |
| `docs/a14-research-protocol-2026-10-31.md` | 历史材料：A14 任务型用户研究与单项体验实验（预注册） # 1 目标人群与招募 # 2 形成性研究脚本（每场 30–40 分钟） # 3 单项体验实验（每轮只验证一个假设） ## 3.1 本轮假设（H1） #…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/README.md` | 历史材料：后台管理面板审计、优化与数据清理 — 2026-10-26 # 1. 结论摘要 # 2. 清理 ## 2.1 兑换码系统（删除） ## 2.2 退役功能用户数据表（删除） ## 2.3 本地 dev …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/backend-fixes-admin.md` | 历史材料：后端修复 B：channels / feedback / 公告 / video_service 管理面板健壮性（2026-10-26） # 1. 结论 # 2. 修复明细 ## 2.1 ADM-19 …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/backend-fixes-pipeline.md` | 历史材料：后端修复 A：管线与字幕编辑数据安全（2026-10-26） # 1. 结论 # 2. 修复明细 ## 2.1 ADM-01 重断句（resegment）与回滚：保留并重映射用户数据 ## 2.2 A…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/backend-removal.md` | 历史材料：后端清理：移除兑换码系统与退役用户数据表（2026-10-26） # 1. 结论 # 2. 迁移 # 3. 改动清单 ## 3.1 删除的文件 ## 3.2 新增的文件 ## 3.3 修改的文件（ba…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/backend.md` | 历史材料：后台管理面板后端审计 — 2026-10-26 # 0. 快照、范围与方法 ## 0.1 并行清理导致的快照漂移（重要） ## 0.2 并行清理相关的集成提示（不计入 finding，交给 Lead …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/frontend-fixes-pages.md` | 历史材料：前端修复 B 报告：后台列表/详情页 UX + a11y（users / videos / channels / feedback） # 1. 修复清单（19 条 finding） # 2. 改动文件…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/frontend-fixes-shell.md` | 历史材料：后台壳层/弹窗/下拉/登录/设置/统计修复报告（task-8，2026-10-26） # 0. 结论 # 1. 修复一览 # 2. 关键实现细节（给评审） ## 2.1 壳层错误分级（A-05） ##…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/frontend-removal.md` | 历史材料：前端清理报告：移除兑换码后台与退役 /redeem 壳 # 1. 删除的文件（4 个页面/spec + 对应目录） # 2. 修改的文件（13 个） ## 文案调整（用户可见） # 3. 验证（真实输…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/frontend.md` | 历史材料：SeeWord 后台管理面板前端审计（2026-10-26） （redesign 分支，Next.js 16 App Router + React 19 + Tailwind v4；后端 dev :8…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/admin-audit-2026-10-26/payments-admin.md` | 历史材料：后台「付费记录」页 + 管理面核心审计修复（task-5） # 1. 结论 # 2. API 契约 ## 2.1 GET /api/v1/admin/payments ## 2.2 GET /api/…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/architecture-fix-plan-2026-10.md` | 历史材料：SeeWord 架构缺陷修复方案（2026-10） # 0. 结论提要 # 1. 批 0 — 契约快照（设施） ## 为什么必须最先做 ## 前置 ## 改动点 ## 验收口径 ## 回滚；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/audit-2026-10-24/README.md` | 历史材料：全站审计与优化 — 2026-10-24 # 1. 结论摘要 # 2. 本轮已落地的修复 ## 2.1 后端 ## 2.2 前端视觉（设计还原） ## 2.3 前端功能 / 可访问性 ## 2.4 测…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/audit-2026-10-24/backend-architecture.md` | 历史材料：后端架构审计 — 2026-10-24 # 概览 # 发现表 ## P1 — 高 ## P2 — 中 ## P3 — 低 # 按维度索引 # 已确认健康的部分；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/audit-2026-10-24/frontend-functional.md` | 历史材料：SeeWord 前端功能 / 交互 / 可访问性审计（2026-10-24） # 0. 环境与方法 ## 0.1 环境 ## 0.2 方法 # 1. 发现表 ## 1.1 已确认正常、但容易被误报的点…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/audit-2026-10-24/frontend-visual.md` | 历史材料：SeeWord 用户端视觉还原审计（2026-10-24） # 0. 结论速览 # 1. 审计范围与方法 ## 1.1 账号 ## 1.2 截图脚本（临时产物，仅本次审计） ## 1.3 视口与截图 …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/audit-2026-10-24/metrics-pre.json` | 历史材料：metrics-pre.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/metrics.json` | 历史材料：metrics.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/no-response-model-endpoints.md` | 历史材料：尚无 response_model 的数据端点清单（BE-07 跟踪）；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/audit-2026-10-24/shots/probe-channel.png` | 历史 shots 方案的 probe-channel.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/probe-channels-rachel-s-english.png` | 历史 shots 方案的 probe-channels-rachel-s-english.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/probe-channels.png` | 历史 shots 方案的 probe-channels.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/probe-home.png` | 历史 shots 方案的 probe-home.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/probe-watch-28091082-12e9-47dd-ab0c-8533e3bc27a8.png` | 历史 shots 方案的 probe-watch-28091082-12e9-47dd-ab0c-8533e3bc27a8.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-channels-desktop.png` | 历史 shots 方案的 vis-audit-1-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-favorites-desktop.png` | 历史 shots 方案的 vis-audit-1-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-history-desktop.png` | 历史 shots 方案的 vis-audit-1-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-home-desktop.png` | 历史 shots 方案的 vis-audit-1-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-home-mobile.png` | 历史 shots 方案的 vis-audit-1-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-notifications-desktop.png` | 历史 shots 方案的 vis-audit-1-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-practice-desktop.png` | 历史 shots 方案的 vis-audit-1-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-profile-desktop.png` | 历史 shots 方案的 vis-audit-1-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-search-dialog-desktop.png` | 历史 shots 方案的 vis-audit-1-search-dialog-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-upgrade-desktop.png` | 历史 shots 方案的 vis-audit-1-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-vocabulary-desktop.png` | 历史 shots 方案的 vis-audit-1-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-vocabulary-review-desktop.png` | 历史 shots 方案的 vis-audit-1-vocabulary-review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-1-vocabulary-sets-desktop.png` | 历史 shots 方案的 vis-audit-1-vocabulary-sets-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-channels-desktop.png` | 历史 shots 方案的 vis-audit-2-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-channels-mobile.png` | 历史 shots 方案的 vis-audit-2-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-dark-home.png` | 历史 shots 方案的 vis-audit-2-dark-home.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-dark-profile.png` | 历史 shots 方案的 vis-audit-2-dark-profile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-dark-vocabulary.png` | 历史 shots 方案的 vis-audit-2-dark-vocabulary.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-favorites-desktop.png` | 历史 shots 方案的 vis-audit-2-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-history-desktop.png` | 历史 shots 方案的 vis-audit-2-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-home-desktop.png` | 历史 shots 方案的 vis-audit-2-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-home-mobile.png` | 历史 shots 方案的 vis-audit-2-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-notifications-desktop.png` | 历史 shots 方案的 vis-audit-2-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-practice-desktop.png` | 历史 shots 方案的 vis-audit-2-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-practice-mobile.png` | 历史 shots 方案的 vis-audit-2-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-profile-desktop.png` | 历史 shots 方案的 vis-audit-2-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-report.json` | 历史材料：vis-audit-2-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-search-dialog-desktop.png` | 历史 shots 方案的 vis-audit-2-search-dialog-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-upgrade-desktop.png` | 历史 shots 方案的 vis-audit-2-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-vocabulary-desktop.png` | 历史 shots 方案的 vis-audit-2-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-vocabulary-mobile.png` | 历史 shots 方案的 vis-audit-2-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-vocabulary-review-desktop.png` | 历史 shots 方案的 vis-audit-2-vocabulary-review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-vocabulary-review-mobile.png` | 历史 shots 方案的 vis-audit-2-vocabulary-review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-vocabulary-sets-desktop.png` | 历史 shots 方案的 vis-audit-2-vocabulary-sets-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-2-vocabulary-sets-mobile.png` | 历史 shots 方案的 vis-audit-2-vocabulary-sets-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-channel-detail-desktop.png` | 历史 shots 方案的 vis-audit-3-channel-detail-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-channel-detail-mobile.png` | 历史 shots 方案的 vis-audit-3-channel-detail-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-favorites-desktop.png` | 历史 shots 方案的 vis-audit-3-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-favorites-mobile.png` | 历史 shots 方案的 vis-audit-3-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-history-desktop.png` | 历史 shots 方案的 vis-audit-3-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-history-mobile.png` | 历史 shots 方案的 vis-audit-3-history-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-home-1024x768.png` | 历史 shots 方案的 vis-audit-3-home-1024x768.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-home-820x1180.png` | 历史 shots 方案的 vis-audit-3-home-820x1180.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-notifications-desktop.png` | 历史 shots 方案的 vis-audit-3-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-notifications-mobile.png` | 历史 shots 方案的 vis-audit-3-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-profile-desktop.png` | 历史 shots 方案的 vis-audit-3-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-profile-mobile.png` | 历史 shots 方案的 vis-audit-3-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-report.json` | 历史材料：vis-audit-3-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-search-dialog-mobile.png` | 历史 shots 方案的 vis-audit-3-search-dialog-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-upgrade-desktop.png` | 历史 shots 方案的 vis-audit-3-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-upgrade-mobile.png` | 历史 shots 方案的 vis-audit-3-upgrade-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-watch-desktop.png` | 历史 shots 方案的 vis-audit-3-watch-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-3-watch-mobile.png` | 历史 shots 方案的 vis-audit-3-watch-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-4-home-dark-desktop.png` | 历史 shots 方案的 vis-audit-4-home-dark-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-4-home-dark-mobile.png` | 历史 shots 方案的 vis-audit-4-home-dark-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-4-home-desktop.png` | 历史 shots 方案的 vis-audit-4-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-10-24/shots/vis-audit-4-home-mobile.png` | 历史 shots 方案的 vis-audit-4-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/audit-2026-11-13-workspace/README.md` | 历史材料：全仓缺陷巡检：已修 / 待你决定 # A. 已修（工作区未提交） ## A1 真实缺陷（会出错、会误导、或有安全隐患） ## A2 契约 / 事实不一致 ## A3 配置 / 死设置（零读取） ## …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/beta-prototype-alignment-2026-10.md` | 历史材料：公测版对齐原型 · 需求记录（2026-10-19） # 0. 版本目标 # 1. 总原则（红线） # 2. 首页 # 3. 频道页 # 4. 练习 # 5. 词汇 # 6. 我的与其他页面；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/code-review-2026-10-20-checklist.md` | 历史材料：代码审查处置清单（2026-10-20） # 第 1 组 · 恢复 CI 绿（阻塞其余一切） ## [x] 1.1 真修 4 条 mypy 新增错误 ## [x] 1.2 同步 test_home_c…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/code-review-2026-10-20.md` | 历史材料：SeeWord 代码框架梳理与审查报告（2026-10-20） # 0. 结论提要 ## 门禁实测总表 # 1. 架构骨架 ## 1.1 后端 ## 1.2 前端 # 2. 必须先处理（会红 CI /…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/README.md` | 历史材料：SeeWord 全面审计与持续优化方案 # 1. 决策结论 # 2. 已核对的项目现状 # 3. 十个审计方向的判断 # 4. 产品定位与功能取舍 # 5. 优先级与投入原则 # 6. 建议执行节奏 …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/backend.md` | 历史材料：后端专项审计（2026-10-29） # 已执行验证 # 已确认的问题与可执行方案 ## BE-01 · P1 · GPU 回调提交后入队失败，重试会确认但无法补发 tail ## BE-02 · P…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/.gitignore` | 历史材料：.gitignore；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/analytics-watch-time-repro.json` | 历史材料：analytics-watch-time-repro.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/backend-findings-repro.txt` | 历史材料：backend-findings-repro.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/backend-format.txt` | 历史材料：backend-format.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/backend-mypy-baseline.txt` | 历史材料：backend-mypy-baseline.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/backend-mypy.txt` | 历史材料：backend-mypy.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/backend-pytest-unsandboxed.txt` | 历史材料：backend-pytest-unsandboxed.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/backend-pytest.txt` | 历史材料：backend-pytest.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/backend-ruff.txt` | 历史材料：backend-ruff.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/browser-01.mjs` | 历史材料：browser-01.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/browser-02.mjs` | 历史材料：browser-02.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/browser-03.mjs` | 历史材料：browser-03.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/browser-04.mjs` | 历史材料：browser-04.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/browser-05.mjs` | 历史材料：browser-05.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/browser-observations.md` | 历史材料：当前浏览器取证边界；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/check-mypy-baseline.mjs` | 历史材料：check-mypy-baseline.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/ci-jwt-repro.txt` | 历史材料：ci-jwt-repro.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/entrypoint-migration-failure-network.txt` | 历史材料：entrypoint-migration-failure-network.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/entrypoint-migration-failure.txt` | 历史材料：entrypoint-migration-failure.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/entrypoint-stub/alembic` | 历史材料：!/bin/sh；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/frontend-build-sandbox.txt` | 历史材料：frontend-build-sandbox.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/frontend-build-webpack.txt` | 历史材料：frontend-build-webpack.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/frontend-build.txt` | 历史材料：frontend-build.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/frontend-check.txt` | 历史材料：frontend-check.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/frontend-repros.cjs` | 历史材料：Run from frontend/: node ../docs/comprehensive-audit-2026-10-29/evidence/frontend-repros.cjs Execute…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/frontend-unit-workspace-temp.txt` | 历史材料：frontend-unit-workspace-temp.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/frontend-unit.txt` | 历史材料：frontend-unit.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/inventory.json` | 历史材料：inventory.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/inventory.mjs` | 历史材料：inventory.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/local-runtime.json` | 历史材料：local-runtime.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/metrics-reproduction-final.txt` | 历史材料：metrics-reproduction-final.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/metrics-reproduction.txt` | 历史材料：metrics-reproduction.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/migrations-postgres.txt` | 历史材料：migrations-postgres.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/npm-audit-runtime-official-network.json` | 历史材料：npm-audit-runtime-official-network.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/npm-audit-runtime-official-registry.json` | 历史材料：npm-audit-runtime-official-registry.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/npm-audit-runtime.json` | 历史材料：npm-audit-runtime.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/pagination-retry-repro.json` | 历史材料：pagination-retry-repro.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/pip-audit-cloud-official-network.txt` | 历史材料：pip-audit-cloud-official-network.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/pip-audit-cloud-workspace-temp.txt` | 历史材料：pip-audit-cloud-workspace-temp.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/pip-audit-cloud.txt` | 历史材料：pip-audit-cloud.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/playwright-browser-install.txt` | 历史材料：playwright-browser-install.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/postgres-container-log.txt` | 历史材料：postgres-container-log.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/postgres-container-state.txt` | 历史材料：postgres-container-state.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/report-link-check.json` | 历史材料：report-link-check.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/reproduce-metrics.py` | 历史材料：Audit reproduction restricted to disposable SQLite or the named audit DB.；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/test_backend_findings.py` | 历史材料：Read-only audit reproductions: in-memory SQLite + fake Redis only. Run from backend with PYTHONUTF8=…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/validate-report.mjs` | 历史材料：validate-report.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/evidence/watch-browser-tests.txt` | 历史材料：watch-browser-tests.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/execution-plan.md` | 历史材料：优化任务、依赖与关闭条件 # 1. 任务表 # 2. 首轮承诺边界 # 3. 每个任务的最小工作卡 # 4. 回归矩阵 # 5. 持续执行节奏；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/frontend.md` | 历史材料：前端、产品与体验审计（2026-10-29） # 当前实现与已有基础 # 本轮验证 # 现存发现 ## FE-01：无限列表翻页失败后，“重试”跳过失败页（建议 P2，已复现） ## FE-02：学习…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/metrics.md` | 历史材料：指标、学习记录与效果验证专项 # 已确认的计量问题 ## MET-01 / P1：后台历史活跃趋势基于可变的最后访问时间 ## MET-02 / P2：展示为“转化漏斗”的实际是相互独立的累计人数 #…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/ops.md` | 历史材料：运维、依赖与 GPU 组件审计（2026-10-29） # 已执行检查 # OPS-01 / P1：运行依赖硬门失败，应先完成受控升级 # OPS-02 / P1：迁移失败被转换成成功返回值，健康检查…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/comprehensive-audit-2026-10-29/verification.md` | 历史材料：本轮验证清单 # 可重复检查 # 缺陷复现与环境探测 # 本轮未执行的验收；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/design-direction-2026-10-20.md` | 历史材料：SeeWord 后续设计方向与落地思路 # 1. 建议方向 # 2. 本次依据与边界 # 3. 两个版本如何取舍 # 4. 视觉语言：保留什么，收敛什么 ## 保留 ## 收敛 # 5. 首页：让继续…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/development-plan-2026-10-29.md` | 历史材料：SeeWord 开发计划（2026-10-29 起） # 1 三条排序原则 # 2 两条轨道与依赖 # 3 迭代排期 ## 迭代 2 的实施记录（2026-10-29） ## 迭代 3 的实施记录（2…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/a11y-confirm-dialog.png` | 历史 admin-audit-2026-10-26 方案的 a11y-confirm-dialog.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/a11y-report.json` | 历史材料：a11y-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark-a11y-dashboard.png` | 历史 admin-audit-2026-10-26 方案的 dark-a11y-dashboard.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark-a11y-login.png` | 历史 admin-audit-2026-10-26 方案的 dark-a11y-login.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark-a11y-settings.png` | 历史 admin-audit-2026-10-26 方案的 dark-a11y-settings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark-a11y-videos.png` | 历史 admin-audit-2026-10-26 方案的 dark-a11y-videos.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark-dashboard.png` | 历史 admin-audit-2026-10-26 方案的 dark-dashboard.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark-login.png` | 历史 admin-audit-2026-10-26 方案的 dark-login.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark-settings.png` | 历史 admin-audit-2026-10-26 方案的 dark-settings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark-videos.png` | 历史 admin-audit-2026-10-26 方案的 dark-videos.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark2-channels.png` | 历史 admin-audit-2026-10-26 方案的 dark2-channels.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark2-dashboard.png` | 历史 admin-audit-2026-10-26 方案的 dark2-dashboard.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark2-feedback.png` | 历史 admin-audit-2026-10-26 方案的 dark2-feedback.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark2-settings.png` | 历史 admin-audit-2026-10-26 方案的 dark2-settings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark2-users.png` | 历史 admin-audit-2026-10-26 方案的 dark2-users.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/dark2-videos.png` | 历史 admin-audit-2026-10-26 方案的 dark2-videos.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-admin-login-wrong-password.png` | 历史 admin-audit-2026-10-26 方案的 desktop-admin-login-wrong-password.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-admin-login.png` | 历史 admin-audit-2026-10-26 方案的 desktop-admin-login.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-channels-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-channels-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-channels.png` | 历史 admin-audit-2026-10-26 方案的 desktop-channels.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-dashboard-clean.png` | 历史 admin-audit-2026-10-26 方案的 desktop-dashboard-clean.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-dashboard-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-dashboard-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-dashboard.png` | 历史 admin-audit-2026-10-26 方案的 desktop-dashboard.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-feedback-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-feedback-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-feedback.png` | 历史 admin-audit-2026-10-26 方案的 desktop-feedback.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-home-editorial-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-home-editorial-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-home-editorial.png` | 历史 admin-audit-2026-10-26 方案的 desktop-home-editorial.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-report.json` | 历史材料：desktop-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-settings-dirty.png` | 历史 admin-audit-2026-10-26 方案的 desktop-settings-dirty.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-settings-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-settings-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-settings.png` | 历史 admin-audit-2026-10-26 方案的 desktop-settings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-stats-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-stats-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-stats.png` | 历史 admin-audit-2026-10-26 方案的 desktop-stats.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-users-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-users-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-users.png` | 历史 admin-audit-2026-10-26 方案的 desktop-users.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-video-detail-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-video-detail-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-video-detail.png` | 历史 admin-audit-2026-10-26 方案的 desktop-video-detail.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-videos-viewport.png` | 历史 admin-audit-2026-10-26 方案的 desktop-videos-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/desktop-videos.png` | 历史 admin-audit-2026-10-26 方案的 desktop-videos.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/drawer-closed.png` | 历史 admin-audit-2026-10-26 方案的 drawer-closed.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/drawer-opened.png` | 历史 admin-audit-2026-10-26 方案的 drawer-opened.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/drawer-report.json` | 历史材料：drawer-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/drawer-trap.png` | 历史 admin-audit-2026-10-26 方案的 drawer-trap.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-ban-403.png` | 历史 admin-audit-2026-10-26 方案的 err-ban-403.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-dashboard-500.png` | 历史 admin-audit-2026-10-26 方案的 err-dashboard-500.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-expired-session.png` | 历史 admin-audit-2026-10-26 方案的 err-expired-session.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-non-admin.png` | 历史 admin-audit-2026-10-26 方案的 err-non-admin.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-path-report.json` | 历史材料：err-path-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-settings-500.png` | 历史 admin-audit-2026-10-26 方案的 err-settings-500.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-settings-threshold-422.png` | 历史 admin-audit-2026-10-26 方案的 err-settings-threshold-422.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-stats-500-v2.png` | 历史 admin-audit-2026-10-26 方案的 err-stats-500-v2.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-stats-500.png` | 历史 admin-audit-2026-10-26 方案的 err-stats-500.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-users-me-500.png` | 历史 admin-audit-2026-10-26 方案的 err-users-me-500.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/err-videos-500.png` | 历史 admin-audit-2026-10-26 方案的 err-videos-500.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/final-_admin.png` | 历史 admin-audit-2026-10-26 方案的 final-_admin.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/final-_admin_feedback.png` | 历史 admin-audit-2026-10-26 方案的 final-_admin_feedback.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/final-_admin_payments.png` | 历史 admin-audit-2026-10-26 方案的 final-_admin_payments.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/final-_admin_settings.png` | 历史 admin-audit-2026-10-26 方案的 final-_admin_settings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/final-_admin_stats.png` | 历史 admin-audit-2026-10-26 方案的 final-_admin_stats.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/final-_admin_users.png` | 历史 admin-audit-2026-10-26 方案的 final-_admin_users.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/final-_admin_videos.png` | 历史 admin-audit-2026-10-26 方案的 final-_admin_videos.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/channels-filtered-empty-1440.png` | 历史 fixes-pages 方案的 channels-filtered-empty-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/feedback-announce-confirm-1440.png` | 历史 fixes-pages 方案的 feedback-announce-confirm-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/feedback-pagination-1440.png` | 历史 fixes-pages 方案的 feedback-pagination-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/users-error-1440.png` | 历史 fixes-pages 方案的 users-error-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/users-expanded-1440.png` | 历史 fixes-pages 方案的 users-expanded-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/users-filtered-empty-1440.png` | 历史 fixes-pages 方案的 users-filtered-empty-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/users-lastrow-dropdown-1440.png` | 历史 fixes-pages 方案的 users-lastrow-dropdown-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/verify-report.json` | 历史材料：verify-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/video-detail-390.png` | 历史 fixes-pages 方案的 video-detail-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/videos-error-1440.png` | 历史 fixes-pages 方案的 videos-error-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/videos-filtered-empty-1440.png` | 历史 fixes-pages 方案的 videos-filtered-empty-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes-pages/videos-takedown-confirm-1440.png` | 历史 fixes-pages 方案的 videos-takedown-confirm-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-1440-login.png` | 历史 fixes 方案的 fixes-1440-login.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-1440-settings.png` | 历史 fixes 方案的 fixes-1440-settings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-1440-stats.png` | 历史 fixes 方案的 fixes-1440-stats.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-1440-users.png` | 历史 fixes 方案的 fixes-1440-users.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-login-error.png` | 历史 fixes 方案的 fixes-login-error.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-mobile-390-login.png` | 历史 fixes 方案的 fixes-mobile-390-login.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-mobile-390-settings.png` | 历史 fixes 方案的 fixes-mobile-390-settings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-mobile-390-stats.png` | 历史 fixes 方案的 fixes-mobile-390-stats.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-settings-500-error.png` | 历史 fixes 方案的 fixes-settings-500-error.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-settings-normal.png` | 历史 fixes 方案的 fixes-settings-normal.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-settings-threshold-invalid.png` | 历史 fixes 方案的 fixes-settings-threshold-invalid.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-shell-users-me-500.png` | 历史 fixes 方案的 fixes-shell-users-me-500.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-stats-500-error.png` | 历史 fixes 方案的 fixes-stats-500-error.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-stats-normal.png` | 历史 fixes 方案的 fixes-stats-normal.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-users-confirm-dialog.png` | 历史 fixes 方案的 fixes-users-confirm-dialog.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/fixes/fixes-users-lastrow-dropdown.png` | 历史 fixes 方案的 fixes-users-lastrow-dropdown.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/frontend-removal/admin-1440.png` | 历史 frontend-removal 方案的 admin-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/frontend-removal/admin-390.png` | 历史 frontend-removal 方案的 admin-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/frontend-removal/admin-stats-1440.png` | 历史 frontend-removal 方案的 admin-stats-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/frontend-removal/admin-stats-390.png` | 历史 frontend-removal 方案的 admin-stats-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/frontend-removal/admin-users-1440.png` | 历史 frontend-removal 方案的 admin-users-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/frontend-removal/admin-users-390.png` | 历史 frontend-removal 方案的 admin-users-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/frontend-removal/walkthrough.json` | 历史材料：walkthrough.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-confirm-ban.png` | 历史 admin-audit-2026-10-26 方案的 ix-confirm-ban.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-feedback.png` | 历史 admin-audit-2026-10-26 方案的 ix-feedback.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-login-next.png` | 历史 admin-audit-2026-10-26 方案的 ix-login-next.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-report.json` | 历史材料：ix-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-settings-after-nav.png` | 历史 admin-audit-2026-10-26 方案的 ix-settings-after-nav.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-settings-decimal.png` | 历史 admin-audit-2026-10-26 方案的 ix-settings-decimal.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-settings-dirty.png` | 历史 admin-audit-2026-10-26 方案的 ix-settings-dirty.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-stats-7d.png` | 历史 admin-audit-2026-10-26 方案的 ix-stats-7d.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-users-empty-filtered.png` | 历史 admin-audit-2026-10-26 方案的 ix-users-empty-filtered.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-users-expanded.png` | 历史 admin-audit-2026-10-26 方案的 ix-users-expanded.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-users-page2-filter.png` | 历史 admin-audit-2026-10-26 方案的 ix-users-page2-filter.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-users-search.png` | 历史 admin-audit-2026-10-26 方案的 ix-users-search.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-videos-empty-filtered.png` | 历史 admin-audit-2026-10-26 方案的 ix-videos-empty-filtered.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-videos-expanded.png` | 历史 admin-audit-2026-10-26 方案的 ix-videos-expanded.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-videos-search.png` | 历史 admin-audit-2026-10-26 方案的 ix-videos-search.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/ix-videos-status-filter.png` | 历史 admin-audit-2026-10-26 方案的 ix-videos-status-filter.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-admin-login.png` | 历史 admin-audit-2026-10-26 方案的 mobile-admin-login.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-channels-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-channels-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-channels.png` | 历史 admin-audit-2026-10-26 方案的 mobile-channels.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-dashboard-drawer-closed.png` | 历史 admin-audit-2026-10-26 方案的 mobile-dashboard-drawer-closed.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-dashboard-drawer-open.png` | 历史 admin-audit-2026-10-26 方案的 mobile-dashboard-drawer-open.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-dashboard-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-dashboard-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-dashboard.png` | 历史 admin-audit-2026-10-26 方案的 mobile-dashboard.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-dialog-add-video.png` | 历史 admin-audit-2026-10-26 方案的 mobile-dialog-add-video.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-feedback-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-feedback-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-feedback.png` | 历史 admin-audit-2026-10-26 方案的 mobile-feedback.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-home-editorial-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-home-editorial-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-home-editorial.png` | 历史 admin-audit-2026-10-26 方案的 mobile-home-editorial.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-report.json` | 历史材料：mobile-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-settings-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-settings-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-settings.png` | 历史 admin-audit-2026-10-26 方案的 mobile-settings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-stats-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-stats-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-stats.png` | 历史 admin-audit-2026-10-26 方案的 mobile-stats.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-users-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-users-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-users.png` | 历史 admin-audit-2026-10-26 方案的 mobile-users.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-video-detail-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-video-detail-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-video-detail.png` | 历史 admin-audit-2026-10-26 方案的 mobile-video-detail.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-videos-viewport.png` | 历史 admin-audit-2026-10-26 方案的 mobile-videos-viewport.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/mobile-videos.png` | 历史 admin-audit-2026-10-26 方案的 mobile-videos.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/payments-390.png` | 历史 admin-audit-2026-10-26 方案的 payments-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/payments-walkthrough.json` | 历史材料：payments-walkthrough.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/payments.png` | 历史 admin-audit-2026-10-26 方案的 payments.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/perf-report.json` | 历史材料：perf-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/probe-dark-focus-report.json` | 历史材料：probe-dark-focus-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/probe-double-submit.json` | 历史材料：probe-double-submit.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/probe-dropdown-clip.json` | 历史材料：probe-dropdown-clip.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/probe-focus-login.json` | 历史材料：probe-focus-login.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/probe-lastrow-dropdown.png` | 历史 admin-audit-2026-10-26 方案的 probe-lastrow-dropdown.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/probe-nav-report.json` | 历史材料：probe-nav-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/probe-taborder.json` | 历史材料：probe-taborder.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/admin-audit-2026-10-26/probe-threshold.json` | 历史材料：probe-threshold.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/_gloss-debug.png` | 历史 audit-2026-10-24 方案的 _gloss-debug.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/_home-error-debug.png` | 历史 audit-2026-10-24 方案的 _home-error-debug.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/_probe-home.png` | 历史 audit-2026-10-24 方案的 _probe-home.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/_probe-home2.png` | 历史 audit-2026-10-24 方案的 _probe-home2.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-contact.png` | 历史 audit-2026-10-24 方案的 anon-contact.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-forgot-password.png` | 历史 audit-2026-10-24 方案的 anon-forgot-password.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-login.png` | 历史 audit-2026-10-24 方案的 anon-login.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-onboarding.png` | 历史 audit-2026-10-24 方案的 anon-onboarding.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-privacy.png` | 历史 audit-2026-10-24 方案的 anon-privacy.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-register.png` | 历史 audit-2026-10-24 方案的 anon-register.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-set-password.png` | 历史 audit-2026-10-24 方案的 anon-set-password.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-set-password_token_invalid-token.png` | 历史 audit-2026-10-24 方案的 anon-set-password_token_invalid-token.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/anon-terms.png` | 历史 audit-2026-10-24 方案的 anon-terms.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/bp-home-1024.png` | 历史 audit-2026-10-24 方案的 bp-home-1024.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/bp-home-1440.png` | 历史 audit-2026-10-24 方案的 bp-home-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/bp-home-1920.png` | 历史 audit-2026-10-24 方案的 bp-home-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/bp-home-390.png` | 历史 audit-2026-10-24 方案的 bp-home-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/bp-home-600.png` | 历史 audit-2026-10-24 方案的 bp-home-600.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/bp-home-768.png` | 历史 audit-2026-10-24 方案的 bp-home-768.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/bp-home-820.png` | 历史 audit-2026-10-24 方案的 bp-home-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/channels-filter-rachel.png` | 历史 audit-2026-10-24 方案的 channels-filter-rachel.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/dark-home.png` | 历史 audit-2026-10-24 方案的 dark-home.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/dark-profile.png` | 历史 audit-2026-10-24 方案的 dark-profile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/dark-vocabulary.png` | 历史 audit-2026-10-24 方案的 dark-vocabulary.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/dark-watch_63288cd3-2789-47d7-ba66-a83c982f33a9.png` | 历史 audit-2026-10-24 方案的 dark-watch_63288cd3-2789-47d7-ba66-a83c982f33a9.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-channels.png` | 历史 audit-2026-10-24 方案的 desktop-channels.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-channels_cnbc.png` | 历史 audit-2026-10-24 方案的 desktop-channels_cnbc.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-checkout.png` | 历史 audit-2026-10-24 方案的 desktop-checkout.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-definitely-not-a-page.png` | 历史 audit-2026-10-24 方案的 desktop-definitely-not-a-page.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-favorites.png` | 历史 audit-2026-10-24 方案的 desktop-favorites.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-history.png` | 历史 audit-2026-10-24 方案的 desktop-history.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-notifications.png` | 历史 audit-2026-10-24 方案的 desktop-notifications.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-practice-FAIL.png` | 历史 audit-2026-10-24 方案的 desktop-practice-FAIL.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-practice.png` | 历史 audit-2026-10-24 方案的 desktop-practice.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-practice_daily-FAIL.png` | 历史 audit-2026-10-24 方案的 desktop-practice_daily-FAIL.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-practice_daily.png` | 历史 audit-2026-10-24 方案的 desktop-practice_daily.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-practice_exams.png` | 历史 audit-2026-10-24 方案的 desktop-practice_exams.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-practice_listening-FAIL.png` | 历史 audit-2026-10-24 方案的 desktop-practice_listening-FAIL.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-practice_listening.png` | 历史 audit-2026-10-24 方案的 desktop-practice_listening.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-pricing.png` | 历史 audit-2026-10-24 方案的 desktop-pricing.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-profile.png` | 历史 audit-2026-10-24 方案的 desktop-profile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-rankings.png` | 历史 audit-2026-10-24 方案的 desktop-rankings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-redeem.png` | 历史 audit-2026-10-24 方案的 desktop-redeem.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-root.png` | 历史 audit-2026-10-24 方案的 desktop-root.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-search_q_english.png` | 历史 audit-2026-10-24 方案的 desktop-search_q_english.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-upgrade.png` | 历史 audit-2026-10-24 方案的 desktop-upgrade.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-vocabulary.png` | 历史 audit-2026-10-24 方案的 desktop-vocabulary.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-vocabulary_drill.png` | 历史 audit-2026-10-24 方案的 desktop-vocabulary_drill.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-vocabulary_review.png` | 历史 audit-2026-10-24 方案的 desktop-vocabulary_review.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-vocabulary_sets.png` | 历史 audit-2026-10-24 方案的 desktop-vocabulary_sets.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-watch_63288cd3-2789-47d7-ba66-a83c982f33a9.png` | 历史 audit-2026-10-24 方案的 desktop-watch_63288cd3-2789-47d7-ba66-a83c982f33a9.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-watch_63288cd3-2789-47d7-ba66-a83c982f33a9_transcript.png` | 历史 audit-2026-10-24 方案的 desktop-watch_63288cd3-2789-47d7-ba66-a83c982f33a9_transcript.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/desktop-weekly-report.png` | 历史 audit-2026-10-24 方案的 desktop-weekly-report.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-channels.png` | 历史 audit-2026-10-24 方案的 eyebrow-channels.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-favorites.png` | 历史 audit-2026-10-24 方案的 eyebrow-favorites.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-history.png` | 历史 audit-2026-10-24 方案的 eyebrow-history.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-notifications.png` | 历史 audit-2026-10-24 方案的 eyebrow-notifications.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-practice.png` | 历史 audit-2026-10-24 方案的 eyebrow-practice.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-practice_exams.png` | 历史 audit-2026-10-24 方案的 eyebrow-practice_exams.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-profile.png` | 历史 audit-2026-10-24 方案的 eyebrow-profile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-rankings.png` | 历史 audit-2026-10-24 方案的 eyebrow-rankings.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-search_q_english.png` | 历史 audit-2026-10-24 方案的 eyebrow-search_q_english.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-upgrade.png` | 历史 audit-2026-10-24 方案的 eyebrow-upgrade.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-vocabulary.png` | 历史 audit-2026-10-24 方案的 eyebrow-vocabulary.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/eyebrow-vocabulary_sets.png` | 历史 audit-2026-10-24 方案的 eyebrow-vocabulary_sets.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/fix-mobile-home.png` | 历史 audit-2026-10-24 方案的 fix-mobile-home.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/home-with-subscriptions.png` | 历史 audit-2026-10-24 方案的 home-with-subscriptions.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/ix-FAIL-profile-tabs.png` | 历史 audit-2026-10-24 方案的 ix-FAIL-profile-tabs.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/ix-FAIL-watch-return-source.png` | 历史 audit-2026-10-24 方案的 ix-FAIL-watch-return-source.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/ix-dark-home.png` | 历史 audit-2026-10-24 方案的 ix-dark-home.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/ix-mobile-watch-sticky.png` | 历史 audit-2026-10-24 方案的 ix-mobile-watch-sticky.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/ix-mobile-wordcard.png` | 历史 audit-2026-10-24 方案的 ix-mobile-wordcard.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/lead-diag_profile_tab_progress.png` | 历史 audit-2026-10-24 方案的 lead-diag_profile_tab_progress.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/lead-diag_set-password_from_login.png` | 历史 audit-2026-10-24 方案的 lead-diag_set-password_from_login.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/lead-diag_watch_63288cd3-2789-47d7-ba66-a83c982f33a9_t_30.png` | 历史 audit-2026-10-24 方案的 lead-diag_watch_63288cd3-2789-47d7-ba66-a83c982f33a9_t_30.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/lead-home.png` | 历史 audit-2026-10-24 方案的 lead-home.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/level-selector-mobile.png` | 历史 audit-2026-10-24 方案的 level-selector-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-channels.png` | 历史 audit-2026-10-24 方案的 mobile-channels.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-channels_cnbc.png` | 历史 audit-2026-10-24 方案的 mobile-channels_cnbc.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-favorites.png` | 历史 audit-2026-10-24 方案的 mobile-favorites.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-history.png` | 历史 audit-2026-10-24 方案的 mobile-history.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-notifications.png` | 历史 audit-2026-10-24 方案的 mobile-notifications.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-practice.png` | 历史 audit-2026-10-24 方案的 mobile-practice.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-profile.png` | 历史 audit-2026-10-24 方案的 mobile-profile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-root.png` | 历史 audit-2026-10-24 方案的 mobile-root.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-search_q_english.png` | 历史 audit-2026-10-24 方案的 mobile-search_q_english.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-upgrade.png` | 历史 audit-2026-10-24 方案的 mobile-upgrade.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-vocabulary.png` | 历史 audit-2026-10-24 方案的 mobile-vocabulary.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/mobile-watch_63288cd3-2789-47d7-ba66-a83c982f33a9.png` | 历史 audit-2026-10-24 方案的 mobile-watch_63288cd3-2789-47d7-ba66-a83c982f33a9.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/notif-dropdown-stuck.png` | 历史 audit-2026-10-24 方案的 notif-dropdown-stuck.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/p2-channel-detail.png` | 历史 audit-2026-10-24 方案的 p2-channel-detail.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/p2-history.png` | 历史 audit-2026-10-24 方案的 p2-history.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/p2-home.png` | 历史 audit-2026-10-24 方案的 p2-home.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/p2-upgrade.png` | 历史 audit-2026-10-24 方案的 p2-upgrade.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/recheck-home-390.png` | 历史 audit-2026-10-24 方案的 recheck-home-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/recheck-profile-1024.png` | 历史 audit-2026-10-24 方案的 recheck-profile-1024.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/recheck-profile-1025.png` | 历史 audit-2026-10-24 方案的 recheck-profile-1025.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/recheck-profile-820.png` | 历史 audit-2026-10-24 方案的 recheck-profile-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/redesign-practice-mobile.png` | 历史 audit-2026-10-24 方案的 redesign-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/redesign-practice.png` | 历史 audit-2026-10-24 方案的 redesign-practice.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/redesign-profile-mobile.png` | 历史 audit-2026-10-24 方案的 redesign-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/redesign-profile.png` | 历史 audit-2026-10-24 方案的 redesign-profile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/redesign-vocabulary-mobile.png` | 历史 audit-2026-10-24 方案的 redesign-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/redesign-vocabulary.png` | 历史 audit-2026-10-24 方案的 redesign-vocabulary.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/retest-FAIL-watch-return-source.png` | 历史 audit-2026-10-24 方案的 retest-FAIL-watch-return-source.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/retest-mobile-watch.png` | 历史 audit-2026-10-24 方案的 retest-mobile-watch.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/retest-wordcard-content.png` | 历史 audit-2026-10-24 方案的 retest-wordcard-content.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-channels-1920.png` | 历史 audit-2026-10-24 方案的 rwd-channels-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-channels-360.png` | 历史 audit-2026-10-24 方案的 rwd-channels-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-channels-820.png` | 历史 audit-2026-10-24 方案的 rwd-channels-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-home-1920.png` | 历史 audit-2026-10-24 方案的 rwd-home-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-home-360.png` | 历史 audit-2026-10-24 方案的 rwd-home-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-home-820.png` | 历史 audit-2026-10-24 方案的 rwd-home-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-profile-1920.png` | 历史 audit-2026-10-24 方案的 rwd-profile-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-profile-360.png` | 历史 audit-2026-10-24 方案的 rwd-profile-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-profile-820.png` | 历史 audit-2026-10-24 方案的 rwd-profile-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-vocabulary-1920.png` | 历史 audit-2026-10-24 方案的 rwd-vocabulary-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-vocabulary-360.png` | 历史 audit-2026-10-24 方案的 rwd-vocabulary-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-vocabulary-820.png` | 历史 audit-2026-10-24 方案的 rwd-vocabulary-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-watch-1920.png` | 历史 audit-2026-10-24 方案的 rwd-watch-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-watch-360.png` | 历史 audit-2026-10-24 方案的 rwd-watch-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/rwd-watch-820.png` | 历史 audit-2026-10-24 方案的 rwd-watch-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/audit-2026-10-24/watch-1024.png` | 历史 audit-2026-10-24 方案的 watch-1024.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/brand-refresh-2026-10-31/asset-preview.png` | 历史 brand-refresh-2026-10-31 方案的 asset-preview.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/brand-refresh-2026-10-31/browser-checks.json` | 历史材料：browser-checks.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/brand-refresh-2026-10-31/prompts.json` | 历史材料：prompts.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/brand-refresh-2026-10-31/validation.md` | 历史材料：品牌图标与默认头像替换验证 # 已通过 # 验证限制；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/design-redo/anon-contact-desktop.png` | 历史 design-redo 方案的 anon-contact-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-contact-mobile.png` | 历史 design-redo 方案的 anon-contact-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-forgot-password-desktop.png` | 历史 design-redo 方案的 anon-forgot-password-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-forgot-password-mobile.png` | 历史 design-redo 方案的 anon-forgot-password-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-forgot_password-desktop.png` | 历史 design-redo 方案的 anon-forgot_password-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-forgot_password-mobile.png` | 历史 design-redo 方案的 anon-forgot_password-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-login-desktop.png` | 历史 design-redo 方案的 anon-login-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-login-mobile.png` | 历史 design-redo 方案的 anon-login-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-onboarding-desktop.png` | 历史 design-redo 方案的 anon-onboarding-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-onboarding-mobile.png` | 历史 design-redo 方案的 anon-onboarding-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-pricing-desktop.png` | 历史 design-redo 方案的 anon-pricing-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-pricing-mobile.png` | 历史 design-redo 方案的 anon-pricing-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-privacy-desktop.png` | 历史 design-redo 方案的 anon-privacy-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-privacy-mobile.png` | 历史 design-redo 方案的 anon-privacy-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-redeem-desktop.png` | 历史 design-redo 方案的 anon-redeem-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-redeem-mobile.png` | 历史 design-redo 方案的 anon-redeem-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-register-desktop.png` | 历史 design-redo 方案的 anon-register-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-register-mobile.png` | 历史 design-redo 方案的 anon-register-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-set-password-desktop.png` | 历史 design-redo 方案的 anon-set-password-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-set-password-mobile.png` | 历史 design-redo 方案的 anon-set-password-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-terms-desktop.png` | 历史 design-redo 方案的 anon-terms-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-terms-mobile.png` | 历史 design-redo 方案的 anon-terms-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-upgrade-desktop.png` | 历史 design-redo 方案的 anon-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/anon-upgrade-mobile.png` | 历史 design-redo 方案的 anon-upgrade-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-channels-desktop.png` | 历史 design-redo 方案的 audit-20261024-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-channels-mobile.png` | 历史 design-redo 方案的 audit-20261024-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-favorites-desktop.png` | 历史 design-redo 方案的 audit-20261024-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-favorites-mobile.png` | 历史 design-redo 方案的 audit-20261024-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-history-desktop.png` | 历史 design-redo 方案的 audit-20261024-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-history-mobile.png` | 历史 design-redo 方案的 audit-20261024-history-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-home-desktop.png` | 历史 design-redo 方案的 audit-20261024-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-home-mobile.png` | 历史 design-redo 方案的 audit-20261024-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-index.json` | 历史材料：audit-20261024-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-notifications-desktop.png` | 历史 design-redo 方案的 audit-20261024-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-notifications-mobile.png` | 历史 design-redo 方案的 audit-20261024-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-practice-desktop.png` | 历史 design-redo 方案的 audit-20261024-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-practice-mobile.png` | 历史 design-redo 方案的 audit-20261024-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-profile-desktop.png` | 历史 design-redo 方案的 audit-20261024-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-profile-mobile.png` | 历史 design-redo 方案的 audit-20261024-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-rankings-desktop.png` | 历史 design-redo 方案的 audit-20261024-rankings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-rankings-mobile.png` | 历史 design-redo 方案的 audit-20261024-rankings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-search_q_english-desktop.png` | 历史 design-redo 方案的 audit-20261024-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-search_q_english-mobile.png` | 历史 design-redo 方案的 audit-20261024-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-upgrade-desktop.png` | 历史 design-redo 方案的 audit-20261024-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-upgrade-mobile.png` | 历史 design-redo 方案的 audit-20261024-upgrade-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-vocabulary-desktop.png` | 历史 design-redo 方案的 audit-20261024-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-vocabulary-mobile.png` | 历史 design-redo 方案的 audit-20261024-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-vocabulary_review-desktop.png` | 历史 design-redo 方案的 audit-20261024-vocabulary_review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit-20261024-vocabulary_review-mobile.png` | 历史 design-redo 方案的 audit-20261024-vocabulary_review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-favorites-desktop.png` | 历史 design-redo 方案的 audit1-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-favorites-mobile.png` | 历史 design-redo 方案的 audit1-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-index.json` | 历史材料：audit1-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-practice-desktop.png` | 历史 design-redo 方案的 audit1-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-practice-mobile.png` | 历史 design-redo 方案的 audit1-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-profile-desktop.png` | 历史 design-redo 方案的 audit1-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-profile-mobile.png` | 历史 design-redo 方案的 audit1-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-rankings-desktop.png` | 历史 design-redo 方案的 audit1-rankings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-rankings-mobile.png` | 历史 design-redo 方案的 audit1-rankings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-search_q_english-desktop.png` | 历史 design-redo 方案的 audit1-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-search_q_english-mobile.png` | 历史 design-redo 方案的 audit1-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-vocabulary-desktop.png` | 历史 design-redo 方案的 audit1-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit1-vocabulary-mobile.png` | 历史 design-redo 方案的 audit1-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit2-favorites-desktop.png` | 历史 design-redo 方案的 audit2-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit2-favorites-mobile.png` | 历史 design-redo 方案的 audit2-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit2-index.json` | 历史材料：audit2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit2-search_q_english-desktop.png` | 历史 design-redo 方案的 audit2-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit2-search_q_english-mobile.png` | 历史 design-redo 方案的 audit2-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-channels-desktop.png` | 历史 design-redo 方案的 audit3-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-channels-mobile.png` | 历史 design-redo 方案的 audit3-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-channels_english-with-lucy-desktop.png` | 历史 design-redo 方案的 audit3-channels_english-with-lucy-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-channels_english-with-lucy-mobile.png` | 历史 design-redo 方案的 audit3-channels_english-with-lucy-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-index.json` | 历史材料：audit3-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-practice_daily-desktop.png` | 历史 design-redo 方案的 audit3-practice_daily-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-practice_daily-mobile.png` | 历史 design-redo 方案的 audit3-practice_daily-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-profile_tab_settings-desktop.png` | 历史 design-redo 方案的 audit3-profile_tab_settings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-profile_tab_settings-mobile.png` | 历史 design-redo 方案的 audit3-profile_tab_settings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-vocabulary_review-desktop.png` | 历史 design-redo 方案的 audit3-vocabulary_review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit3-vocabulary_review-mobile.png` | 历史 design-redo 方案的 audit3-vocabulary_review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit4-channels-desktop.png` | 历史 design-redo 方案的 audit4-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit4-channels-mobile.png` | 历史 design-redo 方案的 audit4-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit4-index.json` | 历史材料：audit4-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit4-practice_daily-desktop.png` | 历史 design-redo 方案的 audit4-practice_daily-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit4-practice_daily-mobile.png` | 历史 design-redo 方案的 audit4-practice_daily-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit4-profile_tab_settings-desktop.png` | 历史 design-redo 方案的 audit4-profile_tab_settings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit4-profile_tab_settings-mobile.png` | 历史 design-redo 方案的 audit4-profile_tab_settings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit5-index.json` | 历史材料：audit5-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit5-practice_exams-desktop.png` | 历史 design-redo 方案的 audit5-practice_exams-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit5-practice_exams-mobile.png` | 历史 design-redo 方案的 audit5-practice_exams-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit5-redeem-desktop.png` | 历史 design-redo 方案的 audit5-redeem-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit5-redeem-mobile.png` | 历史 design-redo 方案的 audit5-redeem-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit5-vocabulary_review-desktop.png` | 历史 design-redo 方案的 audit5-vocabulary_review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit5-vocabulary_review-mobile.png` | 历史 design-redo 方案的 audit5-vocabulary_review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit6-exam-desktop.png` | 历史 design-redo 方案的 audit6-exam-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit6-exam-mobile.png` | 历史 design-redo 方案的 audit6-exam-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit7-index.json` | 历史材料：audit7-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit7-vocabulary_drill-desktop.png` | 历史 design-redo 方案的 audit7-vocabulary_drill-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit7-vocabulary_drill-mobile.png` | 历史 design-redo 方案的 audit7-vocabulary_drill-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-checkout-desktop.png` | 历史 design-redo 方案的 audit8-checkout-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-checkout-mobile.png` | 历史 design-redo 方案的 audit8-checkout-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-contact-desktop.png` | 历史 design-redo 方案的 audit8-contact-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-contact-mobile.png` | 历史 design-redo 方案的 audit8-contact-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-index.json` | 历史材料：audit8-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-pricing-desktop.png` | 历史 design-redo 方案的 audit8-pricing-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-pricing-mobile.png` | 历史 design-redo 方案的 audit8-pricing-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-rankings-desktop.png` | 历史 design-redo 方案的 audit8-rankings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-rankings-mobile.png` | 历史 design-redo 方案的 audit8-rankings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-redeem-desktop.png` | 历史 design-redo 方案的 audit8-redeem-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-redeem-mobile.png` | 历史 design-redo 方案的 audit8-redeem-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-weekly-report-desktop.png` | 历史 design-redo 方案的 audit8-weekly-report-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/audit8-weekly-report-mobile.png` | 历史 design-redo 方案的 audit8-weekly-report-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_forgot-password-1440.png` | 历史 auth-final 方案的 _forgot-password-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_forgot-password-390.png` | 历史 auth-final 方案的 _forgot-password-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_login-1440.png` | 历史 auth-final 方案的 _login-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_login-390.png` | 历史 auth-final 方案的 _login-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_privacy-1440.png` | 历史 auth-final 方案的 _privacy-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_privacy-390.png` | 历史 auth-final 方案的 _privacy-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_register-1440.png` | 历史 auth-final 方案的 _register-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_register-390.png` | 历史 auth-final 方案的 _register-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_terms-1440.png` | 历史 auth-final 方案的 _terms-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/_terms-390.png` | 历史 auth-final 方案的 _terms-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/auth-final/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-channels-desktop.png` | 历史 design-redo 方案的 baseline-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-channels-mobile.png` | 历史 design-redo 方案的 baseline-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-favorites-desktop.png` | 历史 design-redo 方案的 baseline-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-favorites-mobile.png` | 历史 design-redo 方案的 baseline-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-history-desktop.png` | 历史 design-redo 方案的 baseline-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-history-mobile.png` | 历史 design-redo 方案的 baseline-history-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-home-desktop.png` | 历史 design-redo 方案的 baseline-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-home-mobile.png` | 历史 design-redo 方案的 baseline-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-index.json` | 历史材料：baseline-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-notifications-desktop.png` | 历史 design-redo 方案的 baseline-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-notifications-mobile.png` | 历史 design-redo 方案的 baseline-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-practice-desktop.png` | 历史 design-redo 方案的 baseline-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-practice-mobile.png` | 历史 design-redo 方案的 baseline-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-profile-desktop.png` | 历史 design-redo 方案的 baseline-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-profile-mobile.png` | 历史 design-redo 方案的 baseline-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-search_q_english-desktop.png` | 历史 design-redo 方案的 baseline-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-search_q_english-mobile.png` | 历史 design-redo 方案的 baseline-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-upgrade-desktop.png` | 历史 design-redo 方案的 baseline-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-upgrade-mobile.png` | 历史 design-redo 方案的 baseline-upgrade-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-vocabulary-desktop.png` | 历史 design-redo 方案的 baseline-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/baseline-vocabulary-mobile.png` | 历史 design-redo 方案的 baseline-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-history-desktop.png` | 历史 design-redo 方案的 batch1-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-history-mobile.png` | 历史 design-redo 方案的 batch1-history-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-index.json` | 历史材料：batch1-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-notifications-desktop.png` | 历史 design-redo 方案的 batch1-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-notifications-mobile.png` | 历史 design-redo 方案的 batch1-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-profile-desktop.png` | 历史 design-redo 方案的 batch1-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-profile-mobile.png` | 历史 design-redo 方案的 batch1-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-vocabulary_review-desktop.png` | 历史 design-redo 方案的 batch1-vocabulary_review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-vocabulary_review-mobile.png` | 历史 design-redo 方案的 batch1-vocabulary_review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-vocabulary_sets-desktop.png` | 历史 design-redo 方案的 batch1-vocabulary_sets-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch1-vocabulary_sets-mobile.png` | 历史 design-redo 方案的 batch1-vocabulary_sets-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch2-index.json` | 历史材料：batch2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch2-vocabulary_review-desktop.png` | 历史 design-redo 方案的 batch2-vocabulary_review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch2-vocabulary_review-mobile.png` | 历史 design-redo 方案的 batch2-vocabulary_review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch2-vocabulary_sets-desktop.png` | 历史 design-redo 方案的 batch2-vocabulary_sets-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch2-vocabulary_sets-mobile.png` | 历史 design-redo 方案的 batch2-vocabulary_sets-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch3-index.json` | 历史材料：batch3-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch3-vocabulary_review-desktop.png` | 历史 design-redo 方案的 batch3-vocabulary_review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch3-vocabulary_review-mobile.png` | 历史 design-redo 方案的 batch3-vocabulary_review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch3-vocabulary_sets-desktop.png` | 历史 design-redo 方案的 batch3-vocabulary_sets-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch3-vocabulary_sets-mobile.png` | 历史 design-redo 方案的 batch3-vocabulary_sets-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-index.json` | 历史材料：batch4-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-notifications-desktop.png` | 历史 design-redo 方案的 batch4-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-notifications-mobile.png` | 历史 design-redo 方案的 batch4-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-profile_tab_account-desktop.png` | 历史 design-redo 方案的 batch4-profile_tab_account-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-profile_tab_account-mobile.png` | 历史 design-redo 方案的 batch4-profile_tab_account-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-profile_tab_profile-desktop.png` | 历史 design-redo 方案的 batch4-profile_tab_profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-profile_tab_profile-mobile.png` | 历史 design-redo 方案的 batch4-profile_tab_profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-profile_tab_progress-desktop.png` | 历史 design-redo 方案的 batch4-profile_tab_progress-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-profile_tab_progress-mobile.png` | 历史 design-redo 方案的 batch4-profile_tab_progress-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-profile_tab_settings-desktop.png` | 历史 design-redo 方案的 batch4-profile_tab_settings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch4-profile_tab_settings-mobile.png` | 历史 design-redo 方案的 batch4-profile_tab_settings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-index.json` | 历史材料：batch5-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-notifications-desktop.png` | 历史 design-redo 方案的 batch5-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-notifications-mobile.png` | 历史 design-redo 方案的 batch5-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-profile-desktop.png` | 历史 design-redo 方案的 batch5-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-profile-mobile.png` | 历史 design-redo 方案的 batch5-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-profile_tab_progress-desktop.png` | 历史 design-redo 方案的 batch5-profile_tab_progress-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-profile_tab_progress-mobile.png` | 历史 design-redo 方案的 batch5-profile_tab_progress-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-profile_tab_settings-desktop.png` | 历史 design-redo 方案的 batch5-profile_tab_settings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch5-profile_tab_settings-mobile.png` | 历史 design-redo 方案的 batch5-profile_tab_settings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch6-index.json` | 历史材料：batch6-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch6-profile_tab_progress-desktop.png` | 历史 design-redo 方案的 batch6-profile_tab_progress-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch6-profile_tab_progress-mobile.png` | 历史 design-redo 方案的 batch6-profile_tab_progress-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch6-profile_tab_settings-desktop.png` | 历史 design-redo 方案的 batch6-profile_tab_settings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch6-profile_tab_settings-mobile.png` | 历史 design-redo 方案的 batch6-profile_tab_settings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch7-index.json` | 历史材料：batch7-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch7-notifications-desktop.png` | 历史 design-redo 方案的 batch7-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch7-notifications-mobile.png` | 历史 design-redo 方案的 batch7-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch8-index.json` | 历史材料：batch8-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch8-notifications-desktop.png` | 历史 design-redo 方案的 batch8-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/batch8-notifications-mobile.png` | 历史 design-redo 方案的 batch8-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-channels-desktop.png` | 历史 design-redo 方案的 before-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-channels-mobile.png` | 历史 design-redo 方案的 before-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-favorites-desktop.png` | 历史 design-redo 方案的 before-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-favorites-mobile.png` | 历史 design-redo 方案的 before-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-history-desktop.png` | 历史 design-redo 方案的 before-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-history-mobile.png` | 历史 design-redo 方案的 before-history-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-home-desktop.png` | 历史 design-redo 方案的 before-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-home-mobile.png` | 历史 design-redo 方案的 before-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-index.json` | 历史材料：before-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-notifications-desktop.png` | 历史 design-redo 方案的 before-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-notifications-mobile.png` | 历史 design-redo 方案的 before-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-practice-desktop.png` | 历史 design-redo 方案的 before-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-practice-mobile.png` | 历史 design-redo 方案的 before-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-profile-desktop.png` | 历史 design-redo 方案的 before-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-profile-mobile.png` | 历史 design-redo 方案的 before-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-rankings-desktop.png` | 历史 design-redo 方案的 before-rankings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-rankings-mobile.png` | 历史 design-redo 方案的 before-rankings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-search_q_english-desktop.png` | 历史 design-redo 方案的 before-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-search_q_english-mobile.png` | 历史 design-redo 方案的 before-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-upgrade-desktop.png` | 历史 design-redo 方案的 before-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-upgrade-mobile.png` | 历史 design-redo 方案的 before-upgrade-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-vocabulary-desktop.png` | 历史 design-redo 方案的 before-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-vocabulary-mobile.png` | 历史 design-redo 方案的 before-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-vocabulary_review-desktop.png` | 历史 design-redo 方案的 before-vocabulary_review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/before-vocabulary_review-mobile.png` | 历史 design-redo 方案的 before-vocabulary_review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channel-detail-index.json` | 历史材料：channel-detail-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channels-channels-desktop.png` | 历史 design-redo 方案的 channels-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channels-channels-mobile.png` | 历史 design-redo 方案的 channels-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channels-channels_$slug-desktop.png` | 历史 design-redo 方案的 channels-channels_$slug-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channels-channels_$slug-mobile.png` | 历史 design-redo 方案的 channels-channels_$slug-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channels-index.json` | 历史材料：channels-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channels2-channels-desktop.png` | 历史 design-redo 方案的 channels2-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channels2-channels-mobile.png` | 历史 design-redo 方案的 channels2-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/channels2-index.json` | 历史材料：channels2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_-1024.png` | 历史 dark-breakpoints 方案的 _-1024.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_-1366.png` | 历史 dark-breakpoints 方案的 _-1366.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_-1920.png` | 历史 dark-breakpoints 方案的 _-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_-360.png` | 历史 dark-breakpoints 方案的 _-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_-430.png` | 历史 dark-breakpoints 方案的 _-430.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_-600.png` | 历史 dark-breakpoints 方案的 _-600.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_-820.png` | 历史 dark-breakpoints 方案的 _-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_channels-1024.png` | 历史 dark-breakpoints 方案的 _channels-1024.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_channels-1366.png` | 历史 dark-breakpoints 方案的 _channels-1366.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_channels-1920.png` | 历史 dark-breakpoints 方案的 _channels-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_channels-360.png` | 历史 dark-breakpoints 方案的 _channels-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_channels-430.png` | 历史 dark-breakpoints 方案的 _channels-430.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_channels-600.png` | 历史 dark-breakpoints 方案的 _channels-600.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_channels-820.png` | 历史 dark-breakpoints 方案的 _channels-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_practice_listening-1024.png` | 历史 dark-breakpoints 方案的 _practice_listening-1024.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_practice_listening-1366.png` | 历史 dark-breakpoints 方案的 _practice_listening-1366.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_practice_listening-1920.png` | 历史 dark-breakpoints 方案的 _practice_listening-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_practice_listening-360.png` | 历史 dark-breakpoints 方案的 _practice_listening-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_practice_listening-430.png` | 历史 dark-breakpoints 方案的 _practice_listening-430.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_practice_listening-600.png` | 历史 dark-breakpoints 方案的 _practice_listening-600.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_practice_listening-820.png` | 历史 dark-breakpoints 方案的 _practice_listening-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1024.png` | 历史 dark-breakpoints 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1024.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1366.png` | 历史 dark-breakpoints 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1366.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1920.png` | 历史 dark-breakpoints 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1920.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-360.png` | 历史 dark-breakpoints 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-360.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-430.png` | 历史 dark-breakpoints 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-430.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-600.png` | 历史 dark-breakpoints 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-600.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-820.png` | 历史 dark-breakpoints 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-820.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/dark-breakpoints/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-index.json` | 历史材料：data1-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-profile-desktop.png` | 历史 design-redo 方案的 data1-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-profile-mobile.png` | 历史 design-redo 方案的 data1-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-vocabulary-desktop.png` | 历史 design-redo 方案的 data1-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-vocabulary-mobile.png` | 历史 design-redo 方案的 data1-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-vocabulary_drill-desktop.png` | 历史 design-redo 方案的 data1-vocabulary_drill-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-vocabulary_drill-mobile.png` | 历史 design-redo 方案的 data1-vocabulary_drill-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-vocabulary_sets-desktop.png` | 历史 design-redo 方案的 data1-vocabulary_sets-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-vocabulary_sets-mobile.png` | 历史 design-redo 方案的 data1-vocabulary_sets-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-vocabulary_tab_library_sub_words-desktop.png` | 历史 design-redo 方案的 data1-vocabulary_tab_library_sub_words-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data1-vocabulary_tab_library_sub_words-mobile.png` | 历史 design-redo 方案的 data1-vocabulary_tab_library_sub_words-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data2-index.json` | 历史材料：data2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data2-vocabulary-desktop.png` | 历史 design-redo 方案的 data2-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data2-vocabulary-mobile.png` | 历史 design-redo 方案的 data2-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data2-vocabulary_drill-desktop.png` | 历史 design-redo 方案的 data2-vocabulary_drill-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data2-vocabulary_drill-mobile.png` | 历史 design-redo 方案的 data2-vocabulary_drill-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data2-vocabulary_tab_library_sub_words-desktop.png` | 历史 design-redo 方案的 data2-vocabulary_tab_library_sub_words-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data2-vocabulary_tab_library_sub_words-mobile.png` | 历史 design-redo 方案的 data2-vocabulary_tab_library_sub_words-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-index.json` | 历史材料：data3-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-practice_exams_redo-desktop.png` | 历史 design-redo 方案的 data3-practice_exams_redo-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-practice_exams_redo-mobile.png` | 历史 design-redo 方案的 data3-practice_exams_redo-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png` | 历史 design-redo 方案的 data3-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png` | 历史 design-redo 方案的 data3-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-vocabulary_sets-desktop.png` | 历史 design-redo 方案的 data3-vocabulary_sets-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-vocabulary_sets-mobile.png` | 历史 design-redo 方案的 data3-vocabulary_sets-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png` | 历史 design-redo 方案的 data3-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png` | 历史 design-redo 方案的 data3-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5_sieve-desktop.png` | 历史 design-redo 方案的 data3-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5_sieve-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data3-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5_sieve-mobile.png` | 历史 design-redo 方案的 data3-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5_sieve-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data4-index.json` | 历史材料：data4-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data4-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png` | 历史 design-redo 方案的 data4-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data4-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png` | 历史 design-redo 方案的 data4-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data4-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5_sieve-desktop.png` | 历史 design-redo 方案的 data4-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5_sieve-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data4-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5_sieve-mobile.png` | 历史 design-redo 方案的 data4-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5_sieve-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data5-index.json` | 历史材料：data5-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data5-practice_exams_redo-desktop.png` | 历史 design-redo 方案的 data5-practice_exams_redo-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data5-practice_exams_redo-mobile.png` | 历史 design-redo 方案的 data5-practice_exams_redo-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data5-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png` | 历史 design-redo 方案的 data5-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data5-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png` | 历史 design-redo 方案的 data5-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data6-index.json` | 历史材料：data6-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data6-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png` | 历史 design-redo 方案的 data6-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data6-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png` | 历史 design-redo 方案的 data6-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data7-index.json` | 历史材料：data7-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data7-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png` | 历史 design-redo 方案的 data7-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/data7-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png` | 历史 design-redo 方案的 data7-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam1-index.json` | 历史材料：exam1-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam1-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-desktop.png` | 历史 design-redo 方案的 exam1-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam1-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-mobile.png` | 历史 design-redo 方案的 exam1-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam1-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png` | 历史 design-redo 方案的 exam1-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam1-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png` | 历史 design-redo 方案的 exam1-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam2-index.json` | 历史材料：exam2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam2-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-desktop.png` | 历史 design-redo 方案的 exam2-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam2-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-mobile.png` | 历史 design-redo 方案的 exam2-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam2-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png` | 历史 design-redo 方案的 exam2-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam2-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png` | 历史 design-redo 方案的 exam2-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam3-index.json` | 历史材料：exam3-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam3-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-desktop.png` | 历史 design-redo 方案的 exam3-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/exam3-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-mobile.png` | 历史 design-redo 方案的 exam3-practice_exams_a761e56d-5e35-48fc-9825-26e6e6d49939-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/examrunner-desktop.png` | 历史 design-redo 方案的 examrunner-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/examrunner-mobile.png` | 历史 design-redo 方案的 examrunner-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/extra-channels_rachel-s-english-desktop.png` | 历史 design-redo 方案的 extra-channels_rachel-s-english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/extra-channels_rachel-s-english-mobile.png` | 历史 design-redo 方案的 extra-channels_rachel-s-english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/extra-index.json` | 历史材料：extra-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/extra-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-desktop.png` | 历史 design-redo 方案的 extra-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/extra-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-mobile.png` | 历史 design-redo 方案的 extra-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-home-register/_-1440.png` | 历史 final-home-register 方案的 _-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-home-register/_-390.png` | 历史 final-home-register 方案的 _-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-home-register/_channels-1440.png` | 历史 final-home-register 方案的 _channels-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-home-register/_channels-390.png` | 历史 final-home-register 方案的 _channels-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-home-register/_practice-1440.png` | 历史 final-home-register 方案的 _practice-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-home-register/_practice-390.png` | 历史 final-home-register 方案的 _practice-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-home-register/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_-1440.png` | 历史 final-pages 方案的 _-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_-390.png` | 历史 final-pages 方案的 _-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_channels-1440.png` | 历史 final-pages 方案的 _channels-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_channels-390.png` | 历史 final-pages 方案的 _channels-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_channels_rachel-s-english-1440.png` | 历史 final-pages 方案的 _channels_rachel-s-english-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_channels_rachel-s-english-390.png` | 历史 final-pages 方案的 _channels_rachel-s-english-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_contact-1440.png` | 历史 final-pages 方案的 _contact-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_contact-390.png` | 历史 final-pages 方案的 _contact-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_favorites-1440.png` | 历史 final-pages 方案的 _favorites-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_favorites-390.png` | 历史 final-pages 方案的 _favorites-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_history-1440.png` | 历史 final-pages 方案的 _history-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_history-390.png` | 历史 final-pages 方案的 _history-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_notifications-1440.png` | 历史 final-pages 方案的 _notifications-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_notifications-390.png` | 历史 final-pages 方案的 _notifications-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_practice-1440.png` | 历史 final-pages 方案的 _practice-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_practice-390.png` | 历史 final-pages 方案的 _practice-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_practice_listening-1440.png` | 历史 final-pages 方案的 _practice_listening-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_practice_listening-390.png` | 历史 final-pages 方案的 _practice_listening-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_profile-1440.png` | 历史 final-pages 方案的 _profile-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_profile-390.png` | 历史 final-pages 方案的 _profile-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_profile_tab_settings-1440.png` | 历史 final-pages 方案的 _profile_tab_settings-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_profile_tab_settings-390.png` | 历史 final-pages 方案的 _profile_tab_settings-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_rankings-1440.png` | 历史 final-pages 方案的 _rankings-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_rankings-390.png` | 历史 final-pages 方案的 _rankings-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_search_q_english-1440.png` | 历史 final-pages 方案的 _search_q_english-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_search_q_english-390.png` | 历史 final-pages 方案的 _search_q_english-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_upgrade-1440.png` | 历史 final-pages 方案的 _upgrade-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_upgrade-390.png` | 历史 final-pages 方案的 _upgrade-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_vocabulary-1440.png` | 历史 final-pages 方案的 _vocabulary-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_vocabulary-390.png` | 历史 final-pages 方案的 _vocabulary-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_vocabulary_review-1440.png` | 历史 final-pages 方案的 _vocabulary_review-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_vocabulary_review-390.png` | 历史 final-pages 方案的 _vocabulary_review-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_vocabulary_sets-1440.png` | 历史 final-pages 方案的 _vocabulary_sets-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_vocabulary_sets-390.png` | 历史 final-pages 方案的 _vocabulary_sets-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1440.png` | 历史 final-pages 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-390.png` | 历史 final-pages 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-pages/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-register/_register-1440.png` | 历史 final-register 方案的 _register-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-register/_register-390.png` | 历史 final-register 方案的 _register-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-register/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/final-report.json` | 历史材料：final-report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/fixdrill-index.json` | 历史材料：fixdrill-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/fixdrill-vocabulary_drill-desktop.png` | 历史 design-redo 方案的 fixdrill-vocabulary_drill-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/fixdrill-vocabulary_drill-mobile.png` | 历史 design-redo 方案的 fixdrill-vocabulary_drill-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/fixdrill2-index.json` | 历史材料：fixdrill2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/fixdrill2-vocabulary_drill-desktop.png` | 历史 design-redo 方案的 fixdrill2-vocabulary_drill-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/fixdrill2-vocabulary_drill-mobile.png` | 历史 design-redo 方案的 fixdrill2-vocabulary_drill-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/flow-0-1440.png` | 历史 flows-final 方案的 flow-0-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/flow-0-390.png` | 历史 flows-final 方案的 flow-0-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/flow-1-1440.png` | 历史 flows-final 方案的 flow-1-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/flow-1-390.png` | 历史 flows-final 方案的 flow-1-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/flow-2-1440.png` | 历史 flows-final 方案的 flow-2-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/flow-2-390.png` | 历史 flows-final 方案的 flow-2-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/flow-3-1440.png` | 历史 flows-final 方案的 flow-3-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/flow-3-390.png` | 历史 flows-final 方案的 flow-3-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/result-1440.png` | 历史 flows-final 方案的 result-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/flows-final/result-390.png` | 历史 flows-final 方案的 result-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/home-home-desktop.png` | 历史 design-redo 方案的 home-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/home-home-mobile.png` | 历史 design-redo 方案的 home-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/home-index.json` | 历史材料：home-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/home2-channels-desktop.png` | 历史 design-redo 方案的 home2-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/home2-channels-mobile.png` | 历史 design-redo 方案的 home2-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/home2-home-desktop.png` | 历史 design-redo 方案的 home2-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/home2-home-mobile.png` | 历史 design-redo 方案的 home2-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/home2-index.json` | 历史材料：home2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/listening-ui/_practice_listening-1440.png` | 历史 listening-ui 方案的 _practice_listening-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/listening-ui/_practice_listening-390.png` | 历史 listening-ui 方案的 _practice_listening-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/listening-ui/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_contact-1440.png` | 历史 other-pages 方案的 _contact-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_contact-390.png` | 历史 other-pages 方案的 _contact-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_notifications-1440.png` | 历史 other-pages 方案的 _notifications-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_notifications-390.png` | 历史 other-pages 方案的 _notifications-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_profile-1440.png` | 历史 other-pages 方案的 _profile-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_profile-390.png` | 历史 other-pages 方案的 _profile-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_profile_tab_progress-1440.png` | 历史 other-pages 方案的 _profile_tab_progress-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_profile_tab_progress-390.png` | 历史 other-pages 方案的 _profile_tab_progress-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_profile_tab_settings-1440.png` | 历史 other-pages 方案的 _profile_tab_settings-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_profile_tab_settings-390.png` | 历史 other-pages 方案的 _profile_tab_settings-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_rankings-1440.png` | 历史 other-pages 方案的 _rankings-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_rankings-390.png` | 历史 other-pages 方案的 _rankings-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_upgrade-1440.png` | 历史 other-pages 方案的 _upgrade-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_upgrade-390.png` | 历史 other-pages 方案的 _upgrade-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_vocabulary-1440.png` | 历史 other-pages 方案的 _vocabulary-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_vocabulary-390.png` | 历史 other-pages 方案的 _vocabulary-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_vocabulary_review-1440.png` | 历史 other-pages 方案的 _vocabulary_review-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_vocabulary_review-390.png` | 历史 other-pages 方案的 _vocabulary_review-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_vocabulary_sets-1440.png` | 历史 other-pages 方案的 _vocabulary_sets-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/_vocabulary_sets-390.png` | 历史 other-pages 方案的 _vocabulary_sets-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/other-pages/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p2-index.json` | 历史材料：p2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p2-practice-desktop.png` | 历史 design-redo 方案的 p2-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p2-practice-mobile.png` | 历史 design-redo 方案的 p2-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p2-vocabulary-desktop.png` | 历史 design-redo 方案的 p2-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p2-vocabulary-mobile.png` | 历史 design-redo 方案的 p2-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p2-vocabulary_review-desktop.png` | 历史 design-redo 方案的 p2-vocabulary_review-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p2-vocabulary_review-mobile.png` | 历史 design-redo 方案的 p2-vocabulary_review-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-favorites-desktop.png` | 历史 design-redo 方案的 p3-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-favorites-mobile.png` | 历史 design-redo 方案的 p3-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-history-desktop.png` | 历史 design-redo 方案的 p3-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-history-mobile.png` | 历史 design-redo 方案的 p3-history-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-index.json` | 历史材料：p3-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-notifications-desktop.png` | 历史 design-redo 方案的 p3-notifications-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-notifications-mobile.png` | 历史 design-redo 方案的 p3-notifications-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-profile-desktop.png` | 历史 design-redo 方案的 p3-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-profile-mobile.png` | 历史 design-redo 方案的 p3-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-rankings-desktop.png` | 历史 design-redo 方案的 p3-rankings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-rankings-mobile.png` | 历史 design-redo 方案的 p3-rankings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-search_q_english-desktop.png` | 历史 design-redo 方案的 p3-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-search_q_english-mobile.png` | 历史 design-redo 方案的 p3-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-upgrade-desktop.png` | 历史 design-redo 方案的 p3-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/p3-upgrade-mobile.png` | 历史 design-redo 方案的 p3-upgrade-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-channels-desktop.png` | 历史 design-redo 方案的 page-audit-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-channels-mobile.png` | 历史 design-redo 方案的 page-audit-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-channels_cnbc-desktop.png` | 历史 design-redo 方案的 page-audit-channels_cnbc-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-channels_cnbc-mobile.png` | 历史 design-redo 方案的 page-audit-channels_cnbc-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-channels_rachel-s-english-desktop.png` | 历史 design-redo 方案的 page-audit-channels_rachel-s-english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-channels_rachel-s-english-mobile.png` | 历史 design-redo 方案的 page-audit-channels_rachel-s-english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-checkout-desktop.png` | 历史 design-redo 方案的 page-audit-checkout-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-checkout-mobile.png` | 历史 design-redo 方案的 page-audit-checkout-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-favorites-desktop.png` | 历史 design-redo 方案的 page-audit-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-favorites-mobile.png` | 历史 design-redo 方案的 page-audit-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-history-desktop.png` | 历史 design-redo 方案的 page-audit-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-history-mobile.png` | 历史 design-redo 方案的 page-audit-history-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-index.json` | 历史材料：page-audit-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-onboarding-desktop.png` | 历史 design-redo 方案的 page-audit-onboarding-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-onboarding-mobile.png` | 历史 design-redo 方案的 page-audit-onboarding-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-practice-desktop.png` | 历史 design-redo 方案的 page-audit-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-practice-mobile.png` | 历史 design-redo 方案的 page-audit-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-pricing-desktop.png` | 历史 design-redo 方案的 page-audit-pricing-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-pricing-mobile.png` | 历史 design-redo 方案的 page-audit-pricing-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-rankings-desktop.png` | 历史 design-redo 方案的 page-audit-rankings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-rankings-mobile.png` | 历史 design-redo 方案的 page-audit-rankings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-redeem-desktop.png` | 历史 design-redo 方案的 page-audit-redeem-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-redeem-mobile.png` | 历史 design-redo 方案的 page-audit-redeem-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-search-desktop.png` | 历史 design-redo 方案的 page-audit-search-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-search-mobile.png` | 历史 design-redo 方案的 page-audit-search-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-set-password-desktop.png` | 历史 design-redo 方案的 page-audit-set-password-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-set-password-mobile.png` | 历史 design-redo 方案的 page-audit-set-password-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-upgrade-desktop.png` | 历史 design-redo 方案的 page-audit-upgrade-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-upgrade-mobile.png` | 历史 design-redo 方案的 page-audit-upgrade-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-desktop.png` | 历史 design-redo 方案的 page-audit-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-mobile.png` | 历史 design-redo 方案的 page-audit-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit10-index.json` | 历史材料：page-audit10-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit10-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-desktop.png` | 历史 design-redo 方案的 page-audit10-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit10-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-mobile.png` | 历史 design-redo 方案的 page-audit10-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-contact-desktop.png` | 历史 design-redo 方案的 page-audit11-contact-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-contact-mobile.png` | 历史 design-redo 方案的 page-audit11-contact-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-forgot-password-desktop.png` | 历史 design-redo 方案的 page-audit11-forgot-password-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-forgot-password-mobile.png` | 历史 design-redo 方案的 page-audit11-forgot-password-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-index.json` | 历史材料：page-audit11-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-login-desktop.png` | 历史 design-redo 方案的 page-audit11-login-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-login-mobile.png` | 历史 design-redo 方案的 page-audit11-login-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png` | 历史 design-redo 方案的 page-audit11-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png` | 历史 design-redo 方案的 page-audit11-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-register-desktop.png` | 历史 design-redo 方案的 page-audit11-register-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-register-mobile.png` | 历史 design-redo 方案的 page-audit11-register-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png` | 历史 design-redo 方案的 page-audit11-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit11-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png` | 历史 design-redo 方案的 page-audit11-vocabulary_sets_24b300dc-a2f9-4ce6-9e37-719c5bf8a2e5-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit12-index.json` | 历史材料：page-audit12-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit12-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png` | 历史 design-redo 方案的 page-audit12-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit12-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png` | 历史 design-redo 方案的 page-audit12-practice_exams_result_daca7401-33e3-43cd-9c66-98974cc90e1e-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit13-index.json` | 历史材料：page-audit13-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit2-channels_rachel-s-english-desktop.png` | 历史 design-redo 方案的 page-audit2-channels_rachel-s-english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit2-channels_rachel-s-english-mobile.png` | 历史 design-redo 方案的 page-audit2-channels_rachel-s-english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit2-index.json` | 历史材料：page-audit2-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-channels_rachel-s-english-desktop.png` | 历史 design-redo 方案的 page-audit3-channels_rachel-s-english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-channels_rachel-s-english-mobile.png` | 历史 design-redo 方案的 page-audit3-channels_rachel-s-english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-index.json` | 历史材料：page-audit3-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-practice_daily-desktop.png` | 历史 design-redo 方案的 page-audit3-practice_daily-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-practice_daily-mobile.png` | 历史 design-redo 方案的 page-audit3-practice_daily-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-practice_exams-desktop.png` | 历史 design-redo 方案的 page-audit3-practice_exams-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-practice_exams-mobile.png` | 历史 design-redo 方案的 page-audit3-practice_exams-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-vocabulary_drill-desktop.png` | 历史 design-redo 方案的 page-audit3-vocabulary_drill-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit3-vocabulary_drill-mobile.png` | 历史 design-redo 方案的 page-audit3-vocabulary_drill-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit4-channels_rachel-s-english-desktop.png` | 历史 design-redo 方案的 page-audit4-channels_rachel-s-english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit4-channels_rachel-s-english-mobile.png` | 历史 design-redo 方案的 page-audit4-channels_rachel-s-english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit4-index.json` | 历史材料：page-audit4-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit4-practice_exams-desktop.png` | 历史 design-redo 方案的 page-audit4-practice_exams-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit4-practice_exams-mobile.png` | 历史 design-redo 方案的 page-audit4-practice_exams-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit5-index.json` | 历史材料：page-audit5-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit5-practice-desktop.png` | 历史 design-redo 方案的 page-audit5-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit5-practice-mobile.png` | 历史 design-redo 方案的 page-audit5-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit5-vocabulary-desktop.png` | 历史 design-redo 方案的 page-audit5-vocabulary-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit5-vocabulary-mobile.png` | 历史 design-redo 方案的 page-audit5-vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit5-vocabulary_tab_library-desktop.png` | 历史 design-redo 方案的 page-audit5-vocabulary_tab_library-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit5-vocabulary_tab_library-mobile.png` | 历史 design-redo 方案的 page-audit5-vocabulary_tab_library-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit6-index.json` | 历史材料：page-audit6-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit6-rankings-desktop.png` | 历史 design-redo 方案的 page-audit6-rankings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit6-rankings-mobile.png` | 历史 design-redo 方案的 page-audit6-rankings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit6-search_q_english-desktop.png` | 历史 design-redo 方案的 page-audit6-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit6-search_q_english-mobile.png` | 历史 design-redo 方案的 page-audit6-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit7-index.json` | 历史材料：page-audit7-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit7-practice-desktop.png` | 历史 design-redo 方案的 page-audit7-practice-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit7-practice-mobile.png` | 历史 design-redo 方案的 page-audit7-practice-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit7-search_q_english-desktop.png` | 历史 design-redo 方案的 page-audit7-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit7-search_q_english-mobile.png` | 历史 design-redo 方案的 page-audit7-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit8-index.json` | 历史材料：page-audit8-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit8-profile-desktop.png` | 历史 design-redo 方案的 page-audit8-profile-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit8-profile-mobile.png` | 历史 design-redo 方案的 page-audit8-profile-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit8-profile_tab_settings-desktop.png` | 历史 design-redo 方案的 page-audit8-profile_tab_settings-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit8-profile_tab_settings-mobile.png` | 历史 design-redo 方案的 page-audit8-profile_tab_settings-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit9-home-desktop.png` | 历史 design-redo 方案的 page-audit9-home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit9-home-mobile.png` | 历史 design-redo 方案的 page-audit9-home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit9-index.json` | 历史材料：page-audit9-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit9-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c_transcript-desktop.png` | 历史 design-redo 方案的 page-audit9-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c_transcript-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/page-audit9-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c_transcript-mobile.png` | 历史 design-redo 方案的 page-audit9-watch_7fb154f5-3017-41c1-b372-1d065b0cbf6c_transcript-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/personal-channels-desktop.png` | 历史 design-redo 方案的 personal-channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/personal-channels-mobile.png` | 历史 design-redo 方案的 personal-channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/personal-favorites-desktop.png` | 历史 design-redo 方案的 personal-favorites-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/personal-favorites-mobile.png` | 历史 design-redo 方案的 personal-favorites-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/personal-history-desktop.png` | 历史 design-redo 方案的 personal-history-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/personal-history-mobile.png` | 历史 design-redo 方案的 personal-history-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/personal-index.json` | 历史材料：personal-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_-1440.png` | 历史 post-build-final 方案的 _-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_-390.png` | 历史 post-build-final 方案的 _-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_channels-1440.png` | 历史 post-build-final 方案的 _channels-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_channels-390.png` | 历史 post-build-final 方案的 _channels-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_favorites-1440.png` | 历史 post-build-final 方案的 _favorites-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_favorites-390.png` | 历史 post-build-final 方案的 _favorites-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_practice-1440.png` | 历史 post-build-final 方案的 _practice-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_practice-390.png` | 历史 post-build-final 方案的 _practice-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_practice_listening-1440.png` | 历史 post-build-final 方案的 _practice_listening-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_practice_listening-390.png` | 历史 post-build-final 方案的 _practice_listening-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_practice_listening_6db76fc8-baef-4ef6-8b06-0c319e9a135c-1440.png` | 历史 post-build-final 方案的 _practice_listening_6db76fc8-baef-4ef6-8b06-0c319e9a135c-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_practice_listening_6db76fc8-baef-4ef6-8b06-0c319e9a135c-390.png` | 历史 post-build-final 方案的 _practice_listening_6db76fc8-baef-4ef6-8b06-0c319e9a135c-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_search_q_english-1440.png` | 历史 post-build-final 方案的 _search_q_english-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_search_q_english-390.png` | 历史 post-build-final 方案的 _search_q_english-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1440.png` | 历史 post-build-final 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9-390.png` | 历史 post-build-final 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/post-build-final/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/practice/_channels_rachel-s-english-1440.png` | 历史 practice 方案的 _channels_rachel-s-english-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/practice/_channels_rachel-s-english-390.png` | 历史 practice 方案的 _channels_rachel-s-english-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/practice/_practice-1440.png` | 历史 practice 方案的 _practice-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/practice/_practice-390.png` | 历史 practice 方案的 _practice-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/practice/_search_q_english-1440.png` | 历史 practice 方案的 _search_q_english-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/practice/_search_q_english-390.png` | 历史 practice 方案的 _search_q_english-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/practice/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-fixed-channels_rachel-s-english-desktop.png` | 历史 design-redo 方案的 search-fixed-channels_rachel-s-english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-fixed-channels_rachel-s-english-mobile.png` | 历史 design-redo 方案的 search-fixed-channels_rachel-s-english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-fixed-index.json` | 历史材料：search-fixed-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-fixed-search_q_TED_group_channels-desktop.png` | 历史 design-redo 方案的 search-fixed-search_q_TED_group_channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-fixed-search_q_TED_group_channels-mobile.png` | 历史 design-redo 方案的 search-fixed-search_q_TED_group_channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-fixed-search_q_english-desktop.png` | 历史 design-redo 方案的 search-fixed-search_q_english-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-fixed-search_q_english-mobile.png` | 历史 design-redo 方案的 search-fixed-search_q_english-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-index.json` | 历史材料：search-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-search_q_TED_group_channels-desktop.png` | 历史 design-redo 方案的 search-search_q_TED_group_channels-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/search-search_q_TED_group_channels-mobile.png` | 历史 design-redo 方案的 search-search_q_TED_group_channels-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpage-recheck/_practice_exams_redo-1440.png` | 历史 subpage-recheck 方案的 _practice_exams_redo-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpage-recheck/_practice_exams_redo-390.png` | 历史 subpage-recheck 方案的 _practice_exams_redo-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpage-recheck/_vocabulary_drill-1440.png` | 历史 subpage-recheck 方案的 _vocabulary_drill-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpage-recheck/_vocabulary_drill-390.png` | 历史 subpage-recheck 方案的 _vocabulary_drill-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpage-recheck/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_checkout-1440.png` | 历史 subpages-final 方案的 _checkout-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_checkout-390.png` | 历史 subpages-final 方案的 _checkout-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_practice_daily-1440.png` | 历史 subpages-final 方案的 _practice_daily-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_practice_daily-390.png` | 历史 subpages-final 方案的 _practice_daily-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_practice_exams-1440.png` | 历史 subpages-final 方案的 _practice_exams-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_practice_exams-390.png` | 历史 subpages-final 方案的 _practice_exams-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_pricing-1440.png` | 历史 subpages-final 方案的 _pricing-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_pricing-390.png` | 历史 subpages-final 方案的 _pricing-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_redeem-1440.png` | 历史 subpages-final 方案的 _redeem-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_redeem-390.png` | 历史 subpages-final 方案的 _redeem-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9_transcript-1440.png` | 历史 subpages-final 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9_transcript-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_watch_63288cd3-2789-47d7-ba66-a83c982f33a9_transcript-390.png` | 历史 subpages-final 方案的 _watch_63288cd3-2789-47d7-ba66-a83c982f33a9_transcript-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_weekly-report-1440.png` | 历史 subpages-final 方案的 _weekly-report-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/_weekly-report-390.png` | 历史 subpages-final 方案的 _weekly-report-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/subpages-final/report.json` | 历史材料：report.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch-index.json` | 历史材料：watch-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch-watch_63288cd3-2789-47d7-ba66-a83c982f33a9-desktop.png` | 历史 design-redo 方案的 watch-watch_63288cd3-2789-47d7-ba66-a83c982f33a9-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch-watch_63288cd3-2789-47d7-ba66-a83c982f33a9-mobile.png` | 历史 design-redo 方案的 watch-watch_63288cd3-2789-47d7-ba66-a83c982f33a9-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch3-index.json` | 历史材料：watch3-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch3-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-desktop.png` | 历史 design-redo 方案的 watch3-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch3-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-mobile.png` | 历史 design-redo 方案的 watch3-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch4-index.json` | 历史材料：watch4-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch4-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-desktop.png` | 历史 design-redo 方案的 watch4-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch4-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-mobile.png` | 历史 design-redo 方案的 watch4-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch5-index.json` | 历史材料：watch5-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch5-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-desktop.png` | 历史 design-redo 方案的 watch5-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch5-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-mobile.png` | 历史 design-redo 方案的 watch5-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch6-index.json` | 历史材料：watch6-index.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch6-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-desktop.png` | 历史 design-redo 方案的 watch6-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch6-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-mobile.png` | 历史 design-redo 方案的 watch6-watch_28091082-12e9-47dd-ab0c-8533e3bc27a8-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/design-redo/watch7-note-mobile.png` | 历史 design-redo 方案的 watch7-note-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/chromium/channel-1440.png` | 历史 chromium 方案的 channel-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/chromium/channel-390.png` | 历史 chromium 方案的 channel-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/chromium/discover-1440.png` | 历史 chromium 方案的 discover-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/chromium/discover-390.png` | 历史 chromium 方案的 discover-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/chromium/immersive-1440.png` | 历史 chromium 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/chromium/immersive-390.png` | 历史 chromium 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/chromium/watch-1440.png` | 历史 chromium 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/chromium/watch-390.png` | 历史 chromium 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/firefox/immersive-1440.png` | 历史 firefox 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/firefox/immersive-390.png` | 历史 firefox 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/firefox/watch-1440.png` | 历史 firefox 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/firefox/watch-390.png` | 历史 firefox 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/mobile-chrome/immersive-1440.png` | 历史 mobile-chrome 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/mobile-chrome/immersive-390.png` | 历史 mobile-chrome 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/mobile-chrome/watch-1440.png` | 历史 mobile-chrome 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/mobile-chrome/watch-390.png` | 历史 mobile-chrome 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/mobile-iphone/immersive-1440.png` | 历史 mobile-iphone 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/mobile-iphone/immersive-390.png` | 历史 mobile-iphone 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/mobile-iphone/watch-1440.png` | 历史 mobile-iphone 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/mobile-iphone/watch-390.png` | 历史 mobile-iphone 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-2026-10-26/verification.md` | 历史材料：发现与观看体验优化验收 # 结果 # 覆盖范围 # 截图；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/channel-1440.png` | 历史 chromium 方案的 channel-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/channel-390.png` | 历史 chromium 方案的 channel-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/discover-1440.png` | 历史 chromium 方案的 discover-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/discover-390.png` | 历史 chromium 方案的 discover-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/immersive-1440.png` | 历史 chromium 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/immersive-390.png` | 历史 chromium 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/watch-1440.png` | 历史 chromium 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/chromium/watch-390.png` | 历史 chromium 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/firefox/immersive-1440.png` | 历史 firefox 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/firefox/immersive-390.png` | 历史 firefox 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/firefox/watch-1440.png` | 历史 firefox 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/firefox/watch-390.png` | 历史 firefox 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-chrome/immersive-1440.png` | 历史 mobile-chrome 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-chrome/immersive-390.png` | 历史 mobile-chrome 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-chrome/watch-1440.png` | 历史 mobile-chrome 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-chrome/watch-390.png` | 历史 mobile-chrome 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-iphone/immersive-1440.png` | 历史 mobile-iphone 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-iphone/immersive-390.png` | 历史 mobile-iphone 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-iphone/watch-1440.png` | 历史 mobile-iphone 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/mobile-iphone/watch-390.png` | 历史 mobile-iphone 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/verification.md` | 历史材料：发现与观看体验 · 第二版 # 设计变化 # 实景预览 # 验证；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/visual/discover-1440.png` | 历史 visual 方案的 discover-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/visual/discover-390.png` | 历史 visual 方案的 discover-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/visual/discover-feed-390.png` | 历史 visual 方案的 discover-feed-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/visual/immersive-1440.png` | 历史 visual 方案的 immersive-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/visual/immersive-390.png` | 历史 visual 方案的 immersive-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/visual/watch-1440.png` | 历史 visual 方案的 watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/discover-watch-v2-2026-10-26/visual/watch-390.png` | 历史 visual 方案的 watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/design-refresh-desktop.png` | 历史 home-design-refresh 方案的 design-refresh-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/final-channel-detail-1440.png` | 历史 home-design-refresh 方案的 final-channel-detail-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/final-channel-detail-390.png` | 历史 home-design-refresh 方案的 final-channel-detail-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/final-channels-1440.png` | 历史 home-design-refresh 方案的 final-channels-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/final-channels-390.png` | 历史 home-design-refresh 方案的 final-channels-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/final-home-1440.png` | 历史 home-design-refresh 方案的 final-home-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/final-home-390.png` | 历史 home-design-refresh 方案的 final-home-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/home-desktop-1440.png` | 历史 home-design-refresh 方案的 home-desktop-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/home-mobile-390.png` | 历史 home-design-refresh 方案的 home-mobile-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/live-desktop.png` | 历史 home-design-refresh 方案的 live-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-design-refresh/live-mobile.png` | 历史 home-design-refresh 方案的 live-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/01-首页-新编排-1440.png` | 历史 home-editorial 方案的 01-首页-新编排-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/02-首页-新编排-390.png` | 历史 home-editorial 方案的 02-首页-新编排-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/03-管理员-视频详情-首页内容面板.png` | 历史 home-editorial 方案的 03-管理员-视频详情-首页内容面板.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/04-首页编排页-1440.png` | 历史 home-editorial 方案的 04-首页编排页-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/05-预览弹层.png` | 历史 home-editorial 方案的 05-预览弹层.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/06-首页互动-选项反馈展开.png` | 历史 home-editorial 方案的 06-首页互动-选项反馈展开.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/07-首页-发布后-B-1440.png` | 历史 home-editorial 方案的 07-首页-发布后-B-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/08-首页-恢复后-A-1440.png` | 历史 home-editorial 方案的 08-首页-恢复后-A-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/09-恢复上一版-被拒绝.png` | 历史 home-editorial 方案的 09-恢复上一版-被拒绝.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/10-首页-新编排-320.png` | 历史 home-editorial 方案的 10-首页-新编排-320.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/11-real-generation-probe.json` | 历史材料：11-real-generation-probe.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/11-real-generation-probe.txt` | 历史材料：11-real-generation-probe.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/12-homepage-console-probe.json` | 历史材料：12-homepage-console-probe.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/12-homepage-console.txt` | 历史材料：12-homepage-console.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/13-nextjs-dev-issue-evidence.txt` | 历史材料：13-nextjs-dev-issue-evidence.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/14-e2e-full-loop.txt` | 历史材料：14-e2e-full-loop.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/15-e2e-full-loop-final.txt` | 历史材料：15-e2e-full-loop-final.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/16-old-home-regression.txt` | 历史材料：16-old-home-regression.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-390.png` | 历史 home-editorial 方案的 admin-home-editorial-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-409-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-409-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-actions-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-actions-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-preview-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-preview-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-publish-confirm-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-publish-confirm-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-publish-success-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-publish-success-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-rollback-cleared-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-rollback-cleared-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-rollback-cleared-confirm-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-rollback-cleared-confirm-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-rollback-confirm-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-rollback-confirm-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-home-editorial-rollback-success-1440.png` | 历史 home-editorial 方案的 admin-home-editorial-rollback-success-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-390.png` | 历史 home-editorial 方案的 admin-video-home-content-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-409-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-409-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-actions-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-actions-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-error-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-error-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-generation-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-generation-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-generation-success-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-generation-success-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-loading-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-loading-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-preview-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-preview-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/admin-video-home-content-preview-issues-1440.png` | 历史 home-editorial 方案的 admin-video-home-content-preview-issues-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/design-refresh-desktop.png` | 历史 home-editorial 方案的 design-refresh-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/home-desktop-1440.png` | 历史 home-editorial 方案的 home-desktop-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/home-editorial/home-mobile-390.png` | 历史 home-editorial 方案的 home-mobile-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-2/README.md` | 历史材料：迭代 2 浏览器走查证据（购买页 / 个人页会员文案） # 账号与结果 # 文案与代码的对照 # 视口与分支 # 未产出与未执行；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/iteration-2/broker-outage-drill.py` | 历史材料：A05 broker-outage drill: pending intent survives a dead broker and the beat sweep delivers it once t…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/iteration-2/browser-walkthrough-paid.json` | 历史材料：browser-walkthrough-paid.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-2/browser-walkthrough-states.json` | 历史材料：browser-walkthrough-states.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-2/verification-2026-10-30.md` | 历史材料：迭代 2 收尾复核（2026-10-30） # 出口条件对照 # A05：真实 broker 停机演练 # A06：真实 Postgres 并发提交 # A13：契约与页面承诺 # 门禁（本轮真实执行…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/iteration-3/README.md` | 历史材料：迭代 3 · 实施与演练记录（A09、A07、A10、A08） # A09：站外告警与备份恢复（OPS-05/06） ## 0 环境 ## 1 本任务的实现 ### 站外告警（OPS-05） ### …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/iteration-3/a07-2026-10-30.json` | 历史材料：a07-2026-10-30.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/a08-2026-10-30.json` | 历史材料：a08-2026-10-30.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/a08_account_data_drill.py` | 历史材料：A08 / BE-04 隔离演练：数据导出完整性与注销清理。 在一次性 Postgres（隔离 compose 的 pg profile，127.0.0.1:15432）与临时媒体目录 上跑真实的服务…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/iteration-3/a09-webhook-received.jsonl` | 历史材料：a09-webhook-received.jsonl；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/a09_backup_restore_drill.sh` | 历史材料：!/usr/bin/env bash A09 / OPS-06 backup+restore drill, run inside WSL (needs the Docker CLI). # Assum…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/iteration-3/a10-2026-10-30.json` | 历史材料：a10-2026-10-30.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/backup_fail.txt` | 历史材料：backup_fail.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/manifest.json` | 历史材料：manifest.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/restore.txt` | 历史材料：restore.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/restored_media_count.txt` | 历史材料：restored_media_count.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/row_counts.txt` | 历史材料：row_counts.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/summary.txt` | 历史材料：summary.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/target_counts.txt` | 历史材料：target_counts.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/target_revision.txt` | 历史材料：target_revision.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/backup-restore/verify_only.txt` | 历史材料：verify_only.txt；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-3/seed_a09.py` | 历史材料：Seed a throwaway Postgres with representative rows for the A09 drill. Run with the backend venv and …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/iteration-3/webhook_receiver.py` | 历史材料：Tiny webhook receiver for the A09 alert drill. Accepts POST /alert, appends the JSON body as one lin…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/iteration-4/README.md` | 历史材料：迭代 4 · 测量与供应链（A12 + A11） # A12 / 激活留存与事件测量 # A11 / 生产、移动与 GPU 供应链 # 遗留（明确不在本轮「已完成」里）；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/iteration-4/baseline-2026-10-30.json` | 历史材料：baseline-2026-10-30.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/iteration-4/production-smoke-2026-10-31.md` | 历史材料：迭代 4 · 生产 smoke 实跑与负控（A11 第二条出口条件） # 环境与方法 # 实跑结果 # 实跑抓到的三处问题（都已修） ## 1. 生产包客户端崩溃：模块级 let 的 TDZ（产品缺陷…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/iteration-5/README.md` | 历史材料：迭代 5（A14 / A15）实施记录 — 2026-10-31 # 1 A15 切片与落点 # 2 本轮实际执行的验证 # 3 未执行 # 4 本机附带变更（不在仓库内） # 5 第二轮（2026-…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/perf-2026-11/README.md` | 历史材料：加载/处理速度优化 · 实施与实测记录（2026-11） # 1 改了什么 # 2 实测（同一开发库、同一用户/数据，HEAD 与改动后各跑一遍） ## 2.1 /users/me/overview（…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/slcs-2026-11-11/acceptance.md` | 历史材料：SLCS 隔离环境验收记录 · 2026-11-11 # 已执行并通过 # ego-browser 走查（隔离站点，桌面 1080×595 与移动 390×844） # 签发方工具与浏览器发布走查（2…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/slcs-2026-11-11/fsrs_candidate_eval.py` | 历史材料：Compare the shipped S6 scheduler with the Py-FSRS 6.3.2 candidate. Run in a scratch environment that…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/slcs-2026-11-11/isolated-environment.md` | 历史材料：SLCS 隔离验收环境 # 组成 # 重建步骤 # 签发收据（本轮新增） 一次：生成密钥对，私钥写到仓库外，公钥按打印的 JSON 填进后端环境 核对某修订会被签进去的声明（只读） 签发，stdout…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/slcs-2026-11-11/lesson-mobile.png` | 历史 slcs-2026-11-11 方案的 lesson-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/slcs-2026-11-11/word-card.png` | 历史 slcs-2026-11-11 方案的 word-card.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-gateway-capacity-2026-11-04/README.md` | 历史材料：网关降配容量评估（2026-11-04） # 测量方法 # 结论 # 建议 # 复跑；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-capacity-2026-11-04/docker-compose.eval.yml` | 历史材料：Local capacity evaluation for the reduced-footprint gateway. Synthetic provider, disposable DB/Redis…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-host-2026-11-04/README.md` | 历史材料：网关独立主机联调（2026-11-04） # 拓扑 # 本机侧 # 生产侧改动（唯一一处） /etc/ssh/sshd_config.d/20-seeword-gateway-tunnel.conf …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-real-2026-11-03/README.md` | 历史材料：真实网关接入（2026-11-03） # 已落地的接入面 # 已通过的验证 # 免费模型测试（2026-11-03，新 key） # 阻塞：生产侧仍未切换 # 生产资源阻塞 # 生产 provider…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-real-2026-11-03/docker-compose.real.yml` | 历史材料：Local real-provider verification for the V2 gateway stack. Pass the backend .env for COMMANDCODE_* a…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-real-2026-11-03/smoke_real.py` | 历史材料：One real-provider smoke through the adapter → LiteLLM → shim path. Requires the real gateway stack f…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/.gitignore` | 历史材料：.gitignore；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/README.md` | 历史材料：V2 模型网关重新选型（E3a，2026-11-03） # 候选与锁定 # 方法 # 结果 # 结论 # 未验证 # 复跑 LiteLLM；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/bifrost-data/config.json` | 历史材料：config.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/bifrost-results.json` | 历史材料：bifrost-results.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/bifrost.config.json` | 历史材料：bifrost.config.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/docker-compose.bifrost.yml` | 历史材料：Synthetic E3a reselection spike: Bifrost only. No real provider credentials.；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/docker-compose.newapi.yml` | 历史材料：Synthetic E3a reselection spike: New API only. No real provider credentials. Local SQLite under /dat…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/newapi-results.json` | 历史材料：newapi-results.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/provider_stub.py` | 历史材料：Local OpenAI-compatible synthetic provider. Does not call any external service.；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/spike_bifrost.py` | 历史材料：Synthetic E3a reselection probe for Bifrost. Runs against the disposable stack in docker-compose.bif…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-gateway-reselection-2026-11-03/spike_newapi.py` | 历史材料：Synthetic E3a reselection probe for New API. Runs against the disposable stack in docker-compose.new…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-gateway-spike-2026-11-03/README.md` | 历史材料：V2 独立模型网关 E3a 选型 spike（2026-11-03） # 测什么 # 本轮修正的配置错误 # 结果（2026-11-03T11:19Z 本次复跑） # 薄适配层结果（2026-11-0…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-gateway-spike-2026-11-03/results.json` | 历史材料：results.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-kernel-2026-11-03/content-inventory.json` | 历史材料：content-inventory.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-mcp-spike-2026-11-03/README.md` | 历史材料：MCP SDK 依赖与适配层 spike（E0 / E8 前置，2026-11-03） # 结论 # 已验证 # 未证明 / 阻塞 # 下一步（二选一，需独立决定） # 复现要点；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-p024-2026-11/README.md` | 历史材料：P02.4 四题小测与统一命令层（2026-11-09） # 1 为什么没有新表 # 2 落点 # 3 可见性口径（复用，不是新规则） # 4 独立 review 发现并已修复的四类缺陷 # 5 实现…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/README.md` | 历史材料：V2 教学与外部连接 UI 验收（2026-11-03） # 环境 # 本轮走查（接手后复跑） # 截图 # 未覆盖；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/desktop-before.png` | 历史 v2-ui-2026-11-03 方案的 desktop-before.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/desktop-hint-1440.png` | 历史 v2-ui-2026-11-03 方案的 desktop-hint-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/mobile-account-buttons-390.png` | 历史 v2-ui-2026-11-03 方案的 mobile-account-buttons-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/mobile-connections-390.png` | 历史 v2-ui-2026-11-03 方案的 mobile-connections-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/mobile-restored-390.png` | 历史 v2-ui-2026-11-03 方案的 mobile-restored-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-01.mjs` | 历史材料：round-01.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-02.mjs` | 历史材料：round-02.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-03.mjs` | 历史材料：round-03.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-04.mjs` | 历史材料：round-04.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-05.mjs` | 历史材料：round-05.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-06.mjs` | 历史材料：round-06.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-07.mjs` | 历史材料：round-07.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-08.mjs` | 历史材料：round-08.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-09.mjs` | 历史材料：round-09.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-10.mjs` | 历史材料：round-10.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-11.mjs` | 历史材料：round-11.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-12.mjs` | 历史材料：round-12.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-13.mjs` | 历史材料：round-13.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-14.mjs` | 历史材料：round-14.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-15.mjs` | 历史材料：round-15.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-16.mjs` | 历史材料：round-16.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-17.mjs` | 历史材料：round-17.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-18.mjs` | 历史材料：round-18.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-19.mjs` | 历史材料：round-19.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-20.mjs` | 历史材料：round-20.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-21.mjs` | 历史材料：round-21.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-22.mjs` | 历史材料：round-22.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-23.mjs` | 历史材料：round-23.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-24.mjs` | 历史材料：round-24.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-25.mjs` | 历史材料：round-25.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-26.mjs` | 历史材料：round-26.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-27.mjs` | 历史材料：round-27.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-28.mjs` | 历史材料：round-28.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-29.mjs` | 历史材料：round-29.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-30.mjs` | 历史材料：round-30.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-31.mjs` | 历史材料：round-31.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-32.mjs` | 历史材料：round-32.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-33.mjs` | 历史材料：round-33.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-34.mjs` | 历史材料：round-34.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/round-35.mjs` | 历史材料：round-35.mjs；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/v2-ui-2026-11-03/seed_ui.py` | 历史材料：Seed original content only in the dedicated, disposable UI acceptance DB.；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/evidence/w0-merge-2026-11/README.md` | 历史材料：W0 分支合入与门禁归位（2026-11-09） # 1 合入了什么 # 2 SLCS 合入后修补的三件事 # 3 性能分支合并中的冲突与修正 # 4 实际执行的检查 # 5 刻意没合的两条依赖升级 …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/evidence/watch-layout-refresh/desktop-1366.png` | 历史 watch-layout-refresh 方案的 desktop-1366.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/watch-layout-refresh/mobile-compact.png` | 历史 watch-layout-refresh 方案的 mobile-compact.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/watch-layout-refresh/mobile-dark.png` | 历史 watch-layout-refresh 方案的 mobile-dark.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/watch-layout-refresh/mobile-standard.png` | 历史 watch-layout-refresh 方案的 mobile-standard.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/evidence/watch-layout-refresh/verification.md` | 历史材料：播放页布局与缩放验收 · 2026-10-26 # 验证结果 # 覆盖场景 # 截图与素材；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/frontend-ui-interaction-upgrade-2026-11.md` | 历史材料：SeeWord 前端 UI 与交互提升方案 # 1. 结论 # 2. 现状（代码事实） ## 2.1 组件缺口 ## 2.2 依赖现状 # 3. 选型 ## 3.1 2026 年的实际格局 ## 3.…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/gpu-worker-split-2026-10.md` | 历史材料：GPU 转录 worker 拆分：gpu-worker/ 独立组件（2026-10 实施记录） # 1. 背景与目标 # 2. 拆分边界 ## 2.1 移出 backend/ 的东西 ## 2.2 留…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/home-content-operation-guide-2026-10.md` | 历史材料：首页换内容操作说明（管理员日常） # 0. 先弄清两个概念（避免叫混） # 1. 日常换一条主推（最常用，1 分钟） # 2. 用编排页整版调整（换次推、加场景卡） # 3. 恢复上一版 # 4. 状…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/home-design-refresh-verification-2026-10.md` | 历史材料：首页 / 频道页学习决策改版验证（2026-10-20） # 产品改动 ## 首页 ## 频道列表 ## 频道详情 ## 附带修复 # 检查结果 # 数据限制（如实说明）；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/home-editorial-content-execution-plan-2026-10.md` | 历史材料：首页内容维护与 AI 编辑草稿：执行方案 # 1. 要解决的问题与交付结果 # 2. 视觉与产品边界 # 3. 已核实的代码入口 # 4. 实现选择 ## 4.1 内容包与首页位置分开 ## 4.2 …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/home-editorial-content-implementation-2026-10.md` | 历史材料：首页编辑内容 —— 实施契约（2026-10） # 0. 环境事实（已经核过，不用再查） # 1. 架构决定（已拍板，实施时不要自行改成别的形状） # 2. 后端数据模型 ## home_conten…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/home-editorial-verification-2026-10.md` | 历史材料：首页编辑内容 · 独立验证报告（2026-10-20） # 0. 结论摘要 # 1. 环境与基线事实（验证时实测） # 2. 后端验证（backend/，全部带 PYTHONUTF8=1，backen…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/iteration-3-isolation-validation-2026-10-30.md` | 历史材料：迭代 3 · A07 / A10 的隔离环境验证方案（D6 决议） # 1 D6 结论 # 2 隔离环境定义 ## 2.1 边界（不与开发栈、生产共用任何资源） ## 2.2 文件落点 # 3 A07…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/jinshuju-payment-integration-2026-10.md` | 历史材料：金数据收款 → SeeWord 会员自动开通（2026-10 接入说明） # 方案：站内购买（B） # 已验证的事实（2026-10-18 实测） # 代码 # 签名 token 格式 # 配置 # …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/llm-provider-commandcode-integration-2026-10.md` | 历史材料：LLM 接入：Command Code provider（2026-10-20） # 0. 结论先行 # 1. 与 pi 的对应关系（照搬什么、为什么没照搬什么） # 2. 配置契约（backend/…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/llm-provider-commandcode-research-2026-10.md` | 历史材料：pi 的模型接入设计 + commandcode 免费模型调研（2026-10-20） # 0. 结论先行 # A. pi 的模型接入设计 ## A.1 配置文件位置 **[实测]** ## A.2 …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/oss-reference-2026-10.md` | 历史材料：同类项目技术调研（2026-10） # 0. 结论提要 # 1. 分类框架 # 2. 梯队 A：架构同构 ## 2.1 mirumoji — 形态最像 ## 2.2 PolyglotWhisperer…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/product-framework-2026-10-20.md` | 历史材料：SeeWord 产品框架大纲 # 1. 这一轮要解决什么 # 2. 产品定位：真实语境中的英语学习 # 3. 系统的主线、专项和支撑 # 4. 模块边界 ## 4.1 内容发现：帮助用户选 ## 4.…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/product-review-2026-10.md` | 历史材料：SeeWord 产品设计评审（2026-10） # 0. 结论提要 # 1. 已有资产盘点 ## 1.1 内容生产（真正的护城河） ## 1.2 观看与查询体验 ## 1.3 学习闭环（已建的四个环）…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/prototypes/home-direction-2026-10-20/index.html` | 历史材料： Structural alternatives ；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/assets/bob-thumb.png` | 历史 assets 方案的 bob-thumb.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/assets/hero.png` | 历史 assets 方案的 hero.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/assets/shot-desktop-notes.png` | 历史 assets 方案的 shot-desktop-notes.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/assets/shot-desktop.png` | 历史 assets 方案的 shot-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/assets/shot-first-screen.png` | 历史 assets 方案的 shot-first-screen.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/assets/shot-mobile.png` | 历史 assets 方案的 shot-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/assets/thumb-ai-lonely.png` | 历史 assets 方案的 thumb-ai-lonely.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/assets/thumb-relationships.png` | 历史 assets 方案的 thumb-relationships.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/critique-peer.md` | 历史材料：首页新版设计稿 · 同行评审 # 一句话诊断 # P0 · 首屏与核心转化 # P1 · 体验与状态（公测前改） # P2 · 打磨 # 如果只改 3 处；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/current-original.png` | 历史 home-refresh-2026-10 方案的 current-original.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/design-original.png` | 历史 home-refresh-2026-10 方案的 design-original.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/prototypes/home-refresh-2026-10/index.html` | 历史材料： ---------------- sidebar ---------------- ---------------- topbar ---------------- ----------------…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧原型/一次性证据采集程序；不在应用构建、CI 或运行依赖内；可恢复隔离 |
| `docs/security-ssh-credential-rotation-2026-10.md` | 历史材料：生产 SSH 凭据轮换清单（2026-10-29） # 为什么现在要做 # 影响面：谁会用到这把密码 # 第 0 步：先让 sshx.py 能跑 # 前置：先留一条不断链的后路 # 轮换 # 收尾（可…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/slcs/01-product-vision.md` | 历史材料：01 Product Vision · 产品愿景 # 服务对象 # 三个开放方向 # 不做什么 # 首期范围与成功条件；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/slcs/02-product-requirements.md` | 历史材料：02 Product Requirements · 产品需求 # 贡献与站内目录 # 看视频、读字幕与查词 # 站内导师与自带 Agent # 收词与复习 # 页面与入口 # 主要流程 # 交互状态；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/slcs/03-system-architecture.md` | 历史材料：03 System Architecture · 系统架构 # 现状审计 ## 保留 ## 抽离 ## 重设计 ## 退役 ## 可复用的既有实现 ## 必须先解决；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/slcs/05-community-governance.md` | 历史材料：05 Community Governance · 社区治理 # 贡献与用途审核 # 角色与权限 # 发布、修订与撤回 # 规范版本管理 # 对外分发；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/slcs/06-implementation-roadmap.md` | 历史材料：06 Implementation Roadmap · 实施路线 # 阶段 0 · 独立读取与自带 Agent # 阶段 1 · 贡献、发布与撤回 # 阶段 2 · 外链观看，再验收官方嵌入 # 阶段…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/slcs/handover-2026-11-11.md` | 历史材料：SLCS 交接 · 2026-11-11 # 当前状态 # 已经核实的事实 # 审计结果 ## 本轮推翻或修正的审计结论 # 需要你决定的事 # 后续怎么做 ## 第 1 步：读取器独立化 —— **…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/slcs/start-here.md` | 历史材料：明早从这里开始 · SLCS v0.1 放行手册 # 一、现在仓库处于什么状态 # 二、今天要做的四件事 ## 第 1 步 · 配好签发方（不做这步，任何课都发不出去） ## 第 2 步 · 选第一份…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/ui-review-2026-10-21.md` | 历史材料：SeeWord 视觉、布局与交互评审 # 结论 # 范围与验证边界 # F1 · P1 · 交互 / 布局：手机词卡正文被挤为 0px # F2 · P2 · 布局：短屏观看页的显式播放与重听落在首屏…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/ui-review-2026-10-21/drill-mobile.png` | 历史 ui-review-2026-10-21 方案的 drill-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-clip-end.png` | 历史 ui-review-2026-10-21 方案的 fixed-clip-end.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-drill-390.png` | 历史 ui-review-2026-10-21 方案的 fixed-drill-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-clip-end.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-clip-end.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-clip-start.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-clip-start.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-home-1440.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-home-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-home-390.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-home-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-more-390.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-more-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-watch-1280.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-watch-1280.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-watch-1440.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-watch-1440.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-watch-375.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-watch-375.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-watch-390.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-live-word-390.png` | 历史 ui-review-2026-10-21 方案的 fixed-live-word-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-vocabulary-390.png` | 历史 ui-review-2026-10-21 方案的 fixed-vocabulary-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-watch-375.png` | 历史 ui-review-2026-10-21 方案的 fixed-watch-375.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-watch-390.png` | 历史 ui-review-2026-10-21 方案的 fixed-watch-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-word-375.png` | 历史 ui-review-2026-10-21 方案的 fixed-word-375.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/fixed-word-390.png` | 历史 ui-review-2026-10-21 方案的 fixed-word-390.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/home-desktop.png` | 历史 ui-review-2026-10-21 方案的 home-desktop.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/home-mobile.png` | 历史 ui-review-2026-10-21 方案的 home-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/more-mobile.png` | 历史 ui-review-2026-10-21 方案的 more-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/vocabulary-mobile.png` | 历史 ui-review-2026-10-21 方案的 vocabulary-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/watch-desktop-720.png` | 历史 ui-review-2026-10-21 方案的 watch-desktop-720.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/watch-mobile-short.png` | 历史 ui-review-2026-10-21 方案的 watch-mobile-short.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/watch-mobile.png` | 历史 ui-review-2026-10-21 方案的 watch-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/word-mobile-clipped.png` | 历史 ui-review-2026-10-21 方案的 word-mobile-clipped.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/word-mobile-short.png` | 历史 ui-review-2026-10-21 方案的 word-mobile-short.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-2026-10-21/word-mobile.png` | 历史 ui-review-2026-10-21 方案的 word-mobile.png 截图/二进制证据，供当时人工验收；不是业务资源。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/ui-review-fixes-2026-10-21.md` | 历史材料：SeeWord UI 评审修复与本地验收 # F1—F9 处理结果 # 实际页面验收 # 自动检查 # 截图 # 剩余边界；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/v2-direction-alignment-2026-11-02.md` | 历史材料：SeeWord V2 方向对齐：三层路线、独立模型网关与个人记忆 # 0 决策摘要 # 1 三层路线 # 2 独立模型网关 ## 2.1 为什么改 ## 2.2 目标拓扑 ## 2.3 职责边界 ##…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/v2-plan-review-2026-10-31.md` | 历史材料：SeeWord 产品与技术一体化方案 V2.0 · 只读评审 # 0 结论先行 # A 现状证据表 ## A.1 两个必须写进方案前提的数据事实 ## A.2 已有快照与日志的实际边界 # B V2.…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/v2-preparation-2026-11-02.md` | 历史材料：SeeWord V2 升级前准备清单 # 0 结论 # 1 首版目标与边界 # 2 实施前现状核查（2026-11-02，历史基线） # 3 G0 / T0 决策工作卡 ## G0-1 内容资格（阻塞…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/v2-research-review-2026-11-02.md` | 历史材料：SeeWord V2 最新方案复审与选型核查 # 1 结论 # 2 评审输入与证据等级 # 3 优先补进 PR1 的两项遗漏 ## 3.1 账号导出是未交卷答案的出站旁路 ## 3.2 快照需要同时冻…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/v2-technical-design-2026-10-31.md` | 历史材料：SeeWord V2 技术设计方案 ## 2026-11-02 本轮实施决定 # 1. 设计结论与首版边界 # 2. 当前代码接缝与目标组件 # 3. 身份、版本与可信度契约 # 4. 可信内容、快照…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/vocabulary-exam-presentation-implementation.md` | 历史材料：词汇与真题呈现改版实施记录 # 已实现 # 接口增量 # 验证方式与边界 # 验收结果；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/vocabulary-exam-presentation-research-2026-10-22.md` | 历史材料：词汇页与真题页的呈现方式调研 # 结论 # 1. 资料与证据边界 # 2. 当前实现：哪些已经有，哪些值得调整 ## 词汇 ## 真题 # 3. 词汇页：三种形态分别放在合适的位置 ## 推荐首屏；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/watch-baseline-2026-10-20/01-analysis.md` | 历史材料：观看体验基线与核心路径：第一轮论证 # 结论 # 依据与范围 # 本轮交付导航 # 当前能力与复用边界 # 问题与证据 ## 播放可靠性 ## 字幕与内容质量；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/watch-baseline-2026-10-20/02-state-design.md` | 历史材料：观看核心路径：七状态与低保真交互结构 # 设计目标及已确认规则 # 一条状态流 # 一套信息骨架 ## 桌面 ## 手机 # 七个关键状态的结构稿 ## S1 进入；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/watch-baseline-2026-10-20/03-acceptance.md` | 历史材料：AC-01～AC-08：差距与可执行验收清单 # 当前差距总表 # 测试环境与记录要求 # AC-01 内容基线 # AC-02 播放、暂停、拖动与当前句 # AC-03 本句定位与区间重听 # AC…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/watch-baseline-2026-10-20/04-browser-observations.md` | 历史材料：本轮浏览器复现记录 # UI-01：进入与当前句 # UI-02：当前句查词的来源错位 # UI-03：关闭字幕与再次听辨的入口 # UI-04：恢复环境 # 复现边界；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/watch-baseline-2026-10-20/05-implementation-2026-10-21.md` | 历史材料：SeeWord 观看基线：实施与验证记录 # 已实现的观看闭环 # 后端与保存契约 # 已取消能力 # 验证记录 # AC 对照与未完成的人工验收 # 复现入口 ；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/watch-baseline-2026-10-20/collect-samples.ps1` | 历史材料：Analysis-only: public localhost GETs; no account, media, or database writes.；服务当时方案、演练或交接，未用作当前代码运行契约。 | 被新大纲替代的历史方案、审查、交接或说明；必要当前契约另行精简更新；可恢复隔离 |
| `docs/watch-baseline-2026-10-20/listening-checklist.csv` | 历史材料：listening-checklist.csv；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `docs/watch-baseline-2026-10-20/samples.json` | 历史材料：samples.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧方案的截图、运行记录或验收副产物；不属于最新提交保留组；可恢复隔离 |
| `frontend/DESIGN.md` | 旧设计说明合并到 frontend/CLAUDE.md，去掉重复文档入口。 | 旧设计说明合并到 frontend/CLAUDE.md，去掉重复文档入口；可恢复隔离 |
| `refactor-blueprint/README.md` | 历史材料：SeeWord V2 后端框架与重构标准 # 阅读顺序与职责 # 当前进度 ；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/acceptance.md` | 历史材料：后端重构验收标准 # 检查入口 # 上线硬门；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/agent-plan.md` | 历史材料：V2 AI 学习助手实施计划：对齐 ChatGPT 的对话与学习交互 # 1. 已确认的目标与取舍 ## 1.1 最新范围修正：对齐聊天体验，不以自主 Agent 为前提 # 2. 当前起点与必须解决…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/architecture.md` | 历史材料：后端目标框架与边界 # 0. V2 目标依据与范围 # 1. 整体结构 # 2. 模块与数据归属 # 3. 目录与依赖标准 # 4. 事务和队列 # 5. 两种外部推理模式 # 6. 商业与运维底线 ；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/content-verification.md` | 历史材料：内容核验采集操作（P01.4 / CTX09） # 输入与权限 # 操作顺序 只有 qualified 后才有可导入产物；check-manifest 本身仍只检查结构。 # 中断、恢复与冲突；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/contracts.md` | 历史材料：后端接口与共同学习契约 # CTX01 身份与资源 # CTX02 最小学习上下文 # CTX03 确定性教学写入 # CTX04 持久运行与 SSE # CTX05 网关与两种推理模式 # CTX0…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/current-state.md` | 历史材料：后端代码现状 # 装配和运行组件 # 业务模块地图 # V2 已提交试做与待补能力 # 已有验证落点 ；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/execution.md` | 历史材料：后端重构实施包 # 当前实施主线 # B01 基线、归属与消费者清单 # B02 整理模块、数据与事务边界 # B03 教学运行时与记忆 # B04 网关治理与外部生态 # B05 收费、运营与可观测…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/implementation.md` | 历史材料：后端重构实施记录 # B02.1 · 支付结算、通知事务与依赖方向 ## 最终行为与问题对应 ## 文件、消费者与事务拥有者 ## 必要回归与实际检查 只可指向一次性 PG 测试库；fixture 会…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/preparation.md` | 历史材料：V2 开工前准备：环境基线、惰性边界与 P02.2 契约 # 1 结论 # 2 环境与基线 # 3 审计发现与处置 # 4 P02.2 契约冻结 # 5 迁移与发布契约 # 6 本轮实际验证 # 7 …；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/docs/review.md` | 历史材料：后端审查结论与工作区处置 # 1. 结论与代码基线 # 2. 审查发现 ## REV01 · P1 · 本地过期会把漏通知的已付订单排除出补单 ## REV02 · P1 · 批量补单调用内部 com…；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/evidence/content-receipts/README.md` | 历史材料：P01.3 隔离网关回归证据 核对该项目仅含本次测试资源后清理；会停止并移除该项目资源。；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/evidence/content-receipts/gateway-readiness-failure.json` | 历史材料：gateway-readiness-failure.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/evidence/content-receipts/results.json` | 历史材料：results.json；服务当时方案、演练或交接，未用作当前代码运行契约。 | 旧 V2 蓝图/审查/实施快照或其历史证据；当前现状重建于本轮审计；可恢复隔离 |
| `refactor-blueprint/evidence/content-receipts/synthetic.override.yaml` | 独立合成收据演练的 Compose override；仍有运行用途，迁出旧蓝图而非废弃。 | 仍可执行的合成演练配置；移出旧蓝图，输出改为忽略的 tmp/gateway-receipts/；新位置 deploy/v2-gateway/synthetic.receipts.override.yaml |
| `scripts/release.sh` | release；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。 | 唯一 CHANGELOG 依赖早已删除，守卫永久退出；无现存消费者；可恢复隔离 |
