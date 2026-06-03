# Quantum Shield Core — System Architecture

## Overview

Quantum Shield Core is a **stateless, post-quantum cryptographic microservice** that provides:

- **ML-KEM-768 (Kyber768)** key generation
- **Hybrid encryption** (Kyber768 KEM + AES-256-GCM)
- **HMAC-SHA256 signed audit trail** with key rotation
- **Enterprise KMS integration** (AWS KMS, HashiCorp Vault, Azure Key Vault)
- **Stateless architecture**: private keys NEVER persisted server-side

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Clients                             │
│  (SDK Python / SDK Go / cURL / Custom)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ X-API-Key + JSON
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application (main.py)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │
│  │ Auth     │  │ Crypto   │  │ Audit    │  │ Observability  │ │
│  │ (RBAC)   │  │ Endpoints│  │ Endpoints│  │ (Prom/OTel)    │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────────────┘ │
└───────┼──────────────┼────────────┼─────────────────────────────┘
        │              │            │
        ▼              ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SecurityEngine (security_engine.py)           │
│                                                                  │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│  │  PQC Operations     │  │  Audit Trail (HMAC-SHA256)       │  │
│  │  - Key Generation   │  │  - generate_signed_log()         │  │
│  │  - encrypt_hybrid() │  │  - verify_log()                  │  │
│  │  - decrypt_hybrid() │  │  - Key versioning                │  │
│  └──────────┬──────────┘  └────────────────┬─────────────────┘  │
│             │                              │                    │
│             ▼                              ▼                    │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│  │  Rust Engine (opt)  │  │  KMS Abstraction (AbstractKMS)   │  │
│  │  quantum_shield_en-  │  │  ┌────────┐ ┌───────┐ ┌──────┐ │  │
│  │  gine (PyO3)         │  │  │ Local  │ │ AWS   │ │Vault │ │  │
│  │  - Constant-time     │  │  │ EnvKMS │ │ KMS   │ │ KMS  │ │  │
│  │  - AES-GCM           │  │  └────────┘ └───────┘ └──────┘ │  │
│  │  - HMAC              │  └──────────────────────────────────┘  │
│  └─────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
┌──────────────────┐    ┌─────────────────────────────┐
│  PostgreSQL /    │    │  Audit Store                │
│  SQLite (Async)  │    │  - In-memory (OSS)          │
│  - api_keys      │    │  - PostgreSQL (Enterprise)  │
│  - audit_logs    │    └─────────────────────────────┘
└──────────────────┘
```

---

## Component Breakdown

### 1. API Layer (`main.py`)
- FastAPI application with async support
- 8 endpoints grouped into 4 categories (System, Key Management, Cryptography, Audit Trail)
- Rate limiting via `slowapi` (200 req/min default)
- CORS, security headers, correlation IDs
- Prometheus metrics via `prometheus-fastapi-instrumentator`
- OpenTelemetry tracing

### 2. Authentication (`auth.py`)
- API key authentication via `X-API-Key` header
- Keys hashed with SHA-256 before storage/query
- RBAC with two roles: `operator` and `auditor`
- Constant-time comparison via hash equality
- Keys stored in database (`api_keys` table)

### 3. Cryptographic Engine (`security_engine.py`)
- **SecurityEngine** class orchestrating all crypto operations
- **AbstractKMS** interface for key management abstraction
- **LocalEnvKMS** fallback for development/OSS
- Uses `oqs` (liboqs-python) for Kyber768 operations
- Uses `cryptography.hazmat` for AES-256-GCM
- Optional Rust engine (`quantum_shield_engine`) for constant-time operations
- HMAC-SHA256 signed audit trail with key versioning

### 4. KMS Providers (`providers/kms/`)
- **Base interfaces**: `KeyWrapper`, `SecretProvider`, `KMSProvider`
- **AWS KMS**: RSAES_OAEP_SHA_256 for DEK wrapping, env-based audit keys
- **HashiCorp Vault**: Transit Engine + KV v2 for secrets
- **Azure Key Vault**: secrets management (stub)
- All providers implement retry via `tenacity`

### 5. Data Layer
- **SQLAlchemy async** ORM with SQLite (dev) or PostgreSQL (prod)
- **Models**: `ApiKey` (hashed keys), `AuditLog` (signed entries)
- **Alembic** for schema migrations
- **In-memory audit store** as OSS fallback (`audit_store.py`)

### 6. Observability (`observability/`)
- **Structured JSON logging** with `JsonFormatter`
- **Prometheus metrics**: CRYPTO_OPS, AUDIT_WRITES, REQUEST_LATENCY
- **OpenTelemetry tracing** via OTLP exporter
- **Correlation ID middleware** for request tracing

### 7. Rust Engine (`rust-engine/`)
- Memory-safe Rust implementation via PyO3
- constant-time AES-GCM and HMAC
- Aborts on panic in release mode
- Optional — falls back to Python implementation

### 8. SDKs
- **Python SDK** (`sdk/`): Full-featured client
- **Go SDK** (`sdk-go/`): Client library for Go consumers

---

## Data Flow

### Key Generation Flow
```
Client → POST /api/v1/keys/generate
  → auth.py (validate API key, check operator role)
  → SecurityEngine.generate_keypair()
    → oqs.KeyEncapsulation.generate_keypair()
    → returns (public_key, secret_key)
  → Audit: generate_signed_log("KEY_GENERATE", ...)
  → Store audit entry
  → Return {public_key_b64, private_key_b64}
  → Private key NEVER stored server-side ✓
```

### Seal (Encryption) Flow
```
Client → POST /api/v1/crypto/seal
  → auth.py (validate API key, check operator role)
  → SecurityEngine.encrypt_hybrid(pub_key, plaintext, context)
    → oqs.KeyEncapsulation.encap_secret(public_key)
      → generates ephemeral KEM keypair
      → returns (ciphertext_pqc, shared_secret)
    → AES_key = SHA256(shared_secret)
    → AESGCM.encrypt(nonce, plaintext, context=AAD)
    → returns {ciphertext_pqc, nonce, encrypted_data}
  → Audit: generate_signed_log("SEAL", context, user)
  → Return sealed payload
```

### Unseal (Decryption) Flow
```
Client → POST /api/v1/crypto/unseal
  → auth.py (validate API key, check operator role)
  → SecurityEngine.decrypt_hybrid(priv_key, ciphertext_pqc, nonce, enc_data, context)
    → oqs.KeyEncapsulation.decap_secret(ciphertext_pqc) with secret_key
      → returns shared_secret
    → AES_key = SHA256(shared_secret)
    → AESGCM.decrypt(nonce, encrypted_data, context=AAD)
    → returns plaintext
  → Audit: generate_signed_log("UNSEAL", context, user)
  → Return decrypted data
  → Error 401 on: wrong key, wrong context, tampered data
```

### Audit Trail Flow
```
Client → POST /api/v1/audit/log
  → auth.py (validate API key, check operator/auditor role)
  → SecurityEngine.generate_signed_log(action, target, user)
    → Build JSON with {action, key_version, target, timestamp, user}
    → HMAC-SHA256(key, json_bytes)
    → Returns {log, signature, key_version}
  → Store in audit store (in-memory or PostgreSQL)
  → Return {id, log, signature}

Verification:
  Client → GET /api/v1/audit/logs
  → For each entry:
    → SecurityEngine.verify_log(log_json, signature)
      → Parse key_version from log
      → Retrieve key from KMS
      → HMAC-SHA256(key, log_bytes) == signature?
    → Mark integrity status (OK/FAIL)
  → Return entries with integrity status
```

---

## Security Architecture

### Post-Quantum Cryptography
- **ML-KEM-768** (formerly Kyber768): NIST-selected post-quantum KEM
- Module-Lattice-Based Key Encapsulation Mechanism
- 768-bit security level (AES-192 equivalent)
- Resistant to quantum computer attacks (Shor's algorithm)

### Hybrid Encryption Scheme
```
Kyber768 KEM                  AES-256-GCM
┌──────────────┐              ┌──────────────┐
│ Shared Secret │──SHA256──→ │  AES Key      │
│ (32 bytes)    │              │  (32 bytes)   │
└──────────────┘              └──────┬───────┘
                                     │
Ciphertext PQC ──────────────────────┤
Nonce (random 12B) ──────────────────┤
Context (AAD) ───────────────────────┤
                                     ▼
                            Encrypted Data + GCM Tag
```

### Key Separation
- **Encryption keys**: Ephemeral Kyber768 keypairs — never stored server-side
- **Audit keys**: HMAC keys managed via KMS (local env / AWS KMS / Vault)
- **API keys**: SHA-256 hashed in database — plaintext never persisted

### Audit Trail Integrity
- HMAC-SHA256 signatures with key versioning
- Hash-chain preparation (prev_entry_hash + entry_hash fields)
- Key rotation support (multiple AUDIT_KEY_vX versions)
- Integrity verification on every read

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | FastAPI (Python) | Async web framework |
| Crypto (PQC) | liboqs-python / oqs | Kyber768 operations |
| Crypto (AES) | PyCA cryptography | AES-256-GCM |
| Crypto (Rust) | PyO3 + aes-gcm crate | Constant-time fallback |
| Database | PostgreSQL / SQLite | Production / dev |
| ORM | SQLAlchemy 2.0 (async) | Data access |
| Auth | API Key (SHA-256 hash) | Authentication |
| KMS (AWS) | boto3 | Key management |
| KMS (Vault) | httpx + hvac | Key management |
| Observability | Prometheus + OpenTelemetry | Monitoring |
| Container | Docker | Deployment |
| Orchestration | Docker Compose / Helm | Service orchestration |
| CI/CD | GitHub Actions | Automation |

---

## Deployment Architecture

### Development
```
docker compose up --build
→ PostgreSQL 16 (Alpine)
→ Quantum Shield API (FastAPI + Uvicorn)
→ Port 8000 (localhost only)
```

### Production (Helm)
```
helm install quantum-shield deploy/helm/quantum-shield/
→ Configurable replicas, HPA, resource limits
→ Secret management via Kubernetes secrets
→ Health checks, readiness probes
```

### Kubernetes Deployment
```yaml
- Container: ghcr.io/quantum-shield/core:latest
- Ports: 8000
- Environment: From secrets/configmap
- Probes: HTTP /health
- Security: runAsNonRoot, readOnlyRootFilesystem, drop ALL capabilities
```

---

## Enterprise Features

- **KMS Integration**: AWS KMS, HashiCorp Vault, Azure Key Vault
- **License Enforcement**: Enterprise license key validation
- **Audit Trail**: HMAC-signed, append-only, integrity-verified
- **Rate Limiting**: Per-endpoint rate limits
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **Correlation IDs**: End-to-end request tracing
- **Structured Logging**: JSON format for SIEM ingestion
- **Prometheus Metrics**: Custom crypto/audit operation counters
- **OpenTelemetry**: Distributed tracing with OTLP export
- **Docker Security**: Read-only filesystem, no-new-privileges, resource limits

---

## Dependencies

| Dependency | Version | Purpose |
|-----------|---------|---------|
| fastapi | 0.111.0 | Web framework |
| cryptography | 42.0.7 | AES-256-GCM |
| liboqs-python | 0.14.1 | Kyber768 PQC |
| sqlalchemy | 2.0.31 | ORM |
| boto3 | 1.34.128 | AWS SDK |
| httpx | 0.27.0 | HTTP client (Vault) |
| hvac | 1.2.1 | Vault client |
| tenacity | >=8.2 | Retry logic |
| prometheus-client | 0.20.0 | Metrics |
| opentelemetry-api | 1.25.0 | Distributed tracing |