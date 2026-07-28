"""
Abstract AI provider interface.
All AI providers must implement this interface.
Swapping providers = implementing this class. No other code changes needed.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional


@dataclass
class AIMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class AIResponse:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"


@dataclass
class AIStreamChunk:
    content: str
    is_final: bool = False
    finish_reason: Optional[str] = None


class BaseAIProvider(ABC):
    """
    Abstract base class for all AI providers.
    Implement this to add a new AI provider (e.g., OpenAI, Anthropic, Gemini).
    """

    @abstractmethod
    async def complete(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """
        Send a completion request and return the full response.
        Used for structured JSON responses (quiz, summary).
        """
        ...

    @abstractmethod
    async def stream(
        self,
        messages: List[AIMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[AIStreamChunk]:
        """
        Stream a completion response chunk by chunk.
        Used for long-form content (summaries, explanations).
        """
        ...

    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Return list of model IDs this provider supports."""
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider's name string."""
        ...
