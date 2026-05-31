# ◈ Quantum Shield Core

[![CI](https://github.com/quantum-shield/core/actions/workflows/ci.yml/badge.svg)](https://github.com/quantum-shield/core/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-139%2F139-green)](tests/)
[![Security](https://img.shields.io/badge/security-bandit%20%7C%20pip--audit%20%7C%20semgrep-blue)](.github/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue)](Dockerfile)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)](pyproject.toml)
[![Rust](https://img.shields.io/badge/rust-stable-orange)](rust-engine/Cargo.toml)
[![ML-KEM](https://img.shields.io/badge/pqc-ML--KEM--768-purple)](docs/adr/001-ml-kem-768.md)

Enterprise post-quantum cryptographic microservice — **ML-KEM-768** (Kyber768) + **AES-256-GCM** hybrid encryption.

```text
┌──────────────┐     ┌─────────────────────────────────────────────┐
│  Client SDK  │────▶│         Quantum Shield Core API              │
│  (Python/Go) │     │  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
└──────────────┘     │  │  Rust     │  │  Python  │  │  Audit    │ │
                     │  │  Crypto   │  │  KEM     │  │  Store    │ │
                     │  │  Engine   │  │  (Kyber) │  │  (HMAC)   │ │
                     │  └──────────┘  └──────────┘  └───────────┘ │
                     └──────────────────────┬──────────────────────┘
                                            │
                                    ┌───────▼───────┐
                                    │   PostgreSQL  │
                                    │  (Audit Log)  │
                                    └───────────────┘
```

## Features

- **NIST-standard PQC**: ML-KEM-768 key encapsulation (FIPS 203) + AES-256-GCM (SP 800-38D)
- **Stateless**: No private keys stored server-side
- **Signed audit trail**: Append-only, HMAC-SHA256 with key rotation
- **Memory-safe**: Rust core engine (PyO3 bindings), panic-abort on release
- **Pluggable KMS**: Local env, AWS KSM, HashiCorp Vault, Azure Key Vault (stubs)
- **Observability**: Prometheus metrics, OpenTelemetry tracing, JSON logs
- **Rate limiting**: Per-IP rate limiting on all endpoints
- **2 SDKs**: [Python](sdk/), [Go](sdk-go/)

## Quick Start

```bash
# One Docker command
docker run -p 8000:8000 \
  -e AUDIT_KEY="your-32-byte-key-here-xxxxxxxxxxxxxxxx" \
  -e API_KEY_OPERATOR="my-operator-key" \
  ghcr.io/quantum-shield/core:latest

# Verify
curl http://localhost:8000/health
# → {"status":"healthy","algorithm":"Kyber768","version":"1.0.0"}

# Encrypt
curl -s -X POST http://localhost:8000/api/v1/keys/generate \
  -H "X-API-Key: my-operator-key" | jq .
```

Full deploy guide: [docs/live-demo-deployment.md](docs/live-demo-deployment.md)

## Interactive Demo

A live, browser-based demo is available at `/demo` when the service runs:

1. **Generate Keys** — creates an ML-KEM-768 key pair
2. **Encrypt (Seal)** — hybrid encrypts your message
3. **Decrypt (Unseal)** — recovers the original plaintext

The demo shows timing for each operation and handles errors gracefully.

## Architecture

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI (Python 3.12) | HTTP endpoints, validation, routing |
| Auth | SQLAlchemy + SHA-256 | API key hashing, RBAC |
| KEM | liboqs-python | ML-KEM-768 key encapsulation |
| AEAD | pyca/cryptography | AES-256-GCM with AAD |
| Rust | PyO3 | HMAC-SHA256, AES-GCM (constant-time) |
| Audit | PostgreSQL | Append-only signed log storage |
| Metrics | Prometheus | Crypto operations, request latency |
| Tracing | OpenTelemetry | W3C trace context, OTLP export |

## Performance Benchmarks

| Operation | Latency (avg) | Notes |
|-----------|--------------|-------|
| Key Generation | ~8 ms | ML-KEM-768 keypair |
| Seal (1 KB) | ~5 ms | Hybrid encrypt |
| Seal (1 MB) | ~12 ms | Hybrid encrypt |
| Audit Log | ~3 ms | HMAC sign + store |

Run reproducible benchmarks locally: `bash scripts/benchmark.sh --md`

Full methodology: [docs/benchmarks/latest.md](docs/benchmarks/latest.md)

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
- **Side-channels**: Constant-time HMAC comparison, opaque unseal errors
- **Memory**: Rust borrow checker, `panic = "abort"` in release

Full security posture: [evidence-pack/security-overview.md](evidence-pack/security-overview.md)  
Threat model: [docs/security/threat-model.md](docs/security/threat-model.md)

## SDKs

- **Python**: `sdk/client.py` — typed async client with retry logic
- **Go**: `sdk-go/` — idiomatic Go client with rate limiting, functional options

Both SDKs support all API endpoints.

## Evidence Pack

The [evidence-pack/](evidence-pack/) directory contains verifiable documentation:

- [Architecture Summary](evidence-pack/architecture-summary.md)
- [Security Overview](evidence-pack/security-overview.md)
- [Test Summary](evidence-pack/test-summary.md)
- [Benchmark Results](evidence-pack/benchmark-results.md)
- [Dependency Audit](evidence-pack/dependency-audit.md)
- [License Review](evidence-pack/license-review.md)
- [Index](evidence-pack/index.md)

## Roadmap

- CI/CD pipeline automation (GitHub Actions)
- PyPI package publication for Python SDK
- KMS provider implementations (AWS, Vault, Azure)
- Rust native ML-KEM-768 via liboqs-sys
- Hash-chain verification for audit trail

## Documentation

- [API Guide](docs/API_GUIDE.md)
- [Architecture](docs/architecture/overview.md)
- [Architecture decisions](docs/adr/)
- [Security guide](docs/SECURITY_GUIDE.md)
- [Deployment guide](docs/live-demo-deployment.md)
- [Environment guide](docs/ENV_GUIDE.md)
- [Docker guide](docs/DOCKER_GUIDE.md)

## License

MIT — see [LICENSE](LICENSE).