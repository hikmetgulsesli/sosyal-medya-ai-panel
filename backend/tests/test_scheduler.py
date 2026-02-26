"""Tests for scheduler endpoints."""
import pytest
from datetime import datetime, timedelta


class TestSchedulePost:
    """Tests for scheduling posts."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        # Register user
        user_data = {
            "email": "scheduler_test@example.com",
            "password": "securepassword123",
            "full_name": "Scheduler Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Login
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    def test_schedule_post_success(self, client, auth_headers):
        """Test successful post scheduling."""
        post_data = {
            "platform": "twitter",
            "content": "Test scheduled post content",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["content"] == post_data["content"]
        assert data["platform"] == "twitter"
        assert data["status"] == "pending"
        assert "id" in data
    
    def test_schedule_post_with_media(self, client, auth_headers):
        """Test scheduling post with media URLs."""
        post_data = {
            "platform": "twitter",
            "content": "Test post with media",
            "media_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["media_urls"] == post_data["media_urls"]
    
    def test_schedule_post_past_time_fails(self, client, auth_headers):
        """Test that scheduling in the past fails."""
        post_data = {
            "platform": "twitter",
            "content": "Test post",
            "scheduled_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        assert response.status_code == 400
        assert "future" in response.json()["detail"].lower()
    
    def test_schedule_post_invalid_platform(self, client, auth_headers):
        """Test scheduling with invalid platform fails."""
        post_data = {
            "platform": "invalid_platform",
            "content": "Test post",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_schedule_post_twitter_too_long(self, client, auth_headers):
        """Test that Twitter posts over 280 characters fail."""
        post_data = {
            "platform": "twitter",
            "content": "x" * 281,
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_schedule_post_no_auth(self, client):
        """Test that scheduling without auth fails."""
        post_data = {
            "platform": "twitter",
            "content": "Test post",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data)
        assert response.status_code == 401


class TestGetQueue:
    """Tests for queue endpoints."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        user_data = {
            "email": "queue_test@example.com",
            "password": "securepassword123",
            "full_name": "Queue Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    @pytest.fixture
    def sample_posts(self, client, auth_headers):
        """Create sample posts for testing."""
        posts = []
        for i in range(5):
            post_data = {
                "platform": "twitter",
                "content": f"Test post {i}",
                "scheduled_at": (datetime.utcnow() + timedelta(hours=i+1)).isoformat()
            }
            response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
            posts.append(response.json()["data"])
        return posts
    
    def test_get_queue_success(self, client, auth_headers, sample_posts):
        """Test getting queue with posts."""
        response = client.get("/api/posts/queue", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert "meta" in data
        assert data["meta"]["total"] == 5
    
    def test_get_queue_empty(self, client, auth_headers):
        """Test getting empty queue."""
        response = client.get("/api/posts/queue", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 0
        assert data["meta"]["total"] == 0
    
    def test_get_queue_with_pagination(self, client, auth_headers, sample_posts):
        """Test queue pagination."""
        response = client.get("/api/posts/queue?limit=2&offset=0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["limit"] == 2
        assert data["meta"]["offset"] == 0
        assert data["meta"]["has_more"] is True
    
    def test_get_queue_filter_by_status(self, client, auth_headers, sample_posts):
        """Test filtering queue by status."""
        response = client.get("/api/posts/queue?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(post["status"] == "pending" for post in data["data"])
    
    def test_get_queue_sort_by_scheduled_at(self, client, auth_headers, sample_posts):
        """Test sorting queue by scheduled_at."""
        response = client.get("/api/posts/queue?sort_by=scheduled_at&sort_order=asc", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        scheduled_times = [post["scheduled_at"] for post in data["data"]]
        assert scheduled_times == sorted(scheduled_times)


class TestGetQueueStats:
    """Tests for queue statistics endpoint."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        user_data = {
            "email": "stats_test@example.com",
            "password": "securepassword123",
            "full_name": "Stats Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    def test_get_queue_stats_empty(self, client, auth_headers):
        """Test getting stats with empty queue."""
        response = client.get("/api/posts/queue/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_pending"] == 0
        assert data["total_queued"] == 0
        assert data["total_published"] == 0
        assert data["total_failed"] == 0
        assert "by_platform" in data
        assert "upcoming_posts" in data
    
    def test_get_queue_stats_with_posts(self, client, auth_headers):
        """Test getting stats with posts."""
        # Create some posts
        for i in range(3):
            post_data = {
                "platform": "twitter",
                "content": f"Test post {i}",
                "scheduled_at": (datetime.utcnow() + timedelta(hours=i+1)).isoformat()
            }
            client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        
        response = client.get("/api/posts/queue/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_pending"] == 3
        assert len(data["upcoming_posts"]) <= 5


class TestGetScheduledPost:
    """Tests for getting specific scheduled post."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        user_data = {
            "email": "get_post_test@example.com",
            "password": "securepassword123",
            "full_name": "Get Post Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    @pytest.fixture
    def sample_post(self, client, auth_headers):
        """Create a sample post."""
        post_data = {
            "platform": "twitter",
            "content": "Test post for get",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        return response.json()["data"]
    
    def test_get_scheduled_post_success(self, client, auth_headers, sample_post):
        """Test getting a scheduled post by ID."""
        post_id = sample_post["id"]
        response = client.get(f"/api/posts/{post_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == post_id
        assert data["content"] == sample_post["content"]
    
    def test_get_scheduled_post_not_found(self, client, auth_headers):
        """Test getting non-existent post fails."""
        response = client.get("/api/posts/non-existent-id", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateScheduledPost:
    """Tests for updating scheduled posts."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        user_data = {
            "email": "update_test@example.com",
            "password": "securepassword123",
            "full_name": "Update Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    @pytest.fixture
    def sample_post(self, client, auth_headers):
        """Create a sample post."""
        post_data = {
            "platform": "twitter",
            "content": "Original content",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        return response.json()["data"]
    
    def test_update_post_content(self, client, auth_headers, sample_post):
        """Test updating post content."""
        post_id = sample_post["id"]
        update_data = {"content": "Updated content"}
        response = client.put(f"/api/posts/{post_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["content"] == "Updated content"
    
    def test_update_post_scheduled_time(self, client, auth_headers, sample_post):
        """Test updating post scheduled time."""
        post_id = sample_post["id"]
        new_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        update_data = {"scheduled_at": new_time}
        response = client.put(f"/api/posts/{post_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["scheduled_at"] == new_time
    
    def test_update_published_post_fails(self, client, auth_headers, sample_post):
        """Test that updating published post fails."""
        post_id = sample_post["id"]
        # Publish the post first
        client.put(f"/api/posts/{post_id}/publish", headers=auth_headers)
        
        # Try to update
        update_data = {"content": "Should fail"}
        response = client.put(f"/api/posts/{post_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 400
    
    def test_update_nonexistent_post(self, client, auth_headers):
        """Test updating non-existent post fails."""
        update_data = {"content": "Updated"}
        response = client.put("/api/posts/non-existent", json=update_data, headers=auth_headers)
        assert response.status_code == 404


class TestPublishImmediately:
    """Tests for immediate publishing endpoint."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        user_data = {
            "email": "publish_test@example.com",
            "password": "securepassword123",
            "full_name": "Publish Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    @pytest.fixture
    def sample_post(self, client, auth_headers):
        """Create a sample post."""
        post_data = {
            "platform": "twitter",
            "content": "Test post to publish",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        return response.json()["data"]
    
    def test_publish_immediately_success(self, client, auth_headers, sample_post):
        """Test publishing a scheduled post immediately."""
        post_id = sample_post["id"]
        response = client.put(f"/api/posts/{post_id}/publish", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Post published successfully"
        assert data["data"]["status"] == "published"
        assert data["data"]["published_at"] is not None
        assert data["data"]["external_post_id"] is not None
    
    def test_publish_already_published_fails(self, client, auth_headers, sample_post):
        """Test that publishing already published post fails."""
        post_id = sample_post["id"]
        # Publish once
        client.put(f"/api/posts/{post_id}/publish", headers=auth_headers)
        # Try to publish again
        response = client.put(f"/api/posts/{post_id}/publish", headers=auth_headers)
        assert response.status_code == 400
    
    def test_publish_nonexistent_post(self, client, auth_headers):
        """Test publishing non-existent post fails."""
        response = client.put("/api/posts/non-existent/publish", headers=auth_headers)
        assert response.status_code == 404


class TestCancelScheduledPost:
    """Tests for cancelling scheduled posts."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        user_data = {
            "email": "cancel_test@example.com",
            "password": "securepassword123",
            "full_name": "Cancel Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    @pytest.fixture
    def sample_post(self, client, auth_headers):
        """Create a sample post."""
        post_data = {
            "platform": "twitter",
            "content": "Test post to cancel",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        response = client.post("/api/posts/schedule", json=post_data, headers=auth_headers)
        return response.json()["data"]
    
    def test_cancel_post_success(self, client, auth_headers, sample_post):
        """Test cancelling a scheduled post."""
        post_id = sample_post["id"]
        response = client.delete(f"/api/posts/{post_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify it's cancelled
        get_response = client.get(f"/api/posts/{post_id}", headers=auth_headers)
        assert get_response.json()["data"]["status"] == "cancelled"
    
    def test_cancel_published_post_fails(self, client, auth_headers, sample_post):
        """Test that cancelling published post fails."""
        post_id = sample_post["id"]
        # Publish the post first
        client.put(f"/api/posts/{post_id}/publish", headers=auth_headers)
        
        # Try to cancel
        response = client.delete(f"/api/posts/{post_id}", headers=auth_headers)
        assert response.status_code == 400
    
    def test_cancel_nonexistent_post(self, client, auth_headers):
        """Test cancelling non-existent post fails."""
        response = client.delete("/api/posts/non-existent", headers=auth_headers)
        assert response.status_code == 404


class TestOptimalTimes:
    """Tests for optimal posting time suggestions."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        user_data = {
            "email": "optimal_test@example.com",
            "password": "securepassword123",
            "full_name": "Optimal Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    def test_get_optimal_times_success(self, client, auth_headers):
        """Test getting optimal posting times."""
        request_data = {
            "platform": "twitter",
            "content_type": "text"
        }
        response = client.post("/api/posts/optimal-times", json=request_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        assert data["platform"] == "twitter"
        assert "timezone" in data
        
        # Check structure of suggestions
        suggestion = data["data"][0]
        assert "suggested_time" in suggestion
        assert "expected_engagement_score" in suggestion
        assert "reason" in suggestion
    
    def test_get_optimal_times_invalid_platform(self, client, auth_headers):
        """Test optimal times with invalid platform fails."""
        request_data = {
            "platform": "invalid_platform"
        }
        response = client.post("/api/posts/optimal-times", json=request_data, headers=auth_headers)
        assert response.status_code == 422


class TestPublishNow:
    """Tests for immediate publish without scheduling."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for tests."""
        user_data = {
            "email": "publish_now_test@example.com",
            "password": "securepassword123",
            "full_name": "Publish Now Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        login_response = client.post("/api/auth/login", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    def test_publish_now_success(self, client, auth_headers):
        """Test publishing a post immediately."""
        request_data = {
            "platform": "twitter",
            "content": "Immediate post content",
            "media_urls": ["https://example.com/image.jpg"]
        }
        response = client.post("/api/posts/publish-now", json=request_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Post published immediately"
        assert data["data"]["status"] == "published"
        assert data["data"]["published_at"] is not None
    
    def test_publish_now_no_auth(self, client):
        """Test publishing without auth fails."""
        request_data = {
            "platform": "twitter",
            "content": "Immediate post"
        }
        response = client.post("/api/posts/publish-now", json=request_data)
        assert response.status_code == 401
    
    def test_publish_now_invalid_platform(self, client, auth_headers):
        """Test publishing with invalid platform fails."""
        request_data = {
            "platform": "invalid",
            "content": "Immediate post"
        }
        response = client.post("/api/posts/publish-now", json=request_data, headers=auth_headers)
        assert response.status_code == 400


class TestSchedulerAuthorization:
    """Tests for authorization and security."""
    
    def test_cannot_access_other_users_posts(self, client):
        """Test that users cannot access other users' posts."""
        # Create first user and post
        user1_data = {
            "email": "user1_scheduler@example.com",
            "password": "securepassword123",
            "full_name": "User One"
        }
        client.post("/api/auth/register", json=user1_data)
        login1 = client.post("/api/auth/login", data={
            "username": user1_data["email"],
            "password": user1_data["password"]
        })
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}
        
        post_data = {
            "platform": "twitter",
            "content": "User 1's post",
            "scheduled_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
        post_response = client.post("/api/posts/schedule", json=post_data, headers=headers1)
        post_id = post_response.json()["data"]["id"]
        
        # Create second user
        user2_data = {
            "email": "user2_scheduler@example.com",
            "password": "securepassword123",
            "full_name": "User Two"
        }
        client.post("/api/auth/register", json=user2_data)
        login2 = client.post("/api/auth/login", data={
            "username": user2_data["email"],
            "password": user2_data["password"]
        })
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # User 2 tries to access User 1's post
        response = client.get(f"/api/posts/{post_id}", headers=headers2)
        assert response.status_code == 404
        
        # User 2 tries to update User 1's post
        response = client.put(f"/api/posts/{post_id}", json={"content": "Hacked"}, headers=headers2)
        assert response.status_code == 404
        
        # User 2 tries to delete User 1's post
        response = client.delete(f"/api/posts/{post_id}", headers=headers2)
        assert response.status_code == 404
        
        # User 2 tries to publish User 1's post
        response = client.put(f"/api/posts/{post_id}/publish", headers=headers2)
        assert response.status_code == 404
