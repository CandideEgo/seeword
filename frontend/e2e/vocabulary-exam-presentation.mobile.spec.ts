import { test, expect, type Page } from "@playwright/test";

import examReading from "./fixtures/exam-reading.json";
const passage = examReading.bank;
const matchingPassage = examReading.matching;
const questions = [
  {
    id: "q1",
    number: 26,
    section: "reading_A",
    question_type: "cloze",
    passage,
    question: null,
    options: null,
  },
  {
    id: "q2",
    number: 27,
    section: "reading_A",
    question_type: "cloze",
    passage,
    question: null,
    options: null,
  },
  {
    id: "q3",
    number: 36,
    section: "reading_B",
    question_type: "matching",
    passage: matchingPassage,
    question: "Match this statement to a paragraph.",
    options: null,
  },
  {
    id: "q4",
    number: 46,
    section: "reading_C",
    question_type: "reading",
    passage: examReading.reading,
    question: "What does the author suggest?",
    options: {
      A: "Read the evidence carefully and compare all alternatives. ".repeat(6),
      B: "Ignore evidence.",
    },
  },
];
const wordNames = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota"];
const meanings = ["开始", "比较", "来源", "文章", "练习", "证据", "答案", "单词", "理解"];
const words = wordNames.map((word, i) => ({
  id: `w${i}`,
  word,
  translation: meanings[i],
  definition: null,
  part_of_speech: "n.",
  ipa: "test",
  mastery_level: "new",
  context_sentence: `We use ${word} in this sentence.`,
  video_id: null,
  subtitle_id: null,
}));
const preferences = { daily_new_target: 5, daily_review_target: 20, quota_min: 5, quota_max: 100 };

async function setup(page: Page) {
  const token = `e30.${Buffer.from(JSON.stringify({ sub: "test-user", exp: Math.floor(Date.now() / 1000) + 3600 })).toString("base64url")}.test`;
  await page.context().addCookies([
    {
      name: "seeword_token",
      value: token,
      url: test.info().project.use.baseURL ?? "http://localhost:3000",
    },
  ]);
  await page.addInitScript((value) => {
    localStorage.setItem("seeword_token", value);
    localStorage.setItem("seeword_coach_done", "true");
  }, token);
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    let json: unknown = {};
    if (path === "/api/v1/users/me")
      json = {
        id: "test-user",
        nickname: "Test",
        phone: "13800000000",
        onboarding_completed: true,
      };
    else if (path === "/api/v1/notifications/unread-count") json = { count: 0 };
    else if (path === "/api/v1/vocabulary/stats")
      json = { total: 9, due_count: 9, mastered_count: 0, learning_count: 4, reviewing_count: 0 };
    else if (path === "/api/v1/vocabulary" || path === "/api/v1/vocab-sets")
      json = { items: [], total: 0, has_more: false };
    else if (path === "/api/v1/vocabulary/daily-session")
      json = {
        training_preview: {
          new_words: words.slice(0, 5),
          review_words: words.slice(5),
          active_session_id: null,
        },
        new_words: words.slice(0, 5),
        review_words: words.slice(5),
        totals: { new_total: 5, due_total: 4 },
        preferences,
        today: { words_learned: 0, rounds: 0 },
      };
    else if (path === "/api/v1/vocabulary/sessions/current")
      json = { session: null, today: { words_learned: 0, rounds: 0 } };
    else if (path === "/api/v1/vocabulary/sessions")
      json = {
        session: {
          id: "round",
          kind: "daily",
          status: "active",
          target_count: 5,
          done_count: 0,
          correct_count: 0,
          items: words.slice(0, 5).map((word, i) => ({
            id: `item${i}`,
            vocabulary_id: word.id,
            sort_order: i,
            correct_streak: 0,
            wrong_in_round: false,
            status: "pending",
            word,
          })),
        },
        today: { words_learned: 0, rounds: 1 },
      };
    else if (path === "/api/v1/vocabulary/preferences") json = preferences;
    else if (path === "/api/v1/exams/fake-paper")
      json = {
        id: "fake-paper",
        level: "ky1",
        year: 2025,
        month: 12,
        set_no: 1,
        total_questions: 4,
        questions,
      };
    else if (path === "/api/v1/exams/fake-paper/attempts")
      json = {
        session_id: "attempt",
        paper_id: "fake-paper",
        mode: "paper_exam",
        question_count: 4,
        questions,
      };
    else if (path === "/api/v1/exams/attempts/attempt")
      json = {
        id: "attempt",
        paper_id: "fake-paper",
        mode: "paper_exam",
        submitted: true,
        question_count: 4,
        part_scores: { reading_A: { correct: 1, total: 2 } },
        results: questions.map((q, i) => ({
          ...q,
          question_id: q.id,
          user_answer: "A",
          correct: i === 0,
          correct_answer: i === 0 ? "A" : "B",
          explanation: "Compare the information in the passage.",
        })),
      };
    else if (path === "/api/v1/exams/wrong/redo")
      json = {
        session_id: "redo",
        mode: "wrong_redo",
        question_count: 3,
        questions: questions.slice(1),
      };
    else if (path === "/api/v1/exams")
      json = {
        items: [
          {
            id: "fake-paper",
            level: url.searchParams.get("level") ?? "cet4",
            year: 2025,
            month: 6,
            set_no: 1,
            total_questions: 4,
            last_session_id: url.searchParams.get("status") === "submitted" ? "attempt" : null,
            last_correct_count: 1,
            last_question_count: 4,
          },
        ],
        total: 55,
        available_years: [2025, 2024],
      };
    else if (path === "/api/v1/exam-pdfs")
      json = {
        items: [
          { slug: "tem4", title: "专四原卷", subject: "tem4", year: 2025 },
          { slug: "cet4", title: "四级原卷", subject: "cet4", year: 2024 },
        ],
      };
    await route.fulfill({ json });
  });
}
async function jump(page: Page, number: number) {
  await page.getByRole("button", { name: "答题卡", exact: true }).click();
  await page
    .getByRole("dialog", { name: "答题卡", exact: true })
    .getByRole("button", { name: new RegExp(`第 ${number} 题，`) })
    .click();
}

test("题组作答、滚动、缩放、提交失败重试和错题回顾", async ({ page, isMobile }) => {
  await setup(page);
  if (!isMobile) await page.setViewportSize({ width: 1600, height: 1200 });
  let submits = 0;
  let submittedAnswers: unknown[] = [];
  await page.route("**/api/v1/exams/attempts/attempt/submit", async (route) => {
    submits++;
    submittedAnswers = route.request().postDataJSON().answers;
    if (submits === 1)
      await route.fulfill({ status: 400, json: { code: "TEST_ERROR", message: "暂时无法交卷" } });
    else await route.fulfill({ json: { session_id: "attempt", correct_count: 1, total: 4 } });
  });
  await page.goto(
    "/practice/exams/fake-paper?return_to=%2Fpractice%2Fexams%3Flevel%3Dky1%26page%3D2"
  );
  await expect(page.getByRole("heading", { level: 1 })).not.toContainText("12 月");
  const workspace = page.getByTestId("exam-workspace");
  await expect(workspace).toBeVisible();
  if (!isMobile) await expect(workspace).toHaveAttribute("data-layout", "dual");
  else await expect(page.getByRole("region", { name: "原文", exact: true })).toBeVisible();
  for (const number of [26, 27, 36, 46]) {
    await jump(page, number);

    await page
      .getByTestId("exam-question")
      .filter({ has: page.getByRole("heading", { name: new RegExp(`^${number}\\.`) }) })
      .getByTestId("exam-option")
      .first()
      .click();
  }
  await expect(page.getByTestId("exam-progress")).toHaveText("已答 4/4");
  await jump(page, 26);
  await expect(
    page.getByTestId("exam-question").first().getByTestId("exam-option").first()
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "答题卡", exact: true }).click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(page.getByRole("button", { name: "答题卡", exact: true })).toBeFocused();
  if (!isMobile) {
    await jump(page, 36);
    const original = page.getByRole("region", { name: "原文", exact: true });
    await original.evaluate((el) => {
      el.scrollTop = 220;
    });
    await expect.poll(() => original.evaluate((el) => el.scrollTop)).toBe(220);
    await jump(page, 26);
    await jump(page, 36);
    await expect.poll(() => original.evaluate((el) => el.scrollTop)).toBe(220);
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(workspace).toHaveAttribute("data-layout", "switch");
    await page.getByRole("button", { name: "原文", exact: true }).click();
    await expect(original).toBeVisible();
    await page.getByRole("button", { name: "题目", exact: true }).click();
    await expect(
      page.getByTestId("exam-question").first().getByTestId("exam-option").first()
    ).toHaveAttribute("aria-pressed", "true");
    await page.setViewportSize({ width: 1600, height: 1200 });
    await expect(workspace).toHaveAttribute("data-layout", "dual");
    await expect.poll(() => original.evaluate((el) => el.scrollTop)).toBe(220);
  }
  await page.getByRole("button", { name: "交卷", exact: true }).click();
  await expect(page.getByRole("dialog")).toContainText("未答 0 题");
  await page.getByRole("button", { name: "确认交卷", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "暂时无法交卷" })).toBeVisible();
  await expect(page.getByTestId("exam-progress")).toHaveText("已答 4/4");
  await page.getByRole("button", { name: "重新交卷", exact: true }).click();
  await page.getByRole("button", { name: "确认交卷", exact: true }).click();
  await expect(page).toHaveURL(/result\/attempt/);
  expect(submittedAnswers).toHaveLength(4);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("答对 1 / 4 题");
  await expect(page.getByRole("listitem", { name: /题回顾/ })).toHaveCount(3);
  await expect(page.getByRole("link", { name: "返回真题目录" })).toHaveAttribute(
    "href",
    "/practice/exams?level=ky1&page=2"
  );
  await page.getByRole("link", { name: "重做错题", exact: true }).click();
  await expect(page.getByTestId("exam-workspace")).toBeVisible();
  await jump(page, 27);
  await expect(page.getByTestId("exam-option").first()).toBeVisible();
});

test("词汇真实队列、分组预览和直接开始", async ({ page }) => {
  await setup(page);
  await page.goto("/vocabulary");
  await expect(page.getByTestId("training-counts")).toHaveText("本轮复习 4 个 · 新词 5 个");
  await expect(
    page.getByRole("region", { name: "本轮词汇", exact: true }).getByRole("listitem")
  ).toHaveCount(6);
  await page.getByRole("button", { name: "展开本轮全部 9 个词" }).click();
  await expect(
    page.getByRole("region", { name: "本轮词汇", exact: true }).getByRole("listitem")
  ).toHaveCount(9);
  await page.getByRole("link", { name: "开始本轮", exact: true }).click();
  await expect(page).toHaveURL(/drill\?start=1/);
  await expect(page.getByText("认词", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /^开始训练/ })).toBeHidden();
});

test("词汇失败不会伪装成空词库或完成", async ({ page }) => {
  await setup(page);
  let failed = true;
  await page.route("**/api/v1/vocabulary/stats", async (route) => {
    if (failed)
      await route.fulfill({ status: 400, json: { code: "TEST_ERROR", message: "统计不可用" } });
    else
      await route.fulfill({
        json: { total: 9, due_count: 9, mastered_count: 0, learning_count: 4, reviewing_count: 0 },
      });
  });
  await page.goto("/vocabulary");
  await expect(page.getByText("学习队列加载失败", { exact: true })).toBeVisible();
  await expect(page.getByText("词库还是空的", { exact: true })).toBeHidden();
  await expect(page.getByRole("link", { name: "开始本轮", exact: true })).toBeHidden();
  failed = false;
  await page.getByRole("button", { name: /重试/ }).click();
  await expect(page.getByTestId("training-counts")).toBeVisible();
});

test("目录分页、状态、返回结果和 PDF 筛选", async ({ page }) => {
  await setup(page);
  await page.goto("/practice/exams?level=ky1&page=5");
  await expect(page.getByText("第 5 / 5 页", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "2025 年", exact: true })).toBeVisible();
  await page.getByRole("combobox", { name: "状态", exact: true }).selectOption("submitted");
  await expect(page).toHaveURL(/page=1/);
  await page.getByRole("link", { name: "看结果", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("答对 1 / 4 题");
  await page.getByRole("link", { name: "返回真题目录" }).click();
  await expect(page.getByRole("combobox", { name: "状态", exact: true })).toHaveValue("submitted");
  await page.getByText("原卷 PDF", { exact: true }).click();
  await page.getByRole("combobox", { name: "PDF 科目", exact: true }).selectOption("tem4");
  await expect(page.getByRole("link", { name: "专四原卷" })).toBeVisible();
  await expect(page.getByRole("link", { name: "四级原卷" })).toBeHidden();
});

test("长内容在窄屏、短视口、暗色和放大字号下可读可操作", async ({ page }, testInfo) => {
  await setup(page);
  for (const view of [
    { name: "desktop", width: 1600, height: 1200, dark: false, large: false },
    { name: "mobile-dark", width: 375, height: 667, dark: true, large: false },
    { name: "tablet-large", width: 1024, height: 1000, dark: false, large: true },
    { name: "desktop-short", width: 1600, height: 650, dark: false, large: false },
  ]) {
    await page.setViewportSize({ width: view.width, height: view.height });
    await page.emulateMedia({ colorScheme: view.dark ? "dark" : "light" });
    await page.goto("/practice/exams/fake-paper");
    await expect(page.getByTestId("exam-workspace")).toBeVisible();
    await page.evaluate((large) => {
      document.documentElement.style.fontSize = large ? "20px" : "16px";
    }, view.large);
    // ExamRunner 双栏判定：宽度 ≥900 且可用高度 ≥560。用 1024×1000 避开阈值边界
    // （1024×768 在大字号下高度预算会落到单栏），650 高的桌面档仍走单栏切换。
    const dual = view.name === "desktop" || view.name === "tablet-large";
    await expect(page.getByTestId("exam-workspace")).toHaveAttribute(
      "data-layout",
      dual ? "dual" : "switch"
    );
    await expect(page.getByRole("region", { name: "原文", exact: true })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath(`${view.name}.png`) });
    if (!dual) {
      const pane = page.getByRole("region", { name: "原文", exact: true });
      await pane.evaluate(() => document.getElementById("main-scroll")?.scrollTo(0, 500));
      await expect
        .poll(() => page.locator("#main-scroll").evaluate((el) => el.scrollTop))
        .toBe(500);
      // Native focus may scroll a sticky control before click; preserve the position at the switch itself.
      const [savedPosition] = await Promise.all([
        page.getByRole("button", { name: "查看题目", exact: true }).evaluate(
          (button) =>
            new Promise<number>((resolve) => {
              button.addEventListener(
                "click",
                () => resolve(document.getElementById("main-scroll")?.scrollTop ?? 0),
                { once: true, capture: true }
              );
            })
        ),
        page.getByRole("button", { name: "查看题目", exact: true }).click(),
      ]);
      await expect(page.getByTestId("exam-option").first()).toBeVisible();
      await page.getByRole("button", { name: "查看原文", exact: true }).click();

      await expect
        .poll(() => page.locator("#main-scroll").evaluate((el) => el.scrollTop))
        .toBe(savedPosition);
      await page.getByRole("button", { name: "查看题目", exact: true }).click();
    }
    await jump(page, 46);
    const option = page.getByTestId("exam-option").first();
    await option.click();
    await expect(option).toHaveAttribute("aria-pressed", "true");
    expect(
      await option.evaluate((el) => {
        const box = el.getBoundingClientRect();
        const hit = document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2);
        return hit === el || el.contains(hit);
      })
    ).toBe(true);
    expect(
      await page.locator("#main-scroll").evaluate((el) => el.scrollWidth <= el.clientWidth)
    ).toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`${view.name}-options.png`) });
  }
});
