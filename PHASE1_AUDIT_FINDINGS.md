# PHASE 1 — Audit de Crédibilité

## Issues détectés (classés par sévérité)

### CRITICAL
1. **Tests broken** — `conftest.py` uses `:memory:` with `NullPool` → each connection gets a new DB. Fixed with temp file.
2. **`test_x_frame_options_deny`** — uses broken inline if/else that doesn't evaluate.
3. **Empty `services/crypto/` and `services/audit/`** — directories exist but are dead.
4. **Rust benchmark** — `crypto_bench.rs` does `1 + 1` (placeholder, never replaced).

### HIGH
5. **Stub KMS providers** — `aws_kms.py`, `azure_kms.py`, `vault_kms.py` are likely unimplemented stubs.
6. **Duplicate tests** — `test_security.py` largely duplicates `test_api.py`.
7. **`_StrEnum` in `constants.py`** — unnecessary when Python 3.11+ `StrEnum` exists.
8. **HSTS condition in middleware** — conditionally adds HSTS based on scheme, but test expects it always.

### MEDIUM
9. **43 files of documentation** — far too many for the project size: `FINAL_REPORT.md`, `TECHNICAL_DUE_DILIGENCE.md`, `CHANGELOG.md`, `RELEASE_NOTES.md`, `DOSSIER_VENTE.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`.
10. **`Pillow` in `requirements-dev.txt`** — not used anywhere in the project.
11. **`black` in `requirements-dev.txt`** — ruff replaces both linting and formatting.
12. **`VERSION` file** — single line version, should be in code or pyproject.toml.
13. **`example_integration.py`** — belongs in `demo/` or `docs/`, not root.

### LOW
14. **Over-documented files** — every single file has a verbose docstring; some are useful, many are noise.
15. **`ruff.toml` exists but no pyproject.toml** — inconsistent config layout.
16. **`prometheus-fastapi-instrumentator`** + `REQUEST_LATENCY` histogram — double instrumentation.
17. **`import hashlib` in `security_engine.py`** — unused (HMAC is used, not hashlib directly).
18. **`models.py` has `prev_entry_hash`/`entry_hash` fields** — documented as "future hash-chain" but never used.
19. **`IntegrityDisplay` uses emoji** — `🛡️ OK` / `🚨 FAIL` — unprofessional for an API response.
20. **`benchmarks/BENCHMARK_RESULTS.md` and `BENCHMARK_REPORT.md`** — likely AI-generated.