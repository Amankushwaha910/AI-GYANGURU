"""
OpenAI AI provider implementation.
Requires: openai>=1.0 (pip install openai)
Configure: OPENAI_API_KEY in backend/.env
"""
from typing import AsyncIterator, List, Optional

from app.ai.base import AIMessage, AIResponse, AIStreamChunk, BaseAIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderError


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI API provider using the official openai-python SDK (v1+).
    """

    def __init__(self) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise AIProviderError(
                "openai package is not installed. Run: pip install openai>=1.0"
            )
        if not settings.openai_api_key:
            raise AIProviderError(
                "OpenAI is not configured. Please add OPENAI_API_KEY to your .env file."
            )
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.ai_request_timeout,
        )

    def get_provider_name(self) -> str:
        return "openai"

    def get_supported_models(self) -> List[str]:
        return settings.openai_supported_models

    def _to_openai_messages(self, messages: List[AIMessage]) -> List[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def complete(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """Non-streaming completion."""
        try:
            kwargs: dict = {
                "model": model,
                "messages": self._to_openai_messages(messages),
                "temperature": temperature,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            response = await self._client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            usage = response.usage

            return AIResponse(
                content=choice.message.content or "",
                model=model,
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
                finish_reason=choice.finish_reason or "stop",
            )
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"OpenAI completion failed: {str(exc)}") from exc

    async def stream(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[AIStreamChunk]:
        """Streaming completion."""
        try:
            kwargs: dict = {
                "model": model,
                "messages": self._to_openai_messages(messages),
                "temperature": temperature,
                "stream": True,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            stream = await self._client.chat.completions.create(**kwargs)
            async for chunk in stream:
                delta = chunk.choices[0].delta
                content = delta.content or ""
                finish = chunk.choices[0].finish_reason
                if content:
                    yield AIStreamChunk(
                        content=content,
                        is_final=bool(finish),
                        finish_reason=finish,
                    )
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"OpenAI streaming failed: {str(exc)}") from exc
