"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { ArrowRight, Calendar, Check, GraduationCap, Play } from "lucide-react";
import { api } from "@/lib/api";
import { Image } from "@/components/ui/Image";
import { PageHeader } from "@/components/ui/PageHeader";
import { TabPills } from "@/components/ui/TabPills";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { usePlan } from "@/hooks/usePlan";
import { useScrollRestore } from "@/hooks/useScrollRestore";
import { scrollKey } from "@/lib/scrollMemory";
import { watchHref } from "@/lib/watchEntry";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadMoreError } from "@/components/common/LoadMoreError";
import { InlineSpinner } from "@/components/common/Spinner";
import { PageTransition } from "@/components/common/PageTransition";
import { LinkButton } from "@/components/ui/LinkButton";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { DifficultyBadge } from "@/components/video/DifficultyBadge";
import { VideoMetadata } from "@/components/video/VideoMetadata";
import { VideoTitle } from "@/components/video/VideoTitle";
import { formatDuration } from "@/lib/format";
import { formatTimeSpent } from "@/lib/date";
import { videoTitleZh } from "@/lib/videoDisplay";
import type { LearningRecord, Paginated } from "@/types";

type FilterKey = "all" | "active" | "completed";

/** 设计「最近练习」卡：最近一次作答的试卷与答对数。 */
interface LatestAttempt {
  id: string;
  mode: string;
  exam_level: string | null;
  paper_title: string | null;
  question_count: number;
  score: number | null;
  correct_count: number | null;
  started_at: string;
  submitted_at: string | null;
}

interface VocabStats {
  total: number;
  due_review_count: number;
  mastered_count: number;
}

const FILTER_TABS: { key: FilterKey; label: string }[] = [
  { key: "all", label: "全部" },
  { key: "active", label: "学习中" },
  { key: "completed", label: "已完成" },
];

/**
 * 分组：今天 / 昨天 / 更早（对齐 stage-3/history.html）。
 *
 * 共享 `groupByDate` 多一个「本周」档（今天/昨天之外的最近 7 天），会把
 * 3–7 天前的记录单独成组，与设计三组口径不符；这里页面内自持三组口径。
 */
function dayBucket(iso: string | null): "今天" | "昨天" | "更早" {
  if (!iso) return "更早";
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return "更早";
  const now = new Date();
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterdayStart = todayStart - 86_400_000;
  const t = then.getTime();
  if (t >= todayStart) return "今天";
  if (t >= yesterdayStart) return "昨天";
  return "更早";
}

function formatRecordTime(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const hh = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  const bucket = dayBucket(iso);
  if (bucket === "今天") return `今天 ${hh}`;
  if (bucket === "昨天") return `昨天 ${hh}`;
  return `${d.getMonth() + 1}月${d.getDate()}日 ${hh}`;
}

function formatClock(seconds: number | null | undefined): string {
  if (seconds == null || Number.isNaN(seconds)) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatNotifyDate(iso: string | null): string {
  if (!iso) return "日期待定";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "日期待定";
  return `${d.getMonth() + 1}月${d.getDate()}日`;
}

/** 本周时长：设计口径写「3.4 小时」，按量级选单位。 */
function weekDuration(seconds: number): { value: string; unit: string } {
  if (!seconds || seconds < 60) {
    return { value: String(Math.max(0, Math.round(seconds))), unit: "秒" };
  }
  if (seconds < 3600) return { value: String(Math.floor(seconds / 60)), unit: "分钟" };
  return { value: (seconds / 3600).toFixed(1), unit: "小时" };
}

export default function HistoryPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const { profile } = usePlan();
  const [filter, setFilter] = useState<FilterKey>("all");
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const {
    items: records,
    hasMore,
    loading,
    error,
    loaderRef,
    loadMore,
    reload,
  } = usePaginatedList<LearningRecord>({
    fetcher: (pg) => {
      const params = new URLSearchParams({ page: String(pg), page_size: "20" });
      if (filter === "active") params.set("completed", "false");
      if (filter === "completed") params.set("completed", "true");
      return api<Paginated<LearningRecord>>(`/api/v1/learning/records?${params.toString()}`);
    },
    mode: "append",
    filters: [filter],
    enabled: isAuthenticated && !isLoading,
  });

  useScrollRestore(scrollKey(pathname, searchParams.toString()), records.length > 0);

  // 汇总统计（设计 4 项 stat：本周学习时长 / 已学视频 / 学完视频 / 连续学习）。
  const [stats, setStats] = useState<{
    weekSeconds: number;
    completedCount: number;
    overallTotal: number;
  } | null>(null);
  // 设计在记录列表上方还有最近观看 / 最近练习 / 词汇进展三张卡（V-19）。
  const [recent, setRecent] = useState<LearningRecord | null>(null);
  const [attempt, setAttempt] = useState<LatestAttempt | null>(null);
  const [vocab, setVocab] = useState<VocabStats | null>(null);

  useEffect(() => {
    if (!isAuthenticated || isLoading) return;
    let alive = true;
    Promise.all([
      api<{ this_week_minutes: number }>("/api/v1/learning/stats/weekly").catch(() => null),
      api<Paginated<LearningRecord>>(
        "/api/v1/learning/records?page=1&page_size=1&completed=true"
      ).catch(() => null),
      api<Paginated<LearningRecord>>("/api/v1/learning/records?page=1&page_size=1").catch(
        () => null
      ),
      api<Paginated<LatestAttempt>>("/api/v1/exams/attempts?page=1&page_size=1").catch(() => null),
      api<VocabStats>("/api/v1/vocabulary/stats").catch(() => null),
    ]).then(([weekly, completed, overall, attempts, vocabStats]) => {
      if (!alive) return;
      setStats({
        weekSeconds: (weekly?.this_week_minutes ?? 0) * 60,
        completedCount: completed?.total ?? 0,
        overallTotal: overall?.total ?? 0,
      });
      setRecent(overall?.items?.[0] ?? null);
      setAttempt(attempts?.items?.[0] ?? null);
      setVocab(vocabStats);
    });
    return () => {
      alive = false;
    };
  }, [isAuthenticated, isLoading]);

  // 三组：今天 / 昨天 / 更早。组头带「N 段 · 共 X 分钟」（设计口径）。
  const groups = useMemo(() => {
    const order: ("今天" | "昨天" | "更早")[] = ["今天", "昨天", "更早"];
    const buckets = new Map<string, LearningRecord[]>(order.map((k) => [k, []]));
    for (const record of records) {
      const key = dayBucket(record.last_accessed_at || record.created_at);
      buckets.get(key)!.push(record);
    }
    return order
      .map((label) => {
        const items = buckets.get(label)!;
        const seconds = items.reduce((sum, r) => sum + (r.time_spent_seconds || 0), 0);
        return { label, items, seconds };
      })
      .filter((g) => g.items.length > 0);
  }, [records]);

  const week = weekDuration(stats?.weekSeconds ?? 0);
  const overallTotal = stats?.overallTotal ?? 0;
  const completedCount = stats?.completedCount ?? 0;
  const activeCount = Math.max(overallTotal - completedCount, 0);

  const resume = useMemo(
    () =>
      records.find((r) => !r.completed && (r.progress_percentage > 0 || r.time_spent_seconds > 0)),
    [records]
  );

  const counts: Record<FilterKey, number> = {
    all: overallTotal,
    active: activeCount,
    completed: completedCount,
  };

  const tabs = FILTER_TABS.map((t) => ({
    key: t.key,
    label: (
      <span className="inline-flex items-center gap-1.5">
        {t.label}
        <span className="text-caption font-medium text-muted">{counts[t.key]}</span>
      </span>
    ),
  }));

  return (
    <PageTransition>
      <div className="user-page">
        <PageHeader
          crumb="我的"
          title="观看历史"

          variant="eyebrow"
          actions={
            resume ? (
              <LinkButton
                href={watchHref(resume.video_id, { from: "history" })}
                variant="primary"
                icon={Play}
              >
                继续《
                {(resume.video ? videoTitleZh(resume.video) : "上一段").slice(0, 18)}》
              </LinkButton>
            ) : undefined
          }
        />

        {/* 汇总统计：设计把 4 个数字放进描边卡里（不是裸铺在画布上）。 */}
        {stats && overallTotal > 0 && (
          <Card variant="outline" padding={5} className="mt-6">
            <div className="user-stat-grid">
              <div className="user-stat">
                <span className="user-stat-num">
                  {week.value}
                  <span className="ml-1 text-meta font-semibold text-muted">{week.unit}</span>
                </span>
                <span className="user-stat-label">本周学习时长</span>
              </div>
              <div className="user-stat">
                <span className="user-stat-num">
                  {overallTotal}
                  <span className="ml-1 text-meta font-semibold text-muted">段</span>
                </span>
                <span className="user-stat-label">已学视频</span>
              </div>
              <div className="user-stat">
                <span className="user-stat-num">
                  {completedCount}
                  <span className="ml-1 text-meta font-semibold text-muted">段</span>
                </span>
                <span className="user-stat-label">学完视频</span>
              </div>
              <div className="user-stat">
                <span className="user-stat-num">
                  {profile?.current_streak ?? 0}
                  <span className="ml-1 text-meta font-semibold text-muted">天</span>
                </span>
                <span className="user-stat-label">连续学习</span>
              </div>
            </div>
          </Card>
        )}

        {/* 设计在记录列表上方补三张卡：最近观看 / 最近练习 / 词汇进展（V-19）。
            手机必须显式 grid-cols-1：裸 `grid` 的列宽是 auto，卡片里那条不换行的
            视频标题会把列撑到 560px，整页在 375px 下横向溢出（e2e 三档视口用例）。 */}
        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          <Card variant="outline" padding={5}>
            <h2 className="text-copy font-semibold text-ink">最近观看</h2>
            {recent ? (
              <div className="mt-3 flex items-center gap-3">
                <span className="relative block aspect-video w-20 shrink-0 overflow-hidden rounded-sm border border-hairline bg-surface-card">
                  <Image src={recent.video?.thumbnail_url} alt="" sizes="80px" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-meta font-semibold text-ink">
                    {recent.video ? videoTitleZh(recent.video) : "未知视频"}
                  </p>
                  <p className="mt-0.5 text-caption text-muted">
                    看到 {formatClock(recent.position_seconds)} ·{" "}
                    {Math.round(recent.progress_percentage || 0)}%
                  </p>
                </div>
                <LinkButton
                  href={watchHref(recent.video_id, { from: "history" })}
                  variant="outline"
                  size="sm"
                >
                  继续
                </LinkButton>
              </div>
            ) : (
              <p className="mt-3 text-meta text-muted">
                还没有观看记录，看一段视频就会出现在这里。
              </p>
            )}
          </Card>

          <Card variant="outline" padding={5}>
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-copy font-semibold text-ink">最近练习</h2>
              <Link href="/practice" className="text-caption text-brand-700 hover:underline">
                去练习
              </Link>
            </div>
            {attempt ? (
              <div className="mt-3 flex items-center gap-3">
                <span className="grid h-10 w-14 shrink-0 place-items-center rounded-sm bg-surface-soft text-muted">
                  <GraduationCap size={18} aria-hidden />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-meta font-semibold text-ink">
                    {attempt.paper_title ||
                      (attempt.mode === "daily_check" ? "每日一练" : "真题练习")}
                  </p>
                  <p className="mt-0.5 text-caption text-muted">
                    {formatNotifyDate(attempt.submitted_at ?? attempt.started_at)} ·{" "}
                    {attempt.submitted_at
                      ? `${attempt.correct_count ?? 0} / ${attempt.question_count} 答对`
                      : "进行中"}
                  </p>
                </div>
                <LinkButton
                  href={`/practice/exams/result/${attempt.id}`}
                  variant="outline"
                  size="sm"
                >
                  回看
                </LinkButton>
              </div>
            ) : (
              <p className="mt-3 text-meta text-muted">还没有练习记录，去题库挑一套试试。</p>
            )}
          </Card>

          <Card variant="outline" padding={5}>
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-copy font-semibold text-ink">词汇进展</h2>
              <Link href="/vocabulary" className="text-caption text-brand-700 hover:underline">
                去复习
              </Link>
            </div>
            <div className="mt-3 space-y-1.5 text-meta">
              <div className="flex justify-between gap-3">
                <span className="text-muted">全部词汇</span>
                <span className="tabular-nums text-ink">{vocab?.total ?? "—"}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-muted">今天到期</span>
                <span className="tabular-nums text-ink">{vocab?.due_review_count ?? "—"}</span>
              </div>
              <div className="flex justify-between gap-3">
                <span className="text-muted">已掌握</span>
                <span className="tabular-nums text-ink">{vocab?.mastered_count ?? "—"}</span>
              </div>
            </div>
          </Card>
        </div>

        <div className="mt-6">
          <TabPills
            tabs={tabs}
            activeKey={filter}
            onChange={(key) => setFilter(key as FilterKey)}
          />
        </div>

        <div className="mt-6">
          <div>
            {loading && records.length === 0 ? (
              <InlineSpinner className="py-12" />
            ) : error && records.length === 0 ? (
              <ErrorState title={error} onRetry={reload} className="py-12" />
            ) : records.length === 0 && overallTotal === 0 ? (
              <EmptyState
                icon={Calendar}
                title="暂无学习记录"
                description="看完第一个视频就会出现在这里。"
                action={
                  <Link
                    href="/"
                    className="mt-3 inline-block text-copy font-semibold text-brand-700 hover:underline"
                  >
                    开始学习 →
                  </Link>
                }
                className="py-12"
              />
            ) : records.length === 0 ? (
              /* 筛选无结果 ≠ 没有记录：给筛选专用空态 + 回全部记录（设计口径）。 */
              <div className="rounded-lg border border-dashed border-hairline-strong bg-surface-soft p-5">
                <p className="text-copy font-semibold text-ink">这个筛选下还没有记录</p>
                <p className="mt-1 max-w-[44ch] text-copy leading-relaxed text-body">
                  {filter === "completed"
                    ? `「已完成」只统计看到最后一行的视频，目前有 ${completedCount} 段；在学的还有 ${activeCount} 段，换成「全部」能看到 ${overallTotal} 段。`
                    : `「学习中」只统计还没看到最后一行的视频，目前有 ${activeCount} 段；已看完的有 ${completedCount} 段，换成「全部」能看到 ${overallTotal} 段。`}
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <Button variant="outline" size="sm" onClick={() => setFilter("all")}>
                    看全部记录
                  </Button>
                  <LinkButton href="/" variant="text" size="sm" iconRight>
                    去浏览视频
                  </LinkButton>
                </div>
              </div>
            ) : (
              <div>
                {groups.map((group) => (
                  <section key={group.label}>
                    <h2 className="mb-2 mt-6 text-meta font-bold tracking-[0.06em] text-muted first:mt-0">
                      {group.label} · {group.items.length} 段 · 共 {formatTimeSpent(group.seconds)}
                    </h2>
                    <ul className="divide-y divide-hairline-soft">
                      {group.items.map((record) => (
                        <RecordRow key={record.id} record={record} />
                      ))}
                    </ul>
                  </section>
                ))}
              </div>
            )}

            <div ref={loaderRef} className="mt-8 flex justify-center">
              {loading && records.length > 0 && (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-muted-soft border-t-ink" />
              )}
              {!loading && error && records.length > 0 && (
                <LoadMoreError message={error} onRetry={loadMore} />
              )}
              {!hasMore && records.length > 0 && !loading && (
                <p className="text-meta text-muted">已加载全部内容</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}

/** 单条学习记录：发丝线行（缩略图 / 标题+元信息 / 进度+继续观看）。 */
function RecordRow({ record }: { record: LearningRecord }) {
  const pct = Math.min(Math.max(record.progress_percentage || 0, 0), 100);
  const duration = record.video?.duration ?? null;
  const remaining =
    duration && !record.completed ? Math.max(0, Math.round(duration * (1 - pct / 100))) : null;
  const href = watchHref(record.video_id, { from: "history" });
  const titleZh = record.video ? videoTitleZh(record.video) : "未知视频";

  return (
    <li className="grid grid-cols-1 items-center gap-3 py-4 md:grid-cols-[10rem_minmax(0,1fr)_13rem]">
      <Link
        href={href}
        aria-label={`继续观看 ${titleZh}`}
        className="relative block aspect-video overflow-hidden rounded-md border border-hairline bg-surface-card"
      >
        <Image
          src={record.video?.thumbnail_url}
          alt=""
          fill
          fallback={
            <div className="absolute inset-0 flex items-center justify-center text-title">🎬</div>
          }
        />
        {duration != null && duration > 0 && (
          <span className="absolute bottom-1.5 right-1.5 rounded-sm bg-surface-dark/80 px-1 text-caption font-semibold tabular-nums text-on-dark">
            {formatDuration(duration)}
          </span>
        )}
      </Link>

      <div className="min-w-0">
        {record.video ? (
          <Link href={href} className="block hover:text-brand-700">
            <VideoTitle
              video={record.video}
              as="span"
              zhClassName="text-copy font-semibold leading-snug text-ink"
            />
          </Link>
        ) : (
          <p className="text-copy font-semibold leading-snug text-ink">未知视频</p>
        )}
        {record.video && <VideoMetadata video={record.video} className="mt-1" />}
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-meta text-muted">
          {record.video?.channel_name && <span>{record.video.channel_name}</span>}
          <DifficultyBadge level={record.video?.difficulty_level} size="sm" />
          {record.time_spent_seconds > 0 && (
            <span>看了 {formatTimeSpent(record.time_spent_seconds)}</span>
          )}
          {record.position_seconds != null && (
            <span>停在 {formatClock(record.position_seconds)}</span>
          )}
          {record.completed && (
            <span className="inline-flex items-center gap-1 font-semibold text-success-text">
              <Check size={12} />
              已完成
            </span>
          )}
          <span>{formatRecordTime(record.last_accessed_at || record.created_at)}</span>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <div className="h-1.5 flex-1 rounded-pill bg-surface-card">
            <div
              className="h-full rounded-pill bg-brand-500 transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="w-10 text-right text-meta tabular-nums text-body">
            {Math.round(pct)}%
          </span>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className="text-caption text-muted">
            {record.completed
              ? "看完了，可再听一遍"
              : remaining != null
                ? `还剩 ${formatTimeSpent(remaining)}`
                : "从上次的位置接着看"}
          </span>
          <Link
            href={href}
            className="inline-flex shrink-0 items-center gap-1 text-meta font-semibold text-body transition-colors hover:text-brand-700"
          >
            {record.completed ? "复习" : "继续观看"}
            <ArrowRight size={13} />
          </Link>
        </div>
      </div>
    </li>
  );
}
