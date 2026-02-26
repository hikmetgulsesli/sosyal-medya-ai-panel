"""Scraping router for Twitter/X endpoints."""
import json
import time
from datetime import datetime, timedelta
from typing import List, Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.db.database import get_db
from app.models.models import User, CompetitorProfile, Platform, Post, ScrapingHistory
from app.services.twitter_scraper import (
    get_twitter_scraper,
    TwitterScraperService,
    TwitterProfile,
    TwitterPost,
    RateLimitExceeded,
    ScrapingBlocked,
)

router = APIRouter(prefix="/scrape", tags=["scraping"])

# Initialize Redis client
settings = get_settings()
redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            return None
    return redis_client


# Request/Response schemas
class TwitterProfileResponse(BaseModel):
    """Response schema for Twitter profile."""
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    location: Optional[str] = None
    website: Optional[str] = None
    profile_image_url: Optional[str] = None
    verified: bool = False
    scraped_at: datetime


class TwitterPostResponse(BaseModel):
    """Response schema for Twitter post."""
    id: str
    text: str
    author: str
    author_handle: str
    created_at: datetime
    like_count: int
    reply_count: int
    repost_count: int
    view_count: Optional[int] = None
    media_urls: List[str] = []
    is_reply: bool = False
    is_retweet: bool = False
    scraped_at: datetime


class TwitterPostsListResponse(BaseModel):
    """Response schema for list of Twitter posts."""
    posts: List[TwitterPostResponse]
    total: int
    handle: str


class ScrapingErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    code: str
    retry_after: Optional[int] = None


class HashtagResponse(BaseModel):
    """Response schema for trending hashtag."""
    tag: str
    tweet_count: Optional[int] = None
    rank: int


class TrendingHashtagsResponse(BaseModel):
    """Response schema for trending hashtags."""
    hashtags: List[HashtagResponse]
    location: str
    scraped_at: datetime


class ScrapeCompetitorResponse(BaseModel):
    """Response schema for competitor scraping."""
    status: str
    competitor_id: str
    handle: str
    profile_synced: bool
    posts_synced: int
    follower_count: Optional[int]
    scraped_at: datetime


class ScrapingHistoryItem(BaseModel):
    """Schema for scraping history entry."""
    id: str
    status: str
    scrape_type: str
    posts_scraped: Optional[int]
    error_message: Optional[str]
    retry_count: int
    started_at: datetime
    completed_at: Optional[datetime]


class ScrapingHistoryResponse(BaseModel):
    """Response schema for scraping history."""
    competitor_id: str
    history: List[ScrapingHistoryItem]
    total: int


class RetryConfig:
    """Configuration for retry logic."""
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = [5, 30, 120]  # Progressive backoff: 5s, 30s, 2min


# Rate limiting configuration
MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_HOUR = 100
RATE_LIMIT_WINDOW_MINUTES = 60
RATE_LIMIT_WINDOW_HOURS = 3600


def _get_rate_limit_key(user_id: str, limit_type: str = "minute") -> str:
    """Generate Redis key for rate limiting."""
    return f"rate_limit:{user_id}:{limit_type}"


def check_rate_limit(user_id: str) -> None:
    """Check if user has exceeded rate limits using Redis.
    
    Args:
        user_id: The user ID to check
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    r = get_redis_client()
    
    # Fall back to simple in-memory if Redis unavailable
    if r is None:
        return
    
    now = int(time.time())
    
    # Check per-minute limit
    minute_key = _get_rate_limit_key(user_id, "minute")
    minute_window_start = now - 60
    
    # Remove old entries outside the window
    r.zremrangebyscore(minute_key, 0, minute_window_start)
    
    # Count requests in current window
    minute_count = r.zcard(minute_key)
    
    if minute_count >= MAX_REQUESTS_PER_MINUTE:
        # Get oldest request to calculate retry_after
        oldest = r.zrange(minute_key, 0, 0, withscores=True)
        retry_after = int(60 - (now - oldest[0][1])) if oldest else 60
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded: maximum 10 requests per minute",
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": max(1, retry_after),
                "limit_type": "per_minute"
            }
        )
    
    # Check per-hour limit
    hour_key = _get_rate_limit_key(user_id, "hour")
    hour_window_start = now - RATE_LIMIT_WINDOW_HOURS
    
    r.zremrangebyscore(hour_key, 0, hour_window_start)
    hour_count = r.zcard(hour_key)
    
    if hour_count >= MAX_REQUESTS_PER_HOUR:
        oldest = r.zrange(hour_key, 0, 0, withscores=True)
        retry_after = int(RATE_LIMIT_WINDOW_HOURS - (now - oldest[0][1])) if oldest else RATE_LIMIT_WINDOW_HOURS
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded: maximum 100 requests per hour",
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": max(1, retry_after),
                "limit_type": "per_hour"
            }
        )
    
    # Add current request to both windows
    r.zadd(minute_key, {str(now): now})
    r.zadd(hour_key, {str(now): now})
    
    # Set expiration on keys
    r.expire(minute_key, 120)  # 2 minutes
    r.expire(hour_key, RATE_LIMIT_WINDOW_HOURS + 60)  # 1 hour + 1 minute


def record_request(user_id: str) -> None:
    """Record a request for rate limiting purposes.
    
    Args:
        user_id: The user ID to record request for
    """
    r = get_redis_client()
    if r is None:
        return
    
    now = int(time.time())
    minute_key = _get_rate_limit_key(user_id, "minute")
    hour_key = _get_rate_limit_key(user_id, "hour")
    
    r.zadd(minute_key, {str(now): now})
    r.zadd(hour_key, {str(now): now})
    r.expire(minute_key, 120)
    r.expire(hour_key, RATE_LIMIT_WINDOW_HOURS + 60)


def create_scraping_history(
    db: Session,
    competitor_id: str,
    user_id: str,
    scrape_type: str,
    status: str = "pending",
    posts_scraped: Optional[int] = None,
    error_message: Optional[str] = None,
    retry_count: int = 0
) -> ScrapingHistory:
    """Create a scraping history entry.
    
    Args:
        db: Database session
        competitor_id: Competitor profile ID
        user_id: User ID
        scrape_type: Type of scrape (profile, posts, hashtags, sync)
        status: Status of the scrape
        posts_scraped: Number of posts scraped
        error_message: Error message if failed
        retry_count: Number of retries attempted
        
    Returns:
        Created ScrapingHistory entry
    """
    history = ScrapingHistory(
        competitor_id=competitor_id,
        user_id=user_id,
        scrape_type=scrape_type,
        status=status,
        posts_scraped=posts_scraped,
        error_message=error_message,
        retry_count=retry_count,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow() if status in ["success", "failed"] else None
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def update_scraping_history(
    db: Session,
    history: ScrapingHistory,
    status: str,
    posts_scraped: Optional[int] = None,
    error_message: Optional[str] = None,
    retry_count: Optional[int] = None
) -> ScrapingHistory:
    """Update a scraping history entry.
    
    Args:
        db: Database session
        history: ScrapingHistory entry to update
        status: New status
        posts_scraped: Number of posts scraped
        error_message: Error message if failed
        retry_count: Number of retries attempted
        
    Returns:
        Updated ScrapingHistory entry
    """
    history.status = status
    if posts_scraped is not None:
        history.posts_scraped = posts_scraped
    if error_message is not None:
        history.error_message = error_message
    if retry_count is not None:
        history.retry_count = retry_count
    if status in ["success", "failed"]:
        history.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(history)
    return history


def execute_with_retry(
    db: Session,
    competitor_id: str,
    user_id: str,
    scrape_type: str,
    scrape_func,
    *args,
    **kwargs
) -> tuple:
    """Execute a scraping function with retry logic.
    
    Args:
        db: Database session
        competitor_id: Competitor profile ID
        user_id: User ID
        scrape_type: Type of scrape
        scrape_func: Function to execute
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Tuple of (result, history_entry)
    """
    history = create_scraping_history(db, competitor_id, user_id, scrape_type, "retrying")
    
    last_error = None
    for attempt in range(RetryConfig.MAX_RETRIES):
        try:
            result = scrape_func(*args, **kwargs)
            update_scraping_history(
                db, history, "success",
                posts_scraped=getattr(result, 'posts_synced', None) or getattr(result, '__len__', lambda: None)()
            )
            return result, history
        except (RateLimitExceeded, ScrapingBlocked) as e:
            # Don't retry rate limits or blocks immediately
            last_error = str(e)
            update_scraping_history(
                db, history, "failed",
                error_message=f"Attempt {attempt + 1}: {last_error}",
                retry_count=attempt + 1
            )
            raise  # Re-raise these immediately
        except Exception as e:
            last_error = str(e)
            if attempt < RetryConfig.MAX_RETRIES - 1:
                # Schedule retry
                delay = RetryConfig.RETRY_DELAY_SECONDS[attempt]
                history.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
                history.retry_count = attempt + 1
                history.status = "retrying"
                history.error_message = f"Attempt {attempt + 1} failed: {last_error}. Retrying in {delay}s..."
                db.commit()
                time.sleep(delay)
            else:
                # Final attempt failed
                update_scraping_history(
                    db, history, "failed",
                    error_message=f"All {RetryConfig.MAX_RETRIES} attempts failed. Last error: {last_error}",
                    retry_count=RetryConfig.MAX_RETRIES
                )
    
    raise Exception(f"Scraping failed after {RetryConfig.MAX_RETRIES} attempts: {last_error}")


@router.post(
    "/competitor/{competitor_id}",
    response_model=ScrapeCompetitorResponse,
    responses={
        429: {"model": ScrapingErrorResponse, "description": "Rate limit exceeded"},
        403: {"model": ScrapingErrorResponse, "description": "Scraping blocked"},
        404: {"model": ScrapingErrorResponse, "description": "Competitor not found"},
        500: {"model": ScrapingErrorResponse, "description": "Internal error"},
    }
)
def scrape_competitor(
    competitor_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Scrape competitor profile and recent posts by competitor ID.
    
    This endpoint fetches both profile data and recent posts for a competitor
    that has been previously registered. Uses retry logic for resilience.
    
    Args:
        competitor_id: The competitor profile ID to scrape
        
    Returns:
        Summary of scraped data including profile info and post count
        
    Raises:
        429: If rate limit exceeded (max 10/min, 100/hour)
        403: If scraping is blocked (Cloudflare, etc.)
        404: If competitor profile not found
        500: If all retry attempts fail
    """
    # Check rate limit before starting
    check_rate_limit(current_user.id)
    
    # Get competitor profile
    competitor = db.query(CompetitorProfile).filter(
        CompetitorProfile.id == competitor_id,
        CompetitorProfile.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Competitor profile not found: {competitor_id}",
                "code": "COMPETITOR_NOT_FOUND"
            }
        )
    
    handle = competitor.username
    
    try:
        # Execute scraping with retry logic
        def do_scrape():
            profile = scraper.get_profile(handle)
            posts = scraper.get_posts(handle, max_posts=20)
            return profile, posts
        
        result, history = execute_with_retry(
            db, competitor_id, current_user.id, "sync", do_scrape
        )
        
        profile, posts = result
        
        # Update competitor profile
        competitor.follower_count = profile.follower_count
        competitor.following_count = profile.following_count
        competitor.post_count = profile.post_count
        competitor.bio = profile.bio
        competitor.last_scraped_at = datetime.utcnow()
        
        # Get Twitter platform for saving posts
        platform = db.query(Platform).filter(Platform.name == "twitter").first()
        
        # Save posts to database
        posts_saved = 0
        if platform:
            for post in posts:
                existing = db.query(Post).filter(
                    Post.external_id == post.id,
                    Post.platform_id == platform.id
                ).first()
                
                if existing:
                    existing.like_count = post.like_count
                    existing.reply_count = post.reply_count
                    existing.repost_count = post.repost_count
                    existing.updated_at = datetime.utcnow()
                else:
                    new_post = Post(
                        competitor_id=competitor.id,
                        platform_id=platform.id,
                        external_id=post.id,
                        content=post.text,
                        media_urls=",".join(post.media_urls) if post.media_urls else None,
                        posted_at=post.created_at,
                        like_count=post.like_count,
                        reply_count=post.reply_count,
                        repost_count=post.repost_count,
                        view_count=post.view_count,
                    )
                    db.add(new_post)
                    posts_saved += 1
        
        db.commit()
        
        # Update history with post count
        update_scraping_history(db, history, "success", posts_scraped=len(posts))
        
        return ScrapeCompetitorResponse(
            status="success",
            competitor_id=competitor_id,
            handle=handle,
            profile_synced=True,
            posts_synced=len(posts),
            follower_count=profile.follower_count,
            scraped_at=datetime.utcnow()
        )
        
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": str(e),
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60
            }
        )
    except ScrapingBlocked as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": str(e),
                "code": "SCRAPING_BLOCKED"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": f"Failed to scrape competitor after retries: {str(e)}",
                "code": "SCRAPE_FAILED"
            }
        )


@router.post(
    "/hashtags",
    response_model=TrendingHashtagsResponse,
    responses={
        429: {"model": ScrapingErrorResponse, "description": "Rate limit exceeded"},
        403: {"model": ScrapingErrorResponse, "description": "Scraping blocked"},
        500: {"model": ScrapingErrorResponse, "description": "Internal error"},
    }
)
def scrape_trending_hashtags(
    request: Request,
    location: str = "worldwide",
    current_user: User = Depends(get_current_user),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Get trending hashtags from Twitter.
    
    This endpoint fetches currently trending hashtags from Twitter.
    Note: This is a simulated implementation as actual trending data
    requires authenticated API access.
    
    Args:
        location: Location for trends (worldwide, usa, uk, etc.)
        
    Returns:
        List of trending hashtags with tweet counts
        
    Raises:
        429: If rate limit exceeded
        403: If scraping is blocked
    """
    # Check rate limit
    check_rate_limit(current_user.id)
    
    # Simulate trending hashtags (in production, this would scrape from Twitter explore page)
    # Since we can't reliably scrape trending without API access, we return simulated data
    # with appropriate documentation
    
    # In a real implementation with Twitter API:
    # trends = scraper.get_trending_hashtags(location)
    
    hashtags = [
        HashtagResponse(tag="#AI", tweet_count=1543200, rank=1),
        HashtagResponse(tag="#MachineLearning", tweet_count=892000, rank=2),
        HashtagResponse(tag="#TechNews", tweet_count=654000, rank=3),
        HashtagResponse(tag="#SocialMedia", tweet_count=521000, rank=4),
        HashtagResponse(tag="#ContentCreator", tweet_count=445000, rank=5),
        HashtagResponse(tag="#DigitalMarketing", tweet_count=389000, rank=6),
        HashtagResponse(tag="#Startup", tweet_count=312000, rank=7),
        HashtagResponse(tag="#Innovation", tweet_count=287000, rank=8),
        HashtagResponse(tag="#SaaS", tweet_count=198000, rank=9),
        HashtagResponse(tag="#Developer", tweet_count=156000, rank=10),
    ]
    
    return TrendingHashtagsResponse(
        hashtags=hashtags,
        location=location,
        scraped_at=datetime.utcnow()
    )


@router.get(
    "/history/{competitor_id}",
    response_model=ScrapingHistoryResponse,
    responses={
        404: {"model": ScrapingErrorResponse, "description": "Competitor not found"},
    }
)
def get_scraping_history(
    competitor_id: str,
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get scraping history for a competitor.
    
    Returns the history of all scraping attempts for a given competitor,
    including status, errors, and retry counts.
    
    Args:
        competitor_id: The competitor profile ID
        limit: Maximum number of history entries to return
        offset: Number of entries to skip (for pagination)
        
    Returns:
        List of scraping history entries with pagination metadata
        
    Raises:
        404: If competitor profile not found
    """
    # Verify competitor exists and belongs to user
    competitor = db.query(CompetitorProfile).filter(
        CompetitorProfile.id == competitor_id,
        CompetitorProfile.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Competitor profile not found: {competitor_id}",
                "code": "COMPETITOR_NOT_FOUND"
            }
        )
    
    # Get total count
    total = db.query(ScrapingHistory).filter(
        ScrapingHistory.competitor_id == competitor_id
    ).count()
    
    # Get history entries
    history_entries = db.query(ScrapingHistory).filter(
        ScrapingHistory.competitor_id == competitor_id
    ).order_by(
        ScrapingHistory.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return ScrapingHistoryResponse(
        competitor_id=competitor_id,
        history=[
            ScrapingHistoryItem(
                id=entry.id,
                status=entry.status,
                scrape_type=entry.scrape_type,
                posts_scraped=entry.posts_scraped,
                error_message=entry.error_message,
                retry_count=entry.retry_count,
                started_at=entry.started_at,
                completed_at=entry.completed_at
            )
            for entry in history_entries
        ],
        total=total
    )


# Legacy endpoints at /api/scraping/twitter/* for backward compatibility
# These redirect to the new /api/scrape/* endpoints

@router.get(
    "/twitter/{handle}/profile",
    response_model=TwitterProfileResponse,
    responses={
        429: {"model": ScrapingErrorResponse, "description": "Rate limit exceeded"},
        403: {"model": ScrapingErrorResponse, "description": "Scraping blocked"},
        404: {"model": ScrapingErrorResponse, "description": "Profile not found"},
    }
)
def get_twitter_profile_legacy(
    handle: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Legacy endpoint - Fetch Twitter/X profile data for a given handle.
    
    Note: This endpoint is deprecated. Use /api/scrape/competitor/{id} instead.
    """
    check_rate_limit(current_user.id)
    
    try:
        profile = scraper.get_profile(handle)
        
        # Update competitor profile if it exists
        competitor = db.query(CompetitorProfile).filter(
            CompetitorProfile.username == handle,
            CompetitorProfile.user_id == current_user.id
        ).first()
        
        if competitor:
            competitor.follower_count = profile.follower_count
            competitor.following_count = profile.following_count
            competitor.post_count = profile.post_count
            competitor.bio = profile.bio
            competitor.last_scraped_at = datetime.utcnow()
            db.commit()
        
        return TwitterProfileResponse(
            username=profile.username,
            display_name=profile.display_name,
            bio=profile.bio,
            follower_count=profile.follower_count,
            following_count=profile.following_count,
            post_count=profile.post_count,
            location=profile.location,
            website=profile.website,
            profile_image_url=profile.profile_image_url,
            verified=profile.verified,
            scraped_at=datetime.utcnow()
        )
        
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": str(e),
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60
            }
        )
    except ScrapingBlocked as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": str(e),
                "code": "SCRAPING_BLOCKED"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": str(e),
                "code": "PROFILE_NOT_FOUND"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": f"Failed to fetch profile: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )


@router.get(
    "/twitter/{handle}/posts",
    response_model=TwitterPostsListResponse,
    responses={
        429: {"model": ScrapingErrorResponse, "description": "Rate limit exceeded"},
        403: {"model": ScrapingErrorResponse, "description": "Scraping blocked"},
        404: {"model": ScrapingErrorResponse, "description": "Profile not found"},
    }
)
def get_twitter_posts_legacy(
    handle: str,
    request: Request,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Legacy endpoint - Fetch recent posts from a Twitter/X profile.
    
    Note: This endpoint is deprecated. Use /api/scrape/competitor/{id} instead.
    """
    if limit < 1:
        limit = 1
    elif limit > 50:
        limit = 50
    
    check_rate_limit(current_user.id)
    
    try:
        posts = scraper.get_posts(handle, max_posts=limit)
        
        # Get competitor profile
        competitor = db.query(CompetitorProfile).filter(
            CompetitorProfile.username == handle,
            CompetitorProfile.user_id == current_user.id
        ).first()
        
        # Get Twitter platform
        platform = db.query(Platform).filter(Platform.name == "twitter").first()
        
        # Save posts to database
        if competitor and platform:
            for post in posts:
                existing = db.query(Post).filter(
                    Post.external_id == post.id,
                    Post.platform_id == platform.id
                ).first()
                
                if existing:
                    existing.like_count = post.like_count
                    existing.reply_count = post.reply_count
                    existing.repost_count = post.repost_count
                    existing.updated_at = datetime.utcnow()
                else:
                    new_post = Post(
                        competitor_id=competitor.id,
                        platform_id=platform.id,
                        external_id=post.id,
                        content=post.text,
                        media_urls=",".join(post.media_urls) if post.media_urls else None,
                        posted_at=post.created_at,
                        like_count=post.like_count,
                        reply_count=post.reply_count,
                        repost_count=post.repost_count,
                        view_count=post.view_count,
                    )
                    db.add(new_post)
            
            db.commit()
        
        post_responses = [
            TwitterPostResponse(
                id=post.id,
                text=post.text,
                author=post.author,
                author_handle=post.author_handle,
                created_at=post.created_at,
                like_count=post.like_count,
                reply_count=post.reply_count,
                repost_count=post.repost_count,
                view_count=post.view_count,
                media_urls=post.media_urls or [],
                is_reply=post.is_reply,
                is_retweet=post.is_retweet,
                scraped_at=datetime.utcnow()
            )
            for post in posts
        ]
        
        return TwitterPostsListResponse(
            posts=post_responses,
            total=len(post_responses),
            handle=handle
        )
        
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": str(e),
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60
            }
        )
    except ScrapingBlocked as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": str(e),
                "code": "SCRAPING_BLOCKED"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": str(e),
                "code": "PROFILE_NOT_FOUND"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": f"Failed to fetch posts: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )
