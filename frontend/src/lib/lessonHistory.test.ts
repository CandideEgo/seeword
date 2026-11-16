import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import {
  getLessonHistoryPage,
  lessonHistoryHref,
  LESSON_HISTORY_PAGE_SIZE,
} from "@/lib/lessonHistory";
import type { LessonHistoryItem } from "@/lib/lessons";

vi.mock("@/lib/api", () => ({ api: vi.fn() }));

function item(index: number, available = true): LessonHistoryItem {
  return {
    lesson_id: `lesson-${index}`,
    revision_id: `revision-${index}`,
    title: available ? `Lesson ${index}` : null,
    available,
    pointer_available: available,
    position_ms: 1250,
    completed: true,
    watch_seconds: 3,
    updated_at: "2026-11-14T00:00:00Z",
  };
}

beforeEach(() => vi.resetAllMocks());

describe("lesson history fixed links", () => {
  it("retains the original revision even for a withdrawn pointer", () => {
    expect(lessonHistoryHref(item(1, false))).toBe("/lessons/lesson-1?revision=revision-1");
  });

  it("does not substitute a current revision when the pointer is missing", () => {
    expect(lessonHistoryHref({ ...item(1, false), revision_id: null })).toBeNull();
  });

  it("encodes lesson and revision identifiers", () => {
    const href = lessonHistoryHref({
      ...item(1),
      lesson_id: "lesson / 中文",
      revision_id: "rev+1",
    });
    const url = new URL(href!, "https://example.org");
    expect(decodeURIComponent(url.pathname)).toBe("/lessons/lesson / 中文");
    expect(url.searchParams.get("revision")).toBe("rev+1");
  });
});

describe("lesson history look-ahead pagination", () => {
  it("requests limit + 1 without relying on a total and retains personal facts", async () => {
    const rows = Array.from({ length: LESSON_HISTORY_PAGE_SIZE + 1 }, (_, index) =>
      item(index, index !== 0)
    );
    vi.mocked(api).mockResolvedValue({ items: rows });
    const signal = new AbortController().signal;
    const page = await getLessonHistoryPage(0, signal);

    expect(api).toHaveBeenCalledExactlyOnceWith("/api/v1/lessons/_history?offset=0&limit=21", {
      signal,
      cache: "no-store",
    });
    expect(page.hasMore).toBe(true);
    expect(page.items).toEqual(rows.slice(0, 20));
    expect(page.items[0]).toMatchObject({
      available: false,
      revision_id: "revision-0",
      completed: true,
      position_ms: 1250,
    });
  });

  it("uses page size, not look-ahead size, for the next offset", async () => {
    const boundary = item(20);
    vi.mocked(api)
      .mockResolvedValueOnce({
        items: [...Array.from({ length: 20 }, (_, index) => item(index)), boundary],
      })
      .mockResolvedValueOnce({ items: [boundary] });
    const signal = new AbortController().signal;
    await getLessonHistoryPage(0, signal);
    const second = await getLessonHistoryPage(LESSON_HISTORY_PAGE_SIZE, signal);

    expect(api).toHaveBeenLastCalledWith("/api/v1/lessons/_history?offset=20&limit=21", {
      signal,
      cache: "no-store",
    });
    expect(second).toEqual({ items: [boundary], hasMore: false });
  });

  it.each([0, 19, 20])("has no phantom next page for %s rows", async (count) => {
    const rows = Array.from({ length: count }, (_, index) => item(index));
    vi.mocked(api).mockResolvedValue({ items: rows });
    expect(await getLessonHistoryPage(0, new AbortController().signal)).toEqual({
      items: rows,
      hasMore: false,
    });
  });

  it("propagates failures for the component's retry state", async () => {
    vi.mocked(api).mockRejectedValue(new Error("offline"));
    await expect(getLessonHistoryPage(20, new AbortController().signal)).rejects.toThrow("offline");
  });
});
