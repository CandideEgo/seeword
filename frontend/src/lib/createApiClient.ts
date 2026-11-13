/**
 * createApiClient — factory for typed API clients with shared retry/auth logic.
 *
 * Extracts the duplicated infrastructure between lib/api.ts (user) and
 * lib/adminApi.ts (admin): retry with backoff, 401 refresh, error parsing.
 *
 * Each consumer provides its own "auth adapter" (getToken, refresh, logout)
 * so the core loop stays identical while auth specifics remain isolated.
 */

import type { RefreshOutcome } from "@/lib/sessionRefresh";

// ---------------------------------------------------------------------------
// Shared retry helpers
// ---------------------------------------------------------------------------

export const MAX_RETRIES = 2;
export const RETRY_DELAYS_MS = [1000, 2000]; // 1s, then 2s

export function isRetryableStatus(status: number): boolean {
  return status >= 500 && status < 600;
}

export function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    if (signal) {
      const onAbort = () => {
        clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      };
      if (signal.aborted) {
        clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      } else {
        signal.addEventListener("abort", onAbort, { once: true });
      }
    }
  });
}

/**
 * 单次请求的默认期限（A03 / FE-07）。没有这条，一个卡在半开连接上的请求会让
 * 页面壳永远停在骨架屏 —— 例如 MainLayoutInner 等 `/users/me` 的 onboarding 门。
 * 大文件上传等场景可以按请求传 `timeoutMs` 覆盖。
 */
export const DEFAULT_REQUEST_TIMEOUT_MS = 20_000;

interface Deadline {
  signal: AbortSignal;
  timedOut: () => boolean;
  cleanup: () => void;
}

/** 把调用方的 signal 与一个超时合并成同一个 AbortSignal。 */
function withDeadline(signal: AbortSignal | undefined, timeoutMs: number): Deadline {
  const controller = new AbortController();
  let timedOut = false;
  const timer =
    timeoutMs > 0
      ? setTimeout(() => {
          timedOut = true;
          controller.abort();
        }, timeoutMs)
      : null;
  const onAbort = () => controller.abort();
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", onAbort, { once: true });
  }
  return {
    signal: controller.signal,
    timedOut: () => timedOut,
    cleanup: () => {
      if (timer) clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
    },
  };
}

// ---------------------------------------------------------------------------
// Auth adapter — pluggable token / refresh / logout
// ---------------------------------------------------------------------------

export interface AuthAdapter {
  /** Return the current access token (null if not logged in) */
  getToken(): string | null;
  /**
   * Attempt to refresh the access token.
   *
   * The three outcomes are not interchangeable: only ``"expired"`` means the
   * session is over. ``"unavailable"`` (network/timeout/5xx) must not clear
   * the session — the refresh token is probably still valid.
   */
  refreshToken(): Promise<RefreshOutcome>;
  /** Called when the session is definitively invalid (e.g. refresh said 401). */
  onSessionExpired(): void;
}

// ---------------------------------------------------------------------------
// Error class
// ---------------------------------------------------------------------------

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly response: Response | null;
  /** Structured API diagnostics, when supplied by the error envelope. */
  detail: unknown;

  constructor(
    message: string,
    status: number = 0,
    code: string | null = null,
    response: Response | null = null
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.response = response;
  }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

export interface CreateApiClientOptions {
  /** Base URL for API requests */
  baseUrl: string;
  /** Auth adapter for token management */
  auth: AuthAdapter;
  /** Custom error class (must accept the same constructor args as ApiClientError) */
  ErrorClass?: typeof ApiClientError;
  /** Whether to handle 204 No Content and non-JSON responses (admin client needs this) */
  handleNonJsonResponses?: boolean;
  /**
   * Identity of this client for cache / in-flight isolation (defaults to an
   * auto-generated per-instance id).
   *
   * The user client (`lib/api.ts`) and the admin client (`lib/adminApi.ts`) are
   * two separate sessions with two separate tokens, but the GET cache and the
   * in-flight dedupe live at module level. Give each client its own scope so
   * one session can never read another's cached payload or borrow its
   * Authorization header — see the "key composition" note below.
   */
  cacheScope?: string;
}

export interface ApiClientRequestOptions extends Omit<RequestInit, "signal"> {
  signal?: AbortSignal;
  /**
   * Per-attempt deadline in milliseconds. Defaults to
   * ``DEFAULT_REQUEST_TIMEOUT_MS``; pass 0 to disable (long uploads/downloads).
   */
  timeoutMs?: number;
  /**
   * GET-only: serve this request from a local TTL cache (milliseconds).
   * Responses are cloned on read/write so callers can't poison the cache.
   * Leave unset for requests that must always be fresh.
   */
  cacheTtlMs?: number;
}

// ---------------------------------------------------------------------------
// GET cache + in-flight dedupe
// ---------------------------------------------------------------------------
//
// - Dedupe: concurrent identical GETs (e.g. two components mounting at once)
//   share one network request. Always on, zero staleness risk.
// - TTL cache: opt-in via `cacheTtlMs`; useful for near-static payloads.
// Any non-GET request invalidates the whole TTL cache (crude but safe —
// mutations are rare relative to reads).
//
// **键里必须带身份**（G2 / checklist 6.1）：`lib/api.ts`（用户端）与
// `lib/adminApi.ts`（管理端）是两套会话、两套 token，却共用本模块的模块级缓存。
// 键只有 url 时会出两个真故障：
//   1) 用户端登录后 `/api/v1/users/me` 进 30s TTL 缓存；管理端再请求同一 URL
//      会**命中用户端的缓存**（不校验 admin token）→ `u.role !== "admin"`
//      → 管理员被弹回 `/admin/login`，表现为「明明是管理员却登不进后台」；
//   2) `_inflightGets` 无条件对所有 GET 生效：两个 client 同时请求同一 URL 时
//      共用同一个 in-flight promise，只发一次请求、带的是先发起那次的 token。
// 现在键 = `<scope>|<session token>|<url>`：
//   - scope：每个 client 实例一个（可用 `cacheScope` 显式命名，如 user/admin），
//     两套会话的缓存与在途请求天然不互通；
//   - session token：同一 client 里换人登录（token 变了）也不会读到上一个人的缓存；
//   - url：请求本身。
//
// 存储仍是一个模块级 Map（不是每 client 一个实例）：这样任何非 GET 写操作
// 依旧能一次性作废全部 TTL 缓存（见 request() 里的 clear），不会因为隔离而
// 让「管理端改了内容、用户端还拿着旧缓存」。

type CacheEntry = { value: unknown; expiresAt: number; url: string };

const _getCache = new Map<string, CacheEntry>();
const _inflightGets = new Map<string, Promise<unknown>>();
const _GET_CACHE_MAX = 200;

/** Auto-incrementing id: gives every client instance an independent scope. */
let _clientSeq = 0;

/**
 * Session identity for cache keys — the access token itself.
 *
 * The token *is* the session identity: a hash would only trade a (tiny but
 * real) collision risk — i.e. one session reading another session's payload —
 * for a shorter key. The key never leaves this module's in-memory Map: it is
 * not logged, not persisted and not sent anywhere.
 */
function _sessionIdentity(token: string | null): string {
  return token ?? "anon";
}

/** Cache key: client identity + session identity + request. */
function _cacheKey(scope: string, token: string | null, url: string): string {
  return `${scope}|${_sessionIdentity(token)}|${url}`;
}

/** Drop cached GET responses (all of them, or those whose URL starts with `prefix`). */
export function clearApiCache(prefix?: string) {
  if (!prefix) {
    _getCache.clear();
    return;
  }
  // The key is now composite, so match on the URL it was stored with — the
  // documented semantics ("drop cached GETs whose URL starts with prefix")
  // stay the same for callers.
  for (const [key, entry] of _getCache) {
    if (entry.url.startsWith(prefix)) _getCache.delete(key);
  }
}

function _clone<T>(value: T): T {
  if (typeof structuredClone === "function") return structuredClone(value);
  // Old engines: a JSON round-trip still deep-copies (API payloads are plain
  // JSON) — returning the original reference would let one caller poison the
  // cache for every other consumer.
  return JSON.parse(JSON.stringify(value)) as T;
}

async function _dedupedGet<T>(key: string, fn: () => Promise<T>): Promise<T> {
  let pending = _inflightGets.get(key) as Promise<T> | undefined;
  if (!pending) {
    pending = fn().finally(() => _inflightGets.delete(key));
    _inflightGets.set(key, pending);
  }
  // Clone so each consumer gets its own copy (protects cache + other callers).
  return _clone(await pending);
}

export function createApiClient(options: CreateApiClientOptions) {
  const { baseUrl, auth, ErrorClass = ApiClientError, handleNonJsonResponses = false } = options;
  // Each client instance gets its own scope, so the user session and the admin
  // session never share a cached payload or an in-flight request.
  const scope = options.cacheScope ?? `client-${++_clientSeq}`;

  async function request<T = unknown>(
    path: string,
    reqOptions: ApiClientRequestOptions = {}
  ): Promise<T> {
    const { cacheTtlMs, ...rest } = reqOptions;
    const method = (rest.method ?? "GET").toUpperCase();
    const url = path.startsWith("http") ? path : `${baseUrl}${path}`;

    if (method === "GET" && !rest.body && !rest.signal) {
      // Identity-aware key: same URL under a different client or a different
      // session is a different entry (and a different in-flight request).
      const key = _cacheKey(scope, auth.getToken(), url);
      const fetchFn = () => performRequest<T>(url, rest);
      if (cacheTtlMs && cacheTtlMs > 0) {
        const hit = _getCache.get(key);
        if (hit && hit.expiresAt > Date.now()) {
          return _clone(hit.value) as T;
        }
        const value = await _dedupedGet(key, fetchFn);
        if (_getCache.size >= _GET_CACHE_MAX) _getCache.clear();
        _getCache.set(key, { value, expiresAt: Date.now() + cacheTtlMs, url });
        return _clone(value) as T;
      }
      return _dedupedGet(key, fetchFn);
    }

    // Mutations invalidate cached GET payloads.
    if (_getCache.size > 0) _getCache.clear();
    return performRequest<T>(url, rest);
  }

  async function performRequest<T = unknown>(
    url: string,
    reqOptions: Omit<ApiClientRequestOptions, "cacheTtlMs">
  ): Promise<T> {
    const { signal, timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS, ...restOptions } = reqOptions;
    const method = (restOptions.method ?? "GET").toUpperCase();
    // Re-sending a non-idempotent request whose response was lost can duplicate
    // the server-side side effect, so retries are limited to GET/HEAD.
    const retryable = method === "GET" || method === "HEAD";
    const headers = new Headers(restOptions.headers as HeadersInit);

    // Content-Type
    if (
      restOptions.body &&
      !(restOptions.body instanceof FormData) &&
      !headers.has("Content-Type")
    ) {
      headers.set("Content-Type", "application/json");
    }

    // Token + pre-request expiry check
    let token = auth.getToken();
    let alreadyRefreshed = false;
    if (token) {
      const { isTokenExpired } = await import("./jwt");
      if (isTokenExpired(token)) {
        const outcome = await auth.refreshToken();
        if (outcome === "refreshed") {
          token = auth.getToken();
          alreadyRefreshed = true;
        } else if (outcome === "unavailable") {
          // 临时不可用：会话可能仍然有效，绝不清空。给调用方一个可重试的错误。
          throw new ErrorClass("暂时无法验证登录状态，请检查网络后重试", 0);
        } else {
          throw new ErrorClass("登录已过期，请重新登录", 401);
        }
      }
      if (token) headers.set("Authorization", `Bearer ${token}`);
    }
    // Did the first attempt go out with credentials? A 401 on a request that
    // carried none is the server rejecting the request itself (failed login,
    // missing permission), not an expired session — see the 401 branch below.
    const sentWithAuth = headers.has("Authorization");

    let lastError: InstanceType<typeof ErrorClass> | null = null;

    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
      if (signal?.aborted) {
        throw new DOMException("Aborted", "AbortError");
      }

      let res: Response;
      const deadline = withDeadline(signal, timeoutMs);
      try {
        res = await fetch(url, { ...restOptions, headers, signal: deadline.signal });
      } catch (err) {
        const timedOut = deadline.timedOut();
        // 调用方主动取消（切页、组件卸载）原样抛 AbortError，不当作网络错误。
        if (!timedOut && err instanceof DOMException && err.name === "AbortError") throw err;

        lastError = new ErrorClass(
          timedOut ? "请求超时，请稍后重试" : "网络连接失败，请检查网络或稍后重试",
          0,
          null,
          null
        ) as InstanceType<typeof ErrorClass>;

        if (retryable && attempt < MAX_RETRIES) {
          await sleep(RETRY_DELAYS_MS[attempt], signal);
          continue;
        }
        throw lastError;
      } finally {
        deadline.cleanup();
      }

      // 401 → refresh token and retry. Only when the request actually carried
      // credentials (an unauthenticated 401 is a rejection of the request, e.g.
      // a failed login, and refreshing would log the user out instead of letting
      // the caller show the server's message), only once per request, and only if
      // we haven't already refreshed in the pre-request check — with rotating
      // refresh tokens, a second refresh would fail and cause unexpected logout.
      if (res.status === 401 && attempt === 0 && !alreadyRefreshed && sentWithAuth) {
        const outcome = await auth.refreshToken();
        if (outcome === "refreshed") {
          const newToken = auth.getToken();
          if (newToken) headers.set("Authorization", `Bearer ${newToken}`);
          // Continue the retry loop with the new token
          continue;
        }
        if (outcome === "unavailable") {
          // 服务端/网络临时故障不是账号失效：保留会话，让用户重试。
          throw new ErrorClass("暂时无法刷新登录状态，请稍后重试", 0, null, res) as InstanceType<
            typeof ErrorClass
          >;
        }
        // Refresh failed — session is over
        auth.onSessionExpired();
        throw new ErrorClass("登录已过期，请重新登录", 401, null, res) as InstanceType<
          typeof ErrorClass
        >;
      }

      // Non-ok response
      if (!res.ok) {
        let detail = "请求失败";
        let code: string | null = null;
        let structuredDetail: unknown;
        try {
          const data = await res.json();
          code = data.code ?? null;
          structuredDetail = data.detail;
          // 统一 envelope: {code, message, detail?}。优先 message（后端全局
          // handler 已格式化），回退 detail（向后兼容 / 422 数组）。
          if (typeof data.message === "string" && data.message) {
            detail = data.message;
          } else {
            const d = data.detail;
            if (Array.isArray(d)) {
              // FastAPI/Pydantic 422 validation error: [{loc, msg, type}, ...].
              // Strip Pydantic's "Value error, " prefix.
              detail = d
                .map((e: { loc?: unknown[]; msg?: unknown }) => {
                  const rawMsg = typeof e.msg === "string" ? e.msg : JSON.stringify(e.msg);
                  const cleanMsg = rawMsg.replace(/^Value error,\s*/, "");
                  const field =
                    Array.isArray(e.loc) && e.loc.length > 1
                      ? String(e.loc[e.loc.length - 1])
                      : null;
                  return field ? `${field}: ${cleanMsg}` : cleanMsg;
                })
                .join("; ");
            } else if (typeof d === "string") {
              detail = d;
            } else if (d !== undefined && d !== null) {
              detail = JSON.stringify(d);
            }
          }
        } catch {
          /* non-JSON error body */
        }

        lastError = new ErrorClass(detail, res.status, code, res) as InstanceType<
          typeof ErrorClass
        >;
        lastError.detail = structuredDetail;

        // Retry on 5xx (server errors), not 4xx (client errors); idempotent
        // methods only, see `retryable`.
        if (retryable && isRetryableStatus(res.status) && attempt < MAX_RETRIES) {
          await sleep(RETRY_DELAYS_MS[attempt], signal);
          continue;
        }

        throw lastError;
      }

      // Success — parse response
      if (handleNonJsonResponses) {
        if (res.status === 204) return undefined as T;
        const contentType = res.headers.get("content-type") || "";
        if (contentType.includes("application/json")) return (await res.json()) as T;
        return (await res.text()) as unknown as T;
      }

      return res.json();
    }

    throw lastError ?? new ErrorClass("请求失败", 0);
  }

  return { request };
}
