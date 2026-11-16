"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { FilePlus, FileText } from "lucide-react";
import { toast } from "sonner";
import { AdminEmptyState, AdminPageHeader } from "@/components/admin/ui";
import { ErrorState } from "@/components/common/ErrorState";
import { InlineSpinner } from "@/components/common/Spinner";
import { Button } from "@/components/ui/Button";
import { FormField } from "@/components/ui/FormField";
import { Input, Textarea } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { adminApi } from "@/lib/adminApi";
import { ApiClientError } from "@/lib/createApiClient";
import { apiErrorMessage } from "@/lib/errors";
import {
  adminLessonAction,
  adminLessonRevisionApiPath,
  getAdminLessonDiff,
  type AdminLesson,
  type AdminLessonDiff,
  type LessonDiffCategory,
  type AdminLessonDetail,
  type AdminLessonRevision,
  type ReviewUse,
} from "@/lib/lessons";

const labels = { candidate: "候选", published: "已发布", withdrawn: "已撤回" } as const;
const reviewUses: { key: ReviewUse; label: string }[] = [
  { key: "site_display", label: "站内展示" },
  { key: "model_processing", label: "向模型披露" },
  { key: "external_redistribution", label: "对外再分发" },
];
type Selection = { lessonId: string; revisionId: string };
type Diagnostic = { path: string; message: string };
type Action = "import" | "review" | "publish" | "withdraw";

function getDiagnostics(error: unknown) {
  if (!(error instanceof ApiClientError) || !Array.isArray(error.detail)) return [];
  return error.detail.filter(
    (item): item is Diagnostic =>
      typeof item?.path === "string" && typeof item?.message === "string"
  );
}

const diffLabels: Record<LessonDiffCategory, string> = {
  metadata: "材料信息",
  media: "媒体",
  provenance: "来源与权利依据",
  segments: "段落结构",
  original: "原文",
  translation: "译文",
  timing: "时间对齐",
  anchors: "词锚点",
  vocabulary: "词汇",
};

function RevisionDiff({ detail, lesson }: { detail: AdminLessonDetail; lesson: AdminLesson }) {
  const baselines = lesson.revisions.filter((item) => item.revision_id !== detail.revision_id);
  const [baseline, setBaseline] = useState(
    baselines.find((item) => item.revision_id === lesson.current_revision_id)?.revision_id ??
      baselines[0]?.revision_id ??
      ""
  );
  const [result, setResult] = useState<{
    baseline: string;
    data?: AdminLessonDiff;
    error?: string;
  } | null>(null);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    if (!baseline) return;
    const controller = new AbortController();
    getAdminLessonDiff(detail.lesson_id, detail.revision_id, baseline, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setResult({ baseline, data });
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted)
          setResult({ baseline, error: apiErrorMessage(error, "差异加载失败") });
      });
    return () => controller.abort();
  }, [detail.lesson_id, detail.revision_id, baseline, retry]);

  if (!baselines.length) return null;
  const visible = result?.baseline === baseline ? result : null;
  return (
    <section aria-label="修订差异" className="space-y-3 border-t border-hairline pt-4">
      <FormField label="对比基准修订" htmlFor="lesson-diff-baseline">
        <Select
          id="lesson-diff-baseline"
          value={baseline}
          onChange={(event) => {
            setBaseline(event.target.value);
            setResult(null);
          }}
        >
          {baselines.map((item) => (
            <option key={item.revision_id} value={item.revision_id}>
              {item.title} · {item.revision_id} · {labels[item.status]}
            </option>
          ))}
        </Select>
      </FormField>
      {!visible ? (
        <div role="status" aria-label="正在加载差异">
          <InlineSpinner />
        </div>
      ) : visible.error ? (
        <ErrorState
          title={visible.error}
          onRetry={() => {
            setResult(null);
            setRetry((value) => value + 1);
          }}
        />
      ) : visible.data ? (
        visible.data.changes.length ? (
          <div className="space-y-2">
            <p className="text-meta text-muted">
              影响：{visible.data.impacts.map((category) => diffLabels[category]).join("、")}
            </p>
            <div className="max-h-96 space-y-2 overflow-auto">
              {visible.data.changes.map((change) => (
                <details
                  key={`${change.category}:${change.path}`}
                  className="rounded-md border border-hairline p-3"
                >
                  <summary className="cursor-pointer break-all text-meta text-ink">
                    {diffLabels[change.category]} · {change.path} ·{" "}
                    {{ added: "新增", removed: "删除", modified: "修改" }[change.kind]}
                  </summary>
                  <dl className="mt-2 space-y-2 text-meta">
                    {(["before", "after"] as const).map((side) => (
                      <div key={side}>
                        <dt className="font-medium text-ink">
                          {side === "before" ? "基准" : "此修订"}
                        </dt>
                        <dd>
                          <pre className="break-words whitespace-pre-wrap text-muted">
                            {JSON.stringify(change[side], null, 2)}
                          </pre>
                        </dd>
                      </div>
                    ))}
                  </dl>
                </details>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-copy text-muted">与基准修订无差异</p>
        )
      ) : null}
    </section>
  );
}

export function LessonAdmin() {
  const [lessons, setLessons] = useState<AdminLesson[] | null>(null);
  const [failure, setFailure] = useState<number | null>(null);
  const [detail, setDetail] = useState<AdminLessonDetail | null>(null);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [detailError, setDetailError] = useState("");
  const [retry, setRetry] = useState(0);
  const [busy, setBusy] = useState<Action | null>(null);
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]);
  const [operationError, setOperationError] = useState("");
  const operation = useRef<{ key: string; id: string } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    adminApi<{ lessons: AdminLesson[] }>("/api/v1/admin/lessons", {
      cache: "no-store",
      signal: controller.signal,
    })
      .then((data) => {
        if (!controller.signal.aborted) {
          setLessons(data.lessons);
          setFailure(null);
        }
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setFailure(error instanceof ApiClientError ? error.status : 0);
        }
      });
    return () => controller.abort();
  }, [retry]);

  useEffect(() => {
    if (!selection) return;
    const controller = new AbortController();
    adminApi<AdminLessonDetail>(
      adminLessonRevisionApiPath(selection.lessonId, selection.revisionId),
      { cache: "no-store", signal: controller.signal }
    )
      .then((data) => {
        if (!controller.signal.aborted) setDetail(data);
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setDetailError(apiErrorMessage(error, "修订加载失败"));
      });
    return () => controller.abort();
  }, [selection]);

  function choose(lessonId: string, revisionId: string) {
    setSelection({ lessonId, revisionId });
    setDetail(null);
    setDetailError("");
    setDiagnostics([]);
    setOperationError("");
  }

  async function execute(action: Action, body: Record<string, unknown>) {
    const key = JSON.stringify([action, selection, body]);
    if (operation.current?.key !== key) {
      operation.current = { key, id: crypto.randomUUID() };
    }
    const request = { ...body, operation_id: operation.current.id };
    setBusy(action);
    setDiagnostics([]);
    setOperationError("");
    try {
      const updated =
        action === "import"
          ? await adminApi<AdminLessonDetail>("/api/v1/admin/lessons/import", {
              method: "POST",
              body: JSON.stringify(request),
            })
          : await adminLessonAction(selection!.lessonId, selection!.revisionId, action, request);
      operation.current = null;
      setDetail(updated);
      if (action === "import") {
        setSelection({ lessonId: updated.lesson_id, revisionId: updated.revision_id });
      }
      setRetry((value) => value + 1);
      toast.success(
        { import: "已导入", review: "已记录审核", publish: "已发布", withdraw: "已撤回" }[action]
      );
      return true;
    } catch (error) {
      setDiagnostics(getDiagnostics(error));
      setOperationError(apiErrorMessage(error, "操作失败"));
      if (error instanceof ApiClientError && error.status === 409) setRetry((value) => value + 1);
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function importFile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const file = new FormData(form).get("pack");
    if (!(file instanceof File) || !file.size) return;
    try {
      const text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      if (await execute("import", { pack_json: text })) form.reset();
    } catch {
      setDiagnostics([{ path: "/", message: "文件必须使用 UTF-8 编码" }]);
      setOperationError("无法读取学习包");
    }
  }

  function review(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const uses = Object.fromEntries(
      reviewUses.map(({ key }) => [
        key,
        {
          approved: form.get(key) === "on",
          evidence: String(form.get(`${key}-evidence`) ?? "").trim(),
        },
      ])
    );
    const minutes = String(form.get("human_minutes") ?? "").trim();
    void execute("review", {
      source_commit: String(form.get("source_commit") ?? "")
        .trim()
        .toLowerCase(),
      uses,
      verification_method: String(form.get("verification_method") ?? "").trim() || null,
      limitations: String(form.get("limitations") ?? "").trim() || null,
      human_minutes: minutes === "" ? null : Number(minutes),
    });
  }

  const selectedLesson = lessons?.find((lesson) => lesson.lesson_id === detail?.lesson_id);
  const currentRevisionId = selectedLesson?.current_revision_id ?? null;

  return (
    <div className="space-y-6">
      <AdminPageHeader title="课程材料" />
      {failure === 503 ? (
        <AdminEmptyState text="课程试点暂未开启" icon={<FileText size={26} />} />
      ) : failure !== null ? (
        <ErrorState title="课程材料加载失败" onRetry={() => setRetry((value) => value + 1)} />
      ) : lessons === null ? (
        <div className="flex justify-center py-12" role="status" aria-label="正在加载">
          <InlineSpinner />
        </div>
      ) : (
        <>
          <form
            onSubmit={(event) => void importFile(event)}
            className="space-y-3 rounded-lg border border-hairline bg-canvas p-4"
          >
            <FormField label="学习包 JSON" htmlFor="lesson-import">
              <Input
                id="lesson-import"
                name="pack"
                type="file"
                accept=".json,application/json"
                required
              />
            </FormField>
            <Button
              type="submit"
              icon={FilePlus}
              loading={busy === "import"}
              disabled={busy !== null}
            >
              导入候选修订
            </Button>
          </form>
          {operationError && (
            <div
              role="alert"
              className="space-y-2 rounded-lg border border-error/30 bg-red-soft p-4 text-copy text-error"
            >
              <p className="font-semibold">{operationError}</p>
              {diagnostics.length > 0 && (
                <ul className="space-y-1">
                  {diagnostics.map(({ path, message }, index) => (
                    <li key={`${path}-${index}`} className="break-words">
                      <code>{path}</code> · {message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          <div className="grid items-start gap-4 xl:grid-cols-[minmax(15rem,0.7fr)_minmax(0,1fr)]">
            <section
              aria-label="课程修订列表"
              className="min-w-0 rounded-lg border border-hairline bg-canvas p-4"
            >
              {!lessons.length ? (
                <AdminEmptyState text="暂无课程材料" icon={<FileText size={26} />} />
              ) : (
                <ul className="divide-y divide-hairline">
                  {lessons.map((lesson) => (
                    <li key={lesson.lesson_id} className="space-y-2 py-3 first:pt-0 last:pb-0">
                      <h2 className="font-semibold break-words text-ink">{lesson.lesson_id}</h2>
                      <ul className="space-y-1.5">
                        {lesson.revisions.map((revision: AdminLessonRevision) => (
                          <li key={revision.revision_id}>
                            <Button
                              variant={
                                selection?.revisionId === revision.revision_id ? "tonal" : "outline"
                              }
                              size="sm"
                              disabled={busy !== null}
                              aria-pressed={selection?.revisionId === revision.revision_id}
                              className="w-full justify-between text-left"
                              onClick={() => choose(lesson.lesson_id, revision.revision_id)}
                            >
                              <span className="min-w-0 break-words">{revision.title}</span>
                              <span className="shrink-0">
                                {lesson.current_revision_id === revision.revision_id
                                  ? "当前版"
                                  : labels[revision.status]}
                              </span>
                            </Button>
                          </li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {detailError ? (
              <ErrorState
                title={detailError}
                onRetry={() => selection && choose(selection.lessonId, selection.revisionId)}
              />
            ) : selection && !detail ? (
              <div className="flex justify-center py-12" role="status" aria-label="正在加载修订">
                <InlineSpinner />
              </div>
            ) : detail ? (
              <section
                className="min-w-0 space-y-5 rounded-lg border border-hairline bg-canvas p-4"
                aria-label="审核与发布"
              >
                <div className="space-y-1">
                  <h2 className="text-title font-semibold break-words text-ink">{detail.title}</h2>
                  <p className="text-meta text-muted">{labels[detail.status]}</p>
                  <dl className="space-y-1 text-meta text-muted">
                    <div>
                      <dt className="inline font-medium text-ink">修订：</dt>
                      <dd className="inline break-all">{detail.revision_id}</dd>
                    </div>
                    <div>
                      <dt className="inline font-medium text-ink">指纹：</dt>
                      <dd className="inline break-all">{detail.fingerprint}</dd>
                    </div>
                    {detail.review && (
                      <div>
                        <dt className="inline font-medium text-ink">审核摘要：</dt>
                        <dd className="inline break-all">{detail.review.review_sha256}</dd>
                      </div>
                    )}
                  </dl>
                </div>
                {detail.pack && (
                  <details className="rounded-md border border-hairline bg-surface-card p-3">
                    <summary className="cursor-pointer font-medium text-ink">
                      预览材料与来源
                    </summary>
                    <div className="mt-3 max-h-80 space-y-3 overflow-auto">
                      <a
                        href={detail.pack.media.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="break-all text-brand-700 underline"
                      >
                        {detail.pack.media.source_url}
                      </a>
                      {Object.entries(detail.pack.provenance).map(([key, source]) =>
                        source && typeof source !== "string" ? (
                          <p key={key} className="break-words text-meta text-muted">
                            {source.attribution} ·{" "}
                            <a
                              href={source.evidence_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-brand-700 underline"
                            >
                              {source.basis}
                            </a>
                          </p>
                        ) : null
                      )}
                      {detail.pack.segments.map((segment) => (
                        <div
                          key={segment.id}
                          className="break-words border-t border-hairline pt-2 text-copy"
                        >
                          <p lang="en" className="text-ink">
                            {segment.text}
                          </p>
                          <p lang="zh-CN" className="text-muted">
                            {segment.translation}
                          </p>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
                {selectedLesson && (
                  <RevisionDiff
                    key={`diff:${detail.revision_id}`}
                    detail={detail}
                    lesson={selectedLesson}
                  />
                )}
                {detail.review && (
                  <details className="rounded-md border border-hairline p-3">
                    <summary className="cursor-pointer font-medium text-ink">已记录的审核</summary>
                    <pre className="mt-2 max-h-64 overflow-auto text-meta break-words whitespace-pre-wrap text-muted">
                      {JSON.stringify(detail.review, null, 2)}
                    </pre>
                  </details>
                )}
                {(detail.status === "candidate" || detail.status === "withdrawn") && (
                  <form
                    key={`review:${detail.revision_id}:${detail.review?.review_sha256 ?? ""}`}
                    onSubmit={review}
                    className="space-y-3 border-t border-hairline pt-4"
                  >
                    <h3 className="font-semibold text-ink">
                      {detail.status === "withdrawn" ? "重新审核用途" : "用途审核"}
                    </h3>
                    {detail.status === "withdrawn" && detail.requires_review && (
                      <p role="status" className="text-copy text-muted">
                        恢复前须针对最近撤回重新审核；旧审核和撤回前收据不能恢复此修订。
                      </p>
                    )}
                    <FormField label="来源 Git 提交" htmlFor="lesson-review-commit">
                      <Input
                        id="lesson-review-commit"
                        name="source_commit"
                        pattern="[A-Fa-f0-9]{40}"
                        required
                        defaultValue={detail.review?.source_commit}
                      />
                    </FormField>
                    {reviewUses.map(({ key, label }) => (
                      <div key={key} className="space-y-1.5">
                        <label className="flex items-center gap-2 text-copy text-ink">
                          <input
                            type="checkbox"
                            name={key}
                            defaultChecked={detail.review?.uses[key]?.approved}
                          />
                          允许{label}
                        </label>
                        <FormField label={`${label}的审核依据`} htmlFor={`lesson-review-${key}`}>
                          <Textarea
                            id={`lesson-review-${key}`}
                            name={`${key}-evidence`}
                            rows={2}
                            required
                            maxLength={4000}
                            defaultValue={detail.review?.uses[key]?.evidence}
                          />
                        </FormField>
                      </div>
                    ))}
                    <FormField label="核对方式（可留空）" htmlFor="lesson-review-method">
                      <Textarea
                        id="lesson-review-method"
                        name="verification_method"
                        rows={2}
                        maxLength={4000}
                        defaultValue={
                          detail.requires_review ? "" : (detail.review?.verification_method ?? "")
                        }
                      />
                    </FormField>
                    <FormField label="争议与限制（可留空）" htmlFor="lesson-review-limitations">
                      <Textarea
                        id="lesson-review-limitations"
                        name="limitations"
                        rows={2}
                        maxLength={4000}
                        defaultValue={
                          detail.requires_review ? "" : (detail.review?.limitations ?? "")
                        }
                      />
                    </FormField>
                    <FormField
                      label="本次人工工时（分钟，未知留空）"
                      htmlFor="lesson-review-minutes"
                    >
                      <Input
                        id="lesson-review-minutes"
                        name="human_minutes"
                        type="number"
                        min={0}
                        step="any"
                        defaultValue={
                          detail.requires_review ? "" : (detail.review?.human_minutes ?? "")
                        }
                      />
                    </FormField>
                    <Button
                      type="submit"
                      variant="outline"
                      loading={busy === "review"}
                      disabled={busy !== null}
                    >
                      保存审核
                    </Button>
                  </form>
                )}
                {!detail.requires_review &&
                  detail.review?.uses.site_display.approved &&
                  currentRevisionId !== detail.revision_id && (
                    <form
                      key={`publish:${detail.revision_id}:${detail.review.review_sha256}`}
                      className="space-y-3 border-t border-hairline pt-4"
                      onSubmit={(event) => {
                        event.preventDefault();
                        const form = event.currentTarget;
                        const receipt = String(new FormData(form).get("receipt") ?? "").trim();
                        if (receipt)
                          void execute("publish", {
                            expected_current_revision_id: currentRevisionId,
                            receipt,
                          }).then((ok) => {
                            if (ok) form.reset();
                          });
                      }}
                    >
                      <FormField label="签名发布收据" htmlFor="lesson-publish-receipt">
                        <Textarea id="lesson-publish-receipt" name="receipt" rows={3} required />
                      </FormField>
                      <Button type="submit" loading={busy === "publish"} disabled={busy !== null}>
                        {detail.status === "withdrawn" ? "以新收据恢复发布" : "发布为当前版"}
                      </Button>
                    </form>
                  )}
                {detail.status === "published" && (
                  <form
                    key={`withdraw:${detail.revision_id}`}
                    className="space-y-3 border-t border-hairline pt-4"
                    onSubmit={(event) => {
                      event.preventDefault();
                      const reason = String(
                        new FormData(event.currentTarget).get("reason") ?? ""
                      ).trim();
                      if (reason) void execute("withdraw", { reason });
                    }}
                  >
                    <FormField
                      label="撤回原因"
                      htmlFor="lesson-withdraw-reason"
                      hint="撤回会停止提供此修订的字幕、释义与导师语境。"
                    >
                      <Textarea id="lesson-withdraw-reason" name="reason" rows={2} required />
                    </FormField>
                    <Button
                      type="submit"
                      variant="destructive"
                      loading={busy === "withdraw"}
                      disabled={busy !== null}
                    >
                      撤回此修订
                    </Button>
                  </form>
                )}
              </section>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
