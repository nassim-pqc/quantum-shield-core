# Public Documentation Index

> Index of technical documentation available in this repository.
> Generated during `repo-public-cleanup`.

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

## KMS Providers

| Document | Description |
|----------|-------------|
| [Azure Key Vault Guide](AZURE_KEY_VAULT_GUIDE.md) | Azure KMS integration |
| [Azure KMS Implementation Summary](AZURE_KMS_IMPLEMENTATION_SUMMARY.md) | Azure integration details |
| [Azure KMS Audit](AZURE_KMS_AUDIT.md) | Azure KMS audit findings |

## Performance

| Document | Description |
|----------|-------------|
| [Performance Benchmark Report](PERFORMANCE_BENCHMARK_REPORT.md) | Full benchmark methodology and results |
| [Performance Regression Guide](PERFORMANCE_REGRESSION_GUIDE.md) | How to detect regressions |
| [Performance Audit](PERFORMANCE_AUDIT.md) | Performance audit findings |

## SDK

| Document | Description |
|----------|-------------|
| [Go SDK Guide](GO_SDK_GUIDE.md) | Go SDK usage and examples |
| [Go SDK Implementation Summary](GO_SDK_IMPLEMENTATION_SUMMARY.md) | Go SDK design notes |
| [Go SDK Audit](GO_SDK_AUDIT.md) | Go SDK code review |
| [PyPI Release Guide](PYPI_RELEASE_GUIDE.md) | Publishing Python SDK to PyPI |

## API

| Document | Description |
|----------|-------------|
| [API Guide](API_GUIDE.md) | Full API reference |

## Cloud Validation

| Document | Description |
|----------|-------------|
| [AWS KMS Provider Audit](../evidence/cloud-validation/aws-kms/AWS_KMS_PROVIDER_AUDIT.md) | AWS KMS implementation audit |
| [AWS KMS Real Validation Summary](../evidence/cloud-validation/aws-kms/AWS_KMS_REAL_VALIDATION_SUMMARY.md) | Real AWS KMS validation |
| [AWS KMS Algorithm Fix Summary](../evidence/cloud-validation/aws-kms/AWS_KMS_ALGORITHM_FIX_SUMMARY.md) | Algorithm fix documentation |
| [AWS KMS Manual Setup Guide](../evidence/cloud-validation/aws-kms/AWS_KMS_MANUAL_SETUP_GUIDE.md) | Manual setup instructions |
| [AWS KMS CloudTrail Evidence](../evidence/cloud-validation/aws-kms/AWS_KMS_CLOUDTRAIL_EVIDENCE.md) | CloudTrail integration |

## Operations

| Document | Description |
|----------|-------------|
| [Deployment Guide](live-demo-deployment.md) | Running the service |
| [Environment Guide](ENV_GUIDE.md) | Environment variable reference |
| [Docker Guide](DOCKER_GUIDE.md) | Docker usage |
| [Observability Guide](OBSERVABILITY_GUIDE.md) | Metrics, tracing, logging |

## Limitations

- [Known Limitations](../README.md#known-limitations) (in README)