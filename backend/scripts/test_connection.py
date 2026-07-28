"""
Quick end-to-end connection test.
Run from: backend/
  python scripts/test_connection.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    from app.core.config import settings
    from app.core.database import get_engine
    engine = get_engine()
    from sqlalchemy import text

    print(f"Connecting to: {settings.supabase_url}")
    print(f"AI Provider  : {settings.ai_provider} / {settings.groq_default_model}")
    print()

    async with engine.connect() as conn:
        # Basic ping
        result = await conn.execute(text("SELECT 1"))
        print("Ping             : OK ->", result.scalar())

        # List tables
        result = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        ))
        tables = [r[0] for r in result]
        print(f"Tables in schema : {tables}")

    await engine.dispose()
    print("\nAll checks passed.")

asyncio.run(main())
