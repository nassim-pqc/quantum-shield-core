"""
audit_store.py — In-memory audit store (open-source version).

This is a lightweight fallback for the open-source community edition.
For production-grade PostgreSQL audit storage, use enterprise/audit/.
"""
from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from typing import Any, Optional

from constants import IntegrityStatus


@dataclass
class AuditLogEntry:
    """Lightweight audit log entry (in-memory, no ORM)."""
    id: int = 0
    sequence_number: int = 0
    created_at: str = ""
    action: str = ""
    target: str = ""
    actor: str = ""
    key_version: str = "v1"
    log_json: str = ""
    signature: str = ""
    integrity: str = IntegrityStatus.PENDING.value
    prev_entry_hash: Optional[str] = None
    entry_hash: Optional[str] = None


def _compute_entry_hash(log_json: str, signature: str, prev_hash: str | None) -> str:
    chain_input = f"{prev_hash or 'GENESIS'}|{log_json}|{signature}"
    return hashlib.sha256(chain_input.encode("utf-8")).hexdigest()


class _InMemoryStore:
    """Thread-safe in-memory audit log store."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: list[AuditLogEntry] = []
        self._next_id: int = 1
        self._next_seq: int = 1

    def store_log(
        self,
        log_data: dict[str, Any],
        signature: str,
        key_version: str | None = None,
    ) -> AuditLogEntry:
        log_json = json.dumps(log_data, sort_keys=True)
        with self._lock:
            prev_hash = self._entries[-1].entry_hash if self._entries else None
            entry_hash = _compute_entry_hash(log_json, signature, prev_hash)
            kv = key_version or log_data.get("key_version", "v1")

            entry = AuditLogEntry(
                id=self._next_id,
                sequence_number=self._next_seq,
                created_at=log_data.get("timestamp", ""),
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
            self._entries.append(entry)
            self._next_id += 1
            self._next_seq += 1
            return entry

    def get_logs(
        self,
        skip: int = 0,
        limit: int = 100,
        action_filter: str | None = None,
        actor_filter: str | None = None,
    ) -> list[AuditLogEntry]:
        with self._lock:
            result = list(self._entries)
        if action_filter:
            result = [e for e in result if e.action == action_filter]
        if actor_filter:
            result = [e for e in result if e.actor == actor_filter]
        result.reverse()
        return result[skip: skip + limit]

    def get_log_by_id(self, log_id: int) -> AuditLogEntry | None:
        with self._lock:
            for e in self._entries:
                if e.id == log_id:
                    return e
        return None

    def count_logs(self) -> int:
        with self._lock:
            return len(self._entries)

    def mark_integrity(self, entry: AuditLogEntry, is_valid: bool) -> None:
        with self._lock:
            entry.integrity = (
                IntegrityStatus.OK.value if is_valid else IntegrityStatus.FAIL.value
            )


_store = _InMemoryStore()


async def store_log(
    log_data: dict[str, Any],
    signature: str,
    db: Any = None,
    *,
    key_version: str | None = None,
) -> AuditLogEntry:
    return _store.store_log(log_data, signature, key_version=key_version)


async def get_logs(
    db: Any = None,
    skip: int = 0,
    limit: int = 100,
    action_filter: str | None = None,
    actor_filter: str | None = None,
) -> list[AuditLogEntry]:
    return _store.get_logs(skip, limit, action_filter, actor_filter)


async def get_log_by_id(log_id: int, db: Any = None) -> AuditLogEntry | None:
    return _store.get_log_by_id(log_id)


async def count_logs(db: Any = None) -> int:
    return _store.count_logs()


async def mark_integrity(entry: AuditLogEntry, is_valid: bool, db: Any = None) -> None:
    _store.mark_integrity(entry, is_valid)