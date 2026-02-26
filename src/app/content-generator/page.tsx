"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import {
  ContentGenerationForm,
  ContentPreview,
} from "@/components/content-generator";
import {
  ContentFormData,
  GeneratedContent,
} from "@/types/ai-content";
import { generateContent, saveToScheduler } from "@/lib/ai-content";
import { useAuth } from "@/contexts/AuthContext";
import { Sparkles, Wand2, AlertCircle } from "lucide-react";

export default function ContentGeneratorPage() {
  const { getToken } = useAuth();
  const [generatedContent, setGeneratedContent] =
    useState<GeneratedContent | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleGenerate = async (formData: ContentFormData) => {
    setError(null);
    setSuccessMessage(null);
    setIsGenerating(true);

    try {
      const content = await generateContent({
        topic: formData.topic,
        tone: formData.tone,
        platform: formData.platform,
        contentType: formData.contentType,
      });
      setGeneratedContent(content);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to generate content";
      setError(message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveToScheduler = async (
    contentId: string,
    scheduledAt?: string
  ) => {
    setError(null);
    setSuccessMessage(null);
    setIsScheduling(true);

    try {
      const token = getToken();
      await saveToScheduler(contentId, scheduledAt, token || undefined);
      setSuccessMessage(
        scheduledAt
          ? "Content scheduled successfully!"
          : "Content added to queue!"
      );
      // Clear the generated content after successful scheduling
      setTimeout(() => {
        setGeneratedContent(null);
        setSuccessMessage(null);
      }, 2000);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to schedule content";
      setError(message);
    } finally {
      setIsScheduling(false);
    }
  };

  const handleDiscard = () => {
    setGeneratedContent(null);
    setError(null);
    setSuccessMessage(null);
  };

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-[var(--text)]">
              Content Generator
            </h1>
            <p className="mt-1 text-[var(--text-muted)]">
              Create engaging content with AI assistance.
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-3 rounded-lg border border-[var(--error)]/20 bg-[var(--error)]/10 px-4 py-3 text-sm text-[var(--error)]">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <p>{error}</p>
            </div>
          )}

          {/* Success Message */}
          {successMessage && (
            <div className="flex items-center gap-3 rounded-lg border border-[var(--success)]/20 bg-[var(--success)]/10 px-4 py-3 text-sm text-[var(--success)]">
              <Sparkles className="h-5 w-5 shrink-0" />
              <p>{successMessage}</p>
            </div>
          )}

          <div className="grid gap-8 lg:grid-cols-[1fr,1.2fr]">
            {/* Generation Form */}
            <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
              <div className="mb-6 flex items-center gap-2">
                <Wand2 className="h-5 w-5 text-[var(--primary)]" />
                <h2 className="text-lg font-semibold text-[var(--text)]">
                  Generate Content
                </h2>
              </div>
              <ContentGenerationForm
                onGenerate={handleGenerate}
                isGenerating={isGenerating}
              />
            </div>

            {/* Content Preview */}
            <div>
              {generatedContent ? (
                <ContentPreview
                  content={generatedContent}
                  onSaveToScheduler={handleSaveToScheduler}
                  onDiscard={handleDiscard}
                  isScheduling={isScheduling}
                />
              ) : (
                <div className="flex h-full min-h-[400px] flex-col items-center justify-center rounded-xl border border-dashed border-[var(--border)] bg-[var(--card)] p-8 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--primary)]/10">
                    <Sparkles className="h-8 w-8 text-[var(--primary)]" />
                  </div>
                  <h3 className="mt-4 text-lg font-medium text-[var(--text)]">
                    Ready to Generate
                  </h3>
                  <p className="mt-2 max-w-sm text-sm text-[var(--text-muted)]">
                    Fill out the form and click Generate to create AI-powered
                    content for your social media platforms.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </DashboardLayout>
    </ProtectedRoute>
  );
}
