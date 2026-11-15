"use client";

/**
 * 视频详情「首页内容」面板（backend/app/schemas/home_content.py）。
 *
 * 负责：状态行（未制作/草稿/已发布/来源已变更 + 生成任务）、生成草稿（覆盖前确认）、
 * 保存（expected_revision，409 提示刷新）、预览（管理员 preview 接口）、
 * 发布到主推/次推（一次点击完成「发布并替换」）、复制历史版本为草稿。
 *
 * 两条硬边界：
 * 1. 所有写操作都带 `expected_revision`，409 时提示刷新，绝不做最后写入者覆盖；
 * 2. 预览只走管理员接口，不请求公共 `/browse/home-editorial`，也没有 `?draft=true`。
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Eye, Loader2, RefreshCw, Save, Sparkles, Wand2 } from "lucide-react";
import { mediaUrl } from "@/lib/api";
import { apiErrorMessage, toastApiError } from "@/lib/errors";
import { useAdminAuthStore } from "@/stores/adminAuthStore";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  emptyDraft,
  generateHomeContentDraft,
  getHomeContentGeneration,
  getHomeContentPreview,
  getHomeContentVideoState,
  isGenerationActive,
  isOverwriteConfirmError,
  isRevisionConflictError,
  publishHomeContent,
  restoreHomeContentDraft,
  saveHomeContentDraft,
  REVISION_CONFLICT_MESSAGE,
} from "@/lib/adminHomeContent";
import type {
  HomeContentDraft,
  HomeContentGeneration,
  HomeContentRevisionSummary,
  HomeContentVideoState,
  HomeLayoutPreview,
} from "@/types/homeContent";
import type { Subtitle, VideoDetail } from "@/types";
import { HomeContentDraftForm } from "./HomeContentDraftForm";
import { HomeContentStatus } from "./HomeContentStatus";
import { HomeContentVersions } from "./HomeContentVersions";
import { HomePreviewDialog } from "./HomePreviewDialog";

const GENERATION_POLL_INTERVAL_MS = 4000;

interface ConfirmState {
  title: string;
  message: string;
  confirmLabel?: string;
  tone?: "default" | "danger";
  action: () => void;
}

export function HomeContentPanel({
  videoId,
  subtitles,
  video,
}: {
  videoId: string;
  /** 该视频真实字幕：所有引用只能从这里选。 */
  subtitles: Subtitle[];
  /** 详情页已有视频事实；只用于片段试听的本地媒体地址。 */
  video?: VideoDetail;
}) {
  const adminToken = useAdminAuthStore((store) => store.token);
  const [state, setState] = useState<HomeContentVideoState | null>(null);
  const [draft, setDraft] = useState<HomeContentDraft>(() => emptyDraft());
  const [generation, setGeneration] = useState<HomeContentGeneration | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [publishingPlace, setPublishingPlace] = useState<"lead" | "secondary" | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [conflict, setConflict] = useState(false);
  const [remoteDraftPending, setRemoteDraftPending] = useState(false);
  const [confirm, setConfirm] = useState<ConfirmState | null>(null);
  const [preview, setPreview] = useState<HomeLayoutPreview | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const dirtyRef = useRef(false);

  // 片段试听：管理端媒体需要 `?token=`（<audio> 发不了 Authorization 头）。
  const mediaPath = video
    ? video.video_url_720p || video.video_url_480p || video.video_url_1080p
    : null;
  const auditionSource =
    mediaPath && adminToken ? mediaUrl(mediaPath, { token: adminToken }) : null;

  const markDraft = useCallback((next: HomeContentDraft) => {
    setDraft(next);
    dirtyRef.current = true;
    setDirty(true);
  }, []);

  const applyState = useCallback(
    (next: HomeContentVideoState, options: { forceDraft?: boolean } = {}) => {
      setState(next);
      setGeneration(next.generation);
      if (options.forceDraft || !dirtyRef.current) {
        setDraft(next.draft ?? emptyDraft());
        dirtyRef.current = false;
        setDirty(false);
        setRemoteDraftPending(false);
      } else {
        setRemoteDraftPending(true);
      }
    },
    []
  );

  const fetchPreview = useCallback(async (): Promise<HomeLayoutPreview | null> => {
    try {
      return await getHomeContentPreview(videoId);
    } catch {
      return null;
    }
  }, [videoId]);

  const refreshPreviewSilently = useCallback(async () => {
    const next = await fetchPreview();
    if (next) setPreview(next);
  }, [fetchPreview]);

  const loadState = useCallback(
    async (options: { silent?: boolean; forceDraft?: boolean } = {}) => {
      if (!options.silent) setLoading(true);
      setLoadError(null);
      try {
        const next = await getHomeContentVideoState(videoId);
        applyState(next, { forceDraft: options.forceDraft ?? true });
        if (next.draft || next.revisions.length > 0) void refreshPreviewSilently();
      } catch (err) {
        if (options.silent) toastApiError(err, "刷新首页内容失败");
        else setLoadError(apiErrorMessage(err, "加载首页内容状态失败"));
      } finally {
        if (!options.silent) setLoading(false);
      }
    },
    [videoId, applyState, refreshPreviewSilently]
  );

  useEffect(() => {
    void loadState();
  }, [loadState]);

  // 生成任务轮询：queued/running 每 4 秒查一次；结束后刷新整个状态。
  useEffect(() => {
    if (!isGenerationActive(generation)) return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void (async () => {
        try {
          const next = await getHomeContentGeneration(videoId);
          if (cancelled) return;
          setGeneration(next);
          if (isGenerationActive(next)) return;
          const full = await getHomeContentVideoState(videoId);
          if (cancelled) return;
          applyState(full);
          if (!dirtyRef.current) void refreshPreviewSilently();
          if (next?.status === "succeeded") toast.success("首页内容草稿已生成");
          if (next?.status === "failed") {
            toast.error(
              `生成失败：${next.error_code ?? "未知错误"}${
                next.error_message ? ` · ${next.error_message}` : ""
              }`
            );
          }
        } catch {
          // 网络抖动不打断轮询，下一轮继续。
        }
      })();
    }, GENERATION_POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [generation, videoId, applyState, refreshPreviewSilently]);

  // --- 生成 ---
  // 普通函数而非 useCallback：确认弹层的回调会在事件时刻调用它，避免自引用依赖。
  function runGenerate(overwrite: boolean) {
    if (!state) return;
    setGenerating(true);
    void (async () => {
      try {
        const result = await generateHomeContentDraft(videoId, {
          expectedRevision: state.draft_revision,
          overwrite,
        });
        setGeneration(result.generation);
        if (result.reused) toast.info("已有生成任务正在进行，已复用该任务");
        else toast.success("已提交生成任务，正在后台生成…");
      } catch (err) {
        if (isOverwriteConfirmError(err) && !overwrite) {
          setConfirm({
            title: "重新生成草稿",
            message:
              "该视频已有草稿。重新生成会覆盖草稿内容（已发布版本不受影响），生成过程在后台进行。继续？",
            confirmLabel: "覆盖并生成",
            action: () => runGenerate(true),
          });
          return;
        }
        toastApiError(err, "提交生成任务失败");
        void loadState({ silent: true, forceDraft: false });
      } finally {
        setGenerating(false);
      }
    })();
  }

  function handleGenerate() {
    if (!state) return;
    if (isGenerationActive(generation)) {
      toast.info("已有生成任务在进行中，请等待完成");
      return;
    }
    if (state.draft) {
      setConfirm({
        title: "重新生成草稿",
        message:
          "该视频已有草稿。重新生成会覆盖草稿内容（已发布版本不受影响），生成过程在后台进行。继续？",
        confirmLabel: "覆盖并生成",
        action: () => runGenerate(true),
      });
      return;
    }
    runGenerate(false);
  }

  // --- 保存 ---
  const handleSave = useCallback(() => {
    if (!state) return;
    setSaving(true);
    setConflict(false);
    void (async () => {
      try {
        const next = await saveHomeContentDraft(videoId, draft, state.draft_revision);
        applyState(next, { forceDraft: true });
        toast.success("草稿已保存");
        void refreshPreviewSilently();
      } catch (err) {
        if (isRevisionConflictError(err)) {
          setConflict(true);
          toast.error(REVISION_CONFLICT_MESSAGE);
        } else {
          toastApiError(err, "保存草稿失败");
        }
      } finally {
        setSaving(false);
      }
    })();
  }, [state, draft, videoId, applyState, refreshPreviewSilently]);

  // --- 发布 ---
  const doPublish = useCallback(
    (place: "lead" | "secondary") => {
      if (!state) return;
      setPublishingPlace(place);
      setConflict(false);
      void (async () => {
        try {
          const result = await publishHomeContent(videoId, state.draft_revision, place);
          toast.success(`已发布 v${result.version} 并替换${place === "lead" ? "主推" : "次推"}`);
          await loadState({ silent: true, forceDraft: true });
          void refreshPreviewSilently();
        } catch (err) {
          if (isRevisionConflictError(err)) {
            setConflict(true);
            toast.error(REVISION_CONFLICT_MESSAGE);
          } else {
            toastApiError(err, place === "lead" ? "发布到主推失败" : "发布到次推失败");
          }
          void loadState({ silent: true, forceDraft: false });
        } finally {
          setPublishingPlace(null);
        }
      })();
    },
    [state, videoId, loadState, refreshPreviewSilently]
  );

  const handlePublish = useCallback(
    (place: "lead" | "secondary") => {
      if (!state?.draft) return;
      setConfirm({
        title: place === "lead" ? "发布并替换主推" : "发布并替换次推",
        message:
          "将为当前草稿创建不可变版本，并在同一事务中替换首页位置；新版本发布前线上内容不变。确认发布？",
        confirmLabel: "发布",
        action: () => doPublish(place),
      });
    },
    [state, doPublish]
  );

  // --- 恢复历史版本为草稿 ---
  const doRestore = useCallback(
    (revision: HomeContentRevisionSummary) => {
      if (!state) return;
      setRestoring(true);
      void (async () => {
        try {
          const next = await restoreHomeContentDraft(videoId, revision.id, state.draft_revision);
          applyState(next, { forceDraft: true });
          toast.success(`已把 v${revision.version} 复制为草稿`);
          void refreshPreviewSilently();
        } catch (err) {
          if (isRevisionConflictError(err)) {
            setConflict(true);
            toast.error(REVISION_CONFLICT_MESSAGE);
          } else {
            toastApiError(err, "复制历史版本失败");
          }
        } finally {
          setRestoring(false);
        }
      })();
    },
    [state, videoId, applyState, refreshPreviewSilently]
  );

  const handleRestore = useCallback(
    (revision: HomeContentRevisionSummary) => {
      setConfirm({
        title: `复制 v${revision.version} 为草稿`,
        message:
          "将把该历史版本内容复制为可编辑草稿；当前草稿的未保存修改会丢失。线上已发布内容不变。继续？",
        confirmLabel: "复制",
        action: () => doRestore(revision),
      });
    },
    [doRestore]
  );

  // --- 预览 ---
  const loadPreview = useCallback(() => {
    setPreviewOpen(true);
    setPreviewLoading(true);
    setPreviewError(null);
    void (async () => {
      try {
        setPreview(await getHomeContentPreview(videoId));
      } catch (err) {
        setPreviewError(apiErrorMessage(err, "预览加载失败"));
      } finally {
        setPreviewLoading(false);
      }
    })();
  }, [videoId]);

  // --- 刷新：有未保存编辑时先确认 ---
  const handleRefresh = useCallback(() => {
    if (dirtyRef.current) {
      setConfirm({
        title: "刷新会丢弃未保存编辑",
        message: "当前草稿有未保存的修改，刷新会从服务端重新加载草稿。继续？",
        confirmLabel: "刷新",
        action: () => void loadState({ forceDraft: true }),
      });
      return;
    }
    void loadState({ forceDraft: true });
  }, [loadState]);

  const loadRemoteDraft = useCallback(() => {
    setDraft(state?.draft ?? emptyDraft());
    dirtyRef.current = false;
    setDirty(false);
    setRemoteDraftPending(false);
  }, [state]);

  // 保存后由服务端解析出的片段时长；与当前草稿的起止句匹配才采用，避免旧预览串台。
  const serverClipDuration = useMemo(() => {
    const clip = preview?.page?.lead?.content.clip;
    if (!clip || !draft.clip) return null;
    if (clip.start_subtitle_id !== draft.clip.start_subtitle_id) return null;
    if (clip.end_subtitle_id !== draft.clip.end_subtitle_id) return null;
    return clip.duration;
  }, [preview, draft.clip]);

  const generationActive = isGenerationActive(generation);
  const publishDisabled =
    !state?.draft ||
    dirty ||
    saving ||
    generating ||
    generationActive ||
    publishingPlace !== null ||
    restoring ||
    !state.publicly_visible;

  let publishHint: string | null = null;
  if (state) {
    if (!state.draft) publishHint = "先生成或保存一份草稿，才能发布。";
    else if (!state.publicly_visible)
      publishHint = "视频当前不满足公共展示条件（发布/状态/可见性），发布会被拒绝。";
    else if (dirty) publishHint = "先保存草稿，发布的是服务端保存的内容。";
  }

  return (
    <Card as="section" padding={5} className="space-y-5" aria-label="首页内容">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-copy-lg font-semibold text-ink">首页内容</h2>
          <p className="mt-0.5 text-meta text-muted">
            生成/编辑这条视频的首页编辑内容；草稿修改不影响线上，发布后公共首页显示不可变版本。
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="compact"
            icon={RefreshCw}
            onClick={handleRefresh}
            disabled={loading || saving || publishingPlace !== null}
          >
            刷新
          </Button>
          <Button
            variant="outline"
            size="compact"
            icon={Eye}
            onClick={loadPreview}
            disabled={loading}
          >
            预览
          </Button>
          <Button
            variant="secondary"
            size="compact"
            icon={Sparkles}
            onClick={handleGenerate}
            disabled={!state || generating || generationActive || publishingPlace !== null}
          >
            {state?.draft ? "重新生成" : "生成草稿"}
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center gap-2 py-10 text-meta text-muted">
          <Loader2 size={16} className="animate-spin" aria-hidden />
          正在加载首页内容状态…
        </div>
      ) : loadError ? (
        <div className="space-y-3 rounded-sm border border-error/40 bg-red-soft px-4 py-3">
          <p className="text-meta text-error-text">{loadError}</p>
          <Button variant="outline" size="compact" onClick={handleRefresh}>
            重新加载
          </Button>
        </div>
      ) : state ? (
        <>
          <HomeContentStatus
            state={state}
            generation={generation}
            generationActive={generationActive}
          />

          {conflict && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-sm border border-error/40 bg-red-soft px-3 py-2">
              <p className="text-meta text-error-text">{REVISION_CONFLICT_MESSAGE}</p>
              <Button variant="outline" size="compact" onClick={handleRefresh}>
                刷新
              </Button>
            </div>
          )}

          {remoteDraftPending && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-sm border border-warning/40 bg-warning-soft px-3 py-2">
              <p className="text-meta text-warning-text">
                服务端草稿已更新（生成结果或被其他管理员修改）。当前有未保存编辑，未自动覆盖。
              </p>
              <Button variant="outline" size="compact" onClick={loadRemoteDraft}>
                加载服务端草稿
              </Button>
            </div>
          )}

          <div className="rounded-md border border-hairline bg-canvas p-4">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-copy font-semibold text-ink">草稿编辑</h3>
              <span className="text-caption text-muted">
                {dirty ? "有未保存修改" : "与服务端一致"}
              </span>
            </div>
            <HomeContentDraftForm
              videoId={videoId}
              draft={draft}
              subtitles={subtitles}
              clipDuration={serverClipDuration}
              mediaSource={auditionSource}
              disabled={saving || publishingPlace !== null}
              onChange={markDraft}
            />
            <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-hairline pt-4">
              <Button
                size="sm"
                icon={saving ? Loader2 : Save}
                disabled={!dirty || saving || publishingPlace !== null || restoring}
                onClick={handleSave}
              >
                {saving ? "保存中…" : "保存草稿"}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                icon={Wand2}
                disabled={publishDisabled}
                onClick={() => handlePublish("lead")}
              >
                {publishingPlace === "lead" ? "发布中…" : "发布到主推"}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={publishDisabled}
                onClick={() => handlePublish("secondary")}
              >
                {publishingPlace === "secondary" ? "发布中…" : "发布到次推"}
              </Button>
            </div>
            {publishHint && <p className="mt-2 text-caption text-muted-soft">{publishHint}</p>}
            <p className="mt-2 text-caption text-muted-soft">
              「发布到主推/次推」会创建不可变版本并在同一事务中替换首页位置；已发布版本可在下方复制回草稿编辑。
            </p>
          </div>

          <HomeContentVersions
            revisions={state.revisions}
            busy={restoring || publishingPlace !== null}
            onRestore={handleRestore}
          />
        </>
      ) : null}

      <ConfirmDialog
        open={confirm !== null}
        tone={confirm?.tone ?? "default"}
        title={confirm?.title}
        message={confirm?.message ?? ""}
        confirmLabel={confirm?.confirmLabel ?? "确认"}
        onClose={() => setConfirm(null)}
        onConfirm={() => {
          const current = confirm;
          setConfirm(null);
          current?.action();
        }}
      />

      <HomePreviewDialog
        open={previewOpen}
        title="首页内容预览（管理员接口）"
        preview={preview}
        loading={previewLoading}
        error={previewError}
        onClose={() => setPreviewOpen(false)}
        onRetry={loadPreview}
      />
    </Card>
  );
}
