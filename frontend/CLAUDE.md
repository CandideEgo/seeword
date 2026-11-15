# 前端工作规则

全局规则见 [根 CLAUDE.md](../CLAUDE.md)，模块关系见 [当前框架](../docs/project-audit/architecture.md)。本文件是当前前端操作和设计约束的唯一说明入口。

## 运行与检查

Next.js 16 App Router / React 19。改 Next 代码前先读本机 `node_modules/next/dist/docs/` 对应指南。`src/proxy.ts` 是网络边界登录墙，不再用 middleware 文件约定。Next 自动维护 agent 规则块；不要在人写段落逐字重复其起止标记。

以下命令都在 `frontend/`：

```bash
npm ci --legacy-peer-deps
```

```bash
npm run dev
```

```bash
npm run check
```

```bash
npm run test:unit
```

```bash
npm run build
```

```bash
npx playwright test
```

- `check` 的组成认 package.json：设计系统、会话写入、tsc、ESLint、Prettier。不得放宽脚本/白名单来让改动过门。
- 低内存本机构建可用 `NEXT_BUILD_CPUS=1 npm run build` 限制静态生成并发；仍执行全部页面与类型检查，不调整超时或检查项。未设置时保留 Next 默认并发。
- Vitest 跑 node 环境下 `src/**/*.test.{ts,tsx}`；Playwright 跑 `e2e/`，不是同一套测试。
- PR CI 主要 Chromium，跨浏览器在独立 workflow；有服务仍要播种 e2e 材料，不能把观看测试 skip 当通过。
- 全量 e2e 使用 `ENV=testing` 的专用后端/数据库，避免开发限流制造假失败。生产镜像 smoke 使用 `scripts/production-smoke.ps1` 与 production 配置，仅限 localhost 的独立栈。

## 会话与代理

- 用户 `authStore` / `api.ts`，管理员 `adminAuthStore` / `adminApi.ts`，互不共用 token。底层 `createApiClient` 共享重试/刷新/错误规则，GET 缓存按身份隔离。
- `authHelpers` 是 localStorage 会话与镜像 cookie 的唯一写入口；`check-session-writes.mjs` 守它。proxy 只查 cookie 是否非空，实际鉴权在后端。
- `mediaUrl()` 对受保护媒体附 query token，日志和错误采集不得泄露查询串。
- `next.config.js` 的 dev rewrite 转发 API/媒体/health；容器开发用 `BACKEND_PROXY_ORIGIN` 指向 backend。生产 standalone 由 nginx 转发，`next start` 自身不会补后端代理。
- `NEXT_PUBLIC_*` 在构建期固定。图片保持 `unoptimized`；远程图源变更同步 remotePatterns，不能让优化器去错误的 standalone `/media` 地址取图。
- `devIndicators: false` 避免徽标覆盖手机播放器操作；不要无理由恢复。局域网 HMR 来源由 `DEV_ALLOWED_ORIGINS` 配置。

## 设计系统

数值只认 `src/app/globals.css` 与 `src/app/user-ui.css`，不在文档抄第二份色值/尺寸表。

- Tailwind v4 CSS-first，无 tailwind.config。全局 token 服务全站；用户端蓝色和版式只在 `.user-ui`，管理端仍使用自己的品牌变量。
- 深色模式换变量，`useTheme` + 根布局脚本防闪烁。改用户端视觉不应改坏后台。
- 只用语义色：canvas、surface、ink/body/muted、hairline、action-primary 等，不写原始调色板/任意 hex。主按钮 `bg-action-primary + text-on-primary`；不把 brand-500 与白字配对。
- 裸 white/black 不作面；透明叠加层与深底白字按检查器允许规则使用。圆角允许集认检查器，不加任意新档位。
- 字号用 display/display-sm/title/copy-lg/copy/meta/caption；数字列用 tabular-nums。数量统一 `lib/format.formatCount`，未知不是 0，真实 0 要展示。
- 页面壳 `MainLayoutInner` 拥有容器和 main；页面不再套 container 或 main。页面 h1 使用 `PageHeader`，首页专用标题例外认检查器。
- 优先复用 `ui` 的 Button/LinkButton/Card/Dialog 等、EmptyState/ErrorState/Spinner 和既有版式原语；状态与 API 错误统一处理，不每页造一套。
- 不加冗余小字、标签、说明和 slogan；必要 label、可访问名称、危险操作后果提示不可删。

### Astryx 试点

词汇模块 layout 挂 `AstryxProvider`，使用官方预编译 CSS，不接 Tailwind token bridge。主题映射放在 `user-ui.css` 局部作用域；同名状态色在 globals 的 `@theme inline` 保持 SeeWord 语义。其它页面/共享控件未迁移，不能把试点当全站替换。相关真实回归是 `e2e/astryx-vocabulary.spec.ts`。

### 播放与响应式

- 观看页共享全站导航，手机播放栏通过 `WatchChromeProvider` 接壳；词卡、抽屉不能挡住播放控制和底部导航。
- 普通断点和版式认 CSS；观看专用手机/桌面切分与画框偏好认 `lib/watchLayout.ts`，不能用统一断点猜测。
- 调布局运行 mobile 系列、watch-desktop-stage、watch-layout.mobile 相关测试；实际核对 390px/1440px 与键盘/暗色状态。
- 品牌文件由 public 和 app 图标入口提供，不复制另一套字母标；头像保留原色，不在暗色反相。
- `scripts/design-shots.mjs` 是可选截图工具，输出本地忽略的 `tmp/design-shots/`；人工浏览器验收仍按根规则执行。

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
