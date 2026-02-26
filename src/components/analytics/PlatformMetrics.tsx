"use client";

import { Twitter, Linkedin, Instagram, Cloud } from "lucide-react";
import type { PlatformMetrics as PlatformMetricsType } from "@/types/analytics";

interface PlatformMetricsProps {
  metrics: PlatformMetricsType[];
}

const platformIcons: Record<string, React.ReactNode> = {
  "Twitter/X": <Twitter className="h-5 w-5" />,
  LinkedIn: <Linkedin className="h-5 w-5" />,
  Instagram: <Instagram className="h-5 w-5" />,
  Bluesky: <Cloud className="h-5 w-5" />,
};

const platformColors: Record<string, string> = {
  "Twitter/X": "#0ea5e9",
  LinkedIn: "#0077b5",
  Instagram: "#f472b6",
  Bluesky: "#3b82f6",
};

export function PlatformMetrics({ metrics }: PlatformMetricsProps) {
  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
      <h3 className="text-lg font-semibold text-[var(--text)]">Platform Breakdown</h3>
      <p className="text-sm text-[var(--text-muted)]">Performance by platform</p>
      <div className="mt-6 space-y-4">
        {metrics.map((metric) => (
          <div
            key={metric.platform}
            className="flex items-center justify-between rounded-lg border border-[var(--border-subtle)] p-4 transition-colors hover:bg-[var(--secondary)] cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div
                className="flex h-10 w-10 items-center justify-center rounded-lg text-white"
                style={{ backgroundColor: platformColors[metric.platform] || "var(--primary)" }}
              >
                {platformIcons[metric.platform] || <Cloud className="h-5 w-5" />}
              </div>
              <div>
                <p className="font-medium text-[var(--text)]">{metric.platform}</p>
                <p className="text-sm text-[var(--text-muted)]">
                  {formatNumber(metric.posts)} posts
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-medium text-[var(--text)] tabular-nums">
                {formatNumber(metric.followers)} followers
              </p>
              <p className="text-sm text-[var(--success)]">{metric.engagement}% engagement</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
