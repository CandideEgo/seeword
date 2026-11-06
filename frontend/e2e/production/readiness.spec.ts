import { test, expect } from "@playwright/test";
import { loginViaToken, registerUserViaApi, uniquePhone } from "../helpers";

let token = "";
let videoId = "";
test.beforeAll(async ({ request }) => {
  token = (await registerUserViaApi(request, uniquePhone())).token;
  const response = await request.get("/api/v1/videos/public?page_size=1");
  expect(response.ok()).toBe(true);
  videoId = (await response.json()).items[0]?.id;
  expect(videoId, "The production smoke environment must have playable seeded media").toBeTruthy();
});

test("生产资源、公开元数据与 HTTPS 策略", async ({ request }) => {
  const origin = new URL(process.env.PRODUCTION_SMOKE_URL || "https://localhost:18443").origin;
  for (const route of ["/login", "/terms", "/privacy", "/contact", "/robots.txt", "/logo.png"]) {
    const response = await request.get(route);
    expect(response.status(), route).toBe(200);
    expect(response.headers()["x-powered-by"]).toBeUndefined();
    expect(response.headers()["permissions-policy"]).toContain("microphone=(self)");
    const csp = response.headers()["content-security-policy"];
    expect(csp).toContain("media-src 'self' blob:");
    expect(csp).toContain(`wss://${new URL(origin).host}`);
  }
  const denied = await request.get("/profile", { maxRedirects: 0 });
  expect(denied.status()).toBe(307);
  expect(denied.headers().location).toContain("/login?next=");
  const privatePage = await request.get("/profile", {
    headers: { Cookie: `seeword_token=${token}` },
  });
  expect(await privatePage.text()).toMatch(/name="robots" content="[^"]*noindex/);
  const loginPage = await request.get("/admin/login");
  expect(await loginPage.text()).toMatch(/name="robots" content="[^"]*noindex/);
  const terms = await request.get("/terms");
  const termsHtml = await terms.text();
  expect(termsHtml.match(/name="robots" content="([^"]+)"/)?.[1]).not.toContain("noindex");
  expect(termsHtml).toContain(`${origin}/og-image.png`);
  const protectedLookalike = await request.get("/robots.txt/private", { maxRedirects: 0 });
  expect(protectedLookalike.status()).toBe(307);
  const anonymousMedia = await request.get(`/media/${videoId}.mp4`, {
    headers: { Range: "bytes=0-1023" },
  });
  expect(anonymousMedia.status()).toBe(403);
  const range = await request.get(`/media/${videoId}.mp4`, {
    headers: { Range: "bytes=0-1023", Authorization: `Bearer ${token}` },
  });
  expect(range.status()).toBe(206);
  expect(range.headers()["content-range"]).toMatch(/^bytes 0-1023\//);
  const afterAuthenticated = await request.get(`/media/${videoId}.mp4`, {
    headers: { Range: "bytes=0-1023" },
  });
  expect(
    afterAuthenticated.status(),
    "Authenticated media must never populate an anonymous shared cache"
  ).toBe(403);
  const missing = await request.get("/media/shadowing/smoke-missing.webm");
  expect(missing.headers()["permissions-policy"]).toContain("microphone=(self)");
});

test("用户页面三档视口与亮暗主题布局", async ({ page }, testInfo) => {
  test.setTimeout(480000);
  await loginViaToken(page, token);
  await page.addInitScript(() => localStorage.setItem("seeword_coach_done", "true"));
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  for (const width of [375, 768, 1440]) {
    await page.setViewportSize({ width, height: width === 375 ? 812 : 900 });
    for (const theme of ["light", "dark"]) {
      await page.addInitScript((value) => localStorage.setItem("theme", value), theme);
      for (const route of [
        "/",
        "/channels",
        "/vocabulary",
        "/vocabulary/sets",
        "/practice",
        "/practice/exams",
        "/profile",
        "/contact",
        "/favorites",
        "/history",
        "/search?q=practice",
        "/notifications",
        "/weekly-report",
        "/rankings",
      ]) {
        await page.goto(route);
        await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
        await expect(page.locator("html")).toHaveClass(
          theme === "dark" ? /dark/ : /^(?!.*\bdark\b).*$/
        );
        expect(
          await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
          route
        ).toBe(false);
        const main = page.locator("#main-scroll");
        if (await main.count())
          expect(await main.evaluate((el) => el.scrollWidth > el.clientWidth), route).toBe(false);
        await expect(
          page.getByText(/数据边界|本页分组各管什么|反馈接口|轮询模式|不补演示数据|内测免费/)
        ).toHaveCount(0);
        if (route === "/")
          // 改版后首页是「发现」流：导航在 375 宽度收进折叠菜单，所以断言发现流
          // 本身（视频列表区 + level-1 标题），而不是导航里那个「发现视频」旧入口。
          await expect(page.getByRole("region", { name: "视频列表" })).toBeVisible();
        await page.screenshot({
          path: testInfo.outputPath(`${route.replace(/\W/g, "-") || "home"}-${width}-${theme}.png`),
          fullPage: true,
        });
        // Respect the real account read limits, including shell reads on full navigations.
        await page.waitForTimeout(3000);
      }
    }
  }
  expect(errors).toEqual([]);
});

test("生产视频拖动、录音回放与通知连接", async ({ page, context }) => {
  await loginViaToken(page, token);
  await page.addInitScript(() => localStorage.setItem("seeword_coach_done", "true"));
  await context.grantPermissions(["microphone"]);
  const connections: string[] = [];
  page.on("websocket", (socket) => connections.push(socket.url()));
  await page.goto(`/watch/${videoId}`);
  const video = page.locator("video").first();
  await expect(video).toBeVisible();
  await expect
    .poll(() => video.evaluate((el: HTMLVideoElement) => el.readyState))
    .toBeGreaterThanOrEqual(2);
  await video.evaluate((el: HTMLVideoElement) => {
    el.currentTime = 8;
  });
  await expect
    .poll(() => video.evaluate((el: HTMLVideoElement) => el.currentTime))
    .toBeGreaterThanOrEqual(7.5);
  await expect(page.getByText("本视频练习试卷")).toHaveCount(0);
  await page.getByRole("button", { name: "通知", exact: true }).click();
  await expect
    .poll(() => connections.some((url) => url.includes("/api/v1/notifications/ws")))
    .toBe(true);
  const pong = await page.evaluate(
    (accessToken) =>
      new Promise<boolean>((resolve, reject) => {
        const ws = new WebSocket(`wss://${location.host}/api/v1/notifications/ws`, [
          "bearer",
          accessToken,
        ]);
        const timer = setTimeout(() => {
          ws.close();
          reject(new Error("Notification handshake timed out"));
        }, 5000);
        ws.onopen = () => ws.send("ping");
        ws.onmessage = (event) => {
          clearTimeout(timer);
          ws.close();
          resolve(event.data === "pong");
        };
        ws.onerror = () => {
          clearTimeout(timer);
          reject(new Error("Notification handshake failed"));
        };
      }),
    token
  );
  expect(pong).toBe(true);
  const recording = await page.evaluate(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    const chunks: Blob[] = [];
    recorder.ondataavailable = (event) => chunks.push(event.data);
    const blob = await new Promise<Blob>((resolve) => {
      recorder.onstop = () => resolve(new Blob(chunks, { type: recorder.mimeType }));
      recorder.start();
      setTimeout(() => recorder.stop(), 500);
    });
    stream.getTracks().forEach((track) => track.stop());
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    try {
      await audio.play();
      return { size: blob.size, playing: !audio.paused };
    } finally {
      audio.pause();
      URL.revokeObjectURL(url);
    }
  });
  expect(recording.size).toBeGreaterThan(0);
  expect(recording.playing).toBe(true);
});
