# Quantum Shield Core — Investor Package

## Executive Summary

**Quantum Shield Core** is an enterprise-grade, post-quantum cryptographic microservice that future-proofs data against both classical and quantum computing threats.

| Metric | Value |
|--------|-------|
| **Technology** | ML-KEM-768 (NIST-standard) + AES-256-GCM |
| **Architecture** | Stateless microservice (private keys NEVER persisted) |
| **Languages** | Python (API) + Rust (crypto engine) |
| **KMS Support** | AWS KMS, HashiCorp Vault, Azure Key Vault |
| **Audit Trail** | HMAC-SHA256 signed, append-only, integrity-verified |
| **SDKs** | Python (pip installable), Go |
| **Deployment** | Docker, Kubernetes (Helm), Docker Compose |
| **Observability** | Prometheus, OpenTelemetry, structured JSON logging |
| **Auth** | API key + RBAC (operator/auditor) |
| **License** | Open-source (MIT) with Enterprise tier |
| **Maturity** | 159/159 tests passing, CI/CD hardened |

---

## Value Proposition

### Why Post-Quantum Cryptography Now?

| Threat | Timeline | Impact |
|--------|----------|--------|
| "Harvest Now, Decrypt Later" attacks | Ongoing | Data encrypted today decrypted when quantum arrives |
| NIST PQC standardization | 2024 | Regulatory mandate for government contracts |
| Crypto-agility requirements | 2025+ | NIS2, DORA, PCI DSS v5 |
| Quantum advantage | 2029–2035 | RSA/ECC broken by Shor's algorithm |

Quantum Shield Core solves all of these today.

### Key Differentiators

1. **Stateless by design** — private keys never stored server-side. No key escrow, no data breach risk.
2. **Hybrid PQC** — combines post-quantum KEM (Kyber768) with AES-256-GCM for quantum-resistant encryption.
3. **Enterprise KMS** — native integration with AWS KMS, HashiCorp Vault, Azure Key Vault.
4. **Tamper-evident audit** — HMAC-signed trail with key rotation and integrity verification.
5. **Rust core** — constant-time cryptographic operations, memory safety, no buffer overflows.
6. **Future-proof** — ML-KEM-768 is NIST-selected for long-term security.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Clients                             │
│  (Python SDK / Go SDK / cURL)                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ X-API-Key Header
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Quantum Shield Core API                       │
│                                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐                │
│  │ Auth     │  │ PQC Engine   │  │ Audit      │                │
│  │ (RBAC)   │  │ Kyber768 +   │  │ Trail      │                │
│  │          │  │ AES-256-GCM  │  │ HMAC-SHA256│                │
│  └──────────┘  └──────┬───────┘  └────────────┘                │
│                        │                                         │
│               ┌────────┴────────┐                               │
│               │  KMS Providers  │                               │
│               │ AWS │ Vault │ AZ │                               │
│               └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **API Layer** | FastAPI (Python) | Async, production-ready, OpenAPI |
| **PQC Engine** | liboqs-python (Kyber768) | NIST-standard post-quantum KEM |
| **Symmetric Crypto** | PyCA cryptography (AES-256-GCM) | AEAD, FIPS-compliant |
| **Constant-Time Engine** | Rust (PyO3) | Memory-safe, constant-time operations |
| **Database** | PostgreSQL / SQLite | Async, production-grade |
| **KMS** | AWS KMS / Vault / Azure | Enterprise key management |
| **Observability** | Prometheus + OpenTelemetry | Industry-standard monitoring |
| **Container** | Docker + Docker Compose | Portable, reproducible deployments |
| **Orchestration** | Kubernetes (Helm chart) | Enterprise-grade scheduling |
| **CI/CD** | GitHub Actions | Automated testing and deployment |

---

## Why Rust + Python?

### Python Advantages
- **Productivity**: Fast development cycle, extensive ecosystem
- **Integration**: Easy integration with existing Python infrastructure
- **SDK ecosystem**: Python is the #1 language for machine learning and data science
- **FastAPI**: Industry-leading async web framework

### Rust Advantages (via PyO3)
- **Memory safety**: No buffer overflows, use-after-free, or null pointer dereferences
- **Constant-time cryptography**: Protection against timing side-channel attacks
- **Panic abort**: Release builds abort on panic to prevent undefined behavior
- **Performance**: Near C/C++ speed for critical crypto operations

### The Combination
```
Python API Layer (productivity, ecosystem)
       │
       ▼
Rust Crypto Core (security, performance)
       │
       ▼
KMS Providers (AWS / Vault / Azure)
```

This gives enterprise customers the best of both worlds: **fast development** with **military-grade cryptography**.

---

## Market Opportunity

### Target Sectors

| Sector | Need | Quantum Shield Solution |
|--------|------|------------------------|
| **Government/Defense** | PQC migration mandate | ML-KEM-768, stateless, audit trail |
| **Financial Services** | NIS2/DORA compliance | HMAC audit, RBAC, KMS integration |
| **Healthcare** | GDPR, HIPAA compliance | Encrypted PHI, stateless, audit |
| **Legal** | Client confidentiality | Per-client keys, tamper-evident audit |
| **Technology** | API-first encryption | Docker/Helm, SDKs, OpenAPI |
| **Cloud/SaaS** | Multi-tenant encryption | KMS integration, stateless, RBAC |

### Competitive Landscape

| Feature | Quantum Shield | DIY Crypto | Cloud KMS Only | HSMs |
|---------|---------------|------------|----------------|------|
| Post-Quantum Ready | ✅ ML-KEM-768 | ❌ RSA/ECC | ❌ | ❌ |
| Stateless Architecture | ✅ | ❌ | ✅ | ❌ |
| Audit Trail | ✅ HMAC-signed | ❌ | ✅ | ✅ |
| KMS Integration | ✅ AWS/Vault/Azure | ❌ | ✅ | ✅ |
| Open Source | ✅ MIT | N/A | ❌ | ❌ |
| SDKs | ✅ Python + Go | ❌ | ✅ | ❌ |
| Rust Core | ✅ | ❌ | ❌ | ✅ |
| API-First | ✅ FastAPI | ❌ | ❌ | ❌ |
| Container Native | ✅ Docker/Helm | ❌ | ✅ | ❌ |

---

## Security Architecture

### Post-Quantum Cryptography
```
ML-KEM-768 (Kyber768)
├── NIST-selected (FIPS 203)
├── Module-Lattice-based KEM
├── 768-bit security (AES-192 equivalent)
├── Resistant to Shor's & Grover's algorithms
└── NIST security category 3
```

### Hybrid Encryption Scheme
```
Kyber768 KEM → Shared Secret (32 bytes)
    ↓ SHA-256
AES-256-GCM Key (32 bytes)
    + Random Nonce (12 bytes)
    + Plaintext
    + Context (AAD)
    ↓
Encrypted Data + GCM Tag
```

### Stateless Security
```
Private Key Lifetime:
┌─────────────────────┐
│ Generate in memory  │──→ Return to client
│                     │
│ Never persist to:   │
│  ✗ Database         │
│  ✗ Cache            │
│  ✗ Logs             │
│  ✗ Disk             │
│  ✗ Audit trail      │
└─────────────────────┘
    ↓
Garbage collected after request
```

---

## Technical Maturity

### Test Results
- **159/159 tests passing** (100%)
- **API integration tests**: health, auth, CRUD, security
- **KMS provider tests**: AWS KMS + Vault (mocked)
- **Security engine tests**: key gen, seal, unseal, tamper detection
- **Audit trail tests**: HMAC verification, tamper detection

### Security Posture
- ✅ HSTS (2 years, includeSubDomains, preload)
- ✅ X-Frame-Options: DENY
- ✅ X-Content-Type-Options: nosniff
- ✅ Content-Security-Policy: default-src 'none'
- ✅ Permissions-Policy: all disabled
- ✅ Referrer-Policy: no-referrer
- ✅ Server header stripped
- ✅ Opaque error messages (no oracle attacks)
- ✅ Rate limiting (200 req/min default)

### DevOps Maturity
- ✅ Multi-stage Docker build
- ✅ Docker security: read-only FS, no-new-privileges, cap_drop ALL
- ✅ Docker health check
- ✅ Kubernetes Helm chart
- ✅ GitHub Actions CI/CD (lint, test, security, build, deploy)
- ✅ Locust load testing

---

## Revenue Model

| Tier | Features | Target |
|------|----------|--------|
| **Open Source** (MIT) | Core API, SDK, audit trail, 200 req/min | Developers, startups |
| **Enterprise** (License) | AWS KMS, Vault, Azure KMS, priority support | Mid-market, regulated industries |
| **Enterprise Premium** | Dedicated instances, SLA, custom integrations | Enterprise, government |

---

## Business Case

### For Investors
- **First-mover advantage** in post-quantum cryptography
- **NIST standardization** creates regulatory tailwinds
- **"Harvest Now, Decrypt Later"** creates urgency for early adoption
- **Stateless architecture** eliminates key escrow liability
- **Open-source core** builds community and developer trust

### For Customers
- **Future-proof**: PQ-secure today, no migration needed later
- **Compliance-ready**: NIS2, DORA, GDPR, HIPAA alignment
- **Low friction**: Docker Compose → production in minutes
- **Vendor independence**: Multiple KMS backends
- **Developer experience**: SDKs, OpenAPI, clear documentation

---

## Roadmap

| Phase | Features | Timeline |
|-------|----------|----------|
| **1.0** (Current) | Core API, SDK, audit, KMS, observability | ✅ Released |
| **1.1** | PyPI package, API key management endpoints | Q2 2026 |
| **1.2** | Async SDK, expanded Go SDK | Q3 2026 |
| **2.0** | WebAuthn, OAuth2, hash chain enforcement | Q4 2026 |
| **2.1** | HSM integration, key ceremony, FIPS 140-3 | Q1 2027 |

---

## Competitive Advantage Summary

1. **First-mover in open-source PQ crypto**: First MIT-licensed PQC microservice
2. **NIST-standard algorithm**: ML-KEM-768 is the recommended PQC KEM
3. **Stateless by design**: Eliminates the #1 risk in cryptography — key exposure
4. **Enterprise KMS**: Works with existing AWS/Vault/Azure investments
5. **Tamper-evident audit**: Built-in compliance for regulated industries
6. **Rust core**: Memory-safe, constant-time, auditable
7. **Container-native**: Docker + Kubernetes out of the box
8. **Developer experience**: SDKs, OpenAPI, curl-compatible

---

## Contact

- **Repository**: https://github.com/nassim-pqc/quantum-shield-core
- **Documentation**: https://github.com/nassim-pqc/quantum-shield-core/tree/main/docs
- **License**: MIT (Open Source)