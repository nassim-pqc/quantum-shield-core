# Dependency Audit — Quantum Shield Core

_Generated from repository state on 31 May 2026_

## Python Dependencies (requirements.txt)

| Dependency | Version | Risk | License | Notes |
|-----------|---------|------|---------|-------|
| fastapi | 0.111.0 | Low | MIT | Stable, active |
| uvicorn | 0.30.1 | Low | BSD-3-Clause | Standard ASGI server |
| pydantic | 2.7.4 | Low | MIT | Core data validation |
| cryptography | 42.0.7 | Low | Apache-2.0 / BSD | Well-maintained, frequent releases |
| liboqs-python | 0.14.1 | Medium | MIT | C library dependency, pin required |
| sqlalchemy | 2.0.31 | Low | MIT | Mature ORM |
| aiosqlite | 0.20.0 | Low | MIT | Async SQLite driver |
| asyncpg | 0.29.0 | Low | Apache-2.0 | PostgreSQL async driver |
| slowapi | 0.1.9 | Low | MIT | Rate limiting |
| prometheus-client | 0.20.0 | Low | Apache-2.0 | Metrics standard |
| opentelemetry-* | 1.25.0 | Low | Apache-2.0 | CNCF standard |
| boto3 | 1.34.128 | Low | Apache-2.0 | AWS SDK (optional) |
| python-dotenv | 1.0.1 | Low | BSD-3-Clause | Env file loading |

## Rust Dependencies (Cargo.toml)

| Crate | Version | Risk | License |
|-------|---------|------|---------|
| aes-gcm | 0.10 | Low | Apache-2.0 / MIT |
| rand | 0.8 | Low | MIT / Apache-2.0 |
| sha2 | 0.10 | Low | MIT / Apache-2.0 |
| hmac | 0.12 | Low | MIT / Apache-2.0 |
| serde | 1.x | Low | MIT / Apache-2.0 |
| serde_json | 1.x | Low | MIT / Apache-2.0 |
| thiserror | 1.x | Low | MIT / Apache-2.0 |
| pyo3 | 0.21 | Low | Apache-2.0 |
| hex | 0.4 | Low | MIT / Apache-2.0 |

## License Compliance

- No GPL, AGPL, or LGPL dependencies found
- All licenses are MIT, Apache-2.0, BSD-3-Clause, or dual MIT/Apache-2.0
- Project license: MIT (see LICENSE file)
- Fully compatible with commercial use, redistribution, and SaaS hosting

## Security Alerts

- Python: No known vulnerabilities at pinned versions (verified via pip-audit)
- Rust: No known advisories at pinned versions (verified via cargo-audit)
- liboqs: Monitor for CVE updates (C library, well-maintained by OQS team)

_This audit was generated from the repository. Run `pip-audit` and `cargo audit` locally for the latest results._