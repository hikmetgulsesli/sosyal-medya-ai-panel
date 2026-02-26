export type Platform = "twitter" | "linkedin" | "instagram" | "bluesky";

export interface Competitor {
  id: string;
  user_id: string;
  platform_id: string;
  platform?: {
    id: string;
    name: string;
    display_name: string;
  };
  username: string;
  display_name: string | null;
  profile_url: string | null;
  follower_count: number | null;
  following_count: number | null;
  post_count: number | null;
  bio: string | null;
  is_active: boolean;
  last_scraped_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompetitorPost {
  id: string;
  competitor_id: string;
  platform_id: string;
  external_id: string;
  content: string | null;
  media_urls: string | null;
  posted_at: string;
  like_count: number;
  reply_count: number;
  repost_count: number;
  view_count: number | null;
  is_viral: boolean;
  viral_score: number | null;
  scraped_at: string;
  created_at: string;
  updated_at: string;
}

export interface CompetitorCreateInput {
  platform_id: string;
  username: string;
  display_name?: string;
  profile_url?: string;
}

export interface CompetitorUpdateInput {
  display_name?: string;
  profile_url?: string;
  is_active?: boolean;
}

export interface ScrapedPost {
  id: string;
  text: string;
  author: string;
  author_handle: string;
  created_at: string;
  like_count: number;
  reply_count: number;
  repost_count: number;
  view_count: number | null;
  media_urls: string[];
  is_reply: boolean;
  is_retweet: boolean;
  scraped_at: string;
}

export interface ScrapingSyncResponse {
  status: string;
  handle: string;
  profile_synced: boolean;
  posts_synced: number;
  follower_count: number | null;
  synced_at: string;
}

export interface CompetitorWithPosts extends Competitor {
  posts: CompetitorPost[];
}

export const PLATFORM_CONFIG: Record<Platform, { name: string; icon: string; color: string; domain: string }> = {
  twitter: {
    name: "Twitter/X",
    icon: "twitter",
    color: "#000000",
    domain: "x.com",
  },
  linkedin: {
    name: "LinkedIn",
    icon: "linkedin",
    color: "#0A66C2",
    domain: "linkedin.com",
  },
  instagram: {
    name: "Instagram",
    icon: "instagram",
    color: "#E4405F",
    domain: "instagram.com",
  },
  bluesky: {
    name: "Bluesky",
    icon: "cloud",
    color: "#0085FF",
    domain: "bsky.app",
  },
};
