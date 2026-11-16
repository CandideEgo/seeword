"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface DataTableColumn {
  label: string;
  align?: "right";
}

/**
 * Shared admin table shell. Owns the duplicated chrome every admin list page
 * hand-rolled: the `overflow-x-auto` wrapper, `<table className="w-full
 * text-copy">`, the canonical header row, the `divide-y` body, the empty-state
 * row, and — for expandable tables — the `flatMap([main, expanded && detail])`
 * wiring plus the detail row's `<tr bg-surface-soft/40><td colSpan>` wrapper.
 *
 * Callers keep full control of cell contents via `renderRow` (returns the full
 * `<tr>`) and `renderDetail` (returns inner content; the wrapper is added
 * here). Expand state is caller-owned (`expandedId`) so async-on-expand (e.g.
 * fetching comments) and whole-row-click variants fit without contortion.
 *
 * `emptyContent` 让列表把「失败 / 真空 / 筛选后为空」三态交给页面自绘（默认仍是
 * 一行 `emptyText`）。展开内容的 `<tr>` 会带 `id={`row-detail-${rowKey}`}`，
 * 页面的展开按钮可用 `aria-controls` 指过去。
 */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  loading,
  emptyText,
  emptyContent,
  expandedId,
  renderRow,
  renderDetail,
  className,
}: {
  columns: DataTableColumn[];
  rows: T[];
  rowKey: (item: T) => string;
  loading: boolean;
  emptyText: string;
  /** 有数据为空时的自定义内容（错误/筛选空等）；优先于 `emptyText`。 */
  emptyContent?: ReactNode;
  /** Caller-owned expand state; omit for non-expandable tables. */
  expandedId?: string | null;
  /** Returns the full `<tr>` for a row. `isExpanded` lets the caller render a
   * chevron / lock UI without reading its own state. */
  renderRow: (item: T, isExpanded: boolean) => ReactNode;
  /** Returns the inner content of the detail row. When omitted the table is
   * non-expandable. */
  renderDetail?: (item: T) => ReactNode;
  className?: string;
}) {
  const colSpan = columns.length;
  const expandable = !!renderDetail;

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full text-copy">
        <thead>
          <tr className="border-b border-hairline text-left text-meta text-muted uppercase tracking-wider">
            {columns.map((c, i) => (
              <th
                key={i}
                scope="col"
                className={cn("pb-2 font-medium", c.align === "right" && "text-right")}
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="motion-stagger divide-y divide-hairline">
          {rows.length === 0 ? (
            <tr>
              <td colSpan={colSpan} className={cn(!loading && emptyContent && "p-0")}>
                {loading ? (
                  <div className="py-8 text-center text-muted">加载中...</div>
                ) : emptyContent ? (
                  emptyContent
                ) : (
                  <div className="py-8 text-center text-muted">{emptyText}</div>
                )}
              </td>
            </tr>
          ) : expandable ? (
            rows.flatMap((item) => {
              const id = rowKey(item);
              const isExpanded = expandedId === id;
              return [
                <RowGroup key={id}>
                  {renderRow(item, isExpanded)}
                  {isExpanded && (
                    <tr id={`row-detail-${id}`} className="bg-surface-soft/40">
                      <td colSpan={colSpan} className="p-4">
                        {/* The table scrolls horizontally on phones; without pinning,
                            an expanded editor sits past the fold until the reader
                            scrolls the table sideways. */}
                        <div className="sticky left-0 w-full max-w-[calc(100vw-6rem)] lg:static lg:max-w-none">
                          {renderDetail!(item)}
                        </div>
                      </td>
                    </tr>
                  )}
                </RowGroup>,
              ];
            })
          ) : (
            rows.map((item) => <RowGroup key={rowKey(item)}>{renderRow(item, false)}</RowGroup>)
          )}
        </tbody>
      </table>
    </div>
  );
}

/**
 * A keyed fragment wrapper so `flatMap`/`map` can return a main row plus an
 * optional detail row as a single keyed array element.
 */
function RowGroup({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
