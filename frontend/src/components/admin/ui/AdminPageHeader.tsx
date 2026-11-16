"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface AdminPageHeaderProps {
  /** 页面标题（h1）。允许 ReactNode：频道管理等页面在标题里带图标。 */
  title: ReactNode;
  description?: string;
  actions?: ReactNode;
  className?: string;
}

export function AdminPageHeader({ title, description, actions, className }: AdminPageHeaderProps) {
  return (
    <div
      className={cn(
        "admin-page-header flex flex-wrap items-end justify-between gap-x-4 gap-y-3 border-b border-hairline pb-5",
        className
      )}
    >
      <div className="min-w-0">
        <h1 className="text-display-sm font-semibold tracking-tight text-ink">{title}</h1>
        {description && <p className="mt-1 text-copy text-muted">{description}</p>}
      </div>
      {/* 窄屏下按钮组自己也要能换行：否则两个以上操作会把页头撑出横向滚动 */}
      {actions && (
        <div className="flex flex-wrap items-center justify-end gap-2 sm:gap-3">{actions}</div>
      )}
    </div>
  );
}
