from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    PostMetricsResponse,
    DashboardOverviewResponse,
    TrackEventResponse,
    DateRangeFilter
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/track", response_model=TrackEventResponse)
def track_analytics_event(
    event: AnalyticsEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Track a new analytics event for a post.
    
    - **post_id**: ID of the post being tracked
    - **event_type**: Type of event (view, like, retweet, reply, share)
    - **metric_name**: Name of the metric
    - **metric_value**: Value to add to the metric
    """
    try:
        tracked_event = AnalyticsService.track_event(
            db=db,
            post_id=event.post_id,
            event_type=event.event_type,
            metric_name=event.metric_name,
            metric_value=event.metric_value
        )
        
        return TrackEventResponse(
            success=True,
            event_id=tracked_event.id,
            message=f"Event tracked successfully: {event.event_type} - {event.metric_name}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "TRACKING_ERROR",
                    "message": f"Failed to track event: {str(e)}"
                }
            }
        )


@router.get("/posts/{post_id}", response_model=PostMetricsResponse)
def get_post_metrics(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics metrics for a specific post.
    
    Returns detailed metrics including:
    - Current engagement counts (likes, replies, reposts, views)
    - Calculated engagement rate
    - Event history
    """
    metrics = AnalyticsService.get_post_metrics(db, post_id)
    
    if not metrics:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Post with id {post_id} not found"
                }
            }
        )
    
    return PostMetricsResponse(**metrics)


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive dashboard overview for the current user.
    
    Returns:
    - Total posts tracked
    - Total competitors and platforms
    - Engagement totals (likes, replies, reposts, shares, views)
    - Growth metrics for 7d, 30d, and 90d periods
    - Platform breakdowns
    - Recent activity
    - Top performing posts
    """
    overview = AnalyticsService.get_dashboard_overview(db, current_user.id)
    
    return DashboardOverviewResponse(**overview)


@router.get("/posts/{post_id}/events", response_model=list[AnalyticsEventResponse])
def get_post_events(
    post_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=100, description="Number of events to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics events for a specific post.
    
    - **post_id**: ID of the post
    - **event_type**: Optional filter by event type
    - **limit**: Maximum number of events to return (1-100)
    """
    from sqlalchemy import desc
    from app.models.models import AnalyticsEvent
    
    query = db.query(AnalyticsEvent).filter(AnalyticsEvent.post_id == post_id)
    
    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)
    
    events = query.order_by(desc(AnalyticsEvent.recorded_at)).limit(limit).all()
    
    return [AnalyticsEventResponse.model_validate(e) for e in events]
