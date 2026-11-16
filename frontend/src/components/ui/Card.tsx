"use client";

import type { ElementType, ReactNode } from "react";
import { cn } from "@/lib/utils";

export type CardVariant = "outline" | "surface" | "soft" | "dark";
export type CardPadding = 0 | 3 | 4 | 5 | 6;

const VARIANT: Record<CardVariant, string> = {
  outline: "bg-canvas border border-hairline",
  surface: "bg-surface-card border border-hairline",
  soft: "bg-surface-soft border border-hairline",
  dark: "bg-surface-dark text-on-dark",
};

const PADDING: Record<CardPadding, string> = {
  0: "",
  3: "p-3",
  4: "p-4",
  5: "p-5",
  6: "p-6",
};

/**
 * Card primitive — the only home for a card face (DEC-075 §5 P5). Replaces the
 * `.card-outline`/`.card-soft`/`.card-dark` CSS `@apply` classes plus the `!p-*`
 * padding overrides that fought them, and the hand-rolled card-face class
 * strings (`rounded…` + `border-hairline` + `bg…`) scattered across pages.
 *
 * - `variant` picks the surface: `outline` 画布白 / `surface` 卡片灰
 *   （`--color-surface-card` 这个名字的家就在这里）/ `soft` / `dark`。
 * - `padding` (default 6) 吸收 p-3/p-4/p-5/p-6 覆盖；`0` 给「子元素自带内边距」
 *   的列表卡（`.divide-y` 那种）。
 * - 默认不带 hover 抬升：静态面板（后台 section、统计卡）不该「不是链接却会浮起来」。
 *   可点卡片的 hover（边框/底色/阴影）写在各自的 `className` 里，语义留在调用点。
 * - 圆角固定 `rounded-md`（DEC-075 §4.1：卡片与面板的默认）；弹层/抽屉/大容器
 *   用 `rounded-lg`，它们不该走这个 primitive。
 * - `children` 可选：加载骨架（空占位盒）也复用同一个卡面，免得骨架与加载后的
 *   圆角/边框各写一份而漂移。
 * - Polymorphic via `as` for semantic tags (section/article/div/form).
 */
export function Card({
  variant = "outline",
  padding = 6,
  as: Tag = "div",
  className,
  children,
  ...props
}: {
  variant?: CardVariant;
  padding?: CardPadding;
  as?: ElementType;
  className?: string;
  children?: ReactNode;
} & Omit<React.ComponentPropsWithoutRef<ElementType>, "className" | "children">) {
  return (
    <Tag
      className={cn(
        "sw-card rounded-md transition-colors duration-150",
        VARIANT[variant],
        PADDING[padding],
        className
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}
