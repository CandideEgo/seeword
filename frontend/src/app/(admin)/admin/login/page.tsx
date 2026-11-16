"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { ArrowLeft, Eye, EyeOff, Lock, Phone, ShieldCheck } from "lucide-react";
import { useAdminAuthStore } from "@/stores/adminAuthStore";
import { adminApi } from "@/lib/adminApi";
import { apiErrorMessage } from "@/lib/errors";
import { Button } from "@/components/ui/Button";
import { LogoutNotice } from "@/components/auth/LogoutNotice";

interface LoginResponse {
  token: string;
  refresh_token?: string;
}

/** Only the independent admin surface may be a post-login destination. */
function resolveAdminNext(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return "/admin";
  if (/[\\\r\n]/.test(raw)) return "/admin";
  const path = raw.split(/[?#]/)[0] ?? "";
  if (path !== "/admin" && !path.startsWith("/admin/")) return "/admin";
  if (path === "/admin/login") return "/admin";
  return raw;
}

function currentAdminNext(): string {
  if (typeof window === "undefined") return "/admin";
  return resolveAdminNext(new URLSearchParams(window.location.search).get("next"));
}

const LOGIN_ERROR_ID = "admin-login-error";
const PHONE_INPUT_ID = "admin-login-phone";
const PASSWORD_INPUT_ID = "admin-login-password";
const FIELD =
  "w-full rounded-md border border-hairline bg-canvas py-3 pl-10 pr-4 text-copy text-ink placeholder:text-muted-soft focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-focus-ring transition-colors";

export default function AdminLoginPage() {
  const router = useRouter();
  const login = useAdminAuthStore((s) => s.login);
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (loading) return;
    setError("");
    if (!/^1[3-9]\d{9}$/.test(phone)) {
      setError("请输入正确的手机号");
      return;
    }
    setLoading(true);
    try {
      const data = await adminApi<LoginResponse>("/api/v1/auth/phone-login", {
        method: "POST",
        body: JSON.stringify({ phone, password }),
      });
      login(data.token, data.refresh_token ?? null);
      router.replace(currentAdminNext());
    } catch (err) {
      setError(apiErrorMessage(err, "登录失败，请重试"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-dvh bg-surface-soft px-5 py-10 sm:py-16">
      <section className="mx-auto w-full max-w-md rounded-lg border border-hairline bg-canvas p-6 sm:p-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2.5 rounded-sm text-copy-lg font-semibold text-ink"
          aria-label="SeeWord 首页"
        >
          <Image src="/logo.png" alt="" width={30} height={30} priority />
          SeeWord
        </Link>
        <header className="mt-9 mb-7">
          <h1 className="text-display-sm font-semibold tracking-tight text-ink">管理员登录</h1>
          <p className="mt-2 flex items-center gap-1.5 text-meta text-muted">
            <ShieldCheck size={15} aria-hidden /> 仅限授权管理员访问
          </p>
        </header>
        <LogoutNotice />
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor={PHONE_INPUT_ID} className="mb-2 block text-copy font-medium text-ink">
              手机号
            </label>
            <div className="relative">
              <Phone
                size={16}
                className="absolute top-1/2 left-3.5 -translate-y-1/2 text-muted-soft"
                aria-hidden
              />
              <input
                id={PHONE_INPUT_ID}
                type="tel"
                inputMode="numeric"
                maxLength={11}
                value={phone}
                onChange={(e) => setPhone(e.target.value.replace(/\D/g, ""))}
                required
                autoComplete="tel"
                placeholder="请输入手机号"
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? LOGIN_ERROR_ID : undefined}
                className={FIELD}
              />
            </div>
          </div>
          <div>
            <label
              htmlFor={PASSWORD_INPUT_ID}
              className="mb-2 block text-copy font-medium text-ink"
            >
              密码
            </label>
            <div className="relative">
              <Lock
                size={16}
                className="absolute top-1/2 left-3.5 -translate-y-1/2 text-muted-soft"
                aria-hidden
              />
              <input
                id={PASSWORD_INPUT_ID}
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="请输入密码"
                aria-invalid={error ? true : undefined}
                aria-describedby={error ? LOGIN_ERROR_ID : undefined}
                className={`${FIELD} pr-12`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? "隐藏密码" : "显示密码"}
                aria-pressed={showPassword}
                className="absolute top-1/2 right-0 grid size-11 -translate-y-1/2 place-items-center rounded-sm text-muted hover:text-ink"
              >
                {showPassword ? <EyeOff size={17} aria-hidden /> : <Eye size={17} aria-hidden />}
              </button>
            </div>
          </div>
          {error && (
            <p
              id={LOGIN_ERROR_ID}
              role="alert"
              className="rounded-md bg-red-soft p-3 text-copy text-error-text"
            >
              {error}
            </p>
          )}
          <Button type="submit" fullWidth loading={loading} className="min-h-11">
            登录
          </Button>
        </form>
        <Link
          href="/"
          className="mt-7 inline-flex min-h-11 items-center gap-1.5 text-meta text-muted transition-colors hover:text-ink"
        >
          <ArrowLeft size={15} aria-hidden /> 返回用户端
        </Link>
      </section>
    </main>
  );
}
