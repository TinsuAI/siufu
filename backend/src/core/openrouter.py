"""
OpenRouter API Client for GPT-5 LLM Integration
"""
import httpx
import json
from typing import List, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import sentry_sdk

from .config import settings
from .errors import OpenRouterException


class OpenRouterClient:
    """
    Client for OpenRouter API (GPT-5 access)

    OpenRouter provides a unified API for multiple LLM providers.
    This client implements OpenAI-compatible chat completions endpoint.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str | None = None):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key. If None, uses settings.OPENROUTER_API_KEY

        Raises:
            ValueError: If API key is not provided and not in settings
        """
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable."
            )

        # Initialize async HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/logai/customs-platform",  # For OpenRouter analytics
                "X-Title": "LogAI Customs Declaration Platform",  # Application identifier
                "Content-Type": "application/json"
            },
            timeout=240.0  # 240 second (4 minute) timeout for LLM responses - GPT-5 can be slow for large extractions
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "openai/gpt-5",
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Create a chat completion using OpenRouter API

        Args:
            messages: List of message dicts with 'role' and 'content' keys
                Example: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
            model: Model identifier (e.g., "openai/gpt-5", "openai/gpt-5-mini", "openai/gpt-5-nano")
            temperature: Sampling temperature (0.0-2.0). Lower = more deterministic
            max_tokens: Maximum tokens to generate

        Returns:
            API response dict with structure:
            {
                "id": "gen-...",
                "model": "openai/gpt-5",
                "choices": [{
                    "message": {"role": "assistant", "content": "..."},
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 1200,
                    "completion_tokens": 800,
                    "total_tokens": 2000
                }
            }

        Raises:
            OpenRouterException: For API errors
            httpx.HTTPStatusError: For 4xx/5xx responses
            httpx.TimeoutException: If request exceeds timeout
        """
        return await self._call_openrouter_api_with_retry(messages, model, temperature, max_tokens)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError))
    )
    async def _call_openrouter_api_with_retry(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Call OpenRouter API with retry logic for transient failures

        Retries on:
        - Timeout errors (httpx.TimeoutException)
        - Rate limit errors (429)
        - Server errors (5xx)

        Does NOT retry on:
        - Auth errors (401)
        - Bad requests (400)

        Args:
            messages: Message list
            model: Model identifier
            temperature: Temperature parameter
            max_tokens: Max tokens to generate

        Returns:
            API response dict

        Raises:
            OpenRouterException: For permanent API errors
        """
        try:
            response = await self.client.post(
                "/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()

            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError as e:
                # Log the raw response for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"OpenRouter API returned invalid JSON. "
                    f"Status code: {response.status_code}, "
                    f"Response length: {len(response.text)}, "
                    f"First 1000 chars: {response.text[:1000]}, "
                    f"Last 500 chars: {response.text[-500:]}, "
                    f"JSON error: {str(e)}"
                )
                raise OpenRouterException(
                    detail=f"OpenRouter API returned invalid JSON: {str(e)}. Response: {response.text[:200]}",
                    original_error=e
                )

        except httpx.HTTPStatusError as e:
            # Handle specific HTTP errors
            if e.response.status_code == 401:
                # Auth error - don't retry
                raise OpenRouterException(
                    detail="Invalid OpenRouter API key. Please check OPENROUTER_API_KEY in environment variables.",
                    api_status_code=401,
                    original_error=e
                )
            elif e.response.status_code == 429:
                # Rate limit - will retry with backoff
                sentry_sdk.add_breadcrumb(
                    category="llm",
                    message="OpenRouter rate limit hit, retrying...",
                    level="warning"
                )
                raise  # Re-raise to trigger retry
            elif e.response.status_code >= 500:
                # Server error - will retry
                sentry_sdk.add_breadcrumb(
                    category="llm",
                    message=f"OpenRouter server error ({e.response.status_code}), retrying...",
                    level="warning"
                )
                raise  # Re-raise to trigger retry
            else:
                # Other 4xx errors - don't retry
                error_detail = e.response.text if e.response.text else str(e)
                raise OpenRouterException(
                    detail=f"OpenRouter API error: {error_detail}",
                    api_status_code=e.response.status_code,
                    original_error=e
                )

        except httpx.TimeoutException as e:
            # Timeout - will retry
            sentry_sdk.add_breadcrumb(
                category="llm",
                message="OpenRouter API timeout, retrying...",
                level="warning"
            )
            raise  # Re-raise to trigger retry

        except Exception as e:
            # Unexpected error
            raise OpenRouterException(
                detail=f"Unexpected error calling OpenRouter API: {str(e)}",
                original_error=e
            )

    async def close(self):
        """Close the HTTP client connection pool"""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
