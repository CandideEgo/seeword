"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Download, Loader2, ShieldAlert, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { toastApiError } from "@/lib/errors";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import type { DeletionStatus, ExportStatus, ExportTask } from "@/types";

/** 账户生命周期变更后广播，供壳层 `DeletionBanner` 立即刷新倒计时。 */
export const DELETION_CHANGED_EVENT = "seeword:deletion-changed";

function notifyDeletionChanged() {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(DELETION_CHANGED_EVENT));
  }
}

/**
 * 「设置 → 账户 → 数据与账户」：异步数据导出 + 30 天可撤回注销（P1-7）。
 *
 * 导出走 `GET /users/me/export`（建任务）→ 轮询 `/{task_id}` → ready 后给出
 * 一次性短时下载链接；注销走 `POST/DELETE /users/me/deletion`，冷静期内允许
 * 登录，用户必须显式撤销（不在登录时自动取消）。
 */
export function AccountLifecycleSettings() {
  const [deletion, setDeletion] = useState<DeletionStatus | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [exportTask, setExportTask] = useState<ExportTask | null>(null);
  const [exportStatus, setExportStatus] = useState<ExportStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<DeletionStatus>("/api/v1/users/me/deletion")
      .then((s) => {
        if (!cancelled) setDeletion(s);
      })
      .catch(() => {
        /* 未登录 / 失败：不渲染倒计时 */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // 导出任务轮询：pending/running 每 5s 查一次，ready/failed 停。
  useEffect(() => {
    if (!exportTask) return;
    if (exportStatus?.status === "ready" || exportStatus?.status === "failed") return;
    let cancelled = false;
    const poll = async () => {
      try {
        const s = await api<ExportStatus>(`/api/v1/users/me/export/${exportTask.task_id}`);
        if (!cancelled) setExportStatus(s);
      } catch {
        /* 单次失败继续轮询 */
      }
    };
    void poll();
    const t = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [exportTask, exportStatus?.status]);

  const requestDeletion = useCallback(async () => {
    setBusy(true);
    try {
      const s = await api<DeletionStatus>("/api/v1/users/me/deletion", {
        method: "POST",
        body: JSON.stringify({ confirm: true }),
      });
      setDeletion(s);
      notifyDeletionChanged();
      toast.success(`已提交注销，账户将于 ${s.days_remaining ?? 30} 天后删除`);
    } catch (err) {
      toastApiError(err, "提交失败，请重试");
    } finally {
      setBusy(false);
      setConfirmOpen(false);
    }
  }, []);

  const cancelDeletion = useCallback(async () => {
    setBusy(true);
    try {
      await api("/api/v1/users/me/deletion", { method: "DELETE" });
      setDeletion({
        scheduled: false,
        requested_at: null,
        scheduled_at: null,
        days_remaining: null,
        reason: null,
      });
      notifyDeletionChanged();
      toast.success("已撤销注销");
    } catch (err) {
      toastApiError(err, "撤销失败，请重试");
    } finally {
      setBusy(false);
    }
  }, []);

  async function startExport() {
    try {
      const task = await api<ExportTask>("/api/v1/users/me/export");
      setExportTask(task);
      setExportStatus(null);
      toast.success("导出任务已创建，完成后会站内通知你");
    } catch (err) {
      toastApiError(err, "导出创建失败");
    }
  }

  const exportPreparing =
    !!exportTask && exportStatus?.status !== "ready" && exportStatus?.status !== "failed";

  return (
    <div className="space-y-4">
      {/* 数据导出 */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-copy font-medium text-ink">导出我的数据</div>
          <p className="text-meta text-muted mt-0.5">
            打包资料、词汇、跟读记录、学习记录与媒体原件为 ZIP，完成后可下载。
          </p>
          {exportStatus?.status === "ready" && exportStatus.download_url && (
            <a
              href={exportStatus.download_url}
              className="mt-1.5 inline-flex items-center gap-1.5 text-meta font-semibold text-brand-700 hover:underline"
            >
              <Download size={13} />
              下载导出包（15 分钟内有效，仅可下载一次）
            </a>
          )}
          {exportStatus?.status === "failed" && (
            <p className="mt-1.5 text-meta text-error-text">导出失败，请重新发起</p>
          )}
          {exportPreparing && (
            <p className="mt-1.5 text-meta text-muted inline-flex items-center gap-1.5">
              <Loader2 size={13} className="animate-spin" />
              正在准备导出包…
            </p>
          )}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={startExport}
          disabled={exportPreparing}
          className="shrink-0 whitespace-nowrap"
        >
          导出
        </Button>
      </div>

      <div className="pt-4 border-t border-hairline">
        {deletion?.scheduled ? (
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-copy font-medium text-ink flex items-center gap-1.5">
                <ShieldAlert size={14} className="text-warning" />
                账户将于 {deletion.days_remaining} 天后删除
              </div>
              <p className="text-meta text-muted mt-0.5">
                冷静期内仍可正常登录。到期后将删除个人数据与上传媒体，手机号随之释放。
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={cancelDeletion}
              disabled={busy}
              className="shrink-0 whitespace-nowrap"
            >
              撤销注销
            </Button>
          </div>
        ) : (
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-copy font-medium text-ink">注销账户</div>
              <p className="text-meta text-muted mt-0.5">
                提交后有 30 天冷静期，期间可随时撤销；到期删除个人数据与自产媒体。
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              icon={Trash2}
              onClick={() => setConfirmOpen(true)}
              disabled={busy}
              className="shrink-0 whitespace-nowrap text-error-text border-error/40 hover:bg-red-soft"
            >
              注销
            </Button>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={confirmOpen}
        tone="danger"
        title="确认注销账户？"
        message={
          <ul className="list-disc space-y-1 pl-5">
            <li>提交后进入 30 天冷静期，期间仍可登录、继续学习。</li>
            <li>冷静期内随时可以「撤销注销」，不会自动恢复。</li>
            <li>到期后删除个人数据与上传的媒体原件，手机号释放，词汇与学习记录不可恢复。</li>
          </ul>
        }
        confirmLabel="提交注销"
        busy={busy}
        onConfirm={requestDeletion}
        onClose={() => setConfirmOpen(false)}
      />
    </div>
  );
}
