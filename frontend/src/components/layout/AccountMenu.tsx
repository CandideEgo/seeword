"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronsUpDown, HelpCircle, LogOut, Moon, Settings, Sun } from "lucide-react";
import { useThemeContext } from "@/components/common/ThemeProvider";
import { Avatar } from "@/components/ui/Avatar";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useAuthStore } from "@/stores/authStore";
import { useProfileStore } from "@/stores/profileStore";
import { cn } from "@/lib/utils";

const LINKS = [{ label: "账户设置", icon: Settings, href: "/profile?tab=settings" }];

export function AccountMenu({
  placement,
  collapsed = false,
}: {
  placement: "sidebar" | "topbar";
  collapsed?: boolean;
}) {
  const pathname = usePathname();
  // Shell breakpoint: sidebar shows ≥1025, bottom tabs + mobile topbar below
  // (matches user-ui.css and WatchTopBar). Must not be 768 or the topbar loses
  // its account menu between 768 and 1024.
  const isDesktop = useMediaQuery("(min-width: 1025px)");
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const me = useProfileStore((s) => s.me);
  const fetchMe = useProfileStore((s) => s.fetchMe);
  const { theme, toggleTheme, mounted } = useThemeContext();
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const panelId = useId();
  const visible = placement === "sidebar" ? isDesktop : !isDesktop;

  useEffect(() => {
    if (visible && user) void fetchMe();
  }, [visible, user, fetchMe]);

  useEffect(() => {
    setOpen(false);
  }, [pathname, visible]);

  useEffect(() => {
    if (!open) return;
    panelRef.current?.querySelector<HTMLElement>("a, button")?.focus();
    function handleOutside(event: PointerEvent) {
      if (!wrapperRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("pointerdown", handleOutside);
    return () => document.removeEventListener("pointerdown", handleOutside);
  }, [open]);

  if (!visible) return null;

  const isSidebar = placement === "sidebar";
  const itemClass =
    "flex min-h-11 w-full items-center gap-2.5 rounded-sm px-3 text-copy text-body transition-colors hover:bg-surface-card hover:text-ink";

  return (
    <div
      ref={wrapperRef}
      className={cn("relative", isSidebar && "w-full")}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape" && open) {
          event.preventDefault();
          setOpen(false);
          triggerRef.current?.focus();
        }
      }}
    >
      <button
        ref={triggerRef}
        type="button"
        aria-label="账号菜单"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        onClick={() => setOpen((value) => !value)}
        className={cn(
          "flex min-h-11 items-center rounded-md transition-colors hover:bg-surface-card",
          isSidebar ? "w-full gap-2.5 px-2 py-2" : "min-w-11 justify-center px-1",
          collapsed && "justify-center px-0"
        )}
      >
        <Avatar src={me?.url} name={user} seed={user?.sub} gender={me?.gender} size="md" />
        {isSidebar && !collapsed && (
          <>
            <span className="min-w-0 flex-1 text-left">
              <span className="block truncate text-meta font-medium text-ink">
                {user?.name || "学习者"}
              </span>
              <span className="block text-caption text-muted">账户设置</span>
            </span>
            <ChevronsUpDown size={14} className="shrink-0 text-muted" aria-hidden />
          </>
        )}
      </button>
      {open && (
        <div
          id={panelId}
          ref={panelRef}
          role="dialog"
          aria-label="账户与常用操作"
          className={cn(
            "absolute z-50 w-56 rounded-lg border border-hairline bg-canvas p-1.5 shadow-lift",
            isSidebar ? "bottom-full left-0 mb-2" : "right-0 top-full mt-2"
          )}
        >
          {LINKS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className={itemClass}
            >
              <item.icon size={16} className="text-muted" aria-hidden />
              {item.label}
            </Link>
          ))}
          <div className="my-1 border-t border-hairline" />
          {mounted && (
            <button type="button" className={itemClass} onClick={toggleTheme} aria-label="切换主题">
              {theme === "dark" ? (
                <Moon size={16} className="text-muted" aria-hidden />
              ) : (
                <Sun size={16} className="text-muted" aria-hidden />
              )}
              外观 · {theme === "dark" ? "深色" : "浅色"}
            </button>
          )}
          <Link href="/contact" onClick={() => setOpen(false)} className={itemClass}>
            <HelpCircle size={16} className="text-muted" aria-hidden />
            帮助与反馈
          </Link>
          <div className="my-1 border-t border-hairline" />
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              logout();
            }}
            className="flex min-h-11 w-full items-center gap-2.5 rounded-sm px-3 text-copy text-muted transition-colors hover:bg-red-soft hover:text-error"
          >
            <LogOut size={16} aria-hidden />
            退出登录
          </button>
        </div>
      )}
    </div>
  );
}
