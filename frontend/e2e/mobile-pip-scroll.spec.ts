/**
 * 移动端播放页的滚动形态 —— wayfinder #30 决议（**画面贴顶常驻**）+ DEC-069 / #31
 * （钉住位置 64 → 44）的毕业物验收。
 *
 * 定稿的形态：滚过画框之后，画面**不缩、不飞、不消失** —— 它贴住 `main#main-scroll`
 * 上沿（= 壳顶栏下沿）常驻（`sticky`，活动范围是左列那层 grid item），`<video>` 节点
 * 不换父，所以内联 ↔ 常驻切换不丢播放进度。被否的三条与它们的读数代价在
 * `frontend/src/hooks/useStickyPip.ts`：
 *   · A2「只留一条」—— 当前句与点词热区整体出画（#27 的锚点在滚动后失效）
 *   · B「画面缩成条」—— 长句被画框切掉（216 字符句：条内只看得见 62/107px）
 *   · C「右下角 160×90」—— 当前句份数归零（INV-021 的锚点消失）+ iOS 地址栏 40px
 *
 * DEC-069 改的两处：
 *   · 钉住位置从 64（全局顶栏）变成 **44**（观看页顶栏）—— 断言按 44 写，不再写死 64；
 *   · 画面里的入画字幕与「退出小窗播放」的 X 全删 —— 贴顶态由**滚回顶部**自然解除，
 *     所以「退出口 44×44」那条用例换成「常驻是可逆的」。
 *
 * 断言的数字全部来自 `getBoundingClientRect()`；词热区用 `elementFromPoint` 逐像素探。
 *
 * 需要本地库里有**真能播**的视频（CI seed 的 `/media/<id>.mp4` 是占位 URL 404）→ skip。
 *
 * 运行：npx playwright test e2e/mobile-pip-scroll.spec.ts --project=chromium
 */

import { test, expect, type Page, type APIRequestContext } from "@playwright/test";
import { registerUserViaApi, loginViaToken, uniquePhone } from "./helpers";

// 串行 + 一次注册：/auth/sms/register 是 3/minute（按 IP），每个用例各注册一个用户会 429。
test.describe.configure({ mode: "serial" });
let token = "";
test.beforeAll(async ({ request }) => {
  token = process.env.DESIGN_E2E_TOKEN || (await registerUserViaApi(request, uniquePhone())).token;
});

const FRAME = '[data-testid="video-frame"]';
const CARD = '[data-testid="current-sentence-card"]';

async function boxOf(page: Page, selector: string) {
  const box = await page.locator(selector).first().boundingBox();
  if (!box) throw new Error(`no bounding box for ${selector}`);
  return box;
}

/** 滚到某一处（滚动容器是壳里的 `main#main-scroll`，`window.scrollY` 恒 0）。 */
async function scrollTo(page: Page, top: number) {
  await page.evaluate((y) => {
    const main = document.querySelector("main#main-scroll");
    if (main) main.scrollTop = y;
  }, top);
  await page.waitForTimeout(500);
}

/**
 * 登录 → 打开第一条 ready 视频 → 跳过教程浮层 → 等到真能播。
 * **不**退出常驻态：本票量的就是常驻态本身。`mobile=false` 时不等壳底栏（桌面渲染 null）。
 */
async function enterWatch(page: Page, request: APIRequestContext, { mobile = true } = {}) {
  await page.addInitScript(() => window.localStorage.setItem("seeword_coach_done", "true"));
  await loginViaToken(page, token);

  const res = await request.get("/api/v1/videos/public?page=1&page_size=1");
  const videoId = (await res.json())?.items?.[0]?.id ?? null;
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

  await expect(page.locator(CARD)).toBeVisible({ timeout: 5000 });
  if (mobile) {
    await expect(page.locator('[data-testid="watch-bottom-bar"]')).toBeVisible({ timeout: 5000 });
  }
}

/**
 * 贴顶常驻的对象 = **画框自己**：移动端左列是 `display: contents`，画框直接成为 grid item，
 * 包含块是整个网格容器（余量 > 滚动上限），所以滚动全程都钉得住。
 * 别再量左列：它没有盒子（rect 恒 0×0、`position` 恒 static），量它只会量到空气。
 */
async function frameState(page: Page) {
  return page.evaluate((sel) => {
    const f = document.querySelector(sel) as HTMLElement | null;
    if (!f) return null;
    const r = f.getBoundingClientRect();
    return { y: r.y, height: r.height, position: getComputedStyle(f).position };
  }, FRAME);
}

/** 壳顶（`main#main-scroll` 上沿）与观看页顶栏下沿 —— DEC-069 之后这两个数必须相等。 */
async function shellEdges(page: Page) {
  return page.evaluate(() => {
    const main = document.querySelector("main#main-scroll");
    const topBar = document.querySelector(".user-topbar");
    return {
      shellTop: main ? main.getBoundingClientRect().top : null,
      topBarBottom: topBar ? topBar.getBoundingClientRect().bottom : null,
    };
  });
}

/**
 * 量一个词 span 的**可点带**：从它的垂直中心往上/下探，直到 `elementsFromPoint` 不再命中它。
 *
 * 量的是 span 自己的**行内盒**（17px 字号 ≈ 20px），不是方案里那个 32px 的行高 ——
 * 行高管的是「行与行不重叠」，命中区仍然是词自己。
 */
async function wordHitBand(page: Page, selector: string) {
  return page.evaluate((sel) => {
    const w = document.querySelector(sel) as HTMLElement | null;
    if (!w) return null;
    const r = w.getBoundingClientRect();
    const cx = Math.round(r.left + r.width / 2);
    const mid = r.top + r.height / 2;
    const at = (y: number) => document.elementsFromPoint(cx, y).indexOf(w) >= 0;
    if (!at(mid)) return { h: 0, tappable: false };
    let lo = mid,
      hi = mid;
    for (let i = 0; i < 40 && lo > r.top - 26; i++) {
      if (!at(lo - 1)) break;
      lo--;
    }
    for (let i = 0; i < 40 && hi < r.bottom + 26; i++) {
      if (!at(hi + 1)) break;
      hi++;
    }
    return { h: Math.round(hi - lo), tappable: true };
  }, selector);
}

test.use({ viewport: { width: 375, height: 812 } });

test.describe("移动端滚动形态：画面贴顶常驻（#30 + #31，375×812）", () => {
  test("首屏不受影响：画框顶 = 壳顶 = 顶栏下沿、不常驻；当前句卡在画面正下方且词可点", async ({
    page,
    request,
  }) => {
    await enterWatch(page, request);

    const frame = await boxOf(page, FRAME);
    const edges = await shellEdges(page);
    const st = await frameState(page);

    expect(edges.topBarBottom, "观看页顶栏下沿 = 44px").toBeCloseTo(56, 0);
    expect(edges.shellTop, "壳顶 = 顶栏下沿").toBeCloseTo(edges.topBarBottom!, 0);
    expect(frame.y, "首屏页头位于画框之前").toBeGreaterThan(edges.shellTop!);
    expect(st?.position, "首屏不贴顶常驻").not.toBe("sticky");

    // 画面内零文字；当前句在画面正下方的卡里（唯一锚点）。
    expect((await page.locator(FRAME).innerText()).trim(), "画框内零文字").toBe("");
    const card = await boxOf(page, CARD);
    expect(card.y, "当前句卡在画框下沿之下").toBeGreaterThanOrEqual(frame.y + frame.height - 1);

    // 词热区仍在，且不是一条 1px 细缝（锚点从「入画字幕」搬到当前句卡）。
    const hit = await wordHitBand(page, `${CARD} .now-sub-word`);
    expect(hit?.tappable, "首屏画面下方的词仍可点").toBe(true);
    expect(hit!.h, "词热区是词自己的行内盒（17px 字号 ≈ 20px）").toBeGreaterThanOrEqual(18);
    console.log(`[#27] 375×812 当前句卡词热区实测 ${hit!.h}px`);
  });

  test("滚过画框 → 画面贴顶常驻：画框顶 = 壳顶 = 顶栏下沿(44)、尺寸一像素没缩、画面里仍零文字", async ({
    page,
    request,
  }) => {
    await enterWatch(page, request);
    const before = await boxOf(page, FRAME);

    await scrollTo(page, 400);

    const st = await frameState(page);
    const frame = await boxOf(page, FRAME);
    const edges = await shellEdges(page);

    // ① 真的粘住了：滚过画框下沿之后画框顶仍在壳顶。
    // 注意滚动上限不是 1200（`scrollTop=1200` 会被夹住）——上限那条另有 ①′ 单独断言。
    expect(st?.position, "滚过之后画框是 sticky").toBe("sticky");
    expect(edges.topBarBottom, "顶栏下沿 = 44px（DEC-069 把钉住位置从 64 改到 44）").toBeCloseTo(
      56,
      0
    );
    expect(
      frame.y,
      "常驻时画框顶 = 顶栏下沿（`top-0` 贴的是 main 上沿，而 main 上沿 = 顶栏下沿）"
    ).toBeCloseTo(edges.shellTop!, 0);

    // ② 尺寸一像素没缩（这就是「不缩成小窗」的硬证据）
    expect(frame.width, "常驻时画框仍满宽").toBeCloseTo(before.width, 0);
    expect(frame.height, "常驻时画框高不变").toBeCloseTo(before.height, 0);
    expect(frame.height, "画框保持 16:9（手机按页面内边距收窄）").toBeCloseTo(
      (frame.width * 9) / 16,
      0
    );

    // ③ 画面里零文字（入画字幕已删，常驻时也不会冒出来）；当前句仍只有卡里那一份。
    expect((await page.locator(FRAME).innerText()).trim(), "常驻态画框内零文字").toBe("");
    expect(await page.locator(`${CARD} .now-sub-word`).count(), "当前句仍只有一份").toBeGreaterThan(
      0
    );

    // ①′ 一路滚到**滚动上限**仍然钉得住 —— 这是旧实现翻车的地方，单独留一条回归：
    // sticky 的活动范围是它的包含块。旧实现把它挂在 490px 高的左列上（包含块余量 635px
    // < 滚动上限 707px），于是最后 ~72px 里画面被包含块底边推着走（实测滚到上限时
    // 画框顶 y=-28，而壳顶是 64）。现在挂在画框自己身上、包含块是整个网格容器。
    await scrollTo(page, 9999);
    const atMax = await page.evaluate(() =>
      Math.round(document.querySelector("main#main-scroll")!.scrollTop)
    );
    expect(atMax, "确实滚到了上限（上限不是 1200，别被 scrollTo(1200) 骗了）").toBeGreaterThan(400);
    expect((await boxOf(page, FRAME)).y, "滚到上限画框顶仍 = 壳顶").toBeCloseTo(edges.shellTop!, 0);
  });

  test("常驻不丢播放进度：切进常驻前后 currentTime 连续", async ({ page, request }) => {
    await enterWatch(page, request);

    await page
      .locator("video")
      .first()
      .evaluate((v) => (v as HTMLVideoElement).play());
    await page.waitForTimeout(1500);
    const before = await page
      .locator("video")
      .first()
      .evaluate((v) => (v as HTMLVideoElement).currentTime);

    await scrollTo(page, 1200);
    await page.waitForTimeout(1200);
    const after = await page
      .locator("video")
      .first()
      .evaluate((v) => (v as HTMLVideoElement).currentTime);

    // 元素没被换父重建 → 播放继续、时间只前进
    expect(after, "常驻后播放没有归零").toBeGreaterThanOrEqual(before);
    expect(
      await page
        .locator("video")
        .first()
        .evaluate((v) => (v as HTMLVideoElement).paused),
      "常驻后仍在播"
    ).toBe(false);
  });

  /**
   * DEC-069 删掉了画面里的「关闭小窗播放」X（`aria-label="关闭小窗播放"`）：常驻态不再有
   * 退出口，**滚回顶部自然解除**。这条替代原来的「退出出口 44×44」用例 ——
   * 贴顶常驻仍是「跟 / 不跟」的可逆状态，只是切换方式换成了滚动位置。
   */
  test("贴顶常驻可逆：滚回顶部自动解除，再滚下去重新武装（X 已删）", async ({ page, request }) => {
    await enterWatch(page, request);

    await scrollTo(page, 1200);
    expect((await frameState(page))?.position, "滚下去 → 常驻").toBe("sticky");

    await scrollTo(page, 0);
    expect((await frameState(page))?.position, "滚回顶部 → 解除常驻").not.toBe("sticky");

    await scrollTo(page, 1200);
    expect((await frameState(page))?.position, "再滚下去 → 重新武装").toBe("sticky");
  });

  test("不压底栏、不引入横向溢出；四态里没有第二个贴底 fixed（INV-019）", async ({
    page,
    request,
  }) => {
    await enterWatch(page, request);
    await scrollTo(page, 1200);

    // INV-019 的另一半：观看页的最后一行是 `WatchBottomBar`（不是 5 Tab），同样非 fixed。
    const bar = await boxOf(page, '[data-testid="mobile-tab-bar"]');
    const frame = await boxOf(page, FRAME);
    expect(frame.y + frame.height, "常驻的画框不越到壳底栏上沿以下").toBeLessThanOrEqual(bar.y + 1);

    const probe = await page.evaluate(() => {
      const fixedBottom: string[] = [];
      document.querySelectorAll("body *").forEach((el) => {
        const c = getComputedStyle(el);
        if (
          el.getClientRects().length &&
          c.visibility !== "hidden" &&
          c.position === "fixed" &&
          /px$/.test(c.bottom) &&
          parseFloat(c.bottom) < 200
        ) {
          fixedBottom.push(el.tagName + "." + String(el.className).slice(0, 40));
        }
      });
      const barEl = document.querySelector('[data-testid="mobile-tab-bar"]') as HTMLElement | null;
      return {
        fixedBottom,
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        burnCount: document.querySelectorAll('[data-testid="burn-subtitle"]').length,
        burnWords: document.querySelectorAll(".burn-sub-word").length,
        cardWords: document.querySelectorAll('[data-testid="current-sentence-card"] .now-sub-word')
          .length,
        barPosition: barEl ? getComputedStyle(barEl).position : null,
      };
    });
    expect(probe.fixedBottom, "底栏之外不许再有贴底 fixed 常驻件（INV-019）").toEqual([]);
    expect(probe.barPosition, "观看页底栏是常规流收尾行，不是 fixed").not.toBe("fixed");
    expect(probe.scrollWidth, "无横向溢出").toBeLessThanOrEqual(probe.clientWidth + 2);
    expect(probe.burnCount, "画面内不再有入画字幕（INV-021 换了锚点）").toBe(0);
    expect(probe.burnWords, "画面内不再有点词热区").toBe(0);
    expect(probe.cardWords, "当前句卡里的点词热区还在").toBeGreaterThan(0);
  });
});

test.describe("390 / 414 两档复算（#30 的常驻形态在别的主流宽度也成立）", () => {
  test("390×812", async ({ page, request }) => {
    test.skip(!token, "no session");
    await page.setViewportSize({ width: 390, height: 812 });
    await enterWatch(page, request);
    const before = await boxOf(page, FRAME);
    await scrollTo(page, 1200);
    const frame = await boxOf(page, FRAME);
    const st = await frameState(page);
    const edges = await shellEdges(page);
    expect(st?.position, "滚过之后是 sticky").toBe("sticky");
    expect(frame.y, "画框顶仍贴壳顶").toBeCloseTo(edges.shellTop!, 0);
    expect(frame.height, "画框高不变").toBeCloseTo(before.height, 0);
    expect(frame.width, "画框仍满宽").toBeCloseTo(358, 0);
    expect((await page.locator(FRAME).innerText()).trim(), "画框内零文字").toBe("");
  });

  test("414×812", async ({ page, request }) => {
    test.skip(!token, "no session");
    await page.setViewportSize({ width: 414, height: 812 });
    await enterWatch(page, request);
    const before = await boxOf(page, FRAME);
    await scrollTo(page, 1200);
    const frame = await boxOf(page, FRAME);
    const st = await frameState(page);
    const edges = await shellEdges(page);
    expect(st?.position, "滚过之后是 sticky").toBe("sticky");
    expect(frame.y, "画框顶仍贴壳顶").toBeCloseTo(edges.shellTop!, 0);
    expect(frame.height, "画框高不变").toBeCloseTo(before.height, 0);
    expect(frame.width, "画框仍满宽").toBeCloseTo(382, 0);
    expect((await page.locator(FRAME).innerText()).trim(), "画框内零文字").toBe("");
  });
});

test.describe("桌面端不受影响（#30/#31 只动 ≤1023px）", () => {
  test.use({ viewport: { width: 1280, height: 900 } });

  test("1280：滚过画框之后不出现贴顶常驻，也没有壳观看页两栏", async ({ page, request }) => {
    await enterWatch(page, request, { mobile: false });
    await scrollTo(page, 1200);
    const st = await frameState(page);
    expect(st?.position, "桌面端不走移动端的常驻分支").not.toBe("sticky");
    await expect(page.locator('[data-testid="watch-top-bar"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="watch-bottom-bar"]')).toHaveCount(0);
    const frame = await boxOf(page, FRAME);
    expect(frame.x, "桌面画框有左内边距（不出血）").toBeGreaterThan(8);
  });
});
