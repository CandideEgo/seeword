# SeeWord 用户端设计规范

这份文件只说明**规则怎么用、去哪里取值**；色值、字号、圆角等实际数值只有两个家，
改数值永远改那里，不要在这里复制一份：

| 家                                  | 管什么                                                        |
| ----------------------------------- | ------------------------------------------------------------- |
| `src/app/globals.css` 的 `@theme`   | 全站 token 与 Tailwind 工具类（管理端沿用橙色 brand）         |
| `src/app/user-ui.css` 的 `.user-ui` | 用户端视觉（蓝色 accent、Apple 式编辑版式）；只在用户壳内生效 |
| `src/app/user-ui.css` 的 `.dark`    | 暗色变量（`useTheme` + 布局内联脚本防闪烁）                   |

`frontend/scripts/check-design-system.mjs` 是下面几条硬规则的机器执行点，`npm run check` 会跑。

## 1. 颜色

只用语义 token，不写原始调色板、不写任意 hex：

- 面：`bg-canvas`（页面）、`bg-surface-soft` / `bg-surface-card`（分区、输入框底色）、
  `bg-surface-dark`（视频舞台）
- 字：`text-ink`（标题）、`text-body`（正文）、`text-muted`（次要）、`text-on-dark`
- 线：`border-hairline` / `-soft` / `-strong`
- 品牌：`text-brand-700`（链接与强调）、`bg-brand-50`（浅底选中）、`bg-action-primary`（实心主操作）
- 状态：`text-success-text`、`text-error-text`、`bg-red-soft`

硬规则：

1. 实心主操作一律 `bg-action-primary` + `text-on-primary`；**不要** `bg-brand-500` 配白字
   （对比度不够，门禁第 7/9 条会拦）。
2. `bg-white` / `bg-black` 不能当面用；叠加层（带透明度的 `bg-black/45`）与深底白字可以用。
3. 用户端的 `--color-brand-*` 与 `--color-action-primary` 在 `.user-ui` 里被改成蓝色；
   新增浅色档位时必须同时覆盖 `--brand-*` 与 `--color-brand-*`（Tailwind 工具类读后者）。

## 2. 字体与字号

系统字体栈，英文标题允许 `lang="en"` + `text-balance`。层级只用以下几步：

| token             | 用途                          |
| ----------------- | ----------------------------- |
| `text-display`    | 首页主推标题（`sm:` 起）      |
| `text-display-sm` | 页面内大标题 / 观看页英文标题 |
| `text-title`      | 卡片标题、区块主标题          |
| `text-copy-lg`    | 强调正文、字幕原句            |
| `text-copy`       | 正文                          |
| `text-meta`       | 辅助信息、时间、频道名        |
| `text-caption`    | 标签、计数、脚注              |

数字列（计数、时长、进度）加 `tabular-nums`。中文正文行高 `leading-relaxed`。

## 3. 间距、圆角、阴影

- 页面纵向节奏用 `space-y-6` / `gap-6`；区块之间 `2rem`（`user-page-layout` 已内置）。
- 圆角只允许 `rounded-sm|md|lg|pill|full|none`：按钮在 `.user-ui` 里统一胶囊；
  卡片用 `rounded-lg`，图片框 `rounded-md`，小标签 `rounded-sm`。
- 阴影只用于浮层（`shadow` / `user-search-dialog`）；内容卡一律发丝线描边，不加阴影。
  `.user-ui` 已把旧的橙色 `shadow-brand` 中和为无阴影。

## 4. 版式原语（页面复用，不各写一套）

- `components/ui/PageHeader`：页面唯一 `h1` + `crumb` + 描述 + `actions`。
  页面文件里不得自写 `<h1>`（门禁第 4 条）。
- 壳层 `MainLayoutInner` 拥有唯一 `.container-page` 和 `<main>`；页面不得再加容器（门禁第 1/8 条）。
- `.user-page-layout.has-aside` + `.user-page-main` + `.user-page-aside`：1280px 起双栏，
  窄屏右栏落到内容之后。
- `.user-sec-head` / `.user-sec-title` / `.user-sec-sub`：区块标题行（标题 + 计数/链接）。
- `.user-stat-grid` / `.user-stat`：平铺统计（20px 数值 + 13px 标签）。
- `.user-kv` / `.user-kv-row`：右栏键值表。
- `components/common/EmptyState`、`ErrorState`、`Spinner`：空/错/加载三态，页面不再自拼。

## 5. 组件

- `Button`（`primary|tonal|dark|outline|ghost|text|destructive|secondary`，尺寸 `xs|sm|compact|md|nav|lg|icon`）
  与 `LinkButton` 同构；异步用 `loading`。
- `Card`：`padding` 取 3–6；默认描边无阴影。
- `TabPills`：顶部类型筛选（胶囊，选中黑底）；`Button` 的 `tonal` 用于「已选中但仍可点」的行内动作。
- `VideoCard`：视频封面卡，英文标题优先、中文名次行，右下角时长，底部互动计数。
- `Image`：默认 `fill`，父级必须 `relative` 且给定尺寸；远程图源要加 `next.config.js` 的 `remotePatterns`。

### Astryx 首批接入

- 官方发布包通过预编译 CSS 与 Tailwind 共存；入口在 `src/app/globals.css`，不引入 Astryx 的 Tailwind token bridge。
- `components/common/AstryxProvider` 复用现有主题状态，由词汇模块布局挂接。主题映射只放在 `user-ui.css` 的局部主题作用域，不给后台套用户端主题。
- `vocabulary/page.tsx` 的跨页视图入口使用官方 `Button` 与 Next Link，掌握程度和复习范围使用 `SegmentedControl`，搜索使用 `TextInput`，分页使用 `Button`。数据接口与学习流程不变；其它页面与共享基础组件尚未迁移。
- 与 Astryx 同名的既有颜色工具类在 `globals.css` 的 `@theme inline` 中保留 SeeWord 语义；不要把这些声明移回普通 `@theme`，也不要在用户端样式中直接读取 Astryx 的同名状态色。
- 接入回归在 `e2e/astryx-vocabulary.spec.ts`，使用真实 API 验证筛选、搜索、分页、导航键盘行为与路由主题清理；系统主题和站内偏好相反时，原生 UI 也必须跟随站内偏好。

## 6. 状态与文案

- 空状态要说清「为什么空 + 下一步怎么做」，一个页面最多一个主 CTA；
  整页都没有数据时合并成一张卡，不要每组各弹一次同样的按钮。
- 失败用 `ErrorState` + 重试；API 错误统一交给 `toastApiError`。
- 数字说明只在一个地方出现：计数放标签或区块头，右栏不再重复一遍。
- 说明性文字只留一处：标题描述已经讲过的规则，不在正文/右栏再讲一遍。

## 7. 响应式

- 断点用 Tailwind 默认：`sm 640` / `md 768` / `lg 1024` / `xl 1280`。
- 页面内容宽度由壳层控制（`--max-width-page`）；表格/双栏在 `md` 或 `lg` 收起为单栏。
- 手机端底部导航是硬边界：观看页词卡、动作行不得被底栏遮挡（`mobile-*.spec.ts` 守这条）。
- 任何新页面都要在 390px 与 1440px 下各看一遍，确认无横向溢出。

## 8. 验证

```bash
npm run check                     # 设计系统 + 会话写入 + tsc + ESLint + Prettier
npx vitest run                    # 单测
npx playwright test e2e/watch-desktop-stage.spec.ts   # 观看页版式不变量
node scripts/design-shots.mjs --tag=<tag> --routes=/a,/b   # 桌面/手机截图到 docs/evidence/design-redo/
```
