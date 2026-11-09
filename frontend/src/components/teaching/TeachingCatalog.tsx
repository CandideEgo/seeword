"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { teachingHref } from "@/lib/teaching";
import type { TeachingContent, TeachingSession } from "@/types/teaching";

/** Closed gates omit the private entry; existing practice stays available. */
export function TeachingCatalog() {
  const [contents, setContents] = useState<TeachingContent[]>([]);
  const [sessions, setSessions] = useState<TeachingSession[]>([]);
  const [error, setError] = useState("");
  const [starting, setStarting] = useState<string | null>(null);
  // A quiz is built from one paper's verified questions; grouping the catalog by
  // paper is what makes "为什么这几道题能一起练" answerable without new copy.
  const papers = Array.from(
    contents.reduce((map, content) => {
      const key = content.paper_id ?? "";
      if (!key) return map;
      const entry = map.get(key) ?? { title: content.title, count: 0 };
      map.set(key, { title: entry.title || content.title, count: entry.count + 1 });
      return map;
    }, new Map<string, { title: string; count: number }>())
  ).filter(([, entry]) => entry.count >= 4);

  const startQuiz = async (paperId: string) => {
    if (starting) return;
    setStarting(paperId);
    setError("");
    try {
      const quiz = await api<TeachingSession>("/api/v1/teaching/quizzes", {
        method: "POST",
        body: JSON.stringify({ operation_id: crypto.randomUUID(), paper_id: paperId }),
      });
      window.location.href = teachingHref(
        paperId === "teaching" ? null : paperId,
        quiz.id,
        quiz.current_item_id
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "小测暂时无法开始，请重试。");
    } finally {
      setStarting(null);
    }
  };
  useEffect(() => {
    const controller = new AbortController();
    void Promise.all([
      api<{ items: TeachingContent[] }>("/api/v1/teaching/content", { signal: controller.signal }),
      api<{ items: TeachingSession[] }>("/api/v1/teaching/sessions", { signal: controller.signal }),
    ])
      .then(([catalog, recent]) => {
        setContents(catalog.items);
        setSessions(recent.items);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (
          err instanceof ApiError &&
          ([403, 404].includes(err.status) || err.code === "SERVICE_UNAVAILABLE")
        )
          return;
        setError("单题教学暂时无法加载，稍后重新打开练习页即可重试。");
      });
    return () => controller.abort();
  }, []);
  if (!contents.length && !sessions.length && !error) return null;
  return (
    <section
      className="mb-6 space-y-4 rounded-lg border border-hairline p-4 sm:p-5"
      aria-label="单题教学"
    >
      <div>
        <h2 className="user-sec-title">单题教学 · 私测</h2>
        <p className="mt-1 text-meta text-muted">
          先自己作答，再按需看提示与解析。教学结果单独记录。
        </p>
      </div>
      {error && (
        <p role="status" className="text-meta text-muted">
          {error}
        </p>
      )}
      {!!sessions.length && (
        <ul className="space-y-2">
          {sessions.slice(0, 3).map((session) => (
            <li key={session.id}>
              <Link
                href={teachingHref(null, session.id, session.current_item_id)}
                className="text-copy font-semibold text-brand-700 underline underline-offset-4"
              >
                继续教学 · {session.items?.[0]?.question_key ?? session.id.slice(0, 8)}
              </Link>
            </li>
          ))}
        </ul>
      )}
      {!!papers.length && (
        <ul className="space-y-2">
          {papers.map(([paperId, entry]) => (
            <li key={paperId}>
              <Button
                variant="outline"
                disabled={!!starting}
                loading={starting === paperId}
                onClick={() => void startQuiz(paperId)}
              >
                四题小测 · {entry.title || paperId.slice(0, 8)}
              </Button>
            </li>
          ))}
        </ul>
      )}
      {!!contents.length && (
        <ul className="grid gap-2 sm:grid-cols-2">
          {contents.slice(0, 20).map((content) => (
            <li key={content.id}>
              <Link
                href={`/practice/exams/${encodeURIComponent(content.paper_id ?? "teaching")}?mode=teach&content_revision_id=${encodeURIComponent(content.id)}`}
                className="block rounded-sm border border-hairline p-3 text-copy text-ink transition-colors hover:bg-surface-soft"
              >
                {content.title || content.question_key} · 第 {content.number} 题
                <span className="mt-1 block text-caption text-muted">自动核验内容</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
