export interface LearningResourceLimits {
  lesson_ids: string[];
  word_ids: string[];
}

export interface LearningIntent {
  id: string;
  connection_id: string;
  host_label: string;
  action: "review" | "complete";
  resource: {
    word_id?: string;
    word?: string;
    lesson_id?: string;
    revision_id?: string;
    title?: string;
    available: boolean;
  };
  quality: number | null;
  expires_at: string;
  status: "pending" | "approved" | "consumed" | "expired" | "unavailable";
}

const dependencies: Record<string, string[]> = {
  "teaching:analysis:read": ["teaching:read"],
  "teaching:analysis:reveal": ["teaching:read"],
  "teaching:attempts:submit": ["teaching:read"],
  "learning:feedback:write": ["teaching:read"],
  "learning:profile:read": ["teaching:read"],
  "learning:vocabulary:write": ["materials:read"],
  "learning:progress:read": ["materials:read"],
  "learning:progress:write": ["materials:read", "learning:progress:read"],
  "review:write": ["review:read"],
};

export function toggleConnectionScope(
  current: string[],
  scope: string,
  enabled: boolean
): string[] {
  const next = new Set(current);
  if (enabled) {
    next.add(scope);
    for (const dependency of dependencies[scope] ?? []) next.add(dependency);
  } else {
    next.delete(scope);
    // Remove dependent capabilities too; never silently re-grant a removed root.
    let changed = true;
    while (changed) {
      changed = false;
      for (const selected of next) {
        if ((dependencies[selected] ?? []).some((required) => !next.has(required))) {
          next.delete(selected);
          changed = true;
        }
      }
    }
  }
  return [...next];
}

export function needsLearningResources(scopes: string[]): boolean {
  return scopes.some(
    (scope) =>
      scope === "materials:read" ||
      scope.startsWith("learning:progress:") ||
      scope === "learning:vocabulary:write" ||
      scope === "review:read" ||
      scope === "review:write"
  );
}

export function learningIntentSummary(intent: LearningIntent): string {
  if (intent.action === "review") {
    const word = intent.resource.word ?? "所选词语";
    return `记录「${word}」的复习结果：${intent.quality ?? "未提供"} / 5`;
  }
  return `将「${intent.resource.title ?? "所选课程"}」标为学完`;
}
