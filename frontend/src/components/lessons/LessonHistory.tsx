"use client";

import { useEffect, useId, useState } from "react";
import Link from "next/link";
import { BookOpen } from "lucide-react";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { InlineSpinner } from "@/components/common/Spinner";
import { Button } from "@/components/ui/Button";
import { ApiClientError } from "@/lib/createApiClient";
import { formatTime } from "@/lib/format";
import {
  getLessonHistoryPage,
  lessonHistoryHref,
  LESSON_HISTORY_PAGE_SIZE,
} from "@/lib/lessonHistory";

type HistoryPage = Awaited<ReturnType<typeof getLessonHistoryPage>>;

export function LessonHistory() {
  const [offset, setOffset] = useState(0);
  const titleId = useId();
  return (
    <section aria-labelledby={titleId} className="space-y-3">
      <h2 id={titleId} className="text-title font-semibold text-ink">
        课程学习历史
      </h2>
      <HistoryPageContent key={offset} offset={offset} onPage={setOffset} />
    </section>
  );
}

function HistoryPageContent({
  offset,
  onPage,
}: {
  offset: number;
  onPage: (offset: number) => void;
}) {
  const [page, setPage] = useState<HistoryPage | null>(null);
  const [error, setError] = useState<number | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getLessonHistoryPage(offset, controller.signal).then(
      (result) => {
        if (!controller.signal.aborted) setPage(result);
      },
      (failure: unknown) => {
        if (!controller.signal.aborted) {
          setError(failure instanceof ApiClientError ? failure.status : 0);
        }
      }
    );
    return () => controller.abort();
  }, [offset, retry]);

  return (
    <div className="space-y-3">
      {error === 503 ? (
        <EmptyState icon={BookOpen} title="课程试点暂未开放" className="py-8" />
      ) : error !== null ? (
        <ErrorState
          title="课程历史加载失败"
          className="py-8"
          onRetry={() => {
            setError(null);
            setRetry((value) => value + 1);
          }}
        />
      ) : page === null ? (
        <div role="status" aria-label="正在加载课程历史" className="flex justify-center py-8">
          <InlineSpinner />
        </div>
      ) : !page.items.length ? (
        <EmptyState icon={BookOpen} title="暂无课程学习记录" className="py-8" />
      ) : (
        <ul className="divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface-card">
          {page.items.map((item) => {
            const href = lessonHistoryHref(item);
            const content = (
              <>
                <span className="min-w-0 break-words font-medium text-ink">
                  {item.available ? item.title : "材料已不可用"}
                </span>
                <span className="text-meta text-muted tabular-nums">
                  {item.completed
                    ? "已学完"
                    : item.position_ms === null
                      ? "已开始"
                      : `进度 ${formatTime(item.position_ms / 1000)}`}
                </span>
              </>
            );
            const rowClass =
              "flex min-w-0 flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-3";
            return (
              <li key={item.lesson_id}>
                {href ? (
                  <Link href={href} className={`${rowClass} hover:bg-surface-soft`}>
                    {content}
                  </Link>
                ) : (
                  <div className={rowClass}>{content}</div>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {(offset > 0 || page?.hasMore) && (
        <nav aria-label="课程历史分页" className="flex items-center justify-between gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0}
            onClick={() => onPage(Math.max(0, offset - LESSON_HISTORY_PAGE_SIZE))}
          >
            上一页
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={!page?.hasMore || error !== null}
            onClick={() => onPage(offset + LESSON_HISTORY_PAGE_SIZE)}
          >
            下一页
          </Button>
        </nav>
      )}
    </div>
  );
}
