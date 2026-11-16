"use client";

import { cn } from "@/lib/utils";

/** Shared answer controls; the caller owns exam or teaching submission. */
export function ExamAnswerOptions({
  options,
  value,
  onChange,
  disabled,
  label,
}: {
  options: Record<string, string>;
  value: string;
  onChange: (answer: string) => void;
  disabled?: boolean;
  label: string;
}) {
  return (
    <div className="mt-3 space-y-2" role="group" aria-label={label}>
      {Object.entries(options).map(([key, text]) => (
        <button
          type="button"
          key={key}
          data-testid="exam-option"
          aria-pressed={value === key}
          disabled={disabled}
          onClick={() => onChange(key)}
          className={cn(
            "exam-answer flex min-h-14 w-full items-start gap-3 rounded-md border p-4 text-left text-copy leading-relaxed text-ink transition-colors disabled:cursor-not-allowed disabled:opacity-60",
            value === key
              ? "border-brand-500 bg-brand-50"
              : "border-hairline bg-canvas hover:border-hairline-strong"
          )}
        >
          <span className="flex size-7 shrink-0 items-center justify-center rounded-sm border border-current/20 text-meta font-semibold">
            {key}
          </span>
          <span className="min-w-0 break-words">{text}</span>
          <span className="sr-only">{value === key ? "已选择" : "未选择"}</span>
        </button>
      ))}
    </div>
  );
}
