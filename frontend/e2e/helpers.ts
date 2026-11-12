import { expect, type Locator, type Page, type APIRequestContext } from "@playwright/test";

/**
 * Shared helpers for the e2e suite.
 *
 * The app uses phone + SMS-code authentication (ADR: email auth removed). In
 * dev/CI the backend runs without Aliyun credentials, so `sms_service` accepts
 * a fixed dev-fake code (see backend/app/services/sms_service.py). These
 * helpers drive that flow both through the UI and the API.
 */

/** Fixed code accepted by the backend when no Aliyun SMS credentials are set. */
export const DEV_SMS_CODE = "1234";

/**
 * Fill the four-box registration OTP. Production codes are 4 digits (dev/CI
 * uses 1234); the page's cells are single-digit, so type one digit per box.
 */
export async function fillSmsOtp(page: Page, code = DEV_SMS_CODE): Promise<void> {
  const digits = code.replace(/\D/g, "");
  for (let i = 0; i < digits.length; i += 1) {
    await page.getByLabel(`验证码第 ${i + 1} 位`).fill(digits[i]);
  }
}

/** Password meeting the frontend policy (>=8 chars, upper + lower + digit). */
export const TEST_PASSWORD = "TestPass123";

/**
 * 选择 Base UI `ui/SelectMenu` 的选项：点开触发器，再点弹层里的选项。
 *
 * `#feed-level` / `#feed-sort` 已从原生 `<select>` 换成 Base UI Select
 * （触发器是 `button[role="combobox"]`），Playwright 的 `selectOption()` 与
 * `toHaveValue()` 都不再适用。选项标签含等级提示（如 `B2 · ≈六级`），需要按
 * 前缀选时传 RegExp。
 */
export async function chooseSelectMenu(
  page: Page,
  trigger: Locator,
  option: string | RegExp
): Promise<void> {
  await trigger.click();
  // The popup mounts asynchronously — measured in a real browser: right after
  // the click `aria-expanded` is still "false" and no listbox is visible yet,
  // and it only settles over a second later. Reading the listbox immediately
  // resolves to an empty set and the click then waits out the whole timeout.
  // So wait for the trigger to report itself expanded first.
  await expect(trigger).toHaveAttribute("aria-expanded", "true", { timeout: 15000 });
  // Two SelectMenus keep their listboxes mounted at once (Base UI keeps the
  // closed one in the DOM), so take the visible one rather than merely the last.
  const listbox = page.getByRole("listbox").filter({ visible: true }).last();
  await listbox.getByRole("option", { name: option, exact: typeof option === "string" }).click();
}

let phoneCounter = 0;

// Playwright evaluates this module per (worker, spec file) instance — module
// state is not shared between spec files, and with fullyParallel a file's
// tests can even span workers. So salt/base/counter are per instance, not
// per worker process: the counter only makes calls unique within one spec
// file (up to its 3-digit cap); everything else rides on the random draw
// (7 salts × 10⁶ bases; two of n instances collide with probability
// C(n,2)/(7×10⁶) ≈ 9×10⁻⁷ for n=12). CI (1 worker, fresh DB) never
// contends in the first place. A Date.now()-derived tail was tried before
// and abandoned: workers burst in the same millisecond, and a dev DB keeps
// old users across runs (409 该手机号已注册 kills the spec).
const workerSalt = 3 + Math.floor(Math.random() * 7); // second digit, 3-9
const workerBase = Math.floor(Math.random() * 10 ** 6);

/** Generate a unique valid Chinese mobile number (matches /^1[3-9]\d{9}$/). */
export function uniquePhone(): string {
  phoneCounter += 1;
  const base = workerBase.toString().padStart(6, "0");
  const c = phoneCounter.toString().padStart(3, "0");
  return `1${workerSalt}${base}${c}`; // 1 + salt + base(6) + counter(3) = 11 digits
}

/**
 * Register a user via the API and mark onboarding complete, so that a
 * subsequent UI login lands on "/" (not "/onboarding"). Returns the session.
 *
 * Canonical flow (no password at signup): send-code(auth) → sms/login (creates
 * the account) → change-password (first-time set, no current_password) →
 * complete onboarding.
 */
export async function registerUserViaApi(
  request: APIRequestContext,
  phone: string,
  password = TEST_PASSWORD
): Promise<{ token: string; phone: string; password: string }> {
  await request.post("/api/v1/auth/sms/send-code", {
    data: { phone, purpose: "auth" },
  });
  const login = await request.post("/api/v1/auth/sms/login", {
    data: { phone, code: DEV_SMS_CODE },
  });
  if (!login.ok()) {
    throw new Error(`API registration failed: ${login.status()} ${await login.text()}`);
  }
  const { token } = await login.json();
  const change = await request.post("/api/v1/auth/change-password", {
    headers: { Authorization: `Bearer ${token}` },
    data: { new_password: password },
  });
  if (!change.ok()) {
    throw new Error(`API password setup failed: ${change.status()} ${await change.text()}`);
  }
  // Complete onboarding so login doesn't bounce to /onboarding.
  await request.post("/api/v1/users/me/onboarding", {
    headers: { Authorization: `Bearer ${token}` },
    data: { onboarding_completed: true },
  });
  return { token, phone, password };
}

/** Register a user through the register page UI (exercises the real flow). */
export async function registerViaUi(page: Page, phone: string): Promise<void> {
  await page.goto("/register");
  await page.locator('input[placeholder="请输入手机号"]').fill(phone);
  await page.getByRole("button", { name: "获取验证码" }).click();
  await fillSmsOtp(page);
  await page.getByRole("checkbox").focus();
  await page.getByRole("checkbox").press("Space");
  await page.locator('button[type="submit"]').click();

  // New users land on the set-password step (from=register); save a password.
  await page.waitForURL((url) => url.pathname === "/set-password", { timeout: 15000 });
  await page.locator('input[placeholder="请输入新密码"]').fill(TEST_PASSWORD);
  await page.locator('input[placeholder="再次输入密码"]').fill(TEST_PASSWORD);
  await page.locator('button[type="submit"]').click();

  // After saving, the new user goes to /onboarding.
  await page.waitForURL((url) => url.pathname === "/" || url.pathname === "/onboarding", {
    timeout: 15000,
  });
}

/**
 * 切到登录页的「密码登录」tab。
 *
 * 26ff9c6 起 /login 默认是「验证码登录」，密码框只在切过去之后才渲染 ——
 * 任何按 `input[type="password"]` 定位 /login 的用例都必须先切这一下。
 */
export async function switchToPasswordLogin(page: Page): Promise<void> {
  await page.getByRole("tab", { name: "密码登录" }).click();
}

/** Log in through the login page UI (password mode). Onboarding must be done. */
export async function loginViaUi(
  page: Page,
  phone: string,
  password = TEST_PASSWORD
): Promise<void> {
  await page.goto("/login");
  await switchToPasswordLogin(page);
  await page.locator('input[placeholder="请输入手机号"]').fill(phone);
  await page.locator('input[type="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL((url) => url.pathname === "/", { timeout: 15000 });
}

/**
 * Bypass the login UI with an already-issued token.
 *
 * Injects the token into localStorage before any script runs, so the auth
 * store's initialize() picks it up like a real login. Use when a spec runs
 * many tests against one user — each UI login consumes the per-IP
 * phone-login rate limit (5/minute), which a 6-test file would exhaust.
 */
export async function loginViaToken(page: Page, token: string): Promise<void> {
  await page.addInitScript((t) => {
    window.localStorage.setItem("seeword_token", t);
  }, token);
  await page.goto("/");
  await page.waitForURL((url) => url.pathname === "/", { timeout: 15000 });
}
