import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ADMIN_SESSION_KEYS, USER_SESSION_KEYS } from "@/lib/authHelpers";
import { useAdminAuthStore } from "@/stores/adminAuthStore";
import { useAuthStore } from "@/stores/authStore";

vi.mock("@/stores/watchStore", () => ({ useWatchStore: { getState: () => ({ reset: vi.fn() }) } }));
vi.mock("@/stores/vocabularyStore", () => ({
  useVocabularyStore: { getState: () => ({ reset: vi.fn() }) },
}));
vi.mock("@/stores/planStore", () => ({ usePlanStore: { getState: () => ({ reset: vi.fn() }) } }));
vi.mock("@/stores/profileStore", () => ({
  useProfileStore: { getState: () => ({ reset: vi.fn() }) },
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((fulfill) => {
    resolve = fulfill;
  });
  return { promise, resolve };
}

function token(subject: string) {
  const payload = Buffer.from(JSON.stringify({ sub: subject, exp: 4_000_000_000 })).toString(
    "base64url"
  );
  return `header.${payload}.signature`;
}

beforeEach(() => {
  const storage = new Map<string, string>();
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => storage.get(key) ?? null,
    setItem: (key: string, value: string) => storage.set(key, value),
    removeItem: (key: string) => storage.delete(key),
  });
  vi.stubGlobal("document", { cookie: "" });
  vi.stubGlobal("window", { location: { href: "", pathname: "/" } });
  useAuthStore.setState({ token: null, refreshToken: null, user: null, isAuthenticated: false });
  useAdminAuthStore.setState({
    token: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false,
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const surfaces = [
  {
    name: "用户",
    store: useAuthStore,
    keys: USER_SESSION_KEYS,
    otherKeys: ADMIN_SESSION_KEYS,
    path: "/login",
  },
  {
    name: "管理员",
    store: useAdminAuthStore,
    keys: ADMIN_SESSION_KEYS,
    otherKeys: USER_SESSION_KEYS,
    path: "/admin/login",
  },
];

describe.each(surfaces)("$name退出契约", ({ store, keys, otherKeys, path }) => {
  it("立即清除本机会话，服务端未确认时保留准确提示，不触碰另一身份", async () => {
    const pending = deferred<Response>();
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(pending.promise));
    useAuthStore.getState().login(token("user"), "user-refresh");
    useAdminAuthStore.getState().login(token("admin"), "admin-refresh");

    store.getState().logout();
    expect(store.getState().token).toBeNull();
    expect(store.getState().isAuthenticated).toBe(false);
    expect(localStorage.getItem(keys.token)).toBeNull();
    expect(localStorage.getItem(keys.refreshToken)).toBeNull();
    expect(document.cookie).toContain(`${keys.token}=;`);
    expect(localStorage.getItem(otherKeys.token)).not.toBeNull();
    expect(localStorage.getItem(otherKeys.refreshToken)).not.toBeNull();
    expect(window.location.href).toBe("");

    pending.resolve(new Response("{}", { status: 503 }));
    await vi.waitFor(() => expect(window.location.href).toBe(`${path}?revocation=unconfirmed`));
  });

  it("刷新晚到不能恢复已退出的本机会话", async () => {
    const pending = deferred<Response>();
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) =>
        url.endsWith("/refresh")
          ? pending.promise
          : Promise.resolve(new Response("{}", { status: 200 }))
      )
    );
    store.getState().login(token("old"), "old-refresh");
    const refreshing = store.getState().refreshAccessToken();
    store.getState().logout();
    await vi.waitFor(() => expect(window.location.href).toBe(path));
    pending.resolve(
      new Response(JSON.stringify({ token: token("old"), refresh_token: "late-refresh" }))
    );
    await refreshing;
    expect(store.getState().token).toBeNull();
    expect(localStorage.getItem(keys.token)).toBeNull();
    expect(localStorage.getItem(keys.refreshToken)).toBeNull();
  });

  it("退出请求晚到不能把新登录会话导航回登录页", async () => {
    const pending = deferred<Response>();
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(pending.promise));
    store.getState().login(token("old"), "old-refresh");
    store.getState().logout();
    store.getState().login(token("new"), "new-refresh");
    pending.resolve(new Response("{}", { status: 503 }));
    await new Promise((resolve) => setTimeout(resolve, 30));
    expect(window.location.href).toBe("");
    expect(localStorage.getItem(keys.token)).toBe(token("new"));
  });
});
