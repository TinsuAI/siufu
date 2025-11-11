#!/usr/bin/env python3
"""
Seed script to create MVP user and organization for development/testing
This script is idempotent - it checks if records exist before creating them.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.core.security import get_password_hash
from src.models.organization import Organization
from src.models.user import User


async def seed_mvp_data():
    """Create MVP organization and user if they don't exist"""

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        # Check if organization exists
        result = await session.execute(
            select(Organization).where(Organization.name == "Demo Organization")
        )
        organization = result.scalars().first()

        if not organization:
            print("Creating Demo Organization...")
            organization = Organization(
                name="Demo Organization"
            )
            session.add(organization)
            await session.commit()
            await session.refresh(organization)
            print(f"✓ Created organization: {organization.name} (ID: {organization.id})")
        else:
            print(f"✓ Organization already exists: {organization.name} (ID: {organization.id})")

        # Check if demo user exists
        result = await session.execute(
            select(User).where(User.email == "demo@example.com")
        )
        user = result.scalars().first()

        if not user:
            print("Creating Demo User...")
            hashed_password = get_password_hash("password123")
            user = User(
                email="demo@example.com",
                hashed_password=hashed_password,
                full_name="Demo User",
                role="admin",
                is_active=True,
                organization_id=organization.id
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"✓ Created user: {user.email} (ID: {user.id}, Role: {user.role})")
            print("  Password: password123")
        else:
            print(f"✓ User already exists: {user.email} (ID: {user.id}, Role: {user.role})")

    await engine.dispose()

    print("\n✓ MVP seeding complete!")
    print("  Login credentials:")
    print("  - Email: demo@example.com")
    print("  - Password: password123")


if __name__ == "__main__":
    asyncio.run(seed_mvp_data())
