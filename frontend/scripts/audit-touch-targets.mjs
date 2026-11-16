#!/usr/bin/env node
/**
 * audit-touch-targets.mjs — 触控目标量具（wayfinder #20 · Destination §2）
 *
 * 做什么：在 375×812 @2x、`isMobile` + `hasTouch` 的 Chromium 里遍历「本图交付面」的
 * 路由与浮层态，枚举**所有**可点/可擦目标，逐条输出 `getBoundingClientRect()` 的 w/h，
 * 并按两个阈值判定：< 44（WCAG 2.2 SC 2.5.5 Enhanced，AAA）与 < 24（SC 2.5.8 Minimum，AA）。
 *
 * 为什么不手抄：数字全部由本脚本从真实 DOM 取，原始读数落 JSON，Markdown 表由 `--emit-md`
 * 从同一份 JSON 生成。两次运行之间若源码被人改动，读数的差异就是证据（见文档「两次跑」一节）。
 *
 * 口径（与文档同名小节一致，改这里等于改口径）：
 *   - 阈值来源：SC 2.5.8 = 24×24 CSS px（AA）；SC 2.5.5 = 44×44 CSS px（AAA）；Apple HIG
 *     iOS 默认控件 44×44 pt。44 不是合规线，是 AAA + 平台建议。
 *   - `<44` = w < 44 || h < 44（SC 要求「能放进一个对齐的 44×44 实心方块」，两个维度都要够）。
 *   - `wcag258`：
 *       pass           ≥24×24
 *       pass-spacing   <24，但以目标外接盒中心为心、直径 24 的圆不与任何其它目标（或另一个
 *                      未达标目标的圆）相交 —— SC 2.5.8 的 Spacing 豁免
 *       exempt-inline  行内目标（行高约束），SC 2.5.8/2.5.5 的 Inline 豁免
 *       fail           剩余情况
 *   - `wcag255`：pass / exempt-inline / fail（AAA，没有 Spacing 豁免）。
 *   - `criticalPath`：见 MOBILE_CRITICAL 注释 —— 本图交付面（壳层 + 播放页交互面 + 登录入口）。
 *
 * 用法：
 *   node frontend/scripts/audit-touch-targets.mjs                 # 用 auto-mint 铸 token
 *   SEE_WORD_TOKEN=... node frontend/scripts/audit-touch-targets.mjs
 *   node frontend/scripts/audit-touch-targets.mjs --out docs/.../touch-targets-375.json
 *   node frontend/scripts/audit-touch-targets.mjs --emit-md        # 从 JSON 打印 Markdown 表
 *
 * 退出码：0 = 跑完（有 <44 目标不算失败，这是测量不是门禁）；1 = 环境/导航失败。
 */

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const FRONTEND = resolve(HERE, "..");
const REPO = resolve(FRONTEND, "..");

// ---------------------------------------------------------------- 参数

const argv = process.argv.slice(2);
function arg(name, fallback = null) {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[i + 1] : fallback;
}
const has = (name) => argv.includes(`--${name}`);

const BASE_URL = arg("base-url", process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000");
const OUT =
  arg("out") ||
  resolve(REPO, "docs/design/mobile/destination/readings/touch-targets-375.json");
const EMIT_MD = has("emit-md");
const SETTLE_MS = Number(arg("settle", "450"));
const VIDEO_ID_ARG = arg("video-id");
const HEADED = has("headed");
/** 冒烟用：只跑 route+state 里含这个子串的条目。全量跑不要带。 */
const ONLY = arg("only");

/** 参考机型：与 frontend/src/lib/watchLayout.ts 同一口径。 */
const VIEWPORT = { width: 375, height: 812 };
const DEVICE_SCALE_FACTOR = 2;
const UA =
  "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 " +
  "(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1";

/** 短视口 —— 只为一件事：触发 `ShadowingDrawer` 的第二档（顶边钉画框下沿）。 */
const SHORT_VIEWPORT = { width: 375, height: 700 };

/**
 * 本图（wayfinder #20）的交付面 =「移动端关键路径」。
 *
 * 判据是**容器归属**，不是「这个控件重不重要」：落在壳层常驻控件（顶栏 / 底栏）或播放页交互面
 * （画框、入画字幕、控制条、词卡浮层、跟读抽屉、伴侣条动作行）里的目标才算，`/login` 的表单
 * 是唯一入口所以整体计入。列表项 / 卡片 / 文稿列表 / 个人页设置项一律**不**计入 ——
 * 不是它们不该够大，而是本图不交付它们；把全站无障碍审计混进这份基线会让「关键路径 <44 几条」
 * 失去意义。全站读数仍在 JSON 里，逐条带 criticalPath 字段。
 */
const CRITICAL_CONTAINERS = [
  "header",
  // 观看页（DEC-069 / #31）在 `/watch/*` 换掉壳的两栏：44px 顶栏 + 常规流底栏。
  // 这两个是移动端播放页现在唯一常驻的控件面。
  '[data-testid="watch-top-bar"]',
  '[data-testid="watch-bottom-bar"]',
  // 其他路由仍是 5 Tab 底栏。
  '[data-testid="mobile-tab-bar"]',
  // 播放页交互面：画框（移动端零覆盖物，点它只切播放/暂停）、当前句卡（点词锚点）、
  // 两个浮层。桌面专属的 `controls-bar` 也留着 —— 375 档量不到，但量具同一份跑 1280 时要用。
  '[data-testid="video-frame"]',
  '[data-testid="current-sentence-card"]',
  // DEC-073：当前句带内新增的展开开关（44×24，只有超预算长句才出现）。
  '[data-testid="current-sentence-expand"]',
  '[data-testid="controls-bar"]',
  '[data-testid="word-tooltip"]',
  '[data-testid="watch-more-sheet"]',
  '[data-testid="shadowing-drawer"]',
];

/** 量具版本：口径/判据一改就 +1，写进 JSON 的 meta，便于判断两份读数能不能比。 */
// rev6（2026-10-02，DEC-069）：关键路径容器与枚举目标改成壳层两栏 —— 旧读数（rev5 及以前）
// 量的是入画字幕 / 画框内覆盖物 / 5 Tab 底栏，与现在的 DOM 不是同一批目标，**不可直接比较**。
// rev7（2026-10-11，DEC-073）：移动端当前句带改成三行（计数与展开开关进元信息行）、文稿改页级
// 滚动、壳顶栏级别药丸改浅色 —— 播放页的可点目标集合变了，rev6 读数不可直接对比。
// 行内词热区（`.now-sub-word`）的 Inline 豁免仍在（见 EXPLICIT 与 inlineConstrained）。
const SCRIPT_REVISION = 7;

// ---------------------------------------------------------------- 路由与状态

/**
 * 每个 entry = 一次独立的页面加载（状态之间不共享，读数才互不污染）。
 * `prepare` 在页面稳定后、枚举前执行。
 */
function routePlan(videoId) {
  const watch = `/watch/${videoId}`;
  return [
    { route: "/", state: "base", label: "首页" },
    { route: "/vocabulary", state: "base", label: "词汇训练" },
    { route: "/practice", state: "base", label: "练习" },
    { route: "/profile", state: "base", label: "我的" },
    {
      route: "/login",
      state: "base",
      label: "登录（匿名）—— 唯一入口，整表单计入关键路径",
      anonymous: true,
      allCritical: true,
    },
    { route: watch, state: "base", label: "播放页·静息（画面零文字、当前句卡、壳底栏四键）" },
    {
      route: watch,
      state: "overlay-more-sheet",
      label: "播放页·⋯ 面板（语言/字号/倍速/来源版权/动作行；DEC-069 之后移动端唯一抽屉）",
      prepare: "openMoreSheet",
    },
    {
      route: watch,
      state: "overlay-wordcard",
      label: "播放页·词卡浮层（#27 乙）",
      prepare: "openWordCard",
    },
    {
      route: watch,
      state: "overlay-drawer-rec",
      label: "播放页·跟读抽屉半屏 / 录音中（#26 乙；入口键「录音」直接进录音态）",
      prepare: "drawerRecord",
    },
    {
      route: watch,
      state: "overlay-drawer-review",
      label: "播放页·跟读抽屉半屏 / 回放态",
      prepare: "drawerReview",
    },
    {
      route: watch,
      state: "overlay-drawer-tall",
      label: "播放页·抽屉第二档（顶边钉画框下沿；375×812 触发不到，用 375×700）",
      prepare: "drawerRecord",
      viewport: SHORT_VIEWPORT,
    },
    {
      route: watch,
      state: "overlay-drawer-history",
      label:
        "播放页·跟读抽屉 / 回放态 + 已保存（**唯一允许写库的一态**：量 D10 进度条标记与「最近跟读」行）",
      prepare: "drawerReview",
      allowWrites: true,
    },
  ];
}

// ---------------------------------------------------------------- 环境

function gitSnapshot() {
  const run = (cmd) => {
    const r = spawnSync(cmd, { cwd: REPO, encoding: "utf8", shell: true });
    return r.status === 0 ? r.stdout.trim() : `<${cmd} failed: ${r.status}>`;
  };
  const porcelain = run("git status --porcelain");
  return {
    head: run("git rev-parse HEAD"),
    headShort: run("git rev-parse --short HEAD"),
    headSubject: run("git log -1 --pretty=%s"),
    statusPorcelain: porcelain ? porcelain.split("\n") : [],
    dirty: Boolean(porcelain),
    capturedAt: new Date().toISOString(),
  };
}

/** 用后端自己的 create_token 铸 JWT（与 e2e helpers.ts:110 注入的是同一种票）。 */
function mintToken() {
  if (process.env.SEE_WORD_TOKEN) return { token: process.env.SEE_WORD_TOKEN, userId: "env" };
  const py = resolve(REPO, "backend/.venv/Scripts/python.exe");
  if (!existsSync(py)) throw new Error(`no backend venv python at ${py}`);
  const prog = [
    "import asyncio",
    "from sqlalchemy import text",
    "from app.core.database import get_session_maker",
    "from app.core.security import create_token",
    "async def m():",
    "    async with get_session_maker()() as s:",
    '        uid = (await s.execute(text("select id from users order by onboarding_completed desc nulls last, created_at limit 1"))).scalar()',
    "        if uid is None: raise SystemExit('no users in DB')",
    "        print(create_token(str(uid)))",
    "        print(str(uid))",
    "asyncio.run(m())",
  ].join("\n");
  const r = spawnSync(py, ["-c", prog], { cwd: resolve(REPO, "backend"), encoding: "utf8" });
  const lines = (r.stdout || "").trim().split("\n");
  const userId = lines.pop();
  const token = lines.pop();
  if (!token || token.length < 40) {
    throw new Error(`token mint failed: status=${r.status} out=${r.stdout} err=${r.stderr}`);
  }
  return { token, userId };
}

function firstReadyVideoId() {
  if (VIDEO_ID_ARG) return VIDEO_ID_ARG;
  const py = resolve(REPO, "backend/.venv/Scripts/python.exe");
  const prog = [
    "import asyncio",
    "from sqlalchemy import text",
    "from app.core.database import get_session_maker",
    "async def m():",
    "    async with get_session_maker()() as s:",
    '        v = (await s.execute(text("select id from videos where status = \'ready\' order by created_at limit 1"))).scalar()',
    "        print(v)",
    "asyncio.run(m())",
  ].join("\n");
  const r = spawnSync(py, ["-c", prog], { cwd: resolve(REPO, "backend"), encoding: "utf8" });
  const id = (r.stdout || "").trim().split("\n").pop();
  if (!id || !/^[0-9a-f-]{36}$/.test(id)) throw new Error(`no ready video: ${r.stdout} ${r.stderr}`);
  return id;
}

// ---------------------------------------------------------------- 页面内枚举

/**
 * 在页面里跑的采集函数。注意：这里**不能**引用 Node 侧作用域（会被序列化送进浏览器）。
 * 返回 { targets, geometry, notes }。
 */
function collectInPage(opts) {
  const { criticalContainers, viewportHeight, allCritical } = opts;

  const CSS_ESCAPE = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : s.replace(/["\\]/g, "\\$&"));

  function stableSelector(el) {
    const parts = [];
    let node = el;
    let depth = 0;
    while (node && node.nodeType === 1 && depth < 6) {
      const tag = node.tagName.toLowerCase();
      if (tag === "body" || tag === "html") {
        parts.unshift(tag);
        break;
      }
      const testid = node.getAttribute("data-testid");
      const aria = node.getAttribute("aria-label");
      const id = node.id;
      let seg = tag;
      if (id) seg += `#${CSS_ESCAPE(id)}`;
      if (testid) seg += `[data-testid="${testid}"]`;
      else if (aria) seg += `[aria-label="${aria.replace(/"/g, '\\"')}"]`;
      else {
        const parent = node.parentElement;
        if (parent) {
          const sameTag = [...parent.children].filter((c) => c.tagName === node.tagName);
          if (sameTag.length > 1) seg += `:nth-of-type(${sameTag.indexOf(node) + 1})`;
        }
      }
      parts.unshift(seg);
      if (id || testid) break;
      node = node.parentElement;
      depth += 1;
    }
    return parts.join(" > ");
  }

  function textOf(el) {
    const t = (el.innerText || el.textContent || "").replace(/\s+/g, " ").trim();
    return t.length > 80 ? `${t.slice(0, 77)}…` : t;
  }

  function nameOf(el) {
    return (
      el.getAttribute("aria-label") ||
      textOf(el) ||
      el.getAttribute("title") ||
      el.getAttribute("placeholder") ||
      el.getAttribute("name") ||
      (el.getAttribute("alt") ?? "") ||
      ""
    )
      .toString()
      .slice(0, 120);
  }

  function kindOf(el) {
    const tag = el.tagName.toLowerCase();
    if (tag === "a") return "link";
    if (tag === "button") return "button";
    if (tag === "input") {
      const t = el.getAttribute("type") || "text";
      return t === "range" ? "input-range" : `input-${t}`;
    }
    if (tag === "select") return "select";
    if (tag === "textarea") return "textarea";
    if (tag === "summary") return "summary";
    if (tag === "label") return "label";
    if (tag === "video") return "video";
    if (el.classList.contains("now-sub-word")) return "inline-word";
    const role = el.getAttribute("role");
    if (role) return `role-${role}`;
    if (el.hasAttribute("onclick")) return "onclick";
    return "pointer-cursor";
  }

  /** 是否落在关键路径容器里（含自身）。 */
  function inCritical(el) {
    for (const sel of criticalContainers) {
      try {
        if (el.closest(sel)) return true;
      } catch {
        /* 选择器写错不该让整次采集挂掉 */
      }
    }
    return false;
  }

  /** 行内豁免代理判据：行内显示 + 同一段文本里还有别的兄弟内容。 */
  function inlineConstrained(el, cs) {
    if (!cs.display.startsWith("inline")) return false;
    const parent = el.parentElement;
    if (!parent) return false;
    const parentText = (parent.textContent || "").trim();
    const own = (el.textContent || "").trim();
    return parentText.length > own.length + 1;
  }

  // ---- 候选：显式标签 + 「点了有反应」的启发式（React 17+ 事件委托 → 没有 onclick 属性，
  //      所以用 cursor:pointer 兜住挂在 div/span 上的 onClick）
  const EXPLICIT = [
    "button",
    "a[href]",
    '[role="button"]',
    '[role="link"]',
    '[role="switch"]',
    '[role="tab"]',
    '[role="checkbox"]',
    "[role=button]",
    "input",
    "select",
    "textarea",
    "summary",
    "[onclick]",
    "label[for]",
    "[contenteditable=true]",
    "[draggable=true]",
    ".now-sub-word",
    '[data-testid$="-grab"]',
    // 播放页覆盖面：移动端是当前句卡（点空白 = 播放/暂停，点词 = 词卡），
    // 桌面端还有 `VideoControls` 的根（点它 = 播放/暂停或点出控制条）。
    // 这两条不是标签语义能表达的，写死源码里的字面量（INV-004：v4 CSS-first，类名就是源码）。
    "div.absolute.inset-0.z-10",
  ];
  const explicitSet = new Set();
  for (const sel of EXPLICIT) {
    for (const el of document.querySelectorAll(sel)) explicitSet.add(el);
  }
  // 裸 <video>：只有带原生 controls 时它自己才是目标（本项目是 controls=false + 自定义控制条，
  // 点画面落在 VideoControls 的覆盖层上）。
  for (const el of document.querySelectorAll("video")) {
    if (el.hasAttribute("controls")) explicitSet.add(el);
  }

  /** 祖先已经是目标 → 这个孩子只是继承了 cursor:pointer，不是独立目标。 */
  const inheritsTarget = (el) => {
    let p = el.parentElement;
    while (p && p !== document.body) {
      if (explicitSet.has(p)) return true;
      p = p.parentElement;
    }
    return false;
  };

  for (const el of document.querySelectorAll("div,span,li,td,svg,p,h3")) {
    if (explicitSet.has(el)) continue;
    if (getComputedStyle(el).cursor !== "pointer") continue;
    if (inheritsTarget(el)) continue;
    explicitSet.add(el);
  }

  const candidates = [...explicitSet];
  const visible = [];
  for (const el of candidates) {
    const cs = getComputedStyle(el);
    if (cs.display === "none" || cs.visibility === "hidden") continue;
    if (Number(cs.opacity) === 0) continue;
    if (el.getAttribute("aria-hidden") === "true") continue;
    if (el.hasAttribute("hidden")) continue;
    if (cs.pointerEvents === "none") continue;
    const r = el.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    visible.push({ el, cs, r });
  }

  // 包含关系两趟走完（O(n·depth)），别用 n² 次 el.contains()
  const visSet = new Set(visible.map((v) => v.el));
  const hasTargetChild = new Set();
  for (const { el } of visible) {
    let p = el.parentElement;
    while (p && p !== document.body) {
      if (visSet.has(p)) hasTargetChild.add(p);
      p = p.parentElement;
    }
  }

  // ---- 有效命中区：元素盒 ≠ 目标区。`::after{inset:-4px -1px}` 这类伪元素外扩真的接指针
  //      真的接指针（WCAG 的 target 定义是「会接受指针动作的显示区域」），相邻元素的 ::after
  //      又会互相压。所以对「两边有一边 < 48」的目标，从中心线向外逐像素用 elementFromPoint
  //      探到连续可命中的范围，作为 effective 盒；原始 rect 照留。只探小目标：探针是 O(pixels)。
  const PROBE_LIMIT = 24;
  /** dev 的 Next 浮标（`<nextjs-portal>`）会在左下角抢命中 —— 产品里不存在，命中判定时跳过它。 */
  const topAt = (x, y) => {
    const stack = document.elementsFromPoint(x, y);
    for (const e of stack) {
      if (e.tagName && e.tagName.toLowerCase() === "nextjs-portal") continue;
      return e;
    }
    return null;
  };
  function probe(el, r) {
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    // 探针不适用的两种情况，一律回落到元素盒（否则会造出假的「被盖/变小」）：
    //  a) 中心点在视口外 —— elementFromPoint 直接返回 null；
    //  b) 行内元素跨行 —— getBoundingClientRect 是几行的并集，其中心可能落在两行之间的空隙里。
    const outside = cx < 0 || cy < 0 || cx > window.innerWidth || cy > window.innerHeight;
    const multiRect = el.getClientRects().length > 1;
    if (outside || multiRect) {
      return {
        reliable: false,
        reason: outside ? "center outside viewport" : "inline element spans multiple line boxes",
        selfHit: null,
        probe: null,
        hitW: Math.round(r.width * 10) / 10,
        hitH: Math.round(r.height * 10) / 10,
        hitX: Math.round(r.left * 10) / 10,
        hitY: Math.round(r.top * 10) / 10,
        occluder: null,
      };
    }
    // 祖先不算命中：覆盖在目标之上的元素才是要抓的（返回键被控制条盖住那种）。
    const hitsSelf = (x, y) => {
      const found = topAt(x, y);
      return !!found && (found === el || el.contains(found));
    };
    const selfHit = hitsSelf(cx, cy);
    const scan = (dx, dy) => {
      let d = 0;
      while (d < PROBE_LIMIT) {
        const nx = cx + dx * (d + 1);
        const ny = cy + dy * (d + 1);
        if (nx < 0 || ny < 0 || nx > window.innerWidth || ny > window.innerHeight) break;
        if (!hitsSelf(nx, ny)) break;
        d += 1;
      }
      return d;
    };
    const up = scan(0, -1);
    const down = scan(0, 1);
    const left = scan(-1, 0);
    const right = scan(1, 0);
    // 有效命中区 = 元素盒 ∪ 从中心向四个方向探到的可达范围。
    // 取并集而不是取探到的矩形：探针从中心出发，元素自身边界那半像素会先被相邻元素接走
    // （44×44 会被量成 43×43），拿它当"目标变小了"是假阳性。伪元素 / 负外边距外扩（例：词的
    // 热区用 `-mb-1 pb-1` 往下多接 4px）是真的按到了盒子外面，并集捕得到 —— 探到的四个方向
    const top = Math.min(r.top, cy - up);
    const bottom = Math.max(r.bottom, cy + down);
    const l = Math.min(r.left, cx - left);
    const rt = Math.max(r.right, cx + right);
    const hitW = Math.round((rt - l) * 10) / 10;
    const hitH = Math.round((bottom - top) * 10) / 10;
    return {
      reliable: true,
      reason: null,
      selfHit,
      probe: { up, down, left, right },
      hitW,
      hitH,
      hitX: Math.round(l * 10) / 10,
      hitY: Math.round(top * 10) / 10,
      occluder: selfHit
        ? null
        : (() => {
            const f = topAt(cx, cy);
            if (!f) return "null";
            return `${f.tagName.toLowerCase()}.${(f.getAttribute("class") || "").slice(0, 80)}`;
          })(),
    };
  }

  const targets = visible.map(({ el, cs, r }, i) => {
    let nested = false;
    let p = el.parentElement;
    while (p && p !== document.body) {
      if (visSet.has(p)) {
        nested = true;
        break;
      }
      p = p.parentElement;
    }
    const contains = hasTargetChild.has(el);
    const w = Math.round(r.width * 10) / 10;
    const h = Math.round(r.height * 10) / 10;
    const critical = allCritical || inCritical(el);
    // 只对「有一边 < 48」的目标做探针（探针是逐像素的），大目标不必探。
    const hit = w < 48 || h < 48 ? probe(el, r) : null;
    const effW = hit ? hit.hitW : w;
    const effH = hit ? hit.hitH : h;
    const effL = hit ? hit.hitX : r.left;
    const effT = hit ? hit.hitY : r.top;
    const effR = effL + effW;
    const effB = effT + effH;
    return {
      id: `t${String(i + 1).padStart(4, "0")}`,
      selector: stableSelector(el),
      domPath: (() => {
        const p = [];
        let n = el;
        while (n && n.nodeType === 1 && p.length < 5) {
          p.unshift(n.tagName.toLowerCase());
          n = n.parentElement;
        }
        return p.join(">");
      })(),
      tag: el.tagName.toLowerCase(),
      kind: kindOf(el),
      role: el.getAttribute("role"),
      testid: el.getAttribute("data-testid"),
      ariaLabel: el.getAttribute("aria-label"),
      title: el.getAttribute("title"),
      text: textOf(el),
      name: nameOf(el),
      type: el.getAttribute("type"),
      disabled: el.disabled === true || el.getAttribute("aria-disabled") === "true",
      x: Math.round(r.left * 10) / 10,
      y: Math.round(r.top * 10) / 10,
      w,
      h,
      lt44: w < 44 || h < 44,
      lt24: w < 24 || h < 24,
      // 有效命中区（含 ::after 外扩、扣掉被相邻元素压掉的部分）—— 判定用这一组
      effW,
      effH,
      effLt44: effW < 44 || effH < 44,
      effLt24: effW < 24 || effH < 24,
      hitProbe: hit,
      /** 目标中心点上的最上层**产品**元素不是它自己（也不是它的后代）→ 它接不到指针。 */
      occluded: hit && hit.reliable ? !hit.selfHit : false,
      criticalPath: critical,
      inViewport: r.bottom > 0 && r.top < window.innerHeight,
      aboveFold: r.top < viewportHeight,
      nestedInTarget: nested,
      containsTarget: contains,
      inlineConstrained: inlineConstrained(el, cs),
      classes: (el.getAttribute("class") || "").slice(0, 200),
      css: {
        display: cs.display,
        width: cs.width,
        height: cs.height,
        minHeight: cs.minHeight,
        minWidth: cs.minWidth,
        padding: cs.padding,
        fontSize: cs.fontSize,
        lineHeight: cs.lineHeight,
        cursor: cs.cursor,
        touchAction: cs.touchAction,
      },
      // 半径 12 的间距圆 —— SC 2.5.8 的 Spacing 豁免判据（脚本随后做相交检查）。
      // 用有效盒，不用原始 rect：SC 判的是目标区。
      _circle: { cx: effL + effW / 2, cy: effT + effH / 2, r: 12 },
      _rect: { l: effL, t: effT, r: effR, b: effB },
    };
  });

  // ---- SC 2.5.8 判定（含 Spacing 豁免）
  const circleHitsRect = (c, q) => {
    const nx = Math.max(q.l, Math.min(c.cx, q.r));
    const ny = Math.max(q.t, Math.min(c.cy, q.b));
    return (c.cx - nx) ** 2 + (c.cy - ny) ** 2 < c.r * c.r;
  };
  const circleHitsCircle = (a, b) => (a.cx - b.cx) ** 2 + (a.cy - b.cy) ** 2 < (a.r + b.r) ** 2;

  for (const t of targets) {
    // 祖先/后代候选是同一个目标的不同包装，不算「相邻目标」。
    const others = targets.filter(
      (o) =>
        o.id !== t.id &&
        // 排除包含关系（祖先/后代候选是同一个目标的不同包装，不是「相邻目标」）
        !(
          (o._rect.l <= t._rect.l &&
            o._rect.t <= t._rect.t &&
            o._rect.r >= t._rect.r &&
            o._rect.b >= t._rect.b) ||
          (t._rect.l <= o._rect.l &&
            t._rect.t <= o._rect.t &&
            t._rect.r >= o._rect.r &&
            t._rect.b >= o._rect.b)
        )
    );
    let spacingOk = true;
    for (const o of others) {
      if (circleHitsRect(t._circle, o._rect)) {
        spacingOk = false;
        break;
      }
      if (o.effLt24 && circleHitsCircle(t._circle, o._circle)) {
        spacingOk = false;
        break;
      }
    }
    t.spacingClearance24 = spacingOk;
    t.wcag258 = !t.effLt24
      ? "pass"
      : t.inlineConstrained
        ? "exempt-inline"
        : spacingOk
          ? "pass-spacing"
          : "fail";
    t.wcag255 = !t.effLt44 ? "pass" : t.inlineConstrained ? "exempt-inline" : "fail";
  }
  // 几何辅助字段只用于上面那趟判定，出页面之前删掉（_rect/_circle 在判定中还要用，
  // 所以只能等整趟跑完再删 —— 边判边删会让后面的目标读到 undefined）。
  for (const t of targets) {
    delete t._circle;
    delete t._rect;
  }

  // ---- 结构性读数（同一份量具里顺手记，供文档引用与 INV 交叉核对）
  const box = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      x: +r.left.toFixed(1),
      y: +r.top.toFixed(1),
      w: +r.width.toFixed(1),
      h: +r.height.toFixed(1),
    };
  };
  const video = document.querySelector("video");
  const geometry = {
    innerHeight: window.innerHeight,
    innerWidth: window.innerWidth,
    dpr: window.devicePixelRatio,
    mainTop: (() => {
      const m = document.querySelector("main#main-scroll") || document.querySelector("main");
      return m ? +m.getBoundingClientRect().top.toFixed(1) : null;
    })(),
    docScroll: {
      scrollWidth: document.documentElement.scrollWidth,
      clientWidth: document.documentElement.clientWidth,
    },
    frame: box("video"),
    videoFrame: box('[data-testid="video-frame"]'),
    watchTopBar: box('[data-testid="watch-top-bar"]'),
    watchBottomBar: box('[data-testid="watch-bottom-bar"]'),
    watchProgress: box('[data-testid="watch-progress"]'),
    currentSentenceCard: box('[data-testid="current-sentence-card"]'),
    moreSheet: box('[data-testid="watch-more-sheet"]'),
    controlsBar: box('[data-testid="controls-bar"]'),
    tabBar: box('[data-testid="mobile-tab-bar"]'),
    header: box("header"),
    wordCard: box('[data-testid="word-tooltip"][data-variant="sheet"]'),
    drawer: box('[data-testid="shadowing-drawer"]'),
    videoPaused: video ? video.paused : null,
    videoReadyState: video ? video.readyState : null,
    videoCurrentTime: video ? +video.currentTime.toFixed(2) : null,
    videoHasControlsAttr: video ? video.hasAttribute("controls") : null,
    drawerTop: (() => {
      const d = document.querySelector('[data-testid="shadowing-drawer"]');
      return d ? +(d.style.top || "").replace("px", "") || null : null;
    })(),
  };

  const notes = [];
  if (
    location.pathname.startsWith("/watch") &&
    !document.querySelector('[data-testid="watch-bottom-bar"]')
  ) {
    notes.push("no watch-bottom-bar in this state (desktop width? see route plan)");
  }
  return { targets, geometry, notes };
}

// ---------------------------------------------------------------- 状态驱动

async function settle(page, ms = SETTLE_MS) {
  await page.waitForTimeout(ms);
}

/** 播放页通用开局：关教程浮层 → 冻结视频 → 回到「静息」态。返回 note 数组。 */
async function watchBoot(page, notes) {
  // 视频暂停：否则当前句随时间前进，两次跑的目标集合就不一样了。
  await page
    .waitForFunction(() => {
      const v = document.querySelector("video");
      return !!v && v.readyState >= 1;
    }, null, { timeout: 12000 })
    .catch(() => notes.push("video readyState<1 within 12s"));
  await page.evaluate(() => {
    const v = document.querySelector("video");
    if (v) {
      // 回到 0 秒再暂停：当前句由播放位置决定，不钉住它两次跑的字词集合就不一样。
      try {
        v.currentTime = 0;
      } catch {
        /* 元数据还没到时忽略 */
      }
      if (!v.paused) v.pause();
    }
  });

  // 贴顶常驻（useStickyPip）：读数针对**首屏内联**形态，所以先把滚动容器归零 ——
  // DEC-069 之后跟随态没有出口键了（那个 X 删了），滚回顶部就是解除办法。
  const scrolled = await page.evaluate(() => {
    const main = document.querySelector("main#main-scroll");
    const before = main ? main.scrollTop : window.scrollY;
    if (main) main.scrollTop = 0;
    else window.scrollTo(0, 0);
    return before;
  });
  notes.push(scrolled > 0 ? `scrolled to top (was ${scrolled})` : "already at top");
  await settle(page, 400);
}

const PREPARERS = {
  async openMoreSheet(page, notes) {
    await page.locator('[data-testid="watch-more-button"]').click();
    await page.waitForSelector('[data-testid="watch-more-sheet"]', { timeout: 6000 });
    await settle(page, 500);
    const bar = await page.locator('[data-testid="watch-bottom-bar"]').count();
    notes.push(
      bar === 0
        ? "⋯ 面板打开时底栏让位（count 0）—— 这是设计，不是缺陷"
        : `⋯ 面板打开时底栏仍在（count ${bar}），与设计不符`
    );
  },

  async openWordCard(page, notes) {
    await page.locator('[data-testid="current-sentence-card"] .now-sub-word').first().click();
    await page.waitForSelector('[data-testid="word-tooltip"][data-variant="sheet"]', {
      timeout: 6000,
    });
    // 词释是异步拉的（先「查询中…」）：等它落定，否则卡高两次跑不一样。
    await page
      .waitForFunction(
        () => {
          const el = document.querySelector('[data-testid="word-tooltip"][data-variant="sheet"]');
          return !!el && !el.textContent.includes("查询中");
        },
        null,
        { timeout: 8000 }
      )
      .catch(() => notes.push("word gloss still 查询中 after 8s"));
    await settle(page, 600);
  },

  async openDrawer(page, notes) {
    // DEC-069 之后移动端入口只有壳底栏那个键；点开先落在抽屉的 idle 档，
    // 由 `drawerRecord` 再点「开始跟读本句」进录音态。
    await page.locator('[data-testid="watch-shadowing"]').click();
    await page.waitForSelector('[data-testid="shadowing-drawer"]', { timeout: 6000 });
    await settle(page, 600);
  },

  async drawerRecord(page, notes, ctx) {
    await PREPARERS.openDrawer(page, notes, ctx);
    await page.getByRole("button", { name: "开始跟读本句" }).click();
    await page.waitForSelector('[data-testid="recording-timer"]', { timeout: 8000 });
    await settle(page, 600);
  },

  async drawerReview(page, notes, ctx) {
    await PREPARERS.drawerRecord(page, notes, ctx);
    await page.getByRole("button", { name: "停止录音" }).click();
    await page.getByRole("button", { name: "重录" }).waitFor({ timeout: 10000 });
    await settle(page, 700);
  },
};

// ---------------------------------------------------------------- 主流程

async function run() {
  const { chromium } = await import("playwright");

  const git = gitSnapshot();
  const { token, userId } = mintToken();
  const videoId = firstReadyVideoId();
  const plan = routePlan(videoId).filter((e) => !ONLY || `${e.route}${e.state}`.includes(ONLY));

  const browser = await chromium.launch({ headless: !HEADED });
  const consoleErrors = [];
  let suppressedConsoleErrors = 0;
  const results = [];

  for (const entry of plan) {
    const vp = entry.viewport || VIEWPORT;
    const context = await browser.newContext({
      viewport: vp,
      deviceScaleFactor: DEVICE_SCALE_FACTOR,
      isMobile: true,
      hasTouch: true,
      userAgent: UA,
      locale: "zh-CN",
    });
    const page = await context.newPage();
    const notes = [];

    // 注入：登录票（与 frontend/e2e/helpers.ts:110 同款：localStorage + 同名 cookie）、
    // 关教程浮层、关 CSS 过渡（读数取终值而不是动画中间帧）、假麦克风（抽屉能跑到录音/回放态）。
    await page.addInitScript(
      ({ t, anon }) => {
        if (!anon && t) {
          try {
            window.localStorage.setItem("seeword_token", t);
            document.cookie = `seeword_token=${t}; path=/`;
          } catch {
            /* about:blank 上写不了 localStorage，正式导航时会再跑一次 */
          }
        }
        try {
          window.localStorage.setItem("seeword_coach_done", "true");
        } catch {
          /* 同上 */
        }
        const style = document.createElement("style");
        style.textContent =
          "*,*::before,*::after{transition:none!important;animation-duration:0s!important;animation-delay:0s!important}";
        const attach = () => document.head && document.head.appendChild(style);
        if (document.head) attach();
        else document.addEventListener("DOMContentLoaded", attach);
      },
      { t: token, anon: Boolean(entry.anonymous) }
    );

    // 假麦克风（同 mobile-wordcard-drawer.spec.ts 的 mockMic）
    await page.addInitScript(() => {
      const track = { stop() {}, kind: "audio" };
      const fakeStream = { getTracks: () => [track] };
      Object.defineProperty(navigator, "mediaDevices", {
        configurable: true,
        value: { getUserMedia: async () => fakeStream },
      });
      class FakeMediaRecorder {
        state = "inactive";
        ondataavailable = null;
        onstop = null;
        static isTypeSupported() {
          return true;
        }
        start() {
          this.state = "recording";
        }
        stop() {
          this.state = "inactive";
          this.ondataavailable?.({
            data: new Blob([new Uint8Array([1, 2, 3])], { type: "audio/webm" }),
          });
          this.onstop?.();
        }
      }
      Object.defineProperty(window, "MediaRecorder", {
        configurable: true,
        value: FakeMediaRecorder,
      });
    });

    page.on("console", (m) => {
      if (m.type() !== "error") return;
      const url = (m.location && m.location().url) || "";
      // 我们自己掐掉的上传（route.abort）会在 console 里留一条 ERR_FAILED —— 那是量具干的，不是产品缺陷。
      if (/shadowing\/attempts/.test(url)) {
        suppressedConsoleErrors += 1;
        return;
      }
      consoleErrors.push(`[${entry.route} ${entry.state}] ${m.text()}`);
    });

    // 默认**不写库**：跟读录音的上传落库会让下一次跑多出「D10 进度条标记」与「最近跟读」两族目标，
    // 读数就不稳定了。除了唯一一态 `overlay-drawer-history`（它就是来量这两族的），
    // 其余状态把 POST /api/v1/shadowing/attempts 掐掉 —— 回放态的 UI 不依赖落库结果。
    if (!entry.allowWrites) {
      await page.route("**/api/v1/shadowing/attempts**", (route) =>
        route.request().method() === "POST" ? route.abort("failed") : route.continue()
      );
    } else {
      notes.push("allowWrites: 这一态会往本地 dev 库写一条跟读记录（其余状态不写）");
    }

    const url = `${BASE_URL}${entry.route}`;
    let ok = true;
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
      await page.waitForLoadState("networkidle", { timeout: 12000 }).catch(() => {
        notes.push("networkidle timeout (dev overlay / HMR socket keeps it busy)");
      });
      // 壳层 / 观看页两栏 / 登录表单出现即视为渲染完成
      await page
        .waitForSelector(
          'main#main-scroll, form, [data-testid="watch-bottom-bar"], [data-testid="mobile-tab-bar"]',
          { timeout: 20000 }
        )
        .catch(() => notes.push("no shell/form anchor found"));
      await page.evaluate(() => document.fonts && document.fonts.ready).catch(() => {});
      await settle(page, 700);

      if (entry.route.startsWith("/watch/")) await watchBoot(page, notes);
      if (entry.prepare) await PREPARERS[entry.prepare](page, notes, entry);
      await settle(page);

      const collected = await page.evaluate(collectInPage, {
        criticalContainers: CRITICAL_CONTAINERS,
        viewportHeight: vp.height,
        allCritical: Boolean(entry.allCritical),
      });

      const t = collected.targets;
      const summary = {
        total: t.length,
        lt44: t.filter((x) => x.lt44).length,
        lt24: t.filter((x) => x.lt24).length,
        lt44Eff: t.filter((x) => x.effLt44).length,
        lt24Eff: t.filter((x) => x.effLt24).length,
        critical: t.filter((x) => x.criticalPath).length,
        lt44Critical: t.filter((x) => x.lt44 && x.criticalPath).length,
        lt44CriticalEff: t.filter((x) => x.effLt44 && x.criticalPath).length,
        lt24Critical: t.filter((x) => x.lt24 && x.criticalPath).length,
        lt24CriticalEff: t.filter((x) => x.effLt24 && x.criticalPath).length,
        wcag258Fail: t.filter((x) => x.wcag258 === "fail").length,
        wcag255Fail: t.filter((x) => x.wcag255 === "fail").length,
        wcag258FailCritical: t.filter((x) => x.wcag258 === "fail" && x.criticalPath).length,
        occluded: t.filter((x) => x.occluded).length,
        occludedCritical: t.filter((x) => x.occluded && x.criticalPath).length,
      };

      results.push({
        route: entry.route,
        state: entry.state,
        label: entry.label,
        url: page.url(),
        title: await page.title(),
        viewport: { ...vp, deviceScaleFactor: DEVICE_SCALE_FACTOR, isMobile: true, hasTouch: true },
        anonymous: Boolean(entry.anonymous),
        summary,
        notes: [...notes, ...collected.notes],
        geometry: collected.geometry,
        targets: t,
      });
    } catch (err) {
      ok = false;
      results.push({
        route: entry.route,
        state: entry.state,
        label: entry.label,
        url,
        error: String(err && err.message ? err.message : err),
        summary: null,
        notes,
        targets: [],
      });
    }
    const s = results.at(-1).summary;
    process.stdout.write(
      `${ok ? "ok  " : "FAIL"} ${entry.route} [${entry.state}] ` +
        (s
          ? `targets=${s.total} <44=${s.lt44} <24=${s.lt24} 关键路径<44=${s.lt44Critical} ` +
            `有效<44=${s.lt44Eff} 有效<24=${s.lt24Eff} 被盖=${s.occluded}(关键路径 ${s.occludedCritical}) ` +
            `2.5.8fail=${s.wcag258Fail}\n`
          : "\n")
    );
    await context.close();
  }

  await browser.close();

  const doc = {
    $comment:
      "wayfinder #20 Destination §2 触控目标基线的原始读数。由 frontend/scripts/audit-touch-targets.mjs 生成；不要手改。",
    meta: {
      generatedAt: new Date().toISOString(),
      scriptRevision: SCRIPT_REVISION,
      baseUrl: BASE_URL,
      viewport: { ...VIEWPORT, deviceScaleFactor: DEVICE_SCALE_FACTOR, isMobile: true, hasTouch: true },
      userAgent: UA,
      videoId,
      /** 铸票用的用户（本地 dev 库第一行）；读数里的跟读记录属于这个用户。 */
      userId,
      probeLimitPx: 24,
      thresholds: {
        wcag258Min: 24,
        wcag255Enhanced: 44,
        source258: "https://www.w3.org/TR/WCAG22/#target-size-minimum",
        source255: "https://www.w3.org/TR/WCAG22/#target-size-enhanced",
        appleHig: "https://developer.apple.com/design/human-interface-guidelines/accessibility",
      },
      criticalPathContainers: CRITICAL_CONTAINERS,
      git,
    },
    consoleErrors,
    suppressedConsoleErrors,
    states: results,
  };

  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, `${JSON.stringify(doc, null, 2)}\n`, "utf8");
  console.log(`\n→ ${OUT}`);
  const all = results.flatMap((r) => r.targets);
  console.log(
    `合计 ${all.length} 个目标；<44 ${all.filter((t) => t.lt44).length}；<24 ${
      all.filter((t) => t.lt24).length
    }；关键路径 <44 ${all.filter((t) => t.lt44 && t.criticalPath).length}；` +
      `有效命中区 <44 ${all.filter((t) => t.effLt44).length}；2.5.8 fail ${
        all.filter((t) => t.wcag258 === "fail").length
      }`
  );
  if (consoleErrors.length) console.log(`console errors: ${consoleErrors.length}`);
}

// ---------------------------------------------------------------- Markdown 生成

/**
 * 合并同一「模式」的目标：只留**元素自身那一段** + **最近的稳定祖先**（带 data-testid / #id 的那段），
 * 并去掉 `:nth-of-type(n)`。理由：`#subtitle-137` 这种按行编号的 id 会让每一行都成一组，
 * 表里就会出现上百行同形状的记录 —— 那些逐条读数在 JSON 里，表里合并成一行 + 尺寸区间更可读。
 */
function groupKey(t) {
  const norm = (s) =>
    s
      .replace(/:nth-of-type\(\d+\)/g, "")
      // 按行编号的 id（`#subtitle-137`）与带时间的 aria-label（`已跟读，回到 0:07`）都要数字化，
      // 否则每一行都是独立一组，表里会出现上百行同形状的记录。
      .replace(/#([A-Za-z_-]*)\d+/g, "#$1{n}")
      .replace(/aria-label="[^"]*\d[^"]*"/g, 'aria-label="…{n}"');
  const parts = t.selector.split(" > ");
  const self = norm(parts[parts.length - 1]);
  const anchors = parts.slice(0, -1).filter((p) => /\[data-testid=|#/.test(p));
  const anchor = norm(anchors.length ? anchors[anchors.length - 1] : parts[0]);
  return [anchor, self, t.kind, t.role || "", t.testid || ""].join("|");
}

const dim = (arr) =>
  Math.min(...arr) === Math.max(...arr)
    ? `${Math.min(...arr)}`
    : `${Math.min(...arr)}–${Math.max(...arr)}`;
const flag = (v) => (v ? "**是**" : "·");
const esc = (s) => String(s || "—").replace(/\|/g, "\\|");
const sel = (s) => `\`${s.replace(/body > div:nth-of-type\(2\) > /, "").replace(/ \> /g, " › ")}\``;

/** 一组目标的一行。names 不同就折叠成两个示例 + 计数。 */
function rowOf(g, cols = "full") {
  const names = [...new Set(g.map((x) => x.name))];
  const shown = names.slice(0, 2).map(esc);
  const nameStr =
    names.length === 1
      ? shown[0]
      : `${shown.join(" / ")} 等 ${names.length} 种文案（共 ${g.length} 条）`;
  const w258 = [...new Set(g.map((x) => x.wcag258))].join(",");
  const base = `| ${sel(g[0].selector)} | ${nameStr} | ${g.length} | ${dim(g.map((x) => x.w))}×${dim(
    g.map((x) => x.h)
  )} | ${dim(g.map((x) => x.effW))}×${dim(g.map((x) => x.effH))}`;
  if (cols === "short") return `${base} |`;
  return `${base} | ${flag(g.some((x) => x.lt44))} | ${flag(g.some((x) => x.lt24))} | ${w258} | ${flag(
    g.some((x) => x.criticalPath)
  )} |`;
}

const HEAD_FULL = `| 目标（选择器） | 文案 / aria-label | n | rect w×h | 有效命中 w×h | <44 | <24 | 2.5.8 | 关键路径 |`;
const HEAD_SHORT = `| 目标（选择器） | 文案 / aria-label | n | rect w×h | 有效命中 w×h |`;
const SEP_FULL = `|---|---|---|---|---|---|---|---|---|`;
const SEP_SHORT = `|---|---|---|---|---|`;

function groupsOf(targets) {
  const m = new Map();
  for (const t of targets) {
    const k = groupKey(t);
    if (!m.has(k)) m.set(k, []);
    m.get(k).push(t);
  }
  return [...m.values()].sort(
    (a, b) => Math.min(...a.map((x) => Math.min(x.w, x.h))) - Math.min(...b.map((x) => Math.min(x.w, x.h)))
  );
}

function emitMarkdown(jsonPath) {
  const doc = JSON.parse(readFileSync(jsonPath, "utf8"));
  const out = [];
  const p = (s = "") => out.push(s);
  const ok = doc.states.filter((s) => !s.error);

  // ---------- 0 表头读数 ----------
  p(`### 0 · 每状态的壳层与浮层几何（同一份量具顺带量，供交叉核对）`);
  p();
  p(
    `| 状态 | 视口 | 画框 x/y/w/h | 顶栏 y/h | 底栏 y/h | 当前句卡 y/h | 控制条 y/h（桌面） | 5 Tab y/h | 词卡 y/h | 抽屉 y/h |`,
  );
  p(`|---|---|---|---|---|---|---|---|---|---|`);
  for (const s of ok) {
    const g = s.geometry;
    const f = (b) => (b ? `${b.y} / ${b.h}` : "—");
    p(
      `| ${s.state} | ${s.viewport.width}×${s.viewport.height} | ${g.frame ? `${g.frame.x}/${g.frame.y}/${g.frame.w}/${g.frame.h}` : "—"} | ${f(
        g.watchTopBar
      )} | ${f(g.watchBottomBar)} | ${f(g.currentSentenceCard)} | ${f(g.controlsBar)} | ${f(
        g.tabBar
      )} | ${f(g.wordCard)} | ${f(g.drawer)} |`
    );
  }
  p();

  // ---------- 1 壳层逐条 ----------
  const home = ok.find((s) => s.route === "/");
  if (home) {
    p(`### 1 · 壳层逐条（量在 \`/\`；顶栏 + 底栏在所有 \`(main)\` 路由上共用）`);
    p();
    p(HEAD_FULL);
    p(SEP_FULL);
    for (const t of home.targets) p(rowOf([t]));
    p();
  }

  // ---------- 2 逐状态全量（按选择器模式合并） ----------
  p(`### 2 · 逐状态全量读数（同一选择器模式的 N 条合并成一行；逐条原始记录在 JSON）`);
  p();
  for (const s of doc.states) {
    p(`#### ${s.route} · ${s.state}`);
    p();
    p(`> ${s.label}`);
    p();
    if (s.error) {
      p(`**采集失败**：\`${s.error.split("\n")[0]}\``);
      p();
      continue;
    }
    const sm = s.summary;
    p(
      `目标 ${sm.total}（关键路径 ${sm.critical}）｜rect <44：**${sm.lt44}**（关键路径 ${sm.lt44Critical}）｜rect <24：${sm.lt24}（关键路径 ${sm.lt24Critical}）｜有效命中区 <44：${sm.lt44Eff}｜<24：${sm.lt24Eff}｜SC 2.5.8 fail：${sm.wcag258Fail}｜SC 2.5.5 fail：${sm.wcag255Fail}｜被盖：${sm.occluded}（关键路径 ${sm.occludedCritical}）`
    );
    p();
    if (s.notes.length) {
      p(`备注：${s.notes.map((n) => `\`${n}\``).join(" · ")}`);
      p();
    }
    p(HEAD_FULL);
    p(SEP_FULL);
    for (const g of groupsOf(s.targets)) p(rowOf(g));
    p();
  }

  // ---------- 3 关键路径 <44 逐条（跨状态去重） ----------
  const crit = new Map();
  for (const s of doc.states) {
    for (const t of s.targets || []) {
      if (!(t.lt44 || t.occluded) || !t.criticalPath) continue;
      const k = `${t.selector.replace(/:nth-of-type\(\d+\)/g, "")}|${t.w}x${t.h}|${t.occluded ? "occ" : ""}`;
      if (!crit.has(k)) crit.set(k, { t, states: new Set() });
      crit.get(k).states.add(s.state);
    }
  }
  p(`### 3 · 关键路径上的 <44 / 接不到指针的目标（跨状态去重）`);
  p();
  p(`| 目标（选择器） | 文案 / aria-label | rect w×h | 有效命中 w×h | 2.5.8 | 接不到指针 | 出现于 |`);
  p(`|---|---|---|---|---|---|---|`);
  for (const { t, states } of [...crit.values()].sort(
    (a, b) => Math.min(a.t.w, a.t.h) - Math.min(b.t.w, b.t.h)
  )) {
    p(
      `| ${sel(t.selector)} | ${esc(t.name)} | ${t.w}×${t.h} | ${t.effW}×${t.effH} | ${t.wcag258} | ${
        t.occluded ? `**是**（${esc(t.hitProbe.occluder).slice(0, 46)}）` : "·"
      } | ${[...states].join(", ")} |`
    );
  }
  p();

  // ---------- 4 非关键路径 <44（按路由去重） ----------
  const nonCrit = new Map();
  for (const s of doc.states) {
    for (const t of s.targets || []) {
      if (!t.lt44 || t.criticalPath) continue;
      const k = `${s.route}|${t.selector.replace(/:nth-of-type\(\d+\)/g, "")}|${t.name}|${t.w}x${t.h}`;
      if (!nonCrit.has(k)) nonCrit.set(k, { t, route: s.route });
    }
  }
  p(`### 4 · 关键路径之外（列表 / 卡片 / 文稿列表 / 个人页…）的 <44 目标 —— 本图不交付，列出备查`);
  p();
  p(`| 路由 | 目标（选择器） | 文案 / aria-label | rect w×h | 有效命中 w×h | 2.5.8 |`);
  p(`|---|---|---|---|---|---|`);
  for (const { t, route } of [...nonCrit.values()].sort(
    (a, b) => Math.min(a.t.w, a.t.h) - Math.min(b.t.w, b.t.h)
  )) {
    p(`| \`${route}\` | ${sel(t.selector)} | ${esc(t.name)} | ${t.w}×${t.h} | ${t.effW}×${t.effH} | ${t.wcag258} |`);
  }
  p();

  console.log(out.join("\n"));
}

// ---------------------------------------------------------------- 入口

if (EMIT_MD) {
  emitMarkdown(OUT);
} else {
  run().catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
