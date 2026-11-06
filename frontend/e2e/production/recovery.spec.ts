import { test, expect } from "@playwright/test";
import { loginViaToken, registerUserViaApi, uniquePhone } from "../helpers";

let token = "";
test.beforeAll(async ({ request }) => {
  token = (await registerUserViaApi(request, uniquePhone())).token;
});
test.beforeEach(async ({ page }) => loginViaToken(page, token));

test("学习记录断网可重试，不能当作新用户", async ({ page }) => {
  // 改版后「继续观看」区域由首页 DiscoverRail 的 DiscoverContinue 承担：
  // 接口从 /learning/records 换成 /learning/continue，文案是「观看记录暂时未能加载」，
  // 「开始学习」入口已随旧首页一起下线——这里断言同一件行为：失败时给错误与重试，
  // 而不是一条假的空状态；重试成功后空列表就是静默不渲染。
  let fail = true;
  await page.route("**/api/v1/learning/continue**", (route) =>
    fail ? route.abort() : route.continue()
  );
  await page.goto("/");
  const recovery = page.getByRole("status").filter({ hasText: "观看记录暂时未能加载" });
  await expect(recovery).toBeVisible();
  await expect(page.getByTestId("continue-learning-rail")).toHaveCount(0);
  fail = false;
  await recovery.getByRole("button", { name: "重试" }).click();
  await expect(recovery).toHaveCount(0);
});

test("帮助页请求失败显示恢复入口", async ({ page }) => {
  await page.route("**/api/v1/feedback/mine", (route) => route.abort());
  await page.goto("/contact");
  await expect(page.getByText("反馈记录暂时未能加载")).toBeVisible();
  await expect(page.getByRole("heading", { name: "常见问题", exact: true })).toBeVisible();
});
