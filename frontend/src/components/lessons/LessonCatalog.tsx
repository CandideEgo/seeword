"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, BookOpen, Clapperboard } from "lucide-react";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { InlineSpinner } from "@/components/common/Spinner";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { ApiClientError } from "@/lib/createApiClient";
import { formatTime } from "@/lib/format";
import { lessonHref, type LessonHistoryItem, type LessonSummary } from "@/lib/lessons";

export function LessonCatalog() {
  const [retry, setRetry] = useState(0);
  const [lessons, setLessons] = useState<LessonSummary[] | null>(null);
  const [error, setError] = useState<number | null>(null);
  const [history, setHistory] = useState<LessonHistoryItem[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    api<{ lessons: LessonSummary[] }>("/api/v1/lessons", {
      signal: controller.signal,
      cache: "no-store",
    })
      .then((data) => {
        setLessons(data.lessons);
        setError(null);
      })
      .catch((failure: unknown) => {
        if (!controller.signal.aborted) {
          setLessons(null);
          setError(failure instanceof ApiClientError ? failure.status : 0);
        }
      });
    api<{ items: LessonHistoryItem[] }>("/api/v1/lessons/_history", {
      signal: controller.signal,
      cache: "no-store",
    }).then(
      (result) => {
        if (!controller.signal.aborted) setHistory(result.items);
      },
      () => {}
    );
    return () => controller.abort();
  }, [retry]);

  return (
    <div className="mx-auto max-w-4xl space-y-7 py-6 sm:py-9">
      <PageHeader title="视频课程" />
      {error === 503 ? (
        <EmptyState icon={BookOpen} title="课程试点暂未开放" />
      ) : error !== null ? (
        <ErrorState title="课程目录加载失败" onRetry={() => setRetry((count) => count + 1)} />
      ) : lessons === null ? (
        <div role="status" aria-label="正在加载课程" className="flex justify-center py-16">
          <InlineSpinner />
        </div>
      ) : !lessons.length ? (
        <EmptyState icon={BookOpen} title="暂无已发布课程" />
      ) : (
        <ul className="divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface-card">
          {lessons.map((lesson) => (
            <li key={lesson.lesson_id}>
              <Link
                href={lessonHref(lesson.lesson_id)}
                className="group flex min-w-0 items-center gap-4 px-4 py-5 transition-colors hover:bg-surface-soft sm:px-6"
              >
                <span className="grid size-12 shrink-0 place-items-center rounded-md bg-surface-soft text-brand-700">
                  <Clapperboard size={21} aria-hidden />
                </span>
                <span className="min-w-0 flex-1">
                  <span lang="en" className="block text-title font-semibold break-words text-ink">
                    {lesson.title}
                  </span>
                  <span className="mt-1 block text-meta text-muted">
                    {lesson.access_mode === "provider_embed" ? "站内播放" : "原站观看"}
                  </span>
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
      {history.length > 0 && (
        <section aria-labelledby="lesson-history-title" className="space-y-3">
          <h2 id="lesson-history-title" className="text-title font-semibold text-ink">
            学习历史
          </h2>
          <ul className="divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface-card">
            {history.map((item) => (
              <li key={item.lesson_id}>
                <Link
                  // A withdrawn revision would answer 410; open the lesson so the
                  // catalog can show whatever is published now instead.
                  href={lessonHref(item.lesson_id, item.available ? item.revision_id : null)}
                  className="flex min-w-0 flex-wrap items-center justify-between gap-x-4 gap-y-1 px-4 py-3 hover:bg-surface-soft"
                >
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
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
