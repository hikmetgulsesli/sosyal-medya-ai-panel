"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { fetchAnalyticsOverview, type AnalyticsApiError } from "@/lib/analytics";
import { useAuth } from "@/contexts/AuthContext";
import type { AnalyticsOverview, FollowerGrowthPoint } from "@/types/analytics";
import {
  TrendingUp,
  Users,
  Heart,
  Share2,
  FileText,
  AlertCircle,
  Loader2,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + "M";
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + "K";
  }
  return num.toString();
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: string;
  icon: React.ComponentType<{ className?: string }>;
  isLoading?: boolean;
}

function MetricCard({ label, value, change, icon: Icon, isLoading }: MetricCardProps) {
  return (
    <div
      className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 transition-all hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
      style={{ transitionDuration: "var(--duration-normal)" }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-[var(--text-muted)]">{label}</p>
          {isLoading ? (
            <div className="mt-2 h-8 w-20 animate-pulse rounded bg-[var(--surface)]" />
          ) : (
            <p className="mt-2 text-3xl font-bold text-[var(--text)]">{value}</p>
          )}
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--primary)]/10">
          <Icon className="h-6 w-6 text-[var(--primary)]" />
        </div>
      </div>
      {change && (
        <div className="mt-4 flex items-center gap-2">
          <span className="text-sm font-medium text-[var(--success)]">{change}</span>
          <span className="text-xs text-[var(--text-muted)]">vs last month</span>
        </div>
      )}
    </div>
  );
}

interface FollowerChartProps {
  data: FollowerGrowthPoint[];
  isLoading?: boolean;
}

function FollowerChart({ data, isLoading }: FollowerChartProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="mb-4 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-[var(--primary)]" />
          <h2 className="text-lg font-semibold text-[var(--text)]">Follower Growth (30 Days)</h2>
        </div>
        <div className="h-[300px] w-full animate-pulse rounded-lg bg-[var(--surface)]" />
      </div>
    );
  }

  const chartData = data.map((point) => ({
    ...point,
    displayDate: formatDate(point.date),
  }));

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
      <div className="mb-4 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-[var(--primary)]" />
        <h2 className="text-lg font-semibold text-[var(--text)]">Follower Growth (30 Days)</h2>
      </div>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
            <XAxis
              dataKey="displayDate"
              stroke="var(--text-muted)"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              minTickGap={30}
            />
            <YAxis
              stroke="var(--text-muted)"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              tickFormatter={(value) => formatNumber(value)}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--card)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
              }}
              labelStyle={{ color: "var(--text)" }}
              itemStyle={{ color: "var(--text)" }}
              formatter={(value: number | undefined) => [formatNumber(value ?? 0), "Followers"]}
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

interface RecentPostsTableProps {
  posts: AnalyticsOverview["recent_posts"];
  isLoading?: boolean;
}

function RecentPostsTable({ posts, isLoading }: RecentPostsTableProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="mb-4 flex items-center gap-2">
          <FileText className="h-5 w-5 text-[var(--primary)]" />
          <h2 className="text-lg font-semibold text-[var(--text)]">Recent Posts</h2>
        </div>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 w-full animate-pulse rounded-lg bg-[var(--surface)]" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
      <div className="mb-4 flex items-center gap-2">
        <FileText className="h-5 w-5 text-[var(--primary)]" />
        <h2 className="text-lg font-semibold text-[var(--text)]">Recent Posts</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--border)]">
              <th className="pb-3 text-left text-sm font-medium text-[var(--text-muted)]">Content</th>
              <th className="pb-3 text-left text-sm font-medium text-[var(--text-muted)]">Platform</th>
              <th className="pb-3 text-left text-sm font-medium text-[var(--text-muted)]">Status</th>
              <th className="pb-3 text-right text-sm font-medium text-[var(--text-muted)]">Likes</th>
              <th className="pb-3 text-right text-sm font-medium text-[var(--text-muted)]">Engagement</th>
            </tr>
          </thead>
          <tbody>
            {posts.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-[var(--text-muted)]">
                  No posts yet. Start creating content to see analytics.
                </td>
              </tr>
            ) : (
              posts.map((post) => (
                <tr key={post.id} className="border-b border-[var(--border-subtle)] last:border-0">
                  <td className="py-4">
                    <p className="max-w-xs truncate text-sm text-[var(--text)]">{post.content}</p>
                  </td>
                  <td className="py-4">
                    <span className="text-sm text-[var(--text-muted)]">{post.platform}</span>
                  </td>
                  <td className="py-4">
                    <span
                      className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${
                        post.status === "published"
                          ? "bg-[var(--success)]/10 text-[var(--success)]"
                          : post.status === "scheduled"
                          ? "bg-[var(--warning)]/10 text-[var(--warning)]"
                          : "bg-[var(--surface)] text-[var(--text-muted)]"
                      }`}
                    >
                      {post.status}
                    </span>
                  </td>
                  <td className="py-4 text-right">
                    <span className="text-sm text-[var(--text)]">{formatNumber(post.likes)}</span>
                  </td>
                  <td className="py-4 text-right">
                    <span className="text-sm text-[var(--success)]">{post.engagement_rate.toFixed(2)}%</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface PlatformMetricsProps {
  metrics: AnalyticsOverview["platform_metrics"];
  isLoading?: boolean;
}

function PlatformMetrics({ metrics, isLoading }: PlatformMetricsProps) {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
        <div className="mb-4 flex items-center gap-2">
          <Share2 className="h-5 w-5 text-[var(--primary)]" />
          <h2 className="text-lg font-semibold text-[var(--text)]">Platform Performance</h2>
        </div>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-12 w-full animate-pulse rounded-lg bg-[var(--surface)]" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
      <div className="mb-4 flex items-center gap-2">
        <Share2 className="h-5 w-5 text-[var(--primary)]" />
        <h2 className="text-lg font-semibold text-[var(--text)]">Platform Performance</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--border)]">
              <th className="pb-3 text-left text-sm font-medium text-[var(--text-muted)]">Platform</th>
              <th className="pb-3 text-right text-sm font-medium text-[var(--text-muted)]">Followers</th>
              <th className="pb-3 text-right text-sm font-medium text-[var(--text-muted)]">Engagement</th>
              <th className="pb-3 text-right text-sm font-medium text-[var(--text-muted)]">Posts</th>
            </tr>
          </thead>
          <tbody>
            {metrics.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-8 text-center text-[var(--text-muted)]">
                  No platforms connected yet.
                </td>
              </tr>
            ) : (
              metrics.map((stat) => (
                <tr key={stat.platform} className="border-b border-[var(--border-subtle)] last:border-0">
                  <td className="py-4 text-sm font-medium text-[var(--text)]">{stat.platform}</td>
                  <td className="py-4 text-right text-sm text-[var(--text)]">
                    {formatNumber(stat.followers)}
                  </td>
                  <td className="py-4 text-right text-sm text-[var(--success)]">
                    {stat.engagement_rate.toFixed(2)}%
                  </td>
                  <td className="py-4 text-right text-sm text-[var(--text-muted)]">{stat.posts}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  const { getToken } = useAuth();
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalytics = async () => {
      const token = getToken();
      if (!token) return;

      try {
        setLoading(true);
        setError(null);
        const overview = await fetchAnalyticsOverview(token, 30);
        setData(overview);
      } catch (err) {
        const apiError = err as AnalyticsApiError;
        setError(apiError.message || "Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, [getToken]);

  const metrics = data
    ? [
        { label: "Total Posts", value: formatNumber(data.total_posts), icon: FileText },
        { label: "Avg Engagement", value: `${data.avg_engagement_rate.toFixed(2)}%`, icon: Heart },
        { label: "Total Followers", value: formatNumber(data.total_followers), icon: Users },
        { label: "Published", value: formatNumber(data.published_posts), icon: Share2 },
      ]
    : [
        { label: "Total Posts", value: "0", icon: FileText },
        { label: "Avg Engagement", value: "0%", icon: Heart },
        { label: "Total Followers", value: "0", icon: Users },
        { label: "Published", value: "0", icon: Share2 },
      ];

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-[var(--text)]">Analytics</h1>
            <p className="mt-1 text-[var(--text-muted)]">
              Track your social media performance across all platforms.
            </p>
          </div>

          {/* Error State */}
          {error && (
            <div className="flex items-center gap-3 rounded-xl border border-[var(--danger)]/20 bg-[var(--danger)]/10 p-4 text-[var(--danger)]">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Loading State */}
          {loading && !error && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-[var(--primary)]" />
              <span className="ml-3 text-[var(--text-muted)]">Loading analytics...</span>
            </div>
          )}

          {/* Metrics Grid */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {metrics.map((metric) => (
              <MetricCard
                key={metric.label}
                label={metric.label}
                value={metric.value}
                icon={metric.icon}
                isLoading={loading}
              />
            ))}
          </div>

          {/* Follower Growth Chart */}
          <FollowerChart data={data?.follower_growth ?? []} isLoading={loading} />

          {/* Platform Metrics & Recent Posts */}
          <div className="grid gap-6 lg:grid-cols-2">
            <PlatformMetrics metrics={data?.platform_metrics ?? []} isLoading={loading} />
            <RecentPostsTable posts={data?.recent_posts ?? []} isLoading={loading} />
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
