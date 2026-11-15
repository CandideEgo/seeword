import { describe, expect, it } from "vitest";
import {
  learningIntentSummary,
  needsLearningResources,
  toggleConnectionScope,
  type LearningIntent,
} from "./learningConnections";

const intent: LearningIntent = {
  id: "intent",
  connection_id: "connection",
  host_label: "My assistant",
  action: "review",
  resource: { word_id: "word", word: "bank", available: true },
  quality: 0,
  expires_at: "2026-11-15T12:00:00Z",
  status: "pending",
};

describe("scoped learning connections", () => {
  it("adds necessary read scopes without forcing teaching access", () => {
    const scopes = toggleConnectionScope([], "learning:progress:write", true);
    expect(scopes).toEqual(["learning:progress:write", "materials:read", "learning:progress:read"]);
    expect(scopes).not.toContain("teaching:read");
  });
  it("removes all dependent course capabilities with their read root", () => {
    const scopes = [
      "materials:read",
      "learning:vocabulary:write",
      "learning:progress:read",
      "learning:progress:write",
      "review:read",
    ];
    expect(toggleConnectionScope(scopes, "materials:read", false)).toEqual(["review:read"]);
  });
  it("keeps review and teaching families separately constrained", () => {
    expect(toggleConnectionScope([], "review:write", true)).toEqual([
      "review:write",
      "review:read",
    ]);
    expect(toggleConnectionScope(["review:read", "review:write"], "review:read", false)).toEqual(
      []
    );
    expect(toggleConnectionScope([], "teaching:attempts:submit", true)).toEqual([
      "teaching:attempts:submit",
      "teaching:read",
    ]);
  });
  it("requires explicit resources for new learning and existing review reads", () => {
    expect(needsLearningResources(["materials:read"])).toBe(true);
    expect(needsLearningResources(["review:read"])).toBe(true);
    expect(needsLearningResources(["learning:progress:read"])).toBe(true);
    expect(needsLearningResources(["teaching:read"])).toBe(false);
  });
  it("shows zero as an actual review value, not a missing result", () => {
    expect(learningIntentSummary(intent)).toBe("记录「bank」的复习结果：0 / 5");
    expect(learningIntentSummary({ ...intent, quality: null })).toContain("未提供");
  });
  it("describes explicit completion rather than mastery", () => {
    const text = learningIntentSummary({
      ...intent,
      action: "complete",
      resource: { lesson_id: "lesson", title: "River study", available: true },
      quality: null,
    });
    expect(text).toBe("将「River study」标为学完");
    expect(text).not.toContain("掌握");
  });
});
