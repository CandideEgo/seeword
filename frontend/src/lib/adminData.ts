/**
 * Real data-access layer for the admin console.
 *
 * Replaces `adminMock.ts` — every function calls the real backend API
 * via `adminApi`. The function signatures match the mock exports so
 * page components only need an import path change.
 */

import { adminApi } from "@/lib/adminApi";
import type {
  AdminAccount,
  AdminChannel,
  AdminLearningMetrics,
  AdminSettings,
  AdminStats,
  AdminUser,
  Paginated,
  Subtitle,
  SubtitleRevision,
  VideoAdmin,
  VideoDetail,
} from "@/types";

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------

export function getAdminStats(days?: number): Promise<AdminStats> {
  const params = days ? `?days=${days}` : "";
  return adminApi<AdminStats>(`/api/v1/admin/stats${params}`);
}

/**
 * A12 学习测量：激活/留存、事件质量与性能基线。
 * 口径随响应返回（`definitions`），页面只展示，不自行解释分母。
 */
export function getLearningMetrics(days?: number): Promise<AdminLearningMetrics> {
  const params = days ? `?days=${days}` : "";
  return adminApi<AdminLearningMetrics>(`/api/v1/admin/metrics/learning${params}`);
}

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------

export function listUsers(
  opts: {
    page?: number;
    page_size?: number;
    role?: string;
    keyword?: string;
  } = {}
): Promise<Paginated<AdminUser>> {
  const params = new URLSearchParams();
  if (opts.page) params.set("page", String(opts.page));
  if (opts.page_size) params.set("page_size", String(opts.page_size));
  if (opts.role) params.set("role", opts.role);
  if (opts.keyword) params.set("keyword", opts.keyword);
  const qs = params.toString();
  return adminApi<Paginated<AdminUser>>(`/api/v1/admin/users${qs ? `?${qs}` : ""}`);
}

export async function setUserBanned(id: string, banned: boolean): Promise<Partial<AdminUser>> {
  return adminApi<Partial<AdminUser>>(`/api/v1/admin/users/${id}/ban`, {
    method: "PATCH",
    body: JSON.stringify({ is_banned: banned }),
  });
}

export async function promoteUser(id: string, role: "user" | "admin"): Promise<Partial<AdminUser>> {
  return adminApi<Partial<AdminUser>>(`/api/v1/admin/users/${id}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

// ---------------------------------------------------------------------------
// Videos (existing admin endpoints in videos.py)
// ---------------------------------------------------------------------------

/** Check if the local GPU worker is online (heartbeat present in Redis). */
export function getWorkerStatus(): Promise<{ worker_online: boolean }> {
  return adminApi<{ worker_online: boolean }>("/api/v1/admin/worker-status");
}

/** Count UGC videos awaiting admin action: pending_processing + pending_review. */
export function getUgcPendingCount(): Promise<{
  pending_processing: number;
  pending_review: number;
  total: number;
}> {
  return adminApi<{
    pending_processing: number;
    pending_review: number;
    total: number;
  }>("/api/v1/videos/admin/pending-count");
}

/** Trigger GPU processing for a pending video. Worker must be online. */
export function startProcessing(id: string): Promise<VideoAdmin> {
  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}/start-processing`, {
    method: "POST",
  });
}

/** Re-dispatch finalize for a video stuck mid-pipeline (processing / ready_subtitles).
 * Clears the stale Redis lock and re-dispatches finalize_video (resume-safe). */
export function recoverVideo(id: string): Promise<VideoAdmin> {
  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}/recover`, {
    method: "POST",
  });
}

/** Resume a failed (error) video from the last completed pipeline step.
 *  If subtitles exist, jumps straight to finalize (skips transcription);
 *  otherwise resets to pending_processing for a fresh full run. */
export function retryVideo(id: string): Promise<VideoAdmin> {
  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}/retry`, {
    method: "POST",
  });
}

export function listVideos(
  opts: {
    page?: number;
    page_size?: number;
    status?: string;
    review_status?: string;
    keyword?: string;
    /** 质量门禁筛选: quality_warning | quality_blocked | low_coverage */
    quality?: string;
  } = {}
): Promise<Paginated<VideoAdmin>> {
  const params = new URLSearchParams();
  if (opts.page) params.set("page", String(opts.page));
  if (opts.page_size) params.set("page_size", String(opts.page_size));
  if (opts.status) params.set("status", opts.status);
  if (opts.review_status) params.set("review_status", opts.review_status);
  if (opts.keyword) params.set("keyword", opts.keyword);
  if (opts.quality) params.set("quality", opts.quality);
  const qs = params.toString();
  return adminApi<Paginated<VideoAdmin>>(`/api/v1/videos/admin${qs ? `?${qs}` : ""}`);
}

export function getVideoStatus(id: string): Promise<{
  status: string;
  video_url_720p: string | null;
  processing_step: string | null;
  processing_progress?: number;
  error_message?: string | null;
}> {
  return adminApi(`/api/v1/videos/admin/${id}/status`);
}

/** One-click seed: ensure cookies, seed, auto-publish on ready. Returns the new video id. */
export async function seedVideoFull(source_url: string): Promise<string> {
  const data = await adminApi<{ id: string }>("/api/v1/videos/seed-full", {
    method: "POST",
    body: JSON.stringify({ source_url }),
  });
  return data.id;
}

export async function updateVideo(id: string, patch: Partial<VideoAdmin>): Promise<VideoAdmin> {
  // Map admin-only fields to the VideoAdminUpdate schema
  const body: Record<string, unknown> = {};
  if (patch.title !== undefined) body.title = patch.title;
  // "" clears the Chinese title (backend normalizes it to NULL).
  if (patch.title_zh !== undefined) body.title_zh = patch.title_zh ?? "";
  if (patch.difficulty_level !== undefined) body.difficulty_level = patch.difficulty_level;
  if (patch.topic_tags !== undefined) body.topic_tags = patch.topic_tags;
  if (patch.is_official !== undefined) body.is_official = patch.is_official;
  if (patch.is_featured !== undefined) body.is_featured = patch.is_featured;
  if (patch.is_published !== undefined) body.is_published = patch.is_published;
  if (patch.show_on_homepage !== undefined) body.show_on_homepage = patch.show_on_homepage;
  if (patch.is_demo !== undefined) body.is_demo = patch.is_demo;
  if (patch.admin_notes !== undefined) body.admin_notes = patch.admin_notes;
  // ADR-0014: "" clears the channel assignment (backend maps it to NULL).
  if (patch.channel_ref !== undefined) body.channel_ref = patch.channel_ref ?? "";

  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deleteVideo(id: string): Promise<void> {
  await adminApi<void>(`/api/v1/videos/admin/${id}`, { method: "DELETE" });
}

export async function localizeVideo(id: string): Promise<VideoAdmin> {
  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}/localize`, {
    method: "POST",
  });
}

/** 下线视频（需求 §5.3）：隐藏 + 删除本地媒体释放空间，学习记录保留。 */
export async function takedownVideo(id: string): Promise<VideoAdmin> {
  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}/takedown`, {
    method: "POST",
  });
}

/** Re-run translation, optionally with a different engine. Use after a quality
 *  block to retry — same engine + same input would reproduce low coverage.
 *  Engines: glm | qwen | hy_mt2 | agnes | custom. Clears text_zh + quality_flag. */
export async function retranslateVideo(id: string, engine?: string): Promise<VideoAdmin> {
  const qs = engine ? `?engine=${encodeURIComponent(engine)}` : "";
  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}/retranslate${qs}`, {
    method: "POST",
  });
}

/** Quality report row (transcription/translation history across re-runs). */
export interface QualityReport {
  id: string;
  stage: string;
  passed: boolean;
  coverage_ratio: number | null;
  metrics: Record<string, unknown> | null;
  issues: string[] | null;
  segment_count: number | null;
  created_at: string | null;
}

/** All quality reports for a video (powers the video-detail quality panel). */
export async function getQualityReports(id: string): Promise<QualityReport[]> {
  return adminApi<QualityReport[]>(`/api/v1/videos/admin/${id}/quality-reports`);
}

// ---------------------------------------------------------------------------
// UGC review (admin approve / reject) — Phase 2A
// ---------------------------------------------------------------------------

/** Approve a UGC video pending review: freezes live subtitles + practice as
 * the public version and marks it published. */
export function approveReview(id: string): Promise<VideoAdmin> {
  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}/review/approve`, {
    method: "POST",
  });
}

/** Reject a UGC video pending review with a reason. The public keeps the last
 * approved snapshot (if any); the owner can edit & resubmit. */
export function rejectReview(id: string, reason: string): Promise<VideoAdmin> {
  return adminApi<VideoAdmin>(`/api/v1/videos/admin/${id}/review/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

// ---------------------------------------------------------------------------
// Subtitle & word-level editing (Phase 5 review/edit flow)
// ---------------------------------------------------------------------------

/** Fetch video detail with subtitles. Uses admin-scoped endpoint to bypass
 *  check_video_access (so admins can view UGC drafts they don't own). */
export function getVideoDetail(id: string): Promise<VideoDetail> {
  return adminApi<VideoDetail>(`/api/v1/videos/admin/${id}/detail`);
}

export interface SubtitlePatch {
  text_en?: string;
  text_zh?: string | null;
  start_time?: number;
  end_time?: number;
  grammar_note?: string | null;
  speaker?: string;
  /** Keep existing word_levels overrides when text_en changes (default false
   * resets them to the ECDICT baseline). */
  preserve_word_levels?: boolean;
}

export async function updateSubtitle(
  videoId: string,
  subtitleId: string,
  patch: SubtitlePatch
): Promise<Subtitle> {
  return adminApi<Subtitle>(`/api/v1/videos/admin/${videoId}/subtitles/${subtitleId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export interface SubtitleSplitPayload {
  split_time: number;
  text_before: string;
  text_after: string;
}

export async function splitSubtitle(
  videoId: string,
  subtitleId: string,
  payload: SubtitleSplitPayload
): Promise<Subtitle[]> {
  return adminApi<Subtitle[]>(`/api/v1/videos/admin/${videoId}/subtitles/${subtitleId}/split`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function mergeSubtitle(videoId: string, subtitleId: string): Promise<Subtitle> {
  return adminApi<Subtitle>(`/api/v1/videos/admin/${videoId}/subtitles/${subtitleId}/merge`, {
    method: "POST",
  });
}

export interface SubtitleCreatePayload {
  start_time: number;
  end_time: number;
  text_en?: string;
  text_zh?: string | null;
  speaker?: string | null;
}

/** Append a new subtitle row at the end of the video (canvas editor). The
 * English text may be empty initially (a placeholder). Admin only. */
export async function createSubtitle(
  videoId: string,
  payload: SubtitleCreatePayload
): Promise<Subtitle> {
  return adminApi<Subtitle>(`/api/v1/videos/admin/${videoId}/subtitles`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** Delete one subtitle and close the gap in sentence_index. Admin only. */
export async function deleteSubtitle(
  videoId: string,
  subtitleId: string
): Promise<{ deleted_id: string; remaining_count: number }> {
  return adminApi<{ deleted_id: string; remaining_count: number }>(
    `/api/v1/videos/admin/${videoId}/subtitles/${subtitleId}`,
    { method: "DELETE" }
  );
}

/** List edit revisions for one subtitle (newest first). Admin only. */
export async function listSubtitleRevisions(
  videoId: string,
  subtitleId: string,
  page = 1,
  pageSize = 50
): Promise<Paginated<SubtitleRevision>> {
  return adminApi<Paginated<SubtitleRevision>>(
    `/api/v1/videos/admin/${videoId}/subtitles/${subtitleId}/revisions?page=${page}&page_size=${pageSize}`
  );
}

/** Roll back a subtitle to the before-state of a prior edit. Admin only. */
export async function rollbackSubtitle(
  videoId: string,
  subtitleId: string,
  revisionId: string
): Promise<Subtitle> {
  return adminApi<Subtitle>(
    `/api/v1/videos/admin/${videoId}/subtitles/${subtitleId}/rollback/${revisionId}`,
    { method: "POST" }
  );
}

export interface ResegmentResult {
  before_count: number;
  after_count: number;
  translations_cleared: boolean;
  snapshot_id: string;
}

export async function resegmentSubtitles(videoId: string): Promise<ResegmentResult> {
  return adminApi<ResegmentResult>(`/api/v1/videos/admin/${videoId}/subtitles/resegment`, {
    method: "POST",
  });
}

export async function rollbackResegment(videoId: string): Promise<{ restored_count: number }> {
  return adminApi<{ restored_count: number }>(
    `/api/v1/videos/admin/${videoId}/subtitles/resegment/rollback`,
    { method: "POST" }
  );
}

export async function updateWordLevels(
  videoId: string,
  subtitleId: string,
  wordLevels: Record<string, string[]> | null
): Promise<Subtitle> {
  return adminApi<Subtitle>(`/api/v1/videos/admin/${videoId}/subtitles/${subtitleId}/word-levels`, {
    method: "PATCH",
    body: JSON.stringify({ word_levels: wordLevels }),
  });
}

export async function recomputeWordLevels(
  videoId: string,
  subtitleIds?: string[]
): Promise<{ subtitles_updated: number; exam_words_found: number }> {
  return adminApi<{ subtitles_updated: number; exam_words_found: number }>(
    `/api/v1/videos/admin/${videoId}/subtitles/word-levels/recompute`,
    {
      method: "POST",
      body: JSON.stringify(subtitleIds ? { subtitle_ids: subtitleIds } : {}),
    }
  );
}

// ---------------------------------------------------------------------------
// Platform settings (prototype 32 系统设置)
// ---------------------------------------------------------------------------

export function getAdminSettings(): Promise<AdminSettings> {
  return adminApi<AdminSettings>("/api/v1/admin/settings");
}

export function saveAdminSettings(patch: Partial<AdminSettings>): Promise<AdminSettings> {
  return adminApi<AdminSettings>("/api/v1/admin/settings", {
    method: "PUT",
    body: JSON.stringify(patch),
  });
}

export function listAdminAccounts(): Promise<AdminAccount[]> {
  return adminApi<AdminAccount[]>("/api/v1/admin/admins");
}

// ---------------------------------------------------------------------------
// Feedback & announcements (Stage 4)
// ---------------------------------------------------------------------------

export interface AdminFeedback {
  id: string;
  user_id: string;
  user_name: string | null;
  category: string;
  content: string;
  contact: string | null;
  status: string;
  admin_reply: string | null;
  handled_by: string | null;
  created_at: string;
  updated_at: string;
}

export async function listAdminFeedback(
  status?: string,
  page = 1,
  pageSize = 50
): Promise<Paginated<AdminFeedback>> {
  const qs = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (status) qs.set("status", status);
  return adminApi<Paginated<AdminFeedback>>(`/api/v1/admin/feedback?${qs}`);
}

export async function updateAdminFeedback(
  id: string,
  patch: { status?: string; admin_reply?: string }
): Promise<AdminFeedback> {
  return adminApi<AdminFeedback>(`/api/v1/admin/feedback/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export async function broadcastAnnouncement(payload: {
  title: string;
  message: string;
  related_url?: string | null;
}): Promise<{ notified_count: number; title: string; message: string }> {
  return adminApi(`/api/v1/admin/announcements`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Channels (ADR-0014 — official curated channels)
// ---------------------------------------------------------------------------

export interface ChannelUpsertPayload {
  name: string;
  slug?: string;
  description?: string | null;
  cover_url?: string | null;
  upstream_channel_id?: string | null;
  sort_order?: number;
  is_visible?: boolean;
}

export function listChannelsAdmin(): Promise<{ items: AdminChannel[] }> {
  return adminApi<{ items: AdminChannel[] }>(`/api/v1/channels/admin/all`);
}

export function createChannel(
  payload: ChannelUpsertPayload
): Promise<{ id: string; slug: string }> {
  return adminApi<{ id: string; slug: string }>(`/api/v1/channels/admin`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateChannel(
  id: string,
  patch: Partial<ChannelUpsertPayload>
): Promise<{ id: string; slug: string }> {
  return adminApi<{ id: string; slug: string }>(`/api/v1/channels/admin/${id}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function deleteChannel(id: string): Promise<void> {
  return adminApi<void>(`/api/v1/channels/admin/${id}`, { method: "DELETE" });
}
