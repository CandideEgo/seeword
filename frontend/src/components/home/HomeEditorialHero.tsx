"use client";

/** 首页与后台预览共用已发布的完整视频推荐。 */

import type { ReactElement } from "react";
import { FeaturedVideoCard } from "@/components/home/FeaturedVideoCard";
import type { HomeEditorialPage, HomeLayoutIssue } from "@/types/homeContent";

export type HomeEditorialMode = "preview" | "live";

/** 首页唯一页头；不与视频标题抢层级。 */
export function HomeEditorialHeader(): ReactElement {
  const now = new Date();
  const label = `${now.getMonth() + 1} 月 ${now.getDate()} 日`;
  return (
    <header className="home-editorial-heading mb-6 flex items-baseline justify-between gap-4">
      <h1 className="text-display font-semibold tracking-tight text-ink">发现</h1>
      <time suppressHydrationWarning className="text-meta text-muted">
        {label}
      </time>
    </header>
  );
}

/** 已发布内容只取主推；次推/独立表达位不再占据首页上半区。 */
export function HomeEditorialHero({
  page,
}: {
  page: HomeEditorialPage;
  mode?: HomeEditorialMode;
}): ReactElement | null {
  if (!page.lead) return null;
  return (
    <section aria-label="精选推荐">
      <FeaturedVideoCard
        video={page.lead.video}
        dek={page.lead.content.dek}
        content={page.lead.content}
      />
    </section>
  );
}

/**
 * 后台预览入口：页头 + 单个完整视频推荐，
 * 不含续学/复习入口与下方 feed。`issues` 是编排校验的字段级错误。
 */
export function HomeEditorialPreview({
  page,
  issues = [],
}: {
  page: HomeEditorialPage;
  mode?: HomeEditorialMode;
  issues?: HomeLayoutIssue[];
}): ReactElement {
  return (
    <div className="user-ui home-editorial-preview home-compact">
      {issues.length > 0 && (
        <div className="home-editorial-issues" role="alert">
          <strong>预览数据校验未通过</strong>
          <ul>
            {issues.map((issue, index) => (
              <li key={`${issue.field}:${issue.code}:${index}`}>
                <span>{issue.field}</span>
                {issue.message}
              </li>
            ))}
          </ul>
        </div>
      )}
      <HomeEditorialHeader />
      {page.lead && <HomeEditorialHero page={page} />}
    </div>
  );
}
