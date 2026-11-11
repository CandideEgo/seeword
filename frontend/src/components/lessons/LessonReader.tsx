"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowUpRight, BookOpen, Check, Link2, Play, Plus } from "lucide-react";
import { toast } from "sonner";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { InlineSpinner } from "@/components/common/Spinner";
import { Button } from "@/components/ui/Button";
import { LinkButton } from "@/components/ui/LinkButton";
import { PageHeader } from "@/components/ui/PageHeader";
import { LessonTutor } from "@/components/lessons/LessonTutor";
import { useLessonYouTube } from "@/hooks/useLessonYouTube";
import { ApiClientError } from "@/lib/createApiClient";
import { formatTime } from "@/lib/format";
import {
  collectLessonWord,
  getLesson,
  getLessonState,
  getLessonProgress,
  lessonHref,
  lessonWordPieces,
  lessonYouTubeId,
  recordLessonActivity,
  resolveLessonAnchor,
  writeLessonProgress,
  type LessonAnchor,
  type LessonDetail,
  type LessonProgress,
  type LessonVocabulary,
} from "@/lib/lessons";
import { toastApiError } from "@/lib/errors";
import { cn } from "@/lib/utils";
import { WatchProgressQueue, type ProgressSaveState } from "@/lib/watchProgressQueue";
import { createWatchTimeState, flushWatchTime, updateWatchTime } from "@/lib/watchTime";

const attributionLabels = {
  media: "原片",
  transcript: "字幕",
  translation: "翻译",
  vocabulary: "释义",
} as const;

function intervalLabel(start: number, end: number) {
  const seconds = (value: number) => {
    const remainder = value % 1000;
    return `${formatTime(value / 1000)}${remainder ? `.${String(remainder).padStart(3, "0")}` : ""}`;
  };
  return `${seconds(start)} – ${seconds(end)}`;
}

type ReaderState = { lesson: LessonDetail } | { error: number } | null;

export function LessonReader({
  lessonId,
  revision,
  anchor,
  conversationId,
}: {
  lessonId: string;
  revision: string | null;
  anchor: LessonAnchor | null;
  conversationId: string | null;
}) {
  const [state, setState] = useState<ReaderState>(null);
  const [retry, setRetry] = useState(0);
  const [progress, setProgress] = useState<LessonProgress | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    let pinnedRevision = revision;
    let inFlight = false;

    async function refresh(blocking: boolean) {
      if (inFlight || controller.signal.aborted || document.visibilityState === "hidden") return;
      inFlight = true;
      if (blocking) setRefreshing(true);
      try {
        if (pinnedRevision) {
          // The pack is immutable per revision, so revalidation only asks
          // whether this revision is still servable and what it now permits.
          // Re-downloading every segment on a timer is what this avoids.
          const current = await getLessonState(lessonId, pinnedRevision, controller.signal);
          if (controller.signal.aborted) return;
          setState((previous) => {
            if (!previous || !("lesson" in previous)) return previous;
            const lesson = previous.lesson;
            const same =
              lesson.permissions.model_processing === current.permissions.model_processing &&
              lesson.permissions.tutor_enabled === current.permissions.tutor_enabled &&
              lesson.permissions.vocabulary_enabled === current.permissions.vocabulary_enabled;
            return same ? previous : { lesson: { ...lesson, permissions: current.permissions } };
          });
          return;
        }
        const lesson = await getLesson(lessonId, null, controller.signal);
        if (controller.signal.aborted) return;
        pinnedRevision = lesson.revision_id;
        setState({ lesson });
      } catch (error) {
        if (!controller.signal.aborted) {
          setState({ error: error instanceof ApiClientError ? error.status : 0 });
        }
      } finally {
        inFlight = false;
        if (!controller.signal.aborted) setRefreshing(false);
      }
    }

    function revalidateVisible() {
      if (document.visibilityState === "visible") void refresh(true);
    }

    void refresh(false);
    getLessonProgress(lessonId, controller.signal).then(setProgress, () => {});
    document.addEventListener("visibilitychange", revalidateVisible);
    window.addEventListener("pageshow", revalidateVisible);
    const poll = setInterval(() => void refresh(false), 20_000);
    return () => {
      controller.abort();
      document.removeEventListener("visibilitychange", revalidateVisible);
      window.removeEventListener("pageshow", revalidateVisible);
      clearInterval(poll);
    };
  }, [lessonId, revision, retry]);

  if (state && "lesson" in state) {
    return (
      <LessonContent
        key={state.lesson.revision_id}
        lesson={state.lesson}
        anchor={anchor}
        progress={progress}
        onProgress={setProgress}
        refreshing={refreshing}
        conversationId={conversationId}
      />
    );
  }

  const status = state?.error;
  return (
    <div className="mx-auto max-w-5xl space-y-6 py-6 sm:py-9">
      <PageHeader
        title="视频课程"
        crumb={
          <Link href="/lessons" className="inline-flex items-center gap-1 hover:text-ink">
            <ArrowLeft size={14} aria-hidden /> 课程目录
          </Link>
        }
      />
      {status === undefined ? (
        <div role="status" aria-label="正在加载课程" className="flex justify-center py-16">
          <InlineSpinner />
        </div>
      ) : status === 403 || status === 404 || status === 410 || status === 503 ? (
        <EmptyState
          icon={BookOpen}
          title={status === 503 ? "课程试点暂未开放" : "材料已不可用"}
          description={progress?.completed ? "学习状态：已学完" : undefined}
          action={
            <LinkButton variant="outline" href="/lessons">
              返回课程目录
            </LinkButton>
          }
        />
      ) : (
        <ErrorState
          title="课程加载失败"
          onRetry={() => {
            setState(null);
            setRetry((value) => value + 1);
          }}
        />
      )}
    </div>
  );
}

function LessonContent({
  lesson,
  anchor,
  progress,
  onProgress,
  refreshing,
  conversationId,
}: {
  lesson: LessonDetail;
  anchor: LessonAnchor | null;
  progress: LessonProgress | null;
  onProgress: (progress: LessonProgress) => void;
  refreshing: boolean;
  conversationId: string | null;
}) {
  const { lesson_id: lessonId, revision_id: revisionId, pack } = lesson;
  const youtubeId = lessonYouTubeId(pack.media);
  const player = useLessonYouTube(youtubeId);
  const { state: playback, position, seek } = player;
  const [focus, setFocus] = useState<LessonAnchor | null>(anchor);
  const [completionPending, setCompletionPending] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [collected, setCollected] = useState<Set<string>>(() => new Set());
  const [saveState, setSaveState] = useState<ProgressSaveState>("idle");
  const queue = useRef<WatchProgressQueue | null>(null);
  const completionId = useRef<string | null>(null);
  const timeState = useRef(createWatchTimeState());
  const selected = focus && resolveLessonAnchor(pack, focus);
  const explicit = anchor && resolveLessonAnchor(pack, anchor);
  const active =
    position === null
      ? null
      : pack.segments.find((segment) => segment.start_ms <= position && position < segment.end_ms);
  const bySegment = useMemo(() => {
    const entries = new Map<string, LessonVocabulary[]>();
    for (const word of pack.vocabulary) {
      const segment = entries.get(word.segment_id) ?? [];
      segment.push(word);
      entries.set(word.segment_id, segment);
    }
    return entries;
  }, [pack.vocabulary]);
  const chosenWord =
    focus &&
    bySegment
      .get(focus.segment_id)
      ?.find(
        (word) =>
          word.token_ids.length === focus.token_ids.length &&
          word.token_ids.every((token, index) => token === focus.token_ids[index])
      );
  const focusKey = focus ? `${focus.segment_id}:${focus.token_ids.join(",")}` : null;
  const initialFocusKey = anchor ? `${anchor.segment_id}:${anchor.token_ids.join(",")}` : null;
  const tutorAvailable = lesson.permissions.tutor_enabled && lesson.permissions.model_processing;
  const incomingSegmentId = explicit?.segment.id;
  const incomingPosition = explicit?.start_ms;

  useEffect(() => {
    const progressQueue = new WatchProgressQueue(async (value) => {
      await writeLessonProgress(lessonId, revisionId, value);
    }, setSaveState);
    queue.current = progressQueue;
    return () => {
      queue.current = null;
      progressQueue.dispose();
    };
  }, [lessonId, revisionId]);

  const report = useCallback(
    (delta: number) => {
      void recordLessonActivity(lessonId, revisionId, crypto.randomUUID(), {
        event_type: "watch_time",
        delta_s: delta,
      }).catch(() => {});
    },
    [lessonId, revisionId]
  );

  useEffect(() => {
    function update() {
      const result = updateWatchTime(timeState.current, {
        videoId: revisionId,
        playing: playback === "playing",
        visible: document.visibilityState === "visible",
        nowMs: performance.now(),
      });
      timeState.current = result.state;
      if (result.report) report(result.report.deltaSeconds);
    }
    update();
    document.addEventListener("visibilitychange", update);
    const timer = setInterval(update, 1000);
    return () => {
      document.removeEventListener("visibilitychange", update);
      clearInterval(timer);
    };
  }, [playback, report, revisionId]);

  useEffect(() => {
    function flush() {
      const result = flushWatchTime(timeState.current, performance.now());
      timeState.current = result.state;
      if (result.report) report(result.report.deltaSeconds);
    }
    window.addEventListener("pagehide", flush);
    return () => {
      window.removeEventListener("pagehide", flush);
      flush();
    };
  }, [report]);

  useEffect(() => {
    if (position !== null && (playback === "playing" || playback === "ended")) {
      queue.current?.enqueue(Math.min(position, pack.media.duration_ms));
    }
  }, [pack.media.duration_ms, playback, position]);

  useEffect(() => {
    if (incomingSegmentId && incomingPosition !== undefined) {
      seek(incomingPosition);
      document.getElementById(`lesson-line-${incomingSegmentId}`)?.scrollIntoView({
        block: "nearest",
      });
    }
  }, [incomingSegmentId, incomingPosition, seek]);

  const [following, setFollowing] = useState(true);
  const playingSegment = active?.id;
  useEffect(() => {
    if (playingSegment && following && playback === "playing") {
      document.getElementById(`lesson-line-${playingSegment}`)?.scrollIntoView({
        block: "nearest",
      });
    }
  }, [following, playback, playingSegment]);

  function jump(next: LessonAnchor, scroll = false) {
    const resolved = resolveLessonAnchor(pack, next);
    if (!resolved) return;
    setFocus(next);
    seek(resolved.start_ms);
    queue.current?.enqueue(resolved.start_ms);
    if (scroll) {
      document.getElementById(`lesson-line-${next.segment_id}`)?.scrollIntoView({
        block: "nearest",
      });
    }
  }

  async function finish() {
    setCompletionPending(true);
    completionId.current ??= crypto.randomUUID();
    try {
      onProgress(
        await recordLessonActivity(lessonId, revisionId, completionId.current, {
          event_type: "complete",
        })
      );
    } catch {
      toast.error("学习状态保存失败，请重试");
    } finally {
      setCompletionPending(false);
    }
  }

  async function copyAnchor() {
    if (!focus) return;
    try {
      await navigator.clipboard.writeText(
        new URL(lessonHref(lessonId, revisionId, focus), location.origin).href
      );
      toast.success("已复制原句链接");
    } catch {
      toast.error("链接复制失败");
    }
  }

  async function collect() {
    if (!focus || !focusKey || !chosenWord || collected.has(focusKey)) return;
    setCollecting(true);
    try {
      await collectLessonWord(lessonId, revisionId, focus);
      setCollected((words) => new Set(words).add(focusKey));
      toast.success("已加入词库");
    } catch (failure) {
      toastApiError(failure, "收词失败");
    } finally {
      setCollecting(false);
    }
  }

  const source = (
    <LinkButton
      variant="outline"
      size="sm"
      href={pack.media.source_url}
      target="_blank"
      rel="noopener noreferrer"
      icon={ArrowUpRight}
      iconRight
    >
      打开原片
    </LinkButton>
  );
  const resumePosition = progress?.position_ms;
  const resumeSegment =
    resumePosition == null
      ? null
      : pack.segments.findLast((segment) => segment.start_ms <= resumePosition);

  return (
    <div className="mx-auto max-w-6xl space-y-6 py-6 sm:py-9">
      <PageHeader
        title={
          refreshing ? (
            "视频课程"
          ) : (
            <span lang="en" className="break-words">
              {pack.title}
            </span>
          )
        }
        crumb={
          <Link href="/lessons" className="inline-flex items-center gap-1 hover:text-ink">
            <ArrowLeft size={14} aria-hidden /> 课程目录
          </Link>
        }
      />
      {refreshing && (
        <p role="status" className="text-meta text-muted">
          正在核对材料状态…
        </p>
      )}
      <div
        className={cn(
          "grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(17rem,21rem)]",
          refreshing && "hidden"
        )}
      >
        <div className="min-w-0 space-y-6">
          <section aria-label="视频来源" className="space-y-3">
            {youtubeId && (
              <div className="relative grid aspect-video place-items-center overflow-hidden rounded-lg bg-surface-dark text-on-dark">
                <div
                  ref={player.containerRef}
                  className="absolute inset-0 [&>iframe]:h-full [&>iframe]:w-full"
                />
                {playback === "idle" || playback === "failed" ? (
                  <div className="relative flex flex-col items-center gap-3 px-4 text-center">
                    {playback === "failed" && <p role="status">嵌入播放暂不可用</p>}
                    <Button onClick={player.start} variant="secondaryDark" icon={Play}>
                      {playback === "failed" ? "重试嵌入" : "加载 YouTube 播放器"}
                    </Button>
                  </div>
                ) : playback === "loading" ? (
                  <div
                    role="status"
                    aria-label="正在加载播放器"
                    className="pointer-events-none relative"
                  >
                    <InlineSpinner />
                  </div>
                ) : null}
              </div>
            )}
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-hairline bg-surface-card p-3 sm:px-4">
              <span className="text-meta text-muted">
                {pack.media.access_mode === "external_link" ? "原站观看" : "YouTube"}
                <span className="ml-2 tabular-nums">
                  {formatTime(pack.media.duration_ms / 1000)}
                </span>
              </span>
              <div className="flex flex-wrap items-center gap-2">
                {position !== null && (
                  <Button
                    variant={following ? "tonal" : "ghost"}
                    size="sm"
                    aria-pressed={following}
                    onClick={() => setFollowing((value) => !value)}
                  >
                    字幕跟随
                  </Button>
                )}
                {source}
              </div>
            </div>
          </section>

          <section aria-labelledby="lesson-transcript-title">
            <h2 id="lesson-transcript-title" className="mb-3 text-title font-semibold text-ink">
              双语字幕
            </h2>
            {anchor && !explicit && (
              <p role="status" className="mb-3 text-meta text-error">
                这条原句引用已不可用
              </p>
            )}
            <ol className="divide-y divide-hairline overflow-hidden rounded-lg border border-hairline bg-surface-card">
              {pack.segments.map((segment) => (
                <li
                  key={segment.id}
                  id={`lesson-line-${segment.id}`}
                  aria-current={active?.id === segment.id ? "true" : undefined}
                  className={cn(
                    "grid min-w-0 scroll-m-3 gap-1.5 px-3 py-3 sm:grid-cols-[3.8rem_minmax(0,1fr)] sm:gap-3 sm:px-4",
                    (active?.id === segment.id || selected?.segment.id === segment.id) &&
                      "bg-brand-50"
                  )}
                >
                  <Button
                    size="compact"
                    variant="ghost"
                    className="w-fit self-start text-muted tabular-nums"
                    aria-label={`定位到 ${formatTime(segment.start_ms / 1000)}`}
                    onClick={() => jump({ segment_id: segment.id, token_ids: [] })}
                  >
                    {formatTime(segment.start_ms / 1000)}
                  </Button>
                  <div className="min-w-0 space-y-0.5">
                    <p
                      lang="en"
                      className="text-copy-lg leading-relaxed break-words whitespace-pre-wrap text-ink"
                    >
                      {lessonWordPieces(segment).map(({ text, token }, index) => {
                        const phrase =
                          token &&
                          bySegment
                            .get(segment.id)
                            ?.find((item) => item.token_ids.includes(token.id));
                        const current =
                          token?.timing &&
                          position !== null &&
                          token.timing.start_ms <= position &&
                          position < token.timing.end_ms;
                        const pressed =
                          token &&
                          focus?.segment_id === segment.id &&
                          focus.token_ids.includes(token.id);
                        const highlight =
                          (current || pressed) && "rounded-sm bg-brand-100 text-brand-700";
                        return phrase ? (
                          <button
                            key={token.id}
                            type="button"
                            aria-label={`查看 ${phrase.headword} 的释义（${text}）`}
                            aria-pressed={!!pressed}
                            className={cn(
                              "inline cursor-pointer font-medium decoration-brand-400 underline decoration-dotted underline-offset-4 hover:text-brand-700",
                              highlight
                            )}
                            onClick={() => jump(phrase)}
                          >
                            {text}
                          </button>
                        ) : (
                          <span key={token?.id ?? `gap-${index}`} className={cn(highlight)}>
                            {text}
                          </span>
                        );
                      })}
                    </p>
                    <p lang="zh-CN" className="text-copy leading-relaxed break-words text-muted">
                      {segment.translation}
                    </p>
                    {chosenWord && chosenWord.segment_id === segment.id && (
                      <p className="mt-2 break-words text-meta text-brand-700 lg:hidden">
                        {chosenWord.headword} · {chosenWord.gloss}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </div>

        <aside aria-label="课程学习" className="min-w-0 space-y-4 lg:sticky lg:top-5">
          <section className="space-y-3 rounded-lg border border-hairline bg-surface-card p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-title font-semibold text-ink">学习进度</h2>
              {progress?.completed && (
                <span className="flex items-center gap-1 text-meta text-success-text">
                  <Check size={14} />
                  已学完
                </span>
              )}
            </div>
            {resumeSegment && progress?.revision_id === revisionId && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  jump({ segment_id: resumeSegment.id, token_ids: [] }, true);
                  if (resumePosition != null) {
                    seek(resumePosition);
                    queue.current?.enqueue(resumePosition);
                  }
                }}
              >
                继续学习 · {formatTime((resumePosition ?? 0) / 1000)}
              </Button>
            )}
            {progress?.revision_id &&
              progress.revision_id !== revisionId &&
              progress.pointer_available !== false && (
                <LinkButton
                  variant="outline"
                  size="sm"
                  href={lessonHref(lessonId, progress.revision_id)}
                >
                  打开上次学习的修订
                </LinkButton>
              )}
            {!progress?.completed && (
              <Button
                variant="tonal"
                size="sm"
                loading={completionPending}
                onClick={() => void finish()}
              >
                标为学完
              </Button>
            )}
            {saveState === "error" && (
              <p role="status" className="text-meta text-error">
                位置保存失败，定位原句后可重试。
              </p>
            )}
          </section>

          <section
            aria-labelledby="lesson-words-title"
            className="space-y-3 rounded-lg border border-hairline bg-surface-card p-4"
          >
            <h2 id="lesson-words-title" className="text-title font-semibold text-ink">
              语境词义
            </h2>
            {selected && (
              <div aria-live="polite" className="space-y-1.5 rounded-md bg-surface-soft p-3">
                <p lang="en" className="text-copy font-semibold break-words text-ink">
                  {chosenWord?.headword ?? selected.text}
                </p>
                {chosenWord && (
                  <p className="text-copy break-words text-body">{chosenWord.gloss}</p>
                )}
                <p className="text-caption text-muted tabular-nums">
                  {intervalLabel(selected.start_ms, selected.end_ms)}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  <Button
                    variant="ghost"
                    size="compact"
                    icon={Link2}
                    onClick={() => void copyAnchor()}
                  >
                    复制原句链接
                  </Button>
                  {lesson.permissions.vocabulary_enabled && chosenWord && focusKey && (
                    <Button
                      variant="outline"
                      size="compact"
                      icon={collected.has(focusKey) ? Check : Plus}
                      disabled={collected.has(focusKey)}
                      loading={collecting}
                      onClick={() => void collect()}
                    >
                      {collected.has(focusKey) ? "已加入词库" : "加入词库"}
                    </Button>
                  )}
                </div>
              </div>
            )}
            <ul className="flex flex-wrap gap-1.5">
              {pack.vocabulary.map((word) => (
                <li key={`${word.segment_id}:${word.token_ids.join(",")}`} className="max-w-full">
                  <Button
                    variant={word === chosenWord ? "tonal" : "outline"}
                    size="sm"
                    className="break-words"
                    aria-pressed={word === chosenWord}
                    onClick={() => jump(word, true)}
                  >
                    <span lang="en">{word.headword}</span>
                  </Button>
                </li>
              ))}
            </ul>
            {!refreshing && tutorAvailable && focus && focus.token_ids.length > 0 && selected && (
              <LessonTutor
                key={focusKey}
                lessonId={lessonId}
                revisionId={revisionId}
                anchor={focus}
                initialConversation={initialFocusKey === focusKey ? conversationId : null}
                onCitation={(citation) => jump(citation, true)}
              />
            )}
          </section>

          <details className="rounded-lg border border-hairline bg-surface-card p-4 text-meta text-muted">
            <summary className="cursor-pointer font-semibold text-ink">来源与署名</summary>
            <dl className="mt-3 space-y-2">
              {Object.entries(attributionLabels).map(([key, label]) => {
                const item = pack.provenance[key as keyof typeof attributionLabels];
                return (
                  <div key={key} className="break-words">
                    <dt className="font-medium text-ink">{label}</dt>
                    <dd>{item.attribution}</dd>
                    <dd>
                      <a
                        href={item.evidence_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-brand-700 underline"
                      >
                        {item.basis}
                      </a>
                    </dd>
                  </div>
                );
              })}
            </dl>
            {pack.provenance.changes && (
              <p className="mt-2 break-words">{pack.provenance.changes}</p>
            )}
          </details>
        </aside>
      </div>
    </div>
  );
}
