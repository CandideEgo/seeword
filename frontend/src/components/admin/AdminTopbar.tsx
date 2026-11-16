"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, ChevronDown, ClipboardList, ExternalLink, LogOut, ShieldCheck } from "lucide-react";
import { useAdminAuthStore } from "@/stores/adminAuthStore";
import { getUgcPendingCount } from "@/lib/adminData";
import { useVisibilityAwareInterval } from "@/hooks/useVisibilityAwareInterval";
import { AdminBreadcrumb, type BreadcrumbItem } from "./ui/AdminBreadcrumb";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuPortal,
  DropdownMenuPositioner,
  DropdownMenuPopup,
  DropdownMenuItem,
} from "@/components/ui/DropdownMenu";

// ---------------------------------------------------------------------------
// Breadcrumb mapping
// ---------------------------------------------------------------------------

const BREADCRUMBS: Record<string, BreadcrumbItem[]> = {
  "/admin": [{ label: "仪表盘" }],
  "/admin/videos": [{ label: "视频管理" }],
  "/admin/lessons": [{ label: "课程材料" }],
  "/admin/home-editorial": [{ label: "首页编排" }],
  "/admin/channels": [{ label: "频道管理" }],
  "/admin/users": [{ label: "用户管理" }],
  "/admin/feedback": [{ label: "反馈与公告" }],
  "/admin/stats": [{ label: "数据统计" }],
  "/admin/settings": [{ label: "系统设置" }],
};

/** 详情页（`/admin/videos/123`）继承父级面包屑，并补一段当前层级。 */
function resolveBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const exact = BREADCRUMBS[pathname];
  if (exact) return exact;
  const parent = Object.keys(BREADCRUMBS)
    .filter((href) => href !== "/admin" && pathname.startsWith(`${href}/`))
    .sort((a, b) => b.length - a.length)[0];
  if (!parent) return [{ label: "管理后台" }];
  const base = BREADCRUMBS[parent];
  return parent === "/admin/videos" ? [...base, { label: "视频详情" }] : base;
}

// ---------------------------------------------------------------------------
// User dropdown
// ---------------------------------------------------------------------------

function UserMenu({ name }: { name: string }) {
  const logout = useAdminAuthStore((s) => s.logout);
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label="管理员账号菜单"
        className="flex min-h-11 items-center gap-2 rounded-md px-2 py-1.5 text-copy transition-colors hover:bg-surface-soft"
      >
        <span className="flex size-8 items-center justify-center rounded-full bg-brand-100 text-meta font-medium text-brand-700">
          {name.slice(0, 1).toUpperCase()}
        </span>
        <span className="hidden font-medium text-ink sm:block">{name}</span>
        <ChevronDown size={14} className="text-muted" aria-hidden />
      </DropdownMenuTrigger>
      <DropdownMenuPortal>
        <DropdownMenuPositioner align="end" sideOffset={8}>
          <DropdownMenuPopup aria-label="管理员账号操作" className="w-52">
            <div className="border-b border-hairline px-3 py-3">
              <p className="break-words text-copy font-medium text-ink">{name}</p>
              <p className="mt-1 flex items-center gap-1 text-meta text-muted">
                <ShieldCheck size={12} aria-hidden /> 管理员
              </p>
            </div>
            <DropdownMenuItem render={<Link href="/" />}>
              <ExternalLink size={15} aria-hidden /> 访问用户端
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => void logout()} className="text-error">
              <LogOut size={15} aria-hidden /> 退出登录
            </DropdownMenuItem>
          </DropdownMenuPopup>
        </DropdownMenuPositioner>
      </DropdownMenuPortal>
    </DropdownMenu>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AdminTopbar() {
  const pathname = usePathname();
  const authUser = useAdminAuthStore((s) => s.user);
  const [pendingCount, setPendingCount] = useState(0);

  // UGC pending count polling — pauses while the tab is hidden.
  useEffect(() => {
    let cancelled = false;
    async function fetchCount() {
      try {
        const data = await getUgcPendingCount();
        if (!cancelled) setPendingCount(data.total);
      } catch {
        /* silently fail */
      }
    }
    fetchCount();
    return () => {
      cancelled = true;
    };
  }, []);

  useVisibilityAwareInterval(async () => {
    try {
      const data = await getUgcPendingCount();
      setPendingCount(data.total);
    } catch {
      /* silently fail */
    }
  }, 60000);

  const breadcrumbs = resolveBreadcrumbs(pathname);
  const displayName = authUser?.name || "管理员";

  return (
    <header className="flex h-16 flex-shrink-0 items-center justify-between border-b border-hairline bg-canvas px-4 pl-16 md:px-6">
      {/* Left: Breadcrumb — 窄屏（390）必须能让位并截断，否则会挤压右侧操作区
          （frontend-fixes-pages A-23 转交的纯样式修复）。 */}
      <div className="flex min-w-0 items-center gap-4">
        <AdminBreadcrumb
          items={breadcrumbs}
          className="min-w-0 [&_span]:min-w-0 [&_span]:truncate"
        />
      </div>

      {/* Right: Actions */}
      <div className="flex shrink-0 items-center gap-3">
        {/* Pending badge */}
        {pendingCount > 0 && (
          <Link
            href="/admin/videos"
            className="inline-flex items-center gap-1.5 rounded-full bg-brand-50 px-3 py-1.5 text-meta font-semibold text-brand-700 hover:bg-brand-100 transition-colors"
            title="待处理 UGC 视频"
          >
            <ClipboardList size={14} />
            <span className="hidden sm:inline">待处理</span>
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-action-primary px-1 text-caption text-on-primary">
              {pendingCount}
            </span>
          </Link>
        )}

        {/* 反馈与公告：此前是无 handler 的占位铃铛，点了没反应。
            后台没有独立通知中心，真实的「待看消息」就在反馈与公告页。 */}
        <Link
          href="/admin/feedback"
          aria-label="反馈与公告"
          title="反馈与公告"
          className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted hover:bg-surface-soft hover:text-ink transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        >
          <Bell size={18} aria-hidden="true" />
        </Link>

        {/* Divider */}
        <div className="h-6 w-px bg-hairline" />

        {/* User menu */}
        <UserMenu name={displayName} />
      </div>
    </header>
  );
}
