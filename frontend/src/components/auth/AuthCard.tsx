import Image from "next/image";
import Link from "next/link";
import { siteConfig } from "@/lib/siteConfig";
import { AuthThemeToggle } from "@/components/auth/AuthThemeToggle";
import { cn } from "@/lib/utils";
import { ComplianceInfo } from "@/components/common/ComplianceInfo";
import { AstryxProvider } from "@/components/common/AstryxProvider";
import { LogoutNotice } from "@/components/auth/LogoutNotice";

/**
 * 账号流程公共壳：表单与引导页共用 user-auth-shell；宽版仅用于引导。
 * 宽度、标题和响应式间距由 user-ui.css 维护，品牌与主题切换同排。
 */
export function AuthCard({
  title,
  children,
  wide = false,
  headerActions,
}: {
  title: string;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  /** `auth-shell-wide`（44rem）：引导页使用。 */
  wide?: boolean;
  /** 页头右侧除主题切换外的附加动作（例如引导页的「跳过设置」）。 */
  headerActions?: React.ReactNode;
}) {
  const content = (
    <>
      <div className="mb-8 flex items-center justify-between gap-4">
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
        <div className="flex flex-none items-center gap-3">
          {headerActions}
          <AuthThemeToggle />
        </div>
      </div>

      <header>
        <h1 className={cn("font-display text-ink", wide && "max-w-[40rem]")}>{title}</h1>
      </header>

      <LogoutNotice />
      {children}
      <ComplianceInfo className="mt-6 text-center" />
    </>
  );

  return (
    <main className="user-ui user-auth min-h-dvh bg-canvas px-5 py-8 md:px-6 md:py-14">
      <section className={cn("user-auth-shell mx-auto w-full", wide && "is-wide")}>
        <AstryxProvider>{content}</AstryxProvider>
      </section>
    </main>
  );
}
