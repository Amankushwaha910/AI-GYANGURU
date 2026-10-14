from types import SimpleNamespace

import pytest

from app.ai.base import AIMessage
from app.ai.providers.google_provider import GoogleProvider
from app.ai.response_formatter import ResponseFormatter
from app.core.exceptions import AIProviderError


def test_empty_and_malformed_ai_responses_are_rejected_without_echoing_content():
    formatter = ResponseFormatter()

    with pytest.raises(AIProviderError, match="empty response"):
        formatter.extract_json("  \n")

    marker = "PRIVATE_DOCUMENT_CONTENT_DO_NOT_ECHO"
    with pytest.raises(AIProviderError, match="invalid response format") as error:
        formatter.extract_json(f"not json: {marker}")

    assert marker not in error.value.message


@pytest.mark.asyncio
async def test_google_provider_passes_configured_request_timeout(monkeypatch):
    captured = {}

    class FakeModel:
        def __init__(self, **kwargs):
            captured["model_kwargs"] = kwargs

        def generate_content(self, contents, **kwargs):
            captured["contents"] = contents
            captured["request_kwargs"] = kwargs
            return SimpleNamespace(text="ok", usage_metadata=None)

    provider = GoogleProvider.__new__(GoogleProvider)
    provider._genai = SimpleNamespace(GenerativeModel=FakeModel)
    monkeypatch.setattr(
        "app.ai.providers.google_provider.settings",
        SimpleNamespace(ai_request_timeout=17),
    )

    response = await provider.complete(
        [AIMessage(role="user", content="safe test prompt")],
        model="gemini-test",
    )

    assert response.content == "ok"
    assert captured["request_kwargs"] == {"request_options": {"timeout": 17}}
