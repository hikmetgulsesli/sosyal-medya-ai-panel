"use client";

import { useState } from "react";
import {
  ContentFormData,
  TONE_OPTIONS,
  PLATFORM_OPTIONS,
  CONTENT_TYPE_OPTIONS,
} from "@/types/ai-content";
import { Sparkles, Loader2, Type, MessageSquare, Hash } from "lucide-react";

interface ContentGenerationFormProps {
  onGenerate: (data: ContentFormData) => Promise<void>;
  isGenerating: boolean;
}

export function ContentGenerationForm({
  onGenerate,
  isGenerating,
}: ContentGenerationFormProps) {
  const [formData, setFormData] = useState<ContentFormData>({
    topic: "",
    tone: "professional",
    platform: "twitter",
    contentType: "post",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.topic.trim() || isGenerating) return;
    await onGenerate(formData);
  };

  const isValid = formData.topic.trim().length > 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Content Type Selection */}
      <div>
        <label className="mb-3 block text-sm font-medium text-[var(--text)]">
          Content Type
        </label>
        <div className="grid gap-3 sm:grid-cols-3">
          {CONTENT_TYPE_OPTIONS.map((option) => {
            const Icon =
              option.value === "post"
                ? Type
                : option.value === "thread"
                ? MessageSquare
                : Hash;
            const isSelected = formData.contentType === option.value;

            return (
              <button
                key={option.value}
                type="button"
                onClick={() =>
                  setFormData((prev) => ({ ...prev, contentType: option.value }))
                }
                className={`flex flex-col items-start gap-2 rounded-xl border p-4 text-left transition-all cursor-pointer ${
                  isSelected
                    ? "border-[var(--primary)] bg-[var(--primary)]/5"
                    : "border-[var(--border)] bg-[var(--card)] hover:border-[var(--primary)]/50"
                }`}
                style={{ transitionDuration: "var(--duration-normal)" }}
              >
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                    isSelected
                      ? "bg-[var(--primary)] text-white"
                      : "bg-[var(--surface)] text-[var(--text-muted)]"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p
                    className={`font-medium ${
                      isSelected ? "text-[var(--primary)]" : "text-[var(--text)]"
                    }`}
                  >
                    {option.label}
                  </p>
                  <p className="text-xs text-[var(--text-muted)]">
                    {option.description}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Topic Input */}
      <div>
        <label
          htmlFor="topic"
          className="mb-2 block text-sm font-medium text-[var(--text)]"
        >
          Topic or Prompt
        </label>
        <textarea
          id="topic"
          rows={4}
          placeholder="Describe what you want to write about..."
          value={formData.topic}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, topic: e.target.value }))
          }
          className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20 resize-none"
        />
        <p className="mt-1 text-xs text-[var(--text-muted)]">
          Be specific for better results. Include key points you want to cover.
        </p>
      </div>

      {/* Platform Selection */}
      <div>
        <label className="mb-3 block text-sm font-medium text-[var(--text)]">
          Target Platform
        </label>
        <div className="flex flex-wrap gap-2">
          {PLATFORM_OPTIONS.map((platform) => {
            const isSelected = formData.platform === platform.value;
            return (
              <button
                key={platform.value}
                type="button"
                onClick={() =>
                  setFormData((prev) => ({ ...prev, platform: platform.value }))
                }
                className={`rounded-full border px-4 py-2 text-sm font-medium transition-all cursor-pointer ${
                  isSelected
                    ? "border-[var(--primary)] bg-[var(--primary)] text-white"
                    : "border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] hover:border-[var(--primary)]/50 hover:text-[var(--text)]"
                }`}
                style={{ transitionDuration: "var(--duration-fast)" }}
              >
                {platform.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Tone Selection */}
      <div>
        <label className="mb-3 block text-sm font-medium text-[var(--text)]">
          Tone of Voice
        </label>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {TONE_OPTIONS.map((tone) => {
            const isSelected = formData.tone === tone.value;
            return (
              <button
                key={tone.value}
                type="button"
                onClick={() =>
                  setFormData((prev) => ({ ...prev, tone: tone.value }))
                }
                className={`flex flex-col items-start gap-1 rounded-lg border px-4 py-3 text-left transition-all cursor-pointer ${
                  isSelected
                    ? "border-[var(--primary)] bg-[var(--primary)]/5"
                    : "border-[var(--border)] bg-[var(--card)] hover:border-[var(--primary)]/50"
                }`}
                style={{ transitionDuration: "var(--duration-normal)" }}
              >
                <span
                  className={`font-medium ${
                    isSelected ? "text-[var(--primary)]" : "text-[var(--text)]"
                  }`}
                >
                  {tone.label}
                </span>
                <span className="text-xs text-[var(--text-muted)]">
                  {tone.description}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Generate Button */}
      <button
        type="submit"
        disabled={!isValid || isGenerating}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-[var(--primary)] px-6 py-3 text-sm font-medium text-white transition-all hover:bg-[var(--primary-hover)] disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer active:scale-[0.98]"
        style={{ transitionDuration: "var(--duration-normal)" }}
      >
        {isGenerating ? (
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
    </form>
  );
}
