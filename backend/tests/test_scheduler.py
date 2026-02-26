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
    
    # Schedule a post for tomorrow
    scheduled_time = datetime.utcnow() + timedelta(days=1)
    
    response = client.post(
        "/api/scheduler",
        json={
            "platform_id": test_platform.id,
            "content": "Test scheduled post content",
            "media_urls": "https://example.com/image.jpg",
            "scheduled_at": scheduled_time.isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Test scheduled post content"
    assert data["platform_id"] == test_platform.id
    assert data["platform_name"] == "Twitter/X"
    assert data["status"] == "pending"
    assert data["user_id"] == test_user.id
    assert data["media_urls"] == "https://example.com/image.jpg"
    assert "id" in data


def test_create_scheduled_post_past_time(client, test_user, test_platform):
    """Test creating a scheduled post with past time fails."""
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to schedule for yesterday
    past_time = datetime.utcnow() - timedelta(days=1)
    
    response = client.post(
        "/api/scheduler",
        json={
            "platform_id": test_platform.id,
            "content": "Test content",
            "scheduled_at": past_time.isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "future" in response.json()["detail"].lower()


def test_create_scheduled_post_invalid_platform(client, test_user):
    """Test creating a scheduled post with invalid platform fails."""
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    scheduled_time = datetime.utcnow() + timedelta(days=1)
    
    response = client.post(
        "/api/scheduler",
        json={
            "platform_id": "invalid-platform-id",
            "content": "Test content",
            "scheduled_at": scheduled_time.isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "Platform not found" in response.json()["detail"]


def test_list_scheduled_posts(client, test_user, test_platform, db):
    """Test listing scheduled posts."""
    from app.models.models import ScheduledPost
    
    # Create some scheduled posts
    for i in range(3):
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content=f"Test post {i}",
            scheduled_at=datetime.utcnow() + timedelta(days=i + 1),
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


def test_list_scheduled_posts_with_filters(client, test_user, test_platform, db):
    """Test listing scheduled posts with status filter."""
    from app.models.models import ScheduledPost
    
    # Create posts with different statuses
    for i in range(2):
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content=f"Pending post {i}",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
            status="pending"
        )
        db.add(post)
    
    published_post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Published post",
        scheduled_at=datetime.utcnow() - timedelta(days=1),
        status="published",
        published_at=datetime.utcnow()
    )
    db.add(published_post)
    db.commit()
    
    # Login
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
    assert len(data["data"]) == 2
    assert all(p["status"] == "pending" for p in data["data"])
    
    # Filter by published status
    response = client.get(
        "/api/scheduler?status=published",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["status"] == "published"


def test_list_scheduled_posts_pagination(client, test_user, test_platform, db):
    """Test pagination for scheduled posts."""
    from app.models.models import ScheduledPost
    
    # Create 5 posts
    for i in range(5):
        post = ScheduledPost(
            user_id=test_user.id,
            platform_id=test_platform.id,
            content=f"Post {i}",
            scheduled_at=datetime.utcnow() + timedelta(days=i + 1),
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
    
    # Test limit
    response = client.get(
        "/api/scheduler?limit=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["meta"]["limit"] == 2
    assert data["meta"]["has_more"] is True
    
    # Test offset
    response = client.get(
        "/api/scheduler?limit=2&offset=2",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["meta"]["page"] == 2


def test_get_scheduled_post(client, test_user, test_platform, db):
    """Test getting a single scheduled post."""
    from app.models.models import ScheduledPost
    
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Single post",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Get the post
    response = client.get(
        f"/api/scheduler/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == post.id
    assert data["content"] == "Single post"
    assert data["platform_name"] == "Twitter/X"


def test_get_scheduled_post_not_found(client, test_user):
    """Test getting a non-existent scheduled post."""
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


def test_update_scheduled_post(client, test_user, test_platform, db):
    """Test updating a scheduled post."""
    from app.models.models import ScheduledPost
    
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Original content",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Update the post
    new_time = datetime.utcnow() + timedelta(days=2)
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


def test_update_scheduled_post_published_fails(client, test_user, test_platform, db):
    """Test updating a published post fails."""
    from app.models.models import ScheduledPost
    
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Published content",
        scheduled_at=datetime.utcnow() - timedelta(days=1),
        status="published",
        published_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to update
    response = client.put(
        f"/api/scheduler/{post.id}",
        json={"content": "New content"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "published" in response.json()["detail"].lower()


def test_delete_scheduled_post(client, test_user, test_platform, db):
    """Test deleting a scheduled post."""
    from app.models.models import ScheduledPost
    
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="To be deleted",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Delete the post
    response = client.delete(
        f"/api/scheduler/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify it's deleted
    response = client.get(
        f"/api/scheduler/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_delete_scheduled_post_published_fails(client, test_user, test_platform, db):
    """Test deleting a published post fails."""
    from app.models.models import ScheduledPost
    
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Published",
        scheduled_at=datetime.utcnow() - timedelta(days=1),
        status="published",
        published_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to delete
    response = client.delete(
        f"/api/scheduler/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "published" in response.json()["detail"].lower()


def test_manually_publish_post(client, test_user, test_platform, db):
    """Test manually triggering publish for a scheduled post."""
    from app.models.models import ScheduledPost, ApiKey
    
    # Create API key for the platform
    api_key = ApiKey(
        user_id=test_user.id,
        platform_id=test_platform.id,
        key_name="Test API Key",
        encrypted_key="encrypted_test_key",
        is_active=True
    )
    db.add(api_key)
    db.commit()
    
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Manual publish test",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Publish the post
    response = client.patch(
        f"/api/scheduler/{post.id}/publish",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "published" in data["message"].lower()
    assert "external_post_id" in data


def test_manually_publish_post_no_api_key(client, test_user, test_platform, db):
    """Test publishing fails without API key."""
    from app.models.models import ScheduledPost
    
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="No API key test",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status="pending"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login
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
    
    assert response.status_code == 400
    assert "API key" in response.json()["detail"]


def test_manually_publish_already_published(client, test_user, test_platform, db):
    """Test publishing an already published post fails."""
    from app.models.models import ScheduledPost
    
    post = ScheduledPost(
        user_id=test_user.id,
        platform_id=test_platform.id,
        content="Already published",
        scheduled_at=datetime.utcnow() - timedelta(days=1),
        status="published",
        published_at=datetime.utcnow(),
        external_post_id="test_123"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login
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


def test_get_optimal_times(client, test_user, test_platform):
    """Test getting optimal posting times."""
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/scheduler/optimal-times",
        json={
            "platform_id": test_platform.id,
            "days_ahead": 7
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["platform_id"] == test_platform.id
    assert "optimal_slots" in data
    assert len(data["optimal_slots"]) > 0
    
    # Check slot structure
    slot = data["optimal_slots"][0]
    assert "datetime" in slot
    assert "score" in slot
    assert "reason" in slot
    assert 0 <= slot["score"] <= 1


def test_get_optimal_times_invalid_platform(client, test_user):
    """Test getting optimal times for invalid platform fails."""
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/scheduler/optimal-times",
        json={
            "platform_id": "invalid-platform",
            "days_ahead": 7
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_scheduler_endpoints_require_auth(client, test_platform):
    """Test that all scheduler endpoints require authentication."""
    endpoints = [
        ("post", "/api/scheduler", {"platform_id": test_platform.id, "content": "test", "scheduled_at": (datetime.utcnow() + timedelta(days=1)).isoformat()}),
        ("get", "/api/scheduler", None),
        ("get", "/api/scheduler/test-id", None),
        ("put", "/api/scheduler/test-id", {"content": "updated"}),
        ("delete", "/api/scheduler/test-id", None),
        ("patch", "/api/scheduler/test-id/publish", None),
        ("post", "/api/scheduler/optimal-times", {"platform_id": test_platform.id}),
    ]
    
    for method, endpoint, json_data in endpoints:
        if method == "post":
            response = client.post(endpoint, json=json_data)
        elif method == "get":
            response = client.get(endpoint)
        elif method == "put":
            response = client.put(endpoint, json=json_data)
        elif method == "delete":
            response = client.delete(endpoint)
        elif method == "patch":
            response = client.patch(endpoint)
        
        assert response.status_code == 401, f"{method.upper()} {endpoint} should require auth"


def test_user_can_only_access_own_posts(client, test_user, test_platform, db):
    """Test that users can only access their own scheduled posts."""
    from app.models.models import ScheduledPost, User
    
    # Create another user
    from app.core.security import get_password_hash
    other_user = User(
        email="other@example.com",
        hashed_password=get_password_hash("otherpass123"),
        full_name="Other User",
        is_active=True
    )
    db.add(other_user)
    db.commit()
    db.refresh(other_user)
    
    # Create post for other user
    other_post = ScheduledPost(
        user_id=other_user.id,
        platform_id=test_platform.id,
        content="Other user's post",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status="pending"
    )
    db.add(other_post)
    db.commit()
    db.refresh(other_post)
    
    # Login as first user
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Try to access other user's post
    response = client.get(
        f"/api/scheduler/{other_post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_create_scheduled_post_validation(client, test_user, test_platform):
    """Test validation for scheduled post creation."""
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    scheduled_time = datetime.utcnow() + timedelta(days=1)
    
    # Test empty content
    response = client.post(
        "/api/scheduler",
        json={
            "platform_id": test_platform.id,
            "content": "",
            "scheduled_at": scheduled_time.isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    
    # Test missing content
    response = client.post(
        "/api/scheduler",
        json={
            "platform_id": test_platform.id,
            "scheduled_at": scheduled_time.isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
