"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Users, TrendingUp, AlertCircle } from "lucide-react";
import { MetricCard, FollowerChart, PlatformMetrics, RecentPostsTable } from "@/components/analytics";
import { fetchAnalyticsOverview, getMockAnalyticsData } from "@/lib/analytics";
import type { AnalyticsResponse } from "@/types/analytics";

function SkeletonCard() {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="space-y-3">
          <div className="h-4 w-24 rounded bg-[var(--secondary)]" />
          <div className="h-8 w-32 rounded bg-[var(--secondary)]" />
          <div className="h-4 w-20 rounded bg-[var(--secondary)]" />
        </div>
        <div className="h-12 w-12 rounded-lg bg-[var(--secondary)]" />
      </div>
    </div>
  );
}

function SkeletonChart() {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 animate-pulse">
      <div className="h-6 w-32 rounded bg-[var(--secondary)]" />
      <div className="mt-2 h-4 w-24 rounded bg-[var(--secondary)]" />
      <div className="mt-6 h-[300px] rounded bg-[var(--secondary)]" />
    </div>
  );
}

function SkeletonTable() {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 animate-pulse">
      <div className="h-6 w-32 rounded bg-[var(--secondary)]" />
      <div className="mt-2 h-4 w-48 rounded bg-[var(--secondary)]" />
      <div className="mt-6 space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-16 rounded bg-[var(--secondary)]" />
        ))}
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoading(true);
        setError(null);

        // Try to fetch from API first
        const token = localStorage.getItem("accessToken");
        if (token) {
          try {
            const response = await fetchAnalyticsOverview(token);
            setData(response);
            setLoading(false);
            return;
          } catch (apiError) {
            console.warn("API fetch failed, using mock data:", apiError);
          }
        }

        // Fall back to mock data
        const mockData = getMockAnalyticsData();
        setData(mockData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    }

    loadAnalytics();
  }, []);

  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--surface)]">
        {/* Header */}
        <header className="border-b border-[var(--border)] bg-[var(--surface-elevated)]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex h-16 items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-[var(--primary)]" />
                <h1 className="text-xl font-semibold text-[var(--text)]">Analytics Dashboard</h1>
              </div>
              <nav className="flex items-center gap-6">
                <Link
                  href="/"
                  className="text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] transition-colors cursor-pointer"
                >
                  Home
                </Link>
              </nav>
            </div>
          </div>
        </header>

        {/* Error State */}
        <main className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--card)] p-12 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--error)]/10">
              <AlertCircle className="h-8 w-8 text-[var(--error)]" />
            </div>
            <h2 className="mt-4 text-xl font-semibold text-[var(--text)]">Failed to Load Analytics</h2>
            <p className="mt-2 text-[var(--text-muted)]">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 inline-flex items-center justify-center rounded-lg bg-[var(--primary)] px-6 py-3 text-sm font-medium text-white hover:bg-[var(--primary-hover)] transition-colors cursor-pointer"
            >
              Try Again
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--surface)]">
      {/* Header */}
      <header className="border-b border-[var(--border)] bg-[var(--surface-elevated)]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg bg-[var(--primary)]" />
              <h1 className="text-xl font-semibold text-[var(--text)]">Analytics Dashboard</h1>
            </div>
            <nav className="flex items-center gap-6">
              <Link
                href="/"
                className="text-sm font-medium text-[var(--text-muted)] hover:text-[var(--text)] transition-colors cursor-pointer"
              >
                Home
              </Link>
              <span className="text-sm font-medium text-[var(--primary)]">
                Analytics
              </span>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Overview Cards */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {loading ? (
            <>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </>
          ) : data ? (
            <>
              <MetricCard
                title="Total Posts"
                value={formatNumber(data.overview.totalPosts)}
                icon={<FileText className="h-6 w-6" />}
                color="var(--chart-1)"
              />
              <MetricCard
                title="Avg Engagement"
                value={`${data.overview.avgEngagement}%`}
                change={0.8}
                changeLabel="vs last month"
                icon={<TrendingUp className="h-6 w-6" />}
                color="var(--chart-2)"
              />
              <MetricCard
                title="Followers"
                value={formatNumber(data.overview.followerCount)}
                change={data.overview.followerGrowth}
                changeLabel="vs last month"
                icon={<Users className="h-6 w-6" />}
                color="var(--chart-3)"
              />
              <MetricCard
                title="Active Platforms"
                value={data.platformMetrics.length}
                icon={<TrendingUp className="h-6 w-6" />}
                color="var(--chart-4)"
              />
            </>
          ) : null}
        </div>

        {/* Charts Row */}
        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            {loading ? (
              <SkeletonChart />
            ) : data ? (
              <FollowerChart data={data.followerGrowth} />
            ) : null}
          </div>
          <div>
            {loading ? (
              <SkeletonChart />
            ) : data ? (
              <PlatformMetrics metrics={data.platformMetrics} />
            ) : null}
          </div>
        </div>

        {/* Recent Posts Table */}
        <div className="mt-8">
          {loading ? (
            <SkeletonTable />
          ) : data ? (
            <RecentPostsTable posts={data.recentPosts} />
          ) : null}
        </div>
      </main>
    </div>
  );
}
