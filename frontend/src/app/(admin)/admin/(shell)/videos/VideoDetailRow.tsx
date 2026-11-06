"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { toastApiError } from "@/lib/errors";
import {
  Download,
  Loader2,
  Pencil,
  Captions,
  Trash2,
  Video as VideoIcon,
  Check,
  XCircle,
  Play,
  RefreshCw,
  AlertCircle,
  Archive,
} from "lucide-react";
import { mediaUrl } from "@/lib/api";
import { useAdminAuthStore } from "@/stores/adminAuthStore";
import { useVideoPolling } from "@/hooks/useVideoPolling";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { STEP_LABELS_SHORT } from "@/lib/videoStatus";
import type { VideoAdmin } from "@/types";
import { updateVideo } from "@/lib/adminData";

const DIFFICULTY_OPTIONS = ["A1", "A2", "B1", "B2", "C1", "C2"];

/** Extract a YouTube video id from a URL, or null if it isn't a YouTube link. */
function youtubeId(url: string): string | null {
  const m = url.match(
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([A-Za-z0-9_-]{11})/
  );
  return m ? m[1] : null;
}

interface DetailRowProps {
  video: VideoAdmin;
  patchVideo: (id: string, patch: Partial<VideoAdmin>) => void;
  onSaved: () => void;
  onLocalize: (v: VideoAdmin) => void;
  onDelete: (v: VideoAdmin) => void;
  onApprove: (v: VideoAdmin) => void;
  onReject: (id: string) => void;
  onStartProcessing: (v: VideoAdmin) => void;
  onRecover: (v: VideoAdmin) => void;
  workerOnline: boolean;
  reviewBusy: boolean;
  onEditSubtitles: (id: string) => void;
  onRetry: (v: VideoAdmin) => void;
  onTakedown: (v: VideoAdmin) => void;
}

export function VideoDetailRow({
  video,
  patchVideo,
  onSaved,
  onEditSubtitles,
  onLocalize,
  onDelete,
  onApprove,
  onReject,
  onStartProcessing,
  onRecover,
  workerOnline,
  reviewBusy,
  onRetry,
  onTakedown,
}: DetailRowProps) {
  const ytId = youtubeId(video.source_url);
  const hasLocal = Boolean(video.video_url_720p || video.video_url_480p || video.video_url_1080p);
  // 管理端会话与用户端分离：媒体预览需显式带 admin token。
  const adminToken = useAdminAuthStore((s) => s.token);
  const isProcessing = video.status === "processing" || video.status === "ready_subtitles";
  const stepLabel = video.processing_step
    ? STEP_LABELS_SHORT[video.processing_step] || video.processing_step
    : "";

  // Edit form state.
  const [title, setTitle] = useState(video.title);
  const [titleZh, setTitleZh] = useState(video.title_zh || "");
  const [difficulty, setDifficulty] = useState(video.difficulty_level || "");
  const [topicTags, setTopicTags] = useState(video.topic_tags || "");
  const [isOfficial, setIsOfficial] = useState(video.is_official);
  const [isFeatured, setIsFeatured] = useState(video.is_featured);
  const [isPublished, setIsPublished] = useState(video.is_published);
  const [showOnHomepage, setShowOnHomepage] = useState(video.show_on_homepage ?? false);
  const [isDemo, setIsDemo] = useState(video.is_demo ?? false);
  const [adminNotes, setAdminNotes] = useState(video.admin_notes || "");
  const [saving, setSaving] = useState(false);

  // 父级动作（批准/驳回/下线/轮询）会改写这些布尔字段，需重新同步本地表单，
  // 否则随后的「保存」会把服务端刚写入的状态改回旧值。
  useEffect(() => {
    setIsOfficial(video.is_official);
    setIsFeatured(video.is_featured);
    setIsPublished(video.is_published);
    setShowOnHomepage(video.show_on_homepage ?? false);
    setIsDemo(video.is_demo ?? false);
  }, [
    video.is_official,
    video.is_featured,
    video.is_published,
    video.show_on_homepage,
    video.is_demo,
  ]);

  // Poll while processing.
  useVideoPolling(video.id, video.status, patchVideo, onSaved);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await updateVideo(video.id, {
        title,
        title_zh: titleZh.trim() || null,
        difficulty_level: difficulty || null,
        topic_tags: topicTags || null,
        is_official: isOfficial,
        is_featured: isFeatured,
        is_published: isPublished,
        show_on_homepage: showOnHomepage,
        is_demo: isDemo,
        admin_notes: adminNotes || null,
      });
      patchVideo(video.id, updated);
      toast.success("已保存");
    } catch (err) {
      toastApiError(err, "保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Left: preview + localize */}
      <div className="space-y-4">
        <div>
          <h3 className="text-meta font-medium text-muted uppercase tracking-wider mb-2">预览</h3>
          <div className="aspect-video w-full overflow-hidden rounded-sm bg-ink/5 flex items-center justify-center">
            {hasLocal && video.video_url_720p ? (
              <video
                src={mediaUrl(video.video_url_720p, {
                  // D0 媒体门控：/media 需可识别观看者；管理端会话独立，
                  // 显式传 admin token（不能依赖用户端 authStore）。
                  token: adminToken,
                })}
                controls
                playsInline
                webkit-playsinline="true"
                className="h-full w-full object-contain"
              />
            ) : ytId ? (
              <iframe
                src={`https://www.youtube.com/embed/${ytId}`}
                title="YouTube preview"
                className="h-full w-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : (
              <div className="text-center p-4">
                <VideoIcon size={32} className="mx-auto text-muted-soft" />
                <p className="mt-2 text-meta text-muted">无本地视频文件</p>
                <a
                  href={video.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1 inline-block text-meta text-brand-600 hover:underline break-all"
                >
                  打开源链接
                </a>
              </div>
            )}
          </div>
          {isProcessing && (
            <div className="mt-2 space-y-1">
              <div className="flex items-center gap-2 text-meta text-muted">
                <Loader2 size={12} className="animate-spin" />
                处理中{stepLabel ? ` · ${stepLabel}` : ""}
                {video.processing_progress
                  ? `（${video.processing_progress}%）`
                  : "（进度自动更新）"}
              </div>
              {video.processing_progress != null && video.processing_progress > 0 && (
                <div className="h-1 w-full rounded-full bg-ink/10">
                  <div
                    className="h-full rounded-full bg-brand-500 transition-all duration-500"
                    style={{
                      width: `${Math.min(video.processing_progress, 100)}%`,
                    }}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        <div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onLocalize(video)}
            disabled={hasLocal || isProcessing}
            title={hasLocal ? "已有本地视频" : isProcessing ? "搬运进行中" : "下载并转码到本地存储"}
          >
            <Download size={12} />
            {isProcessing ? "搬运中..." : hasLocal ? "已有本地" : "搬运到本地"}
          </Button>
        </div>

        {/* 内容三态（需求 §5.3）：下线 = 隐藏 + 释放媒体，保留学习记录。 */}
        <div>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onTakedown(video)}
            disabled={video.storage_mode === "offline"}
            title={
              video.storage_mode === "offline"
                ? "已下线"
                : "从所有列表隐藏并删除本地媒体文件，学习记录保留"
            }
          >
            <Archive size={12} />
            {video.storage_mode === "offline" ? "已下线" : "下线"}
          </Button>
        </div>
      </div>

      {/* Right: edit form */}
      <form onSubmit={handleSave} className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-meta font-medium text-muted uppercase tracking-wider">编辑</h3>
          <Button
            type="button"
            variant="outline"
            size="compact"
            onClick={() => onEditSubtitles(video.id)}
            title="编辑字幕文本、时间轴与单词高亮"
          >
            <Captions size={12} />
            字幕 / 高亮
          </Button>
        </div>

        {/* UGC review actions (pending_review only) */}
        {video.review_status === "pending_review" && !video.is_official && (
          <div className="rounded-sm border border-brand-200 bg-brand-50 p-3 space-y-2">
            <div className="text-meta font-medium text-brand-700">
              待审核 · 提交于{" "}
              {video.submitted_at ? new Date(video.submitted_at).toLocaleString() : "未知时间"}
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                size="sm"
                onClick={() => onApprove(video)}
                disabled={reviewBusy}
              >
                <Check size={13} />
                批准并发布
              </Button>
              <Button
                type="button"
                variant="destructive"
                size="sm"
                onClick={() => onReject(video.id)}
                disabled={reviewBusy}
              >
                <XCircle size={13} />
                驳回
              </Button>
            </div>
          </div>
        )}

        {/* Pending-processing: admin can trigger GPU processing */}
        {video.status === "pending_processing" && (
          <div className="rounded-sm border border-indigo/25 bg-sky-soft p-3 space-y-2">
            <div className="text-meta font-medium text-indigo">
              视频等待处理 · {workerOnline ? "Worker 在线" : "Worker 离线"}
            </div>
            {!workerOnline && (
              <div className="text-caption text-indigo/80">请先启动本地处理服务</div>
            )}
            <Button
              type="button"
              size="sm"
              onClick={() => onStartProcessing(video)}
              disabled={!workerOnline}
              icon={Play}
            >
              开始处理
            </Button>
          </div>
        )}
        {/* Processing / ready_subtitles: normal progress with optional recover link */}
        {(video.status === "processing" || video.status === "ready_subtitles") && (
          <div className="rounded-sm border border-warning/30 bg-warning-soft p-3 space-y-2">
            <div className="flex items-center gap-2 text-meta font-medium text-warning-text">
              <Loader2 size={12} className="animate-spin text-warning" />
              处理中{stepLabel ? ` · ${stepLabel}` : ""}
              {video.processing_progress ? `（${video.processing_progress}%）` : ""}
            </div>
            {video.processing_progress != null && video.processing_progress > 0 && (
              <div className="h-1.5 w-full rounded-full bg-ink/10">
                <div
                  className="h-full rounded-full bg-warning transition-all duration-500"
                  style={{
                    width: `${Math.min(video.processing_progress, 100)}%`,
                  }}
                />
              </div>
            )}
            <button
              type="button"
              onClick={() => onRecover(video)}
              className="inline-flex items-center gap-1 text-meta text-warning-text hover:opacity-80 underline underline-offset-2"
            >
              <RefreshCw size={10} />
              卡住了？重新恢复处理
            </button>
          </div>
        )}
        {/* Error state: show error_message + retry button */}
        {video.status === "error" && (
          <div className="rounded-sm border border-error/30 bg-red-soft p-3 space-y-2">
            <div className="flex items-center gap-2 text-meta font-medium text-error-text">
              <AlertCircle size={12} className="text-error" />
              处理失败
              {video.processing_step
                ? `（卡在 ${STEP_LABELS_SHORT[video.processing_step] || video.processing_step}）`
                : ""}
            </div>
            {video.error_message && (
              <div className="text-meta text-error-text break-all">{video.error_message}</div>
            )}
            {/* Resume hint: if subtitles exist, retry will skip transcription */}
            {video.processing_step &&
              (video.processing_step === "transcribing" ||
                video.processing_step === "extracting") && (
                <div className="text-caption text-error-text bg-error/10 rounded-md px-2 py-1">
                  重新处理时将从转录步骤开始（无字幕缓存）
                </div>
              )}
            {video.processing_step &&
              video.processing_step !== "transcribing" &&
              video.processing_step !== "extracting" && (
                <div className="text-caption text-error-text bg-error/10 rounded-md px-2 py-1">
                  重新处理将从转录后的步骤继续（已有字幕缓存，无需重新转录）
                </div>
              )}
            {!video.processing_step && (
              <div className="text-caption text-error-text bg-error/10 rounded-md px-2 py-1">
                重新处理将从转录步骤开始（无字幕缓存）
              </div>
            )}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => onRetry(video)}
              icon={RefreshCw}
            >
              重新处理
            </Button>
          </div>
        )}
        {video.review_status === "rejected" && !video.is_official && video.rejection_reason && (
          <div className="rounded-sm border border-error/30 bg-red-soft p-3 text-meta text-error-text">
            已驳回：{video.rejection_reason}
          </div>
        )}

        <div>
          <label className="block text-meta font-medium text-muted mb-1">标题</label>
          <Input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>

        <div>
          <label className="block text-meta font-medium text-muted mb-1">中文标题</label>
          <Input
            type="text"
            value={titleZh}
            onChange={(e) => setTitleZh(e.target.value)}
            placeholder="留空则全站回退英文标题"
          />
          <p className="mt-1 text-caption text-muted">管线会自动翻译；这里可手改或清空。</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-meta font-medium text-muted mb-1">难度</label>
            <Select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value="">-</option>
              {DIFFICULTY_OPTIONS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="block text-meta font-medium text-muted mb-1">标签</label>
            <Input
              type="text"
              value={topicTags}
              onChange={(e) => setTopicTags(e.target.value)}
              placeholder="逗号分隔"
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <label className="inline-flex items-center gap-2 whitespace-nowrap text-copy text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={isOfficial}
              onChange={(e) => setIsOfficial(e.target.checked)}
              className="h-4 w-4 rounded-sm border-hairline"
            />
            官方
          </label>
          <label className="inline-flex items-center gap-2 whitespace-nowrap text-copy text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={isFeatured}
              onChange={(e) => setIsFeatured(e.target.checked)}
              className="h-4 w-4 rounded-sm border-hairline"
            />
            精选
          </label>
          <label className="inline-flex items-center gap-2 whitespace-nowrap text-copy text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={isPublished}
              disabled={video.status !== "ready" && !isPublished}
              onChange={(e) => setIsPublished(e.target.checked)}
              className="h-4 w-4 rounded-sm border-hairline"
            />
            已发布
            {video.status !== "ready" && !isPublished && (
              <span className="text-meta text-muted">（需 ready）</span>
            )}
          </label>
          <label className="inline-flex items-center gap-2 whitespace-nowrap text-copy text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={showOnHomepage}
              onChange={(e) => setShowOnHomepage(e.target.checked)}
              className="h-4 w-4 rounded-sm border-hairline"
            />
            首页展示
          </label>
          <label className="inline-flex items-center gap-2 whitespace-nowrap text-copy text-ink cursor-pointer">
            <input
              type="checkbox"
              checked={isDemo}
              onChange={(e) => setIsDemo(e.target.checked)}
              className="h-4 w-4 rounded-sm border-hairline"
            />
            示范视频（匿名可直接播放）
          </label>
        </div>

        <div>
          <label className="block text-meta font-medium text-muted mb-1">管理员备注</label>
          <Textarea
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            rows={3}
            className="resize-none"
            placeholder="仅管理员可见..."
          />
        </div>

        <div className="flex items-center justify-between gap-3 pt-2">
          <button
            type="button"
            onClick={() => onDelete(video)}
            className="inline-flex items-center gap-1.5 text-meta text-error-text hover:opacity-80"
          >
            <Trash2 size={12} />
            删除视频
          </button>
          <Button type="submit" size="sm" disabled={saving} icon={Pencil}>
            {saving ? "保存中..." : "保存"}
          </Button>
        </div>
      </form>
    </div>
  );
}
