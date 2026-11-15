import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { searchLessonCatalog, LESSON_CATALOG_PAGE_SIZE } from "@/lib/lessonCatalog";

vi.mock("@/lib/api", () => ({ api: vi.fn() }));
beforeEach(() => vi.resetAllMocks());

describe("lesson catalog search contract", () => {
  it("reads the shared search endpoint with an explicit empty query and page size", async () => {
    const result = { items: [], total: 0, offset: 0, limit: LESSON_CATALOG_PAGE_SIZE };
    vi.mocked(api).mockResolvedValue(result);
    const signal = new AbortController().signal;

    expect(await searchLessonCatalog("", 0, signal)).toBe(result);
    expect(api).toHaveBeenCalledExactlyOnceWith("/api/v1/lessons/_search?q=&offset=0&limit=20", {
      signal,
      cache: "no-store",
    });
  });

  it("encodes and trims the submitted query without changing the fixed revision", async () => {
    const lesson = {
      lesson_id: "sample",
      revision_id: "old-revision",
      title: "Test",
      fingerprint_version: "v1",
      fingerprint: "fingerprint",
    };
    const result = { items: [lesson], total: 21, offset: 20, limit: 20 };
    vi.mocked(api).mockResolvedValue(result);
    const signal = new AbortController().signal;

    expect(await searchLessonCatalog("  中文 & phrase+  ", 20, signal)).toEqual(result);
    const [path, options] = vi.mocked(api).mock.calls[0];
    const url = new URL(path, "https://example.org");
    expect(url.pathname).toBe("/api/v1/lessons/_search");
    expect(url.searchParams.get("q")).toBe("中文 & phrase+");
    expect(url.searchParams.get("offset")).toBe("20");
    expect(options).toEqual({ signal, cache: "no-store" });
  });

  it("propagates search errors instead of fabricating an empty catalog", async () => {
    vi.mocked(api).mockRejectedValue(new Error("offline"));
    await expect(searchLessonCatalog("test", 0, new AbortController().signal)).rejects.toThrow(
      "offline"
    );
  });
});
