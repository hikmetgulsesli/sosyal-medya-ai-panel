"""Tests for Twitter scraping endpoints."""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.services.twitter_scraper import (
    TwitterScraperService,
    TwitterProfile,
    TwitterPost,
    RateLimitExceeded,
    ScrapingBlocked,
)


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


class TestScrapingEndpoints:
    """Tests for scraping API endpoints."""
    
    def test_get_twitter_profile_success(self, client: TestClient, test_user, mock_scraper):
        """Test getting Twitter profile via API."""
        # Login
        login_response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "testpassword123"})
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        token = login_response.json()["access_token"]
        
        # Setup mock profile
        mock_profile = TwitterProfile(
            username="testuser",
            display_name="Test User",
            bio="Test bio",
            follower_count=1000,
            following_count=500,
            post_count=200,
            verified=True
        )
        mock_scraper.get_profile.return_value = mock_profile
        
        response = client.get(
            "/api/scraping/twitter/testuser/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["follower_count"] == 1000
        assert data["verified"] == True
    
    def test_get_twitter_profile_rate_limited(self, client: TestClient, test_user, mock_scraper):
        """Test rate limit handling in API."""
        # Login
        login_response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "testpassword123"})
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        token = login_response.json()["access_token"]
        
        mock_scraper.get_profile.side_effect = RateLimitExceeded("Rate limit exceeded")
        
        response = client.get(
            "/api/scraping/twitter/testuser/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 429
        data = response.json()
        assert data["detail"]["code"] == "RATE_LIMIT_EXCEEDED"
    
    def test_get_twitter_profile_blocked(self, client: TestClient, test_user, mock_scraper):
        """Test scraping blocked handling in API."""
        # Login
        login_response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "testpassword123"})
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        token = login_response.json()["access_token"]
        
        mock_scraper.get_profile.side_effect = ScrapingBlocked("Cloudflare blocked")
        
        response = client.get(
            "/api/scraping/twitter/testuser/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["code"] == "SCRAPING_BLOCKED"
    
    def test_get_twitter_profile_not_found(self, client: TestClient, test_user, mock_scraper):
        """Test profile not found handling in API."""
        # Login
        login_response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "testpassword123"})
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        token = login_response.json()["access_token"]
        
        mock_scraper.get_profile.side_effect = ValueError("Profile not found")
        
        response = client.get(
            "/api/scraping/twitter/nonexistent/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "PROFILE_NOT_FOUND"
    
    def test_get_twitter_posts_success(self, client: TestClient, test_user, mock_scraper):
        """Test getting Twitter posts via API."""
        # Login
        login_response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "testpassword123"})
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        token = login_response.json()["access_token"]
        
        mock_posts = [
            TwitterPost(
                id="123456",
                text="Test tweet 1",
                author="Test User",
                author_handle="testuser",
                created_at=datetime.utcnow(),
                like_count=100,
                reply_count=10,
                repost_count=5
            ),
            TwitterPost(
                id="123457",
                text="Test tweet 2",
                author="Test User",
                author_handle="testuser",
                created_at=datetime.utcnow(),
                like_count=50,
                reply_count=5,
                repost_count=2
            )
        ]
        
        mock_scraper.get_posts.return_value = mock_posts
        
        response = client.get(
            "/api/scraping/twitter/testuser/posts?limit=10",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["handle"] == "testuser"
        assert data["total"] == 2
        assert len(data["posts"]) == 2
        assert data["posts"][0]["text"] == "Test tweet 1"
    
    def test_get_twitter_posts_limit_validation(self, client: TestClient, test_user, mock_scraper):
        """Test limit parameter validation."""
        # Login
        login_response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "testpassword123"})
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        token = login_response.json()["access_token"]
        
        mock_scraper.get_posts.return_value = []
        
        # Test limit > 50 gets clamped
        response = client.get(
            "/api/scraping/twitter/testuser/posts?limit=100",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        # Should call with max 50
        mock_scraper.get_posts.assert_called_with("testuser", max_posts=50)
    
    def test_sync_twitter_profile(self, client: TestClient, test_user, mock_scraper):
        """Test sync endpoint."""
        # Login
        login_response = client.post("/api/auth/login", data={"username": "test@example.com", "password": "testpassword123"})
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        token = login_response.json()["access_token"]
        
        mock_profile = TwitterProfile(
            username="testuser",
            follower_count=1000
        )
        mock_posts = [TwitterPost(
            id="123",
            text="Test",
            author="Test",
            author_handle="testuser",
            created_at=datetime.utcnow()
        )]
        
        mock_scraper.get_profile.return_value = mock_profile
        mock_scraper.get_posts.return_value = mock_posts
        
        response = client.post(
            "/api/scraping/twitter/testuser/sync",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["handle"] == "testuser"
        assert data["posts_synced"] == 1
        assert data["follower_count"] == 1000


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
