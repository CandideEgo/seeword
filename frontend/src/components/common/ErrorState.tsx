"use client";

import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import type { LucideIcon } from "lucide-react";

interface ErrorStateProps {
  /** Error title — default "出错了" */
  title?: string;
  /** Error detail message */
  message?: string;
  /** Icon — default AlertCircle */
  icon?: LucideIcon;
  /** Retry callback. When provided, a "重试" button is shown. */
  onRetry?: () => void;
  /** Custom retry button label — default "重试" */
  retryLabel?: string;
  /** Custom action node (overrides onRetry button) */
  action?: React.ReactNode;
  /** Full-page mode: centers on min-h-dvh bg-canvas */
  fullPage?: boolean;
  /**
   * Render the full-page wrapper as the page's `<main>` landmark. Only the
   * boundaries ABOVE the app shell may set this (app/error.tsx,
   * app/global-error.tsx): inside `(main)` / `(admin)` the shell already owns
   * the single `<main>`, and a second one nests landmarks.
   */
  landmark?: boolean;
  /** Additional classes on the wrapper */
  className?: string;
}

/**
 * Error state display with optional retry action.
 * Use for inline errors (`fullPage={false}`) or full-page errors (`fullPage`).
 */
export function ErrorState({
  title = "出错了",
  message,
  icon: Icon = AlertCircle,
  onRetry,
  retryLabel = "重试",
  action,
  fullPage = false,
  landmark = false,
  className,
}: ErrorStateProps) {
  const content = (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center",
        fullPage ? "" : "py-20",
        className
      )}
    >
      <span className="mb-4 inline-grid size-12 place-items-center rounded-full bg-red-soft text-error">
        <Icon size={24} />
      </span>
      <p className="text-copy font-semibold text-ink">{title}</p>
      {message && <p className="mt-1 max-w-[32rem] text-copy text-muted">{message}</p>}
      {action ? (
        <div className="mt-3 flex flex-wrap items-center justify-center gap-3">{action}</div>
      ) : onRetry ? (
        <Button onClick={onRetry} className="mt-3">
          {retryLabel}
        </Button>
      ) : null}
    </div>
  );

  if (fullPage) {
    const shell = "flex min-h-dvh items-center justify-center bg-canvas";
    // `landmark` is opt-in so a boundary rendered INSIDE the app shell does not
    // nest a second <main> (the shell already provides the only one).
    return landmark ? (
      <main className={shell}>{content}</main>
    ) : (
      <div className={shell}>{content}</div>
    );
  }

  return content;
}
