import pytest
from datetime import datetime, timedelta


def test_track_event_success(client, test_user, test_platform, db):
    """Test tracking an analytics event for a post."""
    # First create a competitor profile
    from app.models.models import CompetitorProfile, Post
    
    competitor = CompetitorProfile(
        user_id=test_user.id,
        platform_id=test_platform.id,
        username="testcompetitor",
        display_name="Test Competitor",
        is_active=True
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    
    # Create a post
    post = Post(
        competitor_id=competitor.id,
        platform_id=test_platform.id,
        external_id="123456789",
        content="Test post content",
        posted_at=datetime.utcnow(),
        like_count=10,
        reply_count=2,
        repost_count=5
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Login to get token (using Form data)
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Track a like event
    response = client.post(
        "/api/analytics/track",
        json={
            "post_id": post.id,
            "event_type": "like",
            "metric_name": "likes",
            "metric_value": 5
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "event_id" in data
    assert "tracked successfully" in data["message"]
    
    # Verify post metrics were updated
    db.refresh(post)
    assert post.like_count == 15  # Original 10 + 5 from event


def test_track_event_post_not_found(client, test_user):
    """Test tracking an event for a non-existent post."""
    # Login to get token
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/api/analytics/track",
        json={
            "post_id": "non-existent-id",
            "event_type": "like",
            "metric_name": "likes",
            "metric_value": 5
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "Post not found" in response.json()["detail"]


def test_track_event_unauthorized(client):
    """Test tracking an event without authentication."""
    response = client.post(
        "/api/analytics/track",
        json={
            "post_id": "some-id",
            "event_type": "like",
            "metric_name": "likes",
            "metric_value": 5
        }
    )
    
    assert response.status_code == 401


def test_track_multiple_event_types(client, test_user, test_platform, db):
    """Test tracking different types of analytics events."""
    from app.models.models import CompetitorProfile, Post
    
    competitor = CompetitorProfile(
        user_id=test_user.id,
        platform_id=test_platform.id,
        username="testcompetitor",
        display_name="Test Competitor",
        is_active=True
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    
    post = Post(
        competitor_id=competitor.id,
        platform_id=test_platform.id,
        external_id="123456789",
        content="Test post content",
        posted_at=datetime.utcnow(),
        like_count=10,
        reply_count=2,
        repost_count=5,
        view_count=100
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
    
    # Track different event types
    event_types = [
        ("like", "likes", 5),
        ("reply", "replies", 3),
        ("retweet", "retweets", 2),
        ("view", "views", 50),
        ("share", "shares", 1)
    ]
    
    for event_type, metric_name, value in event_types:
        response = client.post(
            "/api/analytics/track",
            json={
                "post_id": post.id,
                "event_type": event_type,
                "metric_name": metric_name,
                "metric_value": value
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201, f"Failed to track {event_type}"
    
    # Verify post metrics
    db.refresh(post)
    assert post.like_count == 15  # 10 + 5
    assert post.reply_count == 5  # 2 + 3
    assert post.repost_count == 7  # 5 + 2
    assert post.view_count == 150  # 100 + 50


def test_get_post_metrics_success(client, test_user, test_platform, db):
    """Test getting metrics for a specific post."""
    from app.models.models import CompetitorProfile, Post, AnalyticsEvent
    
    competitor = CompetitorProfile(
        user_id=test_user.id,
        platform_id=test_platform.id,
        username="testcompetitor",
        display_name="Test Competitor",
        is_active=True
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    
    post = Post(
        competitor_id=competitor.id,
        platform_id=test_platform.id,
        external_id="123456789",
        content="Test post content for metrics",
        posted_at=datetime.utcnow() - timedelta(days=5),
        like_count=50,
        reply_count=10,
        repost_count=20,
        view_count=1000,
        is_viral=True,
        viral_score=85.5
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Add some analytics events
    events = [
        AnalyticsEvent(post_id=post.id, event_type="like", metric_name="likes", metric_value=10, recorded_at=datetime.utcnow() - timedelta(days=2)),
        AnalyticsEvent(post_id=post.id, event_type="view", metric_name="views", metric_value=100, recorded_at=datetime.utcnow() - timedelta(days=1)),
        AnalyticsEvent(post_id=post.id, event_type="reply", metric_name="replies", metric_value=5, recorded_at=datetime.utcnow()),
    ]
    for event in events:
        db.add(event)
    db.commit()
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Get post metrics
    response = client.get(
        f"/api/analytics/posts/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["post_id"] == post.id
    assert data["external_id"] == "123456789"
    assert data["platform_name"] == "Twitter/X"
    assert data["competitor_username"] == "testcompetitor"
    
    # Check aggregated metrics (post values + event values)
    assert data["total_likes"] == 60  # 50 + 10
    assert data["total_replies"] == 15  # 10 + 5
    assert data["total_views"] == 1100  # 1000 + 100
    assert data["is_viral"] is True
    assert data["viral_score"] == 85.5
    
    # Engagement rate = (60+20+15) / 1100 * 100 = 8.64%
    assert "engagement_rate" in data
    assert data["engagement_rate"] > 0
    
    # Check daily metrics
    assert "daily_metrics" in data
    assert isinstance(data["daily_metrics"], list)


def test_get_post_metrics_not_found(client, test_user):
    """Test getting metrics for a non-existent post."""
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/analytics/posts/non-existent-id",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "Post not found" in response.json()["detail"]


def test_get_dashboard_overview(client, test_user, test_platform, db):
    """Test getting dashboard overview."""
    from app.models.models import CompetitorProfile, Post, AnalyticsEvent
    
    # Create competitor and posts
    competitor = CompetitorProfile(
        user_id=test_user.id,
        platform_id=test_platform.id,
        username="testcompetitor",
        display_name="Test Competitor",
        follower_count=1000,
        is_active=True
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    
    # Create multiple posts
    posts = []
    for i in range(3):
        post = Post(
            competitor_id=competitor.id,
            platform_id=test_platform.id,
            external_id=f"post_{i}",
            content=f"Test post content {i}",
            posted_at=datetime.utcnow() - timedelta(days=i),
            like_count=20 * (i + 1),
            reply_count=5 * (i + 1),
            repost_count=10 * (i + 1),
            view_count=100 * (i + 1),
            is_viral=(i == 0),
            viral_score=90.0 if i == 0 else 50.0
        )
        db.add(post)
        posts.append(post)
    db.commit()
    
    # Add analytics events
    for i, post in enumerate(posts):
        event = AnalyticsEvent(
            post_id=post.id,
            event_type="like",
            metric_name="likes",
            metric_value=5 * (i + 1),
            recorded_at=datetime.utcnow() - timedelta(days=i)
        )
        db.add(event)
    db.commit()
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Get dashboard overview
    response = client.get(
        "/api/analytics/overview",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check summary stats
    assert data["total_posts_tracked"] == 3
    assert data["total_competitors"] == 1
    assert data["total_platforms"] >= 1
    
    # Check engagement totals
    assert data["total_likes"] > 0
    assert data["total_retweets"] > 0
    assert data["total_replies"] >= 0
    
    # Check averages
    assert "avg_engagement_rate" in data
    assert "avg_viral_score" in data
    assert data["viral_posts_count"] == 1
    
    # Check platform stats
    assert "platform_stats" in data
    assert isinstance(data["platform_stats"], list)
    
    # Check growth metrics
    assert "growth_metrics" in data
    assert isinstance(data["growth_metrics"], list)
    
    # Check top posts
    assert "top_posts" in data
    assert isinstance(data["top_posts"], list)
    assert len(data["top_posts"]) <= 5
    
    # Check date range
    assert "date_from" in data
    assert "date_to" in data


def test_get_dashboard_overview_with_days_param(client, test_user, test_platform, db):
    """Test dashboard overview with custom days parameter."""
    from app.models.models import CompetitorProfile, Post
    
    competitor = CompetitorProfile(
        user_id=test_user.id,
        platform_id=test_platform.id,
        username="testcompetitor",
        is_active=True
    )
    db.add(competitor)
    db.commit()
    
    post = Post(
        competitor_id=competitor.id,
        platform_id=test_platform.id,
        external_id="test_post",
        content="Test content",
        posted_at=datetime.utcnow(),
        like_count=10,
        reply_count=2,
        repost_count=5
    )
    db.add(post)
    db.commit()
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Test with 7 days
    response = client.get(
        "/api/analytics/overview?days=7",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Test with 90 days
    response = client.get(
        "/api/analytics/overview?days=90",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Test invalid days (too high)
    response = client.get(
        "/api/analytics/overview?days=400",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    
    # Test invalid days (too low)
    response = client.get(
        "/api/analytics/overview?days=0",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


def test_get_post_events(client, test_user, test_platform, db):
    """Test getting analytics events for a post with pagination."""
    from app.models.models import CompetitorProfile, Post, AnalyticsEvent
    
    competitor = CompetitorProfile(
        user_id=test_user.id,
        platform_id=test_platform.id,
        username="testcompetitor",
        is_active=True
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    
    post = Post(
        competitor_id=competitor.id,
        platform_id=test_platform.id,
        external_id="test_post",
        content="Test content",
        posted_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Add multiple events
    for i in range(10):
        event = AnalyticsEvent(
            post_id=post.id,
            event_type="like" if i % 2 == 0 else "view",
            metric_name="likes" if i % 2 == 0 else "views",
            metric_value=i + 1,
            recorded_at=datetime.utcnow() - timedelta(hours=i)
        )
        db.add(event)
    db.commit()
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Get all events
    response = client.get(
        f"/api/analytics/events/{post.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    
    # Test with limit
    response = client.get(
        f"/api/analytics/events/{post.id}?limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Test with offset
    response = client.get(
        f"/api/analytics/events/{post.id}?limit=5&offset=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    
    # Test with event_type filter
    response = client.get(
        f"/api/analytics/events/{post.id}?event_type=like",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(e["event_type"] == "like" for e in data)


def test_get_post_events_not_found(client, test_user):
    """Test getting events for a non-existent post."""
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/analytics/events/non-existent-id",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_analytics_endpoints_require_auth(client):
    """Test that all analytics endpoints require authentication."""
    endpoints = [
        ("post", "/api/analytics/track", {"post_id": "test", "event_type": "like", "metric_name": "likes", "metric_value": 1}),
        ("get", "/api/analytics/posts/test-id", None),
        ("get", "/api/analytics/overview", None),
        ("get", "/api/analytics/events/test-id", None),
    ]
    
    for method, endpoint, json_data in endpoints:
        if method == "post":
            response = client.post(endpoint, json=json_data)
        else:
            response = client.get(endpoint)
        
        assert response.status_code == 401, f"{method.upper()} {endpoint} should require auth"


def test_track_event_invalid_data(client, test_user, test_platform, db):
    """Test tracking an event with invalid data."""
    from app.models.models import CompetitorProfile, Post
    
    competitor = CompetitorProfile(
        user_id=test_user.id,
        platform_id=test_platform.id,
        username="testcompetitor",
        is_active=True
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    
    post = Post(
        competitor_id=competitor.id,
        platform_id=test_platform.id,
        external_id="123456789",
        content="Test post content",
        posted_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    
    # Login
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    # Test with negative metric_value
    response = client.post(
        "/api/analytics/track",
        json={
            "post_id": post.id,
            "event_type": "like",
            "metric_name": "likes",
            "metric_value": -5
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    
    # Test with missing required fields
    response = client.post(
        "/api/analytics/track",
        json={
            "post_id": post.id,
            "event_type": "like"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422


def test_empty_dashboard_overview(client, test_user):
    """Test dashboard overview when user has no data."""
    login_response = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/analytics/overview",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return empty but valid data
    assert data["total_posts_tracked"] == 0
    assert data["total_competitors"] == 0
    assert data["total_likes"] == 0
    assert data["platform_stats"] == []
    assert data["top_posts"] == []
