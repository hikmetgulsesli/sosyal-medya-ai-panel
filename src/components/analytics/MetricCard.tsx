"use client";

import { TrendingUp, TrendingDown } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  color: string;
}

export function MetricCard({ title, value, change, changeLabel, icon, color }: MetricCardProps) {
  const isPositive = change && change >= 0;
  const isNegative = change && change < 0;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 transition-all hover:-translate-y-0.5 hover:shadow-md cursor-pointer" style={{ transitionDuration: "var(--duration-normal)" }}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--text-muted)]">{title}</p>
          <p className="mt-2 text-3xl font-bold text-[var(--text)] tabular-nums">{value}</p>
          {change !== undefined && (
            <div className="mt-2 flex items-center gap-1">
              {isPositive ? (
                <TrendingUp className="h-4 w-4 text-[var(--success)]" />
              ) : isNegative ? (
                <TrendingDown className="h-4 w-4 text-[var(--error)]" />
              ) : null}
              <span
                className={`text-sm font-medium ${
                  isPositive ? "text-[var(--success)]" : isNegative ? "text-[var(--error)]" : "text-[var(--text-muted)]"
                }`}
              >
                {isPositive ? "+" : ""}
                {change}%
              </span>
              {changeLabel && (
                <span className="text-sm text-[var(--text-muted)]">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
        <div
          className="flex h-12 w-12 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${color}20`, color }}
        >
          {icon}
        </div>
      </div>
    </div>
  );
}
