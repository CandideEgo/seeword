/**
 * 首页编辑内容（"好奇心优先" 首页 + 后台维护闭环）的唯一前端类型契约。
 *
 * 后端契约在 `backend/app/schemas/home_content.py`，两者必须一一对应；本文件是
 * 前端**唯一**解释这份 JSON 的地方，页面组件不得再自己 `as` cast 任意结构。
 *
 * 三个概念（对应三张表，见 backend/app/models/home_content.py）：
 *
 * - **内容草稿**（`HomeContentDraft`）：每条视频一份、可编辑、可被 AI 生成结果替换。
 * - **已发布内容版本**（`HomeContentRevisionSummary`）：不可变；公共接口只返回它。
 * - **首页布局**（`HomeLayoutPlacement`）：只引用已发布版本 + 稳定 ID，决定位置。
 *
 * 公共展示 DTO（`HomeEditorialPage`）里所有原句、译文、时间、封面、时长都来自
 * 真实字幕/视频数据；后台预览也用同一份 DTO，所以「后台看到什么 = 首页显示什么」。
 */

import type { VideoCard } from "@/types";

// ---------------------------------------------------------------------------
// 基础事实（服务端从真实数据解析，模型只能选，不能写）
// ---------------------------------------------------------------------------

/** 一条真实字幕句。时间与原文由服务端按 subtitle_id 读库填充。 */
export interface HomeEditorialSentence {
  subtitle_id: string;
  sentence_index: number;
  text_en: string;
  text_zh: string | null;
  start_time: number;
  end_time: number;
}

/** 词级时间戳（WhisperX 对齐）；缺失时为空数组。 */
export interface HomeEditorialWordTimestamp {
  word: string;
  start: number;
  end: number;
}

/** 一条编辑表达。`phrase` 必须真实出现在 `sentence.text_en` 里。 */
export interface HomeEditorialExpression {
  id: string;
  subtitle_id: string;
  /** 选中的词或短语（必须在原句里出现）。 */
  phrase: string;
  /** 收词入口用单词（短语为 null）。 */
  word: string | null;
  /** 中文教学说明 / 词典释义；没有就 null，不伪造。 */
  gloss_zh: string | null;
  /** 为什么值得学（编辑理由）。 */
  note_zh: string | null;
  phonetic: string | null;
  /** 服务端按词级时间戳解析；缺时间戳时为 null（此时不显示"听这个词"）。 */
  word_start_time: number | null;
  word_end_time: number | null;
  sentence: HomeEditorialSentence;
}

/** 主观选择，不判对错；选项反馈是预先生成/保存的固定文案。 */
export interface HomeEditorialInteractionOption {
  id: string;
  label: string;
  feedback: string;
}

export interface HomeEditorialInteraction {
  id: string;
  question: string;
  /** 2–3 个选项；没有"正确答案"字段。 */
  options: HomeEditorialInteractionOption[];
}

/** 场景卡：参考表达是生成的教学例句，不是视频原话。 */
export interface HomeEditorialScenario {
  id: string;
  situation_zh: string;
  prompt_zh: string;
  reply_en: string;
  reply_zh: string;
  /**
   * 该场景锚定的真实字幕语境（可定位/跟读）；无则为 null。
   * 页面必须把 `reply_en` 标成"参考表达"，不能用 `sentence` 冒充它。
   */
  sentence: HomeEditorialSentence | null;
}

/** 连续片段，由服务端按字幕 ID 解析并校验时间顺序。 */
export interface HomeEditorialClip {
  start_subtitle_id: string;
  end_subtitle_id: string;
  start_time: number;
  end_time: number;
  /** 秒；页面按钮按它显示真实时长，不得写死的数字。 */
  duration: number;
}

/** 一条已发布内容版本的完整展示数据（不含位置）。 */
export interface HomeEditorialContent {
  content_revision_id: string;
  video_id: string;
  /** 该视频的不可变版本号，从 1 递增。 */
  version: number;
  headline: string;
  dek: string;
  topic_label: string | null;
  /** 来源标签（频道名，缺省 "SeeWord"）。 */
  source_label: string | null;
  published_at: string | null;
  clip: HomeEditorialClip | null;
  /** 1–3 条。 */
  expressions: HomeEditorialExpression[];
  interaction: HomeEditorialInteraction | null;
  /** 0–3 条。 */
  scenarios: HomeEditorialScenario[];
  /** 该内容版本引用的全部字幕（依据 + 片段 + 表达 + 场景），供"看原文"。 */
  sentences: HomeEditorialSentence[];
}

// ---------------------------------------------------------------------------
// 公共展示 DTO —— 首页与后台预览共用
// ---------------------------------------------------------------------------

/** 主推 / 次推卡：整条视频的内容版本。 */
export interface HomeEditorialVideoSlot {
  content: HomeEditorialContent;
  /** 视频事实（与列表卡片同一形状）；媒体鉴权、封面、时长都读它。 */
  video: VideoCard;
}

/** 「换个说法」卡：选定内容版本里的某一条表达。 */
export interface HomeEditorialExpressionSlot {
  content_revision_id: string;
  expression_id: string;
  headline: string;
  topic_label: string | null;
  video: VideoCard;
  expression: HomeEditorialExpression;
}

/** 「今天就能用」场景卡：选定内容版本里的某一个场景。 */
export interface HomeEditorialScenarioSlot {
  content_revision_id: string;
  scenario_id: string;
  video: VideoCard;
  scenario: HomeEditorialScenario;
}

/**
 * `GET /api/v1/browse/home-editorial` 的 `editorial` 字段。
 *
 * `lead == null` 表示没有可用的新编排（未发布 / 全部失效），首页整块退回既有
 * `featured + learning metadata` 流程。次推失效时会被提升为主推，所以只要
 * `lead != null` 就至少有一条可展示内容。
 */
export interface HomeEditorialPage {
  /** 当前发布布局的 revision，用于缓存键/调试，不影响展示。 */
  layout_revision: number;
  published_at: string | null;
  lead: HomeEditorialVideoSlot | null;
  /** 最多 2 条，且与主推不同视频。 */
  secondary: HomeEditorialVideoSlot[];
  expression: HomeEditorialExpressionSlot | null;
  scenarios: HomeEditorialScenarioSlot[];
}

// ---------------------------------------------------------------------------
// 后台：草稿（可编辑、允许不完整）
// ---------------------------------------------------------------------------

export interface HomeContentDraftExpression {
  id: string;
  subtitle_id: string;
  phrase: string;
  word: string | null;
  gloss_zh: string | null;
  note_zh: string | null;
}

export interface HomeContentDraftScenario {
  id: string;
  situation_zh: string;
  prompt_zh: string;
  reply_en: string;
  reply_zh: string;
  subtitle_id: string | null;
}

/** 草稿只存"编辑决策 + 引用"，原文/时间/封面永远读真实数据。 */
export interface HomeContentDraft {
  headline: string;
  dek: string;
  topic_label: string | null;
  evidence_subtitle_ids: string[];
  clip: { start_subtitle_id: string; end_subtitle_id: string } | null;
  expressions: HomeContentDraftExpression[];
  interaction: HomeEditorialInteraction | null;
  scenarios: HomeContentDraftScenario[];
}

// ---------------------------------------------------------------------------
// 后台：生成状态 + 版本列表 + 布局
// ---------------------------------------------------------------------------

export type HomeContentGenerationStatus = "idle" | "queued" | "running" | "succeeded" | "failed";

export interface HomeContentGenerationCoverage {
  mode: "single" | "segmented";
  ai_calls: number;
  total_sentences: number;
  covered_sentences: number;
  planned_segments: number;
  segments_sent: number;
  truncated: boolean;
  is_full_coverage: boolean;
  covered_ranges: [number, number][];
}

export interface HomeContentGeneration {
  generation_id: string;
  status: HomeContentGenerationStatus;
  /** 入队时间（ISO）。 */
  started_at: string | null;
  finished_at: string | null;
  error_code: string | null;
  error_message: string | null;
  /** 生成时使用的模型 / prompt 版本；不可用则为 null。 */
  model: string | null;
  prompt_version: string | null;
  /** AI 服务返回的 token 统计；服务不返回时为 null（不估算）。 */
  usage: { prompt_tokens: number | null; completion_tokens: number | null } | null;
  /** 真实送入模型的字幕覆盖情况；历史任务为空。 */
  coverage: HomeContentGenerationCoverage | null;
}

export interface HomeContentRevisionSummary {
  id: string;
  version: number;
  headline: string;
  dek: string;
  published_at: string | null;
  published_by_name: string | null;
  /** 该版本存储的来源指纹与当前字幕是否已不一致（不一致则不可再用于布局）。 */
  source_changed: boolean;
  /** 该版本当前被摆在哪些位置。 */
  positions: HomeContentSlotPosition[];
  expression_ids: string[];
  scenario_ids: string[];
}

export type HomeContentSlotPosition = "lead" | "secondary" | "expression" | "scenario";

/** `GET /api/v1/admin/home-content/videos/{video_id}` */
export interface HomeContentVideoState {
  video_id: string;
  video_title: string;
  /** 视频是否满足公共可见条件（发布时强制校验）。 */
  publicly_visible: boolean;
  /** 当前视频字幕指纹，供前端展示"来源已变更"。 */
  source_fingerprint: string;
  draft: HomeContentDraft | null;
  /** 草稿乐观锁 revision；无草稿时 0。 */
  draft_revision: number;
  /** 草稿依据的来源指纹与当前不一致。 */
  source_changed: boolean;
  /** 草稿是否有未保存的编辑依据变化（同 source_changed，保留语义别名）。 */
  generation: HomeContentGeneration | null;
  revisions: HomeContentRevisionSummary[];
  /** 该视频当前在发布布局里的位置（无则空数组）。 */
  positions: HomeContentSlotPosition[];
}

export interface HomeLayoutPlacement {
  lead: { content_revision_id: string } | null;
  secondary: { content_revision_id: string }[];
  expression: { content_revision_id: string; expression_id: string } | null;
  scenarios: { content_revision_id: string; scenario_id: string }[];
}

/** 可选内容版本（编排页的候选池；只含已发布、来源有效的版本）。 */
export interface HomeContentCandidate {
  content_revision_id: string;
  video_id: string;
  video_title: string;
  thumbnail_url: string | null;
  duration: number | null;
  difficulty_level: string | null;
  topic_label: string | null;
  headline: string;
  dek: string;
  published_at: string | null;
  /** 来源或可见性已失效的版本仍列出（给人解释为什么不能选），但不能被发布。 */
  source_changed: boolean;
  publicly_visible: boolean;
  expression_ids: string[];
  scenario_ids: string[];
  positions: HomeContentSlotPosition[];
}

export interface HomeLayoutIssue {
  /** 字段路径，如 "lead" / "secondary[0]" / "scenarios[1]" / "expression"。 */
  field: string;
  code: string;
  message: string;
}

/** `GET /api/v1/admin/home-content/layout` */
export interface HomeLayoutState {
  draft_layout: HomeLayoutPlacement;
  published_layout: HomeLayoutPlacement | null;
  previous_published_layout: HomeLayoutPlacement | null;
  /** 草稿布局的乐观锁 revision。 */
  revision: number;
  /** 已发布布局生效时的 revision（可能小于 revision，表示草稿未发布）。 */
  published_revision: number | null;
  /** 发布布局当前是否还有可用内容（公开接口是否走新首页）。 */
  published_active: boolean;
  updated_at: string | null;
  published_at: string | null;
  candidates: HomeContentCandidate[];
  /** 当前 draft_layout 的字段级问题；发布会被拒绝。 */
  issues: HomeLayoutIssue[];
}

/**
 * 后台预览统一响应：`GET /admin/home-content/videos/{id}/preview` 与
 * `GET /admin/home-content/layout/preview` 都返回 `{page, issues}`。
 *
 * `page` 是按草稿（或草稿布局）尽力构造的展示数据 —— 与公共接口同形，直接喂给
 * 公共展示组件；`issues` 是该草稿/布局当前发布会被拒绝的字段级问题。
 */
export interface HomeLayoutPreview {
  page: HomeEditorialPage | null;
  issues: HomeLayoutIssue[];
}
