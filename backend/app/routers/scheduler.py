"""Scheduler router for managing scheduled posts."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.models.models import User
from app.services.scheduler_service import (
    SchedulerService,
    SchedulerError,
    PostNotFoundError,
    InvalidScheduleError
)

router = APIRouter(prefix="/posts", tags=["scheduler"])


# Pydantic schemas
class SchedulePostRequest(BaseModel):
    platform_id: str = Field(..., description="Platform ID to post to")
    content: str = Field(..., min_length=1, max_length=2000, description="Post content")
    scheduled_at: datetime = Field(..., description="When to publish the post (UTC)")
    media_urls: Optional[List[str]] = Field(None, description="Optional media URLs")
    priority: int = Field(default=2, ge=1, le=4, description="Priority: 1=LOW, 2=NORMAL, 3=HIGH, 4=URGENT")


class UpdatePostRequest(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=2000, description="Post content")
    scheduled_at: Optional[datetime] = Field(None, description="When to publish the post (UTC)")
    media_urls: Optional[List[str]] = Field(None, description="Optional media URLs")
    priority: Optional[int] = Field(None, ge=1, le=4, description="Priority: 1=LOW, 2=NORMAL, 3=HIGH, 4=URGENT")


class ScheduledPostResponse(BaseModel):
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


class QueueResponse(BaseModel):
    posts: List[ScheduledPostResponse]
    total: int
    limit: int
    offset: int


class QueueStatsResponse(BaseModel):
    total_posts: int
    pending: int
    published: int
    failed: int
    cancelled: int
    upcoming_count: int
    next_scheduled_at: Optional[str] = None


class OptimalTimesResponse(BaseModel):
    times: List[datetime]


class BulkScheduleRequest(BaseModel):
    posts: List[SchedulePostRequest]


class BulkScheduleResponse(BaseModel):
    scheduled_count: int
    posts: List[ScheduledPostResponse]


# Helper function to convert model to response
def post_to_response(post) -> ScheduledPostResponse:
    """Convert ScheduledPost model to response schema."""
    return ScheduledPostResponse(
        id=post.id,
        user_id=post.user_id,
        platform_id=post.platform_id,
        content=post.content,
        media_urls=post.media_urls.split(",") if post.media_urls else None,
        scheduled_at=post.scheduled_at,
        status=post.status,
        priority=post.priority,
        published_at=post.published_at,
        external_post_id=post.external_post_id,
        error_message=post.error_message,
        created_at=post.created_at,
        updated_at=post.updated_at
    )


@router.post("/schedule", response_model=ScheduledPostResponse)
def schedule_post(
    request: SchedulePostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule a new post for future publication."""
    service = SchedulerService(db)
    try:
        post = service.schedule_post(
            user_id=current_user.id,
            platform_id=request.platform_id,
            content=request.content,
            scheduled_at=request.scheduled_at,
            media_urls=request.media_urls,
            priority=request.priority
        )
        return post_to_response(post)
    except InvalidScheduleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SchedulerError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue", response_model=QueueResponse)
def get_queue(
    status: Optional[str] = Query(None, description="Filter by status: pending, published, failed, cancelled"),
    platform_id: Optional[str] = Query(None, description="Filter by platform ID"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the scheduled posts queue for the current user."""
    service = SchedulerService(db)
    result = service.get_queue(
        user_id=current_user.id,
        status=status,
        platform_id=platform_id,
        limit=limit,
        offset=offset
    )

    return QueueResponse(
        posts=[post_to_response(p) for p in result["posts"]],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"]
    )


@router.get("/queue/stats", response_model=QueueStatsResponse)
def get_queue_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about the user's scheduled posts queue."""
    service = SchedulerService(db)
    stats = service.get_queue_stats(current_user.id)
    return QueueStatsResponse(**stats)


@router.get("/optimal-times", response_model=OptimalTimesResponse)
def get_optimal_times(
    days_ahead: int = Query(7, ge=1, le=30, description="Number of days to look ahead"),
    count_per_day: int = Query(3, ge=1, le=10, description="Number of suggestions per day"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recommended optimal posting times based on engagement data."""
    service = SchedulerService(db)
    times = service.get_optimal_posting_times(days_ahead=days_ahead, count_per_day=count_per_day)
    return OptimalTimesResponse(times=times)


@router.get("/{post_id}", response_model=ScheduledPostResponse)
def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific scheduled post by ID."""
    service = SchedulerService(db)
    try:
        post = service.get_post(post_id, current_user.id)
        return post_to_response(post)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")


@router.put("/{post_id}", response_model=ScheduledPostResponse)
def update_post(
    post_id: str,
    request: UpdatePostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a scheduled post."""
    service = SchedulerService(db)
    try:
        post = service.update_post(
            post_id=post_id,
            user_id=current_user.id,
            content=request.content,
            scheduled_at=request.scheduled_at,
            media_urls=request.media_urls,
            priority=request.priority
        )
        return post_to_response(post)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
    except InvalidScheduleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SchedulerError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{post_id}/publish", response_model=ScheduledPostResponse)
def publish_now(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish a scheduled post immediately."""
    service = SchedulerService(db)
    try:
        post = service.publish_now(post_id, current_user.id)
        return post_to_response(post)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
    except SchedulerError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{post_id}", response_model=ScheduledPostResponse)
def cancel_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a scheduled post."""
    service = SchedulerService(db)
    try:
        post = service.cancel_post(post_id, current_user.id)
        return post_to_response(post)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
    except SchedulerError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bulk-schedule", response_model=BulkScheduleResponse)
def bulk_schedule(
    request: BulkScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule multiple posts at once."""
    service = SchedulerService(db)

    posts_data = []
    for post in request.posts:
        posts_data.append({
            "platform_id": post.platform_id,
            "content": post.content,
            "scheduled_at": post.scheduled_at,
            "media_urls": post.media_urls,
            "priority": post.priority
        })

    created_posts = service.bulk_schedule(current_user.id, posts_data)

    return BulkScheduleResponse(
        scheduled_count=len(created_posts),
        posts=[post_to_response(p) for p in created_posts]
    )
