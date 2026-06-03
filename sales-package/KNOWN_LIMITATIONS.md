# Quantum Shield Core — Known Limitations

> **Purpose**: Transparent disclosure of limitations  
> **Audience**: All buyers, due diligence reviewers  
> **Date**: June 2026

---

## Honest Assessment

This document lists all known limitations of Quantum Shield Core. Transparency is essential for building trust with potential buyers and partners.

---

## Critical Limitations

| Limitation | Impact | Mitigation | Timeline |
|------------|--------|------------|----------|
| **No independent crypto audit** | High — required before production use | Budget $30K-$80K for audit | 2-4 months |
| **No revenue or customers** | High — no market validation | Seek design partners for POC | 3-6 months |
| **No SOC 2 / ISO 27001** | Medium — required for enterprise procurement | Begin certification process | 6-12 months |

---

## Technical Limitations

| Limitation | Impact | Explanation |
|------------|--------|-------------|
| **FIPS-aware but not certified** | Medium | Uses FIPS-approved algorithms but module not validated |
| **Side-channel-aware but not verified** | Medium | Basic protections exist, needs independent audit |
| **No production deployment** | Medium | Unproven at scale with real workloads |
| **Single developer** | Medium | Bus factor risk |
| **Benchmarks are local** | Low | Not measured on production cloud hardware |
| **No key recovery mechanism** | Low | By design (stateless), but may be required by some buyers |
| **Enterprise KMS requires license** | Low | AWS/Vault/Azure not in community edition |

---

## Market Limitations

| Limitation | Impact | Explanation |
|------------|--------|-------------|
| **PQC market is emerging** | Medium | Adoption still early, buyer education needed |
| **No brand recognition** | Medium | New project, no established reputation |
| **No integration partners** | Low | No consulting firms recommending the product |
| **No case studies** | Low | No production deployments to reference |

---

## What We Are NOT

| Claim | Status |
|-------|--------|
| FIPS certified | ❌ No |
| Formally verified | ❌ No |
| Side-channel proof | ❌ No |
| Production-proven | ❌ No |
| Revenue-generating | ❌ No |
| SOC 2 compliant | ❌ No |
| ISO 27001 certified | ❌ No |

---

## What We ARE

| Attribute | Status |
|-----------|--------|
| Working code | ✅ 139 passing tests |
| NIST-standardized algorithms | ✅ ML-KEM-768 (FIPS 203) |
| Stateless architecture | ✅ No user keys stored |
| Enterprise KMS | ✅ AWS, Azure, Vault |
| Two SDKs | ✅ Python + Go |
| CI/CD | ✅ GitHub Actions |
| Documentation | ✅ 20+ documents |
| Benchmarks | ✅ Automated, reproducible |
| Container hardening | ✅ Dockerfile.hardened |
| FIPS-aware | ✅ Uses approved algorithms |
| Side-channel-aware | ✅ Constant-time comparisons |

---

## Honest Transparency

This is a **pre-commercial technical asset** with:

- ✅ Working code
- ✅ Comprehensive documentation
- ✅ CI/CD pipeline
- ✅ Enterprise KMS integrations
- ✅ Automated benchmarks
- ✅ Container hardening

It does **not** have:

- ❌ Revenue or customers
- ❌ Independent cryptographic audit
- ❌ Production deployment history
- ❌ SOC 2 or ISO 27001 certification
- ❌ Bug bounty program
- ❌ Multiple developers

The project is ready for **POC, integration, acquisition, or further development**. It requires investment in audit, certification, and go-to-market to reach production readiness.

---

*This document is honest and transparent. No limitations are hidden or downplayed.*