"""
Seed script — creates a demo user for local development.
Run once after `alembic upgrade head`:

    python scripts/seed_demo.py

Demo credentials:
    Email:    demo@gyanguru.com
    Password: Demo@1234
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.user import Profile
from sqlalchemy import select


DEMO_EMAIL = "demo@gyanguru.com"
DEMO_PASSWORD = "Demo@1234"
DEMO_NAME = "Demo Student"


async def seed():
    async with AsyncSessionLocal() as session:
        # Check if demo user already exists
        result = await session.execute(
            select(User).where(User.email == DEMO_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"✓ Demo user already exists: {DEMO_EMAIL}")
            return

        # Create user
        user = User(
            email=DEMO_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            role=UserRole.student,
            is_active=True,
            is_email_verified=True,
        )
        session.add(user)
        await session.flush()

        # Create profile
        profile = Profile(
            user_id=user.id,
            full_name=DEMO_NAME,
            education_level="B.Tech",
            exam_target="GATE",
        )
        session.add(profile)
        await session.commit()

        print("=" * 45)
        print("✅ Demo user created successfully!")
        print("=" * 45)
        print(f"  Email    : {DEMO_EMAIL}")
        print(f"  Password : {DEMO_PASSWORD}")
        print(f"  Role     : student")
        print("=" * 45)
        print("Go to http://localhost:5174/login to sign in.")


if __name__ == "__main__":
    asyncio.run(seed())
