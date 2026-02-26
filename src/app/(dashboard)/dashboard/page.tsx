"use client";

import { useAuth } from '@/hooks/use-auth';
import { LayoutDashboard, TrendingUp, Users, MessageSquare } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();

  const stats = [
    { label: 'Total Posts', value: '0', icon: MessageSquare, change: '+0%' },
    { label: 'Followers', value: '0', icon: Users, change: '+0%' },
    { label: 'Engagement', value: '0%', icon: TrendingUp, change: '+0%' },
    { label: 'Scheduled', value: '0', icon: LayoutDashboard, change: '0 pending' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[var(--text)]">
          Dashboard
        </h1>
        <p className="mt-1 text-[var(--text-muted)]">
          Welcome back, {user?.name || 'User'}! Here&apos;s what&apos;s happening with your social media.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6 transition-all hover:shadow-md"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-[var(--text-muted)]">
                    {stat.label}
                  </p>
                  <p className="mt-2 text-3xl font-bold text-[var(--text)]">
                    {stat.value}
                  </p>
                  <p className="mt-1 text-xs text-[var(--success)]">
                    {stat.change}
                  </p>
                </div>
                <div className="h-12 w-12 rounded-lg bg-[var(--primary)]/10 flex items-center justify-center">
                  <Icon className="h-6 w-6 text-[var(--primary)]" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick actions */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-elevated)] p-6">
        <h2 className="text-lg font-semibold text-[var(--text)] mb-4">
          Quick Actions
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <a
            href="/dashboard/content"
            className="group flex items-center gap-4 p-4 rounded-lg border border-[var(--border)] hover:border-[var(--primary)] hover:bg-[var(--primary)]/5 transition-colors cursor-pointer"
          >
            <div className="h-10 w-10 rounded-lg bg-[var(--chart-2)]/10 flex items-center justify-center group-hover:bg-[var(--chart-2)]/20 transition-colors">
              <span className="text-lg">✨</span>
            </div>
            <div>
              <p className="font-medium text-[var(--text)]">Generate Content</p>
              <p className="text-sm text-[var(--text-muted)]">Create AI-powered posts</p>
            </div>
          </a>
          
          <a
            href="/dashboard/scheduler"
            className="group flex items-center gap-4 p-4 rounded-lg border border-[var(--border)] hover:border-[var(--primary)] hover:bg-[var(--primary)]/5 transition-colors cursor-pointer"
          >
            <div className="h-10 w-10 rounded-lg bg-[var(--chart-3)]/10 flex items-center justify-center group-hover:bg-[var(--chart-3)]/20 transition-colors">
              <span className="text-lg">📅</span>
            </div>
            <div>
              <p className="font-medium text-[var(--text)]">Schedule Post</p>
              <p className="text-sm text-[var(--text-muted)]">Plan your content calendar</p>
            </div>
          </a>
          
          <a
            href="/dashboard/competitors"
            className="group flex items-center gap-4 p-4 rounded-lg border border-[var(--border)] hover:border-[var(--primary)] hover:bg-[var(--primary)]/5 transition-colors cursor-pointer"
          >
            <div className="h-10 w-10 rounded-lg bg-[var(--chart-1)]/10 flex items-center justify-center group-hover:bg-[var(--chart-1)]/20 transition-colors">
              <span className="text-lg">🔍</span>
            </div>
            <div>
              <p className="font-medium text-[var(--text)]">Add Competitor</p>
              <p className="text-sm text-[var(--text-muted)]">Track competitor activity</p>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
