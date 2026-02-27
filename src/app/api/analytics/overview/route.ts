import { NextResponse } from "next/server";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4522/api";

export async function GET(request: Request) {
  try {
    const authHeader = request.headers.get("authorization");
    if (!authHeader) {
      return NextResponse.json(
        { error: { code: "UNAUTHORIZED", message: "Authentication required" } },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const days = searchParams.get("days") || "30";

    const res = await fetch(`${API_BASE_URL}/analytics/overview?days=${days}`, {
      headers: { Authorization: authHeader },
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to fetch analytics" }));
      return NextResponse.json(
        { error: { code: "API_ERROR", message: err.detail || "Analytics fetch failed" } },
        { status: res.status }
      );
    }

    const raw = await res.json();

    // Transform backend schema to frontend AnalyticsOverview schema
    const transformed = {
      total_posts: raw.total_posts_tracked ?? raw.total_posts ?? 0,
      published_posts: raw.published_posts ?? raw.total_posts_tracked ?? 0,
      avg_engagement_rate: raw.avg_engagement_rate ?? 0,
      total_followers: raw.total_followers ?? 0,
      follower_growth: Array.isArray(raw.follower_growth) ? raw.follower_growth : [],
      platform_metrics: Array.isArray(raw.platform_stats)
        ? raw.platform_stats.map((s: Record<string, unknown>) => ({
            platform: s.platform ?? s.name ?? "unknown",
            followers: s.followers ?? s.follower_count ?? 0,
            engagement_rate: s.engagement_rate ?? s.avg_engagement ?? 0,
            posts: s.posts ?? s.post_count ?? 0,
          }))
        : Array.isArray(raw.platform_metrics)
          ? raw.platform_metrics
          : [],
      recent_posts: Array.isArray(raw.top_posts)
        ? raw.top_posts.map((p: Record<string, unknown>) => ({
            id: p.id ?? p.post_id ?? String(Math.random()),
            content: p.content ?? p.text ?? "",
            platform: p.platform ?? "",
            status: p.status ?? "published",
            scheduled_at: p.scheduled_at ?? null,
            published_at: p.published_at ?? p.created_at ?? null,
            likes: p.likes ?? p.total_likes ?? 0,
            replies: p.replies ?? p.total_replies ?? 0,
            reposts: p.reposts ?? p.total_retweets ?? 0,
            engagement_rate: p.engagement_rate ?? 0,
          }))
        : Array.isArray(raw.recent_posts)
          ? raw.recent_posts
          : [],
    };

    return NextResponse.json(transformed);
  } catch {
    return NextResponse.json(
      { error: { code: "INTERNAL_ERROR", message: "An unexpected error occurred" } },
      { status: 500 }
    );
  }
}
