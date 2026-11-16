"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { lessonHref, type LessonVocabularySource } from "@/lib/lessons";

export function LessonWordSources({ wordId }: { wordId: string }) {
  const [open, setOpen] = useState(false);
  const [sources, setSources] = useState<LessonVocabularySource[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    api<{ sources: LessonVocabularySource[] }>(
      `/api/v1/vocabulary/${encodeURIComponent(wordId)}/sources`,
      {
        signal: controller.signal,
        cache: "no-store",
      }
    ).then(
      (data) => {
        if (!controller.signal.aborted) setSources(data.sources);
      },
      () => {
        if (!controller.signal.aborted) setFailed(true);
      }
    );
    return () => controller.abort();
  }, [wordId, open]);

  return (
    <details
      className="space-y-1.5 text-meta"
      onToggle={(event) => {
        const next = event.currentTarget.open;
        if (next) {
          setSources(null);
          setFailed(false);
        }
        setOpen(next);
      }}
    >
      <summary className="cursor-pointer text-brand-700 hover:underline">课程出处</summary>
      {failed ? (
        <p role="status" className="text-muted">
          课程出处暂不可用
        </p>
      ) : sources === null ? (
        <p role="status" className="text-muted">
          正在读取课程出处…
        </p>
      ) : !sources.length ? (
        <p className="text-muted">暂无课程出处</p>
      ) : (
        <ul className="space-y-1">
          {sources.map((source, index) => (
            <li
              key={JSON.stringify([
                source.lesson_id,
                source.revision_id,
                source.segment_id,
                source.token_ids,
                index,
              ])}
            >
              {source.available ? (
                <Link
                  href={lessonHref(source.lesson_id, source.revision_id, source)}
                  className="text-brand-700 hover:underline"
                >
                  打开原句{sources.length > 1 ? ` ${index + 1}` : ""}
                </Link>
              ) : (
                <span className="text-muted">材料已不可用</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </details>
  );
}
