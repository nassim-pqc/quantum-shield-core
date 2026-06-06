# Changelog

All notable changes to **Quantum Shield Core** follow [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-05-28 — First public release (pre-production)

First public, pre-production release.

### Added
- Release packaging: `RELEASE_NOTES.md`, `scripts/validate_release.sh`
- Demo kit: `demo.sh`, walkthrough, Swagger tour, curl examples
- Landing page, observability package, KMS providers (AWS, Vault, Azure)

### Security
- No secrets in repository — `.env.example` placeholders only
- liboqs 0.14.0 aligned with liboqs-python 0.14.1
- CI: Ruff, Black, pytest, Bandit, pip-audit, Docker build

### Changed
- Product version unified to **1.0.0** (API, VERSION file, release tag)
- Branding: **Quantum Shield Core** everywhere

## [0.9.0] — 2026-05-28 — Pre-release (internal)

### Added
- PostgreSQL async, Alembic migrations, append-only audit with hash-chain fields
- Prometheus custom metrics, OpenTelemetry hooks, correlation IDs

### Changed
- Docker multi-stage build, non-root runtime, resource limits

## [0.1.0] — Initial

- ML-KEM-768 hybrid API, HMAC audit trail, RBAC API keys, SQLite/PostgreSQL support
