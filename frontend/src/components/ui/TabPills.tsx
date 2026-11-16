"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/** A single tab item passed to `<TabPills>`. */
export interface TabItem<K extends string = string> {
  /** Unique key for React list rendering. */
  key: K;
  /** Display label. */
  label: ReactNode;
}

/** Active-state visual style for the selected tab. */
export type ActiveStyle = "default" | "dark" | "brand";

/** Size preset controlling padding. */
export type TabSize = "md" | "sm";

/** Visual variants: segmented tabs / bare ghost tabs. */
export type TabVariant = "default" | "ghost";

export interface TabPillsProps<K extends string = string> {
  /** List of tabs to render. */
  tabs: TabItem<K>[];
  /** The key of the currently active tab. */
  activeKey: K;
  /** Called when a tab is clicked. */
  onChange: (key: K) => void;
  /** Additional className for the outer container. */
  className?: string;
  /**
   * Visual variant. Default "default" = segmented pill control (设计 `.tabs`);
   * "ghost" = no background, tighter. 筛选 chip 行用 `ui/ToggleGroup`，不在这里。
   */
  variant?: TabVariant;
  /** Tab shape override. Default "pill"; "rect" = sharper corners. */
  shape?: "pill" | "rect";
  /** Active-state style. "default" = canvas bg + shadow; "dark" = ink bg; "brand" = action bg. */
  activeStyle?: ActiveStyle;
  /** Size preset. "md" = larger pill (tab-pill); "sm" = compact chip (fchip). */
  size?: TabSize;
}

const ACTIVE_CLASSES: Record<ActiveStyle, string> = {
  default: "bg-canvas text-ink shadow-soft",
  dark: "bg-ink text-canvas",
  brand: "bg-action-primary text-on-primary",
};

const SIZE_CLASSES: Record<TabSize, string> = {
  md: "h-8 px-3.5",
  sm: "h-8 px-3",
};

export function TabPills<K extends string = string>({
  tabs,
  activeKey,
  onChange,
  className,
  variant = "default",
  shape = "pill",
  activeStyle = "default",
  size = "md",
}: TabPillsProps<K>) {
  return (
    <div
      className={cn(
        "sw-tab-filters inline-flex gap-1",
        variant === "default" &&
          "flex-wrap items-center rounded-pill border border-hairline bg-surface-soft p-1",
        variant === "ghost" && "flex-nowrap bg-transparent p-0",
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = tab.key === activeKey;
        return (
          <button
            key={tab.key}
            type="button"
            aria-pressed={isActive}
            onClick={() => onChange(tab.key)}
            className={cn(
              // shrink-0 + nowrap：放进 overflow-x-auto 的筛选行时不被压缩成多行/竖排。
              // 移动端把 tab 的高度抬到 44px 触控基线；桌面仍按设计 32px。
              "inline-flex min-h-11 shrink-0 cursor-pointer items-center justify-center whitespace-nowrap transition-colors duration-150 min-[1025px]:min-h-8",
              "rounded-pill text-meta font-medium text-muted",
              !isActive && "hover:text-ink",
              SIZE_CLASSES[size],
              shape === "rect" && "rounded-sm",
              isActive && ACTIVE_CLASSES[activeStyle]
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
