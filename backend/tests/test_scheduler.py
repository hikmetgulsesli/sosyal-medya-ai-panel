"""Tests for scheduler endpoints."""
import pytest
from datetime import datetime, timedelta


def test_create_scheduled_post_success(client, test_user, test_platform, db):
    """Test creating a scheduled post."""
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Create scheduled post
    scheduled_time = datetime.utcnow() + timedelta(hours=2)
    response = client.post(
        "/api/scheduler",
        json={
            "content": "Test scheduled post content",
            "media_urls": "https://example.com/image1.jpg,https://example.com/image2.jpg",
            "scheduled_at": scheduled_time.isoformat(),
            "platform_id": test_platform.id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Test scheduled post content"
    assert data["platform_id"] == test_platform.id
    assert data["status"] == "pending"
    assert data["user_id"] == test_user.id
    assert "id" in data


def test_create_scheduled_post_past_time(client, test_user, test_platform, db):
    """Test creating a scheduled post with past time fails."""
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to create scheduled post in the past
    past_time = datetime.utcnow() - timedelta(hours=1)
    response = client.post(
        "/api/scheduler",
        json={
            "content": "Test scheduled post content",
            "scheduled_at": past_time.isoformat(),
            "platform_id": test_platform.id
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "future" in response.json()["detail"].lower()


def test_create_scheduled_post_invalid_platform(client, test_user, db):
    """Test creating a scheduled post with invalid platform fails."""
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    scheduled_time = datetime.utcnow() + timedelta(hours=2)
    response = client.post(
        "/api/scheduler",
        json={
            "content": "Test scheduled post content",
            "scheduled_at": scheduled_time.isoformat(),
            "platform_id": "invalid-platform-id"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "Platform not found" in response.json()["detail"]


def test_create_scheduled_post_unauthorized(client, test_platform):
    """Test creating a scheduled post without authentication fails."""
    scheduled_time = datetime.utcnow() + timedelta(hours=2)
    response = client.post(
        "/api/scheduler",
        json={
            "content": "Test scheduled post content",
            "scheduled_at": scheduled_time.isoformat(),
            "platform_id": test_platform.id
        }
    )
    
    assert response.status_code == 401


def test_list_scheduled_posts(client, test_user, test_platform, db):
    """Test listing scheduled posts."""
    from app.models.models import ScheduledPost
    
    # Create some scheduled posts
    for i in range(3):
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content=f"Test post {i}",
            scheduled_at=datetime.utcnow() + timedelta(hours=i+1),
            status="pending"
        )
        db.add(post)
    db.commit()
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # List posts
    response = client.get(
        "/api/scheduler",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert len(data["data"]) == 3
    assert data["meta"]["total"] == 3


def test_list_scheduled_posts_with_status_filter(client, test_user, test_platform, db):
    """Test listing scheduled posts with status filter."""
    from app.models.models import ScheduledPost
    
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
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Filter by pending status
    response = client.get(
        "/api/scheduler?status=pending",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["status"] == "pending"
    
    # Filter by published status
    response = client.get(
        "/api/scheduler?status=published",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["status"] == "published"


def test_list_scheduled_posts_invalid_status(client, test_user, db):
    """Test listing scheduled posts with invalid status fails."""
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/scheduler?status=invalid",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "Invalid status" in response.json()["detail"]


def test_list_scheduled_posts_pagination(client, test_user, test_platform, db):
    """Test pagination for listing scheduled posts."""
    from app.models.models import ScheduledPost
    
    # Create 5 posts
    for i in range(5):
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content=f"Test post {i}",
            scheduled_at=datetime.utcnow() + timedelta(hours=i+1),
            status="pending"
        )
        db.add(post)
    db.commit()
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Get first page (limit 2)
    response = client.get(
        "/api/scheduler?page=1&limit=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["meta"]["page"] == 1
    assert data["meta"]["limit"] == 2
    assert data["meta"]["total"] == 5
    assert data["meta"]["total_pages"] == 3


def test_get_scheduled_post_detail(client, test_user, test_platform, db):
    """Test getting a single scheduled post."""
    from app.models.models import ScheduledPost
    
    # Create a scheduled post
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Test post detail",
        scheduled_at=datetime.utcnow() + timedelta(hours=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Get post detail
    response = client.get(
        f"/api/scheduler/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post.id
    assert data["content"] == "Test post detail"
    assert data["platform_name"] == "Twitter/X"  # From test_platform fixture
    assert "user_id" in data


def test_get_scheduled_post_not_found(client, test_user, db):
    """Test getting a non-existent scheduled post fails."""
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/scheduler/non-existent-id",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_scheduled_post_other_user(client, test_user, test_platform, db):
    """Test getting another user's scheduled post fails."""
    from app.models.models import ScheduledPost, User
    from app.core.security import get_password_hash
    
    # Create another user
    other_user = User(
        email="other@example.com",
        hashed_password=get_password_hash("otherpass123"),
        full_name="Other User",
        is_active=True
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    
    # Create a post for the other user
    post = ScheduledPost(
        user_id=other_user.id,
        platform_id=test_platform.id,
        content="Other user's post",
        scheduled_at=datetime.utcnow() + timedelta(hours=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login as test_user
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to get other user's post
    response = client.get(
        f"/api/scheduler/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_update_scheduled_post(client, test_user, test_platform, db):
    """Test updating a scheduled post."""
    from app.models.models import ScheduledPost
    
    # Create a scheduled post
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Original content",
        scheduled_at=datetime.utcnow() + timedelta(hours=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Update post
    new_time = datetime.utcnow() + timedelta(hours=3)
    response = client.put(
        f"/api/scheduler/{post.id}",
        json={
            "content": "Updated content",
            "scheduled_at": new_time.isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content"


def test_update_scheduled_post_published(client, test_user, test_platform, db):
    """Test updating an already published post fails."""
    from app.models.models import ScheduledPost
    
    # Create a published post
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Published content",
        scheduled_at=datetime.utcnow() - timedelta(hours=1),
        status="published",
        published_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to update published post
    response = client.put(
        f"/api/scheduler/{post.id}",
        json={
            "content": "Updated content"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "published" in response.json()["detail"].lower()


def test_delete_scheduled_post(client, test_user, test_platform, db):
    """Test deleting a scheduled post."""
    from app.models.models import ScheduledPost
    
    # Create a scheduled post
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Post to delete",
        scheduled_at=datetime.utcnow() + timedelta(hours=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    post_id = post.id
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Delete post
    response = client.delete(
        f"/api/scheduler/{post_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify post is deleted
    deleted_post = db.query(ScheduledPost).filter(ScheduledPost.id == post_id).first()
    assert deleted_post is None


def test_delete_scheduled_post_published(client, test_user, test_platform, db):
    """Test deleting an already published post fails."""
    from app.models.models import ScheduledPost
    
    # Create a published post
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Published content",
        scheduled_at=datetime.utcnow() - timedelta(hours=1),
        status="published",
        published_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to delete published post
    response = client.delete(
        f"/api/scheduler/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "published" in response.json()["detail"].lower()


def test_manually_publish_post(client, test_user, test_platform, db):
    """Test manually publishing a scheduled post."""
    from app.models.models import ScheduledPost, ApiKey
    from app.core.security import encrypt_api_key
    
    # Create an API key for the user and platform
    api_key = ApiKey(
        user_id=test_user.id,
        platform_id=test_platform.id,
        key_name="Test Key",
        encrypted_key=encrypt_api_key("test-api-key"),
        is_active=True
    )
    db.add(api_key)
    
    # Create a scheduled post
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Post to publish manually",
        scheduled_at=datetime.utcnow() + timedelta(hours=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Manually publish
    response = client.patch(
        f"/api/scheduler/{post.id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should succeed (mock publishing returns success)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "published successfully" in data["message"]
    assert "external_post_id" in data


def test_manually_publish_post_already_published(client, test_user, test_platform, db):
    """Test manually publishing an already published post fails."""
    from app.models.models import ScheduledPost
    
    # Create an already published post
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Already published",
        scheduled_at=datetime.utcnow() - timedelta(hours=1),
        status="published",
        published_at=datetime.utcnow(),
        external_post_id="twitter_12345"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to publish again
    response = client.patch(
        f"/api/scheduler/{post.id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "already published" in response.json()["detail"].lower()


def test_manually_publish_post_no_api_key(client, test_user, test_platform, db):
    """Test manually publishing without API key fails gracefully."""
    from app.models.models import ScheduledPost
    
    # Create a scheduled post (no API key for this platform)
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Post without API key",
        scheduled_at=datetime.utcnow() + timedelta(hours=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to publish without API key
    response = client.patch(
        f"/api/scheduler/{post.id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should fail with 500 since no API key is configured
    assert response.status_code == 500
    assert "API key" in response.json()["detail"]


# Tests for scheduler service

def test_scheduler_service_get_pending_posts(client, test_user, test_platform, db):
    """Test SchedulerService.get_pending_posts returns only due posts."""
    from app.models.models import ScheduledPost
    from app.services.scheduler import SchedulerService
    
    # Create posts - one due, one not
    due_post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Due post",
        scheduled_at=datetime.utcnow() - timedelta(minutes=5),  # Past
        status="pending"
    )
    future_post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Future post",
        scheduled_at=datetime.utcnow() + timedelta(hours=1),  # Future
        status="pending"
    )
    db.add_all([due_post, future_post])
    db.commit()
    
    service = SchedulerService(db)
    pending = service.get_pending_posts()
    
    # Should only get the due post
    assert len(pending) == 1
    assert pending[0].content == "Due post"


def test_scheduler_service_process_due_posts(client, test_user, test_platform, db):
    """Test SchedulerService.process_due_posts publishes due posts."""
    from app.models.models import ScheduledPost, ApiKey
    from app.services.scheduler import SchedulerService
    from app.core.security import encrypt_api_key
    
    # Create API key
    api_key = ApiKey(
        user_id=test_user.id,
        platform_id=test_platform.id,
        key_name="Test Key",
        encrypted_key=encrypt_api_key("test-api-key"),
        is_active=True
    )
    db.add(api_key)
    
    # Create due posts
    for i in range(2):
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content=f"Due post {i}",
            scheduled_at=datetime.utcnow() - timedelta(minutes=i+1),
            status="pending"
        )
        db.add(post)
    db.commit()
    
    service = SchedulerService(db)
    results = service.process_due_posts()
    
    # Both should be published (mock returns success)
    assert results["total"] == 2
    assert results["published"] == 2
    assert results["failed"] == 0
