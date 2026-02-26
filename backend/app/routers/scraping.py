"""Scraping router for Twitter/X endpoints."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.auth import get_current_user
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

router = APIRouter(prefix="/scraping", tags=["scraping"])

# Router for new scrape endpoints (US-011)
scrape_router = APIRouter(prefix="/scrape", tags=["scraping"])


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


class ScrapeCompetitorRequest(BaseModel):
    """Request schema for scraping competitor."""
    posts_limit: int = 20
    sync_profile: bool = True


class ScrapeCompetitorResponse(BaseModel):
    """Response schema for scraping competitor."""
    competitor_id: str
    username: str
    profile_synced: bool
    posts_scraped: int
    posts: List[TwitterPostResponse]
    scraped_at: datetime


class TrendingHashtagResponse(BaseModel):
    """Response schema for trending hashtag."""
    rank: int
    hashtag: str
    volume: Optional[int]
    scraped_at: datetime


class TrendingHashtagsResponse(BaseModel):
    """Response schema for trending hashtags list."""
    hashtags: List[TrendingHashtagResponse]
    location: str
    total: int
    scraped_at: datetime


class ScrapingHistoryResponse(BaseModel):
    """Response schema for scraping history entry."""
    id: str
    competitor_id: Optional[str]
    operation_type: str
    status: str
    posts_scraped: Optional[int]
    error_message: Optional[str]
    retry_count: int
    started_at: datetime
    completed_at: Optional[datetime]


class ScrapingHistoryListResponse(BaseModel):
    """Response schema for scraping history list."""
    history: List[ScrapingHistoryResponse]
    total: int
    competitor_id: str


# Rate limiting storage (in production, use Redis)
_request_timestamps: dict = {}
MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_HOUR = 100


class RateLimitChecker:
    """Rate limiting service with tiered limits."""
    
    def __init__(self):
        self._timestamps: dict = {}
    
    def check_rate_limit(
        self,
        request: Request,
        per_minute: int = MAX_REQUESTS_PER_MINUTE,
        per_hour: int = MAX_REQUESTS_PER_HOUR
    ) -> None:
        """Check if request exceeds rate limit.
        
        Args:
            request: FastAPI request object
            per_minute: Max requests per minute
            per_hour: Max requests per hour
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        client_ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()
        now_ts = now.timestamp()
        
        # Get timestamps for this IP
        timestamps = self._timestamps.get(client_ip, [])
        
        # Filter to relevant time windows
        one_minute_ago = now_ts - 60
        one_hour_ago = now_ts - 3600
        
        recent_requests = [ts for ts in timestamps if ts > one_minute_ago]
        hourly_requests = [ts for ts in timestamps if ts > one_hour_ago]
        
        # Check per-minute limit
        if len(recent_requests) >= per_minute:
            retry_after = 60 - int(now_ts - recent_requests[0])
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": max(1, retry_after)
                }
            )
        
        # Check per-hour limit (more strict for scraping)
        if len(hourly_requests) >= per_hour:
            retry_after = 3600 - int(now_ts - hourly_requests[0])
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Hourly rate limit exceeded",
                    "code": "HOURLY_RATE_LIMIT_EXCEEDED",
                    "retry_after": max(1, retry_after)
                }
            )
        
        # Add current request
        hourly_requests.append(now_ts)
        self._timestamps[client_ip] = hourly_requests


# Singleton rate limiter
_rate_limiter = RateLimitChecker()


def check_rate_limit(request: Request) -> None:
    """Check if request exceeds rate limit (legacy compatibility)."""
    _rate_limiter.check_rate_limit(request)


@router.get(
    "/twitter/{handle}/profile",
    response_model=TwitterProfileResponse,
    responses={
        429: {"model": ScrapingErrorResponse, "description": "Rate limit exceeded"},
        403: {"model": ScrapingErrorResponse, "description": "Scraping blocked"},
        404: {"model": ScrapingErrorResponse, "description": "Profile not found"},
    }
)
def get_twitter_profile(
    handle: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Fetch Twitter/X profile data for a given handle.
    
    Args:
        handle: Twitter username (without @)
        
    Returns:
        Twitter profile data with follower counts, bio, etc.
        
    Raises:
        429: If rate limit exceeded (max 10 requests/minute)
        403: If scraping is blocked (Cloudflare, etc.)
        404: If profile not found
    """
    # Check rate limit
    check_rate_limit(request)
    
    try:
        # Fetch profile
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
def get_twitter_posts(
    handle: str,
    request: Request,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Fetch recent posts from a Twitter/X profile.
    
    Args:
        handle: Twitter username (without @)
        limit: Maximum number of posts to fetch (default 20, max 50)
        
    Returns:
        List of posts with engagement metrics
        
    Raises:
        429: If rate limit exceeded (max 10 requests/minute)
        403: If scraping is blocked (Cloudflare, etc.)
        404: If profile not found
    """
    # Validate limit
    if limit < 1:
        limit = 1
    elif limit > 50:
        limit = 50
    
    # Check rate limit
    check_rate_limit(request)
    
    try:
        # Fetch posts
        posts = scraper.get_posts(handle, max_posts=limit)
        
        # Get or create competitor profile
        competitor = db.query(CompetitorProfile).filter(
            CompetitorProfile.username == handle,
            CompetitorProfile.user_id == current_user.id
        ).first()
        
        # Get Twitter platform
        platform = db.query(Platform).filter(Platform.name == "twitter").first()
        
        # Save posts to database
        if competitor and platform:
            for post in posts:
                # Check if post already exists
                existing = db.query(Post).filter(
                    Post.external_id == post.id,
                    Post.platform_id == platform.id
                ).first()
                
                if existing:
                    # Update engagement metrics
                    existing.like_count = post.like_count
                    existing.reply_count = post.reply_count
                    existing.repost_count = post.repost_count
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new post
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
        
        # Convert to response format
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


@router.post(
    "/twitter/{handle}/sync",
    response_model=dict,
    responses={
        429: {"model": ScrapingErrorResponse, "description": "Rate limit exceeded"},
        403: {"model": ScrapingErrorResponse, "description": "Scraping blocked"},
        404: {"model": ScrapingErrorResponse, "description": "Profile not found"},
    }
)
def sync_twitter_profile(
    handle: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Sync both profile and posts for a Twitter/X handle.
    
    This is a convenience endpoint that fetches both profile data
    and recent posts in one request.
    
    Args:
        handle: Twitter username (without @)
        
    Returns:
        Summary of synced data
        
    Raises:
        429: If rate limit exceeded (max 10 requests/minute)
        403: If scraping is blocked (Cloudflare, etc.)
        404: If profile not found
    """
    # Check rate limit (counts as 2 requests)
    check_rate_limit(request)
    check_rate_limit(request)  # Double count for profile + posts
    
    try:
        # Fetch profile
        profile = scraper.get_profile(handle)
        
        # Fetch posts
        posts = scraper.get_posts(handle, max_posts=20)
        
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
        
        return {
            "status": "success",
            "handle": handle,
            "profile_synced": True,
            "posts_synced": len(posts),
            "follower_count": profile.follower_count,
            "synced_at": datetime.utcnow().isoformat()
        }
        
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
                "error": f"Failed to sync profile: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )


# =============================================================================
# NEW ENDPOINTS FOR US-011
# =============================================================================


@scrape_router.post(
    "/competitor/{competitor_id}",
    response_model=ScrapeCompetitorResponse,
    responses={
        429: {"model": ScrapingErrorResponse, "description": "Rate limit exceeded"},
        403: {"model": ScrapingErrorResponse, "description": "Scraping blocked"},
        404: {"model": ScrapingErrorResponse, "description": "Competitor not found"},
    }
)
def scrape_competitor(
    competitor_id: str,
    scrape_request: ScrapeCompetitorRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Scrape competitor profile and recent posts by competitor ID.
    
    This endpoint scrapes a competitor's profile data and recent posts
    and saves them to the database. Includes retry logic for failed scrapes.
    
    Args:
        competitor_id: ID of the competitor to scrape
        scrape_request: Scrape options (posts_limit, sync_profile)
        
    Returns:
        Scraped data summary with posts
        
    Raises:
        429: If rate limit exceeded
        403: If scraping is blocked
        404: If competitor not found
        400: If competitor platform is not Twitter
    """
    # Validate posts limit
    posts_limit = max(1, min(scrape_request.posts_limit, 50))
    
    # Check rate limit (more restrictive for competitor scraping)
    _rate_limiter.check_rate_limit(request, per_minute=5, per_hour=50)
    
    # Find competitor
    competitor = db.query(CompetitorProfile).filter(
        CompetitorProfile.id == competitor_id,
        CompetitorProfile.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Competitor not found: {competitor_id}",
                "code": "COMPETITOR_NOT_FOUND"
            }
        )
    
    # Check if platform is Twitter
    platform = db.query(Platform).filter(Platform.id == competitor.platform_id).first()
    if not platform or platform.name.lower() not in ["twitter", "x"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Scraping not supported for platform: {platform.name if platform else 'unknown'}",
                "code": "UNSUPPORTED_PLATFORM"
            }
        )
    
    # Create scraping history entry
    history = ScrapingHistory(
        competitor_id=competitor_id,
        user_id=current_user.id,
        operation_type="sync",
        status="pending"
    )
    db.add(history)
    db.commit()
    
    handle = competitor.username
    profile = None
    posts = []
    retry_count = 0
    
    try:
        # Scrape profile with retry logic
        if scrape_request.sync_profile:
            history.status = "retrying"
            db.commit()
            
            profile = scraper.retry_with_backoff(scraper.get_profile, handle)
            
            # Update competitor profile
            competitor.follower_count = profile.follower_count
            competitor.following_count = profile.following_count
            competitor.post_count = profile.post_count
            competitor.bio = profile.bio
            competitor.display_name = profile.display_name
            competitor.last_scraped_at = datetime.utcnow()
        
        # Scrape posts with retry logic
        history.status = "retrying"
        db.commit()
        
        posts = scraper.retry_with_backoff(scraper.get_posts, handle, max_posts=posts_limit)
        
        # Save posts to database
        for post in posts:
            existing = db.query(Post).filter(
                Post.external_id == post.id,
                Post.platform_id == platform.id
            ).first()
            
            if existing:
                # Update engagement metrics
                existing.like_count = post.like_count
                existing.reply_count = post.reply_count
                existing.repost_count = post.repost_count
                existing.updated_at = datetime.utcnow()
            else:
                # Create new post
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
        
        # Update history as successful
        history.status = "success"
        history.posts_scraped = len(posts)
        history.retry_count = retry_count
        history.completed_at = datetime.utcnow()
        db.commit()
        
        # Convert to response format
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
        
        return ScrapeCompetitorResponse(
            competitor_id=competitor_id,
            username=handle,
            profile_synced=scrape_request.sync_profile,
            posts_scraped=len(posts),
            posts=post_responses,
            scraped_at=datetime.utcnow()
        )
        
    except RateLimitExceeded as e:
        history.status = "failed"
        history.error_message = str(e)
        history.completed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": str(e),
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60
            }
        )
    except ScrapingBlocked as e:
        history.status = "failed"
        history.error_message = str(e)
        history.completed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": str(e),
                "code": "SCRAPING_BLOCKED"
            }
        )
    except Exception as e:
        history.status = "failed"
        history.error_message = str(e)
        history.retry_count = retry_count
        history.completed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": f"Failed to scrape competitor: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )


@scrape_router.post(
    "/hashtags",
    response_model=TrendingHashtagsResponse,
    responses={
        429: {"model": ScrapingErrorResponse, "description": "Rate limit exceeded"},
        403: {"model": ScrapingErrorResponse, "description": "Scraping blocked"},
    }
)
def get_trending_hashtags(
    request: Request,
    location: str = "worldwide",
    current_user: User = Depends(get_current_user),
    scraper: TwitterScraperService = Depends(get_twitter_scraper),
):
    """Get trending hashtags from Twitter.
    
    This endpoint fetches current trending hashtags from Twitter/X.
    Rate limited to prevent account bans.
    
    Args:
        location: Location for trends (default: worldwide)
        
    Returns:
        List of trending hashtags with volume data
        
    Raises:
        429: If rate limit exceeded
        403: If scraping is blocked
    """
    # Check rate limit (stricter for trends endpoint)
    _rate_limiter.check_rate_limit(request, per_minute=3, per_hour=30)
    
    try:
        # Fetch trending hashtags with retry
        hashtags = scraper.retry_with_backoff(scraper.get_trending_hashtags, location)
        
        # Convert to response format
        hashtag_responses = [
            TrendingHashtagResponse(
                rank=tag["rank"],
                hashtag=tag["hashtag"],
                volume=tag.get("volume"),
                scraped_at=datetime.utcnow()
            )
            for tag in hashtags
        ]
        
        return TrendingHashtagsResponse(
            hashtags=hashtag_responses,
            location=location,
            total=len(hashtag_responses),
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
                "error": f"Failed to fetch trending hashtags: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
        )


@scrape_router.get(
    "/history/{competitor_id}",
    response_model=ScrapingHistoryListResponse,
)
def get_scraping_history(
    competitor_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get scraping history for a competitor.
    
    This endpoint returns the history of scraping operations
    performed on a specific competitor.
    
    Args:
        competitor_id: ID of the competitor
        limit: Maximum number of history entries to return
        
    Returns:
        List of scraping history entries
        
    Raises:
        404: If competitor not found
    """
    # Validate limit
    limit = max(1, min(limit, 100))
    
    # Find competitor
    competitor = db.query(CompetitorProfile).filter(
        CompetitorProfile.id == competitor_id,
        CompetitorProfile.user_id == current_user.id
    ).first()
    
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Competitor not found: {competitor_id}",
                "code": "COMPETITOR_NOT_FOUND"
            }
        )
    
    # Get scraping history
    history_entries = db.query(ScrapingHistory).filter(
        ScrapingHistory.competitor_id == competitor_id,
        ScrapingHistory.user_id == current_user.id
    ).order_by(desc(ScrapingHistory.started_at)).limit(limit).all()
    
    # Convert to response format
    history_responses = [
        ScrapingHistoryResponse(
            id=entry.id,
            competitor_id=entry.competitor_id,
            operation_type=entry.operation_type,
            status=entry.status,
            posts_scraped=entry.posts_scraped,
            error_message=entry.error_message,
            retry_count=entry.retry_count,
            started_at=entry.started_at,
            completed_at=entry.completed_at
        )
        for entry in history_entries
    ]
    
    return ScrapingHistoryListResponse(
        history=history_responses,
        total=len(history_responses),
        competitor_id=competitor_id
    )
