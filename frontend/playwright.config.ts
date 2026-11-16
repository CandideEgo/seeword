import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testIgnore: "**/production/**",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  // 60s gives headroom for Next dev on-demand compilation of the first
  // page visit (CI e2e runs against `next dev` so the /api rewrite proxy is
  // active - see .github/workflows/ci.yml and next.config.js rewrites).
  timeout: 60000,
  // CI runners are slower than local machines; 5s (Playwright's default) is
  // tight for Next dev's on-demand compilation and for media readiness.
  expect: { timeout: 10000 },

  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000",
    // The app supports prefers-reduced-motion. Disabling motion keeps dialog
    // and drawer elements stable for clicks; otherwise Playwright can spend
    // the whole test timeout waiting for an animating element to settle.
    contextOptions: { reducedMotion: "reduce" },
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "mobile-iphone",
      use: { ...devices["iPhone X"] },
      testMatch: /mobile\.spec\.ts/,
    },
  ],

  webServer: process.env.CI
    ? undefined
    : [
        {
          // 120s keep-alive：Next dev 代理会复用空闲连接，uvicorn 默认 5s 超时关闭
          // 时与复用请求撞车 → ECONNRESET → 代理 500（本地全量 e2e 的随机假红）。
          command: "cd ../backend && uvicorn app.main:app --port 8000 --timeout-keep-alive 120",
          port: 8000,
          reuseExistingServer: !process.env.CI,
          timeout: 10000,
        },
        {
          command: "npm run dev",
          port: 3000,
          reuseExistingServer: !process.env.CI,
          timeout: 30000,
        },
      ],
});
