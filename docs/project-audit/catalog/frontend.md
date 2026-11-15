# 前端逐文件索引

本分册 496 项。每项来自实际文件、符号/表/路由和引用提取；关系未显示的其余项在 [完整机器清单](../inventory.json)。无 import 不等于无调用，动态入口/收集器/配置关系另列。

## `frontend`

### [frontend/.dockerignore](../../../frontend/.dockerignore)

该组件构建/版本化排除边界，防依赖、凭据和生成物误入制品。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/.env.example](../../../frontend/.env.example)

安全的环境变量模板，不是真实凭据；加载方为对应组件 Settings/启动脚本。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/.prettierignore](../../../frontend/.prettierignore)

格式化排除范围，不是测试跳过清单。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/.prettierrc](../../../frontend/.prettierrc)

前端格式化规则。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/AGENTS.md](../../../frontend/AGENTS.md)

Next 自动维护的框架版本提醒；不是可手工删掉的产品需求。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [frontend/CLAUDE.md](../../../frontend/CLAUDE.md)

前端命令、会话/代理、当前设计和 Next 自动规则的唯一说明。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：更新必要说明/引用或生成路径。

### [frontend/Dockerfile](../../../frontend/Dockerfile)

容器构建入口：前端开发环境；与同组件 Compose build 相连。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/Dockerfile.prod](../../../frontend/Dockerfile.prod)

容器构建入口：生产 standalone 前端；与同组件 Compose build 相连。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/components.json](../../../frontend/components.json)

组件生成工具的别名和样式接入配置，不是页面内容。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

## `frontend/e2e`

### [frontend/e2e/astryx-vocabulary.spec.ts](../../../frontend/e2e/astryx-vocabulary.spec.ts)

Playwright 真实浏览器回归：Astryx 词汇试点的筛选/搜索/分页/键盘与主题。断言主题：Astryx 词汇控件保留搜索、筛选、分页与 URL 恢复；跨页词汇入口使用链接，方向键不触发路由跳转；Astryx 词汇控件保留搜索、筛选、分页与 URL 恢复。

- 代码入口/类型：`libraryUrl`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/auth-hydration.spec.ts](../../../frontend/e2e/auth-hydration.spec.ts)

Playwright 真实浏览器回归：持久会话恢复与页面水合。断言主题：找回密码慢加载时填写的号码仍能启用发送按钮；找回密码慢加载时填写的号码仍能启用发送按钮。

- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/auth.spec.ts](../../../frontend/e2e/auth.spec.ts)

Playwright 真实浏览器回归：短信/密码登录注册及退出。断言主题：Registration；full registration flow: phone + 4-digit code + set password, then redirect；new user can skip the set-password step and continue。

- 代码入口/类型：`SHARED_PHONE`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/avatar.spec.ts](../../../frontend/e2e/avatar.spec.ts)

Playwright 真实浏览器回归：头像上传/默认图和主题显示。断言主题：改性别后顶栏头像立即跟随，无需刷新；改性别后顶栏头像立即跟随，无需刷新。

- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/command-palette.spec.ts](../../../frontend/e2e/command-palette.spec.ts)

Playwright 真实浏览器回归：全局搜索弹层和键盘导航。断言主题：空查询显示跳转命令，键盘可跳转，Escape 回焦；输入关键词后展示四组搜索结果与结果数；390 视口下面板不横向溢出。

- 代码入口/类型：`token`、`MOCK_RESULTS`、`openWithButton`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/container-align.spec.ts](../../../frontend/e2e/container-align.spec.ts)

Playwright 真实浏览器回归：壳层容器、标题与内容对齐。通过测试定义中的实际页面/请求验证行为。

- 代码入口/类型：`mintToken`、`BAR_CONTAINER`、`PAGE_CONTAINER`、`CONTAINER_MAX`、`VIEWPORTS`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/design-rollout.spec.ts](../../../frontend/e2e/design-rollout.spec.ts)

Playwright 真实浏览器回归：公共页面布局与设计不变量。断言主题：账号读取暂时失败显示重试状态，保留当前页面；导航按断点切换，观看页归属首页；自建词单管理刷新后保留，删除不删除生词。

- 代码入口/类型：`token`、`videoId`、`lastStarted`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/discover-layout.spec.ts](../../../frontend/e2e/discover-layout.spec.ts)

Playwright 真实浏览器回归：发现页筛选和多尺寸布局。通过测试定义中的实际页面/请求验证行为。

- 代码入口/类型：`videos`、`setupDiscovery`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)、[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [frontend/e2e/exam.spec.ts](../../../frontend/e2e/exam.spec.ts)

Playwright 真实浏览器回归：试卷作答、交卷与结果。断言主题：Exam Runner - full answer journey；every question has clickable options; submit lands on the result page；Exam Runner - full answer journey。

- 代码入口/类型：`PaperSummary`、`firstPaperId`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

## `frontend/e2e/fixtures`

### [frontend/e2e/fixtures/README.md](../../../frontend/e2e/fixtures/README.md)

该组件必要运行/契约说明；操作条件与限制就近维护，不是历史方案。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [frontend/e2e/fixtures/exam-reading.json](../../../frontend/e2e/fixtures/exam-reading.json)

词汇/考试移动回归 import 的固定阅读题面和选项，避免依赖可变线上题库。

- 直接使用者：[frontend/e2e/vocabulary-exam-presentation.mobile.spec.ts](../../../frontend/e2e/vocabulary-exam-presentation.mobile.spec.ts)。
- 处置：保留。

### [frontend/e2e/fixtures/watch-clock.mp4](../../../frontend/e2e/fixtures/watch-clock.mp4)

自产 20 秒黑场提示音测试媒体，供解码/定位/倍速，不证明学习效果。

- 配置/资源消费者：[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 处置：保留。

## `frontend/e2e`

### [frontend/e2e/grid-columns.spec.ts](../../../frontend/e2e/grid-columns.spec.ts)

Playwright 真实浏览器回归：视频网格列数和断点。断言主题：网格列数自适应（S6）；网格列数自适应（S6）。

- 代码入口/类型：`GRID_SELECTOR`、`readTracks`、`VIEWPORTS`、`token`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)

真实 e2e 的测试账号、会话、数据和 API 交互辅助。

- 代码入口/类型：`DEV_SMS_CODE`、`fillSmsOtp`、`TEST_PASSWORD`、`chooseSelectMenu`、`phoneCounter`、`workerSalt`、`workerBase`、`uniquePhone`、`registerUserViaApi`、`registerViaUi`（其余见机器清单）。
- 直接使用者：[frontend/e2e/astryx-vocabulary.spec.ts](../../../frontend/e2e/astryx-vocabulary.spec.ts)、[frontend/e2e/auth.spec.ts](../../../frontend/e2e/auth.spec.ts)、[frontend/e2e/avatar.spec.ts](../../../frontend/e2e/avatar.spec.ts)、[frontend/e2e/command-palette.spec.ts](../../../frontend/e2e/command-palette.spec.ts)、[frontend/e2e/design-rollout.spec.ts](../../../frontend/e2e/design-rollout.spec.ts)、[frontend/e2e/discover-layout.spec.ts](../../../frontend/e2e/discover-layout.spec.ts)；其余 27 项见机器清单。
- 处置：保留。

### [frontend/e2e/home-continue-learning.spec.ts](../../../frontend/e2e/home-continue-learning.spec.ts)

Playwright 真实浏览器回归：首页继续观看入口和恢复。断言主题：首页续看入口；只展示最近一条有效续看记录，恢复真实时间；没有可继续记录时直接展示精选，不留空的续看条。

- 代码入口/类型：`mintToken`、`MockRecord`、`recordJson`、`IN_PROGRESS`、`RECOMMENDATION`、`FEATURED`、`METADATA`、`mockHome`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/home-editorial-full-loop.spec.ts](../../../frontend/e2e/home-editorial-full-loop.spec.ts)

Playwright 真实浏览器回归：真实 API 的首页草稿→预览→发布→撤回/回退闭环。断言主题：1/12 基线：未发布编排时公共接口为空，首页走旧兜底显示 A；2/12 管理员为 A 制作并发布主推，并在编排页摆好换说法/场景卡（回滚目标）；3/12 管理员详情页：B 草稿（真实 AI 结果或手写兜底）改标题与选项反馈，预览。

- 代码入口/类型：`BASE_URL`、`EVIDENCE_DIR`、`ADMIN_PHONE`、`ADMIN_PASSWORD`、`VIDEO_IDS`、`A`、`B`、`C`、`D`、`A_HEADLINE`（其余见机器清单）。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [frontend/e2e/home-editorial.spec.ts](../../../frontend/e2e/home-editorial.spec.ts)

Playwright 真实浏览器回归：首页发布内容的显示与失败兜底。断言主题：已发布编排：完整视频发现；双语标题保留，辅助导语移除，完整视频入口保留；编辑标题不替换视频原名，不展示辅助导语。

- 代码入口/类型：`BASE_URL`、`COVER_SVG`、`mintToken`、`videoCard`、`LEAD_SENTENCE`、`TELL_SENTENCE`、`SPOT_EXPRESSION`、`TELL_EXPRESSION`、`LEAD_CONTENT`、`LEAD_SLOT`（其余见机器清单）。
- 直接依赖：[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/home-feed.spec.ts](../../../frontend/e2e/home-feed.spec.ts)

Playwright 真实浏览器回归：首页视频流筛选、排序和旧链接。断言主题：首页下滑流 · 筛选；收藏最多 / 本周收藏 写进 URL 且带进 /browse/feed 请求；分类与难度写进 URL 并带进请求；筛选时不再提供「推荐」排序。

- 代码入口/类型：`token`、`openHome`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [frontend/e2e/home-learning-stories.spec.ts](../../../frontend/e2e/home-learning-stories.spec.ts)

Playwright 真实浏览器回归：首页学习内容/元信息与观看衔接。断言主题：普通精选不请求字幕预览或媒体，不展示学习任务；媒体不可试听仍可进入完整视频；普通精选不请求字幕预览或媒体，不展示学习任务。

- 代码入口/类型：`previewAudio`、`mockStories`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/library-persistence.spec.ts](../../../frontend/e2e/library-persistence.spec.ts)

Playwright 真实浏览器回归：收藏/订阅/笔记跨刷新持久化。断言主题：真实收藏与订阅在观看、频道和收藏页保持一致；真实收藏与订阅在观看、频道和收藏页保持一致。

- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/listening.spec.ts](../../../frontend/e2e/listening.spec.ts)

Playwright 真实浏览器回归：听力选材、草稿、提交与重放。断言主题：真实原声：调速、片段控制、草稿续做、提交解析与重练；音频失败可重试、素材为空有明确状态；真实原声：调速、片段控制、草稿续做、提交解析与重练。

- 代码入口/类型：`createAttempt`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/login-redirect-loop.spec.ts](../../../frontend/e2e/login-redirect-loop.spec.ts)

Playwright 真实浏览器回归：会话 cookie 镜像错位导致的登录循环。断言主题：login wall cookie mirror (stuck spinner regression)；镜像缺失 → 渲染恢复卡，且不再发出注定被弹回的跳转；镜像存在 + 导航慢 → spinner 持续，不出恢复卡。

- 代码入口/类型：`makeToken`、`isRscNavToHome`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/login-white-screen.spec.ts](../../../frontend/e2e/login-white-screen.spec.ts)

Playwright 真实浏览器回归：登录页加载/恢复与白屏防回归。断言主题：login transition (white screen regression)；spinner stays visible while post-login navigation is in flight；login transition (white screen regression)。

- 代码入口/类型：`PHONE`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/mobile-current-sentence-card.spec.ts](../../../frontend/e2e/mobile-current-sentence-card.spec.ts)

Playwright 真实浏览器回归：手机当前句卡、点词和操作可达性。断言主题：当前句卡（414×896 移动端）；卡在画面正下方、在文稿之前，且与画面同宽（不浮在画面里）；长句：英文夹两行、出现展开开关；展开读到完整英文、点它不切播放。

- 代码入口/类型：`SubtitleRow`、`FRAME`、`CARD`、`WORD`、`SHEET`、`token`、`openFirstReadyVideo`、`enterWatch`、`getSubtitles`、`firstWordText`（其余见机器清单）。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [frontend/e2e/mobile-d1-d10.spec.ts](../../../frontend/e2e/mobile-d1-d10.spec.ts)

Playwright 真实浏览器回归：手机观看主流程的多项交互。断言主题：Mobile D1 + D10 Acceptance (iPhone X 375x812)；watch page: 新壳两栏在位、无溢出、进页面即可播（底栏播放键）；D1: 播放中闲置 4s 后底栏常驻可点（不再有 3s 自收）。

- 代码入口/类型：`SCREENSHOT_DIR`、`TOP_BAR`、`BOTTOM_BAR`、`FRAME`、`CARD`、`PHONE`、`token`、`openFirstReadyVideo`、`assertNoHorizontalOverflow`、`enterWatch`（其余见机器清单）。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [frontend/e2e/mobile-inline-subtitle.spec.ts](../../../frontend/e2e/mobile-inline-subtitle.spec.ts)

Playwright 真实浏览器回归：手机行内字幕和词提示。断言主题：移动端当前句卡（#31，375×812）；进入页面即内联播放器：375 首屏不收成跟随态；画面内零文字，当前句卡贴画面正下方；向下滚动把画框滚出视口顶部 → 仍进跟随态（贴顶常驻，钉在 44px 顶栏下沿）。

- 代码入口/类型：`token`、`FRAME`、`CARD`、`openFirstReadyVideo`、`boxOf`、`enterWatch`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/mobile-pip-scroll.spec.ts](../../../frontend/e2e/mobile-pip-scroll.spec.ts)

Playwright 真实浏览器回归：手机滚动时播放器画中画。断言主题：移动端滚动形态：画面贴顶常驻（#30 + #31，375×812）；首屏不受影响：画框顶 = 壳顶 = 顶栏下沿、不常驻；当前句卡在画面正下方且词可点；滚过画框 → 画面贴顶常驻：画框顶 = 壳顶 = 顶栏下沿(44)、尺寸一像素没缩、画面里仍零文字。

- 代码入口/类型：`token`、`FRAME`、`CARD`、`boxOf`、`scrollTo`、`enterWatch`、`frameState`、`shellEdges`、`wordHitBand`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [frontend/e2e/mobile-player-shell.spec.ts](../../../frontend/e2e/mobile-player-shell.spec.ts)

Playwright 真实浏览器回归：手机播放器与页面壳配合。断言主题：用户端观看布局；首访直接观看，词卡可点开且不盖住五项导航；内容区返回键可点，回到原页面。

- 代码入口/类型：`token`、`FRAME`、`TOP_BAR`、`CARD`、`boxOf`、`openWatch`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/mobile-sentence-nav.spec.ts](../../../frontend/e2e/mobile-sentence-nav.spec.ts)

Playwright 真实浏览器回归：手机上一句/下一句导航。断言主题：句导航（真媒体，414×896）；用例 A：「下一句」连点 3 次只前进、不回退；用例 B：「上一句」连点 2 次只后退。

- 代码入口/类型：`navigationCues`、`COUNTER`、`PREV`、`NEXT`、`PROGRESS`、`BOTTOM_KEYS`、`CLICK_SETTLE_MS`、`tapByDispatch`、`counterValue`、`enterWatch`（其余见机器清单）。
- 直接依赖：[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/mobile-transcript-scroll.spec.ts](../../../frontend/e2e/mobile-transcript-scroll.spec.ts)

Playwright 真实浏览器回归：手机整篇字幕滚动和当前句跟随。断言主题：移动端文稿滚动模型（414×896）；文稿容器没有自己的滚动条，页面只有 main 一层滚动；滚过画框后画框贴顶常驻，并带一条下边线。

- 代码入口/类型：`FRAME`、`CARD`、`LIST`、`BAR`、`SCROLLER`、`SubtitleRow`、`token`、`openFirstReadyVideo`、`enterWatch`、`getSubtitles`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [frontend/e2e/mobile-watch-chrome.spec.ts](../../../frontend/e2e/mobile-watch-chrome.spec.ts)

Playwright 真实浏览器回归：手机常驻观看控制条。断言主题：判据（414×896）：零文字画面 / 完整首屏 / 1 次点击（DEC-069 / #31）；判据 1：video-frame 内无任何文字；全站底栏完整可见，页面内播放操作和完整当前句可滚动到达。

- 代码入口/类型：`token`、`FRAME`、`CARD`、`BAR`、`TOP_BAR`、`enterWatch`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/mobile-wordcard-drawer.spec.ts](../../../frontend/e2e/mobile-wordcard-drawer.spec.ts)

Playwright 真实浏览器回归：手机词卡抽屉和底栏避让。断言主题：加入词库保留词卡，短拉回弹、长拉关闭；观看页不再提供录音或跟读抽屉；桌面端。

- 代码入口/类型：`PHONE`、`token`、`FRAME`、`CARD`、`WORD_SHEET`、`openFirstReadyVideo`、`boxOf`、`enterWatch`、`tapWord`、`assertSheetAboveNavigation`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/mobile.spec.ts](../../../frontend/e2e/mobile.spec.ts)

Playwright 真实浏览器回归：手机主页面适配。断言主题：Mobile - Login Wall；login page renders without horizontal overflow；login form inputs are visible on mobile。

- 代码入口/类型：`MOBILE_PHONE`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

## `frontend/e2e/production`

### [frontend/e2e/production/readiness.spec.ts](../../../frontend/e2e/production/readiness.spec.ts)

Playwright 真实浏览器回归：本文件所列页面/媒体/身份的交互与状态边界。断言主题：生产资源、公开元数据与 HTTPS 策略；用户页面三档视口与亮暗主题布局；生产视频拖动、录音回放与通知连接。

- 代码入口/类型：`token`、`videoId`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/production/recovery.spec.ts](../../../frontend/e2e/production/recovery.spec.ts)

Playwright 真实浏览器回归：本文件所列页面/媒体/身份的交互与状态边界。断言主题：学习记录断网可重试，不能当作新用户；帮助页请求失败显示恢复入口；学习记录断网可重试，不能当作新用户。

- 代码入口/类型：`token`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/production/seed.py](../../../frontend/e2e/production/seed.py)

仅在独立 smoke 测试库补 16 句字幕并用 ffmpeg 生成可播放合成媒体；有 ENV/数据库地址守卫，会写专用库。

- 代码入口/类型：`main`。
- 直接依赖：[backend/app/core/config.py](../../../backend/app/core/config.py)、[backend/app/core/database.py](../../../backend/app/core/database.py)、[backend/app/core/redis.py](../../../backend/app/core/redis.py)、[backend/app/models/subtitle.py](../../../backend/app/models/subtitle.py)、[backend/app/models/video.py](../../../backend/app/models/video.py)。
- 处置：保留。

## `frontend/e2e`

### [frontend/e2e/public-layout.spec.ts](../../../frontend/e2e/public-layout.spec.ts)

Playwright 真实浏览器回归：公开页面布局和登录墙边界。断言主题：账号、协议及未找到页面在三档视口与亮暗主题下可读；首次引导各步骤和设置密码支持三档视口与亮暗主题；账号、协议及未找到页面在三档视口与亮暗主题下可读。

- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/repro-stage1.spec.ts](../../../frontend/e2e/repro-stage1.spec.ts)

Playwright 真实浏览器回归：已知观看/滚动问题的可重复回归。断言主题：Stage1 - watch page layout (A2/A4/A5)；desktop: renders subtitle panel + current subtitle card, no errors；desktop: word card defaults to bottom-LEFT when panel expanded。

- 代码入口/类型：`PHONE`、`openFirstWatch`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/transcript-document.spec.ts](../../../frontend/e2e/transcript-document.spec.ts)

Playwright 真实浏览器回归：整篇文稿的词锚点与定位。断言主题：全文文稿页；整段字幕按段落排成文档，考试词点回播放器；译文可以一键隐藏。

- 代码入口/类型：`mintToken`、`subtitle`、`VIDEO`、`mockTranscript`。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/ui-review-fixes-mobile.spec.ts](../../../frontend/e2e/ui-review-fixes-mobile.spec.ts)

Playwright 真实浏览器回归：手机触控/遮挡修复回归。断言主题：复习总量、预览与训练分开说明，词性归一化与来源链接一致；主按钮明暗主题默认与悬停文字对比度至少 4.5；更多设置模态焦点进入、约束、Escape 与把手键盘关闭。

- 代码入口/类型：`reachable`。
- 直接依赖：[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/user-information.spec.ts](../../../frontend/e2e/user-information.spec.ts)

Playwright 真实浏览器回归：真实个人资料/统计的展示和空状态。断言主题：我的默认展示学习资产与账户卡，五个一级导航和旧设置链接可用；搜索先给视频和频道，双语标题及简介与完整视频入口一致；频道视频用已有简介解释内容，不展示字幕与考试词计数。

- 代码入口/类型：`VIDEO`、`mockContent`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)、[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/video.spec.ts](../../../frontend/e2e/video.spec.ts)

Playwright 真实浏览器回归：视频列表/详情和访问行为。断言主题：Home Page；unauthenticated visit redirects to the login wall；home page loads within 5 seconds。

- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/viewport-height.spec.ts](../../../frontend/e2e/viewport-height.spec.ts)

Playwright 真实浏览器回归：短/高视口的观看区域可达性。断言主题：Viewport height - app shell；shell fills the visible viewport and the document does not scroll；bottom tab bar is the shell's last in-flow row, not a fixed overlay。

- 代码入口/类型：`PHONE`、`token`、`shellMetrics`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/vocabulary-exam-presentation.mobile.spec.ts](../../../frontend/e2e/vocabulary-exam-presentation.mobile.spec.ts)

Playwright 真实浏览器回归：手机词汇/考试内容密度与作答显示。断言主题：题组作答、滚动、缩放、提交失败重试和错题回顾；词汇真实队列、分组预览和直接开始；词汇失败不会伪装成空词库或完成。

- 代码入口/类型：`passage`、`matchingPassage`、`questions`、`wordNames`、`meanings`、`words`、`preferences`、`setup`、`jump`。
- 直接依赖：[frontend/e2e/fixtures/exam-reading.json](../../../frontend/e2e/fixtures/exam-reading.json)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/vocabulary-learning.spec.ts](../../../frontend/e2e/vocabulary-learning.spec.ts)

Playwright 真实浏览器回归：收词、训练、自评与来源回看。断言主题：考试词库分批加入、筛词断点和掌握进度持久化，移出保留学习记录；考试词库分批加入、筛词断点和掌握进度持久化，移出保留学习记录。

- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/watch-baseline-mobile.spec.ts](../../../frontend/e2e/watch-baseline-mobile.spec.ts)

Playwright 真实浏览器回归：合成媒体的跨浏览器手机观看基线。断言主题：当前句同词来源正确，关闭恢复播放，原本暂停则不播放；减少辅助只影响本次，重听到句末停，文稿行连续播放；重听期间求助关闭后保留句末边界，新定位取消旧边界。

- 代码入口/类型：`reduceAidReplay`。
- 直接依赖：[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)

合成观看测试数据及独立 HTTP Range 媒体服务，覆盖 WebKit 请求差异。

- 代码入口/类型：`VIDEO_ID`、`subtitles`、`clockMedia`、`setupWatch`、`openWatch`、`mediaState`、`installYoutubeClock`、`clickReplay`、`clickLearningAction`。
- 直接使用者：[frontend/e2e/discover-layout.spec.ts](../../../frontend/e2e/discover-layout.spec.ts)、[frontend/e2e/mobile-sentence-nav.spec.ts](../../../frontend/e2e/mobile-sentence-nav.spec.ts)、[frontend/e2e/ui-review-fixes-mobile.spec.ts](../../../frontend/e2e/ui-review-fixes-mobile.spec.ts)、[frontend/e2e/user-information.spec.ts](../../../frontend/e2e/user-information.spec.ts)、[frontend/e2e/watch-baseline-mobile.spec.ts](../../../frontend/e2e/watch-baseline-mobile.spec.ts)、[frontend/e2e/watch-desktop-stage.spec.ts](../../../frontend/e2e/watch-desktop-stage.spec.ts)；其余 3 项见机器清单。
- 处置：保留。

### [frontend/e2e/watch-desktop-stage.spec.ts](../../../frontend/e2e/watch-desktop-stage.spec.ts)

Playwright 真实浏览器回归：桌面播放器画框、分栏和尺寸不变量。断言主题：watch-stage.png；watch-stage.png。

- 直接依赖：[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/watch-end-screen.spec.ts](../../../frontend/e2e/watch-end-screen.spec.ts)

Playwright 真实浏览器回归：视频结束后的可用动作。通过测试定义中的实际页面/请求验证行为。

- 代码入口/类型：`token`、`enterEndedWatch`、`VIEWPORTS`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/watch-immersive.mobile.spec.ts](../../../frontend/e2e/watch-immersive.mobile.spec.ts)

Playwright 真实浏览器回归：手机/桌面沉浸观看进退和状态恢复。断言主题：A/R/D 与按钮共用逐句语义，输入、组合键与弹层不误触；播放中切换沉浸、导航离开和重访不重置媒体或残留沉浸；YouTube 回退与横屏沉浸可退出。

- 代码入口/类型：`evidence`、`noOverflow`。
- 直接依赖：[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：更新必要说明/引用或生成路径。

### [frontend/e2e/watch-layout.mobile.spec.ts](../../../frontend/e2e/watch-layout.mobile.spec.ts)

Playwright 真实浏览器回归：多视口下播放器/字幕/词卡布局。断言主题：桌面拖动、键盘边界、沉浸与复位保留媒体和偏好；字幕、字号与笔记不再缩小视频，窗口不足时上下排布；播放中跨桌面、上下布局和手机切换，媒体节点与进度连续。

- 代码入口/类型：`noOverflow`。
- 直接依赖：[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/watch-return.spec.ts](../../../frontend/e2e/watch-return.spec.ts)

Playwright 真实浏览器回归：从观看页回来源列表与状态恢复。断言主题：Watch Page - Return to source；首页筛选在往返中保留，返回不会落回 /watch；Watch Page - Return to source。

- 代码入口/类型：`hasVideo`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/e2e/watch.spec.ts](../../../frontend/e2e/watch.spec.ts)

Playwright 真实浏览器回归：真实 API 的播放、点词与学习行为。断言主题：Watch Page - Error States；invalid video ID shows an error state, not a white screen；Watch Page - Valid Video。

- 代码入口/类型：`openFirstVideo`。
- 直接依赖：[frontend/e2e/helpers.ts](../../../frontend/e2e/helpers.ts)、[frontend/e2e/watch-baseline.fixture.ts](../../../frontend/e2e/watch-baseline.fixture.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

## `frontend`

### [frontend/eslint.config.mjs](../../../frontend/eslint.config.mjs)

ESLint 与 React Hooks/TS 静态规则，不放宽来掩盖问题。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/next.config.js](../../../frontend/next.config.js)

Next standalone、开发代理、图源/图片策略和构建优化。

- 代码入口/类型：`nextConfig`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/package-lock.json](../../../frontend/package-lock.json)

npm 完整解析结果，ci 安装和许可核对的版本依据。

- 配置/资源消费者：[frontend/Dockerfile](../../../frontend/Dockerfile)、[frontend/Dockerfile.prod](../../../frontend/Dockerfile.prod)、[.github/workflows/ci.yml](../../../.github/workflows/ci.yml)。
- 处置：保留。

### [frontend/package.json](../../../frontend/package.json)

npm 命令、直接依赖和检查链定义。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [frontend/playwright.config.ts](../../../frontend/playwright.config.ts)

日常浏览器回归项目、baseURL、并发与本地 webServer。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/playwright.crossbrowser.config.ts](../../../frontend/playwright.crossbrowser.config.ts)

夜间 Firefox/WebKit 的独立测试装配。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/playwright.production.config.ts](../../../frontend/playwright.production.config.ts)

本机 HTTPS nginx 生产镜像回归，拒绝远程目标。

- 代码入口/类型：`baseURL`。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/postcss.config.js](../../../frontend/postcss.config.js)

Tailwind v4 的 PostCSS 构建入口。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `frontend/public`

### [frontend/public/default-avatar-female.webp](../../../frontend/public/default-avatar-female.webp)

品牌/默认头像二进制素材：default-avatar-female.webp；按 public URL 或组件资源入口读取，不是历史文档截图。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/public/default-avatar-male.webp](../../../frontend/public/default-avatar-male.webp)

品牌/默认头像二进制素材：default-avatar-male.webp；按 public URL 或组件资源入口读取，不是历史文档截图。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/public/logo-large.png](../../../frontend/public/logo-large.png)

品牌/默认头像二进制素材：logo-large.png；按 public URL 或组件资源入口读取，不是历史文档截图。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/public/logo.png](../../../frontend/public/logo.png)

品牌/默认头像二进制素材：logo.png；按 public URL 或组件资源入口读取，不是历史文档截图。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/public/og-image.png](../../../frontend/public/og-image.png)

品牌/默认头像二进制素材：og-image.png；按 public URL 或组件资源入口读取，不是历史文档截图。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/public/project-icon.svg](../../../frontend/public/project-icon.svg)

品牌项目图标，按公开资源 URL 被导航/壳和浏览器使用，不是文档截图。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `frontend/scripts`

### [frontend/scripts/audit-touch-targets.mjs](../../../frontend/scripts/audit-touch-targets.mjs)

扫描现有页面触控目标的可选浏览器量具；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`HERE`、`FRONTEND`、`REPO`、`argv`、`arg`、`has`、`BASE_URL`、`OUT`、`EMIT_MD`、`SETTLE_MS`（其余见机器清单）。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：更新必要说明/引用或生成路径。

### [frontend/scripts/check-design-system.mjs](../../../frontend/scripts/check-design-system.mjs)

机器执行的语义色/容器/h1/圆角等设计不变量；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`HERE`、`FRONTEND`、`REPO`、`posix`、`rel`、`SKIP_DIRS`、`walk`、`SRC`、`allSrc`、`isTs`（其余见机器清单）。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/scripts/check-session-writes.mjs](../../../frontend/scripts/check-session-writes.mjs)

阻止 authHelpers 之外写会话 cookie/localStorage；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`HERE`、`FRONTEND`、`REPO`、`posix`、`rel`、`SKIP_DIRS`、`walk`、`SRC`、`ALLOWED`、`SESSION_KEY`（其余见机器清单）。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/scripts/design-shots.mjs](../../../frontend/scripts/design-shots.mjs)

可选实际浏览器截图量具，生成物留本地 tmp；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 代码入口/类型：`HERE`、`OUT`、`BASE`、`API`、`TAG`、`ROUTE_ARG`、`ROUTES`、`VIEWPORTS`、`loginToken`、`token`（其余见机器清单）。
- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：更新必要说明/引用或生成路径。

### [frontend/scripts/production-smoke.ps1](../../../frontend/scripts/production-smoke.ps1)

创建本机独立生产镜像/HTTPS 测试栈并驱动检查；运行入口/参数由脚本 main/argparse/命令定义，独立于 Web 请求。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/channels`

### [frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)

网址 /admin/channels 的频道管理页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`FormState`、`EMPTY_FORM`、`AdminChannelsPage`。
- 直接依赖：[frontend/src/components/admin/ui/AdminEmptyState.tsx](../../../frontend/src/components/admin/ui/AdminEmptyState.tsx)、[frontend/src/components/admin/ui/AdminPageHeader.tsx](../../../frontend/src/components/admin/ui/AdminPageHeader.tsx)、[frontend/src/components/admin/ui/AdminSearchInput.tsx](../../../frontend/src/components/admin/ui/AdminSearchInput.tsx)、[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 7 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/feedback`

### [frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)

网址 /admin/feedback 的反馈管理页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`PAGE_SIZE`、`STATUS_TABS`、`STATUS_BADGE`、`AdminFeedbackPage`。
- 直接依赖：[frontend/src/components/admin/Pagination.tsx](../../../frontend/src/components/admin/Pagination.tsx)、[frontend/src/components/admin/ui/AdminPageHeader.tsx](../../../frontend/src/components/admin/ui/AdminPageHeader.tsx)、[frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)、[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 6 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/home-editorial`

### [frontend/src/app/(admin)/admin/(shell)/home-editorial/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/home-editorial/page.tsx)

网址 /admin/home-editorial 的首页编排管理页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`HomeEditorialPage`。
- 直接依赖：[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)`

### [frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)

/admin 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`ShellStatus`、`AdminShellLayout`。
- 直接依赖：[frontend/src/components/admin/AdminSidebar.tsx](../../../frontend/src/components/admin/AdminSidebar.tsx)、[frontend/src/components/admin/AdminTopbar.tsx](../../../frontend/src/components/admin/AdminTopbar.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/adminApi.ts](../../../frontend/src/lib/adminApi.ts)、[frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)；其余 2 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/lessons`

### [frontend/src/app/(admin)/admin/(shell)/lessons/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/lessons/page.tsx)

网址 /admin/lessons 的课程发布管理页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`AdminLessonsPage`。
- 直接依赖：[frontend/src/components/lessons/LessonAdmin.tsx](../../../frontend/src/components/lessons/LessonAdmin.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)`

### [frontend/src/app/(admin)/admin/(shell)/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/page.tsx)

网址 /admin 的管理概览页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`GrowthTrendChart`、`UgcPending`、`KpiCard`、`StatusBadge`、`AdminDashboardPage`。
- 直接依赖：[frontend/src/components/admin/GrowthTrendChart.tsx](../../../frontend/src/components/admin/GrowthTrendChart.tsx)、[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)；其余 1 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/settings`

### [frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)

网址 /admin/settings 的系统设置页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`FieldIds`、`fieldIds`、`IDS`、`STORED_ONLY_NOTE`、`ratioToPercentText`、`parsePercentText`、`isPercentInRange`、`settingsErrorMessage`、`Toggle`、`Row`（其余见机器清单）。
- 直接依赖：[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)；其余 3 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/stats`

### [frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)

网址 /admin/stats 的后台学习/运营统计页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`StatsTrendChart`、`StatsStatusBarChart`、`STATUS_LABEL`、`TOPIC_COLORS`、`ACTIVITY_ICON`、`KpiCard`、`ChartCard`、`pct`、`msText`、`MetricRow`（其余见机器清单）。
- 直接依赖：[frontend/src/components/admin/StatsCharts.tsx](../../../frontend/src/components/admin/StatsCharts.tsx)、[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/lib/chart-theme.ts](../../../frontend/src/lib/chart-theme.ts)；其余 4 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/users`

### [frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)

网址 /admin/users 的用户管理页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`ROLE_FILTERS`、`PAGE_SIZE`、`RowAction`、`filterSummary`、`AdminUsersPage`、`UserRow`、`DetailStat`。
- 直接依赖：[frontend/src/components/admin/FilterPills.tsx](../../../frontend/src/components/admin/FilterPills.tsx)、[frontend/src/components/admin/Pagination.tsx](../../../frontend/src/components/admin/Pagination.tsx)、[frontend/src/components/admin/StatChip.tsx](../../../frontend/src/components/admin/StatChip.tsx)、[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)、[frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)、[frontend/src/components/ui/Avatar.tsx](../../../frontend/src/components/ui/Avatar.tsx)；其余 8 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/videos`

### [frontend/src/app/(admin)/admin/(shell)/videos/VideoDetailRow.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoDetailRow.tsx)

视频管理路由的局部 UI 编排；公开符号 DIFFICULTY_OPTIONS、youtubeId、DetailRowProps、VideoDetailRow。

- 代码入口/类型：`DIFFICULTY_OPTIONS`、`youtubeId`、`DetailRowProps`、`VideoDetailRow`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)、[frontend/src/hooks/useVideoPolling.ts](../../../frontend/src/hooks/useVideoPolling.ts)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)；其余 4 项见机器清单。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)。
- 处置：保留。

### [frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)

视频管理路由的局部 UI 编排；公开符号 PAGE_SIZE、STATUS_FILTERS、REVIEW_FILTERS、QUALITY_FILTERS、QUALITY_BADGE、REVIEW_BADGE。

- 代码入口/类型：`PAGE_SIZE`、`STATUS_FILTERS`、`REVIEW_FILTERS`、`QUALITY_FILTERS`、`QUALITY_BADGE`、`REVIEW_BADGE`、`VideoManager`。
- 直接依赖：[frontend/src/app/(admin)/admin/(shell)/videos/VideoDetailRow.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoDetailRow.tsx)、[frontend/src/components/admin/DataTable.tsx](../../../frontend/src/components/admin/DataTable.tsx)、[frontend/src/components/admin/FilterPills.tsx](../../../frontend/src/components/admin/FilterPills.tsx)、[frontend/src/components/admin/Pagination.tsx](../../../frontend/src/components/admin/Pagination.tsx)、[frontend/src/components/admin/SectionCard.tsx](../../../frontend/src/components/admin/SectionCard.tsx)、[frontend/src/components/admin/ui/AdminEmptyState.tsx](../../../frontend/src/components/admin/ui/AdminEmptyState.tsx)；其余 16 项见机器清单。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/page.tsx)。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/videos/[id]`

### [frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)

网址 /admin/videos/[id] 的视频详情/字幕维护页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`DIFFICULTY_OPTIONS`、`VideoEditPage`、`MetadataForm`。
- 直接依赖：[frontend/src/components/admin/QualityReportPanel.tsx](../../../frontend/src/components/admin/QualityReportPanel.tsx)、[frontend/src/components/admin/home/HomeContentPanel.tsx](../../../frontend/src/components/admin/home/HomeContentPanel.tsx)、[frontend/src/components/admin/ui/AdminPageHeader.tsx](../../../frontend/src/components/admin/ui/AdminPageHeader.tsx)、[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)；其余 7 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/(shell)/videos`

### [frontend/src/app/(admin)/admin/(shell)/videos/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/page.tsx)

网址 /admin/videos 的视频管理页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`AdminVideosPage`。
- 直接依赖：[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(admin)/admin/login`

### [frontend/src/app/(admin)/admin/login/page.tsx](../../../frontend/src/app/%28admin%29/admin/login/page.tsx)

网址 /admin/login 的管理员登录页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`LoginResponse`、`resolveAdminNext`、`currentAdminNext`、`LOGIN_ERROR_ID`、`PHONE_INPUT_ID`、`PASSWORD_INPUT_ID`、`AdminLoginPage`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/adminApi.ts](../../../frontend/src/lib/adminApi.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/stores/adminAuthStore.ts](../../../frontend/src/stores/adminAuthStore.ts)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)`

### [frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)

用户端共享壳：会话/引导门、桌面与手机导航、唯一 main/页面容器及观看控制条接入。

- 代码入口/类型：`MainLayoutInner`、`MainLayoutContent`。
- 直接依赖：[frontend/src/components/common/ShellSkeleton.tsx](../../../frontend/src/components/common/ShellSkeleton.tsx)、[frontend/src/components/layout/MobileTabBar.tsx](../../../frontend/src/components/layout/MobileTabBar.tsx)、[frontend/src/components/layout/PublicTopBar.tsx](../../../frontend/src/components/layout/PublicTopBar.tsx)、[frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx)、[frontend/src/components/layout/SiteFooter.tsx](../../../frontend/src/components/layout/SiteFooter.tsx)、[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)；其余 8 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/layout.tsx](../../../frontend/src/app/%28main%29/layout.tsx)。
- 处置：保留。

## `frontend/src/app/(main)/browse`

### [frontend/src/app/(main)/browse/route.ts](../../../frontend/src/app/%28main%29/browse/route.ts)

/browse 的服务器路由响应；当前 browse 用于兼容跳转，不渲染页面组件。

- 代码入口/类型：`FEED_KEYS`、`GET`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/channels/[slug]`

### [frontend/src/app/(main)/channels/[slug]/layout.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/layout.tsx)

/channels/[slug] 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)

网址 /channels/[slug] 的频道发现页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`PAGE_SIZE`、`CEFR_ORDER`、`ChannelVideoCard`、`ChannelRecommendedStart`、`ChannelDetailResponse`、`idOf`、`deriveDifficultyRange`、`FactSeparator`、`ChannelDetailSkeleton`、`ChannelDetailPage`。
- 直接依赖：[frontend/src/components/channels/ChannelStartCard.tsx](../../../frontend/src/components/channels/ChannelStartCard.tsx)、[frontend/src/components/channels/ChannelSubscribeButton.tsx](../../../frontend/src/components/channels/ChannelSubscribeButton.tsx)、[frontend/src/components/channels/ChannelVideoRow.tsx](../../../frontend/src/components/channels/ChannelVideoRow.tsx)、[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)；其余 13 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/channels`

### [frontend/src/app/(main)/channels/layout.tsx](../../../frontend/src/app/%28main%29/channels/layout.tsx)

/channels 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)

网址 /channels 的频道发现页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`PAGE_SIZE`、`ChannelsResponse`、`SubscriptionStatus`、`DirectionOption`、`ChannelsPage`。
- 直接依赖：[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)、[frontend/src/components/channels/SubscribedChannels.tsx](../../../frontend/src/components/channels/SubscribedChannels.tsx)、[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 7 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/contact`

### [frontend/src/app/(main)/contact/layout.tsx](../../../frontend/src/app/%28main%29/contact/layout.tsx)

/contact 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)

网址 /contact 的联系与反馈页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`Announcement`、`Feedback`、`CATEGORIES`、`STATUS_LABEL`、`FaqItem`、`FAQ`、`ContactPage`。
- 直接依赖：[frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)；其余 6 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)`

### [frontend/src/app/(main)/error.tsx](../../../frontend/src/app/%28main%29/error.tsx)

/ 范围的 Next error 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`Error`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/favorites`

### [frontend/src/app/(main)/favorites/layout.tsx](../../../frontend/src/app/%28main%29/favorites/layout.tsx)

/favorites 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)

网址 /favorites 的个人收藏页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`SavedSentence`、`formatMonthDay`、`formatClock`、`GroupEmpty`、`FavoritesPage`。
- 直接依赖：[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/LoadMoreError.tsx](../../../frontend/src/components/common/LoadMoreError.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 13 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/history`

### [frontend/src/app/(main)/history/layout.tsx](../../../frontend/src/app/%28main%29/history/layout.tsx)

/history 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)

网址 /history 的观看历史页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`FilterKey`、`LatestAttempt`、`VocabStats`、`FILTER_TABS`、`dayBucket`、`formatRecordTime`、`formatClock`、`formatNotifyDate`、`weekDuration`、`HistoryPage`（其余见机器清单）。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/LoadMoreError.tsx](../../../frontend/src/components/common/LoadMoreError.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 19 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)`

### [frontend/src/app/(main)/layout.tsx](../../../frontend/src/app/%28main%29/layout.tsx)

/ 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`MainLayout`。
- 直接依赖：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/lessons/[lessonId]`

### [frontend/src/app/(main)/lessons/[lessonId]/page.tsx](../../../frontend/src/app/%28main%29/lessons/%5BlessonId%5D/page.tsx)

网址 /lessons/[lessonId] 的SLCS 课程页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`Query`、`LessonPage`。
- 直接依赖：[frontend/src/components/lessons/LessonReader.tsx](../../../frontend/src/components/lessons/LessonReader.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/lessons`

### [frontend/src/app/(main)/lessons/page.tsx](../../../frontend/src/app/%28main%29/lessons/page.tsx)

网址 /lessons 的SLCS 课程页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`LessonsPage`。
- 直接依赖：[frontend/src/components/lessons/LessonCatalog.tsx](../../../frontend/src/components/lessons/LessonCatalog.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)`

### [frontend/src/app/(main)/loading.tsx](../../../frontend/src/app/%28main%29/loading.tsx)

/ 范围的 Next loading 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`MainLoading`。
- 直接依赖：[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/not-found.tsx](../../../frontend/src/app/%28main%29/not-found.tsx)

/ 范围的 Next not-found 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`MainNotFound`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/notifications`

### [frontend/src/app/(main)/notifications/layout.tsx](../../../frontend/src/app/%28main%29/notifications/layout.tsx)

/notifications 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/notifications/page.tsx](../../../frontend/src/app/%28main%29/notifications/page.tsx)

网址 /notifications 的本人通知页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`Notification`、`TYPE_LABELS`、`formatNotifyTime`、`NotificationsPage`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/LoadMoreError.tsx](../../../frontend/src/components/common/LoadMoreError.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)；其余 7 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)`

### [frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)

网址 / 的首页与继续学习页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`EDITORIAL_TIMEOUT_MS`、`editorialRequest`、`editorialAbort`、`editorialReleaseTimer`、`loadHomeEditorial`、`releaseHomeEditorial`、`EditorialState`、`HomePage`、`EditorialSkeleton`、`FeedSkeleton`。
- 直接依赖：[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/components/home/DiscoverRail.tsx](../../../frontend/src/components/home/DiscoverRail.tsx)、[frontend/src/components/home/FeaturedListening.tsx](../../../frontend/src/components/home/FeaturedListening.tsx)、[frontend/src/components/home/HomeEditorialHero.tsx](../../../frontend/src/components/home/HomeEditorialHero.tsx)、[frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)、[frontend/src/components/home/HomeSubscribedChannels.tsx](../../../frontend/src/components/home/HomeSubscribedChannels.tsx)；其余 5 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice/daily`

### [frontend/src/app/(main)/practice/daily/layout.tsx](../../../frontend/src/app/%28main%29/practice/daily/layout.tsx)

/practice/daily 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/practice/daily/page.tsx](../../../frontend/src/app/%28main%29/practice/daily/page.tsx)

网址 /practice/daily 的每日检查页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`Recommendation`、`Attempt`、`PracticeSummary`、`WrongItem`、`TYPE_LABELS`、`LINK_OUTLINE`、`formatDate`、`suggestedMinutesFor`、`DailyCheckPage`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)；其余 1 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice/exams/[id]`

### [frontend/src/app/(main)/practice/exams/[id]/layout.tsx](../../../frontend/src/app/%28main%29/practice/exams/%5Bid%5D/layout.tsx)

/practice/exams/[id] 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/practice/exams/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/%5Bid%5D/page.tsx)

网址 /practice/exams/[id] 的真题试卷页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`PaperDetail`、`AttemptCreate`、`ExamPaperPage`、`ExamModePage`。
- 直接依赖：[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/components/teaching/TeachingWorkspace.tsx](../../../frontend/src/components/teaching/TeachingWorkspace.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/hooks/useRequireAuth.ts](../../../frontend/src/hooks/useRequireAuth.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)；其余 1 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice/exams`

### [frontend/src/app/(main)/practice/exams/layout.tsx](../../../frontend/src/app/%28main%29/practice/exams/layout.tsx)

/practice/exams 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 直接依赖：[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/practice/exams/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/page.tsx)

网址 /practice/exams 的真题试卷页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`PaperListItem`、`PaperList`、`ExamPdfItem`、`ExamPapersPage`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/hooks/useRequireAuth.ts](../../../frontend/src/hooks/useRequireAuth.ts)；其余 3 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice/exams/redo`

### [frontend/src/app/(main)/practice/exams/redo/layout.tsx](../../../frontend/src/app/%28main%29/practice/exams/redo/layout.tsx)

/practice/exams/redo 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/practice/exams/redo/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/redo/page.tsx)

网址 /practice/exams/redo 的错题重做页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`WrongRedoStart`、`WrongRedoPage`。
- 直接依赖：[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/hooks/useRequireAuth.ts](../../../frontend/src/hooks/useRequireAuth.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)；其余 1 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice/exams/result/[id]`

### [frontend/src/app/(main)/practice/exams/result/[id]/layout.tsx](../../../frontend/src/app/%28main%29/practice/exams/result/%5Bid%5D/layout.tsx)

/practice/exams/result/[id] 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/practice/exams/result/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/result/%5Bid%5D/page.tsx)

网址 /practice/exams/result/[id] 的考试结果页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`AttemptDetail`、`ExamResultPage`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/components/ui/ToggleGroup.tsx](../../../frontend/src/components/ui/ToggleGroup.tsx)；其余 5 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice`

### [frontend/src/app/(main)/practice/layout.tsx](../../../frontend/src/app/%28main%29/practice/layout.tsx)

/practice 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice/listening/[id]`

### [frontend/src/app/(main)/practice/listening/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/%5Bid%5D/page.tsx)

网址 /practice/listening/[id] 的听力练习页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`ListeningAttempt`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/components/listening/ClipPlayer.tsx](../../../frontend/src/components/listening/ClipPlayer.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)；其余 4 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice/listening`

### [frontend/src/app/(main)/practice/listening/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/page.tsx)

网址 /practice/listening 的听力练习页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`ListeningLibrary`。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)、[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)；其余 4 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/practice`

### [frontend/src/app/(main)/practice/page.tsx](../../../frontend/src/app/%28main%29/practice/page.tsx)

网址 /practice 的练习中心页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`Summary`、`Wrong`、`PaperItem`、`TYPES`、`LINK_TEXT`、`formatDate`、`formatShortDate`、`suggestedMinutesFor`、`SECTION_LABELS`、`sectionSummary`（其余见机器清单）。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/components/teaching/TeachingCatalog.tsx](../../../frontend/src/components/teaching/TeachingCatalog.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)；其余 2 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/profile`

### [frontend/src/app/(main)/profile/layout.tsx](../../../frontend/src/app/%28main%29/profile/layout.tsx)

/profile 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)

网址 /profile 的个人档案/设置页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`VocabStats`、`maskPhone`、`daysSince`、`joinedLabel`、`targetLabel`、`TABS`、`TabKey`、`TAB_HEADERS`、`ProfilePage`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/profile/EventDistributionChart.tsx](../../../frontend/src/components/profile/EventDistributionChart.tsx)、[frontend/src/components/profile/MasteryTrend.tsx](../../../frontend/src/components/profile/MasteryTrend.tsx)、[frontend/src/components/profile/ProfileOverview.tsx](../../../frontend/src/components/profile/ProfileOverview.tsx)、[frontend/src/components/profile/ProfileTab.tsx](../../../frontend/src/components/profile/ProfileTab.tsx)；其余 12 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/rankings`

### [frontend/src/app/(main)/rankings/layout.tsx](../../../frontend/src/app/%28main%29/rankings/layout.tsx)

/rankings 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/rankings/loading.tsx](../../../frontend/src/app/%28main%29/rankings/loading.tsx)

/rankings 范围的 Next loading 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`RankingsLoading`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/rankings/page.tsx](../../../frontend/src/app/%28main%29/rankings/page.tsx)

网址 /rankings 的学习视频榜单页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`TABS`、`SKELETON_ROWS`、`RankingsPage`。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/rankings/RankingRow.tsx](../../../frontend/src/components/rankings/RankingRow.tsx)、[frontend/src/components/rankings/TopPodium.tsx](../../../frontend/src/components/rankings/TopPodium.tsx)；其余 8 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/search`

### [frontend/src/app/(main)/search/layout.tsx](../../../frontend/src/app/%28main%29/search/layout.tsx)

/search 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/search/page.tsx](../../../frontend/src/app/%28main%29/search/page.tsx)

网址 /search 的视频/原句搜索页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`Word`、`SubtitleResult`、`Group`、`Results`、`GROUPS`、`GROUP_UNITS`、`WORD_LEVEL_LABELS`、`HISTORY_KEY`、`stamp`、`Highlight`（其余见机器清单）。
- 直接依赖：[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)、[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)；其余 9 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/vocabulary/drill`

### [frontend/src/app/(main)/vocabulary/drill/layout.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/layout.tsx)

/vocabulary/drill 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)

网址 /vocabulary/drill 的单词训练页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`VocabDrillPage`、`DrillHeader`、`VideoScopedDrill`、`QuickReview`、`Phase`、`REVIEW_FLUSH_SIZE`、`DailyTraining`、`DrillIntro`。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/practice/PracticePanels.tsx](../../../frontend/src/components/practice/PracticePanels.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)；其余 15 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/vocabulary`

### [frontend/src/app/(main)/vocabulary/layout.tsx](../../../frontend/src/app/%28main%29/vocabulary/layout.tsx)

/vocabulary 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 直接依赖：[frontend/src/components/common/AstryxProvider.tsx](../../../frontend/src/components/common/AstryxProvider.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)

网址 /vocabulary 的词汇本页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`VocabStatsResponse`、`PAGE_SIZE`、`InPlaceLink`、`masteryBadge`、`VocabSetsPanel`、`VocabularyPage`。
- 直接依赖：[frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)、[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)；其余 17 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/vocabulary/review`

### [frontend/src/app/(main)/vocabulary/review/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/review/page.tsx)

网址 /vocabulary/review 的复习入口页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`DEFAULT_BATCH`、`MIN_BATCH`、`MAX_BATCH`、`clampBatch`、`VocabularyReviewPage`、`ReviewSkeleton`。
- 直接依赖：[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/components/vocabulary/LessonWordSources.tsx](../../../frontend/src/components/vocabulary/LessonWordSources.tsx)、[frontend/src/hooks/useRequireAuth.ts](../../../frontend/src/hooks/useRequireAuth.ts)；其余 6 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/vocabulary/sets/[id]`

### [frontend/src/app/(main)/vocabulary/sets/[id]/layout.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/layout.tsx)

/vocabulary/sets/[id] 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/vocabulary/sets/[id]/loading.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/loading.tsx)

/vocabulary/sets/[id] 范围的 Next loading 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`VocabSetLoading`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)

网址 /vocabulary/sets/[id] 的词集详情页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`SetWord`、`VocabStats`、`BATCH`、`SCOPE_TABS`、`ScopeKey`、`levelLabel`、`ipaText`、`isMastered`、`typeLabel`、`sourceLabel`（其余见机器清单）。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)；其余 12 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/vocabulary/sets/[id]/sieve`

### [frontend/src/app/(main)/vocabulary/sets/[id]/sieve/layout.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/sieve/layout.tsx)

/vocabulary/sets/[id]/sieve 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/vocabulary/sets/[id]/sieve/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/sieve/page.tsx)

网址 /vocabulary/sets/[id]/sieve 的快速过筛页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`VocabSievePage`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/vocabulary/HighlightedSentence.tsx](../../../frontend/src/components/vocabulary/HighlightedSentence.tsx)、[frontend/src/components/vocabulary/VocabWordCard.tsx](../../../frontend/src/components/vocabulary/VocabWordCard.tsx)；其余 5 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/vocabulary/sets`

### [frontend/src/app/(main)/vocabulary/sets/layout.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/layout.tsx)

/vocabulary/sets 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/vocabulary/sets/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/page.tsx)

网址 /vocabulary/sets 的个人词集页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`SetFilter`、`typeLabel`、`sourceLabel`、`statusLabel`、`VocabSetsPage`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)；其余 8 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/watch/[id]`

### [frontend/src/app/(main)/watch/[id]/layout.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/layout.tsx)

/watch/[id] 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)

网址 /watch/[id] 的视频逐句点词学习页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`useWatchReturn`、`VideoActions`、`WatchPage`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/subtitle/WordTooltipInline.tsx](../../../frontend/src/components/subtitle/WordTooltipInline.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)；其余 40 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/watch/[id]/transcript`

### [frontend/src/app/(main)/watch/[id]/transcript/layout.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/transcript/layout.tsx)

/watch/[id]/transcript 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/watch/[id]/transcript/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/transcript/page.tsx)

网址 /watch/[id]/transcript 的视频整篇文稿页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`TranscriptPage`。
- 直接依赖：[frontend/src/components/transcript/TranscriptDocument.tsx](../../../frontend/src/components/transcript/TranscriptDocument.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/(main)/weekly-report`

### [frontend/src/app/(main)/weekly-report/layout.tsx](../../../frontend/src/app/%28main%29/weekly-report/layout.tsx)

/weekly-report 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`Layout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/(main)/weekly-report/page.tsx](../../../frontend/src/app/%28main%29/weekly-report/page.tsx)

网址 /weekly-report 的退役周报兼容跳转页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`RetiredWeeklyReport`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app`

### [frontend/src/app/apple-icon.png](../../../frontend/src/app/apple-icon.png)

Next 静态 metadata 图标：apple-icon.png；框架按文件约定生成页面 head/图标路由，不是 TS/React UI 编排。

- 隐式入口：Next.js 静态 metadata 图标文件约定（favicon/icon/apple-icon）。
- 处置：保留。

### [frontend/src/app/error.tsx](../../../frontend/src/app/error.tsx)

/frontend/src/app 范围的 Next error 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`Error`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/favicon.ico](../../../frontend/src/app/favicon.ico)

Next 静态 metadata 图标：favicon.ico；框架按文件约定生成页面 head/图标路由，不是 TS/React UI 编排。

- 隐式入口：Next.js 静态 metadata 图标文件约定（favicon/icon/apple-icon）。
- 处置：保留。

## `frontend/src/app/forgot-password`

### [frontend/src/app/forgot-password/layout.tsx](../../../frontend/src/app/forgot-password/layout.tsx)

/forgot-password 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`ForgotPasswordLayout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/forgot-password/page.tsx](../../../frontend/src/app/forgot-password/page.tsx)

网址 /forgot-password 的短信重置密码页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`maskPhone`、`OTP_LENGTH`、`STEPS`、`ForgotPasswordPage`。
- 直接依赖：[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/auth/PasswordField.tsx](../../../frontend/src/components/auth/PasswordField.tsx)、[frontend/src/components/auth/SmsOtpInput.tsx](../../../frontend/src/components/auth/SmsOtpInput.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/hooks/useSmsCode.ts](../../../frontend/src/hooks/useSmsCode.ts)；其余 5 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app`

### [frontend/src/app/global-error.tsx](../../../frontend/src/app/global-error.tsx)

/frontend/src/app 范围的 Next global-error 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`GlobalError`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/globals.css](../../../frontend/src/app/globals.css)

Tailwind v4、全局语义 token、基础样式和 Astryx CSS 入口。

- 直接使用者：[frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx)。
- 处置：保留。

### [frontend/src/app/icon-192.png](../../../frontend/src/app/icon-192.png)

品牌多尺寸备用导出：icon-192.png；当前无 import/manifest 引用，Next 图标约定不识别此带连字符命名，构建没有该路由；非运行必需，暂保留素材原件。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/src/app/icon-512.png](../../../frontend/src/app/icon-512.png)

品牌多尺寸备用导出：icon-512.png；当前无 import/manifest 引用，Next 图标约定不识别此带连字符命名，构建没有该路由；非运行必需，暂保留素材原件。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。

### [frontend/src/app/icon.png](../../../frontend/src/app/icon.png)

Next 静态 metadata 图标：icon.png；框架按文件约定生成页面 head/图标路由，不是 TS/React UI 编排。

- 隐式入口：Next.js 静态 metadata 图标文件约定（favicon/icon/apple-icon）。
- 处置：保留。

### [frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx)

/frontend/src/app 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`viewport`、`themeInitScript`、`RootLayout`。
- 直接依赖：[frontend/src/app/globals.css](../../../frontend/src/app/globals.css)、[frontend/src/app/user-ui.css](../../../frontend/src/app/user-ui.css)、[frontend/src/components/common/AuthInitializer.tsx](../../../frontend/src/components/common/AuthInitializer.tsx)、[frontend/src/components/common/ThemeProvider.tsx](../../../frontend/src/components/common/ThemeProvider.tsx)、[frontend/src/components/common/ThemedToaster.tsx](../../../frontend/src/components/common/ThemedToaster.tsx)、[frontend/src/lib/siteConfig.ts](../../../frontend/src/lib/siteConfig.ts)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/loading.tsx](../../../frontend/src/app/loading.tsx)

/frontend/src/app 范围的 Next loading 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`RootLoading`。
- 直接依赖：[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/login`

### [frontend/src/app/login/layout.tsx](../../../frontend/src/app/login/layout.tsx)

/login 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`LoginLayout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)

网址 /login 的登录页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`LoginMode`、`OTP_LENGTH`、`TABS`、`LoginPage`、`LoginForm`。
- 直接依赖：[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/auth/AuthenticatedRedirect.tsx](../../../frontend/src/components/auth/AuthenticatedRedirect.tsx)、[frontend/src/components/auth/PasswordField.tsx](../../../frontend/src/components/auth/PasswordField.tsx)、[frontend/src/components/auth/SmsOtpInput.tsx](../../../frontend/src/components/auth/SmsOtpInput.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 10 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app`

### [frontend/src/app/not-found.tsx](../../../frontend/src/app/not-found.tsx)

/frontend/src/app 范围的 Next not-found 状态边界；由框架自动调用，负责错误/无内容/加载反馈。

- 代码入口/类型：`RootNotFound`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/onboarding`

### [frontend/src/app/onboarding/layout.tsx](../../../frontend/src/app/onboarding/layout.tsx)

/onboarding 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`OnboardingLayout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/onboarding/page.tsx](../../../frontend/src/app/onboarding/page.tsx)

网址 /onboarding 的个人引导页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`LEVELS`、`EXAMS`、`DAILY_MINUTES`、`TOTAL_STEPS`、`PickOption`、`SwitchRow`、`OnboardingPage`。
- 直接依赖：[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)、[frontend/src/components/profile/InterestPicker.tsx](../../../frontend/src/components/profile/InterestPicker.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/hooks/useRequireAuth.ts](../../../frontend/src/hooks/useRequireAuth.ts)、[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)；其余 4 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/privacy`

### [frontend/src/app/privacy/page.tsx](../../../frontend/src/app/privacy/page.tsx)

网址 /privacy 的隐私政策页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`metadata`、`operatorName`、`uscc`、`SECTIONS`、`H2`、`PrivacyPage`。
- 直接依赖：[frontend/src/components/legal/LegalLayout.tsx](../../../frontend/src/components/legal/LegalLayout.tsx)、[frontend/src/components/legal/LegalTable.tsx](../../../frontend/src/components/legal/LegalTable.tsx)、[frontend/src/lib/siteConfig.ts](../../../frontend/src/lib/siteConfig.ts)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/register`

### [frontend/src/app/register/layout.tsx](../../../frontend/src/app/register/layout.tsx)

/register 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`RegisterLayout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)

网址 /register 的注册页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`OTP_LENGTH`、`RegisterPage`、`RegisterForm`。
- 直接依赖：[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/auth/AuthenticatedRedirect.tsx](../../../frontend/src/components/auth/AuthenticatedRedirect.tsx)、[frontend/src/components/auth/PasswordField.tsx](../../../frontend/src/components/auth/PasswordField.tsx)、[frontend/src/components/auth/SmsOtpInput.tsx](../../../frontend/src/components/auth/SmsOtpInput.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 9 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app`

### [frontend/src/app/robots.ts](../../../frontend/src/app/robots.ts)

按框架约定生成 robots.txt，非普通 import 消费。

- 代码入口/类型：`robots`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/set-password`

### [frontend/src/app/set-password/layout.tsx](../../../frontend/src/app/set-password/layout.tsx)

/set-password 及子路由的布局/metadata/provider 边界；由 Next 目录约定隐式装配。

- 代码入口/类型：`metadata`、`SetPasswordLayout`。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

### [frontend/src/app/set-password/page.tsx](../../../frontend/src/app/set-password/page.tsx)

网址 /set-password 的首次设置密码页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`Origin`、`SUBTITLE`、`SetPasswordPage`、`SetPasswordForm`。
- 直接依赖：[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/auth/PasswordField.tsx](../../../frontend/src/components/auth/PasswordField.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/hooks/useRequireAuth.ts](../../../frontend/src/hooks/useRequireAuth.ts)；其余 4 项见机器清单。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app/terms`

### [frontend/src/app/terms/page.tsx](../../../frontend/src/app/terms/page.tsx)

网址 /terms 的用户协议页面；在父 layout 内组合组件、Hook 和 API，不是后端授权入口。

- 代码入口/类型：`metadata`、`operatorName`、`uscc`、`SECTIONS`、`H2`、`TermsPage`。
- 直接依赖：[frontend/src/components/legal/LegalLayout.tsx](../../../frontend/src/components/legal/LegalLayout.tsx)、[frontend/src/lib/siteConfig.ts](../../../frontend/src/lib/siteConfig.ts)。
- 隐式入口：Next.js App Router 文件约定。
- 处置：保留。

## `frontend/src/app`

### [frontend/src/app/user-ui.css](../../../frontend/src/app/user-ui.css)

仅用户壳的蓝色主题、深浅变量、版式和观看/词汇交互样式。

- 直接使用者：[frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx)。
- 处置：保留。

## `frontend/src/components/admin`

### [frontend/src/components/admin/AdminSidebar.tsx](../../../frontend/src/components/admin/AdminSidebar.tsx)

可复用 UI：管理员侧栏；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`NavItem`、`NavSection`、`ADMIN_SIDEBAR_KEY`、`NAV`、`CollapseContext`、`useSidebarCollapse`、`NavLinks`、`Brand`、`AdminSidebar`。
- 直接依赖：[frontend/src/hooks/useLessonAvailability.ts](../../../frontend/src/hooks/useLessonAvailability.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)。
- 处置：保留。

### [frontend/src/components/admin/AdminTopbar.tsx](../../../frontend/src/components/admin/AdminTopbar.tsx)

可复用 UI：后台顶栏和管理身份入口；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`BREADCRUMBS`、`resolveBreadcrumbs`、`UserMenu`、`AdminTopbar`。
- 直接依赖：[frontend/src/components/admin/ui/AdminBreadcrumb.tsx](../../../frontend/src/components/admin/ui/AdminBreadcrumb.tsx)、[frontend/src/hooks/useVisibilityAwareInterval.ts](../../../frontend/src/hooks/useVisibilityAwareInterval.ts)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/stores/adminAuthStore.ts](../../../frontend/src/stores/adminAuthStore.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)。
- 处置：保留。

### [frontend/src/components/admin/DataTable.tsx](../../../frontend/src/components/admin/DataTable.tsx)

可复用 UI：后台表格公共布局；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`DataTableColumn`、`DataTable`、`RowGroup`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)。
- 处置：保留。

### [frontend/src/components/admin/FilterPills.tsx](../../../frontend/src/components/admin/FilterPills.tsx)

可复用 UI：后台筛选入口；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`FilterOption`、`FilterPills`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)。
- 处置：保留。

### [frontend/src/components/admin/GrowthTrendChart.tsx](../../../frontend/src/components/admin/GrowthTrendChart.tsx)

可复用 UI：按需加载的后台增长趋势图；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`GrowthTrendPoint`、`GrowthTrendChart`。
- 直接依赖：[frontend/src/lib/chart-theme.ts](../../../frontend/src/lib/chart-theme.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/page.tsx)。
- 处置：保留。

### [frontend/src/components/admin/Pagination.tsx](../../../frontend/src/components/admin/Pagination.tsx)

可复用 UI：后台分页；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Pagination`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)。
- 处置：保留。

### [frontend/src/components/admin/QualityReportPanel.tsx](../../../frontend/src/components/admin/QualityReportPanel.tsx)

可复用 UI：视频转录/翻译质量报告；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ENGINES`、`stageLabel`、`formatCoverage`、`ReportRow`、`QualityReportPanel`。
- 直接依赖：[frontend/src/components/admin/SectionCard.tsx](../../../frontend/src/components/admin/SectionCard.tsx)、[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/admin/SectionCard.tsx](../../../frontend/src/components/admin/SectionCard.tsx)

可复用 UI：后台分区边界；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SectionCard`。
- 直接依赖：[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/components/admin/QualityReportPanel.tsx](../../../frontend/src/components/admin/QualityReportPanel.tsx)。
- 处置：保留。

### [frontend/src/components/admin/StatChip.tsx](../../../frontend/src/components/admin/StatChip.tsx)

可复用 UI：后台轻量真实统计字段；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`StatChip`。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)。
- 处置：保留。

### [frontend/src/components/admin/StatsCharts.tsx](../../../frontend/src/components/admin/StatsCharts.tsx)

可复用 UI：后台趋势/状态图集合；所在业务范围为 admin，事件/数据来自列出的直接依赖。

- 代码入口/类型：`StatsTrendPoint`、`StatsChartSlice`、`StatsTrendChart`、`StatsStatusBarChart`。
- 直接依赖：[frontend/src/lib/chart-theme.ts](../../../frontend/src/lib/chart-theme.ts)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)。
- 处置：保留。

## `frontend/src/components/admin/home`

### [frontend/src/components/admin/home/EditorialPreviewPane.tsx](../../../frontend/src/components/admin/home/EditorialPreviewPane.tsx)

可复用 UI：当前首页草稿/发布版本可视预览；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`EditorialPreviewPane`。
- 直接依赖：[frontend/src/components/admin/home/HomeLayoutIssues.tsx](../../../frontend/src/components/admin/home/HomeLayoutIssues.tsx)、[frontend/src/components/home/HomeEditorialHero.tsx](../../../frontend/src/components/home/HomeEditorialHero.tsx)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomePreviewDialog.tsx](../../../frontend/src/components/admin/home/HomePreviewDialog.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/HomeContentDraftForm.tsx](../../../frontend/src/components/admin/home/HomeContentDraftForm.tsx)

可复用 UI：首页草稿各字段编辑与字幕引用选择；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`slugFromText`、`newStableId`、`phraseOccursInSentence`、`FormSection`、`Field`、`ExpressionRow`、`ScenarioRow`、`HomeContentDraftForm`。
- 直接依赖：[frontend/src/components/admin/home/SubtitlePickers.tsx](../../../frontend/src/components/admin/home/SubtitlePickers.tsx)、[frontend/src/components/admin/home/format.ts](../../../frontend/src/components/admin/home/format.ts)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeContentPanel.tsx](../../../frontend/src/components/admin/home/HomeContentPanel.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/HomeContentPanel.tsx](../../../frontend/src/components/admin/home/HomeContentPanel.tsx)

可复用 UI：视频侧首页草稿/生成/发布总面板；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`GENERATION_POLL_INTERVAL_MS`、`ConfirmState`、`HomeContentPanel`。
- 直接依赖：[frontend/src/components/admin/home/HomeContentDraftForm.tsx](../../../frontend/src/components/admin/home/HomeContentDraftForm.tsx)、[frontend/src/components/admin/home/HomeContentStatus.tsx](../../../frontend/src/components/admin/home/HomeContentStatus.tsx)、[frontend/src/components/admin/home/HomeContentVersions.tsx](../../../frontend/src/components/admin/home/HomeContentVersions.tsx)、[frontend/src/components/admin/home/HomePreviewDialog.tsx](../../../frontend/src/components/admin/home/HomePreviewDialog.tsx)、[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 7 项见机器清单。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)。
- 处置：更新必要说明/引用或生成路径。

### [frontend/src/components/admin/home/HomeContentStatus.tsx](../../../frontend/src/components/admin/home/HomeContentStatus.tsx)

可复用 UI：草稿生成状态和冲突/错误反馈；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`latestRevision`、`StatusBlock`、`GenerationStatus`、`HomeContentStatus`。
- 直接依赖：[frontend/src/components/admin/home/format.ts](../../../frontend/src/components/admin/home/format.ts)、[frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeContentPanel.tsx](../../../frontend/src/components/admin/home/HomeContentPanel.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/HomeContentVersions.tsx](../../../frontend/src/components/admin/home/HomeContentVersions.tsx)

可复用 UI：已发布版本历史与恢复草稿；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`HomeContentVersions`。
- 直接依赖：[frontend/src/components/admin/home/format.ts](../../../frontend/src/components/admin/home/format.ts)、[frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeContentPanel.tsx](../../../frontend/src/components/admin/home/HomeContentPanel.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)

可复用 UI：首页位置、候选内容和整版发布/回退；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`HomeLayoutEditor`。
- 直接依赖：[frontend/src/components/admin/home/HomeLayoutIssues.tsx](../../../frontend/src/components/admin/home/HomeLayoutIssues.tsx)、[frontend/src/components/admin/home/HomePreviewDialog.tsx](../../../frontend/src/components/admin/home/HomePreviewDialog.tsx)、[frontend/src/components/admin/home/LayoutPositionSummary.tsx](../../../frontend/src/components/admin/home/LayoutPositionSummary.tsx)、[frontend/src/components/admin/home/LayoutSlotSections.tsx](../../../frontend/src/components/admin/home/LayoutSlotSections.tsx)、[frontend/src/components/admin/home/format.ts](../../../frontend/src/components/admin/home/format.ts)、[frontend/src/components/admin/ui/AdminPageHeader.tsx](../../../frontend/src/components/admin/ui/AdminPageHeader.tsx)；其余 6 项见机器清单。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/home-editorial/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/home-editorial/page.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/HomeLayoutIssues.tsx](../../../frontend/src/components/admin/home/HomeLayoutIssues.tsx)

可复用 UI：布局字段校验问题定位；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`FIELD_LABELS`、`fieldLabel`、`HomeLayoutIssues`。
- 直接依赖：[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/EditorialPreviewPane.tsx](../../../frontend/src/components/admin/home/EditorialPreviewPane.tsx)、[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/HomePreviewDialog.tsx](../../../frontend/src/components/admin/home/HomePreviewDialog.tsx)

可复用 UI：复用公共首页组件的草稿预览对话框；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`HomePreviewDialog`。
- 直接依赖：[frontend/src/components/admin/home/EditorialPreviewPane.tsx](../../../frontend/src/components/admin/home/EditorialPreviewPane.tsx)、[frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeContentPanel.tsx](../../../frontend/src/components/admin/home/HomeContentPanel.tsx)、[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/LayoutCandidateSelect.tsx](../../../frontend/src/components/admin/home/LayoutCandidateSelect.tsx)

可复用 UI：按可用候选选择布局引用；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`candidateLabel`、`candidateReason`、`CandidateSelect`、`CandidateSummary`。
- 直接依赖：[frontend/src/components/admin/home/format.ts](../../../frontend/src/components/admin/home/format.ts)、[frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)、[frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/LayoutSlotSections.tsx](../../../frontend/src/components/admin/home/LayoutSlotSections.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/LayoutPositionSummary.tsx](../../../frontend/src/components/admin/home/LayoutPositionSummary.tsx)

可复用 UI：布局位置和引用摘要；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`StatusCell`、`revisionTitle`、`LayoutPositionSummary`。
- 直接依赖：[frontend/src/components/admin/home/format.ts](../../../frontend/src/components/admin/home/format.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/LayoutSlotSections.tsx](../../../frontend/src/components/admin/home/LayoutSlotSections.tsx)

可复用 UI：主推/表达/情境位置编辑区；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`MAX_SECONDARY_SLOTS`、`MAX_SCENARIO_SLOTS`、`LeadSection`、`SecondarySection`、`ExpressionSection`、`ScenarioSection`。
- 直接依赖：[frontend/src/components/admin/home/LayoutCandidateSelect.tsx](../../../frontend/src/components/admin/home/LayoutCandidateSelect.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/SubtitlePickers.tsx](../../../frontend/src/components/admin/home/SubtitlePickers.tsx)

可复用 UI：从真实字幕挑句/片段；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SUBTITLE_OPTION_LENGTH`、`subtitleOptionLabel`、`SubtitleSelect`、`SubtitleQuote`、`SubtitleMultiPicker`。
- 直接依赖：[frontend/src/components/admin/home/format.ts](../../../frontend/src/components/admin/home/format.ts)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)、[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeContentDraftForm.tsx](../../../frontend/src/components/admin/home/HomeContentDraftForm.tsx)。
- 处置：保留。

### [frontend/src/components/admin/home/format.ts](../../../frontend/src/components/admin/home/format.ts)

可复用 UI：时间、时长和数量统一格式化；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`formatClock`、`formatSeconds`、`shortenLine`、`formatDateTime`、`POSITION_LABELS`。
- 直接依赖：[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeContentDraftForm.tsx](../../../frontend/src/components/admin/home/HomeContentDraftForm.tsx)、[frontend/src/components/admin/home/HomeContentStatus.tsx](../../../frontend/src/components/admin/home/HomeContentStatus.tsx)、[frontend/src/components/admin/home/HomeContentVersions.tsx](../../../frontend/src/components/admin/home/HomeContentVersions.tsx)、[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)、[frontend/src/components/admin/home/LayoutCandidateSelect.tsx](../../../frontend/src/components/admin/home/LayoutCandidateSelect.tsx)、[frontend/src/components/admin/home/LayoutPositionSummary.tsx](../../../frontend/src/components/admin/home/LayoutPositionSummary.tsx)；其余 1 项见机器清单。
- 处置：保留。

## `frontend/src/components/admin/ui`

### [frontend/src/components/admin/ui/AdminBreadcrumb.tsx](../../../frontend/src/components/admin/ui/AdminBreadcrumb.tsx)

可复用 UI：管理员专用 面包屑；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`BreadcrumbItem`、`AdminBreadcrumbProps`、`AdminBreadcrumb`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/admin/AdminTopbar.tsx](../../../frontend/src/components/admin/AdminTopbar.tsx)、[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)。
- 处置：保留。

### [frontend/src/components/admin/ui/AdminDialog.tsx](../../../frontend/src/components/admin/ui/AdminDialog.tsx)

可复用 UI：管理员专用 对话框；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AdminDialogProps`、`SIZES`、`AdminDialog`、`AdminConfirmDialogProps`、`AdminConfirmDialog`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/hooks/useModalFocus.ts](../../../frontend/src/hooks/useModalFocus.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)。
- 处置：保留。

### [frontend/src/components/admin/ui/AdminDropdown.tsx](../../../frontend/src/components/admin/ui/AdminDropdown.tsx)

可复用 UI：管理员专用 下拉菜单；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AdminDropdownItem`、`AdminDropdownProps`、`AdminDropdown`。
- 直接依赖：[frontend/src/components/ui/DropdownMenu.tsx](../../../frontend/src/components/ui/DropdownMenu.tsx)、[frontend/src/hooks/useOverlayContainer.ts](../../../frontend/src/hooks/useOverlayContainer.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)。
- 处置：保留。

### [frontend/src/components/admin/ui/AdminEmptyState.tsx](../../../frontend/src/components/admin/ui/AdminEmptyState.tsx)

可复用 UI：管理员专用 空状态；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AdminEmptyStateProps`、`AdminEmptyState`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)。
- 处置：保留。

### [frontend/src/components/admin/ui/AdminPageHeader.tsx](../../../frontend/src/components/admin/ui/AdminPageHeader.tsx)

可复用 UI：管理员专用 页标题；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AdminPageHeaderProps`、`AdminPageHeader`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)、[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)、[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)。
- 处置：保留。

### [frontend/src/components/admin/ui/AdminSearchInput.tsx](../../../frontend/src/components/admin/ui/AdminSearchInput.tsx)

可复用 UI：管理员专用 搜索输入；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AdminSearchInputProps`、`AdminSearchInput`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)。
- 处置：保留。

### [frontend/src/components/admin/ui/AdminSkeleton.tsx](../../../frontend/src/components/admin/ui/AdminSkeleton.tsx)

可复用 UI：管理员专用 加载骨架；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Skeleton`、`TableRows`、`Cards`、`Chart`、`Page`、`AdminSkeleton`。
- 直接依赖：[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)。
- 处置：保留。

### [frontend/src/components/admin/ui/AdminTabs.tsx](../../../frontend/src/components/admin/ui/AdminTabs.tsx)

可复用 UI：管理员专用 页签；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AdminTab`、`AdminTabsProps`、`AdminTabs`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)。
- 处置：保留。

### [frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)

组件包统一 re-export 出口；把本目录公共组件提供给上游，具体导出关系见直接依赖。

- 直接依赖：[frontend/src/components/admin/ui/AdminBreadcrumb.tsx](../../../frontend/src/components/admin/ui/AdminBreadcrumb.tsx)、[frontend/src/components/admin/ui/AdminDialog.tsx](../../../frontend/src/components/admin/ui/AdminDialog.tsx)、[frontend/src/components/admin/ui/AdminDropdown.tsx](../../../frontend/src/components/admin/ui/AdminDropdown.tsx)、[frontend/src/components/admin/ui/AdminEmptyState.tsx](../../../frontend/src/components/admin/ui/AdminEmptyState.tsx)、[frontend/src/components/admin/ui/AdminPageHeader.tsx](../../../frontend/src/components/admin/ui/AdminPageHeader.tsx)、[frontend/src/components/admin/ui/AdminSearchInput.tsx](../../../frontend/src/components/admin/ui/AdminSearchInput.tsx)；其余 2 项见机器清单。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)、[frontend/src/components/lessons/LessonAdmin.tsx](../../../frontend/src/components/lessons/LessonAdmin.tsx)。
- 处置：保留。

## `frontend/src/components/auth`

### [frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)

可复用 UI：认证页面统一容器；所在业务范围为 auth，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AuthCard`。
- 直接依赖：[frontend/src/components/auth/AuthThemeToggle.tsx](../../../frontend/src/components/auth/AuthThemeToggle.tsx)、[frontend/src/components/common/ComplianceInfo.tsx](../../../frontend/src/components/common/ComplianceInfo.tsx)、[frontend/src/lib/siteConfig.ts](../../../frontend/src/lib/siteConfig.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/forgot-password/page.tsx](../../../frontend/src/app/forgot-password/page.tsx)、[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)、[frontend/src/app/onboarding/page.tsx](../../../frontend/src/app/onboarding/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)、[frontend/src/app/set-password/page.tsx](../../../frontend/src/app/set-password/page.tsx)、[frontend/src/components/auth/RedirectStuckState.tsx](../../../frontend/src/components/auth/RedirectStuckState.tsx)。
- 处置：保留。

### [frontend/src/components/auth/AuthThemeToggle.tsx](../../../frontend/src/components/auth/AuthThemeToggle.tsx)

可复用 UI：认证页主题切换；所在业务范围为 auth，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AuthThemeToggle`。
- 直接依赖：[frontend/src/components/common/ThemeProvider.tsx](../../../frontend/src/components/common/ThemeProvider.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/layout/PublicTopBar.tsx](../../../frontend/src/components/layout/PublicTopBar.tsx)、[frontend/src/components/legal/LegalLayout.tsx](../../../frontend/src/components/legal/LegalLayout.tsx)。
- 处置：保留。

### [frontend/src/components/auth/AuthenticatedRedirect.tsx](../../../frontend/src/components/auth/AuthenticatedRedirect.tsx)

可复用 UI：已登录访问认证页时的安全跳转；所在业务范围为 auth，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AuthenticatedRedirect`。
- 直接依赖：[frontend/src/components/auth/RedirectStuckState.tsx](../../../frontend/src/components/auth/RedirectStuckState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)。
- 直接使用者：[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)。
- 处置：保留。

### [frontend/src/components/auth/PasswordField.tsx](../../../frontend/src/components/auth/PasswordField.tsx)

可复用 UI：密码输入可见性和反馈；所在业务范围为 auth，事件/数据来自列出的直接依赖。

- 代码入口/类型：`STRENGTH_LABEL`、`STRENGTH_SEG`、`RULES`、`PasswordFieldProps`、`PasswordField`。
- 直接依赖：[frontend/src/lib/password.ts](../../../frontend/src/lib/password.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/forgot-password/page.tsx](../../../frontend/src/app/forgot-password/page.tsx)、[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)、[frontend/src/app/set-password/page.tsx](../../../frontend/src/app/set-password/page.tsx)。
- 处置：保留。

### [frontend/src/components/auth/RedirectStuckState.tsx](../../../frontend/src/components/auth/RedirectStuckState.tsx)

可复用 UI：会话镜像错位后的恢复界面；所在业务范围为 auth，事件/数据来自列出的直接依赖。

- 代码入口/类型：`RedirectStuckState`。
- 直接依赖：[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/authHelpers.ts](../../../frontend/src/lib/authHelpers.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)。
- 直接使用者：[frontend/src/components/auth/AuthenticatedRedirect.tsx](../../../frontend/src/components/auth/AuthenticatedRedirect.tsx)。
- 处置：保留。

### [frontend/src/components/auth/SmsOtpInput.tsx](../../../frontend/src/components/auth/SmsOtpInput.tsx)

可复用 UI：短信验证码输入；所在业务范围为 auth，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SmsOtpInputProps`、`SmsOtpInput`。
- 直接依赖：[frontend/src/lib/smsCode.ts](../../../frontend/src/lib/smsCode.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/forgot-password/page.tsx](../../../frontend/src/app/forgot-password/page.tsx)、[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)。
- 处置：保留。

## `frontend/src/components/channels`

### [frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)

可复用 UI：频道封面/身份/学习信息入口；所在业务范围为 channels，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ChannelCard`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)、[frontend/src/components/video/VideoTitle.tsx](../../../frontend/src/components/video/VideoTitle.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)；其余 7 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/search/page.tsx](../../../frontend/src/app/%28main%29/search/page.tsx)。
- 处置：保留。

### [frontend/src/components/channels/ChannelStartCard.tsx](../../../frontend/src/components/channels/ChannelStartCard.tsx)

可复用 UI：频道推荐起学视频；所在业务范围为 channels，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ChannelStartBasis`、`ChannelStartCardProps`、`ChannelStartCard`。
- 直接依赖：[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)、[frontend/src/components/video/DifficultyBadge.tsx](../../../frontend/src/components/video/DifficultyBadge.tsx)、[frontend/src/components/video/VideoDescription.tsx](../../../frontend/src/components/video/VideoDescription.tsx)；其余 5 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/channels/ChannelSubscribeButton.tsx](../../../frontend/src/components/channels/ChannelSubscribeButton.tsx)

可复用 UI：订阅按钮及状态；所在业务范围为 channels，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Subscription`、`ChannelSubscribeButton`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/lib/subscriptionEvents.ts](../../../frontend/src/lib/subscriptionEvents.ts)。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/components/watch/WatchSourceCard.tsx](../../../frontend/src/components/watch/WatchSourceCard.tsx)。
- 处置：保留。

### [frontend/src/components/channels/ChannelVideoRow.tsx](../../../frontend/src/components/channels/ChannelVideoRow.tsx)

可复用 UI：频道视频行；所在业务范围为 channels，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ChannelVideoRowProps`、`ChannelVideoRow`。
- 直接依赖：[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)、[frontend/src/components/video/DifficultyBadge.tsx](../../../frontend/src/components/video/DifficultyBadge.tsx)、[frontend/src/components/video/VideoDescription.tsx](../../../frontend/src/components/video/VideoDescription.tsx)、[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)、[frontend/src/components/video/VideoTitle.tsx](../../../frontend/src/components/video/VideoTitle.tsx)；其余 2 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/channels/SubscribedChannels.tsx](../../../frontend/src/components/channels/SubscribedChannels.tsx)

可复用 UI：已订阅频道列表；所在业务范围为 channels，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SubscribedChannels`、`SubscriptionCard`。
- 直接依赖：[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)、[frontend/src/components/video/VideoTitle.tsx](../../../frontend/src/components/video/VideoTitle.tsx)、[frontend/src/lib/avatar.ts](../../../frontend/src/lib/avatar.ts)；其余 3 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)。
- 处置：保留。

## `frontend/src/components/common`

### [frontend/src/components/common/AstryxProvider.tsx](../../../frontend/src/components/common/AstryxProvider.tsx)

可复用 UI：词汇路由范围内 Astryx 主题与全站偏好映射；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AstryxProvider`。
- 直接依赖：[frontend/src/components/common/ThemeProvider.tsx](../../../frontend/src/components/common/ThemeProvider.tsx)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/layout.tsx](../../../frontend/src/app/%28main%29/vocabulary/layout.tsx)。
- 处置：保留。

### [frontend/src/components/common/AuthInitializer.tsx](../../../frontend/src/components/common/AuthInitializer.tsx)

可复用 UI：壳层会话恢复启动；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AuthInitializer`。
- 直接依赖：[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)。
- 直接使用者：[frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx)。
- 处置：保留。

### [frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)

可复用 UI：状态徽章；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`BadgeTone`、`TONE`、`Badge`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/components/admin/home/HomeContentStatus.tsx](../../../frontend/src/components/admin/home/HomeContentStatus.tsx)；其余 4 项见机器清单。
- 处置：保留。

### [frontend/src/components/common/ComplianceInfo.tsx](../../../frontend/src/components/common/ComplianceInfo.tsx)

可复用 UI：真实公示字段展示；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ComplianceInfo`。
- 直接依赖：[frontend/src/lib/siteConfig.ts](../../../frontend/src/lib/siteConfig.ts)。
- 直接使用者：[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/layout/SiteFooter.tsx](../../../frontend/src/components/layout/SiteFooter.tsx)、[frontend/src/components/legal/LegalLayout.tsx](../../../frontend/src/components/legal/LegalLayout.tsx)。
- 处置：保留。

### [frontend/src/components/common/Confetti.tsx](../../../frontend/src/components/common/Confetti.tsx)

可复用 UI：完成反馈动效；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ConfettiProps`、`Confetti`。
- 直接使用者：[frontend/src/components/vocabulary/TrainSummary.tsx](../../../frontend/src/components/vocabulary/TrainSummary.tsx)。
- 处置：保留。

### [frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)

可复用 UI：有后果提示的确认对话框；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ConfirmDialog`。
- 直接依赖：[frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/components/admin/QualityReportPanel.tsx](../../../frontend/src/components/admin/QualityReportPanel.tsx)；其余 7 项见机器清单。
- 处置：保留。

### [frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)

可复用 UI：无数据时的统一结构和必要操作；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`EmptyStateProps`、`EmptyState`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/practice/listening/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/page.tsx)、[frontend/src/app/(main)/rankings/page.tsx](../../../frontend/src/app/%28main%29/rankings/page.tsx)；其余 8 项见机器清单。
- 处置：保留。

### [frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)

可复用 UI：失败状态与重试操作；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ErrorStateProps`、`ErrorState`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/(main)/error.tsx](../../../frontend/src/app/%28main%29/error.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)；其余 29 项见机器清单。
- 处置：保留。

### [frontend/src/components/common/LoadMoreError.tsx](../../../frontend/src/components/common/LoadMoreError.tsx)

可复用 UI：分页加载失败时保留已载入内容；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`LoadMoreErrorProps`、`LoadMoreError`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/notifications/page.tsx](../../../frontend/src/app/%28main%29/notifications/page.tsx)、[frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)。
- 处置：保留。

### [frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)

可复用 UI：旧模态封装及兼容消费者；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Modal`。
- 直接依赖：[frontend/src/components/ui/Dialog.tsx](../../../frontend/src/components/ui/Dialog.tsx)、[frontend/src/hooks/useOverlayContainer.ts](../../../frontend/src/hooks/useOverlayContainer.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/onboarding/page.tsx](../../../frontend/src/app/onboarding/page.tsx)、[frontend/src/components/admin/home/HomePreviewDialog.tsx](../../../frontend/src/components/admin/home/HomePreviewDialog.tsx)、[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)；其余 1 项见机器清单。
- 处置：保留。

### [frontend/src/components/common/PageTransition.tsx](../../../frontend/src/components/common/PageTransition.tsx)

可复用 UI：路由切换的原生过渡辅助；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`PageTransitionProps`、`PageTransition`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/notifications/page.tsx](../../../frontend/src/app/%28main%29/notifications/page.tsx)；其余 5 项见机器清单。
- 处置：保留。

### [frontend/src/components/common/ShellSkeleton.tsx](../../../frontend/src/components/common/ShellSkeleton.tsx)

可复用 UI：壳层等待骨架；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ShellSkeleton`。
- 直接依赖：[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 处置：保留。

### [frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)

可复用 UI：内容卡片加载骨架；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SkeletonCardProps`、`Skeleton`、`SkeletonText`、`SkeletonCard`、`SkeletonCardGridProps`、`SkeletonCardGrid`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/loading.tsx](../../../frontend/src/app/%28main%29/loading.tsx)、[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)、[frontend/src/app/(main)/practice/listening/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/practice/page.tsx](../../../frontend/src/app/%28main%29/practice/page.tsx)、[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/app/(main)/vocabulary/review/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/review/page.tsx)；其余 4 项见机器清单。
- 处置：保留。

### [frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)

可复用 UI：加载动画和整页等待；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`FullPageSpinnerProps`、`sizeMap`、`FullPageSpinner`、`InlineSpinnerProps`、`InlineSpinner`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/notifications/page.tsx](../../../frontend/src/app/%28main%29/notifications/page.tsx)、[frontend/src/app/(main)/practice/exams/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/practice/exams/layout.tsx](../../../frontend/src/app/%28main%29/practice/exams/layout.tsx)；其余 18 项见机器清单。
- 处置：保留。

### [frontend/src/components/common/ThemeProvider.tsx](../../../frontend/src/components/common/ThemeProvider.tsx)

可复用 UI：全站主题偏好上下文；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ThemeContextValue`、`ThemeContext`、`ThemeProvider`、`useThemeContext`。
- 直接依赖：[frontend/src/hooks/useTheme.ts](../../../frontend/src/hooks/useTheme.ts)。
- 直接使用者：[frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx)、[frontend/src/components/auth/AuthThemeToggle.tsx](../../../frontend/src/components/auth/AuthThemeToggle.tsx)、[frontend/src/components/common/AstryxProvider.tsx](../../../frontend/src/components/common/AstryxProvider.tsx)、[frontend/src/components/common/ThemedToaster.tsx](../../../frontend/src/components/common/ThemedToaster.tsx)、[frontend/src/components/layout/AccountMenu.tsx](../../../frontend/src/components/layout/AccountMenu.tsx)、[frontend/src/lib/chart-theme.ts](../../../frontend/src/lib/chart-theme.ts)。
- 处置：保留。

### [frontend/src/components/common/ThemedToaster.tsx](../../../frontend/src/components/common/ThemedToaster.tsx)

可复用 UI：随站内主题变化的统一 toast；所在业务范围为 common，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ThemedToaster`。
- 直接依赖：[frontend/src/components/common/ThemeProvider.tsx](../../../frontend/src/components/common/ThemeProvider.tsx)。
- 直接使用者：[frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx)。
- 处置：保留。

## `frontend/src/components/exam`

### [frontend/src/components/exam/ExamAnswerOptions.tsx](../../../frontend/src/components/exam/ExamAnswerOptions.tsx)

可复用 UI：考试/教学共用的答案选项交互；所在业务范围为 exam，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ExamAnswerOptions`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/components/teaching/TeachingWorkspace.tsx](../../../frontend/src/components/teaching/TeachingWorkspace.tsx)。
- 处置：保留。

### [frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)

可复用 UI：冻结试卷逐题作答、交卷和恢复页面；所在业务范围为 exam，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ExamQuestionPublic`、`ExamSubmitResultItem`、`ExamSubmitResponse`、`ExamRunner`。
- 直接依赖：[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)、[frontend/src/components/exam/ExamAnswerOptions.tsx](../../../frontend/src/components/exam/ExamAnswerOptions.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)；其余 2 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/practice/daily/page.tsx](../../../frontend/src/app/%28main%29/practice/daily/page.tsx)、[frontend/src/app/(main)/practice/exams/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/practice/exams/redo/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/redo/page.tsx)、[frontend/src/app/(main)/practice/exams/result/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/result/%5Bid%5D/page.tsx)、[frontend/src/lib/examPresentation.test.ts](../../../frontend/src/lib/examPresentation.test.ts)、[frontend/src/lib/examPresentation.ts](../../../frontend/src/lib/examPresentation.ts)。
- 处置：保留。

### [frontend/src/components/exam/TargetExamSetting.tsx](../../../frontend/src/components/exam/TargetExamSetting.tsx)

可复用 UI：目标考试级别设置；所在业务范围为 exam，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TargetExamSettingProps`、`TargetExamSetting`。
- 直接依赖：[frontend/src/hooks/useUserPreferences.ts](../../../frontend/src/hooks/useUserPreferences.ts)、[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/stores/watchStore.ts](../../../frontend/src/stores/watchStore.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/profile/SettingsTab.tsx](../../../frontend/src/components/profile/SettingsTab.tsx)。
- 处置：保留。

## `frontend/src/components/home`

### [frontend/src/components/home/DiscoverRail.tsx](../../../frontend/src/components/home/DiscoverRail.tsx)

可复用 UI：首页学习侧栏；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`DiscoverContinue`、`Overview`、`DiscoverRail`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)、[frontend/src/hooks/useContinueLearning.ts](../../../frontend/src/hooks/useContinueLearning.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)；其余 4 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)。
- 处置：保留。

### [frontend/src/components/home/FeaturedListening.tsx](../../../frontend/src/components/home/FeaturedListening.tsx)

可复用 UI：首页听力入口；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`FeaturedListening`。
- 直接依赖：[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/components/home/FeaturedVideoCard.tsx](../../../frontend/src/components/home/FeaturedVideoCard.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)。
- 处置：保留。

### [frontend/src/components/home/FeaturedVideoCard.tsx](../../../frontend/src/components/home/FeaturedVideoCard.tsx)

可复用 UI：旧精选兜底卡；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`FeaturedVideoCard`。
- 直接依赖：[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/video/DifficultyBadge.tsx](../../../frontend/src/components/video/DifficultyBadge.tsx)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)、[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)；其余 1 项见机器清单。
- 直接使用者：[frontend/src/components/home/FeaturedListening.tsx](../../../frontend/src/components/home/FeaturedListening.tsx)、[frontend/src/components/home/HomeEditorialHero.tsx](../../../frontend/src/components/home/HomeEditorialHero.tsx)。
- 处置：保留。

### [frontend/src/components/home/HomeEditorialHero.tsx](../../../frontend/src/components/home/HomeEditorialHero.tsx)

可复用 UI：首页编辑主推、表达、情境及专用主标题；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`HomeEditorialMode`、`HomeEditorialHeader`、`HomeEditorialHero`、`HomeEditorialPreview`。
- 直接依赖：[frontend/src/components/home/FeaturedVideoCard.tsx](../../../frontend/src/components/home/FeaturedVideoCard.tsx)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)、[frontend/src/components/admin/home/EditorialPreviewPane.tsx](../../../frontend/src/components/admin/home/EditorialPreviewPane.tsx)。
- 处置：保留。

### [frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)

可复用 UI：首页筛选和分页视频流；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`DIFFICULTY_OPTIONS`、`HomeFeed`。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/LoadMoreError.tsx](../../../frontend/src/components/common/LoadMoreError.tsx)、[frontend/src/components/home/HomeFeedCard.tsx](../../../frontend/src/components/home/HomeFeedCard.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)；其余 7 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)。
- 处置：保留。

### [frontend/src/components/home/HomeFeedCard.tsx](../../../frontend/src/components/home/HomeFeedCard.tsx)

可复用 UI：首页视频卡；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`HomeFeedCard`。
- 直接依赖：[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)、[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)。
- 直接使用者：[frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)。
- 处置：保留。

### [frontend/src/components/home/HomeSubscribedChannels.tsx](../../../frontend/src/components/home/HomeSubscribedChannels.tsx)

可复用 UI：首页订阅频道入口；所在业务范围为 home，事件/数据来自列出的直接依赖。

- 代码入口/类型：`HomeSubscribedChannels`。
- 直接依赖：[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/lib/avatar.ts](../../../frontend/src/lib/avatar.ts)、[frontend/src/lib/channelSubscriptions.ts](../../../frontend/src/lib/channelSubscriptions.ts)、[frontend/src/types/channels.ts](../../../frontend/src/types/channels.ts)。
- 直接使用者：[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)。
- 处置：保留。

## `frontend/src/components/layout`

### [frontend/src/components/layout/AccountMenu.tsx](../../../frontend/src/components/layout/AccountMenu.tsx)

可复用 UI：本人账户菜单；所在业务范围为 layout，事件/数据来自列出的直接依赖。

- 代码入口/类型：`LINKS`、`AccountMenu`。
- 直接依赖：[frontend/src/components/common/ThemeProvider.tsx](../../../frontend/src/components/common/ThemeProvider.tsx)、[frontend/src/components/ui/Avatar.tsx](../../../frontend/src/components/ui/Avatar.tsx)、[frontend/src/hooks/useLessonAvailability.ts](../../../frontend/src/hooks/useLessonAvailability.ts)、[frontend/src/hooks/useMediaQuery.ts](../../../frontend/src/hooks/useMediaQuery.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)；其余 1 项见机器清单。
- 直接使用者：[frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx)、[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)。
- 处置：保留。

### [frontend/src/components/layout/MobileTabBar.tsx](../../../frontend/src/components/layout/MobileTabBar.tsx)

可复用 UI：手机主导航；所在业务范围为 layout，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TABS`、`MobileTabBar`。
- 直接依赖：[frontend/src/lib/navigation.ts](../../../frontend/src/lib/navigation.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/stores/vocabularyStore.ts](../../../frontend/src/stores/vocabularyStore.ts)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 处置：保留。

### [frontend/src/components/layout/PublicTopBar.tsx](../../../frontend/src/components/layout/PublicTopBar.tsx)

可复用 UI：公开页面导航；所在业务范围为 layout，事件/数据来自列出的直接依赖。

- 代码入口/类型：`PublicTopBar`。
- 直接依赖：[frontend/src/components/auth/AuthThemeToggle.tsx](../../../frontend/src/components/auth/AuthThemeToggle.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/lib/siteConfig.ts](../../../frontend/src/lib/siteConfig.ts)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 处置：保留。

### [frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx)

可复用 UI：用户桌面侧栏；所在业务范围为 layout，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Sidebar`。
- 直接依赖：[frontend/src/components/layout/AccountMenu.tsx](../../../frontend/src/components/layout/AccountMenu.tsx)、[frontend/src/hooks/useLessonAvailability.ts](../../../frontend/src/hooks/useLessonAvailability.ts)、[frontend/src/lib/navigation.ts](../../../frontend/src/lib/navigation.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/stores/notificationStore.ts](../../../frontend/src/stores/notificationStore.ts)、[frontend/src/stores/vocabularyStore.ts](../../../frontend/src/stores/vocabularyStore.ts)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 处置：保留。

### [frontend/src/components/layout/SiteFooter.tsx](../../../frontend/src/components/layout/SiteFooter.tsx)

可复用 UI：站点页脚与公示；所在业务范围为 layout，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SiteFooter`。
- 直接依赖：[frontend/src/components/common/ComplianceInfo.tsx](../../../frontend/src/components/common/ComplianceInfo.tsx)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 处置：保留。

### [frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)

可复用 UI：用户桌面导航/搜索/账户入口；所在业务范围为 layout，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TopBar`。
- 直接依赖：[frontend/src/components/layout/AccountMenu.tsx](../../../frontend/src/components/layout/AccountMenu.tsx)、[frontend/src/components/notifications/NotificationDropdown.tsx](../../../frontend/src/components/notifications/NotificationDropdown.tsx)、[frontend/src/components/search/CommandPalette.tsx](../../../frontend/src/components/search/CommandPalette.tsx)、[frontend/src/components/ui/Avatar.tsx](../../../frontend/src/components/ui/Avatar.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Popover.tsx](../../../frontend/src/components/ui/Popover.tsx)；其余 6 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 处置：保留。

### [frontend/src/components/layout/UnreadCountSync.tsx](../../../frontend/src/components/layout/UnreadCountSync.tsx)

可复用 UI：未读轮询/WebSocket 与导航同步；所在业务范围为 layout，事件/数据来自列出的直接依赖。

- 代码入口/类型：`UnreadCountSync`。
- 直接依赖：[frontend/src/hooks/useVisibilityAwareInterval.ts](../../../frontend/src/hooks/useVisibilityAwareInterval.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)、[frontend/src/stores/notificationStore.ts](../../../frontend/src/stores/notificationStore.ts)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 处置：保留。

## `frontend/src/components/legal`

### [frontend/src/components/legal/LegalLayout.tsx](../../../frontend/src/components/legal/LegalLayout.tsx)

可复用 UI：公开法律文本的页面结构；所在业务范围为 legal，事件/数据来自列出的直接依赖。

- 代码入口/类型：`LegalSection`、`LegalLayoutProps`、`LegalLayout`。
- 直接依赖：[frontend/src/components/auth/AuthThemeToggle.tsx](../../../frontend/src/components/auth/AuthThemeToggle.tsx)、[frontend/src/components/common/ComplianceInfo.tsx](../../../frontend/src/components/common/ComplianceInfo.tsx)、[frontend/src/lib/siteConfig.ts](../../../frontend/src/lib/siteConfig.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/privacy/page.tsx](../../../frontend/src/app/privacy/page.tsx)、[frontend/src/app/terms/page.tsx](../../../frontend/src/app/terms/page.tsx)。
- 处置：保留。

### [frontend/src/components/legal/LegalTable.tsx](../../../frontend/src/components/legal/LegalTable.tsx)

可复用 UI：法律条款表格可读结构；所在业务范围为 legal，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Cell`、`normalize`、`LegalTable`。
- 直接使用者：[frontend/src/app/privacy/page.tsx](../../../frontend/src/app/privacy/page.tsx)。
- 处置：保留。

## `frontend/src/components/lessons`

### [frontend/src/components/lessons/LessonAdmin.tsx](../../../frontend/src/components/lessons/LessonAdmin.tsx)

可复用 UI：课程导入、审核、签收据发布和撤回管理；所在业务范围为 lessons，事件/数据来自列出的直接依赖。

- 代码入口/类型：`labels`、`reviewUses`、`Selection`、`Diagnostic`、`Action`、`getDiagnostics`、`LessonAdmin`。
- 直接依赖：[frontend/src/components/admin/ui/index.ts](../../../frontend/src/components/admin/ui/index.ts)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/FormField.tsx](../../../frontend/src/components/ui/FormField.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)；其余 4 项见机器清单。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/lessons/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/lessons/page.tsx)。
- 处置：保留。

### [frontend/src/components/lessons/LessonCatalog.tsx](../../../frontend/src/components/lessons/LessonCatalog.tsx)

可复用 UI：课程目录和可用性状态；所在业务范围为 lessons，事件/数据来自列出的直接依赖。

- 代码入口/类型：`LessonCatalog`。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)；其余 2 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/lessons/page.tsx](../../../frontend/src/app/%28main%29/lessons/page.tsx)。
- 处置：保留。

### [frontend/src/components/lessons/LessonReader.tsx](../../../frontend/src/components/lessons/LessonReader.tsx)

可复用 UI：读取固定修订、字幕词锚点、播放与进度恢复；所在业务范围为 lessons，事件/数据来自列出的直接依赖。

- 代码入口/类型：`attributionLabels`、`intervalLabel`、`ReaderState`、`LessonReader`、`LessonContent`。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/lessons/LessonTutor.tsx](../../../frontend/src/components/lessons/LessonTutor.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)；其余 9 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/lessons/[lessonId]/page.tsx](../../../frontend/src/app/%28main%29/lessons/%5BlessonId%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/lessons/LessonTutor.tsx](../../../frontend/src/components/lessons/LessonTutor.tsx)

可复用 UI：课程语境绑定的导师对话；所在业务范围为 lessons，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TutorMessage`、`TutorPage`、`terminal`、`LessonTutor`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/FormField.tsx](../../../frontend/src/components/ui/FormField.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)；其余 4 项见机器清单。
- 直接使用者：[frontend/src/components/lessons/LessonReader.tsx](../../../frontend/src/components/lessons/LessonReader.tsx)。
- 处置：保留。

## `frontend/src/components/listening`

### [frontend/src/components/listening/ClipPlayer.tsx](../../../frontend/src/components/listening/ClipPlayer.tsx)

可复用 UI：听力片段播放器与句末停止；所在业务范围为 listening，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ClipPlayer`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)。
- 直接使用者：[frontend/src/app/(main)/practice/listening/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/%5Bid%5D/page.tsx)。
- 处置：保留。

## `frontend/src/components/notifications`

### [frontend/src/components/notifications/NotificationDropdown.tsx](../../../frontend/src/components/notifications/NotificationDropdown.tsx)

可复用 UI：导航中的未读消息与操作；所在业务范围为 notifications，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Notification`、`NotificationDropdownProps`、`buildWsUrl`、`NotificationDropdown`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)。
- 处置：保留。

### [frontend/src/components/notifications/NotificationPreferences.tsx](../../../frontend/src/components/notifications/NotificationPreferences.tsx)

可复用 UI：通知开关和时区/提醒设置；所在业务范围为 notifications，事件/数据来自列出的直接依赖。

- 代码入口/类型：`NotificationType`、`NOTIFICATION_TYPES`、`Preferences`、`NotificationPreferences`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/profile/SettingsTab.tsx](../../../frontend/src/components/profile/SettingsTab.tsx)。
- 处置：保留。

## `frontend/src/components/practice`

### [frontend/src/components/practice/PracticePanels.tsx](../../../frontend/src/components/practice/PracticePanels.tsx)

可复用 UI：练习总览各入口面板；所在业务范围为 practice，事件/数据来自列出的直接依赖。

- 代码入口/类型：`QuestionCard`、`OptionList`、`CheckButton`、`CompletionSummary`、`AudioPlayButton`、`WordDisplay`、`TranslationDisplay`、`SentenceWithBlank`、`PracticeItemRenderer`、`SessionLike`（其余见机器清单）。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/hooks/usePracticeAudio.ts](../../../frontend/src/hooks/usePracticeAudio.ts)、[frontend/src/hooks/useUserPreferences.ts](../../../frontend/src/hooks/useUserPreferences.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)；其余 2 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)。
- 处置：保留。

## `frontend/src/components/profile`

### [frontend/src/components/profile/AccountLifecycleSettings.tsx](../../../frontend/src/components/profile/AccountLifecycleSettings.tsx)

可复用 UI：导出/注销/取消注销的后果明确操作；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`DELETION_CHANGED_EVENT`、`notifyDeletionChanged`、`AccountLifecycleSettings`。
- 直接依赖：[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/profile/DeletionBanner.tsx](../../../frontend/src/components/profile/DeletionBanner.tsx)、[frontend/src/components/profile/SettingsTab.tsx](../../../frontend/src/components/profile/SettingsTab.tsx)。
- 处置：保留。

### [frontend/src/components/profile/DeletionBanner.tsx](../../../frontend/src/components/profile/DeletionBanner.tsx)

可复用 UI：注销冷静期提示与恢复入口；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`DeletionBanner`。
- 直接依赖：[frontend/src/components/profile/AccountLifecycleSettings.tsx](../../../frontend/src/components/profile/AccountLifecycleSettings.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)。
- 处置：保留。

### [frontend/src/components/profile/EventDistributionChart.tsx](../../../frontend/src/components/profile/EventDistributionChart.tsx)

可复用 UI：有效学习事件分布图；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Pie`、`PieChart`、`Cell`、`ResponsiveContainer`、`Tooltip`、`EventDistributionItem`、`LABELS`、`EventDistributionChartProps`、`EventDistributionChart`。
- 直接依赖：[frontend/src/lib/chart-theme.ts](../../../frontend/src/lib/chart-theme.ts)。
- 直接使用者：[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)。
- 处置：保留。

### [frontend/src/components/profile/ExternalConnections.tsx](../../../frontend/src/components/profile/ExternalConnections.tsx)

可复用 UI：本人外部凭据/连接管理；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ExternalConnections`。
- 直接依赖：[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/teaching.ts](../../../frontend/src/types/teaching.ts)。
- 直接使用者：[frontend/src/components/profile/SettingsTab.tsx](../../../frontend/src/components/profile/SettingsTab.tsx)。
- 处置：保留。

### [frontend/src/components/profile/InterestPicker.tsx](../../../frontend/src/components/profile/InterestPicker.tsx)

可复用 UI：用户兴趣选择；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`InterestPicker`。
- 直接依赖：[frontend/src/lib/topicCategories.ts](../../../frontend/src/lib/topicCategories.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/onboarding/page.tsx](../../../frontend/src/app/onboarding/page.tsx)、[frontend/src/components/profile/SettingsTab.tsx](../../../frontend/src/components/profile/SettingsTab.tsx)。
- 处置：保留。

### [frontend/src/components/profile/MasteryTrend.tsx](../../../frontend/src/components/profile/MasteryTrend.tsx)

可复用 UI：按需加载掌握趋势图；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`MasteryTrendChart`、`MasteryTrend`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/profile/MasteryTrendChart.tsx](../../../frontend/src/components/profile/MasteryTrendChart.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)。
- 处置：保留。

### [frontend/src/components/profile/MasteryTrendChart.tsx](../../../frontend/src/components/profile/MasteryTrendChart.tsx)

可复用 UI：本人掌握趋势图；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TrendDataPoint`、`MasteryTrendChart`。
- 直接依赖：[frontend/src/lib/chart-theme.ts](../../../frontend/src/lib/chart-theme.ts)。
- 直接使用者：[frontend/src/components/profile/MasteryTrend.tsx](../../../frontend/src/components/profile/MasteryTrend.tsx)。
- 处置：保留。

### [frontend/src/components/profile/ProfileOverview.tsx](../../../frontend/src/components/profile/ProfileOverview.tsx)

可复用 UI：真实学习概览；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Overview`、`ProfileOverview`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)。
- 直接使用者：[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)。
- 处置：保留。

### [frontend/src/components/profile/ProfileTab.tsx](../../../frontend/src/components/profile/ProfileTab.tsx)

可复用 UI：本人资料编辑；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ProfileTabProps`、`ProfileTab`。
- 直接依赖：[frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)、[frontend/src/components/ui/Avatar.tsx](../../../frontend/src/components/ui/Avatar.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/hooks/useSmsCode.ts](../../../frontend/src/hooks/useSmsCode.ts)；其余 5 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)。
- 处置：保留。

### [frontend/src/components/profile/SettingsTab.tsx](../../../frontend/src/components/profile/SettingsTab.tsx)

可复用 UI：个人设置区域编排；所在业务范围为 profile，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SettingsTabProps`、`COMMON_TIMEZONES`、`GOAL_TYPE_LABELS`、`GOAL_UNIT_LABELS`、`REMINDER_TIMES`、`SettingsTab`、`PasswordChangeForm`。
- 直接依赖：[frontend/src/components/exam/TargetExamSetting.tsx](../../../frontend/src/components/exam/TargetExamSetting.tsx)、[frontend/src/components/notifications/NotificationPreferences.tsx](../../../frontend/src/components/notifications/NotificationPreferences.tsx)、[frontend/src/components/profile/AccountLifecycleSettings.tsx](../../../frontend/src/components/profile/AccountLifecycleSettings.tsx)、[frontend/src/components/profile/ExternalConnections.tsx](../../../frontend/src/components/profile/ExternalConnections.tsx)、[frontend/src/components/profile/InterestPicker.tsx](../../../frontend/src/components/profile/InterestPicker.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 9 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)。
- 处置：保留。

## `frontend/src/components/rankings`

### [frontend/src/components/rankings/RankingRow.tsx](../../../frontend/src/components/rankings/RankingRow.tsx)

可复用 UI：排行列表行；所在业务范围为 rankings，事件/数据来自列出的直接依赖。

- 代码入口/类型：`RankingRowMode`、`RANKING_METRIC_LABELS`、`rankClass`、`NEW_WINDOW_MS`、`isFreshPublished`、`RankingRowProps`、`RankingRow`、`RankingRowSkeleton`。
- 直接依赖：[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)、[frontend/src/components/video/VideoThumbnail.tsx](../../../frontend/src/components/video/VideoThumbnail.tsx)、[frontend/src/components/video/VideoTitle.tsx](../../../frontend/src/components/video/VideoTitle.tsx)、[frontend/src/hooks/useRankings.ts](../../../frontend/src/hooks/useRankings.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)；其余 1 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/rankings/page.tsx](../../../frontend/src/app/%28main%29/rankings/page.tsx)、[frontend/src/components/rankings/TopPodium.tsx](../../../frontend/src/components/rankings/TopPodium.tsx)。
- 处置：保留。

### [frontend/src/components/rankings/TopPodium.tsx](../../../frontend/src/components/rankings/TopPodium.tsx)

可复用 UI：排行前三名展示；所在业务范围为 rankings，事件/数据来自列出的直接依赖。

- 代码入口/类型：`rankClass`、`PodiumMetric`、`PodiumCardProps`、`PodiumCard`、`TopPodiumProps`、`TopPodium`。
- 直接依赖：[frontend/src/components/rankings/RankingRow.tsx](../../../frontend/src/components/rankings/RankingRow.tsx)、[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)、[frontend/src/components/video/VideoThumbnail.tsx](../../../frontend/src/components/video/VideoThumbnail.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/rankings/page.tsx](../../../frontend/src/app/%28main%29/rankings/page.tsx)。
- 处置：保留。

## `frontend/src/components/search`

### [frontend/src/components/search/CommandPalette.tsx](../../../frontend/src/components/search/CommandPalette.tsx)

可复用 UI：全局搜索/导航弹层与键盘入口；所在业务范围为 search，事件/数据来自列出的直接依赖。

- 代码入口/类型：`HISTORY_KEY`、`MAX_HISTORY`、`VISIBLE_HISTORY`、`SearchVideo`、`SearchSubtitle`、`SearchWord`、`SearchChannel`、`SearchPayload`、`PublicSubtitleResult`、`CommandKind`（其余见机器清单）。
- 直接依赖：[frontend/src/components/ui/Dialog.tsx](../../../frontend/src/components/ui/Dialog.tsx)、[frontend/src/hooks/useOverlayContainer.ts](../../../frontend/src/hooks/useOverlayContainer.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/navigation.ts](../../../frontend/src/lib/navigation.ts)。
- 直接使用者：[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)。
- 处置：保留。

## `frontend/src/components/subtitle`

### [frontend/src/components/subtitle/WordTooltipInline.tsx](../../../frontend/src/components/subtitle/WordTooltipInline.tsx)

可复用 UI：字幕内部单词提示及词卡入口；所在业务范围为 subtitle，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WordHelpActions`、`parseSenses`、`highlightWord`、`HeaderDrag`、`WordCardBody`、`WordAnchorRect`、`sidebarRightEdge`、`clampCardX`、`clampCardY`、`placementForAnchor`（其余见机器清单）。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/lib/vocabularyPresentation.ts](../../../frontend/src/lib/vocabularyPresentation.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/watch/WordCardSheet.tsx](../../../frontend/src/components/watch/WordCardSheet.tsx)。
- 处置：保留。

## `frontend/src/components/teaching`

### [frontend/src/components/teaching/TeachingCards.tsx](../../../frontend/src/components/teaching/TeachingCards.tsx)

可复用 UI：不同教学卡类型的展示；所在业务范围为 teaching，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TeachingCards`。
- 直接依赖：[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/teaching.ts](../../../frontend/src/lib/teaching.ts)、[frontend/src/types/teaching.ts](../../../frontend/src/types/teaching.ts)。
- 直接使用者：[frontend/src/components/teaching/TeachingWorkspace.tsx](../../../frontend/src/components/teaching/TeachingWorkspace.tsx)。
- 处置：保留。

### [frontend/src/components/teaching/TeachingCatalog.tsx](../../../frontend/src/components/teaching/TeachingCatalog.tsx)

可复用 UI：教学材料和已有会话目录；所在业务范围为 teaching，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TeachingCatalog`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/teaching.ts](../../../frontend/src/lib/teaching.ts)、[frontend/src/types/teaching.ts](../../../frontend/src/types/teaching.ts)。
- 直接使用者：[frontend/src/app/(main)/practice/page.tsx](../../../frontend/src/app/%28main%29/practice/page.tsx)。
- 处置：保留。

### [frontend/src/components/teaching/TeachingQuiz.tsx](../../../frontend/src/components/teaching/TeachingQuiz.tsx)

可复用 UI：四题小测进度与统一写动作；所在业务范围为 teaching，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Props`、`TeachingQuiz`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/types/teaching.ts](../../../frontend/src/types/teaching.ts)。
- 直接使用者：[frontend/src/components/teaching/TeachingWorkspace.tsx](../../../frontend/src/components/teaching/TeachingWorkspace.tsx)。
- 处置：保留。

### [frontend/src/components/teaching/TeachingWorkspace.tsx](../../../frontend/src/components/teaching/TeachingWorkspace.tsx)

可复用 UI：教学卡片、会话、导师消息与恢复编排；所在业务范围为 teaching，事件/数据来自列出的直接依赖。

- 代码入口/类型：`RUN_LABEL`、`TeachingWorkspace`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/common/Spinner.tsx](../../../frontend/src/components/common/Spinner.tsx)、[frontend/src/components/exam/ExamAnswerOptions.tsx](../../../frontend/src/components/exam/ExamAnswerOptions.tsx)、[frontend/src/components/teaching/TeachingCards.tsx](../../../frontend/src/components/teaching/TeachingCards.tsx)、[frontend/src/components/teaching/TeachingQuiz.tsx](../../../frontend/src/components/teaching/TeachingQuiz.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)；其余 7 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/practice/exams/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/%5Bid%5D/page.tsx)。
- 处置：保留。

## `frontend/src/components/transcript`

### [frontend/src/components/transcript/TranscriptDocument.tsx](../../../frontend/src/components/transcript/TranscriptDocument.tsx)

可复用 UI：可点词与定位的整篇字幕文稿；所在业务范围为 transcript，事件/数据来自列出的直接依赖。

- 代码入口/类型：`RAIL_WORD_LIMIT`、`TranscriptDocument`、`PageFrame`、`BackHome`、`SectionBlock`、`SentenceRow`、`TableOfContents`、`WordIndexPanel`。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)；其余 6 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/transcript/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/transcript/page.tsx)。
- 处置：保留。

## `frontend/src/components/ui`

### [frontend/src/components/ui/Avatar.tsx](../../../frontend/src/components/ui/Avatar.tsx)

可复用 UI：统一用户头像与 fallback；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`AvatarSize`、`SIZE`、`Avatar`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/avatar.ts](../../../frontend/src/lib/avatar.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)、[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)、[frontend/src/components/layout/AccountMenu.tsx](../../../frontend/src/components/layout/AccountMenu.tsx)、[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)、[frontend/src/components/profile/ProfileTab.tsx](../../../frontend/src/components/profile/ProfileTab.tsx)。
- 处置：保留。

### [frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)

可复用 UI：通用语义按钮、尺寸、变体与加载态；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ButtonVariant`、`ButtonSize`、`VARIANT`、`SIZE`、`ICON_SIZE`、`Button`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)、[frontend/src/app/(admin)/admin/(shell)/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)；其余 75 项见机器清单。
- 处置：保留。

### [frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)

可复用 UI：统一卡片边界与内间距；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`CardVariant`、`CardPadding`、`VARIANT`、`PADDING`、`Card`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)；其余 32 项见机器清单。
- 处置：保留。

### [frontend/src/components/ui/Dialog.tsx](../../../frontend/src/components/ui/Dialog.tsx)

可复用 UI：可访问模态对话框；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Dialog`、`DialogTrigger`、`DialogPortal`、`DialogClose`、`DialogBackdrop`、`DialogPopup`、`DialogTitle`、`DialogDescription`、`DialogPopupProps`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)、[frontend/src/components/search/CommandPalette.tsx](../../../frontend/src/components/search/CommandPalette.tsx)、[frontend/src/components/watch/WordCardSheet.tsx](../../../frontend/src/components/watch/WordCardSheet.tsx)。
- 处置：保留。

### [frontend/src/components/ui/Drawer.tsx](../../../frontend/src/components/ui/Drawer.tsx)

可复用 UI：移动抽屉及焦点/关闭行为；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Drawer`、`DrawerPortal`、`DrawerVirtualKeyboardProvider`、`DrawerBackdrop`、`DrawerViewport`、`DrawerPopup`、`DrawerContent`、`DrawerTitle`、`DrawerClose`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/watch/WatchMoreSheet.tsx](../../../frontend/src/components/watch/WatchMoreSheet.tsx)。
- 处置：保留。

### [frontend/src/components/ui/DropdownMenu.tsx](../../../frontend/src/components/ui/DropdownMenu.tsx)

可复用 UI：菜单触发和键盘选择；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`DropdownMenu`、`DropdownMenuTrigger`、`DropdownMenuPortal`、`DropdownMenuPositioner`、`DropdownMenuPopup`、`DropdownMenuItem`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/admin/ui/AdminDropdown.tsx](../../../frontend/src/components/admin/ui/AdminDropdown.tsx)。
- 处置：保留。

### [frontend/src/components/ui/FormField.tsx](../../../frontend/src/components/ui/FormField.tsx)

可复用 UI：表单标签、帮助/错误与控件关系；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`FormFieldProps`、`FormField`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/components/lessons/LessonAdmin.tsx](../../../frontend/src/components/lessons/LessonAdmin.tsx)、[frontend/src/components/lessons/LessonTutor.tsx](../../../frontend/src/components/lessons/LessonTutor.tsx)、[frontend/src/components/profile/SettingsTab.tsx](../../../frontend/src/components/profile/SettingsTab.tsx)。
- 处置：保留。

### [frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)

可复用 UI：品牌/远程图片失败回退；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Image`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/page.tsx)；其余 10 项见机器清单。
- 处置：保留。

### [frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)

可复用 UI：输入/文本域公共样式；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Input`、`Textarea`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoDetailRow.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoDetailRow.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)；其余 14 项见机器清单。
- 处置：保留。

### [frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)

可复用 UI：与按钮同构的导航链接；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`LinkButton`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/error.tsx](../../../frontend/src/app/%28main%29/error.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/not-found.tsx](../../../frontend/src/app/%28main%29/not-found.tsx)；其余 24 项见机器清单。
- 处置：保留。

### [frontend/src/components/ui/PageHeader.tsx](../../../frontend/src/components/ui/PageHeader.tsx)

可复用 UI：页面唯一主标题、操作和导航摘要；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`PageHeaderProps`、`PageHeader`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/notifications/page.tsx](../../../frontend/src/app/%28main%29/notifications/page.tsx)；其余 20 项见机器清单。
- 处置：保留。

### [frontend/src/components/ui/Popover.tsx](../../../frontend/src/components/ui/Popover.tsx)

可复用 UI：锚定浮层；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Popover`、`PopoverTrigger`、`PopoverPortal`、`PopoverPositioner`、`PopoverPopup`、`PopoverTitle`、`PopoverClose`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)。
- 处置：保留。

### [frontend/src/components/ui/ProgressRing.tsx](../../../frontend/src/components/ui/ProgressRing.tsx)

可复用 UI：圆环进度呈现；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ProgressRingProps`、`ProgressRing`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)。
- 处置：保留。

### [frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)

可复用 UI：原生选择控件封装；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Select`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoDetailRow.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoDetailRow.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/practice/listening/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/page.tsx)、[frontend/src/components/admin/home/LayoutCandidateSelect.tsx](../../../frontend/src/components/admin/home/LayoutCandidateSelect.tsx)、[frontend/src/components/admin/home/LayoutSlotSections.tsx](../../../frontend/src/components/admin/home/LayoutSlotSections.tsx)；其余 5 项见机器清单。
- 处置：保留。

### [frontend/src/components/ui/SelectMenu.tsx](../../../frontend/src/components/ui/SelectMenu.tsx)

可复用 UI：可访问自定义选单；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SelectMenuOption`、`SelectMenu`。
- 直接依赖：[frontend/src/hooks/useOverlayContainer.ts](../../../frontend/src/hooks/useOverlayContainer.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)。
- 处置：保留。

### [frontend/src/components/ui/TabPills.tsx](../../../frontend/src/components/ui/TabPills.tsx)

可复用 UI：胶囊式筛选入口；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TabItem`、`ActiveStyle`、`TabSize`、`TabVariant`、`TabPillsProps`、`ACTIVE_CLASSES`、`SIZE_CLASSES`、`TabPills`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/rankings/page.tsx](../../../frontend/src/app/%28main%29/rankings/page.tsx)。
- 处置：保留。

### [frontend/src/components/ui/Tabs.tsx](../../../frontend/src/components/ui/Tabs.tsx)

可复用 UI：页签状态与键盘切换；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Tabs`、`TabsList`、`TabsTab`、`TabsPanel`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)、[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)。
- 处置：保留。

### [frontend/src/components/ui/ToggleGroup.tsx](../../../frontend/src/components/ui/ToggleGroup.tsx)

可复用 UI：互斥或多选切换控件；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`ToggleGroupProps`、`ToggleGroup`、`ToggleGroupItem`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/(main)/practice/exams/result/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/result/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/page.tsx)、[frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)。
- 处置：保留。

### [frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)

可复用 UI：统一视频封面卡片与真实元数据；所在业务范围为 ui，事件/数据来自列出的直接依赖。

- 代码入口/类型：`VideoCardData`、`VideoCardProps`、`clickSource`、`VideoCard`、`VideoCardSkeleton`。
- 直接依赖：[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/video/DifficultyBadge.tsx](../../../frontend/src/components/video/DifficultyBadge.tsx)、[frontend/src/components/video/VideoDescription.tsx](../../../frontend/src/components/video/VideoDescription.tsx)、[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)、[frontend/src/components/video/VideoTitle.tsx](../../../frontend/src/components/video/VideoTitle.tsx)；其余 6 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)、[frontend/src/app/(main)/practice/listening/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/page.tsx)、[frontend/src/app/(main)/search/page.tsx](../../../frontend/src/app/%28main%29/search/page.tsx)、[frontend/src/components/channels/ChannelStartCard.tsx](../../../frontend/src/components/channels/ChannelStartCard.tsx)；其余 4 项见机器清单。
- 处置：保留。

## `frontend/src/components/video-edit`

### [frontend/src/components/video-edit/SubtitleEditor.tsx](../../../frontend/src/components/video-edit/SubtitleEditor.tsx)

可复用 UI：管理员逐条字幕文本/时间编辑；所在业务范围为 video-edit，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SubtitleSplitPayload`、`SubtitleEditor`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/components/video-edit/WordLevelsEditor.tsx](../../../frontend/src/components/video-edit/WordLevelsEditor.tsx)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)；其余 2 项见机器清单。
- 直接使用者：[frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx](../../../frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx)。
- 处置：保留。

### [frontend/src/components/video-edit/SubtitleHistory.tsx](../../../frontend/src/components/video-edit/SubtitleHistory.tsx)

可复用 UI：字幕变更历史与回退；所在业务范围为 video-edit，事件/数据来自列出的直接依赖。

- 代码入口/类型：`FIELD_LABELS`、`formatValue`、`SubtitleHistory`。
- 直接依赖：[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx](../../../frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx)。
- 处置：保留。

### [frontend/src/components/video-edit/SubtitleTimeline.tsx](../../../frontend/src/components/video-edit/SubtitleTimeline.tsx)

可复用 UI：编辑时的时间轴；所在业务范围为 video-edit，事件/数据来自列出的直接依赖。

- 代码入口/类型：`PX_PER_SEC`、`RULER_HEIGHT`、`BLOCK_HEIGHT`、`MIN_BLOCK_WIDTH`、`MIN_DURATION`、`EDGE_HANDLE`、`formatTs`、`tickInterval`、`SubtitleTimelineProps`、`DragMode`（其余见机器清单）。
- 直接依赖：[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx](../../../frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx)。
- 处置：保留。

### [frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx](../../../frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx)

可复用 UI：整视频字幕编辑区域编排；所在业务范围为 video-edit，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SubtitleMode`、`MODE_LABEL`、`VideoSubtitleEditorPanelProps`、`VideoSubtitleEditorPanel`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/ui/Select.tsx](../../../frontend/src/components/ui/Select.tsx)、[frontend/src/components/video-edit/SubtitleEditor.tsx](../../../frontend/src/components/video-edit/SubtitleEditor.tsx)、[frontend/src/components/video-edit/SubtitleHistory.tsx](../../../frontend/src/components/video-edit/SubtitleHistory.tsx)、[frontend/src/components/video-edit/SubtitleTimeline.tsx](../../../frontend/src/components/video-edit/SubtitleTimeline.tsx)；其余 8 项见机器清单。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/video-edit/WordLevelsEditor.tsx](../../../frontend/src/components/video-edit/WordLevelsEditor.tsx)

可复用 UI：逐词考试难度修订；所在业务范围为 video-edit，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WordLevelsEditor`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/video-edit/SubtitleEditor.tsx](../../../frontend/src/components/video-edit/SubtitleEditor.tsx)。
- 处置：保留。

## `frontend/src/components/video`

### [frontend/src/components/video/DifficultyBadge.tsx](../../../frontend/src/components/video/DifficultyBadge.tsx)

可复用 UI：语言难度徽章；所在业务范围为 video，事件/数据来自列出的直接依赖。

- 代码入口/类型：`KNOWN_LEVELS`、`BADGE_CLASS`、`DifficultyBadgeProps`、`DifficultyBadge`。
- 直接依赖：[frontend/src/lib/cefrLevels.ts](../../../frontend/src/lib/cefrLevels.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/components/channels/ChannelStartCard.tsx](../../../frontend/src/components/channels/ChannelStartCard.tsx)、[frontend/src/components/channels/ChannelVideoRow.tsx](../../../frontend/src/components/channels/ChannelVideoRow.tsx)、[frontend/src/components/home/FeaturedVideoCard.tsx](../../../frontend/src/components/home/FeaturedVideoCard.tsx)、[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)。
- 处置：保留。

### [frontend/src/components/video/VideoDescription.tsx](../../../frontend/src/components/video/VideoDescription.tsx)

可复用 UI：视频真实简介；所在业务范围为 video，事件/数据来自列出的直接依赖。

- 代码入口/类型：`cleanForPreview`、`VideoDescription`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/channels/ChannelStartCard.tsx](../../../frontend/src/components/channels/ChannelStartCard.tsx)、[frontend/src/components/channels/ChannelVideoRow.tsx](../../../frontend/src/components/channels/ChannelVideoRow.tsx)、[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)。
- 处置：保留。

### [frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)

可复用 UI：视频来源、日期和学习元信息；所在业务范围为 video，事件/数据来自列出的直接依赖。

- 代码入口/类型：`VideoMetadataData`、`VideoMetadata`。
- 直接依赖：[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)、[frontend/src/components/channels/ChannelStartCard.tsx](../../../frontend/src/components/channels/ChannelStartCard.tsx)、[frontend/src/components/channels/ChannelVideoRow.tsx](../../../frontend/src/components/channels/ChannelVideoRow.tsx)、[frontend/src/components/channels/SubscribedChannels.tsx](../../../frontend/src/components/channels/SubscribedChannels.tsx)、[frontend/src/components/home/DiscoverRail.tsx](../../../frontend/src/components/home/DiscoverRail.tsx)；其余 5 项见机器清单。
- 处置：保留。

### [frontend/src/components/video/VideoStats.tsx](../../../frontend/src/components/video/VideoStats.tsx)

可复用 UI：本站播放/赞/收藏统计；所在业务范围为 video，事件/数据来自列出的直接依赖。

- 代码入口/类型：`VideoStats`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/video/VideoStatus.tsx](../../../frontend/src/components/video/VideoStatus.tsx)

可复用 UI：管线状态反馈；所在业务范围为 video，事件/数据来自列出的直接依赖。

- 代码入口/类型：`TEXT_TONE`、`readableTone`、`VideoStatusBadge`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/lib/videoStatus.tsx](../../../frontend/src/lib/videoStatus.tsx)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/[id]/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/video/VideoThumbnail.tsx](../../../frontend/src/components/video/VideoThumbnail.tsx)

可复用 UI：可播放视频封面与回退；所在业务范围为 video，事件/数据来自列出的直接依赖。

- 代码入口/类型：`VideoThumbnailProps`、`gradientFromString`、`initialFromTitle`、`VideoThumbnail`。
- 直接依赖：[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/rankings/RankingRow.tsx](../../../frontend/src/components/rankings/RankingRow.tsx)、[frontend/src/components/rankings/TopPodium.tsx](../../../frontend/src/components/rankings/TopPodium.tsx)。
- 处置：保留。

### [frontend/src/components/video/VideoTitle.tsx](../../../frontend/src/components/video/VideoTitle.tsx)

可复用 UI：统一英文/中文显示标题；所在业务范围为 video，事件/数据来自列出的直接依赖。

- 代码入口/类型：`VideoTitle`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/lib/videoDisplay.ts](../../../frontend/src/lib/videoDisplay.ts)。
- 直接使用者：[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)、[frontend/src/components/channels/ChannelStartCard.tsx](../../../frontend/src/components/channels/ChannelStartCard.tsx)、[frontend/src/components/channels/ChannelVideoRow.tsx](../../../frontend/src/components/channels/ChannelVideoRow.tsx)、[frontend/src/components/channels/SubscribedChannels.tsx](../../../frontend/src/components/channels/SubscribedChannels.tsx)；其余 2 项见机器清单。
- 处置：保留。

## `frontend/src/components/vocabulary`

### [frontend/src/components/vocabulary/DictionaryMeaning.tsx](../../../frontend/src/components/vocabulary/DictionaryMeaning.tsx)

可复用 UI：词典释义的语义结构；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`DictionaryMeaning`。
- 直接依赖：[frontend/src/lib/vocabularyPresentation.ts](../../../frontend/src/lib/vocabularyPresentation.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)、[frontend/src/components/vocabulary/VocabWordCard.tsx](../../../frontend/src/components/vocabulary/VocabWordCard.tsx)、[frontend/src/components/vocabulary/VocabularyToday.tsx](../../../frontend/src/components/vocabulary/VocabularyToday.tsx)、[frontend/src/components/vocabulary/WordFlashcard.tsx](../../../frontend/src/components/vocabulary/WordFlashcard.tsx)。
- 处置：保留。

### [frontend/src/components/vocabulary/HighlightedSentence.tsx](../../../frontend/src/components/vocabulary/HighlightedSentence.tsx)

可复用 UI：保留词来源的原句高亮；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`HighlightedSentence`。
- 直接使用者：[frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/sieve/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/sieve/page.tsx)、[frontend/src/components/vocabulary/VocabularyToday.tsx](../../../frontend/src/components/vocabulary/VocabularyToday.tsx)、[frontend/src/components/vocabulary/WordFlashcard.tsx](../../../frontend/src/components/vocabulary/WordFlashcard.tsx)。
- 处置：保留。

### [frontend/src/components/vocabulary/LessonWordSources.tsx](../../../frontend/src/components/vocabulary/LessonWordSources.tsx)

可复用 UI：课程修订来源投影与不可用状态；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`LessonWordSources`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/lessons.ts](../../../frontend/src/lib/lessons.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/app/(main)/vocabulary/review/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/review/page.tsx)。
- 处置：保留。

### [frontend/src/components/vocabulary/SetEditor.tsx](../../../frontend/src/components/vocabulary/SetEditor.tsx)

可复用 UI：词集名称与成员编辑；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`Candidate`、`SetEditor`。
- 直接依赖：[frontend/src/components/common/ConfirmDialog.tsx](../../../frontend/src/components/common/ConfirmDialog.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Input.tsx](../../../frontend/src/components/ui/Input.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/vocabulary/TrainSummary.tsx](../../../frontend/src/components/vocabulary/TrainSummary.tsx)

可复用 UI：训练结束结果和下一步；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WeakWord`、`TrainSummary`。
- 直接依赖：[frontend/src/components/common/Confetti.tsx](../../../frontend/src/components/common/Confetti.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)。
- 处置：保留。

### [frontend/src/components/vocabulary/VocabOverview.tsx](../../../frontend/src/components/vocabulary/VocabOverview.tsx)

可复用 UI：词汇统计与学习状态摘要；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`VocabOverview`。
- 直接依赖：[frontend/src/components/common/SkeletonCard.tsx](../../../frontend/src/components/common/SkeletonCard.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)。
- 处置：保留。

### [frontend/src/components/vocabulary/VocabWordCard.tsx](../../../frontend/src/components/vocabulary/VocabWordCard.tsx)

可复用 UI：词条、释义、来源与个人掌握动作；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`VocabWordCard`、`VocabWordAction`。
- 直接依赖：[frontend/src/components/common/Badge.tsx](../../../frontend/src/components/common/Badge.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/vocabulary/DictionaryMeaning.tsx](../../../frontend/src/components/vocabulary/DictionaryMeaning.tsx)、[frontend/src/lib/vocabularyPresentation.ts](../../../frontend/src/lib/vocabularyPresentation.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/sieve/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/sieve/page.tsx)。
- 处置：保留。

### [frontend/src/components/vocabulary/VocabularyToday.tsx](../../../frontend/src/components/vocabulary/VocabularyToday.tsx)

可复用 UI：今日词汇训练入口；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`VocabularyToday`。
- 直接依赖：[frontend/src/components/common/EmptyState.tsx](../../../frontend/src/components/common/EmptyState.tsx)、[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/LinkButton.tsx](../../../frontend/src/components/ui/LinkButton.tsx)、[frontend/src/components/vocabulary/DictionaryMeaning.tsx](../../../frontend/src/components/vocabulary/DictionaryMeaning.tsx)、[frontend/src/components/vocabulary/HighlightedSentence.tsx](../../../frontend/src/components/vocabulary/HighlightedSentence.tsx)；其余 6 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)。
- 处置：保留。

### [frontend/src/components/vocabulary/WordFlashcard.tsx](../../../frontend/src/components/vocabulary/WordFlashcard.tsx)

可复用 UI：词汇回忆/揭晓/自评交互；所在业务范围为 vocabulary，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WordQuizCard`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/components/ui/Card.tsx](../../../frontend/src/components/ui/Card.tsx)、[frontend/src/components/vocabulary/DictionaryMeaning.tsx](../../../frontend/src/components/vocabulary/DictionaryMeaning.tsx)、[frontend/src/components/vocabulary/HighlightedSentence.tsx](../../../frontend/src/components/vocabulary/HighlightedSentence.tsx)、[frontend/src/hooks/useSpeech.ts](../../../frontend/src/hooks/useSpeech.ts)、[frontend/src/lib/drillQuestions.ts](../../../frontend/src/lib/drillQuestions.ts)；其余 2 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)。
- 处置：保留。

## `frontend/src/components/watch`

### [frontend/src/components/watch/CurrentSentenceCard.tsx](../../../frontend/src/components/watch/CurrentSentenceCard.tsx)

可复用 UI：手机/桌面当前句字幕、点词和句操作；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SUBTITLE_FONT_EN_MOBILE`、`SUBTITLE_FONT_ZH_MOBILE`、`SUBTITLE_FONT_EN_DESKTOP`、`SUBTITLE_FONT_ZH_DESKTOP`、`SUBTITLE_LINE_HEIGHT`、`CurrentSentenceCard`。
- 直接依赖：[frontend/src/components/watch/VideoControls.tsx](../../../frontend/src/components/watch/VideoControls.tsx)、[frontend/src/hooks/useMediaQuery.ts](../../../frontend/src/hooks/useMediaQuery.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/watch/ExamLevelSelector.tsx](../../../frontend/src/components/watch/ExamLevelSelector.tsx)

可复用 UI：观看时考试词级别筛选；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`PANEL_WIDTH`、`ExamLevelSelector`。
- 直接依赖：[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/hooks/useWatchChromeBridge.tsx](../../../frontend/src/hooks/useWatchChromeBridge.tsx)。
- 处置：保留。

### [frontend/src/components/watch/LearningActions.tsx](../../../frontend/src/components/watch/LearningActions.tsx)

可复用 UI：当前句学习动作与可用状态；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`LearningActions`。
- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/watch/PublishedVideoEditorial.tsx](../../../frontend/src/components/watch/PublishedVideoEditorial.tsx)

可复用 UI：视频已发布编辑内容展示；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`PublishedVideoEditorial`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)、[frontend/src/lib/homeEditorial.ts](../../../frontend/src/lib/homeEditorial.ts)、[frontend/src/lib/watchClip.ts](../../../frontend/src/lib/watchClip.ts)、[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)；其余 1 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/watch/RelatedVideos.tsx](../../../frontend/src/components/watch/RelatedVideos.tsx)

可复用 UI：当前视频相关推荐；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`RelatedVideos`。
- 直接依赖：[frontend/src/components/common/ErrorState.tsx](../../../frontend/src/components/common/ErrorState.tsx)、[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/watch/SaveSentenceButton.tsx](../../../frontend/src/components/watch/SaveSentenceButton.tsx)

可复用 UI：句子收藏动作；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SaveSentenceButton`。
- 直接依赖：[frontend/src/components/ui/Button.tsx](../../../frontend/src/components/ui/Button.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/watch/SheetHandle.tsx](../../../frontend/src/components/watch/SheetHandle.tsx)

可复用 UI：手机抽屉拖动手柄；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SHEET_CLOSE_DRAG_PX`、`SheetHandle`。
- 直接使用者：[frontend/src/components/watch/WatchMoreSheet.tsx](../../../frontend/src/components/watch/WatchMoreSheet.tsx)、[frontend/src/components/watch/WordCardSheet.tsx](../../../frontend/src/components/watch/WordCardSheet.tsx)。
- 处置：保留。

### [frontend/src/components/watch/VideoControls.tsx](../../../frontend/src/components/watch/VideoControls.tsx)

可复用 UI：播放器播放/速度/定位等常用操作；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`SubtitleFontSize`、`FONT_SIZE_LABEL`、`HIDE_DELAY_MS`、`VideoControlsProps`、`VideoControls`。
- 直接依赖：[frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)、[frontend/src/lib/subtitleModes.ts](../../../frontend/src/lib/subtitleModes.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)、[frontend/src/stores/watchStore.ts](../../../frontend/src/stores/watchStore.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/watch/CurrentSentenceCard.tsx](../../../frontend/src/components/watch/CurrentSentenceCard.tsx)、[frontend/src/components/watch/WatchMoreSheet.tsx](../../../frontend/src/components/watch/WatchMoreSheet.tsx)、[frontend/src/hooks/useWatchPreferences.ts](../../../frontend/src/hooks/useWatchPreferences.ts)。
- 处置：保留。

### [frontend/src/components/watch/WatchBottomBar.tsx](../../../frontend/src/components/watch/WatchBottomBar.tsx)

可复用 UI：手机观看常驻控制条；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WatchBottomBar`、`WATCH_BOTTOM_BAR_HEIGHT`、`WatchBottomBarMobile`、`formatClock`。
- 直接依赖：[frontend/src/components/watch/WatchChromeProvider.tsx](../../../frontend/src/components/watch/WatchChromeProvider.tsx)、[frontend/src/hooks/useMediaQuery.ts](../../../frontend/src/hooks/useMediaQuery.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 直接使用者：[frontend/src/components/watch/WatchChromeProvider.tsx](../../../frontend/src/components/watch/WatchChromeProvider.tsx)。
- 处置：保留。

### [frontend/src/components/watch/WatchChromeProvider.tsx](../../../frontend/src/components/watch/WatchChromeProvider.tsx)

可复用 UI：观看控制条与全站壳层的桥接上下文；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WatchChromeState`、`ChromeContext`、`PublishContext`、`WatchChromeProvider`、`usePublishWatchChrome`、`WatchShellControls`。
- 直接依赖：[frontend/src/components/watch/WatchBottomBar.tsx](../../../frontend/src/components/watch/WatchBottomBar.tsx)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)、[frontend/src/components/watch/WatchBottomBar.tsx](../../../frontend/src/components/watch/WatchBottomBar.tsx)、[frontend/src/hooks/useWatchChromeBridge.tsx](../../../frontend/src/hooks/useWatchChromeBridge.tsx)。
- 处置：保留。

### [frontend/src/components/watch/WatchDivider.tsx](../../../frontend/src/components/watch/WatchDivider.tsx)

可复用 UI：桌面观看区域尺寸分隔与交互；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WatchDivider`。
- 直接依赖：[frontend/src/lib/watchLayout.ts](../../../frontend/src/lib/watchLayout.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/watch/WatchMoreSheet.tsx](../../../frontend/src/components/watch/WatchMoreSheet.tsx)

可复用 UI：不常用观看操作的移动选单；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WatchMoreSheet`、`Row`、`Chip`。
- 直接依赖：[frontend/src/components/ui/Drawer.tsx](../../../frontend/src/components/ui/Drawer.tsx)、[frontend/src/components/watch/SheetHandle.tsx](../../../frontend/src/components/watch/SheetHandle.tsx)、[frontend/src/components/watch/VideoControls.tsx](../../../frontend/src/components/watch/VideoControls.tsx)、[frontend/src/hooks/useOverlayContainer.ts](../../../frontend/src/hooks/useOverlayContainer.ts)、[frontend/src/lib/subtitleModes.ts](../../../frontend/src/lib/subtitleModes.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)；其余 1 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/watch/WatchSourceCard.tsx](../../../frontend/src/components/watch/WatchSourceCard.tsx)

可复用 UI：原片来源与简介/订阅；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`WatchSourceCard`。
- 直接依赖：[frontend/src/components/channels/ChannelSubscribeButton.tsx](../../../frontend/src/components/channels/ChannelSubscribeButton.tsx)、[frontend/src/components/ui/Image.tsx](../../../frontend/src/components/ui/Image.tsx)、[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/avatar.ts](../../../frontend/src/lib/avatar.ts)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)；其余 3 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/components/watch/WordCardSheet.tsx](../../../frontend/src/components/watch/WordCardSheet.tsx)

可复用 UI：观看页词卡与底部播放器间的抽屉几何约束；所在业务范围为 watch，事件/数据来自列出的直接依赖。

- 代码入口/类型：`MIN_SHEET_HEIGHT`、`WordCardSheet`。
- 直接依赖：[frontend/src/components/subtitle/WordTooltipInline.tsx](../../../frontend/src/components/subtitle/WordTooltipInline.tsx)、[frontend/src/components/ui/Dialog.tsx](../../../frontend/src/components/ui/Dialog.tsx)、[frontend/src/components/watch/SheetHandle.tsx](../../../frontend/src/components/watch/SheetHandle.tsx)、[frontend/src/hooks/useOverlayContainer.ts](../../../frontend/src/hooks/useOverlayContainer.ts)、[frontend/src/hooks/useSheetGeometry.ts](../../../frontend/src/hooks/useSheetGeometry.ts)、[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)；其余 1 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

## `frontend/src/hooks`

### [frontend/src/hooks/useContinueLearning.ts](../../../frontend/src/hooks/useContinueLearning.ts)

React Hook：本人继续观看数据；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`ContinueItem`、`ContinueResponse`、`continueRequest`、`ContinueLearningState`、`useContinueLearning`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/sharedRequest.ts](../../../frontend/src/lib/sharedRequest.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)、[frontend/src/components/home/DiscoverRail.tsx](../../../frontend/src/components/home/DiscoverRail.tsx)。
- 处置：保留。

### [frontend/src/hooks/useDailySession.ts](../../../frontend/src/hooks/useDailySession.ts)

React Hook：每日词汇轮次获取和恢复；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`DailySessionTotals`、`DailySession`、`useDailySession`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)、[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/components/vocabulary/VocabularyToday.tsx](../../../frontend/src/components/vocabulary/VocabularyToday.tsx)。
- 处置：保留。

### [frontend/src/hooks/useDeepLink.ts](../../../frontend/src/hooks/useDeepLink.ts)

React Hook：字幕/时间 URL 深链定位；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`DeepLinkArgs`、`useDeepLink`。
- 直接依赖：[frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)、[frontend/src/lib/subtitles.ts](../../../frontend/src/lib/subtitles.ts)、[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useHomeLayoutEditor.ts](../../../frontend/src/hooks/useHomeLayoutEditor.ts)

React Hook：管理员首页布局草稿状态与写入；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`ConfirmState`、`PlacementUpdater`、`useHomeLayoutEditor`、`HomeLayoutEditorModel`。
- 直接依赖：[frontend/src/lib/adminHomeContent.ts](../../../frontend/src/lib/adminHomeContent.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)。
- 处置：保留。

### [frontend/src/hooks/useLessonAvailability.ts](../../../frontend/src/hooks/useLessonAvailability.ts)

React Hook：课程版本可用性轮询/撤回响应；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useLessonAvailability`。
- 直接依赖：[frontend/src/lib/lessons.ts](../../../frontend/src/lib/lessons.ts)。
- 直接使用者：[frontend/src/components/admin/AdminSidebar.tsx](../../../frontend/src/components/admin/AdminSidebar.tsx)、[frontend/src/components/layout/AccountMenu.tsx](../../../frontend/src/components/layout/AccountMenu.tsx)、[frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx)。
- 处置：保留。

### [frontend/src/hooks/useLessonYouTube.ts](../../../frontend/src/hooks/useLessonYouTube.ts)

React Hook：课程 YouTube 嵌入与失败回退；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`PlayerState`、`useLessonYouTube`。
- 直接依赖：[frontend/src/lib/youtubePlayer.ts](../../../frontend/src/lib/youtubePlayer.ts)。
- 直接使用者：[frontend/src/components/lessons/LessonReader.tsx](../../../frontend/src/components/lessons/LessonReader.tsx)。
- 处置：保留。

### [frontend/src/hooks/useMediaQuery.ts](../../../frontend/src/hooks/useMediaQuery.ts)

React Hook：响应式媒体查询订阅；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useMediaQuery`。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/layout/AccountMenu.tsx](../../../frontend/src/components/layout/AccountMenu.tsx)、[frontend/src/components/watch/CurrentSentenceCard.tsx](../../../frontend/src/components/watch/CurrentSentenceCard.tsx)、[frontend/src/components/watch/WatchBottomBar.tsx](../../../frontend/src/components/watch/WatchBottomBar.tsx)。
- 处置：保留。

### [frontend/src/hooks/useModalFocus.ts](../../../frontend/src/hooks/useModalFocus.ts)

React Hook：浮层焦点圈定和退出恢复；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useModalFocus`。
- 直接使用者：[frontend/src/components/admin/ui/AdminDialog.tsx](../../../frontend/src/components/admin/ui/AdminDialog.tsx)。
- 处置：保留。

### [frontend/src/hooks/useOverlayContainer.ts](../../../frontend/src/hooks/useOverlayContainer.ts)

React Hook：浮层在主题/壳范围内的挂载容器；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useOverlayContainer`。
- 直接使用者：[frontend/src/components/admin/ui/AdminDropdown.tsx](../../../frontend/src/components/admin/ui/AdminDropdown.tsx)、[frontend/src/components/common/Modal.tsx](../../../frontend/src/components/common/Modal.tsx)、[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)、[frontend/src/components/search/CommandPalette.tsx](../../../frontend/src/components/search/CommandPalette.tsx)、[frontend/src/components/ui/SelectMenu.tsx](../../../frontend/src/components/ui/SelectMenu.tsx)、[frontend/src/components/watch/WatchMoreSheet.tsx](../../../frontend/src/components/watch/WatchMoreSheet.tsx)；其余 1 项见机器清单。
- 处置：保留。

### [frontend/src/hooks/usePaginatedList.test.ts](../../../frontend/src/hooks/usePaginatedList.test.ts)

Vitest 规则回归：分页读取、刷新、追加和取消生命周期。断言主题：nextPageToLoad；advances one page after a successful load；retries the failed page instead of skipping past it。

- 直接依赖：[frontend/src/hooks/usePaginatedList.ts](../../../frontend/src/hooks/usePaginatedList.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/hooks/usePaginatedList.ts](../../../frontend/src/hooks/usePaginatedList.ts)

React Hook：分页读取、刷新、追加和取消生命周期；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`PaginationMode`、`UsePaginatedListOptions`、`UsePaginatedListReturn`、`nextPageToLoad`、`usePaginatedList`。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/notifications/page.tsx](../../../frontend/src/app/%28main%29/notifications/page.tsx)、[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)；其余 2 项见机器清单。
- 处置：保留。

### [frontend/src/hooks/usePlan.ts](../../../frontend/src/hooks/usePlan.ts)

React Hook：学习档案/掌握趋势加载，不是付费套餐；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`usePlan`。
- 直接依赖：[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)、[frontend/src/stores/planStore.ts](../../../frontend/src/stores/planStore.ts)。
- 直接使用者：[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/usePlatformFeed.ts](../../../frontend/src/hooks/usePlatformFeed.ts)

React Hook：主题视频流分页；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`SORT_VALUES`、`FeedSort`、`FEED_SORT_OPTIONS`、`isFeedSort`、`BROWSE_SORT_PARAM`、`browseSortParam`、`DEFAULT_SORT`、`CategoryResponse`、`TOPIC_TABS`、`FALLBACK_CATEGORIES`（其余见机器清单）。
- 直接依赖：[frontend/src/hooks/usePaginatedList.ts](../../../frontend/src/hooks/usePaginatedList.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/cefrLevels.ts](../../../frontend/src/lib/cefrLevels.ts)、[frontend/src/lib/topicCategories.ts](../../../frontend/src/lib/topicCategories.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)、[frontend/src/types/platform.ts](../../../frontend/src/types/platform.ts)。
- 直接使用者：[frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)。
- 处置：保留。

### [frontend/src/hooks/usePractice.ts](../../../frontend/src/hooks/usePractice.ts)

React Hook：词汇练习加载、提交和恢复；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`normalizeWord`、`gradePracticeItem`、`UseVocabularyPracticeOptions`、`UseVocabularyPracticeReturn`、`useVocabularyPractice`。
- 直接依赖：[frontend/src/hooks/useSession.ts](../../../frontend/src/hooks/useSession.ts)、[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/usePracticeAudio.ts](../../../frontend/src/hooks/usePracticeAudio.ts)

React Hook：练习发音/片段音频生命周期；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`UsePracticeAudioReturn`、`usePracticeAudio`。
- 直接依赖：[frontend/src/hooks/useSpeech.ts](../../../frontend/src/hooks/useSpeech.ts)。
- 直接使用者：[frontend/src/components/practice/PracticePanels.tsx](../../../frontend/src/components/practice/PracticePanels.tsx)。
- 处置：保留。

### [frontend/src/hooks/useRankings.ts](../../../frontend/src/hooks/useRankings.ts)

React Hook：榜单数据请求；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`RankingScope`、`UseRankingsReturn`、`useRankings`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/rankings/page.tsx](../../../frontend/src/app/%28main%29/rankings/page.tsx)、[frontend/src/components/rankings/RankingRow.tsx](../../../frontend/src/components/rankings/RankingRow.tsx)。
- 处置：保留。

### [frontend/src/hooks/useRequireAuth.ts](../../../frontend/src/hooks/useRequireAuth.ts)

React Hook：客户端受保护入口与加载态；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`UseRequireAuthOptions`、`UseRequireAuthReturn`、`useRequireAuth`、`UseRedirectIfAuthenticatedReturn`、`useRedirectIfAuthenticated`。
- 直接依赖：[frontend/src/lib/authHelpers.ts](../../../frontend/src/lib/authHelpers.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)。
- 直接使用者：[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/notifications/page.tsx](../../../frontend/src/app/%28main%29/notifications/page.tsx)、[frontend/src/app/(main)/practice/exams/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/practice/exams/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/page.tsx)、[frontend/src/app/(main)/practice/exams/redo/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/redo/page.tsx)；其余 15 项见机器清单。
- 处置：保留。

### [frontend/src/hooks/useScrollRestore.ts](../../../frontend/src/hooks/useScrollRestore.ts)

React Hook：路由滚动位置恢复；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`RESTORE_HITS`、`RESTORE_TIMEOUT_MS`、`SAVE_THROTTLE_MS`、`useScrollRestore`、`watchContainer`。
- 直接依赖：[frontend/src/lib/scrollMemory.ts](../../../frontend/src/lib/scrollMemory.ts)。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/rankings/page.tsx](../../../frontend/src/app/%28main%29/rankings/page.tsx)、[frontend/src/app/(main)/search/page.tsx](../../../frontend/src/app/%28main%29/search/page.tsx)、[frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)。
- 处置：保留。

### [frontend/src/hooks/useSession.ts](../../../frontend/src/hooks/useSession.ts)

React Hook：从当前 store 读取会话；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`SessionItem`、`SessionGradedResult`、`SessionFetcher`、`SessionGrader`、`UseSessionReturn`、`UseSessionOptions`、`useSession`。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/hooks/usePractice.ts](../../../frontend/src/hooks/usePractice.ts)。
- 处置：保留。

### [frontend/src/hooks/useSheetGeometry.ts](../../../frontend/src/hooks/useSheetGeometry.ts)

React Hook：词卡/抽屉和播放器边界的几何计算；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`SheetGeometry`、`TAB_BAR_SELECTOR`、`PLAYBACK_BAR_SELECTOR`、`FALLBACK_HEIGHT`、`MIN_SHEET_HEIGHT`、`useSheetGeometry`。
- 直接使用者：[frontend/src/components/watch/WordCardSheet.tsx](../../../frontend/src/components/watch/WordCardSheet.tsx)。
- 处置：保留。

### [frontend/src/hooks/useSmsCode.ts](../../../frontend/src/hooks/useSmsCode.ts)

React Hook：短信发码、倒计时和失败反馈；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useSmsCode`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/lib/smsCode.ts](../../../frontend/src/lib/smsCode.ts)。
- 直接使用者：[frontend/src/app/forgot-password/page.tsx](../../../frontend/src/app/forgot-password/page.tsx)、[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)、[frontend/src/components/profile/ProfileTab.tsx](../../../frontend/src/components/profile/ProfileTab.tsx)。
- 处置：保留。

### [frontend/src/hooks/useSpeech.ts](../../../frontend/src/hooks/useSpeech.ts)

React Hook：浏览器语音/发音播放；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`UseSpeechOptions`、`UseSpeechReturn`、`useSpeech`。
- 直接使用者：[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/app/(main)/vocabulary/review/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/review/page.tsx)、[frontend/src/components/vocabulary/VocabularyToday.tsx](../../../frontend/src/components/vocabulary/VocabularyToday.tsx)、[frontend/src/components/vocabulary/WordFlashcard.tsx](../../../frontend/src/components/vocabulary/WordFlashcard.tsx)、[frontend/src/hooks/usePracticeAudio.ts](../../../frontend/src/hooks/usePracticeAudio.ts)、[frontend/src/hooks/useWordLookup.ts](../../../frontend/src/hooks/useWordLookup.ts)。
- 处置：保留。

### [frontend/src/hooks/useStickyPip.ts](../../../frontend/src/hooks/useStickyPip.ts)

React Hook：手机滚动时播放器画中画状态；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`StickyPipResult`、`useStickyPip`。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useStudySession.ts](../../../frontend/src/hooks/useStudySession.ts)

React Hook：持久词汇训练轮次的答题/结束与恢复；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`SessionEnvelope`、`AnswerResponse`、`EMPTY_TODAY`、`useStudySession`。
- 直接依赖：[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useSubtitleFollow.ts](../../../frontend/src/hooks/useSubtitleFollow.ts)

React Hook：播放当前句与用户手动滚动协作；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`SubtitleFollowArgs`、`SubtitleFollowResult`、`useSubtitleFollow`。
- 直接依赖：[frontend/src/lib/scrollMemory.ts](../../../frontend/src/lib/scrollMemory.ts)、[frontend/src/lib/subtitleFollow.ts](../../../frontend/src/lib/subtitleFollow.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useTheme.ts](../../../frontend/src/hooks/useTheme.ts)

React Hook：站内主题偏好及系统主题订阅；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`Theme`、`getSystemTheme`、`getStoredTheme`、`applyThemeClass`、`useTheme`。
- 直接使用者：[frontend/src/components/common/ThemeProvider.tsx](../../../frontend/src/components/common/ThemeProvider.tsx)。
- 处置：保留。

### [frontend/src/hooks/useUserPreferences.ts](../../../frontend/src/hooks/useUserPreferences.ts)

React Hook：本人偏好获取和更新；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useUserPreferences`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/exam/TargetExamSetting.tsx](../../../frontend/src/components/exam/TargetExamSetting.tsx)、[frontend/src/components/practice/PracticePanels.tsx](../../../frontend/src/components/practice/PracticePanels.tsx)。
- 处置：保留。

### [frontend/src/hooks/useVideoMeta.ts](../../../frontend/src/hooks/useVideoMeta.ts)

React Hook：当前视频详情、点赞/收藏/笔记等元数据；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`getVideoLikeStatus`、`toggleVideoLike`、`useVideoMeta`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)

React Hook：本地/YouTube 播放器、倍速、循环、句末与释放生命周期；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`PlaybackMode`、`PLAYBACK_RATES`、`RATE_STORAGE_KEY`、`loadPersistedRate`、`bestVideoUrl`、`youtubeId`、`canPlay`、`isIOS`、`UseVideoPlayerOptions`、`UseVideoPlayerReturn`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/mediaLifecycle.ts](../../../frontend/src/lib/mediaLifecycle.ts)、[frontend/src/lib/subtitleModes.ts](../../../frontend/src/lib/subtitleModes.ts)、[frontend/src/lib/watchProgressQueue.ts](../../../frontend/src/lib/watchProgressQueue.ts)、[frontend/src/lib/watchSession.ts](../../../frontend/src/lib/watchSession.ts)、[frontend/src/lib/youtubePlayer.ts](../../../frontend/src/lib/youtubePlayer.ts)；其余 2 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx](../../../frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx)、[frontend/src/components/watch/VideoControls.tsx](../../../frontend/src/components/watch/VideoControls.tsx)、[frontend/src/hooks/useDeepLink.ts](../../../frontend/src/hooks/useDeepLink.ts)。
- 处置：保留。

### [frontend/src/hooks/useVideoPolling.ts](../../../frontend/src/hooks/useVideoPolling.ts)

React Hook：视频处理进度轮询；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useVideoPolling`。
- 直接依赖：[frontend/src/hooks/useVideoStatusPolling.ts](../../../frontend/src/hooks/useVideoStatusPolling.ts)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoDetailRow.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoDetailRow.tsx)。
- 处置：保留。

### [frontend/src/hooks/useVideoStatusPolling.ts](../../../frontend/src/hooks/useVideoStatusPolling.ts)

React Hook：可见性约束的状态轮询；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`VideoStatusPatch`、`UseVideoStatusPollingOptions`、`useVideoStatusPolling`。
- 直接依赖：[frontend/src/lib/videoStatus.tsx](../../../frontend/src/lib/videoStatus.tsx)。
- 直接使用者：[frontend/src/hooks/useVideoPolling.ts](../../../frontend/src/hooks/useVideoPolling.ts)。
- 处置：保留。

### [frontend/src/hooks/useVisibilityAwareInterval.ts](../../../frontend/src/hooks/useVisibilityAwareInterval.ts)

React Hook：页面隐藏时暂停的定时刷新；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useVisibilityAwareInterval`。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/components/admin/AdminTopbar.tsx](../../../frontend/src/components/admin/AdminTopbar.tsx)、[frontend/src/components/layout/UnreadCountSync.tsx](../../../frontend/src/components/layout/UnreadCountSync.tsx)。
- 处置：保留。

### [frontend/src/hooks/useVocabSetDetail.ts](../../../frontend/src/hooks/useVocabSetDetail.ts)

React Hook：词集详情请求和个人状态；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`UseVocabSetDetailReturn`、`useVocabSetDetail`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/sieve/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/sieve/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useVocabSets.ts](../../../frontend/src/hooks/useVocabSets.ts)

React Hook：词集列表和刷新；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`UseVocabSetsReturn`、`useVocabSets`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useVocabSieve.ts](../../../frontend/src/hooks/useVocabSieve.ts)

React Hook：词汇过筛进度、判断和恢复；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`UseVocabSieveReturn`、`useVocabSieve`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/sets/[id]/sieve/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/sieve/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useWatchChromeBridge.tsx](../../../frontend/src/hooks/useWatchChromeBridge.tsx)

React Hook：观看页操作绑定到壳层手机控制条；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`WatchChromeBridgeArgs`、`useWatchChromeBridge`。
- 直接依赖：[frontend/src/components/watch/ExamLevelSelector.tsx](../../../frontend/src/components/watch/ExamLevelSelector.tsx)、[frontend/src/components/watch/WatchChromeProvider.tsx](../../../frontend/src/components/watch/WatchChromeProvider.tsx)、[frontend/src/lib/cefrLevels.ts](../../../frontend/src/lib/cefrLevels.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useWatchClip.ts](../../../frontend/src/hooks/useWatchClip.ts)

React Hook：观看片段的跳转和停止；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useWatchClip`。
- 直接依赖：[frontend/src/lib/homeEditorial.ts](../../../frontend/src/lib/homeEditorial.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useWatchLayout.ts](../../../frontend/src/hooks/useWatchLayout.ts)

React Hook：观看画框/分栏尺寸和持久偏好；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`useWatchLayout`。
- 直接依赖：[frontend/src/lib/watchLayout.ts](../../../frontend/src/lib/watchLayout.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useWatchPreferences.ts](../../../frontend/src/hooks/useWatchPreferences.ts)

React Hook：字幕、播放等观看偏好；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`FONT_SIZES`、`DEFAULT_EXAM_LEVEL`、`Options`、`WatchPreferences`、`useWatchPreferences`。
- 直接依赖：[frontend/src/components/watch/VideoControls.tsx](../../../frontend/src/components/watch/VideoControls.tsx)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useWatchVocabulary.ts](../../../frontend/src/hooks/useWatchVocabulary.ts)

React Hook：观看页收词、词集和学习上下文；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`WatchVocabSet`、`WatchContextResponse`、`Options`、`WatchVocabulary`、`useWatchVocabulary`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)、[frontend/src/lib/watchWordHighlight.ts](../../../frontend/src/lib/watchWordHighlight.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useWatchWordCard.ts](../../../frontend/src/hooks/useWatchWordCard.ts)

React Hook：词卡选择、开启/关闭和复习入口；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`WordAnchorRect`、`Options`、`WatchWordCard`、`useWatchWordCard`。
- 直接依赖：[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)、[frontend/src/lib/watchWordSource.ts](../../../frontend/src/lib/watchWordSource.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

### [frontend/src/hooks/useWordLookup.ts](../../../frontend/src/hooks/useWordLookup.ts)

React Hook：当前词来源的查义请求和加载错误；封装有状态的请求/订阅/生命周期供调用组件复用。

- 代码入口/类型：`Options`、`useWordLookup`。
- 直接依赖：[frontend/src/hooks/useSpeech.ts](../../../frontend/src/hooks/useSpeech.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)。
- 处置：保留。

## `frontend/src/lib`

### [frontend/src/lib/adminApi.ts](../../../frontend/src/lib/adminApi.ts)

前端共享工具：独立管理员会话的 API 实例；实际导出 AdminApiError、getApiUrl、adminAuthAdapter、client、adminApi，上游页面/Hook 共用。

- 代码入口/类型：`AdminApiError`、`getApiUrl`、`adminAuthAdapter`、`client`、`adminApi`。
- 直接依赖：[frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)、[frontend/src/app/(admin)/admin/login/page.tsx](../../../frontend/src/app/%28admin%29/admin/login/page.tsx)、[frontend/src/components/lessons/LessonAdmin.tsx](../../../frontend/src/components/lessons/LessonAdmin.tsx)、[frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)、[frontend/src/lib/adminHomeContent.ts](../../../frontend/src/lib/adminHomeContent.ts)、[frontend/src/lib/lessons.ts](../../../frontend/src/lib/lessons.ts)。
- 处置：保留。

### [frontend/src/lib/adminData.ts](../../../frontend/src/lib/adminData.ts)

前端共享工具：管理页面数据格式与状态辅助；实际导出 getAdminStats、getLearningMetrics、listUsers、setUserBanned、promoteUser、getWorkerStatus、getUgcPendingCount、startProcessing、recoverVideo，上游页面/Hook 共用。

- 代码入口/类型：`getAdminStats`、`getLearningMetrics`、`listUsers`、`setUserBanned`、`promoteUser`、`getWorkerStatus`、`getUgcPendingCount`、`startProcessing`、`recoverVideo`、`retryVideo`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/adminApi.ts](../../../frontend/src/lib/adminApi.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)；其余 8 项见机器清单。
- 处置：保留。

### [frontend/src/lib/adminHomeContent.ts](../../../frontend/src/lib/adminHomeContent.ts)

前端共享工具：管理员首页草稿/版本/布局 API；实际导出 BASE、HomeContentGenerateResult、HomeContentPublishResult、HomeLayoutRevisionResult、HOME_CONTENT_REVISION_CONFLICT、HOME_CONTENT_OVERWRITE_CONFIRM、REVISION_CONFLICT_MESSAGE、ApiErrorLike、isApiErrorWithCode，上游页面/Hook 共用。

- 代码入口/类型：`BASE`、`HomeContentGenerateResult`、`HomeContentPublishResult`、`HomeLayoutRevisionResult`、`HOME_CONTENT_REVISION_CONFLICT`、`HOME_CONTENT_OVERWRITE_CONFIRM`、`REVISION_CONFLICT_MESSAGE`、`ApiErrorLike`、`isApiErrorWithCode`、`apiErrorStatus`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/adminApi.ts](../../../frontend/src/lib/adminApi.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)。
- 直接使用者：[frontend/src/components/admin/home/HomeContentPanel.tsx](../../../frontend/src/components/admin/home/HomeContentPanel.tsx)、[frontend/src/components/admin/home/HomeLayoutEditor.tsx](../../../frontend/src/components/admin/home/HomeLayoutEditor.tsx)、[frontend/src/hooks/useHomeLayoutEditor.ts](../../../frontend/src/hooks/useHomeLayoutEditor.ts)。
- 处置：更新必要说明/引用或生成路径。

### [frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)

前端共享工具：前端行为/学习意图事件、去重 ID、批次与退出冲刷；实际导出 EVENT_SCHEMA_VERSION、BehaviorEvent、QUEUE、FLUSH_INTERVAL_MS、MAX_QUEUE、MAX_RETAINED_QUEUE、makeSessionId、SESSION_ID、makeEventId，上游页面/Hook 共用。

- 代码入口/类型：`EVENT_SCHEMA_VERSION`、`BehaviorEvent`、`QUEUE`、`FLUSH_INTERVAL_MS`、`MAX_QUEUE`、`MAX_RETAINED_QUEUE`、`makeSessionId`、`SESSION_ID`、`makeEventId`、`flushTimer`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/watchTime.ts](../../../frontend/src/lib/watchTime.ts)、[frontend/src/lib/webVitals.ts](../../../frontend/src/lib/webVitals.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)。
- 直接使用者：[frontend/src/app/(main)/practice/listening/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)、[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/app/onboarding/page.tsx](../../../frontend/src/app/onboarding/page.tsx)、[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)；其余 5 项见机器清单。
- 处置：保留。

### [frontend/src/lib/analyticsContract.test.ts](../../../frontend/src/lib/analyticsContract.test.ts)

Vitest 规则回归：前端行为/学习意图事件、去重 ID、批次与退出冲刷。断言主题：behavior event contract；上报契约版本与后端一致（v3）；词卡重听配对窗口与后端 GLOSS_REPLAY_WINDOW_SECONDS 一致。

- 直接依赖：[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/analyticsGloss.test.ts](../../../frontend/src/lib/analyticsGloss.test.ts)

Vitest 规则回归：前端行为/学习意图事件、去重 ID、批次与退出冲刷。断言主题：gloss_open → replay 配对；窗口内且同一句 → 配对；超出 10 秒窗口 → 不配对。

- 直接依赖：[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)

前端共享工具：用户 API 实例和分领域请求方法、媒体 URL 归一；实际导出 API_URL、ApiError、getApiUrl、PROXY_HOST_SUFFIXES、shouldProxyHost、mediaUrl、getToken、userAuthAdapter、client，上游页面/Hook 共用。

- 代码入口/类型：`API_URL`、`ApiError`、`getApiUrl`、`PROXY_HOST_SUFFIXES`、`shouldProxyHost`、`mediaUrl`、`getToken`、`userAuthAdapter`、`client`、`ApiOptions`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)、[frontend/src/lib/publicError.ts](../../../frontend/src/lib/publicError.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoDetailRow.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoDetailRow.tsx)、[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)、[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)；其余 80 项见机器清单。
- 处置：保留。

### [frontend/src/lib/authHelpers.test.ts](../../../frontend/src/lib/authHelpers.test.ts)

Vitest 规则回归：用户/管理会话双存储唯一写入及安全回跳。断言主题：hasAuthCookieMirror；没有 document（SSR / node）时判为缺失；cookie 为空串时判为缺失。

- 代码入口/类型：`stubCookie`、`FakeStorage`、`stubBrowser`。
- 直接依赖：[frontend/src/lib/authHelpers.ts](../../../frontend/src/lib/authHelpers.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/authHelpers.ts](../../../frontend/src/lib/authHelpers.ts)

前端共享工具：用户/管理会话双存储唯一写入及安全回跳；实际导出 BaseAuthUser、migrateTokenKeys、deriveAuthenticated、AUTH_COOKIE_NAME、hasAuthCookieMirror、syncAuthCookie、SessionKeys、USER_SESSION_KEYS、ADMIN_SESSION_KEYS，上游页面/Hook 共用。

- 代码入口/类型：`BaseAuthUser`、`migrateTokenKeys`、`deriveAuthenticated`、`AUTH_COOKIE_NAME`、`hasAuthCookieMirror`、`syncAuthCookie`、`SessionKeys`、`USER_SESSION_KEYS`、`ADMIN_SESSION_KEYS`、`setSession`（其余见机器清单）。
- 直接使用者：[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)、[frontend/src/app/set-password/page.tsx](../../../frontend/src/app/set-password/page.tsx)、[frontend/src/components/auth/RedirectStuckState.tsx](../../../frontend/src/components/auth/RedirectStuckState.tsx)、[frontend/src/hooks/useRequireAuth.ts](../../../frontend/src/hooks/useRequireAuth.ts)、[frontend/src/lib/authHelpers.test.ts](../../../frontend/src/lib/authHelpers.test.ts)；其余 2 项见机器清单。
- 处置：保留。

### [frontend/src/lib/avatar.test.ts](../../../frontend/src/lib/avatar.test.ts)

Vitest 规则回归：头像地址归一和默认品牌素材。断言主题：avatarColor；keeps the mapping users already have；gives one seed one colour。

- 直接依赖：[frontend/src/lib/avatar.ts](../../../frontend/src/lib/avatar.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/avatar.ts](../../../frontend/src/lib/avatar.ts)

前端共享工具：头像地址归一和默认品牌素材；实际导出 AVATAR_COLORS、AvatarGender、AVATAR_GENDERS、DEFAULT_AVATAR_URL、hashSeed、avatarColor、defaultAvatarUrl、userInitial，上游页面/Hook 共用。

- 代码入口/类型：`AVATAR_COLORS`、`AvatarGender`、`AVATAR_GENDERS`、`DEFAULT_AVATAR_URL`、`hashSeed`、`avatarColor`、`defaultAvatarUrl`、`userInitial`。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)、[frontend/src/components/channels/SubscribedChannels.tsx](../../../frontend/src/components/channels/SubscribedChannels.tsx)、[frontend/src/components/home/HomeSubscribedChannels.tsx](../../../frontend/src/components/home/HomeSubscribedChannels.tsx)、[frontend/src/components/profile/ProfileTab.tsx](../../../frontend/src/components/profile/ProfileTab.tsx)、[frontend/src/components/ui/Avatar.tsx](../../../frontend/src/components/ui/Avatar.tsx)；其余 3 项见机器清单。
- 处置：保留。

### [frontend/src/lib/cefrLevels.ts](../../../frontend/src/lib/cefrLevels.ts)

前端共享工具：语言难度显示与考试提示；实际导出 CEFR_LEVELS、CefrLevel、isCefrLevel、CEFR_EXAM_EQUIVALENT、cefrExamHint、cefrWithExamHint，上游页面/Hook 共用。

- 代码入口/类型：`CEFR_LEVELS`、`CefrLevel`、`isCefrLevel`、`CEFR_EXAM_EQUIVALENT`、`cefrExamHint`、`cefrWithExamHint`。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/app/onboarding/page.tsx](../../../frontend/src/app/onboarding/page.tsx)、[frontend/src/components/home/HomeFeed.tsx](../../../frontend/src/components/home/HomeFeed.tsx)、[frontend/src/components/video/DifficultyBadge.tsx](../../../frontend/src/components/video/DifficultyBadge.tsx)、[frontend/src/hooks/usePlatformFeed.ts](../../../frontend/src/hooks/usePlatformFeed.ts)、[frontend/src/hooks/useWatchChromeBridge.tsx](../../../frontend/src/hooks/useWatchChromeBridge.tsx)。
- 处置：保留。

### [frontend/src/lib/channelLearning.test.ts](../../../frontend/src/lib/channelLearning.test.ts)

Vitest 规则回归：频道学习方向/难度与起学信息展示。断言主题：formatDifficultyRange；formats a real CEFR range and a single level；returns null when the server has no usable range。

- 代码入口/类型：`rachel`、`bare`。
- 直接依赖：[frontend/src/lib/channelLearning.ts](../../../frontend/src/lib/channelLearning.ts)、[frontend/src/types/channels.ts](../../../frontend/src/types/channels.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/channelLearning.ts](../../../frontend/src/lib/channelLearning.ts)

前端共享工具：频道学习方向/难度与起学信息展示；实际导出 CEFR_ORDER、DIRECTION_SEARCH_ALIASES、formatDifficultyRange、formatCollectedVideos、directionLabels、channelSearchText、channelMatchesQuery、latestVideoMeta、formatMonthDay，上游页面/Hook 共用。

- 代码入口/类型：`CEFR_ORDER`、`DIRECTION_SEARCH_ALIASES`、`formatDifficultyRange`、`formatCollectedVideos`、`directionLabels`、`channelSearchText`、`channelMatchesQuery`、`latestVideoMeta`、`formatMonthDay`。
- 直接依赖：[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)、[frontend/src/types/channels.ts](../../../frontend/src/types/channels.ts)。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)、[frontend/src/lib/channelLearning.test.ts](../../../frontend/src/lib/channelLearning.test.ts)。
- 处置：保留。

### [frontend/src/lib/channelSubscriptions.ts](../../../frontend/src/lib/channelSubscriptions.ts)

前端共享工具：订阅请求和跨组件状态同步；实际导出 SubscriptionsPayload、channelSubscriptionsRequest，上游页面/Hook 共用。

- 代码入口/类型：`SubscriptionsPayload`、`channelSubscriptionsRequest`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/sharedRequest.ts](../../../frontend/src/lib/sharedRequest.ts)、[frontend/src/types/channels.ts](../../../frontend/src/types/channels.ts)。
- 直接使用者：[frontend/src/components/home/DiscoverRail.tsx](../../../frontend/src/components/home/DiscoverRail.tsx)、[frontend/src/components/home/HomeSubscribedChannels.tsx](../../../frontend/src/components/home/HomeSubscribedChannels.tsx)。
- 处置：保留。

### [frontend/src/lib/chart-theme.ts](../../../frontend/src/lib/chart-theme.ts)

前端共享工具：现有图表读取语义 CSS 变量的主题适配；实际导出 ChartTheme、LIGHT、DARK、useChartTheme，上游页面/Hook 共用。

- 代码入口/类型：`ChartTheme`、`LIGHT`、`DARK`、`useChartTheme`。
- 直接依赖：[frontend/src/components/common/ThemeProvider.tsx](../../../frontend/src/components/common/ThemeProvider.tsx)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)、[frontend/src/components/admin/GrowthTrendChart.tsx](../../../frontend/src/components/admin/GrowthTrendChart.tsx)、[frontend/src/components/admin/StatsCharts.tsx](../../../frontend/src/components/admin/StatsCharts.tsx)、[frontend/src/components/profile/EventDistributionChart.tsx](../../../frontend/src/components/profile/EventDistributionChart.tsx)、[frontend/src/components/profile/MasteryTrendChart.tsx](../../../frontend/src/components/profile/MasteryTrendChart.tsx)。
- 处置：保留。

### [frontend/src/lib/createApiClient.test.ts](../../../frontend/src/lib/createApiClient.test.ts)

Vitest 规则回归：身份隔离 GET 去重/缓存、请求期限、5xx 重试、401 刷新与 envelope 解析。断言主题：createApiClient 401 handling；unauthenticated 401 surfaces the server message and leaves the session alone；authenticated 401 still refreshes, then expires the session when refresh fails。

- 代码入口/类型：`makeToken`、`liveToken`、`expiredToken`、`jsonResponse`、`WRONG_PASSWORD`、`AdapterSpy`、`makeAdapter`、`clientWith`、`scopedClientWith`、`loginRequest`。
- 直接依赖：[frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)

前端共享工具：身份隔离 GET 去重/缓存、请求期限、5xx 重试、401 刷新与 envelope 解析；实际导出 MAX_RETRIES、RETRY_DELAYS_MS、isRetryableStatus、sleep、DEFAULT_REQUEST_TIMEOUT_MS、Deadline、withDeadline、AuthAdapter、ApiClientError，上游页面/Hook 共用。

- 代码入口/类型：`MAX_RETRIES`、`RETRY_DELAYS_MS`、`isRetryableStatus`、`sleep`、`DEFAULT_REQUEST_TIMEOUT_MS`、`Deadline`、`withDeadline`、`AuthAdapter`、`ApiClientError`、`CreateApiClientOptions`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/jwt.ts](../../../frontend/src/lib/jwt.ts)、[frontend/src/lib/sessionRefresh.ts](../../../frontend/src/lib/sessionRefresh.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/components/lessons/LessonAdmin.tsx](../../../frontend/src/components/lessons/LessonAdmin.tsx)、[frontend/src/components/lessons/LessonCatalog.tsx](../../../frontend/src/components/lessons/LessonCatalog.tsx)、[frontend/src/components/lessons/LessonReader.tsx](../../../frontend/src/components/lessons/LessonReader.tsx)、[frontend/src/lib/adminApi.ts](../../../frontend/src/lib/adminApi.ts)；其余 2 项见机器清单。
- 处置：保留。

### [frontend/src/lib/date.ts](../../../frontend/src/lib/date.ts)

前端共享工具：日期输入/显示归一；实际导出 relativeTime、formatTimeSpent、DateGroup、groupByDate，上游页面/Hook 共用。

- 代码入口/类型：`relativeTime`、`formatTimeSpent`、`DateGroup`、`groupByDate`。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)。
- 处置：保留。

### [frontend/src/lib/drillQuestions.test.ts](../../../frontend/src/lib/drillQuestions.test.ts)

Vitest 规则回归：词汇练习题型、选项和答案纯规则。断言主题：conciseTranslation；取释义首行，多行只留一行；空释义返回空串。

- 代码入口/类型：`seq`、`GLOSSES`、`word`、`zeroRand`。
- 直接依赖：[frontend/src/lib/drillQuestions.ts](../../../frontend/src/lib/drillQuestions.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/drillQuestions.ts](../../../frontend/src/lib/drillQuestions.ts)

前端共享工具：词汇练习题型、选项和答案纯规则；实际导出 DrillQuestionKind、DRILL_KIND_LABEL、DrillQuestion、OPTION_COUNT、MIN_DISTRACTORS、POS_ALIASES、conciseTranslation、questionKindForAppearance、posTokens，上游页面/Hook 共用。

- 代码入口/类型：`DrillQuestionKind`、`DRILL_KIND_LABEL`、`DrillQuestion`、`OPTION_COUNT`、`MIN_DISTRACTORS`、`POS_ALIASES`、`conciseTranslation`、`questionKindForAppearance`、`posTokens`、`sharesPos`（其余见机器清单）。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)、[frontend/src/components/vocabulary/WordFlashcard.tsx](../../../frontend/src/components/vocabulary/WordFlashcard.tsx)、[frontend/src/lib/drillQuestions.test.ts](../../../frontend/src/lib/drillQuestions.test.ts)。
- 处置：保留。

### [frontend/src/lib/drillRound.test.ts](../../../frontend/src/lib/drillRound.test.ts)

Vitest 规则回归：单词训练轮次的判定和恢复规则。断言主题：nextAppearanceFromItem (S3 落库 → 出现次序)；pending 词下一次是第 1 次；答对一次（streak=1）下一次是第 2 次。

- 代码入口/类型：`seq`、`word`、`item`、`drive`。
- 直接依赖：[frontend/src/lib/drillRound.ts](../../../frontend/src/lib/drillRound.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/drillRound.ts](../../../frontend/src/lib/drillRound.ts)

前端共享工具：单词训练轮次的判定和恢复规则；实际导出 GRADUATE_STREAK、GAP_AFTER_WRONG、GAP_AFTER_CORRECT、DrillEntrySource、DrillEntry、DrillSchedulerState、AnswerOutcome、nextAppearanceFromItem、buildDrillScheduler，上游页面/Hook 共用。

- 代码入口/类型：`GRADUATE_STREAK`、`GAP_AFTER_WRONG`、`GAP_AFTER_CORRECT`、`DrillEntrySource`、`DrillEntry`、`DrillSchedulerState`、`AnswerOutcome`、`nextAppearanceFromItem`、`buildDrillScheduler`、`applyAnswer`（其余见机器清单）。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)、[frontend/src/lib/drillRound.test.ts](../../../frontend/src/lib/drillRound.test.ts)。
- 处置：保留。

### [frontend/src/lib/errors.ts](../../../frontend/src/lib/errors.ts)

前端共享工具：统一 API 错误到用户反馈转换；实际导出 apiErrorMessage、toastApiError，上游页面/Hook 共用。

- 代码入口/类型：`apiErrorMessage`、`toastApiError`。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/feedback/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/feedback/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)；其余 37 项见机器清单。
- 处置：保留。

### [frontend/src/lib/examLevels.generated.ts](../../../frontend/src/lib/examLevels.generated.ts)

前端共享工具：由后端权威生成的考试等级表，不手改；实际导出 GeneratedExamLevel、EXAM_LEVEL_TAXONOMY、TARGET_LEVEL_KEYS，上游页面/Hook 共用。

- 代码入口/类型：`GeneratedExamLevel`、`EXAM_LEVEL_TAXONOMY`、`TARGET_LEVEL_KEYS`。
- 直接使用者：[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)。
- 处置：保留。

### [frontend/src/lib/examLevels.test.ts](../../../frontend/src/lib/examLevels.test.ts)

Vitest 规则回归：考试词难度展示与后端规则镜像。断言主题：generated taxonomy covers the frontend's color maps；every level has a color token with a non-empty highlight class；offers the annotation-only levels as targets to nobody。

- 直接依赖：[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)

前端共享工具：考试词难度展示与后端规则镜像；实际导出 ExamLevelMeta、LEVEL_COLORS、LEVEL_BY_KEY、EXAM_LEVELS、TARGET_LEVEL_OPTIONS、levelMeta、levelOrder、maxLevel、shouldDisplay，上游页面/Hook 共用。

- 代码入口/类型：`ExamLevelMeta`、`LEVEL_COLORS`、`LEVEL_BY_KEY`、`EXAM_LEVELS`、`TARGET_LEVEL_OPTIONS`、`levelMeta`、`levelOrder`、`maxLevel`、`shouldDisplay`、`displayLevel`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/examLevels.generated.ts](../../../frontend/src/lib/examLevels.generated.ts)。
- 直接使用者：[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/page.tsx)、[frontend/src/components/exam/TargetExamSetting.tsx](../../../frontend/src/components/exam/TargetExamSetting.tsx)、[frontend/src/components/subtitle/WordTooltipInline.tsx](../../../frontend/src/components/subtitle/WordTooltipInline.tsx)、[frontend/src/components/transcript/TranscriptDocument.tsx](../../../frontend/src/components/transcript/TranscriptDocument.tsx)；其余 7 项见机器清单。
- 处置：保留。

### [frontend/src/lib/examPresentation.test.ts](../../../frontend/src/lib/examPresentation.test.ts)

Vitest 规则回归：试卷分区、题型与作答结果的展示规则。断言主题：exam presentation；keeps the word bank selectable and separate from the passage；groups only the same section and passage and preserves paragraph letters。

- 代码入口/类型：`question`。
- 直接依赖：[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/lib/examPresentation.ts](../../../frontend/src/lib/examPresentation.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/examPresentation.ts](../../../frontend/src/lib/examPresentation.ts)

前端共享工具：试卷分区、题型与作答结果的展示规则；实际导出 SECTION_LABELS、WORD_BANK_MARKER、DerivedOptions、deriveOptions、stripWordBank、MISSING_SPACE_RE、normalizePassageSpacing、QuestionGroup、buildGroups，上游页面/Hook 共用。

- 代码入口/类型：`SECTION_LABELS`、`WORD_BANK_MARKER`、`DerivedOptions`、`deriveOptions`、`stripWordBank`、`MISSING_SPACE_RE`、`normalizePassageSpacing`、`QuestionGroup`、`buildGroups`、`paperIdentity`（其余见机器清单）。
- 直接依赖：[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/lib/examSubjects.ts](../../../frontend/src/lib/examSubjects.ts)。
- 直接使用者：[frontend/src/app/(main)/practice/exams/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/practice/exams/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/page.tsx)、[frontend/src/app/(main)/practice/exams/redo/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/redo/page.tsx)、[frontend/src/app/(main)/practice/exams/result/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/result/%5Bid%5D/page.tsx)、[frontend/src/components/exam/ExamRunner.tsx](../../../frontend/src/components/exam/ExamRunner.tsx)、[frontend/src/lib/examPresentation.test.ts](../../../frontend/src/lib/examPresentation.test.ts)。
- 处置：保留。

### [frontend/src/lib/examSubjects.ts](../../../frontend/src/lib/examSubjects.ts)

前端共享工具：考试科目显示信息；实际导出 EXAM_SUBJECTS、subjectLabel、subjectOrder、PAPER_LEVELS，上游页面/Hook 共用。

- 代码入口/类型：`EXAM_SUBJECTS`、`subjectLabel`、`subjectOrder`、`PAPER_LEVELS`。
- 直接使用者：[frontend/src/app/(main)/practice/daily/page.tsx](../../../frontend/src/app/%28main%29/practice/daily/page.tsx)、[frontend/src/app/(main)/practice/exams/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/page.tsx)、[frontend/src/app/(main)/practice/page.tsx](../../../frontend/src/app/%28main%29/practice/page.tsx)、[frontend/src/lib/examPresentation.ts](../../../frontend/src/lib/examPresentation.ts)。
- 处置：保留。

### [frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)

前端共享工具：时间、时长和数量统一格式化；实际导出 formatTime、formatDuration、timeAgo、formatRelativeDay、formatCount、formatViews、formatMonthDay，上游页面/Hook 共用。

- 代码入口/类型：`formatTime`、`formatDuration`、`timeAgo`、`formatRelativeDay`、`formatCount`、`formatViews`、`formatMonthDay`。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)、[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/admin/StatsCharts.tsx](../../../frontend/src/components/admin/StatsCharts.tsx)、[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)；其余 20 项见机器清单。
- 处置：保留。

### [frontend/src/lib/formatCount.test.ts](../../../frontend/src/lib/formatCount.test.ts)

Vitest 规则回归：数量显示回归。断言主题：shared count presentation；distinguishes zero, unknown and invalid values；uses consistent Chinese and English units without trailing decimals。

- 直接依赖：[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/homeEditorial.test.ts](../../../frontend/src/lib/homeEditorial.test.ts)

Vitest 规则回归：首页编辑 DTO 到渲染与来源深链的纯投影。断言主题：fetchHomeEditorial；reads the public endpoint and returns the published page；maps an unpublished/empty layout to null so the home page can fall back。

- 代码入口/类型：`videoCard`、`sentence`、`expression`、`content`、`slot`、`page`。
- 直接依赖：[frontend/src/lib/homeEditorial.ts](../../../frontend/src/lib/homeEditorial.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/homeEditorial.ts](../../../frontend/src/lib/homeEditorial.ts)

前端共享工具：首页编辑 DTO 到渲染与来源深链的纯投影；实际导出 HOME_EDITORIAL_ENDPOINT、VideoMedia、ClipPlayback、WordPlayback、HighlightSegment、VocabularyEntry、fetchHomeEditorial、normalizeHomeEditorial、mediaSource，上游页面/Hook 共用。

- 代码入口/类型：`HOME_EDITORIAL_ENDPOINT`、`VideoMedia`、`ClipPlayback`、`WordPlayback`、`HighlightSegment`、`VocabularyEntry`、`fetchHomeEditorial`、`normalizeHomeEditorial`、`mediaSource`、`clipPlayback`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)、[frontend/src/components/watch/PublishedVideoEditorial.tsx](../../../frontend/src/components/watch/PublishedVideoEditorial.tsx)、[frontend/src/hooks/useWatchClip.ts](../../../frontend/src/hooks/useWatchClip.ts)、[frontend/src/lib/homeEditorial.test.ts](../../../frontend/src/lib/homeEditorial.test.ts)。
- 处置：更新必要说明/引用或生成路径。

### [frontend/src/lib/jwt.test.ts](../../../frontend/src/lib/jwt.test.ts)

Vitest 规则回归：浏览器 JWT 载荷与有效期解析，不替代后端验签。断言主题：decodeJwt；decodes a valid payload；returns null for malformed tokens。

- 代码入口/类型：`makeToken`。
- 直接依赖：[frontend/src/lib/jwt.ts](../../../frontend/src/lib/jwt.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/jwt.ts](../../../frontend/src/lib/jwt.ts)

前端共享工具：浏览器 JWT 载荷与有效期解析，不替代后端验签；实际导出 JwtPayload、base64UrlDecode、decodeJwt、isTokenExpired，上游页面/Hook 共用。

- 代码入口/类型：`JwtPayload`、`base64UrlDecode`、`decodeJwt`、`isTokenExpired`。
- 直接使用者：[frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)、[frontend/src/lib/jwt.test.ts](../../../frontend/src/lib/jwt.test.ts)、[frontend/src/lib/teachingStream.ts](../../../frontend/src/lib/teachingStream.ts)、[frontend/src/stores/adminAuthStore.ts](../../../frontend/src/stores/adminAuthStore.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)。
- 处置：保留。

### [frontend/src/lib/lessons.test.ts](../../../frontend/src/lib/lessons.test.ts)

Vitest 规则回归：课程 API、材料/修订和来源锚点处理。断言主题：lesson reader primitives；slices text by Unicode code point offsets, not UTF-16 units；resolves a consecutive anchor to its own text and word timing。

- 代码入口/类型：`pack`。
- 直接依赖：[frontend/src/lib/lessons.ts](../../../frontend/src/lib/lessons.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/lessons.ts](../../../frontend/src/lib/lessons.ts)

前端共享工具：课程 API、材料/修订和来源锚点处理；实际导出 LessonAccessMode、LessonRevisionStatus、LessonTimeRange、LessonToken、LessonSegment、LessonVocabulary、LessonProvenance、LessonPack、LessonSummary，上游页面/Hook 共用。

- 代码入口/类型：`LessonAccessMode`、`LessonRevisionStatus`、`LessonTimeRange`、`LessonToken`、`LessonSegment`、`LessonVocabulary`、`LessonProvenance`、`LessonPack`、`LessonSummary`、`LessonDetail`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/adminApi.ts](../../../frontend/src/lib/adminApi.ts)、[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)。
- 直接使用者：[frontend/src/components/lessons/LessonAdmin.tsx](../../../frontend/src/components/lessons/LessonAdmin.tsx)、[frontend/src/components/lessons/LessonCatalog.tsx](../../../frontend/src/components/lessons/LessonCatalog.tsx)、[frontend/src/components/lessons/LessonReader.tsx](../../../frontend/src/components/lessons/LessonReader.tsx)、[frontend/src/components/lessons/LessonTutor.tsx](../../../frontend/src/components/lessons/LessonTutor.tsx)、[frontend/src/components/vocabulary/LessonWordSources.tsx](../../../frontend/src/components/vocabulary/LessonWordSources.tsx)、[frontend/src/hooks/useLessonAvailability.ts](../../../frontend/src/hooks/useLessonAvailability.ts)；其余 1 项见机器清单。
- 处置：保留。

### [frontend/src/lib/listeningMode.test.ts](../../../frontend/src/lib/listeningMode.test.ts)

Vitest 规则回归：听力模式/状态切换规则。断言主题：listening practice mode；未知值与缺失值都回落成听音默写；合法模式原样保留。

- 代码入口/类型：`stubStorage`。
- 直接依赖：[frontend/src/lib/listeningMode.ts](../../../frontend/src/lib/listeningMode.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/listeningMode.ts](../../../frontend/src/lib/listeningMode.ts)

前端共享工具：听力模式/状态切换规则；实际导出 ListeningMode、DEFAULT_LISTENING_MODE、LISTENING_MODE_STORAGE_KEY、LISTENING_MODES、normalizeListeningMode、listeningModeMeta、loadListeningMode、saveListeningMode，上游页面/Hook 共用。

- 代码入口/类型：`ListeningMode`、`DEFAULT_LISTENING_MODE`、`LISTENING_MODE_STORAGE_KEY`、`LISTENING_MODES`、`normalizeListeningMode`、`listeningModeMeta`、`loadListeningMode`、`saveListeningMode`。
- 直接使用者：[frontend/src/app/(main)/practice/listening/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/%5Bid%5D/page.tsx)、[frontend/src/lib/listeningMode.test.ts](../../../frontend/src/lib/listeningMode.test.ts)。
- 处置：保留。

### [frontend/src/lib/mediaLifecycle.test.ts](../../../frontend/src/lib/mediaLifecycle.test.ts)

Vitest 规则回归：媒体监听/释放和恢复顺序辅助。断言主题：mediaStateFor；播放/结束/错误是直接映射；暂停在播完之后是 ended，否则是 paused。

- 代码入口/类型：`playing`、`paused`、`ended`。
- 直接依赖：[frontend/src/lib/mediaLifecycle.ts](../../../frontend/src/lib/mediaLifecycle.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/mediaLifecycle.ts](../../../frontend/src/lib/mediaLifecycle.ts)

前端共享工具：媒体监听/释放和恢复顺序辅助；实际导出 MediaUiState、MediaLifecycleEvent、MediaFacts、mediaStateFor、youTubeEventFor，上游页面/Hook 共用。

- 代码入口/类型：`MediaUiState`、`MediaLifecycleEvent`、`MediaFacts`、`mediaStateFor`、`youTubeEventFor`。
- 直接使用者：[frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)、[frontend/src/lib/mediaLifecycle.test.ts](../../../frontend/src/lib/mediaLifecycle.test.ts)。
- 处置：保留。

### [frontend/src/lib/navigation.test.ts](../../../frontend/src/lib/navigation.test.ts)

Vitest 规则回归：当前导航匹配与入口规则。断言主题：导航项：一级 5 项 + 资料库 3 项；MAIN_NAV 恰好 5 项，href 顺序固定；SECONDARY_NAV 恰好 3 项，href 顺序固定。

- 代码入口/类型：`ALL_NAV`、`activeHrefs`、`allScopes`。
- 直接依赖：[frontend/src/lib/navigation.ts](../../../frontend/src/lib/navigation.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/navigation.ts](../../../frontend/src/lib/navigation.ts)

前端共享工具：当前导航匹配与入口规则；实际导出 NavItem、MAIN_NAV、SECONDARY_NAV、ACTIVE_SCOPE、inScope、navigationActive，上游页面/Hook 共用。

- 代码入口/类型：`NavItem`、`MAIN_NAV`、`SECONDARY_NAV`、`ACTIVE_SCOPE`、`inScope`、`navigationActive`。
- 直接使用者：[frontend/src/components/layout/MobileTabBar.tsx](../../../frontend/src/components/layout/MobileTabBar.tsx)、[frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx)、[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)、[frontend/src/components/search/CommandPalette.tsx](../../../frontend/src/components/search/CommandPalette.tsx)、[frontend/src/lib/navigation.test.ts](../../../frontend/src/lib/navigation.test.ts)。
- 处置：保留。

### [frontend/src/lib/password.test.ts](../../../frontend/src/lib/password.test.ts)

Vitest 规则回归：密码 UTF-8 字节限制的客户端反馈。断言主题：isPasswordAcceptable；字符规则与后端一致：至少 8 位、含大小写与数字；限制的是 UTF-8 字节而不是字符（bcrypt 的前 72 字节）。

- 代码入口/类型：`SAMPLES`。
- 直接依赖：[frontend/src/lib/password.ts](../../../frontend/src/lib/password.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/password.ts](../../../frontend/src/lib/password.ts)

前端共享工具：密码 UTF-8 字节限制的客户端反馈；实际导出 PASSWORD_RE、PASSWORD_MAX_BYTES、PASSWORD_RULE_MESSAGE、PASSWORD_HINT、passwordByteLength、isPasswordAcceptable、passwordStrength，上游页面/Hook 共用。

- 代码入口/类型：`PASSWORD_RE`、`PASSWORD_MAX_BYTES`、`PASSWORD_RULE_MESSAGE`、`PASSWORD_HINT`、`passwordByteLength`、`isPasswordAcceptable`、`passwordStrength`。
- 直接使用者：[frontend/src/app/forgot-password/page.tsx](../../../frontend/src/app/forgot-password/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)、[frontend/src/app/set-password/page.tsx](../../../frontend/src/app/set-password/page.tsx)、[frontend/src/components/auth/PasswordField.tsx](../../../frontend/src/components/auth/PasswordField.tsx)、[frontend/src/components/profile/SettingsTab.tsx](../../../frontend/src/components/profile/SettingsTab.tsx)、[frontend/src/lib/password.test.ts](../../../frontend/src/lib/password.test.ts)。
- 处置：保留。

### [frontend/src/lib/publicError.test.ts](../../../frontend/src/lib/publicError.test.ts)

Vitest 规则回归：安全用户错误文案投影。断言主题：用户可见错误；保留可执行的业务提示；隐藏内部诊断：%s。

- 直接依赖：[frontend/src/lib/publicError.ts](../../../frontend/src/lib/publicError.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/publicError.ts](../../../frontend/src/lib/publicError.ts)

前端共享工具：安全用户错误文案投影；实际导出 publicErrorMessage，上游页面/Hook 共用。

- 代码入口/类型：`publicErrorMessage`。
- 直接使用者：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/publicError.test.ts](../../../frontend/src/lib/publicError.test.ts)。
- 处置：保留。

### [frontend/src/lib/reviewRating.ts](../../../frontend/src/lib/reviewRating.ts)

前端共享工具：认识/模糊/不认识到复习质量分值映射；实际导出 ReviewRating、REVIEW_RATINGS、QUALITY、qualityFor、ratingForKey，上游页面/Hook 共用。

- 代码入口/类型：`ReviewRating`、`REVIEW_RATINGS`、`QUALITY`、`qualityFor`、`ratingForKey`。
- 直接使用者：[frontend/src/app/(main)/vocabulary/review/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/review/page.tsx)。
- 处置：保留。

### [frontend/src/lib/scrollMemory.ts](../../../frontend/src/lib/scrollMemory.ts)

前端共享工具：路由滚动位置的本地记忆；实际导出 SCROLL_CONTAINER_ID、KEY_PREFIX、scrollKey、loadScroll、saveScroll，上游页面/Hook 共用。

- 代码入口/类型：`SCROLL_CONTAINER_ID`、`KEY_PREFIX`、`scrollKey`、`loadScroll`、`saveScroll`。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)、[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/rankings/page.tsx](../../../frontend/src/app/%28main%29/rankings/page.tsx)、[frontend/src/app/(main)/search/page.tsx](../../../frontend/src/app/%28main%29/search/page.tsx)；其余 4 项见机器清单。
- 处置：保留。

### [frontend/src/lib/sessionRefresh.ts](../../../frontend/src/lib/sessionRefresh.ts)

前端共享工具：按成功/过期/暂不可用分类的续签协调；实际导出 RefreshOutcome、TokenPair、RefreshResult、REFRESH_TIMEOUT_MS、requestTokenRefresh，上游页面/Hook 共用。

- 代码入口/类型：`RefreshOutcome`、`TokenPair`、`RefreshResult`、`REFRESH_TIMEOUT_MS`、`requestTokenRefresh`。
- 直接使用者：[frontend/src/lib/createApiClient.ts](../../../frontend/src/lib/createApiClient.ts)、[frontend/src/lib/teachingStream.ts](../../../frontend/src/lib/teachingStream.ts)、[frontend/src/stores/adminAuthStore.ts](../../../frontend/src/stores/adminAuthStore.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)。
- 处置：保留。

### [frontend/src/lib/sharedRequest.test.ts](../../../frontend/src/lib/sharedRequest.test.ts)

Vitest 规则回归：多个消费者共享请求的生命周期与取消协作。断言主题：createSharedRequest；shares one in-flight load between consumers；keeps a settled result until released。

- 代码入口/类型：`flushTimer`。
- 直接依赖：[frontend/src/lib/sharedRequest.ts](../../../frontend/src/lib/sharedRequest.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/sharedRequest.ts](../../../frontend/src/lib/sharedRequest.ts)

前端共享工具：多个消费者共享请求的生命周期与取消协作；实际导出 SharedRequest、createSharedRequest，上游页面/Hook 共用。

- 代码入口/类型：`SharedRequest`、`createSharedRequest`。
- 直接使用者：[frontend/src/hooks/useContinueLearning.ts](../../../frontend/src/hooks/useContinueLearning.ts)、[frontend/src/lib/channelSubscriptions.ts](../../../frontend/src/lib/channelSubscriptions.ts)、[frontend/src/lib/sharedRequest.test.ts](../../../frontend/src/lib/sharedRequest.test.ts)。
- 处置：保留。

### [frontend/src/lib/siteConfig.ts](../../../frontend/src/lib/siteConfig.ts)

前端共享工具：构建期站点地址和公示信息；实际导出 siteConfig、hasComplianceInfo，上游页面/Hook 共用。

- 代码入口/类型：`siteConfig`、`hasComplianceInfo`。
- 直接使用者：[frontend/src/app/layout.tsx](../../../frontend/src/app/layout.tsx)、[frontend/src/app/privacy/page.tsx](../../../frontend/src/app/privacy/page.tsx)、[frontend/src/app/terms/page.tsx](../../../frontend/src/app/terms/page.tsx)、[frontend/src/components/auth/AuthCard.tsx](../../../frontend/src/components/auth/AuthCard.tsx)、[frontend/src/components/common/ComplianceInfo.tsx](../../../frontend/src/components/common/ComplianceInfo.tsx)、[frontend/src/components/layout/PublicTopBar.tsx](../../../frontend/src/components/layout/PublicTopBar.tsx)；其余 1 项见机器清单。
- 处置：保留。

### [frontend/src/lib/smsCode.test.ts](../../../frontend/src/lib/smsCode.test.ts)

Vitest 规则回归：短信验证码输入/冷却纯规则。断言主题：PHONE_RE；与后端 pattern 一致：1 开头、第二位 3-9、共 11 位；cooldownRemaining。

- 直接依赖：[frontend/src/lib/smsCode.ts](../../../frontend/src/lib/smsCode.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/smsCode.ts](../../../frontend/src/lib/smsCode.ts)

前端共享工具：短信验证码输入/冷却纯规则；实际导出 PHONE_RE、CODE_COOLDOWN_SECONDS、SentCode、cooldownRemaining、distributeDigits，上游页面/Hook 共用。

- 代码入口/类型：`PHONE_RE`、`CODE_COOLDOWN_SECONDS`、`SentCode`、`cooldownRemaining`、`distributeDigits`。
- 直接使用者：[frontend/src/app/forgot-password/page.tsx](../../../frontend/src/app/forgot-password/page.tsx)、[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)、[frontend/src/components/auth/SmsOtpInput.tsx](../../../frontend/src/components/auth/SmsOtpInput.tsx)、[frontend/src/hooks/useSmsCode.ts](../../../frontend/src/hooks/useSmsCode.ts)、[frontend/src/lib/smsCode.test.ts](../../../frontend/src/lib/smsCode.test.ts)。
- 处置：保留。

### [frontend/src/lib/subscriptionEvents.ts](../../../frontend/src/lib/subscriptionEvents.ts)

前端共享工具：频道订阅变更的客户端事件通知；实际导出 SUBSCRIPTION_EVENT、SubscriptionChange、publishSubscription，上游页面/Hook 共用。

- 代码入口/类型：`SUBSCRIPTION_EVENT`、`SubscriptionChange`、`publishSubscription`。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)、[frontend/src/components/channels/ChannelSubscribeButton.tsx](../../../frontend/src/components/channels/ChannelSubscribeButton.tsx)、[frontend/src/components/watch/WatchSourceCard.tsx](../../../frontend/src/components/watch/WatchSourceCard.tsx)。
- 处置：保留。

### [frontend/src/lib/subtitleFollow.test.ts](../../../frontend/src/lib/subtitleFollow.test.ts)

Vitest 规则回归：当前句跟随/手动滚动协作的纯判定。断言主题：mobileFollowScroll；returns null when the sentence already sits at the target；tolerates a drift inside one line。

- 直接依赖：[frontend/src/lib/subtitleFollow.ts](../../../frontend/src/lib/subtitleFollow.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/subtitleFollow.ts](../../../frontend/src/lib/subtitleFollow.ts)

前端共享工具：当前句跟随/手动滚动协作的纯判定；实际导出 MOBILE_FOLLOW_GAP、MOBILE_FOLLOW_TOLERANCE、mobileFollowScroll、FollowBox、desktopFollowOffset、desktopFollowScroll，上游页面/Hook 共用。

- 代码入口/类型：`MOBILE_FOLLOW_GAP`、`MOBILE_FOLLOW_TOLERANCE`、`mobileFollowScroll`、`FollowBox`、`desktopFollowOffset`、`desktopFollowScroll`。
- 直接使用者：[frontend/src/hooks/useSubtitleFollow.ts](../../../frontend/src/hooks/useSubtitleFollow.ts)、[frontend/src/lib/subtitleFollow.test.ts](../../../frontend/src/lib/subtitleFollow.test.ts)。
- 处置：保留。

### [frontend/src/lib/subtitleModes.ts](../../../frontend/src/lib/subtitleModes.ts)

前端共享工具：字幕显示模式列表；实际导出 SUBTITLE_MODE_ORDER、SUBTITLE_MODE_LABEL，上游页面/Hook 共用。

- 代码入口/类型：`SUBTITLE_MODE_ORDER`、`SUBTITLE_MODE_LABEL`。
- 直接依赖：[frontend/src/stores/watchStore.ts](../../../frontend/src/stores/watchStore.ts)。
- 直接使用者：[frontend/src/components/watch/VideoControls.tsx](../../../frontend/src/components/watch/VideoControls.tsx)、[frontend/src/components/watch/WatchMoreSheet.tsx](../../../frontend/src/components/watch/WatchMoreSheet.tsx)、[frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)。
- 处置：保留。

### [frontend/src/lib/subtitleSplit.test.ts](../../../frontend/src/lib/subtitleSplit.test.ts)

Vitest 规则回归：字幕编辑拆分的纯规则。断言主题：splitSubtitleTextAtTime；uses current text when word timestamps belong to older text；uses word boundaries when timestamps match current text。

- 直接依赖：[frontend/src/lib/subtitleSplit.ts](../../../frontend/src/lib/subtitleSplit.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/subtitleSplit.ts](../../../frontend/src/lib/subtitleSplit.ts)

前端共享工具：字幕编辑拆分的纯规则；实际导出 WordTiming、splitSubtitleTextAtTime，上游页面/Hook 共用。

- 代码入口/类型：`WordTiming`、`splitSubtitleTextAtTime`。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/video-edit/SubtitleEditor.tsx](../../../frontend/src/components/video-edit/SubtitleEditor.tsx)、[frontend/src/lib/subtitleSplit.test.ts](../../../frontend/src/lib/subtitleSplit.test.ts)。
- 处置：保留。

### [frontend/src/lib/subtitles.test.ts](../../../frontend/src/lib/subtitles.test.ts)

Vitest 规则回归：字幕查找、词字段与时间规则。断言主题：subtitle seek boundaries；selects the sentence being entered when adjacent cues share a boundary；retains the last cue at its end and excludes gaps and out-of-range times。

- 代码入口/类型：`cue`。
- 直接依赖：[frontend/src/lib/subtitles.ts](../../../frontend/src/lib/subtitles.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/subtitles.ts](../../../frontend/src/lib/subtitles.ts)

前端共享工具：字幕查找、词字段与时间规则；实际导出 findSubtitleIndex，上游页面/Hook 共用。

- 代码入口/类型：`findSubtitleIndex`。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx](../../../frontend/src/components/video-edit/VideoSubtitleEditorPanel.tsx)、[frontend/src/hooks/useDeepLink.ts](../../../frontend/src/hooks/useDeepLink.ts)、[frontend/src/lib/subtitles.test.ts](../../../frontend/src/lib/subtitles.test.ts)。
- 处置：保留。

### [frontend/src/lib/teaching.test.ts](../../../frontend/src/lib/teaching.test.ts)

Vitest 规则回归：教学会话/操作 API、DTO 与运行恢复。断言主题：teaching disclosure-safe UI；does not merge cards from a stale session revision or a different user resource；rejects unknown versions, arbitrary actions and malformed card payloads。

- 代码入口/类型：`card`。
- 直接依赖：[frontend/src/lib/teaching.ts](../../../frontend/src/lib/teaching.ts)、[frontend/src/types/teaching.ts](../../../frontend/src/types/teaching.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/teaching.ts](../../../frontend/src/lib/teaching.ts)

前端共享工具：教学会话/操作 API、DTO 与运行恢复；实际导出 record、isTeachingCard、teachingHref、teachingResumeText、isActiveRun、mergeTeachingCard，上游页面/Hook 共用。

- 代码入口/类型：`record`、`isTeachingCard`、`teachingHref`、`teachingResumeText`、`isActiveRun`、`mergeTeachingCard`。
- 直接依赖：[frontend/src/types/teaching.ts](../../../frontend/src/types/teaching.ts)。
- 直接使用者：[frontend/src/components/lessons/LessonTutor.tsx](../../../frontend/src/components/lessons/LessonTutor.tsx)、[frontend/src/components/teaching/TeachingCards.tsx](../../../frontend/src/components/teaching/TeachingCards.tsx)、[frontend/src/components/teaching/TeachingCatalog.tsx](../../../frontend/src/components/teaching/TeachingCatalog.tsx)、[frontend/src/components/teaching/TeachingWorkspace.tsx](../../../frontend/src/components/teaching/TeachingWorkspace.tsx)、[frontend/src/lib/teaching.test.ts](../../../frontend/src/lib/teaching.test.ts)。
- 处置：保留。

### [frontend/src/lib/teachingStream.test.ts](../../../frontend/src/lib/teachingStream.test.ts)

Vitest 规则回归：教学 SSE 事件解析、游标与增量恢复。断言主题：teaching SSE；handles split CRLF, comments and multiline data without emitting an incomplete frame；decodes every UTF-8 byte boundary and only subscribes with the retained cursor。

- 代码入口/类型：`token`、`event`、`streamResponse`。
- 直接依赖：[frontend/src/lib/teachingStream.ts](../../../frontend/src/lib/teachingStream.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/teachingStream.ts](../../../frontend/src/lib/teachingStream.ts)

前端共享工具：教学 SSE 事件解析、游标与增量恢复；实际导出 SseMessage、createSseParser、StreamAuth、defaultAuth、readTeachingEvents，上游页面/Hook 共用。

- 代码入口/类型：`SseMessage`、`createSseParser`、`StreamAuth`、`defaultAuth`、`readTeachingEvents`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/jwt.ts](../../../frontend/src/lib/jwt.ts)、[frontend/src/lib/sessionRefresh.ts](../../../frontend/src/lib/sessionRefresh.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)、[frontend/src/types/teaching.ts](../../../frontend/src/types/teaching.ts)。
- 直接使用者：[frontend/src/components/lessons/LessonTutor.tsx](../../../frontend/src/components/lessons/LessonTutor.tsx)、[frontend/src/components/teaching/TeachingWorkspace.tsx](../../../frontend/src/components/teaching/TeachingWorkspace.tsx)、[frontend/src/lib/teachingStream.test.ts](../../../frontend/src/lib/teachingStream.test.ts)。
- 处置：保留。

### [frontend/src/lib/topicCategories.test.ts](../../../frontend/src/lib/topicCategories.test.ts)

Vitest 规则回归：主题分类标签与归一。断言主题：topicLabel；maps canonical ids to Chinese labels；is case-insensitive for legacy uppercase values。

- 直接依赖：[frontend/src/lib/topicCategories.ts](../../../frontend/src/lib/topicCategories.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/topicCategories.ts](../../../frontend/src/lib/topicCategories.ts)

前端共享工具：主题分类标签与归一；实际导出 TOPIC_CATEGORY_LABELS、topicLabel，上游页面/Hook 共用。

- 代码入口/类型：`TOPIC_CATEGORY_LABELS`、`topicLabel`。
- 直接使用者：[frontend/src/components/profile/InterestPicker.tsx](../../../frontend/src/components/profile/InterestPicker.tsx)、[frontend/src/components/ui/VideoCard.tsx](../../../frontend/src/components/ui/VideoCard.tsx)、[frontend/src/hooks/usePlatformFeed.ts](../../../frontend/src/hooks/usePlatformFeed.ts)、[frontend/src/lib/topicCategories.test.ts](../../../frontend/src/lib/topicCategories.test.ts)。
- 处置：保留。

### [frontend/src/lib/transcriptDoc.test.ts](../../../frontend/src/lib/transcriptDoc.test.ts)

Vitest 规则回归：整篇字幕文稿的顺序/词锚点/段落投影。断言主题：buildTranscriptSections；keeps contiguous sentences in one section；breaks on a silence longer than the gap threshold。

- 代码入口/类型：`sub`。
- 直接依赖：[frontend/src/lib/transcriptDoc.ts](../../../frontend/src/lib/transcriptDoc.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/transcriptDoc.ts](../../../frontend/src/lib/transcriptDoc.ts)

前端共享工具：整篇字幕文稿的顺序/词锚点/段落投影；实际导出 SECTION_GAP_SECONDS、SECTION_MAX_SENTENCES、TranscriptSection、ordered、buildTranscriptSections、TranscriptWord、buildWordIndex、TranscriptToken、splitSentenceTokens，上游页面/Hook 共用。

- 代码入口/类型：`SECTION_GAP_SECONDS`、`SECTION_MAX_SENTENCES`、`TranscriptSection`、`ordered`、`buildTranscriptSections`、`TranscriptWord`、`buildWordIndex`、`TranscriptToken`、`splitSentenceTokens`、`countTranscriptWords`（其余见机器清单）。
- 直接依赖：[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/components/transcript/TranscriptDocument.tsx](../../../frontend/src/components/transcript/TranscriptDocument.tsx)、[frontend/src/lib/transcriptDoc.test.ts](../../../frontend/src/lib/transcriptDoc.test.ts)。
- 处置：保留。

### [frontend/src/lib/utils.test.ts](../../../frontend/src/lib/utils.test.ts)

Vitest 规则回归：通用 className 合并等小工具与兼容导出。断言主题：cn；merges conflicting tailwind classes (last wins)；skips falsy values。

- 直接依赖：[frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/utils.ts](../../../frontend/src/lib/utils.ts)

前端共享工具：通用 className 合并等小工具与兼容导出；实际导出 twMerge、cn、classNames、relativeTime，上游页面/Hook 共用。

- 代码入口/类型：`twMerge`、`cn`、`classNames`、`relativeTime`。
- 直接依赖：[frontend/src/lib/format.ts](../../../frontend/src/lib/format.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/(admin)/admin/login/page.tsx](../../../frontend/src/app/%28admin%29/admin/login/page.tsx)；其余 94 项见机器清单。
- 处置：保留。

### [frontend/src/lib/videoDisplay.ts](../../../frontend/src/lib/videoDisplay.ts)

前端共享工具：视频标题/来源/封面展示归一；实际导出 VideoTitleLike、videoTitleZh、videoTitleEn，上游页面/Hook 共用。

- 代码入口/类型：`VideoTitleLike`、`videoTitleZh`、`videoTitleEn`。
- 直接使用者：[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/components/video/VideoTitle.tsx](../../../frontend/src/components/video/VideoTitle.tsx)。
- 处置：保留。

### [frontend/src/lib/videoStatus.tsx](../../../frontend/src/lib/videoStatus.tsx)

前端共享工具：管线步骤名称、状态反馈与进度展示；实际导出 STEP_LABELS、STEP_LABELS_SHORT、StatusBadgeConfig、PROCESSING_STATUS_CONFIG、ACTIVE_POLLING_STATUSES，上游页面/Hook 共用。

- 代码入口/类型：`STEP_LABELS`、`STEP_LABELS_SHORT`、`StatusBadgeConfig`、`PROCESSING_STATUS_CONFIG`、`ACTIVE_POLLING_STATUSES`。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/videos/VideoDetailRow.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoDetailRow.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoManager.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoManager.tsx)、[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/video/VideoStatus.tsx](../../../frontend/src/components/video/VideoStatus.tsx)、[frontend/src/hooks/useVideoStatusPolling.ts](../../../frontend/src/hooks/useVideoStatusPolling.ts)。
- 处置：保留。

### [frontend/src/lib/vocabularyPresentation.test.ts](../../../frontend/src/lib/vocabularyPresentation.test.ts)

Vitest 规则回归：词汇释义/来源/练习进度展示。断言主题：词汇展示；词性比例不进入展示，也不按占比猜语境；明确单一词性时优先同词性的已有释义，保留完整词典。

- 直接依赖：[frontend/src/lib/vocabularyPresentation.ts](../../../frontend/src/lib/vocabularyPresentation.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/vocabularyPresentation.ts](../../../frontend/src/lib/vocabularyPresentation.ts)

前端共享工具：词汇释义/来源/练习进度展示；实际导出 POS、partOfSpeechLabel、dictionaryPreview、vocabularySource，上游页面/Hook 共用。

- 代码入口/类型：`POS`、`partOfSpeechLabel`、`dictionaryPreview`、`vocabularySource`。
- 直接依赖：[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)、[frontend/src/app/(main)/vocabulary/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/page.tsx)、[frontend/src/app/(main)/vocabulary/review/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/review/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/sieve/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/sieve/page.tsx)；其余 6 项见机器清单。
- 处置：保留。

### [frontend/src/lib/watchClip.test.ts](../../../frontend/src/lib/watchClip.test.ts)

Vitest 规则回归：片段范围和定位参数校验。断言主题：字幕边界必须与当前已发布片段一致；字幕边界必须与当前已发布片段一致。

- 代码入口/类型：`cues`、`slot`。
- 直接依赖：[frontend/src/lib/watchClip.ts](../../../frontend/src/lib/watchClip.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/watchClip.ts](../../../frontend/src/lib/watchClip.ts)

前端共享工具：片段范围和定位参数校验；实际导出 validWatchClip，上游页面/Hook 共用。

- 代码入口/类型：`validWatchClip`。
- 直接依赖：[frontend/src/lib/watchSession.ts](../../../frontend/src/lib/watchSession.ts)、[frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/watch/PublishedVideoEditorial.tsx](../../../frontend/src/components/watch/PublishedVideoEditorial.tsx)、[frontend/src/lib/watchClip.test.ts](../../../frontend/src/lib/watchClip.test.ts)。
- 处置：保留。

### [frontend/src/lib/watchEntry.test.ts](../../../frontend/src/lib/watchEntry.test.ts)

Vitest 规则回归：观看来源/回跳/深链和焦点定位规则。断言主题：buildWatchEntryQuery；emits only the source marker when there is no extra；keeps the caller's param order and encodes values。

- 代码入口/类型：`params`、`subs`。
- 直接依赖：[frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/watchEntry.ts](../../../frontend/src/lib/watchEntry.ts)

前端共享工具：观看来源/回跳/深链和焦点定位规则；实际导出 WatchSource、WatchEntry、WatchReturn、SOURCE_LABELS、FEED_FILTER_KEYS、appendParam、buildWatchEntryQuery、watchHref、SentenceFocus，上游页面/Hook 共用。

- 代码入口/类型：`WatchSource`、`WatchEntry`、`WatchReturn`、`SOURCE_LABELS`、`FEED_FILTER_KEYS`、`appendParam`、`buildWatchEntryQuery`、`watchHref`、`SentenceFocus`、`sentenceFocusParams`（其余见机器清单）。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/favorites/page.tsx](../../../frontend/src/app/%28main%29/favorites/page.tsx)、[frontend/src/app/(main)/history/page.tsx](../../../frontend/src/app/%28main%29/history/page.tsx)、[frontend/src/app/(main)/search/page.tsx](../../../frontend/src/app/%28main%29/search/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/vocabulary/sets/[id]/sieve/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/sets/%5Bid%5D/sieve/page.tsx)、[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)；其余 17 项见机器清单。
- 处置：保留。

### [frontend/src/lib/watchLayout.test.ts](../../../frontend/src/lib/watchLayout.test.ts)

Vitest 规则回归：观看画框尺寸、偏好与桌面分栏纯规则。断言主题：watch layout constraints；stacks until both columns and the handle fit；keeps both columns usable at either drag boundary。

- 直接依赖：[frontend/src/lib/watchLayout.ts](../../../frontend/src/lib/watchLayout.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/watchLayout.ts](../../../frontend/src/lib/watchLayout.ts)

前端共享工具：观看画框尺寸、偏好与桌面分栏纯规则；实际导出 WATCH_LAYOUT_STORAGE_KEY、DEFAULT_WATCH_RATIO、MIN_VIDEO_WIDTH、MIN_TRANSCRIPT_WIDTH、WATCH_DIVIDER_WIDTH、MobileFrameSize、watchSplit、readWatchLayout，上游页面/Hook 共用。

- 代码入口/类型：`WATCH_LAYOUT_STORAGE_KEY`、`DEFAULT_WATCH_RATIO`、`MIN_VIDEO_WIDTH`、`MIN_TRANSCRIPT_WIDTH`、`WATCH_DIVIDER_WIDTH`、`MobileFrameSize`、`watchSplit`、`readWatchLayout`。
- 直接使用者：[frontend/src/components/watch/WatchDivider.tsx](../../../frontend/src/components/watch/WatchDivider.tsx)、[frontend/src/hooks/useWatchLayout.ts](../../../frontend/src/hooks/useWatchLayout.ts)、[frontend/src/lib/watchLayout.test.ts](../../../frontend/src/lib/watchLayout.test.ts)、[frontend/src/stores/watchStore.ts](../../../frontend/src/stores/watchStore.ts)。
- 处置：保留。

### [frontend/src/lib/watchProgressQueue.test.ts](../../../frontend/src/lib/watchProgressQueue.test.ts)

Vitest 规则回归：观看进度请求串行/合并和离开前冲刷。断言主题：watch position writes；serializes and coalesces pauses and periodic saves to the latest position；does not retry failure in a loop or claim it was saved。

- 直接依赖：[frontend/src/lib/watchProgressQueue.ts](../../../frontend/src/lib/watchProgressQueue.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/watchProgressQueue.ts](../../../frontend/src/lib/watchProgressQueue.ts)

前端共享工具：观看进度请求串行/合并和离开前冲刷；实际导出 ProgressSaveState、WatchProgressQueue，上游页面/Hook 共用。

- 代码入口/类型：`ProgressSaveState`、`WatchProgressQueue`。
- 直接使用者：[frontend/src/components/lessons/LessonReader.tsx](../../../frontend/src/components/lessons/LessonReader.tsx)、[frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)、[frontend/src/lib/watchProgressQueue.test.ts](../../../frontend/src/lib/watchProgressQueue.test.ts)。
- 处置：保留。

### [frontend/src/lib/watchSession.test.ts](../../../frontend/src/lib/watchSession.test.ts)

Vitest 规则回归：字幕辅助、循环和有效区间规则。断言主题：watch commands；resumes help only when the original playback was running；never resumes stale help after a new seek or pause command。

- 直接依赖：[frontend/src/lib/watchSession.ts](../../../frontend/src/lib/watchSession.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/watchSession.ts](../../../frontend/src/lib/watchSession.ts)

前端共享工具：字幕辅助、循环和有效区间规则；实际导出 reducedAid、validInterval、WatchSession，上游页面/Hook 共用。

- 代码入口/类型：`reducedAid`、`validInterval`、`WatchSession`。
- 直接依赖：[frontend/src/stores/watchStore.ts](../../../frontend/src/stores/watchStore.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)、[frontend/src/lib/watchClip.ts](../../../frontend/src/lib/watchClip.ts)、[frontend/src/lib/watchSession.test.ts](../../../frontend/src/lib/watchSession.test.ts)。
- 处置：保留。

### [frontend/src/lib/watchTime.test.ts](../../../frontend/src/lib/watchTime.test.ts)

Vitest 规则回归：可见且播放中的墙钟学习时长累计。断言主题：updateWatchTime；按秒累计播放时间，每 10 秒上报一次；短片段反复重听会正常累计（旧实现记 0）。

- 代码入口/类型：`run`、`ticks`。
- 直接依赖：[frontend/src/lib/watchTime.ts](../../../frontend/src/lib/watchTime.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/watchTime.ts](../../../frontend/src/lib/watchTime.ts)

前端共享工具：可见且播放中的墙钟学习时长累计；实际导出 WATCH_TIME_SCHEMA_VERSION、REPORT_INTERVAL_SECONDS、MIN_FLUSH_SECONDS、MAX_SEGMENT_SECONDS、WatchTimeState、WatchTimeInput、WatchTimeReport、WatchTimeResult、createWatchTimeState，上游页面/Hook 共用。

- 代码入口/类型：`WATCH_TIME_SCHEMA_VERSION`、`REPORT_INTERVAL_SECONDS`、`MIN_FLUSH_SECONDS`、`MAX_SEGMENT_SECONDS`、`WatchTimeState`、`WatchTimeInput`、`WatchTimeReport`、`WatchTimeResult`、`createWatchTimeState`、`settle`（其余见机器清单）。
- 直接使用者：[frontend/src/components/lessons/LessonReader.tsx](../../../frontend/src/components/lessons/LessonReader.tsx)、[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)、[frontend/src/lib/watchTime.test.ts](../../../frontend/src/lib/watchTime.test.ts)。
- 处置：保留。

### [frontend/src/lib/watchWordHighlight.test.ts](../../../frontend/src/lib/watchWordHighlight.test.ts)

Vitest 规则回归：按词 ID/字符范围判定高亮与选择。断言主题：wordHighlightClassFor；正在学的词压过其它档位，即使它也已掌握；未收录且命中目标级别的词落到浅底 + 虚线档。

- 代码入口/类型：`ctx`、`softTier`、`underlineTier`。
- 直接依赖：[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)、[frontend/src/lib/watchWordHighlight.ts](../../../frontend/src/lib/watchWordHighlight.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/watchWordHighlight.ts](../../../frontend/src/lib/watchWordHighlight.ts)

前端共享工具：按词 ID/字符范围判定高亮与选择；实际导出 LEARNING_WORD_CLASS、WordHighlightContext、wordHighlightClassFor、isWordSelected，上游页面/Hook 共用。

- 代码入口/类型：`LEARNING_WORD_CLASS`、`WordHighlightContext`、`wordHighlightClassFor`、`isWordSelected`。
- 直接依赖：[frontend/src/lib/examLevels.ts](../../../frontend/src/lib/examLevels.ts)。
- 直接使用者：[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/hooks/useWatchVocabulary.ts](../../../frontend/src/hooks/useWatchVocabulary.ts)、[frontend/src/lib/watchWordHighlight.test.ts](../../../frontend/src/lib/watchWordHighlight.test.ts)。
- 处置：保留。

### [frontend/src/lib/watchWordSource.test.ts](../../../frontend/src/lib/watchWordSource.test.ts)

Vitest 规则回归：点词来源与字幕上下文归一。断言主题：resolveWordSource；按 显式来源 → 重听句 → 词卡句 → 播放头句 的优先级取值；越界索引、空字幕与全空候选都返回 null。

- 代码入口/类型：`sub`、`a`、`b`、`c`。
- 直接依赖：[frontend/src/lib/watchWordSource.ts](../../../frontend/src/lib/watchWordSource.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/watchWordSource.ts](../../../frontend/src/lib/watchWordSource.ts)

前端共享工具：点词来源与字幕上下文归一；实际导出 WordSourceCandidates、resolveWordSource、WordSourcePosition、wordSourcePosition、wordSourceLabel、isSameWordSelection，上游页面/Hook 共用。

- 代码入口/类型：`WordSourceCandidates`、`resolveWordSource`、`WordSourcePosition`、`wordSourcePosition`、`wordSourceLabel`、`isSameWordSelection`。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/hooks/useWatchWordCard.ts](../../../frontend/src/hooks/useWatchWordCard.ts)、[frontend/src/lib/watchWordSource.test.ts](../../../frontend/src/lib/watchWordSource.test.ts)。
- 处置：保留。

### [frontend/src/lib/webVitals.test.ts](../../../frontend/src/lib/webVitals.test.ts)

Vitest 规则回归：浏览器性能指标观测与上报边界。断言主题：webVitals；只有已有样本才上报：没有 CLS 偏移不是 0；LCP 取最后一次候选（后到的更大元素覆盖先到的）。

- 代码入口/类型：`shifts`。
- 直接依赖：[frontend/src/lib/webVitals.ts](../../../frontend/src/lib/webVitals.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/lib/webVitals.ts](../../../frontend/src/lib/webVitals.ts)

前端共享工具：浏览器性能指标观测与上报边界；实际导出 VitalName、WEB_VITAL_SCHEMA_VERSION、CLS_SESSION_GAP_MS、CLS_SESSION_MAX_MS、LayoutShiftSample、VitalsState、createVitalsState、recordLcp、recordInp，上游页面/Hook 共用。

- 代码入口/类型：`VitalName`、`WEB_VITAL_SCHEMA_VERSION`、`CLS_SESSION_GAP_MS`、`CLS_SESSION_MAX_MS`、`LayoutShiftSample`、`VitalsState`、`createVitalsState`、`recordLcp`、`recordInp`、`recordLayoutShift`（其余见机器清单）。
- 直接使用者：[frontend/src/lib/analytics.ts](../../../frontend/src/lib/analytics.ts)、[frontend/src/lib/webVitals.test.ts](../../../frontend/src/lib/webVitals.test.ts)。
- 处置：保留。

### [frontend/src/lib/youtubePlayer.ts](../../../frontend/src/lib/youtubePlayer.ts)

前端共享工具：YouTube IFrame SDK 加载和共享播放器边界；实际导出 YTPlayerInstance、YTPlayerHandlers、YTPlayerOptions、YTPlayerClass、API_SCRIPT_ID、ensureYouTubeApi、createYouTubePlayer、destroyYouTubePlayer，上游页面/Hook 共用。

- 代码入口/类型：`YTPlayerInstance`、`YTPlayerHandlers`、`YTPlayerOptions`、`YTPlayerClass`、`API_SCRIPT_ID`、`ensureYouTubeApi`、`createYouTubePlayer`、`destroyYouTubePlayer`。
- 直接使用者：[frontend/src/hooks/useLessonYouTube.ts](../../../frontend/src/hooks/useLessonYouTube.ts)、[frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)。
- 处置：保留。

## `frontend/src`

### [frontend/src/proxy.ts](../../../frontend/src/proxy.ts)

Next.js 登录墙：按用户/管理镜像 cookie 是否存在决定导航，不验签或查询数据库。

- 代码入口/类型：`PUBLIC_PATHS`、`isPublicPath`、`PUBLIC_ASSETS`、`proxy`、`config`。
- 配置/资源消费者：[frontend/next.config.js](../../../frontend/next.config.js)。
- 处置：保留。

## `frontend/src/stores`

### [frontend/src/stores/adminAuthStore.test.ts](../../../frontend/src/stores/adminAuthStore.test.ts)

Vitest 规则回归：管理员独立登录初始化、刷新和退出。断言主题：useAdminAuthStore.bootstrap；keeps isLoading true while an expired token refreshes (no premature login bounce)；useAdminAuthStore.bootstrap。

- 代码入口/类型：`makeToken`、`nowSec`。
- 直接依赖：[frontend/src/stores/adminAuthStore.ts](../../../frontend/src/stores/adminAuthStore.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/stores/adminAuthStore.ts](../../../frontend/src/stores/adminAuthStore.ts)

Zustand 共享状态：管理员独立登录初始化、刷新和退出；页面通过 Hook/selector 读取，不是服务器事实源。

- 代码入口/类型：`AdminAuthUser`、`AdminAuthState`、`AdminAuthActions`、`MIGRATION_MAPPINGS`、`refreshPromise`、`sessionEpoch`、`useAdminAuthStore`。
- 直接依赖：[frontend/src/lib/authHelpers.ts](../../../frontend/src/lib/authHelpers.ts)、[frontend/src/lib/jwt.ts](../../../frontend/src/lib/jwt.ts)、[frontend/src/lib/sessionRefresh.ts](../../../frontend/src/lib/sessionRefresh.ts)。
- 直接使用者：[frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/users/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/users/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/videos/VideoDetailRow.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/videos/VideoDetailRow.tsx)、[frontend/src/app/(admin)/admin/login/page.tsx](../../../frontend/src/app/%28admin%29/admin/login/page.tsx)、[frontend/src/components/admin/AdminTopbar.tsx](../../../frontend/src/components/admin/AdminTopbar.tsx)；其余 3 项见机器清单。
- 处置：保留。

### [frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)

Zustand 共享状态：用户登录状态、初始化、刷新与退出；页面通过 Hook/selector 读取，不是服务器事实源。

- 代码入口/类型：`AuthUser`、`AuthState`、`AuthActions`、`MIGRATION_MAPPINGS`、`AuthStore`、`refreshPromise`、`adoptStoredSession`、`useAuthStore`。
- 直接依赖：[frontend/src/lib/authHelpers.ts](../../../frontend/src/lib/authHelpers.ts)、[frontend/src/lib/jwt.ts](../../../frontend/src/lib/jwt.ts)、[frontend/src/lib/sessionRefresh.ts](../../../frontend/src/lib/sessionRefresh.ts)、[frontend/src/stores/planStore.ts](../../../frontend/src/stores/planStore.ts)、[frontend/src/stores/profileStore.ts](../../../frontend/src/stores/profileStore.ts)、[frontend/src/stores/vocabularyStore.ts](../../../frontend/src/stores/vocabularyStore.ts)；其余 1 项见机器清单。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)、[frontend/src/app/(main)/contact/page.tsx](../../../frontend/src/app/%28main%29/contact/page.tsx)、[frontend/src/app/login/page.tsx](../../../frontend/src/app/login/page.tsx)、[frontend/src/app/register/page.tsx](../../../frontend/src/app/register/page.tsx)、[frontend/src/components/auth/RedirectStuckState.tsx](../../../frontend/src/components/auth/RedirectStuckState.tsx)、[frontend/src/components/common/AuthInitializer.tsx](../../../frontend/src/components/common/AuthInitializer.tsx)；其余 10 项见机器清单。
- 处置：保留。

### [frontend/src/stores/notificationStore.ts](../../../frontend/src/stores/notificationStore.ts)

Zustand 共享状态：通知和未读客户端状态；页面通过 Hook/selector 读取，不是服务器事实源。

- 代码入口/类型：`NotificationState`、`useNotificationStore`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)。
- 直接使用者：[frontend/src/app/(main)/notifications/page.tsx](../../../frontend/src/app/%28main%29/notifications/page.tsx)、[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)、[frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx)、[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)、[frontend/src/components/layout/UnreadCountSync.tsx](../../../frontend/src/components/layout/UnreadCountSync.tsx)。
- 处置：保留。

### [frontend/src/stores/planStore.ts](../../../frontend/src/stores/planStore.ts)

Zustand 共享状态：档案和掌握趋势状态，非收费套餐；页面通过 Hook/selector 读取，不是服务器事实源。

- 代码入口/类型：`PlanState`、`PlanActions`、`PlanStore`、`INITIAL_STATE`、`generation`、`usePlanStore`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/hooks/usePlan.ts](../../../frontend/src/hooks/usePlan.ts)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)。
- 处置：保留。

### [frontend/src/stores/profileStore.test.ts](../../../frontend/src/stores/profileStore.test.ts)

Vitest 规则回归：学习档案获取/刷新及状态。断言主题：useProfileStore；publishes avatar_url + gender from /users/me；maps missing fields to nulls (no upload, no gender filled in)。

- 代码入口/类型：`mockedApi`、`deferred`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/stores/profileStore.ts](../../../frontend/src/stores/profileStore.ts)。
- 隐式入口：pytest / Vitest / Playwright 收集器；不是产品页面调用。
- 处置：保留。

### [frontend/src/stores/profileStore.ts](../../../frontend/src/stores/profileStore.ts)

Zustand 共享状态：学习档案获取/刷新及状态；页面通过 Hook/selector 读取，不是服务器事实源。

- 代码入口/类型：`MeProfile`、`ProfileState`、`ProfileActions`、`inflight`、`generation`、`useProfileStore`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)、[frontend/src/lib/avatar.ts](../../../frontend/src/lib/avatar.ts)。
- 直接使用者：[frontend/src/app/(main)/profile/page.tsx](../../../frontend/src/app/%28main%29/profile/page.tsx)、[frontend/src/components/layout/AccountMenu.tsx](../../../frontend/src/components/layout/AccountMenu.tsx)、[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)、[frontend/src/stores/authStore.ts](../../../frontend/src/stores/authStore.ts)、[frontend/src/stores/profileStore.test.ts](../../../frontend/src/stores/profileStore.test.ts)。
- 处置：保留。

### [frontend/src/stores/vocabularyStore.ts](../../../frontend/src/stores/vocabularyStore.ts)

Zustand 共享状态：个人词汇列表和掌握操作状态；页面通过 Hook/selector 读取，不是服务器事实源。

- 代码入口/类型：`VocabStats`、`VocabularyState`、`VocabularyActions`、`VocabularyStore`、`INITIAL_STATE`、`generation`、`useVocabularyStore`。
- 直接依赖：[frontend/src/lib/api.ts](../../../frontend/src/lib/api.ts)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)、[frontend/src/app/(main)/vocabulary/drill/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/drill/page.tsx)、[frontend/src/app/(main)/vocabulary/review/page.tsx](../../../frontend/src/app/%28main%29/vocabulary/review/page.tsx)、[frontend/src/components/layout/MobileTabBar.tsx](../../../frontend/src/components/layout/MobileTabBar.tsx)、[frontend/src/components/layout/Sidebar.tsx](../../../frontend/src/components/layout/Sidebar.tsx)、[frontend/src/components/layout/TopBar.tsx](../../../frontend/src/components/layout/TopBar.tsx)；其余 1 项见机器清单。
- 处置：保留。

### [frontend/src/stores/watchStore.ts](../../../frontend/src/stores/watchStore.ts)

Zustand 共享状态：观看页当前句、字幕模式、播放/循环状态；页面通过 Hook/selector 读取，不是服务器事实源。

- 代码入口/类型：`SubtitleMode`、`SUBTITLE_MODE_STORAGE_KEY`、`VALID_MODES`、`loadPersistedSubtitleMode`、`WatchStore`、`INITIAL_STATE`、`persistLayout`、`useWatchStore`。
- 直接依赖：[frontend/src/lib/watchLayout.ts](../../../frontend/src/lib/watchLayout.ts)。
- 直接使用者：[frontend/src/app/(main)/MainLayoutInner.tsx](../../../frontend/src/app/%28main%29/MainLayoutInner.tsx)、[frontend/src/app/(main)/watch/[id]/page.tsx](../../../frontend/src/app/%28main%29/watch/%5Bid%5D/page.tsx)、[frontend/src/components/exam/TargetExamSetting.tsx](../../../frontend/src/components/exam/TargetExamSetting.tsx)、[frontend/src/components/watch/VideoControls.tsx](../../../frontend/src/components/watch/VideoControls.tsx)、[frontend/src/components/watch/WatchMoreSheet.tsx](../../../frontend/src/components/watch/WatchMoreSheet.tsx)、[frontend/src/hooks/useVideoPlayer.ts](../../../frontend/src/hooks/useVideoPlayer.ts)；其余 3 项见机器清单。
- 处置：保留。

## `frontend/src/types`

### [frontend/src/types/channels.ts](../../../frontend/src/types/channels.ts)

TypeScript DTO：频道列表、详情与管理员维护；与后端响应对齐，不包含执行逻辑。

- 代码入口/类型：`ChannelLatestVideo`、`ChannelLearningDirection`、`ChannelDifficultyRange`、`ChannelSummary`、`ChannelSubscriptionSummary`。
- 直接依赖：[frontend/src/components/video/VideoMetadata.tsx](../../../frontend/src/components/video/VideoMetadata.tsx)。
- 直接使用者：[frontend/src/app/(main)/channels/[slug]/page.tsx](../../../frontend/src/app/%28main%29/channels/%5Bslug%5D/page.tsx)、[frontend/src/app/(main)/channels/page.tsx](../../../frontend/src/app/%28main%29/channels/page.tsx)、[frontend/src/app/(main)/search/page.tsx](../../../frontend/src/app/%28main%29/search/page.tsx)、[frontend/src/components/channels/ChannelCard.tsx](../../../frontend/src/components/channels/ChannelCard.tsx)、[frontend/src/components/channels/SubscribedChannels.tsx](../../../frontend/src/components/channels/SubscribedChannels.tsx)、[frontend/src/components/home/DiscoverRail.tsx](../../../frontend/src/components/home/DiscoverRail.tsx)；其余 5 项见机器清单。
- 处置：保留。

### [frontend/src/types/homeContent.ts](../../../frontend/src/types/homeContent.ts)

TypeScript DTO：首页草稿/版本/布局与公共编排；与后端响应对齐，不包含执行逻辑。

- 代码入口/类型：`HomeEditorialSentence`、`HomeEditorialWordTimestamp`、`HomeEditorialExpression`、`HomeEditorialInteractionOption`、`HomeEditorialInteraction`、`HomeEditorialScenario`、`HomeEditorialClip`、`HomeEditorialContent`、`HomeEditorialVideoSlot`、`HomeEditorialExpressionSlot`（其余见机器清单）。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/e2e/home-editorial-full-loop.spec.ts](../../../frontend/e2e/home-editorial-full-loop.spec.ts)、[frontend/e2e/home-editorial.spec.ts](../../../frontend/e2e/home-editorial.spec.ts)、[frontend/src/app/(main)/page.tsx](../../../frontend/src/app/%28main%29/page.tsx)、[frontend/src/components/admin/home/EditorialPreviewPane.tsx](../../../frontend/src/components/admin/home/EditorialPreviewPane.tsx)、[frontend/src/components/admin/home/HomeContentDraftForm.tsx](../../../frontend/src/components/admin/home/HomeContentDraftForm.tsx)、[frontend/src/components/admin/home/HomeContentPanel.tsx](../../../frontend/src/components/admin/home/HomeContentPanel.tsx)；其余 17 项见机器清单。
- 处置：更新必要说明/引用或生成路径。

### [frontend/src/types/index.ts](../../../frontend/src/types/index.ts)

TypeScript DTO：用户/视频/字幕/词汇公共字段；与后端响应对齐，不包含执行逻辑。

- 代码入口/类型：`User`、`VideoCard`、`VideoAdmin`、`AdminChannel`、`Paginated`、`Subtitle`、`SubtitleRevision`、`VideoDetail`、`LearningRecord`、`GradedResult`（其余见机器清单）。
- 直接使用者：[frontend/e2e/home-editorial.spec.ts](../../../frontend/e2e/home-editorial.spec.ts)、[frontend/src/app/(admin)/admin/(shell)/channels/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/channels/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/layout.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/layout.tsx)、[frontend/src/app/(admin)/admin/(shell)/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/settings/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/settings/page.tsx)、[frontend/src/app/(admin)/admin/(shell)/stats/page.tsx](../../../frontend/src/app/%28admin%29/admin/%28shell%29/stats/page.tsx)；其余 87 项见机器清单。
- 处置：保留。

### [frontend/src/types/listening.ts](../../../frontend/src/types/listening.ts)

TypeScript DTO：字幕句冻结的听力练习会话；与后端响应对齐，不包含执行逻辑。

- 代码入口/类型：`ListeningQuestion`、`ListeningResult`、`ListeningSession`、`ListeningRecent`。
- 直接依赖：[frontend/src/types/index.ts](../../../frontend/src/types/index.ts)。
- 直接使用者：[frontend/src/app/(main)/practice/listening/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/%5Bid%5D/page.tsx)、[frontend/src/app/(main)/practice/listening/page.tsx](../../../frontend/src/app/%28main%29/practice/listening/page.tsx)。
- 处置：保留。

### [frontend/src/types/platform.ts](../../../frontend/src/types/platform.ts)

TypeScript DTO：平台浏览和发现返回格式；与后端响应对齐，不包含执行逻辑。

- 代码入口/类型：`Category`、`VideoItem`。
- 直接使用者：[frontend/src/hooks/usePlatformFeed.ts](../../../frontend/src/hooks/usePlatformFeed.ts)。
- 处置：保留。

### [frontend/src/types/teaching.ts](../../../frontend/src/types/teaching.ts)

TypeScript DTO：确定性教学材料、会话、作答、提示和揭晓；与后端响应对齐，不包含执行逻辑。

- 代码入口/类型：`LEARNING_EVENT_SCHEMA_VERSION`、`TeachingQuestionPayload`、`CardBase`、`TeachingCard`、`TeachingItem`、`TeachingAttempt`、`TeachingSession`、`TeachingSessionSummary`、`TeachingContent`、`TeachingRunStatus`（其余见机器清单）。
- 直接使用者：[frontend/src/app/(main)/practice/exams/result/[id]/page.tsx](../../../frontend/src/app/%28main%29/practice/exams/result/%5Bid%5D/page.tsx)、[frontend/src/components/lessons/LessonTutor.tsx](../../../frontend/src/components/lessons/LessonTutor.tsx)、[frontend/src/components/profile/ExternalConnections.tsx](../../../frontend/src/components/profile/ExternalConnections.tsx)、[frontend/src/components/teaching/TeachingCards.tsx](../../../frontend/src/components/teaching/TeachingCards.tsx)、[frontend/src/components/teaching/TeachingCatalog.tsx](../../../frontend/src/components/teaching/TeachingCatalog.tsx)、[frontend/src/components/teaching/TeachingQuiz.tsx](../../../frontend/src/components/teaching/TeachingQuiz.tsx)；其余 4 项见机器清单。
- 处置：保留。

## `frontend`

### [frontend/tsconfig.json](../../../frontend/tsconfig.json)

TypeScript 检查范围、模块/路径别名与 Next 类型配置。

- 关系边界：文档/法律/证据供人或发行流程读取，不要求源码 import；链接/类别见职责。
- 处置：保留。

### [frontend/vitest.config.mts](../../../frontend/vitest.config.mts)

node 环境单测的文件范围与别名。

- 关系边界：入口可能来自命令、配置、框架约定或资源 URL；未证明可删，不把缺静态边当死代码。
- 处置：保留。
