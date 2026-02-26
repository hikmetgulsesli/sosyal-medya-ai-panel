import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Calendar, Clock, Plus, ChevronLeft, ChevronRight } from "lucide-react";

export const metadata = {
  title: "Scheduler | Social Media AI Panel",
  description: "Schedule your social media posts",
};

export default function SchedulerPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-[var(--text)]">Scheduler</h1>
              <p className="mt-1 text-[var(--text-muted)]">
                Plan and schedule your content calendar.
              </p>
            </div>
            <button className="flex items-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)] cursor-pointer"
              style={{ transitionDuration: "var(--duration-normal)" }}
            >
              <Plus className="h-4 w-4" />
              New Post
            </button>
          </div>

          {/* Calendar Header */}
          <div className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
            <div className="flex items-center gap-4">
              <h2 className="text-lg font-semibold text-[var(--text)]">February 2026</h2>
              <div className="flex gap-1">
                <button className="rounded-lg p-1 text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
                  style={{ transitionDuration: "var(--duration-fast)" }}
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button className="rounded-lg p-1 text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
                  style={{ transitionDuration: "var(--duration-fast)" }}
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>
            </div>
            <button className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-sm font-medium text-[var(--text)] hover:bg-[var(--secondary)] cursor-pointer"
              style={{ transitionDuration: "var(--duration-fast)" }}
            >
              Today
            </button>
          </div>

          {/* Calendar Grid */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
            {/* Days Header */}
            <div className="mb-2 grid grid-cols-7 gap-2">
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
                <div key={day} className="py-2 text-center text-sm font-medium text-[var(--text-muted)]">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Days */}
            <div className="grid grid-cols-7 gap-2">
              {Array.from({ length: 35 }, (_, i) => {
                const day = i - 4; // Offset for February 2026
                const isCurrentMonth = day > 0 && day <= 28;
                const isToday = day === 26;
                const hasPosts = [3, 8, 15, 22, 26].includes(day);

                return (
                  <div
                    key={i}
                    className={`min-h-[100px] rounded-lg border p-2 ${
                      isCurrentMonth
                        ? "border-[var(--border)] bg-[var(--surface)]"
                        : "border-[var(--border-subtle)] bg-[var(--surface)]/50"
                    } ${isToday ? "ring-2 ring-[var(--primary)]" : ""}`}
                  >
                    {isCurrentMonth && (
                      <>
                        <span
                          className={`text-sm ${
                            isToday
                              ? "flex h-6 w-6 items-center justify-center rounded-full bg-[var(--primary)] text-white"
                              : "text-[var(--text)]"
                          }`}
                        >
                          {day}
                        </span>
                        {hasPosts && (
                          <div className="mt-2 space-y-1">
                            <div className="rounded bg-[var(--primary)]/10 px-2 py-1 text-xs text-[var(--primary)]">
                              <div className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                10:00 AM
                              </div>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Upcoming Posts */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="text-lg font-semibold text-[var(--text)]">Upcoming Posts</h2>
            <div className="mt-4 space-y-3">
              {[
                { time: "Today, 2:00 PM", platform: "Twitter/X", content: "Check out our latest AI features..." },
                { time: "Tomorrow, 10:00 AM", platform: "LinkedIn", content: "How AI is transforming social media..." },
                { time: "Feb 28, 3:00 PM", platform: "Instagram", content: "Behind the scenes of our AI..." },
              ].map((post, i) => (
                <div
                  key={i}
                  className="flex items-center gap-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--primary)]/10">
                    <Calendar className="h-5 w-5 text-[var(--primary)]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--text)]">{post.content}</p>
                    <p className="text-xs text-[var(--text-muted)]">
                      {post.time} · {post.platform}
                    </p>
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
