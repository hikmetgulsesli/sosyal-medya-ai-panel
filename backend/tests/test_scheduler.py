"""Tests for the scheduler service and router."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import ScheduledPost, Platform, User
from app.services.scheduler_service import (
    SchedulerService,
    Priority,
    InvalidScheduleError,
    PostNotFoundError,
    SchedulerError
)


class TestSchedulerService:
    """Test cases for SchedulerService."""

    def test_schedule_post_success(self, db: Session, test_user: User, test_platform: Platform):
        """Test scheduling a post successfully."""
        service = SchedulerService(db)
        scheduled_time = datetime.utcnow() + timedelta(hours=1)

        post = service.schedule_post(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post content",
            scheduled_at=scheduled_time,
            priority=Priority.HIGH
        )

        assert post.id is not None
        assert post.user_id == test_user.id
        assert post.platform_id == test_platform.id
        assert post.content == "Test post content"
        assert post.status == "pending"
        assert post.priority == Priority.HIGH

    def test_schedule_post_with_media(self, db: Session, test_user: User, test_platform: Platform):
        """Test scheduling a post with media URLs."""
        service = SchedulerService(db)
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        media_urls = ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]

        post = service.schedule_post(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post with media",
            scheduled_at=scheduled_time,
            media_urls=media_urls
        )

        assert post.media_urls == ",".join(media_urls)

    def test_schedule_post_past_time_raises_error(self, db: Session, test_user: User, test_platform: Platform):
        """Test that scheduling in the past raises an error."""
        service = SchedulerService(db)
        past_time = datetime.utcnow() - timedelta(hours=1)

        with pytest.raises(InvalidScheduleError, match="Scheduled time must be in the future"):
            service.schedule_post(
                user_id=test_user.id,
                platform_id=test_platform.id,
                content="Test content",
                scheduled_at=past_time
            )

    def test_schedule_post_empty_content_raises_error(self, db: Session, test_user: User, test_platform: Platform):
        """Test that empty content raises an error."""
        service = SchedulerService(db)
        scheduled_time = datetime.utcnow() + timedelta(hours=1)

        with pytest.raises(InvalidScheduleError, match="Content cannot be empty"):
            service.schedule_post(
                user_id=test_user.id,
                platform_id=test_platform.id,
                content="   ",
                scheduled_at=scheduled_time
            )

    def test_schedule_post_invalid_priority_raises_error(self, db: Session, test_user: User, test_platform: Platform):
        """Test that invalid priority raises an error."""
        service = SchedulerService(db)
        scheduled_time = datetime.utcnow() + timedelta(hours=1)

        with pytest.raises(InvalidScheduleError, match="Priority must be"):
            service.schedule_post(
                user_id=test_user.id,
                platform_id=test_platform.id,
                content="Test content",
                scheduled_at=scheduled_time,
                priority=5
            )

    def test_schedule_post_invalid_platform_raises_error(self, db: Session, test_user: User):
        """Test that invalid platform ID raises an error."""
        service = SchedulerService(db)
        scheduled_time = datetime.utcnow() + timedelta(hours=1)

        with pytest.raises(InvalidScheduleError, match="Platform with ID"):
            service.schedule_post(
                user_id=test_user.id,
                platform_id="invalid-platform-id",
                content="Test content",
                scheduled_at=scheduled_time
            )

    def test_get_queue(self, db: Session, test_user: User, test_platform: Platform):
        """Test getting the queue."""
        service = SchedulerService(db)

        # Create multiple posts
        for i in range(3):
            post = ScheduledPost(
                user_id=test_user.id,
                platform_id=test_platform.id,
                content=f"Post {i}",
                scheduled_at=datetime.utcnow() + timedelta(hours=i+1),
                status="pending",
                priority=Priority.NORMAL
            )
            db.add(post)
        db.commit()

        result = service.get_queue(test_user.id)

        assert result["total"] == 3
        assert len(result["posts"]) == 3
        assert result["limit"] == 50
        assert result["offset"] == 0

    def test_get_queue_with_status_filter(self, db: Session, test_user: User, test_platform: Platform):
        """Test getting the queue with status filter."""
        service = SchedulerService(db)

        # Create posts with different statuses
        post1 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Pending post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        post2 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Published post",
            scheduled_at=datetime.utcnow() - timedelta(hours=1),
            status="published",
            published_at=datetime.utcnow()
        )
        db.add_all([post1, post2])
        db.commit()

        result = service.get_queue(test_user.id, status="pending")

        assert result["total"] == 1
        assert result["posts"][0].status == "pending"

    def test_get_queue_ordering(self, db: Session, test_user: User, test_platform: Platform):
        """Test that queue is ordered by priority desc, then scheduled_at asc."""
        service = SchedulerService(db)

        # Create posts with different priorities and times
        post1 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Low priority, later",
            scheduled_at=datetime.utcnow() + timedelta(hours=2),
            status="pending",
            priority=Priority.LOW
        )
        post2 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="High priority, earlier",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending",
            priority=Priority.HIGH
        )
        post3 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Normal priority",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending",
            priority=Priority.NORMAL
        )
        db.add_all([post1, post2, post3])
        db.commit()

        result = service.get_queue(test_user.id)

        # Should be ordered: HIGH (post2), NORMAL (post3), LOW (post1)
        assert result["posts"][0].priority == Priority.HIGH
        assert result["posts"][1].priority == Priority.NORMAL
        assert result["posts"][2].priority == Priority.LOW

    def test_publish_now_success(self, db: Session, test_user: User, test_platform: Platform):
        """Test publishing a post immediately."""
        service = SchedulerService(db)

        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db.add(post)
        db.commit()

        updated_post = service.publish_now(post.id, test_user.id)

        assert updated_post.status == "published"
        assert updated_post.published_at is not None

    def test_publish_now_not_found(self, db: Session, test_user: User):
        """Test publishing a non-existent post."""
        service = SchedulerService(db)

        with pytest.raises(PostNotFoundError):
            service.publish_now("non-existent-id", test_user.id)

    def test_publish_now_already_published(self, db: Session, test_user: User, test_platform: Platform):
        """Test publishing an already published post."""
        service = SchedulerService(db)

        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() - timedelta(hours=1),
            status="published",
            published_at=datetime.utcnow()
        )
        db.add(post)
        db.commit()

        with pytest.raises(SchedulerError, match="already published"):
            service.publish_now(post.id, test_user.id)

    def test_cancel_post_success(self, db: Session, test_user: User, test_platform: Platform):
        """Test cancelling a post."""
        service = SchedulerService(db)

        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db.add(post)
        db.commit()

        updated_post = service.cancel_post(post.id, test_user.id)

        assert updated_post.status == "cancelled"

    def test_cancel_post_not_found(self, db: Session, test_user: User):
        """Test cancelling a non-existent post."""
        service = SchedulerService(db)

        with pytest.raises(PostNotFoundError):
            service.cancel_post("non-existent-id", test_user.id)

    def test_cancel_post_already_published(self, db: Session, test_user: User, test_platform: Platform):
        """Test cancelling an already published post."""
        service = SchedulerService(db)

        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() - timedelta(hours=1),
            status="published",
            published_at=datetime.utcnow()
        )
        db.add(post)
        db.commit()

        with pytest.raises(SchedulerError, match="Cannot cancel"):
            service.cancel_post(post.id, test_user.id)

    def test_update_post_success(self, db: Session, test_user: User, test_platform: Platform):
        """Test updating a post."""
        service = SchedulerService(db)

        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Original content",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending",
            priority=Priority.NORMAL
        )
        db.add(post)
        db.commit()

        new_time = datetime.utcnow() + timedelta(hours=2)
        updated_post = service.update_post(
            post_id=post.id,
            user_id=test_user.id,
            content="Updated content",
            scheduled_at=new_time,
            priority=Priority.HIGH
        )

        assert updated_post.content == "Updated content"
        assert updated_post.scheduled_at == new_time
        assert updated_post.priority == Priority.HIGH

    def test_get_post_success(self, db: Session, test_user: User, test_platform: Platform):
        """Test getting a single post."""
        service = SchedulerService(db)

        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db.add(post)
        db.commit()

        retrieved = service.get_post(post.id, test_user.id)

        assert retrieved.id == post.id
        assert retrieved.content == "Test post"

    def test_get_post_not_found(self, db: Session, test_user: User):
        """Test getting a non-existent post."""
        service = SchedulerService(db)

        with pytest.raises(PostNotFoundError):
            service.get_post("non-existent-id", test_user.id)

    def test_get_pending_posts(self, db: Session, test_user: User, test_platform: Platform):
        """Test getting posts ready for publishing."""
        service = SchedulerService(db)

        # Create a post scheduled in the past (ready to publish)
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Ready to publish",
            scheduled_at=datetime.utcnow() - timedelta(minutes=5),
            status="pending"
        )
        db.add(post)
        db.commit()

        pending = service.get_pending_posts()

        assert len(pending) == 1
        assert pending[0].id == post.id

    def test_mark_as_published(self, db: Session, test_user: User, test_platform: Platform):
        """Test marking a post as published."""
        service = SchedulerService(db)

        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db.add(post)
        db.commit()

        updated = service.mark_as_published(post.id, external_post_id="ext-123")

        assert updated.status == "published"
        assert updated.external_post_id == "ext-123"
        assert updated.published_at is not None

    def test_mark_as_failed(self, db: Session, test_user: User, test_platform: Platform):
        """Test marking a post as failed."""
        service = SchedulerService(db)

        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db.add(post)
        db.commit()

        updated = service.mark_as_failed(post.id, "API error occurred")

        assert updated.status == "failed"
        assert updated.error_message == "API error occurred"

    def test_get_optimal_posting_times(self, db: Session):
        """Test getting optimal posting times."""
        service = SchedulerService(db)

        times = service.get_optimal_posting_times(days_ahead=3, count_per_day=2)

        assert len(times) > 0
        # All times should be in the future
        now = datetime.utcnow()
        for t in times:
            assert t > now

    def test_bulk_schedule(self, db: Session, test_user: User, test_platform: Platform):
        """Test bulk scheduling posts."""
        service = SchedulerService(db)

        posts_data = [
            {
                "platform_id": test_platform.id,
                "content": "Post 1",
                "scheduled_at": datetime.utcnow() + timedelta(hours=1),
                "priority": Priority.HIGH
            },
            {
                "platform_id": test_platform.id,
                "content": "Post 2",
                "scheduled_at": datetime.utcnow() + timedelta(hours=2),
                "priority": Priority.NORMAL
            }
        ]

        created = service.bulk_schedule(test_user.id, posts_data)

        assert len(created) == 2

    def test_get_queue_stats(self, db: Session, test_user: User, test_platform: Platform):
        """Test getting queue statistics."""
        service = SchedulerService(db)

        # Create posts with different statuses
        post1 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Pending",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        post2 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Published",
            scheduled_at=datetime.utcnow() - timedelta(hours=1),
            status="published",
            published_at=datetime.utcnow()
        )
        post3 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Cancelled",
            scheduled_at=datetime.utcnow() + timedelta(hours=2),
            status="cancelled"
        )
        db.add_all([post1, post2, post3])
        db.commit()

        stats = service.get_queue_stats(test_user.id)

        assert stats["total_posts"] == 3
        assert stats["pending"] == 1
        assert stats["published"] == 1
        assert stats["cancelled"] == 1
        assert stats["upcoming_count"] == 1


class TestSchedulerRouter:
    """Test cases for scheduler router endpoints."""

    def test_schedule_post_endpoint(self, client: TestClient, test_user: User, test_platform: Platform):
        """Test POST /api/posts/schedule endpoint."""
        # Login first
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        scheduled_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()

        response = client.post(
            "/api/posts/schedule",
            json={
                "platform_id": test_platform.id,
                "content": "Test post via API",
                "scheduled_at": scheduled_time,
                "priority": 3
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test post via API"
        assert data["status"] == "pending"
        assert data["priority"] == 3

    def test_get_queue_endpoint(self, client: TestClient, test_user: User, test_platform: Platform, db: Session):
        """Test GET /api/posts/queue endpoint."""
        # Create a post
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Queue test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db.add(post)
        db.commit()

        # Login
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
        assert data["total"] == 1
        assert len(data["posts"]) == 1
        assert data["posts"][0]["content"] == "Queue test post"

    def test_publish_now_endpoint(self, client: TestClient, test_user: User, test_platform: Platform, db: Session):
        """Test PUT /api/posts/{id}/publish endpoint."""
        # Create a post
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Publish test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db.add(post)
        db.commit()

        # Login
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

    def test_cancel_post_endpoint(self, client: TestClient, test_user: User, test_platform: Platform, db: Session):
        """Test DELETE /api/posts/{id} endpoint."""
        # Create a post
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Cancel test post",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        db.add(post)
        db.commit()

        # Login
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

    def test_get_queue_stats_endpoint(self, client: TestClient, test_user: User, test_platform: Platform, db: Session):
        """Test GET /api/posts/queue/stats endpoint."""
        # Create posts with different statuses
        post1 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Pending",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="pending"
        )
        post2 = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Published",
            scheduled_at=datetime.utcnow() - timedelta(hours=1),
            status="published",
            published_at=datetime.utcnow()
        )
        db.add_all([post1, post2])
        db.commit()

        # Login
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/posts/queue/stats",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_posts"] == 2
        assert data["pending"] == 1
        assert data["published"] == 1

    def test_get_optimal_times_endpoint(self, client: TestClient, test_user: User):
        """Test GET /api/posts/optimal-times endpoint."""
        # Login
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        response = client.get(
            "/api/posts/optimal-times?days_ahead=3&count_per_day=2",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["times"]) > 0

    def test_bulk_schedule_endpoint(self, client: TestClient, test_user: User, test_platform: Platform):
        """Test POST /api/posts/bulk-schedule endpoint."""
        # Login
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        scheduled_time1 = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        scheduled_time2 = (datetime.utcnow() + timedelta(hours=2)).isoformat()

        response = client.post(
            "/api/posts/bulk-schedule",
            json={
                "posts": [
                    {
                        "platform_id": test_platform.id,
                        "content": "Bulk post 1",
                        "scheduled_at": scheduled_time1,
                        "priority": 3
                    },
                    {
                        "platform_id": test_platform.id,
                        "content": "Bulk post 2",
                        "scheduled_at": scheduled_time2,
                        "priority": 2
                    }
                ]
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scheduled_count"] == 2
        assert len(data["posts"]) == 2

    def test_schedule_post_past_time_returns_400(self, client: TestClient, test_user: User, test_platform: Platform):
        """Test that scheduling in the past returns 400."""
        # Login
        login_response = client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token = login_response.json()["access_token"]

        past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        response = client.post(
            "/api/posts/schedule",
            json={
                "platform_id": test_platform.id,
                "content": "Test post",
                "scheduled_at": past_time
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 400
        assert "future" in response.json()["detail"].lower()

    def test_cancel_published_post_returns_400(self, client: TestClient, test_user: User,
                                               test_platform: Platform, db: Session):
        """Test that cancelling a published post returns 400."""
        # Create a published post
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content="Published post",
            scheduled_at=datetime.utcnow() - timedelta(hours=1),
            status="published",
            published_at=datetime.utcnow()
        )
        db.add(post)
        db.commit()

        # Login
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
        assert "cancel" in response.json()["detail"].lower()

    def test_get_nonexistent_post_returns_404(self, client: TestClient, test_user: User):
        """Test that getting a non-existent post returns 404."""
        # Login
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
