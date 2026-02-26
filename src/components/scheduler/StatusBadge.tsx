'use client';

import { PostStatus, StatusColors } from '@/types/scheduler';

interface StatusBadgeProps {
  status: PostStatus;
  showDot?: boolean;
}

export function StatusBadge({ status, showDot = true }: StatusBadgeProps) {
  const colors = StatusColors[status];
  
  const labels: Record<PostStatus, string> = {
    scheduled: 'Scheduled',
    published: 'Published',
    failed: 'Failed',
    draft: 'Draft',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${colors.bg} ${colors.text}`}
    >
      {showDot && (
        <span className={`h-1.5 w-1.5 rounded-full ${colors.dot}`} />
      )}
      {labels[status]}
    </span>
  );
}
