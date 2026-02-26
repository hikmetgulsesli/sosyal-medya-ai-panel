'use client';

import { useState } from 'react';
import { Platform, CreatePostInput, PlatformLabels } from '@/types/scheduler';
import { X, Calendar, Clock } from 'lucide-react';

interface CreatePostModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (input: CreatePostInput) => void;
  initialDate?: Date;
}

const platforms: Platform[] = ['twitter', 'linkedin', 'instagram', 'bluesky'];

export function CreatePostModal({ isOpen, onClose, onCreate, initialDate }: CreatePostModalProps) {
  const [content, setContent] = useState('');
  const [platform, setPlatform] = useState<Platform>('twitter');
  const [date, setDate] = useState(() => {
    const d = initialDate || new Date();
    return d.toISOString().split('T')[0];
  });
  const [time, setTime] = useState(() => {
    const d = initialDate || new Date();
    const hours = d.getHours().toString().padStart(2, '0');
    const minutes = Math.ceil(d.getMinutes() / 5) * 5;
    const mins = minutes.toString().padStart(2, '0');
    return `${hours}:${mins}`;
  });
  const [errors, setErrors] = useState<{ content?: string; scheduledAt?: string }>({});

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const newErrors: { content?: string; scheduledAt?: string } = {};
    
    if (!content.trim()) {
      newErrors.content = 'Content is required';
    } else if (content.length > 280 && platform === 'twitter') {
      newErrors.content = 'Twitter posts must be 280 characters or less';
    }
    
    if (!date || !time) {
      newErrors.scheduledAt = 'Date and time are required';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    const scheduledAt = new Date(`${date}T${time}`).toISOString();
    
    onCreate({
      content: content.trim(),
      platform,
      scheduledAt,
    });
    
    // Reset form
    setContent('');
    setPlatform('twitter');
    setErrors({});
    onClose();
  };

  const getMaxLength = () => {
    switch (platform) {
      case 'twitter':
        return 280;
      case 'linkedin':
        return 3000;
      case 'instagram':
        return 2200;
      case 'bluesky':
        return 300;
      default:
        return 280;
    }
  };

  const maxLength = getMaxLength();
  const charCount = content.length;
  const isOverLimit = charCount > maxLength;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        style={{ transitionDuration: 'var(--duration-normal)' }}
      />
      <div className="relative w-full max-w-lg rounded-xl border border-[var(--border)] bg-[var(--card)] shadow-lg">
        <div className="flex items-center justify-between border-b border-[var(--border)] px-6 py-4">
          <h2 className="text-lg font-semibold text-[var(--text)]">Schedule New Post</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
            style={{ transitionDuration: 'var(--duration-fast)' }}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 p-6">
          {/* Platform Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--text)]">Platform</label>
            <div className="grid grid-cols-2 gap-2">
              {platforms.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPlatform(p)}
                  className={`flex items-center justify-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer ${
                    platform === p
                      ? 'border-[var(--primary)] bg-[var(--primary)]/10 text-[var(--primary)]'
                      : 'border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)]'
                  }`}
                  style={{ transitionDuration: 'var(--duration-fast)' }}
                >
                  {PlatformLabels[p]}
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--text)]">
              Content
              <span className="ml-2 text-xs text-[var(--text-muted)]">
                ({charCount}/{maxLength})
              </span>
            </label>
            <textarea
              value={content}
              onChange={(e) => {
                setContent(e.target.value);
                if (errors.content) setErrors({ ...errors, content: undefined });
              }}
              placeholder="What's on your mind?"
              rows={5}
              className={`w-full resize-none rounded-lg border bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)] ${
                errors.content ? 'border-[var(--error)]' : 'border-[var(--border)]'
              } ${isOverLimit ? 'border-[var(--error)]' : ''}`}
            />
            {errors.content && (
              <p className="text-xs text-[var(--error)]">{errors.content}</p>
            )}
            {isOverLimit && !errors.content && (
              <p className="text-xs text-[var(--error)]">
                Content exceeds {maxLength} character limit for {PlatformLabels[platform]}
              </p>
            )}
          </div>

          {/* Date and Time */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--text)]">Date</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] py-2.5 pl-10 pr-4 text-sm text-[var(--text)] focus:border-[var(--primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)]"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--text)]">Time</label>
              <div className="relative">
                <Clock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-muted)]" />
                <input
                  type="time"
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] py-2.5 pl-10 pr-4 text-sm text-[var(--text)] focus:border-[var(--primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)]"
                />
              </div>
            </div>
          </div>
          {errors.scheduledAt && (
            <p className="text-xs text-[var(--error)]">{errors.scheduledAt}</p>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-medium text-[var(--text)] transition-colors hover:bg-[var(--secondary)] cursor-pointer"
              style={{ transitionDuration: 'var(--duration-fast)' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!content.trim() || isOverLimit}
              className="flex-1 rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)] disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
              style={{ transitionDuration: 'var(--duration-fast)' }}
            >
              Schedule Post
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
