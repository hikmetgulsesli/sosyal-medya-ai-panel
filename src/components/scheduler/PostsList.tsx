'use client';

import { useMemo, useState } from 'react';
import { ScheduledPost } from '@/types/scheduler';
import { StatusBadge } from './StatusBadge';
import { PlatformBadge } from './PlatformBadge';
import { Calendar, Clock, Edit, Trash2, ChevronUp, ChevronDown } from 'lucide-react';

type SortField = 'scheduledAt' | 'platform' | 'status' | 'createdAt';
type SortDirection = 'asc' | 'desc';

interface PostsListProps {
  posts: ScheduledPost[];
  onEdit: (post: ScheduledPost) => void;
  onDelete: (post: ScheduledPost) => void;
}

interface SortHeaderProps {
  field: SortField;
  currentField: SortField;
  direction: SortDirection;
  onSort: (field: SortField) => void;
  children: React.ReactNode;
}

function SortHeader({ field, currentField, direction, onSort, children }: SortHeaderProps) {
  return (
    <button
      onClick={() => onSort(field)}
      className="flex items-center gap-1 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text)] cursor-pointer"
    >
      {children}
      {currentField === field && (
        direction === 'asc' ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />
      )}
    </button>
  );
}

export function PostsList({ posts, onEdit, onDelete }: PostsListProps) {
  const [sortField, setSortField] = useState<SortField>('scheduledAt');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  const sortedPosts = useMemo(() => {
    return [...posts].sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case 'scheduledAt':
          comparison = new Date(a.scheduledAt).getTime() - new Date(b.scheduledAt).getTime();
          break;
        case 'platform':
          comparison = a.platform.localeCompare(b.platform);
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        case 'createdAt':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
      }
      
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [posts, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return {
      date: date.toLocaleDateString('default', { month: 'short', day: 'numeric' }),
      time: date.toLocaleTimeString('default', { hour: '2-digit', minute: '2-digit' }),
      full: date.toLocaleString(),
    };
  };

  if (posts.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-12 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[var(--muted)]">
          <Calendar className="h-8 w-8 text-[var(--text-muted)]" />
        </div>
        <h3 className="mt-4 text-lg font-medium text-[var(--text)]">No scheduled posts</h3>
        <p className="mt-1 text-sm text-[var(--text-muted)]">
          Get started by scheduling your first post.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="border-b border-[var(--border)] bg-[var(--surface)]">
            <tr>
              <th className="px-4 py-3 text-left">
                <SortHeader 
                  field="scheduledAt" 
                  currentField={sortField} 
                  direction={sortDirection} 
                  onSort={handleSort}
                >
                  Schedule Time
                </SortHeader>
              </th>
              <th className="px-4 py-3 text-left">
                <span className="text-xs font-medium text-[var(--text-muted)]">Content</span>
              </th>
              <th className="px-4 py-3 text-left">
                <SortHeader 
                  field="platform" 
                  currentField={sortField} 
                  direction={sortDirection} 
                  onSort={handleSort}
                >
                  Platform
                </SortHeader>
              </th>
              <th className="px-4 py-3 text-left">
                <SortHeader 
                  field="status" 
                  currentField={sortField} 
                  direction={sortDirection} 
                  onSort={handleSort}
                >
                  Status
                </SortHeader>
              </th>
              <th className="px-4 py-3 text-right">
                <span className="text-xs font-medium text-[var(--text-muted)]">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]">
            {sortedPosts.map((post) => {
              const scheduled = formatDateTime(post.scheduledAt);
              
              return (
                <tr key={post.id} className="hover:bg-[var(--surface)]/50">
                  <td className="px-4 py-4">
                    <div className="flex flex-col gap-0.5">
                      <span className="text-sm font-medium text-[var(--text)]">
                        {scheduled.date}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                        <Clock className="h-3 w-3" />
                        {scheduled.time}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <p className="max-w-xs truncate text-sm text-[var(--text)]" title={post.content}>
                      {post.content}
                    </p>
                  </td>
                  <td className="px-4 py-4">
                    <PlatformBadge platform={post.platform} />
                  </td>
                  <td className="px-4 py-4">
                    <StatusBadge status={post.status} />
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onEdit(post)}
                        className="rounded-lg p-2 text-[var(--text-muted)] hover:bg-[var(--primary)]/10 hover:text-[var(--primary)] cursor-pointer"
                        style={{ transitionDuration: 'var(--duration-fast)' }}
                        title="Edit post"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDelete(post)}
                        className="rounded-lg p-2 text-[var(--text-muted)] hover:bg-[var(--destructive)]/10 hover:text-[var(--destructive)] cursor-pointer"
                        style={{ transitionDuration: 'var(--duration-fast)' }}
                        title="Cancel post"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
