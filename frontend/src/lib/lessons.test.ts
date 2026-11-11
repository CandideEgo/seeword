import { describe, expect, it } from "vitest";
import {
  lessonHref,
  lessonWordPieces,
  lessonYouTubeId,
  resolveLessonAnchor,
  type LessonPack,
} from "@/lib/lessons";

const pack: LessonPack = {
  title: "Welcome to Wikisource",
  media: {
    source_url: "https://www.youtube.com/watch?v=abcdefghijk",
    duration_ms: 49_453,
    access_mode: "provider_embed",
  },
  segments: [
    {
      id: "s03",
      start_ms: 12_000,
      end_ms: 16_000,
      text: "🎬 We digitize public domain books.",
      translation: "我们把公有领域的书籍数字化。",
      // Code-point offsets: the leading emoji is one code point, so "We" starts
      // at 2 rather than the 3 a UTF-16 index would produce.
      tokens: [
        { id: "w01", start_char: 2, end_char: 4, timing: null },
        { id: "w02", start_char: 5, end_char: 13, timing: { start_ms: 12_500, end_ms: 13_000 } },
        { id: "w03", start_char: 14, end_char: 20, timing: { start_ms: 13_602, end_ms: 14_000 } },
        { id: "w04", start_char: 21, end_char: 27, timing: { start_ms: 14_000, end_ms: 14_242 } },
        { id: "w05", start_char: 28, end_char: 33, timing: { start_ms: 14_242, end_ms: 15_000 } },
      ],
      vocabulary: [],
    } as LessonPack["segments"][number],
  ],
  vocabulary: [
    { headword: "public domain", gloss: "公有领域", segment_id: "s03", token_ids: ["w04", "w05"] },
  ],
  provenance: {
    media: { attribution: "a", basis: "b", evidence_url: "https://example.org/m" },
    transcript: { attribution: "a", basis: "b", evidence_url: "https://example.org/t" },
    translation: { attribution: "a", basis: "b", evidence_url: "https://example.org/x" },
    vocabulary: { attribution: "a", basis: "b", evidence_url: "https://example.org/v" },
  },
};

describe("lesson reader primitives", () => {
  it("slices text by Unicode code point offsets, not UTF-16 units", () => {
    const pieces = lessonWordPieces(pack.segments[0]);
    expect(pieces.map((piece) => piece.text).join("")).toBe(pack.segments[0].text);
    expect(pieces[0].token).toBeNull();
    expect(pieces.find((piece) => piece.token?.id === "w01")?.text).toBe("We");
    // The emoji is one code point but two UTF-16 units; the anchor after it must
    // still land on the right word.
    expect(pieces.find((piece) => piece.token?.id === "w03")?.text).toBe("public");
    expect(pieces.find((piece) => piece.token?.id === "w04")?.text).toBe("domain");
  });

  it("resolves a consecutive anchor to its own text and word timing", () => {
    const anchor = resolveLessonAnchor(pack, { segment_id: "s03", token_ids: ["w03", "w04"] });
    expect(anchor?.text).toBe("public domain");
    expect(anchor?.start_ms).toBe(13_602);
    expect(anchor?.end_ms).toBe(14_242);
  });

  it("falls back to the whole segment when any token is unaligned", () => {
    const anchor = resolveLessonAnchor(pack, { segment_id: "s03", token_ids: ["w01", "w02"] });
    expect(anchor?.start_ms).toBe(12_000);
    expect(anchor?.end_ms).toBe(16_000);
    expect(anchor?.text).toBe("We digitize");
  });

  it("rejects anchors that are not consecutive or name unknown tokens", () => {
    expect(resolveLessonAnchor(pack, { segment_id: "s03", token_ids: ["w01", "w03"] })).toBeNull();
    expect(resolveLessonAnchor(pack, { segment_id: "s03", token_ids: ["w99"] })).toBeNull();
    expect(resolveLessonAnchor(pack, { segment_id: "s99", token_ids: [] })).toBeNull();
  });

  it("pins deep links to a revision without carrying any media token", () => {
    const href = lessonHref("welcome-to-wikisource", "rev-1", {
      segment_id: "s03",
      token_ids: ["w04", "w05"],
    });
    const url = new URL(href, "https://example.test");
    expect(url.pathname).toBe("/lessons/welcome-to-wikisource");
    expect(url.searchParams.get("revision")).toBe("rev-1");
    expect(url.searchParams.getAll("token")).toEqual(["w04", "w05"]);
    expect(url.searchParams.has("token_type")).toBe(false);
    expect(href).not.toContain("Bearer");
  });

  it("only accepts an official YouTube watch page for the embed mode", () => {
    expect(lessonYouTubeId(pack.media)).toBe("abcdefghijk");
    expect(lessonYouTubeId({ ...pack.media, access_mode: "external_link" })).toBeNull();
    expect(
      lessonYouTubeId({ ...pack.media, source_url: "https://evil.test/watch?v=abcdefghijk" })
    ).toBeNull();
    expect(
      lessonYouTubeId({ ...pack.media, source_url: "https://user@youtube.com/watch?v=abcdefghijk" })
    ).toBeNull();
    expect(
      lessonYouTubeId({
        ...pack.media,
        source_url: "https://youtube.com/watch?v=abcdefghijk&v=zzzzzzzzzzz",
      })
    ).toBeNull();
  });
});
