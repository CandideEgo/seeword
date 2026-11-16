"use client";

/**
 * GrowthTrendChart — recharts area chart for the admin overview page.
 * Split out so the recharts bundle loads lazily via next/dynamic.
 */

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { useChartTheme } from "@/lib/chart-theme";

export interface GrowthTrendPoint {
  date: string;
  注册: number;
  活跃: number;
  词汇: number;
}

export function GrowthTrendChart({ data }: { data: GrowthTrendPoint[] }) {
  // Series colors come from the shared chart theme so dark mode and the admin
  // stats page stay in sync (recharts cannot take Tailwind classes).
  const ct = useChartTheme();
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="gradSignup" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={ct.series.brand} stopOpacity={0.15} />
            <stop offset="95%" stopColor={ct.series.brand} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradActive" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={ct.series.indigo} stopOpacity={0.15} />
            <stop offset="95%" stopColor={ct.series.indigo} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradVocab" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={ct.series.success} stopOpacity={0.15} />
            <stop offset="95%" stopColor={ct.series.success} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: ct.tick }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis tick={{ fontSize: 11, fill: ct.tick }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={{ ...ct.tooltipStyle, borderRadius: "8px" }} />
        <Area
          type="monotone"
          dataKey="注册"
          stroke={ct.series.brand}
          strokeWidth={2}
          fill="url(#gradSignup)"
        />
        <Area
          type="monotone"
          dataKey="活跃"
          stroke={ct.series.indigo}
          strokeWidth={2}
          fill="url(#gradActive)"
        />
        {/* 后端每天下发 vocabulary；不画出来等于算了却丢掉（见 dashboard 的 trendData）。 */}
        <Area
          type="monotone"
          dataKey="词汇"
          stroke={ct.series.success}
          strokeWidth={2}
          fill="url(#gradVocab)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
