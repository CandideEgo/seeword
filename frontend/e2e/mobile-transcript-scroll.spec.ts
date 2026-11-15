/**
 * 移动端文稿的滚动模型 —— DEC-073 判据 4。
 *
 * 方案：`frontend/src/lib/watchLayout.ts`。
 *
 * 断言的契约（移动端 ≤1023px）：
 *   ① 文稿容器**不再有自己的滚动**：`[data-coach="subtitles"]` 的 `overflow-y` 不是
 *      auto/scroll，且 `scrollHeight == clientHeight`（去掉 `max-h-[560px] overflow-y-auto`）。
 *   ② 页面只有一层滚动 = 壳里的 `main#main-scroll`；滚它就能滚到文稿。
 *   ③ 滚过画框之后画框贴顶常驻，且**多了一条下边线**（DEC-073：文字从画框下穿过时
 *      要读成图层关系，而不是被切掉半行）。
 *   ④ 跟随：手动滚过一下 → 之后自动换句**不会**把页面抢回去；点一次「下一句」恢复跟随，
 *      当前句被钉回「画框下沿 + 8px」。
 *
 * 需要本地库里有**真能播**的视频：CI seed 写的是占位 URL（404），这时整条 skip
 * （与 mobile-inline-subtitle / mobile-current-sentence-card 同策）。
 *
 * 运行：npx playwright test e2e/mobile-transcript-scroll.spec.ts --project=chromium
 */

import { test, expect, type Page, type APIRequestContext } from "@playwright/test";
import { registerUserViaApi, loginViaToken, uniquePhone } from "./helpers";

const FRAME = '[data-testid="video-frame"]';
const CARD = '[data-testid="current-sentence-card"]';
const LIST = '[data-coach="subtitles"]';
const BAR = '[data-testid="mobile-tab-bar"]';
const SCROLLER = "main#main-scroll";

interface SubtitleRow {
  start_time: number;
  text_en: string;
  text_zh: string | null;
}

test.describe.configure({ mode: "serial" });
let token = "";

test.use({ viewport: { width: 414, height: 896 } });

test.beforeAll(async ({ request }) => {
  token = process.env.DESIGN_E2E_TOKEN || (await registerUserViaApi(request, uniquePhone())).token;
});

async function openFirstReadyVideo(request: APIRequestContext): Promise<string | null> {
  const res = await request.get("/api/v1/videos/public?page=1&page_size=1");
  if (!res.ok()) return null;
  const data = await res.json();
  return data?.items?.[0]?.id ?? null;
}

async function enterWatch(page: Page, request: APIRequestContext) {
  await page.addInitScript(() => window.localStorage.setItem("seeword_coach_done", "true"));
  await loginViaToken(page, token);

  const videoId = await openFirstReadyVideo(request);
  test.skip(!videoId, "no ready video in local DB; seed first");

  await page.goto(`/watch/${videoId}`);
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(2500);

  const playable = await page
    .waitForFunction(
      () => {
        const v = document.querySelector("video");
        return !!v && v.readyState >= 2;
      },
      null,
      { timeout: 8000 }
    )
    .then(() => true)
    .catch(() => false);
  test.skip(!playable, "no playable media in local DB (the CI seed writes a placeholder URL)");

  await expect(page.locator(CARD)).toHaveCount(1, { timeout: 15000 });
  return videoId as string;
}

async function getSubtitles(request: APIRequestContext, videoId: string): Promise<SubtitleRow[]> {
  const res = await request.get(`/api/v1/videos/${videoId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(res.ok(), `取字幕失败：${res.status()}`).toBe(true);
  return ((await res.json())?.subtitles ?? []) as SubtitleRow[];
}

test.describe("移动端文稿滚动模型（414×896）", () => {
  test("文稿容器没有自己的滚动条，页面只有 main 一层滚动", async ({ page, request }) => {
    await enterWatch(page, request);

    const m = await page.evaluate((listSel) => {
      const list = document.querySelector(listSel) as HTMLElement | null;
      const main = document.querySelector("main#main-scroll") as HTMLElement | null;
      if (!list || !main) return null;
      const cs = getComputedStyle(list);
      return {
        overflowY: cs.overflowY,
        listScrollable: list.scrollHeight - list.clientHeight,
        mainScrollable: main.scrollHeight - main.clientHeight,
        mainOverflowY: getComputedStyle(main).overflowY,
      };
    }, LIST);

    expect(m, "文稿容器与壳滚动容器都在").not.toBeNull();
    expect(m!.overflowY, "移动端文稿容器不该是内部滚动容器").not.toMatch(/auto|scroll/);
    expect(m!.listScrollable, "文稿容器内部没有可滚动的余量").toBeLessThanOrEqual(1);
    expect(m!.mainScrollable, "整页该滚的内容在 main 上").toBeGreaterThan(40);
    expect(m!.mainOverflowY, "壳滚动容器才是那个 overflow-y:auto").toMatch(/auto|scroll/);

    // 滚 main 就能真的滚到文稿（不是被内部容器吃掉）。
    const moved = await page.evaluate((sel) => {
      const main = document.querySelector(sel) as HTMLElement | null;
      if (!main) return null;
      const before = document
        .querySelector('[data-coach="subtitles"]')!
        .getBoundingClientRect().top;
      main.scrollTop = 600;
      const after = document.querySelector('[data-coach="subtitles"]')!.getBoundingClientRect().top;
      return { before, after, scrollTop: main.scrollTop };
    }, SCROLLER);
    expect(moved!.scrollTop, "main 真的滚了").toBeGreaterThan(100);
    expect(moved!.after, "文稿跟着页面滚（相对视口上移）").toBeLessThan(moved!.before - 100);
  });

  test("滚过画框后画框贴顶常驻，并带一条下边线", async ({ page, request }) => {
    await enterWatch(page, request);

    const mainTop = await page.evaluate(
      (sel) => document.querySelector(sel)!.getBoundingClientRect().top,
      SCROLLER
    );

    await page.evaluate((sel) => {
      (document.querySelector(sel) as HTMLElement).scrollTop = 420;
    }, SCROLLER);
    // 等两帧 + 让 sticky 生效
    await page.waitForTimeout(400);

    const m = await page.evaluate(
      ({ frameSel, barSel }) => {
        const frame = document.querySelector(frameSel) as HTMLElement | null;
        const bar = document.querySelector(barSel) as HTMLElement | null;
        if (!frame || !bar) return null;
        const fr = frame.getBoundingClientRect();
        const br = bar.getBoundingClientRect();
        return {
          frameTop: fr.top,
          frameBottom: fr.bottom,
          frameWidth: fr.width,
          borderBottom: getComputedStyle(frame).borderBottomWidth,
          barTop: br.top,
        };
      },
      { frameSel: FRAME, barSel: BAR }
    );

    expect(m).not.toBeNull();
    expect(Math.abs(m!.frameTop - mainTop), "画框钉在滚动容器上沿（顶栏下沿）").toBeLessThanOrEqual(
      1
    );
    expect(m!.frameBottom, "贴顶后画框仍然不压住底栏").toBeLessThanOrEqual(m!.barTop + 1);
    expect(m!.borderBottom, "贴顶时画框有下边线（DEC-073）").toBe("1px");
    expect(m!.frameWidth, "贴顶不缩宽（不缩成小窗）").toBeGreaterThan(300);
  });

  test("手动滚一下 → 自动换句不抢回页面；点「下一句」恢复跟随并钉回画框下沿", async ({
    page,
    request,
  }) => {
    const videoId = await enterWatch(page, request);
    const subs = await getSubtitles(request, videoId);
    test.skip(subs.length < 3, "本地这条视频字幕太少，测不了换句跟随");

    // 先把页面滚下去、模拟一次手动滚动（wheel 会让跟随暂停）。
    await page.evaluate((sel) => {
      const main = document.querySelector(sel) as HTMLElement;
      main.scrollTop = 500;
      main.dispatchEvent(new WheelEvent("wheel", { deltaY: 120, bubbles: true }));
    }, SCROLLER);
    await page.waitForTimeout(400);
    const parked = await page.evaluate(
      (sel) => (document.querySelector(sel) as HTMLElement).scrollTop,
      SCROLLER
    );

    // 直接 seek 到更靠后的句子：这是 timeupdate 驱动的自动换句，**不是**显式导航，
    // 所以跟随必须保持暂停、页面不许被抢回去。
    const target = subs[Math.min(subs.length - 1, 2)];
    await page
      .locator("video")
      .first()
      .evaluate((v, t) => {
        const el = v as HTMLVideoElement;
        el.currentTime = t + 0.05;
      }, target.start_time);
    await page.waitForTimeout(1200);
    const afterAuto = await page.evaluate(
      (sel) => (document.querySelector(sel) as HTMLElement).scrollTop,
      SCROLLER
    );
    expect(
      Math.abs(afterAuto - parked),
      `自动换句后页面不该被抢走（${parked.toFixed(0)} → ${afterAuto.toFixed(0)}）`
    ).toBeLessThanOrEqual(24);

    // 显式「下一句」= 恢复跟随：当前句被钉回「画框下沿 + 8px」附近。
    await page.locator('[data-testid="watch-next"]').click();
    await expect
      .poll(
        async () =>
          page.evaluate(
            ({ frameSel, cardSel }) => {
              const frame = document.querySelector(frameSel)!.getBoundingClientRect();
              const counter = document
                .querySelector(cardSel)!
                .querySelector('[data-testid="subtitle-counter"]')!
                .textContent!.trim();
              const idx = Number(/^(\d+)/.exec(counter)?.[1] ?? "0") - 1;
              const row = document.getElementById(`subtitle-${idx}`);
              if (!row) return Number.POSITIVE_INFINITY;
              // 目标：当前句条目顶边 = 画框下沿 + 8px（跟随的落点）。
              return Math.abs(row.getBoundingClientRect().top - (frame.bottom + 8));
            },
            { frameSel: FRAME, cardSel: CARD }
          ),
        { timeout: 8000 }
      )
      .toBeLessThanOrEqual(60);
  });
});
