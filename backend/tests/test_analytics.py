import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import User, Platform, CompetitorProfile, Post, AnalyticsEvent


@pytest.fixture(scope="function")
def test_competitor(db: Session, test_user: User, test_platform: Platform):
    """Create a test competitor profile."""
    competitor = CompetitorProfile(
        user_id=test_user.id,
        platform_id=test_platform.id,
        username="testcompetitor",
        display_name="Test Competitor",
        follower_count=1000,
        following_count=500,
        post_count=50,
        is_active=True
    )
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@pytest.fixture(scope="function")
def test_post(db: Session, test_competitor: CompetitorProfile, test_platform: Platform):
    """Create a test post."""
    post = Post(
        competitor_id=test_competitor.id,
        platform_id=test_platform.id,
        external_id="123456789",
        content="This is a test post content",
        posted_at=datetime.utcnow() - timedelta(days=1),
        like_count=10,
        reply_count=2,
        repost_count=5,
        view_count=100,
        is_viral=False
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@pytest.fixture(scope="function")
def test_analytics_events(db: Session, test_post: Post):
    """Create test analytics events."""
    events = [
        AnalyticsEvent(
            post_id=test_post.id,
            event_type="engagement",
            metric_name="like",
            metric_value=5,
            recorded_at=datetime.utcnow()
        ),
        AnalyticsEvent(
            post_id=test_post.id,
            event_type="engagement",
            metric_name="reply",
            metric_value=2,
            recorded_at=datetime.utcnow()
        ),
        AnalyticsEvent(
            post_id=test_post.id,
            event_type="engagement",
            metric_name="view",
            metric_value=50,
            recorded_at=datetime.utcnow()
        )
    ]
    for event in events:
        db.add(event)
    db.commit()
    return events


@pytest.fixture(scope="function")
def auth_token(client: TestClient, test_user: User):
    """Get auth token for test user."""
    login_response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"}
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


class TestTrackAnalyticsEvent:
    """Tests for POST /api/analytics/track endpoint."""
    
    def test_track_event_success(self, client: TestClient, test_post: Post, auth_token: str):
        """Test successfully tracking an analytics event."""
        # Track event
        response = client.post(
            "/api/analytics/track",
            json={
                "post_id": test_post.id,
                "event_type": "engagement",
                "metric_name": "like",
                "metric_value": 10
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "event_id" in data
        assert "tracked successfully" in data["message"]
    
    def test_track_event_unauthorized(self, client: TestClient, test_post: Post):
        """Test tracking event without authentication."""
        response = client.post(
            "/api/analytics/track",
            json={
                "post_id": test_post.id,
                "event_type": "engagement",
                "metric_name": "like",
                "metric_value": 10
            }
        )
        
        assert response.status_code == 401
    
    def test_track_event_invalid_post(self, client: TestClient, auth_token: str):
        """Test tracking event for non-existent post."""
        # Track event with invalid post_id
        response = client.post(
            "/api/analytics/track",
            json={
                "post_id": "invalid-post-id",
                "event_type": "engagement",
                "metric_name": "like",
                "metric_value": 10
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should still succeed as we don't validate post existence in track endpoint
        assert response.status_code == 200
    
    def test_track_event_negative_value(self, client: TestClient, test_post: Post, auth_token: str):
        """Test tracking event with negative metric value."""
        # Track event with negative value
        response = client.post(
            "/api/analytics/track",
            json={
                "post_id": test_post.id,
                "event_type": "engagement",
                "metric_name": "like",
                "metric_value": -5
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should fail validation
        assert response.status_code == 422
    
    def test_track_event_various_types(self, client: TestClient, test_post: Post, auth_token: str):
        """Test tracking different event types."""
        event_types = [
            ("engagement", "like", 5),
            ("engagement", "reply", 3),
            ("engagement", "repost", 2),
            ("engagement", "share", 1),
            ("view", "view", 100)
        ]
        
        for event_type, metric_name, value in event_types:
            response = client.post(
                "/api/analytics/track",
                json={
                    "post_id": test_post.id,
                    "event_type": event_type,
                    "metric_name": metric_name,
                    "metric_value": value
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200, f"Failed for {event_type}/{metric_name}"
            assert response.json()["success"] is True


class TestGetPostMetrics:
    """Tests for GET /api/analytics/posts/{post_id} endpoint."""
    
    def test_get_post_metrics_success(
        self, client: TestClient, test_post: Post, test_analytics_events, auth_token: str
    ):
        """Test getting metrics for a post with events."""
        # Get metrics
        response = client.get(
            f"/api/analytics/posts/{test_post.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["post_id"] == test_post.id
        assert data["like_count"] >= 5  # From fixture
        assert data["reply_count"] >= 2  # From fixture
        assert "total_engagement" in data
        assert "engagement_rate" in data
        assert "events" in data
    
    def test_get_post_metrics_not_found(self, client: TestClient, auth_token: str):
        """Test getting metrics for non-existent post."""
        # Get metrics for invalid post
        response = client.get(
            "/api/analytics/posts/non-existent-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        assert "error" in response.json()["detail"]
    
    def test_get_post_metrics_unauthorized(self, client: TestClient, test_post: Post):
        """Test getting metrics without authentication."""
        response = client.get(f"/api/analytics/posts/{test_post.id}")
        
        assert response.status_code == 401
    
    def test_get_post_metrics_calculations(
        self, client: TestClient, test_post: Post, test_analytics_events, auth_token: str
    ):
        """Test that engagement calculations are correct."""
        # Get metrics
        response = client.get(
            f"/api/analytics/posts/{test_post.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify calculations - total_engagement is calculated from events
        # Events in fixture: like=5, reply=2, view=50
        expected_engagement = data["like_count"] + data["reply_count"] + data["repost_count"] + data["share_count"]
        assert data["total_engagement"] == expected_engagement
        
        # Engagement rate should be calculated if views exist
        if data["view_count"] and data["view_count"] > 0:
            expected_rate = round((expected_engagement / data["view_count"]) * 100, 2)
            assert data["engagement_rate"] == expected_rate


class TestGetDashboardOverview:
    """Tests for GET /api/analytics/overview endpoint."""
    
    def test_get_overview_success(
        self, client: TestClient, test_post: Post, test_analytics_events, auth_token: str
    ):
        """Test getting dashboard overview."""
        # Get overview
        response = client.get(
            "/api/analytics/overview",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "total_posts_tracked" in data
        assert "total_competitors" in data
        assert "total_platforms" in data
        assert "total_likes" in data
        assert "total_replies" in data
        assert "total_reposts" in data
        assert "growth_7d" in data
        assert "growth_30d" in data
        assert "growth_90d" in data
        assert "platform_overviews" in data
        assert "recent_events" in data
        assert "top_posts" in data
        assert "generated_at" in data
    
    def test_get_overview_empty_user(self, client: TestClient, auth_token: str):
        """Test getting overview for user with no data."""
        # Get overview
        response = client.get(
            "/api/analytics/overview",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return empty but valid data
        assert data["total_posts_tracked"] == 0
        assert data["total_likes"] == 0
    
    def test_get_overview_unauthorized(self, client: TestClient):
        """Test getting overview without authentication."""
        response = client.get("/api/analytics/overview")
        
        assert response.status_code == 401
    
    def test_get_overview_growth_metrics(
        self, client: TestClient, test_post: Post, test_analytics_events, auth_token: str
    ):
        """Test that growth metrics are properly structured."""
        # Get overview
        response = client.get(
            "/api/analytics/overview",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify growth metrics structure
        for period in ["growth_7d", "growth_30d", "growth_90d"]:
            growth = data[period]
            assert "period" in growth
            assert "follower_delta" in growth
            assert "follower_growth_rate" in growth
            assert "post_count" in growth
            assert "avg_engagement_rate" in growth
            assert "total_likes" in growth
            assert "total_replies" in growth
            assert "total_reposts" in growth


class TestGetPostEvents:
    """Tests for GET /api/analytics/posts/{post_id}/events endpoint."""
    
    def test_get_post_events_success(
        self, client: TestClient, test_post: Post, test_analytics_events, auth_token: str
    ):
        """Test getting events for a post."""
        # Get events
        response = client.get(
            f"/api/analytics/posts/{test_post.id}/events",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # From fixture
        
        # Verify event structure
        for event in data:
            assert "id" in event
            assert "post_id" in event
            assert "event_type" in event
            assert "metric_name" in event
            assert "metric_value" in event
            assert "recorded_at" in event
    
    def test_get_post_events_with_filter(
        self, client: TestClient, test_post: Post, test_analytics_events, auth_token: str
    ):
        """Test getting events with event_type filter."""
        # Get events with filter
        response = client.get(
            f"/api/analytics/posts/{test_post.id}/events",
            params={"event_type": "engagement"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned events should match the filter
        for event in data:
            assert event["event_type"] == "engagement"
    
    def test_get_post_events_with_limit(
        self, client: TestClient, test_post: Post, test_analytics_events, auth_token: str
    ):
        """Test getting events with limit."""
        # Get events with limit
        response = client.get(
            f"/api/analytics/posts/{test_post.id}/events",
            params={"limit": 2},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2
    
    def test_get_post_events_invalid_limit(
        self, client: TestClient, test_post: Post, auth_token: str):
        """Test getting events with invalid limit."""
        # Get events with invalid limit
        response = client.get(
            f"/api/analytics/posts/{test_post.id}/events",
            params={"limit": 200},  # Exceeds max of 100
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422
    
    def test_get_post_events_unauthorized(self, client: TestClient, test_post: Post):
        """Test getting events without authentication."""
        response = client.get(f"/api/analytics/posts/{test_post.id}/events")
        
        assert response.status_code == 401


class TestAnalyticsService:
    """Tests for AnalyticsService class."""
    
    def test_track_event(self, db: Session, test_post: Post):
        """Test AnalyticsService.track_event."""
        from app.services.analytics_service import AnalyticsService
        
        event = AnalyticsService.track_event(
            db=db,
            post_id=test_post.id,
            event_type="test",
            metric_name="test_metric",
            metric_value=42
        )
        
        assert event.id is not None
        assert event.post_id == test_post.id
        assert event.event_type == "test"
        assert event.metric_name == "test_metric"
        assert event.metric_value == 42
        assert event.recorded_at is not None
    
    def test_get_post_metrics(self, db: Session, test_post: Post, test_analytics_events):
        """Test AnalyticsService.get_post_metrics."""
        from app.services.analytics_service import AnalyticsService
        
        metrics = AnalyticsService.get_post_metrics(db, test_post.id)
        
        assert metrics is not None
        assert metrics["post_id"] == test_post.id
        assert metrics["like_count"] >= 5
        assert metrics["reply_count"] >= 2
        assert "total_engagement" in metrics
        assert "engagement_rate" in metrics
    
    def test_get_post_metrics_not_found(self, db: Session):
        """Test AnalyticsService.get_post_metrics for non-existent post."""
        from app.services.analytics_service import AnalyticsService
        
        metrics = AnalyticsService.get_post_metrics(db, "non-existent-id")
        
        assert metrics is None
    
    def test_calculate_growth_metrics(self, db: Session, test_user: User, test_post: Post):
        """Test AnalyticsService.calculate_growth_metrics."""
        from app.services.analytics_service import AnalyticsService
        
        growth = AnalyticsService.calculate_growth_metrics(db, test_user.id, 7)
        
        assert "period" in growth
        assert growth["period"] == "7d"
        assert "follower_delta" in growth
        assert "follower_growth_rate" in growth
        assert "post_count" in growth
        assert "avg_engagement_rate" in growth
    
    def test_get_dashboard_overview(self, db: Session, test_user: User, test_post: Post, test_analytics_events):
        """Test AnalyticsService.get_dashboard_overview."""
        from app.services.analytics_service import AnalyticsService
        
        overview = AnalyticsService.get_dashboard_overview(db, test_user.id)
        
        assert "total_posts_tracked" in overview
        assert overview["total_posts_tracked"] >= 1
        assert "growth_7d" in overview
        assert "growth_30d" in overview
        assert "growth_90d" in overview
        assert "platform_overviews" in overview
        assert "recent_events" in overview
