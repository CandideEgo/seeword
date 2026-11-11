export interface User {
  id: string;
  phone: string | null;
  name: string | null;
  bio: string | null;
  avatar_url: string | null;
  /** The user's gender; null = not filled in (the client then falls back to a seed hash). */
  gender: "male" | "female" | null;
  level: string | null;
  timezone: string | null;
  role?: "user" | "admin";
  last_active_at: string | null;
  onboarding_completed: boolean;
  /** False for phone-only accounts; /set-password uses it to pick first-setup UX. */
  has_password?: boolean;
  created_at: string;
}

/**
 * 卡片形状：**每个**列表端点返回的同一张卡片。
 *
 * 后端由 `services/video_card.serialize_video_card` 唯一产出，键集与
 * `schemas/video.py::VideoResponse` 一一对应（response_model 保证 44 个键都在）。
 * 浏览/首页 feed、搜索、排行榜、收藏、已解锁列表全是它 —— 差别只在 `scope`
 * 填不填 `metric` / `note_excerpt` / `has_note` / `favorited_at` 这几个注解字段。
 *
 * 别名与 `video_id` 这类本地鸭子类型都是形状分叉的产物，别再往回加。
 */
export interface VideoCard {
  id: string;
  title: string;
  /** 中文展示标题（管线翻译 / 管理员维护）；为空时前端回退 title。 */
  title_zh: string | null;
  source_url: string;
  video_source: string;
  thumbnail_url: string | null;
  duration: number | null;
  difficulty_level: string | null;
  status: "pending_processing" | "processing" | "ready_subtitles" | "ready" | "error";
  error_message: string | null;
  topic_tags: string | null;
  is_official: boolean;
  /** Public visibility gate — distinct from is_official (source attribution).
   * Official videos go through draft → review → publish; only published ones
   * appear on the homepage / browse feed. */
  is_published: boolean;
  /** Video review lifecycle (draft/pending_review/published/rejected). */
  review_status: "draft" | "pending_review" | "published" | "rejected";
  /** Admin's rejection reason — 非 owner 一律 null（projector 抹白）。 */
  rejection_reason: string | null;
  video_url_480p: string | null;
  video_url_720p: string | null;
  video_url_1080p: string | null;
  processing_mode: string | null;
  processing_step: string | null;
  processing_progress: number;
  like_count: number;
  favorite_count: number;
  /** 站内播放完成数（complete 事件计数，区别于 ext_view_count 的 YouTube 侧数据）。 */
  view_count: number;
  /** P1 learning_score (0-100). Null until first computed; drives list sorting. */
  score: number | null;
  score_updated_at: string | null;
  /** External (YouTube) metadata + speech metrics (阶段 1/3). Null for local videos. */
  yt_video_id: string | null;
  channel_name: string | null;
  /** 视频简介（来自 external_meta，列表接口截断到 200 字符，详情为全文）；本地视频为 null。 */
  description: string | null;
  /** 首次发布时间；rankings 卡片显示它，其余端点也有。 */
  published_at: string | null;
  /** 作者页 slug（ADR-0014 修订）：视频已挂频道时非空，卡片/播放页链接到 /channels/{slug}。 */
  channel_slug: string | null;
  /** 频道封面（播放页频道入口卡用）；未挂频道或无封面时为 null。 */
  channel_cover_url: string | null;
  upload_date: string | null;
  ext_view_count: number | null;
  ext_like_count: number | null;
  wpm: number | null;
  subtitle_count?: number | null;
  exam_word_count?: number | null;
  sample_text_en?: string | null;
  sample_text_zh?: string | null;
  vocabulary_density: number | null;
  created_at: string;
  /** 榜单名次依据（weekly_views/weekly_favorites 的周增量）；latest 榜与普通卡片为 null。 */
  metric: number | null;
  /** 收藏列表独有：该观看者笔记的前 60 字。其余端点恒为 null。 */
  note_excerpt: string | null;
  /** 是否写过笔记（仅收藏列表会为 true）。 */
  has_note: boolean;
  /** 收藏时间（仅收藏列表）。 */
  favorited_at: string | null;
  /** Fork lineage (Phase 2 standard version): null for originals, UUID of source video for forks */
  forked_from: string | null;
  /** D0 示范视频：不消耗解锁额度，卡片不显示锁标。 */
  is_demo: boolean;
  /** 内容三态（需求 §5.1）：`offline` = 已下线（不可播，学习记录保留）。 */
  storage_mode: "local" | "proxy" | "offline";
}

/** 管理端视频视图：后端 `VideoAdminResponse` = 卡片 + 这几个只有管理员看得见的字段。 */
export interface VideoAdmin extends VideoCard {
  /** Admin-only fields exposed by GET /admin/videos. */
  is_featured: boolean;
  show_on_homepage: boolean;
  admin_notes: string | null;
  /** 翻译质量门禁标记（None | quality_warning | quality_blocked）。只在管理端下发 ——
   * 之前它挂在被所有页面共用的 `Video` 上，等于把管理端字段声明成了公共契约。 */
  quality_flag: string | null;
  /** Review audit fields (admin sees when a video was submitted/reviewed). */
  submitted_at: string | null;
  reviewed_at: string | null;
  /** ADR-0014 站内策展频道（null = 未归属）。 */
  channel_ref?: string | null;
}

/** ADR-0014 官方策展频道。 */
export interface AdminChannel {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  cover_url: string | null;
  upstream_channel_id: string | null;
  sort_order: number;
  is_visible: boolean;
  /** ADR-0014 修订：true = ingest 自动建档的作者页，false = 管理员手建策展频道。 */
  is_auto?: boolean;
  video_count: number;
  created_at: string | null;
}

export interface Paginated<T> {
  items: T[];
  page: number;
  page_size: number;
  has_more: boolean;
  /** 总数（后端 PaginatedResponse.total 可选；列表端点不一定返回）。 */
  total?: number;
}

export interface Subtitle {
  id: string;
  video_id: string;
  start_time: number;
  end_time: number;
  text_en: string;
  text_zh: string | null;
  sentence_index: number;
  grammar_note: string | null;
  /** Exam-level word annotations: lowercased surface token -> exam level keys.
   * Computed once at ingest from ECDICT; see lib/examLevels.ts. */
  word_levels: Record<string, string[]> | null;
  /** Word-level timestamps from WhisperX alignment: [{word, start, end}, ...].
   * Populated at ingest; null for legacy rows / faster-whisper fallback. Used
   * by the subtitle editor split/merge to assign precise timestamps. */
  words?: { word: string; start: number; end: number }[] | null;
  speaker: string | null;
  index?: number;
}

/** One audited subtitle edit (before/after field deltas). Returned by the
 * subtitle revisions endpoints (admin + owner). `before`/`after` map audited
 * field names (text_en, start_time, ...) to their old/new values. */
export interface SubtitleRevision {
  id: string;
  subtitle_id: string;
  video_id: string;
  edited_by: string | null;
  scope: "fork" | "standard" | "sync" | string;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
  created_at: string;
}

/**
 * 播放页 / 视频详情：卡片 + 字幕 + 观看权限。
 * 后端 `VideoDetailResponse` = `VideoResponse` + `subtitles`，同构。
 */
export interface VideoDetail extends VideoCard {
  subtitles: Subtitle[];
}

export interface LearningRecord {
  id: string;
  video_id: string;
  words_learned: number;
  speaking_attempts: number;
  quiz_score: number | null;
  completed: boolean;
  time_spent_seconds: number;
  position_seconds: number;
  created_at: string;
  progress_percentage: number;
  last_accessed_at: string | null;
  video: {
    title: string;
    /** 中文展示标题（VideoBrief 下发，可空）。 */
    title_zh?: string | null;
    thumbnail_url: string | null;
    /** BUG-20：后端 VideoBrief 一直下发这两个字段，此前前端类型漏声明。
     *  duration 是「继续观看」进度分母的权威值（DB `videos.duration`）。 */
    duration: number | null;
    channel_name: string | null;
    view_count?: number | null;
    favorite_count?: number | null;
    upload_date?: string | null;
    published_at?: string | null;
    created_at?: string | null;
    /** 续播卡也展示真实难度；后端 VideoBrief 已下发。 */
    difficulty_level?: string | null;
  } | null;
}

/** Per-question grading result shared by all practice hooks. */
export interface GradedResult {
  correct: boolean;
  /** Textual explanation (null for client-graded items). */
  explanation: string | null;
  /** The correct answer, shown when the learner was wrong. */
  correctAnswer?: string;
}

/* ── Vocabulary ── */
export type MasteryLevel = "new" | "learning" | "reviewing" | "mastered";

export interface VocabularyWord {
  has_lesson_sources?: boolean;
  review_operations_enabled?: boolean;
  id: string;
  word: string;
  ipa: string | null;
  part_of_speech: string | null;
  mastery_level: MasteryLevel;
  review_count: number;
  definition: string | null;
  translation: string | null;
  example_sentences: string[] | null;
  collocations: string[] | null;
  difficulty_level: string | null;
  context_sentence: string | null;
  video_id: string | null;
  /** Display-only enrichment from the backend list/daily-session endpoints. */
  video_title?: string | null;
  subtitle_start_time?: number | null;
  /** 来源字幕（D3b）：存在时闪卡/词卡可「回看原句」深链回播放页。 */
  subtitle_id: string | null;
  next_review_at: string | null;
  created_at: string;
}

/* ── Study rounds + daily quota (DEC-053) ── */

/** Lifecycle of a word inside one round. */
export type StudyItemStatus = "pending" | "learning" | "graduated";

/** One word inside one round; repeated answers UPDATE this row. */
export interface StudySessionItem {
  id: string;
  vocabulary_id: string;
  sort_order: number;
  /** 连续答对计数：答对 +1、答错清零，达到 2 即毕业（设计 §5.1）。 */
  correct_streak: number;
  wrong_in_round: boolean;
  status: StudyItemStatus;
  /** null 表示该词已被删除，前端应跳过该项。 */
  word: VocabularyWord | null;
}

export interface StudySession {
  id: string;
  /** daily = 当日配额那一轮；extra = 加练轮（计入今日累计，不计入今日目标）。 */
  kind: "daily" | "extra";
  local_date: string;
  target_count: number;
  done_count: number;
  correct_count: number;
  status: "active" | "finished" | "abandoned";
  items: StudySessionItem[];
}

/** 今日累计：含加练的已学词数 + 已开始的轮数。 */
export interface TodayTrainingSummary {
  words_learned: number;
  rounds: number;
}

/** GET/PUT /api/v1/vocabulary/preferences — 全局每日配额（非每视频）。 */
export interface VocabularyPreferences {
  daily_new_target: number;
  daily_review_target: number;
  quota_min: number;
  quota_max: number;
}

/* ── Vocab sets (视频词汇集合 + 快速过筛) ── */

/** Sieve/learn lifecycle of a word inside a vocab set. */
export type VocabSetWordStatus = "pending" | "known" | "unknown" | "learned";

/** GET /api/v1/vocab-sets — one video's vocab set summary card. */
export interface VocabSet {
  id: string;
  source_type?: "video" | "exam" | "custom";
  video_id: string | null;
  exam_level: string | null;
  /** Denormalized video fields for card rendering. */
  title: string;
  thumbnail_url: string | null;
  total: number;
  /** known + learned — 集合进度 = mastered_count / total. */
  mastered_count: number;
  last_activity_at: string | null;
  created_at: string;
}

/** POST /api/v1/vocab-sets — creation result (dedupes per video). */
export interface VocabSetCreateResponse {
  id: string;
  video_id: string;
  exam_level: string | null;
  total: number;
  added: number;
  existed: number;
  message: string;
}

/** One word row inside a vocab set (GET /api/v1/vocab-sets/{id}). */
export interface VocabSetWord {
  video_id?: string | null;
  set_word_id: string;
  position: number;
  status: VocabSetWordStatus;
  word: string;
  ipa: string | null;
  translation: string | null;
  part_of_speech: string | null;
  definition: string | null;
  mastery_level: MasteryLevel | null;
  context_sentence: string | null;
  /** 来源句的中文翻译；来自视频时随字幕一起返回，考试/自建词单为 null。 */
  context_sentence_zh?: string | null;
  /** 词的考试级别（取自 ECDICT 标记里的最高级），未知时为 null。 */
  exam_level?: string | null;
  /** Source sentence for 「回到对应句子」 (S7). Null → deep link hidden. */
  subtitle_id?: string | null;
  start_time?: number | null;
}

export type VocabSetScope = "all" | "unmastered" | "learning";

/** GET /api/v1/vocab-sets/{id}?scope=... — set detail incl. word rows. */
export interface VocabSetDetail extends VocabSet {
  words: VocabSetWord[];
}

/** GET /api/v1/vocab-sets/{id}/sieve — current sieve position (resumable). */
export interface VocabSieveState {
  /** Current unsieved word id; null when the pending pass is exhausted. */
  set_word_id: string | null;
  position: number;
  /** 已过筛词数（已掌握 + 待学清单）— 进度 = sieved_count / total。 */
  sieved_count: number;
  total: number;
  /** 已掌握词数（known + learned）— 集合进度分子。 */
  mastered_count: number;
  /** 尚未过筛的词数（第一遍剩余）。 */
  pending_count: number;
  /** 待学清单词数（判「不会」的词，需标记已掌握才闭环）。 */
  unknown_count: number;
  /** 闭环：无 pending 且无 unknown。 */
  completed: boolean;
  word: {
    word: string;
    ipa: string | null;
    translation: string | null;
    part_of_speech: string | null;
    definition: string | null;
  } | null;
}

/* ── Admin ── */
// 与后端 AdminUserResponse 对齐（不 extends User：admin 响应不含
// streak_count/longest_streak/onboarding_completed）。
export interface AdminUser {
  id: string;
  phone: string | null;
  name: string | null;
  bio: string | null;
  avatar_url: string | null;
  /** 默认头像跟随性别（与后端 AdminUserResponse 对齐；null = 按 id 哈希兜底）。 */
  gender: "male" | "female" | null;
  level: string | null;
  timezone: string | null;
  role: string;
  is_banned: boolean;
  created_at: string;
  last_active_at: string | null;
  videos_watched: number;
  learned_words: number;
}

export interface AdminStatsTrend {
  dates: string[];
  signups: number[];
  vocabulary: number[];
  active_users: number[];
}

export type RecentActivityType = "signup";

export interface RecentActivity {
  id: string;
  type: RecentActivityType;
  summary: string;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  new_users_7d: number;
  total_videos: number;
  videos_ready: number;
  total_vocabulary: number;
  active_users_today: number;
  active_users_7d: number;
  // Real-time / today KPIs (DEV-FLOW 2026-07 Phase B2)
  online_now: number;
  gpu_queue_depth: number;
  videos_error_count: number;
  signups_today: number;
  trend: AdminStatsTrend;
  videos_by_status: { status: string; count: number }[];
  recent_activity: RecentActivity[];
  // Prototype 31 extensions
  funnel: {
    registered: number;
    watched: number;
    vocab_saved: number;
  };
  videos_by_topic: { topic: string; count: number }[];
}

/** Singleton admin settings (prototype 32 系统设置). */
export interface AdminSettings {
  site_name: string;
  registration_enabled: boolean;
  quality_block_enabled: boolean;
  quality_block_threshold: number;
  quality_warn_threshold: number;
  hallucination_detection_enabled: boolean;
  translate_timeout_sec: number;
  download_timeout_sec: number;
  download_auto_retry_enabled: boolean;
  watchdog_enabled: boolean;
  updated_at: string | null;
}

/** One admin account row (settings page 管理员账户). */
export interface AdminAccount {
  id: string;
  name: string | null;
  phone: string | null;
  last_active_at: string | null;
}

/* ── Profile ── */
export interface UserPreferences {
  interest_categories?: string[];
  // 后端 UserPreferencesUpdate 限制为 minutes|words；历史 DB 行的
  // speaking_attempts 由设置页（SettingsTab）读取时净化为 "words"。
  daily_goal_type: "minutes" | "words";
  daily_goal_value: number;
  reminder_enabled: boolean;
  reminder_time: string | null;
  reminder_timezone: string | null;
  auto_play_next_subtitle: boolean;
  /** P1-5: vocabulary drills auto-advance ~800ms after a correct answer. */
  auto_advance_on_correct: boolean;
  subtitle_mode_default: "bilingual" | "english" | "chinese";
  preferred_difficulty: string | null;
  /** User's target exam level (canonical key from lib/examLevels.ts, e.g. "cet4"). */
  target_exam: string | null;
}

/* ── Account lifecycle (P1-7) ── */

/** GET/POST /users/me/deletion — 30-day cancellable deletion countdown. */
export interface DeletionStatus {
  scheduled: boolean;
  requested_at: string | null;
  scheduled_at: string | null;
  days_remaining: number | null;
  reason: string | null;
}

/** GET /users/me/export — a queued async export task. */
export interface ExportTask {
  task_id: string;
  status: "pending" | "running" | "ready" | "failed";
  created_at: string | null;
}

/** GET /users/me/export/{task_id} — status + short-lived single-use URL. */
export interface ExportStatus {
  task_id: string;
  status: "pending" | "running" | "ready" | "failed";
  created_at: string | null;
  size_bytes: number | null;
  error: string | null;
  download_url: string | null;
  download_expires_at: string | null;
}

/* ── Exam vocabulary (CET/高考/考研) ── */

/** Rich gloss for a clicked subtitle word (GET /api/v1/words/gloss). */
export interface WordGloss {
  note_scope?: "video" | "general" | null;
  word: string;
  lemma: string | null;
  /** Word-form label, e.g. "复数形式" — present when word is an inflected form of lemma. */
  inflection?: string | null;
  phonetic: string | null;
  pos: string | null;
  definition: string | null;
  translation: string | null;
  levels: string[];
  example_sentence: string | null;
  example_sentence_zh: string | null;
  example_source: string | null;
  is_high_freq: boolean;
  contextual_note: string | null;
  pitfalls: string | null;
  knowledge: string | null;
}

/** A practice question generated from a video's subtitles (GET /videos/{id}/practice). */
export type PracticeItemType =
  | "listen_choose_meaning"
  | "see_word_choose_meaning"
  | "see_meaning_spell_word"
  | "listen_spell_word"
  | "context_fill"
  | "sentence_repeat";

export type PracticeItemCategory = "recognition" | "production" | "context";

/** One adaptive practice item, scored client-side.
 * 6 types across 3 categories. Type is chosen by SM-2 mastery level. */
export interface PracticeItem {
  word: string;
  category: PracticeItemCategory;
  type: PracticeItemType;
  translation: string;
  options: string[] | null;
  answer: string;
  /** context_fill: sentence with ___ blank. */
  sentence_template?: string | null;
  /** sentence_repeat / audio seek. */
  start_time?: number | null;
  end_time?: number | null;
  full_sentence?: string | null;
  phonetic?: string | null;
  /** Phase 1 D3b: source video/subtitle for "回看原句" deep link.
   *  Populated when the drill was scoped to a single video (B0 video_id filter).
   *  start_time/end_time above are reused as the seek targets. */
  video_id?: string | null;
  subtitle_id?: string | null;
}

export interface PracticeResultItem {
  word: string;
  correct: boolean;
}

/** Vocabulary-page practice response (no exam_level wrapper). */
export interface VocabularyPracticeSet {
  items: PracticeItem[];
}

// ---------------------------------------------------------------------------
// Learning Profile (ADR-0012) — streak/掌握度统计由 /plan/profile 提供
// ---------------------------------------------------------------------------

export interface LearningProfile {
  estimated_level: string | null;
  current_streak: number;
  longest_streak: number;
  weekly_cycles_completed: number;
  mastery_by_level: Record<string, Record<string, number>> | null;
  strengths: string[] | null;
  weaknesses: string[] | null;
  milestones?: Milestone[];
  /** 今日累计已学词数（含加练）——DEC-053 起由词汇训练事件驱动。 */
  today_words_learned?: number;
  /** 用户本地日期（YYYY-MM-DD）与本地小时，按学习时区由后端下发（BUG-05）：
   *  首页问候与日期标签用它，不再用浏览器时区自己算「今天」。 */
  local_date?: string;
  local_hour?: number;
}

// ---------------------------------------------------------------------------
// Sprint 4: Milestones + Mastery Trend
// ---------------------------------------------------------------------------

export interface Milestone {
  id: string;
  milestone_type: string;
  achieved_at: string | null;
  metadata_json: Record<string, unknown> | null;
}

export interface MasterySnapshot {
  date: string;
  mastery_json: Record<string, Record<string, number>> | null;
}

export interface MasteryTrendResponse {
  snapshots: MasterySnapshot[];
}

// ---------------------------------------------------------------------------
// A12 学习测量（管理端 /admin/metrics/learning）
// ---------------------------------------------------------------------------

export interface AdminActivationMetrics {
  window_registered: number;
  activated_within_24h: number;
  rate: number | null;
}

export interface AdminCohortRow {
  cohort_date: string;
  size: number;
  d1_eligible: boolean;
  d1_retained: number | null;
  d1_rate: number | null;
  d7_eligible: boolean;
  d7_retained: number | null;
  d7_rate: number | null;
}

export interface AdminWeeklyVolume {
  active_7d: number;
  multi_day_7d: number;
  volume_rate: number | null;
}

export interface AdminEventTypeQuality {
  event_type: string;
  events: number;
  with_event_id: number;
  versions: Record<string, number>;
  missing_event_id_rate: number | null;
}

export interface AdminFlowReconciliation {
  path: string;
  client_results: number;
  client_distinct_flows: number;
  server_facts: number;
  matched: number;
  client_only: number;
  server_only: number;
  duplicate_intents: number;
  loss_rate: number | null;
}

export interface AdminEventQuality {
  by_type: AdminEventTypeQuality[];
  flows: AdminFlowReconciliation[];
}

export interface AdminVitalMetric {
  p75: number | null;
  samples: number;
}

export interface AdminPerformanceMetrics {
  web_vitals: Record<string, AdminVitalMetric>;
  first_play: { p75_ms: number | null; samples: number };
  pipeline_backlog: { pending_dispatches: number; oldest_pending_age_s: number | null };
  schema_version: number;
}

export interface AdminLearningMetrics {
  days: number;
  definitions: Record<string, string>;
  activation: AdminActivationMetrics;
  cohorts: AdminCohortRow[];
  weekly: AdminWeeklyVolume;
  event_quality: AdminEventQuality;
  performance: AdminPerformanceMetrics;
}
