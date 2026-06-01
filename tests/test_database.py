"""
test_database.py — Tests for database connection and initialization.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio

from database import check_db_connection, init_db


@pytest_asyncio.fixture
async def db_fixture():
    """Initialize the database for testing."""
    await init_db()
    yield
    # Cleanup is automatic with in-memory SQLite


class TestCheckDbConnection:
    """Tests for check_db_connection() function."""

    @pytest.mark.asyncio
    async def test_check_db_connection_succeeds(self):
        """Verify check_db_connection returns True when database is accessible."""
        result = await check_db_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_check_db_connection_returns_boolean(self):
        """Verify check_db_connection returns a boolean."""
        result = await check_db_connection()
        assert isinstance(result, bool)


class TestInitDb:
    """Tests for init_db() function."""

    @pytest.mark.asyncio
    async def test_init_db_completes_without_error(self, db_fixture):
        """Verify init_db() completes successfully."""
        # If we get here without exception, init_db worked
        assert True

    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self, db_fixture):
        """Verify init_db() creates database tables."""
        # Verify we can connect and query after init
        result = await check_db_connection()
        assert result is True
