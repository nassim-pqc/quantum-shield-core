"""
test_audit_store.py — Tests unitaires du module de persistance d'audit.
"""

import json
import os

os.environ.setdefault("AUDIT_KEY", "test-audit-key-minimum-32-bytes-ok!")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from audit_store import count_logs, get_log_by_id, get_logs, mark_integrity, store_log
from constants import IntegrityStatus
from database import Base
from models import AuditLog


@pytest_asyncio.fixture
async def test_db():
    """Create an isolated in-memory database for each test."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def _sample_log(action="SEAL", target="doc.pdf", user="operator", version="v1"):
    """Create a sample log dict for testing."""
    return {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "action": action,
        "target": target,
        "user": user,
        "key_version": version,
    }


class TestStoreLog:
    """Tests for store_log() function."""

    @pytest.mark.asyncio
    async def test_store_returns_audit_log_with_id(self, test_db: AsyncSession):
        """Verify store_log returns an AuditLog object with an ID."""
        entry = await store_log(_sample_log(), "sig_abc123", test_db)
        await test_db.commit()
        assert entry.id is not None
        assert entry.id > 0

    @pytest.mark.asyncio
    async def test_store_sets_correct_action(self, test_db: AsyncSession):
        """Verify action is correctly stored."""
        entry = await store_log(_sample_log(action="UNSEAL"), "sig", test_db)
        await test_db.commit()
        assert entry.action == "UNSEAL"

    @pytest.mark.asyncio
    async def test_store_increments_sequence_number(self, test_db: AsyncSession):
        """Verify sequence numbers increment."""
        e1 = await store_log(_sample_log(), "sig1", test_db)
        e2 = await store_log(_sample_log(), "sig2", test_db)
        await test_db.commit()
        assert e2.sequence_number > e1.sequence_number

    @pytest.mark.asyncio
    async def test_store_computes_entry_hash(self, test_db: AsyncSession):
        """Verify entry_hash is computed (SHA-256 hex)."""
        entry = await store_log(_sample_log(), "sig_xyz", test_db)
        await test_db.commit()
        assert entry.entry_hash is not None
        assert len(entry.entry_hash) == 64  # SHA-256 hex

    @pytest.mark.asyncio
    async def test_store_first_entry_has_no_prev_hash(self, test_db: AsyncSession):
        """Verify first entry has no previous hash."""
        entry = await store_log(_sample_log(), "sig", test_db)
        await test_db.commit()
        assert entry.prev_entry_hash is None

    @pytest.mark.asyncio
    async def test_store_second_entry_links_to_first(self, test_db: AsyncSession):
        """Verify hash chain linkage."""
        e1 = await store_log(_sample_log(), "sig1", test_db)
        await test_db.flush()
        e2 = await store_log(_sample_log(), "sig2", test_db)
        await test_db.commit()
        assert e2.prev_entry_hash == e1.entry_hash

    @pytest.mark.asyncio
    async def test_store_key_version_override(self, test_db: AsyncSession):
        """Verify key_version parameter overrides log_data value."""
        entry = await store_log(_sample_log(version="v1"), "sig", test_db, key_version="v2")
        await test_db.commit()
        assert entry.key_version == "v2"

    @pytest.mark.asyncio
    async def test_store_sets_integrity_pending(self, test_db: AsyncSession):
        """Verify integrity is initially PENDING."""
        entry = await store_log(_sample_log(), "sig", test_db)
        await test_db.commit()
        assert entry.integrity == IntegrityStatus.PENDING.value


class TestGetLogs:
    """Tests for get_logs() function."""

    @pytest.mark.asyncio
    async def test_get_logs_returns_list(self, test_db: AsyncSession):
        """Verify get_logs returns a list."""
        logs = await get_logs(test_db)
        assert isinstance(logs, list)

    @pytest.mark.asyncio
    async def test_get_logs_returns_inserted_entries(self, test_db: AsyncSession):
        """Verify inserted entries are returned."""
        await store_log(_sample_log(action="KEY_GENERATE"), "sig", test_db)
        await test_db.commit()
        logs = await get_logs(test_db)
        assert len(logs) >= 1

    @pytest.mark.asyncio
    async def test_get_logs_filter_by_action(self, test_db: AsyncSession):
        """Verify action_filter parameter works."""
        await store_log(_sample_log(action="SEAL"), "sig1", test_db)
        await store_log(_sample_log(action="UNSEAL"), "sig2", test_db)
        await test_db.commit()
        logs = await get_logs(test_db, action_filter="SEAL")
        assert all(l.action == "SEAL" for l in logs)
        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_get_logs_filter_by_actor(self, test_db: AsyncSession):
        """Verify actor_filter parameter works."""
        await store_log(_sample_log(user="alice"), "sig1", test_db)
        await store_log(_sample_log(user="bob"), "sig2", test_db)
        await test_db.commit()
        logs = await get_logs(test_db, actor_filter="alice")
        assert all(l.actor == "alice" for l in logs)
        assert len(logs) == 1

    @pytest.mark.asyncio
    async def test_get_logs_respects_limit(self, test_db: AsyncSession):
        """Verify limit parameter restricts results."""
        for i in range(5):
            await store_log(_sample_log(target=f"doc{i}.pdf"), f"sig{i}", test_db)
        await test_db.commit()
        logs = await get_logs(test_db, limit=3)
        assert len(logs) == 3

    @pytest.mark.asyncio
    async def test_get_logs_respects_skip(self, test_db: AsyncSession):
        """Verify skip parameter offsets results."""
        for i in range(5):
            await store_log(_sample_log(target=f"doc{i}.pdf"), f"sig{i}", test_db)
        await test_db.commit()
        logs_skip_2 = await get_logs(test_db, skip=2, limit=10)
        assert len(logs_skip_2) == 3

    @pytest.mark.asyncio
    async def test_get_logs_ordered_by_id_desc(self, test_db: AsyncSession):
        """Verify logs are ordered by ID descending (newest first)."""
        e1 = await store_log(_sample_log(target="doc1"), "sig1", test_db)
        e2 = await store_log(_sample_log(target="doc2"), "sig2", test_db)
        e3 = await store_log(_sample_log(target="doc3"), "sig3", test_db)
        await test_db.commit()
        logs = await get_logs(test_db)
        assert logs[0].id == e3.id  # newest first
        assert logs[-1].id == e1.id  # oldest last


class TestGetLogById:
    """Tests for get_log_by_id() function."""

    @pytest.mark.asyncio
    async def test_get_log_by_id_returns_entry(self, test_db: AsyncSession):
        """Verify get_log_by_id returns the correct entry."""
        entry = await store_log(_sample_log(), "sig", test_db)
        await test_db.commit()
        retrieved = await get_log_by_id(entry.id, test_db)
        assert retrieved is not None
        assert retrieved.id == entry.id

    @pytest.mark.asyncio
    async def test_get_log_by_id_returns_none_for_missing(self, test_db: AsyncSession):
        """Verify get_log_by_id returns None for non-existent ID."""
        retrieved = await get_log_by_id(999, test_db)
        assert retrieved is None


class TestCountLogs:
    """Tests for count_logs() function."""

    @pytest.mark.asyncio
    async def test_count_logs_returns_zero_for_empty(self, test_db: AsyncSession):
        """Verify count_logs returns 0 for empty database."""
        count = await count_logs(test_db)
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_logs_returns_correct_count(self, test_db: AsyncSession):
        """Verify count_logs returns the correct count."""
        for i in range(5):
            await store_log(_sample_log(target=f"doc{i}"), f"sig{i}", test_db)
        await test_db.commit()
        count = await count_logs(test_db)
        assert count == 5


class TestMarkIntegrity:
    """Tests for mark_integrity() function."""

    @pytest.mark.asyncio
    async def test_mark_integrity_ok(self, test_db: AsyncSession):
        """Verify mark_integrity sets OK status."""
        entry = await store_log(_sample_log(), "sig", test_db)
        await test_db.commit()
        await mark_integrity(entry, True, test_db)
        await test_db.commit()
        assert entry.integrity == IntegrityStatus.OK.value

    @pytest.mark.asyncio
    async def test_mark_integrity_fail(self, test_db: AsyncSession):
        """Verify mark_integrity sets FAIL status."""
        entry = await store_log(_sample_log(), "sig", test_db)
        await test_db.commit()
        await mark_integrity(entry, False, test_db)
        await test_db.commit()
        assert entry.integrity == IntegrityStatus.FAIL.value
