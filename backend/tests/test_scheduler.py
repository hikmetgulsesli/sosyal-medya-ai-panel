"""Tests for scheduler endpoints and service."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.services.scheduler_service import (
    SchedulerService,
    PostStatus,
    Priority,
    PostNotFoundError,
    InvalidScheduleError,
)
from app.models.models import ScheduledPost, Platform


class TestSchedulerService:
    """Tests for SchedulerService."""
    
    def test_schedule_post_success(self, db):
        """Test scheduling a post successfully."""
        # Create a platform first
        platform = Platform(
            name="twitter",
            display_name="Twitter/X"
        )
        db.add(platform)
        db.commit()
        
        service = SchedulerService(db)
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        
        post = service.schedule_post(
            user_id="user-123",
            platform_id=platform.id,
            content="Test post content",
            scheduled_at=scheduled_time,
            priority=Priority.NORMAL
        )
        
        assert post.content == "Test post content"
        assert post.status == PostStatus.PENDING.value
        assert post.priority == Priority.NORMAL.value
        assert post.user_id == "user-123"
    
    def test_schedule_post_past_time(self, db):
        """Test scheduling a post in the past fails."""
        platform = Platform(
            name="twitter",
            display_name="Twitter/X"
        )
        db.add(platform)
        db.commit()
        
        service = SchedulerService(db)
        past_time = datetime.utcnow() - timedelta(hours=1)
        
        with pytest.raises(InvalidScheduleError, match="in the future"):
            service.schedule_post(
                user_id="user-123",
                platform_id=platform.id,
                content="Test post",
                scheduled_at=past_time
            )
    
    def test_schedule_post_invalid_platform(self, db):
        """Test scheduling with invalid platform fails."""
        service = SchedulerService(db)
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        
        with pytest.raises(InvalidScheduleError, match="Platform"):
            service.schedule_post(
                user_id="user-123",
                platform_id="invalid-platform-id",
                content="Test post",
                scheduled_at=scheduled_time
            )
    
    def test_get_queue(self, db):
        """Test getting queue of posts."""
        # Create platform and posts
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        service = SchedulerService(db)
        
        # Create multiple posts
        for i in range(5):
            post = ScheduledPost(
                user_id="user-123",
                platform_id=platform.id,
                content=f"Post {i}",
                scheduled_at=datetime.utcnow() + timedelta(hours=i),
                status=PostStatus.PENDING.value,
                priority=Priority.NORMAL.value
            )
            db.add(post)
        db.commit()
        
        result = service.get_queue(user_id="user-123")
        
        assert result["total"] == 5
        assert len(result["posts"]) == 5
        assert result["limit"] == 50
    
    def test_get_queue_with_status_filter(self, db):
        """Test getting queue with status filter."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        # Create posts with different statuses
        for status in [PostStatus.PENDING.value, PostStatus.PUBLISHED.value]:
            post = ScheduledPost(
                user_id="user-123",
                platform_id=platform.id,
                content=f"Post {status}",
                scheduled_at=datetime.utcnow() + timedelta(hours=1),
                status=status,
                priority=Priority.NORMAL.value
            )
            db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        result = service.get_queue(user_id="user-123", status=PostStatus.PENDING.value)
        
        assert result["total"] == 1
        assert result["posts"][0].status == PostStatus.PENDING.value
    
    def test_get_post_by_id(self, db):
        """Test getting a specific post."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        found_post = service.get_post_by_id(post.id, "user-123")
        
        assert found_post is not None
        assert found_post.id == post.id
        assert found_post.content == "Test post"
    
    def test_get_post_by_id_not_found(self, db):
        """Test getting non-existent post returns None."""
        service = SchedulerService(db)
        found_post = service.get_post_by_id("non-existent-id", "user-123")
        
        assert found_post is None
    
    def test_publish_immediately(self, db):
        """Test publishing a post immediately."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        published = service.publish_immediately(post.id, "user-123")
        
        assert published.status == PostStatus.PUBLISHED.value
        assert published.published_at is not None
        assert published.external_post_id is not None
    
    def test_publish_immediately_not_found(self, db):
        """Test publishing non-existent post fails."""
        service = SchedulerService(db)
        
        with pytest.raises(PostNotFoundError):
            service.publish_immediately("non-existent", "user-123")
    
    def test_publish_immediately_already_published(self, db):
        """Test publishing already published post fails."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PUBLISHED.value,
            priority=Priority.NORMAL.value,
            published_at=datetime.utcnow()
        )
        db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        
        with pytest.raises(InvalidScheduleError, match="Cannot publish"):
            service.publish_immediately(post.id, "user-123")
    
    def test_cancel_post(self, db):
        """Test cancelling a post."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        cancelled = service.cancel_post(post.id, "user-123")
        
        assert cancelled.status == PostStatus.CANCELLED.value
    
    def test_cancel_post_not_found(self, db):
        """Test cancelling non-existent post fails."""
        service = SchedulerService(db)
        
        with pytest.raises(PostNotFoundError):
            service.cancel_post("non-existent", "user-123")
    
    def test_cancel_already_published(self, db):
        """Test cancelling published post fails."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PUBLISHED.value,
            priority=Priority.NORMAL.value,
            published_at=datetime.utcnow()
        )
        db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        
        with pytest.raises(InvalidScheduleError, match="Cannot cancel"):
            service.cancel_post(post.id, "user-123")
    
    def test_update_post(self, db):
        """Test updating a post."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Original content",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        new_time = datetime.utcnow() + timedelta(hours=2)
        
        updated = service.update_post(
            post_id=post.id,
            user_id="user-123",
            content="Updated content",
            scheduled_at=new_time,
            priority=Priority.HIGH
        )
        
        assert updated.content == "Updated content"
        assert updated.priority == Priority.HIGH.value
    
    def test_update_post_not_found(self, db):
        """Test updating non-existent post fails."""
        service = SchedulerService(db)
        
        with pytest.raises(PostNotFoundError):
            service.update_post("non-existent", "user-123", content="New content")
    
    def test_update_post_past_time(self, db):
        """Test updating post to past time fails."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        past_time = datetime.utcnow() - timedelta(hours=1)
        
        with pytest.raises(InvalidScheduleError, match="in the future"):
            service.update_post(post.id, "user-123", scheduled_at=past_time)
    
    def test_get_due_posts(self, db):
        """Test getting posts due for publishing."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        # Create a post that's due
        due_post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Due post",
            scheduled_at=datetime.utcnow() - timedelta(minutes=5),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(due_post)
        
        # Create a post that's not due yet
        future_post = ScheduledPost(
            user_id="user-123",
            platform_id=platform.id,
            content="Future post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(future_post)
        db.commit()
        
        service = SchedulerService(db)
        due_posts = service.get_due_posts()
        
        assert len(due_posts) == 1
        assert due_posts[0].content == "Due post"
    
    def test_get_optimal_posting_times(self, db):
        """Test getting optimal posting times."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        service = SchedulerService(db)
        times = service.get_optimal_posting_times("user-123", platform.id, days=7)
        
        assert len(times) > 0
        assert all("datetime" in t for t in times)
        assert all("score" in t for t in times)
        assert all("period" in t for t in times)
        assert all(t["score"] <= 1.0 for t in times)
    
    def test_get_queue_stats(self, db):
        """Test getting queue statistics."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        # Create posts with different statuses
        statuses = [
            PostStatus.PENDING.value,
            PostStatus.PENDING.value,
            PostStatus.PUBLISHED.value,
            PostStatus.CANCELLED.value,
        ]
        
        for status in statuses:
            post = ScheduledPost(
                user_id="user-123",
                platform_id=platform.id,
                content=f"Post {status}",
                scheduled_at=datetime.utcnow() + timedelta(hours=1),
                status=status,
                priority=Priority.NORMAL.value
            )
            db.add(post)
        db.commit()
        
        service = SchedulerService(db)
        stats = service.get_queue_stats("user-123")
        
        assert stats["total"] == 4
        assert stats["pending"] == 2
        assert stats["published"] == 1
        assert stats["cancelled"] == 1
    
    def test_bulk_schedule(self, db):
        """Test bulk scheduling posts."""
        platform = Platform(name="twitter", display_name="Twitter/X")
        db.add(platform)
        db.commit()
        
        service = SchedulerService(db)
        base_time = datetime.utcnow() + timedelta(hours=1)
        
        posts_data = [
            {
                "platform_id": platform.id,
                "content": f"Bulk post {i}",
                "scheduled_at": base_time + timedelta(hours=i),
                "priority": Priority.NORMAL.value
            }
            for i in range(3)
        ]
        
        created = service.bulk_schedule("user-123", posts_data)
        
        assert len(created) == 3
        assert all(post.status == PostStatus.PENDING.value for post in created)


class TestSchedulerEndpoints:
    """Tests for scheduler API endpoints."""
    
    def test_schedule_post_endpoint(self, client: TestClient, test_user, test_platform):
        """Test scheduling a post via API."""
        # Login
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        scheduled_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        response = client.post(
            "/api/posts/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "platform_id": test_platform.id,
                "content": "Test scheduled post",
                "scheduled_at": scheduled_time,
                "priority": 2
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test scheduled post"
        assert data["status"] == "pending"
        assert data["priority"] == 2
    
    def test_schedule_post_past_time_endpoint(self, client: TestClient, test_user, test_platform):
        """Test scheduling with past time returns error."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        response = client.post(
            "/api/posts/schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "platform_id": test_platform.id,
                "content": "Test post",
                "scheduled_at": past_time
            }
        )
        
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_SCHEDULE"
    
    def test_get_queue_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test getting queue via API."""
        # Create a post first
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Queue test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/posts/queue",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert "posts" in data
    
    def test_get_queue_with_status_filter_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test getting queue with status filter."""
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Pending post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/posts/queue?status=pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(p["status"] == "pending" for p in data["posts"])
    
    def test_get_post_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test getting specific post via API."""
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Specific post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(
            f"/api/posts/{post.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post.id
        assert data["content"] == "Specific post"
    
    def test_get_post_not_found_endpoint(self, client: TestClient, test_user):
        """Test getting non-existent post returns 404."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/posts/non-existent-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    def test_update_post_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test updating a post via API."""
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Original content",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        new_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        
        response = client.put(
            f"/api/posts/{post.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "content": "Updated content",
                "priority": 3
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["priority"] == 3
    
    def test_publish_immediately_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test publishing immediately via API."""
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Publish me now",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.put(
            f"/api/posts/{post.id}/publish",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert data["published_at"] is not None
        assert "message" in data
    
    def test_publish_already_published_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test publishing already published post returns error."""
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Already published",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PUBLISHED.value,
            priority=Priority.NORMAL.value,
            published_at=datetime.utcnow()
        )
        db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.put(
            f"/api/posts/{post.id}/publish",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_PUBLISH"
    
    def test_cancel_post_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test cancelling a post via API."""
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Cancel me",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PENDING.value,
            priority=Priority.NORMAL.value
        )
        db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.delete(
            f"/api/posts/{post.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert "message" in data
    
    def test_cancel_already_published_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test cancelling published post returns error."""
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Already published",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status=PostStatus.PUBLISHED.value,
            priority=Priority.NORMAL.value,
            published_at=datetime.utcnow()
        )
        db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.delete(
            f"/api/posts/{post.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_CANCEL"
    
    def test_get_queue_stats_endpoint(self, client: TestClient, test_user, test_platform, db):
        """Test getting queue stats via API."""
        # Create posts with different statuses
        for status in [PostStatus.PENDING.value, PostStatus.PUBLISHED.value]:
            post = ScheduledPost(
                user_id=test_user.id,
                platform_id=test_platform.id,
                content=f"Post {status}",
                scheduled_at=datetime.utcnow() + timedelta(hours=1),
                status=status,
                priority=Priority.NORMAL.value
            )
            db.add(post)
        db.commit()
        
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(
            "/api/posts/stats/queue",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "published" in data
    
    def test_get_optimal_times_endpoint(self, client: TestClient, test_user, test_platform):
        """Test getting optimal times via API."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        response = client.get(
            f"/api/posts/optimal-times/{test_platform.id}?days=7",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "datetime" in data[0]
            assert "score" in data[0]
            assert "period" in data[0]
    
    def test_bulk_schedule_endpoint(self, client: TestClient, test_user, test_platform):
        """Test bulk scheduling via API."""
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]
        
        scheduled_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        response = client.post(
            "/api/posts/bulk-schedule",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "posts": [
                    {
                        "platform_id": test_platform.id,
                        "content": "Bulk post 1",
                        "scheduled_at": scheduled_time,
                        "priority": 2
                    },
                    {
                        "platform_id": test_platform.id,
                        "content": "Bulk post 2",
                        "scheduled_at": scheduled_time,
                        "priority": 3
                    }
                ]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["scheduled_count"] == 2
        assert len(data["posts"]) == 2
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access returns 401."""
        response = client.get("/api/posts/queue")
        assert response.status_code == 401


class TestPriorityEnum:
    """Tests for Priority enum."""
    
    def test_priority_values(self):
        """Test priority enum values."""
        assert Priority.LOW.value == 1
        assert Priority.NORMAL.value == 2
        assert Priority.HIGH.value == 3
        assert Priority.URGENT.value == 4
    
    def test_priority_ordering(self):
        """Test priority ordering."""
        assert Priority.LOW < Priority.NORMAL
        assert Priority.NORMAL < Priority.HIGH
        assert Priority.HIGH < Priority.URGENT


class TestPostStatusEnum:
    """Tests for PostStatus enum."""
    
    def test_status_values(self):
        """Test status enum values."""
        assert PostStatus.PENDING.value == "pending"
        assert PostStatus.QUEUED.value == "queued"
        assert PostStatus.PUBLISHING.value == "publishing"
        assert PostStatus.PUBLISHED.value == "published"
        assert PostStatus.FAILED.value == "failed"
        assert PostStatus.CANCELLED.value == "cancelled"
