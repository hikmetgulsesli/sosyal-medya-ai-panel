from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, Post, AnalyticsEvent, CompetitorProfile, Platform
from app.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    PostMetricsResponse,
    DashboardOverviewResponse,
    PlatformStats,
    GrowthMetrics,
    TopPerformingPost,
    TrackEventResponse
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/track", response_model=TrackEventResponse, status_code=status.HTTP_201_CREATED)
def track_event(
    event_data: AnalyticsEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track a post analytics event (view, like, retweet, reply, share)."""
    # Verify post exists
    post = db.query(Post).filter(Post.id == event_data.post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Create analytics event
    analytics_event = AnalyticsEvent(
        post_id=event_data.post_id,
        event_type=event_data.event_type,
        metric_name=event_data.metric_name,
        metric_value=event_data.metric_value
    )
    
    db.add(analytics_event)
    db.commit()
    db.refresh(analytics_event)
    
    # Update post metrics based on event type
    if event_data.event_type == "like":
        post.like_count += event_data.metric_value
    elif event_data.event_type == "reply":
        post.reply_count += event_data.metric_value
    elif event_data.event_type == "retweet":
        post.repost_count += event_data.metric_value
    elif event_data.event_type == "view":
        if post.view_count is None:
            post.view_count = 0
        post.view_count += event_data.metric_value
    
    post.updated_at = datetime.utcnow()
    db.commit()
    
    return TrackEventResponse(
        success=True,
        event_id=analytics_event.id,
        message=f"Event '{event_data.event_type}' tracked successfully"
    )


@router.get("/posts/{post_id}", response_model=PostMetricsResponse)
def get_post_metrics(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed analytics metrics for a specific post."""
    # Get post with related data
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Get competitor and platform info
    competitor = db.query(CompetitorProfile).filter(
        CompetitorProfile.id == post.competitor_id
    ).first()
    
    platform = db.query(Platform).filter(
        Platform.id == post.platform_id
    ).first()
    
    # Aggregate analytics events by type
    analytics_summary = db.query(
        AnalyticsEvent.event_type,
        func.sum(AnalyticsEvent.metric_value).label("total_value")
    ).filter(
        AnalyticsEvent.post_id == post_id
    ).group_by(AnalyticsEvent.event_type).all()
    
    # Build metrics dictionary for shares (only tracked via events)
    metrics_dict = {event_type: int(total_value) for event_type, total_value in analytics_summary}
    
    # Use Post model counts as source of truth for current metrics
    total_views = post.view_count or 0
    total_likes = post.like_count
    total_retweets = post.repost_count
    total_replies = post.reply_count
    
    # Shares are only tracked via events, so get them from AnalyticsEvent
    total_shares = metrics_dict.get("share", 0)
    
    # Calculate engagement rate
    total_engagement = total_likes + total_retweets + total_replies + total_shares
    engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0.0
    
    # Get daily metrics for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_events = db.query(
        func.date(AnalyticsEvent.recorded_at).label("date"),
        AnalyticsEvent.event_type,
        func.sum(AnalyticsEvent.metric_value).label("total")
    ).filter(
        AnalyticsEvent.post_id == post_id,
        AnalyticsEvent.recorded_at >= thirty_days_ago
    ).group_by(
        func.date(AnalyticsEvent.recorded_at),
        AnalyticsEvent.event_type
    ).all()
    
    # Organize daily metrics
    daily_metrics_map = {}
    for date, event_type, total in daily_events:
        # Handle both string (SQLite) and date object (PostgreSQL)
        if isinstance(date, str):
            date_str = date
        else:
            date_str = date.isoformat()
        if date_str not in daily_metrics_map:
            daily_metrics_map[date_str] = {"date": date_str}
        daily_metrics_map[date_str][event_type] = int(total)
    
    daily_metrics = list(daily_metrics_map.values())
    
    # Calculate growth metrics
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Likes 7 days ago (approximate from events)
    likes_7d_ago = db.query(func.sum(AnalyticsEvent.metric_value)).filter(
        AnalyticsEvent.post_id == post_id,
        AnalyticsEvent.event_type == "like",
        AnalyticsEvent.recorded_at < seven_days_ago
    ).scalar() or 0
    
    likes_30d_ago = db.query(func.sum(AnalyticsEvent.metric_value)).filter(
        AnalyticsEvent.post_id == post_id,
        AnalyticsEvent.event_type == "like",
        AnalyticsEvent.recorded_at < thirty_days_ago
    ).scalar() or 0
    
    current_likes_from_events = metrics_dict.get("like", 0)
    
    likes_growth_7d = (current_likes_from_events - int(likes_7d_ago)) if likes_7d_ago > 0 else float(current_likes_from_events)
    likes_growth_30d = (current_likes_from_events - int(likes_30d_ago)) if likes_30d_ago > 0 else float(current_likes_from_events)
    
    return PostMetricsResponse(
        post_id=post.id,
        external_id=post.external_id,
        content=post.content,
        platform_name=platform.display_name if platform else "Unknown",
        competitor_username=competitor.username if competitor else "Unknown",
        total_views=total_views,
        total_likes=total_likes,
        total_retweets=total_retweets,
        total_replies=total_replies,
        total_shares=total_shares,
        engagement_rate=round(engagement_rate, 2),
        viral_score=post.viral_score,
        is_viral=post.is_viral,
        daily_metrics=daily_metrics,
        likes_growth_7d=float(likes_growth_7d),
        likes_growth_30d=float(likes_growth_30d),
        created_at=post.created_at,
        posted_at=post.posted_at
    )


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to include in overview"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard overview with aggregated analytics statistics."""
    date_from = datetime.utcnow() - timedelta(days=days)
    date_to = datetime.utcnow()
    
    # Get user's competitors
    user_competitor_ids = db.query(CompetitorProfile.id).filter(
        CompetitorProfile.user_id == current_user.id
    ).all()
    user_competitor_ids = [c[0] for c in user_competitor_ids]
    
    # Base query for posts
    posts_query = db.query(Post).filter(
        Post.competitor_id.in_(user_competitor_ids) if user_competitor_ids else False
    )
    
    # Summary stats
    total_posts_tracked = posts_query.count()
    total_competitors = len(user_competitor_ids)
    
    # Get all posts for this user
    user_posts = posts_query.all()
    post_ids = [p.id for p in user_posts]
    
    # Count only platforms that have posts from user's competitors
    user_platform_ids = set(p.platform_id for p in user_posts if p.platform_id)
    total_platforms = len(user_platform_ids) if user_platform_ids else 0
    
    # Calculate totals from post table (Post counts are source of truth for current metrics)
    total_likes = sum(p.like_count for p in user_posts)
    total_retweets = sum(p.repost_count for p in user_posts)
    total_replies = sum(p.reply_count for p in user_posts)
    total_views = sum(p.view_count or 0 for p in user_posts)
    
    # AnalyticsEvents are used for historical tracking only
    # Shares are only tracked via events (not in Post model), so include those
    total_shares = 0
    if post_ids:
        analytics_summary = db.query(
            AnalyticsEvent.event_type,
            func.sum(AnalyticsEvent.metric_value).label("total_value")
        ).filter(
            AnalyticsEvent.post_id.in_(post_ids),
            AnalyticsEvent.recorded_at >= date_from,
            AnalyticsEvent.event_type == "share"  # Only shares are not in Post model
        ).group_by(AnalyticsEvent.event_type).all()
        
        analytics_dict = {event_type: int(total_value) for event_type, total_value in analytics_summary}
        total_shares = analytics_dict.get("share", 0)
    
    # Calculate average engagement rate
    total_engagement = total_likes + total_retweets + total_replies + total_shares
    avg_engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0.0
    
    # Viral posts count
    viral_posts_count = sum(1 for p in user_posts if p.is_viral)
    avg_viral_score = sum(p.viral_score or 0 for p in user_posts) / len(user_posts) if user_posts else 0.0
    
    # Platform stats breakdown
    platform_stats = []
    platforms = db.query(Platform).filter(Platform.is_active == True).all()
    
    for platform in platforms:
        platform_posts = [p for p in user_posts if p.platform_id == platform.id]
        platform_post_ids = [p.id for p in platform_posts]
        
        if not platform_posts:
            continue
        
        # Use Post model counts as source of truth
        p_likes = sum(p.like_count for p in platform_posts)
        p_retweets = sum(p.repost_count for p in platform_posts)
        p_replies = sum(p.reply_count for p in platform_posts)
        p_views = sum(p.view_count or 0 for p in platform_posts)
        
        # Shares are only tracked via events, so include them
        p_shares = 0
        if platform_post_ids:
            p_analytics = db.query(
                AnalyticsEvent.event_type,
                func.sum(AnalyticsEvent.metric_value).label("total_value")
            ).filter(
                AnalyticsEvent.post_id.in_(platform_post_ids),
                AnalyticsEvent.recorded_at >= date_from,
                AnalyticsEvent.event_type == "share"
            ).group_by(AnalyticsEvent.event_type).all()
            
            p_analytics_dict = {event_type: int(total_value) for event_type, total_value in p_analytics}
            p_shares = p_analytics_dict.get("share", 0)
        
        p_total_engagement = p_likes + p_retweets + p_replies + p_shares
        p_views = sum(p.view_count or 0 for p in platform_posts)
        p_avg_engagement = (p_total_engagement / p_views * 100) if p_views > 0 else 0.0
        
        platform_stats.append(PlatformStats(
            platform_id=platform.id,
            platform_name=platform.display_name,
            total_posts=len(platform_posts),
            total_likes=p_likes,
            total_retweets=p_retweets,
            total_replies=p_replies,
            avg_engagement_rate=round(p_avg_engagement, 2)
        ))
    
    # Growth metrics for different periods
    growth_metrics = []
    for period_days in [7, 30, 90]:
        period_date = datetime.utcnow() - timedelta(days=period_days)
        
        # Count events in this period
        if post_ids:
            period_events = db.query(func.count(AnalyticsEvent.id)).filter(
                AnalyticsEvent.post_id.in_(post_ids),
                AnalyticsEvent.recorded_at >= period_date
            ).scalar() or 0
            
            period_engagement = db.query(func.sum(AnalyticsEvent.metric_value)).filter(
                AnalyticsEvent.post_id.in_(post_ids),
                AnalyticsEvent.recorded_at >= period_date,
                AnalyticsEvent.event_type.in_(["like", "retweet", "reply", "share"])
            ).scalar() or 0
        else:
            period_events = 0
            period_engagement = 0
        
        # Calculate growth (compare to previous period)
        prev_period_date = period_date - timedelta(days=period_days)
        
        if post_ids:
            prev_engagement = db.query(func.sum(AnalyticsEvent.metric_value)).filter(
                AnalyticsEvent.post_id.in_(post_ids),
                AnalyticsEvent.recorded_at >= prev_period_date,
                AnalyticsEvent.recorded_at < period_date,
                AnalyticsEvent.event_type.in_(["like", "retweet", "reply", "share"])
            ).scalar() or 0
        else:
            prev_engagement = 0
        
        engagement_growth = float(period_engagement) - float(prev_engagement)
        engagement_growth_percent = (
            (engagement_growth / float(prev_engagement) * 100) if prev_engagement > 0 
            else (100.0 if period_engagement > 0 else 0.0)
        )
        
        growth_metrics.append(GrowthMetrics(
            period=f"{period_days}d",
            follower_growth=0.0,  # Would need historical follower data
            follower_growth_percent=0.0,
            engagement_growth=engagement_growth,
            engagement_growth_percent=round(engagement_growth_percent, 2),
            posts_count=int(period_events)
        ))
    
    # Top performing posts
    top_posts = []
    if user_posts:
        # Sort by engagement (likes + retweets + replies)
        sorted_posts = sorted(
            user_posts,
            key=lambda p: p.like_count + p.repost_count + p.reply_count,
            reverse=True
        )[:5]  # Top 5
        
        for post in sorted_posts:
            competitor = db.query(CompetitorProfile).filter(
                CompetitorProfile.id == post.competitor_id
            ).first()
            
            platform = db.query(Platform).filter(
                Platform.id == post.platform_id
            ).first()
            
            total_eng = post.like_count + post.repost_count + post.reply_count
            views = post.view_count or 1
            eng_rate = (total_eng / views * 100)
            
            content_preview = post.content[:100] + "..." if post.content and len(post.content) > 100 else (post.content or "")
            
            top_posts.append(TopPerformingPost(
                post_id=post.id,
                external_id=post.external_id,
                content_preview=content_preview,
                platform_name=platform.display_name if platform else "Unknown",
                competitor_username=competitor.username if competitor else "Unknown",
                total_engagement=total_eng,
                engagement_rate=round(eng_rate, 2),
                viral_score=post.viral_score or 0.0,
                posted_at=post.posted_at
            ))
    
    # Recent events count (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    if post_ids:
        recent_events_count = db.query(func.count(AnalyticsEvent.id)).filter(
            AnalyticsEvent.post_id.in_(post_ids),
            AnalyticsEvent.recorded_at >= seven_days_ago
        ).scalar() or 0
    else:
        recent_events_count = 0
    
    return DashboardOverviewResponse(
        total_posts_tracked=total_posts_tracked,
        total_competitors=total_competitors,
        total_platforms=total_platforms,
        total_likes=total_likes,
        total_retweets=total_retweets,
        total_replies=total_replies,
        total_shares=total_shares,
        total_views=total_views,
        avg_engagement_rate=round(avg_engagement_rate, 2),
        avg_viral_score=round(avg_viral_score, 2),
        viral_posts_count=viral_posts_count,
        platform_stats=platform_stats,
        growth_metrics=growth_metrics,
        top_posts=top_posts,
        recent_events_count=int(recent_events_count),
        date_from=date_from,
        date_to=date_to
    )


@router.get("/events/{post_id}", response_model=List[AnalyticsEventResponse])
def get_post_events(
    post_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics events for a specific post (paginated)."""
    # Verify post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    # Build query
    query = db.query(AnalyticsEvent).filter(AnalyticsEvent.post_id == post_id)
    
    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)
    
    events = query.order_by(desc(AnalyticsEvent.recorded_at)).offset(offset).limit(limit).all()
    
    return events
