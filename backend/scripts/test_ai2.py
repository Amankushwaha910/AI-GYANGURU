"""Debug exact JSON parse failure."""
import asyncio, sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.ai.providers.groq_provider import GroqProvider
from app.ai.base import AIMessage
from app.ai.prompt_builder import PromptBuilder

async def main():
    provider = GroqProvider()
    builder = PromptBuilder()

    messages = builder.build_summary_prompt(
        topic="Newton's Laws of Motion",
        sections=["definition", "key_concepts", "revision_notes"]
    )
    resp = await provider.complete(messages, model=settings.groq_default_model, temperature=0.3)

    text = resp.content.strip()
    print(f"Length: {len(text)}")
    print(f"Starts with: {repr(text[:20])}")
    print(f"Ends with:   {repr(text[-20:])}")
    print()

    # Try direct parse
    try:
        data = json.loads(text)
        print("Direct parse OK:", list(data.keys()))
        return
    except json.JSONDecodeError as e:
        print(f"Direct parse failed at pos {e.pos}: {e.msg}")
        print(f"Context: {repr(text[max(0,e.pos-30):e.pos+30])}")

    # Try fence strip
    fence_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if fence_match:
        inner = fence_match.group(1).strip()
        print(f"\nFence match found. Inner starts: {repr(inner[:50])}")
        try:
            data = json.loads(inner)
            print("Fence parse OK:", list(data.keys()))
            return
        except json.JSONDecodeError as e:
            print(f"Fence parse failed at pos {e.pos}: {e.msg}")
            print(f"Context: {repr(inner[max(0,e.pos-30):e.pos+30])}")
    else:
        print("\nNo fence match")

    # Brute force: find outermost {}
    start = text.find('{')
    end = text.rfind('}') + 1
    inner = text[start:end]
    print(f"\nBrute force: [{start}:{end}], length={len(inner)}")
    try:
        data = json.loads(inner)
        print("Brute force parse OK:", list(data.keys()))
    except json.JSONDecodeError as e:
        print(f"Brute force failed at pos {e.pos}: {e.msg}")
        print(f"Context: {repr(inner[max(0,e.pos-50):e.pos+50])}")

asyncio.run(main())
