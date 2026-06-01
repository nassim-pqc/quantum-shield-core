"""
database.py — Async database engine and session factory.

Backends (DATABASE_URL):
  - SQLite (dev/tests): sqlite+aiosqlite:///./quantum_shield.db
  - PostgreSQL (prod):  postgresql+asyncpg://user:pass@host:5432/dbname
"""

import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from constants import DB_MAX_OVERFLOW, DB_POOL_SIZE, DB_POOL_TIMEOUT_SECONDS

DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./quantum_shield.db",
)

_engine_kwargs: dict = {"echo": os.environ.get("SQL_ECHO", "").lower() == "true"}

if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["poolclass"] = NullPool
elif DATABASE_URL.startswith("postgresql"):
    _engine_kwargs.update(
        pool_size=int(os.environ.get("DB_POOL_SIZE", DB_POOL_SIZE)),
        max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", DB_MAX_OVERFLOW)),
        pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", DB_POOL_TIMEOUT_SECONDS)),
        pool_pre_ping=True,
    )

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency — yields a session with commit/rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    """Ping the database (used by /health)."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def init_db() -> None:
    """Create all tables if they do not exist (dev fallback; prefer Alembic in prod)."""
    from models import ApiKey, AuditLog  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
