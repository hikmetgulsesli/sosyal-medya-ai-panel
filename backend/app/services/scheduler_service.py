"""Scheduler service for managing scheduled posts."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from app.models.models import ScheduledPost, Platform, User, Post


class PostStatus(str, Enum):
    """Status of a scheduled post."""
    PENDING = "pending"
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(int, Enum):
    """Priority levels for posts."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class SchedulerError(Exception):
    """Base exception for scheduler errors."""
    pass


class PostNotFoundError(SchedulerError):
    """Raised when a post is not found."""
    pass


class InvalidScheduleError(SchedulerError):
    """Raised when schedule parameters are invalid."""
    pass


class SchedulerService:
    """Service for managing scheduled posts."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def schedule_post(
        self,
        user_id: str,
        platform_id: str,
        content: str,
        scheduled_at: datetime,
        media_urls: Optional[List[str]] = None,
        priority: Priority = Priority.NORMAL
    ) -> ScheduledPost:
        """Schedule a new post.
        
        Args:
            user_id: ID of the user scheduling the post
            platform_id: ID of the platform to post to
            content: Content of the post
            scheduled_at: When to publish the post
            media_urls: Optional list of media URLs
            priority: Priority level for queue management
            
        Returns:
            The created ScheduledPost
            
        Raises:
            InvalidScheduleError: If scheduled_at is in the past
        """
        # Validate scheduled time is in the future
        if scheduled_at < datetime.utcnow():
            raise InvalidScheduleError("Scheduled time must be in the future")
        
        # Validate platform exists
        platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            raise InvalidScheduleError(f"Platform with id {platform_id} not found")
        
        # Create the scheduled post
        scheduled_post = ScheduledPost(
            user_id=user_id,
            platform_id=platform_id,
            content=content,
            media_urls=json.dumps(media_urls) if media_urls else None,
            scheduled_at=scheduled_at,
            status=PostStatus.PENDING.value,
            priority=priority.value
        )
        
        self.db.add(scheduled_post)
        self.db.commit()
        self.db.refresh(scheduled_post)
        
        return scheduled_post
    
    def get_queue(
        self,
        user_id: str,
        status: Optional[str] = None,
        platform_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get the queue of scheduled posts for a user.
        
        Args:
            user_id: ID of the user
            status: Filter by status (optional)
            platform_id: Filter by platform (optional)
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            Dictionary with posts list and pagination info
        """
        query = self.db.query(ScheduledPost).filter(ScheduledPost.user_id == user_id)
        
        if status:
            query = query.filter(ScheduledPost.status == status)
        
        if platform_id:
            query = query.filter(ScheduledPost.platform_id == platform_id)
        
        # Order by scheduled_at (earliest first) and priority (highest first)
        query = query.order_by(
            asc(ScheduledPost.scheduled_at),
            desc(ScheduledPost.priority)
        )
        
        total = query.count()
        posts = query.offset(offset).limit(limit).all()
        
        return {
            "posts": posts,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def get_post_by_id(self, post_id: str, user_id: str) -> Optional[ScheduledPost]:
        """Get a specific scheduled post by ID.
        
        Args:
            post_id: ID of the post
            user_id: ID of the user (for authorization)
            
        Returns:
            The ScheduledPost or None if not found
        """
        return self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.id == post_id,
                ScheduledPost.user_id == user_id
            )
        ).first()
    
    def publish_immediately(self, post_id: str, user_id: str) -> ScheduledPost:
        """Publish a scheduled post immediately.
        
        Args:
            post_id: ID of the post to publish
            user_id: ID of the user (for authorization)
            
        Returns:
            The updated ScheduledPost
            
        Raises:
            PostNotFoundError: If post not found
            InvalidScheduleError: If post cannot be published
        """
        post = self.get_post_by_id(post_id, user_id)
        
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        
        if post.status not in [PostStatus.PENDING.value, PostStatus.QUEUED.value]:
            raise InvalidScheduleError(
                f"Cannot publish post with status '{post.status}'. "
                "Only pending or queued posts can be published."
            )
        
        # Update post status to publishing
        post.status = PostStatus.PUBLISHING.value
        post.scheduled_at = datetime.utcnow()
        self.db.commit()
        
        # In a real implementation, this would trigger the actual publishing
        # For now, we simulate a successful publish
        post.status = PostStatus.PUBLISHED.value
        post.published_at = datetime.utcnow()
        post.external_post_id = f"simulated_{post.id}"
        self.db.commit()
        self.db.refresh(post)
        
        return post
    
    def cancel_post(self, post_id: str, user_id: str) -> ScheduledPost:
        """Cancel a scheduled post.
        
        Args:
            post_id: ID of the post to cancel
            user_id: ID of the user (for authorization)
            
        Returns:
            The updated ScheduledPost
            
        Raises:
            PostNotFoundError: If post not found
            InvalidScheduleError: If post cannot be cancelled
        """
        post = self.get_post_by_id(post_id, user_id)
        
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        
        if post.status not in [PostStatus.PENDING.value, PostStatus.QUEUED.value]:
            raise InvalidScheduleError(
                f"Cannot cancel post with status '{post.status}'. "
                "Only pending or queued posts can be cancelled."
            )
        
        post.status = PostStatus.CANCELLED.value
        self.db.commit()
        self.db.refresh(post)
        
        return post
    
    def update_post(
        self,
        post_id: str,
        user_id: str,
        content: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        media_urls: Optional[List[str]] = None,
        priority: Optional[Priority] = None
    ) -> ScheduledPost:
        """Update a scheduled post.
        
        Args:
            post_id: ID of the post to update
            user_id: ID of the user (for authorization)
            content: New content (optional)
            scheduled_at: New scheduled time (optional)
            media_urls: New media URLs (optional)
            priority: New priority (optional)
            
        Returns:
            The updated ScheduledPost
            
        Raises:
            PostNotFoundError: If post not found
            InvalidScheduleError: If post cannot be updated or invalid params
        """
        post = self.get_post_by_id(post_id, user_id)
        
        if not post:
            raise PostNotFoundError(f"Post with id {post_id} not found")
        
        if post.status not in [PostStatus.PENDING.value, PostStatus.QUEUED.value]:
            raise InvalidScheduleError(
                f"Cannot update post with status '{post.status}'. "
                "Only pending or queued posts can be updated."
            )
        
        if content is not None:
            post.content = content
        
        if scheduled_at is not None:
            if scheduled_at < datetime.utcnow():
                raise InvalidScheduleError("Scheduled time must be in the future")
            post.scheduled_at = scheduled_at
        
        if media_urls is not None:
            post.media_urls = json.dumps(media_urls) if media_urls else None
        
        if priority is not None:
            post.priority = priority.value
        
        self.db.commit()
        self.db.refresh(post)
        
        return post
    
    def get_due_posts(self, limit: int = 100) -> List[ScheduledPost]:
        """Get posts that are due for publishing.
        
        Args:
            limit: Maximum number of posts to return
            
        Returns:
            List of posts scheduled for now or earlier
        """
        now = datetime.utcnow()
        
        return self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.scheduled_at <= now,
                ScheduledPost.status == PostStatus.PENDING.value
            )
        ).order_by(
            desc(ScheduledPost.priority),
            asc(ScheduledPost.scheduled_at)
        ).limit(limit).all()
    
    def get_optimal_posting_times(
        self,
        user_id: str,
        platform_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get optimal posting times based on historical engagement.
        
        Args:
            user_id: ID of the user
            platform_id: ID of the platform
            days: Number of days to analyze
            
        Returns:
            List of recommended posting times with scores
        """
        # Get published posts with engagement data
        # In a real implementation, this would analyze actual engagement patterns
        # For now, we return generic optimal times based on common social media best practices
        
        optimal_times = []
        base_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Common optimal posting times (in UTC)
        # Morning: 8-10 AM, Lunch: 12-1 PM, Evening: 6-8 PM
        time_slots = [
            ("morning", 8, 0, 0.85),
            ("lunch", 12, 0, 0.90),
            ("evening", 18, 0, 0.88),
            ("night", 21, 0, 0.75),
        ]
        
        for day_offset in range(days):
            date = base_date + timedelta(days=day_offset)
            
            for slot_name, hour, minute, base_score in time_slots:
                optimal_time = date.replace(hour=hour, minute=minute)
                
                # Skip times in the past
                if optimal_time < datetime.utcnow():
                    continue
                
                # Add some variation based on day of week
                day_multiplier = 1.0
                if date.weekday() < 5:  # Weekdays
                    day_multiplier = 1.1
                else:  # Weekends
                    day_multiplier = 0.95
                
                score = min(1.0, base_score * day_multiplier)
                
                optimal_times.append({
                    "datetime": optimal_time.isoformat(),
                    "score": round(score, 2),
                    "period": slot_name,
                    "day_of_week": date.strftime("%A")
                })
        
        # Sort by score descending
        optimal_times.sort(key=lambda x: x["score"], reverse=True)
        
        return optimal_times[:10]  # Return top 10 recommendations
    
    def get_queue_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about the user's queue.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with queue statistics
        """
        query = self.db.query(ScheduledPost).filter(ScheduledPost.user_id == user_id)
        
        total = query.count()
        pending = query.filter(ScheduledPost.status == PostStatus.PENDING.value).count()
        queued = query.filter(ScheduledPost.status == PostStatus.QUEUED.value).count()
        published = query.filter(ScheduledPost.status == PostStatus.PUBLISHED.value).count()
        failed = query.filter(ScheduledPost.status == PostStatus.FAILED.value).count()
        cancelled = query.filter(ScheduledPost.status == PostStatus.CANCELLED.value).count()
        
        # Get next scheduled post
        next_post = query.filter(
            ScheduledPost.status.in_([PostStatus.PENDING.value, PostStatus.QUEUED.value])
        ).order_by(asc(ScheduledPost.scheduled_at)).first()
        
        return {
            "total": total,
            "pending": pending,
            "queued": queued,
            "published": published,
            "failed": failed,
            "cancelled": cancelled,
            "next_scheduled": next_post.scheduled_at.isoformat() if next_post else None
        }
    
    def bulk_schedule(
        self,
        user_id: str,
        posts: List[Dict[str, Any]]
    ) -> List[ScheduledPost]:
        """Schedule multiple posts at once.
        
        Args:
            user_id: ID of the user
            posts: List of post data dictionaries
            
        Returns:
            List of created ScheduledPosts
        """
        created_posts = []
        
        for post_data in posts:
            try:
                media_urls = post_data.get("media_urls")
                priority_value = post_data.get("priority", Priority.NORMAL.value)
                priority = Priority(priority_value) if isinstance(priority_value, int) else Priority.NORMAL
                
                post = self.schedule_post(
                    user_id=user_id,
                    platform_id=post_data["platform_id"],
                    content=post_data["content"],
                    scheduled_at=post_data["scheduled_at"],
                    media_urls=media_urls,
                    priority=priority
                )
                created_posts.append(post)
            except (InvalidScheduleError, ValueError) as e:
                # Log error but continue with other posts
                # In production, you'd want proper logging
                print(f"Failed to schedule post: {e}")
                continue
        
        return created_posts


def get_scheduler_service(db: Session) -> SchedulerService:
    """Dependency to get scheduler service."""
    return SchedulerService(db)
