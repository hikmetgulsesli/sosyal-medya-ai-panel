"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { LayoutDashboard, TrendingUp, Users, MessageSquare, Loader2 } from "lucide-react";
import type { AnalyticsOverview } from "@/types/analytics";

interface StatItem {
  label: string;
  value: string;
  icon: typeof MessageSquare;
}

function formatNumber(n: number): string {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + "M";
  if (n >= 1000) return (n / 1000).toFixed(1) + "K";
  return n.toLocaleString();
}

export function DashboardStats() {
  const { getToken } = useAuth();
  const [stats, setStats] = useState<StatItem[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const token = getToken();
        if (!token) {
          setLoading(false);
          return;
        }

        const res = await fetch("/api/analytics/overview?days=30", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) {
          setLoading(false);
          return;
        }

        const data: AnalyticsOverview = await res.json();
        setStats([
          { label: "Total Posts", value: formatNumber(data.total_posts), icon: MessageSquare },
          { label: "Followers", value: formatNumber(data.total_followers), icon: Users },
          { label: "Engagement", value: data.avg_engagement_rate.toFixed(1) + "%", icon: TrendingUp },
          { label: "Scheduled", value: formatNumber(data.published_posts), icon: LayoutDashboard },
        ]);
      } catch {
        // API unavailable — show empty state
      } finally {
        setLoading(false);
      }
    }

    fetchStats();
  }, [getToken]);

  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="flex items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 h-[120px]"
          >
            <Loader2 className="h-5 w-5 animate-spin text-[var(--text-muted)]" />
          </div>
        ))}
      </div>
    );
  }

  const displayStats = stats || [
    { label: "Total Posts", value: "\u2014", icon: MessageSquare },
    { label: "Followers", value: "\u2014", icon: Users },
    { label: "Engagement", value: "\u2014", icon: TrendingUp },
    { label: "Scheduled", value: "\u2014", icon: LayoutDashboard },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {displayStats.map((stat) => {
        const Icon = stat.icon;
        return (
          <div
            key={stat.label}
            className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 transition-all hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
            style={{ transitionDuration: "var(--duration-normal)" }}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[var(--text-muted)]">{stat.label}</p>
                <p className="mt-2 text-3xl font-bold text-[var(--text)]">{stat.value}</p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--primary)]/10">
                <Icon className="h-6 w-6 text-[var(--primary)]" />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
