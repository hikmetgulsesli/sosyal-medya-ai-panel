'use client';

import { useState, useMemo, useCallback } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import {
  CalendarView,
  PostsList,
  CreatePostModal,
  EditPostModal,
  DeleteConfirmationModal,
} from '@/components/scheduler';
import {
  ScheduledPost,
  CreatePostInput,
  UpdatePostInput,
  PostStatus,
} from '@/types/scheduler.js';
import { Plus, Calendar, List, Filter } from 'lucide-react';

// Mock data for demonstration
const mockPosts: ScheduledPost[] = [
  {
    id: '1',
    content: 'Check out our latest AI features that are transforming social media management! #AI #SocialMedia',
    platform: 'twitter',
    status: 'scheduled',
    scheduledAt: new Date(Date.now() + 86400000 * 2).toISOString(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '2',
    content: 'How AI is transforming the way businesses approach social media marketing. Read our latest insights.',
    platform: 'linkedin',
    status: 'scheduled',
    scheduledAt: new Date(Date.now() + 86400000 * 3).toISOString(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '3',
    content: 'Behind the scenes of building the most advanced social media AI panel.',
    platform: 'instagram',
    status: 'draft',
    scheduledAt: new Date(Date.now() + 86400000 * 5).toISOString(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '4',
    content: 'Just published a new blog post about AI-powered content scheduling!',
    platform: 'bluesky',
    status: 'published',
    scheduledAt: new Date(Date.now() - 86400000).toISOString(),
    publishedAt: new Date(Date.now() - 86400000).toISOString(),
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: '5',
    content: 'New thread about the future of AI in social media management.',
    platform: 'twitter',
    status: 'failed',
    scheduledAt: new Date(Date.now() - 172800000).toISOString(),
    createdAt: new Date(Date.now() - 259200000).toISOString(),
    updatedAt: new Date(Date.now() - 172800000).toISOString(),
  },
  {
    id: '6',
    content: 'Join us for a webinar on AI-powered social media strategies next week!',
    platform: 'linkedin',
    status: 'scheduled',
    scheduledAt: new Date(Date.now() + 86400000 * 7).toISOString(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '7',
    content: 'Tips for maximizing engagement with AI-generated content.',
    platform: 'twitter',
    status: 'scheduled',
    scheduledAt: new Date(Date.now() + 86400000).toISOString(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

type ViewMode = 'calendar' | 'list';
type StatusFilter = 'all' | PostStatus;

export default function SchedulerPage() {
  const [posts, setPosts] = useState<ScheduledPost[]>(mockPosts);
  const [viewMode, setViewMode] = useState<ViewMode>('calendar');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  
  // Modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [editingPost, setEditingPost] = useState<ScheduledPost | null>(null);
  const [deletingPost, setDeletingPost] = useState<ScheduledPost | null>(null);

  // Filter posts by status
  const filteredPosts = useMemo(() => {
    if (statusFilter === 'all') return posts;
    return posts.filter((post) => post.status === statusFilter);
  }, [posts, statusFilter]);

  // Stats
  const stats = useMemo(() => {
    return {
      total: posts.length,
      scheduled: posts.filter((p) => p.status === 'scheduled').length,
      published: posts.filter((p) => p.status === 'published').length,
      failed: posts.filter((p) => p.status === 'failed').length,
    };
  }, [posts]);

  // Handlers
  const handleCreatePost = useCallback((input: CreatePostInput) => {
    const newPost: ScheduledPost = {
      id: Math.random().toString(36).substring(7),
      content: input.content,
      platform: input.platform,
      status: 'scheduled',
      scheduledAt: input.scheduledAt,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setPosts((prev) => [...prev, newPost]);
  }, []);

  const handleUpdatePost = useCallback((input: UpdatePostInput) => {
    setPosts((prev) =>
      prev.map((post) =>
        post.id === input.id
          ? {
              ...post,
              ...(input.content && { content: input.content }),
              ...(input.platform && { platform: input.platform }),
              ...(input.scheduledAt && { scheduledAt: input.scheduledAt }),
              ...(input.status && { status: input.status }),
              updatedAt: new Date().toISOString(),
            }
          : post
      )
    );
    setEditingPost(null);
  }, []);

  const handleDeletePost = useCallback((postId: string) => {
    setPosts((prev) => prev.filter((post) => post.id !== postId));
    setDeletingPost(null);
  }, []);

  const handleEditClick = useCallback((post: ScheduledPost) => {
    setEditingPost(post);
    setIsEditModalOpen(true);
  }, []);

  const handleDeleteClick = useCallback((post: ScheduledPost) => {
    setDeletingPost(post);
    setIsDeleteModalOpen(true);
  }, []);

  const handleSelectDate = useCallback((date: Date) => {
    setSelectedDate(date);
    setIsCreateModalOpen(true);
  }, []);

  return (
    <ProtectedRoute>
      <DashboardLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-[var(--text)]">Post Scheduler</h1>
              <p className="mt-1 text-[var(--text-muted)]">
                Plan, schedule, and manage your social media content calendar.
              </p>
            </div>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="flex items-center justify-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--primary-hover)] cursor-pointer"
              style={{ transitionDuration: 'var(--duration-normal)' }}
            >
              <Plus className="h-4 w-4" />
              New Post
            </button>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
              <p className="text-sm text-[var(--text-muted)]">Total Posts</p>
              <p className="mt-1 text-2xl font-bold text-[var(--text)]">{stats.total}</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
              <p className="text-sm text-[var(--text-muted)]">Scheduled</p>
              <div className="mt-1 flex items-center gap-2">
                <p className="text-2xl font-bold text-[var(--text)]">{stats.scheduled}</p>
                <span className="h-2 w-2 rounded-full bg-blue-500" />
              </div>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
              <p className="text-sm text-[var(--text-muted)]">Published</p>
              <div className="mt-1 flex items-center gap-2">
                <p className="text-2xl font-bold text-[var(--text)]">{stats.published}</p>
                <span className="h-2 w-2 rounded-full bg-green-500" />
              </div>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
              <p className="text-sm text-[var(--text-muted)]">Failed</p>
              <div className="mt-1 flex items-center gap-2">
                <p className="text-2xl font-bold text-[var(--text)]">{stats.failed}</p>
                <span className="h-2 w-2 rounded-full bg-red-500" />
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            {/* View Toggle */}
            <div className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--card)] p-1">
              <button
                onClick={() => setViewMode('calendar')}
                className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer ${
                  viewMode === 'calendar'
                    ? 'bg-[var(--primary)] text-white'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)]'
                }`}
                style={{ transitionDuration: 'var(--duration-fast)' }}
              >
                <Calendar className="h-4 w-4" />
                Calendar
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors cursor-pointer ${
                  viewMode === 'list'
                    ? 'bg-[var(--primary)] text-white'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)]'
                }`}
                style={{ transitionDuration: 'var(--duration-fast)' }}
              >
                <List className="h-4 w-4" />
                List
              </button>
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-[var(--text-muted)]" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--text)] focus:border-[var(--primary)] focus:outline-none focus:ring-1 focus:ring-[var(--primary)] cursor-pointer"
              >
                <option value="all">All Status</option>
                <option value="scheduled">Scheduled</option>
                <option value="published">Published</option>
                <option value="failed">Failed</option>
                <option value="draft">Draft</option>
              </select>
            </div>
          </div>

          {/* Content */}
          {viewMode === 'calendar' ? (
            <CalendarView
              posts={filteredPosts}
              currentDate={currentDate}
              onDateChange={setCurrentDate}
              onSelectDate={handleSelectDate}
              selectedDate={selectedDate}
            />
          ) : (
            <PostsList
              posts={filteredPosts}
              onEdit={handleEditClick}
              onDelete={handleDeleteClick}
            />
          )}
        </div>

        {/* Modals */}
        <CreatePostModal
          isOpen={isCreateModalOpen}
          onClose={() => {
            setIsCreateModalOpen(false);
            setSelectedDate(null);
          }}
          onCreate={handleCreatePost}
          initialDate={selectedDate || undefined}
        />

        <EditPostModal
          key={editingPost?.id || 'new'}
          post={editingPost}
          isOpen={isEditModalOpen}
          onClose={() => {
            setIsEditModalOpen(false);
            setEditingPost(null);
          }}
          onUpdate={handleUpdatePost}
        />

        <DeleteConfirmationModal
          post={deletingPost}
          isOpen={isDeleteModalOpen}
          onClose={() => {
            setIsDeleteModalOpen(false);
            setDeletingPost(null);
          }}
          onConfirm={handleDeletePost}
        />
      </DashboardLayout>
    </ProtectedRoute>
  );
}
