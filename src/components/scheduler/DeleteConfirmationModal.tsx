'use client';

import { ScheduledPost } from '@/types/scheduler';
import { AlertTriangle } from 'lucide-react';

interface DeleteConfirmationModalProps {
  post: ScheduledPost | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (postId: string) => void;
}

export function DeleteConfirmationModal({ post, isOpen, onClose, onConfirm }: DeleteConfirmationModalProps) {
  if (!isOpen || !post) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        style={{ transitionDuration: 'var(--duration-normal)' }}
      />
      <div className="relative w-full max-w-md rounded-xl border border-[var(--border)] bg-[var(--card)] shadow-lg">
        <div className="p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[var(--destructive)]/10">
              <AlertTriangle className="h-6 w-6 text-[var(--destructive)]" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-[var(--text)]">
                Cancel Scheduled Post
              </h2>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                Are you sure you want to cancel this scheduled post? This action cannot be undone.
              </p>
              
              <div className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3">
                <p className="line-clamp-2 text-sm text-[var(--text)]">&quot;{post.content}&quot;</p>
                <p className="mt-1 text-xs text-[var(--text-muted)]">
                  Scheduled for {new Date(post.scheduledAt).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-2.5 text-sm font-medium text-[var(--text)] transition-colors hover:bg-[var(--secondary)] cursor-pointer"
              style={{ transitionDuration: 'var(--duration-fast)' }}
            >
              Keep Post
            </button>
            <button
              type="button"
              onClick={() => {
                onConfirm(post.id);
                onClose();
              }}
              className="flex-1 rounded-lg bg-[var(--destructive)] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-600 cursor-pointer"
              style={{ transitionDuration: 'var(--duration-fast)' }}
            >
              Cancel Post
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
