import fs from "node:fs";
import path from "node:path";
import { test, expect, type APIRequestContext, type Page } from "@playwright/test";
import { registerUserViaApi, uniquePhone } from "./helpers";
import type {
  HomeContentDraft,
  HomeContentDraftExpression,
  HomeContentDraftScenario,
  HomeContentVideoState,
  HomeEditorialInteraction,
  HomeEditorialPage,
  HomeLayoutPlacement,
  HomeLayoutState,
} from "../src/types/homeContent";

/**
 * 独立验证：管理员真的能换一条首页主推（真实后端 + dev 代理，不 mock 核心链路）。
 *
 * 覆盖 `backend/app/models/home_content.py`：
 *   1. 初始首页是 A（未发布编排时走旧兜底）；
 *   2. 管理员为 A 制作并发布主推（作为「恢复上一版」的回滚目标）；
 *   3. 管理员在 B 的草稿上改标题与一个选项反馈、用真实片段，预览可用；
 *   4. 普通用户仍看到 A，公共响应里没有 B 的草稿；非管理员访问管理接口 403；
 *   5. 乐观锁 409、跨视频引用 / 片段倒序被拒、已有草稿的生成要显式覆盖确认；
 *   6. 「发布并替换主推」后刷新首页立即显示 B（不重建前端）；
 *   7. 来源变化（改一句真实字幕）→ 公共卡失效 + 发布被拒 → 原样改回后恢复；
 *   8. 再改 B 草稿，线上仍是已发布的 B；
 *   9. 已发布导语展示，原教学数据保留但不占首页；
 *  10. 片段深链、原句收词与多尺寸无溢出；
 *  11. 恢复上一版回到 A；
 *  12. A 下线后拒绝恢复并说明，复原 A 后可恢复。
 *
 * 前提与收尾：
 *   - 仅在显式准备的专用 e2e 数据库运行，三张首页编排表应为空；
 *   - 本 spec 会真实发布编排，不能指向开发/生产的已有内容；
 *   - 基线不符时停止，重新创建独立测试数据，不对未知库执行清空；
 *   - B 已有草稿则复用，否则用真实测试字幕手写；不触发付费生成。
 *
 * **外部数据依赖（CI 适配）**：本 spec 依赖下面三项仓库外的数据，因此
 * **不把任何真实账号口令或视频 ID 写进仓库**，全部由环境变量注入：
 *   - `E2E_ADMIN_PHONE` / `E2E_ADMIN_PASSWORD`：专用管理员账号；
 *   - `E2E_HOME_EDITORIAL_VIDEO_A` / `_B` / `_C` / `_D`：四条真实已发布视频；
 *   - 数据库基线：三张编排表为空（未发布编排）。
 * 任一项不满足 → 按 `e2e/watch.spec.ts` 的既有约定整组 `test.skip()` 并写明原因，
 * CI 因此不会必红；条件满足时 12 步的产品断言一条不少地真跑。
 */

test.describe.configure({ mode: "serial" });

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";
const EVIDENCE_DIR = path.resolve(process.cwd(), "../tmp/e2e-evidence/home-editorial");
/** 管理员账号：只从环境变量读，仓库里不留任何真实手机号/口令。 */
const ADMIN_PHONE = process.env.E2E_ADMIN_PHONE ?? "";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "";
/** 四条真实已发布视频（A/B/C/D）：同样只从环境变量读。 */
const VIDEO_IDS = {
  A: process.env.E2E_HOME_EDITORIAL_VIDEO_A ?? "",
  B: process.env.E2E_HOME_EDITORIAL_VIDEO_B ?? "",
  C: process.env.E2E_HOME_EDITORIAL_VIDEO_C ?? "",
  D: process.env.E2E_HOME_EDITORIAL_VIDEO_D ?? "",
};
const A = VIDEO_IDS.A;
const B = VIDEO_IDS.B;
/** 两条真实已发布视频，用来做「次推最多 2 条」的真实位置验证（保存内容版本但不占主推）。 */
const C = VIDEO_IDS.C;
const D = VIDEO_IDS.D;

const A_HEADLINE = "点头和摇头，英语怎么说？";
const A_DEK = "从动作视频里学会用英语描述同意与不同意，听清一句短句的节奏。";
const B_HEADLINE = "看见那只即时满足猴";
const B_DEK = "从 TED 演讲里听懂即时满足的比喻，学会描述自己的拖延冲动。";
const B_TOPIC = "拖延与自控";
const B_FEEDBACK = "验证反馈：先做五分钟也算开始。";
const C_HEADLINE = "验证次推：生日祝福还能怎么说";
const D_HEADLINE = "验证次推：芯片与记忆";

let adminToken = "";
let userToken = "";
/** A 的已发布内容版本 id：用于验证「主推换了 B，侧卡位置仍引用 A」的内容/位置分离。 */
let aRevisionId = "";
let cRevisionId = "";
let dRevisionId = "";

// ---------------------------------------------------------------------------
// 接口类型（只声明本 spec 实际读到的字段）
// ---------------------------------------------------------------------------

interface ApiErrorBody {
  code?: string;
  message?: string;
}

interface PublicEditorialBody {
  editorial: HomeEditorialPage | null;
}

interface PublishResult {
  revision_id: string;
  version: number;
  layout_revision?: number | null;
}

interface AdminSubtitle {
  id: string;
  sentence_index: number;
  start_time: number;
  end_time: number;
  text_en: string;
  text_zh: string | null;
}

interface AdminVideoDetail {
  id: string;
  title: string;
  title_zh?: string | null;
  is_published: boolean;
  is_official: boolean;
  subtitles: AdminSubtitle[];
}

/** 公共卡显示的主标题：后端 title_zh 优先，英文原名回退。 */
function displayTitle(video: AdminVideoDetail): string {
  return video.title_zh?.trim() || video.title;
}

interface FeaturedBody {
  items: { id: string; title: string }[];
}

// ---------------------------------------------------------------------------
// 通用小工具
// ---------------------------------------------------------------------------

function auth(token: string): { Authorization: string } {
  return { Authorization: `Bearer ${token}` };
}

function normalizeText(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

function evidencePath(name: string): string {
  fs.mkdirSync(EVIDENCE_DIR, { recursive: true });
  return path.join(EVIDENCE_DIR, name);
}

interface ResponseLike {
  status(): number;
  text(): Promise<string>;
}

/** 读取 JSON 并断言状态码；失败时把响应正文带进断言消息。 */
async function readJson<T>(res: ResponseLike, expected: number, label: string): Promise<T> {
  const text = await res.text();
  expect(res.status(), `${label} -> ${text.slice(0, 600)}`).toBe(expected);
  return JSON.parse(text) as T;
}

function findSubtitle(subtitles: AdminSubtitle[], needle: string): AdminSubtitle {
  const hit = subtitles.find((subtitle) =>
    normalizeText(subtitle.text_en).toLowerCase().includes(needle.toLowerCase())
  );
  if (!hit) throw new Error(`视频字幕里找不到「${needle}」，数据前提已变化`);
  return hit;
}

/** 管理员会话注入：边缘登录墙读 cookie，管理端 store 读 localStorage。 */
async function loginAdmin(page: Page): Promise<void> {
  await page
    .context()
    .addCookies([{ name: "seeword_admin_token", value: adminToken, url: BASE_URL }]);
  await page.addInitScript((token: string) => {
    window.localStorage.setItem("seeword_admin_token", token);
  }, adminToken);
}

/** 普通用户会话注入：token 双写（localStorage 真身 + 镜像 cookie），与真实登录一致。 */
async function loginUser(page: Page): Promise<void> {
  await page.context().addCookies([{ name: "seeword_token", value: userToken, url: BASE_URL }]);
  await page.addInitScript((token: string) => {
    window.localStorage.setItem("seeword_token", token);
  }, userToken);
}

// ---------------------------------------------------------------------------
// 管理接口封装（全部走真实 dev 代理 → :8000）
// ---------------------------------------------------------------------------

async function adminLogin(request: APIRequestContext): Promise<string> {
  const res = await request.post("/api/v1/auth/phone-login", {
    data: { phone: ADMIN_PHONE, password: ADMIN_PASSWORD },
  });
  const body = await readJson<{ token: string }>(res, 200, "admin phone-login");
  return body.token;
}

async function getVideoState(
  request: APIRequestContext,
  videoId: string
): Promise<HomeContentVideoState> {
  const res = await request.get(`/api/v1/admin/home-content/videos/${videoId}`, {
    headers: auth(adminToken),
  });
  return readJson<HomeContentVideoState>(res, 200, `GET state ${videoId}`);
}

async function getAdminVideoDetail(
  request: APIRequestContext,
  videoId: string
): Promise<AdminVideoDetail> {
  const res = await request.get(`/api/v1/videos/admin/${videoId}/detail`, {
    headers: auth(adminToken),
  });
  return readJson<AdminVideoDetail>(res, 200, `GET admin detail ${videoId}`);
}

async function getPublicEditorial(request: APIRequestContext): Promise<HomeEditorialPage | null> {
  const res = await request.get("/api/v1/browse/home-editorial");
  const body = await readJson<PublicEditorialBody>(res, 200, "GET public home-editorial");
  return body.editorial;
}

async function getLayout(request: APIRequestContext): Promise<HomeLayoutState> {
  const res = await request.get("/api/v1/admin/home-content/layout", {
    headers: auth(adminToken),
  });
  return readJson<HomeLayoutState>(res, 200, "GET admin home-content layout");
}

async function saveDraft(
  request: APIRequestContext,
  videoId: string,
  payload: HomeContentDraft,
  expectedRevision: number
): Promise<HomeContentVideoState> {
  const res = await request.put(`/api/v1/admin/home-content/videos/${videoId}/draft`, {
    headers: auth(adminToken),
    data: { payload, expected_revision: expectedRevision },
  });
  return readJson<HomeContentVideoState>(res, 200, `PUT draft ${videoId}`);
}

async function publishContent(
  request: APIRequestContext,
  videoId: string,
  expectedRevision: number,
  place: "lead" | "secondary" | null
): Promise<PublishResult> {
  const res = await request.post(`/api/v1/admin/home-content/videos/${videoId}/publish`, {
    headers: auth(adminToken),
    data: { expected_revision: expectedRevision, place },
  });
  return readJson<PublishResult>(res, 200, `POST publish ${videoId}`);
}

// ---------------------------------------------------------------------------
// 草稿构造：全部引用真实字幕，不编造时间/原文
// ---------------------------------------------------------------------------

function buildADraft(subtitles: AdminSubtitle[]): HomeContentDraft {
  const nod = findSubtitle(subtitles, "you can nod");
  const shake = findSubtitle(subtitles, "shake your head");
  const no = findSubtitle(subtitles, "it means no");
  return {
    headline: A_HEADLINE,
    dek: A_DEK,
    topic_label: "动作与表达",
    evidence_subtitle_ids: [nod.id, shake.id],
    clip: { start_subtitle_id: nod.id, end_subtitle_id: no.id },
    expressions: [
      {
        id: "nod",
        subtitle_id: nod.id,
        phrase: "nod",
        word: "nod",
        gloss_zh: "v. 点头",
        note_zh: "先听动作词，再看它怎么放进一句话里。",
      },
      {
        id: "shake-your-head",
        subtitle_id: shake.id,
        phrase: "shake your head",
        word: null,
        gloss_zh: "摇头（表示不同意）",
        note_zh: "否定动作的常用搭配。",
      },
    ],
    interaction: {
      id: "first-action",
      question: "如果是你，会先学哪个动作？",
      options: [
        {
          id: "nod-first",
          label: "点头同意",
          feedback: "你会先注意到 nod：它既能当动词，也能当名词。",
        },
        {
          id: "shake-first",
          label: "摇头不同意",
          feedback: "shake your head 常和 disagree 一起出现，先记住这个搭配。",
        },
      ],
    },
    scenarios: [
      {
        id: "nod-along",
        situation_zh: "约朋友 · 临时有事",
        prompt_zh: "同事说完方案，你想表示同意，试着用英语说一句",
        reply_en: "That makes sense to me. I nod along with the plan.",
        reply_zh: "我觉得这个方案说得通，我同意这个计划。",
        subtitle_id: nod.id,
      },
    ],
  };
}

/** B 没有 AI 草稿时的兜底：用 B 的真实字幕手写一份可发布内容。 */
function buildBFallbackDraft(subtitles: AdminSubtitle[]): HomeContentDraft {
  const monkey = findSubtitle(subtitles, "instant gratification monkey");
  const rational = findSubtitle(subtitles, "Both brains have a rational decision maker");
  const wheel = findSubtitle(subtitles, "does not seem like a guy you want behind the wheel");
  return {
    headline: B_HEADLINE,
    dek: B_DEK,
    topic_label: B_TOPIC,
    evidence_subtitle_ids: [monkey.id],
    clip: { start_subtitle_id: rational.id, end_subtitle_id: wheel.id },
    expressions: [
      {
        id: "monkey",
        subtitle_id: monkey.id,
        phrase: "monkey",
        word: "monkey",
        gloss_zh: "n. 猴子",
        note_zh: "比喻里那只“即时满足猴”。",
      },
      {
        id: "instant-gratification",
        subtitle_id: monkey.id,
        phrase: "instant gratification",
        word: null,
        gloss_zh: "即时满足",
        note_zh: "拖延的核心诱因。",
      },
    ],
    interaction: {
      id: "first-move",
      question: "遇到暂时不想做的事，你先做什么？",
      options: [
        { id: "other-first", label: "先做点别的", feedback: B_FEEDBACK },
        { id: "start-first", label: "先开始五分钟", feedback: "验证反馈：直接开始五分钟。" },
      ],
    },
    scenarios: [
      {
        id: "phone-away",
        situation_zh: "学习 · 抵抗手机诱惑",
        prompt_zh: "坐下学习前，手机弹出了新消息，试着用英语给自己一个安排",
        reply_en: "Let me put the phone away and start with five minutes.",
        reply_zh: "先把手机放远，从五分钟开始。",
        subtitle_id: monkey.id,
      },
    ],
  };
}

/** 次推内容版本：只发布内容、不占位置；用于验证「次推最多 2 条」真实可用。 */
function buildSecondaryDraft(headline: string, subtitles: AdminSubtitle[]): HomeContentDraft {
  const startIndex = subtitles.findIndex(
    (subtitle) => normalizeText(subtitle.text_en).length >= 40
  );
  const start = subtitles[Math.max(startIndex, 0)];
  if (!start) throw new Error("次推视频没有可用字幕");
  const end = subtitles[Math.min(startIndex + 4, subtitles.length - 1)] ?? start;
  const tokens = normalizeText(start.text_en).match(/[A-Za-z][A-Za-z'-]{3,}/g) ?? [];
  const stopwords = new Set(["the", "and", "this", "that", "with", "your", "have", "from", "what"]);
  const word =
    tokens.find((token) => !stopwords.has(token.toLowerCase())) ?? tokens[0] ?? "english";
  return {
    headline,
    dek: "独立验证用次推内容：原文、时间与视频事实都来自真实字幕。",
    topic_label: "验证次推",
    evidence_subtitle_ids: [start.id],
    clip: { start_subtitle_id: start.id, end_subtitle_id: end.id },
    expressions: [
      {
        id: "pick-word",
        subtitle_id: start.id,
        phrase: word,
        word,
        gloss_zh: null,
        note_zh: null,
      },
    ],
    interaction: null,
    scenarios: [],
  };
}

const FALLBACK_INTERACTION: HomeEditorialInteraction = {
  id: "b-interaction",
  question: "遇到暂时不想做的事，你先做什么？",
  options: [
    { id: "other-first", label: "先做点别的", feedback: B_FEEDBACK },
    { id: "start-first", label: "先开始五分钟", feedback: "验证反馈：直接开始五分钟。" },
  ],
};

const FALLBACK_SCENARIO: HomeContentDraftScenario = {
  id: "phone-away",
  situation_zh: "学习 · 抵抗手机诱惑",
  prompt_zh: "坐下学习前，手机弹出了新消息，试着用英语给自己一个安排",
  reply_en: "Let me put the phone away and start with five minutes.",
  reply_zh: "先把手机放远，从五分钟开始。",
  subtitle_id: null,
};

/** 保证第一条表达带收词单词（默认选中就能走真实收词接口）。 */
function ensureWordExpression(
  expressions: HomeContentDraftExpression[]
): HomeContentDraftExpression[] {
  const withWord = expressions.find((expression) => expression.word);
  if (withWord) {
    return [withWord, ...expressions.filter((expression) => expression.id !== withWord.id)];
  }
  const target = expressions[0];
  if (!target) throw new Error("B 草稿里没有表达，无法构造收词用例");
  const tokens: string[] =
    normalizeText(target.phrase)
      .toLowerCase()
      .match(/[a-z][a-z'-]{2,}/g) ?? [];
  const word = tokens.includes("monkey") ? "monkey" : tokens[tokens.length - 1];
  if (!word) throw new Error(`无法从短语“${target.phrase}”选出收词单词`);
  return [{ ...target, word }, ...expressions.slice(1)];
}

function ensureInteraction(interaction: HomeEditorialInteraction | null): HomeEditorialInteraction {
  if (interaction && interaction.options.length >= 2) {
    return {
      ...interaction,
      options: interaction.options.map((option, index) =>
        index === 0 ? { ...option, feedback: B_FEEDBACK } : option
      ),
    };
  }
  return structuredClone(FALLBACK_INTERACTION);
}

function ensureScenarioAnchor(
  scenarios: HomeContentDraftScenario[],
  subtitles: AdminSubtitle[]
): HomeContentDraftScenario[] {
  if (scenarios.length === 0) {
    const anchor = findSubtitle(subtitles, "instant gratification monkey");
    return [{ ...structuredClone(FALLBACK_SCENARIO), subtitle_id: anchor.id }];
  }
  if (scenarios.some((scenario) => scenario.subtitle_id)) return scenarios;
  const anchor = findSubtitle(subtitles, "instant gratification monkey");
  const [first, ...rest] = scenarios;
  return [{ ...first, subtitle_id: anchor.id }, ...rest];
}

/** 把草稿改成验收用的确定性内容：改标题、改一个选项反馈，其余保留。 */
function prepareBDraft(draft: HomeContentDraft, subtitles: AdminSubtitle[]): HomeContentDraft {
  const next = structuredClone(draft);
  next.headline = B_HEADLINE;
  next.dek = B_DEK;
  next.topic_label = B_TOPIC;
  next.expressions = ensureWordExpression(next.expressions);
  next.interaction = ensureInteraction(next.interaction);
  next.scenarios = ensureScenarioAnchor(next.scenarios, subtitles);
  return next;
}

// ---------------------------------------------------------------------------
// 浏览器辅助
// ---------------------------------------------------------------------------

async function openAdminPage(page: Page, url: string): Promise<void> {
  await loginAdmin(page);
  await page.goto(url);
}

/** 打开管理员视频详情，等「首页内容」面板加载完成。 */
async function openAdminHomeContentPanel(page: Page, videoId: string) {
  await openAdminPage(page, `/admin/videos/${videoId}`);
  const panel = page.getByRole("region", { name: "首页内容" });
  await expect(panel).toBeVisible({ timeout: 120_000 });
  await expect(panel.getByText(/草稿 rev \d+|未制作/).first()).toBeVisible({ timeout: 120_000 });
  return panel;
}

/**
 * 收起 Next dev tools 的临时「N Issue」徽标（dev-only overlay，不参与产品行为）。
 *
 * 它统计的是 dev 下 React StrictMode 双执行/导航 unmount 造成的 ERR_ABORTED
 * 请求（证据见 `12-homepage-console.log` 与验证报告「发现的问题」一节），
 * 不是运行时错误；这里只是让交付截图不被 dev 工具噪声遮挡。
 */
async function dismissNextDevIssueBadge(page: Page): Promise<void> {
  await page.evaluate(() => {
    const root = document.querySelector("nextjs-portal")?.shadowRoot;
    const collapse = root?.querySelector("[data-issues-collapse]");
    if (collapse instanceof HTMLElement && collapse.getClientRects().length > 0) {
      collapse.click();
    }
  });
  await page.waitForTimeout(250);
}

/** 首页编辑编排整页截图：把视口拉到 feed 之前，避免整页截图只截到壳层滚动区。 */
async function captureEditorialHome(
  page: Page,
  width: number,
  maxHeight: number,
  name: string
): Promise<void> {
  await page.setViewportSize({ width, height: 900 });
  await page.goto("/");
  await expect(page.locator(".home-editorial-lead")).toBeVisible({ timeout: 60_000 });
  // 等 Next dev tools 的临时徽标（dev StrictMode 双执行造成的 abort 可能被它计数）
  // 自行收起，再截真实页面；生产构建没有这个徽标。
  await page.waitForTimeout(1800);
  await dismissNextDevIssueBadge(page);
  const needed = await page.evaluate(() => {
    const feed = document.querySelector("#feed");
    return feed ? Math.ceil(feed.getBoundingClientRect().top + 260) : 2400;
  });
  await page.setViewportSize({ width, height: Math.min(Math.max(needed, 900), maxHeight) });
  await page.waitForTimeout(500);
  await page.screenshot({ path: evidencePath(name) });
}

/** 管理端整页截图：管理壳的滚动容器是 <main>，同样用视口高度展开。 */
async function captureAdminPage(
  page: Page,
  width: number,
  maxHeight: number,
  name: string
): Promise<void> {
  const needed = await page.evaluate(() => {
    const main = document.querySelector("main");
    return Math.ceil((main?.scrollHeight ?? 0) + 160);
  });
  await page.setViewportSize({ width, height: Math.min(Math.max(needed, 900), maxHeight) });
  await page.waitForTimeout(500);
  await page.screenshot({ path: evidencePath(name) });
}

// ---------------------------------------------------------------------------
// 外部数据依赖守卫（CI 适配）
// ---------------------------------------------------------------------------
//
// 这个 spec 依赖仓库外的三样东西：管理员账号、四条真实已发布视频、以及
// 「编排三表为空」的库基线。缺任何一样都跑不出有意义的断言，因此按
// e2e/watch.spec.ts 的既有约定整组 skip 并写明原因——而不是让 CI 必红。
//
// 只在「外部数据不满足」时 skip：本 spec 自己的产品断言（发布、回滚、乐观锁、
// 来源失效、互动反馈、响应式…）在条件满足时一条不少地真跑。

interface DataDependency {
  ok: boolean;
  reason: string;
}

let dataDependency: DataDependency = { ok: false, reason: "外部数据依赖尚未检查" };

async function checkDataDependencies(request: APIRequestContext): Promise<DataDependency> {
  const missing: string[] = [];
  if (!ADMIN_PHONE || !ADMIN_PASSWORD) missing.push("E2E_ADMIN_PHONE / E2E_ADMIN_PASSWORD");
  for (const key of ["A", "B", "C", "D"] as const) {
    if (!VIDEO_IDS[key]) missing.push(`E2E_HOME_EDITORIAL_VIDEO_${key}`);
  }
  if (missing.length > 0) {
    return {
      ok: false,
      reason:
        `外部数据依赖不满足（缺少环境变量注入：${missing.join("、")}）。` +
        "本 spec 需要专用管理员账号与四条真实已发布视频；账号口令与视频 ID 一律由环境变量注入，仓库里不留明文。",
    };
  }

  // 库基线：三张编排表必须为空（未发布编排），否则第 1 步的基线断言必失败。
  adminToken = await adminLogin(request);
  const editorial = await getPublicEditorial(request);
  if (editorial !== null) {
    return {
      ok: false,
      reason:
        "外部数据依赖不满足：库里已经有已发布的首页编排（home_page_config / home_content_revisions 非空），" +
        "本 spec 的基线前提（未发布编排）不成立。请重新准备专用 e2e 数据库，不要清空已有业务数据。",
    };
  }
  for (const key of ["A", "B", "C", "D"] as const) {
    const state = await getVideoState(request, VIDEO_IDS[key]);
    if (state.draft !== null || state.revisions.length > 0) {
      return {
        ok: false,
        reason:
          `外部数据依赖不满足：视频 ${key}（${VIDEO_IDS[key]}）已有草稿或已发布版本` +
          "（home_content_drafts / home_content_revisions 非空），本 spec 的基线前提不成立。" +
          "请重新准备专用 e2e 数据库，不要清空已有业务数据。",
      };
    }
  }
  return { ok: true, reason: "" };
}

test.beforeAll(async ({ request }) => {
  dataDependency = await checkDataDependencies(request);
});

test.beforeEach(() => {
  if (!dataDependency.ok) {
    test.skip(true, dataDependency.reason);
  }
});

// ---------------------------------------------------------------------------
// 用例
// ---------------------------------------------------------------------------

test("1/12 基线：未发布编排时公共接口为空，首页走旧兜底显示 A", async ({ request, page }) => {
  test.setTimeout(180_000);
  adminToken = await adminLogin(request);
  userToken = (await registerUserViaApi(request, uniquePhone())).token;

  expect(await getPublicEditorial(request)).toBeNull();
  const featuredRes = await request.get("/api/v1/browse/featured?limit=6");
  const featured = await readJson<FeaturedBody>(featuredRes, 200, "GET featured");
  expect(featured.items[0]?.id).toBe(A);

  const stateA = await getVideoState(request, A);
  expect(stateA.draft).toBeNull();
  expect(stateA.revisions).toEqual([]);
  expect(stateA.publicly_visible).toBe(true);

  // 公共响应只有 editorial 字段，不含任何草稿/生成信息
  const rawRes = await request.get("/api/v1/browse/home-editorial");
  const raw = await rawRes.text();
  expect(rawRes.status()).toBe(200);
  expect(raw).toContain("editorial");
  expect(raw).not.toContain("draft");
  expect(raw).not.toContain(B_HEADLINE);

  await loginUser(page);
  await page.goto("/");
  await expect(page.locator(".home-editorial-heading")).toBeVisible({ timeout: 60_000 });
  await expect(page.locator(".home-story.is-lead")).toContainText(
    "Learn English with Bob the Canadian",
    { timeout: 60_000 }
  );
  await expect(page.locator(".home-personal")).toHaveCount(0);
});

test("2/12 管理员为 A 制作并发布主推，并在编排页摆好换说法/场景卡（回滚目标）", async ({
  request,
  page,
}) => {
  test.setTimeout(180_000);
  const detailA = await getAdminVideoDetail(request, A);
  const draftA = buildADraft(detailA.subtitles);

  const savedA = await saveDraft(request, A, draftA, 0);
  expect(savedA.draft?.headline).toBe(A_HEADLINE);
  expect(savedA.draft_revision).toBe(1);

  const publishedA = await publishContent(request, A, savedA.draft_revision, "lead");
  expect(publishedA.version).toBe(1);
  expect(publishedA.layout_revision).not.toBeNull();
  aRevisionId = publishedA.revision_id;

  // 只有主推、还没有编排时：次推 0 条是合法状态，不造占位内容
  const leadOnly = await getPublicEditorial(request);
  expect(leadOnly?.lead?.content.video_id).toBe(A);
  expect(leadOnly?.secondary).toEqual([]);
  expect(leadOnly?.expression).toBeNull();
  expect(leadOnly?.scenarios).toEqual([]);

  // 两条真实视频各发布一份内容版本（place=null：只入候选池，不占位置），
  // 然后由管理员编排接口把它们摆到「次推最多 2 条」。
  const detailC = await getAdminVideoDetail(request, C);
  const savedC = await saveDraft(request, C, buildSecondaryDraft(C_HEADLINE, detailC.subtitles), 0);
  const publishedC = await publishContent(request, C, savedC.draft_revision, null);
  cRevisionId = publishedC.revision_id;

  const detailD = await getAdminVideoDetail(request, D);
  const savedD = await saveDraft(request, D, buildSecondaryDraft(D_HEADLINE, detailD.subtitles), 0);
  const publishedD = await publishContent(request, D, savedD.draft_revision, null);
  dRevisionId = publishedD.revision_id;

  // 用管理员编排接口把 A 的「换个说法」「今天就能用」摆到独立位置，并放入 2 条次推；
  // 位置引用的都是已发布的不可变版本。
  const layout = await getLayout(request);
  const placement: HomeLayoutPlacement = {
    lead: { content_revision_id: publishedA.revision_id },
    secondary: [
      { content_revision_id: publishedC.revision_id },
      { content_revision_id: publishedD.revision_id },
    ],
    expression: {
      content_revision_id: publishedA.revision_id,
      expression_id: draftA.expressions[0].id,
    },
    scenarios: [
      { content_revision_id: publishedA.revision_id, scenario_id: draftA.scenarios[0].id },
    ],
  };
  const layoutDraftRes = await request.put("/api/v1/admin/home-content/layout/draft", {
    headers: auth(adminToken),
    data: { layout: placement, expected_revision: layout.revision },
  });
  const layoutDraft = await readJson<HomeLayoutState>(layoutDraftRes, 200, "PUT layout draft");
  expect(layoutDraft.issues).toEqual([]);
  const layoutPublishRes = await request.post("/api/v1/admin/home-content/layout/publish", {
    headers: auth(adminToken),
    data: { expected_revision: layoutDraft.revision },
  });
  await readJson<{ layout_revision: number }>(layoutPublishRes, 200, "POST layout publish");

  const publicPage = await getPublicEditorial(request);
  expect(publicPage?.lead?.content.video_id).toBe(A);
  expect(publicPage?.lead?.content.headline).toBe(A_HEADLINE);
  expect(publicPage?.expression?.content_revision_id).toBe(publishedA.revision_id);
  expect(publicPage?.scenarios.length).toBe(1);
  // 次推顺序与编排一致（最多 2 条，主次不重复），且引用的就是刚发布的版本
  expect(publicPage?.secondary.map((slot) => slot.content.video_id)).toEqual([C, D]);
  expect(publicPage?.secondary.map((slot) => slot.content.content_revision_id)).toEqual([
    cRevisionId,
    dRevisionId,
  ]);
  expect(publicPage?.secondary.map((slot) => slot.content.headline)).toEqual([
    C_HEADLINE,
    D_HEADLINE,
  ]);
  expect(JSON.stringify(publicPage)).not.toContain('"draft"');

  await loginUser(page);
  await page.goto("/");
  await expect(page.locator(".home-editorial-lead")).toContainText(displayTitle(detailA), {
    timeout: 60_000,
  });
  await page.locator(".home-editorial-lead").getByRole("button", { name: "学前预览" }).click();
  await expect(page.getByText("点头同意")).toBeVisible();
  await expect(page.locator("#home-scenarios")).toHaveCount(0);
  // 后端保留两条递补候选，前端只展示一个视频。
  await expect(page.locator(".home-editorial-secondary")).toHaveCount(0);
  await expect(page.locator(".home-feature-card")).toHaveCount(1);
});

test("3/12 管理员详情页：B 草稿（真实 AI 结果或手写兜底）改标题与选项反馈，预览", async ({
  request,
  page,
}) => {
  test.setTimeout(300_000);
  const detailB = await getAdminVideoDetail(request, B);
  let stateB = await getVideoState(request, B);

  const usedGeneratedDraft = stateB.draft !== null;
  const base = stateB.draft ?? buildBFallbackDraft(detailB.subtitles);
  const editedDraft = prepareBDraft(base, detailB.subtitles);
  stateB = await saveDraft(request, B, editedDraft, stateB.draft_revision);

  expect(stateB.draft?.headline).toBe(B_HEADLINE);
  expect(stateB.draft?.interaction?.options[0]?.feedback).toBe(B_FEEDBACK);
  expect(stateB.draft?.expressions[0]?.word).toBeTruthy();
  expect(stateB.revisions).toEqual([]);
  // 真实 AI 生成结果（只记录事实，不评价质量）
  console.log(
    "[real-generation]",
    JSON.stringify({
      reused_generated_draft: usedGeneratedDraft,
      generation: stateB.generation,
      draft_revision: stateB.draft_revision,
    })
  );

  // 面板很长（状态 + 完整草稿表单 + 历史版本）：把视口拉高再截整块元素，
  // 避免元素截图在滚动容器里只画出首屏、其余留白。
  await page.setViewportSize({ width: 1440, height: 5400 });
  const panel = await openAdminHomeContentPanel(page, B);
  await expect(panel.getByText(`草稿 rev ${stateB.draft_revision}`).first()).toBeVisible();
  if (stateB.generation?.status === "succeeded") {
    await expect(panel.getByText("生成完成")).toBeVisible();
    await expect(panel.getByText(/minimax/i)).toBeVisible();
  }
  await panel.scrollIntoViewIfNeeded();
  await page.waitForTimeout(800);
  await panel.screenshot({ path: evidencePath("03-管理员-视频详情-首页内容面板.png") });

  // 回到常规桌面视口再开预览弹层
  await page.setViewportSize({ width: 1440, height: 900 });
  await panel.getByRole("button", { name: "预览" }).click();
  const previewDialog = page.getByRole("dialog", { name: "首页内容预览（管理员接口）" });
  await expect(previewDialog).toBeVisible({ timeout: 60_000 });
  await expect(previewDialog.getByRole("heading", { name: displayTitle(detailB) })).toBeVisible({
    timeout: 60_000,
  });
  // 预览复用完整视频推荐：导语展示，互动与片段不占首页。
  await expect(previewDialog.getByText(B_DEK)).toBeVisible();
  await expect(previewDialog.getByRole("button", { name: "学前预览" })).toHaveCount(0);
  await expect(
    previewDialog.getByRole("link", { name: "观看完整视频", exact: true })
  ).toHaveAttribute("href", `/watch/${B}?from=home`);
  await previewDialog.screenshot({ path: evidencePath("05-预览弹层.png") });
  // 弹层里有两个「关闭」（右上角图标 + 底部按钮），点底部那个
  await previewDialog.getByRole("button", { name: "关闭" }).last().click();
  await expect(previewDialog).toHaveCount(0);
});

test("4/12 草稿对普通用户不可见；非管理员访问管理接口 403", async ({ request, page }) => {
  test.setTimeout(180_000);
  const publicPage = await getPublicEditorial(request);
  expect(publicPage?.lead?.content.video_id).toBe(A);
  const raw = await (await request.get("/api/v1/browse/home-editorial")).text();
  expect(raw).not.toContain(B_HEADLINE);
  expect(raw).not.toContain(B_FEEDBACK);
  expect(raw).not.toContain('"draft"');

  const headers = auth(userToken);
  const adminEndpoints: { method: string; url: string; data?: Record<string, unknown> }[] = [
    { method: "GET", url: `/api/v1/admin/home-content/videos/${B}` },
    {
      method: "POST",
      url: `/api/v1/admin/home-content/videos/${B}/generate`,
      data: { expected_revision: 0 },
    },
    {
      method: "PUT",
      url: `/api/v1/admin/home-content/videos/${B}/draft`,
      data: { payload: {}, expected_revision: 0 },
    },
    {
      method: "POST",
      url: `/api/v1/admin/home-content/videos/${B}/publish`,
      data: { expected_revision: 0, place: "lead" },
    },
    { method: "POST", url: `/api/v1/admin/home-content/videos/${B}/restore-draft`, data: {} },
    { method: "GET", url: `/api/v1/admin/home-content/videos/${B}/preview` },
    { method: "GET", url: "/api/v1/admin/home-content/layout" },
    { method: "PUT", url: "/api/v1/admin/home-content/layout/draft", data: { layout: {} } },
    { method: "POST", url: "/api/v1/admin/home-content/layout/publish", data: {} },
    { method: "POST", url: "/api/v1/admin/home-content/layout/rollback", data: {} },
    { method: "GET", url: "/api/v1/admin/home-content/layout/preview" },
  ];
  for (const endpoint of adminEndpoints) {
    const res = await request.fetch(endpoint.url, {
      method: endpoint.method,
      headers,
      data: endpoint.data,
    });
    expect(res.status(), `${endpoint.method} ${endpoint.url}`).toBe(403);
  }

  const anonymous = await request.get(`/api/v1/admin/home-content/videos/${B}`);
  expect([401, 403]).toContain(anonymous.status());

  await loginUser(page);
  await page.goto("/");
  const detailA = await getAdminVideoDetail(request, A);
  await expect(page.locator(".home-editorial-lead")).toContainText(displayTitle(detailA), {
    timeout: 60_000,
  });
  await expect(page.getByText(B_HEADLINE)).toHaveCount(0);
});

test("5/12 乐观锁 409、跨视频引用/片段倒序被拒、已有草稿的生成需确认覆盖", async ({ request }) => {
  test.setTimeout(180_000);
  const stateB = await getVideoState(request, B);
  expect(stateB.draft).not.toBeNull();
  const currentDraft = stateB.draft!;
  const revision = stateB.draft_revision;

  // 乐观锁：过期 revision → 409 HOME_CONTENT_REVISION_CONFLICT
  const staleRes = await request.put(`/api/v1/admin/home-content/videos/${B}/draft`, {
    headers: auth(adminToken),
    data: { payload: currentDraft, expected_revision: revision - 1 },
  });
  const staleBody = await readJson<ApiErrorBody>(staleRes, 409, "stale revision save");
  expect(staleBody.code).toBe("HOME_CONTENT_REVISION_CONFLICT");
  expect(staleBody.message).toContain("刷新");

  // 跨视频字幕引用 → 422 HOME_CONTENT_INVALID
  const detailA = await getAdminVideoDetail(request, A);
  const aSubtitle = findSubtitle(detailA.subtitles, "you can nod");
  const crossDraft = structuredClone(currentDraft);
  crossDraft.expressions[0] = { ...crossDraft.expressions[0], subtitle_id: aSubtitle.id };
  const crossRes = await request.put(`/api/v1/admin/home-content/videos/${B}/draft`, {
    headers: auth(adminToken),
    data: { payload: crossDraft, expected_revision: revision },
  });
  const crossBody = await readJson<ApiErrorBody>(crossRes, 422, "cross-video subtitle");
  expect(crossBody.code).toBe("HOME_CONTENT_INVALID");

  // 片段起止倒序 → 422（用 B 真实字幕构造）
  const detailB = await getAdminVideoDetail(request, B);
  const monkey = findSubtitle(detailB.subtitles, "instant gratification monkey");
  const later = detailB.subtitles.find(
    (subtitle) =>
      subtitle.sentence_index > monkey.sentence_index && normalizeText(subtitle.text_en).length > 20
  );
  expect(later).toBeTruthy();
  const reversedDraft = structuredClone(currentDraft);
  reversedDraft.clip = {
    start_subtitle_id: later!.id,
    end_subtitle_id: monkey.id,
  };
  const reversedRes = await request.put(`/api/v1/admin/home-content/videos/${B}/draft`, {
    headers: auth(adminToken),
    data: { payload: reversedDraft, expected_revision: revision },
  });
  const reversedBody = await readJson<ApiErrorBody>(reversedRes, 422, "reversed clip");
  expect(reversedBody.code).toBe("HOME_CONTENT_INVALID");

  // 已有草稿时再次生成必须显式 overwrite：A 已有草稿 → 409 OVERWRITE_CONFIRM
  const stateA = await getVideoState(request, A);
  const generateA = await request.post(`/api/v1/admin/home-content/videos/${A}/generate`, {
    headers: auth(adminToken),
    data: { expected_revision: stateA.draft_revision },
  });
  const generateBody = await readJson<ApiErrorBody>(generateA, 409, "generate overwrite confirm");
  expect(generateBody.code).toBe("HOME_CONTENT_OVERWRITE_CONFIRM");

  // 以上失败请求都没有改动草稿与线上内容
  const after = await getVideoState(request, B);
  expect(after.draft_revision).toBe(revision);
  expect(after.draft?.headline).toBe(B_HEADLINE);
  expect(after.draft?.clip).toEqual(currentDraft.clip);
  expect((await getPublicEditorial(request))?.lead?.content.video_id).toBe(A);
});

test("6/12 管理员点击「发布并替换主推」→ 刷新公共首页立即显示 B", async ({ request, page }) => {
  test.setTimeout(300_000);
  const stateB = await getVideoState(request, B);
  const panel = await openAdminHomeContentPanel(page, B);
  await expect(panel.getByText(`草稿 rev ${stateB.draft_revision}`).first()).toBeVisible();

  const publishResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/v1/admin/home-content/videos/${B}/publish`) &&
      response.request().method() === "POST"
  );
  await panel.getByRole("button", { name: "发布到主推" }).click();
  const confirmDialog = page.getByRole("dialog", { name: "发布并替换主推" });
  await expect(confirmDialog).toBeVisible();
  await confirmDialog.getByRole("button", { name: "发布", exact: true }).click();

  const publishResponse = await publishResponsePromise;
  const publishBody = await publishResponse.text();
  expect(publishResponse.status(), publishBody).toBe(200);
  const published = JSON.parse(publishBody) as PublishResult;
  expect(published.version).toBe(1);
  await expect(page.getByText(/已发布 v1 并替换主推/)).toBeVisible({ timeout: 60_000 });

  const publicPage = await getPublicEditorial(request);
  expect(publicPage?.lead?.content.video_id).toBe(B);
  expect(publicPage?.lead?.content.headline).toBe(B_HEADLINE);
  expect(publicPage?.lead?.content.interaction?.options[0]?.feedback).toBe(B_FEEDBACK);
  expect(publicPage?.lead?.content.clip?.duration).toBeGreaterThan(0);
  const slots = [publicPage?.lead, ...(publicPage?.secondary ?? [])].filter(
    (slot): slot is NonNullable<typeof slot> => Boolean(slot)
  );
  expect(slots.every((slot) => slot.content.video_id !== A)).toBe(true);
  // 次推位仍然真实可用：主推 B + 次推 C、D，顺序与编排一致
  expect(publicPage?.secondary.map((slot) => slot.content.video_id)).toEqual([C, D]);
  // 内容与位置分离：主推换成 B，但「换个说法」「今天就能用」仍是 A 的内容版本
  expect(publicPage?.expression?.content_revision_id).toBe(aRevisionId);
  expect(publicPage?.scenarios.length).toBe(1);
  expect(publicPage?.scenarios[0]?.content_revision_id).toBe(aRevisionId);
  expect(JSON.stringify(publicPage)).not.toContain('"draft"');

  await loginUser(page);
  await page.goto("/");
  const detailB = await getAdminVideoDetail(request, B);
  await expect(page.locator(".home-editorial-lead")).toContainText(displayTitle(detailB), {
    timeout: 60_000,
  });
  await expect(page.getByRole("article", { name: "换个说法" })).toHaveCount(0);
  await expect(page.locator("#home-scenarios")).toHaveCount(0);
  await expect(page.locator(".home-editorial-secondary")).toHaveCount(0);
  await captureEditorialHome(page, 1440, 1600, "07-首页-发布后-B-1440.png");
});

test("7/12 来源变化：改一句 B 字幕 → 公共卡失效且发布被拒；原样改回后恢复", async ({
  request,
  page,
}) => {
  test.setTimeout(240_000);
  const detailB = await getAdminVideoDetail(request, B);
  const target = findSubtitle(detailB.subtitles, "instant gratification monkey");
  const originalText = target.text_en;
  const changedText = `${originalText} [verify-source-change]`;

  const patched = await request.patch(`/api/v1/videos/admin/${B}/subtitles/${target.id}`, {
    headers: auth(adminToken),
    data: { text_en: changedText },
  });
  expect(patched.status(), await patched.text()).toBe(200);

  try {
    // 已发布版本来源失效 → 该卡从公共接口消失；次推按 §7.3 提升为主推（不整块消失）
    const degradedPage = await getPublicEditorial(request);
    expect(degradedPage?.lead?.content.video_id).toBe(C);
    expect(degradedPage?.secondary.map((slot) => slot.content.video_id)).toEqual([D]);
    const degradedSlots = [degradedPage?.lead, ...(degradedPage?.secondary ?? [])].filter(
      (slot): slot is NonNullable<typeof slot> => Boolean(slot)
    );
    expect(degradedSlots.every((slot) => slot.content.video_id !== B)).toBe(true);
    const state = await getVideoState(request, B);
    expect(state.source_changed).toBe(true);
    expect(state.revisions.some((revision) => revision.source_changed)).toBe(true);

    // 发布被拒：422 HOME_CONTENT_SOURCE_CHANGED
    const publishRes = await request.post(`/api/v1/admin/home-content/videos/${B}/publish`, {
      headers: auth(adminToken),
      data: { expected_revision: state.draft_revision, place: "lead" },
    });
    const publishBody = await readJson<ApiErrorBody>(
      publishRes,
      422,
      "publish after source change"
    );
    expect(publishBody.code).toBe("HOME_CONTENT_SOURCE_CHANGED");

    // 首页不再是 B，也没有半套编排：次推 C 被提升为主推
    await loginUser(page);
    await page.goto("/");
    const detailC = await getAdminVideoDetail(request, C);
    await expect(page.locator(".home-editorial-lead")).toContainText(displayTitle(detailC), {
      timeout: 60_000,
    });
    await expect(page.getByText(B_HEADLINE)).toHaveCount(0);
  } finally {
    const restored = await request.patch(`/api/v1/videos/admin/${B}/subtitles/${target.id}`, {
      headers: auth(adminToken),
      data: { text_en: originalText },
    });
    expect(restored.status(), await restored.text()).toBe(200);
  }

  const publicPage = await getPublicEditorial(request);
  expect(publicPage?.lead?.content.video_id).toBe(B);
  expect(publicPage?.lead?.content.headline).toBe(B_HEADLINE);
  expect(publicPage?.secondary.map((slot) => slot.content.video_id)).toEqual([C, D]);
  const stateAfter = await getVideoState(request, B);
  expect(stateAfter.source_changed).toBe(false);
  expect(stateAfter.revisions.every((revision) => !revision.source_changed)).toBe(true);
});

test("8/12 再改 B 草稿不改变线上；普通用户仍看已发布 B", async ({ request, page }) => {
  test.setTimeout(240_000);
  const stateB = await getVideoState(request, B);
  const draft = structuredClone(stateB.draft!);
  draft.headline = `${B_HEADLINE}（草稿）`;
  draft.interaction = ensureInteraction(draft.interaction);
  draft.interaction = {
    ...draft.interaction,
    options: draft.interaction.options.map((option, index) =>
      index === 0 ? { ...option, feedback: "草稿里的新反馈" } : option
    ),
  };
  const saved = await saveDraft(request, B, draft, stateB.draft_revision);
  expect(saved.draft_revision).toBe(stateB.draft_revision + 1);
  expect(saved.draft?.headline).toBe(`${B_HEADLINE}（草稿）`);

  // 人工修改不会被后台生成任务自动覆盖（等一个轮询周期再确认）
  await page.waitForTimeout(3000);
  const stable = await getVideoState(request, B);
  expect(stable.draft_revision).toBe(saved.draft_revision);
  expect(stable.draft?.headline).toBe(`${B_HEADLINE}（草稿）`);

  const publicPage = await getPublicEditorial(request);
  expect(publicPage?.lead?.content.headline).toBe(B_HEADLINE);
  expect(publicPage?.lead?.content.interaction?.options[0]?.feedback).toBe(B_FEEDBACK);
  expect(JSON.stringify(publicPage)).not.toContain("草稿里的新反馈");

  await loginUser(page);
  await page.goto("/");
  const detailB = await getAdminVideoDetail(request, B);
  await expect(page.locator(".home-editorial-lead")).toContainText(displayTitle(detailB), {
    timeout: 60_000,
  });
  await expect(page.getByText("草稿里的新反馈")).toHaveCount(0);
});

test("9/12 完整视频介绍使用已发布导语，原有教学数据保留在公共契约中", async ({ request, page }) => {
  const publicPage = await getPublicEditorial(request);
  const lead = publicPage!.lead!;
  expect(lead.content.interaction!.options.length).toBeGreaterThanOrEqual(2);
  expect(lead.content.interaction!.options[0].feedback).toBe(B_FEEDBACK);
  await loginUser(page);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  const card = page.locator(".home-editorial-lead");
  await expect(card).toContainText(displayTitle(await getAdminVideoDetail(request, B)));
  await expect(card).toContainText(lead.content.dek);
  await expect(card.getByRole("link", { name: "观看完整视频", exact: true })).toHaveAttribute(
    "href",
    `/watch/${B}?from=home`
  );
  await expect(card.getByRole("button", { name: "学前预览" })).toHaveCount(0);
  await expect(page.getByText(B_FEEDBACK, { exact: true })).toHaveCount(0);
  expect(errors).toEqual([]);
  await card.screenshot({ path: evidencePath("06-首页-完整视频介绍.png") });
});

test("10/12 片段深链与原句收词仍可用；首页多尺寸无横向溢出", async ({ request, page }) => {
  test.setTimeout(300_000);
  const lead = (await getPublicEditorial(request))!.lead!;
  const clip = lead.content.clip!;
  const expression = lead.content.expressions.find((item) => item.word)!;
  expect(clip.duration).toBeGreaterThan(0);
  expect(expression.word).toBeTruthy();
  const detail = await getAdminVideoDetail(request, B);
  expect(detail.subtitles.some((subtitle) => subtitle.id === expression.sentence.subtitle_id)).toBe(
    true
  );
  await loginUser(page);
  await page.goto(
    `/watch/${B}?from=home&clip=${lead.content.content_revision_id}&sub=${expression.sentence.subtitle_id}&word=${encodeURIComponent(expression.word!)}`
  );
  await expect(page.getByRole("region", { name: "片段任务", exact: true })).toContainText(
    lead.content.headline
  );
  const wordCard = page.getByTestId("word-tooltip");
  await expect(wordCard).toBeVisible();
  const [saved] = await Promise.all([
    page.waitForResponse(
      (response) =>
        new URL(response.url()).pathname === "/api/v1/vocabulary" &&
        response.request().method() === "POST"
    ),
    wordCard.getByRole("button", { name: "加入词库", exact: true }).click(),
  ]);
  expect([200, 201]).toContain(saved.status());
  const params = new URL(saved.request().url()).searchParams;
  expect(params.get("video_id")).toBe(B);
  expect(params.get("subtitle_id")).toBe(expression.sentence.subtitle_id);
  for (const [width, height] of [
    [1440, 900],
    [1280, 720],
    [390, 844],
    [375, 667],
    [320, 800],
  ]) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await expect(page.locator(".home-editorial-lead")).toContainText(lead.content.dek);
    const geometry = await page
      .locator("#main-scroll")
      .evaluate((el) => ({ scroll: el.scrollWidth, width: el.clientWidth }));
    expect(geometry.scroll, `width=${width}`).toBeLessThanOrEqual(geometry.width);
    await page.screenshot({ path: evidencePath(`home-content-${width}.png`) });
  }
});

test("11/12 首页编排页恢复上一版回到 A", async ({ request, page }) => {
  test.setTimeout(300_000);
  await loginAdmin(page);
  await page.setViewportSize({ width: 1440, height: 2600 });
  await page.goto("/admin/home-editorial");
  await expect(page.getByRole("heading", { name: "首页编排" })).toBeVisible({ timeout: 120_000 });
  await expect(page.getByText("使用新编排").first()).toBeVisible({ timeout: 120_000 });
  await captureAdminPage(page, 1440, 2800, "04-首页编排页-1440.png");

  const layout = await getLayout(request);
  expect(layout.published_layout?.lead).not.toBeNull();
  expect(layout.previous_published_layout).not.toBeNull();

  await page.getByRole("button", { name: "恢复上一版" }).click();
  const confirmDialog = page.getByRole("dialog", { name: "恢复上一发布布局" });
  await expect(confirmDialog).toBeVisible();
  const rollbackResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/admin/home-content/layout/rollback") &&
      response.request().method() === "POST"
  );
  await confirmDialog.getByRole("button", { name: "恢复上一版" }).click();
  const rollbackResponse = await rollbackResponsePromise;
  expect(rollbackResponse.status(), await rollbackResponse.text()).toBe(200);
  await expect(page.getByText(/已恢复上一发布布局/)).toBeVisible({ timeout: 60_000 });

  const publicPage = await getPublicEditorial(request);
  expect(publicPage?.lead?.content.video_id).toBe(A);
  expect(publicPage?.lead?.content.headline).toBe(A_HEADLINE);

  await loginUser(page);
  await page.goto("/");
  const detailA = await getAdminVideoDetail(request, A);
  await expect(page.locator(".home-editorial-lead")).toContainText(displayTitle(detailA), {
    timeout: 60_000,
  });
  await captureEditorialHome(page, 1440, 1600, "08-首页-恢复后-A-1440.png");
});

test("12/12 A 下线后拒绝恢复并说明；复原 A 后恢复可用", async ({ request, page }) => {
  test.setTimeout(300_000);
  // 先重新发布 B（当前=B、上一版=A），构造「回滚目标 A 已下线」的场景
  const stateB = await getVideoState(request, B);
  const republished = await publishContent(request, B, stateB.draft_revision, "lead");
  expect(republished.version).toBe(2);
  const layoutBefore = await getLayout(request);
  expect(layoutBefore.published_layout?.lead?.content_revision_id).toBe(republished.revision_id);
  expect(layoutBefore.previous_published_layout?.lead).not.toBeNull();

  // A 下线：走真实管理员 PATCH，公开可见性立即失效
  const offline = await request.patch(`/api/v1/videos/admin/${A}`, {
    headers: auth(adminToken),
    data: { is_published: false },
  });
  expect(offline.status(), await offline.text()).toBe(200);
  const publicWhileOffline = await getPublicEditorial(request);
  expect(publicWhileOffline?.lead?.content.video_id).toBe(B);
  const slotsWhileOffline = [
    publicWhileOffline?.lead,
    ...(publicWhileOffline?.secondary ?? []),
  ].filter((slot): slot is NonNullable<typeof slot> => Boolean(slot));
  expect(slotsWhileOffline.every((slot) => slot.content.video_id !== A)).toBe(true);

  // 管理端恢复上一版 → 409 HOME_CONTENT_ROLLBACK_INVALID，并给出原因
  await loginAdmin(page);
  await page.setViewportSize({ width: 1440, height: 2200 });
  await page.goto("/admin/home-editorial");
  await expect(page.getByRole("heading", { name: "首页编排" })).toBeVisible({ timeout: 120_000 });
  await page.getByRole("button", { name: "恢复上一版" }).click();
  const confirmDialog = page.getByRole("dialog", { name: "恢复上一发布布局" });
  await expect(confirmDialog).toBeVisible();
  const rollbackResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/admin/home-content/layout/rollback") &&
      response.request().method() === "POST"
  );
  await confirmDialog.getByRole("button", { name: "恢复上一版" }).click();
  const rollbackResponse = await rollbackResponsePromise;
  const rollbackBody = await readJson<ApiErrorBody>(
    rollbackResponse,
    409,
    "rollback with offline target"
  );
  expect(rollbackBody.code).toBe("HOME_CONTENT_ROLLBACK_INVALID");
  const rejectionToast = page.getByText(/上一版布局已不可恢复/);
  await expect(rejectionToast).toBeVisible({ timeout: 15_000 });
  // 等 sonner 进入动画结束（0.4s）再截图，否则截到 opacity=0 的瞬间；
  // 同时把页面滚回顶部，让 toast（top-center）+ 字段级错误在证据图里同框。
  console.log("[rollback-rejected] toast box:", JSON.stringify(await rejectionToast.boundingBox()));
  await page.evaluate(() => {
    const main = document.querySelector("main");
    if (main) main.scrollTo(0, 0);
  });
  await page.waitForTimeout(700);
  await page.screenshot({ path: evidencePath("09-恢复上一版-被拒绝.png") });

  // 被拒后公共页仍是 B，没有暴露已下线的 A
  expect((await getPublicEditorial(request))?.lead?.content.video_id).toBe(B);

  // 复原 A：可见性回来，恢复上一版可以成功
  const online = await request.patch(`/api/v1/videos/admin/${A}`, {
    headers: auth(adminToken),
    data: { is_published: true },
  });
  expect(online.status(), await online.text()).toBe(200);
  const layoutAfter = await getLayout(request);
  const rollback = await request.post("/api/v1/admin/home-content/layout/rollback", {
    headers: auth(adminToken),
    data: { expected_revision: layoutAfter.revision },
  });
  const rollbackSuccess = await readJson<PublishResult>(rollback, 200, "rollback after A online");
  expect(rollbackSuccess.layout_revision).toBeGreaterThan(0);
  expect((await getPublicEditorial(request))?.lead?.content.video_id).toBe(A);

  // 收尾自检：A 的可见性与 B 的字幕都已复原（草稿/版本由外部清理记录删除）
  const detailA = await getAdminVideoDetail(request, A);
  expect(detailA.is_published).toBe(true);
  const detailB = await getAdminVideoDetail(request, B);
  const monkey = findSubtitle(detailB.subtitles, "instant gratification monkey");
  expect(monkey.text_en).not.toContain("[verify-source-change]");
});
