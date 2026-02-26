"""Twitter scraping service using Scrapling library."""
import sys
import re
import time
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field

# Add scrapling library path
sys.path.insert(0, '/home/setrox/libs/scrapling')

from scrapling import Fetcher
from scrapling.adaptors import TwitterAdaptor


@dataclass
class TwitterProfile:
    """Twitter profile data."""
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
    created_at: Optional[datetime] = None


@dataclass
class TwitterPost:
    """Twitter/X post data."""
    id: str
    text: str
    author: str
    author_handle: str
    created_at: datetime
    like_count: int = 0
    reply_count: int = 0
    repost_count: int = 0
    view_count: Optional[int] = None
    media_urls: List[str] = field(default_factory=list)
    is_reply: bool = False
    is_retweet: bool = False


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class ScrapingBlocked(Exception):
    """Raised when scraping is blocked (Cloudflare, etc.)."""
    pass


class TwitterScraperService:
    """Service for scraping Twitter/X data using Scrapling."""

    def __init__(self, rate_limit_delay: float = 6.0):
        """Initialize the Twitter scraper service.

        Args:
            rate_limit_delay: Delay between requests in seconds (default 6s for ~10 req/min)
        """
        self.adaptor = TwitterAdaptor()
        self.fetcher = Fetcher()
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: Optional[float] = None

    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    def _check_for_blocks(self, html: str) -> None:
        """Check if the response indicates blocking.

        Args:
            html: HTML response content

        Raises:
            ScrapingBlocked: If scraping is blocked
            RateLimitExceeded: If rate limited
        """
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "429",
            "try again later",
        ]

        html_lower = html.lower()
        for indicator in rate_limit_indicators:
            if indicator in html_lower:
                raise RateLimitExceeded(f"Rate limit detected: {indicator}")

        block_indicators = [
            "cf-browser-verification",
            "cloudflare",
            "access denied",
            "blocked",
            "captcha",
            "verify you are human",
        ]

        for indicator in block_indicators:
            if indicator in html_lower:
                raise ScrapingBlocked(f"Scraping blocked: {indicator}")

    def _parse_count(self, count_str: Optional[str]) -> Optional[int]:
        """Parse count string to integer.

        Args:
            count_str: String like "1.2K", "5M", "1,234"

        Returns:
            Integer count or None
        """
        if not count_str:
            return None

        count_str = count_str.strip().replace(",", "").upper()

        try:
            if count_str.endswith("K"):
                return int(float(count_str[:-1]) * 1000)
            elif count_str.endswith("M"):
                return int(float(count_str[:-1]) * 1000000)
            elif count_str.endswith("B"):
                return int(float(count_str[:-1]) * 1000000000)
            else:
                return int(float(count_str))
        except (ValueError, TypeError):
            return None

    def _extract_profile_from_html(self, username: str, html: str) -> TwitterProfile:
        """Extract profile data from HTML.

        Args:
            username: Twitter handle
            html: Profile page HTML

        Returns:
            TwitterProfile object
        """
        profile = TwitterProfile(username=username)

        # Display name extraction
        name_match = re.search(r'"name":"([^"]+)"', html)
        if name_match:
            profile.display_name = name_match.group(1).encode().decode("unicode_escape")

        # Bio extraction
        bio_match = re.search(r'"description":"([^"]*)"', html)
        if bio_match:
            profile.bio = bio_match.group(1).encode().decode("unicode_escape")

        # Follower count
        follower_match = re.search(r'"followers_count":(\d+)', html)
        if follower_match:
            profile.follower_count = int(follower_match.group(1))
        else:
            follower_match = re.search(r'(\d+[\d,.]*[KMB]?)\s*[Ff]ollowers?', html)
            if follower_match:
                profile.follower_count = self._parse_count(follower_match.group(1))

        # Following count
        following_match = re.search(r'"friends_count":(\d+)', html)
        if following_match:
            profile.following_count = int(following_match.group(1))
        else:
            following_match = re.search(r'(\d+[\d,.]*[KMB]?)\s*[Ff]ollowing', html)
            if following_match:
                profile.following_count = self._parse_count(following_match.group(1))

        # Post count
        post_match = re.search(r'"statuses_count":(\d+)', html)
        if post_match:
            profile.post_count = int(post_match.group(1))
        else:
            post_match = re.search(r'(\d+[\d,.]*[KMB]?)\s*[Pp]osts?', html)
            if post_match:
                profile.post_count = self._parse_count(post_match.group(1))

        # Location
        location_match = re.search(r'"location":"([^"]*)"', html)
        if location_match:
            profile.location = location_match.group(1).encode().decode("unicode_escape")

        # Website/URL
        url_match = re.search(r'"url":"([^"]*)"', html)
        if url_match:
            profile.website = url_match.group(1).encode().decode("unicode_escape")

        # Profile image
        image_match = re.search(r'"profile_image_url_https":"([^"]+)"', html)
        if image_match:
            profile.profile_image_url = image_match.group(1).replace("\\", "")

        # Verified status
        verified_match = re.search(r'"verified":(true|false)', html)
        if verified_match:
            profile.verified = verified_match.group(1) == "true"

        # Account creation date
        created_match = re.search(r'"created_at":"([^"]+)"', html)
        if created_match:
            try:
                created_str = created_match.group(1)
                profile.created_at = datetime.strptime(
                    created_str, "%a %b %d %H:%M:%S +0000 %Y"
                )
            except ValueError:
                pass

        return profile

    def _extract_posts_from_html(self, html: str, max_posts: int = 20) -> List[TwitterPost]:
        """Extract posts from HTML.

        Args:
            html: Page HTML containing tweets
            max_posts: Maximum number of posts to extract

        Returns:
            List of TwitterPost objects
        """
        posts = []

        # Look for tweet objects in timeline data
        timeline_pattern = (
            r'"id_str":"(\d+)".*?"full_text":"((?:[^"\\]|\\.)*)".*?'
            r'"user":\{[^}]*"screen_name":"([^"]*)"[^}]*"name":"([^"]*)"'
        )

        matches = list(re.finditer(timeline_pattern, html, re.DOTALL))

        for match in matches[:max_posts]:
            try:
                tweet_id = match.group(1)
                text = match.group(2).encode().decode("unicode_escape")
                author_handle = match.group(3)
                author = match.group(4).encode().decode("unicode_escape")

                # Extract engagement metrics from nearby content
                search_end = match.start() + 5000
                like_match = re.search(
                    r'"favorite_count":(\d+)',
                    html[match.start():search_end]
                )
                reply_match = re.search(
                    r'"reply_count":(\d+)',
                    html[match.start():search_end]
                )
                retweet_match = re.search(
                    r'"retweet_count":(\d+)',
                    html[match.start():search_end]
                )

                post = TwitterPost(
                    id=tweet_id,
                    text=text,
                    author=author,
                    author_handle=author_handle,
                    created_at=datetime.utcnow(),
                    like_count=int(like_match.group(1)) if like_match else 0,
                    reply_count=int(reply_match.group(1)) if reply_match else 0,
                    repost_count=int(retweet_match.group(1)) if retweet_match else 0,
                )

                # Try to extract timestamp
                timestamp_match = re.search(
                    r'"created_at":"([^"]+)"',
                    html[match.start():search_end]
                )
                if timestamp_match:
                    try:
                        created_str = timestamp_match.group(1)
                        post.created_at = datetime.strptime(
                            created_str, "%a %b %d %H:%M:%S +0000 %Y"
                        )
                    except ValueError:
                        pass

                posts.append(post)
            except Exception:
                continue

        return posts

    def get_profile(self, username: str) -> TwitterProfile:
        """Fetch Twitter profile data.

        Args:
            username: Twitter handle (without @)

        Returns:
            TwitterProfile object

        Raises:
            ScrapingBlocked: If scraping is blocked
            RateLimitExceeded: If rate limited
            ValueError: If profile not found
        """
        username = username.strip().lstrip("@")
        self._enforce_rate_limit()
        url = f"https://twitter.com/{username}"

        try:
            response = self.fetcher.get(url, headers=self.adaptor.get_headers())
            html = response.text
            self._check_for_blocks(html)

            if "page not found" in html.lower() or "this account doesn" in html.lower():
                raise ValueError(f"Profile not found: @{username}")

            profile = self._extract_profile_from_html(username, html)
            return profile

        except (ScrapingBlocked, RateLimitExceeded):
            raise
        except Exception as e:
            raise ValueError(f"Failed to fetch profile: {str(e)}")

    def get_posts(self, username: str, max_posts: int = 20) -> List[TwitterPost]:
        """Fetch recent posts from a Twitter profile.

        Args:
            username: Twitter handle (without @)
            max_posts: Maximum number of posts to fetch (default 20)

        Returns:
            List of TwitterPost objects

        Raises:
            ScrapingBlocked: If scraping is blocked
            RateLimitExceeded: If rate limited
            ValueError: If profile not found
        """
        username = username.strip().lstrip("@")
        self._enforce_rate_limit()
        url = f"https://twitter.com/{username}"

        try:
            response = self.fetcher.get(url, headers=self.adaptor.get_headers())
            html = response.text
            self._check_for_blocks(html)

            if "page not found" in html.lower() or "this account doesn" in html.lower():
                raise ValueError(f"Profile not found: @{username}")

            posts = self._extract_posts_from_html(html, max_posts)
            return posts

        except (ScrapingBlocked, RateLimitExceeded):
            raise
        except Exception as e:
            raise ValueError(f"Failed to fetch posts: {str(e)}")

    def get_post_by_id(self, tweet_id: str) -> TwitterPost:
        """Fetch a specific tweet by ID.

        Args:
            tweet_id: Twitter tweet ID

        Returns:
            TwitterPost object

        Raises:
            ScrapingBlocked: If scraping is blocked
            RateLimitExceeded: If rate limited
            ValueError: If tweet not found
        """
        self._enforce_rate_limit()
        url = f"https://twitter.com/i/web/status/{tweet_id}"

        try:
            response = self.fetcher.get(url, headers=self.adaptor.get_headers())
            html = response.text
            self._check_for_blocks(html)

            if "page not found" in html.lower() or "this tweet is unavailable" in html.lower():
                raise ValueError(f"Tweet not found: {tweet_id}")

            tweet = self.adaptor.extract_tweet_details(url, html)

            post = TwitterPost(
                id=tweet_id,
                text=tweet.text or "",
                author=tweet.author or "",
                author_handle=tweet.author_handle or "",
                created_at=datetime.utcnow(),
                like_count=tweet.likes or 0,
                reply_count=tweet.replies or 0,
                repost_count=tweet.retweets or 0,
            )

            return post

        except (ScrapingBlocked, RateLimitExceeded):
            raise
        except Exception as e:
            raise ValueError(f"Failed to fetch tweet: {str(e)}")


# Singleton instance for reuse
_scraper_service: Optional[TwitterScraperService] = None


def get_twitter_scraper() -> TwitterScraperService:
    """Get or create the Twitter scraper service singleton."""
    global _scraper_service
    if _scraper_service is None:
        _scraper_service = TwitterScraperService()
    return _scraper_service
