import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type Page } from "@playwright/test";

export const VIDEO_ID = "watch-baseline-fixture";
export const subtitles = [
  {
    id: "first",
    start_time: 0,
    end_time: 3,
    sentence_index: 0,
    text_en: "I walk into it.",
    text_zh: "我走进去了。",
    word_levels: null,
  },
  {
    id: "second",
    start_time: 5,
    end_time: 8,
    sentence_index: 1,
    text_en: "Then I walk home.",
    text_zh: "然后我走回家。",
    word_levels: null,
  },
  {
    id: "last",
    start_time: 15,
    end_time: 20,
    sentence_index: 2,
    text_en: "We finish here.",
    text_zh: "我们到此结束。",
    word_levels: null,
  },
];

// Generated H.264/AAC clock fixture; not an English listening-quality sample.
const clockMedia = readFileSync(join(__dirname, "fixtures/watch-clock.mp4"));

export async function setupWatch(
  page: Page,
  options: {
    empty?: boolean;
    brokenMedia?: boolean;
    saved?: number;
    delayProgress?: number;
    youtube?: boolean;
    short?: boolean;
    title?: string;
    longSentence?: boolean;
    richGloss?: boolean;
    cues?: typeof subtitles;
  } = {}
) {
  const token = `fixture.${Buffer.from(JSON.stringify({ sub: "watch-test-user", exp: 4102444800 })).toString("base64url")}.fixture`;
  await page
    .context()
    .addCookies([{ name: "seeword_token", value: token, url: "http://localhost:3000" }]);
  await page.addInitScript((t) => window.localStorage.setItem("seeword_token", t), token);
  if (options.youtube) await installYoutubeClock(page);
  // WebKit media requests bypass page.route on Windows. Use actual HTTP Range responses.
  const mediaServer = createServer((request, response) => {
    if (options.brokenMedia) {
      response.writeHead(404);
      response.end();
      return;
    }
    const range = request.headers.range?.match(/bytes=(\d+)-(\d*)/);
    const start = range ? Number(range[1]) : 0;
    const end = range?.[2]
      ? Math.min(Number(range[2]), clockMedia.length - 1)
      : clockMedia.length - 1;
    response.writeHead(range ? 206 : 200, {
      "Content-Type": "video/mp4",
      "Content-Length": end - start + 1,
      "Accept-Ranges": "bytes",
      "Access-Control-Allow-Origin": "*",
      ...(range ? { "Content-Range": `bytes ${start}-${end}/${clockMedia.length}` } : {}),
    });
    response.end(request.method === "HEAD" ? undefined : clockMedia.subarray(start, end + 1));
  });
  await new Promise<void>((resolve, reject) => {
    mediaServer.once("error", reject);
    mediaServer.listen(0, "127.0.0.1", resolve);
  });
  const address = mediaServer.address();
  if (!address || typeof address === "string") throw new Error("No local media port");
  const mediaUrl = `http://127.0.0.1:${address.port}/watch-clock.mp4`;
  page.once("close", () => {
    mediaServer.closeAllConnections();
    mediaServer.close();
  });
  const calls: { path: string; method: string; params: URLSearchParams; body: unknown }[] = [];
  const writes: number[] = [];
  let staticFails = false;
  let progressFails = false;
  let delayWord = "";
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request(),
      url = new URL(request.url()),
      path = url.pathname;
    calls.push({
      path,
      method: request.method(),
      params: url.searchParams,
      body: request.postDataJSON(),
    });
    let json: unknown;
    if (path === "/api/v1/users/me")
      json = {
        id: "watch-test-user",
        name: "Watch Test",
        phone: "13800000000",
        role: "user",
        onboarding_completed: true,
        created_at: "2026-10-20T00:00:00Z",
        avatar_url: null,
      };
    else if (path === "/api/v1/users/me/preferences")
      json = { target_exam: "cet4", subtitle_font_size: "medium" };
    else if (path === `/api/v1/videos/${VIDEO_ID}`)
      json = {
        id: VIDEO_ID,
        title: options.title ?? "观看路径测试",
        status: "ready",
        storage_mode: "local",
        duration: 20,
        video_url_480p: options.youtube ? null : mediaUrl,
        source_url: "https://www.youtube.com/watch?v=abcdefghijk",
        channel_name: "Test",
        difficulty_level: "B1",
        is_official: true,
        like_count: 0,
        subtitles: options.empty
          ? []
          : options.short
            ? subtitles.map((cue, index) => (index === 0 ? { ...cue, end_time: 0.01 } : cue))
            : options.longSentence
              ? subtitles.map((cue, i) =>
                  i === 0
                    ? {
                        ...cue,
                        text_en:
                          "I slip when I walk into a room and try to explain why this very long sentence needs to remain available in full.",
                        text_zh: "我滑倒了，这是一条需要完整保留并能按需展开阅读的很长的中文翻译。",
                      }
                    : cue
                )
              : (options.cues ?? subtitles),
      };
    else if (path === `/api/v1/learning/progress/${VIDEO_ID}`) {
      if (options.delayProgress) await new Promise((r) => setTimeout(r, options.delayProgress));
      json = { position_seconds: writes.at(-1) ?? options.saved ?? null };
    } else if (path === "/api/v1/learning/progress") {
      if (progressFails)
        return route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "保存失败" } });
      const data = request.postDataJSON() as { position_seconds: number };
      writes.push(data.position_seconds);
      json = {
        position_seconds: data.position_seconds,
        progress_percentage: data.position_seconds * 5,
      };
    } else if (path === "/api/v1/vocab-sets") json = [];
    else if (path === "/api/v1/vocabulary/words") json = { words: [] };
    else if (path.endsWith("/watch-meta")) json = { is_favorited: false, note: "" };
    else if (path.endsWith("/like-status")) json = { is_liked: false };
    else if (path.endsWith("/gloss/static")) {
      if (delayWord === url.searchParams.get("word")) await new Promise((r) => setTimeout(r, 700));
      if (staticFails)
        return route.fulfill({ status: 503, json: { code: "UNAVAILABLE", message: "测试失败" } });
      json = {
        word: url.searchParams.get("word"),
        lemma: url.searchParams.get("word"),
        translation: options.richGloss
          ? "v. 滑倒；失足；溜走\nn. 滑动；失误\n" + "其他词典内容；".repeat(120)
          : "v. 行走",
        phonetic: options.richGloss ? "slɪp" : null,
        levels: options.richGloss ? ["cet4", "cet6", "kaoyan", "ielts", "toefl", "gre"] : [],
      };
    } else if (path.endsWith("/gloss/enrich"))
      json = { levels: [], contextual_note: "视频级用法", note_scope: "video" };
    else if (path.endsWith("/unread-count")) json = { count: 0 };
    else json = { items: [], total: 0, page: 1, page_size: 20 };
    await route.fulfill({ json });
  });
  return {
    calls,
    writes,
    failProgress: (value: boolean) => {
      progressFails = value;
    },
    failLookup: (value: boolean) => {
      staticFails = value;
    },
    delayLookup: (word: string) => {
      delayWord = word;
    },
  };
}

export async function openWatch(page: Page, query = "") {
  await page.goto(`/watch/${VIDEO_ID}${query}`, { waitUntil: "domcontentloaded" });
  await expect(page.getByTestId("video-frame")).toBeVisible({ timeout: 15000 });
  try {
    await expect
      .poll(() => page.locator("video").evaluate((el: HTMLVideoElement) => el.readyState))
      .toBeGreaterThanOrEqual(2);
  } catch (error) {
    const media = await page.locator("video").evaluate((el: HTMLVideoElement) => ({
      ready: el.readyState,
      network: el.networkState,
      error: el.error?.code,
      mp4: el.canPlayType('video/mp4; codecs="avc1.42E01E, mp4a.40.2"'),
      preload: el.preload,
      paused: el.paused,
    }));
    throw new Error("Media fixture was not ready: " + JSON.stringify(media), { cause: error });
  }
}

export async function mediaState(page: Page) {
  return page.locator("video").evaluate((el: HTMLVideoElement) => ({
    time: el.currentTime,
    paused: el.paused,
    rate: el.playbackRate,
  }));
}

async function installYoutubeClock(page: Page) {
  await page.addInitScript(() => {
    class Player {
      private position = 0;
      private playing = false;
      private rate = 1;
      private started = 0;
      private options: {
        events: { onReady: () => void; onStateChange: (e: { data: number }) => void };
      };
      constructor(el: HTMLElement, options: Player["options"]) {
        this.options = options;
        (window as unknown as { watchFixturePlayer: Player }).watchFixturePlayer = this;
        el.textContent = "第三方播放器协议测试";
        setTimeout(() => options.events.onReady(), 20);
      }
      getCurrentTime() {
        return Math.min(
          20,
          this.position +
            (this.playing ? ((performance.now() - this.started) / 1000) * this.rate : 0)
        );
      }
      getState() {
        return { time: this.getCurrentTime(), paused: !this.playing };
      }
      seekTo(time: number) {
        this.position = time;
        this.started = performance.now();
      }
      playVideo() {
        if (!this.playing) {
          this.started = performance.now();
          this.playing = true;
        }
        this.options.events.onStateChange({ data: 1 });
      }
      pauseVideo() {
        this.position = this.getCurrentTime();
        this.playing = false;
        this.options.events.onStateChange({ data: 2 });
      }
      setPlaybackRate(rate: number) {
        this.position = this.getCurrentTime();
        this.started = performance.now();
        this.rate = rate;
      }
      destroy() {
        this.playing = false;
      }
    }
    (window as unknown as { YT: unknown }).YT = { Player };
  });
}

export async function clickReplay(page: Page) {
  const mobile = page.getByTestId("watch-replay");
  if ((await mobile.count()) && (await mobile.isVisible())) await mobile.click();
  else
    await page
      .getByTestId("sentence-actions")
      .getByRole("button", { name: "重听本句", exact: true })
      .click();
}

export async function clickLearningAction(page: Page, name: string) {
  if ((page.viewportSize()?.width ?? 1280) <= 1024)
    await page.getByTestId("watch-more-button").click();
  await page.getByTestId("sentence-actions").getByRole("button", { name, exact: true }).click();
}
