from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session

from app.models.models import AnalyticsEvent, Post, CompetitorProfile, Platform


class AnalyticsService:
    """Service for analytics operations."""
    
    @staticmethod
    def track_event(
        db: Session,
        post_id: str,
        event_type: str,
        metric_name: str,
        metric_value: int
    ) -> AnalyticsEvent:
        """Track a new analytics event."""
        event = AnalyticsEvent(
            post_id=post_id,
            event_type=event_type,
            metric_name=metric_name,
            metric_value=metric_value,
            recorded_at=datetime.utcnow()
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    
    @staticmethod
    def get_post_metrics(db: Session, post_id: str) -> Optional[dict]:
        """Get metrics for a specific post."""
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return None
        
        # Get all events for this post
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.post_id == post_id
        ).order_by(desc(AnalyticsEvent.recorded_at)).all()
        
        # Calculate totals by metric type
        event_totals = {}
        for event in events:
            if event.metric_name not in event_totals:
                event_totals[event.metric_name] = 0
            event_totals[event.metric_name] += event.metric_value
        
        # Get platform and competitor info
        platform = db.query(Platform).filter(Platform.id == post.platform_id).first()
        competitor = db.query(CompetitorProfile).filter(
            CompetitorProfile.id == post.competitor_id
        ).first()
        
        # Calculate total engagement
        total_engagement = (
            event_totals.get('like', 0) +
            event_totals.get('reply', 0) +
            event_totals.get('repost', 0) +
            event_totals.get('share', 0)
        )
        
        # Calculate engagement rate (if we have view data)
        view_count = event_totals.get('view', post.view_count or 0)
        engagement_rate = (total_engagement / view_count * 100) if view_count and view_count > 0 else 0.0
        
        return {
            'post_id': post.id,
            'external_id': post.external_id,
            'content': post.content,
            'platform_name': platform.display_name if platform else None,
            'competitor_username': competitor.username if competitor else None,
            'like_count': event_totals.get('like', post.like_count),
            'reply_count': event_totals.get('reply', post.reply_count),
            'repost_count': event_totals.get('repost', post.repost_count),
            'view_count': view_count,
            'share_count': event_totals.get('share', 0),
            'total_engagement': total_engagement,
            'engagement_rate': round(engagement_rate, 2),
            'events': events,
            'posted_at': post.posted_at,
            'scraped_at': post.scraped_at,
            'last_updated': max([e.recorded_at for e in events]) if events else post.updated_at
        }
    
    @staticmethod
    def get_user_posts(db: Session, user_id: str) -> List[Post]:
        """Get all posts for a user's competitors."""
        return db.query(Post).join(
            CompetitorProfile,
            Post.competitor_id == CompetitorProfile.id
        ).filter(
            CompetitorProfile.user_id == user_id
        ).all()
    
    @staticmethod
    def calculate_growth_metrics(
        db: Session,
        user_id: str,
        days: int
    ) -> dict:
        """Calculate growth metrics for a specific time period."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get posts in this period
        posts = db.query(Post).join(
            CompetitorProfile,
            Post.competitor_id == CompetitorProfile.id
        ).filter(
            CompetitorProfile.user_id == user_id,
            Post.posted_at >= start_date
        ).all()
        
        # Get events in this period
        events = db.query(AnalyticsEvent).join(
            Post,
            AnalyticsEvent.post_id == Post.id
        ).join(
            CompetitorProfile,
            Post.competitor_id == CompetitorProfile.id
        ).filter(
            CompetitorProfile.user_id == user_id,
            AnalyticsEvent.recorded_at >= start_date
        ).all()
        
        # Calculate totals
        total_likes = sum(e.metric_value for e in events if e.metric_name == 'like')
        total_replies = sum(e.metric_value for e in events if e.metric_name == 'reply')
        total_reposts = sum(e.metric_value for e in events if e.metric_name == 'repost')
        
        # Calculate follower delta (from competitor profile changes)
        competitors = db.query(CompetitorProfile).filter(
            CompetitorProfile.user_id == user_id
        ).all()
        
        current_followers = sum(c.follower_count or 0 for c in competitors)
        
        # Estimate previous followers (simplified - in production would track history)
        # For now, we'll use a placeholder calculation
        follower_delta = 0  # Would need historical data for accurate calculation
        follower_growth_rate = 0.0
        
        # Calculate average engagement rate
        total_engagement = total_likes + total_replies + total_reposts
        total_views = sum(e.metric_value for e in events if e.metric_name == 'view')
        avg_engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0.0
        
        return {
            'period': f'{days}d',
            'follower_delta': follower_delta,
            'follower_growth_rate': round(follower_growth_rate, 2),
            'post_count': len(posts),
            'avg_engagement_rate': round(avg_engagement_rate, 2),
            'total_likes': total_likes,
            'total_replies': total_replies,
            'total_reposts': total_reposts
        }
    
    @staticmethod
    def get_platform_overview(db: Session, user_id: str, platform_id: str) -> dict:
        """Get overview for a specific platform."""
        platform = db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            return None
        
        # Get posts for this platform
        posts = db.query(Post).join(
            CompetitorProfile,
            Post.competitor_id == CompetitorProfile.id
        ).filter(
            CompetitorProfile.user_id == user_id,
            Post.platform_id == platform_id
        ).all()
        
        # Get competitors for this platform
        competitors = db.query(CompetitorProfile).filter(
            CompetitorProfile.user_id == user_id,
            CompetitorProfile.platform_id == platform_id
        ).all()
        
        # Calculate average engagement
        total_engagement = 0
        total_views = 0
        for post in posts:
            total_engagement += post.like_count + post.reply_count + post.repost_count
            if post.view_count:
                total_views += post.view_count
        
        avg_engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0.0
        
        # Get top performing posts
        top_posts = sorted(
            posts,
            key=lambda p: p.like_count + p.reply_count + p.repost_count,
            reverse=True
        )[:5]
        
        return {
            'platform_id': platform_id,
            'platform_name': platform.display_name,
            'total_posts': len(posts),
            'total_competitors': len(competitors),
            'avg_engagement_rate': round(avg_engagement_rate, 2),
            'top_performing_posts': [
                {
                    'post_id': p.id,
                    'content': p.content[:100] if p.content else None,
                    'engagement': p.like_count + p.reply_count + p.repost_count
                }
                for p in top_posts
            ]
        }
    
    @staticmethod
    def get_dashboard_overview(db: Session, user_id: str) -> dict:
        """Get comprehensive dashboard overview."""
        # Get all user's posts
        posts = AnalyticsService.get_user_posts(db, user_id)
        
        # Get all events for user's posts
        post_ids = [p.id for p in posts]
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.post_id.in_(post_ids)
        ).order_by(desc(AnalyticsEvent.recorded_at)).limit(50).all()
        
        # Get user's competitors
        competitors = db.query(CompetitorProfile).filter(
            CompetitorProfile.user_id == user_id
        ).all()
        
        # Get platforms
        platform_ids = list(set(p.platform_id for p in posts))
        platforms = db.query(Platform).filter(Platform.id.in_(platform_ids)).all()
        
        # Calculate totals
        total_likes = sum(e.metric_value for e in events if e.metric_name == 'like')
        total_replies = sum(e.metric_value for e in events if e.metric_name == 'reply')
        total_reposts = sum(e.metric_value for e in events if e.metric_name == 'repost')
        total_shares = sum(e.metric_value for e in events if e.metric_name == 'share')
        total_views = sum(e.metric_value for e in events if e.metric_name == 'view')
        
        # Calculate growth metrics
        growth_7d = AnalyticsService.calculate_growth_metrics(db, user_id, 7)
        growth_30d = AnalyticsService.calculate_growth_metrics(db, user_id, 30)
        growth_90d = AnalyticsService.calculate_growth_metrics(db, user_id, 90)
        
        # Get platform overviews
        platform_overviews = [
            AnalyticsService.get_platform_overview(db, user_id, pid)
            for pid in platform_ids
        ]
        
        # Get top posts by engagement
        top_posts = sorted(
            posts,
            key=lambda p: p.like_count + p.reply_count + p.repost_count,
            reverse=True
        )[:10]
        
        # Serialize top posts
        top_posts_serialized = []
        for post in top_posts:
            platform = db.query(Platform).filter(Platform.id == post.platform_id).first()
            competitor = db.query(CompetitorProfile).filter(
                CompetitorProfile.id == post.competitor_id
            ).first()
            
            # Get events for this post
            post_events = db.query(AnalyticsEvent).filter(
                AnalyticsEvent.post_id == post.id
            ).order_by(desc(AnalyticsEvent.recorded_at)).all()
            
            # Calculate totals
            event_totals = {}
            for event in post_events:
                if event.metric_name not in event_totals:
                    event_totals[event.metric_name] = 0
                event_totals[event.metric_name] += event.metric_value
            
            total_engagement = (
                event_totals.get('like', post.like_count) +
                event_totals.get('reply', post.reply_count) +
                event_totals.get('repost', post.repost_count) +
                event_totals.get('share', 0)
            )
            
            view_count = event_totals.get('view', post.view_count or 0)
            engagement_rate = (total_engagement / view_count * 100) if view_count and view_count > 0 else 0.0
            
            top_posts_serialized.append({
                'post_id': post.id,
                'external_id': post.external_id,
                'content': post.content,
                'platform_name': platform.display_name if platform else None,
                'competitor_username': competitor.username if competitor else None,
                'like_count': event_totals.get('like', post.like_count),
                'reply_count': event_totals.get('reply', post.reply_count),
                'repost_count': event_totals.get('repost', post.repost_count),
                'view_count': view_count,
                'share_count': event_totals.get('share', 0),
                'total_engagement': total_engagement,
                'engagement_rate': round(engagement_rate, 2),
                'events': post_events,
                'posted_at': post.posted_at,
                'scraped_at': post.scraped_at,
                'last_updated': max([e.recorded_at for e in post_events]) if post_events else post.updated_at
            })
        
        return {
            'user_id': user_id,
            'total_posts_tracked': len(posts),
            'total_competitors': len(competitors),
            'total_platforms': len(platforms),
            'total_likes': total_likes,
            'total_replies': total_replies,
            'total_reposts': total_reposts,
            'total_shares': total_shares,
            'total_views': total_views,
            'growth_7d': growth_7d,
            'growth_30d': growth_30d,
            'growth_90d': growth_90d,
            'platform_overviews': platform_overviews,
            'recent_events': events[:10],
            'top_posts': top_posts_serialized,
            'generated_at': datetime.utcnow()
        }
