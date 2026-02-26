"""AI Service abstraction layer for content generation.

Supports MiniMax as primary provider with OpenAI fallback.
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Standardized AI response format."""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    error: Optional[str] = None


@dataclass
class GenerationRequest:
    """Request for AI content generation."""
    prompt: str
    tone: str = "professional"
    max_length: int = 500
    temperature: float = 0.7
    context: Optional[str] = None
    hashtags: Optional[List[str]] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_text(self, request: GenerationRequest) -> AIResponse:
        """Generate text content."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available/configured."""
        pass


class MiniMaxProvider(AIProvider):
    """MiniMax AI provider implementation."""
    
    DEFAULT_MODEL = "MiniMax-Text-01"
    API_URL = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.model = os.getenv("MINIMAX_MODEL", self.DEFAULT_MODEL)
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def generate_text(self, request: GenerationRequest) -> AIResponse:
        """Generate text using MiniMax API."""
        if not self.api_key:
            return AIResponse(
                content="",
                provider="minimax",
                model=self.model,
                error="MiniMax API key not configured"
            )
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build system prompt based on tone
            system_prompt = self._build_system_prompt(request.tone)
            
            # Build user prompt with context if provided
            user_prompt = request.prompt
            if request.context:
                user_prompt = f"Context: {request.context}\n\nTask: {request.prompt}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": request.temperature,
                "max_tokens": min(request.max_length * 2, 4096)  # Approximate token count
            }
            
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self.API_URL,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                
                return AIResponse(
                    content=content.strip(),
                    provider="minimax",
                    model=self.model,
                    tokens_used=usage.get("total_tokens"),
                    finish_reason=data["choices"][0].get("finish_reason")
                )
            else:
                return AIResponse(
                    content="",
                    provider="minimax",
                    model=self.model,
                    error=f"Unexpected response format: {data}"
                )
                
        except httpx.HTTPError as e:
            logger.error(f"MiniMax API error: {e}")
            return AIResponse(
                content="",
                provider="minimax",
                model=self.model,
                error=f"API error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"MiniMax generation error: {e}")
            return AIResponse(
                content="",
                provider="minimax",
                model=self.model,
                error=f"Generation failed: {str(e)}"
            )
    
    def _build_system_prompt(self, tone: str) -> str:
        """Build system prompt based on tone."""
        tone_prompts = {
            "professional": "You are a professional social media content creator. Write in a professional, business-appropriate tone.",
            "casual": "You are a friendly social media content creator. Write in a casual, conversational tone.",
            "witty": "You are a witty social media content creator. Write with humor and clever wordplay.",
            "inspirational": "You are an inspirational social media content creator. Write motivational and uplifting content.",
            "educational": "You are an educational content creator. Write informative, clear, and helpful content.",
            "promotional": "You are a marketing expert. Write persuasive, engaging promotional content.",
        }
        return tone_prompts.get(tone, tone_prompts["professional"])


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)
        self.client: Optional[OpenAI] = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    def is_available(self) -> bool:
        return bool(self.api_key and self.client)
    
    def generate_text(self, request: GenerationRequest) -> AIResponse:
        """Generate text using OpenAI API."""
        if not self.client:
            return AIResponse(
                content="",
                provider="openai",
                model=self.model,
                error="OpenAI API key not configured"
            )
        
        try:
            system_prompt = self._build_system_prompt(request.tone)
            
            user_prompt = request.prompt
            if request.context:
                user_prompt = f"Context: {request.context}\n\nTask: {request.prompt}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=request.temperature,
                max_tokens=min(request.max_length * 2, 4096)
            )
            
            return AIResponse(
                content=response.choices[0].message.content.strip(),
                provider="openai",
                model=self.model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return AIResponse(
                content="",
                provider="openai",
                model=self.model,
                error=f"Generation failed: {str(e)}"
            )
    
    def _build_system_prompt(self, tone: str) -> str:
        """Build system prompt based on tone."""
        tone_prompts = {
            "professional": "You are a professional social media content creator. Write in a professional, business-appropriate tone.",
            "casual": "You are a friendly social media content creator. Write in a casual, conversational tone.",
            "witty": "You are a witty social media content creator. Write with humor and clever wordplay.",
            "inspirational": "You are an inspirational social media content creator. Write motivational and uplifting content.",
            "educational": "You are an educational content creator. Write informative, clear, and helpful content.",
            "promotional": "You are a marketing expert. Write persuasive, engaging promotional content.",
        }
        return tone_prompts.get(tone, tone_prompts["professional"])


class AIService:
    """AI Service with primary/fallback provider support."""
    
    def __init__(self):
        self.primary_provider: AIProvider = MiniMaxProvider()
        self.fallback_provider: AIProvider = OpenAIProvider()
    
    def generate_text(self, request: GenerationRequest) -> AIResponse:
        """Generate text using primary provider with fallback."""
        # Try primary provider first
        if self.primary_provider.is_available():
            response = self.primary_provider.generate_text(request)
            if not response.error:
                return response
            logger.warning(f"Primary provider failed: {response.error}, trying fallback")
        
        # Try fallback provider
        if self.fallback_provider.is_available():
            return self.fallback_provider.generate_text(request)
        
        # No providers available
        return AIResponse(
            content="",
            provider="none",
            model="none",
            error="No AI providers available. Please configure MINIMAX_API_KEY or OPENAI_API_KEY."
        )
    
    def generate_post(self, topic: str, tone: str = "professional", 
                      max_length: int = 280, context: Optional[str] = None) -> AIResponse:
        """Generate a single social media post."""
        prompt = f"Write a social media post about: {topic}\n\nKeep it under {max_length} characters."
        request = GenerationRequest(
            prompt=prompt,
            tone=tone,
            max_length=max_length,
            context=context
        )
        return self.generate_text(request)
    
    def generate_thread(self, topic: str, tone: str = "professional",
                        num_posts: int = 5, context: Optional[str] = None) -> AIResponse:
        """Generate a thread of connected posts."""
        prompt = f"""Write a Twitter/X thread about: {topic}

Create {num_posts} connected posts that flow together as a cohesive thread.
Each post should be under 280 characters.
Format as a numbered list (1., 2., etc.).
Make each post engaging and valuable on its own while contributing to the overall thread."""
        
        request = GenerationRequest(
            prompt=prompt,
            tone=tone,
            max_length=num_posts * 300,
            context=context
        )
        return self.generate_text(request)
    
    def suggest_hashtags(self, content: str, count: int = 5) -> AIResponse:
        """Suggest relevant hashtags for content."""
        prompt = f"""Given this social media content, suggest {count} relevant hashtags:

Content: {content}

Requirements:
- Mix of popular and niche hashtags
- Relevant to the content topic
- No spaces in hashtags
- Include the # symbol
- Format as a comma-separated list

Example: #SocialMedia, #ContentStrategy, #DigitalMarketing"""
        
        request = GenerationRequest(
            prompt=prompt,
            tone="professional",
            max_length=200,
            temperature=0.5
        )
        return self.generate_text(request)
    
    def get_available_provider(self) -> str:
        """Get the name of the currently available provider."""
        if self.primary_provider.is_available():
            return "minimax"
        elif self.fallback_provider.is_available():
            return "openai"
        return "none"


# Global AI service instance
ai_service = AIService()
