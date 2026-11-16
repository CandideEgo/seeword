/**
 * 首页编辑内容（「好奇心优先」布局）的数据访问与纯判定函数。
 *
 * 契约来源：`frontend/src/types/homeContent.ts`（唯一前端契约）与
 * `backend/app/schemas/home_content.py`。
 *
 * 这里只做三件事：
 *  1. `fetchHomeEditorial()` 读公共接口（不缓存、不轮询——发布/下线要立即生效）；
 *  2. 把「可能为空/残缺」的响应收敛成 `null`，让首页整块退回旧 `FeaturedListening`；
 *  3. 把媒体/片段/表达词的可用性判定收成纯函数，组件不自己猜时间戳是否合法。
 *
 * 页面点击互动选项、收词、播放片段都不经过这里发 AI 请求：选项反馈是服务端
 * 预先生成并随内容版本发布的固定文案，本文件只负责「怎么播、怎么收、怎么显示」。
 */

import { api } from "@/lib/api";
import { formatTime } from "@/lib/format";
import type { VideoCard } from "@/types";
import type {
  HomeEditorialContent,
  HomeEditorialExpression,
  HomeEditorialPage,
} from "@/types/homeContent";

/** 公共读取接口：每次读库，无响应缓存（见实施契约 §1.4）。 */
export const HOME_EDITORIAL_ENDPOINT = "/api/v1/browse/home-editorial";

type VideoMedia = Pick<
  VideoCard,
  "video_url_480p" | "video_url_720p" | "video_url_1080p" | "storage_mode"
>;

export interface ClipPlayback {
  /** 可直接交给 `mediaUrl(source, { withToken: true })` 的媒体路径。 */
  source: string;
  start: number;
  end: number;
}

export interface WordPlayback {
  start: number;
  end: number;
}

export interface HighlightSegment {
  text: string;
  match: boolean;
}

/** 收词入口的四个参数（`POST /api/v1/vocabulary?…`）。 */
export interface VocabularyEntry {
  word: string;
  video_id: string;
  subtitle_id: string;
  context_sentence: string;
}

/**
 * 读公共首页编排。`editorial === null`（未发布 / 全部失效）与请求失败都由调用方
 * 交给旧首页兜底；这里只在响应形状不可用时返回 `null`，不抛「内容不存在」错误。
 */
export async function fetchHomeEditorial(signal?: AbortSignal): Promise<HomeEditorialPage | null> {
  const data = await api<{ editorial: HomeEditorialPage | null } | null>(HOME_EDITORIAL_ENDPOINT, {
    signal,
  });
  return normalizeHomeEditorial(data?.editorial);
}

/**
 * 收敛公共 DTO：
 * - 没有主推（`lead == null`）→ 整块没有新编排，返回 `null`；
 * - 次推按视频去重（不能与主推占同一视频），最多 2 条；
 * - 场景最多 3 条，缺字段的丢弃。失效位置由后端过滤，前端只做展示前的兜底。
 */
export function normalizeHomeEditorial(
  editorial: HomeEditorialPage | null | undefined
): HomeEditorialPage | null {
  const lead = editorial?.lead;
  if (!lead?.content || !lead.video) return null;

  const seenVideoIds = new Set<string>([lead.video.id || lead.content.video_id]);
  const secondary = (editorial?.secondary ?? []).filter((slot) => {
    if (!slot?.content || !slot.video) return false;
    const videoId = slot.video.id || slot.content.video_id;
    if (!videoId || seenVideoIds.has(videoId)) return false;
    seenVideoIds.add(videoId);
    return true;
  });

  const scenarios = (editorial?.scenarios ?? [])
    .filter((slot) => Boolean(slot?.scenario && slot.video))
    .slice(0, 3);

  const expression =
    editorial?.expression?.expression && editorial.expression.video ? editorial.expression : null;

  return {
    ...(editorial as HomeEditorialPage),
    lead,
    secondary: secondary.slice(0, 2),
    expression,
    scenarios,
  };
}

/** 可播放的站内媒体路径：只认本地/代理媒体，下线的视频一律不试听。 */
export function mediaSource(video: VideoMedia): string | null {
  if (video.storage_mode === "offline") return null;
  return video.video_url_480p || video.video_url_720p || video.video_url_1080p || null;
}

/**
 * 片段试听：需要「有本地媒体」且「起始 < 结束、时间有限且非负」。
 * 任一不满足返回 `null` —— 页面此时改为完整视频入口，不展示假的播放按钮。
 */
export function clipPlayback(
  content: HomeEditorialContent,
  video: VideoMedia
): ClipPlayback | null {
  const clip = content.clip;
  if (!clip) return null;
  if (!Number.isFinite(clip.start_time) || !Number.isFinite(clip.end_time)) return null;
  if (clip.start_time < 0 || clip.end_time <= clip.start_time) return null;
  const source = mediaSource(video);
  if (!source) return null;
  return { source, start: clip.start_time, end: clip.end_time };
}

/**
 * 单词试听：只认服务端按词级时间戳解析出的区间，且必须落在原句内；
 * 缺时间戳、顺序颠倒、越界都返回 `null`（页面不显示「听这个词」）。
 */
export function wordPlayback(expression: HomeEditorialExpression): WordPlayback | null {
  const sentence = expression.sentence;
  if (!sentence) return null;
  const start = expression.word_start_time;
  const end = expression.word_end_time;
  if (typeof start !== "number" || typeof end !== "number") return null;
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
  if (start < sentence.start_time - 0.05 || end > sentence.end_time + 0.05) return null;
  return {
    start: Math.max(start, sentence.start_time),
    end: Math.min(end, sentence.end_time),
  };
}

/**
 * 片段按钮上的真实时长文案（例如「42 秒」「1 分 30 秒」）。
 * 页面不得出现固定 90 秒：没有合法时长时返回 `null`，由调用方隐藏数字。
 */
export function clipDurationLabel(seconds: number | null | undefined): string | null {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds <= 0) return null;
  const rounded = Math.max(1, Math.round(seconds));
  if (rounded < 60) return `${rounded} 秒`;
  const minutes = Math.floor(rounded / 60);
  const rest = rounded % 60;
  return rest === 0 ? `${minutes} 分钟` : `${minutes} 分 ${rest} 秒`;
}

/** 全片时长文案（「全片 12:34」）；没有真实时长时返回 `null`，不写占位数字。 */
export function videoDurationLabel(seconds: number | null | undefined): string | null {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds <= 0) return null;
  return `全片 ${formatTime(seconds)}`;
}

/**
 * 收词参数：复用既有 `POST /api/v1/vocabulary`。
 * 只有 `expression.word`（单词语）可收词；短语没有单词时返回 `null`，不伪造。
 * 上下文用真实原句，字幕 ID 用表达所属字幕 —— 不新增查询参数。
 */
export function vocabularyEntry(
  expression: HomeEditorialExpression,
  videoId: string
): VocabularyEntry | null {
  const word = expression.word?.trim();
  const sentence = expression.sentence;
  if (!word || !sentence?.text_en || !videoId) return null;
  return {
    word,
    video_id: videoId,
    subtitle_id: expression.subtitle_id || sentence.subtitle_id,
    context_sentence: sentence.text_en,
  };
}

/** query 串按「word → video_id → subtitle_id → context_sentence」固定顺序拼接。 */
export function vocabularyQuery(entry: VocabularyEntry): string {
  const params = new URLSearchParams();
  params.set("word", entry.word);
  params.set("video_id", entry.video_id);
  if (entry.subtitle_id) params.set("subtitle_id", entry.subtitle_id);
  if (entry.context_sentence) params.set("context_sentence", entry.context_sentence);
  return params.toString();
}

export function vocabularyRequestPath(entry: VocabularyEntry): string {
  return `/api/v1/vocabulary?${vocabularyQuery(entry)}`;
}

/**
 * 在原句中高亮表达（大小写不敏感、只标第一处、保留原文大小写）。
 * 返回分段而不是 HTML 字符串：页面用 `<mark>` 渲染，不注入 `dangerouslySetInnerHTML`。
 */
export function highlightPhrase(
  text: string,
  phrase: string | null | undefined
): HighlightSegment[] {
  if (!text) return [];
  const needle = phrase?.trim();
  if (!needle) return [{ text, match: false }];
  const index = text.toLowerCase().indexOf(needle.toLowerCase());
  if (index < 0) return [{ text, match: false }];
  const segments: HighlightSegment[] = [];
  if (index > 0) segments.push({ text: text.slice(0, index), match: false });
  segments.push({ text: text.slice(index, index + needle.length), match: true });
  const tail = text.slice(index + needle.length);
  if (tail) segments.push({ text: tail, match: false });
  return segments;
}
