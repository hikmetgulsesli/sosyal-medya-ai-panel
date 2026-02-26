"""Scraping router for Twitter/X endpoints."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.database import get_db
from app.models.models import User, CompetitorProfile, Platform, Post
from app.services.twitter_scraper import (
    get_twitter_scraper,
    TwitterScraperService,
    TwitterProfile,
    TwitterPost,
    RateLimitExceeded,
    ScrapingBlocked,
)

router = APIRouter(prefix="/scraping", tags=["scraping"])


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


# Rate limiting storage (in production, use Redis)
_request_timestamps: dict = {}
MAX_REQUESTS_PER_MINUTE = 10


def check_rate_limit(request: Request) -> None:
    """Check if request exceeds rate limit.
    
    Simple in-memory rate limiting. In production, use Redis.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = datetime.utcnow()
    
    # Get timestamps for this IP
    timestamps = _request_timestamps.get(client_ip, [])
    
    # Filter to last minute
    one_minute_ago = now.timestamp() - 60
    recent_requests = [ts for ts in timestamps if ts > one_minute_ago]
    
    if len(recent_requests) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 60 - int(now.timestamp() - recent_requests[0])
            }
        )
    
    # Add current request
    recent_requests.append(now.timestamp())
    _request_timestamps[client_ip] = recent_requests


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
