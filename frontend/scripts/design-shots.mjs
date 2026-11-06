// Design-review screenshot harness.
// Registers (or reuses) a throwaway account, then captures every user-facing
// route at desktop and mobile widths into docs/evidence/design-redo/.
//
// Usage: node scripts/design-shots.mjs [--routes=/a,/b] [--tag=before]
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium, request } from "@playwright/test";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, "..", "..", "docs", "evidence", "design-redo");

const BASE = process.env.SHOT_BASE ?? "http://localhost:3000";
const API = process.env.SHOT_API ?? "http://localhost:8000";
const TAG = (process.argv.find((a) => a.startsWith("--tag=")) ?? "--tag=latest").slice(6);
const ROUTE_ARG = process.argv.find((a) => a.startsWith("--routes="));

const ROUTES = ROUTE_ARG
  ? ROUTE_ARG.slice(9).split(",")
  : [
      "/",
      "/channels",
      "/practice",
      "/vocabulary",
      "/vocabulary/review",
      "/profile",
      "/favorites",
      "/history",
      "/notifications",
      "/rankings",
      "/search?q=english",
    ];

const VIEWPORTS = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844, isMobile: true, hasTouch: true },
];

async function loginToken() {
  const api = await request.newContext({ baseURL: API });
  const phone = `138${String(Date.now()).slice(-8)}`;
  await api.post("/api/v1/auth/sms/send-code", { data: { phone, purpose: "auth" } });
  const login = await api.post("/api/v1/auth/sms/login", { data: { phone, code: "1234" } });
  if (!login.ok()) throw new Error(`login failed ${login.status()} ${await login.text()}`);
  const { token } = await login.json();
  await api.post("/api/v1/auth/change-password", {
    headers: { Authorization: `Bearer ${token}` },
    data: { new_password: "TestPass123" },
  });
  await api.post("/api/v1/users/me/onboarding", {
    headers: { Authorization: `Bearer ${token}` },
    data: { onboarding_completed: true },
  });
  await api.dispose();
  return token;
}

const token = process.env.SHOT_TOKEN ?? (await loginToken());
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const results = [];

for (const vp of VIEWPORTS) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    isMobile: vp.isMobile ?? false,
    hasTouch: vp.hasTouch ?? false,
    deviceScaleFactor: 1,
  });
  await context.addInitScript((t) => {
    window.localStorage.setItem("seeword_token", t);
    document.cookie = `seeword_token=${t}; path=/;`;
  }, token);
  const page = await context.newPage();
  for (const route of ROUTES) {
    const url = `${BASE}${route}`;
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
      await page.locator("main h1, [role=alert]").first().waitFor({ timeout: 20000 });
      await page.waitForTimeout(1800);
      const slug =
        route === "/"
          ? "home"
          : route.replace(/[/?=&]/g, "_").replace(/^_+/, "").replace(/_+$/g, "");
      const file = join(OUT, `${TAG}-${slug}-${vp.name}.png`);
      await page.screenshot({ path: file, fullPage: true });
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth
      );
      results.push({ route, viewport: vp.name, file, overflow });
      console.log(`ok ${vp.name} ${route} overflow=${overflow}`);
    } catch (err) {
      console.error(`FAIL ${vp.name} ${route}: ${err.message}`);
    }
  }
  await context.close();
}

writeFileSync(join(OUT, `${TAG}-index.json`), JSON.stringify(results, null, 2));
await browser.close();
