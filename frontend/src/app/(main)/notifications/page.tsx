"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Check, ChevronRight, Settings } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { PageHeader } from "@/components/ui/PageHeader";
import { PageTransition } from "@/components/common/PageTransition";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadMoreError } from "@/components/common/LoadMoreError";
import { FullPageSpinner, InlineSpinner } from "@/components/common/Spinner";
import { Button } from "@/components/ui/Button";
import { LinkButton } from "@/components/ui/LinkButton";
import { useNotificationStore } from "@/stores/notificationStore";
import { cn } from "@/lib/utils";
import type { Paginated } from "@/types";

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  related_url: string | null;
  created_at: string;
}

const TYPE_LABELS: Record<string, string> = {
  system: "系统",
  video_ready: "视频就绪",
  vocabulary_reminder: "词汇提醒",
  comment_reply: "互动",
  social_follow: "互动",
  post_liked: "互动",
  quality_alert: "质量提醒",
  announcement: "公告",
};

function formatNotifyTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const t = d.getTime();
  const hh = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  if (t >= todayStart) return `今天 ${hh}`;
  if (t >= todayStart - 86_400_000) return `昨天 ${hh}`;
  return `${d.getMonth() + 1}月${d.getDate()}日 ${hh}`;
}

/**
 * 通知中心。
 *
 * 设计（app.js:2109-2132）是单列列表：页头「通知设置 / 全部标为已读」，
 * 正文只有未读行浅底 + 蓝点 + 查看。类型筛选、设置预览和右栏统计不在
 * 这份导出契约里（V-20），偏好设置统一去「我的 → 设置」。
 */
export default function NotificationsPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const [unread, setUnread] = useState(0);
  const [markingAll, setMarkingAll] = useState(false);

  const fetcher = useCallback(
    (page: number) =>
      api<Paginated<Notification>>(`/api/v1/notifications?page=${page}&page_size=20`),
    []
  );

  const { items, setItems, loading, error, total, hasMore, loaderRef, loadMore, reload } =
    usePaginatedList<Notification>({
      fetcher,
      mode: "append",
      filters: [],
      enabled: isAuthenticated && !isLoading,
    });

  const refreshUnread = useCallback(async () => {
    const res = await api<{ count: number }>("/api/v1/notifications/unread-count").catch(
      () => null
    );
    if (res) {
      setUnread(res.count);
      useNotificationStore.getState().setUnread(res.count);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated || isLoading) return;
    void refreshUnread();
  }, [isAuthenticated, isLoading, refreshUnread]);

  async function markRead(notification: Notification) {
    if (notification.is_read) return;
    try {
      await api(`/api/v1/notifications/${notification.id}/read`, { method: "PATCH" });
      setItems((prev) => prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n)));
      void refreshUnread();
    } catch {
      toast.error("操作失败");
    }
  }

  async function markAllRead() {
    setMarkingAll(true);
    try {
      await api("/api/v1/notifications/read-all", { method: "PATCH" });
      setItems((prev) => prev.map((n) => ({ ...n, is_read: true })));
      toast.success("已全部标记为已读");
      reload();
      void refreshUnread();
    } catch {
      toast.error("操作失败");
    } finally {
      setMarkingAll(false);
    }
  }

  if (isLoading) return <FullPageSpinner />;

  return (
    <PageTransition>
      <div className="user-page">
        <PageHeader
          crumb="我的"
          title="通知"
          variant="eyebrow"
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <LinkButton href="/profile?tab=settings" variant="ghost" icon={Settings}>
                通知设置
              </LinkButton>
              <Button
                variant="secondary"
                icon={Check}
                disabled={unread === 0 || markingAll}
                onClick={() => void markAllRead()}
              >
                {unread === 0 ? "全部已读" : `全部标为已读（${unread}）`}
              </Button>
            </div>
          }
        />

        {loading && items.length === 0 ? (
          <InlineSpinner className="mt-6 py-12" />
        ) : error && items.length === 0 ? (
          <ErrorState title={error} onRetry={reload} className="mt-6 py-12" />
        ) : items.length === 0 && total === 0 ? (
          <div className="mt-6 rounded-lg border border-dashed border-hairline-strong bg-surface-soft p-5">
            <p className="text-copy font-semibold text-ink">暂无通知</p>
            <p className="mt-1 max-w-[44ch] text-copy leading-relaxed text-body">
              新视频就绪和自愿开启的词汇复习提醒会出现在这里；也可以先去首页挑一段开始学。
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <LinkButton href="/" variant="outline" size="sm">
                去首页挑一段
              </LinkButton>
              <LinkButton href="/vocabulary" variant="text" size="sm" iconRight>
                看词库
              </LinkButton>
            </div>
          </div>
        ) : (
          <ul className="mt-6 flex flex-col gap-3">
            {items.map((n) => (
              <li key={n.id}>
                <article
                  className={cn(
                    "relative flex items-start gap-3 rounded-lg border p-4",
                    n.is_read ? "border-hairline bg-canvas" : "border-brand-200 bg-brand-50"
                  )}
                >
                  {!n.is_read && (
                    <span
                      aria-hidden
                      className="absolute bottom-3 left-0 top-3 w-0.5 rounded-pill bg-brand-500"
                    />
                  )}
                  <span
                    aria-hidden
                    className={cn(
                      "mt-1.5 h-2 w-2 shrink-0 rounded-full",
                      n.is_read ? "bg-hairline-strong" : "bg-brand-500"
                    )}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1">
                      <h2 className="min-w-0 text-copy font-semibold leading-snug text-ink">
                        {n.title}
                      </h2>
                      <span className="shrink-0 text-caption text-body">
                        {formatNotifyTime(n.created_at)}
                      </span>
                    </div>
                    {n.message && (
                      <p className="mt-1 whitespace-pre-wrap text-copy leading-relaxed text-body">
                        {n.message}
                      </p>
                    )}
                    <div className="mt-3 flex flex-wrap items-center gap-3">
                      <span className="inline-flex h-6 items-center gap-1 rounded-sm border border-hairline px-2 text-caption text-body">
                        <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current" />
                        {TYPE_LABELS[n.type] ?? "系统"}
                      </span>
                      <span className="text-caption text-body">{n.is_read ? "已读" : "未读"}</span>
                      {n.related_url && (
                        <Link
                          href={n.related_url}
                          onClick={() => void markRead(n)}
                          className="inline-flex min-h-11 items-center gap-1 px-1 text-caption font-semibold text-body transition-colors hover:text-brand-700"
                        >
                          查看详情
                          <ChevronRight size={13} />
                        </Link>
                      )}
                      {!n.is_read && (
                        <button
                          type="button"
                          onClick={() => void markRead(n)}
                          className="inline-flex min-h-11 items-center gap-1 px-1 text-caption text-body transition-colors hover:text-ink"
                        >
                          <Check size={12} />
                          标为已读
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              </li>
            ))}
          </ul>
        )}

        {hasMore && (
          <div ref={loaderRef} className="flex justify-center py-6">
            {error ? (
              // 空列表的失败由上面的 ErrorState 负责，这里只管「后面还有内容」。
              items.length > 0 ? (
                <LoadMoreError message={error} onRetry={loadMore} />
              ) : null
            ) : (
              <span className="text-meta text-muted">加载更多…</span>
            )}
          </div>
        )}
      </div>
    </PageTransition>
  );
}
