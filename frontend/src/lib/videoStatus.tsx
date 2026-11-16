/**
 * Single source of truth for video status badges, processing step labels,
 * and review-status badges.
 *
 * Previously scattered across 4 files with conflicting values:
 *   - watch/[id]/page.tsx STEP_LABELS ("提取视频信息…")
 *   - my-videos/page.tsx STEP_LABELS ("提取音频") ← CONFLICT
 *   - VideoStatus.tsx STATUS_CONFIG (5 keys)
 *   - my-videos/page.tsx STATUS_META (7 keys, different labels/colors)
 *
 * All consumers now import from this module.
 */

import { CheckCircle2, AlertCircle, Loader2, Clock } from "lucide-react";

// ---------------------------------------------------------------------------
// Processing step labels (backend step key → Chinese label)
// ---------------------------------------------------------------------------

/** Step labels shown during video processing. Uses the "…" suffix style
 *  for the watch page (progress indicator) but consumers can strip it. */
export const STEP_LABELS: Record<string, string> = {
  extracting: "提取视频信息…",
  transcribing: "语音转录…",
  translating: "字幕翻译…",
  annotating: "标注考试词汇…",
  prewarm_notes: "预热词注释…",
  classifying: "智能分类…",
  downloading: "下载视频…",
  transcoding: "视频转码…",
};

/** Short variant without trailing "…" — used in list/table contexts where
 *  space is tight. */
export const STEP_LABELS_SHORT: Record<string, string> = {
  extracting: "提取视频信息",
  transcribing: "语音转录",
  translating: "字幕翻译",
  annotating: "标注考级",
  prewarm_notes: "预热笔记",
  classifying: "智能分类",
  downloading: "下载视频",
  transcoding: "转码",
};

// ---------------------------------------------------------------------------
// Processing status badges (raw Video.status → badge config)
// ---------------------------------------------------------------------------

export interface StatusBadgeConfig {
  label: string;
  className: string;
  icon: React.ElementType;
}

/** Badge config for raw processing pipeline statuses. Covers all statuses
 *  that VideoStatus.tsx previously handled. */
export const PROCESSING_STATUS_CONFIG: Record<string, StatusBadgeConfig> = {
  pending_processing: {
    label: "待处理",
    className: "bg-surface-card text-muted",
    icon: Clock,
  },
  processing: {
    label: "处理中",
    className: "bg-warning-soft text-warning",
    icon: Loader2,
  },
  ready_subtitles: {
    label: "视频处理中",
    className: "bg-warning-soft text-warning",
    icon: Loader2,
  },
  ready: {
    label: "就绪",
    className: "bg-success-soft text-success",
    icon: CheckCircle2,
  },
  error: {
    label: "失败",
    className: "bg-red-soft text-error",
    icon: AlertCircle,
  },
};

// ---------------------------------------------------------------------------
// Review status badges are NOT defined here: the only place the UI renders a
// review-status badge is the admin video list, which owns its own
// `REVIEW_BADGE` tone map (components/admin/ui Badge). A duplicate config here
// had zero references in either app or e2e.
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Polling-active statuses — the set that triggers 3s status polling
// ---------------------------------------------------------------------------

export const ACTIVE_POLLING_STATUSES = new Set([
  "pending_processing",
  "processing",
  "ready_subtitles",
]);
