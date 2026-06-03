# Quantum Shield Core — Technical Overview

> **Audience**: CTO, Lead Engineer, Security Architect  
> **Purpose**: Deep technical evaluation  
> **Date**: June 2026

---

## Architecture

```
┌──────────────┐     ┌─────────────────────────────────────────────┐
│  Client SDK  │────▶│         Quantum Shield Core API              │
│  (Python/Go) │     │  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
└──────────────┘     │  │  Rust     │  │  Python  │  │  Audit    │ │
                     │  │  Crypto   │  │  KEM     │  │  Store    │ │
                     │  │  Engine   │  │  (Kyber) │  │  (HMAC)   │ │
                     │  └──────────┘  └──────────┘  └───────────┘ │
                     └──────────────────────┬──────────────────────┘
                                            │
                                    ┌───────▼───────┐
                                    │   PostgreSQL  │
                                    │  (Audit Log)  │
                                    └───────────────┘
```

### Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Stateless** | No user private keys stored server-side |
| **Defense-in-depth** | Hybrid PQ + classical encryption |
| **Audit-first** | Every operation is signed and logged |
| **Pluggable** | KMS, database, observability are interchangeable |
| **Memory-safe** | Rust core engine with panic-abort |

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Liveness + DB health |
| POST | `/api/v1/keys/generate` | operator | Generate ML-KEM-768 keypair |
| POST | `/api/v1/crypto/seal` | operator | Hybrid encrypt (ML-KEM + AES-GCM) |
| POST | `/api/v1/crypto/unseal` | operator | Hybrid decrypt |
| POST | `/api/v1/audit/log` | operator/auditor | Append signed audit entry |
| GET | `/api/v1/audit/logs` | operator/auditor | List audit logs |
| GET | `/api/v1/audit/logs/{id}` | operator/auditor | Get log by ID |
| GET | `/api/v1/audit/stats` | operator/auditor | Audit statistics |
| GET | `/metrics` | None | Prometheus metrics |

Full API documentation: `docs/API_GUIDE.md`

---

## Cryptography

### Algorithm Stack

| Layer | Algorithm | Standard | Purpose |
|-------|-----------|----------|---------|
| Key Encapsulation | ML-KEM-768 (Kyber768) | FIPS 203 | Post-quantum key exchange |
| Key Derivation | SHA-256 | FIPS 180-4 | Shared secret → AES key |
| Symmetric Encryption | AES-256-GCM | FIPS 197 + SP 800-38D | Authenticated encryption |
| Audit Signing | HMAC-SHA256 | FIPS 198-1 | Tamper-evident audit logs |

### Hybrid Encryption Flow

1. Client generates ML-KEM-768 keypair (public + private)
2. **Seal**: Server encapsulates shared secret using public key, derives AES key via SHA-256, encrypts data with AES-256-GCM (AAD = context)
3. **Unseal**: Server decapsulates shared secret using private key, decrypts with AES-256-GCM
4. Private key is never stored server-side (stateless)

### Side-Channel Protections

- `hmac.compare_digest()` for constant-time signature verification
- Rust engine provides constant-time HMAC and AES-GCM when available
- OpenSSL hardware AES-NI acceleration
- Opaque error messages (no internal details leaked)

Full assessment: `docs/SIDE_CHANNEL_READINESS.md`

---

## Stateless Architecture

The server operates in **stateless mode** regarding cryptographic keys:

1. Client generates keypair via API
2. Private key is returned **once** and immediately discarded by server
3. No private key is written to disk, logs, or database
4. Server cannot decrypt data it has encrypted

**Security benefit**: Server compromise does not expose user keys.

**Compliance benefit**: Supports GDPR data minimization, zero-knowledge encryption.

---

## Audit Trail

- Every crypto operation generates a signed audit log entry
- HMAC-SHA256 signature with key versioning
- Append-only, tamper-evident
- Key rotation support (multiple audit key versions)
- In-memory store (community edition) / PostgreSQL (enterprise)

---

## KMS Providers

| Provider | Features | Configuration |
|----------|----------|---------------|
| **Local (default)** | Environment variables | `AUDIT_KEY` |
| **AWS KMS** | DEK wrapping, retry, error classification | `AWS_KMS_KEY_ID`, `AWS_REGION` |
| **HashiCorp Vault** | Transit Engine, KV v2, retry | `VAULT_ADDR`, `VAULT_TOKEN` |
| **Azure Key Vault** | Key wrapping, Identity auth | `AZURE_VAULT_URL` |

All providers implement the `KMSProvider` interface.

---

## SDKs

### Python SDK

```python
from sdk import QuantumShieldClient

client = QuantumShieldClient(base_url="http://localhost:8000", api_key="your-key")
keypair = client.generate_keypair()
sealed = client.seal(public_key_b64=keypair["public_key_b64"], data=b"secret", context="doc-1")
plaintext = client.unseal(private_key_b64=keypair["private_key_b64"], sealed=sealed, context="doc-1")
```

Features: typed client, retry logic, file encryption, text encryption.

### Go SDK

```go
c, _ := client.New(client.DefaultOptions())
c.SetAPIKey(os.Getenv("QS_API_KEY"))
keypair, _ := c.GenerateKeypair(ctx)
sealed, _ := c.Seal(ctx, keypair.PublicKeyB64, []byte("secret"), "doc-1")
plaintext, _ := c.Unseal(ctx, keypair.PrivateKeyB64, sealed, "doc-1")
```

Features: idiomatic Go, rate limiting, TLS 1.2+, functional options, structured logging.

---

## Observability

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Metrics | Prometheus | Crypto ops, request latency, audit writes |
| Tracing | OpenTelemetry | W3C trace context, OTLP export |
| Logs | structlog | Structured JSON logs |
| Correlation | X-Correlation-ID | Request tracing across services |

---

## CI/CD

| Job | Tool | Status |
|-----|------|--------|
| Lint | Ruff check + format | ✅ Configured |
| Security | Bandit SAST + Semgrep | ✅ Configured |
| Tests | pytest (Python 3.11, 3.12) | ✅ 139 tests |
| Rust | cargo build + test | ✅ Configured |
| Docker | Multi-stage build | ✅ Configured |
| Helm | Chart lint | ✅ Configured |

---

## Docker

### Standard Dockerfile

Multi-stage build: liboqs compilation → production image with non-root user.

### Hardened Dockerfile

Additional security: PYTHONDONTWRITEBYTECODE, pip cache purge, nologin shell, strict permissions.

### Docker Compose

Already includes: `cap_drop: ALL`, `no-new-privileges`, `read_only: true`, memory/CPU limits, log rotation.

Full guide: `docs/CONTAINER_HARDENING.md`

---

## Performance Benchmarks

| Operation | Latency (mean) | P95 | P99 | Ops/sec |
|-----------|----------------|-----|-----|---------|
| Key Generation | 0.01 ms | 0.02 ms | 0.02 ms | ~66,871 |
| Seal (1 KB) | 0.20 ms | 0.92 ms | 1.47 ms | 4,880 |
| Seal (1 MB) | 0.37 ms | 0.74 ms | 0.83 ms | 2,729 |
| Seal (10 MB) | 3.86 ms | 6.62 ms | 8.17 ms | 259 |
| Unseal (1 KB) | 0.03 ms | 0.04 ms | 0.05 ms | 32,944 |
| Unseal (1 MB) | 0.38 ms | 0.51 ms | 0.54 ms | 2,620 |
| Audit Write | 0.06 ms | 0.25 ms | 0.40 ms | 18,330 |
| Audit Verify | 0.00 ms | 0.01 ms | 0.01 ms | 244,906 |

*Results from Apple Silicon with Rust engine enabled.*

Full report: `docs/PERFORMANCE_BENCHMARK_REPORT.md`

---

## Security Features

| Feature | Implementation |
|---------|---------------|
| Authentication | API key (SHA-256 hashed) via `X-API-Key` |
| Authorization | RBAC (operator/auditor) |
| Rate Limiting | Per-IP, configurable |
| Security Headers | HSTS, CSP, X-Frame-Options, X-Content-Type-Options |
| CORS | Configurable allowed origins |
| Opaque Errors | No internal details leaked |

---

## FIPS Readiness

- Uses FIPS-approved algorithms: AES-256-GCM, SHA-256, HMAC-SHA256
- **NOT FIPS certified or compliant** — requires external validation
- Can be deployed on FIPS-validated infrastructure (AWS FIPS endpoints, Azure HSM)
- Full assessment: `docs/FIPS_READINESS.md`

---

## Side-Channel Readiness

- Constant-time HMAC verification (`hmac.compare_digest`)
- Constant-time operations via Rust engine (when available)
- OpenSSL hardware AES-NI acceleration
- **NOT formally verified** — requires independent audit for high-assurance
- Full assessment: `docs/SIDE_CHANNEL_READINESS.md`

---

## What This Is NOT

- ❌ Not FIPS certified
- ❌ Not formally verified
- ❌ Not side-channel proof
- ❌ Not production-proven with real customers
- ❌ Not a complete end-to-end encrypted communication system
- ❌ Not a key escrow or recovery system

---

*This document is technical and honest. No capabilities are overstated.*