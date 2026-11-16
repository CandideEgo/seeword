"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { AlertTriangle, Loader2, RefreshCw, ShieldAlert } from "lucide-react";
import { useAdminAuthStore } from "@/stores/adminAuthStore";
import { adminApi } from "@/lib/adminApi";
import { ApiClientError } from "@/lib/createApiClient";
import { apiErrorMessage } from "@/lib/errors";
import type { User } from "@/types";
import { Button } from "@/components/ui/Button";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { AdminTopbar } from "@/components/admin/AdminTopbar";

type ShellStatus = "checking" | "ok" | "denied" | "error";

/**
 * Guarded admin shell. Boots the admin auth store from localStorage, verifies
 * the session is an admin via `/users/me`, then renders the sidebar + topbar
 * + content.
 *
 * A-05: 只有 401/403（会话/权限问题）才回登录页；5xx 与网络错误说明「后端
 * 暂时不可用」，而本地会话可能仍然有效——此时保留会话，渲染壳层级错误 +
 * 重试，绝不把管理员误登出（否则 5xx 持续时会形成「登录后立刻被踢」循环）。
 *
 * A-27: 第一个可聚焦元素是「跳到内容」skip link，main 有 id + tabIndex=-1。
 */
export default function AdminShellLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const bootstrap = useAdminAuthStore((s) => s.bootstrap);
  const isAuthenticated = useAdminAuthStore((s) => s.isAuthenticated);
  const isLoading = useAdminAuthStore((s) => s.isLoading);

  const [status, setStatus] = useState<ShellStatus>("checking");
  const [errorMessage, setErrorMessage] = useState("");
  /** 只接受最新一次校验的结果（重试/卸载后到达的旧响应一律丢弃）。 */
  const checkRunRef = useRef(0);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const checkSession = useCallback(async () => {
    const runId = ++checkRunRef.current;
    try {
      const u = await adminApi<User>("/api/v1/users/me");
      if (runId !== checkRunRef.current) return;
      if (u.role !== "admin") {
        toast.error("该账号无管理员权限");
        setStatus("denied");
        setTimeout(() => router.replace("/admin/login"), 800);
        return;
      }
      setErrorMessage("");
      setStatus("ok");
    } catch (err) {
      if (runId !== checkRunRef.current) return;
      const httpStatus = err instanceof ApiClientError ? err.status : 0;
      if (httpStatus === 401 || httpStatus === 403) {
        toast.error("登录已过期，请重新登录");
        router.replace("/admin/login");
        return;
      }
      // 5xx / 网络错误：保留会话，壳层给出错误 + 重试
      setErrorMessage(
        apiErrorMessage(
          err,
          httpStatus >= 500 ? "服务暂时不可用，请稍后重试" : "无法连接服务器，请检查网络后重试"
        )
      );
      setStatus("error");
    }
  }, [router]);

  const retry = useCallback(() => {
    setErrorMessage("");
    setStatus("checking");
    void checkSession();
  }, [checkSession]);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      router.replace("/admin/login");
      return;
    }
    void checkSession();
  }, [isAuthenticated, isLoading, router, checkSession]);

  if (status === "denied") {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-surface-soft">
        <div className="text-center">
          <ShieldAlert size={40} className="mx-auto text-muted-soft" />
          <p className="mt-3 text-copy text-muted">无管理员权限</p>
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-surface-soft px-4">
        <div
          role="alert"
          className="w-full max-w-md rounded-lg border border-hairline bg-canvas p-6 text-center shadow-sm"
        >
          <AlertTriangle size={32} className="mx-auto text-warning" aria-hidden />
          <h1 className="mt-3 text-copy-lg font-semibold text-ink">无法验证管理员会话</h1>
          <p className="mt-1.5 text-copy leading-relaxed text-muted">{errorMessage}</p>
          <p className="mt-1 text-meta text-muted">
            登录状态已保留。若持续失败，请确认后端服务是否正常，再重试。
          </p>
          <Button onClick={retry} variant="secondary" size="sm" icon={RefreshCw} className="mt-4">
            重试
          </Button>
        </div>
      </div>
    );
  }

  if (status !== "ok") {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-surface-soft">
        <div className="text-center">
          <Loader2 size={28} className="mx-auto animate-spin text-brand-500" />
        </div>
      </div>
    );
  }

  return (
    <div className="admin-workspace flex h-dvh overflow-hidden bg-surface-soft">
      <a
        href="#admin-main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-canvas focus:px-4 focus:py-2 focus:text-copy focus:font-medium focus:text-ink focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
      >
        跳到内容
      </a>
      <AdminSidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <AdminTopbar />
        <main id="admin-main" tabIndex={-1} className="flex-1 overflow-y-auto focus:outline-none">
          <div className="mx-auto max-w-admin px-4 py-6 md:px-6 md:py-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
