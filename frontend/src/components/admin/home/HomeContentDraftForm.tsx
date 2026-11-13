"use client";

/**
 * 首页内容草稿编辑器。
 *
 * 编辑的只是「编辑决策 + 引用」（标题、推荐理由、选句/选词、片段起止、互动、场景）；
 * 原文、译文、时间、封面、时长一律来自 `subtitles`（真实字幕）或服务端解析，
 * 这里不产生任何编造的时间或原创字幕。
 *
 * 草稿允许不完整保存；发布要求由后端校验，本组件只做明显错误的即时提示。
 */

import { useMemo, useRef, useState } from "react";
import { Pause, Play, Plus, Trash2, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import type {
  HomeContentDraft,
  HomeContentDraftExpression,
  HomeContentDraftScenario,
  HomeEditorialInteraction,
} from "@/types/homeContent";
import type { Subtitle } from "@/types";
import { formatClock, formatSeconds } from "./format";
import { SubtitleMultiPicker, SubtitleQuote, SubtitleSelect } from "./SubtitlePickers";

// ---------------------------------------------------------------------------
// 稳定 ID 生成（草稿里的 id 形如 ^[a-z0-9][a-z0-9-]{0,47}$）
// ---------------------------------------------------------------------------

function slugFromText(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
}

function newStableId(prefix: string, existingIds: string[], seed?: string): string {
  let base = slugFromText(seed ?? "");
  if (!base) base = prefix;
  if (!/^[a-z0-9]/.test(base)) base = prefix;
  base = base.slice(0, 44);
  if (!existingIds.includes(base)) return base;
  for (let index = 2; index < 100; index += 1) {
    const candidate = `${base}-${index}`.slice(0, 48);
    if (!existingIds.includes(candidate)) return candidate;
  }
  return `${prefix}-${Date.now().toString(36)}`.slice(0, 48);
}

/** 短语是否按词边界真实出现在原句里（只做即时提示，最终以后端校验为准）。 */
function phraseOccursInSentence(textEn: string, phrase: string): boolean {
  const cleaned = phrase.trim().toLowerCase();
  if (!cleaned) return false;
  const escaped = cleaned.replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\s+/g, "\\s+");
  return new RegExp(`(^|[^a-z0-9])${escaped}([^a-z0-9]|$)`, "i").test(textEn);
}

// ---------------------------------------------------------------------------
// 小组件
// ---------------------------------------------------------------------------

function FormSection({
  title,
  hint,
  actions,
  children,
}: {
  title: string;
  hint?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3 border-t border-hairline pt-4 first:border-t-0 first:pt-0">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-copy font-semibold text-ink">{title}</h3>
          {hint && <p className="mt-0.5 text-caption text-muted">{hint}</p>}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block min-w-0 space-y-1">
      <span className="block text-meta font-medium text-muted">{label}</span>
      {children}
      {hint && <span className="block text-caption text-muted-soft">{hint}</span>}
    </label>
  );
}

function ExpressionRow({
  videoId,
  expression,
  index,
  subtitles,
  subtitle,
  disabled,
  onChange,
  onRemove,
}: {
  videoId: string;
  expression: HomeContentDraftExpression;
  index: number;
  subtitles: Subtitle[];
  subtitle: Subtitle | undefined;
  disabled: boolean;
  onChange: (next: HomeContentDraftExpression) => void;
  onRemove: () => void;
}) {
  const phraseMismatch =
    Boolean(subtitle) &&
    expression.phrase.trim().length > 0 &&
    !phraseOccursInSentence(subtitle!.text_en, expression.phrase);

  return (
    <div className="space-y-3 rounded-md border border-hairline bg-surface-card p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-meta font-medium text-ink">表达 {index + 1}</span>
          <code className="text-caption text-muted-soft">id: {expression.id}</code>
        </div>
        <Button variant="ghost" size="compact" icon={Trash2} onClick={onRemove} disabled={disabled}>
          移除
        </Button>
      </div>
      <Field label="引用字幕句（必须来自该视频）">
        <SubtitleSelect
          subtitles={subtitles}
          value={expression.subtitle_id || null}
          onChange={(subtitleId) => onChange({ ...expression, subtitle_id: subtitleId ?? "" })}
          disabled={disabled}
          emptyLabel="选择一句字幕"
        />
      </Field>
      {subtitle && <SubtitleQuote videoId={videoId} subtitle={subtitle} compact />}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field
          label="短语（原句里的词或短语）"
          hint={
            phraseMismatch
              ? "该短语没有按词边界出现在选中句子里，保存/发布会被拒绝。"
              : "会在公共页面高亮；必须是原句里真实存在的文本。"
          }
        >
          <Input
            value={expression.phrase}
            onChange={(event) => onChange({ ...expression, phrase: event.target.value })}
            disabled={disabled}
            placeholder="例如 spot"
          />
        </Field>
        <Field label="收词单词（可空）" hint="短语是多个词时留空；单字时填同一个词。">
          <Input
            value={expression.word ?? ""}
            onChange={(event) =>
              onChange({ ...expression, word: event.target.value.trim() || null })
            }
            disabled={disabled}
            placeholder="例如 spot"
          />
        </Field>
        <Field label="中文教学说明 / 释义（可空）">
          <Input
            value={expression.gloss_zh ?? ""}
            onChange={(event) => onChange({ ...expression, gloss_zh: event.target.value || null })}
            disabled={disabled}
            placeholder="例如 v. 发现；识别出"
          />
        </Field>
        <Field label="编辑理由（可空）">
          <Input
            value={expression.note_zh ?? ""}
            onChange={(event) => onChange({ ...expression, note_zh: event.target.value || null })}
            disabled={disabled}
            placeholder="为什么值得学"
          />
        </Field>
      </div>
      {subtitle && expression.phrase.trim() && (
        <p className="rounded-sm bg-surface-soft px-2 py-1.5 text-caption text-muted">
          原句：{subtitle.text_en}
          {subtitle.text_zh ? ` · ${subtitle.text_zh}` : ""}
        </p>
      )}
    </div>
  );
}

function ScenarioRow({
  videoId,
  scenario,
  index,
  subtitles,
  subtitle,
  disabled,
  onChange,
  onRemove,
}: {
  videoId: string;
  scenario: HomeContentDraftScenario;
  index: number;
  subtitles: Subtitle[];
  subtitle: Subtitle | undefined;
  disabled: boolean;
  onChange: (next: HomeContentDraftScenario) => void;
  onRemove: () => void;
}) {
  return (
    <div className="space-y-3 rounded-md border border-hairline bg-surface-card p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-meta font-medium text-ink">场景 {index + 1}</span>
          <code className="text-caption text-muted-soft">id: {scenario.id}</code>
        </div>
        <Button variant="ghost" size="compact" icon={Trash2} onClick={onRemove} disabled={disabled}>
          移除
        </Button>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Field label="中文情境">
          <Input
            value={scenario.situation_zh}
            onChange={(event) => onChange({ ...scenario, situation_zh: event.target.value })}
            disabled={disabled}
            placeholder="例如 约朋友·临时有事"
          />
        </Field>
        <Field label="中文提示">
          <Input
            value={scenario.prompt_zh}
            onChange={(event) => onChange({ ...scenario, prompt_zh: event.target.value })}
            disabled={disabled}
            placeholder="例如 朋友约你今晚吃饭，试着回一句"
          />
        </Field>
        <Field label="英语参考回复（生成的教学例句，不是字幕原话）">
          <Textarea
            rows={2}
            value={scenario.reply_en}
            onChange={(event) => onChange({ ...scenario, reply_en: event.target.value })}
            disabled={disabled}
            placeholder="例如 Can I take a rain check?"
          />
        </Field>
        <Field label="中文译文">
          <Textarea
            rows={2}
            value={scenario.reply_zh}
            onChange={(event) => onChange({ ...scenario, reply_zh: event.target.value })}
            disabled={disabled}
            placeholder="例如 这次先不了，下次再约好吗？"
          />
        </Field>
      </div>
      <Field label="锚定原句（可空）" hint="有锚定句时，公共页可展开查看原句并返回观看。">
        <SubtitleSelect
          subtitles={subtitles}
          value={scenario.subtitle_id}
          onChange={(subtitleId) => onChange({ ...scenario, subtitle_id: subtitleId })}
          disabled={disabled}
          emptyLabel="不锚定原句"
        />
      </Field>
      {subtitle && <SubtitleQuote videoId={videoId} subtitle={subtitle} compact />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 主表单
// ---------------------------------------------------------------------------

export function HomeContentDraftForm({
  videoId,
  draft,
  subtitles,
  clipDuration,
  mediaSource,
  onChange,
  disabled = false,
}: {
  videoId: string;
  draft: HomeContentDraft;
  subtitles: Subtitle[];
  /** 保存后服务端解析出的片段时长；未保存过时为 null（不显示估算值）。 */
  clipDuration: number | null;
  /** 本地媒体地址（管理员 token 已附）；null 时禁用试听，不伪造播放。 */
  mediaSource: string | null;
  onChange: (next: HomeContentDraft) => void;
  disabled?: boolean;
}) {
  const subtitleById = useMemo(
    () => new Map(subtitles.map((subtitle) => [subtitle.id, subtitle])),
    [subtitles]
  );
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const stopAtRef = useRef<number | null>(null);
  const [auditioning, setAuditioning] = useState(false);
  const [auditionFailed, setAuditionFailed] = useState(false);

  const patch = (next: Partial<HomeContentDraft>) => onChange({ ...draft, ...next });

  const clipStart = draft.clip?.start_subtitle_id ?? null;
  const clipEnd = draft.clip?.end_subtitle_id ?? null;
  const clipStartSubtitle = clipStart ? subtitleById.get(clipStart) : undefined;
  const clipEndSubtitle = clipEnd ? subtitleById.get(clipEnd) : undefined;
  const clipOrderInvalid = Boolean(
    clipStartSubtitle &&
    clipEndSubtitle &&
    clipStartSubtitle.sentence_index > clipEndSubtitle.sentence_index
  );

  const evidenceSubtitles = draft.evidence_subtitle_ids
    .map((subtitleId) => subtitleById.get(subtitleId))
    .filter((subtitle): subtitle is Subtitle => Boolean(subtitle));

  function setClip(next: { start_subtitle_id?: string | null; end_subtitle_id?: string | null }) {
    const start = next.start_subtitle_id === undefined ? clipStart : next.start_subtitle_id;
    const end = next.end_subtitle_id === undefined ? clipEnd : next.end_subtitle_id;
    if (!start || !end) {
      patch({ clip: null });
      return;
    }
    patch({ clip: { start_subtitle_id: start, end_subtitle_id: end } });
  }

  function stopAudition() {
    audioRef.current?.pause();
    stopAtRef.current = null;
    setAuditioning(false);
  }

  function auditionClip() {
    const audio = audioRef.current;
    if (!audio || !mediaSource || !clipStartSubtitle || !clipEndSubtitle || clipOrderInvalid) {
      return;
    }
    if (auditioning) {
      stopAudition();
      return;
    }
    setAuditionFailed(false);
    stopAtRef.current = clipEndSubtitle.end_time;
    if (audio.src !== mediaSource) audio.src = mediaSource;
    const play = () => {
      audio.currentTime = clipStartSubtitle.start_time;
      void audio
        .play()
        .then(() => setAuditioning(true))
        .catch(() => {
          setAuditioning(false);
          setAuditionFailed(true);
        });
    };
    if (audio.readyState >= 1) play();
    else audio.addEventListener("loadedmetadata", play, { once: true });
  }

  // --- 表达 ---
  function addExpression() {
    if (draft.expressions.length >= 3) return;
    const id = newStableId(
      "expression",
      draft.expressions.map((expression) => expression.id)
    );
    patch({
      expressions: [
        ...draft.expressions,
        {
          id,
          subtitle_id: "",
          phrase: "",
          word: null,
          gloss_zh: null,
          note_zh: null,
        },
      ],
    });
  }

  function updateExpression(index: number, next: HomeContentDraftExpression) {
    patch({
      expressions: draft.expressions.map((expression, current) =>
        current === index ? next : expression
      ),
    });
  }

  // --- 互动 ---
  function enableInteraction() {
    const interaction: HomeEditorialInteraction = {
      id: newStableId("interaction", [], "interaction"),
      question: "",
      options: [
        { id: "option-1", label: "", feedback: "" },
        { id: "option-2", label: "", feedback: "" },
      ],
    };
    patch({ interaction });
  }

  function updateInteraction(next: HomeEditorialInteraction) {
    patch({ interaction: next });
  }

  // --- 场景 ---
  function addScenario() {
    if (draft.scenarios.length >= 3) return;
    const id = newStableId(
      "scenario",
      draft.scenarios.map((scenario) => scenario.id)
    );
    patch({
      scenarios: [
        ...draft.scenarios,
        {
          id,
          situation_zh: "",
          prompt_zh: "",
          reply_en: "",
          reply_zh: "",
          subtitle_id: null,
        },
      ],
    });
  }

  function updateScenario(index: number, next: HomeContentDraftScenario) {
    patch({
      scenarios: draft.scenarios.map((scenario, current) => (current === index ? next : scenario)),
    });
  }

  return (
    <div className="space-y-5">
      <audio
        ref={audioRef}
        preload="none"
        className="hidden"
        aria-hidden
        onTimeUpdate={() => {
          const audio = audioRef.current;
          if (!audio || stopAtRef.current === null) return;
          if (audio.currentTime >= stopAtRef.current) {
            audio.pause();
            stopAtRef.current = null;
            setAuditioning(false);
          }
        }}
        onEnded={() => setAuditioning(false)}
        onError={() => {
          setAuditioning(false);
          setAuditionFailed(true);
        }}
      />

      <FormSection
        title="基础信息"
        hint="中文编辑标题与推荐理由；难度、时长、来源由视频事实决定，不在这里填写。"
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Field label="编辑标题" hint={`${draft.headline.length}/32 字`}>
            <Input
              value={draft.headline}
              maxLength={32}
              disabled={disabled}
              onChange={(event) => patch({ headline: event.target.value })}
              placeholder="一句话让人想点开"
            />
          </Field>
          <Field label="主题标签（可空）" hint={`${(draft.topic_label ?? "").length}/12 字`}>
            <Input
              value={draft.topic_label ?? ""}
              maxLength={12}
              disabled={disabled}
              onChange={(event) => patch({ topic_label: event.target.value || null })}
              placeholder="例如 图片与真相"
            />
          </Field>
          <div className="md:col-span-2">
            <Field label="推荐理由（dek）" hint={`${draft.dek.length}/80 字`}>
              <Textarea
                rows={2}
                value={draft.dek}
                maxLength={80}
                disabled={disabled}
                onChange={(event) => patch({ dek: event.target.value })}
                placeholder="一两句说清话题与英语收获"
              />
            </Field>
          </div>
        </div>
      </FormSection>

      <FormSection
        title="标题依据句"
        hint="标题与导语依据的真实字幕（0–6 句），方便对照原文；发布时服务端会校验归属。"
      >
        <SubtitleMultiPicker
          subtitles={subtitles}
          selectedIds={draft.evidence_subtitle_ids}
          disabled={disabled}
          onChange={(ids) => patch({ evidence_subtitle_ids: ids })}
        />
        {evidenceSubtitles.length > 0 && (
          <div className="grid grid-cols-1 gap-2">
            {evidenceSubtitles.map((subtitle) => (
              <SubtitleQuote key={subtitle.id} videoId={videoId} subtitle={subtitle} />
            ))}
          </div>
        )}
      </FormSection>

      <FormSection
        title="可试听片段"
        hint="起止句都从该视频真实字幕里选；显示时长以保存后服务端解析结果为准。"
      >
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Field label="起始句">
            <SubtitleSelect
              subtitles={subtitles}
              value={clipStart}
              disabled={disabled}
              emptyLabel="未选择起始句"
              onChange={(subtitleId) => setClip({ start_subtitle_id: subtitleId })}
            />
          </Field>
          <Field label="结束句">
            <SubtitleSelect
              subtitles={subtitles}
              value={clipEnd}
              disabled={disabled}
              emptyLabel="未选择结束句"
              onChange={(subtitleId) => setClip({ end_subtitle_id: subtitleId })}
            />
          </Field>
        </div>
        {clipOrderInvalid && (
          <p className="text-caption text-error-text">起始句必须位于结束句之前。</p>
        )}
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="outline"
            size="compact"
            icon={auditioning ? Pause : Volume2}
            disabled={disabled || !mediaSource || !clipStartSubtitle || !clipEndSubtitle}
            onClick={auditionClip}
            title={mediaSource ? "按字幕真实起止时间试听" : "没有本地可播放媒体，无法试听"}
          >
            {auditioning ? "停止试听" : "试听片段"}
          </Button>
          {clipStartSubtitle && clipEndSubtitle && !clipOrderInvalid && (
            <span className="text-caption text-muted">
              字幕时间 {formatClock(clipStartSubtitle.start_time)}–
              {formatClock(clipEndSubtitle.end_time)}
            </span>
          )}
          <span className="text-meta text-ink">
            服务端解析时长：
            {clipDuration === null ? "保存草稿后显示" : formatSeconds(clipDuration)}
          </span>
        </div>
        {!mediaSource && (
          <p className="text-caption text-muted">
            该视频没有本地可播放媒体：不显示假的播放按钮，请到完整视频验证片段。
          </p>
        )}
        {auditionFailed && (
          <p className="text-caption text-error-text">
            试听失败：媒体暂时无法播放，可到完整视频验证片段。
          </p>
        )}
        {clipStartSubtitle && clipEndSubtitle && !clipOrderInvalid && (
          <div className="grid grid-cols-1 gap-2">
            <SubtitleQuote videoId={videoId} subtitle={clipStartSubtitle} compact />
            {clipEndSubtitle.id !== clipStartSubtitle.id && (
              <SubtitleQuote videoId={videoId} subtitle={clipEndSubtitle} compact />
            )}
          </div>
        )}
      </FormSection>

      <FormSection
        title={`编辑表达（${draft.expressions.length}/3）`}
        hint="选一句真实字幕、选其中的词或短语，并写中文教学说明；发布要求 1–3 条。"
        actions={
          <Button
            variant="outline"
            size="compact"
            icon={Plus}
            disabled={disabled || draft.expressions.length >= 3}
            onClick={addExpression}
          >
            添加表达
          </Button>
        }
      >
        {draft.expressions.length === 0 ? (
          <p className="text-meta text-muted">还没有表达，发布前至少需要 1 条。</p>
        ) : (
          <div className="space-y-3">
            {draft.expressions.map((expression, index) => (
              <ExpressionRow
                key={expression.id}
                videoId={videoId}
                expression={expression}
                index={index}
                subtitles={subtitles}
                subtitle={subtitleById.get(expression.subtitle_id)}
                disabled={disabled}
                onChange={(next) => updateExpression(index, next)}
                onRemove={() =>
                  patch({
                    expressions: draft.expressions.filter((_, current) => current !== index),
                  })
                }
              />
            ))}
          </div>
        )}
      </FormSection>

      <FormSection
        title="互动问题（可选）"
        hint="主观选择、不判对错；选项反馈是预先生成/保存的固定文案，不做实时 AI 聊天。发布要求 2–3 个选项。"
        actions={
          <label className="inline-flex cursor-pointer items-center gap-2 text-meta text-muted">
            <input
              type="checkbox"
              checked={draft.interaction !== null}
              disabled={disabled}
              onChange={(event) =>
                event.target.checked ? enableInteraction() : patch({ interaction: null })
              }
            />
            启用互动
          </label>
        }
      >
        {draft.interaction ? (
          <div className="space-y-3 rounded-md border border-hairline bg-surface-card p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <code className="text-caption text-muted-soft">id: {draft.interaction.id}</code>
            </div>
            <Field label="问题">
              <Input
                value={draft.interaction.question}
                disabled={disabled}
                onChange={(event) =>
                  updateInteraction({ ...draft.interaction!, question: event.target.value })
                }
                placeholder="例如 如果是你，会先看哪里？"
              />
            </Field>
            <div className="space-y-2">
              {draft.interaction.options.map((option, index) => (
                <div
                  key={option.id}
                  className="grid grid-cols-1 gap-2 rounded-sm bg-surface-soft px-3 py-2 md:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)_auto]"
                >
                  <Field label={`选项 ${index + 1} 文案`}>
                    <Input
                      value={option.label}
                      disabled={disabled}
                      onChange={(event) =>
                        updateInteraction({
                          ...draft.interaction!,
                          options: draft.interaction!.options.map((current) =>
                            current.id === option.id
                              ? { ...current, label: event.target.value }
                              : current
                          ),
                        })
                      }
                    />
                  </Field>
                  <Field label="选择后的固定反馈">
                    <Textarea
                      rows={1}
                      value={option.feedback}
                      disabled={disabled}
                      onChange={(event) =>
                        updateInteraction({
                          ...draft.interaction!,
                          options: draft.interaction!.options.map((current) =>
                            current.id === option.id
                              ? { ...current, feedback: event.target.value }
                              : current
                          ),
                        })
                      }
                    />
                  </Field>
                  <div className="flex items-end pb-0.5">
                    <Button
                      variant="ghost"
                      size="compact"
                      icon={Trash2}
                      disabled={disabled || draft.interaction!.options.length <= 2}
                      onClick={() =>
                        updateInteraction({
                          ...draft.interaction!,
                          options: draft.interaction!.options.filter(
                            (current) => current.id !== option.id
                          ),
                        })
                      }
                    >
                      移除
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              size="compact"
              icon={Plus}
              disabled={disabled || draft.interaction.options.length >= 3}
              onClick={() => {
                const existing = draft.interaction!.options.map((option) => option.id);
                const id = newStableId("option", existing, "option");
                updateInteraction({
                  ...draft.interaction!,
                  options: [...draft.interaction!.options, { id, label: "", feedback: "" }],
                });
              }}
            >
              添加选项
            </Button>
          </div>
        ) : (
          <p className="text-meta text-muted">未启用互动；主推卡可以选择不展示互动。</p>
        )}
      </FormSection>

      <FormSection
        title={`场景（${draft.scenarios.length}/3）`}
        hint="「今天就能用」：中文情境 + 英语参考回复 + 中文译文；参考回复不是视频原话，不伪造字幕 ID。"
        actions={
          <Button
            variant="outline"
            size="compact"
            icon={Plus}
            disabled={disabled || draft.scenarios.length >= 3}
            onClick={addScenario}
          >
            添加场景
          </Button>
        }
      >
        {draft.scenarios.length === 0 ? (
          <p className="text-meta text-muted">暂无场景卡；公共页面缺少时整块隐藏，不造占位内容。</p>
        ) : (
          <div className="space-y-3">
            {draft.scenarios.map((scenario, index) => (
              <ScenarioRow
                key={scenario.id}
                videoId={videoId}
                scenario={scenario}
                index={index}
                subtitles={subtitles}
                subtitle={scenario.subtitle_id ? subtitleById.get(scenario.subtitle_id) : undefined}
                disabled={disabled}
                onChange={(next) => updateScenario(index, next)}
                onRemove={() =>
                  patch({
                    scenarios: draft.scenarios.filter((_, current) => current !== index),
                  })
                }
              />
            ))}
          </div>
        )}
      </FormSection>

      <p className="flex items-center gap-1.5 text-caption text-muted-soft">
        <Play size={11} aria-hidden />
        草稿保存不影响线上内容；点击「发布」才会创建不可变版本。
      </p>
    </div>
  );
}
