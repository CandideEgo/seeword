import { test, expect, type Page } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { setupWatch } from "./watch-baseline.fixture";
import { chooseSelectMenu } from "./helpers";

const videos = Array.from({ length: 8 }, (_, index) => ({
  id: `discover-layout-${index}`,
  title: [
    "Learn English through everyday stories",
    "A conversation about the world around us",
    "Small moments, useful expressions",
  ][index % 3],
  title_zh: null,
  duration: 180 + index * 47,
  difficulty_level: "B1",
  channel_name: "SeeWord English",
  channel_slug: "layout-fixture",
  topic_tags: "education",
  thumbnail_url: "/media/layout-cover.svg",
  storage_mode: "local",
  status: "ready",
  view_count: index === 0 ? 0 : index * 1024,
  favorite_count: index === 0 ? 0 : index * 3,
  like_count: 0,
  upload_date: index % 2 ? null : "2026-10-01",
  published_at: "2026-10-20T00:00:00Z",
}));

async function setupDiscovery(page: Page) {
  await setupWatch(page);
  await page.route("**/api/v1/discovery/subscriptions", (route) => route.fulfill({ json: [] }));
  await page.route("**/media/layout-cover.svg", (route) =>
    route.fulfill({
      contentType: "image/svg+xml",
      body: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360"><rect width="640" height="360" fill="#e1edf5"/><circle cx="490" cy="160" r="110" fill="#b4d3e8"/><text x="40" y="195" font-family="sans-serif" font-size="38" fill="#17364a">Everyday English</text></svg>',
    })
  );
  await page.route("**/api/v1/browse/home-editorial", (route) =>
    route.fulfill({ json: { editorial: null } })
  );
  await page.route("**/api/v1/browse/featured**", (route) =>
    route.fulfill({ json: { items: videos.slice(0, 1) } })
  );
  await page.route("**/api/v1/recommendations/home**", (route) =>
    route.fulfill({
      json: { items: videos, total: videos.length, has_more: false, page: 1, page_size: 20 },
    })
  );
  await page.route("**/api/v1/browse/feed**", (route) =>
    route.fulfill({
      json: { items: videos, total: videos.length, has_more: false, page: 1, page_size: 20 },
    })
  );
  await page.route("**/api/v1/users/me/overview", (route) =>
    route.fulfill({
      json: {
        words: { total: 24, due_review_count: 0 },
        this_week: { days_active: 1, minutes: 5 },
        streak: { current: 1 },
      },
    })
  );
  await page.route("**/api/v1/channels/layout-fixture?**", (route) =>
    route.fulfill({
      json: {
        channel: {
          id: "layout-channel",
          slug: "layout-fixture",
          name: "SeeWord English",
          description: "日常表达与真实对话",
          video_count: videos.length,
          subscriber_count: 0,
          total_view_count: 0,
          is_subscribed: false,
          cover_url: "/media/layout-cover.svg",
        },
        videos: { items: videos, total: videos.length, page: 1, page_size: 20, has_more: false },
        recommended_start: null,
      },
    })
  );
}

for (const width of [360, 390, 430, 600, 820, 1024, 1366, 1440, 1920]) {
  test(`发现和频道 ${width}：留白、分类、元数据与筛选完整`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: width <= 1024 ? 844 : 900 });
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await setupDiscovery(page);
    await page.goto("/");
    const grid = page.getByTestId("home-feed-grid");
    await expect(grid.locator(":scope > a")).toHaveCount(videos.length);
    const feature = (await page.getByRole("article", { name: "精选视频" }).boundingBox())!;
    const feed = (await page.locator("#feed").boundingBox())!;
    expect(feed.y - feature.y - feature.height).toBeGreaterThanOrEqual(16);
    expect(feed.y - feature.y - feature.height).toBeLessThanOrEqual(32);
    const firstCard = grid.locator(":scope > a").first();
    await expect(firstCard.getByLabel("本站播放 0 次")).toBeVisible();
    await expect(firstCard.getByLabel("收藏 0 次")).toBeVisible();
    await expect(firstCard.locator("time")).toHaveAttribute("title", /原片发布/);
    await expect(firstCard).not.toContainText("次播放");
    const categories = page.getByLabel("视频分类");
    for (const button of await categories.getByRole("button").all()) {
      const bounds = (await button.boundingBox())!;
      expect(bounds.x).toBeGreaterThanOrEqual(0);
      expect(bounds.x + bounds.width).toBeLessThanOrEqual(width);
    }
    await chooseSelectMenu(page, page.locator("#feed-level"), /^C1 · /);
    await expect(page).toHaveURL(/level=C1/);
    await expect(page.locator("#feed-level")).toContainText("C1 · ≈考研/雅思");
    await chooseSelectMenu(page, page.locator("#feed-sort"), "本周收藏");
    const selectFits = await page
      .locator("#feed-level")
      .evaluate((element) => element.scrollWidth <= element.clientWidth + 1);
    expect(selectFits).toBe(true);
    expect(
      await page.locator("main").evaluate((el) => el.scrollWidth - el.clientWidth)
    ).toBeLessThanOrEqual(1);
    const directory = resolve("../tmp/e2e-evidence/discover-watch", info.project.name);
    if (width === 390 || width === 1440) {
      mkdirSync(directory, { recursive: true });
      await page.locator("main").evaluate((el) => {
        el.scrollTop = 0;
      });
      await page.screenshot({
        path: resolve(directory, `discover-${width}.png`),
        animations: "disabled",
      });
    }
    await page.getByRole("button", { name: "清除筛选", exact: true }).click();
    await expect(page.locator("#feed-level")).toContainText("全部档位");
    await expect(page.locator("#feed-sort")).toContainText("本周收藏");
    await expect(page.getByRole("button", { name: "清除筛选", exact: true })).toHaveCount(0);
    await expect(page.getByRole("link", { name: /看全部词汇/ })).toHaveAttribute(
      "href",
      "/vocabulary"
    );
    await page.goto("/channels/layout-fixture");
    await expect(page.getByRole("heading", { name: "SeeWord English" })).toBeVisible();
    await expect(page.getByLabel("本站播放 0 次").first()).toBeVisible();
    expect(
      await page.locator("main").evaluate((el) => el.scrollWidth - el.clientWidth)
    ).toBeLessThanOrEqual(1);
    if (width === 390 || width === 1440)
      await page.screenshot({
        path: resolve(directory, `channel-${width}.png`),
        animations: "disabled",
      });
    expect(errors).toEqual([]);
  });
}
