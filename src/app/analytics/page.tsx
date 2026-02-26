import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { TrendingUp, Users, Heart, MessageCircle, Share2, Eye } from "lucide-react";

export const metadata = {
  title: "Analytics | Social Media AI Panel",
  description: "View your social media analytics",
};

const metrics = [
  { label: "Total Reach", value: "125.4K", change: "+15.3%", icon: Eye },
  { label: "Engagement", value: "8.2K", change: "+12.1%", icon: Heart },
  { label: "Followers", value: "45.2K", change: "+8.4%", icon: Users },
  { label: "Comments", value: "2.1K", change: "+5.7%", icon: MessageCircle },
];

const platformStats = [
  { platform: "Twitter/X", followers: "28.5K", engagement: "4.2%", posts: 156 },
  { platform: "LinkedIn", followers: "12.3K", engagement: "6.8%", posts: 89 },
  { platform: "Instagram", followers: "4.4K", engagement: "8.1%", posts: 67 },
];

const topPosts = [
  { title: "How AI is changing social media marketing", engagement: "2.4K", platform: "LinkedIn" },
  { title: "10 tips for viral content", engagement: "1.8K", platform: "Twitter/X" },
  { title: "Behind the scenes of our AI", engagement: "1.2K", platform: "Instagram" },
];

export default function AnalyticsPage() {
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

          {/* Metrics Grid */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {metrics.map((metric) => {
              const Icon = metric.icon;
              return (
                <div
                  key={metric.label}
                  className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 transition-all hover:-translate-y-0.5 hover:shadow-md cursor-pointer"
                  style={{ transitionDuration: "var(--duration-normal)" }}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-[var(--text-muted)]">{metric.label}</p>
                      <p className="mt-2 text-3xl font-bold text-[var(--text)]">{metric.value}</p>
                    </div>
                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--primary)]/10">
                      <Icon className="h-6 w-6 text-[var(--primary)]" />
                    </div>
                  </div>
                  <div className="mt-4 flex items-center gap-2">
                    <span className="text-sm font-medium text-[var(--success)]">{metric.change}</span>
                    <span className="text-xs text-[var(--text-muted)]">vs last month</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Platform Stats */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div className="mb-4 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-[var(--primary)]" />
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
                  {platformStats.map((stat) => (
                    <tr key={stat.platform} className="border-b border-[var(--border-subtle)] last:border-0">
                      <td className="py-4 text-sm font-medium text-[var(--text)]">{stat.platform}</td>
                      <td className="py-4 text-right text-sm text-[var(--text)]">{stat.followers}</td>
                      <td className="py-4 text-right text-sm text-[var(--success)]">{stat.engagement}</td>
                      <td className="py-4 text-right text-sm text-[var(--text-muted)]">{stat.posts}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top Posts */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div className="mb-4 flex items-center gap-2">
              <Share2 className="h-5 w-5 text-[var(--primary)]" />
              <h2 className="text-lg font-semibold text-[var(--text)]">Top Performing Posts</h2>
            </div>

            <div className="space-y-3">
              {topPosts.map((post, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-[var(--text)]">{post.title}</p>
                    <p className="text-xs text-[var(--text-muted)]">{post.platform}</p>
                  </div>
                  <div className="flex items-center gap-1 text-sm text-[var(--primary)]">
                    <Heart className="h-4 w-4" />
                    {post.engagement}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
