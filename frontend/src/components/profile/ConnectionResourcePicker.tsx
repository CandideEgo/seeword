"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { LearningResourceLimits } from "@/lib/learningConnections";
import type { Paginated } from "@/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

interface Choice {
  id: string;
  label: string;
}
type Kind = "lessons" | "words";
const PAGE_SIZE = 8;

export function ConnectionResourcePicker({
  value,
  onChange,
  disabled = false,
}: {
  value: LearningResourceLimits;
  onChange: (value: LearningResourceLimits) => void;
  disabled?: boolean;
}) {
  const [kind, setKind] = useState<Kind>("lessons");
  const [draft, setDraft] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const [retry, setRetry] = useState(0);
  const key = `${kind}:${query}:${page}:${retry}`;
  const [result, setResult] = useState<{
    key: string;
    choices: Choice[];
    more: boolean;
    error?: string;
  } | null>(null);
  const [labels, setLabels] = useState<Record<string, string>>({});

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      try {
        let choices: Choice[], more: boolean;
        if (kind === "lessons") {
          const params = new URLSearchParams({
            q: query,
            delegable_only: "true",
            offset: String(page * PAGE_SIZE),
            limit: String(PAGE_SIZE),
          });
          const data = await api<{ items: { lesson_id: string; title: string }[]; total: number }>(
            `/api/v1/lessons/_search?${params}`,
            { signal: controller.signal }
          );
          choices = data.items.map((item) => ({ id: item.lesson_id, label: item.title }));
          more = (page + 1) * PAGE_SIZE < data.total;
        } else {
          const params = new URLSearchParams({
            q: query,
            page: String(page + 1),
            page_size: String(PAGE_SIZE),
          });
          const data = await api<Paginated<{ id: string; word: string }>>(
            `/api/v1/vocabulary?${params}`,
            { signal: controller.signal }
          );
          choices = data.items.map((item) => ({ id: item.id, label: item.word }));
          more = data.has_more;
        }
        if (controller.signal.aborted) return;
        setLabels((previous) => ({
          ...previous,
          ...Object.fromEntries(choices.map((choice) => [`${kind}:${choice.id}`, choice.label])),
        }));
        setResult({ key, choices, more });
      } catch (error) {
        if (!controller.signal.aborted)
          setResult({
            key,
            choices: [],
            more: false,
            error: error instanceof Error ? error.message : "资料暂时无法读取",
          });
      }
    };
    void load();
    return () => controller.abort();
  }, [kind, query, page, retry, key]);

  const selected = kind === "lessons" ? value.lesson_ids : value.word_ids;
  const toggle = (id: string) => {
    const ids = selected.includes(id)
      ? selected.filter((entry) => entry !== id)
      : [...selected, id];
    onChange({ ...value, [kind === "lessons" ? "lesson_ids" : "word_ids"]: ids });
  };
  const switchKind = (next: Kind) => {
    setKind(next);
    setDraft("");
    setQuery("");
    setPage(0);
  };
  const visible = result?.key === key ? result : null;
  const selectedLabels = [
    ...value.lesson_ids.map((id) => ({ key: `lessons:${id}`, id, kind: "lessons" as const })),
    ...value.word_ids.map((id) => ({ key: `words:${id}`, id, kind: "words" as const })),
  ];

  return (
    <fieldset className="space-y-3" disabled={disabled}>
      <legend className="mb-2 text-meta font-semibold text-ink">允许访问的资料</legend>
      <div className="flex gap-2" aria-label="资料类型">
        <Button
          size="sm"
          variant={kind === "lessons" ? "tonal" : "ghost"}
          aria-pressed={kind === "lessons"}
          onClick={() => switchKind("lessons")}
        >
          课程
        </Button>
        <Button
          size="sm"
          variant={kind === "words" ? "tonal" : "ghost"}
          aria-pressed={kind === "words"}
          onClick={() => switchKind("words")}
        >
          词库
        </Button>
      </div>
      <form
        className="flex items-center gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          setQuery(draft.trim());
          setPage(0);
        }}
      >
        <Input
          type="search"
          aria-label={kind === "lessons" ? "查找授权课程" : "查找授权词语"}
          value={draft}
          maxLength={200}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={kind === "lessons" ? "查找课程" : "查找词语"}
        />
        <Button type="submit" size="sm" variant="outline">
          查找
        </Button>
      </form>
      {visible?.error ? (
        <div role="alert" className="space-y-2">
          <p className="text-meta text-error-text">{visible.error}</p>
          <Button variant="outline" size="sm" onClick={() => setRetry((current) => current + 1)}>
            重新读取资料
          </Button>
        </div>
      ) : !visible ? (
        <p role="status" className="text-meta text-muted">
          正在读取资料…
        </p>
      ) : visible.choices.length ? (
        <ul className="divide-y divide-hairline rounded-sm border border-hairline">
          {visible.choices.map((choice) => (
            <li key={choice.id}>
              <label className="flex cursor-pointer items-center gap-3 px-3 py-3 text-meta text-body hover:bg-surface-soft">
                <input
                  type="checkbox"
                  className="accent-action-primary"
                  checked={selected.includes(choice.id)}
                  disabled={disabled || (!selected.includes(choice.id) && selected.length >= 200)}
                  onChange={() => toggle(choice.id)}
                />
                <span className="min-w-0 break-words">{choice.label}</span>
              </label>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-meta text-muted">没有匹配的{kind === "lessons" ? "课程" : "词语"}</p>
      )}
      {(page > 0 || visible?.more) && (
        <div className="flex gap-2" aria-label="授权资料分页">
          <Button
            variant="ghost"
            size="sm"
            disabled={page === 0 || !visible}
            onClick={() => setPage((current) => current - 1)}
          >
            上一页
          </Button>
          <Button
            variant="ghost"
            size="sm"
            disabled={!visible?.more}
            onClick={() => setPage((current) => current + 1)}
          >
            下一页
          </Button>
        </div>
      )}
      {selectedLabels.length > 0 && (
        <div className="flex flex-wrap gap-1" aria-label="已选择的授权资料">
          {selectedLabels.map((entry) => (
            <Button
              key={entry.key}
              variant="ghost"
              size="sm"
              aria-label={`移除授权：${labels[entry.key] ?? entry.id}`}
              onClick={() =>
                onChange({
                  ...value,
                  [entry.kind === "lessons" ? "lesson_ids" : "word_ids"]: (entry.kind === "lessons"
                    ? value.lesson_ids
                    : value.word_ids
                  ).filter((id) => id !== entry.id),
                })
              }
            >
              {labels[entry.key] ?? entry.id} ×
            </Button>
          ))}
        </div>
      )}
    </fieldset>
  );
}
