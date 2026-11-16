/**
 * D1 + D10 移动端验收（iPhone X 375×812）—— DEC-069 / #31 换壳之后的版本。
 *
 * 方案：`frontend/src/lib/watchLayout.ts`
 * （§2 第 1/5 条、§4 目标形态、§7 三条判据）。
 *
 * 老文件写的是被删掉的那套移动端 UI（点出式控制条 + 3s 自收 + 入画字幕 + 画面内
 * 标题/返回键/退出 X）。DEC-069 之后移动端的观看控制由**壳的两个栏**承载，
 * 画面里的 `VideoControls` 在 ≤1023px **根本不渲染**（只有 ≥1024px 才渲染），
 * 所以「点画面浮起控制条」这一态在移动端已不存在。本文件按新形态重写，
 * 每条用例保护的东西写在它自己的注释里。
 *
 * 覆盖：
 *   ① 壳两栏 + 当前句卡在位；无横向溢出；进入观看页即可播（底栏播放键）
 *   ② D1：控制条**不再自收**（常驻、可点）—— 老文件量的就是这条，只是形态反了
 *   ③ 底栏进度条是常驻可拖的（老文件里移动端只剩一条 3px 纯展示线，不可拖）
 *   ④ D10：跟读入口在底栏、抽屉仍「不压画面、不越底栏上沿」
 *   ⑤ 登录页无横向溢出（与本轮改动无关，原样保留）
 *
 * 视口由本文件自己 `test.use` 钉住（chromium 项目默认 1280 宽，断言里全是 375 的几何）。
 * 需要本地库里有**真的能播**的视频：CI 的 seed 写的是占位 URL（404），那种情况 skip。
 *
 * 运行：npx playwright test e2e/mobile-d1-d10.spec.ts --project=chromium
 */

import { test, expect, type Page, type APIRequestContext } from "@playwright/test";
import { registerUserViaApi, loginViaToken, uniquePhone } from "./helpers";

const SCREENSHOT_DIR = "test-results/mobile-d1-d10";

const TOP_BAR = ".user-topbar";
const BOTTOM_BAR = '[data-testid="mobile-tab-bar"]';
const FRAME = '[data-testid="video-frame"]';
const CARD = '[data-testid="current-sentence-card"]';

const PHONE = uniquePhone();
let token = "";

// 一次注册：/auth/sms/register 是 3/minute（按 IP），老文件每条用例各注册一个用户，
// 第 4 条就会 429。串行 + beforeAll 与其余移动端 spec 同策。
test.describe.configure({ mode: "serial" });

test.beforeAll(async ({ request }) => {
  token = process.env.DESIGN_E2E_TOKEN || (await registerUserViaApi(request, PHONE)).token;
});

async function openFirstReadyVideo(request: APIRequestContext): Promise<string | null> {
  const res = await request.get("/api/v1/videos/public?page=1&page_size=1");
  if (!res.ok()) return null;
  const data = await res.json();
  return data?.items?.[0]?.id ?? null;
}

async function assertNoHorizontalOverflow(page: Page, label: string): Promise<void> {
  const { scrollWidth, clientWidth } = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  if (scrollWidth > clientWidth + 2) {
    await page.screenshot({
      path: `${SCREENSHOT_DIR}/overflow-${label}.png`,
      fullPage: true,
    });
    throw new Error(
      `[${label}] horizontal overflow: scrollWidth=${scrollWidth} > clientWidth=${clientWidth}`
    );
  }
}

/**
 * 登录 → 打开第一条 ready 视频 → 等到真能播 → 断言新壳在位。返回画框几何。
 *
 * 教程浮层用 app 自己的「看过了」标记关掉（与其余移动端 spec 同法），不再走
 * 「点跳过教程 / 连点下一步」那条路。
 */
async function enterWatch(page: Page, request: APIRequestContext) {
  await page.addInitScript(() => window.localStorage.setItem("seeword_coach_done", "true"));
  await loginViaToken(page, token);

  const videoId = await openFirstReadyVideo(request);
  test.skip(!videoId, "no ready video in local DB; seed first");

  await page.goto(`/watch/${videoId}`);
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1500);

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

  // 新形态：壳的两栏 + 画面正下方的当前句卡（画面里零覆盖物）。
  await expect(page.locator(TOP_BAR)).toBeVisible({ timeout: 5000 });
  await expect(page.locator(BOTTOM_BAR)).toBeVisible({ timeout: 5000 });
  await expect(page.locator(CARD)).toBeVisible({ timeout: 5000 });

  const frame = await page.locator(FRAME).boundingBox();
  if (!frame) throw new Error(`no bounding box for ${FRAME}`);
  return frame;
}

/**
 * 底栏播放键：点一次 → 等它变成「暂停」（`isPlaying` 的 UI 事实源）。
 * 老文件点的是画面中央的播放按钮 + Space 兜底，那两个在移动端都没有了。
 */
async function startPlayback(page: Page): Promise<void> {
  const toggle = page.locator('[data-testid="watch-toggle-play"]');
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-label", "暂停", { timeout: 8000 });
}

/** 底栏进度条已播比例（`watch-progress-fill` 的 inline width，rAF 直写）。 */
async function playedWidth(page: Page): Promise<number> {
  const style =
    (await page.locator('[data-testid="watch-progress-fill"]').getAttribute("style")) ?? "";
  const m = /width:\s*([\d.]+)%/.exec(style);
  return m ? Number(m[1]) : 0;
}

// 这组断言写的是 iPhone X 的几何（375 + 2），所以视口必须由文件自己钉住：
// 桌面项目（chromium）默认 1280 宽，之前靠空库 skip 掩盖了这处不匹配。
test.use({ viewport: { width: 375, height: 812 } });

test.describe("Mobile D1 + D10 Acceptance (iPhone X 375x812)", () => {
  test("watch page: 新壳两栏在位、无溢出、进页面即可播（底栏播放键）", async ({
    page,
    request,
  }) => {
    await enterWatch(page, request);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/01-mobile-shell.png` });
    await assertNoHorizontalOverflow(page, "loaded");

    // ① 顶栏 44px（§2 第 3 条）：老文件没量过，新形态下这条是「首屏还给画面」的根。
    const topBar = await page.locator(TOP_BAR).boundingBox();
    expect(topBar, "顶栏有盒子").not.toBeNull();
    expect(Math.round(topBar!.height), "全站手机顶栏高 56px").toBe(56);

    // ② 底栏在位、在视口内 —— 老断言量的是 `mobile-actions` 行的 x/宽/高，
    //    那行已经进 ⋯ 面板（§2 第 6 条），换成量壳底栏。
    const bottomBar = await page.locator(BOTTOM_BAR).boundingBox();
    expect(bottomBar, "底栏有盒子").not.toBeNull();
    expect(bottomBar!.x).toBeGreaterThanOrEqual(0);
    expect(bottomBar!.x + bottomBar!.width).toBeLessThanOrEqual(375 + 2);
    expect(bottomBar!.y + bottomBar!.height).toBeLessThanOrEqual(812 + 2);
    expect(bottomBar!.height, "底栏有实际高度（2px 进度 + 56px 按键行）").toBeGreaterThanOrEqual(
      44
    );

    // ③ 老断言里的「逐句跟读按钮」现在由底栏的「跟读」承担；D10 完整流程在最后一条用例。
    const shadowing = page.locator('[data-testid="watch-replay"]');
    await expect(shadowing).toBeVisible({ timeout: 10000 });
    const box = await shadowing.boundingBox();
    expect(box, "跟读键 bounding box").not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x + box!.width).toBeLessThanOrEqual(375 + 2);
    expect(box!.height, "跟读键 ≥44 触控基线").toBeGreaterThanOrEqual(44);

    // ④ D1：进入观看页即可播 = 一次点击（§7 判据 3）。
    const pausedBefore = await page
      .locator("video")
      .first()
      .evaluate((v) => (v as HTMLVideoElement).paused);
    expect(pausedBefore, "进入页面时还没播（等这一次点击）").toBe(true);
    await startPlayback(page);

    // ⑤ 底栏进度是活的：播到 rAF 写出正比例。
    await expect.poll(() => playedWidth(page), { timeout: 10000 }).toBeGreaterThan(0);
  });

  /**
   * D1 —— 控制条**不再自收**。
   *
   * 老文件保护的是「播放中闲置 4s 后控制条收起」（当时移动端是「点出式 + 3s 自收」）。
   * DEC-069 把这条**反过来**（§2 第 5 条：控制条常驻，删「点画面浮起 + 3s 自收」），
   * 所以换成正面断言：闲置后底栏仍在视口内、仍在原位，且**依然能点**（暂停 → 播放）。
   * 这一反一正保护的是同一件事：用户不该为了暂停而在画面上先点一下。
   */
  test("D1: 播放中闲置 4s 后底栏常驻可点（不再有 3s 自收）", async ({ page, request }) => {
    await enterWatch(page, request);
    await startPlayback(page);

    // 老文件在这里先点「关闭小窗播放」退出迷你窗 —— 那个出口随 #30/DEC-069 一起删了，
    // 现在改为正面断言它不存在（跟随时画面贴顶常驻，没有「小窗」那一态）。
    await expect(page.locator('[aria-label="关闭小窗播放"]')).toHaveCount(0);

    // 把指针挪出画面、闲置 4s：老的隐藏计时器只在 !paused 时开火，这里是它该开火的条件。
    await page.mouse.move(187, 350);
    await page.waitForTimeout(4000);
    await page.screenshot({ path: `${SCREENSHOT_DIR}/02-after-4s-idle.png` });

    const bottomBar = await page.locator(BOTTOM_BAR).boundingBox();
    expect(bottomBar, "闲置后底栏仍在").not.toBeNull();
    expect(bottomBar!.x).toBeGreaterThanOrEqual(0);
    expect(
      bottomBar!.y,
      "闲置后底栏没有被挪出视口（移动端没有 translate-y-full 那一档）"
    ).toBeLessThan(812);
    expect(bottomBar!.y + bottomBar!.height, "闲置后底栏仍贴住可视区底边").toBeLessThanOrEqual(
      812 + 2
    );

    // ≤1023px 下页面里那份 `VideoControls` 根本不渲染（桌面 ≥1024px 才有）。
    await expect(page.locator('[data-testid="controls-bar"]')).toHaveCount(0);

    // 「可点」才是「常驻」的证据：等 4s 之后再点一次暂停，仍应生效。
    const toggle = page.locator('[data-testid="watch-toggle-play"]');
    await expect(toggle).toHaveAttribute("aria-label", "暂停", { timeout: 5000 });
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-label", "播放", { timeout: 5000 });
    await assertNoHorizontalOverflow(page, "after-idle");
  });

  /**
   * 底栏进度条：老文件那套（点画面浮起控制条再去拖进度）已随 DEC-069 删除；
   * 现在的契约是「2px 细线 + 44px 透明热区，点/拖都在这一条上」（§4 底栏），
   * 也就是**常驻可拖**。这里量热区几何 + 点一下真的换播放头（进度条不是装饰）。
   */
  test("底栏进度：44px 热区常驻可点，点一下真的换播放头", async ({ page, request }) => {
    await enterWatch(page, request);
    await startPlayback(page);
    await page.locator('[data-testid="watch-toggle-play"]').click(); // 暂停：播放头不许自己漂
    await expect(page.locator('[data-testid="watch-toggle-play"]')).toHaveAttribute(
      "aria-label",
      "播放",
      { timeout: 5000 }
    );

    const rail = await page.locator('[data-testid="watch-progress"]').boundingBox();
    expect(rail, "进度热区有盒子").not.toBeNull();
    expect(Math.round(rail!.height), "热区高 44px（不是那条 2px 线）").toBe(44);
    expect(rail!.x).toBeGreaterThanOrEqual(0);
    expect(rail!.x + rail!.width).toBeLessThanOrEqual(375 + 2);

    // 点热区正中 = 跳到总时长的一半（不是「只要动了就算过」）。
    const [before, total] = await page
      .locator("video")
      .first()
      .evaluate((v) => {
        const el = v as HTMLVideoElement;
        return [el.currentTime, el.duration] as const;
      });
    expect(Number.isFinite(total) && total > 0, `视频总时长可读：${total}`).toBe(true);
    await page.mouse.click(rail!.x + rail!.width * 0.5, rail!.y + rail!.height / 2);
    await expect
      .poll(
        () =>
          page
            .locator("video")
            .first()
            .evaluate((v) => (v as HTMLVideoElement).currentTime),
        { timeout: 5000 }
      )
      .toBeGreaterThan(Math.min(before + 1, total - 1));
    const after = await page
      .locator("video")
      .first()
      .evaluate((v) => (v as HTMLVideoElement).currentTime);
    expect(
      Math.abs(after - total / 2),
      `点到热区正中后播放头应在 50%（before=${before.toFixed(1)} total=${total.toFixed(1)} after=${after.toFixed(1)}）`
    ).toBeLessThan(total * 0.1);
    await expect.poll(() => playedWidth(page), { timeout: 5000 }).toBeGreaterThan(0);
  });

  /**
   * D10 —— 跟读抽屉仍「不压画面、不越底栏上沿」。
   *
   * 老文件里这一块是死代码：波形文案只在**录音回放态**出现，而移动端的练习 UI 早已
   * 搬进抽屉，「录音」按钮又埋在字幕卡里 —— 移动端从来不渲染那张卡，所以那个
   * `if (isVisible)` 永远走 else，什么都没量到。新形态的入口是底栏的「跟读」，
   * 这条用例真的把抽屉打开，量的是老文件想量却没量到的两件事：抽屉不盖画面，
   * 也不越底栏上沿；波形文案若在，仍不横向溢出。
   */
  test("重听取代录音入口，不再打开跟读抽屉", async ({ page, request }) => {
    await enterWatch(page, request);
    await expect(page.getByTestId("watch-replay")).toBeVisible();
    await expect(page.getByTestId("shadowing-drawer")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /录音|跟读/ })).toHaveCount(0);
    await assertNoHorizontalOverflow(page, "watch-replay");
  });
});
