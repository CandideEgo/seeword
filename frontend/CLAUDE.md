# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

前端（`frontend/`）专属的命令与局部约定。架构叙述在根 [`CLAUDE.md`](../CLAUDE.md)，本文件只承接前端自己的东西。

## 这个 Next.js 不是你以为的那个

本仓库是 **Next.js 16**（App Router）——API、约定与文件结构都可能和你训练数据里的不同。**写代码前先读 `frontend/node_modules/next/dist/docs/` 里对应的指南**，留心 deprecation 提示。一个已经撞上的例子：Next 16 把 `middleware` 改名成了 [`src/proxy.ts`](src/proxy.ts) 里的 `proxy`。

另注意：**`next dev` 会往 agent 文件里塞一段托管的 nextjs-agent-rules 块**（`node_modules/next/dist/server/lib/generate-agent-files.js`）：`AGENTS.md` 存在且已托管该块时写它，否则写进 `CLAUDE.md`——**本仓库是后者**，所以那段自动块长在这个文件末尾。不要跟它较劲：本文件其余部分才是人写的、稳定的那份；**看到带 `BEGIN:` / `END:` 标记的托管块出现在 diff 里就顺手提交**，删掉只会让它再次出现。

**但别在本文件的人写段落里逐字写出那两个标记。** `upsertAgentRulesBlock` 用 `indexOf` 找**第一处**起始标记，人写文字里出现一次，它就会把「这处标记 → 真正的结束标记」之间的一切当成待替换的块内容，正文被整段吃掉：2026-10-15 实测，这段提醒原先逐字引用了起始标记，一次 `npm run dev` 就把本文件从 71 行削到 19 行（命令表、两道门、局部约定、e2e 全没了，只剩被截断的半句话）。要指代它就写「起始/结束标记」，或拆开写 `BEGIN:` 与 `END:`。

## 命令

| 目的                                                                     | 命令                                                         |
| ------------------------------------------------------------------------ | ------------------------------------------------------------ |
| 装依赖                                                                   | `npm ci --legacy-peer-deps`                                  |
| dev                                                                      | `npm run dev`                                                |
| build                                                                    | `npm run build`                                              |
| 门禁（design-system + session-writes + typecheck + lint + format:check） | `npm run check`                                              |
| 单测（全量 / 单文件）                                                    | `npm run test:unit` · `npx vitest run src/lib/utils.test.ts` |
| e2e                                                                      | `npx playwright test`                                        |

单测是 Vitest 4，**跑在 node 环境**，只收 `src/**/*.test.{ts,tsx}`——测试与源码同目录，`e2e/` 下的 Playwright spec 不会被它收走。

## 设计系统门（`npm run check` 的第一关）

`frontend/scripts/check-design-system.mjs` 是**九条设计不变量唯一的机器执行点**。取值与组件用法见 [`DESIGN.md`](DESIGN.md)——本文件只讲门禁怎么拦、为什么拦。它扫原始文本（**注释里也扫**，故意的：假阳性只是改个措辞，假阴性会真的放行）：

1. `src/app` 下**不得**出现 `container-page` / `container-wide`——容器归壳层所有
2. `src` 下 `.ts`/`.tsx` **不得**出现原始调色板工具类（`bg-blue-100`、`text-slate-700` 之类）——用语义 token
3. `src` 下 `.tsx` **不得**出现允许集外的 `rounded-*`——允许集仅 `sm|md|lg|pill|full|none`（含方向角）
4. `src/app` 下的 `page.tsx` **不得**自己写 `<h1>`——页面级 h1 只能来自 `ui/PageHeader`（通用）与 `components/home/HomeEditorialHero.tsx` 的 `HomeEditorialHeader`（首页专用）这两个组件；规则只管 page.tsx，组件内部不受限
5. `src` 下 `.ts`/`.tsx` **不得**写任意值 hex 颜色（`border-[#2c2c2c]`）——用语义 token
6. `src` 下 `.ts`/`.tsx` 的无色阶 `white`/`black` **不得当「面」用**：裸 `bg-white`/`bg-black` 要走语义 token；带透明度的叠加层（`bg-black/45`）与前景白字（深底上的 `text-white`）允许
7. `src` 下同一处 className **不得**把 `bg-brand-500` 与 `text-on-primary` 配对——白字压 `#ea580c` 只有 3.12:1（AA 要 4.5:1）；实心主操作一律 `bg-action-primary`（`#c2410c`，5.18:1）
8. `src/app/(main)/` 下**不得**自写 `<main>`——壳层 `MainLayoutInner` 已是全站唯一 main landmark；唯一白名单是壳文件本身
9. 同一行**不得**同时出现 `bg-brand-500` 与裸 `text-white`——与第 7 条同因，专防「白字写成 `text-white` 而不是 `text-on-primary`」这整类回归；跨行的 `text-white` 多是压在橙色圆面上的图标，不算

> 规则 6 按「作用面」分三档：叠加层（带透明度）允许；面（裸 `bg-white`/`bg-black`）违规；前景/描边（`text-white`/`border-white`）允许。
> **前景白字不设卡的理由**：深底白字是本仓常态，语义 token `text-on-dark`(#fafafa) 不是逐字等价替换，且白字是否可读取决于**祖先**底色，静态扫不准——要设卡只能靠整文件豁免，那口子更大。

白名单**点名文件并写理由**，不允许通配（逼着人解释"为什么这个文件例外"）。被列进白名单的文件在该条规则下整文件豁免。**要加白名单之前先想清楚是不是在绕门禁**——根规则是「永不为让检查变绿而放宽检查器」。门禁输出会把**生效中的白名单连理由一起打印**出来，方便评审直接看到每条例外为什么存在。

## 会话写入门（`npm run check` 的第二关）

`frontend/scripts/check-session-writes.mjs` 守着一条不变量：**除了 `src/lib/authHelpers.ts`，`src/` 下不得出现任何会话写入**。两条规则——不得写 `document.cookie`（= 赋值；读不算），不得对会话 key 做 `localStorage` 写入。

为什么值得单开一个门：「已登录」有两个家——localStorage（真身，API 调用带它）与镜像 cookie `seeword_token`（`proxy.ts` 的边缘登录墙只查它的存在性）。两者分开写会造出「用户看着已登录、每个请求被 307 弹回 /login」的状态（修过一次，见 `components/auth/RedirectStuckState.tsx`）。收敛后，写两个家只能经 `authHelpers` 的 `setSession` / `clearSession` / `remirrorSessionCookie`。`src` 下其它 `localStorage` 用途（主题、播放倍速、搜索历史…）不受这条规则影响。

## 几条容易踩的局部约定

**容器归属**：全站唯一的 `.container-page` 在 [`src/app/(main)/MainLayoutInner.tsx`](<src/app/(main)/MainLayoutInner.tsx>) 渲染一次。页面**不得**自己再加容器——这正是设计系统第 1 条拦的东西。

**用户端与观看页导航**：用户端视觉变量放在 `.user-ui` 作用域（`src/app/user-ui.css`），避免调整学习页面时改变管理端。观看页共享全站导航；手机播放栏由 `WatchChromeProvider` 接入壳层，在五项底部导航上方以常规流常驻。词卡下边界取播放栏上沿，短视口保留 240px 操作空间。修改播放布局时同时运行 `mobile-*.spec.ts` 的行为与遮挡检查。

观看页以 1024/1025px 区分手机与桌面，桌面是否分栏再由实际内容宽度决定。画框尺寸独立于当前句、操作和笔记；布局约束与本机偏好契约在 `src/lib/watchLayout.ts`。调整布局时运行 `watch-desktop-stage.spec.ts` 与 `watch-layout.mobile.spec.ts`；观看闭环与四种浏览器的隔离测试见 `e2e/watch-baseline-mobile.spec.ts`。旧录音表已在 2026-10-26 清理迁移 `c3d4e5f6a7b8` 中删除，观看页不再读取录音记录；历史录音文件仍留在媒体目录，仅旧媒体路由的 token 鉴权可读。

**`devIndicators: false` 是故意的，不是随手关的**（[`next.config.js`](next.config.js)）：Next 的 dev 徽标正好压在观看页底栏「上一句」的中心点上（实测 `elementFromPoint(52, 868)` 命中 `NEXTJS-PORTAL`），挪到右下角又压「跟读」，而底栏四角没有一个位置不压按钮——所以唯一能同时保住真机可点性与自动化判据的取值是整个关掉。编译/运行时错误浮层不受影响。

**dev 代理只在 dev 生效**：`next.config.js` 的 `rewrites()` 把 `/api`、`/media`、`/health` 转到 `localhost:8000`，**仅当 `NODE_ENV === "development"`**。生产是 `output: "standalone"` + nginx 反代，没有这些 rewrite。**常规 e2e 使用 `next dev`，生产专项通过 nginx 反代运行（见下节）**；`next start` 本身不提供后端代理。同理，本机真机联调（手机走局域网 IP 访问 dev 站）要靠 `allowedDevOrigins`（默认放行 `192.168.x.x`，其它网段用 `DEV_ALLOWED_ORIGINS`），否则 Next 16 的 cross-site 防护会挡掉 HMR WebSocket，页面停在骨架屏、一个 API 都不发。

**token 双重存放**：真身在 Zustand [`authStore`](src/stores/authStore.ts) 的 localStorage，请求时带 `Authorization: Bearer`；同时镜像到 cookie `seeword_token`，供边缘登录墙 [`src/proxy.ts`](src/proxy.ts) 读取。**登录墙只查 cookie 是否存在**，不解析 JWT、不查库。管理端是另一套：独立 `adminAuthStore` + `seeword_admin_token` + [`lib/adminApi.ts`](src/lib/adminApi.ts)。因为 `<video>`/`<audio>` 发不了请求头，`mediaUrl()` 用 `?token=` 附 token。

**图片直接输出、不走 Next 优化器**：[`next.config.js`](next.config.js) 的 `images.unoptimized: true` 让 `next/image` 原样输出 src（生产 standalone server 上没有 `/media` 路由，优化器的服务端抓取会失败）；`mediaUrl()` 把防盗链的 CDN 经 `/media/proxy` 代理。**新增远程图源要同时加 `next.config.js` 的 `images.remotePatterns`**，否则 `next/image` 会拒。

**品牌素材**：品牌图片与浏览器图标沿用 `/logo.png`、`/logo-large.png`、`/project-icon.svg` 和 `src/app/` 中的图标入口；侧栏与手机顶栏也读取同一标志，不另画字母。默认头像为蓝色插画，深色模式保留原色，不做反相。生成提示词、素材预览与浏览器检查记录见 [`docs/evidence/brand-refresh-2026-10-31/`](../docs/evidence/brand-refresh-2026-10-31/)。

## e2e

**生产验收独立运行**：`scripts/production-smoke.ps1` 在专用 Compose 项目中创建临时数据库、生成可播放媒体和 localhost 测试证书；用 `playwright.production.config.ts` 验证生产镜像经过 HTTPS nginx 的行为。`PRODUCTION_REGRESSION=1` 复用观看页与移动端回归，`PLAYWRIGHT_BASE_URL` 要与 `PRODUCTION_SMOKE_URL` 同设为该本机地址（旧测试 helper 读取前者）。结束后用脚本的 `-Stop` 清理专用容器与测试卷。该配置拒绝远程主机，不能用于向线上账户写入测试数据。常规 e2e 仍用下面的开发环境配置；两种方式都要保留，因为开发代理不会覆盖生产响应头、媒体访问与静态资源问题。

**公开配置在构建时固定**：Docker 的 `NEXT_PUBLIC_*` 构建参数负责站点地址和已有公示信息；修改 Compose 运行时变量不会改变已构建的浏览器包。API 与媒体继续同源。会员收费链路已整体下线（无购买入口、无价格配置），公示字段为空时不补占位文字。

Windows 的生产验收把参考词典原样复制到专用 Linux 卷再只读挂载：SQLite 通过 Windows bind mount 随机读的开销会制造搜索冷启动假故障（同一词典实测约 31 秒，本地卷约 0.3 秒）。保持词典内容一致，通过文件系统匹配生产环境，不增加测试等待时间或跳过搜索断言。

[`playwright.config.ts`](playwright.config.ts)：`testDir: ./e2e`，baseURL 取 `PLAYWRIGHT_BASE_URL` 否则 `http://localhost:3000`，四个 project：`chromium` / `firefox` / `mobile-chrome` / `mobile-iphone`。非 CI 环境下有 `webServer` 会自动拉起 backend（uvicorn :8000）+ `npm run dev`。

**CI 的 PR 只跑 `--project=chromium`（Firefox/WebKit 在夜间工作流 `.github/workflows/cross-browser.yml` + `playwright.crossbrowser.config.ts` 里跑），并且必须先把库迁到 head 再 `python scripts/seed_e2e.py` 播种**——否则首页没有视频，观看页那批 spec 会整片 `skip()`（看着绿，其实一条没跑）。

**本地跑全量 e2e 要用 testing 形态的后端**：`ENV=testing` 会把限流装饰器变成 no-op。用 dev 形态的后端起 e2e 时，并行 worker 撞上注册/登录 `20/minute` 会整片 `429`（看起来像认证坏了，实际一条业务请求都没进去）。所以后端要显式给 `ENV=testing` 与 `DATABASE_URL`（非 development 环境缺它会 fail closed、启动失败）；启动命令见 `/dev` skill，只换这两个环境变量。`playwright.config.ts` 自动拉起的 backend 已带 `--timeout-keep-alive 120`，手工起后端时不要省——原因写在该文件注释里。

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
