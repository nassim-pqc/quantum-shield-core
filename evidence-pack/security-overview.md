# Security Overview — Quantum Shield Core

_Generated from repository state on 31 May 2026_

## Cryptographic Standards

| Component | Standard | Implementation |
|-----------|----------|---------------|
| Key Encapsulation | ML-KEM-768 (NIST FIPS 203) | liboqs-python 0.14.1 |
| Symmetric Encryption | AES-256-GCM (NIST SP 800-38D) | pyca/cryptography 42.0.7 |
| Audit Integrity | HMAC-SHA256 | Python hmac + Rust hmac crate |
| Key Derivation | SHA-256 | hashlib / sha2 crate |

## Security Headers

| Header | Value |
|--------|-------|
| Strict-Transport-Security | max-age=63072000; includeSubDomains; preload |
| X-Content-Type-Options | nosniff |
| X-Frame-Options | DENY |
| Content-Security-Policy | default-src 'none' |
| Referrer-Policy | no-referrer |
| Permissions-Policy | geolocation=(), microphone=(), camera=() |
| Cache-Control | no-store, no-cache, must-revalidate |

## Authentication

- API key authentication via X-API-Key header
- Keys stored as SHA-256 hashes (never plaintext)
- RBAC: `operator` (crypto) and `auditor` (read-only)
- Rate limiting: 200/minute default, 10-60/minute per endpoint
- Error messages intentionally opaque on unseal failure

## Code Security

- Rust core: memory-safe by construction (borrow checker)
- Release build: `panic = "abort"`, LTO, codegen-units=1
- HMAC uses `hmac.compare_digest` (Python) and `Hmac::verify_slice` (Rust) — constant-time
- AES-GCM nonce generated fresh per operation via `os.urandom`
- Private keys never stored server-side (stateless design)

## Testing Coverage

- 139 tests passing across 8 test files
- Tests cover: health, auth/RBAC, key generation, seal, unseal, audit trail, tamper detection, payload validation, error opacity
- CI pipeline enforces tests on every PR

## Audit Trail

- Append-only HMAC-SHA256 signed log storage
- Key versioning enables rotation without data loss
- Hash-chain preparation via `prev_entry_hash` / `entry_hash`
- Integrity verified at read time

_This is an overview. See `docs/security/threat-model.md` and `SECURITY.md` for the full assessment._