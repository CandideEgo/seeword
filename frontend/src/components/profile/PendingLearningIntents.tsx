"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import { learningIntentSummary, type LearningIntent } from "@/lib/learningConnections";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";

export function PendingLearningIntents({ refreshKey = "" }: { refreshKey?: string }) {
  const [items, setItems] = useState<LearningIntent[]>([]);
  const [error, setError] = useState("");
  const [candidate, setCandidate] = useState<LearningIntent | null>(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try {
      const data = await api<{ items: LearningIntent[] }>(
        "/api/v1/external-connections/learning-intents"
      );
      setItems(data.items);
      setError("");
    } catch (cause) {
      if (cause instanceof ApiError && [403, 404, 503].includes(cause.status)) {
        setItems([]);
        return;
      }
      setError(cause instanceof Error ? cause.message : "待确认操作暂时无法读取");
    }
  }, []);
  useEffect(() => {
    void load();
    const visible = () => {
      if (document.visibilityState === "visible") void load();
    };
    window.addEventListener("focus", visible);
    const timer = setInterval(visible, 15_000);
    return () => {
      window.removeEventListener("focus", visible);
      clearInterval(timer);
    };
  }, [load, refreshKey]);

  const confirm = async () => {
    if (!candidate || busy) return;
    setBusy(true);
    try {
      await api<LearningIntent>(
        `/api/v1/external-connections/learning-intents/${encodeURIComponent(candidate.id)}/confirm`,
        {
          method: "POST",
          body: JSON.stringify({ confirmed: true }),
        }
      );
      setCandidate(null);
      toast.success("已确认，可由连接完成操作");
      await load();
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "确认失败，请重新读取操作";
      setCandidate(null);
      setError(message);
      toast.error(message);
      await load();
    } finally {
      setBusy(false);
    }
  };
  const pending = items.filter((item) => item.status === "pending" || item.status === "approved");
  if (!pending.length && !error) return null;
  return (
    <div
      id="learning-intents"
      className="space-y-3 scroll-mt-6 rounded-sm border border-hairline p-4"
      aria-label="学习操作确认"
    >
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-copy font-semibold text-ink">学习操作确认</h4>
        <Button size="sm" variant="ghost" onClick={() => void load()}>
          刷新
        </Button>
      </div>
      {error && (
        <p role="alert" className="text-meta text-error-text">
          {error}
        </p>
      )}
      <ul className="divide-y divide-hairline">
        {pending.map((item) => (
          <li key={item.id} className="space-y-2 py-3">
            <p className="break-words text-copy font-medium text-ink">
              {learningIntentSummary(item)}
            </p>
            <p className="text-meta text-muted">
              {item.host_label} 请求，
              {new Date(item.expires_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}{" "}
              前有效
            </p>
            {item.status === "approved" ? (
              <p role="status" className="text-meta text-body">
                已确认，等待连接执行
              </p>
            ) : (
              <Button
                size="sm"
                disabled={
                  busy || !item.resource.available || Date.parse(item.expires_at) <= Date.now()
                }
                onClick={() => setCandidate(item)}
              >
                查看并确认
              </Button>
            )}
          </li>
        ))}
      </ul>
      <ConfirmDialog
        open={!!candidate}
        onClose={() => !busy && setCandidate(null)}
        title="确认这次学习操作？"
        message={
          candidate
            ? `${learningIntentSummary(candidate)}。${candidate.action === "review" ? "这会更新你的复习安排与学习记录，不代表正式成绩。" : "这会保留课程完成记录，不代表掌握了材料。"}`
            : ""
        }
        confirmLabel="确认这次操作"
        cancelLabel="暂不确认"
        busy={busy}
        onConfirm={() => void confirm()}
      />
    </div>
  );
}
