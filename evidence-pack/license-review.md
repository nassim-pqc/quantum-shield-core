# License Review — Quantum Shield Core

_Generated from repository state on 31 May 2026_

## Project License

- **License**: MIT
- **Commercial use**: Fully permitted (SaaS, reselling, OEM embedding)

## Dependency Licenses

All Python and Rust dependencies use permissive licenses (MIT, Apache-2.0, BSD-3-Clause). Zero GPL/AGPL/LGPL/SSPL found.

### Python (requirements.txt)

| Dependency | License | Commercial OK |
|-----------|---------|---------------|
| fastapi | MIT | ✅ |
| uvicorn | BSD-3-Clause | ✅ |
| pydantic | MIT | ✅ |
| cryptography | Apache-2.0 / BSD | ✅ |
| liboqs-python | MIT | ✅ |
| sqlalchemy | MIT | ✅ |
| asyncpg | Apache-2.0 | ✅ |
| prometheus-client | Apache-2.0 | ✅ |
| opentelemetry-* | Apache-2.0 | ✅ |
| boto3 | Apache-2.0 | ✅ |

### Rust (Cargo.toml)

| Crate | License | Commercial OK |
|-------|---------|---------------|
| aes-gcm | Apache-2.0 / MIT | ✅ |
| sha2 | MIT / Apache-2.0 | ✅ |
| hmac | MIT / Apache-2.0 | ✅ |
| serde | MIT / Apache-2.0 | ✅ |
| pyo3 | Apache-2.0 | ✅ |

## Compliance Summary

- Zero copyleft dependencies
- SaaS hosting fully permitted
- OEM embedding fully permitted
- White-label/resell fully permitted

_This review is based on pinned dependency versions. Re-run with `pip-audit` and `cargo audit` after updates._