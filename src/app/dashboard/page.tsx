import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { LayoutDashboard, TrendingUp, Users, MessageSquare } from "lucide-react";

export const metadata = {
  title: "Dashboard | Social Media AI Panel",
  description: "Your social media command center",
};

const stats = [
  { label: "Total Posts", value: "1,234", change: "+12%", icon: MessageSquare },
  { label: "Followers", value: "45.2K", change: "+8%", icon: Users },
  { label: "Engagement", value: "4.8%", change: "+2.1%", icon: TrendingUp },
  { label: "Scheduled", value: "23", change: "+5", icon: LayoutDashboard },
];

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-[var(--text)]">Dashboard</h1>
            <p className="mt-1 text-[var(--text-muted)]">
              Welcome back! Here&apos;s what&apos;s happening with your social media.
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => {
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
                  <div className="mt-4 flex items-center gap-2">
                    <span className="text-sm font-medium text-[var(--success)]">{stat.change}</span>
                    <span className="text-xs text-[var(--text-muted)]">vs last month</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick Actions */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="text-lg font-semibold text-[var(--text)]">Quick Actions</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[
                { title: "Generate Content", description: "Create AI-powered posts", href: "/content-generator" },
                { title: "Schedule Posts", description: "Plan your content calendar", href: "/scheduler" },
                { title: "View Analytics", description: "Check performance metrics", href: "/analytics" },
              ].map((action) => (
                <a
                  key={action.title}
                  href={action.href}
                  className="group rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 transition-all hover:border-[var(--primary)] hover:shadow-sm cursor-pointer"
                  style={{ transitionDuration: "var(--duration-normal)" }}
                >
                  <h3 className="font-medium text-[var(--text)] group-hover:text-[var(--primary)]">
                    {action.title}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">{action.description}</p>
                </a>
              ))}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
