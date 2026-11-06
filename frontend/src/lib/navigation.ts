import { Bell, BookOpen, Bookmark, GraduationCap, History, Home, Layers, User } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** 仅一级：Ctrl/Cmd+数字 跳转由 TopBar 消费。 */
  shortcut?: string;
  /** 仅底栏消费。 */
  showBadge?: boolean;
}

/** 一级：桌面侧栏与手机底栏共用。 */
export const MAIN_NAV: NavItem[] = [
  { label: "发现", href: "/", icon: Home, shortcut: "1" },
  { label: "频道", href: "/channels", icon: Layers, shortcut: "2" },
  { label: "练习", href: "/practice", icon: GraduationCap, shortcut: "3" },
  { label: "词汇", href: "/vocabulary", icon: BookOpen, shortcut: "4", showBadge: true },
  { label: "我的", href: "/profile", icon: User, shortcut: "5" },
];

/** 资料库：只出现在桌面侧栏；不进底栏。 */
export const SECONDARY_NAV: NavItem[] = [
  { label: "收藏", href: "/favorites", icon: Bookmark },
  { label: "学习记录", href: "/history", icon: History },
  { label: "通知", href: "/notifications", icon: Bell },
];

/**
 * 归属表：键是导航项 href，值是该导航项认领的路由前缀。
 *
 * - 键必须是导航项的真实 href；表里没有的 href 回退到「自己认领自己」。
 * - `/` 组写成显式清单，**不能**用 `startsWith("/")`：那会吞掉全站、造成双高亮。
 * - 各组的 scope 前缀两两不相交，任意 pathname 最多命中一项。
 * - `/search`（顶栏能力的落地页）刻意不进表 —— 停在它上面不高亮。
 */
export const ACTIVE_SCOPE: Record<string, string[]> = {
  "/": ["/", "/watch", "/rankings"],
  "/channels": ["/channels"],
  "/practice": ["/practice"],
  "/vocabulary": ["/vocabulary"],
  "/profile": ["/profile", "/contact"],
  "/favorites": ["/favorites"],
  "/history": ["/history"],
  "/notifications": ["/notifications"],
};

/** 精确匹配自身，或其子路径（`/watch` 命中 `/watch/1`，不命中 `/watchlist`）。 */
function inScope(pathname: string, route: string): boolean {
  return pathname === route || pathname.startsWith(`${route}/`);
}

export function navigationActive(pathname: string, href: string): boolean {
  const scope = ACTIVE_SCOPE[href] ?? [href];
  return scope.some((route) => inScope(pathname, route));
}
