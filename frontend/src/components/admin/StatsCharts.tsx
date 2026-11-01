"use client";

/**
 * 管理端统计页的三块 recharts 图表。
 *
 * 单独成模块是**打包**需要，不是分层偏好：`recharts` 约 100KB+ gzip，
 * 只要页面里还有一处静态 `import ... from "recharts"`，整包就会进该路由的
 * 首屏 JS。页面用 `next/dynamic` 加载这里，图表数据到齐后才拉包 —— 与
 * `GrowthTrendChart` 的做法一致。
 */

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatMonthDay } from "@/lib/format";
import { useChartTheme } from "@/lib/chart-theme";

export interface StatsTrendPoint {
  date: string;
  signups: number;
  vocabulary: number;
  active: number;
}

export interface StatsChartSlice {
  name: string;
  value: number;
  color: string;
}

export function StatsTrendChart({ data }: { data: StatsTrendPoint[] }) {
  const ct = useChartTheme();
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <defs>
          <linearGradient id="gSignups" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={ct.series.brand} stopOpacity={0.2} />
            <stop offset="95%" stopColor={ct.series.brand} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gVocab" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={ct.series.success} stopOpacity={0.2} />
            <stop offset="95%" stopColor={ct.series.success} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gActive" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={ct.series.indigo} stopOpacity={0.2} />
            <stop offset="95%" stopColor={ct.series.indigo} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
        <XAxis
          dataKey="date"
          tickFormatter={formatMonthDay}
          tick={{ fontSize: 11, fill: ct.tick }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis tick={{ fontSize: 11, fill: ct.tick }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ ...ct.tooltipStyle, borderRadius: "8px" }}
          labelFormatter={(label) => formatMonthDay(String(label))}
        />
        <Area
          type="monotone"
          dataKey="vocabulary"
          stroke={ct.series.success}
          strokeWidth={2}
          fill="url(#gVocab)"
          name="新增词汇"
        />
        <Area
          type="monotone"
          dataKey="active"
          stroke={ct.series.indigo}
          strokeWidth={2}
          fill="url(#gActive)"
          name="活跃用户"
        />
        <Area
          type="monotone"
          dataKey="signups"
          stroke={ct.series.brand}
          strokeWidth={2}
          fill="url(#gSignups)"
          name="新增注册"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function StatsPlanPieChart({ data }: { data: StatsChartSlice[] }) {
  const ct = useChartTheme();
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={85}
          paddingAngle={2}
        >
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip contentStyle={{ ...ct.tooltipStyle, borderRadius: "8px" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function StatsStatusBarChart({ data }: { data: StatsChartSlice[] }) {
  const ct = useChartTheme();
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} vertical={false} />
        <XAxis
          dataKey="name"
          tick={{ fontSize: 11, fill: ct.tick }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fontSize: 11, fill: ct.tick }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip contentStyle={{ ...ct.tooltipStyle, borderRadius: "8px" }} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={48}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
