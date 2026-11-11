"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState, useEffect, createContext, useContext } from "react";
import {
  ArrowLeft,
  BarChart3,
  BookOpen,
  ChevronLeft,
  LayoutDashboard,
  LayoutTemplate,
  Megaphone,
  Menu,
  Radio,
  Settings,
  UserCog,
  Video,
  X,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useLessonAvailability } from "@/hooks/useLessonAvailability";

// ---------------------------------------------------------------------------
// Navigation config
// ---------------------------------------------------------------------------

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: number;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

/** 后台侧栏折叠状态的存储键（与用户端 `seeword-sidebar` 分开）。 */
const ADMIN_SIDEBAR_KEY = "seeword-admin-sidebar";

const NAV: NavSection[] = [
  {
    title: "概览",
    items: [{ label: "仪表盘", href: "/admin", icon: LayoutDashboard }],
  },
  {
    title: "内容",
    items: [
      { label: "视频管理", href: "/admin/videos", icon: Video },
      { label: "课程材料", href: "/admin/lessons", icon: BookOpen },
      { label: "首页编排", href: "/admin/home-editorial", icon: LayoutTemplate },
      { label: "频道管理", href: "/admin/channels", icon: Radio },
    ],
  },
  {
    title: "运营",
    items: [
      { label: "用户管理", href: "/admin/users", icon: UserCog },
      { label: "反馈公告", href: "/admin/feedback", icon: Megaphone },
    ],
  },
  {
    title: "数据",
    items: [{ label: "数据统计", href: "/admin/stats", icon: BarChart3 }],
  },
  {
    title: "系统",
    items: [{ label: "系统设置", href: "/admin/settings", icon: Settings }],
  },
];

// ---------------------------------------------------------------------------
// Collapse context
// ---------------------------------------------------------------------------

const CollapseContext = createContext<{ collapsed: boolean; toggle: () => void }>({
  collapsed: false,
  toggle: () => {},
});

export const useSidebarCollapse = () => useContext(CollapseContext);

// ---------------------------------------------------------------------------
// Nav links
// ---------------------------------------------------------------------------

function NavLinks({
  pathname,
  collapsed,
  onClick,
}: {
  pathname: string;
  collapsed: boolean;
  onClick?: () => void;
}) {
  const lessonsEnabled = useLessonAvailability(true, true);
  return (
    <>
      {NAV.map((section) => (
        <div key={section.title} className="mb-4">
          {!collapsed && (
            <div className="mb-1.5 px-3 text-caption font-semibold uppercase tracking-wider text-muted-soft">
              {section.title}
            </div>
          )}
          <div className="flex flex-col gap-0.5">
            {section.items
              .filter((item) => lessonsEnabled || item.href !== "/admin/lessons")
              .map((item) => {
                // 详情页（/admin/videos/123）要保留父级高亮；`/admin` 是精确匹配，
                // 否则所有后台路由都会把「仪表盘」点亮。
                const active =
                  item.href === "/admin"
                    ? pathname === "/admin"
                    : pathname === item.href || pathname.startsWith(`${item.href}/`);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onClick}
                    title={collapsed ? item.label : undefined}
                    aria-current={active ? "page" : undefined}
                    className={cn(
                      "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-copy font-medium transition-all",
                      collapsed && "justify-center px-2",
                      active
                        ? "bg-action-primary text-on-primary shadow-sm"
                        : "text-muted hover:bg-surface-soft hover:text-ink"
                    )}
                  >
                    <Icon className="h-[18px] w-[18px] flex-shrink-0" />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                    {!collapsed && item.badge !== undefined && item.badge > 0 && (
                      <span
                        className={cn(
                          "ml-auto inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-meta font-semibold",
                          active ? "bg-white/20 text-white" : "bg-brand-100 text-brand-700"
                        )}
                      >
                        {item.badge}
                      </span>
                    )}
                    {collapsed && item.badge !== undefined && item.badge > 0 && (
                      <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-brand-500" />
                    )}
                  </Link>
                );
              })}
          </div>
        </div>
      ))}
    </>
  );
}

// ---------------------------------------------------------------------------
// Brand
// ---------------------------------------------------------------------------

function Brand({ collapsed }: { collapsed: boolean }) {
  return (
    <Link
      href="/admin"
      className={cn(
        "flex h-16 items-center gap-2.5 border-b border-hairline px-4",
        collapsed && "justify-center px-2"
      )}
    >
      {/* 品牌标与用户端 TopBar 同源（/logo.png），不再自绘橙色方块 + 白字「S」：
          白字压 brand-500 只有 3.12:1，且两套品牌标会让前后台像两个产品。 */}
      <Image src="/logo.png" alt="" width={32} height={32} className="h-8 w-8" />
      {!collapsed && (
        <div className="leading-tight">
          <div className="text-copy-lg font-display font-bold text-ink">SeeWord</div>
          <div className="text-caption uppercase tracking-wider text-muted-soft">管理后台</div>
        </div>
      )}
    </Link>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AdminSidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  // 与用户端侧栏一致：折叠状态持久化，刷新后不弹回展开。
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem(ADMIN_SIDEBAR_KEY) === "1");
    } catch {
      /* localStorage 不可用时保持展开 */
    }
  }, []);

  const toggle = () => {
    setCollapsed((c) => {
      const next = !c;
      try {
        localStorage.setItem(ADMIN_SIDEBAR_KEY, next ? "1" : "0");
      } catch {
        /* 忽略 */
      }
      return next;
    });
  };

  return (
    <CollapseContext.Provider value={{ collapsed, toggle }}>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-50 md:hidden inline-flex h-10 w-10 items-center justify-center rounded-lg bg-canvas border border-hairline shadow-sm"
        aria-label="打开导航"
      >
        <Menu className="h-5 w-5 text-ink" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      {/* 关闭态仍在 DOM 里（滑出屏幕），若不 inert，10 个离屏链接会留在 Tab 序列
          里；inert 同时移除焦点与无障碍树，只在打开时挂上。 */}
      <aside
        aria-label="后台导航"
        inert={!mobileOpen}
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-canvas border-r border-hairline transform transition-transform duration-300 ease-in-out md:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-hairline px-5">
          <div className="flex items-center gap-2.5">
            <Image src="/logo.png" alt="" width={32} height={32} className="h-8 w-8" />
            <div className="leading-tight">
              <div className="text-copy-lg font-display font-bold text-ink">SeeWord</div>
              <div className="text-caption uppercase tracking-wider text-muted-soft">管理后台</div>
            </div>
          </div>
          <button onClick={() => setMobileOpen(false)} aria-label="关闭导航">
            <X className="h-5 w-5 text-muted" />
          </button>
        </div>
        <nav aria-label="后台导航" className="flex-1 overflow-y-auto px-3 py-4">
          <NavLinks pathname={pathname} collapsed={false} onClick={() => setMobileOpen(false)} />
        </nav>
        <div className="border-t border-hairline p-3">
          <Link
            href="/"
            onClick={() => setMobileOpen(false)}
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-meta text-muted hover:bg-surface-soft hover:text-ink transition-colors"
          >
            <ArrowLeft size={14} />
            返回用户端
          </Link>
        </div>
      </aside>

      {/* Desktop sidebar */}
      <aside
        className={cn(
          "hidden md:flex h-full flex-shrink-0 flex-col border-r border-hairline bg-canvas transition-all duration-300",
          collapsed ? "w-[68px]" : "w-60"
        )}
      >
        <Brand collapsed={collapsed} />

        <nav aria-label="后台导航" className="flex-1 overflow-y-auto px-3 py-4">
          <NavLinks pathname={pathname} collapsed={collapsed} />
        </nav>

        {/* Bottom actions */}
        <div className="border-t border-hairline p-3 space-y-1">
          <Link
            href="/"
            title={collapsed ? "返回用户端" : undefined}
            className={cn(
              "flex items-center gap-2 rounded-lg px-3 py-2 text-meta text-muted hover:bg-surface-soft hover:text-ink transition-colors",
              collapsed && "justify-center px-2"
            )}
          >
            <ArrowLeft size={14} />
            {!collapsed && "返回用户端"}
          </Link>
          <button
            onClick={toggle}
            title={collapsed ? "展开侧栏" : "收起侧栏"}
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-meta text-muted hover:bg-surface-soft hover:text-ink transition-colors",
              collapsed && "justify-center px-2"
            )}
          >
            <ChevronLeft
              size={14}
              className={cn("transition-transform", collapsed && "rotate-180")}
            />
            {!collapsed && "收起侧栏"}
          </button>
        </div>
      </aside>
    </CollapseContext.Provider>
  );
}
