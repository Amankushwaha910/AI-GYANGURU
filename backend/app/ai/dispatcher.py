"""
AI Dispatcher — routes requests to the correct provider and model.

Provider selection precedence (highest → lowest):
  1. Explicit `provider` argument passed to complete()
  2. Derived from the model ID prefix (e.g. "openai:gpt-4o" → openai)
  3. `settings.ai_provider` (default, configured in .env)

Model selection precedence:
  1. Explicit `model` argument (must be a valid model for the resolved provider)
  2. Provider's first supported model
  3. `settings.groq_default_model` (global fallback)
"""
import time
from typing import AsyncIterator, Dict, List, Optional, Tuple
from functools import lru_cache

from app.ai.base import AIMessage, AIResponse, AIStreamChunk, BaseAIProvider
from app.core.config import settings
from app.core.exceptions import AIProviderError

# Map of provider name → (module path, class name)
_PROVIDER_REGISTRY: Dict[str, Tuple[str, str]] = {
    "groq":   ("app.ai.providers.groq_provider",   "GroqProvider"),
    "openai": ("app.ai.providers.openai_provider",  "OpenAIProvider"),
    "google": ("app.ai.providers.google_provider",  "GoogleProvider"),
}

# Map of provider name → list of model IDs (from config)
def _provider_model_map() -> Dict[str, List[str]]:
    return {
        "groq":   settings.groq_supported_models,
        "openai": settings.openai_supported_models,
        "google": settings.google_supported_models,
    }


class AIDispatcher:
    """
    Central dispatcher that manages provider instances and routes requests.
    Providers are loaded lazily; only providers with valid API keys are available.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, BaseAIProvider] = {}
        self._load_providers()

    def _load_providers(self) -> None:
        """Load every provider whose API key is configured."""
        for name, (module_path, class_name) in _PROVIDER_REGISTRY.items():
            if self._is_configured(name):
                try:
                    import importlib
                    mod = importlib.import_module(module_path)
                    cls = getattr(mod, class_name)
                    self._providers[name] = cls()
                except AIProviderError:
                    # Missing optional dependency or missing key — skip silently
                    pass
                except Exception:
                    pass  # Don't crash the whole app for one misconfigured provider

    @staticmethod
    def _is_configured(provider: str) -> bool:
        """Return True if the provider has a non-empty API key."""
        key_map = {
            "groq":   settings.groq_api_key,
            "openai": settings.openai_api_key,
            "google": settings.google_api_key,
        }
        return bool(key_map.get(provider, ""))

    def available_providers(self) -> List[str]:
        """Return names of all loaded (configured) providers."""
        return list(self._providers.keys())

    def get_provider(self, provider_name: Optional[str] = None) -> BaseAIProvider:
        """Return the provider instance by name, or the default provider."""
        name = provider_name or settings.ai_provider
        if name not in self._providers:
            configured = list(self._providers.keys())
            if not configured:
                raise AIProviderError(
                    "No AI provider is configured. "
                    "Please add at least one API key (GROQ_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY)."
                )
            raise AIProviderError(
                f"AI provider '{name}' is not configured. "
                f"Add the corresponding API key to .env. "
                f"Currently available: {', '.join(configured)}."
            )
        return self._providers[name]

    def resolve_provider_and_model(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Resolve the provider name and model ID to use for a request.

        Returns (provider_name, model_id).

        Logic:
        - If `model` contains a colon prefix (e.g. "openai:gpt-4o"), split it.
        - If `provider` is explicitly given, use it.
        - Otherwise, check which provider's supported model list contains `model`.
        - Fall back to default provider + its default model.
        """
        model_map = _provider_model_map()

        # Handle "provider:model" shorthand
        if model and ":" in model:
            parts = model.split(":", 1)
            provider = provider or parts[0]
            model = parts[1]

        # If provider is explicit, just validate/resolve the model for it
        if provider:
            if provider not in model_map:
                raise AIProviderError(f"Unknown provider '{provider}'.")
            models = model_map[provider]
            if model and model in models:
                return provider, model
            # model not specified or not valid for provider — use provider's default
            if models:
                return provider, models[0]
            raise AIProviderError(f"Provider '{provider}' has no configured models.")

        # No provider specified — find provider by model name
        if model:
            for pname, models in model_map.items():
                if model in models and pname in self._providers:
                    return pname, model
            # model given but not found in any provider — raise helpful error
            raise AIProviderError(
                f"Model '{model}' is not available. "
                f"Check that the corresponding provider API key is configured."
            )

        # No provider, no model — use defaults
        default_provider = settings.ai_provider
        if default_provider in self._providers:
            default_models = model_map.get(default_provider, [])
            default_model = (
                settings.groq_default_model
                if default_provider == "groq"
                else (default_models[0] if default_models else "")
            )
            return default_provider, default_model

        # Fallback: first available provider
        if self._providers:
            pname = list(self._providers.keys())[0]
            models = model_map.get(pname, [])
            return pname, models[0] if models else ""

        raise AIProviderError("No AI provider is configured.")

    async def complete(
        self,
        messages: List[AIMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
    ) -> tuple[AIResponse, float]:
        """
        Execute a completion with timing and retry logic.
        Returns (AIResponse, latency_ms).

        Note: 404 model_not_found errors are NOT retried — retrying the same
        unavailable model ID is pointless and wastes the user's time.
        Only transient errors (rate limits, timeouts, 5xx) are retried.
        """
        resolved_provider, resolved_model = self.resolve_provider_and_model(model, provider)
        ai_provider = self.get_provider(resolved_provider)
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
                err_str = str(exc).lower()

                # Do NOT retry model-not-found (404) — the same request will
                # always fail.  Surface the error immediately.
                if "404" in err_str or "model_not_found" in err_str or "model not found" in err_str:
                    raise AIProviderError(
                        f"The selected AI model '{resolved_model}' is not available "
                        f"on provider '{resolved_provider}'. "
                        f"Please select a different model from the AI Model selector."
                    ) from exc

                if attempt < settings.ai_max_retries:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                continue

        raise AIProviderError(
            f"AI provider '{resolved_provider}' failed after "
            f"{settings.ai_max_retries + 1} attempts: {last_error}"
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
        resolved_provider, resolved_model = self.resolve_provider_and_model(model, provider)
        ai_provider = self.get_provider(resolved_provider)
        async for chunk in ai_provider.stream(
            messages=messages,
            model=resolved_model,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk


@lru_cache(maxsize=1)
def get_dispatcher() -> AIDispatcher:
    """Singleton AI dispatcher — instantiated once at startup."""
    return AIDispatcher()
