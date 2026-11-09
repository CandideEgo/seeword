"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { api, ApiError } from "@/lib/api";
import {
  isActiveRun,
  isTeachingCard,
  mergeTeachingCard,
  teachingHref,
  teachingResumeText,
} from "@/lib/teaching";
import { readTeachingEvents } from "@/lib/teachingStream";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { ExamAnswerOptions } from "@/components/exam/ExamAnswerOptions";
import { TeachingCards } from "@/components/teaching/TeachingCards";
import { TeachingQuiz } from "@/components/teaching/TeachingQuiz";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { FullPageSpinner } from "@/components/common/Spinner";
import { ErrorState } from "@/components/common/ErrorState";
import type {
  TeachingCard,
  TeachingContent,
  TeachingRun,
  TeachingRunCreated,
  TeachingSession,
} from "@/types/teaching";

const RUN_LABEL: Record<string, string> = {
  queued: "正在排队",
  running: "正在整理讲解",
  succeeded: "讲解完成",
  failed: "讲解未完成",
  cancelled: "已取消讲解",
  needs_retry: "题目状态已变化，请重新发起讲解",
};

export function TeachingWorkspace() {
  const search = useSearchParams();
  const router = useRouter();
  const { isAuthenticated, isLoading } = useRequireAuth();
  const sessionId = search.get("teaching_session_id");
  const contentId = search.get("content_revision_id");
  const sourceAnswerId = search.get("source_exam_answer_id");
  const questionId = search.get("question_id");
  const [session, setSession] = useState<TeachingSession | null>(null);
  const [content, setContent] = useState<TeachingContent[]>([]);
  const [answer, setAnswer] = useState("");
  const [message, setMessage] = useState("");
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const [run, setRun] = useState<TeachingRun | null>(null);
  const [streamError, setStreamError] = useState("");
  const [streamRetry, setStreamRetry] = useState(0);
  const [runCards, setRunCards] = useState<TeachingCard[]>([]);
  // The server keeps ``current_item_id`` on the first question of a quiz; which
  // question the learner is *looking at* is client state, so switching must not
  // be written back as a domain change.
  const [selectedItemId, setSelectedItemIdState] = useState<string | null>(null);
  // Mirror of ``selectedItemId`` for the callbacks below: a state updater must
  // stay pure (StrictMode calls it twice) and ``acceptSession`` also needs the
  // current value synchronously to decide the next selection.
  const selectedItem = useRef<string | null>(null);
  const setSelectedItemId = useCallback((value: string | null) => {
    selectedItem.current = value;
    setSelectedItemIdState(value);
  }, []);
  const operations = useRef(new Map<string, string>());
  const activeAction = useRef(false);
  const cursor = useRef({ runId: "", sequence: 0 });
  const currentSession = useRef<TeachingSession | null>(null);

  const acceptSession = useCallback(
    (next: TeachingSession) => {
      currentSession.current = next;
      setSession(next);
      // Keep looking at the same question across a state refresh; fall back to
      // the server's current item only when it disappeared (e.g. new session).
      const previous = selectedItem.current;
      const chosen =
        (previous && next.items.some((i) => i.id === previous) ? previous : null) ??
        next.current_item_id ??
        next.items[0]?.id ??
        null;
      setSelectedItemId(chosen);
      const item = next.items.find((i) => i.id === chosen) ?? next.items[0];
      setAnswer(item?.draft_answer ?? "");
      if (next.latest_run) setRun(next.latest_run);
    },
    [setSelectedItemId]
  );

  const reload = useCallback(async () => {
    const id = currentSession.current?.id ?? sessionId;
    if (!id) return;
    const next = await api<TeachingSession>(`/api/v1/teaching/sessions/${encodeURIComponent(id)}`);
    acceptSession(next);
  }, [sessionId, acceptSession]);

  useEffect(() => {
    if (!isAuthenticated || isLoading) return;
    const controller = new AbortController();
    setError("");
    if (sessionId) {
      void api<TeachingSession>(`/api/v1/teaching/sessions/${encodeURIComponent(sessionId)}`, {
        signal: controller.signal,
      })
        .then(acceptSession)
        .catch((err: unknown) => {
          if (!controller.signal.aborted)
            setError(err instanceof Error ? err.message : "读取教学失败。");
        });
    } else if (!contentId && !sourceAnswerId) {
      const query = questionId ? `?question_id=${encodeURIComponent(questionId)}` : "";
      void api<{ items: TeachingContent[] }>(`/api/v1/teaching/content${query}`, {
        signal: controller.signal,
      })
        .then((data) => setContent(data.items))
        .catch((err: unknown) => {
          if (!controller.signal.aborted)
            setError(err instanceof Error ? err.message : "读取题目失败。");
        });
    }
    return () => controller.abort();
  }, [
    sessionId,
    contentId,
    sourceAnswerId,
    questionId,
    isAuthenticated,
    isLoading,
    retry,
    acceptSession,
  ]);

  const runId = run?.run_id ?? run?.id;
  const runActive = !!run && isActiveRun(run.status);
  useEffect(() => {
    if (!runId || !runActive) return;
    const controller = new AbortController();
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    if (cursor.current.runId !== runId) cursor.current = { runId, sequence: 0 };
    setStreamError("");
    let failures = 0;
    const connect = async () => {
      try {
        const snapshot = await api<TeachingRun>(
          `/api/v1/teaching/runs/${encodeURIComponent(runId)}`,
          { signal: controller.signal }
        );
        if (controller.signal.aborted) return;
        setRun(snapshot);
        setRunCards(snapshot.cards ?? []);
        cursor.current.sequence = snapshot.last_sequence;
        if (!isActiveRun(snapshot.status)) {
          await reload();
          return;
        }
        await readTeachingEvents(
          runId,
          cursor.current.sequence,
          (event) => {
            if (event.sequence <= cursor.current.sequence) return;
            if (event.sequence !== cursor.current.sequence + 1)
              throw new Error("讲解连接正在同步，请稍候。");
            cursor.current.sequence = event.sequence;
            failures = 0;
            setStreamError("");
            if (event.type === "content.restricted") {
              setRunCards([]);
              void reload().catch(() => setError("材料已受限，请重新读取会话。"));
              return;
            }
            const current = currentSession.current;
            if (current && event.session_revision > current.revision)
              void reload().catch(() => setError("题目状态已变化，请重新读取会话。"));
            if (event.type === "card.upsert" && event.payload?.card && current)
              setRunCards((cards) =>
                mergeTeachingCard(cards, event.payload.card, current.id, current.revision)
              );
            if (["run.completed", "run.failed", "run.cancelled"].includes(event.type)) {
              setRun(
                (previous) =>
                  previous && {
                    ...previous,
                    status:
                      event.type === "run.completed"
                        ? "succeeded"
                        : event.type === "run.cancelled"
                          ? "cancelled"
                          : "failed",
                    error_code: event.payload?.code ?? null,
                  }
              );
              void reload().catch(() => {});
            }
          },
          controller.signal
        );
        if (!controller.signal.aborted) reconnectTimer = setTimeout(() => void connect(), 1000);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === "EVENT_CURSOR_EXPIRED") {
          const snapshot = await api<TeachingRun>(
            `/api/v1/teaching/runs/${encodeURIComponent(runId)}`,
            { signal: controller.signal }
          ).catch(() => null);
          if (snapshot && !controller.signal.aborted) {
            setRun(snapshot);
            setRunCards(snapshot.cards ?? []);
          }
          void reload().catch(() => {});
          setStreamError("较早的运行事件已清理，已改为读取保存的结果。");
          return;
        } else if (err instanceof ApiError && [401, 403, 404].includes(err.status)) {
          setStreamError(err.message);
          return;
        }
        failures += 1;
        setStreamError(err instanceof Error ? err.message : "讲解暂时断开，正在重连。");
        if (failures < 5)
          reconnectTimer = setTimeout(() => void connect(), Math.min(1000 * 2 ** failures, 10000));
      }
    };
    void connect();
    return () => {
      controller.abort();
      clearTimeout(reconnectTimer);
    };
  }, [runId, runActive, reload, streamRetry]);

  const operationId = (key: string) => {
    let id = operations.current.get(key);
    if (!id) {
      id = crypto.randomUUID();
      operations.current.set(key, id);
    }
    return id;
  };
  const create = async (revisionId?: string) => {
    if (activeAction.current) return;
    activeAction.current = true;
    setBusy("create");
    setError("");
    const reference = revisionId || contentId;
    const input = reference
      ? { content_revision_id: reference }
      : sourceAnswerId
        ? { source_exam_answer_id: sourceAnswerId }
        : { question_id: questionId };
    const key = JSON.stringify(["create", input]);
    try {
      const next = await api<TeachingSession>("/api/v1/teaching/sessions", {
        method: "POST",
        body: JSON.stringify({ operation_id: operationId(key), ...input }),
      });
      acceptSession(next);
      router.replace(teachingHref(null, next.id, next.current_item_id));
      operations.current.delete(key);
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败，请重试。");
    } finally {
      activeAction.current = false;
      setBusy(null);
    }
  };
  const item =
    session?.items.find((i) => i.id === selectedItemId) ??
    session?.items.find((i) => i.id === session.current_item_id) ??
    session?.items[0];
  const write = async (action: string, input: Record<string, unknown> = {}) => {
    if (!session || !item || activeAction.current) return;
    activeAction.current = true;
    setBusy(action);
    setError("");
    const key = JSON.stringify([session.id, session.revision, action, input]);
    try {
      // One command entry for every explicit action: the quiz card and the page
      // buttons must not grow two write paths (see backend
      // services/teaching/commands.py).
      const next = await api<TeachingSession>(
        `/api/v1/teaching/sessions/${encodeURIComponent(session.id)}/actions`,
        {
          method: "POST",
          body: JSON.stringify({
            operation_id: operationId(key),
            expected_revision: session.revision,
            action,
            // Session-level commands carry no item; the rest act on one question.
            ...(["complete", "abandon"].includes(action) ? {} : { item_id: item.id }),
            ...input,
          }),
        }
      );
      acceptSession(next);
      setRunCards([]);
      operations.current.delete(key);
      if (action === "attempts") {
        // Advance forward from the question just answered (wrapping once), so
        // skipping ahead and coming back does not drag the learner to question
        // one. When answers are hidden from this scope nothing reads as
        // pending, and staying put is the only safe choice.
        const from = next.items.findIndex((i) => i.id === item.id);
        const ordered = [...next.items.slice(from + 1), ...next.items.slice(0, Math.max(from, 0))];
        const pending = ordered.find((i) => !i.answered && i.id !== item.id);
        if (pending) setSelectedItemId(pending.id);
      }
      if (action === "draft") toast.success("草稿已保存");
      if (action === "feedback") {
        setFeedback("");
        toast.success("反馈已记录");
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        await reload().catch(() => {});
        setError("题目已在其他入口更新，已重新读取。请确认当前状态后再操作。");
      } else setError(err instanceof Error ? err.message : "保存失败，请重试。");
    } finally {
      activeAction.current = false;
      setBusy(null);
    }
  };
  const selectItem = (itemId: string) => {
    if (activeAction.current) return;
    setSelectedItemId(itemId);
    const next = session?.items.find((i) => i.id === itemId);
    setAnswer(next?.draft_answer ?? "");
    setError("");
  };
  const startRun = async () => {
    if (!session || !message.trim() || activeAction.current) return;
    activeAction.current = true;
    setBusy("runs");
    setError("");
    const key = JSON.stringify([session.id, session.revision, "runs", message.trim()]);
    try {
      const next = await api<TeachingRunCreated>(
        `/api/v1/teaching/sessions/${encodeURIComponent(session.id)}/runs`,
        {
          method: "POST",
          body: JSON.stringify({
            operation_id: operationId(key),
            expected_revision: session.revision,
            message: message.trim(),
          }),
        }
      );
      setRun({
        id: next.run_id,
        run_id: next.run_id,
        session_id: session.id,
        status: next.status,
        last_sequence: 0,
        cards: [],
        error_code: null,
      });
      setRunCards([]);
      setMessage("");
      operations.current.delete(key);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) await reload().catch(() => {});
      setError(err instanceof Error ? err.message : "暂时无法发起讲解。");
    } finally {
      activeAction.current = false;
      setBusy(null);
    }
  };

  if (isLoading || !isAuthenticated) return <FullPageSpinner />;
  if (sessionId && !session && !error) return <FullPageSpinner />;
  if (!session)
    return (
      <div className="user-page space-y-6">
        <PageHeader
          crumb={<Link href="/practice">返回练习</Link>}
          title="单题教学"
          meta="先独立作答，再选择提示、复答或解析。结果单独记录。"
        />
        {error && (
          <ErrorState
            title="暂时无法开始教学"
            message={error}
            onRetry={() => setRetry((v) => v + 1)}
          />
        )}
        {(contentId || sourceAnswerId) && (
          <Button loading={busy === "create"} onClick={() => void create()}>
            开始这道题的教学
          </Button>
        )}
        {!!content.length && (
          <ul className="space-y-3">
            {content.map((c) => (
              <li key={c.id}>
                <Button variant="outline" disabled={!!busy} onClick={() => void create(c.id)}>
                  {c.title || c.question_key} · 第 {c.number} 题
                </Button>
              </li>
            ))}
          </ul>
        )}
        {!contentId && !sourceAnswerId && !content.length && !error && (
          <p className="text-copy text-muted">当前没有可用的自动核验题目，请稍后返回练习页查看。</p>
        )}
      </div>
    );
  const question = session.cards.find(
    (c) => isTeachingCard(c) && c.kind === "question" && c.item_id === item?.id
  );
  const questionPayload = question?.kind === "question" ? question.payload : null;
  const active = session.status === "active";
  const cards: TeachingCard[] = [
    ...session.cards.filter((c) => c.kind !== "question" && c.kind !== "progress"),
  ];
  for (const c of runCards)
    if (
      c.session_revision === session.revision &&
      c.session_id === session.id &&
      !cards.some((existing) => existing.card_id === c.card_id)
    )
      cards.push(c);
  // Attempts from every item share this list; the panel must describe the item
  // the learner is looking at, not whichever question was answered last.
  const itemAttempts = session.attempts.filter((a) => a.item_id === item?.id);
  const latestAttempt = itemAttempts.at(-1);
  return (
    <div className="user-page space-y-6">
      <PageHeader
        crumb={<Link href="/practice">返回练习</Link>}
        title="单题教学"
        meta="自动核验内容 · 教学结果独立记录"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => void reload().catch((err) => setError(err.message))}
          >
            重新读取
          </Button>
        }
      />
      {error && (
        <div
          role="alert"
          className="rounded-sm border border-error/40 bg-red-soft p-3 text-copy text-error-text"
        >
          {error}
        </div>
      )}
      <TeachingQuiz
        items={session.items}
        activeItemId={item?.id ?? null}
        disabled={!!busy}
        onSelect={selectItem}
      />
      <div className="grid min-w-0 gap-6 lg:grid-cols-2">
        <Card padding={5} className="min-w-0 space-y-5">
          {questionPayload ? (
            <>
              {questionPayload.passage && (
                <section aria-label="原文">
                  <h2 className="user-sec-title mb-3">原文</h2>
                  <p
                    lang="en"
                    className="whitespace-pre-wrap break-words text-copy leading-loose text-body"
                  >
                    {questionPayload.passage}
                  </p>
                </section>
              )}
              <section aria-label="教学题目">
                <h2 className="text-copy font-semibold leading-relaxed text-ink">
                  {questionPayload.question || "请选择答案"}
                </h2>
                <ExamAnswerOptions
                  options={questionPayload.options ?? {}}
                  value={answer}
                  onChange={setAnswer}
                  disabled={!active || !!busy}
                  label="教学题目选项"
                />
              </section>
            </>
          ) : (
            <p role="status" className="text-copy text-muted">
              这道题的材料当前不可展示。已保存的作答仍然保留。
            </p>
          )}
          {latestAttempt && (
            <p role="status" className="text-copy text-body">
              第 {latestAttempt.attempt_no} 次作答：{latestAttempt.answer}，
              {latestAttempt.correct ? "答对了" : "还需再想想"}。
              {latestAttempt.answer_origin === "external_reported"
                ? "来自外部 AI 辅助，独立性未验证。"
                : latestAttempt.role === "initial"
                  ? ""
                  : "已保留此前的反馈与提示记录。"}
            </p>
          )}
          {active && questionPayload && (
            <div className="flex flex-wrap gap-2">
              <Button
                loading={busy === "attempts"}
                disabled={!answer || !!busy}
                onClick={() => void write("attempts", { answer })}
              >
                {itemAttempts.length ? "提交复答" : "提交答案"}
              </Button>
              <Button
                variant="outline"
                disabled={!answer || !!busy}
                onClick={() => void write("draft", { answer })}
              >
                保存草稿
              </Button>
              <Button variant="outline" disabled={!!busy} onClick={() => void write("hints")}>
                下一条提示
              </Button>
              <Button variant="ghost" disabled={!!busy} onClick={() => void write("reveal")}>
                查看答案与解析
              </Button>
            </div>
          )}
        </Card>
        <div className="min-w-0 space-y-4">
          <TeachingCards cards={cards} />
          {active && (
            <Card padding={4} className="space-y-3">
              <label htmlFor="teaching-message" className="block text-copy font-semibold text-ink">
                向 AI 追问
              </label>
              <textarea
                id="teaching-message"
                value={message}
                maxLength={4000}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                className="w-full rounded-sm border border-hairline bg-canvas p-3 text-copy text-ink"
                placeholder="例如：请再给我一个定位线索"
              />
              <p className="text-caption text-muted">
                追问不会代你提交答案；额度或模型不可用时仍可使用核验提示。
              </p>
              <Button
                disabled={!!busy || runActive || !message.trim()}
                loading={busy === "runs"}
                onClick={() => void startRun()}
              >
                发送追问
              </Button>
            </Card>
          )}
          {run && (
            <div className="space-y-2 rounded-sm border border-hairline p-3" role="status">
              <p className="text-copy text-body">{RUN_LABEL[run.status] ?? "讲解状态已更新"}</p>
              {streamError && <p className="text-meta text-muted">{streamError}</p>}
              {run.error_code && (
                <p className="text-meta text-muted">讲解暂未完成，可继续使用提示或稍后再试。</p>
              )}
              {runActive && (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => setStreamRetry((v) => v + 1)}>
                    重新连接
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      void api<TeachingRun>(
                        `/api/v1/teaching/runs/${encodeURIComponent(run.run_id)}/cancel`,
                        { method: "POST" }
                      )
                        .then(setRun)
                        .catch((err) => setError(err.message))
                    }
                  >
                    取消讲解
                  </Button>
                </div>
              )}
            </div>
          )}
          <Card padding={4} className="space-y-3">
            <h2 className="text-copy font-semibold text-ink">在已连接 AI 中继续</h2>
            <p className="text-meta text-muted">
              复制会话指引给已授权的 Codex 或 Claude，回来后重新读取即可同步进度。
            </p>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  void navigator.clipboard
                    .writeText(teachingResumeText(session))
                    .then(() => toast.success("会话指引已复制"))
                    .catch(() => setError("复制失败，可直接复制地址栏中的会话链接。"))
                }
              >
                复制继续学习指引
              </Button>
              <Link
                href="/profile?tab=account"
                className="self-center text-meta font-semibold text-brand-700 underline"
              >
                管理 AI 连接
              </Link>
            </div>
          </Card>
          {active && (
            <details className="rounded-sm border border-hairline p-4">
              <summary className="cursor-pointer text-copy font-semibold text-ink">
                记录反馈与结束
              </summary>
              <div className="mt-3 space-y-3">
                <label htmlFor="teaching-feedback" className="block text-meta text-muted">
                  哪里还没理解？反馈不改变成绩。
                </label>
                <textarea
                  id="teaching-feedback"
                  value={feedback}
                  maxLength={4000}
                  onChange={(e) => setFeedback(e.target.value)}
                  rows={2}
                  className="w-full rounded-sm border border-hairline bg-canvas p-3 text-copy text-ink"
                />
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!feedback.trim() || !!busy}
                    onClick={() => void write("feedback", { content: feedback.trim() })}
                  >
                    保存反馈
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!!busy}
                    onClick={() => void write("complete")}
                  >
                    完成教学
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={!!busy}
                    onClick={() => void write("abandon")}
                  >
                    结束本次
                  </Button>
                </div>
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}
