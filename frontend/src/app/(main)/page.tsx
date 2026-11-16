"use client";

import { Suspense, useCallback, useEffect, useState, ViewTransition } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { HomeEditorialHeader, HomeEditorialHero } from "@/components/home/HomeEditorialHero";
import { DiscoverContinue, DiscoverRail } from "@/components/home/DiscoverRail";
import { FeaturedListening } from "@/components/home/FeaturedListening";
import { HomeFeed } from "@/components/home/HomeFeed";
import { HomeSubscribedChannels } from "@/components/home/HomeSubscribedChannels";
import { LessonEntry } from "@/components/home/LessonEntry";
import { VideoCardSkeleton } from "@/components/ui/VideoCard";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/common/SkeletonCard";
import { fetchHomeEditorial } from "@/lib/homeEditorial";
import { useContinueLearning } from "@/hooks/useContinueLearning";
import type { HomeEditorialPage } from "@/types/homeContent";

/** 首页以完整视频为浏览单位；编排不可用时回退普通精选。 */

const EDITORIAL_TIMEOUT_MS = 8000;

/**
 * 本次页面加载共享的首页编排请求（SSR 不发起）。
 *
 * 放在模块级的原因：壳层要先解析登录态 / onboarding，页面组件可能几秒后才 mount；
 * 在这之前先把这条公共 GET 发出去，mount 后直接消费结果，首屏不用再等一次往返。
 * 同时它也消化了 dev StrictMode 的「挂载 → 清理 → 再挂载」：两次 effect 订阅同一
 * 个 promise，不会产生两个请求、也不会把第一个请求 abort 成「假失败」。
 *
 * 不做结果缓存：真正离开页面时 `releaseHomeEditorial()` 用 0ms 延迟清掉请求（重挂载
 * 会取消这个延迟），下次进入首页重新取，发布/下线仍然立即生效。
 */
let editorialRequest: Promise<HomeEditorialPage | null> | null = null;
let editorialAbort: AbortController | null = null;
let editorialReleaseTimer: number | null = null;

function loadHomeEditorial(): Promise<HomeEditorialPage | null> {
  if (typeof window === "undefined") return Promise.resolve(null);
  if (editorialReleaseTimer !== null) {
    clearTimeout(editorialReleaseTimer);
    editorialReleaseTimer = null;
  }
  if (!editorialRequest) {
    const controller = new AbortController();
    editorialAbort = controller;
    const timer = window.setTimeout(() => controller.abort(), EDITORIAL_TIMEOUT_MS);
    const request = fetchHomeEditorial(controller.signal).finally(() => window.clearTimeout(timer));
    // 请求可能在页面 mount 之前就失败（壳层还在解析登录态）；先挂一个空 catch，
    // 避免浏览器把「稍后才被 effect 消费的 rejection」报成 unhandled rejection。
    void request.catch(() => {});
    editorialRequest = request;
  }
  return editorialRequest;
}

function releaseHomeEditorial(): void {
  if (typeof window === "undefined") return;
  if (editorialReleaseTimer !== null) clearTimeout(editorialReleaseTimer);
  editorialReleaseTimer = window.setTimeout(() => {
    editorialReleaseTimer = null;
    // 真正离开页面才取消在途请求；StrictMode 的重挂载会先取消这个定时器。
    editorialAbort?.abort();
    editorialAbort = null;
    editorialRequest = null;
  }, 0);
}

if (typeof window !== "undefined") {
  // 路由 chunk 一到就发起公共读取，与壳层的登录态 / onboarding 门并行。
  void loadHomeEditorial();
}

type EditorialState =
  { status: "loading" } | { status: "editorial"; page: HomeEditorialPage } | { status: "fallback" };

export default function HomePage() {
  const [editorial, setEditorial] = useState<EditorialState>({ status: "loading" });
  const [featuredSettled, setFeaturedSettled] = useState(false);
  const markFeaturedSettled = useCallback(() => setFeaturedSettled(true), []);
  const continueLearning = useContinueLearning();
  const layoutReady =
    !continueLearning.loading &&
    (editorial.status === "editorial" || (editorial.status === "fallback" && featuredSettled));

  useEffect(() => {
    // cancelled 只表示「这次订阅作废」（StrictMode 清理 / 真正卸载）；超时由模块级
    // 请求自己的 AbortController 处理，abort 后的 reject 会走到 fallback。
    let cancelled = false;
    loadHomeEditorial()
      .then((page) => {
        if (cancelled) return;
        setEditorial(page ? { status: "editorial", page } : { status: "fallback" });
      })
      .catch(() => {
        if (cancelled) return;
        setEditorial({ status: "fallback" });
      });
    return () => {
      cancelled = true;
      releaseHomeEditorial();
    };
  }, []);

  // 路由过渡（Phase 2）：首页与观看页共享 page-in / page-out 快照动画。
  // 包成变量再交给 <ViewTransition>，避免整页 JSX 缩进 churn。
  const page = (
    <div className="home-compact pt-4 pb-18">
      <HomeEditorialHeader />
      <DiscoverContinue />

      <div className="home-discover-columns">
        <div className="min-w-0">
          {editorial.status === "editorial" && editorial.page.lead ? (
            <HomeEditorialHero page={editorial.page} />
          ) : editorial.status === "loading" ? (
            <EditorialSkeleton />
          ) : (
            <FeaturedListening onSettled={markFeaturedSettled} />
          )}

          {/* id 锚点：站内「去浏览」类入口统一落到 `/`，需要时可 #feed 定位 */}
          <section id="feed" aria-label="视频列表" className="home-video-feed mt-9 scroll-mt-6">
            <div className="mb-3 flex flex-wrap items-end justify-between gap-x-4 gap-y-1">
              <div className="min-w-0">
                <h2 className="text-[1.125rem] font-semibold tracking-tight text-ink">继续发现</h2>
              </div>
              <Link
                href="/channels"
                className="inline-flex items-center gap-1 text-meta font-semibold text-body transition-colors hover:text-ink"
              >
                全部频道
                <ArrowRight size={13} aria-hidden />
              </Link>
            </div>
            <Suspense fallback={<FeedSkeleton />}>
              <HomeFeed layoutReady={layoutReady} />
            </Suspense>
          </section>
        </div>
        <div className="space-y-5">
          <DiscoverRail />
          <LessonEntry />
        </div>
      </div>

      <HomeSubscribedChannels />
    </div>
  );

  return (
    <ViewTransition enter="page-in" exit="page-out" default="none">
      {page}
    </ViewTransition>
  );
}

function EditorialSkeleton() {
  return (
    <Card padding={5} aria-label="正在准备今日精选" role="status">
      <div className="grid gap-5 md:grid-cols-[minmax(0,0.86fr)_minmax(0,1.14fr)]">
        <Skeleton className="aspect-video" />
        <div className="space-y-3 py-2">
          <Skeleton className="h-3 w-24 rounded-pill" />
          <Skeleton className="h-6 w-4/5 rounded-pill" />
          <Skeleton className="h-4 w-3/5 rounded-pill" />
          <Skeleton className="h-9 w-40" />
        </div>
      </div>
    </Card>
  );
}

function FeedSkeleton() {
  return (
    <div className="home-feed-grid mt-5">
      {Array.from({ length: 8 }).map((_, i) => (
        <VideoCardSkeleton key={i} />
      ))}
    </div>
  );
}
