"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { MessageCircle, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Textarea } from "@/components/ui/Input";
import { LinkButton } from "@/components/ui/LinkButton";
import { api } from "@/lib/api";
import { apiErrorMessage } from "@/lib/errors";
import {
  lessonApiPath,
  lessonHref,
  type LessonAnchor,
  type LessonVocabularySource,
} from "@/lib/lessons";
import { isActiveRun } from "@/lib/teaching";
import { readTeachingEvents } from "@/lib/teachingStream";
import type { TeachingRunStatus } from "@/types/teaching";

interface TutorMessage {
  id: string;
  role: "user" | "assistant";
  status: string;
  restricted: boolean;
  body: { text?: string; lesson_citation?: LessonVocabularySource } | null;
}

interface TutorPage {
  items: TutorMessage[];
  next_after: number;
  has_more: boolean;
}

const terminal = new Set(["run.completed", "run.failed", "run.cancelled", "run.needs_retry"]);

export function LessonTutor({
  lessonId,
  revisionId,
  anchor,
  initialConversation,
  onCitation,
}: {
  lessonId: string;
  revisionId: string;
  anchor: LessonAnchor;
  initialConversation: string | null;
  onCitation: (anchor: LessonAnchor) => void;
}) {
  const [conversationId, setConversation] = useState(initialConversation);
  const [runId, setRun] = useState<string | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [sending, setSending] = useState(false);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const request = useRef<{ message: string; id: string } | null>(null);
  const tutorPath = `${lessonApiPath(lessonId)}/tutor`;

  useEffect(() => {
    if (!conversationId) return;
    const controller = new AbortController();
    let pending = false;
    async function load() {
      if (pending || document.visibilityState === "hidden") return;
      pending = true;
      try {
        const items: TutorMessage[] = [];
        let after = 0;
        for (let page = 0; page < 10; page++) {
          const result = await api<TutorPage>(
            `${tutorPath}/${encodeURIComponent(conversationId!)}/messages?after=${after}&limit=50`,
            { signal: controller.signal, cache: "no-store" }
          );
          items.push(...result.items);
          if (!result.has_more || result.next_after <= after) break;
          after = result.next_after;
        }
        if (!controller.signal.aborted) setMessages(items);
      } catch (failure) {
        if (!controller.signal.aborted) {
          setMessages([]);
          setError(apiErrorMessage(failure, "导师对话暂时无法读取"));
        }
      } finally {
        pending = false;
      }
    }
    void load();
    const timer = setInterval(() => void load(), 20_000);
    document.addEventListener("visibilitychange", load);
    return () => {
      controller.abort();
      clearInterval(timer);
      document.removeEventListener("visibilitychange", load);
    };
  }, [conversationId, refresh, tutorPath]);

  useEffect(() => {
    if (!runId) return;
    const controller = new AbortController();
    let stopped = false;
    void readTeachingEvents(
      runId,
      0,
      (event) => {
        if (event.type === "content.restricted") {
          setMessages([]);
          setError("材料已不可用于导师对话");
        }
        if (terminal.has(event.type) || event.type === "content.restricted") {
          stopped = true;
          setRun(null);
          setRefresh((value) => value + 1);
          if (event.type === "run.failed" || event.type === "run.needs_retry") {
            setError("导师暂时无法回答，可重新提问");
          }
          controller.abort();
        }
      },
      controller.signal
    )
      .catch((failure: unknown) => {
        if (!controller.signal.aborted) setError(apiErrorMessage(failure, "导师连接已断开"));
      })
      .finally(() => {
        if (!controller.signal.aborted && !stopped) {
          setRun(null);
          setRefresh((value) => value + 1);
        }
      });
    return () => controller.abort();
  }, [runId]);

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || sending || runId) return;
    if (request.current?.message !== message) {
      request.current = { message, id: crypto.randomUUID() };
    }
    setSending(true);
    setError("");
    try {
      const run = await api<{ run_id: string; conversation_id: string; status: TeachingRunStatus }>(
        tutorPath,
        {
          method: "POST",
          body: JSON.stringify({
            revision_id: revisionId,
            segment_id: anchor.segment_id,
            token_ids: anchor.token_ids,
            request_id: request.current.id,
            message,
            ...(conversationId ? { conversation_id: conversationId } : {}),
          }),
        }
      );
      setConversation(run.conversation_id);
      setRun(isActiveRun(run.status) ? run.run_id : null);
      setRefresh((value) => value + 1);
      setDraft("");
      request.current = null;
      const url = new URL(lessonHref(lessonId, revisionId, anchor), location.origin);
      url.searchParams.set("conversation", run.conversation_id);
      history.replaceState(null, "", url);
    } catch (failure) {
      setError(apiErrorMessage(failure, "无法开始导师对话"));
    } finally {
      setSending(false);
    }
  }

  const restricted = messages.some((message) => message.restricted);
  return (
    <div className="space-y-3 border-t border-hairline pt-3">
      <h3 className="text-copy font-semibold text-ink">导师</h3>
      {messages.length > 0 && (
        <ol aria-live="polite" className="max-h-72 space-y-2 overflow-auto">
          {messages.map((message) => {
            if (message.restricted || message.status !== "complete" || !message.body?.text)
              return null;
            const citation = message.body.lesson_citation;
            return (
              <li key={message.id} className="space-y-1 rounded-md bg-surface-soft p-2.5">
                <p className="text-caption font-medium text-muted">
                  {message.role === "user" ? "你" : "导师"}
                </p>
                <p className="text-copy break-words whitespace-pre-wrap text-ink">
                  {message.body.text}
                </p>
                {citation?.available &&
                  (citation.revision_id === revisionId ? (
                    <Button size="compact" variant="ghost" onClick={() => onCitation(citation)}>
                      定位原句
                    </Button>
                  ) : (
                    <LinkButton
                      size="compact"
                      variant="ghost"
                      icon={ArrowUpRight}
                      href={lessonHref(citation.lesson_id, citation.revision_id, citation)}
                    >
                      打开引用修订
                    </LinkButton>
                  ))}
              </li>
            );
          })}
        </ol>
      )}
      {restricted && (
        <p role="status" className="text-meta text-muted">
          材料已不可用
        </p>
      )}
      {error && (
        <p role="status" className="text-meta text-error">
          {error}
        </p>
      )}
      {!restricted && (
        <form onSubmit={(event) => void ask(event)} className="space-y-2">
          <FormField label="你的问题" htmlFor="lesson-tutor-message">
            <Textarea
              id="lesson-tutor-message"
              rows={2}
              maxLength={1000}
              required
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
            />
          </FormField>
          <Button
            type="submit"
            variant="tonal"
            size="sm"
            loading={sending || Boolean(runId)}
            icon={MessageCircle}
          >
            {runId ? "等待导师" : "问导师"}
          </Button>
        </form>
      )}
    </div>
  );
}
