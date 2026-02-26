"use client";

import { useState, useRef } from "react";
import {
  GeneratedContent,
  Platform,
  PLATFORM_OPTIONS,
} from "@/types/ai-content";
import {
  Copy,
  Check,
  Calendar,
  Edit2,
  Save,
  X,
  Trash2,
  Loader2,
  Twitter,
  Linkedin,
  Instagram,
  Cloud,
} from "lucide-react";

interface ContentPreviewProps {
  content: GeneratedContent | null;
  onSaveToScheduler: (contentId: string, scheduledAt?: string) => Promise<void>;
  onDiscard: () => void;
  isScheduling: boolean;
}

const PLATFORM_ICONS: Record<Platform, typeof Twitter> = {
  twitter: Twitter,
  linkedin: Linkedin,
  instagram: Instagram,
  bluesky: Cloud,
};

const PLATFORM_COLORS: Record<Platform, string> = {
  twitter: "#0ea5e9",
  linkedin: "#0077b5",
  instagram: "#e4405f",
  bluesky: "#0569ff",
};

export function ContentPreview({
  content,
  onSaveToScheduler,
  onDiscard,
  isScheduling,
}: ContentPreviewProps) {
  const [copied, setCopied] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [scheduledDate, setScheduledDate] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  if (!content) return null;

  const PlatformIcon = PLATFORM_ICONS[content.platform];
  const platformColor = PLATFORM_COLORS[content.platform];
  const platformLabel =
    PLATFORM_OPTIONS.find((p) => p.value === content.platform)?.label ||
    content.platform;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(
        isEditing ? editedContent : content.content
      );
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API not available
    }
  };

  const handleEdit = () => {
    setEditedContent(content.content);
    setIsEditing(true);
    setTimeout(() => textareaRef.current?.focus(), 0);
  };

  const handleSaveEdit = () => {
    // In a real implementation, this would update the content on the server
    // Update local state instead of mutating props
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedContent(content.content);
    setIsEditing(false);
  };

  const handleSchedule = async () => {
    const scheduledAt = scheduledDate
      ? new Date(scheduledDate).toISOString()
      : undefined;
    await onSaveToScheduler(content.id, scheduledAt);
  };

  // Calculate character count (Twitter has 280 limit)
  const charCount = (isEditing ? editedContent : content.content).length;
  const charLimit = content.platform === "twitter" ? 280 : 2200;
  const isOverLimit = charCount > charLimit;

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface)] px-4 py-3">
        <div className="flex items-center gap-3">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-lg"
            style={{ backgroundColor: `${platformColor}20` }}
          >
            <PlatformIcon
              className="h-4 w-4"
              style={{ color: platformColor }}
            />
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--text)]">
              {platformLabel}
            </p>
            <p className="text-xs text-[var(--text-muted)]">
              {content.contentType === "thread"
                ? "Thread"
                : content.contentType === "hashtags"
                ? "Hashtags"
                : "Single Post"}{" "}
              •{" "}
              {content.tone.charAt(0).toUpperCase() + content.tone.slice(1)} tone
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleCancelEdit}
                className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-muted)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)] cursor-pointer"
                style={{ transitionDuration: "var(--duration-fast)" }}
              >
                <X className="h-4 w-4" />
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                className="flex items-center gap-1.5 rounded-lg bg-[var(--success)] px-3 py-1.5 text-sm text-white transition-colors hover:bg-[var(--success)]/90 cursor-pointer"
                style={{ transitionDuration: "var(--duration-fast)" }}
              >
                <Save className="h-4 w-4" />
                Save
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-muted)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)] cursor-pointer"
                style={{ transitionDuration: "var(--duration-fast)" }}
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4 text-[var(--success)]" />
                    <span className="text-[var(--success)]">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy
                  </>
                )}
              </button>
              <button
                onClick={handleEdit}
                className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--text-muted)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)] cursor-pointer"
                style={{ transitionDuration: "var(--duration-fast)" }}
              >
                <Edit2 className="h-4 w-4" />
                Edit
              </button>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {isEditing ? (
          <textarea
            ref={textareaRef}
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            rows={8}
            className="w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20"
          />
        ) : (
          <div className="whitespace-pre-wrap text-sm text-[var(--text)] leading-relaxed">
            {content.content}
          </div>
        )}

        {/* Hashtags */}
        {content.hashtags && content.hashtags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {content.hashtags.map((hashtag) => (
              <span
                key={hashtag}
                className="rounded-full bg-[var(--primary)]/10 px-2.5 py-1 text-xs text-[var(--primary)]"
              >
                #{hashtag}
              </span>
            ))}
          </div>
        )}

        {/* Character Count */}
        <div className="mt-4 flex justify-end">
          <span
            className={`text-xs ${
              isOverLimit ? "text-[var(--error)]" : "text-[var(--text-muted)]"
            }`}
          >
            {charCount} / {charLimit}
          </span>
        </div>
      </div>

      {/* Schedule Section */}
      <div className="border-t border-[var(--border)] bg-[var(--surface)] px-4 py-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Calendar className="h-4 w-4 text-[var(--text-muted)]" />
            <input
              type="datetime-local"
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
              className="rounded-lg border border-[var(--border)] bg-[var(--card)] px-3 py-1.5 text-sm text-[var(--text)] focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20"
            />
            <span className="text-xs text-[var(--text-muted)]">
              Leave empty to add to queue
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onDiscard}
              className="flex items-center gap-1.5 rounded-lg border border-[var(--border)] px-4 py-2 text-sm text-[var(--text-muted)] transition-colors hover:bg-[var(--destructive)]/10 hover:text-[var(--destructive)] hover:border-[var(--destructive)]/30 cursor-pointer"
              style={{ transitionDuration: "var(--duration-fast)" }}
            >
              <Trash2 className="h-4 w-4" />
              Discard
            </button>
            <button
              onClick={handleSchedule}
              disabled={isScheduling || isOverLimit || isEditing}
              className="flex items-center gap-1.5 rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)] disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
              style={{ transitionDuration: "var(--duration-fast)" }}
            >
              {isScheduling ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Calendar className="h-4 w-4" />
                  Save to Scheduler
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
