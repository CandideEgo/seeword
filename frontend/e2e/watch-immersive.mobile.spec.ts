import { test, expect, type Page, type TestInfo } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";
import { mediaState, openWatch, setupWatch, VIDEO_ID } from "./watch-baseline.fixture";

async function evidence(page: Page, info: TestInfo, name: string) {
  const directory = resolve("../tmp/e2e-evidence/discover-watch", info.project.name);
  mkdirSync(directory, { recursive: true });
  await page.screenshot({ path: resolve(directory, `${name}.png`), animations: "disabled" });
}

async function noOverflow(page: Page) {
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)
  ).toBeLessThanOrEqual(1);
  expect(
    await page.locator("main").evaluate((el) => el.scrollWidth - el.clientWidth)
  ).toBeLessThanOrEqual(1);
}

for (const width of [360, 390, 430, 600, 820, 1024, 1366, 1440, 1920]) {
  test(`沉浸 ${width}：等比画面、字幕与操作可达，退出恢复`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: width <= 1024 ? 844 : 900 });
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await setupWatch(page, { longSentence: true });
    await openWatch(page, "?sub=first");
    if (width === 390 || width === 1440) await evidence(page, info, `watch-${width}`);
    const media = await page.locator("video").elementHandle();
    const before = await mediaState(page);
    const stored = await page.evaluate(() => localStorage.getItem("seeword_watch_layout"));
    await page.getByRole("button", { name: /沉浸观看/ }).click();
    await expect(page.getByTestId("watch-workspace")).toHaveAttribute("data-layout", "immersive");
    await expect(page.locator(".user-topbar")).toBeHidden();
    await expect(page.locator(".user-sidebar")).toBeHidden();
    await expect(page.getByTestId("mobile-tab-bar")).toBeHidden();
    await expect(page.getByTestId("watch-transcript")).toBeHidden();
    await expect(page.locator(".watch-heading")).toBeHidden();
    await expect(page.getByRole("button", { name: /退出沉浸/ })).toBeInViewport();
    const frame = (await page.getByTestId("video-frame").boundingBox())!;
    expect(frame.width / frame.height).toBeCloseTo(16 / 9, 1);
    if (width <= 1024) {
      const caption = (await page.getByTestId("current-sentence-card").boundingBox())!;
      expect(caption.y - frame.y - frame.height).toBeGreaterThanOrEqual(-1);
      expect(caption.y - frame.y - frame.height).toBeLessThanOrEqual(20);
    }
    expect((await mediaState(page)).time).toBeCloseTo(before.time, 0);
    expect((await mediaState(page)).paused).toBe(before.paused);
    expect(await media!.evaluate((el) => el.isConnected)).toBe(true);
    await noOverflow(page);
    if (width === 390 || width === 1440) await evidence(page, info, `immersive-${width}`);
    await page.getByTestId("current-sentence-expand").click();
    await expect(page.getByRole("button", { name: /退出沉浸/ })).toBeInViewport();
    await page
      .getByTestId("current-sentence-card")
      .getByRole("button", { name: "查看 walk 的词义", exact: true })
      .click();
    const word = page.getByTestId("word-tooltip");
    await expect(word).toBeVisible();
    const box = (await word.boundingBox())!;
    const tools = (await page.locator('[data-immersive-tools="true"]').boundingBox())!;
    expect(box.y + box.height).toBeLessThanOrEqual(tools.y + 1);
    await page.keyboard.press("Escape");
    await expect(word).toHaveCount(0);
    await expect(page.getByTestId("watch-workspace")).toHaveAttribute("data-layout", "immersive");
    await page.getByRole("button", { name: /退出沉浸/ }).click();
    await expect(page.locator(".user-topbar")).toBeVisible();
    await expect(page.getByTestId("watch-transcript")).toBeVisible();
    expect(await page.evaluate(() => localStorage.getItem("seeword_watch_layout"))).toBe(stored);
    expect(errors).toEqual([]);
  });
}

test("A/R/D 与按钮共用逐句语义，输入、组合键与弹层不误触", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await setupWatch(page);
  await openWatch(page, "?sub=second");
  const counter = page.getByTestId("subtitle-counter");
  await page.keyboard.press("a");
  await expect(counter).toHaveText("1 / 3");
  await page.keyboard.press("d");
  await expect(counter).toHaveText("2 / 3");
  await page.keyboard.press("r");
  await expect.poll(async () => (await mediaState(page)).time).toBeGreaterThan(5.3);
  await expect.poll(async () => (await mediaState(page)).paused, { timeout: 6000 }).toBe(true);
  expect((await mediaState(page)).time).toBeLessThanOrEqual(8.3);
  await page.getByRole("button", { name: "下一句", exact: true }).click();
  await expect(counter).toHaveText("3 / 3");
  await page.keyboard.press("Control+a");
  await expect(counter).toHaveText("3 / 3");
  await page.getByRole("button", { name: "笔记", exact: true }).click();
  const note = page.getByPlaceholder("记录重点句型、生词或心得...");
  await note.fill("ards");
  await note.press("t");
  await expect(page.getByTestId("watch-workspace")).not.toHaveAttribute("data-layout", "immersive");
  await page.locator("main").focus();
  await page
    .locator("main")
    .evaluate((el) =>
      el.dispatchEvent(new KeyboardEvent("keydown", { key: "t", bubbles: true, isComposing: true }))
    );
  await expect(page.getByTestId("watch-workspace")).not.toHaveAttribute("data-layout", "immersive");
  await page.keyboard.press("t");
  await expect(page.getByTestId("watch-workspace")).toHaveAttribute("data-layout", "immersive");
  await page.keyboard.press("s");
  await expect(page.getByTestId("current-sentence-zh")).toHaveCount(0);
  await page.keyboard.press("Escape");
  await expect(page.locator(".user-topbar")).toBeVisible();
});

test("播放中切换沉浸、导航离开和重访不重置媒体或残留沉浸", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await setupWatch(page);
  await openWatch(page);
  await page.getByRole("button", { name: "播放（空格）", exact: true }).click();
  await expect.poll(async () => (await mediaState(page)).time).toBeGreaterThan(0.5);
  const media = await page.locator("video").elementHandle();
  for (let i = 0; i < 2; i++) {
    const before = (await mediaState(page)).time;
    await page.keyboard.press("t");
    await expect.poll(async () => (await mediaState(page)).time).toBeGreaterThan(before);
    expect((await mediaState(page)).paused).toBe(false);
    expect(await media!.evaluate((el) => el.isConnected)).toBe(true);
  }
  await page.keyboard.press("t");
  await page.goto("/");
  await expect(page.locator(".user-topbar")).toBeVisible();
  await page.goto(`/watch/${VIDEO_ID}`);
  await expect(page.getByTestId("watch-workspace")).not.toHaveAttribute("data-layout", "immersive");
});

test("YouTube 回退与横屏沉浸可退出", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await setupWatch(page, { youtube: true });
  await page.goto(`/watch/${VIDEO_ID}`);
  await expect(page.getByText("第三方播放器协议测试")).toBeVisible();
  await page.getByRole("button", { name: /沉浸观看/ }).click();
  await expect(page.getByTestId("watch-transcript")).toBeHidden();
  await page.setViewportSize({ width: 844, height: 390 });
  await expect(page.getByRole("button", { name: /退出沉浸/ })).toBeInViewport();
  await noOverflow(page);
  await page.getByRole("button", { name: /退出沉浸/ }).click();
  await expect(page.locator(".user-topbar")).toBeVisible();
});

test("竖屏与超宽媒体按元数据等比布局，浏览器全屏优先处理退出", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await setupWatch(page);
  await openWatch(page);
  await page.keyboard.press("t");
  for (const [width, height] of [
    [1080, 1920],
    [2560, 1080],
  ]) {
    await page.locator("video").evaluate(
      (video, size) => {
        Object.defineProperties(video, {
          videoWidth: { configurable: true, value: size[0] },
          videoHeight: { configurable: true, value: size[1] },
        });
        video.dispatchEvent(new Event("loadedmetadata"));
      },
      [width, height]
    );
    await expect
      .poll(async () => {
        const box = (await page.getByTestId("video-frame").boundingBox())!;
        return box.width / box.height;
      })
      .toBeCloseTo(width / height, 2);
    await expect(page.getByRole("button", { name: "退出沉浸", exact: true })).toBeInViewport();
  }
  if (await page.evaluate(() => document.fullscreenEnabled)) {
    await page.getByRole("button", { name: "全屏（F）", exact: true }).click();
    await expect.poll(() => page.evaluate(() => !!document.fullscreenElement)).toBe(true);
    await page.locator("video").dispatchEvent("keydown", { key: "Escape", bubbles: true });
    await expect(page.getByTestId("watch-workspace")).toHaveAttribute("data-layout", "immersive");
    await page.evaluate(() => document.exitFullscreen());
  } else {
    // iOS exposes native video fullscreen, not document fullscreen. Headless
    // WebKit cannot show that system UI; verify the existing fallback call.
    await page.locator("video").evaluate((video) => {
      Object.defineProperty(video, "webkitEnterFullscreen", {
        configurable: true,
        value: () => {
          video.dataset.nativeFullscreenRequested = "true";
        },
      });
    });
    await page.getByRole("button", { name: "全屏（F）", exact: true }).click();
    await expect(page.locator("video")).toHaveAttribute("data-native-fullscreen-requested", "true");
    await expect(page.getByTestId("watch-workspace")).toHaveAttribute("data-layout", "immersive");
  }
  await page.keyboard.press("Escape");
  await expect(page.locator(".user-topbar")).toBeVisible();
});
