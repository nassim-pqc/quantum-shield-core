# M&A Review — Quantum Shield Core

_Acting as CTO evaluating acquisition at €150,000 valuation_

## Executive Summary

Quantum Shield Core is a functional post-quantum cryptographic microservice with a clean architecture, working tests (139/139), and professional documentation. However, several issues must be addressed before acquisition. The estimated remediation cost is €15,000–€25,000 (2-4 weeks of development time).

**Verdict**: ACQUIRE WITH CONDITIONS — price adjustment of -€20,000 for remediation.

---

## Critical Issues (Block Acquisition)

| # | Issue | Impact | Remediation Cost | Recommendation |
|---|-------|--------|-----------------|----------------|
| C1 | No CI/CD pipeline | Cannot validate quality or regression | €4,000 | Require GitHub Actions pipeline before close |
| C2 | Rust `generate_keypair()` returns `Err` | Half the Rust module is unusable | €3,000 | Implement or document limitation |
| C3 | No documented secret rotation process | Operational risk for audit key | €2,000 | Document rotation procedure |
| C4 | 3 KMS provider stubs (AWS, Azure, Vault) | Would fail in production with non-local config | €5,000 | Remove or implement at least one |

## Important Issues (Negotiate Price)

| # | Issue | Impact | Remediation Cost |
|---|-------|--------|-----------------|
| I1 | `services/` directories empty | Suggests incomplete architecture | €1,000 |
| I2 | No `.env.example` | First-run friction for new developers | €500 |
| I3 | Rust `target/` directory in repo | CI artifact bloat | €500 |
| I4 | No container image published | Requires buyer to build Docker | €2,000 |
| I5 | `alembic/` migrations present but undocumented | Developer confusion | €1,000 |
| I6 | `benchmarks/BENCHMARK_RESULTS.md` and `BENCHMARK_REPORT.md` likely AI-generated | Damages technical credibility | €1,000 |
| I7 | Double Prometheus instrumentation | Redundant metrics, minor confusion | €500 |

## Minor Issues (Post-Acquisition Backlog)

| # | Issue | Impact | Remediation Cost |
|---|-------|--------|-----------------|
| M1 | `VERSION` file redundant with `constants.py` | Two sources of truth | €200 |
| M2 | `ruff.toml` vs missing `pyproject.toml` | Inconsistent config | €200 |
| M3 | `dashboard.html` without authentication | Security theater | €500 |
| M4 | No `.gitignore` for `__pycache__`/`.pytest_cache` | Artifact pollution | €100 |

## Security Assessment

| Category | Rating | Notes |
|----------|--------|-------|
| Cryptography | **Good** | NIST-standard ML-KEM-768 + AES-256-GCM, constant-time HMAC |
| Authentication | **Adequate** | SHA-256 hashed API keys, RBAC implemented |
| Audit Trail | **Good** | HMAC-SHA256 signed, key versioning, append-only |
| Transport Security | **Good** | HSTS, CSP, X-Frame-Options enforced |
| Memory Safety | **Good** | Rust core with panic-abort, borrow checker |
| Secret Management | **Weak** | AUDIT_KEY in env var, no documented rotation |
| CI/CD | **Missing** | No pipeline, no automated security scanning |
| Dependency Auditing | **Partial** | Tools listed but not integrated into CI |

## Dependency Analysis

| Dependency | Risk Level | Notes |
|-----------|------------|-------|
| `liboqs-python` 0.14.1 | **Medium** | C library dependency, version pinned |
| `cryptography` 42.0.7 | **Low** | Well-maintained, frequent releases |
| `rust-engine` deps (7 crates) | **Low** | Well-known crates, no GPL licenses |
| `fastapi` 0.111.0 | **Low** | Stable, active development |
| `opentelemetry-*` | **Low** | Standard instrumentation |

## License Assessment

- **MIT License**: Low risk, permissive
- `bitflags` (BSD-3-Clause), `cpufeatures` (Apache-2.0/MIT): All compatible
- No GPL or AGPL dependencies found
- `liboqs` is MIT licensed

## Operational Risk

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Single developer dependency | High | Critical | Require documentation + knowledge transfer |
| No published Docker image | Medium | High | Build and publish before close |
| No monitoring dashboard | Medium | Medium | Add Grafana dashboard template |
| No backup/restore procedure | Medium | High | Document in operations guide |

## Valuation Impact

| Factor | Adjustment |
|--------|-----------|
| Base valuation | €150,000 |
| No CI/CD pipeline | -€15,000 |
| KMS stubs | -€5,000 |
| Rust limitations | -€3,000 |
| Missing documentation/process | -€2,000 |
| **Adjusted valuation** | **€125,000** |

## Recommended Conditions

1. **Price adjustment**: -€20,000 (final offer €130,000)
2. **30-day escrow**: Developer must fix C1, C2, C4, I1, I2, I5
3. **Knowledge transfer**: 2 half-day sessions with the developer
4. **Source code warranty**: No undisclosed GPL dependencies
5. **IP assignment**: Clean chain of title for all contributions

---

_This review was conducted as a pre-acquisition technical due diligence. All findings are based on the repository state as of 31 May 2026._