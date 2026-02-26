export interface FollowerGrowthPoint {
  date: string;
  followers: number;
}

export interface PlatformMetric {
  platform: string;
  followers: number;
  engagement_rate: number;
  posts: number;
}

export interface RecentPostMetric {
  id: string;
  content: string;
  platform: string;
  status: string;
  scheduled_at: string | null;
  published_at: string | null;
  likes: number;
  replies: number;
  reposts: number;
  engagement_rate: number;
}

export interface AnalyticsOverview {
  total_posts: number;
  published_posts: number;
  avg_engagement_rate: number;
  total_followers: number;
  follower_growth: FollowerGrowthPoint[];
  platform_metrics: PlatformMetric[];
  recent_posts: RecentPostMetric[];
}
