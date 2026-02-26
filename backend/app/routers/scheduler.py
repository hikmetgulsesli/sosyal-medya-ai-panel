"""Scheduler router for managing scheduled posts."""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status as http_status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, ScheduledPost, Platform
from app.schemas.scheduler import (
    ScheduledPostCreate,
    ScheduledPostUpdate,
    ScheduledPostResponse,
    ScheduledPostListResponse,
    ScheduledPostDetailResponse,
    PublishResponse,
    ScheduledPostListWithMeta
)
from app.services.scheduler import SchedulerService

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.post("", response_model=ScheduledPostResponse, status_code=http_status.HTTP_201_CREATED)
def create_scheduled_post(
    post_data: ScheduledPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scheduled post."""
    # Validate platform exists and is active
    platform = db.query(Platform).filter(
        and_(
            Platform.id == post_data.platform_id,
            Platform.is_active
        )
    ).first()
    
    if not platform:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Platform not found or inactive"
        )
    
    # Validate scheduled time is in the future
    if post_data.scheduled_at <= datetime.utcnow():
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Scheduled time must be in the future"
        )
    
    # Create scheduled post
    scheduled_post = ScheduledPost(
        user_id=current_user.id,
        platform_id=post_data.platform_id,
        content=post_data.content,
        media_urls=post_data.media_urls,
        scheduled_at=post_data.scheduled_at,
        status="pending"
    )
    
    db.add(scheduled_post)
    db.commit()
    db.refresh(scheduled_post)
    
    return scheduled_post


@router.get("", response_model=ScheduledPostListWithMeta)
def list_scheduled_posts(
    status: Optional[str] = Query(None, description="Filter by status: pending, published, failed"),
    platform_id: Optional[str] = Query(None, description="Filter by platform ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's scheduled posts with pagination and filters."""
    # Build query
    query = db.query(ScheduledPost).filter(ScheduledPost.user_id == current_user.id)
    
    # Apply status filter
    if status:
        valid_statuses = ["pending", "published", "failed"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        query = query.filter(ScheduledPost.status == status)
    
    # Apply platform filter
    if platform_id:
        query = query.filter(ScheduledPost.platform_id == platform_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    offset = (page - 1) * limit
    posts = query.order_by(desc(ScheduledPost.scheduled_at)).offset(offset).limit(limit).all()
    
    # Calculate pagination meta
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    
    return ScheduledPostListWithMeta(
        data=posts,
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    )


@router.get("/{post_id}", response_model=ScheduledPostDetailResponse)
def get_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single scheduled post by ID."""
    post = db.query(ScheduledPost).filter(
        and_(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user.id
        )
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Get platform name
    platform = db.query(Platform).filter(Platform.id == post.platform_id).first()
    
    # Build response with platform name
    response_data = {
        "id": post.id,
        "user_id": post.user_id,
        "platform_id": post.platform_id,
        "platform_name": platform.display_name if platform else "Unknown",
        "content": post.content,
        "media_urls": post.media_urls,
        "scheduled_at": post.scheduled_at,
        "status": post.status,
        "published_at": post.published_at,
        "external_post_id": post.external_post_id,
        "error_message": post.error_message,
        "created_at": post.created_at,
        "updated_at": post.updated_at
    }
    
    return ScheduledPostDetailResponse(**response_data)


@router.put("/{post_id}", response_model=ScheduledPostResponse)
def update_scheduled_post(
    post_id: str,
    post_data: ScheduledPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a scheduled post (content, time, or platform)."""
    post = db.query(ScheduledPost).filter(
        and_(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user.id
        )
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Cannot update already published posts
    if post.status == "published":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a published post"
        )
    
    # Update fields if provided
    if post_data.content is not None:
        post.content = post_data.content
    
    if post_data.media_urls is not None:
        post.media_urls = post_data.media_urls
    
    if post_data.scheduled_at is not None:
        if post_data.scheduled_at <= datetime.utcnow():
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Scheduled time must be in the future"
            )
        post.scheduled_at = post_data.scheduled_at
    
    if post_data.platform_id is not None:
        # Validate new platform
        platform = db.query(Platform).filter(
            and_(
                Platform.id == post_data.platform_id,
                Platform.is_active == True
            )
        ).first()
        
        if not platform:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Platform not found or inactive"
            )
        post.platform_id = post_data.platform_id
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    
    return post


@router.delete("/{post_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete/cancel a scheduled post."""
    post = db.query(ScheduledPost).filter(
        and_(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user.id
        )
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Cannot delete already published posts
    if post.status == "published":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a published post"
        )
    
    db.delete(post)
    db.commit()
    
    return None


@router.patch("/{post_id}/publish", response_model=PublishResponse)
def manually_publish_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger publishing of a scheduled post."""
    post = db.query(ScheduledPost).filter(
        and_(
            ScheduledPost.id == post_id,
            ScheduledPost.user_id == current_user.id
        )
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Cannot manually publish already published posts
    if post.status == "published":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Post is already published"
        )
    
    # Use scheduler service to publish
    service = SchedulerService(db)
    success = service.publish_post(post)
    
    if success:
        return PublishResponse(
            success=True,
            message="Post published successfully",
            external_post_id=post.external_post_id
        )
    else:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish post: {post.error_message or 'Unknown error'}"
        )
