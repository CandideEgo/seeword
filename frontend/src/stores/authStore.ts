/**
 * Zustand auth store - single source of truth for authentication state.
 *
 * Replaces scattered localStorage.getItem('token') / getToken() / manual JWT
 * decode patterns across the frontend. All auth state flows through here.
 *
 * Usage:
 *   import { useAuthStore } from '@/stores/authStore';
 *   const { token, user, isAuthenticated, login, logout } = useAuthStore();
 *   // Or outside React:
 *   useAuthStore.getState().token
 */

import { create } from "zustand";
import { decodeJwt, isTokenExpired } from "@/lib/jwt";
import {
  USER_SESSION_KEYS,
  migrateTokenKeys,
  deriveAuthenticated,
  setSession,
  clearSession,
  remirrorSessionCookie,
  type BaseAuthUser,
} from "@/lib/authHelpers";
import { useProfileStore } from "@/stores/profileStore";
import { requestTokenRefresh, type RefreshOutcome } from "@/lib/sessionRefresh";
import { requestSessionLogout, logoutLocation } from "@/lib/sessionLogout";

/** JWT payload shape we care about (role 不在 JWT 里，见 authHelpers.BaseAuthUser) */
export type AuthUser = BaseAuthUser;

interface AuthState {
  /** Raw JWT access token string */
  token: string | null;
  /** Refresh token for obtaining new access tokens */
  refreshToken: string | null;
  /** Decoded JWT payload (null if no valid token) */
  user: AuthUser | null;
  /** Convenience flag - true when token exists and is not expired */
  isAuthenticated: boolean;
  /** True while initialize() is running on app load */
  isLoading: boolean;
}

interface AuthActions {
  /**
   * Store a new token (and optional refresh token), decode it, and update auth state.
   * Call this after successful login/register or token refresh.
   */
  login: (token: string, refreshToken?: string | null) => void;

  /**
   * Clear all auth state, remove tokens from localStorage,
   * and redirect to /login.
   */
  logout: () => void;

  /**
   * Check localStorage for existing tokens on app load.
   * Validates expiry - if expired, clears state and redirects.
   * Call once at app startup (e.g. in AuthInitializer component).
   */
  initialize: () => void;

  /**
   * Attempt to refresh the access token using the stored refresh token.
   * Uses a mutex to prevent concurrent refresh calls - if a refresh is
   * already in progress, returns the same promise.
   *
   * 只有 ``"expired"`` 会清会话；``"unavailable"``（断网/超时/5xx）保留凭据，
   * 让下一次请求再试，不能因为一次抖动把用户踢下线。
   */
  refreshAccessToken: () => Promise<RefreshOutcome>;
}

/** One-time migration: move tokens from old "speaking_*" keys to new "seeword_*" keys. */
const MIGRATION_MAPPINGS: [string, string][] = [
  ["speaking_token", USER_SESSION_KEYS.token],
  ["speaking_refresh_token", USER_SESSION_KEYS.refreshToken],
];

type AuthStore = AuthState & AuthActions;

/** Module-level mutex for preventing concurrent refresh calls */
let refreshPromise: Promise<RefreshOutcome> | null = null;
/** Invalidates async work when login/logout changes the local session. */
let sessionEpoch = 0;

/**
 * 另一个标签页可能已经把 refresh 轮换掉了：它会写新的 token 对到 localStorage。
 * 服务端现在保证同一个旧 refresh 只能换出一条后继，所以抢输的一方会拿到 401；
 * 这时先看看存储里是不是别人写进来的新会话，有就接着用，而不是把用户登出。
 */
function adoptStoredSession(attempted: string | null): boolean {
  if (typeof window === "undefined") return false;
  const storedRefresh = localStorage.getItem(USER_SESSION_KEYS.refreshToken);
  const storedToken = localStorage.getItem(USER_SESSION_KEYS.token);
  if (!storedRefresh || !storedToken) return false;
  // 还是自己这一份 —— 没有别人刷新过，这次确实是失效。
  if (storedRefresh === attempted) return false;
  if (isTokenExpired(storedToken)) return false;
  useAuthStore.getState().login(storedToken, storedRefresh);
  return true;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  token: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  isLoading: true, // starts true until initialize() runs

  login(token: string, refreshToken?: string | null) {
    sessionEpoch += 1;
    // localStorage + 镜像 cookie 一起写（唯一入口，见 lib/authHelpers.setSession）。
    setSession(USER_SESSION_KEYS, token, refreshToken);
    const user = decodeJwt(token) as AuthUser | null;
    // A different subject is a different user: drop the cached profile so the next reader
    // fetches theirs rather than showing the previous one's face. `login()` is also the
    // token-refresh path, where the subject is unchanged and the cache must survive.
    // Imported statically, unlike the resets in logout(): this one has to land before the
    // re-render that triggers the next fetch.
    if (user?.sub !== get().user?.sub) {
      useProfileStore.getState().reset();
    }
    set({
      token,
      refreshToken: refreshToken ?? null,
      user,
      isAuthenticated: deriveAuthenticated(token, user),
    });
  },

  logout() {
    const epoch = ++sessionEpoch;
    // Clear locally immediately, but distinguish remote acknowledgement from outage.
    const currentToken = get().token;
    const currentRefreshToken = get().refreshToken;
    const blacklistPromise = requestSessionLogout(currentToken, currentRefreshToken);

    if (typeof window !== "undefined") {
      // 两个存放位置一起清（唯一入口，见 lib/authHelpers.clearSession）。
      clearSession(USER_SESSION_KEYS);
    }
    set({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
    });
    // Reset sibling stores to avoid stale user data after logout.
    // Dynamic imports prevent circular dependency issues.
    const resetPromise = Promise.all([
      import("@/stores/watchStore").then((m) => m.useWatchStore.getState().reset()),
      import("@/stores/vocabularyStore").then((m) => m.useVocabularyStore.getState().reset()),
      import("@/stores/planStore").then((m) => m.usePlanStore.getState().reset()),
      import("@/stores/profileStore").then((m) => m.useProfileStore.getState().reset()),
    ]);

    // Wait for blacklist + store resets, then navigate.
    // Using window.location is correct here because the Zustand store
    // operates outside the React component tree where useRouter is unavailable.
    Promise.all([blacklistPromise, resetPromise]).then(([outcome]) => {
      if (typeof window !== "undefined" && epoch === sessionEpoch) {
        window.location.href = logoutLocation("/login", outcome);
      }
    });
  },

  initialize() {
    migrateTokenKeys(MIGRATION_MAPPINGS);

    if (typeof window === "undefined") {
      set({ isLoading: false });
      return;
    }

    const token = localStorage.getItem(USER_SESSION_KEYS.token);
    const refreshToken = localStorage.getItem(USER_SESSION_KEYS.refreshToken);
    if (!token) {
      // 镜像 cookie 可能是上一轮留下的，清掉避免 middleware 误放行；顺带把
      // 「有 refresh token 没有 access token」的孤儿也扫掉。
      clearSession(USER_SESSION_KEYS);
      set({
        token: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
      return;
    }

    // Check expiry
    if (isTokenExpired(token)) {
      // Access token expired - try refreshing before giving up
      if (refreshToken) {
        // 把（已过期的）token 与 refresh token 一起放进 store 再刷新：刷新遇到
        // 临时故障时不清会话，后续请求带着这个 token 会得到 401 并再次触发刷新，
        // 网络恢复后自动接上，不需要用户重新登录。
        set({
          token,
          refreshToken,
          user: decodeJwt(token) as AuthUser | null,
          isAuthenticated: false,
        });
        get()
          .refreshAccessToken()
          .then(() => {
            // "expired" 时 logout() 已清场并跳转；"unavailable" 保留会话等重试。
            set({ isLoading: false });
          });
        return;
      }
      // No refresh token - clear and redirect (unless on the independent admin
      // console, which manages its own auth via a separate token store).
      clearSession(USER_SESSION_KEYS);
      set({
        token: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
      if (!window.location.pathname.startsWith("/admin")) {
        window.location.href = "/login";
      }
      return;
    }

    const user = decodeJwt(token) as AuthUser | null;
    if (!user) {
      // Token structurally invalid - clear and redirect
      clearSession(USER_SESSION_KEYS);
      set({
        token: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
      if (!window.location.pathname.startsWith("/admin")) {
        window.location.href = "/login";
      }
      return;
    }

    set({
      token,
      refreshToken,
      user,
      isAuthenticated: deriveAuthenticated(token, user),
      isLoading: false,
    });
    // 回访用户 cookie 可能已丢失/过期 — 用有效 token 重新镜像，
    // 否则 middleware 会把已登录用户拦到 /login。只补 cookie，不动 localStorage。
    remirrorSessionCookie(USER_SESSION_KEYS, token);
  },

  async refreshAccessToken(): Promise<RefreshOutcome> {
    // If already refreshing, return the existing promise
    if (refreshPromise) return refreshPromise;

    const epoch = sessionEpoch;
    const attempted = get().refreshToken;
    refreshPromise = (async (): Promise<RefreshOutcome> => {
      if (!attempted) {
        get().logout();
        return "expired";
      }

      const result = await requestTokenRefresh(attempted);
      // Login/logout may have replaced this session while the request was in flight.
      if (epoch !== sessionEpoch) return result.outcome;

      if (result.outcome === "refreshed") {
        get().login(result.pair.token, result.pair.refreshToken);
        return "refreshed";
      }
      if (result.outcome === "unavailable") {
        // 断网 / 超时 / 5xx：会话可能仍然有效。保留 token，不 redirect。
        return "unavailable";
      }
      // 服务端明确拒绝：先看是不是另一个标签页已经轮换成功。
      if (adoptStoredSession(attempted)) return "refreshed";

      get().logout();
      return "expired";
    })().finally(() => {
      refreshPromise = null;
    });

    return refreshPromise;
  },
}));
