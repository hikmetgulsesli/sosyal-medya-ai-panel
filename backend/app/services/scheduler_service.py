"""
Scheduler background worker service.
Polls for pending scheduled posts and publishes them at their scheduled time.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.database import SessionLocal
from app.models.models import ScheduledPost, Platform, ApiKey

logger = logging.getLogger(__name__)


class SchedulerWorker:
    """Background worker that processes scheduled posts."""
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize the scheduler worker.
        
        Args:
            check_interval: Seconds between checks for pending posts (default: 60)
        """
        self.check_interval = check_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background worker."""
        if self._running:
            logger.warning("Scheduler worker is already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Scheduler worker started (checking every {self.check_interval}s)")
    
    async def stop(self):
        """Stop the background worker."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduler worker stopped")
    
    async def _run_loop(self):
        """Main worker loop."""
        while self._running:
            try:
                await self._process_pending_posts()
            except Exception as e:
                logger.error(f"Error in scheduler worker: {e}", exc_info=True)
            
            await asyncio.sleep(self.check_interval)
    
    async def _process_pending_posts(self):
        """Process all pending posts that are due for publishing."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            
            # Find pending posts that should be published now
            pending_posts = db.query(ScheduledPost).filter(
                and_(
                    ScheduledPost.status == "pending",
                    ScheduledPost.scheduled_at <= now
                )
            ).all()
            
            if pending_posts:
                logger.info(f"Found {len(pending_posts)} posts ready to publish")
            
            for post in pending_posts:
                await self._publish_post(post, db)
                
        finally:
            db.close()
    
    async def _publish_post(self, post: ScheduledPost, db: Session):
        """
        Publish a single scheduled post.
        
        Args:
            post: The scheduled post to publish
            db: Database session
        """
        try:
            # Get platform info
            platform = db.query(Platform).filter(Platform.id == post.platform_id).first()
            if not platform:
                raise ValueError(f"Platform {post.platform_id} not found")
            
            # Check if user has API key for this platform
            api_key = db.query(ApiKey).filter(
                ApiKey.user_id == post.user_id,
                ApiKey.platform_id == post.platform_id,
                ApiKey.is_active == True
            ).first()
            
            if not api_key:
                raise ValueError(f"No active API key found for platform {platform.display_name}")
            
            # In a real implementation, we would call the platform's API here
            # For now, simulate successful publishing
            logger.info(f"Publishing post {post.id} to {platform.display_name}")
            
            # Simulate API call delay
            await asyncio.sleep(0.5)
            
            # Generate simulated external post ID
            external_post_id = f"published_{platform.name}_{int(datetime.utcnow().timestamp())}"
            
            # Update post status
            post.status = "published"
            post.published_at = datetime.utcnow()
            post.external_post_id = external_post_id
            post.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Successfully published post {post.id} with ID {external_post_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish post {post.id}: {e}")
            
            # Update post status to failed
            post.status = "failed"
            post.error_message = str(e)
            post.updated_at = datetime.utcnow()
            db.commit()
    
    async def publish_post_now(self, post_id: str, db: Session) -> dict:
        """
        Manually trigger publishing for a specific post.
        
        Args:
            post_id: ID of the post to publish
            db: Database session
            
        Returns:
            Dict with success status and message
        """
        post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
        
        if not post:
            return {"success": False, "message": "Post not found"}
        
        if post.status == "published":
            return {"success": False, "message": "Post already published"}
        
        await self._publish_post(post, db)
        
        if post.status == "published":
            return {
                "success": True,
                "message": "Post published successfully",
                "external_post_id": post.external_post_id
            }
        else:
            return {
                "success": False,
                "message": f"Failed to publish: {post.error_message}"
            }


# Global worker instance
_scheduler_worker: Optional[SchedulerWorker] = None


def get_scheduler_worker() -> SchedulerWorker:
    """Get or create the global scheduler worker instance."""
    global _scheduler_worker
    if _scheduler_worker is None:
        _scheduler_worker = SchedulerWorker()
    return _scheduler_worker


async def start_scheduler_worker():
    """Start the scheduler worker (called on app startup)."""
    worker = get_scheduler_worker()
    await worker.start()


async def stop_scheduler_worker():
    """Stop the scheduler worker (called on app shutdown)."""
    global _scheduler_worker
    if _scheduler_worker:
        await _scheduler_worker.stop()
        _scheduler_worker = None
