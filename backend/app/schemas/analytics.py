from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# Analytics Event schemas
class AnalyticsEventCreate(BaseModel):
    post_id: str
    event_type: str = Field(..., max_length=50, description="Type of event: view, like, retweet, reply, share")
    metric_name: str = Field(..., max_length=50, description="Name of the metric being tracked")
    metric_value: int = Field(..., ge=0, description="Value of the metric")


class AnalyticsEventResponse(BaseModel):
    id: str
    post_id: str
    event_type: str
    metric_name: str
    metric_value: int
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Post metrics schema
class PostMetricsResponse(BaseModel):
    post_id: str
    external_id: str
    content: Optional[str] = None
    platform_name: str
    competitor_username: str
    
    # Engagement metrics
    total_views: int
    total_likes: int
    total_retweets: int
    total_replies: int
    total_shares: int
    
    # Calculated metrics
    engagement_rate: float
    viral_score: Optional[float] = None
    is_viral: bool
    
    # Time series data (last 30 days)
    daily_metrics: List[dict]
    
    # Growth metrics
    likes_growth_7d: float
    likes_growth_30d: float
    
    created_at: datetime
    posted_at: datetime


# Dashboard overview schemas
class PlatformStats(BaseModel):
    platform_id: str
    platform_name: str
    total_posts: int
    total_likes: int
    total_retweets: int
    total_replies: int
    avg_engagement_rate: float


class GrowthMetrics(BaseModel):
    period: str  # '7d', '30d', '90d'
    follower_growth: float
    follower_growth_percent: float
    engagement_growth: float
    engagement_growth_percent: float
    posts_count: int


class TopPerformingPost(BaseModel):
    post_id: str
    external_id: str
    content_preview: str
    platform_name: str
    competitor_username: str
    total_engagement: int
    engagement_rate: float
    viral_score: float
    posted_at: datetime


class DashboardOverviewResponse(BaseModel):
    # Summary stats
    total_posts_tracked: int
    total_competitors: int
    total_platforms: int
    
    # Engagement totals
    total_likes: int
    total_retweets: int
    total_replies: int
    total_shares: int
    total_views: int
    
    # Average metrics
    avg_engagement_rate: float
    avg_viral_score: float
    viral_posts_count: int
    
    # Platform breakdown
    platform_stats: List[PlatformStats]
    
    # Growth trends
    growth_metrics: List[GrowthMetrics]
    
    # Top performing content
    top_posts: List[TopPerformingPost]
    
    # Recent activity (last 7 days)
    recent_events_count: int
    
    # Time range for data
    date_from: datetime
    date_to: datetime


# Track event response
class TrackEventResponse(BaseModel):
    success: bool
    event_id: str
    message: str


# Analytics query parameters
class AnalyticsQueryParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    platform_id: Optional[str] = None
    competitor_id: Optional[str] = None
