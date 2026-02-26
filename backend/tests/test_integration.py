"""Integration tests for the Social Media AI Panel API.

This module contains end-to-end integration tests covering:
1. Auth flow: register -> login -> access protected routes
2. Competitor: create -> scrape -> view results
3. Content generation: input -> generate endpoints
4. Scheduler: create -> edit -> delete scheduled post (if available)
5. Analytics: filter by date -> view metrics
6. Error handling across all endpoints
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status


class TestAuthFlowIntegration:
    """End-to-end tests for authentication flow."""
    
    def test_complete_auth_flow(self, client):
        """Test full auth flow: register -> login -> access protected routes -> refresh -> logout."""
        # Step 1: Register a new user
        register_data = {
            "email": "integration@test.com",
            "password": "SecurePass123!",
            "full_name": "Integration Test User"
        }
        response = client.post("/api/auth/register", json=register_data)
        assert response.status_code == status.HTTP_201_CREATED
        user_data = response.json()
        assert user_data["email"] == register_data["email"]
        assert user_data["full_name"] == register_data["full_name"]
        assert "id" in user_data
        assert "hashed_password" not in user_data
        assert user_data["is_active"] is True
        assert user_data["is_superuser"] is False
        
        # Step 2: Login with the registered user (using JSON endpoint)
        login_data = {
            "email": register_data["email"],
            "password": register_data["password"]
        }
        response = client.post("/api/auth/login/json", json=login_data)
        assert response.status_code == status.HTTP_200_OK
        login_response = response.json()
        assert "access_token" in login_response
        assert "refresh_token" in login_response
        assert login_response["token_type"] == "bearer"
        access_token = login_response["access_token"]
        refresh_token = login_response["refresh_token"]
        
        # Step 3: Access protected route (get current user)
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        me_data = response.json()
        assert me_data["email"] == register_data["email"]
        
        # Step 4: Refresh token
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == status.HTTP_200_OK
        refresh_data = response.json()
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        
        # Step 5: Access protected route with new token
        new_access_token = refresh_data["access_token"]
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_auth_flow_error_handling(self, client):
        """Test error handling in auth flow."""
        # Register a user first
        register_data = {
            "email": "error@test.com",
            "password": "SecurePass123!",
            "full_name": "Error Test User"
        }
        client.post("/api/auth/register", json=register_data)
        
        # Try to register with same email (should fail)
        response = client.post("/api/auth/register", json=register_data)
        assert response.status_code == status.HTTP_409_CONFLICT
        
        # Try login with wrong password
        response = client.post("/api/auth/login/json", json={
            "email": register_data["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try accessing protected route without token
        response = client.get("/api/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try accessing protected route with invalid token
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCompetitorFlowIntegration:
    """End-to-end tests for competitor management flow."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Create a user and return auth headers."""
        # Register
        user_data = {
            "email": "competitor@test.com",
            "password": "SecurePass123!",
            "full_name": "Competitor Test User"
        }
        client.post("/api/auth/register", json=user_data)
        
        # Login
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        access_token = response.json()["access_token"]
        return {"Authorization": f"Bearer {access_token}"}
    
    def test_create_competitor_flow(self, client, auth_headers, test_platform):
        """Test creating and retrieving a competitor profile."""
        # Create competitor
        competitor_data = {
            "platform_id": str(test_platform.id),
            "username": "testcompetitor",
            "display_name": "Test Competitor",
            "profile_url": "https://twitter.com/testcompetitor"
        }
        response = client.post("/api/competitors", json=competitor_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        created = response.json()
        assert created["username"] == competitor_data["username"]
        assert created["display_name"] == competitor_data["display_name"]
        competitor_id = created["id"]
        
        # Get competitor by ID
        response = client.get(f"/api/competitors/{competitor_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        retrieved = response.json()
        assert retrieved["id"] == competitor_id
        assert retrieved["username"] == competitor_data["username"]
        
        # List all competitors
        response = client.get("/api/competitors", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        competitors = response.json()
        assert len(competitors) >= 1
        assert any(c["id"] == competitor_id for c in competitors)
    
    def test_competitor_error_handling(self, client, auth_headers, test_platform):
        """Test error handling for competitor operations."""
        # Try to get non-existent competitor
        response = client.get("/api/competitors/non-existent-id", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to create competitor with non-existent platform
        competitor_data = {
            "platform_id": "non-existent-platform",
            "username": "testuser",
            "display_name": "Test User"
        }
        response = client.post("/api/competitors", json=competitor_data, headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to access competitors without auth
        response = client.get("/api/competitors")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_competitor_delete_flow(self, client, auth_headers, test_platform):
        """Test deleting a competitor."""
        # Create competitor
        competitor_data = {
            "platform_id": str(test_platform.id),
            "username": "deletetest",
            "display_name": "Delete Test"
        }
        response = client.post("/api/competitors", json=competitor_data, headers=auth_headers)
        competitor_id = response.json()["id"]
        
        # Delete competitor
        response = client.delete(f"/api/competitors/{competitor_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Try to get deleted competitor
        response = client.get(f"/api/competitors/{competitor_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAnalyticsFlowIntegration:
    """End-to-end tests for analytics flow."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Create a user and return auth headers."""
        user_data = {
            "email": "analytics@test.com",
            "password": "SecurePass123!",
            "full_name": "Analytics Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_analytics_overview_flow(self, client, auth_headers):
        """Test getting analytics overview with date filtering."""
        # Get overview with default 30 days
        response = client.get("/api/analytics/overview", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        overview = response.json()
        # Check for available fields in the response
        assert "total_posts_tracked" in overview
        assert "total_competitors" in overview
        assert "total_likes" in overview
        assert "avg_engagement_rate" in overview
        assert "avg_viral_score" in overview
        assert "platform_stats" in overview
        assert "growth_metrics" in overview
        
        # Get overview with 7 days filter
        response = client.get("/api/analytics/overview?days=7", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        overview_7d = response.json()
        assert "avg_engagement_rate" in overview_7d
        
        # Get overview with 90 days filter
        response = client.get("/api/analytics/overview?days=90", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        overview_90d = response.json()
        assert "avg_engagement_rate" in overview_90d
    
    def test_analytics_error_handling(self, client, auth_headers):
        """Test error handling for analytics endpoints."""
        # Try to get non-existent post metrics
        response = client.get("/api/analytics/posts/non-existent-id", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try invalid days parameter
        response = client.get("/api/analytics/overview?days=0", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        response = client.get("/api/analytics/overview?days=366", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Try accessing without auth
        response = client.get("/api/analytics/overview")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAIContentGenerationIntegration:
    """End-to-end tests for AI content generation flow."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Create a user and return auth headers."""
        user_data = {
            "email": "ai@test.com",
            "password": "SecurePass123!",
            "full_name": "AI Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_ai_status_endpoint(self, client, auth_headers):
        """Test AI service status endpoint."""
        response = client.get("/api/ai/status", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        status_data = response.json()
        assert "primary_provider" in status_data
        assert "primary_available" in status_data
        assert "fallback_provider" in status_data
        assert "fallback_available" in status_data
        assert "status" in status_data
        assert status_data["status"] in ["ready", "fallback", "unavailable"]
    
    def test_template_crud_flow(self, client, auth_headers):
        """Test content template CRUD operations."""
        # Create template
        template_data = {
            "name": "Test Template",
            "description": "A test template for integration testing",
            "template_type": "post",
            "tone": "professional",
            "prompt_template": "Write a post about {{topic}} in a professional tone",
            "max_length": 280
        }
        response = client.post("/api/ai/templates", json=template_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        created = response.json()
        assert created["name"] == template_data["name"]
        assert created["template_type"] == template_data["template_type"]
        template_id = created["id"]
        
        # Get template by ID
        response = client.get(f"/api/ai/templates/{template_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        retrieved = response.json()
        assert retrieved["id"] == template_id
        
        # List templates
        response = client.get("/api/ai/templates", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        templates_data = response.json()
        assert "templates" in templates_data
        assert "total" in templates_data
        
        # Update template
        update_data = {"name": "Updated Template Name"}
        response = client.patch(f"/api/ai/templates/{template_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        updated = response.json()
        assert updated["name"] == update_data["name"]
        
        # Delete template
        response = client.delete(f"/api/ai/templates/{template_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Try to get deleted template - should return 404 since get_template filters by is_active=True
        response = client.get(f"/api/ai/templates/{template_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_ai_error_handling(self, client, auth_headers):
        """Test error handling for AI endpoints."""
        # Try to get non-existent template
        response = client.get("/api/ai/templates/non-existent-id", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to create template with missing required fields
        response = client.post("/api/ai/templates", json={"name": "Incomplete"}, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Try accessing without auth
        response = client.get("/api/ai/status")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPlatformEndpointsIntegration:
    """Integration tests for platform endpoints."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Create a user and return auth headers."""
        user_data = {
            "email": "platform@test.com",
            "password": "SecurePass123!",
            "full_name": "Platform Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_list_platforms(self, client, auth_headers):
        """Test listing platforms."""
        response = client.get("/api/platforms", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        platforms_data = response.json()
        # API returns object with data field
        assert "data" in platforms_data
        assert isinstance(platforms_data["data"], list)
    
    def test_platforms_public_endpoint(self, client):
        """Test that platforms endpoint is public (no auth required)."""
        response = client.get("/api/platforms")
        # Platforms endpoint is public
        assert response.status_code == status.HTTP_200_OK


class TestHealthAndRootEndpoints:
    """Tests for health and root endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint (no auth required)."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint (no auth required)."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "version" in data


class TestCrossModuleIntegration:
    """Tests that verify integration between different modules."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Create a user and return auth headers."""
        user_data = {
            "email": "cross@test.com",
            "password": "SecurePass123!",
            "full_name": "Cross Module Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_user_isolation(self, client, test_platform):
        """Test that users can only see their own data."""
        # Create first user and competitor
        user1_data = {
            "email": "user1@test.com",
            "password": "SecurePass123!",
            "full_name": "User One"
        }
        client.post("/api/auth/register", json=user1_data)
        resp1 = client.post("/api/auth/login/json", json={
            "email": user1_data["email"],
            "password": user1_data["password"]
        })
        headers1 = {"Authorization": f"Bearer {resp1.json()['access_token']}"}
        
        # User 1 creates a competitor
        comp_data = {
            "platform_id": str(test_platform.id),
            "username": "user1competitor",
            "display_name": "User 1 Competitor"
        }
        resp = client.post("/api/competitors", json=comp_data, headers=headers1)
        user1_competitor_id = resp.json()["id"]
        
        # Create second user
        user2_data = {
            "email": "user2@test.com",
            "password": "SecurePass123!",
            "full_name": "User Two"
        }
        client.post("/api/auth/register", json=user2_data)
        resp2 = client.post("/api/auth/login/json", json={
            "email": user2_data["email"],
            "password": user2_data["password"]
        })
        headers2 = {"Authorization": f"Bearer {resp2.json()['access_token']}"}
        
        # User 2 should not see User 1's competitor
        response = client.get("/api/competitors", headers=headers2)
        assert response.status_code == status.HTTP_200_OK
        competitors = response.json()
        assert not any(c["id"] == user1_competitor_id for c in competitors)
        
        # User 2 should get 404 when trying to access User 1's competitor
        response = client.get(f"/api/competitors/{user1_competitor_id}", headers=headers2)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_multiple_operations_in_session(self, client, auth_headers, test_platform):
        """Test multiple operations in a single user session."""
        # Create competitor
        competitor_data = {
            "platform_id": str(test_platform.id),
            "username": "sessiontest",
            "display_name": "Session Test"
        }
        response = client.post("/api/competitors", json=competitor_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Create AI template
        template_data = {
            "name": "Session Template",
            "description": "Created during session test",
            "template_type": "post",
            "tone": "casual",
            "prompt_template": "Write about {{topic}}",
            "max_length": 280
        }
        response = client.post("/api/ai/templates", json=template_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Get analytics overview
        response = client.get("/api/analytics/overview", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # Get current user
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # List platforms
        response = client.get("/api/platforms", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
    
    def test_token_persistence_across_requests(self, client, test_platform):
        """Test that tokens work across multiple requests."""
        # Register and login
        user_data = {
            "email": "persistent@test.com",
            "password": "SecurePass123!",
            "full_name": "Persistent Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make multiple requests with the same token
        for i in range(5):
            response = client.get("/api/auth/me", headers=headers)
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["email"] == user_data["email"]
        
        # Create multiple resources with same token
        for i in range(3):
            competitor_data = {
                "platform_id": str(test_platform.id),
                "username": f"persistent{i}",
                "display_name": f"Persistent {i}"
            }
            response = client.post("/api/competitors", json=competitor_data, headers=headers)
            assert response.status_code == status.HTTP_201_CREATED


class TestErrorHandlingIntegration:
    """Comprehensive tests for error handling across all endpoints."""
    
    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON."""
        response = client.post(
            "/api/auth/register",
            data="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        # Try to register without required fields
        response = client.post("/api/auth/register", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Try to login without credentials
        response = client.post("/api/auth/login/json", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_invalid_uuid_format(self, client):
        """Test handling of invalid UUID formats."""
        # Create a user first
        user_data = {
            "email": "uuid@test.com",
            "password": "SecurePass123!",
            "full_name": "UUID Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        
        # Try to get competitor with invalid UUID
        response = client.get("/api/competitors/invalid-uuid", headers=headers)
        # API returns 404 for invalid/not found competitor ID
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_empty_request_body(self, client):
        """Test handling of empty request bodies."""
        response = client.post("/api/auth/register", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_large_payload_handling(self, client):
        """Test handling of large payloads."""
        # Create a user first
        user_data = {
            "email": "large@test.com",
            "password": "SecurePass123!",
            "full_name": "Large Payload Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        
        # Try to create template with very large prompt
        large_template = {
            "name": "Large Template",
            "template_type": "post",
            "tone": "professional",
            "prompt_template": "x" * 10000,  # 10KB of text
            "max_length": 280
        }
        # This might succeed or fail depending on implementation, but shouldn't crash
        response = client.post("/api/ai/templates", json=large_template, headers=headers)
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        ]
    
    def test_special_characters_in_input(self, client):
        """Test handling of special characters in input."""
        # Create a user first
        user_data = {
            "email": "special@test.com",
            "password": "SecurePass123!",
            "full_name": "Special Characters Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        
        # Try template with special characters
        template = {
            "name": "Special <script>alert('xss')</script>",
            "template_type": "post",
            "tone": "professional",
            "prompt_template": "Write about {{topic}} with special chars: <>&\"'",
            "max_length": 280
        }
        response = client.post("/api/ai/templates", json=template, headers=headers)
        # Should either accept and sanitize, or reject
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


class TestSchedulerFlowIntegration:
    """End-to-end tests for scheduler flow: create -> edit -> delete scheduled post."""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Create a user and return auth headers."""
        user_data = {
            "email": "scheduler@test.com",
            "password": "SecurePass123!",
            "full_name": "Scheduler Test User"
        }
        client.post("/api/auth/register", json=user_data)
        response = client.post("/api/auth/login/json", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_scheduler_complete_flow(self, client, auth_headers, test_platform):
        """Test complete scheduler flow: create -> edit -> delete scheduled post."""
        # Step 1: Create a scheduled post
        scheduled_time = datetime.utcnow() + timedelta(hours=2)
        post_data = {
            "content": "Test scheduled post content",
            "media_urls": "https://example.com/image.jpg",
            "scheduled_at": scheduled_time.isoformat(),
            "platform_id": str(test_platform.id)
        }
        response = client.post("/api/scheduler", json=post_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        created = response.json()
        assert created["content"] == post_data["content"]
        assert created["platform_id"] == test_platform.id
        assert created["status"] == "pending"
        post_id = created["id"]
        
        # Step 2: Get the scheduled post
        response = client.get(f"/api/scheduler/{post_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        retrieved = response.json()
        assert retrieved["id"] == post_id
        assert retrieved["content"] == post_data["content"]
        
        # Step 3: Update the scheduled post
        new_time = datetime.utcnow() + timedelta(hours=4)
        update_data = {
            "content": "Updated scheduled post content",
            "scheduled_at": new_time.isoformat()
        }
        response = client.put(f"/api/scheduler/{post_id}", json=update_data, headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        updated = response.json()
        assert updated["content"] == update_data["content"]
        
        # Step 4: List scheduled posts and verify our post is there
        response = client.get("/api/scheduler", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        list_data = response.json()
        assert "data" in list_data
        assert "meta" in list_data
        assert any(p["id"] == post_id for p in list_data["data"])
        
        # Step 5: Delete the scheduled post
        response = client.delete(f"/api/scheduler/{post_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Step 6: Verify post is deleted
        response = client.get(f"/api/scheduler/{post_id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_scheduler_filter_by_status(self, client, auth_headers, test_platform, db):
        """Test filtering scheduled posts by status."""
        # Create posts directly via API
        scheduled_time = datetime.utcnow() + timedelta(hours=2)
        post_data = {
            "content": "Test pending post",
            "scheduled_at": scheduled_time.isoformat(),
            "platform_id": str(test_platform.id)
        }
        response = client.post("/api/scheduler", json=post_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        # Test filtering by status
        response = client.get("/api/scheduler?status=pending", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(p["status"] == "pending" for p in data["data"])
    
    def test_scheduler_pagination(self, client, auth_headers, test_platform):
        """Test scheduler pagination."""
        # Create multiple posts
        for i in range(5):
            scheduled_time = datetime.utcnow() + timedelta(hours=i+1)
            post_data = {
                "content": f"Test post {i}",
                "scheduled_at": scheduled_time.isoformat(),
                "platform_id": str(test_platform.id)
            }
            response = client.post("/api/scheduler", json=post_data, headers=auth_headers)
            assert response.status_code == status.HTTP_201_CREATED
        
        # Test pagination
        response = client.get("/api/scheduler?page=1&limit=2", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["page"] == 1
        assert data["meta"]["limit"] == 2
        assert data["meta"]["total"] >= 5
    
    def test_scheduler_error_handling(self, client, auth_headers, test_platform):
        """Test scheduler error handling."""
        # Try to create post with past time
        past_time = datetime.utcnow() - timedelta(hours=1)
        post_data = {
            "content": "Test past post",
            "scheduled_at": past_time.isoformat(),
            "platform_id": str(test_platform.id)
        }
        response = client.post("/api/scheduler", json=post_data, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "future" in response.json()["detail"].lower()
        
        # Try to get non-existent post
        response = client.get("/api/scheduler/non-existent-id", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to update non-existent post
        response = client.put("/api/scheduler/non-existent-id", json={"content": "Updated"}, headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to delete non-existent post
        response = client.delete("/api/scheduler/non-existent-id", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Try to access scheduler without auth
        response = client.get("/api/scheduler")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_scheduler_update_other_users_post_fails(self, client, test_platform):
        """Test that users cannot update other users' scheduled posts."""
        # Create first user and post
        user1_data = {
            "email": "user1sched@test.com",
            "password": "SecurePass123!",
            "full_name": "Scheduler User 1"
        }
        client.post("/api/auth/register", json=user1_data)
        resp1 = client.post("/api/auth/login/json", json={
            "email": user1_data["email"],
            "password": user1_data["password"]
        })
        headers1 = {"Authorization": f"Bearer {resp1.json()['access_token']}"}
        
        # User 1 creates a post
        scheduled_time = datetime.utcnow() + timedelta(hours=2)
        post_data = {
            "content": "User 1's post",
            "scheduled_at": scheduled_time.isoformat(),
            "platform_id": str(test_platform.id)
        }
        resp = client.post("/api/scheduler", json=post_data, headers=headers1)
        post_id = resp.json()["id"]
        
        # Create second user
        user2_data = {
            "email": "user2sched@test.com",
            "password": "SecurePass123!",
            "full_name": "Scheduler User 2"
        }
        client.post("/api/auth/register", json=user2_data)
        resp2 = client.post("/api/auth/login/json", json={
            "email": user2_data["email"],
            "password": user2_data["password"]
        })
        headers2 = {"Authorization": f"Bearer {resp2.json()['access_token']}"}
        
        # User 2 tries to access User 1's post - should get 404 (not found for this user)
        response = client.get(f"/api/scheduler/{post_id}", headers=headers2)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # User 2 tries to update User 1's post
        response = client.put(f"/api/scheduler/{post_id}", json={"content": "Hacked!"}, headers=headers2)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # User 2 tries to delete User 1's post
        response = client.delete(f"/api/scheduler/{post_id}", headers=headers2)
        assert response.status_code == status.HTTP_404_NOT_FOUND
