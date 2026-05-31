# Evidence Pack — Quantum Shield Core

_Generated: 31 May 2026_

This directory contains verifiable documentation generated from the repository. All data is derived from the actual codebase and can be independently verified.

## Contents

| Document | Description | Verification |
|----------|-------------|--------------|
| [Security Overview](security-overview.md) | Cryptographic standards, headers, auth, audit | `security_engine.py`, `main.py` |
| [Architecture Summary](architecture-summary.md) | Component stack, data flow, diagram | `docs/architecture/overview.md` |
| [Test Summary](test-summary.md) | 139 tests, all passing | `pytest tests/ -v` |
| [Benchmark Results](benchmark-results.md) | Reproducible performance numbers | `bash scripts/benchmark.sh` |
| [Dependency Audit](dependency-audit.md) | All dependencies, versions, licenses | `pip-audit`, `cargo audit` |
| [License Review](license-review.md) | License compliance for all components | `LICENSE` + crate metadata |

## Quick Verification

```bash
# Clone and verify tests pass
git clone https://github.com/quantum-shield/core && cd core
pytest tests/ -v          # 139/139

# Run benchmarks
bash scripts/benchmark.sh # Produces JSON + Markdown

# Audit Python dependencies
pip install pip-audit && pip-audit

# Lint
ruff check .

# Bandit SAST
bandit -r . --skip B101,B404,B603,B607
```

## Integrity

- No synthetic data in any document
- No invented metrics or client references
- All numbers are from real tests and benchmarks
- All dependencies are from `requirements.txt` and `Cargo.toml`

---

_This pack is designed for CTO, RSSI, and M&A technical due diligence review._