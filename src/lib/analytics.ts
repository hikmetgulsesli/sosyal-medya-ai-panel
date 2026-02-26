import type { AnalyticsResponse } from "@/types/analytics";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchAnalyticsOverview(token: string): Promise<AnalyticsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analytics/overview`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch analytics: ${response.statusText}`);
  }

  return response.json();
}

// Mock data for development/demo
export function getMockAnalyticsData(): AnalyticsResponse {
  const today = new Date();
  const followerGrowth: { date: string; followers: number }[] = [];
  
  for (let i = 29; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    followerGrowth.push({
      date: date.toISOString().split("T")[0],
      followers: 12500 + Math.floor(Math.random() * 500) + (30 - i) * 15,
    });
  }

  return {
    overview: {
      totalPosts: 2847,
      avgEngagement: 4.8,
      followerCount: 14532,
      followerGrowth: 12.5,
    },
    followerGrowth,
    recentPosts: [
      {
        id: "1",
        content: "Just launched our new AI-powered analytics feature! 🚀 Check out how we're helping brands understand their social media performance better than ever.",
        platform: "twitter",
        postedAt: "2026-02-26T08:30:00Z",
        likes: 234,
        replies: 45,
        shares: 89,
        engagementRate: 5.2,
      },
      {
        id: "2",
        content: "5 tips for optimizing your LinkedIn content strategy in 2026. Thread below 👇",
        platform: "linkedin",
        postedAt: "2026-02-25T14:00:00Z",
        likes: 567,
        replies: 78,
        shares: 123,
        engagementRate: 6.8,
      },
      {
        id: "3",
        content: "Behind the scenes: How we built our smart scheduling algorithm to find the perfect posting times.",
        platform: "instagram",
        postedAt: "2026-02-24T16:45:00Z",
        likes: 892,
        replies: 34,
        shares: 156,
        engagementRate: 4.1,
      },
      {
        id: "4",
        content: "The future of social media management is here. AI + human creativity = unbeatable results.",
        platform: "bluesky",
        postedAt: "2026-02-23T10:15:00Z",
        likes: 145,
        replies: 23,
        shares: 67,
        engagementRate: 3.9,
      },
      {
        id: "5",
        content: "Case study: How @TechStartup increased their engagement by 340% using our platform.",
        platform: "twitter",
        postedAt: "2026-02-22T09:00:00Z",
        likes: 456,
        replies: 89,
        shares: 234,
        engagementRate: 7.5,
      },
    ],
    platformMetrics: [
      { platform: "Twitter/X", posts: 1245, engagement: 5.2, followers: 8234 },
      { platform: "LinkedIn", posts: 567, engagement: 6.8, followers: 3456 },
      { platform: "Instagram", posts: 892, engagement: 4.1, followers: 2341 },
      { platform: "Bluesky", posts: 143, engagement: 3.9, followers: 501 },
    ],
  };
}
