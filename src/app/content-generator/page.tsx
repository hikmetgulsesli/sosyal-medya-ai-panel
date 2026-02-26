"use client";

import { useState, useCallback, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuth } from "@/contexts/AuthContext";
import { Sparkles, Wand2, Hash, Type, Image, Loader2, Copy, Check, AlertCircle } from "lucide-react";
import type { 
  ContentType, 
  Platform, 
  GeneratePostResponse, 
  GenerateThreadResponse,
  SuggestHashtagsResponse 
} from "@/types/ai";

const CONTENT_TYPES: { type: ContentType; title: string; icon: typeof Type; description: string }[] = [
  { type: "post", title: "Post", icon: Type, description: "Generate single posts" },
  { type: "thread", title: "Thread", icon: Sparkles, description: "Create Twitter threads" },
  { type: "hashtags", title: "Hashtags", icon: Hash, description: "Find trending hashtags" },
  { type: "images", title: "Images", icon: Image, description: "AI image suggestions" },
];

const PLATFORMS: { id: Platform; name: string }[] = [
  { id: "twitter", name: "Twitter/X" },
  { id: "linkedin", name: "LinkedIn" },
  { id: "instagram", name: "Instagram" },
  { id: "bluesky", name: "Bluesky" },
];

const TONES = ["professional", "casual", "witty", "inspirational", "educational", "promotional"];

export default function ContentGeneratorPage() {
  const { getToken } = useAuth();
  
  // Form state
  const [contentType, setContentType] = useState<ContentType>("post");
  const [platform, setPlatform] = useState<Platform>("twitter");
  const [topic, setTopic] = useState("");
  const [tone, setTone] = useState("professional");
  const [context, setContext] = useState("");
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GeneratePostResponse | GenerateThreadResponse | SuggestHashtagsResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!topic.trim()) {
      setError("Please enter a topic or prompt");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const token = getToken();
      if (!token) {
        setError("Authentication required. Please log in again.");
        setIsLoading(false);
        return;
      }

      const response = await fetch("/api/ai/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          contentType,
          platform,
          topic: topic.trim(),
          tone,
          context: context.trim() || undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error?.message || "Failed to generate content");
      }

      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  }, [contentType, platform, topic, tone, context, getToken]);

  const handleCopy = useCallback(async () => {
    if (!result) return;
    
    let textToCopy = "";
    if ("content" in result) {
      textToCopy = result.content;
    } else if ("posts" in result) {
      textToCopy = result.posts.map(p => p.content).join("\n\n");
    } else if ("hashtags" in result) {
      textToCopy = result.hashtags.join(" ");
    }

    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy to clipboard");
    }
  }, [result]);

  const handlePlatformChange = useCallback((newPlatform: Platform) => {
    setPlatform(newPlatform);
    // Persist to localStorage
    localStorage.setItem("smp_selected_platform", newPlatform);
  }, []);

  // Load persisted platform on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("smp_selected_platform") as Platform | null;
      if (saved && PLATFORMS.some(p => p.id === saved)) {
        setPlatform(saved);
      }
    }
  }, []);

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
            {CONTENT_TYPES.map((type) => {
              const Icon = type.icon;
              const isSelected = contentType === type.type;
              return (
                <button
                  key={type.type}
                  onClick={() => setContentType(type.type)}
                  className={`flex flex-col items-center rounded-xl border p-6 text-center transition-all cursor-pointer ${
                    isSelected
                      ? "border-[var(--primary)] bg-[var(--primary)]/5 shadow-md"
                      : "border-[var(--border)] bg-[var(--card)] hover:-translate-y-0.5 hover:border-[var(--primary)] hover:shadow-md"
                  }`}
                  style={{ transitionDuration: "var(--duration-normal)" }}
                >
                  <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${
                    isSelected ? "bg-[var(--primary)]" : "bg-[var(--primary)]/10"
                  }`}>
                    <Icon className={`h-6 w-6 ${isSelected ? "text-white" : "text-[var(--primary)]"}`} />
                  </div>
                  <h3 className="mt-4 font-medium text-[var(--text)]">{type.title}</h3>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">{type.description}</p>
                </button>
              );
            })}
          </div>

          {/* Content Input Form */}
          <form onSubmit={handleSubmit} className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div className="mb-4 flex items-center gap-2">
              <Wand2 className="h-5 w-5 text-[var(--primary)]" />
              <h2 className="text-lg font-semibold text-[var(--text)]">Generate Content</h2>
            </div>
            
            <div className="space-y-4">
              {/* Topic Input */}
              <div>
                <label htmlFor="topic" className="mb-1.5 block text-sm font-medium text-[var(--text)]">
                  Topic or Prompt *
                </label>
                <textarea
                  id="topic"
                  rows={4}
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="Describe what you want to write about..."
                  disabled={isLoading}
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20 disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              {/* Context Input */}
              <div>
                <label htmlFor="context" className="mb-1.5 block text-sm font-medium text-[var(--text)]">
                  Additional Context (optional)
                </label>
                <input
                  id="context"
                  type="text"
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder="Any specific details or requirements..."
                  disabled={isLoading}
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2.5 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20 disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              {/* Tone Selection */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-[var(--text)]">Tone</label>
                <div className="flex flex-wrap gap-2">
                  {TONES.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTone(t)}
                      disabled={isLoading}
                      className={`rounded-full border px-4 py-1.5 text-sm capitalize transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${
                        tone === t
                          ? "border-[var(--primary)] bg-[var(--primary)] text-white"
                          : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] hover:border-[var(--primary)] hover:text-[var(--primary)]"
                      }`}
                      style={{ transitionDuration: "var(--duration-fast)" }}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Platform Selection */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-[var(--text)]">Platform</label>
                <div className="flex flex-wrap gap-2">
                  {PLATFORMS.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => handlePlatformChange(p.id)}
                      disabled={isLoading}
                      className={`rounded-full border px-4 py-1.5 text-sm transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${
                        platform === p.id
                          ? "border-[var(--primary)] bg-[var(--primary)] text-white"
                          : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] hover:border-[var(--primary)] hover:text-[var(--primary)]"
                      }`}
                      style={{ transitionDuration: "var(--duration-fast)" }}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading || !topic.trim()}
                className="flex items-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ transitionDuration: "var(--duration-normal)" }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    Generate Content
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Empty State */}
          {!result && !isLoading && !error && (
            <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-12 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[var(--primary)]/10">
                <Sparkles className="h-8 w-8 text-[var(--primary)]" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-[var(--text)]">Ready to Create</h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                Enter a topic above and click Generate to create AI-powered content.
              </p>
            </div>
          )}

          {/* Success State - Generated Content */}
          {result && (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-[var(--primary)]" />
                  <h2 className="text-lg font-semibold text-[var(--text)]">Generated Content</h2>
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-sm text-[var(--text)] transition-colors hover:bg-[var(--primary)]/10 cursor-pointer"
                  style={{ transitionDuration: "var(--duration-fast)" }}
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 text-green-500" />
                      <span className="text-green-600">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Copy
                    </>
                  )}
                </button>
              </div>

              <div className="space-y-4">
                {/* Post Result */}
                {"content" in result && (
                  <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
                    <p className="whitespace-pre-wrap text-[var(--text)]">{result.content}</p>
                    <div className="mt-3 flex items-center gap-4 text-xs text-[var(--text-muted)]">
                      <span>{result.char_count} characters</span>
                      <span>•</span>
                      <span>{result.estimated_read_time}</span>
                      <span>•</span>
                      <span>Generated with {result.provider.provider}</span>
                    </div>
                  </div>
                )}

                {/* Thread Result */}
                {"posts" in result && (
                  <div className="space-y-3">
                    {result.posts.map((post) => (
                      <div key={post.number} className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
                        <div className="mb-2 flex items-center gap-2">
                          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--primary)]/10 text-xs font-medium text-[var(--primary)]">
                            {post.number}
                          </span>
                          <span className="text-xs text-[var(--text-muted)]">{post.char_count} chars</span>
                        </div>
                        <p className="whitespace-pre-wrap text-[var(--text)]">{post.content}</p>
                      </div>
                    ))}
                    <div className="text-xs text-[var(--text-muted)]">
                      Generated with {result.provider.provider} • {result.total_posts} posts
                    </div>
                  </div>
                )}

                {/* Hashtags Result */}
                {"hashtags" in result && (
                  <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4">
                    <div className="flex flex-wrap gap-2">
                      {result.hashtags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full bg-[var(--primary)]/10 px-3 py-1 text-sm font-medium text-[var(--primary)]"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div className="mt-3 text-xs text-[var(--text-muted)]">
                      Generated with {result.provider.provider} • {result.hashtags.length} hashtags
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
