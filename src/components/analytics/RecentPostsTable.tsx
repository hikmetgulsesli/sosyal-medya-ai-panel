"use client";

import { Twitter, Linkedin, Instagram, Cloud, Heart, MessageCircle, Share2 } from "lucide-react";
import type { RecentPost } from "@/types/analytics";

interface RecentPostsTableProps {
  posts: RecentPost[];
}

const platformIcons: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  twitter: { icon: <Twitter className="h-4 w-4" />, color: "#0ea5e9", label: "Twitter/X" },
  linkedin: { icon: <Linkedin className="h-4 w-4" />, color: "#0077b5", label: "LinkedIn" },
  instagram: { icon: <Instagram className="h-4 w-4" />, color: "#f472b6", label: "Instagram" },
  bluesky: { icon: <Cloud className="h-4 w-4" />, color: "#3b82f6", label: "Bluesky" },
};

export function RecentPostsTable({ posts }: RecentPostsTableProps) {
  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const truncateContent = (content: string, maxLength = 60) => {
    if (content.length <= maxLength) return content;
    return `${content.slice(0, maxLength)}...`;
  };

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
      <h3 className="text-lg font-semibold text-[var(--text)]">Recent Posts</h3>
      <p className="text-sm text-[var(--text-muted)]">Latest activity across platforms</p>
      <div className="mt-6 overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[var(--border)]">
              <th className="pb-3 text-left text-sm font-medium text-[var(--text-muted)]">Post</th>
              <th className="pb-3 text-left text-sm font-medium text-[var(--text-muted)]">Platform</th>
              <th className="pb-3 text-right text-sm font-medium text-[var(--text-muted)]">Engagement</th>
              <th className="pb-3 text-right text-sm font-medium text-[var(--text-muted)]">Rate</th>
            </tr>
          </thead>
          <tbody>
            {posts.map((post) => {
              const platform = platformIcons[post.platform];
              return (
                <tr
                  key={post.id}
                  className="border-b border-[var(--border-subtle)] last:border-0 transition-colors hover:bg-[var(--secondary)] cursor-pointer"
                >
                  <td className="py-4">
                    <div>
                      <p className="max-w-[200px] text-sm text-[var(--text)]">
                        {truncateContent(post.content)}
                      </p>
                      <p className="text-xs text-[var(--text-muted)]">{formatDate(post.postedAt)}</p>
                    </div>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-2">
                      <span style={{ color: platform?.color || "var(--primary)" }}>
                        {platform?.icon || <Cloud className="h-4 w-4" />}
                      </span>
                      <span className="text-sm text-[var(--text)]">
                        {platform?.label || post.platform}
                      </span>
                    </div>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center justify-end gap-3">
                      <span className="flex items-center gap-1 text-sm text-[var(--text-muted)]">
                        <Heart className="h-3.5 w-3.5" />
                        {formatNumber(post.likes)}
                      </span>
                      <span className="flex items-center gap-1 text-sm text-[var(--text-muted)]">
                        <MessageCircle className="h-3.5 w-3.5" />
                        {formatNumber(post.replies)}
                      </span>
                      <span className="flex items-center gap-1 text-sm text-[var(--text-muted)]">
                        <Share2 className="h-3.5 w-3.5" />
                        {formatNumber(post.shares)}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 text-right">
                    <span className="inline-flex items-center rounded-full bg-[var(--success)]/10 px-2.5 py-1 text-sm font-medium text-[var(--success)]">
                      {post.engagementRate}%
                    </span>
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
