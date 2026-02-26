"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { FollowerDataPoint } from "@/types/analytics";

interface FollowerChartProps {
  data: FollowerDataPoint[];
}

export function FollowerChart({ data }: FollowerChartProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
      <h3 className="text-lg font-semibold text-[var(--text)]">Follower Growth</h3>
      <p className="text-sm text-[var(--text-muted)]">Last 30 days</p>
      <div className="mt-6 h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="var(--text-muted)"
              fontSize={12}
              tickMargin={10}
              interval="preserveStartEnd"
            />
            <YAxis
              tickFormatter={formatNumber}
              stroke="var(--text-muted)"
              fontSize={12}
              tickMargin={10}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-md)",
                padding: "12px",
              }}
              labelStyle={{ color: "var(--text)", fontWeight: 600 }}
              itemStyle={{ color: "var(--primary)" }}
              formatter={(value) => [formatNumber(value as number), "Followers"]}
              labelFormatter={(label) => formatDate(label as string)}
            />
            <Line
              type="monotone"
              dataKey="followers"
              stroke="var(--primary)"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: "var(--primary)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
