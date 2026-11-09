/**
 * Format a time in seconds to M:SS string (e.g. 90 → "1:30")
 */
export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/**
 * Format a duration in seconds to M:SS string, returning empty for null/0
 */
export function formatDuration(sec: number | null): string {
  if (!sec) return "";
  return formatTime(sec);
}

/**
 * Format a relative time string in Chinese (e.g. "刚刚", "3分钟前", "2天前")
 * Falls back to locale date for dates older than 7 days.
 */
export function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  if (Number.isNaN(then)) return "";
  const diff = Math.max(0, now - then);
  const seconds = Math.floor(diff / 1000);

  if (seconds < 60) return "刚刚";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}分钟前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}天前`;
  // Older than a week — show locale date
  return new Date(dateStr).toLocaleDateString("zh-CN");
}

/**
 * Format a timestamp as a relative *day* label: 今天 / 昨天 / N 天前 / 10月18日.
 * Segment differences are computed on local calendar days, so a record touched
 * at 23:59 and one at 00:01 are "昨天" and "今天" even though both are minutes ago.
 * Returns null for missing/invalid values (callers hide the sentence).
 */
export function formatRelativeDay(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  const startOfDay = (input: Date) =>
    new Date(input.getFullYear(), input.getMonth(), input.getDate()).getTime();
  const days = Math.round((startOfDay(new Date()) - startOfDay(date)) / 86_400_000);
  if (days <= 0) return "今天";
  if (days === 1) return "昨天";
  if (days < 7) return `${days} 天前`;
  return `${date.getMonth() + 1}月${date.getDate()}日`;
}

/**
 * Format a view count to compact string (e.g. 1.2M, 3.4K)
 */
export function formatCount(value: number | null | undefined, locale: "zh" | "en" = "zh"): string {
  if (value == null || !Number.isFinite(value)) return "—";
  const n = Math.max(0, Math.round(value));
  const units: [number, string][] =
    locale === "zh"
      ? [
          [100_000_000, "亿"],
          [10_000, "万"],
        ]
      : [
          [1_000_000_000, "B"],
          [1_000_000, "M"],
          [1_000, "K"],
        ];
  for (const [base, suffix] of units) {
    if (n >= base) return `${Number((n / base).toFixed(1))}${suffix}`;
  }
  return String(n);
}

/** Compatibility alias: all counts now follow one locale-aware formatter. */
export function formatViews(n: number | null): string {
  return formatCount(n);
}

/** `"2026-10-31"` → `"10/31"` — the month/day label used by admin trend axes. */
export function formatMonthDay(value: string): string {
  const date = new Date(value);
  return `${date.getMonth() + 1}/${date.getDate()}`;
}
