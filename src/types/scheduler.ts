export type PostStatus = 'scheduled' | 'published' | 'failed' | 'draft';

export type Platform = 'twitter' | 'linkedin' | 'instagram' | 'bluesky';

export interface ScheduledPost {
  id: string;
  content: string;
  platform: Platform;
  status: PostStatus;
  scheduledAt: string;
  publishedAt?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreatePostInput {
  content: string;
  platform: Platform;
  scheduledAt: string;
}

export interface UpdatePostInput {
  id: string;
  content?: string;
  platform?: Platform;
  scheduledAt?: string;
  status?: PostStatus;
}

export interface PostsByDate {
  [date: string]: ScheduledPost[];
}

export const PLATFORM_LABELS: Record<Platform, string> = {
  twitter: 'Twitter/X',
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  bluesky: 'Bluesky',
};

// CamelCase aliases for convenience
export const PlatformLabels = PLATFORM_LABELS;

export const PLATFORM_COLORS: Record<Platform, string> = {
  twitter: '#0ea5e9',
  linkedin: '#0a66c2',
  instagram: '#e4405f',
  bluesky: '#0560ff',
};

// CamelCase aliases for convenience
export const PlatformColors = PLATFORM_COLORS;

export const STATUS_LABELS: Record<PostStatus, string> = {
  scheduled: 'Scheduled',
  published: 'Published',
  failed: 'Failed',
  draft: 'Draft',
};

// CamelCase aliases for convenience
export const StatusLabels = STATUS_LABELS;

export const STATUS_COLORS: Record<PostStatus, { bg: string; text: string; dot: string }> = {
  scheduled: { bg: 'bg-blue-500/10', text: 'text-blue-500', dot: 'bg-blue-500' },
  published: { bg: 'bg-green-500/10', text: 'text-green-500', dot: 'bg-green-500' },
  failed: { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500' },
  draft: { bg: 'bg-gray-500/10', text: 'text-gray-500', dot: 'bg-gray-500' },
};

// CamelCase aliases for convenience
export const StatusColors = STATUS_COLORS;
