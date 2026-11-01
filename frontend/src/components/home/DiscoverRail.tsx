"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowUpRight, CirclePlay, Check, Flame } from "lucide-react";

import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/common/SkeletonCard";
import { api } from "@/lib/api";
import { channelSubscriptionsRequest } from "@/lib/channelSubscriptions";
import { Image } from "@/components/ui/Image";
import { VideoMetadata } from "@/components/video/VideoMetadata";
import { formatDuration } from "@/lib/format";
import { watchHref } from "@/lib/watchEntry";
import { useContinueLearning } from "@/hooks/useContinueLearning";
import type { ChannelSubscriptionSummary } from "@/types/channels";

/** Compact resume strip: cover, title, remaining time, explicit continue. */
export function DiscoverContinue() {
  // 与首页布局门共用同一次 `/learning/continue` 请求（见 useContinueLearning）。
  const { item, failed, retry } = useContinueLearning();

  if (failed) {
    return (
      <p role="status" className="mb-4 flex items-center gap-2 text-meta text-muted">
        观看记录暂时未能加载
        <button
          type="button"
          onClick={retry}
          className="font-medium text-brand-700 hover:underline"
        >
          重试
        </button>
      </p>
    );
  }
  if (!item) return null;
  const { video } = item;
  const progress = Math.max(0, Math.min(100, Math.round(item.progress_percentage)));
  const remaining = item.remaining_seconds;

  return (
    <Link
      href={watchHref(video.id, {
        from: "home",
        extra: { t: Math.floor(item.position_seconds) },
      })}
      className="discover-resume group mb-5 flex items-center gap-3 rounded-md border border-hairline bg-surface-soft p-3 transition-colors hover:border-hairline-strong"
      data-testid="continue-learning-rail"
    >
      <span className="relative aspect-video w-24 shrink-0 overflow-hidden rounded-sm bg-surface-card">
        <Image src={video.thumbnail_url} alt="" sizes="96px" />
      </span>
      <div className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5 text-caption font-semibold text-brand-700">
          <CirclePlay size={13} aria-hidden /> 继续观看 · {progress}%
        </span>
        <span className="mt-0.5 block truncate text-copy font-semibold text-ink">
          {video.title_zh?.trim() || video.title}
        </span>
        {remaining != null && remaining > 0 && (
          <span className="mt-0.5 block text-meta text-muted">
            还剩 {formatDuration(remaining)}
          </span>
        )}
        <VideoMetadata video={video} className="mt-1" />
        <span className="mt-1.5 block h-[3px] overflow-hidden rounded-pill bg-surface-card">
          <span
            className="block h-full rounded-pill bg-brand-500"
            style={{ width: `${progress}%` }}
          />
        </span>
      </div>
      <span className="shrink-0 rounded-pill border border-hairline px-3 py-1.5 text-meta font-semibold text-ink group-hover:border-hairline-strong">
        继续
      </span>
    </Link>
  );
}

interface Overview {
  streak: { current: number };
  this_week: {
    minutes: number;
    days_active: number;
    daily: { date: string; minutes: number; active?: boolean }[];
  };
  words: { total: number; due_review_count: number };
}

/** Right rail: due words, subscribed channels, and the week's real activity. */
export function DiscoverRail({ initialDue = 0 }: { initialDue?: number }) {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [subs, setSubs] = useState<ChannelSubscriptionSummary[]>([]);

  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoadState("loading");
    Promise.all([
      api<Overview>("/api/v1/users/me/overview", { signal: controller.signal }),
      // 与列表后的「已订阅的频道」共用同一次请求（lib/channelSubscriptions）。
      channelSubscriptionsRequest.get(),
    ])
      .then(([data, channels]) => {
        if (controller.signal.aborted) return;
        if (!data?.words || !data?.this_week || !data?.streak)
          throw new Error("学习进度数据不完整");
        setOverview(data);
        setSubs(channels);
        setLoadState("ready");
      })
      .catch(() => {
        if (!controller.signal.aborted) setLoadState("error");
      });
    return () => {
      controller.abort();
      channelSubscriptionsRequest.release();
    };
  }, [attempt]);
  if (loadState === "error")
    return (
      <aside>
        <ErrorState title="学习进度未能加载" onRetry={() => setAttempt((n) => n + 1)} />
      </aside>
    );
  if (loadState === "loading")
    return (
      <aside aria-busy="true" className="space-y-3">
        <Skeleton className="h-44" />
        <Skeleton className="h-24" />
        <Skeleton className="h-32" />
      </aside>
    );

  const due = overview?.words?.due_review_count ?? initialDue;
  const week = overview?.this_week;
  const weekDays = Math.max(0, Math.min(7, week?.days_active ?? 0));
  const weekProgress = Math.round((weekDays / 7) * 100);

  return (
    <aside className="discover-learning" aria-label="今天的进度">
      <div className="discover-learning-heading">
        <span className="discover-learning-dot" aria-hidden />
        我的学习
      </div>
      <section className="discover-learning-section">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-meta font-semibold text-ink">今天到期</h2>
          {due === 0 && <Check size={16} className="text-brand-700" aria-hidden />}
        </div>
        <p className="mt-2 flex items-baseline gap-1.5">
          <span className="text-[2.625rem] font-semibold leading-none tracking-tight tabular-nums text-ink">
            {due}
          </span>
          <span className="text-meta text-muted">个单词</span>
        </p>
        <p className="mt-2 text-meta leading-relaxed text-muted">
          {due > 0 ? "趁记忆还新鲜，再见一面。" : "已全部复习，去发现新的表达吧。"}
        </p>
        <Link
          href={due > 0 ? "/vocabulary/review" : "/vocabulary"}
          className="discover-review-link"
        >
          {due > 0 ? "开始复习" : "看全部词汇"}
          <ArrowUpRight size={15} aria-hidden />
        </Link>
        <Link
          href="/vocabulary"
          className="mt-2 block text-center text-caption text-muted transition-colors hover:text-ink"
        >
          全部 {overview?.words?.total ?? 0} 词
        </Link>
      </section>

      <section className="discover-learning-section">
        <div className="flex items-center justify-between">
          <h2 className="text-meta font-semibold text-ink">正在学</h2>
          <Link href="/channels" className="text-meta text-brand-700 hover:underline">
            全部
          </Link>
        </div>
        {subs.length === 0 ? (
          <p className="mt-2 text-meta text-muted">
            还没有订阅频道。
            <Link href="/channels" className="ml-1 text-brand-700 hover:underline">
              去挑一个
            </Link>
          </p>
        ) : (
          <ul className="mt-2 space-y-1.5">
            {subs.slice(0, 3).map((channel) => (
              <li key={channel.id}>
                <Link
                  href={`/channels/${channel.slug}`}
                  className="flex items-center gap-2 rounded-sm px-1 py-1 hover:bg-surface-soft"
                >
                  <span className="relative h-7 w-7 shrink-0 overflow-hidden rounded-pill bg-surface-card">
                    <Image src={channel.cover_url} alt="" sizes="28px" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-meta font-medium text-ink">
                      {channel.name}
                    </span>
                    <span className="block truncate text-caption text-muted">
                      {channel.unlearned_count ?? 0} 段未学
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="discover-learning-section">
        <div className="flex items-center justify-between">
          <h2 className="text-meta font-semibold text-ink">本周节奏</h2>
          <span className="text-caption text-muted">记录</span>
        </div>
        <dl className="discover-week-stats">
          <div>
            <dt className="text-muted">有学习的天数</dt>
            <dd className="tabular-nums text-ink">{week ? `${week.days_active} / 7 天` : "—"}</dd>
          </div>
          <div>
            <dt className="text-muted">累计学习</dt>
            <dd className="tabular-nums text-ink">{week ? `${week.minutes} 分钟` : "—"}</dd>
          </div>
          <div>
            <dt className="text-muted">连续学习</dt>
            <dd className="flex items-center gap-1 tabular-nums text-ink">
              <Flame size={12} className="text-brand-500" aria-hidden />
              {overview?.streak ? `${overview.streak.current} 天` : "—"}
            </dd>
          </div>
        </dl>
        <div
          className="mt-2.5 h-1.5 overflow-hidden rounded-pill bg-surface-card"
          role="progressbar"
          aria-label="本周学习天数"
          title="按实际发生的学习记录统计"
          aria-valuemin={0}
          aria-valuemax={7}
          aria-valuenow={weekDays}
        >
          <span
            className="block h-full rounded-pill bg-brand-500"
            style={{ width: `${weekProgress}%` }}
          />
        </div>
      </section>
    </aside>
  );
}
