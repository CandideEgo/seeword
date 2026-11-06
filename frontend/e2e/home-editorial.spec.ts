import { test, expect, type Page } from "@playwright/test";
import type { VideoCard } from "../src/types";
import type {
  HomeEditorialContent,
  HomeEditorialExpression,
  HomeEditorialExpressionSlot,
  HomeEditorialPage,
  HomeEditorialScenarioSlot,
  HomeEditorialSentence,
  HomeEditorialVideoSlot,
} from "../src/types/homeContent";

/**
 * 公共首页以完整视频为单位：展示原名与现有导语，保留发布/兜底边界。
 * 固定接口数据验证字段缺失、完整视频落点、双语推荐流与明暗主题多尺寸布局。
 */

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";

/** 只给 e2e / 证据截图用的封面占位图（真实首页读后端缩略图）。 */
const COVER_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1e3a5f"/>
      <stop offset="1" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <circle cx="930" cy="170" r="160" fill="#f59e0b" opacity="0.32"/>
  <rect x="90" y="370" width="430" height="180" rx="18" fill="#ffffff" opacity="0.12"/>
  <rect x="570" y="280" width="190" height="270" rx="18" fill="#ffffff" opacity="0.08"/>
  <path d="M90 630 L420 300 L640 630 Z" fill="#ffffff" opacity="0.06"/>
</svg>`;

function mintToken(): string {
  const b64 = (value: unknown) => Buffer.from(JSON.stringify(value)).toString("base64url");
  const header = b64({ alg: "HS256", typ: "JWT" });
  const payload = b64({
    sub: "home-editorial-test",
    name: "学习者",
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  return `${header}.${payload}.test`;
}

function videoCard(id: string, overrides: Partial<VideoCard> = {}): VideoCard {
  return {
    id,
    title: `视频 ${id}`,
    title_zh: null,
    source_url: `https://example.com/${id}`,
    video_source: "youtube",
    thumbnail_url: "/media/home-editorial-cover.svg",
    duration: 754,
    difficulty_level: "B1",
    status: "ready",
    error_message: null,
    topic_tags: null,
    is_official: true,
    is_published: true,
    review_status: "published",
    rejection_reason: null,
    video_url_480p: "/media/home-editorial-preview.mp4",
    video_url_720p: null,
    video_url_1080p: null,
    processing_mode: null,
    processing_step: null,
    processing_progress: 100,
    like_count: 0,
    favorite_count: 0,
    view_count: 0,
    score: null,
    score_updated_at: null,
    yt_video_id: null,
    channel_name: "TED",
    description: null,
    published_at: null,
    channel_slug: null,
    channel_cover_url: null,
    upload_date: null,
    ext_view_count: null,
    ext_like_count: null,
    wpm: null,
    vocabulary_density: null,
    created_at: "2026-10-01T00:00:00Z",
    metric: null,
    note_excerpt: null,
    has_note: false,
    favorited_at: null,
    forked_from: null,
    is_demo: false,
    storage_mode: "local",
    ...overrides,
  };
}

const LEAD_SENTENCE: HomeEditorialSentence = {
  subtitle_id: "sub-lead-1",
  sentence_index: 3,
  text_en: "Can you spot the difference?",
  text_zh: "你能看出区别吗？",
  start_time: 12.8,
  end_time: 15.2,
};

const TELL_SENTENCE: HomeEditorialSentence = {
  subtitle_id: "sub-lead-2",
  sentence_index: 6,
  text_en: "It's hard to tell the difference.",
  text_zh: "很难分辨出区别。",
  start_time: 20,
  end_time: 23,
};

const SPOT_EXPRESSION: HomeEditorialExpression = {
  id: "spot",
  subtitle_id: "sub-lead-1",
  phrase: "spot",
  word: "spot",
  gloss_zh: "v. 发现；识别出",
  note_zh: "先观察，再判断。",
  phonetic: "spɒt",
  word_start_time: 13.2,
  word_end_time: 13.8,
  sentence: LEAD_SENTENCE,
};

const TELL_EXPRESSION: HomeEditorialExpression = {
  id: "tell-difference",
  subtitle_id: "sub-lead-2",
  phrase: "tell the difference",
  word: null,
  gloss_zh: "分辨出区别",
  note_zh: "同一层意思，换一种说法。",
  phonetic: null,
  word_start_time: null,
  word_end_time: null,
  sentence: TELL_SENTENCE,
};

const LEAD_CONTENT: HomeEditorialContent = {
  content_revision_id: "rev-lead",
  video_id: "video-lead",
  version: 2,
  headline: "一张图，能藏住多少真相？",
  dek: "AI 图片越来越真。听懂辨别真假的思路，也学会用英语说「识破」。",
  topic_label: "图片辨真",
  source_label: "TED",
  published_at: "2026-10-19T08:00:00Z",
  clip: {
    start_subtitle_id: "sub-lead-1",
    end_subtitle_id: "sub-lead-2",
    start_time: 12.5,
    end_time: 54.5,
    duration: 42,
  },
  expressions: [SPOT_EXPRESSION, TELL_EXPRESSION],
  interaction: {
    id: "first-look",
    question: "如果是你，会先看哪里？",
    options: [
      {
        id: "detail",
        label: "脸和手的细节",
        feedback: "你会先看脸和手 —— 这更像先看局部的人。听听他的判断顺序。",
      },
      {
        id: "light",
        label: "光线和背景",
        feedback: "你会先看光线和背景 —— 这更像先看整体的人。听听他的判断顺序。",
      },
      {
        id: "unsure",
        label: "不太确定",
        feedback: "没关系，先听原片，带着自己的观察再回来选也可以。",
      },
    ],
  },
  scenarios: [],
  sentences: [LEAD_SENTENCE, TELL_SENTENCE],
};

const LEAD_SLOT: HomeEditorialVideoSlot = {
  content: LEAD_CONTENT,
  video: videoCard("video-lead", {
    title: "真实图片辨伪演讲",
    title_zh: "一张图，能藏住多少真相？",
    duration: 754,
    difficulty_level: "B1",
    channel_name: "TED",
  }),
};

const SECONDARY_ONE: HomeEditorialVideoSlot = {
  content: {
    ...LEAD_CONTENT,
    content_revision_id: "rev-secondary-1",
    video_id: "video-secondary-1",
    headline: "期待越多，关系反而越累？",
    dek: "「你应该懂我」的时候，我们究竟期待着什么？",
    topic_label: "关系与沟通",
    clip: null,
    expressions: [
      {
        ...SPOT_EXPRESSION,
        id: "expectations",
        subtitle_id: "sub-secondary-1",
        phrase: "expectations",
        word: "expectations",
        sentence: {
          ...LEAD_SENTENCE,
          subtitle_id: "sub-secondary-1",
          text_en: "Our expectations shape how we hear each other.",
          text_zh: "我们的期待塑造了我们如何听彼此说话。",
        },
      },
    ],
    interaction: null,
    sentences: [],
  },
  video: videoCard("video-secondary-1", {
    title: "关系里的期待",
    duration: 620,
    difficulty_level: "B1",
    channel_name: "TED",
  }),
};

const SECONDARY_TWO: HomeEditorialVideoSlot = {
  content: {
    ...LEAD_CONTENT,
    content_revision_id: "rev-secondary-2",
    video_id: "video-secondary-2",
    headline: "有人随时陪聊，就不会孤独了吗？",
    dek: "AI 能回应每句话。但陪伴，对你意味着什么？",
    topic_label: "科技与生活",
    clip: null,
    expressions: [
      {
        ...SPOT_EXPRESSION,
        id: "loneliness",
        subtitle_id: "sub-secondary-2",
        phrase: "loneliness",
        word: "loneliness",
        sentence: {
          ...LEAD_SENTENCE,
          subtitle_id: "sub-secondary-2",
          text_en: "Loneliness is not the same as being alone.",
          text_zh: "孤独和独处不是一回事。",
        },
      },
    ],
    interaction: null,
    sentences: [],
  },
  video: videoCard("video-secondary-2", {
    title: "AI 陪伴",
    duration: 540,
    difficulty_level: "B2",
    channel_name: "TED",
  }),
};

const EXPRESSION_SLOT: HomeEditorialExpressionSlot = {
  content_revision_id: "rev-lead",
  expression_id: "tell-difference",
  headline: LEAD_CONTENT.headline,
  topic_label: LEAD_CONTENT.topic_label,
  video: LEAD_SLOT.video,
  expression: TELL_EXPRESSION,
};

const SCENARIO_ANCHOR = LEAD_SENTENCE;

const SCENARIO_SLOTS: HomeEditorialScenarioSlot[] = [
  {
    content_revision_id: "rev-lead",
    scenario_id: "rain-check",
    video: LEAD_SLOT.video,
    scenario: {
      id: "rain-check",
      situation_zh: "图片辨真 · 观察细节",
      prompt_zh: "朋友发来一张疑似 AI 生成的图，问他有没有发现异常。",
      reply_en: "Can you spot anything unusual?",
      reply_zh: "你能发现什么异常吗？",
      sentence: SCENARIO_ANCHOR,
    },
  },
  {
    content_revision_id: "rev-lead",
    scenario_id: "loop",
    video: LEAD_SLOT.video,
    scenario: {
      id: "loop",
      situation_zh: "日常比较 · 区分差异",
      prompt_zh: "两张图片看起来一样，你想说很难分辨。",
      reply_en: "It's hard to tell the difference.",
      reply_zh: "很难分辨出区别。",
      sentence: TELL_SENTENCE,
    },
  },
  {
    content_revision_id: "rev-lead",
    scenario_id: "call-it-a-day",
    video: LEAD_SLOT.video,
    scenario: {
      id: "call-it-a-day",
      situation_zh: "看图交流 · 表达判断",
      prompt_zh: "暂时判断不了图片真假，说说你的下一步打算。",
      reply_en: "I would take a closer look.",
      reply_zh: "我会仔细看一下。",
      sentence: LEAD_SENTENCE,
    },
  },
];

LEAD_CONTENT.scenarios = SCENARIO_SLOTS.map((slot) => slot.scenario);

const EDITORIAL: HomeEditorialPage = {
  layout_revision: 7,
  published_at: "2026-10-19T08:00:00Z",
  lead: LEAD_SLOT,
  secondary: [SECONDARY_ONE, SECONDARY_TWO],
  expression: EXPRESSION_SLOT,
  scenarios: SCENARIO_SLOTS,
};

function cloneEditorial(): HomeEditorialPage {
  return structuredClone(EDITORIAL);
}

const FEATURED = {
  items: [
    videoCard("featured-1", {
      title: "本周精选视频",
      video_url_480p: null,
      channel_name: "TED",
    }),
  ],
};

/**
 * 进首页的公共 mock：catch-all 先注册、具体路由后注册（Playwright 后注册的先匹配）。
 * `editorial` 为 null 表示接口返回 `{"editorial": null}`（未发布编排）。
 */
async function mockHome(
  page: Page,
  editorial: HomeEditorialPage | null,
  options: { editorialStatus?: number } = {}
): Promise<void> {
  await page.route("https://fonts.googleapis.com/**", (route) => route.abort());
  await page.route("https://fonts.gstatic.com/**", (route) => route.abort());

  const token = mintToken();
  await page.context().addCookies([{ name: "seeword_token", value: token, url: BASE_URL }]);
  await page.addInitScript((value: string) => {
    window.localStorage.setItem("seeword_token", value);
  }, token);

  await page.route("**/api/**", (route) => route.fulfill({ json: {} }));
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({
      json: { id: "home-editorial-test", name: "学习者", onboarding_completed: true },
    })
  );
  await page.route("**/api/v1/browse/featured**", (route) => route.fulfill({ json: FEATURED }));
  await page.route("**/api/v1/browse/home-editorial", (route) => {
    if (options.editorialStatus) {
      return route.fulfill({
        status: options.editorialStatus,
        json: { code: "HTTP_404", message: "接口尚未发布" },
      });
    }
    return route.fulfill({ json: { editorial } });
  });
  await page.route("**/api/v1/vocabulary/stats**", (route) =>
    route.fulfill({ json: { total: 12, due_count: 0 } })
  );
  await page.route("**/api/v1/learning/records**", (route) =>
    route.fulfill({ json: { items: [] } })
  );
  await page.route("**/api/v1/learning/stats/weekly**", (route) =>
    route.fulfill({
      json: { this_week_minutes: 0, this_week_words: 0, this_week_videos: 0 },
    })
  );
  await page.route("**/api/v1/recommendations/home**", (route) =>
    route.fulfill({ json: { items: [], page: 1, page_size: 20, has_more: false, total: 0 } })
  );
  await page.route("**/media/home-editorial-cover.svg", (route) =>
    route.fulfill({ contentType: "image/svg+xml", body: COVER_SVG })
  );
  await page.route("**/media/home-editorial-preview.mp4", (route) =>
    route.fulfill({ contentType: "video/mp4", body: Buffer.alloc(0) })
  );
}

async function openEditorial(page: Page, editorial: HomeEditorialPage = EDITORIAL): Promise<void> {
  await mockHome(page, editorial);
  await page.goto("/");
  await expect(page.locator(".home-editorial-lead")).toBeVisible();
}

test.describe("已发布编排：完整视频发现", () => {
  test("双语标题保留，辅助导语移除，完整视频入口保留", async ({ page }) => {
    await openEditorial(page);
    await expect(page.getByRole("heading", { name: /^发现 · / })).toBeVisible();
    const card = page.getByRole("article", { name: "精选视频", exact: true });
    await expect(card).toContainText(LEAD_SLOT.video.title);
    await expect(card).toContainText(LEAD_SLOT.video.title_zh!);
    await expect(card).not.toContainText(LEAD_CONTENT.dek);
    await expect(card).toContainText("12:34");
    await expect(card.getByRole("link", { name: "从这句话开始", exact: true })).toHaveAttribute(
      "href",
      /^\/watch\/video-lead\?from=home&t=12$/
    );
    // hero 元信息按设计改为「句数 · 主题 · 点赞 · 收藏」，不展示发布/播放量（V-12）。
    await expect(card).not.toContainText("原片发布");
    await expect(card).not.toContainText("次播放");
    await expect(card.getByLabel(/^点赞 /)).toBeVisible();
    await expect(card.getByLabel(/^收藏 /)).toBeVisible();
    await expect(page.locator("#home-scenarios")).toHaveCount(0);
    await expect(page.getByRole("navigation", { name: "我的学习入口" })).toHaveCount(0);
    await expect(page.getByText(LEAD_SENTENCE.text_en, { exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "脸和手的细节" })).toHaveCount(0);
  });

  test("编辑标题不替换视频原名，不展示辅助导语", async ({ page }) => {
    const editorial = cloneEditorial();
    editorial.lead!.content.headline = "不应替换视频名的编辑标题";
    editorial.lead!.video.description = "原平台内容介绍";
    await openEditorial(page, editorial);
    const card = page.getByRole("article", { name: "精选视频", exact: true });
    await expect(card).toContainText(LEAD_SLOT.video.title_zh!);
    await expect(card).not.toContainText("不应替换视频名的编辑标题");
    await expect(card).not.toContainText(LEAD_CONTENT.dek);
    await expect(card).not.toContainText("原平台内容介绍");
  });

  test("不显示简介小字，缺中文标题与其他元信息时保持可用", async ({ page }) => {
    const editorial = cloneEditorial();
    editorial.lead!.content.dek = " ";
    editorial.lead!.video = videoCard("video-lead", {
      title: "Original English video",
      title_zh: null,
      description: "What happens when we compare real and generated images.",
      duration: null,
      difficulty_level: null,
      channel_name: null,
    });
    await openEditorial(page, editorial);
    const card = page.getByRole("article", { name: "精选视频", exact: true });
    await expect(card).not.toContainText("What happens when we compare real and generated images.");
    await expect(card.getByRole("heading")).toHaveText("Original English video");
    await expect(card.getByRole("link", { name: "从这句话开始", exact: true })).toHaveAttribute(
      "href",
      /^\/watch\/video-lead\?from=home&t=12$/
    );
    await expect(card).not.toContainText("待评估");
  });

  test("没有有效编排或接口失败时回退普通精选", async ({ page }) => {
    await mockHome(page, null, { editorialStatus: 404 });
    await page.goto("/");
    const card = page.getByRole("article", { name: "精选视频", exact: true });
    await expect(card).toContainText("本周精选视频");
    await expect(card.getByRole("link", { name: "观看完整视频", exact: true })).toHaveAttribute(
      "href",
      "/watch/featured-1?from=home"
    );
    await expect(page.locator("#feed")).toBeVisible();
  });

  test("没有精选时省略推荐区，视频流仍然可用", async ({ page }) => {
    await mockHome(page, null);
    await page.route("**/api/v1/browse/featured**", (route) =>
      route.fulfill({ json: { items: [] } })
    );
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "继续发现" })).toBeVisible();
    await expect(page.getByRole("article", { name: "精选视频", exact: true })).toHaveCount(0);
    await expect(page.getByText("精选内容准备中，先去频道找找。")).toHaveCount(0);
  });

  test("推荐流保留双语标题并移除说明小字，不请求学习指标", async ({ page }) => {
    await mockHome(page, null);
    const metadataRequests: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("learning-metadata")) metadataRequests.push(request.url());
    });
    await page.route("**/api/v1/recommendations/home**", (route) =>
      route.fulfill({
        json: {
          items: [
            videoCard("feed-video", {
              title: "English title",
              title_zh: "中文内容标题",
              description: "这条视频介绍动物如何辨认同伴。",
            }),
          ],
          page: 1,
          page_size: 20,
          total: 1,
          has_more: false,
        },
      })
    );
    await page.goto("/");
    const feed = page.locator("#feed");
    await expect(feed).toContainText("中文内容标题");
    await expect(feed).toContainText("English title");
    await expect(feed).not.toContainText("这条视频介绍动物如何辨认同伴。");
    expect(metadataRequests).toEqual([]);
    await expect(
      feed.locator('[aria-label^="点赞数"], [aria-label^="播放量"], [aria-label^="收藏数"]')
    ).toHaveCount(0);
  });

  for (const theme of ["light", "dark"]) {
    test(`${theme}主题：桌面与手机内容可读且无横向溢出`, async ({ page }) => {
      await mockHome(page, EDITORIAL);
      await page.addInitScript((value) => localStorage.setItem("theme", value), theme);
      for (const [width, height] of [
        [1440, 900],
        [1280, 720],
        [390, 844],
        [375, 667],
        [320, 800],
      ]) {
        await page.setViewportSize({ width, height });
        await page.goto("/");
        const card = page.getByRole("article", { name: "精选视频", exact: true });
        await expect(card).toContainText(LEAD_SLOT.video.title);
        await expect(card).not.toContainText(LEAD_CONTENT.dek);
        const action = card.getByRole("link", { name: "从这句话开始", exact: true });
        await action.scrollIntoViewIfNeeded();
        await expect(action).toBeInViewport();
        const geometry = await page
          .locator("#main-scroll")
          .evaluate((el) => ({ scroll: el.scrollWidth, width: el.clientWidth }));
        expect(geometry.scroll).toBeLessThanOrEqual(geometry.width);
        await page.screenshot({ path: test.info().outputPath(`discovery-${theme}-${width}.png`) });
      }
    });
  }
});
