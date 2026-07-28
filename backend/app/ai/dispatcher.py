"""
AI Dispatcher — routes requests to the correct provider.
Provider selection is driven by configuration, not hardcoded logic.
"""
import time
from typing import AsyncIterator, List, Optional
from functools import lru_cache

from app.ai.base import AIMessage, AIResponse, AIStreamChunk, BaseAIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderError


class AIDispatcher:
    """
    Central dispatcher that manages provider instances and routes requests.
    To add a new provider: register it in the provider registry below.
    """

    def __init__(self) -> None:
        self._providers: dict[str, BaseAIProvider] = {}
        self._load_providers()

    def _load_providers(self) -> None:
        """Lazily initialize only the configured provider."""
        # Import here to avoid loading unused provider dependencies
        if settings.ai_provider == "groq":
            from app.ai.providers.groq_provider import GroqProvider
            self._providers["groq"] = GroqProvider()

        # Future providers:
        # elif settings.ai_provider == "openai":
        #     from app.ai.providers.openai_provider import OpenAIProvider
        #     self._providers["openai"] = OpenAIProvider()

    def get_provider(self, provider_name: Optional[str] = None) -> BaseAIProvider:
        """Return the provider instance by name, or the default provider."""
        name = provider_name or settings.ai_provider
        if name not in self._providers:
            raise AIProviderError(f"AI provider '{name}' is not configured")
        return self._providers[name]

    def resolve_model(self, model: Optional[str] = None) -> str:
        """Resolve the model to use — falls back to configured default."""
        if model and model in settings.groq_supported_models:
            return model
        return settings.groq_default_model

    async def complete(
        self,
        messages: List[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
    ) -> tuple[AIResponse, float]:
        """
        Execute a completion with timing.
        Returns (AIResponse, latency_ms).
        Retries up to AI_MAX_RETRIES times on transient failures.
        """
        resolved_model = self.resolve_model(model)
        ai_provider = self.get_provider(provider)
        last_error: Optional[Exception] = None

        for attempt in range(settings.ai_max_retries + 1):
            try:
                start = time.monotonic()
                response = await ai_provider.complete(
                    messages=messages,
                    model=resolved_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                latency_ms = (time.monotonic() - start) * 1000
                return response, latency_ms

            except AIProviderError as exc:
                last_error = exc
                if attempt < settings.ai_max_retries:
                    # Exponential backoff: 1s, 2s
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                continue

        raise AIProviderError(
            f"AI provider failed after {settings.ai_max_retries + 1} attempts: {last_error}"
        )

    async def stream(
        self,
        messages: List[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
    ) -> AsyncIterator[AIStreamChunk]:
        """Stream a completion response."""
        resolved_model = self.resolve_model(model)
        ai_provider = self.get_provider(provider)
        return ai_provider.stream(
            messages=messages,
            model=resolved_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )


@lru_cache(maxsize=1)
def get_dispatcher() -> AIDispatcher:
    """Singleton AI dispatcher — instantiated once at startup."""
    return AIDispatcher()
