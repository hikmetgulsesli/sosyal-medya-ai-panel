"""AI Service abstraction layer for content generation.

Supports MiniMax as primary provider with OpenAI fallback.
"""
import os
import json
import httpx
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class AIResponse:
    """Response from AI provider."""
    content: str
    provider: str
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AIResponse:
        """Generate text from the AI provider."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available (has API key configured)."""
        pass


class MiniMaxProvider(AIProvider):
    """MiniMax AI provider implementation."""
    
    BASE_URL = "https://api.minimaxi.chat/v1/text/chatcompletion_v2"
    DEFAULT_MODEL = "MiniMax-Text-01"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.model = os.getenv("MINIMAX_MODEL", self.DEFAULT_MODEL)
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AIResponse:
        """Generate text using MiniMax API."""
        if not self.api_key:
            return AIResponse(
                content="",
                provider="minimax",
                error="MiniMax API key not configured"
            )
        
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    tokens_used = usage.get("total_tokens")
                    
                    return AIResponse(
                        content=content,
                        provider="minimax",
                        tokens_used=tokens_used
                    )
                else:
                    return AIResponse(
                        content="",
                        provider="minimax",
                        error="No content generated"
                    )
        
        except httpx.HTTPError as e:
            return AIResponse(
                content="",
                provider="minimax",
                error=f"HTTP error: {str(e)}"
            )
        except Exception as e:
            return AIResponse(
                content="",
                provider="minimax",
                error=f"Error: {str(e)}"
            )


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    BASE_URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL = "gpt-4o-mini"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL)
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AIResponse:
        """Generate text using OpenAI API."""
        if not self.api_key:
            return AIResponse(
                content="",
                provider="openai",
                error="OpenAI API key not configured"
            )
        
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                    usage = data.get("usage", {})
                    tokens_used = usage.get("total_tokens")
                    
                    return AIResponse(
                        content=content,
                        provider="openai",
                        tokens_used=tokens_used
                    )
                else:
                    return AIResponse(
                        content="",
                        provider="openai",
                        error="No content generated"
                    )
        
        except httpx.HTTPError as e:
            return AIResponse(
                content="",
                provider="openai",
                error=f"HTTP error: {str(e)}"
            )
        except Exception as e:
            return AIResponse(
                content="",
                provider="openai",
                error=f"Error: {str(e)}"
            )


class AIService:
    """AI Service with primary provider and fallback."""
    
    def __init__(self):
        self.primary = MiniMaxProvider()
        self.fallback = OpenAIProvider()
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> AIResponse:
        """Generate text using primary provider with fallback."""
        
        # Try primary provider first
        if self.primary.is_available():
            response = await self.primary.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt
            )
            if not response.error:
                return response
        
        # Fallback to OpenAI if primary fails or is unavailable
        if self.fallback.is_available():
            response = await self.fallback.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt
            )
            if not response.error:
                return response
        
        # If both fail, return error from primary or fallback
        if self.primary.is_available():
            primary_response = await self.primary.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt
            )
            return primary_response
        
        return AIResponse(
            content="",
            provider="none",
            error="No AI provider available. Please configure MINIMAX_API_KEY or OPENAI_API_KEY."
        )
    
    async def generate_post(
        self,
        topic: str,
        tone: str = "professional",
        platform: str = "twitter",
        max_length: int = 280,
        context: Optional[str] = None
    ) -> AIResponse:
        """Generate a social media post."""
        
        system_prompt = f"""You are a social media content expert. Create engaging {platform} content.
Tone: {tone}
Maximum length: {max_length} characters
Respond with only the post content, no explanations."""
        
        prompt = f"Create a {platform} post about: {topic}"
        if context:
            prompt += f"\n\nContext: {context}"
        
        return await self.generate_text(
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
            system_prompt=system_prompt
        )
    
    async def generate_thread(
        self,
        topic: str,
        tone: str = "professional",
        num_posts: int = 5,
        context: Optional[str] = None
    ) -> AIResponse:
        """Generate a Twitter/X thread."""
        
        system_prompt = f"""You are a Twitter/X thread expert. Create engaging multi-post threads.
Tone: {tone}
Each post should be under 280 characters.
Format as a numbered list (1., 2., etc.).
Make the thread flow logically with a hook in the first post."""
        
        prompt = f"Create a {num_posts}-post Twitter/X thread about: {topic}"
        if context:
            prompt += f"\n\nContext: {context}"
        
        return await self.generate_text(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.7,
            system_prompt=system_prompt
        )
    
    async def suggest_hashtags(
        self,
        content: str,
        platform: str = "twitter",
        count: int = 5
    ) -> AIResponse:
        """Suggest relevant hashtags for content."""
        
        system_prompt = f"""You are a hashtag strategy expert for {platform}.
Suggest relevant, trending hashtags that will increase reach.
Respond with only the hashtags (including #), comma-separated, no explanations."""
        
        prompt = f"Suggest {count} relevant hashtags for this content:\n\n{content}"
        
        return await self.generate_text(
            prompt=prompt,
            max_tokens=200,
            temperature=0.5,
            system_prompt=system_prompt
        )
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        providers = []
        if self.primary.is_available():
            providers.append("minimax")
        if self.fallback.is_available():
            providers.append("openai")
        return providers


# Singleton instance
ai_service = AIService()
