from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    """Schema for creating an analytics event."""
    post_id: str
    event_type: str = Field(..., max_length=50, description="Type of event: view, like, retweet, reply, share")
    metric_name: str = Field(..., max_length=50, description="Name of the metric being tracked")
    metric_value: int = Field(..., ge=0, description="Value of the metric")


class AnalyticsEventResponse(BaseModel):
    """Schema for analytics event response."""
    id: str
    post_id: str
    event_type: str
    metric_name: str
    metric_value: int
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PostMetricsResponse(BaseModel):
    """Schema for post-specific metrics."""
    post_id: str
    external_id: Optional[str] = None
    content: Optional[str] = None
    platform_name: Optional[str] = None
    competitor_username: Optional[str] = None
    
    # Current metrics
    like_count: int = 0
    reply_count: int = 0
    repost_count: int = 0
    view_count: Optional[int] = None
    share_count: int = 0
    
    # Calculated metrics
    total_engagement: int = 0
    engagement_rate: float = 0.0
    
    # Events history
    events: List[AnalyticsEventResponse] = []
    
    # Timestamps
    posted_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None


class GrowthMetrics(BaseModel):
    """Schema for growth metrics over time."""
    period: str  # e.g., "7d", "30d", "90d"
    follower_delta: int
    follower_growth_rate: float
    post_count: int
    avg_engagement_rate: float
    total_likes: int
    total_replies: int
    total_reposts: int


class PlatformOverview(BaseModel):
    """Schema for platform-specific overview."""
    platform_id: str
    platform_name: str
    total_posts: int
    total_competitors: int
    avg_engagement_rate: float
    top_performing_posts: List[dict] = []


class DashboardOverviewResponse(BaseModel):
    """Schema for dashboard overview."""
    user_id: str
    
    # Overall stats
    total_posts_tracked: int
    total_competitors: int
    total_platforms: int
    
    # Engagement totals
    total_likes: int
    total_replies: int
    total_reposts: int
    total_shares: int
    total_views: int
    
    # Growth metrics
    growth_7d: Optional[GrowthMetrics] = None
    growth_30d: Optional[GrowthMetrics] = None
    growth_90d: Optional[GrowthMetrics] = None
    
    # Platform breakdown
    platform_overviews: List[PlatformOverview] = []
    
    # Recent activity
    recent_events: List[AnalyticsEventResponse] = []
    
    # Top content
    top_posts: List[PostMetricsResponse] = []
    
    # Timestamps
    generated_at: datetime


class TrackEventResponse(BaseModel):
    """Schema for track event response."""
    success: bool
    event_id: str
    message: str


class DateRangeFilter(BaseModel):
    """Schema for date range filtering."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
