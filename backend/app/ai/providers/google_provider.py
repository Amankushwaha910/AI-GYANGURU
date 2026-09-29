"""
Google Gemini AI provider implementation.
Requires: google-generativeai>=0.8 (pip install google-generativeai)
Configure: GOOGLE_API_KEY in backend/.env
"""
from typing import AsyncIterator, List, Optional

from app.ai.base import AIMessage, AIResponse, AIStreamChunk, BaseAIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderError


class GoogleProvider(BaseAIProvider):
    """
    Google Gemini API provider using the official google-generativeai SDK.
    """

    def __init__(self) -> None:
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise AIProviderError(
                "google-generativeai package is not installed. "
                "Run: pip install google-generativeai>=0.8"
            )
        if not settings.google_api_key:
            raise AIProviderError(
                "Google Gemini is not configured. "
                "Please add GOOGLE_API_KEY to your .env file."
            )
        genai.configure(api_key=settings.google_api_key)
        self._genai = genai

    def get_provider_name(self) -> str:
        return "google"

    def get_supported_models(self) -> List[str]:
        return settings.google_supported_models

    def _build_contents(self, messages: List[AIMessage]) -> tuple[str, list]:
        """
        Convert AIMessage list to Gemini format.
        Gemini uses a system_instruction + contents list.
        """
        system_instruction = ""
        contents = []
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                contents.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                contents.append({"role": "model", "parts": [msg.content]})
        return system_instruction, contents

    async def complete(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """Non-streaming completion via Google Gemini."""
        try:
            import asyncio
            system_instruction, contents = self._build_contents(messages)

            generation_config: dict = {"temperature": temperature}
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            # Run synchronous Gemini SDK in thread pool to avoid blocking event loop
            def _call():
                gemini_model = self._genai.GenerativeModel(
                    model_name=model,
                    system_instruction=system_instruction or None,
                    generation_config=generation_config,
                )
                response = gemini_model.generate_content(
                    [c["parts"][0] for c in contents] if len(contents) == 1
                    else contents
                )
                return response

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, _call)

            text = response.text if hasattr(response, "text") else ""
            usage = response.usage_metadata if hasattr(response, "usage_metadata") else None

            return AIResponse(
                content=text,
                model=model,
                prompt_tokens=getattr(usage, "prompt_token_count", 0) if usage else 0,
                completion_tokens=getattr(usage, "candidates_token_count", 0) if usage else 0,
                total_tokens=getattr(usage, "total_token_count", 0) if usage else 0,
                finish_reason="stop",
            )
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"Google Gemini completion failed: {str(exc)}") from exc

    async def stream(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[AIStreamChunk]:
        """Streaming is not yet implemented for Google; falls back to full completion."""
        response = await self.complete(messages, model, temperature, max_tokens)
        yield AIStreamChunk(content=response.content, is_final=True, finish_reason="stop")
