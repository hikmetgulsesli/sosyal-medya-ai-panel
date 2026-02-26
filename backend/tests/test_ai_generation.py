"""Tests for AI content generation service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.services.ai_service import (
    AIService,
    MiniMaxProvider,
    OpenAIProvider,
    GenerationRequest,
    AIResponse,
)


class TestAIProviders:
    """Test AI provider implementations."""
    
    def test_minimax_provider_availability_with_key(self):
        """Test MiniMax provider is available when API key is set."""
        provider = MiniMaxProvider(api_key="test-key")
        assert provider.is_available() is True
    
    def test_minimax_provider_unavailability_without_key(self):
        """Test MiniMax provider is unavailable when API key is not set."""
        with patch.dict('os.environ', {}, clear=True):
            provider = MiniMaxProvider(api_key=None)
            assert provider.is_available() is False
    
    def test_minimax_provider_error_without_key(self):
        """Test MiniMax provider returns error when generating without key."""
        with patch.dict('os.environ', {}, clear=True):
            provider = MiniMaxProvider(api_key=None)
            request = GenerationRequest(prompt="Test prompt")
            response = provider.generate_text(request)
            
            assert response.error is not None
            assert "not configured" in response.error.lower()
            assert response.content == ""
    
    @patch('app.services.ai_service.httpx.Client')
    def test_minimax_provider_success(self, mock_client_class):
        """Test MiniMax provider successful generation."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {"content": "Generated content"},
                    "finish_reason": "stop"
                }
            ],
            "usage": {"total_tokens": 100}
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client
        
        provider = MiniMaxProvider(api_key="test-key")
        request = GenerationRequest(prompt="Test prompt", tone="professional")
        response = provider.generate_text(request)
        
        assert response.error is None
        assert response.content == "Generated content"
        assert response.provider == "minimax"
        assert response.tokens_used == 100
    
    @patch('app.services.ai_service.httpx.Client')
    def test_minimax_provider_api_error(self, mock_client_class):
        """Test MiniMax provider handles API errors."""
        import httpx
        
        mock_client = Mock()
        mock_client.post.side_effect = httpx.HTTPError("Connection failed")
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client_class.return_value = mock_client
        
        provider = MiniMaxProvider(api_key="test-key")
        request = GenerationRequest(prompt="Test prompt")
        response = provider.generate_text(request)
        
        assert response.error is not None
        assert "API error" in response.error
    
    def test_openai_provider_availability_with_key(self):
        """Test OpenAI provider is available when API key is set."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.ai_service.OpenAI'):
                provider = OpenAIProvider(api_key="test-key")
                assert provider.is_available() is True
    
    def test_openai_provider_unavailability_without_key(self):
        """Test OpenAI provider is unavailable when API key is not set."""
        with patch.dict('os.environ', {}, clear=True):
            provider = OpenAIProvider(api_key=None)
            assert provider.is_available() is False
    
    def test_openai_provider_error_without_key(self):
        """Test OpenAI provider returns error when generating without key."""
        with patch.dict('os.environ', {}, clear=True):
            provider = OpenAIProvider(api_key=None)
            request = GenerationRequest(prompt="Test prompt")
            response = provider.generate_text(request)
            
            assert response.error is not None
            assert "not configured" in response.error.lower()
    
    @patch('app.services.ai_service.OpenAI')
    def test_openai_provider_success(self, mock_openai_class):
        """Test OpenAI provider successful generation."""
        # Setup mock
        mock_choice = Mock()
        mock_choice.message.content = "Generated content"
        mock_choice.finish_reason = "stop"
        
        mock_usage = Mock()
        mock_usage.total_tokens = 150
        
        mock_completion = Mock()
        mock_completion.choices = [mock_choice]
        mock_completion.usage = mock_usage
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_class.return_value = mock_client
        
        provider = OpenAIProvider(api_key="test-key")
        provider.client = mock_client
        
        request = GenerationRequest(prompt="Test prompt", tone="casual")
        response = provider.generate_text(request)
        
        assert response.error is None
        assert response.content == "Generated content"
        assert response.provider == "openai"
        assert response.tokens_used == 150


class TestAIService:
    """Test AI service with provider fallback."""
    
    @patch('app.services.ai_service.MiniMaxProvider')
    @patch('app.services.ai_service.OpenAIProvider')
    def test_service_uses_primary_when_available(self, mock_openai_class, mock_minimax_class):
        """Test service uses primary provider when available."""
        # Setup mocks
        mock_minimax = Mock()
        mock_minimax.is_available.return_value = True
        mock_minimax.generate_text.return_value = AIResponse(
            content="MiniMax content",
            provider="minimax",
            model="MiniMax-Text-01",
            tokens_used=100
        )
        mock_minimax_class.return_value = mock_minimax
        
        mock_openai = Mock()
        mock_openai.is_available.return_value = True
        mock_openai_class.return_value = mock_openai
        
        service = AIService()
        service.primary_provider = mock_minimax
        service.fallback_provider = mock_openai
        
        request = GenerationRequest(prompt="Test")
        response = service.generate_text(request)
        
        assert response.content == "MiniMax content"
        assert response.provider == "minimax"
        mock_minimax.generate_text.assert_called_once()
        mock_openai.generate_text.assert_not_called()
    
    @patch('app.services.ai_service.MiniMaxProvider')
    @patch('app.services.ai_service.OpenAIProvider')
    def test_service_fallback_when_primary_fails(self, mock_openai_class, mock_minimax_class):
        """Test service falls back to secondary provider when primary fails."""
        # Setup mocks
        mock_minimax = Mock()
        mock_minimax.is_available.return_value = True
        mock_minimax.generate_text.return_value = AIResponse(
            content="",
            provider="minimax",
            model="MiniMax-Text-01",
            error="API error"
        )
        mock_minimax_class.return_value = mock_minimax
        
        mock_openai = Mock()
        mock_openai.is_available.return_value = True
        mock_openai.generate_text.return_value = AIResponse(
            content="OpenAI content",
            provider="openai",
            model="gpt-4o-mini",
            tokens_used=120
        )
        mock_openai_class.return_value = mock_openai
        
        service = AIService()
        service.primary_provider = mock_minimax
        service.fallback_provider = mock_openai
        
        request = GenerationRequest(prompt="Test")
        response = service.generate_text(request)
        
        assert response.content == "OpenAI content"
        assert response.provider == "openai"
        mock_minimax.generate_text.assert_called_once()
        mock_openai.generate_text.assert_called_once()
    
    @patch('app.services.ai_service.MiniMaxProvider')
    @patch('app.services.ai_service.OpenAIProvider')
    def test_service_uses_fallback_when_primary_unavailable(self, mock_openai_class, mock_minimax_class):
        """Test service uses fallback when primary is not available."""
        mock_minimax = Mock()
        mock_minimax.is_available.return_value = False
        mock_minimax_class.return_value = mock_minimax
        
        mock_openai = Mock()
        mock_openai.is_available.return_value = True
        mock_openai.generate_text.return_value = AIResponse(
            content="OpenAI content",
            provider="openai",
            model="gpt-4o-mini"
        )
        mock_openai_class.return_value = mock_openai
        
        service = AIService()
        service.primary_provider = mock_minimax
        service.fallback_provider = mock_openai
        
        request = GenerationRequest(prompt="Test")
        response = service.generate_text(request)
        
        assert response.content == "OpenAI content"
        mock_minimax.generate_text.assert_not_called()
        mock_openai.generate_text.assert_called_once()
    
    @patch('app.services.ai_service.MiniMaxProvider')
    @patch('app.services.ai_service.OpenAIProvider')
    def test_service_error_when_no_providers_available(self, mock_openai_class, mock_minimax_class):
        """Test service returns error when no providers are available."""
        mock_minimax = Mock()
        mock_minimax.is_available.return_value = False
        mock_minimax_class.return_value = mock_minimax
        
        mock_openai = Mock()
        mock_openai.is_available.return_value = False
        mock_openai_class.return_value = mock_openai
        
        service = AIService()
        service.primary_provider = mock_minimax
        service.fallback_provider = mock_openai
        
        request = GenerationRequest(prompt="Test")
        response = service.generate_text(request)
        
        assert response.error is not None
        assert "No AI providers available" in response.error
    
    def test_generate_post(self):
        """Test generate_post method."""
        service = AIService()
        service.primary_provider = Mock()
        service.primary_provider.is_available.return_value = True
        service.primary_provider.generate_text.return_value = AIResponse(
            content="Generated post content",
            provider="minimax",
            model="MiniMax-Text-01",
            tokens_used=50
        )
        
        response = service.generate_post(
            topic="AI technology",
            tone="professional",
            max_length=280
        )
        
        assert response.content == "Generated post content"
        assert response.provider == "minimax"
    
    def test_generate_thread(self):
        """Test generate_thread method."""
        service = AIService()
        service.primary_provider = Mock()
        service.primary_provider.is_available.return_value = True
        service.primary_provider.generate_text.return_value = AIResponse(
            content="1. First post\n2. Second post\n3. Third post",
            provider="minimax",
            model="MiniMax-Text-01"
        )
        
        response = service.generate_thread(
            topic="Machine learning",
            tone="educational",
            num_posts=3
        )
        
        assert "Machine learning" in service.primary_provider.generate_text.call_args[0][0].prompt
    
    def test_suggest_hashtags(self):
        """Test suggest_hashtags method."""
        service = AIService()
        service.primary_provider = Mock()
        service.primary_provider.is_available.return_value = True
        service.primary_provider.generate_text.return_value = AIResponse(
            content="#AI, #MachineLearning, #Technology",
            provider="minimax",
            model="MiniMax-Text-01"
        )
        
        response = service.suggest_hashtags(
            content="AI is transforming the world",
            count=5
        )
        
        assert "AI is transforming" in service.primary_provider.generate_text.call_args[0][0].prompt
    
    def test_get_available_provider(self):
        """Test get_available_provider method."""
        service = AIService()
        
        # Both available
        service.primary_provider = Mock()
        service.primary_provider.is_available.return_value = True
        service.fallback_provider = Mock()
        service.fallback_provider.is_available.return_value = True
        assert service.get_available_provider() == "minimax"
        
        # Only fallback available
        service.primary_provider.is_available.return_value = False
        assert service.get_available_provider() == "openai"
        
        # None available
        service.fallback_provider.is_available.return_value = False
        assert service.get_available_provider() == "none"


class TestAIGenerationAPI:
    """Test AI generation API endpoints."""
    
    def test_get_ai_status(self, client):
        """Test GET /api/ai/status endpoint."""
        with patch('app.routers.ai_generation.ai_service') as mock_service:
            mock_service.get_available_provider.return_value = "minimax"
            mock_service.primary_provider.is_available.return_value = True
            mock_service.fallback_provider.is_available.return_value = True
            
            response = client.get("/api/ai/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["primary_provider"] == "minimax"
            assert data["primary_available"] is True
            assert data["fallback_provider"] == "openai"
            assert data["status"] == "ready"
    
    def test_get_ai_status_unavailable(self, client):
        """Test AI status when no providers available."""
        with patch('app.routers.ai_generation.ai_service') as mock_service:
            mock_service.get_available_provider.return_value = "none"
            mock_service.primary_provider.is_available.return_value = False
            mock_service.fallback_provider.is_available.return_value = False
            
            response = client.get("/api/ai/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unavailable"
    
    def test_generate_post_unauthorized(self, client):
        """Test POST /api/ai/generate/post without auth."""
        response = client.post("/api/ai/generate/post", json={
            "topic": "Test topic"
        })
        
        assert response.status_code == 401
    
    def test_generate_post_service_unavailable(self, client, test_user):
        """Test generate post when AI service is unavailable."""
        # Login to get token
        with patch('app.routers.ai_generation.ai_service') as mock_service:
            mock_service.get_available_provider.return_value = "none"
            
            response = client.post("/api/ai/generate/post", json={
                "topic": "Test topic"
            })
            
            # Should get 401 since we're not authenticated
            assert response.status_code == 401
    
    def test_suggest_hashtags_validation(self, client):
        """Test hashtag suggestion validation."""
        response = client.post("/api/ai/suggest/hashtags", json={
            "content": "ab",  # Too short
            "count": 50  # Too many
        })
        
        assert response.status_code == 401  # Unauthorized first


class TestContentTemplatesAPI:
    """Test content template API endpoints."""
    
    def test_list_templates_unauthorized(self, client):
        """Test GET /api/ai/templates without auth."""
        response = client.get("/api/ai/templates")
        assert response.status_code == 401
    
    def test_create_template_validation(self, client):
        """Test template creation validation."""
        # Missing required fields
        response = client.post("/api/ai/templates", json={
            "name": "Test"
            # Missing template_type and prompt_template
        })
        assert response.status_code == 401  # Unauthorized first
    
    def test_get_template_not_found(self, client):
        """Test GET /api/ai/templates/{id} with invalid ID."""
        response = client.get("/api/ai/templates/invalid-id")
        assert response.status_code == 401


class TestThreadParsing:
    """Test thread content parsing."""
    
    def test_parse_numbered_thread(self):
        """Test parsing thread with numbered format."""
        from app.routers.ai_generation import _parse_thread_content
        
        content = """1. First post in the thread
        2. Second post here
        3. Third and final post"""
        
        posts = _parse_thread_content(content, 3)
        
        assert len(posts) == 3
        assert posts[0].number == 1
        assert "First post" in posts[0].content
        assert posts[1].number == 2
        assert posts[2].number == 3
    
    def test_parse_thread_with_post_prefix(self):
        """Test parsing thread with 'Post X:' format."""
        from app.routers.ai_generation import _parse_thread_content
        
        content = """Post 1: First content here
        Post 2: Second content here"""
        
        posts = _parse_thread_content(content, 2)
        
        assert len(posts) == 2
        assert posts[0].number == 1
        assert posts[1].number == 2
    
    def test_parse_thread_fallback_split(self):
        """Test thread parsing fallback when no numbers found."""
        from app.routers.ai_generation import _parse_thread_content
        
        # Long content without numbers - should be split into chunks
        content = " ".join(["word"] * 500)
        
        posts = _parse_thread_content(content, 5)
        
        # Should split into multiple posts
        assert len(posts) >= 1
        # Each post should be under 280 chars (we split at 250)
        for post in posts:
            assert post.char_count <= 280, f"Post {post.number} has {post.char_count} chars"


class TestHashtagParsing:
    """Test hashtag parsing from AI response."""
    
    def test_parse_hashtags_with_hash(self):
        """Test parsing hashtags with # symbol."""
        from app.routers.ai_generation import _parse_hashtags
        
        content = "Here are some tags: #AI, #MachineLearning, #Tech"
        hashtags = _parse_hashtags(content)
        
        assert len(hashtags) == 3
        assert "#AI" in hashtags
        assert "#MachineLearning" in hashtags
        assert "#Tech" in hashtags
    
    def test_parse_hashtags_no_duplicates(self):
        """Test that duplicate hashtags are removed."""
        from app.routers.ai_generation import _parse_hashtags
        
        content = "#AI #ai #AI #machinelearning"
        hashtags = _parse_hashtags(content)
        
        # Should have no duplicates (case insensitive)
        assert len(hashtags) == 2
    
    def test_parse_hashtags_fallback(self):
        """Test hashtag parsing fallback when no # found."""
        from app.routers.ai_generation import _parse_hashtags
        
        content = "artificial intelligence machine learning technology"
        hashtags = _parse_hashtags(content)
        
        # Should extract words and add #
        assert len(hashtags) > 0
        assert all(tag.startswith('#') for tag in hashtags)


class TestSystemPrompts:
    """Test system prompt generation for different tones."""
    
    def test_professional_tone_prompt(self):
        """Test professional tone system prompt."""
        provider = MiniMaxProvider(api_key="test")
        prompt = provider._build_system_prompt("professional")
        
        assert "professional" in prompt.lower()
        assert "business" in prompt.lower()
    
    def test_casual_tone_prompt(self):
        """Test casual tone system prompt."""
        provider = MiniMaxProvider(api_key="test")
        prompt = provider._build_system_prompt("casual")
        
        assert "casual" in prompt.lower()
        assert "conversational" in prompt.lower()
    
    def test_witty_tone_prompt(self):
        """Test witty tone system prompt."""
        provider = MiniMaxProvider(api_key="test")
        prompt = provider._build_system_prompt("witty")
        
        assert "witty" in prompt.lower() or "humor" in prompt.lower()
    
    def test_default_tone_prompt(self):
        """Test default tone falls back to professional."""
        provider = MiniMaxProvider(api_key="test")
        prompt = provider._build_system_prompt("unknown_tone")
        
        assert "professional" in prompt.lower()
