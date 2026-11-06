"use client";

import Image from "next/image";
import Link from "next/link";
import { AuthThemeToggle } from "@/components/auth/AuthThemeToggle";
import { LinkButton } from "@/components/ui/LinkButton";
import { siteConfig } from "@/lib/siteConfig";

/**
 * 未登录壳层的页头。
 *
 * 白名单页（/contact）渲染时不带应用 shell——侧栏、顶栏、
 * 底部导航都不出现。少了这一行，从登录页底部或外部链接进来的访客在页面里
 * 找不到回首页的入口，只能一路滚到底部页脚。这里只放品牌与「登录」，
 * 不假装成已登录的导航。
 */
export function PublicTopBar() {
  return (
    <header className="flex items-center justify-between gap-4 py-5">
      <Link
        href="/"
        aria-label={`${siteConfig.brandName} 首页`}
        className="flex min-w-0 items-center gap-2 rounded-sm"
      >
        <Image src="/logo.png" alt="" width={26} height={26} priority />
        <span className="font-display text-[17px] font-extrabold tracking-[-0.03em] text-ink">
          {siteConfig.brandName}
        </span>
      </Link>
      <div className="flex flex-none items-center gap-2">
        <AuthThemeToggle />
        <LinkButton href="/login" variant="outline" size="sm">
          登录
        </LinkButton>
      </div>
    </header>
  );
}
