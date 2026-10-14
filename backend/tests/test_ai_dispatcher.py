import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ai import dispatcher as dispatcher_module
from app.ai.base import AIResponse
from app.ai.dispatcher import AIDispatcher
from app.core.exceptions import AIProviderError


class ProviderStatusError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


class StubProvider:
    def __init__(self, first_status=None):
        self.calls = 0
        self.first_status = first_status

    async def complete(self, **_kwargs):
        self.calls += 1
        if self.first_status is not None and self.calls == 1:
            try:
                raise ProviderStatusError(self.first_status)
            except ProviderStatusError as cause:
                raise AIProviderError("provider request failed") from cause
        return AIResponse(content="{}", model="test-model")


@pytest.mark.asyncio
async def test_permanent_provider_failure_is_not_retried(monkeypatch):
    provider = StubProvider(first_status=401)
    dispatcher = AIDispatcher()
    dispatcher._providers = {"groq": provider}
    monkeypatch.setattr(
        dispatcher_module, "_provider_model_map", lambda: {"groq": ["test-model"]}
    )
    monkeypatch.setattr(
        dispatcher_module, "settings", SimpleNamespace(ai_max_retries=2)
    )

    with pytest.raises(AIProviderError):
        await dispatcher.complete([], model="test-model", provider="groq")

    assert provider.calls == 1


@pytest.mark.asyncio
async def test_transient_provider_failure_retries_once_then_succeeds(monkeypatch):
    import asyncio

    provider = StubProvider(first_status=503)
    dispatcher = AIDispatcher()
    dispatcher._providers = {"groq": provider}
    monkeypatch.setattr(
        dispatcher_module, "_provider_model_map", lambda: {"groq": ["test-model"]}
    )
    monkeypatch.setattr(
        dispatcher_module, "settings", SimpleNamespace(ai_max_retries=2)
    )
    sleep = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep)

    response, _ = await dispatcher.complete(
        [], model="test-model", provider="groq"
    )

    assert response.content == "{}"
    assert provider.calls == 2
    sleep.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_rate_limit_retries_only_up_to_the_configured_count(monkeypatch):
    import asyncio

    provider = StubProvider(first_status=429)

    async def always_rate_limited(**_kwargs):
        provider.calls += 1
        try:
            raise ProviderStatusError(429)
        except ProviderStatusError as cause:
            raise AIProviderError("provider request failed") from cause

    provider.complete = always_rate_limited
    dispatcher = AIDispatcher()
    dispatcher._providers = {"groq": provider}
    monkeypatch.setattr(
        dispatcher_module, "_provider_model_map", lambda: {"groq": ["test-model"]}
    )
    monkeypatch.setattr(
        dispatcher_module, "settings", SimpleNamespace(ai_max_retries=2)
    )
    sleep = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep)

    with pytest.raises(AIProviderError, match="failed after 3 attempts"):
        await dispatcher.complete([], model="test-model", provider="groq")

    assert provider.calls == 3
    assert sleep.await_count == 2


@pytest.mark.asyncio
async def test_provider_cancellation_is_not_retried(monkeypatch):
    provider = StubProvider()

    async def cancelled(**_kwargs):
        provider.calls += 1
        raise asyncio.CancelledError()

    provider.complete = cancelled
    dispatcher = AIDispatcher()
    dispatcher._providers = {"groq": provider}
    monkeypatch.setattr(
        dispatcher_module, "_provider_model_map", lambda: {"groq": ["test-model"]}
    )
    monkeypatch.setattr(
        dispatcher_module, "settings", SimpleNamespace(ai_max_retries=2)
    )

    with pytest.raises(asyncio.CancelledError):
        await dispatcher.complete([], model="test-model", provider="groq")

    assert provider.calls == 1


def test_retry_classifier_accepts_timeouts_and_rejects_unknown_errors():
    assert not dispatcher_module._is_retryable_provider_error(
        AIProviderError("unclassified failure")
    )

    try:
        raise TimeoutError("request timed out")
    except TimeoutError as cause:
        wrapped_timeout = AIProviderError("provider request failed")
        wrapped_timeout.__cause__ = cause
    assert dispatcher_module._is_retryable_provider_error(wrapped_timeout)



def test_explicit_provider_does_not_silently_substitute_another_model(monkeypatch):
    dispatcher = AIDispatcher()
    monkeypatch.setattr(
        dispatcher_module, "_provider_model_map",
        lambda: {"groq": ["supported-model"], "openai": ["gpt-example"]},
    )

    with pytest.raises(AIProviderError, match="not available for provider"):
        dispatcher.resolve_provider_and_model(
            model="unsupported-model", provider="groq"
        )

    with pytest.raises(AIProviderError, match="conflicts with provider"):
        dispatcher.resolve_provider_and_model(
            model="openai:gpt-example", provider="groq"
        )


def test_provider_prefixed_model_resolves_only_when_consistent(monkeypatch):
    dispatcher = AIDispatcher()
    monkeypatch.setattr(
        dispatcher_module, "_provider_model_map",
        lambda: {"groq": ["supported-model"]},
    )

    assert dispatcher.resolve_provider_and_model(
        model="groq:supported-model"
    ) == ("groq", "supported-model")
