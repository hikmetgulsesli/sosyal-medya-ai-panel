from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio

from app.db.database import get_db
from app.core.auth import get_current_user
from app.models.models import User, ScheduledPost, Platform
from app.schemas.scheduler import (
    ScheduledPostCreate,
    ScheduledPostUpdate,
    ScheduledPostResponse,
    ScheduledPostListResponse,
    PublishResponse,
    OptimalTimeRequest,
    OptimalTimeResponse,
    OptimalTimeSlot
)

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.post("", response_model=ScheduledPostResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_post(
    post_data: ScheduledPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scheduled post."""
    # Verify platform exists and is active
    platform = db.query(Platform).filter(
        Platform.id == post_data.platform_id,
        Platform.is_active == True
    ).first()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found or inactive"
        )
    
    # Validate scheduled time is in the future
    if post_data.scheduled_at <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
    
    # Add platform name to response
    response_data = ScheduledPostResponse.from_orm(scheduled_post)
    response_data.platform_name = platform.display_name
    
    return response_data


@router.get("", response_model=ScheduledPostListResponse)
async def list_scheduled_posts(
    status: Optional[str] = Query(None, description="Filter by status: pending, published, failed"),
    platform_id: Optional[str] = Query(None, description="Filter by platform ID"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's scheduled posts with pagination and filters."""
    # Build query
    query = db.query(ScheduledPost).filter(ScheduledPost.user_id == current_user.id)
    
    if status:
        query = query.filter(ScheduledPost.status == status)
    
    if platform_id:
        query = query.filter(ScheduledPost.platform_id == platform_id)
    
    # Get total count
    total = query.count()
    
    # Get posts with pagination
    posts = query.order_by(desc(ScheduledPost.scheduled_at)).offset(offset).limit(limit).all()
    
    # Enrich with platform names
    platform_ids = {post.platform_id for post in posts}
    platforms = db.query(Platform).filter(Platform.id.in_(platform_ids)).all()
    platform_map = {p.id: p.display_name for p in platforms}
    
    response_posts = []
    for post in posts:
        post_response = ScheduledPostResponse.from_orm(post)
        post_response.platform_name = platform_map.get(post.platform_id, "Unknown")
        response_posts.append(post_response)
    
    return ScheduledPostListResponse(
        data=response_posts,
        meta={
            "page": (offset // limit) + 1,
            "limit": limit,
            "total": total,
            "has_more": (offset + limit) < total
        }
    )


@router.get("/{post_id}", response_model=ScheduledPostResponse)
async def get_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single scheduled post by ID."""
    post = db.query(ScheduledPost).filter(
        ScheduledPost.id == post_id,
        ScheduledPost.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Get platform name
    platform = db.query(Platform).filter(Platform.id == post.platform_id).first()
    
    response = ScheduledPostResponse.from_orm(post)
    response.platform_name = platform.display_name if platform else "Unknown"
    
    return response


@router.put("/{post_id}", response_model=ScheduledPostResponse)
async def update_scheduled_post(
    post_id: str,
    post_data: ScheduledPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a scheduled post's content or time."""
    post = db.query(ScheduledPost).filter(
        ScheduledPost.id == post_id,
        ScheduledPost.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Cannot update already published posts
    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a published post"
        )
    
    # Update fields
    if post_data.content is not None:
        post.content = post_data.content
    
    if post_data.media_urls is not None:
        post.media_urls = post_data.media_urls
    
    if post_data.scheduled_at is not None:
        # Validate new scheduled time is in the future
        if post_data.scheduled_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scheduled time must be in the future"
            )
        post.scheduled_at = post_data.scheduled_at
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    
    # Get platform name
    platform = db.query(Platform).filter(Platform.id == post.platform_id).first()
    
    response = ScheduledPostResponse.from_orm(post)
    response.platform_name = platform.display_name if platform else "Unknown"
    
    return response


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel/delete a scheduled post."""
    post = db.query(ScheduledPost).filter(
        ScheduledPost.id == post_id,
        ScheduledPost.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    # Cannot delete already published posts
    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a published post"
        )
    
    db.delete(post)
    db.commit()
    
    return None


@router.patch("/{post_id}/publish", response_model=PublishResponse)
async def manually_publish_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger publish for a scheduled post."""
    post = db.query(ScheduledPost).filter(
        ScheduledPost.id == post_id,
        ScheduledPost.user_id == current_user.id
    ).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled post not found"
        )
    
    if post.status == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post is already published"
        )
    
    # Get platform for publishing
    platform = db.query(Platform).filter(Platform.id == post.platform_id).first()
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform not found"
        )
    
    # Check if user has API key for this platform
    from app.models.models import ApiKey
    api_key = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.platform_id == post.platform_id,
        ApiKey.is_active == True
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active API key found for {platform.display_name}"
        )
    
    # Simulate publishing (in production, this would call the actual platform API)
    try:
        # In a real implementation, we would call the platform's API here
        # For now, simulate successful publishing
        external_post_id = f"simulated_{platform.name}_{datetime.utcnow().timestamp()}"
        
        post.status = "published"
        post.published_at = datetime.utcnow()
        post.external_post_id = external_post_id
        post.updated_at = datetime.utcnow()
        db.commit()
        
        return PublishResponse(
            success=True,
            message=f"Post successfully published to {platform.display_name}",
            external_post_id=external_post_id
        )
        
    except Exception as e:
        post.status = "failed"
        post.error_message = str(e)
        post.updated_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish post: {str(e)}"
        )


@router.post("/optimal-times", response_model=OptimalTimeResponse)
async def get_optimal_times(
    request: OptimalTimeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get optimal posting times for a platform."""
    # Verify platform exists
    platform = db.query(Platform).filter(
        Platform.id == request.platform_id,
        Platform.is_active == True
    ).first()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Platform not found or inactive"
        )
    
    # Calculate optimal times based on platform and historical data
    # This is a simplified algorithm - in production, this would use ML/analytics
    
    optimal_slots = []
    base_date = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    # Platform-specific optimal hours (simplified)
    optimal_hours = {
        "twitter": [9, 12, 15, 18, 20],  # X/Twitter peak times
        "linkedin": [8, 12, 17],  # LinkedIn peak times
        "instagram": [11, 13, 17, 19],  # Instagram peak times
        "bluesky": [9, 13, 17, 20],  # Bluesky peak times
    }
    
    platform_key = platform.name.lower()
    hours = optimal_hours.get(platform_key, [9, 12, 15, 18])
    
    # Generate slots for the requested days
    for day_offset in range(request.days_ahead):
        day_base = base_date + timedelta(days=day_offset)
        
        for hour in hours:
            slot_time = day_base.replace(hour=hour)
            
            # Skip times in the past
            if slot_time <= datetime.utcnow():
                continue
            
            # Calculate score based on various factors
            score = 0.7  # Base score
            
            # Boost score for weekdays during business hours
            weekday = slot_time.weekday()
            if weekday < 5:  # Monday-Friday
                score += 0.15
            
            # Boost for peak engagement hours
            if hour in [12, 18, 20]:
                score += 0.1
            
            # Slight randomization for variety
            import random
            score += random.uniform(-0.05, 0.05)
            score = min(1.0, max(0.0, score))
            
            reason = "Peak engagement time"
            if weekday >= 5:
                reason = "Weekend engagement window"
            elif hour in [8, 9]:
                reason = "Morning commute/startup time"
            elif hour in [12, 13]:
                reason = "Lunch break peak"
            elif hour in [17, 18]:
                reason = "End of workday peak"
            
            optimal_slots.append(OptimalTimeSlot(
                datetime=slot_time,
                score=round(score, 2),
                reason=reason
            ))
    
    # Sort by score descending
    optimal_slots.sort(key=lambda x: x.score, reverse=True)
    
    # Return top 10 slots
    return OptimalTimeResponse(
        platform_id=request.platform_id,
        optimal_slots=optimal_slots[:10]
    )
