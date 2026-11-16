/**
 * 管理端「首页编辑内容」数据访问层（backend/app/schemas/home_content.py）。
 *
 * 只封装 `/api/v1/admin/home-content/*` 的管理员接口，鉴权走 `adminApi`
 * （`seeword_admin_token`，与用户端会话分离）。领域类型一律从
 * `@/types/homeContent` 引入——那是前端唯一契约，本文件不重复解释 JSON 形状。
 *
 * 后台预览只走这里的 `getHomeContentPreview` / `getHomeLayoutPreview`；
 * **不**调用公共 `/browse/home-editorial`，更没有 `?draft=true` 这类绕过发布边界的查询。
 */

import { adminApi } from "@/lib/adminApi";
import type {
  HomeContentDraft,
  HomeContentGeneration,
  HomeContentVideoState,
  HomeLayoutPlacement,
  HomeLayoutPreview,
  HomeLayoutState,
} from "@/types/homeContent";

const BASE = "/api/v1/admin/home-content";

// ---------------------------------------------------------------------------
// 响应 envelope（接口层形状；领域 DTO 在 types/homeContent.ts）
// ---------------------------------------------------------------------------

/** `POST /videos/{id}/generate` 的响应；`reused` 表示复用了正在跑的任务。 */
export interface HomeContentGenerateResult {
  generation: HomeContentGeneration;
  reused: boolean;
}

/** `POST /videos/{id}/publish` 的响应。 */
export interface HomeContentPublishResult {
  revision_id: string;
  version: number;
  layout_revision?: number | null;
}

/** `POST /layout/publish` / `POST /layout/rollback` 的响应。 */
export interface HomeLayoutRevisionResult {
  layout_revision: number;
  /**
   * 回滚时没有更早的发布布局：后端已原子撤下当前编排、首页回到旧版精选兜底
   *（`published_layout=null`）。老响应可能不带该字段，按 false 处理。
   */
  cleared?: boolean;
}

// ---------------------------------------------------------------------------
// 错误语义（契约 §4「错误语义」）
// ---------------------------------------------------------------------------

/** 乐观锁不匹配：409。UI 文案必须提示刷新，不做最后写入者覆盖。 */
export const HOME_CONTENT_REVISION_CONFLICT = "HOME_CONTENT_REVISION_CONFLICT";
/** 已有草稿但未确认覆盖：409。 */
export const HOME_CONTENT_OVERWRITE_CONFIRM = "HOME_CONTENT_OVERWRITE_CONFIRM";
/** 409 给用户看的固定文案（验收要求逐字一致）。 */
export const REVISION_CONFLICT_MESSAGE = "内容已在别处修改，请刷新后重试";

interface ApiErrorLike {
  status?: unknown;
  code?: unknown;
}

/** 只按「status + envelope code」判断，不依赖具体错误类，避免重复造错误类型。 */
export function isApiErrorWithCode(err: unknown, code: string): boolean {
  if (!err || typeof err !== "object") return false;
  return (err as ApiErrorLike).code === code;
}

export function apiErrorStatus(err: unknown): number | null {
  if (!err || typeof err !== "object") return null;
  const status = (err as ApiErrorLike).status;
  return typeof status === "number" ? status : null;
}

/** 409 HOME_CONTENT_REVISION_CONFLICT（保存/发布/恢复/布局都要处理）。 */
export function isRevisionConflictError(err: unknown): boolean {
  return apiErrorStatus(err) === 409 && isApiErrorWithCode(err, HOME_CONTENT_REVISION_CONFLICT);
}

/** 409 HOME_CONTENT_OVERWRITE_CONFIRM（生成时未确认覆盖已有草稿）。 */
export function isOverwriteConfirmError(err: unknown): boolean {
  return apiErrorStatus(err) === 409 && isApiErrorWithCode(err, HOME_CONTENT_OVERWRITE_CONFIRM);
}

// ---------------------------------------------------------------------------
// 空值（新建草稿/布局时的起点）
// ---------------------------------------------------------------------------

/** 空白草稿：只含结构，不含任何编造的原文/时间。 */
export function emptyDraft(): HomeContentDraft {
  return {
    headline: "",
    dek: "",
    topic_label: null,
    evidence_subtitle_ids: [],
    clip: null,
    expressions: [],
    interaction: null,
    scenarios: [],
  };
}

/** 空布局常量（与本文件注释一致：lead null / secondary [] / expression null / scenarios []）。 */
export function emptyLayout(): HomeLayoutPlacement {
  return { lead: null, secondary: [], expression: null, scenarios: [] };
}

// ---------------------------------------------------------------------------
// 纯判定
// ---------------------------------------------------------------------------

/** 生成任务是否还在跑（queued/running）——轮询与按钮 disabled 共用这一条。 */
export function isGenerationActive(generation: HomeContentGeneration | null | undefined): boolean {
  return generation?.status === "queued" || generation?.status === "running";
}

// ---------------------------------------------------------------------------
// 视频详情：状态 / 草稿 / 生成任务
// ---------------------------------------------------------------------------

/** `GET /videos/{id}` —— 草稿、版本列表、生成状态、当前位置一次读回。 */
export function getHomeContentVideoState(videoId: string): Promise<HomeContentVideoState> {
  return adminApi<HomeContentVideoState>(`${BASE}/videos/${encodeURIComponent(videoId)}`);
}

/** `POST /videos/{id}/generate` —— 入队生成；重复点击会复用已有任务。 */
export function generateHomeContentDraft(
  videoId: string,
  options: { expectedRevision?: number; overwrite?: boolean } = {}
): Promise<HomeContentGenerateResult> {
  const body: { expected_revision?: number; overwrite?: boolean } = {};
  if (typeof options.expectedRevision === "number")
    body.expected_revision = options.expectedRevision;
  if (typeof options.overwrite === "boolean") body.overwrite = options.overwrite;
  return adminApi<HomeContentGenerateResult>(
    `${BASE}/videos/${encodeURIComponent(videoId)}/generate`,
    { method: "POST", body: JSON.stringify(body) }
  );
}

/** `GET /videos/{id}/generation` —— 轮询生成状态（服务端顺手做超时恢复）。 */
export async function getHomeContentGeneration(
  videoId: string
): Promise<HomeContentGeneration | null> {
  const res = await adminApi<{ generation: HomeContentGeneration | null }>(
    `${BASE}/videos/${encodeURIComponent(videoId)}/generation`
  );
  return res.generation ?? null;
}

/** `PUT /videos/{id}/draft` —— 保存草稿（草稿宽松，允许不完整）。 */
export function saveHomeContentDraft(
  videoId: string,
  payload: HomeContentDraft,
  expectedRevision: number
): Promise<HomeContentVideoState> {
  return adminApi<HomeContentVideoState>(`${BASE}/videos/${encodeURIComponent(videoId)}/draft`, {
    method: "PUT",
    body: JSON.stringify({ payload, expected_revision: expectedRevision }),
  });
}

/** `POST /videos/{id}/publish` —— 校验并创建不可变版本；可同事务替换首页位置。 */
export function publishHomeContent(
  videoId: string,
  expectedRevision: number,
  place: "lead" | "secondary" | null
): Promise<HomeContentPublishResult> {
  return adminApi<HomeContentPublishResult>(
    `${BASE}/videos/${encodeURIComponent(videoId)}/publish`,
    { method: "POST", body: JSON.stringify({ expected_revision: expectedRevision, place }) }
  );
}

/** `POST /videos/{id}/restore-draft` —— 复制历史版本为草稿。 */
export function restoreHomeContentDraft(
  videoId: string,
  revisionId: string,
  expectedRevision: number
): Promise<HomeContentVideoState> {
  return adminApi<HomeContentVideoState>(
    `${BASE}/videos/${encodeURIComponent(videoId)}/restore-draft`,
    {
      method: "POST",
      body: JSON.stringify({ revision_id: revisionId, expected_revision: expectedRevision }),
    }
  );
}

/** `GET /videos/{id}/preview` —— 后台预览：由草稿尽力构造，不要求已发布。 */
export function getHomeContentPreview(videoId: string): Promise<HomeLayoutPreview> {
  return adminApi<HomeLayoutPreview>(`${BASE}/videos/${encodeURIComponent(videoId)}/preview`);
}

// ---------------------------------------------------------------------------
// 首页编排：布局草稿 / 发布 / 回滚 / 预览
// ---------------------------------------------------------------------------

/** `GET /layout` —— 草稿布局、已发布布局、上一版、候选池与字段级问题。 */
export function getHomeLayout(): Promise<HomeLayoutState> {
  return adminApi<HomeLayoutState>(`${BASE}/layout`);
}

/** `PUT /layout/draft` —— 保存编排草稿，乐观锁。 */
export function saveHomeLayoutDraft(
  layout: HomeLayoutPlacement,
  expectedRevision: number
): Promise<HomeLayoutState> {
  return adminApi<HomeLayoutState>(`${BASE}/layout/draft`, {
    method: "PUT",
    body: JSON.stringify({ layout, expected_revision: expectedRevision }),
  });
}

/** `POST /layout/publish` —— 校验并原子发布整版。 */
export function publishHomeLayout(expectedRevision: number): Promise<HomeLayoutRevisionResult> {
  return adminApi<HomeLayoutRevisionResult>(`${BASE}/layout/publish`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: expectedRevision }),
  });
}

/** `POST /layout/rollback` —— 校验并恢复上一发布布局。 */
export function rollbackHomeLayout(expectedRevision: number): Promise<HomeLayoutRevisionResult> {
  return adminApi<HomeLayoutRevisionResult>(`${BASE}/layout/rollback`, {
    method: "POST",
    body: JSON.stringify({ expected_revision: expectedRevision }),
  });
}

/** `GET /layout/preview` —— 用已发布布局渲染整页预览（与公共 DTO 同形）。 */
export function getHomeLayoutPreview(): Promise<HomeLayoutPreview> {
  return adminApi<HomeLayoutPreview>(`${BASE}/layout/preview`);
}
