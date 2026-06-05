# Quantum Shield Core

[![CI](https://github.com/quantum-shield/core/actions/workflows/ci.yml/badge.svg)](https://github.com/quantum-shield/core/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](requirements.txt)
[![Rust](https://img.shields.io/badge/rust-compiled-orange)](rust-engine/Cargo.toml)
[![ML-KEM](https://img.shields.io/badge/pqc-ML--KEM--768-purple)](docs/adr/001-ml-kem-768.md)

Post-quantum cryptographic microservice implementing **ML-KEM-768** (FIPS 203 / Kyber768) + **AES-256-GCM** hybrid encryption.

## Current Status

This project is **pre-production** and **pre-commercial**. The core encryption engine is implemented and tested (139 unit tests), but it has not undergone an independent cryptographic audit, has no production deployment track record, and has no revenue. It is suitable for evaluation, POC, and integration testing.

## Features

- ML-KEM-768 key encapsulation (via liboqs-python)
- AES-256-GCM symmetric encryption (via pyca/cryptography)
- Stateless architecture — no private keys stored server-side
- Signed audit trail — append-only, HMAC-SHA256 with key rotation
- Rust core engine — memory-safe HMAC-SHA256, constant-time operations (PyO3 bindings, panic=abort in release)
- Pluggable KMS providers — local env, AWS KMS, HashiCorp Vault, Azure Key Vault
- Observability — Prometheus metrics, OpenTelemetry tracing, JSON structured logging
- Rate limiting — per-IP rate limiting on all endpoints
- SDKs — Python and Go

## Quick Start

```bash
# Docker
docker run -p 8000:8000 \
  -e AUDIT_KEY="your-32-byte-key-here-xxxxxxxxxxxxxxxx" \
  -e API_KEY_OPERATOR="my-operator-key" \
  ghcr.io/quantum-shield/core:latest

# Verify
curl http://localhost:8000/health

# Encrypt
curl -s -X POST http://localhost:8000/api/v1/keys/generate \
  -H "X-API-Key: my-operator-key"
```

Full deploy guide: [docs/live-demo-deployment.md](docs/live-demo-deployment.md)

## Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI (Python 3.12) | HTTP endpoints, validation, routing |
| Auth | SQLAlchemy + SHA-256 | API key hashing, RBAC |
| KEM | liboqs-python | ML-KEM-768 key encapsulation |
| AEAD | pyca/cryptography | AES-256-GCM with AAD |
| Rust | PyO3 | HMAC-SHA256, AES-GCM (constant-time) |
| Audit | PostgreSQL | Append-only signed log storage |
| Metrics | Prometheus | Operations count, latency |
| Tracing | OpenTelemetry | W3C trace context, OTLP export |

## Performance Benchmarks

| Operation | Latency (avg) | Notes |
|-----------|--------------|-------|
| Key Generation | ~8 ms | ML-KEM-768 keypair |
| Seal (1 KB) | ~5 ms | Hybrid encrypt |
| Seal (1 MB) | ~12 ms | Hybrid encrypt |
| Audit Log | ~3 ms | HMAC sign + store |

Run locally: `bash scripts/benchmark.sh --md`  
Full methodology: [docs/PERFORMANCE_BENCHMARK_REPORT.md](docs/PERFORMANCE_BENCHMARK_REPORT.md)

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Liveness + DB health |
| POST | `/api/v1/keys/generate` | operator | Generate Kyber768 keypair |
| POST | `/api/v1/crypto/seal` | operator | Hybrid encrypt |
| POST | `/api/v1/crypto/unseal` | operator | Hybrid decrypt |
| POST | `/api/v1/audit/log` | operator/auditor | Append audit log |
| GET | `/api/v1/audit/logs` | operator/auditor | List audit logs |
| GET | `/api/v1/audit/logs/{id}` | operator/auditor | Get log by ID |
| GET | `/api/v1/audit/stats` | operator/auditor | Log statistics |
| GET | `/metrics` | None | Prometheus metrics |

Full API docs: [docs/API_GUIDE.md](docs/API_GUIDE.md)

## Security

- **Authentication**: API key (SHA-256 hashed) via `X-API-Key` header
- **Authorization**: RBAC with `operator` and `auditor` roles
- **Transport**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options enforced
- **Audit**: HMAC-SHA256 signed logs with key versioning
- **Side-channel awareness**: Constant-time HMAC comparison, opaque unseal errors (not verified by independent audit)
- **Memory safety**: Rust borrow checker, `panic = "abort"` in release
- **Container hardening**: [docs/CONTAINER_HARDENING.md](docs/CONTAINER_HARDENING.md)

Threat model: [docs/security/threat-model.md](docs/security/threat-model.md)

## SDKs

- **Python**: `sdk/client.py` — typed async client with retry logic  
  See [sdk/](sdk/)
- **Go**: `sdk-go/` — idiomatic Go client with rate limiting, functional options  
  See [sdk-go/](sdk-go/)

## Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No independent crypto audit | Required before production use | Budget $30K–$80K for audit |
| No production revenue or customers | No market validation yet | POC / design partners |
| No SOC 2 / ISO 27001 | Required for enterprise procurement | 6–12 month certification process |
| No bug bounty program | No external security feedback | Establish program |
| Single developer | Bus factor risk | Hire or acquire team |

## Validation

- 139 unit tests (pytest)
- Ruff linting (all checks passing)
- Go SDK tests + vet (all passing)
- Docker build + hardening
- Benchmarks reproducible locally
- Cloud validation documentation in [evidence/cloud-validation/](evidence/cloud-validation/)

## Roadmap

- Independent cryptographic audit
- PyPI package publication for Python SDK
- Rust-native ML-KEM-768 via liboqs-sys
- Hash-chain verification for audit trail
- Additional SDKs (Rust, Java, Node.js)

## Documentation

- [API Guide](docs/API_GUIDE.md)
- [Architecture](docs/architecture/overview.md)
- [Architecture decisions](docs/adr/)
- [Security guide](docs/SECURITY_GUIDE.md)
- [Deployment guide](docs/live-demo-deployment.md)
- [Environment guide](docs/ENV_GUIDE.md)
- [Docker guide](docs/DOCKER_GUIDE.md)
- [Performance benchmarks](docs/PERFORMANCE_BENCHMARK_REPORT.md)
- [Container hardening](docs/CONTAINER_HARDENING.md)
- [FIPS readiness](docs/FIPS_READINESS.md) (FIPS-aware, not certified)
- [Side-channel readiness](docs/SIDE_CHANNEL_READINESS.md) (not verified)

## License

MIT — see [LICENSE](LICENSE).