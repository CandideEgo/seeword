"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Check, RotateCcw, Volume2 } from "lucide-react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { LinkButton } from "@/components/ui/LinkButton";
import { Skeleton } from "@/components/common/SkeletonCard";
import { LessonWordSources } from "@/components/vocabulary/LessonWordSources";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { useSpeech } from "@/hooks/useSpeech";
import { useVocabularyStore } from "@/stores/vocabularyStore";
import { REVIEW_RATINGS, qualityFor, ratingForKey, type ReviewRating } from "@/lib/reviewRating";
import { partOfSpeechLabel, vocabularySource } from "@/lib/vocabularyPresentation";
import type { Paginated, VocabularyWord } from "@/types";

const DEFAULT_BATCH = 10;
const MIN_BATCH = 5;
const MAX_BATCH = 20;

function clampBatch(value: number | null): number {
  if (!value || Number.isNaN(value)) return DEFAULT_BATCH;
  return Math.min(MAX_BATCH, Math.max(MIN_BATCH, Math.round(value)));
}

/**
 * 三档自评复习：认识 / 模糊 / 不认识。
 *
 * 只处理到期复习词（learning / reviewing），新词仍走 /vocabulary/drill 的
 * 学习流程。评分写回 `POST /vocabulary/{id}/review`，调度由后端决定；页面
 * 不展示分数，也不声称“掌握”。
 */
export default function VocabularyReviewPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const searchParams = useSearchParams();
  const batch = clampBatch(Number(searchParams.get("count")));
  const fetchStats = useVocabularyStore((s) => s.fetchStats);
  const dueTotal = useVocabularyStore((s) => s.stats.due_review_count);
  const { speak } = useSpeech();

  const [words, setWords] = useState<VocabularyWord[]>([]);
  const [loading, setLoading] = useState(true);
  const [started, setStarted] = useState(false);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [rating, setRating] = useState<ReviewRating | null>(null);
  const [counts, setCounts] = useState<Record<ReviewRating, number>>({
    known: 0,
    hard: 0,
    unknown: 0,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextButtonRef = useRef<HTMLButtonElement>(null);
  const pendingReview = useRef<{ wordId: string; rating: ReviewRating; id: string } | null>(null);

  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    const controller = new AbortController();
    setLoading(true);
    api<Paginated<VocabularyWord>>(
      `/api/v1/vocabulary?due_only=true&mastery=learning,reviewing&page=${1}&page_size=${batch}`,
      { signal: controller.signal }
    )
      .then((data) => {
        if (!controller.signal.aborted) setWords(data.items ?? []);
      })
      .catch((err) => {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "加载失败");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [isAuthenticated, isLoading, batch]);

  const current = words[index] ?? null;
  const done = started && index >= words.length;

  const rate = useCallback(
    async (value: ReviewRating) => {
      if (!current || revealed || saving) return;
      if (
        current.review_operations_enabled &&
        (pendingReview.current?.wordId !== current.id || pendingReview.current.rating !== value)
      ) {
        pendingReview.current = { wordId: current.id, rating: value, id: crypto.randomUUID() };
      }
      setSaving(true);
      try {
        const query = new URLSearchParams({ quality: String(qualityFor(value)) });
        if (current.review_operations_enabled && pendingReview.current) {
          query.set("operation_id", pendingReview.current.id);
        }
        await api(`/api/v1/vocabulary/${current.id}/review?${query}`, {
          method: "POST",
        });
        pendingReview.current = null;
        setRating(value);
        setRevealed(true);
        setCounts((prev) => ({ ...prev, [value]: prev[value] + 1 }));
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "评分失败，请重试");
      } finally {
        setSaving(false);
      }
    },
    [current, revealed, saving]
  );

  const next = useCallback(() => {
    if (!revealed) return;
    setRevealed(false);
    setRating(null);
    setIndex((value) => value + 1);
  }, [revealed]);

  useEffect(() => {
    if (!started || done) return;
    function onKeyDown(event: KeyboardEvent) {
      const tag = (event.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (!revealed) {
        const value = ratingForKey(event.key);
        if (value) {
          event.preventDefault();
          void rate(value);
        }
        return;
      }
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        next();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [started, done, revealed, rate, next]);

  useEffect(() => {
    if (isAuthenticated && !isLoading) void fetchStats();
  }, [isAuthenticated, isLoading, fetchStats]);

  useEffect(() => {
    if (done) void fetchStats();
  }, [done, fetchStats]);

  if (isLoading) return <ReviewSkeleton />;

  return (
    <div className="user-page">
      <PageHeader
        crumb={
          <>
            <Link href="/vocabulary" className="hover:text-ink">
              词汇
            </Link>
            <span aria-hidden>·</span>
            <span>复习</span>
          </>
        }
        title="复习到期词"
        variant="eyebrow"
      />

      {loading ? (
        <ReviewSkeleton />
      ) : error ? (
        <p className="py-16 text-center text-copy text-error">{error}</p>
      ) : done ? (
        <section className="mx-auto max-w-[46rem] py-10 text-center" aria-label="本轮结束">
          <p className="text-caption font-semibold tracking-[0.09em] text-muted">这一轮结束</p>
          <h2 className="mt-2 text-display-sm font-semibold text-ink">
            复习了 {Object.values(counts).reduce((sum, n) => sum + n, 0)} 个词。
          </h2>

          <div className="mx-auto mt-6 grid max-w-md grid-cols-4 gap-2">
            {REVIEW_RATINGS.map((item) => (
              <div key={item.id} className="rounded-md border border-hairline p-3">
                <p className="text-title font-semibold tabular-nums text-ink">{counts[item.id]}</p>
                <p className="mt-0.5 text-caption text-muted">{item.label}</p>
              </div>
            ))}
            <div className="rounded-md border border-hairline p-3">
              <p className="text-title font-semibold tabular-nums text-ink">
                {Math.max(0, words.length - index)}
              </p>
              <p className="mt-0.5 text-caption text-muted">未处理</p>
            </div>
          </div>
          <div className="mt-6 flex justify-center gap-2">
            <LinkButton href="/vocabulary" variant="outline">
              回词汇
            </LinkButton>
            <Button
              icon={RotateCcw}
              onClick={() => {
                setIndex(0);
                setCounts({ known: 0, hard: 0, unknown: 0 });
                setRevealed(false);
                setRating(null);
              }}
            >
              再复习一轮
            </Button>
          </div>
        </section>
      ) : !started ? (
        words.length > 0 ? (
          <section
            className="mt-6 grid max-w-[60rem] gap-4 sm:grid-cols-[1.15fr_1fr]"
            aria-label="开始复习"
          >
            <article className="rounded-lg border border-hairline bg-canvas p-6 sm:p-8">
              <p className="text-caption font-semibold tracking-[0.09em] text-muted">今日到期</p>
              <p className="mt-3 text-[clamp(3rem,7vw,4rem)] font-semibold leading-none tracking-tight text-ink tabular-nums">
                {Math.max(dueTotal, words.length)}
              </p>
              <p className="mt-2 text-copy leading-relaxed text-body">
                个词到期，本轮先过 {words.length}{" "}
                个。先在心里说出它的意思，再选择认识、模糊或不认识。
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                <Button onClick={() => setStarted(true)}>开始复习</Button>
                <LinkButton href="/vocabulary/drill" variant="outline">
                  去新词训练
                </LinkButton>
              </div>
            </article>
            <article className="rounded-lg border border-hairline bg-surface-soft p-6">
              <h2 className="text-copy font-semibold text-ink">三档自评</h2>
              <ul className="mt-3 divide-y divide-hairline">
                {REVIEW_RATINGS.map((item) => (
                  <li key={item.id} className="flex items-baseline justify-between gap-3 py-2.5">
                    <span className="text-copy text-ink">
                      {item.label}
                      <span className="ml-2 text-meta text-muted">{item.hint}</span>
                    </span>
                    <kbd className="rounded-sm border border-hairline bg-canvas px-1.5 text-caption text-muted">
                      {item.key}
                    </kbd>
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-caption leading-relaxed text-muted">
                评分只决定下一次出现的时间，不改掌握标记；新词仍在训练页学习。
              </p>
            </article>
          </section>
        ) : (
          <section className="mx-auto max-w-[46rem] py-16 text-center" aria-label="今日无到期词">
            <p className="text-caption font-semibold tracking-[0.09em] text-muted">今日复习</p>
            <h2 className="mt-2 text-display-sm font-semibold text-ink">今天的到期词已经清空。</h2>

            <div className="mt-6 flex justify-center gap-2">
              <LinkButton href="/vocabulary">去词汇页</LinkButton>
              <LinkButton href="/vocabulary/drill" variant="outline">
                去新词训练
              </LinkButton>
            </div>
          </section>
        )
      ) : current ? (
        <section className="mx-auto max-w-[46rem]" aria-label="复习卡片">
          <div className="flex items-center justify-between text-meta text-muted">
            <span className="tabular-nums">
              第 {index + 1} 个 / 共 {words.length} 个
            </span>
            <span className="tabular-nums">{words.length - index} 个待复习</span>
          </div>
          <div className="mt-2 h-1 overflow-hidden rounded-pill bg-surface-card">
            <div
              className="h-full rounded-pill bg-brand-500 transition-[width] duration-300"
              style={{ width: `${(index / Math.max(1, words.length)) * 100}%` }}
            />
          </div>

          <article className="mt-5 rounded-lg border border-hairline bg-canvas p-6 text-center sm:p-10">
            <p className="text-caption font-semibold tracking-[0.09em] text-muted">到期复习</p>
            <h2 className="mt-4 break-words text-[clamp(2.5rem,6vw,3.5rem)] font-semibold leading-none tracking-tight text-ink">
              {current.word}
            </h2>
            <div className="mt-3 flex items-center justify-center gap-2 text-meta text-muted">
              {current.ipa && <span className="font-mono">{current.ipa}</span>}
              <button
                type="button"
                onClick={() => speak(current.word)}
                aria-label="朗读单词"
                className="grid min-h-8 min-w-8 place-items-center rounded-pill hover:bg-surface-soft hover:text-ink"
              >
                <Volume2 size={16} />
              </button>
            </div>

            {current.context_sentence && (
              <blockquote className="mx-auto mt-5 max-w-xl border-l-2 border-brand-500 pl-3 text-left text-copy leading-relaxed text-body">
                {current.context_sentence}
                {current.video_title && (
                  <footer className="mt-1 text-caption text-muted">
                    {current.video_title}
                    {current.subtitle_start_time != null
                      ? ` · ${Math.floor(current.subtitle_start_time / 60)}:${String(
                          Math.floor(current.subtitle_start_time % 60)
                        ).padStart(2, "0")}`
                      : ""}
                  </footer>
                )}
              </blockquote>
            )}

            {!revealed ? (
              <>
                <p className="mt-6 text-meta text-muted">先在心里说出它的意思，再选择。</p>
                <div className="mt-3 grid gap-2 sm:grid-cols-3">
                  {REVIEW_RATINGS.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      disabled={saving}
                      onClick={() => void rate(item.id)}
                      className="rounded-md border border-hairline px-4 py-3 text-left transition-colors hover:border-hairline-strong hover:bg-surface-soft disabled:opacity-60"
                    >
                      <span className="flex items-center justify-between">
                        <span className="text-copy font-semibold text-ink">{item.label}</span>
                        <kbd className="rounded-sm border border-hairline px-1.5 text-caption text-muted">
                          {item.key}
                        </kbd>
                      </span>
                      <span className="mt-0.5 block text-caption text-muted">{item.hint}</span>
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <div className="mt-6">
                <p className="text-copy text-body">
                  {partOfSpeechLabel(current.part_of_speech) && (
                    <span className="mr-1 text-muted">
                      {partOfSpeechLabel(current.part_of_speech)}.
                    </span>
                  )}
                  {current.translation || current.definition || "释义待补充"}
                </p>
                <p className="mt-2 text-meta text-muted">
                  已记为「{REVIEW_RATINGS.find((item) => item.id === rating)?.label}」
                </p>
                <Button ref={nextButtonRef} className="mt-4" icon={Check} onClick={next} autoFocus>
                  下一个
                </Button>
              </div>
            )}

            {vocabularySource(current, "vocabulary") && (
              <Link
                href={vocabularySource(current, "vocabulary")!.href}
                className="mt-5 inline-block text-meta text-brand-700 hover:underline"
              >
                {vocabularySource(current, "vocabulary")!.label}
              </Link>
            )}
            {current.has_lesson_sources && (
              <div className="mt-4">
                <LessonWordSources key={current.id} wordId={current.id} />
              </div>
            )}
          </article>
        </section>
      ) : null}
    </div>
  );
}

function ReviewSkeleton() {
  return (
    <div className="mx-auto max-w-[54rem] py-8">
      <Skeleton className="h-3 w-24 rounded-pill" />
      <Skeleton className="mt-6 h-52 w-full rounded-lg" />
      <div className="mt-4 grid gap-2 sm:grid-cols-3">
        <Skeleton className="h-16 rounded-md" />
        <Skeleton className="h-16 rounded-md" />
        <Skeleton className="h-16 rounded-md" />
      </div>
    </div>
  );
}
