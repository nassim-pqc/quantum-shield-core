# Final Due Diligence — Quantum Shield Core

_Reviewed: 31 May 2026 | Reviewer: External CTO_

## CRITIQUE

| # | Issue | Impact | Risk | Correction |
|---|-------|--------|------|------------|
| C1 | No published Docker image on GHCR | Buyer cannot deploy in 1 click | High | Push image to ghcr.io after CI runs on main |
| C2 | KMS providers for AWS/Azure/Vault are stubs | Switching from "local" env vars would fail | Medium | Implement or clearly remove |
| C3 | Rust `generate_keypair()` always returns `Err` | Rust engine cannot generate PQC keys | Medium | Document as "Python-only KEM", remove Err |
| C4 | `services/crypto/` and `services/audit/` are empty dirs | Looks like abandoned planned code | Low | Delete directories |

## IMPORTANT

| # | Issue | Impact | Risk | Correction |
|---|-------|--------|------|------------|
| I1 | `benchmarks/BENCHMARK_RESULTS.md` and `BENCHMARK_REPORT.md` are AI-generated | Damages credibility on close inspection | Medium | Delete or mark as draft |
| I2 | `prev_entry_hash`/`entry_hash` fields in AuditLog never used | Unused schema complexity | Low | Remove or implement hash chain |
| I3 | No `pyproject.toml` — config via `ruff.toml` and `requirements.txt` | Inconsistent project layout | Low | Create pyproject.toml |
| I4 | `VERSION` file duplicates `API_VERSION` in `constants.py` | Two sources of truth | Low | Delete VERSION |
| I5 | Rust `target/` directory in repo | Build artifacts committed | Low | Add to `.gitignore` |
| I6 | No `.env.example` file | Friction for first-time developers | Low | Create .env.example |
| I7 | `sdk/examples/` are in French only | Limits international adoption | Low | English comments |

## MINEUR

| # | Issue | Impact | Risk | Correction |
|---|-------|--------|------|------------|
| M1 | `alembic/` migrations present but never referenced | Dead configuration | None | Document or delete |
| M2 | `dashboard.html` served at `/dashboard` without auth | Minor information leak | Low | Add auth or remove |
| M3 | `TECHNICAL_DUE_DILIGENCE.md` is root marketing doc | Confusion with technical docs | None | Move to sales/ or delete |
| M4 | `DOSSIER_VENTE.md` is a sales doc in root | Confusion with technical docs | None | Move to sales/ or delete |

## Overall Assessment

| Category | Rating | Evidence |
|----------|--------|----------|
| Code quality | **Good** | 139 tests passing, clean Rust core |
| Security | **Good** | NIST-standard crypto, RBAC, signed audit |
| Architecture | **Good** | Stateless, pluggable KMS, proper separation |
| Documentation | **Good** | ADR, threat model, deployment guide, evidence pack |
| CI/CD | **Present** | GitHub Actions with lint, security, tests, Docker, Helm |
| Deployment | **Good** | Docker, Docker Compose, Helm chart |
| Packaging | **Incomplete** | No PyPI, no published Docker image |
| Maintenance | **Unknown** | Single developer, no public activity |

**Verdict: PROCEED with minor remediations (C1, C2, I1, I4, I6, M4)**

Estimated remediation: 2-4 hours of development work.