"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";
import { useVocabularyStore } from "@/stores/vocabularyStore";
import { MAIN_NAV, mobileNavigationActive } from "@/lib/navigation";

/** 手机底部导航与桌面侧栏共用五个**一级**入口，顺序和页面归属一致。 */
const TABS = MAIN_NAV;

export function MobileTabBar() {
  const pathname = usePathname();
  const dueCount = useVocabularyStore((s) => s.stats.due_review_count);
  const [mounted, setMounted] = useState(false);

  // 作答流程为全屏考试模式：ExamRunner 自带底部交卷栏，
  // 两个 fixed bottom 底栏叠加会遮挡末尾选项。
  // 单词训练 drill 与词单过筛 sieve 同为全屏沉浸流程（880px 壳 + 自带 sticky 头），
  // 一并隐藏；此前只隐藏 drill，sieve 底部仍压着全局底栏。
  const isExamFlow =
    pathname.startsWith("/practice/daily") ||
    pathname.startsWith("/practice/exams/redo") ||
    /^\/practice\/exams\/[^/]+$/.test(pathname) ||
    pathname.startsWith("/vocabulary/drill") ||
    (pathname.startsWith("/vocabulary/sets/") && pathname.endsWith("/sieve"));

  useEffect(() => {
    setMounted(true);
  }, []);

  function isActive(href: string) {
    return mobileNavigationActive(pathname, href);
  }

  if (isExamFlow) return null;

  // 底栏是壳里的常规流元素，**不是** `fixed bottom-0`：
  // iOS Safari 上 fixed 锚的是 layout viewport（= 工具栏收起时的高度 100lvh），
  // 地址栏一出来可视区只剩 100dvh（少 40px），底栏就比可视区底边低 40px、压在地址栏上。
  // 壳是 `h-dvh` 的 flex column，让底栏 in-flow 收尾就永远贴在可视区底边；
  // 底部安全区（Home indicator）由壳自己的 padding 兜住，这里不再重复留。
  return (
    <nav
      data-testid="mobile-tab-bar"
      aria-label="底部导航"
      className="user-mobile-tabs z-40 shrink-0 border-t border-hairline bg-canvas"
    >
      <div className="grid grid-cols-5">
        {TABS.map((tab) => {
          const active = isActive(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "relative flex min-h-[60px] flex-col items-center justify-center gap-0.5 transition-colors",
                active ? "text-brand-700" : "text-muted hover:text-ink"
              )}
            >
              <div className="relative">
                <tab.icon size={20} />
                {/* 计数徽标走主色（S8-1）：与 TopBar 到期词徽标同一语言；error 红只留给真错误态 */}
                {tab.showBadge && mounted && dueCount > 0 && (
                  <span className="absolute -top-1.5 -right-2 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-action-primary px-1 text-caption font-bold leading-none text-on-primary">
                    {dueCount > 99 ? "99+" : dueCount}
                  </span>
                )}
              </div>
              <span className="text-caption font-medium">{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
