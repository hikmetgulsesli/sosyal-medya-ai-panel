import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { Sparkles, Wand2, Hash, Type, Image } from "lucide-react";

export const metadata = {
  title: "Content Generator | Social Media AI Panel",
  description: "Generate AI-powered social media content",
};

export default function ContentGeneratorPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-[var(--text)]">Content Generator</h1>
            <p className="mt-1 text-[var(--text-muted)]">
              Create engaging content with AI assistance.
            </p>
          </div>

          {/* Generator Types */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { title: "Post", icon: Type, description: "Generate single posts" },
              { title: "Thread", icon: Sparkles, description: "Create Twitter threads" },
              { title: "Hashtags", icon: Hash, description: "Find trending hashtags" },
              { title: "Images", icon: Image, description: "AI image suggestions" },
            ].map((type) => {
              const Icon = type.icon;
              return (
                <button
                  key={type.title}
                  className="flex flex-col items-center rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 text-center transition-all hover:-translate-y-0.5 hover:border-[var(--primary)] hover:shadow-md cursor-pointer"
                  style={{ transitionDuration: "var(--duration-normal)" }}
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-[var(--primary)]/10">
                    <Icon className="h-6 w-6 text-[var(--primary)]" />
                  </div>
                  <h3 className="mt-4 font-medium text-[var(--text)]">{type.title}</h3>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">{type.description}</p>
                </button>
              );
            })}
          </div>

          {/* Content Input */}
          <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div className="mb-4 flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-[var(--primary)]" />
              <h2 className="text-lg font-semibold text-[var(--text)]">Generate Content</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-[var(--text)]">
                  Topic or Prompt
                </label>
                <textarea
                  rows={4}
                  placeholder="Describe what you want to write about..."
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20"
                />
              </div>

              <div className="flex flex-wrap gap-2">
                {["Twitter/X", "LinkedIn", "Instagram", "Bluesky"].map((platform) => (
                  <button
                    key={platform}
                    type="button"
                    className="rounded-full border border-[var(--border)] bg-[var(--surface)] px-4 py-1.5 text-sm text-[var(--text-muted)] transition-colors hover:border-[var(--primary)] hover:text-[var(--primary)] cursor-pointer"
                    style={{ transitionDuration: "var(--duration-fast)" }}
                  >
                    {platform}
                  </button>
                ))}
              </div>

              <button className="flex items-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)] cursor-pointer"
                style={{ transitionDuration: "var(--duration-normal)" }}
              >
                <Sparkles className="h-4 w-4" />
                Generate Content
              </button>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
