"""
Test AI provider JSON parsing directly.
Run from: backend/
  python scripts/test_ai.py
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.ai.providers.groq_provider import GroqProvider
from app.ai.base import AIMessage
from app.ai.response_formatter import ResponseFormatter
from app.ai.prompt_builder import PromptBuilder


async def main():
    provider = GroqProvider()
    formatter = ResponseFormatter()
    builder = PromptBuilder()

    print(f"Model: {settings.groq_default_model}\n")

    # ── Test 1: Summary ──────────────────────────────────────────────────────
    print("=== SUMMARY TEST ===")
    messages = builder.build_summary_prompt(
        topic="Newton's Laws of Motion",
        sections=["definition", "key_concepts", "revision_notes"]
    )
    resp = await provider.complete(messages, model=settings.groq_default_model, temperature=0.3)
    print("Raw response (first 300 chars):")
    print(repr(resp.content[:300]))
    print()
    try:
        data = formatter.extract_json(resp.content)
        print("Parsed OK. Keys:", list(data.keys()))
    except Exception as e:
        print("PARSE FAILED:", e)

    print()

    # ── Test 2: Explanation ───────────────────────────────────────────────────
    print("=== EXPLANATION TEST ===")
    messages = builder.build_explanation_prompt(topic="Photosynthesis")
    resp = await provider.complete(messages, model=settings.groq_default_model, temperature=0.3)
    print("Raw response (first 300 chars):")
    print(repr(resp.content[:300]))
    print()
    try:
        data = formatter.extract_json(resp.content)
        print("Parsed OK. Keys:", list(data.keys()))
    except Exception as e:
        print("PARSE FAILED:", e)


asyncio.run(main())
