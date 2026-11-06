import { test, expect, type Page } from "@playwright/test";
import { setupWatch, openWatch, VIDEO_ID, subtitles } from "./watch-baseline.fixture";
import { chooseSelectMenu } from "./helpers";

const VIDEO = {
  id: "content-video",
  title: "How birds find their way",
  title_zh: "鸟儿如何找到回家的路",
  description: "跟随研究人员观察候鸟如何利用地标与磁场导航。",
  source_url: "https://example.com/birds",
  thumbnail_url: null,
  duration: 480,
  channel_name: "Nature Lab",
  channel_title: "Nature Lab",
  channel_slug: "nature-lab",
  difficulty_level: "B1",
  storage_mode: "local",
  status: "ready",
  like_count: 17,
  view_count: 58,
  favorite_count: 9,
};

async function mockContent(page: Page) {
  await setupWatch(page);
  await page.route("**/api/v1/discovery/search**", (route) =>
    route.fulfill({
      json: {
        videos: { items: [VIDEO], has_more: true },
        channels: {
          items: [
            {
              id: "channel",
              name: "Nature Lab",
              slug: "nature-lab",
              description: "观察自然与科学",
            },
          ],
          has_more: false,
        },
        subtitles: {
          items: [
            {
              id: "sentence",
              text_en: "Birds find their way.",
              text_zh: "鸟儿找到方向。",
              start_time: 15,
              video: VIDEO,
            },
          ],
          has_more: false,
        },
        words: {
          items: [
            { lemma: "birds", phonetic: null, translation: "鸟", definition: null, levels: [] },
          ],
          has_more: false,
        },
      },
    })
  );
  await page.route("**/api/v1/users/me/preferences", (route) =>
    route.fulfill({ json: { target_exam: "cet4", subtitle_font_size: "medium" } })
  );
  await page.route("**/api/v1/discovery/practice-summary", (route) =>
    route.fulfill({
      json: { types: { reading: { group_count: 2, question_count: 8 } }, recent: [] },
    })
  );
  await page.route("**/api/v1/channels/nature-lab?**", (route) =>
    route.fulfill({
      json: {
        channel: {
          id: "channel",
          slug: "nature-lab",
          name: "Nature Lab",
          description: "观察自然与科学",
          cover_url: null,
          video_count: 1,
        },
        videos: { items: [VIDEO], total: 1, page: 1, page_size: 20, has_more: false },
        recommended_start: null,
      },
    })
  );
}

test("我的默认展示学习资产与账户卡，五个一级导航和旧设置链接可用", async ({ page }) => {
  await mockContent(page);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/profile");
    await expect(page.getByRole("heading", { name: "我的内容", exact: true })).toBeVisible();
    const mainNav =
      width >= 768
        ? page.getByRole("navigation", { name: "学习导航", exact: true })
        : page.getByRole("navigation", { name: "底部导航", exact: true });
    const links = mainNav.getByRole("link");
    // 桌面还包含资料库入口；前五个必须与手机一致。
    for (const [index, label] of ["发现", "频道", "练习", "词汇", "我的"].entries())
      await expect(links.nth(index)).toHaveAccessibleName(label);
    if (width < 768) await expect(links).toHaveCount(5);
    const hub = page.locator("#profile-panel-content");
    // 设计「概览」只有学习资产 + 最近学习/节奏；六宫格快捷入口不在设计里（V-17）。
    await expect(hub.getByRole("region", { name: "学习资产" })).toBeVisible();
    await expect(hub.locator('a[href="/favorites"]')).toHaveCount(0);
    await expect(hub.locator('a[href="/upgrade"]')).toHaveCount(0);
  }
  await page.goto("/profile?tab=settings");
  await expect(page.getByRole("tab", { name: "设置", exact: true })).toHaveAttribute(
    "aria-selected",
    "true"
  );
});

test("搜索先给视频和频道，双语标题及简介与完整视频入口一致", async ({ page }) => {
  await mockContent(page);
  await page.goto("/search?q=birds");
  const results = page.locator(".user-page-main");
  await expect(results.getByRole("region", { name: "视频", exact: true })).toContainText(
    VIDEO.description
  );
  const card = results
    .getByRole("region", { name: "视频", exact: true })
    .locator(".user-content-list > a");
  await expect(card).toContainText(VIDEO.title_zh);
  await expect(card).toContainText(VIDEO.title);
  await expect(card).toContainText("Nature Lab");
  await expect(card).toHaveAttribute("href", /\/watch\/content-video\?from=search/);
  await expect(
    card.locator('[aria-label^="点赞数"], [aria-label^="播放量"], [aria-label^="收藏数"]')
  ).toHaveCount(0);
  const groups = await results
    .getByRole("region")
    .evaluateAll((elements) => elements.map((el) => el.getAttribute("aria-label")));
  expect(groups).toEqual(["视频", "频道", "字幕", "词汇"]);
  await results
    .getByRole("region", { name: "视频", exact: true })
    .getByRole("link", { name: "查看全部 →" })
    .click();
  await expect(page).toHaveURL(/group=videos/);
});

test("频道视频用已有简介解释内容，不展示字幕与考试词计数", async ({ page }) => {
  await mockContent(page);
  await page.goto("/channels/nature-lab");
  await expect(page.getByRole("heading", { name: "Nature Lab", exact: true })).toBeVisible();
  const content = page.locator(".user-page-main");
  await expect(content.getByText(VIDEO.description).first()).toBeVisible();
  await expect(content).not.toContainText("句字幕");
  await expect(content).not.toContainText("个考试词");
});

test("真题的范围与结果说明默认折叠，原练习入口仍可用", async ({ page }) => {
  await mockContent(page);
  await page.goto("/practice");
  // 2026-10 练习页改版把「这一版包含」并入右栏「题库概览」，断言仍覆盖
  // 「范围默认折叠 + 数字来自 practice-summary」两件事。
  const range = page
    .locator("details")
    .filter({ has: page.locator("summary", { hasText: "题库概览" }) });
  await expect(range).toBeVisible();
  await expect(range).not.toHaveAttribute("open", "");
  await range.locator("summary").click();
  await expect(range).toContainText("2 组 · 8 题");
});

test("观看核心区移走互动计数，基础词义直接可读，考试信息按需展开", async ({ page }) => {
  await setupWatch(page, { richGloss: true });
  await openWatch(page, "?sub=second");
  const info = page
    .locator("details")
    .filter({ has: page.locator("summary", { hasText: "视频信息" }) });
  // 视频信息默认展开（描述/来源/互动数可见）；考试标签仍在词卡里按需展开。
  await expect(info).toHaveAttribute("open", "");
  await expect(page.getByLabel("点赞数 0", { exact: true })).toBeVisible();
  await expect(info.getByRole("link", { name: "查看原始来源 ↗" })).toHaveAttribute(
    "href",
    /youtube\.com/
  );
  await page
    .getByTestId("current-sentence-card")
    .getByRole("button", { name: "查看 walk 的词义", exact: true })
    .click();
  const card = page.getByRole("dialog", { name: "walk 词卡", exact: true });
  await expect(card.getByTestId("word-brief-meaning")).toBeVisible();
  await expect(card.getByRole("button", { name: "加入词库", exact: true })).toBeVisible();
  await expect(card.getByText("四级", { exact: true })).not.toBeVisible();
  await card.getByText("考试标签", { exact: true }).click();
  await expect(card.getByText("四级", { exact: true })).toBeVisible();
});

test("片段与表达只在展开后读取，使用当前视频已发布版本，旧片段深链继续可用", async ({ page }) => {
  const fixture = await setupWatch(page);
  let reads = 0;
  await page.route("**/api/v1/browse/home-editorial", (route) => {
    reads++;
    return route.fulfill({
      json: {
        editorial: {
          layout_revision: 1,
          lead: {
            video: { id: VIDEO_ID },
            content: {
              content_revision_id: "published-revision",
              headline: "一段真实的行走表达",
              clip: {
                start_subtitle_id: "second",
                end_subtitle_id: "second",
                start_time: 5,
                end_time: 8,
                duration: 3,
              },
              expressions: [
                {
                  id: "walk",
                  phrase: "walk home",
                  gloss_zh: "走回家",
                  sentence: { ...subtitles[1], subtitle_id: "second" },
                },
              ],
            },
          },
          secondary: [],
          scenarios: [],
          expression: null,
        },
      },
    });
  });
  await openWatch(page, "?from=channel&slug=nature-lab");
  expect(reads).toBe(0);
  const editorial = page
    .locator("details")
    .filter({ has: page.locator("summary", { hasText: "片段与表达" }) });
  await editorial.locator("summary").click();
  await expect(editorial).toContainText("走回家");
  expect(reads).toBe(1);
  const clip = editorial.getByRole("link", { name: /观看片段/ });
  await expect(clip).toHaveAttribute("href", /clip=published-revision/);
  await expect(clip).toHaveAttribute("href", /from=channel&slug=nature-lab/);
  await clip.click();
  await expect(page.getByRole("region", { name: "片段任务", exact: true })).toContainText(
    "一段真实的行走表达"
  );
  expect(fixture.calls.some((call) => call.path.includes("/admin/"))).toBe(false);
});

test("其他视频的发布内容不会出现在当前视频中", async ({ page }) => {
  await setupWatch(page);
  await page.route("**/api/v1/browse/home-editorial", (route) =>
    route.fulfill({
      json: {
        editorial: {
          lead: {
            video: { id: "other" },
            content: { expressions: [{ phrase: "其他视频的表达" }] },
          },
          secondary: [],
          scenarios: [],
        },
      },
    })
  );
  await openWatch(page);
  await page.locator("summary", { hasText: "片段与表达" }).click();
  await expect(page.getByText("其他视频的表达", { exact: true })).toHaveCount(0);
  await expect(page.locator("summary", { hasText: "片段与表达" })).toHaveCount(0);
});

test("词汇区分累计与本轮数量；词库按真实定位区分原句和来源视频", async ({ page }) => {
  await mockContent(page);
  const words = [
    {
      id: "word-1",
      word: "walk",
      ipa: null,
      part_of_speech: "v:100",
      mastery_level: "reviewing",
      review_count: 1,
      definition: null,
      translation: "v. 行走；步行",
      difficulty_level: "cet4",
      context_sentence: "Then I walk home.",
      video_id: VIDEO_ID,
      subtitle_id: "second",
      next_review_at: null,
    },
    {
      id: "word-2",
      word: "birds",
      ipa: null,
      part_of_speech: "n:100",
      mastery_level: "new",
      review_count: 0,
      definition: null,
      translation: "n. 鸟",
      difficulty_level: null,
      context_sentence: null,
      video_id: "content-video",
      subtitle_id: null,
      next_review_at: null,
    },
  ];
  await page.route("**/api/v1/vocabulary/stats", (route) =>
    route.fulfill({
      json: {
        total: 250,
        due_count: 239,
        mastered_count: 0,
        learning_count: 11,
        reviewing_count: 239,
      },
    })
  );
  await page.route("**/api/v1/vocabulary?**", (route) =>
    route.fulfill({ json: { items: words, total: 2, page: 1, page_size: 20, has_more: false } })
  );
  await page.route("**/api/v1/vocabulary/daily-session", (route) =>
    route.fulfill({
      json: {
        new_words: [],
        review_words: words,
        totals: { new_total: 0, due_total: 239 },
        today: { words_learned: 0, rounds: 0 },
        preferences: { daily_new_target: 10, daily_review_target: 10 },
      },
    })
  );
  await page.goto("/vocabulary");
  // 累计到期（239）与本轮队列（2）必须分开表述：一个是大盘，一个是本轮。
  await expect(page.getByText("本轮复习 2 个 · 新词 0 个", { exact: true })).toBeVisible();
  await expect(page.getByText("累计还有 239 个到期词", { exact: false })).toBeVisible();
  await page.goto("/vocabulary?tab=library&sub=words");
  await expect(page.getByText("原句：Then I walk home.")).toBeVisible();
  await expect(page.getByRole("link", { name: "去原句 →", exact: true })).toHaveAttribute(
    "href",
    /sub=second/
  );
  await expect(page.getByRole("link", { name: "去来源视频 →", exact: true })).toHaveAttribute(
    "href",
    "/watch/content-video?from=vocabulary"
  );
  await expect(page.getByText("v:100", { exact: true })).toHaveCount(0);
});

test("通知页是单列列表，页头提供设置与全部已读", async ({ page }) => {
  await mockContent(page);
  await page.route("**/api/v1/notifications?**", (route) =>
    route.fulfill({
      json: {
        items: [
          {
            id: "n1",
            type: "video_ready",
            title: "视频已就绪",
            message: "你收藏的视频已经处理完成。",
            is_read: false,
            related_url: "/watch/content-video",
            created_at: "2026-10-21T12:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        has_more: false,
      },
    })
  );
  await page.route("**/api/v1/notifications/unread-count", (route) =>
    route.fulfill({ json: { count: 1 } })
  );

  await page.goto("/notifications");
  await expect(page.getByRole("heading", { name: "通知", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "通知设置" })).toHaveAttribute(
    "href",
    "/profile?tab=settings"
  );
  await expect(page.getByRole("button", { name: /全部标为已读/ })).toBeVisible();
  await expect(page.getByText("视频已就绪", { exact: true })).toBeVisible();
  // 设计是单列列表，没有类型 tab、最近通知分区或右栏统计（V-20）。
  await expect(page.getByRole("button", { name: /^全部 \d+$/ })).toHaveCount(0);
  await expect(page.getByText("最近通知")).toHaveCount(0);
  await expect(page.getByText("未读统计")).toHaveCount(0);
});

test("收藏保留笔记与日期，历史保留观看进度和来源信息", async ({ page }) => {
  await mockContent(page);
  await page.route("**/api/v1/videos/favorites?**", (route) =>
    route.fulfill({
      json: {
        items: [
          {
            ...VIDEO,
            favorited_at: "2026-10-21T12:00:00Z",
            has_note: true,
            note_excerpt: "想再听一次的内容",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        has_more: false,
      },
    })
  );
  await page.goto("/favorites");
  await expect(page.getByText(VIDEO.description, { exact: true })).toBeVisible();
  await expect(page.getByText("想再听一次的内容", { exact: false })).toBeVisible();
  // 设计是「视频 / 原句」tab，不再是三段常驻（V-18）。
  await expect(page.getByRole("region", { name: "收藏的视频" })).toBeVisible();
  await page.getByRole("button", { name: /^原句 \d+$/ }).click();
  await expect(page.getByRole("region", { name: "收藏的句子" })).toBeVisible();
  await expect(page.getByRole("region", { name: "收藏的视频" })).toHaveCount(0);
  await page.getByRole("button", { name: /^视频 \d+$/ }).click();
  const card = page.locator("a").filter({ has: page.getByText(VIDEO.title_zh, { exact: true }) });
  await expect(card).toBeVisible();
  await expect(
    card.locator('[aria-label^="点赞数"], [aria-label^="播放量"], [aria-label^="收藏数"]')
  ).toHaveCount(0);
  await page.route("**/api/v1/learning/stats/weekly", (route) =>
    route.fulfill({ json: { this_week_minutes: 8 } })
  );
  await page.route("**/api/v1/learning/records?**", (route) =>
    route.fulfill({
      json: {
        items: [
          {
            id: "record",
            video_id: VIDEO.id,
            video: VIDEO,
            completed: false,
            position_seconds: 60,
            progress_percentage: 25,
            words_learned: 3,
            time_spent_seconds: 120,
            quiz_score: null,
            last_accessed_at: "2026-10-21T12:00:00Z",
            created_at: "2026-10-21T12:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
        has_more: false,
      },
    })
  );
  await page.goto("/history");
  await expect(page.getByRole("heading", { name: "观看历史", exact: true })).toBeVisible();
  // 设计在记录列表上方有最近观看 / 最近练习 / 词汇进展三张卡（V-19）。
  await expect(page.getByRole("heading", { name: "最近观看", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "最近练习", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "词汇进展", exact: true })).toBeVisible();
  // 卡片里也会出现标题，这里只断言记录列表中的一条。
  await expect(page.locator("ul").getByText(VIDEO.title_zh, { exact: true })).toBeVisible();
  await expect(page.getByText("停在 1:00", { exact: true })).toBeVisible();
  await expect(page.getByText("25%", { exact: true })).toBeVisible();
  await expect(page.locator("main").getByText("Nature Lab", { exact: true })).toBeVisible();
});

for (const width of [1440, 390]) {
  test(`${width}：筛选写入请求，观看后返回保留筛选与列表位置`, async ({ page }) => {
    await mockContent(page);
    await page.setViewportSize({ width, height: 844 });
    const items = Array.from({ length: 24 }, (_, index) => ({
      ...VIDEO,
      id: index === 6 ? VIDEO_ID : `browse-${index}`,
      title: `English video ${index}`,
      title_zh: `候鸟观察 ${index}`,
      video_id: index === 6 ? VIDEO_ID : `browse-${index}`,
    }));
    await page.route("**/api/v1/browse/home-editorial", (route) =>
      route.fulfill({ json: { editorial: null } })
    );
    await page.route("**/api/v1/browse/featured**", (route) =>
      route.fulfill({ json: { items: [] } })
    );
    const requests: URLSearchParams[] = [];
    await page.route("**/api/v1/browse/feed?**", (route) => {
      requests.push(new URL(route.request().url()).searchParams);
      return route.fulfill({ json: { items, page: 1, page_size: 24, total: 24, has_more: false } });
    });
    await page.goto("/?category=tech&level=B1&sort=favorite");
    await expect(page.locator("#feed-level")).toContainText("B1 · ≈四级");
    await chooseSelectMenu(page, page.locator("#feed-level"), /^A2 · /);
    await expect.poll(() => requests.at(-1)?.get("level")).toBe("A2");
    await chooseSelectMenu(page, page.locator("#feed-sort"), "热播");
    await expect.poll(() => requests.at(-1)?.get("sort")).toBe("hot");
    const video = page
      .locator('#feed [data-testid="home-feed-grid"] > a')
      .filter({ hasText: "候鸟观察 6" });
    await video.scrollIntoViewIfNeeded();
    await expect(video).toHaveAttribute(
      "href",
      `/watch/${VIDEO_ID}?from=home&category=tech&level=A2&sort=hot`
    );
    const scrollTop = await page.locator("#main-scroll").evaluate((element) => element.scrollTop);
    await video.click();
    // 新版 390 手机布局把逐句操作收进壳层播放栏；桌面档仍是内容区的 sentence-actions。
    await expect(
      width < 1024 ? page.getByTestId("watch-bottom-bar") : page.getByTestId("sentence-actions")
    ).toBeVisible();
    await page.getByRole("button", { name: "返回首页", exact: true }).click();
    await expect(page).toHaveURL(/category=tech&level=A2&sort=hot/);
    await expect(page.locator("#feed-level")).toContainText("A2 · ≈高考");
    await expect(page.locator("#feed-sort")).toContainText("热播");
    await expect
      .poll(() => page.locator("#main-scroll").evaluate((element) => element.scrollTop))
      .toBe(scrollTop);
  });
}
