# Public Documentation Index

> Index of technical documentation in this repository.

## Architecture

| Document | Description |
|----------|-------------|
| [Architecture Overview](architecture/overview.md) | System design, layers, data flow |
| [ADR index](adr/) | Architecture Decision Records (ML-KEM, Rust, AES-GCM, microservice) |
| [System Architecture](SYSTEM_ARCHITECTURE.md) | Detailed architecture description |
| [Stateless Explanation](../evidence/STATELESS_EXPLANATION.md) | Why no private keys are stored server-side |

## Security

| Document | Description |
|----------|-------------|
| [Security Guide](SECURITY_GUIDE.md) | Authentication, authorization, transport security |
| [Threat Model](security/threat-model.md) | Threat modeling and mitigations |
| [FIPS Readiness](FIPS_READINESS.md) | FIPS-aware design (not certified) |
| [Side-channel Readiness](SIDE_CHANNEL_READINESS.md) | Side-channel-aware design (not verified) |
| [Container Hardening](CONTAINER_HARDENING.md) | Docker hardening configuration |
| [HKDF Key Derivation](HKDF_KEY_DERIVATION_UPDATE.md) | AES key derivation via HKDF-SHA256 |
| [Rust Fallback & Docs CSP](RUST_FALLBACK_AND_DOCS_CSP_UPDATE.md) | Operational logging + CSP notes |

## KMS Providers

| Document | Description |
|----------|-------------|
| [Azure Key Vault Guide](AZURE_KEY_VAULT_GUIDE.md) | Azure KMS integration |
| [Azure Key Vault Validation Fix](AZURE_KEY_VAULT_REAL_VALIDATION_FIX.md) | Wrap-algorithm enum fix + real validation |

## Performance

| Document | Description |
|----------|-------------|
| [Performance Benchmark Report](PERFORMANCE_BENCHMARK_REPORT.md) | Full benchmark methodology and results |
| [Performance Regression Guide](PERFORMANCE_REGRESSION_GUIDE.md) | How to detect regressions |

## SDK

| Document | Description |
|----------|-------------|
| [Go SDK Guide](GO_SDK_GUIDE.md) | Go SDK usage and examples |
| [PyPI Release Guide](PYPI_RELEASE_GUIDE.md) | Publishing Python SDK to PyPI |

## API

| Document | Description |
|----------|-------------|
| [API Guide](API_GUIDE.md) | Full API reference |

## Cloud Validation

| Document | Description |
|----------|-------------|
| [Azure Key Vault — Real Validation](../evidence/cloud-validation/azure/AZURE_KEY_VAULT_REAL_VALIDATION.md) | Validated against a real Azure Key Vault test environment |
| [HashiCorp Vault — Real Local Validation](../evidence/cloud-validation/vault/VAULT_REAL_LOCAL_VALIDATION.md) | Validated against a real local Vault dev server (Docker) |
| [AWS KMS — Real Cloud Validation](../evidence/cloud-validation/aws-kms/AWS_KMS_REAL_CLOUD_VALIDATION.md) | Validated against a real AWS KMS test key (CLI + provider roundtrip) — PASS |
| [AWS KMS — Provider Audit](../evidence/cloud-validation/aws-kms/AWS_KMS_PROVIDER_AUDIT.md) | AWS KMS provider source audit |
| [AWS KMS — Manual Setup Guide](../evidence/cloud-validation/aws-kms/AWS_KMS_MANUAL_SETUP_GUIDE.md) | Setup steps to reproduce the real AWS validation |

## Operations

| Document | Description |
|----------|-------------|
| [Deployment Guide](live-demo-deployment.md) | Running the service |
| [Environment Guide](ENV_GUIDE.md) | Environment variable reference |
| [Docker Guide](DOCKER_GUIDE.md) | Docker usage |
| [Observability Guide](OBSERVABILITY_GUIDE.md) | Metrics, tracing, logging |

## Limitations

- [Known Limitations](../README.md#known-limitations) (in README)