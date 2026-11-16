"use client";

import { Tabs as TabsPrimitive } from "@base-ui/react/tabs";
import { cn } from "@/lib/utils";

/**
 * Base UI Tabs 的薄封装：`role="tablist" / tab / tabpanel` 关联、
 * 左右方向键切换（自动激活，`activateOnFocus` 默认 true）、Home / End、
 * `aria-selected` 与 roving tabindex 都由原语负责。
 *
 * 与 `ui/TabPills` / `ui/ToggleGroup` 的分工：
 * - 这里只给「多个互斥视图，每个视图是一块内容」用——切换后显示不同面板；
 * - 筛选条件（同一份内容的某个维度）用 `ui/ToggleGroup`；
 * - `TabPills` 仍是纯视觉的分段控件，不提供面板关联。
 *
 * 视觉留给调用方：按钮的激活态用 `data-active:` 变体、面板用 `data-active:`
 * 或直接由原语按 `value` 挂载。
 */

export function Tabs(props: TabsPrimitive.Root.Props) {
  return <TabsPrimitive.Root data-slot="tabs" {...props} />;
}

export function TabsList({
  className,
  activateOnFocus = true,
  ...props
}: TabsPrimitive.List.Props) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      activateOnFocus={activateOnFocus}
      className={cn("sw-tabs-list outline-none", className)}
      {...props}
    />
  );
}

export function TabsTab({ className, ...props }: TabsPrimitive.Tab.Props) {
  return (
    <TabsPrimitive.Tab
      data-slot="tabs-tab"
      className={cn(
        "cursor-pointer outline-none focus-visible:ring-[3px] focus-visible:ring-focus-ring",
        className
      )}
      {...props}
    />
  );
}

export function TabsPanel({ className, ...props }: TabsPrimitive.Panel.Props) {
  return (
    <TabsPrimitive.Panel
      data-slot="tabs-panel"
      // 切换面板 = 卸旧装新（keepMounted 默认 false），所以这里挂一次性进场；
      // 旧面板的退场是瞬时的 —— 面板内容通常不透明，留住它会和新的重叠。
      className={cn("motion-rise-in outline-none", className)}
      {...props}
    />
  );
}
