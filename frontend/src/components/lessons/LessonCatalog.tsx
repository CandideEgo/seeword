"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, BookOpen, Clapperboard, Search } from "lucide-react";
import { Button } from "@astryxdesign/core/Button";
import { TextInput } from "@astryxdesign/core/TextInput";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { InlineSpinner } from "@/components/common/Spinner";
import { LessonHistory } from "@/components/lessons/LessonHistory";
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
    <div className="user-page lesson-library mx-auto max-w-6xl space-y-8">
      <PageHeader title="视频课程" />
      <form
        role="search"
        aria-label="课程检索"
        className="lesson-search flex items-end gap-3"
        onSubmit={(event) => {
          event.preventDefault();
          setRequest({ query: input.trim(), offset: 0 });
        }}
      >
        <TextInput
          type="search"
          label="搜索课程"
          isLabelHidden
          placeholder="搜索课程"
          value={input}
          onChange={setInput}
          startIcon={Search}
          size="lg"
          width="100%"
        />
        <Button type="submit" label="搜索" variant="primary" size="lg" className="shrink-0" />
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
        <ul className="lesson-catalog-grid">
          {page.items.map((lesson) => (
            <li key={lesson.lesson_id}>
              <Link
                href={lessonHref(lesson.lesson_id, lesson.revision_id)}
                className="lesson-catalog-item group"
              >
                <span className="lesson-catalog-icon">
                  <Clapperboard size={22} aria-hidden />
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
            label="上一页"
            variant="secondary"
            size="sm"
            isDisabled={offset === 0}
            onClick={() => onPage(Math.max(0, offset - LESSON_CATALOG_PAGE_SIZE))}
          />
          {page && (
            <span className="text-meta text-muted tabular-nums">
              第 {formatCount(Math.floor(offset / LESSON_CATALOG_PAGE_SIZE) + 1)} 页
            </span>
          )}
          <Button
            label="下一页"
            variant="secondary"
            size="sm"
            isDisabled={page === null || error !== null || offset + page.limit >= page.total}
            onClick={() => onPage(offset + LESSON_CATALOG_PAGE_SIZE)}
          />
        </nav>
      )}
    </section>
  );
}
