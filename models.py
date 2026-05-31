"""
models.py — SQLAlchemy ORM models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from constants import IntegrityStatus
from database import Base


class ApiKey(Base):
    """Multi-tenant API keys stored as SHA-256 hashes."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization: Mapped[str] = mapped_column(String(128), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuditLog(Base):
    """
    Append-only signed audit trail entry.

    ``prev_entry_hash`` + ``entry_hash`` prepare future hash-chain verification.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sequence_number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(256), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    key_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")
    log_json: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(String(64), nullable=False)
    integrity: Mapped[str] = mapped_column(
        String(8), default=IntegrityStatus.PENDING.value, nullable=False
    )
    prev_entry_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entry_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
