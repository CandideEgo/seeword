import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  /** Override padding — default "py-20" */
  className?: string;
}

/**
 * Empty state keeps a clear next action without playing a decorative entrance.
 */
export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "sw-empty flex flex-col items-center justify-center px-4 py-16 text-center",
        className
      )}
    >
      {Icon && (
        <span className="mb-4 inline-grid size-12 place-items-center rounded-full bg-surface-card text-muted">
          <Icon size={24} />
        </span>
      )}
      <p className="text-copy font-semibold text-ink">{title}</p>
      {description && <p className="mt-1 max-w-[32rem] text-copy text-muted">{description}</p>}
      {action && (
        <div className="mt-3 flex flex-wrap items-center justify-center gap-3">{action}</div>
      )}
    </div>
  );
}
