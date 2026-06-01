#!/usr/bin/env python3
"""
Initialize database schema and seed API keys from environment.

Usage:
  python scripts/init_db.py
  DATABASE_URL=postgresql+asyncpg://... python scripts/init_db.py
"""

import asyncio
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import select

from database import AsyncSessionLocal, init_db
from models import ApiKey


async def seed_api_keys() -> None:
    async with AsyncSessionLocal() as db:
        for env_name, role in (
            ("API_KEY_OPERATOR", "operator"),
            ("API_KEY_AUDITOR", "auditor"),
        ):
            raw = os.environ.get(env_name)
            if not raw:
                continue
            key_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            exists = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
            if exists.scalar_one_or_none():
                continue
            db.add(
                ApiKey(
                    organization=f"Seeded {role}",
                    key_hash=key_hash,
                    role=role,
                )
            )
        await db.commit()


async def main() -> None:
    await init_db()
    await seed_api_keys()
    print("Database initialized and API keys seeded.")


if __name__ == "__main__":
    asyncio.run(main())
