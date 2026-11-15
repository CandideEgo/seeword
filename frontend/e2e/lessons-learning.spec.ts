import fs from "node:fs";
import { expect, test, type APIRequestContext, type Page } from "@playwright/test";
import { loginViaToken } from "./helpers";
import type { LessonDetail, LessonHistoryItem, LessonProgress } from "../src/lib/lessons";
import type { LessonCatalogPage } from "../src/lib/lessonCatalog";

/**
 * 真实课程请求；不导入/发布材料，不操作数据库，也不触发模型或播放器。
 * 主验收线程在隔离 testing 栈播种自创材料和专用用户后注入：
 *   E2E_LESSON_FIXTURE=<JSON 文件绝对路径>
 *   E2E_LESSON_PHONE / E2E_LESSON_PASSWORD=<专用用户口令>
 * JSON 契约见 LessonFixture：两个仍可读的不同修订；另一材料的撤回修订
 * （该材料必须另有可读当前版）；search_query 至少命中 21 条；用户至少
 * 有 21 条历史，前 20 条含撤回指针；主材料尚未完成。用户已完成
 * onboarding 并有 v2_access。每次验收重新播种，不复用上一轮完成状态。
 * 未准备外部夹具时明确 skip，不把收集用例或 skip 算成通过。
 * 错误恢复只注入传输 abort；重试后的响应和所有业务写入均来自真实后端。
 */
interface LessonFixture {
  lesson_id: string;
  revision_id: string;
  other_revision_id: string;
  withdrawn_lesson_id: string;
  withdrawn_revision_id: string;
  search_query: string;
}

const fixturePath = process.env.E2E_LESSON_FIXTURE;
const phone = process.env.E2E_LESSON_PHONE;
const password = process.env.E2E_LESSON_PASSWORD;
const fixture = fixturePath
  ? (JSON.parse(fs.readFileSync(fixturePath, "utf8")) as LessonFixture)
  : null;
const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";
let token = "";
let original: LessonDetail;
let other: LessonDetail;
const diagnostics = new WeakMap<Page, object[]>();

function data(): LessonFixture {
  if (!fixture) throw new Error("课程隔离夹具未准备");
  for (const key of [
    "lesson_id",
    "revision_id",
    "other_revision_id",
    "withdrawn_lesson_id",
    "withdrawn_revision_id",
    "search_query",
  ] as const) {
    if (typeof fixture[key] !== "string" || !fixture[key].trim())
      throw new Error(`课程夹具缺少 ${key}`);
  }
  return fixture;
}

function href(lessonId: string, revisionId: string) {
  return `/lessons/${encodeURIComponent(lessonId)}?${new URLSearchParams({ revision: revisionId })}`;
}

function revisionPath(lessonId: string, revisionId: string) {
  return `/api/v1/lessons/${encodeURIComponent(lessonId)}/revisions/${encodeURIComponent(revisionId)}`;
}

function headers() {
  return { Authorization: `Bearer ${token}` };
}

async function getJson<T>(request: APIRequestContext, path: string): Promise<T> {
  const response = await request.get(path, { headers: headers() });
  expect(response.status(), `GET ${path}: ${await response.text()}`).toBe(200);
  return response.json() as Promise<T>;
}

async function signIn(page: Page) {
  await page.context().addCookies([{ name: "seeword_token", value: token, url: baseURL }]);
  await loginViaToken(page, token);
}

async function expectBody(page: Page, lesson: LessonDetail) {
  await expect(page.getByRole("heading", { name: lesson.pack.title, exact: true })).toBeVisible();
  for (const segment of lesson.pack.segments) {
    const line = page.locator(`[id="lesson-line-${segment.id}"]`);
    await expect(line).toContainText(segment.text);
    await expect(line).toContainText(segment.translation);
  }
  await expect(page.getByRole("status", { name: "正在加载课程", exact: true })).toHaveCount(0);
}

test.describe("课程固定修订与历史闭环（真实请求）", () => {
  test.describe.configure({ mode: "serial" });
  test.skip(
    !fixture || !phone || !password,
    "未准备隔离课程数据和专用用户；本组不代表工程验收通过"
  );

  test.beforeEach(async ({ page }) => {
    const events: object[] = [];
    await page.exposeFunction("recordCourseUiClick", (event: object) => events.push(event));
    await page.addInitScript(() => {
      document.addEventListener(
        "click",
        (event) => {
          const target = event.target instanceof Element ? event.target.closest("button") : null;
          if (target)
            void (
              window as unknown as { recordCourseUiClick: (event: object) => Promise<void> }
            ).recordCourseUiClick({
              event: "click",
              button: target.textContent?.trim(),
              disabled: target.hasAttribute("disabled"),
            });
        },
        true
      );
    });
    page.on("request", (request) => {
      const path = new URL(request.url()).pathname;
      if (path.startsWith("/api/v1/lessons/"))
        events.push({ event: "request", method: request.method(), path });
    });
    page.on("response", (response) => {
      const path = new URL(response.url()).pathname;
      if (path.startsWith("/api/v1/lessons/"))
        events.push({ event: "response", status: response.status(), path });
    });
    page.on("pageerror", (error) => events.push({ event: "pageerror", message: error.message }));
    diagnostics.set(page, events);
  });

  test.afterEach(async ({ page }, testInfo) => {
    if (testInfo.status !== testInfo.expectedStatus) {
      await testInfo.attach("course-safe-events", {
        body: JSON.stringify(diagnostics.get(page) ?? [], null, 2),
        contentType: "application/json",
      });
    }
  });

  test.beforeAll(async ({ request }) => {
    const fixture = data();
    expect(fixture.revision_id).not.toBe(fixture.other_revision_id);
    expect(fixture.lesson_id).not.toBe(fixture.withdrawn_lesson_id);
    const login = await request.post("/api/v1/auth/phone-login", { data: { phone, password } });
    expect(login.status(), `课程专用用户登录: ${await login.text()}`).toBe(200);
    token = ((await login.json()) as { token: string }).token;
    original = await getJson(request, revisionPath(fixture.lesson_id, fixture.revision_id));
    other = await getJson(request, revisionPath(fixture.lesson_id, fixture.other_revision_id));
    expect(original.pack.segments.length).toBeGreaterThan(1);
    expect(original.pack.vocabulary.length).toBeGreaterThan(0);
    expect(original.permissions.vocabulary_enabled).toBe(true);
    expect(original.pack.segments).not.toEqual(other.pack.segments);
    const withdrawn = await request.get(
      revisionPath(fixture.withdrawn_lesson_id, fixture.withdrawn_revision_id),
      { headers: headers() }
    );
    expect([403, 404, 410]).toContain(withdrawn.status());
    // A current revision really exists: dropping ?revision would silently open
    // another pack rather than merely rendering the same unavailable screen.
    await getJson(request, `/api/v1/lessons/${encodeURIComponent(fixture.withdrawn_lesson_id)}`);
    const history = await getJson<{ items: LessonHistoryItem[] }>(
      request,
      "/api/v1/lessons/_history?offset=0&limit=21"
    );
    expect(history.items).toHaveLength(21);
    expect(
      history.items
        .slice(0, 20)
        .some(
          (item) =>
            item.lesson_id === fixture.withdrawn_lesson_id &&
            item.revision_id === fixture.withdrawn_revision_id &&
            !item.available
        )
    ).toBe(true);
    const catalog = await getJson<LessonCatalogPage>(
      request,
      `/api/v1/lessons/_search?${new URLSearchParams({ q: fixture.search_query, offset: "0", limit: "20" })}`
    );
    expect(catalog.total).toBeGreaterThan(20);
  });

  test("首次固定 URL 读取正文，后续 _state 不重拉包；修订切换不残留旧正文", async ({ page }) => {
    const fixture = data();
    await signIn(page);
    const calls: string[] = [];
    page.on("request", (request) => {
      const url = new URL(request.url());
      if (url.pathname.startsWith(`/api/v1/lessons/${fixture.lesson_id}`))
        calls.push(url.pathname + url.search);
    });
    await page.goto(href(fixture.lesson_id, fixture.revision_id));
    await expectBody(page, original);
    expect(calls[0]).toBe(revisionPath(fixture.lesson_id, fixture.revision_id));
    // A real pageshow triggers the same lightweight availability refresh as
    // returning to this tab. No fake API response or waiting for a 20s timer.
    await page.bringToFront();
    await expect.poll(() => page.evaluate(() => document.visibilityState)).toBe("visible");
    const stateResponse = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname.endsWith("/_state") &&
        url.searchParams.get("revision") === fixture.revision_id &&
        response.status() === 200
      );
    });
    await page.evaluate(() => window.dispatchEvent(new Event("pageshow")));
    await stateResponse;
    await expectBody(page, original);
    expect(
      calls.filter((path) => path === revisionPath(fixture.lesson_id, fixture.revision_id))
    ).toHaveLength(1);
    expect(calls).not.toContain(`/api/v1/lessons/${fixture.lesson_id}`);

    await page.goto(href(fixture.lesson_id, fixture.other_revision_id));
    await expectBody(page, other);
    const uniqueOldLine = original.pack.segments.find(
      (segment) => !other.pack.segments.some((next) => next.text === segment.text)
    );
    expect(uniqueOldLine).toBeDefined();
    await expect(page.getByText(uniqueOldLine!.text, { exact: true })).toHaveCount(0);
    await page.goBack();
    await expectBody(page, original);
  });

  test("固定修订正文加载失败可重试，恢复时绝不查当前版", async ({ page }) => {
    const fixture = data();
    await signIn(page);
    const path = revisionPath(fixture.lesson_id, fixture.revision_id);
    const pattern = `**${path}`;
    await page.route(pattern, (route) => route.abort("failed"));
    const currentRequests: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname === `/api/v1/lessons/${fixture.lesson_id}`)
        currentRequests.push(request.url());
    });
    await page.goto(href(fixture.lesson_id, fixture.revision_id));
    await expect(page.getByText("课程加载失败", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: original.pack.title, exact: true })).toHaveCount(
      0
    );
    await page.unroute(pattern);
    const response = page.waitForResponse(
      (response) => new URL(response.url()).pathname === path && response.status() === 200
    );
    await page.getByRole("button", { name: "重试", exact: true }).click();
    await response;
    await expectBody(page, original);
    expect(currentRequests).toEqual([]);
  });

  test("共享目录检索分页与失败重试都发送真实请求", async ({ page }) => {
    const fixture = data();
    await signIn(page);
    await page.goto("/lessons");
    await page.getByRole("searchbox", { name: "搜索课程" }).fill(fixture.search_query);
    const firstResponse = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname.endsWith("/_search") &&
        url.searchParams.get("q") === fixture.search_query &&
        response.status() === 200
      );
    });
    await page
      .getByRole("search", { name: "课程检索" })
      .getByRole("button", { name: "搜索", exact: true })
      .click();
    const first = (await (await firstResponse).json()) as LessonCatalogPage;
    const catalog = page.getByRole("region", { name: "课程目录", exact: true });
    const firstLink = catalog.locator(
      `a[href="${href(first.items[0].lesson_id, first.items[0].revision_id)}"]`
    );
    await expect(firstLink).toBeVisible();
    const nav = page.getByRole("navigation", { name: "课程目录分页" });
    await expect(nav.getByRole("button", { name: "下一页" })).toBeEnabled();
    await page.route("**/api/v1/lessons/_search?**", (route) => route.abort("failed"));
    await nav.getByRole("button", { name: "下一页" }).click();
    await expect(page.getByText("课程目录加载失败", { exact: true })).toBeVisible();
    await expect(firstLink).toHaveCount(0);
    await page.unroute("**/api/v1/lessons/_search?**");
    const secondResponse = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname.endsWith("/_search") &&
        url.searchParams.get("offset") === "20" &&
        url.searchParams.get("q") === fixture.search_query &&
        response.status() === 200
      );
    });
    await page.getByRole("button", { name: "重试", exact: true }).click();
    const second = (await (await secondResponse).json()) as LessonCatalogPage;
    await expect(
      catalog.locator(`a[href="${href(second.items[0].lesson_id, second.items[0].revision_id)}"]`)
    ).toBeVisible();
    await expect(nav.getByRole("button", { name: "上一页" })).toBeEnabled();
  });

  test("主学习历史保留撤回修订，前瞻分页失败后可恢复", async ({ page, request }) => {
    const fixture = data();
    await signIn(page);
    await page.goto("/history");
    const history = page.getByRole("region", { name: "课程学习历史" });
    const withdrawnLink = history.locator(
      `a[href="${href(fixture.withdrawn_lesson_id, fixture.withdrawn_revision_id)}"]`
    );
    await expect(withdrawnLink).toContainText("材料已不可用");
    await withdrawnLink.click();
    await expect(page).toHaveURL(new RegExp(`revision=${fixture.withdrawn_revision_id}`));
    await expect(page.getByText("材料已不可用", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "双语字幕", exact: true })).toHaveCount(0);
    const restoredHistory = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname.endsWith("/_history") &&
        url.searchParams.get("offset") === "0" &&
        response.status() === 200
      );
    });
    await page.goto("/history");
    await restoredHistory;
    const nav = history.getByRole("navigation", { name: "课程历史分页" });
    await expect(nav.getByRole("button", { name: "下一页" })).toBeEnabled();
    await page.route("**/api/v1/lessons/_history?**", (route) => route.abort("failed"));
    await nav.getByRole("button", { name: "下一页" }).click();
    await expect(history.getByText("课程历史加载失败", { exact: true })).toBeVisible();
    await page.unroute("**/api/v1/lessons/_history?**");
    const nextResponse = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname.endsWith("/_history") &&
        url.searchParams.get("offset") === "20" &&
        url.searchParams.get("limit") === "21" &&
        response.status() === 200
      );
    });
    await history.getByRole("button", { name: "重试", exact: true }).click();
    const next = (await (await nextResponse).json()) as { items: LessonHistoryItem[] };
    expect(next.items.length).toBeGreaterThan(0);
    await expect(history.locator("li")).toHaveCount(Math.min(20, next.items.length));
    const persisted = await getJson<LessonProgress>(
      request,
      `/api/v1/lessons/${fixture.withdrawn_lesson_id}/progress`
    );
    expect(persisted.revision_id).toBe(fixture.withdrawn_revision_id);
    expect(persisted.pointer_available).toBe(false);
  });

  test("点词收词、保存位置、显式完成与历史回跳保持原修订", async ({ page, request }) => {
    const fixture = data();
    await signIn(page);
    await page.goto(href(fixture.lesson_id, fixture.revision_id));
    await expectBody(page, original);
    const word = original.pack.vocabulary[0];
    await page.getByRole("button", { name: word.headword, exact: true }).click();
    const collectButton = page.getByRole("button", { name: "加入词库", exact: true });
    await expect(collectButton).toBeEnabled();
    const collected = page.waitForResponse(
      (response) =>
        response.request().method() === "POST" &&
        new URL(response.url()).pathname.endsWith(`/${fixture.lesson_id}/vocabulary`)
    );
    await collectButton.click();
    const collectionResponse = await collected;
    expect(collectionResponse.status()).toBe(200);
    expect(collectionResponse.request().postDataJSON()).toEqual({
      revision_id: fixture.revision_id,
      segment_id: word.segment_id,
      token_ids: word.token_ids,
    });
    const savedWord = (await collectionResponse.json()) as { word_id: string };
    const sources = await getJson<{ sources: { revision_id: string; segment_id: string }[] }>(
      request,
      `/api/v1/vocabulary/${savedWord.word_id}/sources`
    );
    expect(sources.sources).toContainEqual(
      expect.objectContaining({ revision_id: fixture.revision_id, segment_id: word.segment_id })
    );

    const segment = original.pack.segments[1];
    const saved = page.waitForResponse(
      (response) =>
        response.request().method() === "PUT" &&
        new URL(response.url()).pathname.endsWith(`/${fixture.lesson_id}/progress`) &&
        response.request().postDataJSON().position_ms === segment.start_ms
    );
    await page
      .locator(`[id="lesson-line-${segment.id}"]`)
      .getByRole("button", { name: /^定位到 / })
      .click();
    expect((await saved).status()).toBe(200);
    await page.reload();
    await expectBody(page, original);
    await expect(page.getByRole("button", { name: /^继续学习 ·/ })).toBeVisible();
    const complete = page.waitForResponse(
      (response) =>
        response.request().method() === "POST" &&
        new URL(response.url()).pathname.endsWith(`/${fixture.lesson_id}/activity`)
    );
    await page.getByRole("button", { name: "标为学完", exact: true }).click();
    const completedResponse = await complete;
    expect(completedResponse.status()).toBe(200);
    expect(completedResponse.request().postDataJSON()).toMatchObject({
      revision_id: fixture.revision_id,
      event_type: "complete",
    });
    await expect(page.getByText("已学完", { exact: true })).toBeVisible();
    const finishedHistory = page.waitForResponse((response) => {
      const url = new URL(response.url());
      return (
        url.pathname.endsWith("/_history") &&
        url.searchParams.get("offset") === "0" &&
        response.status() === 200
      );
    });
    await page.goto("/history");
    const finishedPage = (await (await finishedHistory).json()) as { items: LessonHistoryItem[] };
    expect(finishedPage.items).toContainEqual(
      expect.objectContaining({
        lesson_id: fixture.lesson_id,
        revision_id: fixture.revision_id,
        completed: true,
      })
    );
    const row = page
      .getByRole("region", { name: "课程学习历史" })
      .locator(`a[href="${href(fixture.lesson_id, fixture.revision_id)}"]`);
    await expect(row).toContainText("已学完");
    await row.click();
    await expectBody(page, original);
    const progress = await getJson<LessonProgress>(
      request,
      `/api/v1/lessons/${fixture.lesson_id}/progress`
    );
    expect(progress).toMatchObject({
      revision_id: fixture.revision_id,
      position_ms: segment.start_ms,
      completed: true,
    });
  });
});
