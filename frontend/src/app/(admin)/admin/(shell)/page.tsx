"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { toast } from "sonner";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ArrowUpRight,
  Cpu,
  RefreshCw,
  ServerCog,
  Settings,
  TrendingUp,
  UserPlus,
  Users,
  Video,
} from "lucide-react";

import { AdminPageHeader, AdminEmptyState, AdminSkeleton } from "@/components/admin/ui";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import type { AdminStats } from "@/types";
import { getAdminStats, getUgcPendingCount, getWorkerStatus } from "@/lib/adminData";
import { Card } from "@/components/ui/Card";

// recharts is heavy (~100KB+ gzip) — load it only once stats are in, keeping
// it out of the dashboard's initial JS.
const GrowthTrendChart = dynamic(
  () => import("@/components/admin/GrowthTrendChart").then((m) => m.GrowthTrendChart),
  { ssr: false }
);

interface UgcPending {
  pending_processing: number;
  pending_review: number;
  total: number;
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------

function KpiCard({
  icon: Icon,
  label,
  value,
  delta,
  tone = "default",
  href,
}: {
  icon: typeof Activity;
  label: string;
  value: string | number;
  delta?: string;
  tone?: "default" | "brand" | "green" | "amber" | "red";
  href?: string;
}) {
  const toneStyles = {
    default: "bg-surface-soft text-muted",
    brand: "bg-brand-50 text-brand-600",
    green: "bg-success-soft text-success",
    amber: "bg-warning-soft text-warning",
    red: "bg-error/10 text-error",
  }[tone];

  const content = (
    <Card padding={5} className="group transition-all hover:shadow-md hover:border-brand-200">
      <div className="flex items-start justify-between">
        <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", toneStyles)}>
          <Icon size={18} />
        </div>
        {href && (
          <ArrowUpRight
            size={16}
            className="text-muted-soft opacity-0 transition-opacity group-hover:opacity-100"
          />
        )}
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

  if (href) {
    return <Link href={href}>{content}</Link>;
  }
  return content;
}

// ---------------------------------------------------------------------------
// Status Badge
// ---------------------------------------------------------------------------

function StatusBadge({ online }: { online: boolean | null }) {
  if (online === null) {
    return <span className="text-meta text-muted">检测中...</span>;
  }
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-meta font-medium",
        online ? "bg-success-soft text-success-text" : "bg-error/10 text-error-text"
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", online ? "bg-success" : "bg-error")} />
      {online ? "在线" : "离线"}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [workerOnline, setWorkerOnline] = useState<boolean | null>(null);
  const [ugc, setUgc] = useState<UgcPending | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const [s, w, u] = await Promise.all([
        getAdminStats(),
        getWorkerStatus()
          .then((d) => d.worker_online)
          .catch(() => null),
        getUgcPendingCount().catch(() => null),
      ]);
      setStats(s);
      setWorkerOnline(w);
      setUgc(u);
    } catch {
      setError(true);
      toast.error("加载概览失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (!stats && error) {
    return (
      <div className="space-y-6">
        <AdminPageHeader title="运营概览" description="实时掌握平台运行状态" />
        <AdminEmptyState
          text="加载概览失败"
          description="无法获取运营数据，请检查网络后重试"
          action={
            <Button onClick={load} variant="secondary" size="sm" icon={RefreshCw}>
              重试
            </Button>
          }
        />
      </div>
    );
  }

  if (loading || !stats) {
    return (
      <div className="space-y-6">
        <AdminPageHeader title="运营概览" description="实时掌握平台运行状态" />
        <AdminSkeleton.Page />
      </div>
    );
  }

  const pendingProcessing = ugc?.pending_processing ?? 0;
  const pendingReview = ugc?.pending_review ?? 0;

  // Prepare trend data for chart
  const trendData = stats.trend.dates.map((date, i) => ({
    date: new Date(date).toLocaleDateString("zh-CN", { month: "short", day: "numeric" }),
    注册: stats.trend.signups[i] ?? 0,
    活跃: stats.trend.active_users[i] ?? 0,
    词汇: stats.trend.vocabulary[i] ?? 0,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <AdminPageHeader
        title="运营概览"
        description="实时掌握平台运行状态"
        actions={
          <Button
            onClick={load}
            disabled={loading}
            variant="secondary"
            size="sm"
            icon={RefreshCw}
            className={loading ? "[&_svg]:animate-spin" : ""}
          >
            刷新
          </Button>
        }
      />

      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KpiCard
          icon={Users}
          label="总用户数"
          value={stats.total_users.toLocaleString()}
          delta={`+${stats.signups_today} 今日`}
          tone="brand"
          href="/admin/users"
        />
        <KpiCard
          icon={Activity}
          label="今日活跃"
          value={stats.active_users_today.toLocaleString()}
          tone="green"
        />
        <KpiCard
          icon={Video}
          label="待处理视频"
          value={ugc?.total ?? 0}
          tone={ugc?.total ? "red" : "default"}
          href="/admin/videos"
        />
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Trend Chart */}
        <Card padding={5} className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-copy font-semibold text-ink">增长趋势</h3>
            <span className="text-meta text-muted">近 30 天</span>
          </div>
          <GrowthTrendChart data={trendData} />
        </Card>

        {/* Right column */}
        <div className="space-y-6">
          {/* System Status */}
          <Card padding={5}>
            <h3 className="text-copy font-semibold text-ink mb-4">系统状态</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <ServerCog size={16} className="text-muted" />
                  <span className="text-copy text-body">GPU Worker</span>
                </div>
                <StatusBadge online={workerOnline} />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Cpu size={16} className="text-muted" />
                  <span className="text-copy text-body">GPU 队列</span>
                </div>
                <span
                  className={cn(
                    "text-copy font-medium",
                    stats.gpu_queue_depth > 0 ? "text-warning-text" : "text-muted"
                  )}
                >
                  {stats.gpu_queue_depth} 任务
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <AlertTriangle size={16} className="text-muted" />
                  <span className="text-copy text-body">失败视频</span>
                </div>
                <span
                  className={cn(
                    "text-copy font-medium",
                    stats.videos_error_count > 0 ? "text-error-text" : "text-muted"
                  )}
                >
                  {stats.videos_error_count}
                </span>
              </div>
            </div>
          </Card>

          {/* UGC Queue */}
          <Card padding={5}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-copy font-semibold text-ink">UGC 审核队列</h3>
              <Link href="/admin/videos" className="text-meta text-brand-700 hover:underline">
                查看全部
              </Link>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-surface-soft p-3 text-center">
                <p className="text-title font-semibold text-ink">{pendingProcessing}</p>
                <p className="text-meta text-muted mt-0.5">待处理</p>
              </div>
              <div className="rounded-lg bg-surface-soft p-3 text-center">
                <p className="text-title font-semibold text-ink">{pendingReview}</p>
                <p className="text-meta text-muted mt-0.5">待审核</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Quick Actions */}
      <Card padding={5}>
        <h3 className="text-copy font-semibold text-ink mb-4">快捷入口</h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { href: "/admin/videos", label: "视频管理", icon: Video },
            { href: "/admin/users", label: "用户管理", icon: Users },
            { href: "/admin/stats", label: "数据统计", icon: TrendingUp },
            { href: "/admin/settings", label: "系统设置", icon: Settings },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="group flex items-center gap-3 rounded-lg border border-hairline px-4 py-3 transition-all hover:border-brand-300 hover:bg-brand-50/50"
            >
              <item.icon
                size={18}
                className="text-muted group-hover:text-brand-500 transition-colors"
              />
              <span className="text-copy font-medium text-body group-hover:text-ink transition-colors">
                {item.label}
              </span>
              <ArrowRight
                size={14}
                className="ml-auto text-muted-soft opacity-0 group-hover:opacity-100 transition-opacity"
              />
            </Link>
          ))}
        </div>
      </Card>

      {/* Recent Activity */}
      {stats.recent_activity.length > 0 && (
        <Card padding={5}>
          <h3 className="text-copy font-semibold text-ink mb-4">最近动态</h3>
          <div className="space-y-3">
            {stats.recent_activity.slice(0, 5).map((activity) => (
              <div key={activity.id} className="flex items-center gap-3 text-copy">
                <span
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full",
                    "bg-brand-50 text-brand-500"
                  )}
                >
                  <UserPlus size={14} />
                </span>
                <span className="flex-1 text-body">{activity.summary}</span>
                <span className="text-meta text-muted-soft">
                  {new Date(activity.created_at).toLocaleTimeString("zh-CN", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
