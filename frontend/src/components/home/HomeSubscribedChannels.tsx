"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { channelSubscriptionsRequest } from "@/lib/channelSubscriptions";
import { Image } from "@/components/ui/Image";
import { userInitial } from "@/lib/avatar";
import type { ChannelSubscriptionSummary } from "@/types/channels";

/**
 * 首页「已订阅的频道」：设计稿在视频流之后保留的一段频道入口。
 *
 * 数据与侧栏「正在学」同一接口（真实订阅集合），只是展示形态更紧凑：
 * 34px 方图 + 频道名 + 未学段数，三列。加载失败不阻塞首页——整段隐藏，
 * 因为订阅入口在侧栏与频道页始终可达。
 */
export function HomeSubscribedChannels() {
  const [items, setItems] = useState<ChannelSubscriptionSummary[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    // 与右栏「正在学」共用同一次请求（lib/channelSubscriptions）。
    channelSubscriptionsRequest
      .get()
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
      channelSubscriptionsRequest.release();
    };
  }, []);

  if (failed || (items && items.length === 0)) return null;

  return (
    <section className="mt-9" aria-labelledby="home-subscribed-title">
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
        <h2 id="home-subscribed-title" className="text-title font-semibold text-ink">
          已订阅的频道
        </h2>
        <Link
          href="/channels"
          className="inline-flex items-center gap-1 text-meta font-semibold text-body transition-colors hover:text-ink"
        >
          管理频道
          <ArrowRight size={13} aria-hidden />
        </Link>
      </div>

      {items === null ? (
        <div className="mt-3 grid gap-2.5 sm:grid-cols-2 xl:grid-cols-3" aria-hidden>
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-[54px] animate-pulse rounded-md bg-surface-soft" />
          ))}
        </div>
      ) : (
        <ul className="mt-3 grid gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
          {items.slice(0, 6).map((channel) => (
            <li key={channel.id} className="min-w-0">
              <Link
                href={`/channels/${channel.slug}`}
                className="group flex items-center gap-2.5 rounded-md border border-hairline bg-canvas p-2.5 transition-colors hover:border-hairline-strong"
              >
                <span className="relative h-[34px] w-[34px] shrink-0 overflow-hidden rounded-md bg-surface-card">
                  {channel.cover_url ? (
                    <Image src={channel.cover_url} alt="" sizes="34px" />
                  ) : (
                    <span className="flex h-full w-full items-center justify-center text-caption font-bold text-muted">
                      {userInitial(channel.name)}
                    </span>
                  )}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-caption font-semibold text-ink">
                    {channel.name}
                  </span>
                  <span className="block truncate text-caption text-muted">
                    {channel.unlearned_count > 0
                      ? `${channel.unlearned_count} 段未学`
                      : `${channel.video_count} 段已收录`}
                  </span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
