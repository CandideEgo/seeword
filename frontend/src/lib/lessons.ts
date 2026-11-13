import { api } from "@/lib/api";
import { adminApi } from "@/lib/adminApi";

export type LessonAccessMode = "external_link" | "provider_embed";
export type LessonRevisionStatus = "candidate" | "published" | "withdrawn";

interface LessonTimeRange {
  start_ms: number;
  end_ms: number;
}

export interface LessonToken {
  id: string;
  start_char: number;
  end_char: number;
  timing: LessonTimeRange | null;
}

export interface LessonSegment extends LessonTimeRange {
  id: string;
  text: string;
  translation: string;
  speaker?: string | null;
  tokens: LessonToken[];
}

export interface LessonVocabulary {
  headword: string;
  gloss: string;
  segment_id: string;
  token_ids: string[];
}

interface LessonProvenance {
  attribution: string;
  basis: string;
  evidence_url: string;
}

export interface LessonPack {
  title: string;
  media: { source_url: string; duration_ms: number; access_mode: LessonAccessMode };
  segments: LessonSegment[];
  vocabulary: LessonVocabulary[];
  provenance: {
    media: LessonProvenance;
    transcript: LessonProvenance;
    translation: LessonProvenance;
    vocabulary: LessonProvenance;
    changes?: string | null;
  };
}

export interface LessonSummary {
  lesson_id: string;
  title: string;
  revision_id: string;
  access_mode: LessonAccessMode;
}

export interface LessonDetail {
  lesson_id: string;
  revision_id: string;
  fingerprint: string;
  fingerprint_version: string;
  pack: LessonPack;
  permissions: { model_processing: boolean; tutor_enabled: boolean; vocabulary_enabled: boolean };
}

export interface LessonProgress {
  revision_id: string | null;
  position_ms: number | null;
  completed: boolean;
  watch_seconds: number;
  /** False when the revision the pointer names can no longer be opened. */
  pointer_available?: boolean;
}

export interface LessonHistoryItem extends LessonProgress {
  lesson_id: string;
  title: string | null;
  available: boolean;
  updated_at: string;
}

export interface LessonAnchor {
  segment_id: string;
  token_ids: string[];
}

export interface LessonVocabularySource extends LessonAnchor, LessonTimeRange {
  lesson_id: string;
  revision_id: string;
  available: boolean;
}

export type ReviewUse = "site_display" | "model_processing" | "external_redistribution";
export type ReviewUses = Record<ReviewUse, { approved: boolean; evidence: string }>;

export interface LessonReview {
  source_commit: string;
  uses: ReviewUses;
  reviewer_id: string;
  reviewed_at: string;
  review_sha256: string;
}

export interface AdminLessonRevision {
  revision_id: string;
  title: string;
  fingerprint: string;
  fingerprint_version: string;
  status: LessonRevisionStatus;
  review: LessonReview | null;
}

export interface AdminLesson {
  lesson_id: string;
  current_revision_id: string | null;
  revisions: AdminLessonRevision[];
}

export interface AdminLessonDetail extends AdminLessonRevision {
  lesson_id: string;
  pack: LessonPack | null;
}

export const lessonApiPath = (id: string) => `/api/v1/lessons/${encodeURIComponent(id)}`;
export const adminLessonRevisionApiPath = (id: string, revision: string) =>
  `/api/v1/admin/lessons/${encodeURIComponent(id)}/revisions/${encodeURIComponent(revision)}`;

export function lessonHref(id: string, revision?: string | null, anchor?: LessonAnchor) {
  const query = new URLSearchParams();
  if (revision) query.set("revision", revision);
  if (anchor) {
    query.set("segment", anchor.segment_id);
    for (const token of anchor.token_ids) query.append("token", token);
  }
  return `/lessons/${encodeURIComponent(id)}${query.size ? `?${query}` : ""}`;
}

export function getLesson(lessonId: string, revision: string | null, signal: AbortSignal) {
  const path = lessonApiPath(lessonId);
  return api<LessonDetail>(revision ? `${path}/revisions/${encodeURIComponent(revision)}` : path, {
    signal,
    cache: "no-store",
  });
}

export interface LessonState {
  lesson_id: string;
  revision_id: string;
  title: string;
  access_mode: LessonAccessMode;
  fingerprint: string;
  fingerprint_version: string;
  permissions: LessonDetail["permissions"];
}

/** What the reader polls: a few hundred bytes instead of the whole pack. */
export function getLessonState(lessonId: string, revision: string | null, signal: AbortSignal) {
  const query = revision ? `?revision=${encodeURIComponent(revision)}` : "";
  return api<LessonState>(`${lessonApiPath(lessonId)}/_state${query}`, {
    signal,
    cache: "no-store",
  });
}

export function getLessonProgress(lessonId: string, signal: AbortSignal) {
  return api<LessonProgress>(`${lessonApiPath(lessonId)}/progress`, { signal, cache: "no-store" });
}

export function collectLessonWord(id: string, revision: string, anchor: LessonAnchor) {
  return api<{ word_id: string; word: string; source: LessonVocabularySource }>(
    `${lessonApiPath(id)}/vocabulary`,
    {
      method: "POST",
      body: JSON.stringify({
        revision_id: revision,
        segment_id: anchor.segment_id,
        token_ids: anchor.token_ids,
      }),
    }
  );
}

export function writeLessonProgress(lessonId: string, revisionId: string, position: number) {
  return api<LessonProgress>(`${lessonApiPath(lessonId)}/progress`, {
    method: "PUT",
    body: JSON.stringify({ revision_id: revisionId, position_ms: position }),
    keepalive: true,
  });
}

export function recordLessonActivity(
  lessonId: string,
  revisionId: string,
  eventId: string,
  event: { event_type: "watch_time"; delta_s: number } | { event_type: "complete" }
) {
  return api<LessonProgress>(`${lessonApiPath(lessonId)}/activity`, {
    method: "POST",
    body: JSON.stringify({ revision_id: revisionId, event_id: eventId, ...event }),
    keepalive: true,
  });
}

export function getLessonAvailability(admin: boolean) {
  const path = "/api/v1/lessons/_status";
  return admin
    ? adminApi<{ enabled: boolean }>(path)
    : api<{ enabled: boolean }>(path, { cacheTtlMs: 15_000 });
}

export function adminLessonAction(
  id: string,
  revision: string,
  action: "review" | "publish" | "withdraw",
  body: unknown
) {
  return adminApi<AdminLessonDetail>(`${adminLessonRevisionApiPath(id, revision)}/${action}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function lessonWordPieces(segment: LessonSegment) {
  // SLCS offsets count Unicode code points. Preserve whitespace and punctuation
  // between anchors even when JavaScript would use two units for a character.
  const codePoints = Array.from(segment.text);
  const pieces: { text: string; token: LessonToken | null }[] = [];
  let cursor = 0;
  for (const token of segment.tokens) {
    if (cursor < token.start_char) {
      pieces.push({ text: codePoints.slice(cursor, token.start_char).join(""), token: null });
    }
    pieces.push({
      text: codePoints.slice(token.start_char, token.end_char).join(""),
      token,
    });
    cursor = token.end_char;
  }
  if (cursor < codePoints.length) {
    pieces.push({ text: codePoints.slice(cursor).join(""), token: null });
  }
  return pieces;
}

export function resolveLessonAnchor(pack: LessonPack, anchor: LessonAnchor) {
  const segment = pack.segments.find((item) => item.id === anchor.segment_id);
  if (!segment) return null;
  const firstIndex = segment.tokens.findIndex((token) => token.id === anchor.token_ids[0]);
  const tokens = segment.tokens.slice(firstIndex, firstIndex + anchor.token_ids.length);
  if (
    anchor.token_ids.length &&
    (firstIndex < 0 ||
      tokens.length !== anchor.token_ids.length ||
      !tokens.every((token, index) => token.id === anchor.token_ids[index]))
  ) {
    return null;
  }
  const first = tokens[0];
  const last = tokens.at(-1);
  const aligned = tokens.every((token) => token.timing !== null);
  const text =
    first && last
      ? Array.from(segment.text).slice(first.start_char, last.end_char).join("")
      : segment.text;
  return {
    segment,
    text,
    start_ms: (aligned ? first?.timing?.start_ms : undefined) ?? segment.start_ms,
    end_ms: (aligned ? last?.timing?.end_ms : undefined) ?? segment.end_ms,
  };
}

export function lessonYouTubeId(media: LessonPack["media"]) {
  if (media.access_mode !== "provider_embed") return null;
  try {
    const url = new URL(media.source_url);
    if (
      url.protocol !== "https:" ||
      url.username ||
      url.password ||
      !["www.youtube.com", "youtube.com"].includes(url.host) ||
      url.pathname !== "/watch"
    ) {
      return null;
    }
    const ids = url.searchParams.getAll("v");
    return ids.length === 1 && /^[A-Za-z0-9_-]{11}$/.test(ids[0]) ? ids[0] : null;
  } catch {
    return null;
  }
}
