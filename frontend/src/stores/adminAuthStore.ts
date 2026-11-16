/**
 * Admin auth store - separate from the user-side `authStore`.
 *
 * The admin console is an independent surface with its own login page and its
 * own session: tokens live under dedicated localStorage keys
 * (`seeword_admin_token`), so logging out of the user app does not log out
 * the admin (and vice versa). The backend still uses a single JWT/role system
 * - admin is simply a user with `role === "admin"`.
 *
 * 共享工具（migrateTokenKeys/deriveAuthenticated/BaseAuthUser）见 @/lib/authHelpers。
 */

import { create } from "zustand";
import { decodeJwt, isTokenExpired } from "@/lib/jwt";
import {
  ADMIN_SESSION_KEYS,
  migrateTokenKeys,
  deriveAuthenticated,
  setSession,
  clearSession,
  remirrorSessionCookie,
  type BaseAuthUser,
} from "@/lib/authHelpers";
import { requestTokenRefresh, type RefreshOutcome } from "@/lib/sessionRefresh";
import { requestSessionLogout, logoutLocation } from "@/lib/sessionLogout";

/** JWT payload（role 不在 JWT 里，admin role 经 /users/me DB 查询 + get_admin_user 叠加）。 */
export type AdminAuthUser = BaseAuthUser;

interface AdminAuthState {
  token: string | null;
  refreshToken: string | null;
  user: AdminAuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AdminAuthActions {
  login: (token: string, refreshToken?: string | null) => void;
  logout: () => void;
  /** Read tokens from localStorage into state (no network, no redirect). */
  bootstrap: () => void;
  /** 只有 "expired" 会登出；"unavailable" 保留会话（A03/FE-07）。 */
  refreshAccessToken: () => Promise<RefreshOutcome>;
}

/** One-time migration: move admin tokens from old "speaking_*" keys to new "seeword_*" keys. */
const MIGRATION_MAPPINGS: [string, string][] = [
  ["speaking_admin_token", ADMIN_SESSION_KEYS.token],
  ["speaking_admin_refresh_token", ADMIN_SESSION_KEYS.refreshToken],
];

let refreshPromise: Promise<RefreshOutcome> | null = null;
/** Invalidates async work when login/logout changes the local session. */
let sessionEpoch = 0;

export const useAdminAuthStore = create<AdminAuthState & AdminAuthActions>((set, get) => ({
  token: null,
  refreshToken: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  login(token: string, refreshToken?: string | null) {
    sessionEpoch += 1;
    // localStorage + 镜像 cookie 一起写（唯一入口，见 lib/authHelpers.setSession）。
    setSession(ADMIN_SESSION_KEYS, token, refreshToken);
    const user = decodeJwt(token) as AdminAuthUser | null;
    set({
      token,
      refreshToken: refreshToken ?? null,
      user,
      isAuthenticated: deriveAuthenticated(token, user),
      isLoading: false,
    });
  },

  logout() {
    const epoch = ++sessionEpoch;
    const currentToken = get().token;
    const currentRefreshToken = get().refreshToken;
    const revocation = requestSessionLogout(currentToken, currentRefreshToken);
    if (typeof window !== "undefined") {
      // 两个存放位置一起清（唯一入口，见 lib/authHelpers.clearSession）。
      clearSession(ADMIN_SESSION_KEYS);
    }
    set({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
    });
    void revocation.then((outcome) => {
      if (typeof window !== "undefined" && epoch === sessionEpoch) {
        window.location.href = logoutLocation("/admin/login", outcome);
      }
    });
  },

  async bootstrap() {
    migrateTokenKeys(MIGRATION_MAPPINGS);

    if (typeof window === "undefined") {
      set({ isLoading: false });
      return;
    }
    const token = localStorage.getItem(ADMIN_SESSION_KEYS.token);
    const refreshToken = localStorage.getItem(ADMIN_SESSION_KEYS.refreshToken);
    if (!token) {
      // 镜像 cookie 可能是上一轮留下的，清掉避免 middleware 误放行 /admin。
      clearSession(ADMIN_SESSION_KEYS);
      set({
        token: null,
        refreshToken: null,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
      return;
    }
    const user = decodeJwt(token) as AdminAuthUser | null;
    set({
      token,
      refreshToken,
      user,
      isAuthenticated: deriveAuthenticated(token, user),
      isLoading: false,
    });
    // 回访管理员的镜像 cookie 可能已丢失 — 用有效 token 重新镜像。只补 cookie。
    remirrorSessionCookie(ADMIN_SESSION_KEYS, token);
    // If expired, refresh BEFORE clearing the loading state: the shell guard
    // redirects to /admin/login as soon as isLoading=false && !isAuthenticated,
    // so clearing isLoading synchronously would bounce an expired-but-
    // refreshable session to the login form before the refresh resolves
    // (mirrors the user-side authStore.initialize() pattern).
    if (isTokenExpired(token)) {
      if (refreshToken) {
        set({ isLoading: true, isAuthenticated: false });
        await get().refreshAccessToken();
        set({ isLoading: false });
      } else {
        // No refresh token available - clear stale state so the shell guard
        // redirects to /admin/login instead of showing a blank/loading page.
        get().logout();
      }
    }
  },

  async refreshAccessToken(): Promise<RefreshOutcome> {
    if (refreshPromise) return refreshPromise;
    const epoch = sessionEpoch;
    const attempted = get().refreshToken;
    refreshPromise = (async (): Promise<RefreshOutcome> => {
      if (!attempted) {
        if (epoch === sessionEpoch) get().logout();
        return "expired";
      }

      const result = await requestTokenRefresh(attempted);
      // 刷新期间用户可能已经登出：结果一律作废，不能把会话「复活」。
      if (epoch !== sessionEpoch) return result.outcome;

      if (result.outcome === "refreshed") {
        get().login(result.pair.token, result.pair.refreshToken);
        return "refreshed";
      }
      if (result.outcome === "unavailable") {
        // 临时故障：保留会话，交给下一次请求重试。
        return "unavailable";
      }
      get().logout();
      return "expired";
    })().finally(() => {
      refreshPromise = null;
    });
    return refreshPromise;
  },
}));
