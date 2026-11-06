import { createApiClient, ApiClientError, type AuthAdapter } from "@/lib/createApiClient";
import { publicErrorMessage } from "@/lib/publicError";

// Empty string = relative paths (e.g. "/api/v1/..."). In production, nginx
// proxies /api/ and /media/ to the backend. In development, next.config.js
// rewrites handle the proxying. No build-time API URL configuration needed.
const API_URL = "";

// ---------------------------------------------------------------------------
// ApiError — structured error for API responses (backward-compatible)
// ---------------------------------------------------------------------------

export class ApiError extends ApiClientError {
  constructor(
    message: string,
    status: number = 0,
    code: string | null = null,
    response: Response | null = null
  ) {
    super(publicErrorMessage(message, status), status, code, response);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

export function getApiUrl() {
  return API_URL;
}

// Hostname suffixes whose thumbnail URLs we route through the backend image
// proxy to bypass CDN hotlink protection (Referer) and mixed-content (http://
// thumbnails on an https site). Keep in sync with the backend allowlist in
// backend/app/api/v1/media.py (proxy_image). NOTE: aliyuncs.com is excluded
// on purpose — OSS bucket domains are attacker-controllable (SSRF defense).
const PROXY_HOST_SUFFIXES = [
  "ytimg.com",
  "hdslb.com",
  "biliimg.com",
  "douyinpic.com",
  "douyincdn.com",
  "douyinstatic.com",
];

function shouldProxyHost(host: string): boolean {
  const h = host.toLowerCase();
  return PROXY_HOST_SUFFIXES.some((s) => h === s || h.endsWith("." + s));
}

export function mediaUrl(
  path: string,
  opts?: { withToken?: boolean; token?: string | null }
): string {
  if (!path) return "";
  // Shadowing recordings are access-controlled per user; non-public video
  // media (drafts) require an owner/admin JWT. The backend reads ?token=
  // because <audio>/<video> tags cannot attach Authorization headers.
  // 因此该 URL 里是长期有效的 bearer 凭证：不得写进日志/Referer/分享链接
  // （nginx log_format 用 $uri 不含 query，uvicorn 访问日志默认含 query）。
  if (
    path.startsWith("/media/shadowing/") ||
    opts?.withToken === true ||
    opts?.token !== undefined
  ) {
    try {
      // 显式 token 优先（管理端预览传 admin token，与用户端会话分离）。
      const token = opts?.token ?? getToken();
      if (token) {
        const sep = path.includes("?") ? "&" : "?";
        return `${API_URL}${path}${sep}token=${encodeURIComponent(token)}`;
      }
    } catch {
      // authStore unavailable (SSR edge) — fall through to plain path
    }
  }
  if (path.startsWith("http")) {
    // Route known thumbnail CDN hosts through the backend proxy to dodge
    // hotlink protection and http/https mixed-content issues.
    // NOTE: the media router is mounted at /media (no /api/v1 prefix — see
    // backend/app/main.py: app.include_router(media.router)), so the proxy
    // lives at /media/proxy, NOT /api/v1/media/proxy.
    try {
      const host = new URL(path).hostname;
      if (shouldProxyHost(host)) {
        return `${API_URL}/media/proxy?url=${encodeURIComponent(path)}`;
      }
    } catch {
      // Malformed URL — fall through and return as-is.
    }
    // Best-effort: upgrade plain http to https to avoid mixed-content blocks.
    return path.replace(/^http:\/\//, "https://");
  }
  return `${API_URL}${path}`;
}

/**
 * Get the current auth token from the Zustand auth store.
 *
 * This is the single source of truth — no direct localStorage access.
 * The auth store handles localStorage sync internally.
 */
export function getToken(): string | null {
  // Lazy import to avoid circular dependency at module load time
  // (authStore imports from jwt.ts, which is fine, but api.ts is imported
  // widely and we don't want to force authStore to load before it's needed)
  const { useAuthStore } = require("@/stores/authStore");
  return useAuthStore.getState().token;
}

// ---------------------------------------------------------------------------
// Auth adapter for the user auth store
// ---------------------------------------------------------------------------

const userAuthAdapter: AuthAdapter = {
  getToken,
  async refreshToken() {
    const { useAuthStore } = require("@/stores/authStore");
    return useAuthStore.getState().refreshAccessToken();
  },
  onSessionExpired() {
    const { useAuthStore } = require("@/stores/authStore");
    useAuthStore.getState().logout();
  },
};

// ---------------------------------------------------------------------------
// Core API client (delegates to createApiClient)
// ---------------------------------------------------------------------------

const client = createApiClient({
  baseUrl: API_URL,
  auth: userAuthAdapter,
  ErrorClass: ApiError,
});

export interface ApiOptions extends Omit<RequestInit, "signal"> {
  /** AbortSignal to cancel the request */
  signal?: AbortSignal;
  /** GET-only: serve/cache this request locally for N milliseconds */
  cacheTtlMs?: number;
}

export { clearApiCache } from "@/lib/createApiClient";

export async function api<T = unknown>(path: string, options: ApiOptions = {}): Promise<T> {
  return client.request<T>(path, options);
}
