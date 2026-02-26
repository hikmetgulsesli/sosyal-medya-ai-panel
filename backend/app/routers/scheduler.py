"""Scheduler router for managing scheduled posts."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.database import get_db
from app.models.models import User
from app.services.scheduler_service import (
    SchedulerService,
    PostStatus,
    Priority,
    PostNotFoundError,
    InvalidScheduleError,
)

router = APIRouter(prefix="/posts", tags=["scheduler"])


# Request/Response schemas
class ScheduledPostCreate(BaseModel):
    """Schema for creating a scheduled post."""
    platform_id: str = Field(..., description="ID of the platform to post to")
    content: str = Field(..., min_length=1, max_length=2800, description="Post content")
    media_urls: Optional[List[str]] = Field(None, description="Optional list of media URLs")
    scheduled_at: datetime = Field(..., description="When to publish the post")
    priority: int = Field(default=2, ge=1, le=4, description="Priority: 1=LOW, 2=NORMAL, 3=HIGH, 4=URGENT")


class ScheduledPostUpdate(BaseModel):
    """Schema for updating a scheduled post."""
    content: Optional[str] = Field(None, min_length=1, max_length=2800)
    media_urls: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=4)


class ScheduledPostResponse(BaseModel):
    """Response schema for a scheduled post."""
    id: str
    user_id: str
    platform_id: str
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_at: datetime
    status: str
    priority: int
    published_at: Optional[datetime] = None
    external_post_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class QueueListResponse(BaseModel):
    """Response schema for queue list."""
    posts: List[ScheduledPostResponse]
    total: int
    limit: int
    offset: int


class QueueStatsResponse(BaseModel):
    """Response schema for queue statistics."""
    total: int
    pending: int
    queued: int
    published: int
    failed: int
    cancelled: int
    next_scheduled: Optional[str] = None


class OptimalTimeResponse(BaseModel):
    """Response schema for optimal posting time."""
    datetime: str
    score: float
    period: str
    day_of_week: str


class BulkScheduleRequest(BaseModel):
    """Schema for bulk scheduling posts."""
    posts: List[ScheduledPostCreate]


class BulkScheduleResponse(BaseModel):
    """Response schema for bulk scheduling."""
    scheduled_count: int
    failed_count: int
    posts: List[ScheduledPostResponse]


class PublishResponse(BaseModel):
    """Response schema for publish action."""
    id: str
    status: str
    published_at: Optional[str] = None
    external_post_id: Optional[str] = None
    message: str


class CancelResponse(BaseModel):
    """Response schema for cancel action."""
    id: str
    status: str
    message: str


@router.post(
    "/schedule",
    response_model=ScheduledPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule a new post",
    description="Create a new scheduled post for a specific platform and time."
)
def schedule_post(
    data: ScheduledPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Schedule a new post.
    
    Args:
        data: Post scheduling data
        
    Returns:
        The created scheduled post
        
    Raises:
        400: If scheduled time is in the past or platform not found
    """
    try:
        scheduler = SchedulerService(db)
        priority = Priority(data.priority)
        post = scheduler.schedule_post(
            user_id=current_user.id,
            platform_id=data.platform_id,
            content=data.content,
            scheduled_at=data.scheduled_at,
            media_urls=data.media_urls,
            priority=priority
        )
        
        # Parse media_urls for response
        import json
        if post.media_urls:
            post.media_urls = json.loads(post.media_urls)
        
        return post
        
    except InvalidScheduleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "code": "INVALID_SCHEDULE"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Invalid priority value: {e}",
                "code": "INVALID_PRIORITY"
            }
        )


@router.get(
    "/queue",
    response_model=QueueListResponse,
    summary="View queued posts",
    description="Get the list of scheduled posts for the current user."
)
def get_queue(
    status: Optional[str] = Query(None, description="Filter by status"),
    platform_id: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the queue of scheduled posts.
    
    Args:
        status: Optional status filter (pending, queued, published, etc.)
        platform_id: Optional platform filter
        limit: Maximum number of posts to return
        offset: Number of posts to skip
        
    Returns:
        List of scheduled posts with pagination info
    """
    scheduler = SchedulerService(db)
    result = scheduler.get_queue(
        user_id=current_user.id,
        status=status,
        platform_id=platform_id,
        limit=limit,
        offset=offset
    )
    
    # Parse media_urls for each post
    import json
    for post in result["posts"]:
        if post.media_urls:
            post.media_urls = json.loads(post.media_urls)
    
    return QueueListResponse(
        posts=result["posts"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"]
    )


@router.get(
    "/{post_id}",
    response_model=ScheduledPostResponse,
    summary="Get a specific post",
    description="Get details of a specific scheduled post."
)
def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific scheduled post.
    
    Args:
        post_id: ID of the post
        
    Returns:
        The scheduled post details
        
    Raises:
        404: If post not found
    """
    scheduler = SchedulerService(db)
    post = scheduler.get_post_by_id(post_id, current_user.id)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Post with id {post_id} not found",
                "code": "POST_NOT_FOUND"
            }
        )
    
    # Parse media_urls for response
    import json
    if post.media_urls:
        post.media_urls = json.loads(post.media_urls)
    
    return post


@router.put(
    "/{post_id}",
    response_model=ScheduledPostResponse,
    summary="Update a scheduled post",
    description="Update content, time, or priority of a scheduled post."
)
def update_post(
    post_id: str,
    data: ScheduledPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a scheduled post.
    
    Args:
        post_id: ID of the post to update
        data: Update data
        
    Returns:
        The updated post
        
    Raises:
        404: If post not found
        400: If post cannot be updated or invalid data
    """
    try:
        scheduler = SchedulerService(db)
        priority = Priority(data.priority) if data.priority else None
        
        post = scheduler.update_post(
            post_id=post_id,
            user_id=current_user.id,
            content=data.content,
            scheduled_at=data.scheduled_at,
            media_urls=data.media_urls,
            priority=priority
        )
        
        # Parse media_urls for response
        import json
        if post.media_urls:
            post.media_urls = json.loads(post.media_urls)
        
        return post
        
    except PostNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": str(e),
                "code": "POST_NOT_FOUND"
            }
        )
    except InvalidScheduleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "code": "INVALID_SCHEDULE"
            }
        )


@router.put(
    "/{post_id}/publish",
    response_model=PublishResponse,
    summary="Publish immediately",
    description="Publish a scheduled post immediately."
)
def publish_immediately(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a scheduled post immediately.
    
    Args:
        post_id: ID of the post to publish
        
    Returns:
        Publish result with status
        
    Raises:
        404: If post not found
        400: If post cannot be published
    """
    try:
        scheduler = SchedulerService(db)
        post = scheduler.publish_immediately(post_id, current_user.id)
        
        return PublishResponse(
            id=post.id,
            status=post.status,
            published_at=post.published_at.isoformat() if post.published_at else None,
            external_post_id=post.external_post_id,
            message="Post published successfully"
        )
        
    except PostNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": str(e),
                "code": "POST_NOT_FOUND"
            }
        )
    except InvalidScheduleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "code": "INVALID_PUBLISH"
            }
        )


@router.delete(
    "/{post_id}",
    response_model=CancelResponse,
    summary="Cancel scheduled post",
    description="Cancel a scheduled post."
)
def cancel_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a scheduled post.
    
    Args:
        post_id: ID of the post to cancel
        
    Returns:
        Cancel result with status
        
    Raises:
        404: If post not found
        400: If post cannot be cancelled
    """
    try:
        scheduler = SchedulerService(db)
        post = scheduler.cancel_post(post_id, current_user.id)
        
        return CancelResponse(
            id=post.id,
            status=post.status,
            message="Post cancelled successfully"
        )
        
    except PostNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": str(e),
                "code": "POST_NOT_FOUND"
            }
        )
    except InvalidScheduleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": str(e),
                "code": "INVALID_CANCEL"
            }
        )


@router.get(
    "/stats/queue",
    response_model=QueueStatsResponse,
    summary="Get queue statistics",
    description="Get statistics about the user's scheduled posts."
)
def get_queue_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get queue statistics.
    
    Returns:
        Queue statistics including counts by status
    """
    scheduler = SchedulerService(db)
    stats = scheduler.get_queue_stats(current_user.id)
    
    return QueueStatsResponse(
        total=stats["total"],
        pending=stats["pending"],
        queued=stats["queued"],
        published=stats["published"],
        failed=stats["failed"],
        cancelled=stats["cancelled"],
        next_scheduled=stats["next_scheduled"]
    )


@router.get(
    "/optimal-times/{platform_id}",
    response_model=List[OptimalTimeResponse],
    summary="Get optimal posting times",
    description="Get AI-recommended optimal posting times based on historical engagement."
)
def get_optimal_times(
    platform_id: str,
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get optimal posting times for a platform.
    
    Args:
        platform_id: ID of the platform
        days: Number of days to analyze
        
    Returns:
        List of recommended posting times with engagement scores
    """
    scheduler = SchedulerService(db)
    times = scheduler.get_optimal_posting_times(
        user_id=current_user.id,
        platform_id=platform_id,
        days=days
    )
    
    return [
        OptimalTimeResponse(
            datetime=t["datetime"],
            score=t["score"],
            period=t["period"],
            day_of_week=t["day_of_week"]
        )
        for t in times
    ]


@router.post(
    "/bulk-schedule",
    response_model=BulkScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk schedule posts",
    description="Schedule multiple posts at once."
)
def bulk_schedule(
    data: BulkScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Schedule multiple posts at once.
    
    Args:
        data: List of posts to schedule
        
    Returns:
        Results of the bulk scheduling operation
    """
    scheduler = SchedulerService(db)
    posts_data = []
    for post in data.posts:
        posts_data.append({
            "platform_id": post.platform_id,
            "content": post.content,
            "scheduled_at": post.scheduled_at,
            "media_urls": post.media_urls,
            "priority": post.priority
        })
    
    created_posts = scheduler.bulk_schedule(
        user_id=current_user.id,
        posts=posts_data
    )
    
    # Parse media_urls for each post
    import json
    for post in created_posts:
        if post.media_urls:
            post.media_urls = json.loads(post.media_urls)
    
    return BulkScheduleResponse(
        scheduled_count=len(created_posts),
        failed_count=len(data.posts) - len(created_posts),
        posts=created_posts
    )
