import type { TeachingCard, TeachingSession } from "@/types/teaching";

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Unknown versions and payloads never become executable UI. */
export function isTeachingCard(value: unknown): value is TeachingCard {
  if (!record(value) || value.schema_version !== 1 || !record(value.payload)) return false;
  if (
    typeof value.card_id !== "string" ||
    typeof value.session_id !== "string" ||
    typeof value.item_id !== "string" ||
    !Number.isSafeInteger(value.session_revision)
  )
    return false;
  const p = value.payload;
  switch (value.kind) {
    case "question":
      return (
        typeof p.question_key === "string" &&
        typeof p.question_type === "string" &&
        (p.passage === null || typeof p.passage === "string") &&
        (p.question === null || typeof p.question === "string") &&
        (p.options === null ||
          (record(p.options) && Object.values(p.options).every((v) => typeof v === "string")))
      );
    case "hint":
      return Number.isSafeInteger(p.level) && typeof p.text === "string";
    case "analysis":
      return (
        typeof p.correct_answer === "string" &&
        record(p.analysis) &&
        typeof p.analysis.summary === "string" &&
        record(p.option_analyses) &&
        Object.values(p.option_analyses).every((v) => typeof v === "string")
      );
    case "evidence":
      return (
        Array.isArray(p.quotes) &&
        p.quotes.every(
          (q) =>
            record(q) &&
            Number.isSafeInteger(q.start) &&
            Number.isSafeInteger(q.end) &&
            typeof q.quote === "string"
        )
      );
    case "progress":
      return (
        Number.isSafeInteger(p.answered) &&
        Number.isSafeInteger(p.correct) &&
        Number.isSafeInteger(p.total) &&
        Array.isArray(p.item_ids) &&
        p.item_ids.every((id) => typeof id === "string")
      );
    case "summary":
      return Number.isSafeInteger(p.attempt_count) && typeof p.status === "string";
    case "status":
      return typeof p.message === "string";
    default:
      return false;
  }
}

/** IDs are resource references; URL construction never accepts a remote URL. */
export function teachingHref(paperId: string | null, sessionId: string, itemId?: string | null) {
  const query = new URLSearchParams({ mode: "teach", teaching_session_id: sessionId });
  if (itemId) query.set("item", itemId);
  return `/practice/exams/${encodeURIComponent(paperId ?? "teaching")}?${query}`;
}

export function teachingResumeText(session: TeachingSession) {
  return `继续 SeeWord 教学会话 ${session.id}，题目 ${session.current_item_id ?? ""}。请通过已授权的 SeeWord 工具读取当前状态；提交为辅助作答。网页恢复：${teachingHref(null, session.id, session.current_item_id)}`;
}

export function isActiveRun(status: string) {
  return status === "queued" || status === "running";
}

export function mergeTeachingCard(
  cards: TeachingCard[],
  candidate: unknown,
  sessionId: string,
  revision: number
): TeachingCard[] {
  if (
    !isTeachingCard(candidate) ||
    candidate.session_id !== sessionId ||
    candidate.session_revision !== revision
  )
    return cards;
  return [...cards.filter((card) => card.card_id !== candidate.card_id), candidate];
}

/** Quiz progress as one short, self-describing label ("已答 2/4"). */
export function quizProgressLabel(card: { payload: { answered: number; total: number } } | null) {
  if (!card) return "";
  return `已答 ${card.payload.answered}/${card.payload.total}`;
}
