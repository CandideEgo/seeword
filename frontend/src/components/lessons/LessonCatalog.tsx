"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, BookOpen, Clapperboard } from "lucide-react";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { InlineSpinner } from "@/components/common/Spinner";
import { LessonHistory } from "@/components/lessons/LessonHistory";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/ui/PageHeader";
import { ApiClientError } from "@/lib/createApiClient";
import { formatCount } from "@/lib/format";
import {
  LESSON_CATALOG_PAGE_SIZE,
  searchLessonCatalog,
  type LessonCatalogPage,
} from "@/lib/lessonCatalog";
import { lessonHref } from "@/lib/lessons";

export function LessonCatalog() {
  const [input, setInput] = useState("");
  const [request, setRequest] = useState({ query: "", offset: 0 });

  return (
    <div className="mx-auto max-w-4xl space-y-7 py-6 sm:py-9">
      <PageHeader title="视频课程" />
      <form
        role="search"
        aria-label="课程检索"
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          setRequest({ query: input.trim(), offset: 0 });
        }}
      >
        <Input
          type="search"
          aria-label="搜索课程"
          placeholder="搜索课程"
          value={input}
          onChange={(event) => setInput(event.target.value)}
        />
        <Button type="submit" variant="outline" className="shrink-0">
          搜索
        </Button>
      </form>
      <CatalogPage
        key={JSON.stringify(request)}
        query={request.query}
        offset={request.offset}
        onPage={(offset) => setRequest({ ...request, offset })}
      />
      <LessonHistory />
    </div>
  );
}

function CatalogPage({
  query,
  offset,
  onPage,
}: {
  query: string;
  offset: number;
  onPage: (offset: number) => void;
}) {
  const [retry, setRetry] = useState(0);
  const [page, setPage] = useState<LessonCatalogPage | null>(null);
  const [error, setError] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    searchLessonCatalog(query, offset, controller.signal).then(
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
  }, [query, offset, retry]);

  return (
    <section aria-label="课程目录" className="space-y-3">
      {error === 503 ? (
        <EmptyState icon={BookOpen} title="课程试点暂未开放" />
      ) : error !== null ? (
        <ErrorState
          title="课程目录加载失败"
          onRetry={() => {
            setError(null);
            setRetry((count) => count + 1);
          }}
        />
      ) : page === null ? (
        <div role="status" aria-label="正在加载课程" className="flex justify-center py-16">
          <InlineSpinner />
        </div>
      ) : !page.items.length ? (
        <EmptyState icon={BookOpen} title={query ? "未找到匹配课程" : "暂无已发布课程"} />
      ) : (
        <ul className="divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface-card">
          {page.items.map((lesson) => (
            <li key={lesson.lesson_id}>
              <Link
                href={lessonHref(lesson.lesson_id, lesson.revision_id)}
                className="group flex min-w-0 items-center gap-4 px-4 py-5 transition-colors hover:bg-surface-soft sm:px-6"
              >
                <span className="grid size-12 shrink-0 place-items-center rounded-md bg-surface-soft text-brand-700">
                  <Clapperboard size={21} aria-hidden />
                </span>
                <span
                  lang="en"
                  className="min-w-0 flex-1 text-title font-semibold break-words text-ink"
                >
                  {lesson.title}
                </span>
                <ArrowUpRight
                  size={19}
                  className="shrink-0 text-muted group-hover:text-brand-700"
                  aria-hidden
                />
              </Link>
            </li>
          ))}
        </ul>
      )}
      {(offset > 0 || (page && page.total > LESSON_CATALOG_PAGE_SIZE)) && (
        <nav aria-label="课程目录分页" className="flex items-center justify-between gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={offset === 0}
            onClick={() => onPage(Math.max(0, offset - LESSON_CATALOG_PAGE_SIZE))}
          >
            上一页
          </Button>
          {page && (
            <span className="text-meta text-muted tabular-nums">
              第 {formatCount(Math.floor(offset / LESSON_CATALOG_PAGE_SIZE) + 1)} 页
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            disabled={page === null || error !== null || offset + page.limit >= page.total}
            onClick={() => onPage(offset + LESSON_CATALOG_PAGE_SIZE)}
          >
            下一页
          </Button>
        </nav>
      )}
    </section>
  );
}
