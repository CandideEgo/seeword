/**
 * 当前句卡（画面正下方的唯一一份当前句）—— DEC-069 的毕业物验收。
 *
 * 方案：`frontend/src/lib/watchLayout.ts`。
 * 入画字幕全删之后，当前句只剩这一处：**移动端与桌面端同一张卡**（INV-021 改写后
 * 的「恰好渲染一次」），所以本文件两个 viewport 都量同一组 `data-testid`。
 *
 * 断言的是契约里写死的那几条，不是「看起来差不多」：
 *   ① 卡在画面正下方、在文稿之前（不是浮在画面里，也不是塞在文稿下面）
 *   ② `[data-testid="video-frame"]` 里一个字都没有（入画字幕/标题 overlay 都已删除）
 *   ③ 卡里的词热区点开的是**那一张**手机词卡（`[data-variant="sheet"]`），词对得上
 *   ④ 点卡的空白处 = 播放/暂停，且**不**开词卡（跟点词错开）
 *   ⑤ 1280 桌面端是同一张卡、画面里同样零文字（旧断言「桌面端没有入画字幕」的反转版）
 *
 * 需要本地库里有**真能播**的视频：CI seed 的 `/media/<id>.mp4` 是占位 URL（404），
 * 这种情况下和 mobile-inline-subtitle.spec.ts 一样 skip，而不是在几何断言上失败。
 *
 * 运行：npx playwright test e2e/mobile-current-sentence-card.spec.ts --project=chromium
 */

import { test, expect, type Page, type APIRequestContext } from "@playwright/test";
import { registerUserViaApi, loginViaToken, uniquePhone } from "./helpers";

interface SubtitleRow {
  start_time: number;
  text_en: string;
  text_zh: string | null;
}

const FRAME = '[data-testid="video-frame"]';
const CARD = '[data-testid="current-sentence-card"]';
const WORD = `${CARD} .now-sub-word`;
const SHEET = '[data-testid="word-tooltip"][data-variant="sheet"]';

// 串行 + 一次注册：/auth/sms/register 是 3/minute（按 IP），每条用例各注册一个用户
// 会在第 4 条上 429（本文件 5 条移动 + 1 条桌面，共用一个 beforeAll 注册的用户）。
// 与 mobile-inline-subtitle.spec.ts 同策。
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

/**
 * 登录 → 打开第一条 ready 视频 → 跳过教程浮层 → 等到真能播 → 当前句卡出现。
 *
 * 刻意**不**断言 `controls-bar` / `burn-subtitle`：那条路已由 DEC-069 删除，
 * 这里只认新契约里的 testid，旧壳的残留不该让本文件变红（反过来也一样）。
 */
async function enterWatch(page: Page, request: APIRequestContext) {
  // D2 教程浮层会盖住画面：直接用 app 自己的「看过了」标记关掉，别靠点按钮文案。
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
  return videoId;
}

async function getSubtitles(
  request: APIRequestContext,
  videoId: string | null
): Promise<SubtitleRow[]> {
  const res = await request.get(`/api/v1/videos/${videoId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(res.ok(), `取字幕失败：${res.status()}`).toBe(true);
  return ((await res.json())?.subtitles ?? []) as SubtitleRow[];
}

/** 卡里第一个词热区的文本（`split(" ")` 后的裸词，不含标点）。 */
async function firstWordText(page: Page): Promise<string> {
  return (await page.locator(WORD).first().innerText()).replace(/\s+/g, " ").trim();
}

/**
 * 卡里「空白」的点击坐标。
 *
 * DEC-074 起卡底下多了一行 24px 的元信息行（计数 + 展开开关），所以**不能**再取底部
 * 20% —— 那里可能正好落在展开开关上（它自己吞掉点击，专门不切播放/暂停）。
 * 现在直接点中文行本身的中心：中文行没有词热区、没有 onClick，点了只会冒泡到整卡。
 */
async function blankPoint(page: Page) {
  const zh = await page.locator(`${CARD} [data-testid="current-sentence-zh"]`).boundingBox();
  if (zh) return { x: zh.x + zh.width * 0.5, y: zh.y + zh.height * 0.5 };
  // 英/中模式下没有中文行：退回卡的右下角（避开元信息行那一带）。
  const box = await page.locator(CARD).boundingBox();
  if (!box) throw new Error(`no bounding box for ${CARD}`);
  return { x: box.x + box.width * 0.9, y: box.y + box.height * 0.55 };
}

/** 文稿列表：卡必须在它之前。移动/桌面两条壳路径里找同一个祖先。 */
async function transcriptBox(page: Page) {
  for (const sel of ['[data-coach="subtitles"]', "#subtitle-1"]) {
    const box = await page.locator(sel).first().boundingBox();
    if (box) return box;
  }
  throw new Error("找不到文稿列表（[data-coach=subtitles] / #subtitle-1 都没有盒子）");
}

/**
 * 画框里**一个非空文本节点都没有** —— §7 判据 1。
 * 只走普通元素节点：`<video>` 没有子节点，覆盖物（入画字幕/标题卡）都是元素。
 */
function frameTextNodes(): Promise<string[]> {
  const frame = document.querySelector('[data-testid="video-frame"]');
  if (!frame) return Promise.resolve(["<no video-frame element>"]);
  const walker = document.createTreeWalker(frame, NodeFilter.SHOW_TEXT);
  const out: string[] = [];
  let node = walker.nextNode();
  while (node) {
    const text = (node.textContent ?? "").trim();
    if (text) out.push(text);
    node = walker.nextNode();
  }
  return Promise.resolve(out);
}

test.describe("当前句卡（414×896 移动端）", () => {
  test("卡在画面正下方、在文稿之前，且与画面同宽（不浮在画面里）", async ({ page, request }) => {
    await enterWatch(page, request);

    // 画框与卡：同一个槽位（同宽），卡顶 = 画框底（或极小缝隙）。
    const frame = (await page.locator(FRAME).boundingBox())!;
    const card = await page.locator(CARD).boundingBox();
    expect(card, "当前句卡有布局盒（不是 display:none）").not.toBeNull();
    expect(
      Math.abs(card!.x - frame.x),
      "卡与画框左边对齐（同一个槽位，不出血）"
    ).toBeLessThanOrEqual(2);
    expect(Math.abs(card!.width - frame.width), "卡与画框同宽").toBeLessThanOrEqual(2);
    expect(card!.y, "卡顶不高于画框底（不是浮在画面里）").toBeGreaterThanOrEqual(
      frame.y + frame.height - 1.5
    );
    const controls = (await page.getByTestId("watch-bottom-bar").boundingBox())!;
    expect(Math.abs(card!.y - (frame.y + frame.height)), "当前句紧接画面下沿").toBeLessThanOrEqual(
      2
    );
    expect(controls.y, "播放控制位于当前句之后").toBeGreaterThanOrEqual(card!.y + card!.height);

    // 文稿在卡之下：进页面未滚动时，卡在视口里、文稿顶边在卡底之下。
    const transcribed = await transcriptBox(page);
    expect(transcribed.y, "文稿顶边不高于卡底（卡在文稿之前）").toBeGreaterThanOrEqual(
      card!.y + card!.height - 2
    );

    // 一行英文 + 一行中文（默认双语）。
    await expect(page.locator(`${CARD} [data-testid="current-sentence-en"]`)).toBeVisible();
    expect(await page.locator(WORD).count(), "卡里有词热区").toBeGreaterThan(0);
    await expect(page.locator(`${CARD} [data-testid="subtitle-counter"]`)).toBeVisible();

    // DEC-074：计数从右上角搬进底部元信息行 —— 它不再压在英文第一行上（旧版实测会被长句压住）。
    const enBox = (await page
      .locator(`${CARD} [data-testid="current-sentence-en"]`)
      .boundingBox())!;
    const counterBox = (await page
      .locator(`${CARD} [data-testid="subtitle-counter"]`)
      .boundingBox())!;
    expect(
      counterBox.y,
      `计数顶 ${counterBox.y.toFixed(0)} 必须在英文块下沿 ${(enBox.y + enBox.height).toFixed(0)} 之下`
    ).toBeGreaterThanOrEqual(enBox.y + enBox.height - 1);
  });

  test("长句：英文夹两行、出现展开开关；展开读到完整英文、点它不切播放", async ({
    page,
    request,
  }) => {
    const videoId = await enterWatch(page, request);
    const subs = await getSubtitles(request, videoId);
    test.skip(subs.length === 0, "本地这条视频没有字幕，测不了长句");

    // 取最长的一句：折叠态（两行）必然超预算。
    let idx = 0;
    for (let i = 1; i < subs.length; i++) {
      if ((subs[i].text_en ?? "").length > (subs[idx].text_en ?? "").length) idx = i;
    }
    const longest = subs[idx];
    test.skip(
      (longest.text_en ?? "").length < 90,
      `本地最长句只有 ${(longest.text_en ?? "").length} 字符，够不到两行预算`
    );

    // 直接 seek（不走点文稿行）：贴顶画框会盖住列表行，点击可能被它拦下。
    await page
      .locator("video")
      .first()
      .evaluate((v, t) => {
        const el = v as HTMLVideoElement;
        el.pause();
        el.currentTime = t + 0.05;
      }, longest.start_time);
    await page.waitForTimeout(900);

    const en = page.locator(`${CARD} [data-testid="current-sentence-en"]`);
    await expect(en).toContainText((longest.text_en ?? "").split(" ")[0]);
    const before = (await en.boundingBox())!;

    const toggle = page.locator('[data-testid="current-sentence-expand"]');
    await expect(toggle, "超预算长句要出现展开开关").toBeVisible();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");

    const pausedBefore = await page
      .locator("video")
      .first()
      .evaluate((v) => (v as HTMLVideoElement).paused);
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    const after = (await en.boundingBox())!;
    expect(after.height, "展开后英文块变高（多出被裁掉的行）").toBeGreaterThan(before.height);
    await expect(page.locator(`${CARD} [data-testid="current-sentence-zh"]`)).toBeVisible();
    expect(
      await page
        .locator("video")
        .first()
        .evaluate((v) => (v as HTMLVideoElement).paused),
      "点展开开关不该顺带切播放/暂停（它自己吞掉这次点击）"
    ).toBe(pausedBefore);

    // 收回去：高度回到折叠态量级。
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    const collapsed = (await en.boundingBox())!;
    expect(collapsed.height).toBeLessThan(after.height);
  });

  test("画框里一个非空文本节点都没有（入画字幕/标题 overlay 已删净）", async ({
    page,
    request,
  }) => {
    await enterWatch(page, request);

    // 先等卡渲染出来，避免「页面还没挂载」被误读成「画框里没字」。
    await expect(page.locator(`${CARD} [data-testid="current-sentence-en"]`)).toBeVisible();
    expect(await page.locator(`${CARD} .now-sub-word`).count()).toBeGreaterThan(0);
    // 反转旧断言：那条「入画字幕贴画框下沿」的 testid 不该再存在。
    await expect(page.locator('[data-testid="burn-subtitle"]')).toHaveCount(0);

    const texts = await page.evaluate(frameTextNodes);
    expect(texts, `画框内文本节点：${JSON.stringify(texts)}`).toEqual([]);
  });

  test("点卡里的词 → 开手机词卡（sheet）且词对得上；点卡空白 → 切播放/暂停，不开词卡", async ({
    page,
    request,
  }) => {
    const videoId = await enterWatch(page, request);
    const subs = await getSubtitles(request, videoId);
    test.skip(subs.length === 0, "本地这条视频没有字幕，测不了词热区");

    // 钉在第 1 句、暂停：卡里显示什么由本用例说了算。
    await page
      .locator("video")
      .first()
      .evaluate((v) => {
        const el = v as HTMLVideoElement;
        el.pause();
        el.currentTime = 0;
      });
    await page.waitForTimeout(600);

    // ③ 点词 → 词卡（sheet 变体）打开，且开的就是那个词。
    const word = await firstWordText(page);
    expect(word.length, "第一个热区里有词").toBeGreaterThan(0);
    await page.locator(WORD).first().click();
    await expect(page.locator(SHEET)).toBeVisible({ timeout: 10000 });
    const label = (await page.locator(SHEET).getAttribute("aria-label")) ?? "";
    expect(label.toLowerCase(), `词卡 aria-label=${label}`).toContain(
      word.replace(/[^\p{L}\p{N}'-]/gu, "").toLowerCase()
    );
    expect(subs[0].text_en, `第 1 句里应该真有「${word}」（否则点错了句）`).toContain(
      word.replace(/[^\p{L}\p{N}'-]/gu, "")
    );

    // 关掉词卡：浮层消失，卡重新可点。
    await page.locator(`${SHEET} [aria-label="关闭"]`).click();
    await expect(page.locator('[data-testid="word-tooltip"]')).toHaveCount(0);

    // ④ 点卡的空白处 = 播放/暂停，且不开词卡。
    const before = await page
      .locator("video")
      .first()
      .evaluate((v) => (v as HTMLVideoElement).paused);
    const blank = await blankPoint(page);
    await page.mouse.click(blank.x, blank.y);
    await expect
      .poll(
        () =>
          page
            .locator("video")
            .first()
            .evaluate((v) => (v as HTMLVideoElement).paused),
        { timeout: 5000 }
      )
      .toBe(!before);
    await expect(page.locator('[data-testid="word-tooltip"]')).toHaveCount(0);
  });

  test("中文行只在双语/中文模式渲染（英模式下退场）", async ({ page, request }) => {
    await enterWatch(page, request);

    // 默认双语：中英两行都在。
    await expect(page.locator(`${CARD} [data-testid="current-sentence-en"]`)).toBeVisible();
    await expect(page.locator(`${CARD} [data-testid="current-sentence-zh"]`)).toBeVisible();

    // S 键循环：双语 → 英。中文行退场，英文行还在。
    // （keydown 挂在 window 上；此时焦点还在 body，不是 input/button，所以 S 生效。）
    await page.keyboard.press("S");
    await expect(page.locator(`${CARD} [data-testid="current-sentence-zh"]`)).toHaveCount(0, {
      timeout: 5000,
    });
    await expect(page.locator(`${CARD} [data-testid="current-sentence-en"]`)).toBeVisible();

    // S 键再循环一次：英 → 中。中文行回来，英文行退场。
    await page.keyboard.press("S");
    await expect(page.locator(`${CARD} [data-testid="current-sentence-zh"]`)).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator(`${CARD} [data-testid="current-sentence-en"]`)).toHaveCount(0);
  });
});

test.describe("桌面端同一张卡（1280×900）", () => {
  test.use({ viewport: { width: 1280, height: 900 } });

  test("1280 宽：同一张当前句卡在、画面里零文字、没有入画字幕那层壳", async ({ page, request }) => {
    await enterWatch(page, request);

    await expect(page.locator(CARD)).toHaveCount(1);
    await expect(page.locator(`${CARD} [data-testid="current-sentence-en"]`)).toBeVisible();
    expect(await page.locator(`${CARD} .now-sub-word`).count()).toBeGreaterThan(0);

    // 移动壳的覆盖物在桌面端也一个都不该在（入画字幕、标题卡、返回键、级别药丸）。
    await expect(page.locator('[data-testid="burn-subtitle"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="thin-progress"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="frame-title"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="frame-back"]')).toHaveCount(0);
    // 注意：桌面端**例外**于「画面里零文字」——`VideoControls` 是桌面专属（DEC-069 只把
    // 移动端控制搬进壳），它的时间读数/字幕模式按钮当然在画面里。所以这里量的是
    // 「画面里除了控制条那一层，没有别的东西」。
    const texts = await page.evaluate(() =>
      Array.from(document.querySelectorAll('[data-testid="video-frame"] *'))
        .filter((el) => el.closest('[data-testid="controls-bar"]') === null)
        .flatMap((el) => Array.from(el.childNodes))
        .filter((n) => n.nodeType === Node.TEXT_NODE && (n.textContent ?? "").trim() !== "")
        .map((n) => (n.textContent ?? "").trim())
    );
    expect(texts, `画框内（控制条之外）文本节点：${JSON.stringify(texts)}`).toEqual([]);

    // 卡仍钉在画面正下方、仍与画面同宽（同一张卡，不是只在移动端成立）。
    const frame = (await page.locator(FRAME).boundingBox())!;
    const card = (await page.locator(CARD).boundingBox())!;
    expect(Math.abs(card.x - frame.x), "桌面端卡与画框左边对齐").toBeLessThanOrEqual(2);
    expect(Math.abs(card.width - frame.width), "桌面端卡与画框同宽").toBeLessThanOrEqual(2);
    expect(card.y, "桌面端卡在画框之下").toBeGreaterThanOrEqual(frame.y + frame.height - 1.5);
  });
});
