"""
audit_store.py — Persistent audit store (SQLAlchemy-backed).

Audit log entries are persisted to the relational database via the
``AuditLog`` ORM model:

  - SQLite (``sqlite+aiosqlite://``) for local development and the test suite;
  - PostgreSQL (``postgresql+asyncpg://``) for container / Kubernetes
    deployments (see ``docker-compose.yml`` and the Helm chart).

Each entry carries:
  - the signed log JSON exactly as produced by ``SecurityEngine`` and the
    matching HMAC-SHA256 ``signature`` (used to recompute integrity on read);
  - a SHA-256 hash-chain link (``prev_entry_hash`` → ``entry_hash``) that
    prepares whole-chain tamper-evidence verification.

What is **never** stored: plaintext, key material, private keys, shared
secrets, or API keys. Only action / target / actor metadata, the signed log
JSON, and the HMAC signature are written.

Persistence notes / limitations (pre-production):
  - ``sequence_number`` and ``prev_entry_hash`` are derived from the current
    tail of the chain read inside the caller's session. Under highly concurrent
    writers this last-row lookup is subject to a race; the ``sequence_number``
    UNIQUE constraint rejects a genuine collision rather than silently
    corrupting the chain, but this path has NOT been validated under
    production concurrency. A single-writer or serialized-append deployment
    avoids the race entirely.
  - This module does not itself manage transactions: the caller's session
    owns commit/rollback (the FastAPI ``get_db`` dependency commits at the end
    of each request; the test suite commits explicitly).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from constants import IntegrityStatus
from models import AuditLog


def _compute_entry_hash(log_json: str, signature: str, prev_hash: str | None) -> str:
    """Chain a new entry to its predecessor (or GENESIS for the first entry)."""
    chain_input = f"{prev_hash or 'GENESIS'}|{log_json}|{signature}"
    return hashlib.sha256(chain_input.encode("utf-8")).hexdigest()


async def _tail(db: AsyncSession) -> AuditLog | None:
    """Return the most recently appended entry (highest sequence), or None."""
    result = await db.execute(select(AuditLog).order_by(AuditLog.sequence_number.desc()).limit(1))
    return result.scalar_one_or_none()


async def store_log(
    log_data: dict[str, Any],
    signature: str,
    db: AsyncSession,
    *,
    key_version: str | None = None,
) -> AuditLog:
    """Persist a signed audit log entry and return the ORM row.

    The log JSON is serialized with ``sort_keys=True`` so the stored bytes are
    byte-identical to what ``SecurityEngine`` signed — integrity verification on
    read then recomputes the same HMAC and matches.

    The entry is added and flushed so the autoincrement ``id`` is populated
    before returning; the caller's session controls the final commit.
    """
    log_json = json.dumps(log_data, sort_keys=True)

    tail = await _tail(db)
    prev_hash = tail.entry_hash if tail else None
    next_seq = (tail.sequence_number + 1) if tail else 1
    entry_hash = _compute_entry_hash(log_json, signature, prev_hash)
    kv = key_version or log_data.get("key_version", "v1")

    entry = AuditLog(
        sequence_number=next_seq,
        action=log_data.get("action", ""),
        target=log_data.get("target", ""),
        actor=log_data.get("user", ""),
        key_version=kv,
        log_json=log_json,
        signature=signature,
        integrity=IntegrityStatus.PENDING.value,
        prev_entry_hash=prev_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    action_filter: str | None = None,
    actor_filter: str | None = None,
) -> list[AuditLog]:
    """Return audit entries newest-first, with optional filters + pagination."""
    stmt = select(AuditLog)
    if action_filter:
        stmt = stmt.where(AuditLog.action == action_filter)
    if actor_filter:
        stmt = stmt.where(AuditLog.actor == actor_filter)
    stmt = stmt.order_by(AuditLog.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_log_by_id(log_id: int, db: AsyncSession) -> AuditLog | None:
    """Return a single audit entry by primary key, or None if absent."""
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    return result.scalar_one_or_none()


async def count_logs(db: AsyncSession) -> int:
    """Return the total number of audit entries."""
    result = await db.execute(select(func.count()).select_from(AuditLog))
    return int(result.scalar_one())


async def mark_integrity(entry: AuditLog, is_valid: bool, db: AsyncSession) -> None:
    """Record the verified integrity status on an entry.

    The entry is already attached to ``db`` (fetched or inserted via this
    module), so updating the attribute marks it dirty; the caller's session
    persists it on commit.
    """
    entry.integrity = IntegrityStatus.OK.value if is_valid else IntegrityStatus.FAIL.value
    db.add(entry)
