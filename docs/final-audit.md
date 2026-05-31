# Final Audit — Quantum Shield Core

_Generated: 31 May 2026_

## Critical Issues

| # | Issue | File | Impact |
|---|-------|------|--------|
| C1 | `services/audit/` and `services/crypto/` directories empty | `services/` | Dead code structure, 0 value |
| C2 | Rust `generate_keypair()` always returns `Err` | `rust-engine/src/lib.rs:158` | Rust PQC not usable directly |
| C3 | `AUDIT_KEY` loaded from env var, no encryption at rest | Security posture | Secret management not documented for prod |
| C4 | 3 KMS provider stubs (AWS, Azure, Vault) not implemented | `providers/kms/` | Would fail if switched from "local" |
| C5 | No CI/CD pipeline defined | Root | Cannot validate quality consistently |

## Important Issues

| # | Issue | File | Impact |
|---|-------|------|--------|
| I1 | `benchmarks/BENCHMARK_RESULTS.md` and `BENCHMARK_REPORT.md` likely AI-generated | `benchmarks/` | Not reproducible, damages credibility |
| I2 | Rust bench is `1 + 1` placeholder | `rust-engine/benches/crypto_bench.rs` | Not a real benchmark |
| I3 | `prev_entry_hash`/`entry_hash` fields never populated by hash chain | `models.py:54-55` | Unused schema complexity |
| I4 | `FINAL_REPORT.md`, `TECHNICAL_DUE_DILIGENCE.md`, `DOSSIER_VENTE.md` in root | Root | Not structured for discovery |
| I5 | Double Prometheus instrumentation (Instrumentator + REQUEST_LATENCY) | `observability/metrics.py` + main.py | Redundant metrics |
| I6 | `alembic/` migrations present but not referenced in docs | `alembic/` | Developer confusion |
| I7 | No `.env.example` file | Root | First-run friction |
| I8 | SDK Python examples in French only | `sdk/examples/` | Limits international audience |

## Minor Issues

| # | Issue | File | Impact |
|---|-------|------|--------|
| M1 | `example_integration.py` in root should be in `demo/` | Root | Organizational |
| M2 | 8 documentation files in root (`CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, etc.) | Root | Bloated for a 2-file Python project |
| M3 | `dashboard.html` exists but `/dashboard` endpoint serves static HTML | Root | Unclear value, no authentication |
| M4 | Rust `target/` directory committed (.gitignore may catch it) | `rust-engine/target/` | CI artifact pollution |
| M5 | `ruff.toml` exists but no `pyproject.toml` | Root | Inconsistent config layout |
| M6 | `VERSION` file redundant with `constants.py API_VERSION` | Root | Two sources of truth |
| M7 | No `.gitignore` references to `.pytest_cache/` or `__pycache__/` | `.gitignore` | Artifact leaks |