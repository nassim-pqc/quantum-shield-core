# FULL SECURITY AUDIT — Quantum Shield Core
**Date:** 2026-03-06  
**Auditor:** Automated source code analysis  
**Scope:** All source files, dependencies, infrastructure configuration

---

## 1. CRYPTOGRAPHIC SECURITY

### 1.1 Algorithm Selection

| Algorithm | Standard | Key Size | Security Level | Implementation |
|---|---|---|---|---|
| ML-KEM-768 (Kyber768) | NIST FIPS 203 (draft) | 1184 bytes pub / 2400 bytes priv | AES-192 equivalent | `liboqs` C library via `oqs` Python wrapper |
| AES-256-GCM | NIST FIPS 197 | 256-bit key | 128-bit | `cryptography.hazmat.primitives.ciphers.aead.AESGCM` |
| HMAC-SHA256 | NIST FIPS 198-1 | 32+ bytes key | 128-bit | `hmac` standard library + Rust `hmac` crate |
| SHA-256 (KDF) | NIST FIPS 180-4 | 256-bit output | 128-bit | `hashlib` / `sha2` crate |

**Verdict:** ✅ All algorithms are NIST-standard or NIST-standardizing (Kyber). Appropriate key sizes for "strong crypto" (AES-256, SHA-256).

### 1.2 Key Derivation Security

The shared secret from Kyber768 KEM is NOT used directly as AES key:
```python
aes_key = hashlib.sha256(shared_secret).digest()
```
This is a simple SHA-256 hash, NOT a proper KDF (no HKDF, no PBKDF2, no argon2).

**Risk:** Low — SHA-256 is sufficient for a uniform random shared secret. However, HKDF-SHA256 would be more aligned with NIST SP 800-56C.

### 1.3 AES-GCM Nonce Generation
```python
nonce = os.urandom(AES_GCM_NONCE_BYTES)  # 12 bytes
```
**Verdict:** ✅ `os.urandom()` is cryptographically secure. 12-byte nonce is standard for AES-GCM.

**Risk:** No nonce reuse detection. If two calls use the same key + nonce, AES-GCM security breaks completely. Mitigated by unique Kyber768 shared secret per operation.

### 1.4 Hybrid Encryption Flow
```
plaintext → Kyber768 encapsulate → shared_secret → SHA-256 → AES-256-GCM key
                                                               ↓
public_key + ciphertext_pqc + (nonce + encrypted_data + tag)
```
**Verdict:** ✅ Standard KEM + DEM hybrid encryption construction.

### 1.5 AAD (Additional Authenticated Data)
```python
encrypted_data = AESGCM(aes_key).encrypt(nonce, plaintext, context)  # context = AAD
```
The context parameter is bound to the ciphertext. Unseal with wrong context → authentication failure.

**Tested:** ✅ `test_wrong_context_raises` in `test_security_engine.py` confirms AAD enforcement.

---

## 2. AUDIT TRAIL SECURITY

### 2.1 HMAC-Signed Logs

Each audit log entry contains:
```json
{
  "action": "SEAL",
  "key_version": "v1",
  "target": "doc-42",
  "timestamp": "2026-03-06T...",
  "user": "operator"
}
```
Signed with: `HMAC-SHA256(audit_key_vX, json_bytes)` → 64-character hex signature.

**Verdict:** ✅ Tamper-evident. Any modification to log content invalidates the signature.

### 2.2 Key Rotation Support

- Version identifier (`key_version`) in every log entry
- Multiple audit keys via `AUDIT_KEY_vX` environment variables
- `verify_log()` checks `key_version` from log data and fetches the correct key
- `get_audit_key()` with caching (5 min TTL) for all KMS providers

**Verdict:** ✅ Key rotation is supported at the data model level.

**BUT:** No automatic rotation mechanism exists. Rotation is a manual process (set env var + restart).

### 2.3 Hash Chain (Partial)

The model `AuditLog` includes:
```python
prev_entry_hash: str | None  # hash of previous entry
entry_hash: str | None       # SHA-256(prev_hash | log_json | signature)
```

**Implemented in:** `audit_store.py` (in-memory) ✅  
**NOT implemented in:** Database/enterprise tier ❌

**Verdict:** ⚠️ Hash chain is documented and partially implemented but not active in production database.

---

## 3. AUTHENTICATION SECURITY

### 3.1 API Key Storage

```python
key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
```
- Keys are **SHA-256 hashed** before storage
- Plaintext keys are **never stored in the database**
- SHA-256 without salt is acceptable for API keys (high-entropy secrets)
- Constant-time comparison is implicit (hash equality is fixed-length)

**Verdict:** ✅ Standard API key security practice.

### 3.2 RBAC Enforcement

Two roles: `operator` (crypto operations) and `auditor` (read-only audit).
Enforced via `require_role("operator")` FastAPI dependency.

**Tested:** ✅ `test_auditor_cannot_generate_keys`, `test_auditor_cannot_seal`, etc.

### 3.3 Rate Limiting

| Limit | Applies To |
|---|---|
| 200/min | Global (default) |
| 10/min | `/api/v1/keys/generate` |
| 30/min | `/api/v1/crypto/seal`, `/api/v1/crypto/unseal` |
| 60/min | `/api/v1/audit/log` |
| 20/min | `/api/v1/audit/logs` |

**Verdict:** ✅ Rate limiting uses SlowAPI with consistent configuration.

---

## 4. TRANSPORT SECURITY

### 4.1 HTTP Security Headers (main.py lines 238-250)

| Header | Value | Grade |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | ✅ |
| `X-Frame-Options` | `DENY` | ✅ |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` | ✅ (2 years) |
| `Cache-Control` | `no-store, no-cache, must-revalidate` | ✅ |
| `Pragma` | `no-cache` | ✅ |
| `Referrer-Policy` | `no-referrer` | ✅ |
| `Content-Security-Policy` | `default-src 'none'` | ✅ (strict) |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | ✅ |
| `Server` header | **Removed** | ✅ (line 249) |

**Verdict:** ✅ Excellent security header configuration. All 9 headers present and correctly configured.

### 4.2 CORS Configuration

```python
allow_origins = _allowed_origins or ["*"]
allow_credentials = False
allow_methods = ["GET", "POST"]
allow_headers = ["X-API-Key", "Content-Type", "X-Correlation-ID"]
```

**Note:** Default is `["*"]` (wide open). CORS credentials are disabled. This is appropriate for an API that uses API key auth (not cookies).

### 4.3 TLS

TLS is NOT handled by the application — it's delegated to the reverse proxy (nginx, Traefik, or cloud LB).

**Verdict:** ✅ Standard practice for FastAPI microservices.

---

## 5. INPUT VALIDATION

### 5.1 Validated Fields

| Field | Validation |
|---|---|
| `data_b64` | Size limit: 20 MB decoded |
| `context` | Length: 1-256 characters (min 1, max 256) |
| `public_key_b64` | Base64 with validation (validate=True) |
| `private_key_b64` | Base64 with validation (validate=True) |
| `action` | Length: 1-64 characters |
| `target` | Length: 1-256 characters |
| `user` | Length: 1-64 characters |

### 5.2 Error Messages

Unseal errors use opaque messages:
```python
detail="Unseal failed: invalid key, context mismatch, or tampered payload."
```
**Tested:** ✅ `test_error_message_is_opaque` — no `InvalidTag`, `Traceback`, or `Exception` leaked.

### 5.3 Audit Log Action Enumeration

**Finding:** `action` field is a free-text string (1-64 chars), NOT an enum. This means:
- "KEY_GENERATE" ✅ and "key_generate" ✅ (case consistency is convention, not enforced)
- Any arbitrary action can be written

**Risk:** Low — audit trail integrity is protected by HMAC, but querying/filtering becomes inconsistent without enum enforcement.

---

## 6. DEPENDENCY SECURITY

### 6.1 Python Dependencies

**Key dependencies from requirements.txt:**
- `fastapi==0.115.*` — Web framework
- `oqs==0.14.0` — liboqs Python bindings (post-quantum crypto)
- `cryptography==44.0.*` — AES-GCM (hazmat)
- `pydantic==2.*` — Validation
- `sqlalchemy[asyncio]==2.0.*` — Database
- `prometheus-client` — Metrics
- `opentelemetry-*` — Tracing
- `httpx` — HTTP client (used by Vault KMS)

**Security tools in dev:**
- `bandit` — SAST (runs in CI)
- `semgrep` — SAST (runs in CI, continue-on-error)
- `pip-audit` — **Commented out** in CI ❌
- `cargo-audit` — Runs with `continue-on-error: true` ⚠️
- `cargo-deny` — Runs with `continue-on-error: true` ⚠️

### 6.2 Known Issues

1. **pip-audit is disabled** — vulnerability scanning for Python dependencies is skipped
2. **cargo-audit is non-blocking** — Rust dependency vulnerabilities are warnings only
3. **No dependency pinning with hash** — `requirements.txt` uses version ranges (==) but no `pip freeze` lock file

---

## 7. SECRET MANAGEMENT

### 7.1 Environment Variables for Secrets

| Variable | Purpose |
|---|---|
| `AUDIT_KEY` / `AUDIT_KEY_vX` | HMAC audit keys |
| `API_KEY_OPERATOR` / `API_KEY_AUDITOR` | API keys for seed |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `VAULT_TOKEN` | Vault authentication |
| `AZURE_CLIENT_ID` / `AZURE_TENANT_ID` / `AZURE_CLIENT_SECRET` | Azure credentials |
| `QSC_LICENSE_KEY` | Enterprise license |

**Verdict:** No secrets hardcoded in source code. All secrets come from environment variables. Standard 12-factor app practice.

### 7.2 Secret Rotation

- Audit key rotation: Manual (env var + restart)
- KMS provider credentials: Manual (env var + restart)
- API key rotation: Via database update

**No automatic rotation mechanism exists.**

---

## 8. CONTAINER SECURITY

### 8.1 Dockerfile

```dockerfile
FROM python:3.11-slim-bookworm
RUN groupadd -r appuser && useradd -r -g appuser -u 8888 appuser
USER appuser
```

**Findings:**
- ✅ Multi-stage build (build deps in stage 1, runtime in stage 2)
- ✅ Non-root user (appuser)
- ✅ HEALTHCHECK configured
- ✅ `PYTHONUNBUFFERED=1`
- ❌ No `DOCKER_BUILDKIT` caching optimization
- ⚠️ `liboqs` is built from source (not prebuilt)

### 8.2 Docker Compose

```yaml
# docker-compose.yml
services:
  quantum-shield:
    build: .
    ports: ["8000:8000"]
    environment:
      - AUDIT_KEY=${AUDIT_KEY}
      - API_KEY_OPERATOR=${API_KEY_OPERATOR}
      - API_KEY_AUDITOR=${API_KEY_AUDITOR}
      - DATABASE_URL=sqlite+aiosqlite:///./data/quantum_shield.db
    volumes:
      - ./data:/app/data
```

**Findings:**
- ✅ Secrets passed via env vars (not in docker-compose file)
- ⚠️ SQLite in production (postgres recommended for prod)
- ⚠️ No network restrictions between containers

---

## 9. THREAT MODEL SUMMARY

| Threat | Mitigated? | Details |
|---|---|---|
| Private key theft from server | ✅ | Keys never stored server-side |
| Audit log tampering | ✅ | HMAC-SHA256 signed |
| Ciphertext manipulation | ✅ | AES-GCM authentication tag |
| Context switching attack | ✅ | AAD bound to context |
| Timing side-channel on auth | ✅ | Hash comparison is constant-time via SHA-256 |
| Padding oracle attack | ✅ | AES-GCM is NOT vulnerable to padding oracles |
| Nonce reuse | ⚠️ | Mitigated by unique Kyber768 KEM per operation |
| Replay attack | ⚠️ | Audit logs are timestamped but not checked for freshness |
| KMS credentials theft | ⚠️ | Depends on env var security at infrastructure level |
| Dependency vulnerability | ❌ | pip-audit disabled, cargo-audit non-blocking |

---

## 10. SECURITY FINDINGS SUMMARY

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | pip-audit disabled in CI | **HIGH** | Unfixed |
| 2 | No KDF (HKDF) for key derivation | **LOW** | Acceptable risk |
| 3 | Audit hash chain only in memory | **MEDIUM** | Planned for enterprise |
| 4 | Enterprise license is a stub | **LOW** | Acceptable for open-source |
| 5 | Action field is free-text (not enum) | **LOW** | Convention only |
| 6 | cargo-audit/cargo-deny non-blocking | **MEDIUM** | Unfixed |
| 7 | No automated secret rotation | **LOW** | Acceptable for MVP |
| 8 | No lock file for dependencies | **LOW** | Acceptable for MVP |
| 9 | SQLite as default database | **LOW** | Documented limitation |

---

## 11. COMPLIANCE MAPPING

| Regulation | Requirement | Status | Evidence |
|---|---|---|---|
| **NIS 2** (Art. 21) | Risk management, crypto agility | ✅ | ML-KEM-768, AES-256-GCM |
| **NIS 2** (Art. 23) | Audit trail, integrity | ✅ | HMAC-signed audit logs |
| **GDPR** Art. 32 | Appropriate technical measures | ✅ | Strong encryption |
| **eIDAS 2.0** | Qualified trust services | ⚠️ | Requires external certification |
| **SOC 2** | Access control, encryption | ⚠️ | Controls exist, no audit |
| **PCI DSS** | Key management | ⚠️ | Not specifically designed for PCI |