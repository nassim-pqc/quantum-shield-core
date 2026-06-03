# Quantum Shield Core — Buyer One-Pager

> **Audience**: CTO, CISO, Head of Engineering, Corporate Development, Investors
> **Format**: Executive summary for quick evaluation
> **Date**: June 2026

---

## Project Summary

**Quantum Shield Core** is an open-source, post-quantum cryptographic microservice built for enterprises that need to prepare their encryption infrastructure for the quantum computing era.

It provides a **drop-in encryption layer** using NIST-standardized algorithms (ML-KEM-768 + AES-256-GCM) with a stateless architecture, enterprise KMS integrations, and two client SDKs (Python and Go).

**License**: MIT | **Version**: 1.0.0 | **Status**: Pre-commercial / Ready for POC

---

## Technical Value Proposition

| Capability | Detail |
|------------|--------|
| **Algorithm** | ML-KEM-768 (Kyber768) — NIST FIPS 203 standard |
| **Encryption** | Hybrid: PQ key encapsulation + AES-256-GCM authenticated encryption |
| **Architecture** | Stateless — no user private keys stored server-side |
| **Audit Trail** | HMAC-SHA256 signed, append-only, with key rotation |
| **KMS Integration** | AWS KMS, HashiCorp Vault, Azure Key Vault (pluggable) |
| **SDKs** | Python (typed client with retry) + Go (idiomatic, rate-limited) |
| **Observability** | Prometheus metrics, OpenTelemetry tracing, JSON logs |
| **Security** | RBAC, API key auth (SHA-256 hashed), security headers, rate limiting |
| **Deployment** | Docker, docker-compose, Helm chart |

---

## Differentiators

1. **NIST-Standardized PQC**: Uses ML-KEM-768 (FIPS 203), not experimental or deprecated algorithms
2. **Stateless by Design**: Zero user key storage eliminates an entire attack vector
3. **Enterprise KMS**: Pre-built integrations with AWS, Vault, and Azure — not just local keys
4. **Hybrid Encryption**: PQ + classical provides defense-in-depth during the transition period
5. **Two SDKs**: Python and Go clients ready for integration
6. **Full Observability**: Not just crypto — metrics, tracing, and structured logging included
7. **MIT License**: No vendor lock-in, no licensing friction

---

## Technology Stack

```
FastAPI (Python 3.12)  →  API layer
Rust (PyO3)            →  Constant-time HMAC, AES-GCM
liboqs                 →  ML-KEM-768 key encapsulation
PostgreSQL             →  Audit log storage
Prometheus             →  Metrics
OpenTelemetry          →  Distributed tracing
Docker + Helm          →  Deployment
```

---

## Current Maturity

| Component | Status | Evidence |
|-----------|--------|----------|
| Core crypto engine | Production-ready code | 139 passing tests |
| API endpoints | Complete | OpenAPI/Swagger docs |
| Audit trail | Working | HMAC-signed, integrity-verified |
| KMS providers | Implemented | AWS, Vault, Azure |
| Python SDK | Complete | Typed client, retry logic, file methods |
| Go SDK | Complete | Idiomatic, rate-limited, TLS 1.2+ |
| CI/CD | Configured | GitHub Actions (lint, security, test, build) |
| Docker | Working | Multi-stage build, health checks |
| Helm chart | Available | Linted, configurable |
| Documentation | Comprehensive | 20+ docs, guides, ADRs |
| Performance benchmarks | Automated | JSON + Markdown reports, regression detection |
| Container hardening | Available | Dockerfile.hardened, Kubernetes manifests |
| FIPS readiness | FIPS-aware | Uses FIPS-approved algorithms (not certified) |
| Side-channel readiness | Side-channel-aware | Constant-time comparison, hardened primitives |

---

## What Is Already Done

- [x] ML-KEM-768 key generation and hybrid encryption
- [x] Stateless server architecture
- [x] HMAC-signed audit trail with key rotation
- [x] RBAC authentication (operator/auditor)
- [x] 139 automated tests (Python)
- [x] Go SDK with full API coverage
- [x] AWS KMS provider with retry and error classification
- [x] HashiCorp Vault provider with Transit Engine + KV v2
- [x] Azure Key Vault provider with Identity auth
- [x] Prometheus metrics and OpenTelemetry tracing
- [x] Docker and Helm deployment
- [x] CI/CD pipeline (GitHub Actions)
- [x] Comprehensive documentation

---

## What Remains To Be Done

- [ ] Independent cryptographic audit (recommended before production)
- [ ] SOC 2 / ISO 27001 certification
- [ ] Bug bounty program
- [ ] Production deployment history
- [ ] Performance optimization at scale (10K+ req/s)
- [ ] Additional SDKs (Rust, Java, Node.js)
- [ ] Key recovery / escrow mechanism (optional, customer-managed)
- [ ] Integration tests with live KMS providers

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

---

## Valuation Range (Indicative)

| Scenario | Range | Rationale |
|----------|-------|-----------|
| **Codebase acquisition** | $50K–$150K | Working code, tests, docs, SDKs |
| **Technology licensing** | $100K–$300K | IP + integration support |
| **Startup acquisition** | $200K–$500K | Team + code + market positioning |
| **Strategic partnership** | Revenue share | Joint go-to-market |

*Note: These are indicative ranges for a pre-commercial, pre-audit technical asset. Actual valuation depends on buyer strategic fit, market timing, and negotiation.*

---

## Known Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| No independent crypto audit | High — required for production | Budget $30K–$80K for audit |
| No revenue or customers | Medium — proves market | POC with 2-3 design partners |
| No SOC 2 / ISO 27001 | Medium — required for enterprise | 6-12 month certification process |
| Single developer (current) | Medium — bus factor | Hire or acquire team |
| liboqs dependency | Low — well-maintained open source | Can fork if needed |

---

## Next Steps

1. **Technical Evaluation**: Run the demo locally (30 minutes)
2. **Code Review**: Clone the repo and review the architecture
3. **POC Discussion**: Define a 4-6 week proof of concept scope
4. **Due Diligence Review**: Examine the full evidence package
5. **Term Sheet**: Negotiate acquisition, licensing, or partnership terms

---

## Contact

- **GitHub**: https://github.com/nassim-pqc/quantum-shield-core
- **Repository**: `quantum-shield-core`
- **License**: MIT

---

*This document is honest and non-exaggerated. The project is a pre-commercial technical asset with working code but no revenue, no independent audit, and no production customers.*