import { afterEach, describe, expect, it, vi } from "vitest";
import { logoutLocation, requestSessionLogout } from "./sessionLogout";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("本机退出与服务端撤销分开", () => {
  it("只在服务端确认后标记已撤销", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetcher);
    expect(await requestSessionLogout("synthetic-access", "synthetic-refresh")).toBe("revoked");
    expect(fetcher).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ refresh_token: "synthetic-refresh" }),
        keepalive: true,
      })
    );
    expect(logoutLocation("/login", "revoked")).toBe("/login");
  });
  it.each([401, 403, 503])("HTTP %s 不能伪装成撤销成功", async (status) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status })));
    const outcome = await requestSessionLogout("synthetic", null);
    expect(outcome).toBe("unconfirmed");
    expect(logoutLocation("/admin/login", outcome)).toBe("/admin/login?revocation=unconfirmed");
  });
  it("网络错误保留未确认说明，不阻止本机退出", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    expect(await requestSessionLogout("synthetic", null)).toBe("unconfirmed");
  });
  it("没有会话不发送请求", async () => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    expect(await requestSessionLogout(null, null)).toBe("local");
    expect(fetcher).not.toHaveBeenCalled();
    expect(logoutLocation("/login", "local")).toBe("/login");
  });
  it("只有 refresh token 时不能谎称服务端已撤销", async () => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    const outcome = await requestSessionLogout(null, "synthetic-refresh");
    expect(outcome).toBe("unconfirmed");
    expect(fetcher).not.toHaveBeenCalled();
    expect(logoutLocation("/login", outcome)).toBe("/login?revocation=unconfirmed");
  });
  it("撤销请求有期限，超时不报成功", async () => {
    vi.useFakeTimers();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, options: RequestInit) =>
          new Promise((_, reject) => {
            options.signal?.addEventListener("abort", () =>
              reject(new DOMException("Aborted", "AbortError"))
            );
          })
      )
    );
    const pending = requestSessionLogout("synthetic", null);
    await vi.advanceTimersByTimeAsync(5000);
    expect(await pending).toBe("unconfirmed");
  });
});
