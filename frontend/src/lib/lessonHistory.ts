import { api } from "@/lib/api";
import { lessonHref, type LessonHistoryItem } from "@/lib/lessons";

export const LESSON_HISTORY_PAGE_SIZE = 20;

/** Never fall back to the current revision, even for an unavailable pointer. */
export function lessonHistoryHref(item: LessonHistoryItem) {
  return item.revision_id ? lessonHref(item.lesson_id, item.revision_id) : null;
}

export async function getLessonHistoryPage(offset: number, signal: AbortSignal) {
  // The history contract has no total. One look-ahead row avoids an empty last
  // page, without guessing a count or skipping the boundary item next time.
  const params = new URLSearchParams({
    offset: String(offset),
    limit: String(LESSON_HISTORY_PAGE_SIZE + 1),
  });
  const result = await api<{ items: LessonHistoryItem[] }>(`/api/v1/lessons/_history?${params}`, {
    signal,
    cache: "no-store",
  });
  return {
    items: result.items.slice(0, LESSON_HISTORY_PAGE_SIZE),
    hasMore: result.items.length > LESSON_HISTORY_PAGE_SIZE,
  };
}
