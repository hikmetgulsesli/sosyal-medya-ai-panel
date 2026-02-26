"""Tests for Twitter scraping endpoints."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.services.twitter_scraper import (
    TwitterScraperService,
    TwitterProfile,
    TwitterPost,
    RateLimitExceeded,
    ScrapingBlocked,
)
from app.models.models import ScrapingHistory


class TestTwitterScraperService:
    """Tests for TwitterScraperService."""
    
    def test_parse_count_with_k(self):
        """Test parsing counts with K suffix."""
        service = TwitterScraperService()
        assert service._parse_count("1.2K") == 1200
        assert service._parse_count("5K") == 5000
        assert service._parse_count("10k") == 10000
    
    def test_parse_count_with_m(self):
        """Test parsing counts with M suffix."""
        service = TwitterScraperService()
        assert service._parse_count("1.5M") == 1500000
        assert service._parse_count("2M") == 2000000
    
    def test_parse_count_plain_number(self):
        """Test parsing plain numbers."""
        service = TwitterScraperService()
        assert service._parse_count("1,234") == 1234
        assert service._parse_count("5678") == 5678
    
    def test_parse_count_none(self):
        """Test parsing None returns None."""
        service = TwitterScraperService()
        assert service._parse_count(None) is None
        assert service._parse_count("") is None
    
    def test_check_for_blocks_rate_limit(self):
        """Test rate limit detection."""
        service = TwitterScraperService()
        
        with pytest.raises(RateLimitExceeded):
            service._check_for_blocks("Rate limit exceeded. Please try again later.")
        
        with pytest.raises(RateLimitExceeded):
            service._check_for_blocks("429 Too Many Requests")
    
    def test_check_for_blocks_cloudflare(self):
        """Test Cloudflare block detection."""
        service = TwitterScraperService()
        
        with pytest.raises(ScrapingBlocked):
            service._check_for_blocks("cf-browser-verification required")
        
        with pytest.raises(ScrapingBlocked):
            service._check_for_blocks("Access denied by Cloudflare protection")
    
    def test_check_for_blocks_no_blocks(self):
        """Test normal HTML doesn't raise."""
        service = TwitterScraperService()
        # Should not raise
        service._check_for_blocks("<html><body>Normal content</body></html>")
    
    @patch("app.services.twitter_scraper.Fetcher")
    def test_get_profile_success(self, mock_fetcher_class):
        """Test successful profile fetch."""
        # Setup mock
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>window.__INITIAL_STATE__ = {
            "entities": {
                "users": {
                    "123": {
                        "name": "Test User",
                        "screen_name": "testuser",
                        "description": "Test bio",
                        "followers_count": 1000,
                        "friends_count": 500,
                        "statuses_count": 200,
                        "location": "Test City",
                        "verified": true,
                        "created_at": "Mon Nov 15 12:34:56 +0000 2021"
                    }
                }
            }
        };</script>
        </html>
        '''
        mock_fetcher = Mock()
        mock_fetcher.get.return_value = mock_response
        mock_fetcher_class.return_value = mock_fetcher
        
        service = TwitterScraperService()
        service.fetcher = mock_fetcher
        
        profile = service.get_profile("testuser")
        
        assert profile.username == "testuser"
        mock_fetcher.get.assert_called_once()
    
    @patch("app.services.twitter_scraper.Fetcher")
    def test_get_profile_not_found(self, mock_fetcher_class):
        """Test profile not found."""
        mock_response = Mock()
        mock_response.text = "Page not found. This account doesn't exist."
        mock_fetcher = Mock()
        mock_fetcher.get.return_value = mock_response
        mock_fetcher_class.return_value = mock_fetcher
        
        service = TwitterScraperService()
        service.fetcher = mock_fetcher
        
        with pytest.raises(ValueError, match="Profile not found"):
            service.get_profile("nonexistentuser12345")
    
    @patch("app.services.twitter_scraper.Fetcher")
    def test_get_profile_rate_limited(self, mock_fetcher_class):
        """Test rate limit handling."""
        mock_response = Mock()
        mock_response.text = "Rate limit exceeded. Try again later."
        mock_fetcher = Mock()
        mock_fetcher.get.return_value = mock_response
        mock_fetcher_class.return_value = mock_fetcher
        
        service = TwitterScraperService()
        service.fetcher = mock_fetcher
        
        with pytest.raises(RateLimitExceeded):
            service.get_profile("testuser")
    
    @patch("app.services.twitter_scraper.Fetcher")
    def test_get_posts_success(self, mock_fetcher_class):
        """Test successful posts fetch."""
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>{
            "globalObjects": {
                "tweets": {
                    "123456": {
                        "id_str": "123456",
                        "full_text": "Test tweet content",
                        "created_at": "Mon Nov 15 12:34:56 +0000 2021",
                        "favorite_count": 100,
                        "reply_count": 10,
                        "retweet_count": 5,
                        "user": {
                            "screen_name": "testuser",
                            "name": "Test User"
                        }
                    }
                }
            }
        }</script>
        </html>
        '''
        mock_fetcher = Mock()
        mock_fetcher.get.return_value = mock_response
        mock_fetcher_class.return_value = mock_fetcher
        
        service = TwitterScraperService()
        service.fetcher = mock_fetcher
        
        posts = service.get_posts("testuser", max_posts=5)
        
        assert isinstance(posts, list)
        mock_fetcher.get.assert_called_once()


class TestNewScrapeEndpoints:
    """Tests for new /api/scrape/* endpoints."""
    
    @patch("app.routers.scraping.execute_with_retry")
    @patch("app.routers.scraping.check_rate_limit")
    def test_scrape_competitor_rate_limited(self, mock_check_rate, mock_execute_retry, client: TestClient, test_user, test_platform):
        """Test rate limit during competitor scrape."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Create competitor
        comp_response = client.post(
            "/api/competitors/",
            json={
                "platform_id": test_platform.id,
                "username": "testcompetitor",
                "display_name": "Test Competitor",
                "profile_url": "https://twitter.com/testcompetitor"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        competitor_id = comp_response.json()["id"]
        
        # Mock execute_with_retry to raise rate limit
        mock_execute_retry.side_effect = RateLimitExceeded("Rate limit exceeded")
        
        response = client.post(
            f"/api/scrape/competitor/{competitor_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 429
        data = response.json()
        assert data["detail"]["code"] == "RATE_LIMIT_EXCEEDED"
    
    @patch("app.routers.scraping.execute_with_retry")
    @patch("app.routers.scraping.check_rate_limit")
    def test_scrape_competitor_blocked(self, mock_check_rate, mock_execute_retry, client: TestClient, test_user, test_platform):
        """Test scraping blocked during competitor scrape."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Create competitor
        comp_response = client.post(
            "/api/competitors/",
            json={
                "platform_id": test_platform.id,
                "username": "testcompetitor",
                "display_name": "Test Competitor",
                "profile_url": "https://twitter.com/testcompetitor"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        competitor_id = comp_response.json()["id"]
        
        # Mock execute_with_retry to raise scraping blocked
        mock_execute_retry.side_effect = ScrapingBlocked("Cloudflare protection")
        
        response = client.post(
            f"/api/scrape/competitor/{competitor_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "SCRAPING_BLOCKED"
    
    def test_get_trending_hashtags(self, client: TestClient, test_user):
        """Test POST /api/scrape/hashtags."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.post(
            "/api/scrape/hashtags?location=worldwide",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "hashtags" in data
        assert len(data["hashtags"]) == 10
        assert data["location"] == "worldwide"
        assert data["hashtags"][0]["tag"] == "#AI"
        assert data["hashtags"][0]["rank"] == 1
    
    def test_get_scraping_history(self, client: TestClient, test_user, test_platform, db):
        """Test GET /api/scrape/history/{competitor_id}."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Create competitor
        comp_response = client.post(
            "/api/competitors/",
            json={
                "platform_id": test_platform.id,
                "username": "testcompetitor",
                "display_name": "Test Competitor",
                "profile_url": "https://twitter.com/testcompetitor"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        competitor_id = comp_response.json()["id"]
        
        # Create some scraping history entries
        history_entries = [
            ScrapingHistory(
                competitor_id=competitor_id,
                user_id=test_user.id,
                status="success",
                scrape_type="profile",
                posts_scraped=20,
                retry_count=0,
                started_at=datetime.utcnow() - timedelta(hours=2),
                completed_at=datetime.utcnow() - timedelta(hours=2)
            ),
            ScrapingHistory(
                competitor_id=competitor_id,
                user_id=test_user.id,
                status="failed",
                scrape_type="posts",
                error_message="Network timeout",
                retry_count=3,
                started_at=datetime.utcnow() - timedelta(hours=1),
                completed_at=datetime.utcnow() - timedelta(hours=1)
            ),
        ]
        for entry in history_entries:
            db.add(entry)
        db.commit()
        
        response = client.get(
            f"/api/scrape/history/{competitor_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["competitor_id"] == competitor_id
        assert data["total"] == 2
        assert len(data["history"]) == 2
        
        # Check first entry (most recent first due to ordering)
        assert data["history"][0]["status"] in ["success", "failed"]
        assert data["history"][0]["scrape_type"] in ["profile", "posts"]
    
    def test_get_scraping_history_pagination(self, client: TestClient, test_user, test_platform, db):
        """Test GET /api/scrape/history/{competitor_id} with pagination."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        # Create competitor
        comp_response = client.post(
            "/api/competitors/",
            json={
                "platform_id": test_platform.id,
                "username": "testcompetitor",
                "display_name": "Test Competitor",
                "profile_url": "https://twitter.com/testcompetitor"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        competitor_id = comp_response.json()["id"]
        
        # Create multiple history entries
        for i in range(5):
            entry = ScrapingHistory(
                competitor_id=competitor_id,
                user_id=test_user.id,
                status="success",
                scrape_type="sync",
                posts_scraped=20,
                started_at=datetime.utcnow() - timedelta(hours=i),
                completed_at=datetime.utcnow() - timedelta(hours=i)
            )
            db.add(entry)
        db.commit()
        
        # Test with limit
        response = client.get(
            f"/api/scrape/history/{competitor_id}?limit=2",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["history"]) == 2
        
        # Test with offset
        response = client.get(
            f"/api/scrape/history/{competitor_id}?limit=2&offset=2",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 2


class TestRateLimiting:
    """Tests for rate limiting functionality."""
    
    @patch("app.routers.scraping.get_redis_client")
    def test_rate_limit_with_redis(self, mock_get_redis, client: TestClient, test_user):
        """Test rate limiting with Redis backend."""
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=5)  # Below limit
        mock_redis.zadd = Mock()
        mock_redis.expire = Mock()
        mock_get_redis.return_value = mock_redis
        
        from app.routers.scraping import check_rate_limit
        
        # Should not raise
        check_rate_limit("user_123")
        
        # Verify Redis operations
        mock_redis.zremrangebyscore.assert_called()
        mock_redis.zcard.assert_called()
        mock_redis.zadd.assert_called()
    
    @patch("app.routers.scraping.get_redis_client")
    def test_rate_limit_exceeded(self, mock_get_redis, client: TestClient, test_user):
        """Test rate limit exceeded."""
        mock_redis = Mock()
        mock_redis.zremrangebyscore = Mock()
        mock_redis.zcard = Mock(return_value=10)  # At limit
        mock_redis.zrange = Mock(return_value=[("old_request", 1000)])
        mock_get_redis.return_value = mock_redis
        
        from app.routers.scraping import check_rate_limit
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit("user_123")
        
        assert exc_info.value.status_code == 429
        assert exc_info.value.detail["code"] == "RATE_LIMIT_EXCEEDED"


class TestRetryLogic:
    """Tests for retry logic."""
    
    def test_retry_config_values(self):
        """Test retry configuration."""
        from app.routers.scraping import RetryConfig
        
        assert RetryConfig.MAX_RETRIES == 3
        assert len(RetryConfig.RETRY_DELAY_SECONDS) == 3
        assert RetryConfig.RETRY_DELAY_SECONDS[0] == 5
        assert RetryConfig.RETRY_DELAY_SECONDS[1] == 30
        assert RetryConfig.RETRY_DELAY_SECONDS[2] == 120
    
    @patch("app.routers.scraping.time.sleep")
    def test_execute_with_retry_success_first_attempt(self, mock_sleep, db, test_user, test_platform):
        """Test execute_with_retry succeeds on first attempt."""
        from app.routers.scraping import execute_with_retry, create_scraping_history
        
        # Create a competitor
        competitor = test_platform
        competitor_id = "test-comp-id"
        
        # Mock function that succeeds immediately
        mock_func = Mock(return_value="success_result")
        
        result, history = execute_with_retry(
            db, competitor_id, test_user.id, "test_scrape", mock_func, "arg1", kwarg1="value1"
        )
        
        assert result == "success_result"
        assert history.status == "success"
        assert history.retry_count == 0
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
        mock_sleep.assert_not_called()
    
    @patch("app.routers.scraping.time.sleep")
    def test_execute_with_retry_eventual_success(self, mock_sleep, db, test_user):
        """Test execute_with_retry succeeds after retries."""
        from app.routers.scraping import execute_with_retry
        
        competitor_id = "test-comp-id"
        
        # Mock function that fails twice then succeeds
        mock_func = Mock(side_effect=[Exception("Error 1"), Exception("Error 2"), "success_result"])
        
        result, history = execute_with_retry(
            db, competitor_id, test_user.id, "test_scrape", mock_func
        )
        
        assert result == "success_result"
        assert history.status == "success"
        assert history.retry_count == 2
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2
    
    def test_execute_with_retry_rate_limit_no_retry(self, db, test_user):
        """Test execute_with_retry doesn't retry on rate limit."""
        from app.routers.scraping import execute_with_retry
        
        competitor_id = "test-comp-id"
        
        # Mock function that raises RateLimitExceeded
        mock_func = Mock(side_effect=RateLimitExceeded("Rate limit"))
        
        with pytest.raises(RateLimitExceeded):
            execute_with_retry(db, competitor_id, test_user.id, "test_scrape", mock_func)
        
        # Should only be called once (no retries for rate limits)
        mock_func.assert_called_once()
    
    def test_execute_with_retry_scraping_blocked_no_retry(self, db, test_user):
        """Test execute_with_retry doesn't retry on scraping blocked."""
        from app.routers.scraping import execute_with_retry
        
        competitor_id = "test-comp-id"
        
        # Mock function that raises ScrapingBlocked
        mock_func = Mock(side_effect=ScrapingBlocked("Cloudflare"))
        
        with pytest.raises(ScrapingBlocked):
            execute_with_retry(db, competitor_id, test_user.id, "test_scrape", mock_func)
        
        # Should only be called once (no retries for blocks)
        mock_func.assert_called_once()


class TestScrapingHistoryModel:
    """Tests for ScrapingHistory model operations."""
    
    def test_create_scraping_history(self, db, test_user, test_platform):
        """Test creating scraping history entry."""
        from app.routers.scraping import create_scraping_history
        
        competitor_id = "test-comp-id"
        
        history = create_scraping_history(
            db, competitor_id, test_user.id, "profile",
            status="pending", posts_scraped=None, error_message=None, retry_count=0
        )
        
        assert history.competitor_id == competitor_id
        assert history.user_id == test_user.id
        assert history.scrape_type == "profile"
        assert history.status == "pending"
        assert history.retry_count == 0
        assert history.started_at is not None
    
    def test_update_scraping_history(self, db, test_user):
        """Test updating scraping history entry."""
        from app.routers.scraping import create_scraping_history, update_scraping_history
        
        competitor_id = "test-comp-id"
        
        history = create_scraping_history(db, competitor_id, test_user.id, "posts", "retrying")
        
        updated = update_scraping_history(
            db, history, "success", posts_scraped=25, retry_count=1
        )
        
        assert updated.status == "success"
        assert updated.posts_scraped == 25
        assert updated.retry_count == 1
        assert updated.completed_at is not None


class TestLegacyScrapingEndpoints:
    """Tests for legacy /api/scraping/* endpoints (backward compatibility)."""
    
    def test_legacy_endpoints_require_auth(self, client: TestClient):
        """Test legacy endpoints require authentication."""
        response = client.get("/api/scrape/twitter/testuser/profile")
        assert response.status_code == 401
        
        response = client.get("/api/scrape/twitter/testuser/posts")
        assert response.status_code == 401


class TestTwitterProfileModel:
    """Tests for TwitterProfile dataclass."""
    
    def test_profile_creation(self):
        """Test creating a TwitterProfile."""
        profile = TwitterProfile(
            username="testuser",
            display_name="Test User",
            bio="Test bio",
            follower_count=1000
        )
        
        assert profile.username == "testuser"
        assert profile.display_name == "Test User"
        assert profile.follower_count == 1000
    
    def test_profile_defaults(self):
        """Test TwitterProfile defaults."""
        profile = TwitterProfile(username="testuser")
        
        assert profile.verified == False
        assert profile.bio is None
        assert profile.follower_count is None


class TestTwitterPostModel:
    """Tests for TwitterPost dataclass."""
    
    def test_post_creation(self):
        """Test creating a TwitterPost."""
        post = TwitterPost(
            id="123456",
            text="Test tweet",
            author="Test User",
            author_handle="testuser",
            created_at=datetime.utcnow(),
            like_count=100
        )
        
        assert post.id == "123456"
        assert post.text == "Test tweet"
        assert post.like_count == 100
        assert post.media_urls == []
    
    def test_post_with_media(self):
        """Test TwitterPost with media URLs."""
        post = TwitterPost(
            id="123456",
            text="Test with image",
            author="Test User",
            author_handle="testuser",
            created_at=datetime.utcnow(),
            media_urls=["https://example.com/image.jpg"]
        )
        
        assert len(post.media_urls) == 1
        assert post.media_urls[0] == "https://example.com/image.jpg"
