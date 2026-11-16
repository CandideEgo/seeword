"use client";

import type { ReactNode } from "react";
import { Select } from "@base-ui/react/select";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useOverlayContainer } from "@/hooks/useOverlayContainer";

export interface SelectMenuOption<T extends string> {
  value: T;
  label: ReactNode;
}

/**
 * Base UI Select 的薄封装：键盘（方向键 / Home-End / typeahead / Escape）、
 * `aria-expanded` / `aria-activedescendant`、外部点击关闭都由原语负责。
 *
 * 与 `ui/Select`（原生 `<select>` 的样式包装）的分工：
 * - 选项少、要在手机上调起系统选择器 → 继续用 `ui/Select`；
 * - 需要自定义选项排版、要与站内其它弹层视觉一致 → 用这里。
 *
 * 面板挂到 `useOverlayContainer()` 给的容器，跟随 `.user-ui` 品牌作用域。
 *
 * **`modal={false}` 是修 bug 的，不是偏好。** Base UI 默认 `modal=true`：面板打开
 * 期间铺一层全屏 `InternalBackdrop`，让页面其余部分不可点。Escape 在「打开动画
 * 尚未完成」的窗口里按下时，面板不会关，反而卡在打开态、遮罩留在页面上——之后
 * 整页点不动（首页筛选工具条的 e2e 就这样被卡了 60s）。非对话框式的下拉本来也
 * 不该冻结整页，改用非模态后遮罩层根本不存在，这一类失败面随之消失。
 */
export function SelectMenu<T extends string>({
  value,
  onValueChange,
  options,
  id,
  className,
  placeholder,
  disabled,
  "aria-label": ariaLabel,
}: {
  value: T;
  onValueChange: (value: T) => void;
  options: SelectMenuOption<T>[];
  id?: string;
  className?: string;
  placeholder?: string;
  disabled?: boolean;
  "aria-label"?: string;
}) {
  const container = useOverlayContainer();

  return (
    <Select.Root
      items={options}
      value={value}
      modal={false}
      onValueChange={(next) => {
        if (typeof next === "string") onValueChange(next as T);
      }}
      disabled={disabled}
    >
      <Select.Trigger
        id={id}
        aria-label={ariaLabel}
        className={cn(
          "inline-flex min-h-9 items-center justify-between gap-2 rounded-md border border-hairline bg-canvas px-3 text-meta text-ink transition-colors hover:border-ink focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-focus-ring disabled:opacity-50",
          className
        )}
      >
        <Select.Value placeholder={placeholder} />
        <Select.Icon className="text-muted">
          <ChevronDown size={14} aria-hidden />
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal container={container}>
        <Select.Positioner sideOffset={4} alignItemWithTrigger={false} className="z-50">
          <Select.Popup className="overlay-pop min-w-[var(--anchor-width)] origin-[var(--transform-origin)] rounded-lg border border-hairline bg-canvas p-1 text-meta text-ink shadow-card">
            <Select.List className="max-h-72 overflow-y-auto">
              {options.map((option) => (
                <Select.Item
                  key={option.value}
                  value={option.value}
                  className="grid cursor-pointer grid-cols-[1rem_1fr] items-center gap-2 rounded-sm px-2 py-1.5 outline-none select-none data-highlighted:bg-surface-soft"
                >
                  <Select.ItemIndicator className="col-start-1 text-action-primary">
                    <Check size={14} aria-hidden />
                  </Select.ItemIndicator>
                  <Select.ItemText className="col-start-2">{option.label}</Select.ItemText>
                </Select.Item>
              ))}
            </Select.List>
          </Select.Popup>
        </Select.Positioner>
      </Select.Portal>
    </Select.Root>
  );
}
