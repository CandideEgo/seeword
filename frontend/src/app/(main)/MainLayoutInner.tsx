"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { TopBar } from "@/components/layout/TopBar";
import { MobileTabBar } from "@/components/layout/MobileTabBar";
import { Sidebar } from "@/components/layout/Sidebar";
import { PublicTopBar } from "@/components/layout/PublicTopBar";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { UnreadCountSync } from "@/components/layout/UnreadCountSync";
import { ShellSkeleton } from "@/components/common/ShellSkeleton";
import { DeletionBanner } from "@/components/profile/DeletionBanner";
import { useAuthStore } from "@/stores/authStore";
import { useVocabularyStore } from "@/stores/vocabularyStore";
import { useWatchStore } from "@/stores/watchStore";
import { api } from "@/lib/api";
import { SCROLL_CONTAINER_ID } from "@/lib/scrollMemory";
import { WatchChromeProvider, WatchShellControls } from "@/components/watch/WatchChromeProvider";

export function MainLayoutInner({ children }: { children: React.ReactNode }) {
  return (
    <WatchChromeProvider>
      <MainLayoutContent>{children}</MainLayoutContent>
    </WatchChromeProvider>
  );
}

function MainLayoutContent({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoading = useAuthStore((s) => s.isLoading);
  const [onboardingChecked, setOnboardingChecked] = useState(false);

  const pathname = usePathname();
  const isWatch = pathname.startsWith("/watch/");
  const immersive = useWatchStore((s) => s.immersive) && isWatch;
  const fetchVocabStats = useVocabularyStore((s) => s.fetchStats);

  // Vocab due badges live in three chrome surfaces. Refresh once per shell
  // mount here; the surfaces only read the store.
  useEffect(() => {
    if (isAuthenticated) void fetchVocabStats();
  }, [isAuthenticated, fetchVocabStats]);

  // Onboarding gate: the server flag is the only source of truth. Resolve it
  // before rendering the shell so a new user never sees the home page flash
  // before being sent to /onboarding.
  useEffect(() => {
    if (isLoading) {
      return;
    }

    if (!isAuthenticated) {
      setOnboardingChecked(true);
      return;
    }

    let cancelled = false;

    async function checkOnboarding() {
      try {
        // 30s TTL：整页导航时 onboarding 门与 TopBar 的头像 store 各要读一次
        // `/users/me`；缓存后一次导航只打一个请求，避免贴住后端 30/min 的账号限流。
        const user = await api<{ onboarding_completed?: boolean }>("/api/v1/users/me", {
          cacheTtlMs: 30_000,
        });
        if (cancelled) return;
        if (user.onboarding_completed === false) {
          router.replace("/onboarding");
          return;
        }
      } catch {
        // Fail-open: an API blip must not trap the user on a skeleton.
      }
      if (!cancelled) {
        setOnboardingChecked(true);
      }
    }

    void checkOnboarding();
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isLoading, router]);

  // Skeleton while auth state initializes or the onboarding flag is in flight.
  if (isLoading || (isAuthenticated && !onboardingChecked)) {
    return <ShellSkeleton />;
  }

  // D0 登录墙：受保护路由已被 middleware 302 到 /login；能走到这里的未登录访问
  // 只剩白名单页（/contact 等），直接渲染页面内容（不带应用 shell）。
  // 设计应用壳（index.html:90-113）只有 sidebar/topbar/main：登录后的页面不再
  // 渲染 SiteFooter；未登录白名单页保留协议入口。
  if (!isAuthenticated) {
    return (
      <div className="user-ui min-h-dvh bg-canvas">
        <div className="container-page">
          <PublicTopBar />
          {children}
          <SiteFooter />
        </div>
      </div>
    );
  }

  // 壳统一管理安全区和常规流底部导航，内容滚动区不再补固定底栏占位。
  return (
    <div
      className={`user-ui user-shell h-dvh overflow-hidden${immersive ? " is-watch-immersive" : ""}`}
      style={{
        paddingTop: "env(safe-area-inset-top, 0px)",
        paddingBottom: "env(safe-area-inset-bottom, 0px)",
      }}
    >
      {/* 键盘用户的「跳到正文」必须是页面第一个可聚焦元素：放在 Sidebar 之前，
          否则要穿过侧栏 15+ 个停靠点才到它（审计 F3）。目标仍是唯一的主滚动区。 */}
      <a
        href={`#${SCROLL_CONTAINER_ID}`}
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-sm focus:border focus:border-hairline focus:bg-canvas focus:px-4 focus:py-2 focus:text-meta focus:font-semibold focus:text-ink"
      >
        跳到正文
      </a>
      <Sidebar />
      <UnreadCountSync />
      <div className="user-shell-main">
        <TopBar />
        <DeletionBanner />
        <main
          id={SCROLL_CONTAINER_ID}
          tabIndex={-1}
          className={`flex-1 overflow-y-auto custom-scrollbar focus:outline-none${isWatch ? " user-watch-content" : ""}`}
        >
          {/* DEC-075：容器归壳层所有 —— 全站唯一 .container-page 在这里渲染一次，
            页面不再自带容器类。h-full 让页面根的 min-h-full（练习 / 考试 / 搜索等
            满屏流）仍以滚动容器的高度为基准，几何与「页面自己写容器」时一致。 */}
          <div className="container-page h-full">{children}</div>
        </main>
        <WatchShellControls />
        <MobileTabBar />
      </div>
    </div>
  );
}
