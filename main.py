"""
main.py — Quantum Shield Core API
==================================
Stateless PQC cryptographic microservice (ML-KEM-768 + AES-GCM).
"""
import base64
import hashlib
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, ConfigDict, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import func as sql_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional

from audit_store import count_logs, get_log_by_id, get_logs, mark_integrity, store_log
from auth import require_role
from constants import (
    API_VERSION,
    MAX_CONTEXT_LENGTH,
    MAX_PAYLOAD_DECODED_BYTES,
    IntegrityDisplay,
)
from database import AsyncSessionLocal, check_db_connection, engine, get_db, init_db

# Enterprise license validation (stub for open-source)
def _validate_license_key() -> bool:
    """Check if a valid enterprise license key is configured."""
    license_key = os.environ.get("QSC_LICENSE_KEY", "")
    return license_key.startswith("QSC-ENT-") and len(license_key) >= 32
from models import ApiKey, AuditLog
from observability import (
    AUDIT_WRITES,
    CRYPTO_OPS,
    CorrelationIdMiddleware,
    configure_logging,
    logger,
    setup_opentelemetry,
)
from security_engine import LocalEnvKMS, SecurityEngine

load_dotenv()
configure_logging()

# ---------------------------------------------------------------------------
# Enterprise license check
# ---------------------------------------------------------------------------
ENTERPRISE_LICENSED: bool = _validate_license_key()

if ENTERPRISE_LICENSED:
    logger.info("enterprise_license_active", extra={"key_prefix": os.environ.get("QSC_LICENSE_KEY", "")[:8]})
else:
    logger.info("enterprise_license_inactive", extra={"detail": "Community edition (in-memory audit, no AWS/Vault KMS)"})


# ---------------------------------------------------------------------------
# KMS bootstrap (fail-secure)
# ---------------------------------------------------------------------------
def _bootstrap_kms_keys() -> dict[str, bytes]:
    keys: dict[str, bytes] = {}
    for k, v in os.environ.items():
        if k.startswith("AUDIT_KEY_"):
            version = k.split("AUDIT_KEY_", 1)[1].lower()
            if len(v) >= 32:
                keys[version] = v.encode()
    if not keys and "AUDIT_KEY" in os.environ:
        keys["v1"] = os.environ["AUDIT_KEY"].encode()
    if not keys:
        logger.critical("No AUDIT_KEY or AUDIT_KEY_vX found in environment.")
        sys.exit(1)
    return keys


def _create_kms_provider(keys: dict[str, bytes]):
    provider = os.environ.get("KMS_PROVIDER", "local").lower()
    if provider in ("aws", "vault", "azure"):
        if not ENTERPRISE_LICENSED:
            _ent_license.require_enterprise_license()  # raises HTTPException 402
        if provider == "aws":
            from enterprise.kms.aws_kms import AWSKMSProvider
            return AWSKMSProvider()
        if provider == "vault":
            from enterprise.kms.vault_kms import HashiCorpVaultKMSProvider
            return HashiCorpVaultKMSProvider()
        from enterprise.kms.azure_kms import AzureKeyVaultProvider
        return AzureKeyVaultProvider()
    return LocalEnvKMS(keys)


_keys_dict = _bootstrap_kms_keys()
_active_version = os.environ.get("ACTIVE_AUDIT_KEY_VERSION", "v1")
crypto_engine = SecurityEngine(
    _create_kms_provider(_keys_dict),
    active_key_version=_active_version,
)


async def _seed_api_key(db: AsyncSession, env_var: str, role: str, org: str) -> None:
    raw = os.environ.get(env_var)
    if not raw:
        return
    key_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    exists = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    if not exists.scalar_one_or_none():
        db.add(ApiKey(organization=org, key_hash=key_hash, role=role))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as db:
        await _seed_api_key(db, "API_KEY_OPERATOR", "operator", "System Operator")
        await _seed_api_key(db, "API_KEY_AUDITOR", "auditor", "System Auditor")
        await db.commit()
    logger.info("quantum_shield_started", extra={"version": API_VERSION, "enterprise": ENTERPRISE_LICENSED})
    yield
    logger.info("quantum_shield_shutdown", extra={"version": API_VERSION})
    await engine.dispose()


limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

OPENAPI_TAGS = [
    {
        "name": "System",
        "description": "Health, metrics, and operational endpoints.",
    },
    {
        "name": "Key Management",
        "description": "Post-quantum key pair generation (ML-KEM-768).",
    },
    {
        "name": "Cryptography",
        "description": "Hybrid seal/unseal operations (Kyber768 + AES-256-GCM).",
    },
    {
        "name": "Audit Trail",
        "description": "HMAC-signed, append-only audit log with integrity verification.",
    },
]

app = FastAPI(
    title="Quantum Shield Core API",
    description=(
        "Enterprise post-quantum cryptographic enclave.\n\n"
        "- **Algorithm**: ML-KEM-768 (Kyber768) + AES-256-GCM\n"
        "- **Audit**: HMAC-SHA256 signed logs with key rotation\n"
        "- **Auth**: API key (SHA-256 hashed) with RBAC\n\n"
        "Authenticate with header `X-API-Key`."
    ),
    version=API_VERSION,
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    docs_url="/docs" if os.environ.get("ENABLE_DOCS", "").lower() == "true" else None,
    redoc_url="/redoc" if os.environ.get("ENABLE_DOCS", "").lower() == "true" else None,
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", tags=["System"])
setup_opentelemetry(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CorrelationIdMiddleware)

_allowed_origins = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type", "X-Correlation-ID"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": _safe_errors(errors)},
    )


def _safe_errors(errors: list) -> list:
    """Ensure all error values are JSON-serializable."""
    result = []
    for err in errors:
        safe = {}
        for k, v in err.items():
            if isinstance(v, Exception):
                safe[k] = str(v)
            elif isinstance(v, dict):
                safe[k] = {sk: str(sv) if isinstance(sv, Exception) else sv for sk, sv in v.items()}
            else:
                safe[k] = v
        result.append(safe)
    return result


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = (
        "max-age=63072000; includeSubDomains; preload"
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if "server" in response.headers:
        del response.headers["server"]
    return response


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class KeyPairResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "public_key_b64": "abc123...",
            "private_key_b64": "def456...",
        }
    })
    public_key_b64: str = Field(..., description="Kyber768 public key (Base64).")
    private_key_b64: str = Field(..., description="Kyber768 secret key (Base64). Store securely.")


class SealRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "public_key_b64": "base64-public-key",
            "data_b64": "SGVsbG8=",
            "context": "contract-2025-001",
        }
    })
    public_key_b64: str = Field(..., description="Recipient Kyber768 public key.")
    data_b64: str = Field(..., description="Plaintext (Base64).")
    context: str = Field(..., min_length=1, max_length=MAX_CONTEXT_LENGTH)

    @field_validator("data_b64")
    @classmethod
    def check_payload_size(cls, v: str) -> str:
        approx_decoded = len(v) * 3 // 4
        if approx_decoded > MAX_PAYLOAD_DECODED_BYTES:
            raise ValueError(
                f"Payload exceeds {MAX_PAYLOAD_DECODED_BYTES // (1024 * 1024)}MB limit."
            )
        return v


class SealResponse(BaseModel):
    ciphertext_pqc_b64: str = Field(..., description="Kyber768 KEM ciphertext.")
    nonce_b64: str = Field(..., description="AES-GCM nonce (12 bytes).")
    encrypted_data_b64: str = Field(..., description="AES-256-GCM ciphertext + tag.")


class UnsealRequest(BaseModel):
    private_key_b64: str
    ciphertext_pqc_b64: str
    nonce_b64: str
    encrypted_data_b64: str
    context: str = Field(..., min_length=1, max_length=MAX_CONTEXT_LENGTH)


class UnsealResponse(BaseModel):
    decrypted_data_b64: str = Field(..., description="Recovered plaintext (Base64).")


class AuditRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"action": "EXPORT", "target": "report.pdf", "user": "alice"}
    })
    action: str = Field(..., min_length=1, max_length=64)
    target: str = Field(..., min_length=1, max_length=MAX_CONTEXT_LENGTH)
    user: str = Field(..., min_length=1, max_length=64)


class AuditLogEntryResponse(BaseModel):
    id: int
    action: str
    target: str
    actor: str
    log_json: str
    signature: str
    integrity: str


class HealthResponse(BaseModel):
    status: str
    algorithm: str
    version: str
    database: str


class ErrorResponse(BaseModel):
    detail: str


def _audit_entry_response(entry: AuditLog, is_valid: bool) -> AuditLogEntryResponse:
    return AuditLogEntryResponse(
        id=entry.id,
        action=entry.action,
        target=entry.target,
        actor=entry.actor,
        log_json=entry.log_json,
        signature=entry.signature,
        integrity=IntegrityDisplay.OK.value if is_valid else IntegrityDisplay.FAIL.value,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Liveness and database health",
)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_ok = await check_db_connection()
    total_logs = await count_logs(db) if db_ok else 0
    return {
        "status": "healthy" if db_ok else "degraded",
        "algorithm": crypto_engine.pqc_alg,
        "version": API_VERSION,
        "database": f"{'ok' if db_ok else 'unavailable'} ({total_logs} audit entries)",
    }


@app.post(
    "/api/v1/keys/generate",
    response_model=KeyPairResponse,
    status_code=201,
    tags=["Key Management"],
    summary="Generate ML-KEM-768 key pair",
    responses={403: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
@limiter.limit("10/minute")
async def generate_keys(
    request: Request,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_role("operator")),
):
    pub, priv = crypto_engine.generate_keypair()
    signed = crypto_engine.generate_signed_log("KEY_GENERATE", "keypair", role)
    await store_log(signed["log"], signed["signature"], db, key_version=signed["key_version"])
    CRYPTO_OPS.labels(operation="key_generate").inc()
    AUDIT_WRITES.inc()
    return {
        "public_key_b64": base64.b64encode(pub).decode(),
        "private_key_b64": base64.b64encode(priv).decode(),
    }


@app.post(
    "/api/v1/crypto/seal",
    response_model=SealResponse,
    tags=["Cryptography"],
    summary="Hybrid encrypt (seal)",
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
@limiter.limit("30/minute")
async def seal_data(
    request: Request,
    req: SealRequest,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_role("operator")),
):
    try:
        pub_key = base64.b64decode(req.public_key_b64, validate=True)
        raw_data = base64.b64decode(req.data_b64, validate=True)
        result = crypto_engine.encrypt_hybrid(pub_key, raw_data, req.context.encode())
        signed = crypto_engine.generate_signed_log("SEAL", req.context, role)
        await store_log(signed["log"], signed["signature"], db, key_version=signed["key_version"])
        CRYPTO_OPS.labels(operation="seal").inc()
        AUDIT_WRITES.inc()
        return {
            "ciphertext_pqc_b64": base64.b64encode(result["ciphertext_pqc"]).decode(),
            "nonce_b64": base64.b64encode(result["nonce"]).decode(),
            "encrypted_data_b64": base64.b64encode(result["encrypted_data"]).decode(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("seal_failed")
        raise HTTPException(status_code=500, detail="Seal operation failed.") from exc


@app.post(
    "/api/v1/crypto/unseal",
    response_model=UnsealResponse,
    tags=["Cryptography"],
    summary="Hybrid decrypt (unseal)",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
@limiter.limit("30/minute")
async def unseal_data(
    request: Request,
    req: UnsealRequest,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_role("operator")),
):
    try:
        priv_key = base64.b64decode(req.private_key_b64, validate=True)
        cpqc = base64.b64decode(req.ciphertext_pqc_b64, validate=True)
        nonce = base64.b64decode(req.nonce_b64, validate=True)
        enc_data = base64.b64decode(req.encrypted_data_b64, validate=True)
        plaintext = crypto_engine.decrypt_hybrid(
            priv_key, cpqc, nonce, enc_data, req.context.encode()
        )
        signed = crypto_engine.generate_signed_log("UNSEAL", req.context, role)
        await store_log(signed["log"], signed["signature"], db, key_version=signed["key_version"])
        CRYPTO_OPS.labels(operation="unseal").inc()
        AUDIT_WRITES.inc()
        return {"decrypted_data_b64": base64.b64encode(plaintext).decode()}
    except Exception as exc:
        logger.warning("unseal_failed", exc_info=False)
        raise HTTPException(
            status_code=401,
            detail="Unseal failed: invalid key, context mismatch, or tampered payload.",
        ) from exc


@app.post(
    "/api/v1/audit/log",
    status_code=201,
    tags=["Audit Trail"],
    summary="Append signed audit entry",
    responses={403: {"model": ErrorResponse}},
)
@limiter.limit("60/minute")
async def write_audit_log(
    request: Request,
    req: AuditRequest,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_role("operator", "auditor")),
):
    result = crypto_engine.generate_signed_log(req.action, req.target, req.user)
    entry = await store_log(
        result["log"],
        result["signature"],
        db,
        key_version=result["key_version"],
    )
    AUDIT_WRITES.inc()
    return {"id": entry.id, "log": result["log"], "signature": result["signature"]}


@app.get(
    "/api/v1/audit/logs",
    response_model=list[AuditLogEntryResponse],
    tags=["Audit Trail"],
    summary="List audit logs (newest first)",
)
@limiter.limit("20/minute")
async def read_audit_logs(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    action: Optional[str] = None,
    actor: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_role("operator", "auditor")),
):
    entries = await get_logs(
        db, skip=skip, limit=min(limit, 500), action_filter=action, actor_filter=actor
    )
    result = []
    for entry in entries:
        is_valid = crypto_engine.verify_log(entry.log_json, entry.signature)
        await mark_integrity(entry, is_valid, db)
        result.append(_audit_entry_response(entry, is_valid))
    return result


@app.get(
    "/api/v1/audit/logs/{log_id}",
    response_model=AuditLogEntryResponse,
    tags=["Audit Trail"],
    summary="Get audit log by ID",
    responses={404: {"model": ErrorResponse}},
)
@limiter.limit("60/minute")
async def read_audit_log(
    request: Request,
    log_id: int,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_role("operator", "auditor")),
):
    entry = await get_log_by_id(log_id, db)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Log entry {log_id} not found.")
    is_valid = crypto_engine.verify_log(entry.log_json, entry.signature)
    await mark_integrity(entry, is_valid, db)
    return _audit_entry_response(entry, is_valid)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def product_landing():
    """Product landing page for technical evaluation and OEM positioning."""
    path = os.path.join(os.path.dirname(__file__), "landing", "index.html")
    with open(path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get(
    "/api/v1/audit/stats",
    tags=["Audit Trail"],
    summary="Audit log statistics",
)
@limiter.limit("30/minute")
async def get_audit_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(require_role("operator", "auditor")),
):
    total = await count_logs(db)
    result = await db.execute(
        select(AuditLog.action, sql_func.count(AuditLog.id).label("count")).group_by(
            AuditLog.action
        )
    )
    by_action = {row.action: row.count for row in result}
    return {"total": total, "by_action": by_action}


_landing_dir = os.path.join(os.path.dirname(__file__), "landing")
if os.path.isdir(_landing_dir):
    app.mount("/landing", StaticFiles(directory=_landing_dir), name="landing")