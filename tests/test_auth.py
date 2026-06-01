"""
test_auth.py — Tests for authentication and RBAC.
"""

import hashlib
import os

os.environ.setdefault("API_KEY_OPERATOR", "test-operator-api-key-secure-enough-32chars!!")
os.environ.setdefault("API_KEY_AUDITOR", "test-auditor-api-key-secure-enough-32chars!!!")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from auth import get_current_role, require_role
from database import Base, get_db
from models import ApiKey

OPERATOR_KEY = "test-operator-key-valid"
AUDITOR_KEY = "test-auditor-key-valid"
INVALID_KEY = "invalid-key-does-not-exist"
INACTIVE_KEY = "inactive-key"


@pytest_asyncio.fixture
async def test_db():
    """Create an isolated in-memory database for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        # Insert test keys
        operator_hash = hashlib.sha256(OPERATOR_KEY.encode()).hexdigest()
        auditor_hash = hashlib.sha256(AUDITOR_KEY.encode()).hexdigest()
        inactive_hash = hashlib.sha256(INACTIVE_KEY.encode()).hexdigest()

        session.add(
            ApiKey(organization="Test Org", key_hash=operator_hash, role="operator", is_active=True)
        )
        session.add(
            ApiKey(organization="Test Org", key_hash=auditor_hash, role="auditor", is_active=True)
        )
        session.add(
            ApiKey(
                organization="Test Org", key_hash=inactive_hash, role="operator", is_active=False
            )
        )
        await session.commit()

        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestGetCurrentRole:
    """Tests for get_current_role() dependency."""

    @pytest.mark.asyncio
    async def test_valid_operator_key_returns_operator_role(self, test_db: AsyncSession):
        """Verify valid operator key returns 'operator' role."""

        async def mock_get_db():
            yield test_db

        # Mock the dependency
        role = await get_current_role(api_key=OPERATOR_KEY, db=test_db)
        assert role == "operator"

    @pytest.mark.asyncio
    async def test_valid_auditor_key_returns_auditor_role(self, test_db: AsyncSession):
        """Verify valid auditor key returns 'auditor' role."""
        role = await get_current_role(api_key=AUDITOR_KEY, db=test_db)
        assert role == "auditor"

    @pytest.mark.asyncio
    async def test_invalid_key_raises_403(self, test_db: AsyncSession):
        """Verify invalid key raises HTTP 403."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_role(api_key=INVALID_KEY, db=test_db)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_inactive_key_raises_403(self, test_db: AsyncSession):
        """Verify inactive key raises HTTP 403."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_role(api_key=INACTIVE_KEY, db=test_db)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_missing_key_raises_403(self, test_db: AsyncSession):
        """Verify missing key raises HTTP 403."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_role(api_key="", db=test_db)
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequireRole:
    """Tests for require_role() dependency factory."""

    @pytest.mark.asyncio
    async def test_operator_can_access_operator_endpoint(self, test_db: AsyncSession):
        """Verify operator role passes operator-only check."""
        role_checker = require_role("operator")
        result = role_checker(role="operator")
        assert result == "operator"

    @pytest.mark.asyncio
    async def test_auditor_cannot_access_operator_endpoint(self, test_db: AsyncSession):
        """Verify auditor role blocked from operator-only endpoint."""
        role_checker = require_role("operator")
        with pytest.raises(HTTPException) as exc_info:
            role_checker(role="auditor")
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_auditor_can_access_auditor_endpoint(self, test_db: AsyncSession):
        """Verify auditor role passes auditor-only check."""
        role_checker = require_role("auditor")
        result = role_checker(role="auditor")
        assert result == "auditor"

    @pytest.mark.asyncio
    async def test_operator_cannot_access_auditor_endpoint(self, test_db: AsyncSession):
        """Verify operator role blocked from auditor-only endpoint."""
        role_checker = require_role("auditor")
        with pytest.raises(HTTPException) as exc_info:
            role_checker(role="operator")
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_multiple_roles_allowed(self, test_db: AsyncSession):
        """Verify role checker works with multiple allowed roles."""
        role_checker = require_role("operator", "auditor")
        assert role_checker(role="operator") == "operator"
        assert role_checker(role="auditor") == "auditor"

    @pytest.mark.asyncio
    async def test_invalid_role_raises_403(self, test_db: AsyncSession):
        """Verify invalid role raises HTTP 403."""
        role_checker = require_role("operator")
        with pytest.raises(HTTPException) as exc_info:
            role_checker(role="invalid-role")
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
