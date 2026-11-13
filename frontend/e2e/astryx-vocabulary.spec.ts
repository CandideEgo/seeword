import { expect, test } from "@playwright/test";
import { loginViaToken, registerUserViaApi, uniquePhone } from "./helpers";

const libraryUrl = "/vocabulary?tab=library&sub=words";

/** Real API fixtures: no mocked auth, vocabulary, or filter responses. */
test("Astryx 词汇控件保留搜索、筛选、分页与 URL 恢复", async ({ page, request }) => {
  const { token } = await registerUserViaApi(request, uniquePhone());
  const headers = { Authorization: `Bearer ${token}` };
  const words = [
    "habit",
    "ability",
    "balance",
    "bridge",
    "careful",
    "choice",
    "culture",
    "daily",
    "detail",
    "effort",
    "energy",
    "example",
    "focus",
    "future",
    "garden",
    "growth",
    "health",
    "honest",
    "idea",
    "journey",
    "knowledge",
    "language",
    "memory",
    "nature",
    "ocean",
    "patient",
  ];
  for (const word of words) {
    const response = await request.post(`/api/v1/vocabulary?word=${word}`, { headers });
    expect(response.ok(), `seed ${word}: ${await response.text()}`).toBeTruthy();
  }
  await loginViaToken(page, token);
  await page.goto(libraryUrl);
  const views = page.getByRole("navigation", { name: "词汇视图", exact: true });
  await expect(views.getByRole("link", { name: "词库", exact: true })).toHaveAttribute(
    "aria-current",
    "true"
  );
  await expect(page.getByRole("searchbox", { name: "搜索单词" })).toBeVisible();
  await expect(page.getByRole("button", { name: "上一页", exact: true })).toBeDisabled();

  await page.getByRole("button", { name: "下一页", exact: true }).click();
  await expect(page.getByText("第 2 / 2 页 · 共 26 词", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "下一页", exact: true })).toBeDisabled();

  const searchResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === "/api/v1/vocabulary" && url.searchParams.get("q") === "habit";
  });
  await page.getByRole("searchbox", { name: "搜索单词" }).fill("habit");
  const searched = await (await searchResponse).json();
  expect(searched.total).toBe(1);
  expect(searched.items[0].word).toBe("habit");
  await expect(page.getByRole("button", { name: "下一页", exact: true })).toHaveCount(0);

  const mastery = page.getByRole("radiogroup", { name: "掌握程度", exact: true });
  const masteredResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/vocabulary" &&
      url.searchParams.get("q") === "habit" &&
      url.searchParams.get("mastery") === "mastered"
    );
  });
  await mastery.getByRole("radio", { name: "已掌握", exact: true }).click();
  expect((await (await masteredResponse).json()).total).toBe(0);
  await expect(page.getByText("未找到匹配“habit”的单词", { exact: true })).toBeVisible();

  await mastery.getByRole("radio", { name: "新词", exact: true }).focus();
  const dueResponse = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return (
      url.pathname === "/api/v1/vocabulary" &&
      url.searchParams.get("due_only") === "true" &&
      url.searchParams.get("mastery") === "new" &&
      url.searchParams.get("q") === "habit"
    );
  });
  await page.keyboard.press("Space");
  await expect(mastery.getByRole("radio", { name: "新词", exact: true })).toBeChecked();
  await page
    .getByRole("radiogroup", { name: "复习范围", exact: true })
    .getByRole("radio", { name: "待复习", exact: true })
    .click();
  expect((await (await dueResponse).json()).items[0].word).toBe("habit");

  await page.reload();
  await expect(views.getByRole("link", { name: "词库", exact: true })).toHaveAttribute(
    "aria-current",
    "true"
  );
  await expect(
    page
      .getByRole("navigation", { name: "词库内容", exact: true })
      .getByRole("link", { name: "全部单词", exact: true })
  ).toHaveAttribute("aria-current", "true");
  await expect(page.getByRole("searchbox", { name: "搜索单词" })).toHaveValue("");
});

for (const selectedTheme of ["dark", "light"] as const) {
  test(`Astryx 卸载后原生 UI 保留站内 ${selectedTheme} 偏好而非系统主题`, async ({
    page,
    request,
  }) => {
    const { token } = await registerUserViaApi(request, uniquePhone());
    await page.emulateMedia({ colorScheme: selectedTheme === "dark" ? "light" : "dark" });
    await page.addInitScript((theme) => localStorage.setItem("theme", theme), selectedTheme);
    await page.goto("/login");
    await expect(page.locator("html")).toHaveCSS("color-scheme", selectedTheme);
    await loginViaToken(page, token);
    await expect(page.locator("html")).toHaveCSS("color-scheme", selectedTheme);
    await page.goto(libraryUrl);
    await expect(page.locator(".user-ui [data-astryx-theme='neutral']")).toHaveCount(1);
    await expect(page.locator("html")).toHaveAttribute("data-theme", selectedTheme);
    await expect(page.getByRole("searchbox", { name: "搜索单词" })).toHaveCSS(
      "color",
      selectedTheme === "dark" ? "rgb(245, 245, 247)" : "rgb(29, 29, 31)"
    );

    // Client-side navigation unmounts Astryx, but the app still owns the native UI mode.
    await page.locator('a[href="/"]:visible').first().click();
    await expect(page).toHaveURL("/");
    await expect(page.locator("html")).not.toHaveAttribute("data-astryx-theme");
    await expect(page.locator("html")).not.toHaveAttribute("data-theme");
    await expect(page.locator("html")).toHaveCSS("color-scheme", selectedTheme);
    await page.goto("/admin/login");
    await expect(page.locator("[data-astryx-theme]")).toHaveCount(0);
    await expect(page.locator("html")).toHaveCSS("color-scheme", selectedTheme);
  });
}

test("跨页词汇入口使用链接，方向键不触发路由跳转", async ({ page, request }) => {
  const { token } = await registerUserViaApi(request, uniquePhone());
  await loginViaToken(page, token);
  await page.goto("/vocabulary");
  const views = page.getByRole("navigation", { name: "词汇视图", exact: true });
  await views.getByRole("link", { name: "复习", exact: true }).focus();
  await page.keyboard.press("ArrowRight");
  await expect(page).toHaveURL("/vocabulary");
  await views.getByRole("link", { name: "词库", exact: true }).press("Enter");
  await expect(page).toHaveURL("/vocabulary/sets");

  await page.goto(libraryUrl);
  const content = page.getByRole("navigation", { name: "词库内容", exact: true });
  await content.getByRole("link", { name: "全部单词", exact: true }).focus();
  await page.keyboard.press("ArrowLeft");
  await expect(page).toHaveURL(libraryUrl);
  await content.getByRole("link", { name: "视频集合", exact: true }).press("Enter");
  await expect(page).toHaveURL("/vocabulary/sets");
});
