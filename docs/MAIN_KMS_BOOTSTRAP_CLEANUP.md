# main.py KMS Bootstrap Cleanup

> Date: 2026-06-05
> Branch: `repo-public-cleanup`

## Problem

`main.py` contained stale enterprise license logic that contradicted the public KMS provider implementations in `providers/kms/`.

### Issues Found

| # | Issue | File (line) | Risk |
|---|-------|-------------|------|
| K1 | `_validate_license_key()` checked `QSC_LICENSE_KEY` starting with `QSC-ENT-` | main.py:49-53 | CTO sees contradiction: docs say open-source, code shows feature gating |
| K2 | `ENTERPRISE_LICENSED` constant gated AWS/Vault/Azure access | main.py:62 | Artificial KMS blocking in open-source |
| K3 | `_ent_license.require_enterprise_license()` not defined — NameError risk | main.py:98 | Runtime crash on cloud KMS selection without license |
| K4 | Imports from `enterprise.kms.aws_kms`, `enterprise.kms.vault_kms`, `enterprise.kms.azure_kms` (nonexistent modules) | main.py:107-114 | ImportError for anyone using cloud KMS |
| K5 | Logged license key prefix in `enterprise_license_active` | main.py:66-67 | Accidental secret exposure in logs |
| K6 | Lifespan log included `"enterprise": ENTERPRISE_LICENSED` | main.py:146 | False enterprise claim in startup signal |
| K7 | OpenAPI description: `"Enterprise post-quantum cryptographic enclave"` | main.py:177 | Overclaiming — not enterprise-validated |
| K8 | Community edition error message: `"no AWS/Vault KMS"` | main.py:71 | Implies KMS providers are paywalled when they're actually open-source |

## Changes Applied

### Files Modified

1. **`main.py`**
   - Removed `_validate_license_key()` function entirely
   - Removed `ENTERPRISE_LICENSED` constant and all conditional logic
   - Removed `_ent_license.require_enterprise_license()` dead code
   - Replaced `from enterprise.kms.*` imports with `from providers.kms.*` — the real public modules
   - Rewrote `_create_kms_provider()` to handle each KMS_PROVIDER value independently:
     - `local` → `LocalEnvKMS(keys)` (default)
     - `aws` → `AWSKMSProvider()`
     - `vault` → `HashiCorpVaultKMSProvider()`
     - `azure` → `AzureKeyVaultProvider()`
     - Unknown → raises `ValueError` with clear message
   - Replaced `enterprise_license_active/inactive` logs with `kms_provider_selected`
   - Replaced lifespan log `"enterprise": ENTERPRISE_LICENSED` with `"kms_provider": <provider>`
   - Updated OpenAPI description from `"Enterprise post-quantum cryptographic enclave"` to `"Post-quantum cryptographic microservice."`
   - Merged `from sqlalchemy import func as sql_func; from sqlalchemy import select` into single import

2. **`docs/CODE_REVIEW_FINDINGS.md`**
   - Added `main.py KMS bootstrap cleanup` section documenting all 9 findings (K1-K9)

### Not Modified

- All FastAPI endpoints remain unchanged
- All Pydantic schemas remain unchanged
- `security_engine.py` — not modified
- ML-KEM / Kyber / AES-GCM crypto — not modified
- Audit trail — not modified
- KMS providers in `providers/kms/` — not modified
- No GitHub push, no automatic commit

## New Behaviour

### KMS Provider Selection

```
KMS_PROVIDER  →  Provider Used
─────────────────────────────────────
not set       →  LocalEnvKMS(keys)  [default]
local         →  LocalEnvKMS(keys)
aws           →  AWSKMSProvider()
vault         →  HashiCorpVaultKMSProvider()
azure         →  AzureKeyVaultProvider()
(other)       →  ValueError: Unsupported KMS_PROVIDER '...'
```

### Supported Environment Variables

| Variable | Purpose |
|----------|---------|
| `KMS_PROVIDER` | Provider selection (`local`, `aws`, `vault`, `azure`) |
| `ACTIVE_AUDIT_KEY_VERSION` | Active audit key version (default: `v1`) |
| `AUDIT_KEY`, `AUDIT_KEY_v1`, etc. | Raw audit key material |
| `AWS_KMS_KEY_ID` | AWS KMS key ARN/alias |
| `AWS_REGION` | AWS region |
| `VAULT_ADDR`, `VAULT_TOKEN` | Vault server address and token |
| `AZURE_KEY_VAULT_URL` | Azure Key Vault URL |

### Startup Logs

```json
{"event": "kms_provider_selected", "provider": "local"}
{"event": "quantum_shield_started", "version": "2.4.1", "kms_provider": "local"}
```

### OpenAPI Description

> Post-quantum cryptographic microservice.
> - **Algorithm**: ML-KEM-768 (Kyber768) + AES-256-GCM
> - **Audit**: HMAC-SHA256 signed logs with key rotation
> - **Auth**: API key (SHA-256 hashed) with RBAC

## Tests Executed

| Suite | Result |
|-------|--------|
| `ruff check .` | All checks passed (49 files) |
| `ruff format --check .` | All checks passed (49 files) |
| `pytest tests/test_kms_providers.py` | 30 passed, 0 failed |
| `go test ./...` (sdk-go) | All packages pass |
| `go build ./...` (sdk-go) | Build succeeds |
| `go vet ./...` (sdk-go) | Vet passes |
| API tests | Not executed (database-dependent, no db running) |
| Grep: `enterprise.kms`, `_ent_license`, `ENTERPRISE_LICENSED`, `QSC_LICENSE_KEY` | **No references found in main.py** |

## Limits

1. **AWS KMS**: Not validated against real AWS. Uses `moto` for testing. The real providers exist in `providers/kms/aws_kms.py` but bootstrap correctness is only tested at the import/config level.
2. **Azure KMS**: Not validated against real Azure. Provider exists in `providers/kms/azure_kms.py` but has no dedicated unit tests.
3. **API integration tests**: Not run because they require a running database.
4. The pre-existing test failure `TestAWSKMSConfig::test_invalid_algorithm_raises` has been resolved (now passing).

> This cleanup does not claim production validation for AWS or Azure. It only aligns main.py with the public KMS providers implemented in the repository.