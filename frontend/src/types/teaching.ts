/** Teaching wire contract. Identity, grading and disclosure are server-owned. */
export const LEARNING_EVENT_SCHEMA_VERSION = 3;

export interface TeachingQuestionPayload {
  question_key: string;
  question_type: string;
  passage: string | null;
  question: string | null;
  options: Record<string, string> | null;
  source_url: string | null;
}

interface CardBase<K extends string, P> {
  schema_version: 1;
  card_id: string;
  session_id: string;
  item_id: string;
  session_revision: number;
  kind: K;
  payload: P;
}

export type TeachingCard =
  | CardBase<"question", TeachingQuestionPayload>
  | CardBase<"hint", { level: number; text: string }>
  | CardBase<"evidence", { quotes: { start: number; end: number; quote: string }[] }>
  | CardBase<
      "analysis",
      {
        correct_answer: string;
        option_analyses: Record<string, string>;
        analysis: { summary: string };
      }
    >
  | CardBase<"progress", { answered: number; correct: number; total: number; item_ids: string[] }>
  | CardBase<"summary", { attempt_count: number; status: string }>
  | CardBase<"status", { message: string; code: string | null }>;

export interface TeachingItem {
  id: string;
  question_key: string;
  content_revision_id: string;
  state: string;
  draft_answer: string | null;
  draft_revision: number;
  /** Progress is withheld (false / null) when this scope may not read answers. */
  answered: boolean;
  /** null means "not answered" or "not visible"; a boolean is the latest verdict. */
  correct: boolean | null;
}

export interface TeachingAttempt {
  id: string;
  item_id: string;
  attempt_no: number;
  answer: string | null;
  correct: boolean;
  role: string;
  answer_origin: string;
  server_graded: boolean;
  assistance_snapshot: Record<string, unknown>;
  occurred_at: string;
}

export interface TeachingSession {
  id: string;
  user_id: string;
  status: "active" | "completed" | "abandoned";
  revision: number;
  current_item_id: string | null;
  policy_version: string;
  items: TeachingItem[];
  attempts: TeachingAttempt[];
  cards: TeachingCard[];
  latest_run: TeachingRun | null;
  replayed: boolean;
  created_at: string;
  updated_at: string;
}

export interface TeachingContent {
  id: string;
  question_key: string;
  question_id: string | null;
  paper_id: string | null;
  title: string;
  number: number;
  level: string;
  status: "auto_verified";
}

export type TeachingRunStatus =
  "queued" | "running" | "succeeded" | "failed" | "cancelled" | "needs_retry";

export interface TeachingRun {
  id: string;
  run_id: string;
  session_id: string;
  status: TeachingRunStatus;
  last_sequence: number;
  cards: TeachingCard[];
  error_code: string | null;
}

export interface TeachingRunCreated {
  run_id: string;
  status: TeachingRunStatus;
  state_url: string;
  events_url: string;
}

export interface TeachingRunEvent {
  schema_version: number;
  run_id: string;
  sequence: number;
  session_revision: number;
  type: string;
  payload: { card?: TeachingCard; code?: string; message?: string; [key: string]: unknown };
}

export const EXTERNAL_SCOPES = [
  ["teaching:read", "读取教学题面与进度"],
  ["teaching:analysis:read", "读取已获准可见的解析"],
  ["teaching:analysis:reveal", "主动揭晓答案与解析"],
  ["teaching:attempts:submit", "提交辅助作答"],
  ["learning:feedback:write", "记录学习反馈"],
  ["learning:profile:read", "读取学习概况"],
  ["review:read", "读取复习任务"],
] as const;

export interface ExternalConnection {
  id: string;
  host_label: string;
  granted_scopes: string[];
  expires_at: string;
  revoked_at: string | null;
  created_at?: string;
}

export interface ExternalCredentialCreated {
  connection: ExternalConnection;
  token: string;
  expires_at: string;
}
