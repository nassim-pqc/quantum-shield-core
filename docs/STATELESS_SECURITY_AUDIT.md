# Quantum Shield Core — Stateless Security Audit

## Overview

This document audits Quantum Shield Core's **stateless architecture** — ensuring that **private keys are never persisted server-side**.

The core principle:
> Private keys are generated ephemerally, returned to the client once, and **never written to disk, database, cache, or logs** on the server.

---

## Audit Scope

| Area | Status | Details |
|------|--------|---------|
| **Database** | ✅ Compliant | No private key fields in schema |
| **Logs** | ✅ Compliant | Private keys never logged |
| **Audit Trail** | ✅ Compliant | Logs contain action metadata, not keys |
| **Cache** | ✅ Compliant | No private key caching |
| **Temporary Storage** | ✅ Compliant | No /tmp or file writes of keys |
| **Exports** | ✅ Compliant | API returns keys once, no export endpoint |
| **Memory** | ✅ Compliant | Keys in process memory only, GC'd after request |
| **KMS Providers** | ✅ Compliant | DEK wrapping handles ephemeral keys only |

---

## Detailed Analysis

### 1. Database (`models.py`)

**Schema:**
```python
class ApiKey(Base):
    """Only stores SHA-256 hashes of API keys — not private keys."""
    id, organization, key_hash, role, is_active, created_at

class AuditLog(Base):
    """Stores signed log entries — never contains private keys."""
    id, sequence_number, action, target, actor, key_version, log_json, signature, integrity
```

**Verification:**
- No column stores private keys or raw key material
- `ApiKey.key_hash` stores SHA-256 hashes only
- `AuditLog.log_json` stores action metadata only (action, target, timestamp, user, key_version)
- Private encryption keys never appear in any table
- ✅ **Compliant**

### 2. API Endpoints (`main.py`)

**Key Generation (`POST /api/v1/keys/generate`):**
```python
pub, priv = crypto_engine.generate_keypair()
# Keys returned in response body
return {
    "public_key_b64": base64.b64encode(pub).decode(),
    "private_key_b64": base64.b64encode(priv).decode(),
}
# Keys go out of scope after return — garbage collected
```

**Verification:**
- Private key is returned once in HTTP response
- No database write of private key (only audit log with metadata)
- Key variables go out of scope after function return
- Python garbage collector reclaims memory
- ✅ **Compliant**

### 3. Audit Trail (`audit_store.py`, `security_engine.py`)

**Signed log structure:**
```python
log_data = {
    "action": action,
    "key_version": self.active_key_version,
    "target": target,
    "timestamp": datetime.now(UTC).isoformat(),
    "user": user,
}
# Only metadata — no key material
```

**Verification:**
- Log entries contain action, target, user, key_version only
- Signature is HMAC-SHA256 of log JSON (not of keys)
- No key material in audit store
- ✅ **Compliant**

### 4. Logging (`observability/logging_config.py`)

**Verification:**
- Structured JSON logging uses `JsonFormatter`
- No `repr` or `str` of key material in log records
- Exception logging captures tracebacks but no key data
- Crypto operations logged with metadata only (operation type, duration)
- ✅ **Compliant**

### 5. Temporary Storage

**Verification:**
- Docker has `read_only: true` filesystem
- `/tmp` is tmpfs (in-memory, wiped on restart)
- No file writes of key material in codebase
- `tempfile` usage in tests only (test isolation)
- ✅ **Compliant**

### 6. Cache

**Verification:**
- No caching layer for private encryption keys
- KMS providers cache audit keys (with TTL), not encryption keys
- `_cache` in AWS KMS provider stores audit HMAC keys only
- ✅ **Compliant**

### 7. Error Messages

**Verification:**
```python
# Unseal failure — opaque message
raise HTTPException(
    status_code=401,
    detail="Unseal failed: invalid key, context mismatch, or tampered payload.",
)
```

- Error messages do not reveal whether failure was key, context, or GCM tag
- Anti-oracle padding: no distinction between error types
- ✅ **Compliant**

### 8. KMS Providers

**Verification:**
- `AWSKMSProvider.wrap_key()` wraps DEKs (ephemeral shared secrets), not private keys
- `HashiCorpVaultKMSProvider.wrap_key()` same pattern
- Audit keys are HMAC keys stored in KMS — not private encryption keys
- ✅ **Compliant**

---

## Data Flow Analysis

### Key Generation — Data at Rest
```
Client Request
  → Key Generation (in-memory)
  → Response with keys
  → Audit log (metadata only)
  → Memory freed (GC)
  
┌─────────┐     ┌──────────┐     ┌──────────┐
│  RAM    │     │  Disk    │     │  DB      │
├─────────┤     ├──────────┤     ├──────────┤
│ pub key │────→│ ❌ Never │     │ ❌ Never │
│ priv key│────→│ ❌ Never │     │ ❌ Never │
└─────────┘     └──────────┘     └──────────┘
```

### Seal/Unseal — Data in Use
```
Seal:
  Client provides public_key_b64 → ephemeral in memory → encrypted → response

Unseal:
  Client provides private_key_b64 → ephemeral in memory → decrypted → response
  
No persistence at any point.
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Key in application logs | Very Low | Critical | Code review confirms no logging of key data |
| Key in DB snapshot | Very Low | Critical | Schema has no key columns |
| Key in error traceback | Low | High | Unseal errors return opaque messages |
| Key in memory dump | Very Low | High | Docker container isolation, no core dumps |
| Key in network capture | Low | High | TLS required (documented) |

---

## Compliance

### NIS2 / DORA Readiness
- ✅ Private keys never stored → meets "data minimization" principle
- ✅ Audit trail captures metadata without exposing keys
- ✅ Key separation: encryption keys vs. audit keys

### SOC 2 / ISO 27001 Alignment
- ✅ Access controls on key generation (operator role only)
- ✅ Audit logging of all key generation events
- ✅ Tamper-evident audit trail

### GDPR
- ✅ No personal data in key material
- ✅ No key persistence means no data subject to breach
- ✅ Audit logs contain user identifiers (controlled)

---

## Conclusion

**Quantum Shield Core is fully stateless with respect to private keys.**

1. Private keys exist only in process memory during request handling
2. They are returned once via API response
3. They are never persisted to database, cache, filesystem, or logs
4. All persistent state (audit logs, API key hashes) contains no private key material
5. KMS stores only HMAC audit keys — not private encryption keys

**Risk Level: ✅ No material risk identified**