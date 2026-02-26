"""Scheduler service for managing scheduled posts."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

from app.models.models import ScheduledPost, Platform


class SchedulerError(Exception):
    """Base exception for scheduler errors."""
    pass


class PostNotFoundError(SchedulerError):
    """Raised when a scheduled post is not found."""
    pass


class InvalidScheduleError(SchedulerError):
    """Raised when schedule data is invalid."""
    pass


class Priority:
    """Priority levels for scheduled posts."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class SchedulerService:
    """Service for managing scheduled posts."""

    # Optimal posting times based on general social media best practices
    # Times are in UTC, format: (day_of_week, hour) where Monday=0, Sunday=6
    OPTIMAL_TIMES = [
        # Tuesday, Wednesday, Thursday - peak engagement days
        (1, 9), (1, 12), (1, 15),   # Tuesday
        (2, 9), (2, 12), (2, 15),   # Wednesday
        (3, 9), (3, 12), (3, 15),   # Thursday
        # Monday and Friday
        (0, 10), (0, 14),           # Monday
        (4, 10), (4, 14),           # Friday
    ]

    def __init__(self, db: Session):
        self.db = db

    def schedule_post(
        self,
        user_id: str,
        platform_id: str,
        content: str,
        scheduled_at: datetime,
        media_urls: Optional[List[str]] = None,
        priority: int = Priority.NORMAL
    ) -> ScheduledPost:
        """Schedule a new post.

        Args:
            user_id: The user ID
            platform_id: The platform ID
            content: The post content
            scheduled_at: When to publish the post
            media_urls: Optional list of media URLs
            priority: Post priority (1-4)

        Returns:
            The created ScheduledPost

        Raises:
            InvalidScheduleError: If the schedule data is invalid
        """
        # Validate scheduled time is in the future
        if scheduled_at <= datetime.utcnow():
            raise InvalidScheduleError("Scheduled time must be in the future")

        # Validate priority
        if priority not in [Priority.LOW, Priority.NORMAL, Priority.HIGH, Priority.URGENT]:
            raise InvalidScheduleError("Priority must be 1 (LOW), 2 (NORMAL), 3 (HIGH), or 4 (URGENT)")

        # Validate content
        if not content or len(content.strip()) == 0:
            raise InvalidScheduleError("Content cannot be empty")

        # Check platform exists
        platform = self.db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            raise InvalidScheduleError(f"Platform with ID {platform_id} not found")

        # Create scheduled post
        scheduled_post = ScheduledPost(
            user_id=user_id,
            platform_id=platform_id,
            content=content,
            media_urls=",".join(media_urls) if media_urls else None,
            scheduled_at=scheduled_at,
            status="pending",
            priority=priority
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
        """Get the scheduled posts queue for a user.

        Args:
            user_id: The user ID
            status: Filter by status (pending, published, failed, cancelled)
            platform_id: Filter by platform
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            Dict with posts list and pagination info
        """
        query = self.db.query(ScheduledPost).filter(ScheduledPost.user_id == user_id)

        if status:
            query = query.filter(ScheduledPost.status == status)

        if platform_id:
            query = query.filter(ScheduledPost.platform_id == platform_id)

        # Order by priority (desc) then scheduled_at (asc)
        query = query.order_by(desc(ScheduledPost.priority), asc(ScheduledPost.scheduled_at))

        total = query.count()
        posts = query.offset(offset).limit(limit).all()

        return {
            "posts": posts,
            "total": total,
            "limit": limit,
            "offset": offset
        }

    def publish_now(self, post_id: str, user_id: str) -> ScheduledPost:
        """Publish a scheduled post immediately.

        Args:
            post_id: The post ID
            user_id: The user ID (for authorization)

        Returns:
            The updated ScheduledPost

        Raises:
            PostNotFoundError: If post not found
            SchedulerError: If post cannot be published
        """
        post = self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.id == post_id,
                ScheduledPost.user_id == user_id
            )
        ).first()

        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        if post.status == "published":
            raise SchedulerError("Post is already published")

        if post.status == "cancelled":
            raise SchedulerError("Cannot publish a cancelled post")

        # Mark as published
        post.status = "published"
        post.published_at = datetime.utcnow()
        post.scheduled_at = datetime.utcnow()  # Update scheduled time to now

        self.db.commit()
        self.db.refresh(post)

        return post

    def cancel_post(self, post_id: str, user_id: str) -> ScheduledPost:
        """Cancel a scheduled post.

        Args:
            post_id: The post ID
            user_id: The user ID (for authorization)

        Returns:
            The updated ScheduledPost

        Raises:
            PostNotFoundError: If post not found
            SchedulerError: If post cannot be cancelled
        """
        post = self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.id == post_id,
                ScheduledPost.user_id == user_id
            )
        ).first()

        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        if post.status == "published":
            raise SchedulerError("Cannot cancel an already published post")

        if post.status == "cancelled":
            raise SchedulerError("Post is already cancelled")

        post.status = "cancelled"
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
        priority: Optional[int] = None
    ) -> ScheduledPost:
        """Update a scheduled post.

        Args:
            post_id: The post ID
            user_id: The user ID (for authorization)
            content: New content (optional)
            scheduled_at: New scheduled time (optional)
            media_urls: New media URLs (optional)
            priority: New priority (optional)

        Returns:
            The updated ScheduledPost

        Raises:
            PostNotFoundError: If post not found
            SchedulerError: If post cannot be updated
        """
        post = self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.id == post_id,
                ScheduledPost.user_id == user_id
            )
        ).first()

        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        if post.status == "published":
            raise SchedulerError("Cannot update a published post")

        if post.status == "cancelled":
            raise SchedulerError("Cannot update a cancelled post")

        if content is not None:
            if not content.strip():
                raise InvalidScheduleError("Content cannot be empty")
            post.content = content

        if scheduled_at is not None:
            if scheduled_at <= datetime.utcnow():
                raise InvalidScheduleError("Scheduled time must be in the future")
            post.scheduled_at = scheduled_at

        if media_urls is not None:
            post.media_urls = ",".join(media_urls) if media_urls else None

        if priority is not None:
            if priority not in [Priority.LOW, Priority.NORMAL, Priority.HIGH, Priority.URGENT]:
                raise InvalidScheduleError("Invalid priority value")
            post.priority = priority

        self.db.commit()
        self.db.refresh(post)

        return post

    def get_post(self, post_id: str, user_id: str) -> ScheduledPost:
        """Get a single scheduled post.

        Args:
            post_id: The post ID
            user_id: The user ID (for authorization)

        Returns:
            The ScheduledPost

        Raises:
            PostNotFoundError: If post not found
        """
        post = self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.id == post_id,
                ScheduledPost.user_id == user_id
            )
        ).first()

        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        return post

    def get_pending_posts(self, limit: int = 100) -> List[ScheduledPost]:
        """Get posts that are ready to be published (scheduled time has passed).

        Args:
            limit: Maximum number of posts to return

        Returns:
            List of ScheduledPost objects ready for publishing
        """
        now = datetime.utcnow()
        posts = self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.status == "pending",
                ScheduledPost.scheduled_at <= now
            )
        ).order_by(
            desc(ScheduledPost.priority),
            asc(ScheduledPost.scheduled_at)
        ).limit(limit).all()

        return posts

    def mark_as_published(self, post_id: str, external_post_id: Optional[str] = None) -> ScheduledPost:
        """Mark a post as published (called by the publishing worker).

        Args:
            post_id: The post ID
            external_post_id: The external platform post ID

        Returns:
            The updated ScheduledPost
        """
        post = self.db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()

        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        post.status = "published"
        post.published_at = datetime.utcnow()
        if external_post_id:
            post.external_post_id = external_post_id

        self.db.commit()
        self.db.refresh(post)

        return post

    def mark_as_failed(self, post_id: str, error_message: str) -> ScheduledPost:
        """Mark a post as failed (called by the publishing worker).

        Args:
            post_id: The post ID
            error_message: The error message

        Returns:
            The updated ScheduledPost
        """
        post = self.db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()

        if not post:
            raise PostNotFoundError(f"Post with ID {post_id} not found")

        post.status = "failed"
        post.error_message = error_message

        self.db.commit()
        self.db.refresh(post)

        return post

    def get_optimal_posting_times(
        self,
        days_ahead: int = 7,
        count_per_day: int = 3
    ) -> List[datetime]:
        """Get recommended optimal posting times.

        Args:
            days_ahead: Number of days to look ahead
            count_per_day: Number of suggestions per day

        Returns:
            List of recommended datetime objects
        """
        suggestions = []
        now = datetime.utcnow()

        for day_offset in range(days_ahead):
            target_date = now + timedelta(days=day_offset)
            day_of_week = target_date.weekday()

            # Get optimal hours for this day
            day_times = [hour for d, hour in self.OPTIMAL_TIMES if d == day_of_week]

            if not day_times:
                # Default times for non-optimal days
                day_times = [10, 14, 18]

            for hour in day_times[:count_per_day]:
                suggestion = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                if suggestion > now:
                    suggestions.append(suggestion)

        return sorted(suggestions)

    def bulk_schedule(
        self,
        user_id: str,
        posts_data: List[Dict[str, Any]]
    ) -> List[ScheduledPost]:
        """Schedule multiple posts at once.

        Args:
            user_id: The user ID
            posts_data: List of post data dicts with keys:
                platform_id, content, scheduled_at, media_urls (optional), priority (optional)

        Returns:
            List of created ScheduledPost objects
        """
        created_posts = []

        for post_data in posts_data:
            try:
                post = self.schedule_post(
                    user_id=user_id,
                    platform_id=post_data["platform_id"],
                    content=post_data["content"],
                    scheduled_at=post_data["scheduled_at"],
                    media_urls=post_data.get("media_urls"),
                    priority=post_data.get("priority", Priority.NORMAL)
                )
                created_posts.append(post)
            except InvalidScheduleError:
                # Continue with other posts even if one fails
                continue

        return created_posts

    def get_queue_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about the user's queue.

        Args:
            user_id: The user ID

        Returns:
            Dict with queue statistics
        """
        from sqlalchemy import func

        stats = self.db.query(
            ScheduledPost.status,
            func.count(ScheduledPost.id).label("count")
        ).filter(
            ScheduledPost.user_id == user_id
        ).group_by(ScheduledPost.status).all()

        status_counts = {status: count for status, count in stats}

        # Get upcoming posts count
        upcoming_count = self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.user_id == user_id,
                ScheduledPost.status == "pending",
                ScheduledPost.scheduled_at > datetime.utcnow()
            )
        ).count()

        # Get next scheduled post
        next_post = self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.user_id == user_id,
                ScheduledPost.status == "pending",
                ScheduledPost.scheduled_at > datetime.utcnow()
            )
        ).order_by(asc(ScheduledPost.scheduled_at)).first()

        return {
            "total_posts": sum(status_counts.values()),
            "pending": status_counts.get("pending", 0),
            "published": status_counts.get("published", 0),
            "failed": status_counts.get("failed", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "upcoming_count": upcoming_count,
            "next_scheduled_at": next_post.scheduled_at.isoformat() if next_post else None
        }
