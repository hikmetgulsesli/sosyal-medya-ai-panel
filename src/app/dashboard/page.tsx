import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import Link from "next/link";
import { DashboardStats } from "@/components/dashboard/DashboardStats";

export const metadata = {
  title: "Dashboard | Social Media AI Panel",
  description: "Your social media command center",
};

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

          {/* Stats Grid - Client Component */}
          <DashboardStats />

          {/* Quick Actions */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="text-lg font-semibold text-[var(--text)]">Quick Actions</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[
                { title: "Generate Content", description: "Create AI-powered posts", href: "/content-generator" },
                { title: "Schedule Posts", description: "Plan your content calendar", href: "/scheduler" },
                { title: "View Analytics", description: "Check performance metrics", href: "/analytics" },
              ].map((action) => (
                <Link
                  key={action.title}
                  href={action.href}
                  className="group rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 transition-all hover:border-[var(--primary)] hover:shadow-sm cursor-pointer"
                  style={{ transitionDuration: "var(--duration-normal)" }}
                >
                  <h3 className="font-medium text-[var(--text)] group-hover:text-[var(--primary)]">
                    {action.title}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">{action.description}</p>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
