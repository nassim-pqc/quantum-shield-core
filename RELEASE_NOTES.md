# Release Notes — Quantum Shield Core v1.0.0 (Enterprise)

**Tag:** `v1.0.0`  
**Date:** 2026-05-28  
**Codename:** Enterprise GA

## Summary

First **public enterprise release** of Quantum Shield Core — a sovereign post-quantum cryptographic microservice with NIS2-ready audit trail, PostgreSQL persistence, and Docker-first deployment.

## Highlights

- **PQC:** ML-KEM-768 (Kyber768) hybrid encryption + AES-256-GCM with mandatory AAD
- **Audit:** HMAC-SHA256 append-only trail, key rotation, integrity verification on read
- **Ops:** Docker Compose, Alembic, Prometheus `/metrics`, JSON logs + correlation IDs
- **Commercial:** Benchmarks (1 KB / 1 MB / 10 MB), demo kit, live doc screenshots

## Upgrade from development builds

1. Copy `.env.example` → `.env` (replace all `REPLACE_WITH_*` values)
2. `docker compose up --build`
3. API version reported in `/health` is `1.0.0`

## Breaking changes

- API `version` field set to **1.0.0** (was 4.x during internal development)
- Repository must not contain `.env` or `.env.txt` — use `.env.example` only

## Security

- liboqs **0.14.0** + liboqs-python **0.14.1** (aligned)
- Non-root container, read-only FS, pinned dependencies
- Run `pip-audit` and `bandit` via CI before deploy

## Assets

| Path | Description |
|------|-------------|
| `demo/demo.sh` | Full API walkthrough |
| `benchmarks/BENCHMARK_RESULTS.md` | Performance tables |
| `docs/images/screenshot-*.png` | Live captures |

## Checksums

Build image locally: `docker compose build` → `quantum-shield:latest`

---

See [CHANGELOG.md](CHANGELOG.md) for full history.
