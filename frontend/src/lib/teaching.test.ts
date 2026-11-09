import { describe, expect, it } from "vitest";
import { isTeachingCard, mergeTeachingCard, teachingHref } from "@/lib/teaching";
import type { TeachingCard } from "@/types/teaching";

const card: TeachingCard = {
  schema_version: 1,
  card_id: "c1",
  session_id: "t1",
  item_id: "i1",
  session_revision: 5,
  kind: "hint",
  payload: { level: 1, text: "找表示转折的词。" },
};

describe("teaching disclosure-safe UI", () => {
  it("does not merge cards from a stale session revision or a different user resource", () => {
    expect(mergeTeachingCard([], { ...card, session_revision: 4 }, "t1", 5)).toEqual([]);
    expect(mergeTeachingCard([], { ...card, session_id: "other" }, "t1", 5)).toEqual([]);
    expect(
      mergeTeachingCard([card], { ...card, payload: { level: 1, text: "更新" } }, "t1", 5)
    ).toHaveLength(1);
  });

  it("rejects unknown versions, arbitrary actions and malformed card payloads", () => {
    expect(isTeachingCard({ ...card, schema_version: 99 })).toBe(false);
    expect(
      isTeachingCard({ ...card, kind: "execute", payload: { url: "javascript:alert(1)" } })
    ).toBe(false);
    expect(isTeachingCard({ ...card, payload: { level: 1, text: { html: "untrusted" } } })).toBe(
      false
    );
  });

  it("encodes resource identifiers into a same-site restore link", () => {
    const href = teachingHref("https://attacker.test/", "t?token=bad", "i&answer=B");
    expect(href.startsWith("/practice/exams/")).toBe(true);
    expect(new URL(href, "https://seeword.test").origin).toBe("https://seeword.test");
    const query = new URL(href, "https://seeword.test").searchParams;
    expect(query.get("teaching_session_id")).toBe("t?token=bad");
    expect(query.has("token")).toBe(false);
    expect(query.has("answer")).toBe(false);
  });
});

describe("quiz progress card", () => {
  const progress: TeachingCard = {
    schema_version: 1,
    card_id: "c-progress",
    session_id: "t1",
    item_id: "i1",
    session_revision: 5,
    kind: "progress",
    payload: { answered: 2, correct: 1, total: 4, item_ids: ["i1", "i2", "i3", "i4"] },
  };

  it("accepts a well-formed progress card and rejects malformed counters", () => {
    expect(isTeachingCard(progress)).toBe(true);
    expect(isTeachingCard({ ...progress, payload: { ...progress.payload, total: "4" } })).toBe(
      false
    );
    expect(
      isTeachingCard({ ...progress, payload: { ...progress.payload, item_ids: ["i1", 2] } })
    ).toBe(false);
  });
});
