export interface AnalyticsOverview {
  totalPosts: number;
  avgEngagement: number;
  followerCount: number;
  followerGrowth: number;
}

export interface FollowerDataPoint {
  date: string;
  followers: number;
}

export interface RecentPost {
  id: string;
  content: string;
  platform: "twitter" | "linkedin" | "instagram" | "bluesky";
  postedAt: string;
  likes: number;
  replies: number;
  shares: number;
  engagementRate: number;
}

export interface PlatformMetrics {
  platform: string;
  posts: number;
  engagement: number;
  followers: number;
}

export interface AnalyticsResponse {
  overview: AnalyticsOverview;
  followerGrowth: FollowerDataPoint[];
  recentPosts: RecentPost[];
  platformMetrics: PlatformMetrics[];
}
