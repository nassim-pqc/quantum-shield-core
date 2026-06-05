# Quantum Shield Core — Proof of Usage

> **Purpose**: Verifiable evidence that the project works  
> **Audience**: Technical buyers, due diligence reviewers  
> **Date**: June 2026

---

## 1. CI/CD Evidence

### GitHub Actions Pipeline

| Job | Tool | Status |
|-----|------|--------|
| Lint (Python) | Ruff check + format | ✅ Passing |
| Security (Python) | Bandit SAST + Semgrep | ✅ Configured |
| Tests (Python 3.11) | pytest | ✅ 139 tests passing |
| Tests (Python 3.12) | pytest | ✅ 139 tests passing |
| Rust Build | cargo build + test | ✅ Configured |
| Docker Build | Multi-stage build | ✅ Configured |
| Helm Lint | Chart validation | ✅ Configured |

**Verification**: Check GitHub Actions badges in README.md

---

## 2. Test Evidence

### Python Tests

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_api.py` | API endpoint tests | Full endpoint coverage |
| `test_security_engine.py` | Crypto engine tests | Encrypt/decrypt/sign/verify |
| `test_kms_providers.py` | KMS provider tests | All KMS providers |
| `test_azure_kms.py` | Azure KMS tests | Azure-specific logic |
| `test_audit_store.py` | Audit store tests | CRUD operations |
| `test_auth.py` | Authentication tests | Auth and RBAC |
| `test_database.py` | Database tests | DB connectivity |
| `test_constants.py` | Constants tests | Enum values |
| `test_security.py` | Security tests | Headers, rate limiting |

**Total**: 139 tests (all passing)

### Go SDK Tests

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `client_test.go` | Client tests | HTTP client, retries |
| `types_test.go` | Types tests | Data structures |
| `validate_test.go` | Validation tests | Input validation |
| `config_test.go` | Config tests | Configuration |

**Verification**: `cd sdk-go && go test ./...`

---

## 3. Benchmark Evidence

### Automated Benchmarks

```bash
python scripts/run_performance_benchmarks.py --iterations 30
```

| Operation | Mean (ms) | P95 (ms) | P99 (ms) | Ops/sec |
|-----------|-----------|----------|----------|---------|
| Key Generation | 0.01 | 0.02 | 0.02 | 66,871 |
| Seal (1 KB) | 0.20 | 0.92 | 1.47 | 4,880 |
| Seal (1 MB) | 0.37 | 0.74 | 0.83 | 2,729 |
| Unseal (1 KB) | 0.03 | 0.04 | 0.05 | 32,944 |
| Unseal (1 MB) | 0.38 | 0.51 | 0.54 | 2,620 |
| Audit Write | 0.06 | 0.25 | 0.40 | 18,330 |
| Audit Verify | 0.00 | 0.01 | 0.01 | 244,906 |

**Verification**: Run `python scripts/run_performance_benchmarks.py`

### Regression Detection

```bash
python scripts/compare_performance.py \
  --baseline benchmarks/performance/baseline.json \
  --current benchmarks/performance/results.json
```

**Verification**: Run the comparison script

---

## 4. Documentation Evidence

| Document | Location | Purpose |
|----------|----------|---------|
| Performance Audit | `docs/PERFORMANCE_AUDIT.md` | Existing tooling inventory |
| Benchmark Report | `docs/PERFORMANCE_BENCHMARK_REPORT.md` | Performance characteristics |
| Regression Guide | `docs/PERFORMANCE_REGRESSION_GUIDE.md` | Regression detection |
| Container Hardening | `docs/CONTAINER_HARDENING.md` | Security posture |
| FIPS Readiness | `docs/FIPS_READINESS.md` | Compliance assessment |
| Side-Channel | `docs/SIDE_CHANNEL_READINESS.md` | Security assessment |
| API Guide | `docs/API_GUIDE.md` | API documentation |
| Architecture | `docs/architecture/overview.md` | System design |
| Security Guide | `docs/SECURITY_GUIDE.md` | Security practices |
| Threat Model | `docs/security/threat-model.md` | Threat analysis |
| ADRs | `docs/adr/` | Architecture decisions |

---

## 5. KMS Evidence

### 5.1 Provider Implementations

| Provider | File | Status | Features |
|----------|------|--------|----------|
| Local Environment | `security_engine.py` | Working | Env variable keys |
| AWS KMS | `providers/kms/aws_kms.py` | Implemented | DEK wrapping, retry |
| HashiCorp Vault | `providers/kms/vault_kms.py` | Implemented | Transit Engine, KV v2 |
| Azure Key Vault | `providers/kms/azure_kms.py` | Implemented | Key wrapping, Identity auth |

### 5.2 AWS KMS Real Cloud Validation

| Evidence | Status | Detail |
|----------|--------|--------|
| Provider audit | ✅ Completed | Full source code audit in `evidence/cloud-validation/aws-kms/` |
| Setup guide | ✅ Created | `AWS_KMS_MANUAL_SETUP_GUIDE.md` |
| Validation script | ✅ Created | `scripts/validate_real_aws_kms.py` |
| Real AWS KMS encrypt/decrypt | ❌ Not executed | Requires AWS CLI + credentials |
| Real AWS KMS health check | ❌ Not executed | Requires AWS CLI + credentials |
| CloudTrail evidence | ❌ Not available | Requires AWS CLI + credentials |

**Note**: AWS KMS provider code is implemented and tested with mocks. Real AWS validation was not executed because AWS credentials were not available in the local environment.

---

## 6. Container Evidence

| Feature | Status | Location |
|---------|--------|----------|
| Multi-stage build | ✅ | `Dockerfile` |
| Non-root user | ✅ | `Dockerfile` (appuser:8888) |
| Health check | ✅ | `Dockerfile` |
| Capabilities dropped | ✅ | `docker-compose.yml` (cap_drop: ALL) |
| Read-only filesystem | ✅ | `docker-compose.yml` (read_only: true) |
| Hardened Dockerfile | ✅ | `Dockerfile.hardened` |

---

## 7. SDK Evidence

### Python SDK

| Feature | Status |
|---------|--------|
| Health check | ✅ `client.health()` |
| Key generation | ✅ `client.generate_keypair()` |
| Seal (encrypt) | ✅ `client.seal()` |
| Unseal (decrypt) | ✅ `client.unseal()` |
| File encrypt/decrypt | ✅ `seal_file()` / `unseal_to_file()` |
| Audit log write | ✅ `client.write_audit_log()` |
| Audit log read | ✅ `client.get_audit_logs()` |
| Error handling | ✅ `QuantumShieldError` |

### Go SDK

| Feature | Status |
|---------|--------|
| Health check | ✅ `c.Health(ctx)` |
| Key generation | ✅ `c.GenerateKeypair(ctx)` |
| Seal (encrypt) | ✅ `c.Seal(ctx, ...)` |
| Unseal (decrypt) | ✅ `c.Unseal(ctx, ...)` |
| Text encrypt/decrypt | ✅ `SealText()` / `UnsealText()` |
| Audit log write | ✅ `c.WriteAuditLog(ctx, ...)` |
| Rate limiting | ✅ `golang.org/x/time/rate` |
| TLS 1.2+ | ✅ Configurable cipher suites |

---

## 8. Evidence Pack

Complete evidence package available at `evidence/`:

| Document | Purpose |
|----------|---------|
| `evidence/README.md` | Project overview and verification |
| `evidence/PROOF_OF_USAGE_REPORT.md` | Full technical evidence |
| `evidence/BUYER_ONE_PAGER.md` | Executive summary |
| `evidence/VIDEO_DEMO_SCRIPT.md` | Video script |
| `evidence/DEMO_COMMANDS.md` | Demo commands |
| `evidence/SCREENSHOT_CHECKLIST.md` | Screenshot guide |
| `evidence/STATELESS_EXPLANATION.md` | Architecture explained |

---

## 9. Remaining Limitations

| Limitation | Impact |
|------------|--------|
| No independent crypto audit | Cannot guarantee cryptographic correctness |
| No production deployment | Unproven at scale |
| No revenue/customers | No market validation |
| Benchmarks are local | Not production cloud benchmarks |

---

*All evidence is verifiable by running the commands listed above.*