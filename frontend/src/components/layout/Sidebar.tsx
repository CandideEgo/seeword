"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { BookOpen, ChevronLeft, ChevronRight, Settings } from "lucide-react";
import { MAIN_NAV, SECONDARY_NAV, navigationActive, type NavItem } from "@/lib/navigation";
import { AccountMenu } from "@/components/layout/AccountMenu";
import { useVocabularyStore } from "@/stores/vocabularyStore";
import { useNotificationStore } from "@/stores/notificationStore";
import { cn } from "@/lib/utils";
import { useLessonAvailability } from "@/hooks/useLessonAvailability";

export function Sidebar() {
  const pathname = usePathname();
  const due = useVocabularyStore((s) => s.stats.due_review_count);
  const unread = useNotificationStore((s) => s.unreadCount);
  const [collapsed, setCollapsed] = useState(false);
  const lessonsEnabled = useLessonAvailability();

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem("seeword-sidebar") === "collapsed");
    } catch {
      /* storage unavailable */
    }
  }, []);

  function renderNavLink(item: NavItem) {
    const active = navigationActive(pathname, item.href);
    const showDue = item.href === "/vocabulary" && due > 0 && !collapsed;
    const showDot = item.href === "/notifications" && unread > 0 && !collapsed;
    return (
      <Link
        key={item.href}
        href={item.href}
        aria-label={item.label}
        title={collapsed ? item.label : undefined}
        aria-current={active ? "page" : undefined}
        className={cn("user-nav-link", active && "is-active")}
      >
        <item.icon size={19} className="shrink-0" />
        {!collapsed && <span className="flex-1">{item.label}</span>}
        {showDue && <span className="user-nav-count">{due > 99 ? "99+" : due}</span>}
        {showDot && <span className="user-nav-dot" aria-label={`${unread} 条未读通知`} />}
      </Link>
    );
  }

  return (
    <aside className={cn("user-sidebar", collapsed && "is-collapsed")} aria-label="主导航">
      <div className="user-sidebar-header flex min-h-16 items-center justify-between gap-1 px-2 py-4">
        <Link href="/" className="flex items-center gap-2.5" aria-label="SeeWord 首页">
          <Image src="/logo.png" alt="" width={28} height={28} className="shrink-0" />
          {!collapsed && (
            <span className="text-[17px] font-semibold tracking-[-0.02em] text-ink">SeeWord</span>
          )}
        </Link>
        <button
          type="button"
          aria-label={collapsed ? "展开导航" : "折叠导航"}
          aria-expanded={!collapsed}
          className="grid min-h-8 min-w-8 place-items-center rounded-sm text-muted hover:bg-surface-card"
          onClick={() => {
            const next = !collapsed;
            setCollapsed(next);
            try {
              localStorage.setItem("seeword-sidebar", next ? "collapsed" : "expanded");
            } catch {
              /* storage unavailable */
            }
          }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-1" aria-label="学习导航">
        {MAIN_NAV.map(renderNavLink)}
        {!collapsed && <p className="user-nav-label">资料库</p>}
        {collapsed && <div className="my-2 border-t border-hairline" role="presentation" />}
        {SECONDARY_NAV.map(renderNavLink)}
        {lessonsEnabled && renderNavLink({ href: "/lessons", label: "视频课程", icon: BookOpen })}
      </nav>

      <div className="shrink-0 border-t border-hairline pt-2 pb-2">
        <div className="flex items-center gap-1">
          <div className="min-w-0 flex-1">
            <AccountMenu placement="sidebar" collapsed={collapsed} />
          </div>
          {!collapsed && (
            <Link
              href="/profile?tab=settings"
              aria-label="账户设置"
              className="grid min-h-9 min-w-9 shrink-0 place-items-center rounded-sm text-muted hover:bg-surface-card hover:text-ink"
            >
              <Settings size={17} />
            </Link>
          )}
        </div>
      </div>
    </aside>
  );
}
