"""
tests/conftest.py — Shared pytest fixtures for Quantum Shield.
"""

import hashlib
import os
import tempfile

os.environ.setdefault("AUDIT_KEY", "test-audit-key-secure-enough-for-pytest-32chars!")
os.environ.setdefault("QSC_LICENSE_KEY", "QSC-ENT-TEST-FAKE-12345678-87654321")
os.environ.setdefault("API_KEY_OPERATOR", "test-operator-api-key-secure-enough-32chars!!")
os.environ.setdefault("API_KEY_AUDITOR", "test-auditor-api-key-secure-enough-32chars!!!")

_TEST_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TEST_DB.close()
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{_TEST_DB.name}")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import audit_store
from database import Base, get_db
from main import app, crypto_engine
from models import ApiKey

OPERATOR_KEY = os.environ["API_KEY_OPERATOR"]
AUDITOR_KEY = os.environ["API_KEY_AUDITOR"]
OPERATOR_HEADERS = {"X-API-Key": OPERATOR_KEY}
AUDITOR_HEADERS = {"X-API-Key": AUDITOR_KEY}
INVALID_HEADERS = {"X-API-Key": "this-key-does-not-exist-and-is-invalid"}
TEST_CONTEXT = "test-aad-context-document-42"
TEST_MESSAGE = b"Message ultra-confidentiel pour les tests Quantum Shield."


@pytest.fixture(autouse=True)
def reset_audit_store():
    """Reset the in-memory audit store before each test."""
    audit_store._store = audit_store._InMemoryStore()
    yield


@pytest_asyncio.fixture
async def db_session():
    from database import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        for raw_key, role in (
            (OPERATOR_KEY, "operator"),
            (AUDITOR_KEY, "auditor"),
        ):
            key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
            session.add(ApiKey(organization="Test Org", key_hash=key_hash, role=role))
        await session.commit()
        try:
            yield session
        finally:
            await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session

    # Disable rate limiting for tests
    app.state.limiter.enabled = False

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def keypair(client: AsyncClient) -> dict:
    response = await client.post("/api/v1/keys/generate", headers=OPERATOR_HEADERS)
    assert response.status_code == 201, response.text
    return response.json()


@pytest_asyncio.fixture
async def sealed_payload(client: AsyncClient, keypair: dict) -> dict:
    import base64

    response = await client.post(
        "/api/v1/crypto/seal",
        headers=OPERATOR_HEADERS,
        json={
            "public_key_b64": keypair["public_key_b64"],
            "data_b64": base64.b64encode(TEST_MESSAGE).decode(),
            "context": TEST_CONTEXT,
        },
    )
    assert response.status_code == 200, response.text
    return {"sealed": response.json(), "keypair": keypair}
