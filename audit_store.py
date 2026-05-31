"""
audit_store.py — Append-only persistence for the signed audit trail.

Writes are append-only via store_log(). Integrity is verified at read time
using SecurityEngine.verify_log() — the stored integrity column is a cache only.
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
    """SHA-256 over canonical payload — foundation for future hash-chain audits."""
    chain_input = f"{prev_hash or 'GENESIS'}|{log_json}|{signature}"
    return hashlib.sha256(chain_input.encode("utf-8")).hexdigest()


async def _next_sequence_number(db: AsyncSession) -> int:
    result = await db.execute(select(func.max(AuditLog.sequence_number)))
    current = result.scalar_one_or_none()
    return (current or 0) + 1


async def _latest_entry_hash(db: AsyncSession) -> str | None:
    result = await db.execute(
        select(AuditLog.entry_hash)
        .order_by(AuditLog.sequence_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Write (append-only)
# ---------------------------------------------------------------------------
async def store_log(
    log_data: dict[str, Any],
    signature: str,
    db: AsyncSession,
    *,
    key_version: str | None = None,
) -> AuditLog:
    """
    Persist a signed audit log entry (append-only).

    Parameters
    ----------
    log_data    : dict from SecurityEngine.generate_signed_log()["log"]
    signature   : HMAC-SHA256 hex digest
    key_version : optional override (defaults to log_data["key_version"])
    """
    log_json = json.dumps(log_data, sort_keys=True)
    seq = await _next_sequence_number(db)
    prev_hash = await _latest_entry_hash(db)
    entry_hash = _compute_entry_hash(log_json, signature, prev_hash)
    kv = key_version or log_data.get("key_version", "v1")

    entry = AuditLog(
        sequence_number=seq,
        action=log_data["action"],
        target=log_data["target"],
        actor=log_data["user"],
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


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------
async def get_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    action_filter: str | None = None,
    actor_filter: str | None = None,
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.id.desc())

    if action_filter:
        stmt = stmt.where(AuditLog.action == action_filter)
    if actor_filter:
        stmt = stmt.where(AuditLog.actor == actor_filter)

    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_log_by_id(log_id: int, db: AsyncSession) -> AuditLog | None:
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    return result.scalar_one_or_none()


async def count_logs(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(AuditLog))
    return result.scalar_one()


async def mark_integrity(
    entry: AuditLog,
    is_valid: bool,
    db: AsyncSession,
) -> None:
    """Cache integrity verification result (append-only: only integrity field updates)."""
    entry.integrity = (
        IntegrityStatus.OK.value if is_valid else IntegrityStatus.FAIL.value
    )
    db.add(entry)
    await db.flush()
