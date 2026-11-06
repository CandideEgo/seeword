#!/usr/bin/env node
/**
 * check-design-system.mjs — DEC-075 前端设计系统门禁（9 条规则）
 *
 * 为什么需要它：P1–P5 把容器、页头、圆角、字号、卡片各自收敛成「唯一写法」，但那只是
 * 一次性整理。没有机器检查，下一个人照样可以在页面里写 `container-page`、在组件里写
 * `bg-blue-100`，收敛会在两次改动内回到起点。本脚本是那几条不变量的唯一执行点。
 *
 * 九条规则（DEC-075 ⑤ 末条 + G14 / checklist 5.2 补的两条 + 2026-10 全站重构补的三条）：
 *   1) src/app 下所有文件        不得出现 `container-page` / `container-wide`
 *                                破坏示例：页面自己选容器（P1 已把这活收进壳层）
 *   2) src 下所有 .ts / .tsx     不得出现原始调色板工具类
 *                                破坏示例：`bg-blue-100`、`text-slate-700`
 *   3) src 下所有 .tsx           不得出现允许集外的 `rounded-*`
 *                                允许集：sm|md|lg|pill|full|none（含方向角 t/r/b/l-*）
 *                                破坏示例：`rounded-2xl`、任意值 `rounded-[10px]`
 *   4) src/app 下的 page.tsx     不得自写 `<h1`
 *                                破坏示例：第三套页头（P2 已归一为 ui/PageHeader）
 *   5) src 下所有 .ts / .tsx     不得写任意值 hex 颜色
 *                                破坏示例：`border-[#2c2c2c]`——绕过 token 体系私设颜色
 *   6) src 下所有 .ts / .tsx     无色阶的 white/black 不得当「面」用
 *                                破坏示例：区块底色直接写 `bg-white`（暗色模式必炸）
 *   7) src 下所有 .ts / .tsx     `bg-brand-500` 不得与 `text-on-primary` 同处一个 className
 *                                破坏示例：`bg-brand-500 text-on-primary`——白字对 #ea580c
 *                                只有 3.12:1，低于 WCAG AA 4.5:1。实心主操作一律
 *                                `bg-action-primary`（#c2410c，5.18:1）。
 *   8) src/app/(main) 下所有文件  不得出现 `<main`
 *                                破坏示例：页面自写 `<main>`——壳层 `MainLayoutInner` 已是
 *                                全站唯一 main landmark，再写一个就是嵌套 main（HTML 语义
 *                                错误、屏幕阅读器重复播报路由区）。
 *   9) src 下所有 .ts / .tsx     同一行不得同时出现 `bg-brand-500` 与裸 `text-white`
 *                                破坏示例：`bg-brand-500 text-white`——和规则 7 同因；实际上
 *                                「白字」更多是写成 `text-white` 而不是 `text-on-primary`，
 *                                只卡后者会漏掉整类回归。
 *
 * 判定口径补充（规则 7/8/9）：
 *   规则 7 按「行 + 后两行」拼成的窗口判定，因为 className 常被折成多行；窗口外不误伤。
 *   规则 9 只看同一行，且排除 `bg-brand-500/10` 这类半透明 tint；跨行的 `text-white`
 *          多半是压在 brand-500 圆面上的**图标**（播放键、名次角标），非文本对比度
 *          归 WCAG 1.4.11（图形 3:1，当前 3.12:1 达标），不在这条射程内。
 *   规则 8 只看 `src/app/(main)/`；管理端与裸路由不受限（admin 壳的 `<main>` 在它自己的
 *           layout 里，`/admin/login` 是独立入口）。唯一白名单是壳文件本身。
 *
 * 规则 5/6 的判定口径（写清楚是为了让下一个人能自己判断新写法对不对）：
 *   规则 5 只看「颜色工具类 + 任意值 hex」。用 token 变量的写法
 *           （`shadow-[inset_0_0_0_1px_var(--color-brand-500)]`）不算违规；
 *           尺寸/布局类任意值（`w-[42px]`、`grid-cols-[1fr_2fr]`）本来就不在射程内。
 *   规则 6 把 white/black 按「作用面」分三档：
 *           - 叠加层（带透明度修饰符：`bg-white/10`、`bg-black/45`）：**允许**。
 *             半透明叠层与任意底色兼容，是遮罩/浮层的标准写法。
 *           - 面（裸 `bg-white` / `bg-black` / 渐变端点 `from-black` …）：**违规**。
 *             白色/黑色作为背景必须走语义 token（`bg-canvas` / `bg-surface-card` /
 *             `bg-surface-dark*` / `bg-on-primary`…），否则暗色模式下这块会变成白斑。
 *           - 前景/描边（裸 `text-white` / `border-white` / `accent-white`）：**允许**。
 *             本仓 23 处裸用白字都是「深底上的白字」（品牌块、播放器控件、媒体角标）；
 *             语义 token `text-on-dark` 是 #fafafa、不是逐字等价的 #ffffff，改写会动视觉；
 *             而白字是否可读取决于祖先底色（媒体层/遮罩层），静态扫不准。要把它变成
 *             硬规则只能靠「整文件豁免」兜底——那是更大的口子，故不设卡。
 *           - 黑色一律违规（面与前景都算）：黑面/黑字必须走 `text-ink` /
 *             `bg-surface-dark*` 一类的语义 token（存量 0 处）。
 *
 * 白名单**点名文件 + 写理由**，不允许通配：写理由才逼着人解释「为什么这个文件例外」，
 * 通配会让例外悄悄扩散。被列入白名单的文件在该条规则下整文件豁免。
 * 若白名单条目在当前代码里已经不命中任何违规，脚本会提示（条目可以删了）。
 *
 * 扫的是原始文本，注释里也扫。这是故意的：假阳性只是改个措辞，假阴性会真的放行，
 * 后者的代价更高。
 *
 * 用法：node scripts/check-design-system.mjs      # 退出码 0 = 通过，1 = 有违规
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, resolve, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const FRONTEND = resolve(HERE, "..");
const REPO = resolve(FRONTEND, "..");

const posix = (p) => p.split(sep).join("/");
const rel = (abs) => posix(relative(REPO, abs));

// ---------------------------------------------------------------- 文件遍历

const SKIP_DIRS = new Set(["node_modules", ".next", ".debug-shots", "__snapshots__"]);

function walk(absDir, out = []) {
  for (const name of readdirSync(absDir)) {
    if (SKIP_DIRS.has(name)) continue;
    const abs = join(absDir, name);
    const st = statSync(abs);
    if (st.isDirectory()) walk(abs, out);
    else out.push(abs);
  }
  return out;
}

const SRC = join(FRONTEND, "src");
const allSrc = walk(SRC);
const isTs = (f) => /\.tsx?$/.test(f);
const isTsx = (f) => /\.tsx$/.test(f);
const isApp = (f) => rel(f).startsWith("frontend/src/app/");
const isPage = (f) => isApp(f) && /\/page\.tsx$/.test(posix(f));
const isMainShell = (f) => rel(f).startsWith("frontend/src/app/(main)/");

// ---------------------------------------------------------------- 白名单（点名 + 理由）

const WHITELISTS = {
  1: new Map([
    [
      "frontend/src/app/(main)/MainLayoutInner.tsx",
      "DEC-075 P1：全站唯一 .container-page 的宿主。容器归壳层所有，这一个文件本来就该写它。",
    ],
  ]),
  2: new Map([
    [
      "frontend/src/lib/examLevels.ts",
      "题库等级的功能性多色 chip（等级即语义色），调色板是设计的一部分，没有语义 token 能表达。",
    ],
    [
      "frontend/src/lib/avatar.ts",
      "说话人头像色板：按 id 哈希取一组固定色，颜色本身就是标识，逐个建 token 才是过度设计。",
    ],
    ["frontend/src/lib/examLevels.test.ts", "断言上面那套功能色映射，必须能写出原始类名。"],
    ["frontend/src/lib/avatar.test.ts", "断言头像色板映射，必须能写出原始类名。"],
    [
      "frontend/src/lib/utils.test.ts",
      "cn() 的合并测试，故意用调色板类名当样本（与设计系统无关）。",
    ],
  ]),
  3: new Map(),
  4: new Map([
    [
      "frontend/src/app/(admin)/admin/login/page.tsx",
      "登录页是独立入口（无壳层、无 ui/PageHeader 可挂），自带两段标题。",
    ],
  ]),
  5: new Map(),
  6: new Map(),
  7: new Map(),
  8: new Map([
    [
      "frontend/src/app/(main)/MainLayoutInner.tsx",
      "DEC-075 P1：全站唯一的 <main> landmark 的宿主（同时是唯一 .container-page 宿主）。",
    ],
  ]),
};

// ---------------------------------------------------------------- 规则定义

const PALETTE =
  "slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose";
const COLOR_PREFIX =
  "bg|text|border|divide|ring|outline|fill|stroke|from|via|to|decoration|caret|accent|placeholder";
const SHADE = "50|100|200|300|400|500|600|700|800|900|950";
// 例：bg-blue-100、text-slate-700/60、border-t-red-200、decoration-sky-400
const RAW_PALETTE = new RegExp(
  `\\b(?:${COLOR_PREFIX})(?:-(?:[trblxyse]|offset))?-(?:${PALETTE})-(?:${SHADE})\\b`,
  "g"
);

// 只扫 `rounded-<后缀>` 形态：裸 `rounded` 不在本条规则的射程内（DEC-075 原文是
// 「允许集外的 `rounded-*`」），也就不会被英文散文里的 "rounded" 误伤。
const ROUNDED_TOKEN = /\brounded-[A-Za-z0-9_.\[\]%/:-]+/g;
const ROUNDED_ALLOWED = /^rounded-(?:(?:t|r|b|l|ss|se|ee|es)-)?(?:sm|md|lg|pill|full|none)$/;

// 规则 5：任意值 hex 颜色。`border-[#2c2c2c]` / `hover:border-[#4a4a4a]` 一类——
// 绕过 token 体系私设颜色，暗色模式翻不了，也不受设计评审约束。
const HEX_COLOR = new RegExp(`\\b(?:${COLOR_PREFIX})-\\[#[0-9a-fA-F]{3,8}\\]`, "g");

// 规则 6：无色阶的 white/black。分三档判定（叠加层 / 面 / 前景），口径见文件头。
// 组：1=变体前缀(hover:…) 2=颜色工具类前缀 3=颜色 4=透明度修饰符（含斜杠）
// 结尾用 `(?![-\w])` 而不是 `\b`：`bg-white/[0.06]` 的结尾是 `]`，`]` 与空格之间
// 没有词边界，用 `\b` 会把透明度修饰符吃掉、误判成裸用。
const WHITE_BLACK = new RegExp(
  `\\b((?:[a-z-]+:)*)(${COLOR_PREFIX})-(white|black)(/(\\[[^\\]]+\\]|\\d{1,3}))?(?![-\\w])`,
  "g"
);
// 这些前缀的颜色落在「面」上（背景 / 渐变端点），不是字色
const SURFACE_PREFIXES = new Set(["bg", "from", "via", "to"]);

/**
 * 规则 6 的判定：返回 true = 违规。
 * - 带透明度修饰符 → 叠加层，允许。
 * - 黑色 → 面与前景都要走语义 token，违规。
 * - 白色且是「面」→ 违规；白色且是前景/描边 → 允许（深底白字是本仓常态）。
 */
function isWhiteBlackViolation(_token, match) {
  const prefix = match[2];
  const color = match[3];
  const opacity = match[4];
  if (opacity) return false;
  if (color === "black") return true;
  return SURFACE_PREFIXES.has(prefix);
}

const RULES = [
  {
    id: 1,
    name: "页面不得自带容器类",
    files: (f) => isApp(f) && isTs(f),
    pattern: /\bcontainer-(?:page|wide)\b/g,
  },
  {
    id: 2,
    name: "不得写原始调色板工具类",
    files: (f) => f.startsWith(SRC) && isTs(f),
    pattern: RAW_PALETTE,
  },
  {
    id: 3,
    name: "rounded-* 只允许 sm|md|lg|pill|full|none",
    files: (f) => f.startsWith(SRC) && isTsx(f),
    pattern: ROUNDED_TOKEN,
    filter: (token) => !ROUNDED_ALLOWED.test(token),
  },
  {
    id: 4,
    name: "page.tsx 不得自写 <h1",
    files: (f) => isPage(f),
    pattern: /<h1[\s>]/g,
  },
  {
    id: 5,
    name: "不得写任意值 hex 颜色",
    files: (f) => f.startsWith(SRC) && isTs(f),
    pattern: HEX_COLOR,
  },
  {
    id: 6,
    name: "无色阶 white/black 不得当面用",
    files: (f) => f.startsWith(SRC) && isTs(f),
    pattern: WHITE_BLACK,
    filter: (token, match) => isWhiteBlackViolation(token, match),
  },
  {
    id: 7,
    name: "实心主操作不得用 brand-500 配白字",
    files: (f) => f.startsWith(SRC) && isTs(f),
    pattern: /\bbg-brand-500\b/g,
    // className 常折成多行：按「当前行 + 后两行」判定
    context: 2,
    filter: (token, match, window) => window.includes("text-on-primary"),
  },
  {
    id: 8,
    name: "(main) 下不得自写 <main>",
    files: (f) => isMainShell(f) && isTs(f),
    pattern: /<main\b/g,
  },
  {
    id: 9,
    name: "实心主操作不得用 brand-500 配裸白字",
    files: (f) => f.startsWith(SRC) && isTs(f),
    // 排除 `/10` 之类的半透明底：那是浅色 tint，不承载白字
    pattern: /\bbg-brand-500(?![/\w-])/g,
    // 只看同一行：跨行的 `text-white` 多半是子元素图标压在 brand-500 面上
    // （播放/排名角标），非文本对比度归 WCAG 1.4.11，不在这条射程内。
    filter: (token, match, line) => /\btext-white(?![/\w-])/.test(line),
  },
];

// ---------------------------------------------------------------- 执行

const scanned = new Set();
const violations = [];
const whitelistHits = new Map();

for (const rule of RULES) {
  const wl = WHITELISTS[rule.id] ?? new Map();
  for (const [key] of wl) whitelistHits.set(`${rule.id}:${key}`, false);

  for (const abs of allSrc) {
    if (!rule.files(abs)) continue;
    const file = rel(abs);
    scanned.add(file);

    const lines = readFileSync(abs, "utf8").split(/\r?\n/);
    let fileHit = false;
    lines.forEach((line, i) => {
      rule.pattern.lastIndex = 0;
      // `context` 让规则可以看「当前行 + 后 N 行」：多行 className 里的组合才判得准
      const hay = rule.context ? lines.slice(i, i + rule.context + 1).join(" ") : line;
      for (const m of line.matchAll(rule.pattern)) {
        if (rule.filter && !rule.filter(m[0], m, hay)) continue;
        fileHit = true;
        if (wl.has(file)) continue; // 白名单：命中只用来提示，不报违规
        violations.push({
          rule: rule.id,
          name: rule.name,
          file,
          line: i + 1,
          col: m.index + 1,
          token: m[0],
          text: line.trim(),
        });
      }
    });
    if (fileHit && wl.has(file)) whitelistHits.set(`${rule.id}:${file}`, true);
  }
}

// ---------------------------------------------------------------- 输出

console.log(`check-design-system：DEC-075 前端设计系统门禁（${RULES.length} 条规则）`);
console.log(`扫描 src/ 共 ${scanned.size} 个文件（按规则去重前）`);
for (const rule of RULES) {
  const n = violations.filter((v) => v.rule === rule.id).length;
  console.log(`  规则 ${rule.id} · ${rule.name}：${n === 0 ? "通过" : `${n} 处违规`}`);
}

if (violations.length) {
  console.log("\n违规明细：");
  for (const v of violations) {
    console.log(`  ✗ [规则 ${v.rule}] ${v.file}:${v.line}:${v.col}  ${v.token}`);
    console.log(`      ${v.text}`);
  }
}

const activeWhitelists = [];
for (const rule of RULES) {
  const wl = WHITELISTS[rule.id];
  if (!wl) continue;
  for (const [file, reason] of wl) {
    if (whitelistHits.get(`${rule.id}:${file}`)) activeWhitelists.push({ id: rule.id, file, reason });
  }
}
if (activeWhitelists.length) {
  console.log("\n生效中的白名单（点名文件 + 理由）：");
  for (const entry of activeWhitelists) {
    console.log(`  · 规则 ${entry.id} · ${entry.file}`);
    console.log(`      ${entry.reason}`);
  }
}

const staleWhitelist = [...whitelistHits.entries()].filter(([, hit]) => !hit);
if (staleWhitelist.length) {
  console.log("\n提示：以下白名单条目已不再命中任何违规，可以删掉：");
  for (const [key] of staleWhitelist) {
    const [id, file] = key.split(":");
    console.log(`  · 规则 ${id} · ${file}`);
  }
}

if (violations.length) {
  console.log(`\nFAIL：${violations.length} 处违规。`);
  process.exit(1);
}
console.log(`\nPASS：${RULES.length} 条规则全部通过。`);
