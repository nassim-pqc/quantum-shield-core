# Quantum Shield Core — Buyer Summary

> **Audience**: CTO, CISO, Head of Engineering, Corporate Development  
> **Format**: Executive summary for quick evaluation  
> **Date**: June 2026

---

## What Is Quantum Shield Core?

Quantum Shield Core is an **open-source, post-quantum cryptographic microservice** designed for enterprises preparing their encryption infrastructure for the quantum computing era.

It provides a **drop-in encryption layer** using NIST-standardized algorithms with a stateless architecture, enterprise KMS integrations, and two client SDKs.

**License**: MIT | **Version**: 1.0.0 | **Status**: Pre-commercial / Ready for POC

---

## Why It Matters

The global cryptographic infrastructure is transitioning to post-quantum algorithms. NIST finalized ML-KEM (FIPS 203) in 2024. Organizations handling sensitive data — healthcare, defense, finance, legal, government — need quantum-resistant encryption before current algorithms become vulnerable.

Quantum Shield Core provides a **ready-to-integrate, modular cryptographic layer** that:

- Uses **NIST-standardized algorithms** (ML-KEM-768, FIPS 203)
- Maintains **backward compatibility** via hybrid encryption (PQ + classical)
- Enforces **zero-knowledge key management** (stateless server)
- Provides a **complete audit trail** for compliance (GDPR, NIS2, DORA, HIPAA)

---

## Technical Stack

```
FastAPI (Python 3.12)  →  API layer
Rust (PyO3)            →  Constant-time HMAC, AES-GCM
liboqs                 →  ML-KEM-768 key encapsulation
AES-256-GCM            →  Symmetric authenticated encryption
PostgreSQL             →  Audit log storage
Prometheus             →  Metrics
OpenTelemetry          →  Distributed tracing
Docker + Helm          →  Deployment
```

---

## Key Features

| Feature | Detail |
|---------|--------|
| **Algorithm** | ML-KEM-768 (Kyber768) — NIST FIPS 203 standard |
| **Encryption** | Hybrid: PQ key encapsulation + AES-256-GCM |
| **Architecture** | Stateless — no user private keys stored server-side |
| **Audit Trail** | HMAC-SHA256 signed, append-only, with key rotation |
| **KMS Integration** | AWS KMS, Azure Key Vault, HashiCorp Vault (pluggable) |
| **SDKs** | Python (typed client with retry) + Go (idiomatic, rate-limited) |
| **Observability** | Prometheus metrics, OpenTelemetry tracing, JSON logs |
| **Security** | RBAC, API key auth, security headers, rate limiting |
| **Deployment** | Docker, docker-compose, Helm chart |
| **Container Hardening** | Hardened Dockerfile, Kubernetes manifests |
| **Benchmarks** | Automated, reproducible, with regression detection |

---

## Proof of Usage

| Evidence | Status | Location |
|----------|--------|----------|
| 139 passing Python tests | ✅ | `tests/` |
| Go SDK tests | ✅ | `sdk-go/` |
| CI/CD pipeline | ✅ | GitHub Actions |
| Automated benchmarks | ✅ | `benchmarks/performance/` |
| Container hardening | ✅ | `Dockerfile.hardened` |
| Performance reports | ✅ | `docs/PERFORMANCE_BENCHMARK_REPORT.md` |
| FIPS readiness doc | ✅ | `docs/FIPS_READINESS.md` |
| Side-channel doc | ✅ | `docs/SIDE_CHANNEL_READINESS.md` |

Full evidence: [evidence/README.md](../evidence/README.md)

---

## Ideal Buyer Profile

| Profile | Why They Would Want This |
|---------|--------------------------|
| **Cybersecurity Startup** | Ready-to-integrate PQC layer for their product |
| **Cloud/SaaS Company** | Post-quantum compliance for customer data |
| **Healthcare Platform** | HIPAA-compliant encryption with audit trail |
| **Financial Institution** | DORA compliance, quantum-safe encryption |
| **Legal/Compliance Tech** | Tamper-evident audit trail for regulated documents |
| **Government Contractor** | Post-quantum readiness for classified/sensitive data |
| **M&A / PE Firm** | Acqui-hire a working PQC team and codebase |
| **Cloud Integrator** | PQC offering for their security practice |

---

## Maturity

| Component | Status |
|-----------|--------|
| Core crypto engine | ✅ Working, tested (139 tests) |
| API endpoints | ✅ Complete (9 endpoints) |
| Audit trail | ✅ HMAC-signed, integrity-verified |
| KMS providers | ✅ AWS, Vault, Azure |
| AWS KMS real validation | ⚠️ Pending (requires AWS credentials) |
| Python SDK | ✅ Complete, tested |
| Go SDK | ✅ Complete, tested |
| CI/CD | ✅ GitHub Actions |
| Docker | ✅ Multi-stage build, health checks |
| Helm chart | ✅ Available |
| Documentation | ✅ 20+ documents |
| Performance benchmarks | ✅ Automated |
| Container hardening | ✅ Dockerfile.hardened |
| FIPS readiness | ⚠️ FIPS-aware (not certified) |
| Side-channel readiness | ⚠️ Side-channel-aware (not verified) |
| Independent audit | ❌ Not yet performed |
| Revenue | ❌ None yet |
| Customers | ❌ None yet |

---

## What Makes This Different

1. **NIST-Standardized PQC** — ML-KEM-768 (FIPS 203), not experimental
2. **Stateless by Design** — Zero user key storage, eliminates attack vector
3. **Enterprise KMS** — AWS, Vault, Azure — not just local keys
4. **Hybrid Encryption** — PQ + classical, defense-in-depth
5. **Two SDKs** — Python and Go, ready for integration
6. **Full Observability** — Metrics, tracing, structured logging
7. **MIT License** — No vendor lock-in

---

## Next Steps

1. **Technical Evaluation** — Run the demo locally (30 minutes)
2. **Code Review** — Clone the repo and review architecture
3. **POC Discussion** — Define a 4-6 week proof of concept
4. **Due Diligence** — Review the full evidence package
5. **Term Sheet** — Negotiate acquisition, licensing, or partnership

---

## Contact

- **GitHub**: https://github.com/nassim-pqc/quantum-shield-core
- **License**: MIT

---

*This document is honest and professional. No claims are exaggerated.*