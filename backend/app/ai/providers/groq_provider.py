"""
Groq AI provider implementation.
Supports: Llama 3.x, DeepSeek R1, Gemma, Mixtral
"""
import asyncio
from typing import AsyncIterator, List, Optional

import httpx
from groq import AsyncGroq

from app.ai.base import AIMessage, AIResponse, AIStreamChunk, BaseAIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderError


class GroqProvider(BaseAIProvider):
    """
    Groq API provider using the official groq-python SDK.
    """

    def __init__(self) -> None:
        self._client = AsyncGroq(
            api_key=settings.groq_api_key,
            timeout=settings.ai_request_timeout,
        )

    def get_provider_name(self) -> str:
        return "groq"

    def get_supported_models(self) -> List[str]:
        return settings.groq_supported_models

    def _to_groq_messages(self, messages: List[AIMessage]) -> List[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def complete(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """Non-streaming completion — used for structured JSON responses."""
        try:
            kwargs = {
                "model": model,
                "messages": self._to_groq_messages(messages),
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

        except Exception as exc:
            raise AIProviderError(f"Groq completion failed: {str(exc)}") from exc

    async def stream(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[AIStreamChunk]:
        """Streaming completion — yields chunks as they arrive from Groq."""
        try:
            kwargs = {
                "model": model,
                "messages": self._to_groq_messages(messages),
                "temperature": temperature,
                "stream": True,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            async with self._client.chat.completions.with_streaming_response.create(
                **kwargs
            ) as response:
                async for chunk in response.iter_lines():
                    if chunk.startswith("data: "):
                        data = chunk[6:]
                        if data == "[DONE]":
                            yield AIStreamChunk(content="", is_final=True, finish_reason="stop")
                            return
                        # Parse chunk manually for streaming
                        import json
                        try:
                            parsed = json.loads(data)
                            delta = parsed["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            finish = parsed["choices"][0].get("finish_reason")
                            if content:
                                yield AIStreamChunk(
                                    content=content,
                                    is_final=bool(finish),
                                    finish_reason=finish,
                                )
                        except (json.JSONDecodeError, KeyError):
                            continue

        except Exception as exc:
            raise AIProviderError(f"Groq streaming failed: {str(exc)}") from exc
