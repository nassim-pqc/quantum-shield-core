# Security Overview — Quantum Shield Core

## Cryptographic Architecture

- **Key Encapsulation**: ML-KEM-768 (NIST FIPS 203) via liboqs
- **Symmetric Encryption**: AES-256-GCM (AEAD, NIST SP 800-38D)
- **Audit Integrity**: HMAC-SHA256 with key versioning (rotation support)
- **Key Derivation**: SHA-256 between KEM shared secret and AES key

## Authentication & Authorization

- API key authentication via SHA-256 hashed keys in PostgreSQL
- RBAC with two roles: `operator` (crypto operations) and `auditor` (read-only logs)
- Rate limiting (slowapi) per IP: 200/minute default, 10-60/minute per endpoint

## Transport Security

- TLS 1.3 (terminated at reverse proxy / API gateway)
- HSTS: `max-age=63072000; includeSubDomains; preload`
- CSP: `default-src 'none'`
- All security headers enforced at middleware level

## Audit Trail

- Append-only log storage in PostgreSQL
- Each entry signed with HMAC-SHA256
- Key versioning enables key rotation without data loss
- Hash chain preparation (`prev_entry_hash`, `entry_hash`) for future verification
- Integrity field updated at read time from HMAC verification

## Side-Channel Protections

- HMAC comparison uses `hmac.compare_digest` (constant-time) in Python
- HMAC verification uses `Hmac::verify_slice` (constant-time) in Rust
- AES-GCM nonce generated fresh per operation via `os.urandom`
- Unseal error messages intentionally opaque (hides whether key, context, or GCM tag failed)

## Memory Safety

- Rust core engine: memory-safe by construction (borrow checker, no null pointers)
- Release build: `panic = "abort"` to prevent undefined behavior
- Rust release build: LTO, codegen-units=1, strip symbols

## Infrastructure Security

- Stateless design: no private keys stored server-side
- Database connection pool with `pool_pre_ping` for production
- SQLite for development/testing; PostgreSQL for production
- OpenTelemetry tracing with W3C trace context propagation
- Prometheus metrics exposed on `/metrics`

## Dependency Auditing

| Tool | Scope | Frequency |
|------|-------|-----------|
| `pip-audit` | Python (requirements.txt) | Per CI run |
| `bandit` | Python SAST | Per CI run |
| `semgrep` | Python SAST | Per CI run |
| `cargo-audit` | Rust dependencies | Per CI run (requires Rust toolchain) |
| `cargo-deny` | Rust licenses + advisories | Per CI run (requires Rust toolchain) |
| `ruff` | Python lint + format | Per CI run |

## Compliance-Ready

- Signed audit trail with HMAC-SHA256 satisfies NIS2 article 22 (logging)
- JSON-structured logs ready for SIEM ingestion
- OpenTelemetry integration for SOC/SOAR pipelines
- Rate limiting documented and configurable per endpoint
- HSTS, CSP, X-Frame-Options, X-Content-Type-Options all enforced