"""
auth.py — DB-Backed API Key Authentication & RBAC

Keys are hashed (SHA-256) before DB lookup. Constant-time comparison is
handled natively by checking the hash equality.
"""
import hashlib
from typing import Literal

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ApiKey

RoleType = Literal["operator", "auditor"]
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

async def get_current_role(
    api_key: str = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db)
) -> str:
    """
    FastAPI dependency — resolves the caller's role from DB.
    Uses SHA-256 hashing so plaintext keys are never queried or stored.
    """
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    
    result = await db.execute(
        select(ApiKey.role).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
    )
    role = result.scalar_one_or_none()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid, missing, or inactive API key.",
        )
    return role

def require_role(*allowed_roles: str):
    """
    FastAPI dependency factory — restricts an endpoint to specific roles.
    """
    def _check(role: str = Depends(get_current_role)) -> str:
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges. Requires: {list(allowed_roles)}",
            )
        return role
    return _check