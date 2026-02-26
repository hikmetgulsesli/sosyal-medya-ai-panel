"""Scheduler service for background post publishing."""
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import ScheduledPost, Platform, User
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SchedulerService:
    """Service for managing scheduled posts and background publishing."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_pending_posts(self, limit: int = 100) -> List[ScheduledPost]:
        """Get posts that are pending and due for publishing."""
        now = datetime.utcnow()
        return self.db.query(ScheduledPost).filter(
            and_(
                ScheduledPost.status == "pending",
                ScheduledPost.scheduled_at <= now
            )
        ).order_by(ScheduledPost.scheduled_at.asc()).limit(limit).all()
    
    def publish_post(self, scheduled_post: ScheduledPost) -> bool:
        """
        Publish a scheduled post to the platform.
        
        Returns True if successful, False otherwise.
        """
        try:
            # Get platform details
            platform = self.db.query(Platform).filter(
                Platform.id == scheduled_post.platform_id
            ).first()
            
            if not platform:
                logger.error(f"Platform not found: {scheduled_post.platform_id}")
                self._mark_failed(scheduled_post, "Platform not found")
                return False
            
            # Check if platform supports API posting
            if not platform.supports_api:
                logger.error(f"Platform {platform.name} does not support API posting")
                self._mark_failed(scheduled_post, f"Platform {platform.display_name} does not support API posting")
                return False
            
            # Get user's API key for the platform
            from app.models.models import ApiKey
            api_key = self.db.query(ApiKey).filter(
                and_(
                    ApiKey.user_id == scheduled_post.user_id,
                    ApiKey.platform_id == scheduled_post.platform_id,
                    ApiKey.is_active == True
                )
            ).first()
            
            if not api_key:
                logger.error(f"No API key found for user {scheduled_post.user_id} and platform {platform.name}")
                self._mark_failed(scheduled_post, f"No API key configured for {platform.display_name}")
                return False
            
            # Attempt to publish based on platform
            external_post_id = self._publish_to_platform(
                platform=platform,
                api_key=api_key,
                content=scheduled_post.content,
                media_urls=scheduled_post.media_urls
            )
            
            if external_post_id:
                self._mark_published(scheduled_post, external_post_id)
                logger.info(f"Successfully published post {scheduled_post.id} to {platform.name}")
                return True
            else:
                self._mark_failed(scheduled_post, "Failed to publish to platform")
                return False
                
        except Exception as e:
            logger.exception(f"Error publishing post {scheduled_post.id}: {str(e)}")
            self._mark_failed(scheduled_post, f"Publishing error: {str(e)}")
            return False
    
    def _publish_to_platform(
        self,
        platform: Platform,
        api_key,
        content: str,
        media_urls: Optional[str]
    ) -> Optional[str]:
        """
        Publish content to a specific platform.
        
        Returns the external post ID if successful, None otherwise.
        """
        # For now, return a mock external ID since we don't have actual API integrations
        # In production, this would call the actual platform APIs
        
        if platform.name == "twitter":
            return self._publish_to_twitter(api_key, content, media_urls)
        elif platform.name == "linkedin":
            return self._publish_to_linkedin(api_key, content, media_urls)
        elif platform.name == "bluesky":
            return self._publish_to_bluesky(api_key, content, media_urls)
        else:
            logger.warning(f"Publishing not implemented for platform: {platform.name}")
            return None
    
    def _publish_to_twitter(self, api_key, content: str, media_urls: Optional[str]) -> Optional[str]:
        """Publish to Twitter/X."""
        # Placeholder for actual Twitter API integration
        # Would use Tweepy or similar library
        logger.info(f"Would publish to Twitter: {content[:50]}...")
        # Return mock external ID for now
        import uuid
        return f"twitter_{uuid.uuid4().hex[:16]}"
    
    def _publish_to_linkedin(self, api_key, content: str, media_urls: Optional[str]) -> Optional[str]:
        """Publish to LinkedIn."""
        # Placeholder for actual LinkedIn API integration
        logger.info(f"Would publish to LinkedIn: {content[:50]}...")
        import uuid
        return f"linkedin_{uuid.uuid4().hex[:16]}"
    
    def _publish_to_bluesky(self, api_key, content: str, media_urls: Optional[str]) -> Optional[str]:
        """Publish to Bluesky."""
        # Placeholder for actual Bluesky AT Protocol integration
        logger.info(f"Would publish to Bluesky: {content[:50]}...")
        import uuid
        return f"bluesky_{uuid.uuid4().hex[:16]}"
    
    def _mark_published(self, scheduled_post: ScheduledPost, external_post_id: str):
        """Mark a scheduled post as published."""
        scheduled_post.status = "published"
        scheduled_post.published_at = datetime.utcnow()
        scheduled_post.external_post_id = external_post_id
        scheduled_post.error_message = None
        self.db.commit()
        self.db.refresh(scheduled_post)
    
    def _mark_failed(self, scheduled_post: ScheduledPost, error_message: str):
        """Mark a scheduled post as failed."""
        scheduled_post.status = "failed"
        scheduled_post.error_message = error_message
        self.db.commit()
        self.db.refresh(scheduled_post)
    
    def process_due_posts(self) -> dict:
        """
        Process all posts that are due for publishing.
        
        Returns a summary of processing results.
        """
        pending_posts = self.get_pending_posts()
        
        results = {
            "total": len(pending_posts),
            "published": 0,
            "failed": 0
        }
        
        for post in pending_posts:
            if self.publish_post(post):
                results["published"] += 1
            else:
                results["failed"] += 1
        
        return results


def run_scheduler(db: Session) -> dict:
    """
    Run the scheduler to process due posts.
    
    This function can be called by a background worker (celery, cron, etc.)
    """
    service = SchedulerService(db)
    return service.process_due_posts()
