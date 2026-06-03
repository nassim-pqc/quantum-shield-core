# Quantum Shield Core — Due Diligence Index

> **Purpose**: Index of all due diligence documents  
> **Audience**: Technical buyers, legal teams, investors  
> **Date**: June 2026

---

## How to Use This Index

This document provides a clear index to all due diligence materials. For each document, we explain:
- **What it is** — purpose and content
- **Who should read it** — which role
- **When to send it** — at which stage

---

## Master Reports

| Document | Location | Purpose | Audience | When to Send |
|----------|----------|---------|----------|--------------|
| Full Report (PDF) | `reports/Quantum_Shield_Core_Full_Report.pdf` | Complete technical report | All | First contact |
| Technical Due Diligence | `docs/FULL_TECHNICAL_DUE_DILIGENCE.md` | Technical deep-dive | CTO, engineers | Due diligence |
| Security Audit | `docs/FULL_SECURITY_AUDIT.md` | Security assessment | CISO, security team | Due diligence |
| Commercial Assessment | `docs/FULL_COMMERCIAL_ASSESSMENT.md` | Market analysis | Business development | Negotiation |
| Project Valuation | `docs/FULL_PROJECT_VALUATION.md` | Valuation analysis | Investors, M&A | Negotiation |
| Executive Summary | `docs/EXECUTIVE_SUMMARY.md` | High-level overview | Executives | First contact |
| Final Assessment | `docs/FINAL_VERIFIED_ASSESSMENT.md` | Verified findings | All | Due diligence |

---

## Evidence Package

| Document | Location | Purpose | Audience | When to Send |
|----------|----------|---------|----------|--------------|
| Proof of Usage Report | `evidence/PROOF_OF_USAGE_REPORT.md` | Verifiable evidence | Technical buyers | Due diligence |
| Buyer One-Pager | `evidence/BUYER_ONE_PAGER.md` | Executive summary | CTO, CISO | First contact |
| Evidence README | `evidence/README.md` | Project overview | All | First contact |

---

## Performance Evidence

| Document | Location | Purpose | Audience | When to Send |
|----------|----------|---------|----------|--------------|
| Benchmark Report | `docs/PERFORMANCE_BENCHMARK_REPORT.md` | Performance characteristics | CTO, engineers | Technical review |
| Performance Audit | `docs/PERFORMANCE_AUDIT.md` | Tooling inventory | Engineers | Technical review |
| Regression Guide | `docs/PERFORMANCE_REGRESSION_GUIDE.md` | Regression detection | DevOps, engineers | Technical review |
| Benchmark Results | `benchmarks/performance/results.md` | Actual benchmark data | Engineers | Technical review |

---

## Security Evidence

| Document | Location | Purpose | Audience | When to Send |
|----------|----------|---------|----------|--------------|
| Container Hardening | `docs/CONTAINER_HARDENING.md` | Container security | DevOps, security | Technical review |
| FIPS Readiness | `docs/FIPS_READINESS.md` | Compliance assessment | Compliance, legal | Compliance review |
| Side-Channel Readiness | `docs/SIDE_CHANNEL_READINESS.md` | Side-channel assessment | Security team | Security review |
| Security Guide | `docs/SECURITY_GUIDE.md` | Security practices | All | Technical review |
| Threat Model | `docs/security/threat-model.md` | Threat analysis | Security team | Security review |

---

## Architecture Evidence

| Document | Location | Purpose | Audience | When to Send |
|----------|----------|---------|----------|--------------|
| Architecture Overview | `docs/architecture/overview.md` | System design | Engineers | Technical review |
| API Guide | `docs/API_GUIDE.md` | API documentation | Engineers | Technical review |
| ADR-001: ML-KEM-768 | `docs/adr/001-ml-kem-768.md` | Algorithm decision | Cryptographers | Technical review |
| ADR-002: Rust Core | `docs/adr/002-rust-core.md` | Engine decision | Engineers | Technical review |
| ADR-003: AES-GCM | `docs/adr/003-aes-gcm.md` | Cipher decision | Cryptographers | Technical review |
| ADR-004: Microservice | `docs/adr/004-microservice-architecture.md` | Architecture decision | Architects | Technical review |

---

## SDK Evidence

| Document | Location | Purpose | Audience | When to Send |
|----------|----------|---------|----------|--------------|
| Go SDK Audit | `docs/GO_SDK_AUDIT.md` | Go SDK assessment | Go developers | Technical review |
| Go SDK Guide | `docs/GO_SDK_GUIDE.md` | Go SDK usage | Go developers | Technical review |
| Go SDK Summary | `docs/GO_SDK_IMPLEMENTATION_SUMMARY.md` | Go SDK details | Engineers | Technical review |

---

## Deployment Evidence

| Document | Location | Purpose | Audience | When to Send |
|----------|----------|---------|----------|--------------|
| Docker Guide | `docs/DOCKER_GUIDE.md` | Docker deployment | DevOps | Technical review |
| Environment Guide | `docs/ENV_GUIDE.md` | Configuration | DevOps | Technical review |
| Live Demo Deployment | `docs/live-demo-deployment.md` | Deployment guide | DevOps | Technical review |
| Helm Chart | `deploy/helm/quantum-shield/` | Kubernetes deployment | DevOps | Technical review |

---

## Sending Guide

### First Contact (Day 1)
1. `sales-package/BUYER_SUMMARY.md` — Executive summary
2. `reports/Quantum_Shield_Core_Full_Report.pdf` — PDF report
3. GitHub link — https://github.com/nassim-pqc/quantum-shield-core

### Technical Review (Day 2-5)
4. `sales-package/TECHNICAL_OVERVIEW.md` — Technical deep-dive
5. `sales-package/PROOF_OF_USAGE.md` — Evidence package
6. `docs/PERFORMANCE_BENCHMARK_REPORT.md` — Performance data

### Due Diligence (Week 1-2)
7. `docs/FULL_TECHNICAL_DUE_DILIGENCE.md` — Technical DD
8. `docs/FULL_SECURITY_AUDIT.md` — Security DD
9. `evidence/PROOF_OF_USAGE_REPORT.md` — Full evidence
10. `docs/CONTAINER_HARDENING.md` — Container security
11. `docs/FIPS_READINESS.md` — Compliance
12. `docs/SIDE_CHANNEL_READINESS.md` — Side-channel

### Negotiation (Week 2-4)
13. `sales-package/VALUATION_NOTE.md` — Pricing
14. `sales-package/KNOWN_LIMITATIONS.md` — Limitations
15. `docs/FULL_COMMERCIAL_ASSESSMENT.md` — Market
16. `docs/FULL_PROJECT_VALUATION.md` — Valuation

---

## Document Checklist

Before sending any document, verify:
- [ ] No secrets or API keys in the document
- [ ] No internal URLs or credentials
- [ ] No exaggerated claims
- [ ] All "NOT" disclaimers are present
- [ ] Version number is current
- [ ] Date is current

---

*All documents are honest, professional, and ready for review.*