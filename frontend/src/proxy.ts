/**
 * D0 登录墙（产品设计规划-2026-08 §2.1/§2.5）。
 *
 * Next.js 16 的 proxy 文件约定（原 middleware，已更名）：运行在网络边界，
 * 只能读 cookie，不查 DB、不解码 JWT —— 只做会话存在性检查；token 过期等
 * 细节由客户端 authStore.initialize() 兜底（过期且无法 refresh 时同样跳登录）。
 *
 * 未登录访问受保护路由 → 302 `/login?next={path}`，登录页成功后跳回。
 * token 事实来源仍是 localStorage（zustand authStore），登录/刷新时镜像到
 * 同名 cookie（见 lib/authHelpers.setSession）供本文件读取。
 *
 * 管理端独立会话：/admin/* 检查 `seeword_admin_token`，与用户端互不影响。
 */

import { NextRequest, NextResponse } from "next/server";

/** 公开路由（访问矩阵 §2.1）：未登录可访问。 */
const PUBLIC_PATHS = [
  "/login",
  "/register",
  "/forgot-password",
  "/terms",
  "/privacy",
  // 帮助与反馈页：登录页底部「联系我们」指向这里，未登录也必须能看到开发者联系方式。
  "/contact",
];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
}

// 公开页面也要读取品牌与默认头像；仅放行 public/ 中这些确定的静态资源。
const PUBLIC_ASSETS = new Set([
  "/robots.txt",
  "/logo.png",
  "/logo-large.png",
  "/og-image.png",
  "/project-icon.svg",
  "/default-avatar-male.webp",
  "/default-avatar-female.webp",
]);

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (PUBLIC_ASSETS.has(pathname)) return NextResponse.next();

  // 管理端：独立会话检查（/admin/login 公开）。
  if (pathname.startsWith("/admin")) {
    if (pathname === "/admin/login" || pathname.startsWith("/admin/login/")) {
      return NextResponse.next();
    }
    const adminToken = request.cookies.get("seeword_admin_token")?.value;
    if (!adminToken) {
      const url = new URL("/admin/login", request.url);
      url.searchParams.set("next", pathname + request.nextUrl.search);
      return NextResponse.redirect(url);
    }
    return NextResponse.next();
  }

  if (isPublicPath(pathname)) {
    return NextResponse.next();
  }

  // 用户端登录墙：无镜像 cookie → 跳登录并携带回跳地址。
  const token = request.cookies.get("seeword_token")?.value;
  if (!token) {
    const url = new URL("/login", request.url);
    url.searchParams.set("next", pathname + request.nextUrl.search);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  // 覆盖全部页面路由；排除静态资源与后端代理路径（/api、/media 由后端鉴权）。
  matcher: [
    "/((?!_next/static|_next/image|api/|media/|favicon.ico|icon.png|icon-192.png|icon-512.png|apple-icon.png).*)",
  ],
};
