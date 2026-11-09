"use client";

import { cn } from "@/lib/utils";
import type { TeachingItem } from "@/types/teaching";

interface Props {
  items: TeachingItem[];
  activeItemId: string | null;
  disabled?: boolean;
  onSelect: (itemId: string) => void;
}

/**
 * One question at a time, with a compact "已答 n/总" strip to switch between them.
 *
 * The strip only renders for a multi-question session: a single-question session
 * keeps the plain page, so this never adds chrome where there is nothing to
 * navigate. State comes from the server projection — an item whose answer history
 * is hidden reports `answered: false`, so no guess can be read off the strip.
 */
export function TeachingQuiz({ items, activeItemId, disabled, onSelect }: Props) {
  if (items.length < 2) return null;
  const answered = items.filter((item) => item.answered).length;
  return (
    <nav aria-label="小测题目" className="space-y-2">
      <p className="text-meta text-muted">
        已答 {answered}/{items.length}
      </p>
      <ol className="flex flex-wrap gap-2">
        {items.map((item, index) => {
          const active = item.id === activeItemId;
          return (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => onSelect(item.id)}
                disabled={disabled}
                aria-current={active ? "true" : undefined}
                className={cn(
                  "flex h-10 min-w-10 items-center justify-center gap-1.5 rounded-md border px-3 text-copy font-semibold transition-colors",
                  active
                    ? "border-action-primary bg-action-primary text-on-primary"
                    : "border-hairline text-body hover:bg-surface-soft",
                  disabled && "opacity-60"
                )}
              >
                第 {index + 1} 题
                {item.correct === true && (
                  <span aria-label="已答对" className="text-caption">
                    ✓
                  </span>
                )}
                {item.correct === false && (
                  <span aria-label="已答错" className="text-caption">
                    ×
                  </span>
                )}
                {item.answered && item.correct === null && (
                  <span aria-label="已作答" className="text-caption">
                    •
                  </span>
                )}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
