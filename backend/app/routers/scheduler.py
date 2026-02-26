"""Scheduler router for post scheduling and queue management."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
from typing import Optional, List

from app.db.database import get_db
from app.models.models import ScheduledPost, Platform as PlatformModel, User
from app.core.auth import get_current_user
from app.core.constants import Platform
from app.schemas.scheduler import (
    ScheduledPostCreate,
    ScheduledPostUpdate,
    ScheduledPostResponse,
    ScheduledPostListResponse,
    ScheduledPostInDB,
    PostStatus,
    Priority,
    QueueFilterParams,
    OptimalTimeRequest,
    OptimalTimeResponse,
    OptimalTimeSlot,
    PublishImmediatelyRequest,
    PublishResponse,
    QueueStats,
    QueueStatsResponse
)

router = APIRouter(prefix="/posts", tags=["scheduler"])


def scheduled_post_to_schema(post: ScheduledPost) -> ScheduledPostInDB:
    """Convert DB model to Pydantic schema."""
    media_urls = None
    if post.media_urls:
        media_urls = post.media_urls.split(",") if "," in post.media_urls else [post.media_urls]
    
    return ScheduledPostInDB(
        id=post.id,
        user_id=post.user_id,
        platform=Platform(post.platform.name.lower()) if post.platform else Platform.TWITTER,
        content=post.content,
        media_urls=media_urls,
        scheduled_at=post.scheduled_at,
        status=PostStatus(post.status),
        priority=Priority(getattr(post, 'priority', 2)),
        published_at=post.published_at,
        external_post_id=post.external_post_id,
        error_message=post.error_message,
        created_at=post.created_at,
        updated_at=post.updated_at
    )


@router.post("/schedule", response_model=ScheduledPostResponse, status_code=status.HTTP_201_CREATED)
def schedule_post(
    post_data: ScheduledPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule a new post for future publishing."""
    # Validate scheduled time is in the future
    if post_data.scheduled_at <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )
    
    # Get platform
    platform = db.query(PlatformModel).filter(
        PlatformModel.name == post_data.platform.value
    ).first()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{post_data.platform.value}' not found"
        )
    
    # Convert media_urls to string
    media_urls_str = ",".join(post_data.media_urls) if post_data.media_urls else None
    
    # Create scheduled post
    scheduled_post = ScheduledPost(
        user_id=current_user.id,
        platform_id=platform.id,
        content=post_data.content,
        media_urls=media_urls_str,
        scheduled_at=post_data.scheduled_at,
        status=PostStatus.PENDING.value
    )
    
    db.add(scheduled_post)
    db.commit()
    db.refresh(scheduled_post)
    
    return ScheduledPostResponse(data=scheduled_post_to_schema(scheduled_post))


@router.get("/queue", response_model=ScheduledPostListResponse)
def get_queue(
    status: Optional[str] = Query(None, description="Filter by status"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("scheduled_at", regex="^(scheduled_at|created_at|priority|status)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the queue of scheduled posts with filtering and sorting."""
    query = db.query(ScheduledPost).filter(ScheduledPost.user_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(ScheduledPost.status == status)
    
    if platform:
        platform_obj = db.query(PlatformModel).filter(PlatformModel.name == platform).first()
        if platform_obj:
            query = query.filter(ScheduledPost.platform_id == platform_obj.id)
    
    if from_date:
        query = query.filter(ScheduledPost.scheduled_at >= from_date)
    
    if to_date:
        query = query.filter(ScheduledPost.scheduled_at <= to_date)
    
    # Get total count for pagination
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(ScheduledPost, sort_by, ScheduledPost.scheduled_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Apply pagination
    posts = query.offset(offset).limit(limit).all()
    
    return ScheduledPostListResponse(
        data=[scheduled_post_to_schema(post) for post in posts],
        meta={
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }
    )


@router.get("/queue/stats", response_model=QueueStatsResponse)
def get_queue_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about the scheduled post queue."""
    # Count by status
    total_pending = db.query(ScheduledPost).filter(
        and_(ScheduledPost.user_id == current_user.id, ScheduledPost.status == PostStatus.PENDING.value)
    ).count()
    
    total_queued = db.query(ScheduledPost).filter(
        and_(ScheduledPost.user_id == current_user.id, ScheduledPost.status == PostStatus.QUEUED.value)
    ).count()
    
    total_published = db.query(ScheduledPost).filter(
        and_(ScheduledPost.user_id == current_user.id, ScheduledPost.status == PostStatus.PUBLISHED.value)
    ).count()
    
    total_failed = db.query(ScheduledPost).filter(
        and_(ScheduledPost.user_id == current_user.id, ScheduledPost.status == PostStatus.FAILED.value)
    ).count()
    
    # Count by platform
    by_platform = {}
    platforms = db.query(PlatformModel).all()
    for p in platforms:
        count = db.query(ScheduledPost).filter(
            and_(ScheduledPost.user_id == current_user.id, ScheduledPost.platform_id == p.id)
        ).count()
        by_platform[p.name] = count
    
    # Get upcoming posts (next 5)
    upcoming = db.query(ScheduledPost).filter(
        and_(
            ScheduledPost.user_id == current_user.id,
            ScheduledPost.status.in_([PostStatus.PENDING.value, PostStatus.QUEUED.value]),
            ScheduledPost.scheduled_at >= datetime.utcnow()
        )
    ).order_by(asc(ScheduledPost.scheduled_at)).limit(5).all()
    
    return QueueStatsResponse(
        data=QueueStats(
            total_pending=total_pending,
            total_queued=total_queued,
            total_published=total_published,
            total_failed=total_failed,
            by_platform=by_platform,
            upcoming_posts=[scheduled_post_to_schema(post) for post in upcoming]
        )
    )


@router.get("/{post_id}", response_model=ScheduledPostResponse)
def get_scheduled_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific scheduled post by ID."""
    post = db.query(ScheduledPost).filter(
        and_(ScheduledPost.id == post_id, ScheduledPost.user_id == current_user.id)
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    return ScheduledPostResponse(data=scheduled_post_to_schema(post))


@router.put("/{post_id}", response_model=ScheduledPostResponse)
def update_scheduled_post(
    post_id: str,
    post_data: ScheduledPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a scheduled post."""
    post = db.query(ScheduledPost).filter(
        and_(ScheduledPost.id == post_id, ScheduledPost.user_id == current_user.id)
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Can't update published posts
    if post.status == PostStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a published post"
        )
    
    # Update fields
    if post_data.content is not None:
        post.content = post_data.content
    
    if post_data.media_urls is not None:
        post.media_urls = ",".join(post_data.media_urls)
    
    if post_data.scheduled_at is not None:
        if post_data.scheduled_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled time must be in the future"
            )
        post.scheduled_at = post_data.scheduled_at
    
    if post_data.status is not None:
        post.status = post_data.status.value
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    
    return ScheduledPostResponse(data=scheduled_post_to_schema(post))


@router.put("/{post_id}/publish", response_model=PublishResponse)
def publish_immediately(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Publish a scheduled post immediately."""
    post = db.query(ScheduledPost).filter(
        and_(ScheduledPost.id == post_id, ScheduledPost.user_id == current_user.id)
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Can't republish already published posts
    if post.status == PostStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is already published"
        )
    
    # Simulate publishing (in production, this would call the platform API)
    post.status = PostStatus.PUBLISHED.value
    post.published_at = datetime.utcnow()
    post.external_post_id = f"simulated_{post.platform.name.lower()}_{post.id[:8]}"
    post.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(post)
    
    return PublishResponse(
        data=scheduled_post_to_schema(post),
        message="Post published successfully"
    )


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_scheduled_post(
    post_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel (delete) a scheduled post."""
    post = db.query(ScheduledPost).filter(
        and_(ScheduledPost.id == post_id, ScheduledPost.user_id == current_user.id)
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Can't cancel published posts
    if post.status == PostStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a published post"
        )
    
    # Soft delete - mark as cancelled instead of removing
    post.status = PostStatus.CANCELLED.value
    post.updated_at = datetime.utcnow()
    db.commit()
    
    return None


@router.post("/optimal-times", response_model=OptimalTimeResponse)
def get_optimal_times(
    request: OptimalTimeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get optimal posting time suggestions based on historical engagement."""
    # This is a simplified implementation
    # In production, this would analyze historical data and platform algorithms
    
    now = datetime.utcnow()
    suggestions = []
    
    # Generate suggestions for the next 3 days
    for day_offset in range(3):
        base_date = now + timedelta(days=day_offset)
        
        # Morning slot (9 AM)
        morning = base_date.replace(hour=9, minute=0, second=0, microsecond=0)
        if morning > now:
            suggestions.append(OptimalTimeSlot(
                suggested_time=morning,
                expected_engagement_score=75.0 + (day_offset * -5),
                reason="Morning engagement peak - users checking updates"
            ))
        
        # Lunch slot (12 PM)
        lunch = base_date.replace(hour=12, minute=0, second=0, microsecond=0)
        if lunch > now:
            suggestions.append(OptimalTimeSlot(
                suggested_time=lunch,
                expected_engagement_score=85.0 + (day_offset * -5),
                reason="Lunch break - high activity period"
            ))
        
        # Evening slot (6 PM)
        evening = base_date.replace(hour=18, minute=0, second=0, microsecond=0)
        if evening > now:
            suggestions.append(OptimalTimeSlot(
                suggested_time=evening,
                expected_engagement_score=90.0 + (day_offset * -5),
                reason="Evening peak - highest engagement window"
            ))
    
    # Sort by engagement score (descending)
    suggestions.sort(key=lambda x: x.expected_engagement_score, reverse=True)
    
    # Return top 5 suggestions
    return OptimalTimeResponse(
        data=suggestions[:5],
        platform=request.platform,
        timezone="UTC"
    )


@router.post("/publish-now", response_model=PublishResponse, status_code=status.HTTP_201_CREATED)
def publish_now(
    request: PublishImmediatelyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and publish a post immediately without scheduling."""
    # Get platform
    platform = db.query(PlatformModel).filter(
        PlatformModel.name == request.platform.value
    ).first()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{request.platform.value}' not found"
        )
    
    # Convert media_urls to string
    media_urls_str = ",".join(request.media_urls) if request.media_urls else None
    
    # Create post with published status
    now = datetime.utcnow()
    post = ScheduledPost(
        user_id=current_user.id,
        platform_id=platform.id,
        content=request.content,
        media_urls=media_urls_str,
        scheduled_at=now,
        status=PostStatus.PUBLISHED.value,
        published_at=now,
        external_post_id=f"simulated_{platform.name.lower()}_{now.timestamp():.0f}"
    )
    
    db.add(post)
    db.commit()
    db.refresh(post)
    
    return PublishResponse(
        data=scheduled_post_to_schema(post),
        message="Post published immediately"
    )
