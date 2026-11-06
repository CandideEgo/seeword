import { test, expect, type Page } from "@playwright/test";

function previewAudio() {
  const samples = 16000 * 3;
  const bytes = Buffer.alloc(44 + samples * 2);
  bytes.write("RIFF", 0);
  bytes.writeUInt32LE(bytes.length - 8, 4);
  bytes.write("WAVEfmt ", 8);
  bytes.writeUInt32LE(16, 16);
  bytes.writeUInt16LE(1, 20);
  bytes.writeUInt16LE(1, 22);
  bytes.writeUInt32LE(16000, 24);
  bytes.writeUInt32LE(32000, 28);
  bytes.writeUInt16LE(2, 32);
  bytes.writeUInt16LE(16, 34);
  bytes.write("data", 36);
  bytes.writeUInt32LE(samples * 2, 40);
  return bytes;
}

async function mockStories(page: Page, mediaFails = false) {
  await page.route("https://fonts.googleapis.com/**", (route) => route.abort());
  await page.route("https://fonts.gstatic.com/**", (route) => route.abort());
  const token = `${Buffer.from('{"alg":"HS256"}').toString("base64url")}.${Buffer.from(JSON.stringify({ sub: "home-story-test", exp: Math.floor(Date.now() / 1000) + 3600 })).toString("base64url")}.test`;
  await page.context().addCookies([
    {
      name: "seeword_token",
      value: token,
      url: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000",
    },
  ]);
  await page.addInitScript((value) => localStorage.setItem("seeword_token", value), token);
  await page.route("**/api/**", (route) => route.fulfill({ json: {} }));
  await page.route("**/api/v1/users/me", (route) =>
    route.fulfill({
      json: { id: "home-story-test", name: "学习者", onboarding_completed: true },
    })
  );
  const base = {
    channel_name: "Real source",
    thumbnail_url: null,
    duration: 180,
    storage_mode: "local",
    difficulty_level: "B1",
    video_url_480p: "/media/home-preview.wav",
  };
  await page.route("**/api/v1/browse/featured**", (route) =>
    route.fulfill({
      json: {
        items: [
          { ...base, id: "actions", title: "Action verbs", topic_tags: "education" },
          { ...base, id: "numbers", title: "Memory chips", topic_tags: "tech" },
          { ...base, id: "news", title: "Real news commentary", topic_tags: "news" },
        ],
      },
    })
  );
  const meta = {
    subtitle_count: 25,
    exam_word_count: 40,
    sample_start_time: 0.2,
    sample_end_time: 2.5,
    sample_words: [],
  };
  await page.route("**/api/v1/discovery/learning-metadata**", (route) =>
    route.fulfill({
      json: {
        actions: {
          ...meta,
          sample_subtitle_id: "action-sub",
          sample_text_en: "Kick. Flick. Skip. Punch. Yank.",
          sample_text_zh: "踢。弹。跳。打。拽。",
          sample_word_timestamps: [{ word: "Flick.", start: 0.5, end: 0.8 }],
        },
        numbers: {
          ...meta,
          sample_subtitle_id: "number-sub",
          sample_text_en: "These have billions of memory bits.",
          sample_text_zh: "这些有数十亿个存储位。",
        },
        news: {
          ...meta,
          sample_subtitle_id: "news-sub",
          sample_text_en: "Literally, I do not have any words.",
          sample_text_zh: "我真不知道该说什么了。",
        },
      },
    })
  );
  await page.route("**/api/v1/learning/records**", (route) =>
    route.fulfill({ json: { items: [] } })
  );
  await page.route("**/api/v1/learning/stats/weekly**", (route) =>
    route.fulfill({ json: { this_week_minutes: 18, this_week_words: 3, this_week_videos: 1 } })
  );
  await page.route("**/api/v1/vocabulary/stats**", (route) =>
    route.fulfill({ json: { total: 241, due_count: 24 } })
  );
  await page.route(/\/api\/v1\/vocabulary\?/, (route) =>
    route.fulfill({
      json:
        route.request().method() === "POST"
          ? { id: "saved" }
          : {
              items: [
                { id: "v1", word: "habit", translation: "习惯" },
                { id: "v2", word: "remark", translation: "评论" },
                { id: "v3", word: "memory", translation: "记忆" },
              ],
            },
    })
  );
  await page.route("**/api/v1/recommendations/home**", (route) =>
    route.fulfill({ json: { items: [], has_more: false, total: 0 } })
  );
  await page.route("**/media/home-preview.wav**", (route) => {
    if (mediaFails) return route.abort("failed");
    if (!new URL(route.request().url()).searchParams.get("token")) {
      return route.fulfill({ status: 403, json: { message: "登录后试听" } });
    }
    return route.fulfill({ contentType: "audio/wav", body: previewAudio() });
  });
}

test("普通精选不请求字幕预览或媒体，不展示学习任务", async ({ page }) => {
  await mockStories(page);
  const unnecessary: string[] = [];
  page.on("request", (request) => {
    if (/learning-metadata|home-preview/.test(request.url())) unnecessary.push(request.url());
  });
  await page.goto("/");
  const card = page.getByRole("article", { name: "精选视频", exact: true });
  await expect(card.getByRole("heading", { name: "Action verbs", exact: true })).toBeVisible();
  await expect(card.getByRole("link", { name: "观看完整视频", exact: true })).toHaveAttribute(
    "href",
    "/watch/actions?from=home"
  );
  await expect(page.locator("#home-scenarios")).toHaveCount(0);
  await expect(page.getByText("Kick. Flick. Skip. Punch. Yank.")).toHaveCount(0);
  expect(unnecessary).toEqual([]);
});

test("媒体不可试听仍可进入完整视频", async ({ page }) => {
  await mockStories(page, true);
  await page.goto("/");
  await expect(page.getByRole("link", { name: "观看完整视频", exact: true })).toHaveAttribute(
    "href",
    "/watch/actions?from=home"
  );
});
