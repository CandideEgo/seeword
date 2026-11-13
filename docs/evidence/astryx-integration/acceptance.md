# Astryx 首轮接入验收记录

日期：2026-11-13。范围：词汇页的视图切换、筛选、搜索和分页；不是全站迁移。

## 实现边界

- 安装官方 `@astryxdesign/core@0.7.15`、`@astryxdesign/theme-neutral@0.7.15`、`@stylexjs/stylex@0.19.0`，使用发布包的预编译 CSS；未执行下载源码的脚本。
- 词汇模块布局挂接 `AstryxProvider`，复用 SeeWord 的主题状态；数据接口、搜索防抖、URL 视图状态、学习流程保持原有实现。
- 用户端视觉映射保留在 `user-ui.css` 局部作用域。处理六个与 Astryx 同名的颜色 token，不引入会重定义既有 Tailwind 语义的 bridge。
- 未修改后端源码、业务库或生产配置；未提交、推送、部署。

## 首次自动化验收（审查修复前）

| 验证                                                                                                                                                          | 结果                           |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| `npm run check`                                                                                                                                               | 通过，未放宽设计门或会话写入门 |
| `npm run test:unit`                                                                                                                                           | 42 个测试文件、393 项测试通过  |
| `npm run build`                                                                                                                                               | 通过，44 个静态页面完成生成    |
| `CI=1 PLAYWRIGHT_BASE_URL=http://localhost:3001 npx playwright test e2e/astryx-vocabulary.spec.ts --project=chromium --workers=1 --retries=0 --reporter=line` | 2 项通过，42.8 秒              |

新增 e2e 使用真实 API 注册隔离测试账号、加入 26 个词，覆盖搜索与组合筛选的服务端参数及返回结果、分页与禁用态、空格键选择、URL 刷新恢复、离开词汇模块后 html 主题属性清理以及后台登录页不挂接 Astryx provider。不是 mock API 验证。

上述是审查修复前的历史结果；两项修复后的最终复验结果与日志见「独立审查与修复」。

## 已执行的 ego-browser 检查

- 使用真实站点、真实隔离账号，经登录界面进入词汇页。
- 1440px 桌面检查：视图、筛选与搜索控件真实渲染，无页面横向溢出；见 `vocabulary-desktop-light.png`。
- 390px 手机检查：亮、暗两种主题页面宽度与视口一致；实测 `scrollWidth=390`。亮色截图见 `vocabulary-mobile-light.png`。
- 实际输入 `habit` 后展示该词；方向键切换掌握程度时选中项变更且 `:focus-visible` 生效。
- 经账号菜单真实切换亮暗主题，Astryx `data-theme` 与应用模式同步。深色稳定后搜索文字为 `rgb(245, 245, 247)`，未选中分段文字为 `rgb(198, 198, 198)`。
- 实际翻到第 2 页并检查页面结果，见 `manual-interactions.json`。
- 深色手机尺寸与稳定颜色见 `mobile-dark-metrics.json`。现有 `vocabulary-mobile-dark.png` 捕获于切换过渡附近，不作为稳定颜色或对比度依据，仍待补一张过渡结束后的截图。

## 隔离环境与中断

- 新建专用本地容器 `seeword-astryx-pg-20261113`（15435）与 `seeword-astryx-redis-20261113`（16385）。迁移仅对专用新库执行成功，没有迁移业务库。
- 验收 API：8002；前端：3001，代理指向 8002。没有为此启动 Celery 或 GPU worker。
- 本机既有 8000 API 当时数据库不健康，未重启或更改该进程。
- 首次以 `127.0.0.1` 访问 Next dev 时，开发源限制阻断 HMR/客户端资源，登录辅助超时；改用已有允许的 `localhost` 后同一测试通过，没有放宽检查或鉴权。
- 截图过程中，Ego Lite 的可见区域与 emulation DPR 不匹配曾导致 CDP 截图超时；匹配 DPR 后取得手机亮色截图。失败尝试不算验收通过。
- 恢复限流中断时，原 ego-browser 任务空间 12 已不存在，8002 API 也已停止。未接管用户当前的浏览器空间，未新建空间绕过恢复限制。继续补截图与人工样式隔离检查需重新建立独立验收空间。

## 独立审查与修复

独立 Opus 审查在首次 429 中断后恢复完成。主代理核对已安装库实现后，修复两项有效发现：

1. neutral theme 的全局 `color-scheme: light dark` 会盖过应用 base 层，导致非词汇页原生 UI 跟随系统而非站内偏好。现将原生模式的唯一声明提升到不分层的 `:root` / `:root.dark`，仍由既有主题状态决定。
2. 跨页入口使用 selection-follows-focus 的单选分段控件时，方向键就会触发路由并卸载焦点。两组跨页入口改为官方 `Button` 与 Next Link，保留页内 replace/no-scroll 与跨页 push 行为；筛选继续使用 `SegmentedControl`。

新增回归检查系统主题与站内选择相反的两种组合，在登录页、首页、词汇页及 provider 卸载后读取真正的 computed `color-scheme`，并验证方向键不导航、Enter 才导航。

### 修复后最终自动化复验

| 验证                                                                                                                                                                                  | 结果                                                              | 原始日志                                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------ |
| `npm run check`                                                                                                                                                                       | 通过，设计门 / 会话写入门 / TypeScript / ESLint / Prettier 均通过 | [check/build](post-review-check-build.log) |
| `npm run test:unit`                                                                                                                                                                   | 42 个文件、393 项通过                                             | [unit](post-review-unit.log)               |
| `npm run build`                                                                                                                                                                       | 通过，44 个静态页面完成生成                                       | [check/build](post-review-check-build.log) |
| `CI=1 PLAYWRIGHT_BASE_URL=http://localhost:3000 npx playwright test e2e/astryx-vocabulary.spec.ts --project=chromium --project=mobile-chrome --workers=1 --retries=0 --reporter=line` | 4 场景 × 桌面/移动端，8 项通过，1.5 分钟，无重试                  | [e2e](post-review-e2e.log)                 |

复验时重新启动原有隔离数据库上的测试 API 与前端，均不使用业务库；收尾停止专用 API、前端及两个验收容器，保留测试数据与容器用于后续重启，不删除业务数据。局部启动配置见 `.claude/launch.json` 的 `astryx-acceptance-api` / `astryx-acceptance-frontend`。

过程边界：独立代理开头误调用会再委派并执行额外浏览器检查的 review skill；主代理未采纳该额外报告或将其作为浏览器验收证据。两项发现均由独立代理和主代理直接核对指定源码及已安装发布包实现确认，本轮不再追加 review。

## 人工复验边界

原 ego-browser 任务空间关闭后，用户明确选择「先完成自动化验证」，因此本轮不新建浏览器空间。修复后过渡结束的深色桌面/手机截图及首页、后台人工样式隔离复核**未执行**；此前截图只代表修复前的首批组件效果，不作为最终导航外观证据。自动化回归不替代这些人工检查。
