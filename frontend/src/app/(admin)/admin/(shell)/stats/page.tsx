"use client";

import { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  Activity,
  AlertTriangle,
  BookOpen,
  Cpu,
  RefreshCw,
  TrendingUp,
  UserPlus,
  Users,
  Video,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { apiErrorMessage } from "@/lib/errors";
import { formatMonthDay } from "@/lib/format";
import { AdminEmptyState, AdminPageHeader, AdminSkeleton } from "@/components/admin/ui";
import { Button } from "@/components/ui/Button";
import type { AdminLearningMetrics, AdminStats, RecentActivityType } from "@/types";
import { getAdminStats, getLearningMetrics } from "@/lib/adminData";
import { useChartTheme } from "@/lib/chart-theme";
import { Card } from "@/components/ui/Card";

// recharts 很重（约 100KB+ gzip），只有数据到齐、图表真正要画时才加载 ——
// 与 GrowthTrendChart 同一做法。图表本体在 components/admin/StatsCharts。
const StatsTrendChart = dynamic(
  () => import("@/components/admin/StatsCharts").then((m) => m.StatsTrendChart),
  { ssr: false, loading: () => <AdminSkeleton.Chart /> }
);
const StatsStatusBarChart = dynamic(
  () => import("@/components/admin/StatsCharts").then((m) => m.StatsStatusBarChart),
  { ssr: false, loading: () => <AdminSkeleton.Chart /> }
);

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const STATUS_LABEL: Record<string, string> = {
  ready: "就绪",
  ready_subtitles: "字幕就绪",
  processing: "处理中",
  error: "失败",
};

const TOPIC_COLORS = [
  "#ff5a1f",
  "#6366f1",
  "#16a34a",
  "#d97706",
  "#0ea5e9",
  "#a855f7",
  "#14b8a6",
  "#ef4444",
];

const ACTIVITY_ICON: Record<RecentActivityType, React.ElementType> = {
  signup: UserPlus,
};

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------

function KpiCard({
  icon: Icon,
  label,
  value,
  delta,
  tone = "default",
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  delta?: string;
  tone?: "default" | "brand" | "green" | "amber";
}) {
  const toneStyles = {
    default: "bg-surface-soft text-muted",
    brand: "bg-brand-50 text-brand-600",
    green: "bg-success-soft text-success",
    amber: "bg-warning-soft text-warning",
  }[tone];

  return (
    <Card padding={5}>
      <div className="flex items-start justify-between">
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", toneStyles)}>
          <Icon size={18} />
        </div>
      </div>
      <p className="mt-4 text-display-sm font-semibold text-ink">{value}</p>
      <div className="mt-1 flex items-center gap-2">
        <p className="text-meta text-muted">{label}</p>
        {delta && (
          <span className="inline-flex items-center gap-0.5 text-meta font-medium text-success-text">
            <TrendingUp size={12} />
            {delta}
          </span>
        )}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Section Card
// ---------------------------------------------------------------------------

function ChartCard({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card padding={5}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-copy font-semibold text-ink">{title}</h2>
          {description && <p className="text-meta text-muted mt-0.5">{description}</p>}
        </div>
        {actions}
      </div>
      {children}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// A12 学习测量（激活/留存、事件质量、性能基线）
// ---------------------------------------------------------------------------

function pct(rate: number | null): string {
  return rate === null ? "—" : `${(rate * 100).toFixed(1)}%`;
}

function msText(value: number | null): string {
  return value === null ? "—" : `${Math.round(value)} ms`;
}

function MetricRow({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-hairline py-2 last:border-0">
      <span className="text-copy text-body">{label}</span>
      <span className="text-right">
        <span className="font-mono text-copy font-semibold text-ink">{value}</span>
        {hint && <span className="ml-2 text-meta text-muted">{hint}</span>}
      </span>
    </div>
  );
}

function LearningMetricsSection({ metrics }: { metrics: AdminLearningMetrics }) {
  const mature1 = metrics.cohorts.filter((c) => c.d1_eligible);
  const mature7 = metrics.cohorts.filter((c) => c.d7_eligible);
  const d1Size = mature1.reduce((sum, c) => sum + c.size, 0);
  const d1Retained = mature1.reduce((sum, c) => sum + (c.d1_retained ?? 0), 0);
  const d7Size = mature7.reduce((sum, c) => sum + c.size, 0);
  const d7Retained = mature7.reduce((sum, c) => sum + (c.d7_retained ?? 0), 0);

  const events = metrics.event_quality.by_type.reduce((sum, e) => sum + e.events, 0);
  const withId = metrics.event_quality.by_type.reduce((sum, e) => sum + e.with_event_id, 0);
  const latestCohorts = metrics.cohorts.slice(-6).reverse();
  const vitals = metrics.performance.web_vitals;

  return (
    <>
      <div className="grid gap-6">
        <ChartCard
          title="激活与留存"
          description={`激活日 cohort · 近 ${metrics.days} 天 · 分母固定为入组人数`}
        >
          <div className="flex flex-col">
            <MetricRow
              label="24 小时激活率"
              value={pct(metrics.activation.rate)}
              hint={`${metrics.activation.activated_within_24h}/${metrics.activation.window_registered}`}
            />
            <MetricRow
              label="D1 回访"
              value={pct(d1Size ? d1Retained / d1Size : null)}
              hint={`${d1Retained}/${d1Size}`}
            />
            <MetricRow
              label="D7 回访"
              value={pct(d7Size ? d7Retained / d7Size : null)}
              hint={`${d7Retained}/${d7Size}`}
            />
            <MetricRow
              label="近 7 日活跃 / 至少 2 个学习日"
              value={`${metrics.weekly.active_7d} / ${metrics.weekly.multi_day_7d}`}
              hint={pct(metrics.weekly.volume_rate)}
            />
          </div>
          {latestCohorts.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-meta">
                <thead className="text-muted">
                  <tr>
                    <th className="py-1 pr-3 font-medium">cohort</th>
                    <th className="py-1 pr-3 font-medium">人数</th>
                    <th className="py-1 pr-3 font-medium">D1</th>
                    <th className="py-1 font-medium">D7</th>
                  </tr>
                </thead>
                <tbody className="text-body">
                  {latestCohorts.map((c) => (
                    <tr key={c.cohort_date} className="border-t border-hairline">
                      <td className="py-1 pr-3 font-mono">{c.cohort_date}</td>
                      <td className="py-1 pr-3 font-mono">{c.size}</td>
                      <td className="py-1 pr-3 font-mono">
                        {c.d1_eligible ? pct(c.d1_rate) : "未成熟"}
                      </td>
                      <td className="py-1 font-mono">
                        {c.d7_eligible ? pct(c.d7_rate) : "未成熟"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 text-meta text-muted">
                未成熟 cohort 不出数：D1/D7 要等窗口日过去，不用后来的用户补分母。
              </p>
            </div>
          )}
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="事件质量" description="版本、去重与客户端意图对账">
          <div className="flex flex-col">
            <MetricRow
              label="上报事件"
              value={events.toLocaleString()}
              hint={`缺 event_id ${pct(events ? (events - withId) / events : null)}`}
            />
            {metrics.event_quality.flows.length === 0 ? (
              <p className="py-3 text-meta text-muted">
                近 {metrics.days} 天没有带 flow_id 的提交流程。
              </p>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-meta">
                  <thead className="text-muted">
                    <tr>
                      <th className="py-1 pr-3 font-medium">路径</th>
                      <th className="py-1 pr-3 font-medium">客户端</th>
                      <th className="py-1 pr-3 font-medium">服务端</th>
                      <th className="py-1 pr-3 font-medium">丢失率</th>
                      <th className="py-1 font-medium">重复</th>
                    </tr>
                  </thead>
                  <tbody className="text-body">
                    {metrics.event_quality.flows.map((f) => (
                      <tr key={f.path} className="border-t border-hairline">
                        <td className="py-1 pr-3">{f.path}</td>
                        <td className="py-1 pr-3 font-mono">{f.client_distinct_flows}</td>
                        <td className="py-1 pr-3 font-mono">{f.server_facts}</td>
                        <td className="py-1 pr-3 font-mono">{pct(f.loss_rate)}</td>
                        <td className="py-1 font-mono">{f.duplicate_intents}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </ChartCard>

        <ChartCard title="性能基线" description="RUM p75 · 样本量决定可信度">
          <div className="flex flex-col">
            {(["lcp", "inp", "cls"] as const).map((metric) => {
              const sample = vitals[metric];
              const value = sample?.p75 ?? null;
              return (
                <MetricRow
                  key={metric}
                  label={metric.toUpperCase()}
                  value={
                    metric === "cls" ? (value === null ? "—" : value.toFixed(3)) : msText(value)
                  }
                  hint={`n=${sample?.samples ?? 0}`}
                />
              );
            })}
            <MetricRow
              label="首播耗时"
              value={msText(metrics.performance.first_play.p75_ms)}
              hint={`n=${metrics.performance.first_play.samples}`}
            />
            <MetricRow
              label="管线待派发"
              value={`${metrics.performance.pipeline_backlog.pending_dispatches}`}
              hint={
                metrics.performance.pipeline_backlog.oldest_pending_age_s === null
                  ? "无积压"
                  : `最久 ${metrics.performance.pipeline_backlog.oldest_pending_age_s}s`
              }
            />
          </div>
          <p className="mt-3 text-meta text-muted">
            样本 &lt; 20 只作参考；CLS 为无单位值，LCP/INP/首播为毫秒。
          </p>
        </ChartCard>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AdminStatsPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [metrics, setMetrics] = useState<AdminLearningMetrics | null>(null);
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [range, setRange] = useState<7 | 30 | 90>(30);
  const ct = useChartTheme();

  const STATUS_COLORS: Record<string, string> = {
    ready: ct.series.success,
    ready_subtitles: ct.series.warning,
    processing: ct.series.yellow,
    error: ct.series.error,
  };

  const load = useCallback(async (days: number) => {
    setLoading(true);
    setLoadError(null);
    setMetricsError(null);
    // 学习测量失败不拖垮整页：统计卡片是既有能力，新口径单独降级。
    const [statsResult, metricsResult] = await Promise.allSettled([
      getAdminStats(days),
      getLearningMetrics(days),
    ]);
    if (statsResult.status === "fulfilled") {
      setStats(statsResult.value);
    } else {
      setLoadError(apiErrorMessage(statsResult.reason, "加载统计数据失败，请稍后重试"));
    }
    if (metricsResult.status === "fulfilled") {
      setMetrics(metricsResult.value);
    } else {
      setMetrics(null);
      setMetricsError(apiErrorMessage(metricsResult.reason, "学习测量暂时不可用"));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void load(range);
  }, [range, load]);

  const refreshButton = (
    <Button
      onClick={() => load(range)}
      disabled={loading}
      variant="secondary"
      size="sm"
      icon={RefreshCw}
      className={loading ? "[&_svg]:animate-spin" : ""}
    >
      刷新
    </Button>
  );

  const header = (
    <AdminPageHeader
      title="数据统计"
      description="平台核心指标与趋势分析"
      actions={refreshButton}
    />
  );

  if (!stats) {
    // A-03：加载中 / 失败 / 无数据是三态，不再把失败混成永久骨架。
    return (
      <div className="space-y-6">
        {header}
        {loading ? (
          <div aria-busy="true">
            <p className="sr-only" role="status">
              正在加载统计数据…
            </p>
            <AdminSkeleton.Cards />
            <div className="mt-4">
              <AdminSkeleton.Chart />
            </div>
          </div>
        ) : loadError ? (
          <Card padding={5}>
            <AdminEmptyState
              icon={<AlertTriangle size={28} className="text-warning" />}
              text="无法加载统计数据"
              description={loadError}
              action={
                <Button onClick={() => load(range)} variant="secondary" size="sm" icon={RefreshCw}>
                  重试
                </Button>
              }
            />
          </Card>
        ) : (
          <Card padding={5}>
            <AdminEmptyState
              icon={<AlertTriangle size={28} className="text-muted-soft" />}
              text="暂无统计数据"
              description="后端返回了空数据，请稍后重试或检查统计接口。"
              action={
                <Button onClick={() => load(range)} variant="secondary" size="sm" icon={RefreshCw}>
                  重试
                </Button>
              }
            />
          </Card>
        )}
      </div>
    );
  }

  const slice = range;
  const startIdx = stats.trend.dates.length - slice;
  const trend = stats.trend.dates.slice(-slice).map((date, i) => ({
    date,
    signups: stats.trend.signups[startIdx + i],
    vocabulary: stats.trend.vocabulary[startIdx + i],
    active: stats.trend.active_users[startIdx + i],
  }));

  const newVocab7d = stats.trend.vocabulary.slice(-7).reduce((a, b) => a + b, 0);

  const statusData = stats.videos_by_status.map((s) => ({
    name: STATUS_LABEL[s.status] || s.status,
    value: s.count,
    color: STATUS_COLORS[s.status] || ct.series.neutral,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      {header}

      {/* 刷新失败但仍有上次数据：保留内容，顶部给出错误条 + 重试（A-03） */}
      {loadError && (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-error/30 bg-red-soft px-4 py-3 text-meta text-error-text"
        >
          <span className="flex items-center gap-2">
            <AlertTriangle size={14} aria-hidden />
            {loadError}（当前显示的是上次成功加载的数据）
          </span>
          <Button onClick={() => load(range)} variant="secondary" size="sm" icon={RefreshCw}>
            重试
          </Button>
        </div>
      )}

      {/* KPI Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          icon={Users}
          label="总用户数"
          value={stats.total_users.toLocaleString()}
          delta={`+${stats.signups_today} 今日`}
          tone="brand"
        />
        <KpiCard
          icon={UserPlus}
          label="今日新增"
          value={stats.signups_today}
          delta={`7日 ${stats.new_users_7d}`}
          tone="green"
        />
        <KpiCard icon={Activity} label="实时在线" value={stats.online_now} tone="brand" />
        <KpiCard
          icon={Video}
          label="视频总数"
          value={stats.total_videos}
          delta={`${stats.videos_ready} 就绪`}
        />
        <KpiCard
          icon={BookOpen}
          label="词汇总数"
          value={stats.total_vocabulary.toLocaleString()}
          delta={`+${newVocab7d} 近7日`}
          tone="green"
        />
        <KpiCard
          icon={Cpu}
          label="GPU 队列"
          value={stats.gpu_queue_depth}
          tone={stats.gpu_queue_depth > 0 ? "amber" : "default"}
        />
        <KpiCard
          icon={Video}
          label="失败视频"
          value={stats.videos_error_count}
          tone={stats.videos_error_count > 0 ? "amber" : "default"}
        />
      </div>

      {/* Trend Chart */}
      <ChartCard
        title="平台趋势"
        description="注册、新增词汇与活跃用户"
        actions={
          <div className="flex rounded-lg border border-hairline bg-surface-soft p-0.5">
            {([7, 30, 90] as const).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-meta font-medium transition-colors",
                  range === r ? "bg-canvas text-ink shadow-sm" : "text-muted hover:text-ink"
                )}
              >
                {r} 天
              </button>
            ))}
          </div>
        }
      >
        <StatsTrendChart data={trend} />
      </ChartCard>

      {/* Topic distribution + cumulative behavior distribution (MET-02: 不再叫漏斗) */}
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="视频分类分布" description="按主题">
          {stats.videos_by_topic.length === 0 ? (
            <p className="py-8 text-center text-meta text-muted">暂无已发布视频主题数据</p>
          ) : (
            <div className="flex flex-col gap-3">
              {stats.videos_by_topic.map((t, i) => {
                const max = stats.videos_by_topic[0].count || 1;
                const color = TOPIC_COLORS[i % TOPIC_COLORS.length];
                return (
                  <div key={t.topic} className="flex items-center gap-3">
                    <span className="w-[90px] shrink-0 truncate text-copy text-body">
                      {t.topic}
                    </span>
                    <div className="h-6 flex-1 overflow-hidden rounded-md bg-surface-soft">
                      <div
                        className="flex h-full items-center justify-end rounded-md pr-2 font-mono text-meta font-semibold text-white"
                        style={{
                          width: `${Math.max(12, (t.count / max) * 100)}%`,
                          backgroundColor: color,
                        }}
                      >
                        {t.count}
                      </div>
                    </div>
                    <span className="w-[52px] shrink-0 text-right font-mono text-copy font-semibold text-ink">
                      {t.count}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </ChartCard>

        <ChartCard title="累计行为分布" description="各段独立累计 · 非时序漏斗">
          <div className="flex flex-col gap-2">
            {(
              [
                ["注册用户", stats.funnel.registered, ct.series.brand],
                ["观看视频", stats.funnel.watched, "#ff7a45"],
                ["收藏词汇", stats.funnel.vocab_saved, ct.series.indigo],
              ] as [string, number, string][]
            ).map(([label, value, color]) => {
              const pct = stats.funnel.registered
                ? Math.round((value / stats.funnel.registered) * 1000) / 10
                : 0;
              return (
                <div key={label} className="flex items-center gap-3">
                  <span className="w-[90px] shrink-0 text-copy font-medium text-body">{label}</span>
                  <div className="flex-1">
                    <div
                      className="flex h-[34px] items-center overflow-hidden rounded-lg px-3.5 text-copy font-semibold text-white"
                      style={{
                        width: `${Math.max(8, pct)}%`,
                        backgroundColor: color,
                      }}
                    >
                      {value.toLocaleString()}
                    </div>
                  </div>
                  <span className="w-[70px] shrink-0 text-right font-mono text-copy font-bold text-ink">
                    {value.toLocaleString()}
                  </span>
                  <span className="w-[46px] shrink-0 text-meta text-muted">{pct}%</span>
                </div>
              );
            })}
          </div>
        </ChartCard>
      </div>

      {/* A12 学习测量（激活/留存、事件质量、性能基线） */}
      {metrics ? (
        <LearningMetricsSection metrics={metrics} />
      ) : metricsError ? (
        <Card padding={5}>
          <p className="text-meta text-muted">{metricsError}（已有统计不受影响）</p>
        </Card>
      ) : null}

      {/* Daily vocabulary bar chart (prototype 31 每日词汇学习量) */}
      <ChartCard title="每日词汇学习量" description="近 7 天">
        <div className="flex h-[200px] items-end gap-2.5 pt-2.5">
          {stats.trend.dates.slice(-7).map((date, i) => {
            const vocab = stats.trend.vocabulary.slice(-7);
            const max = Math.max(...vocab, 1);
            const v = vocab[i] ?? 0;
            return (
              <div
                key={date}
                className="flex h-full flex-1 flex-col items-center justify-end gap-2"
              >
                <span className="font-mono text-caption text-muted">{v}</span>
                <div
                  className="w-full max-w-[36px] rounded-t-md transition-opacity hover:opacity-85"
                  style={{
                    height: `${Math.max(3, (v / max) * 100)}%`,
                    backgroundColor: v === max ? "#e84a10" : "#ff7a45",
                  }}
                />
                <span className="font-mono text-caption text-muted">{formatMonthDay(date)}</span>
              </div>
            );
          })}
        </div>
      </ChartCard>

      {/* Distribution Charts */}
      <div className="grid gap-6">
        <ChartCard title="视频状态分布">
          <StatsStatusBarChart data={statusData} />
        </ChartCard>
      </div>

      {/* Recent Activity */}
      <ChartCard title="最近活动">
        <div className="space-y-1">
          {stats.recent_activity.map((a) => {
            const Icon = ACTIVITY_ICON[a.type] || TrendingUp;
            return (
              <div
                key={a.id}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 hover:bg-surface-soft/50 transition-colors"
              >
                <span
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full",
                    a.type === "signup"
                      ? "bg-brand-50 text-brand-500"
                      : "bg-success-soft text-success"
                  )}
                >
                  <Icon size={14} />
                </span>
                <span className="flex-1 text-copy text-body">{a.summary}</span>
                <span className="text-meta text-muted-soft">
                  {new Date(a.created_at).toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            );
          })}
        </div>
      </ChartCard>
    </div>
  );
}
