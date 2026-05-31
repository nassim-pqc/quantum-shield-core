"""
constants.py — Shared application constants and enumerations.
"""
from enum import Enum


class _StrEnum(str, Enum):
    pass


class ApiRole(_StrEnum):
    OPERATOR = "operator"
    AUDITOR = "auditor"


class AuditAction(_StrEnum):
    KEY_GENERATE = "KEY_GENERATE"
    SEAL = "SEAL"
    UNSEAL = "UNSEAL"


class IntegrityStatus(_StrEnum):
    PENDING = "PENDING"
    OK = "OK"
    FAIL = "FAIL"


class IntegrityDisplay(_StrEnum):
    OK = "OK"
    FAIL = "FAIL"


# HTTP / API
API_VERSION: str = "1.0.0"
MAX_PAYLOAD_DECODED_BYTES: int = 20 * 1024 * 1024
MAX_CONTEXT_LENGTH: int = 256
MIN_AUDIT_KEY_BYTES: int = 32

# Headers
CORRELATION_ID_HEADER: str = "X-Correlation-ID"
API_KEY_HEADER_NAME: str = "X-API-Key"

# Crypto
PQC_ALGORITHM: str = "Kyber768"
AES_GCM_NONCE_BYTES: int = 12

# Database pool (PostgreSQL)
DB_POOL_SIZE: int = 10
DB_MAX_OVERFLOW: int = 20
DB_POOL_TIMEOUT_SECONDS: int = 30
