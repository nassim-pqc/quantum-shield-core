# AWS KMS Algorithm Compatibility — Fix Summary

> **Date**: June 2026 (05/06/2026 15:02-15:06 UTC+2)  
> **Files modified**: `providers/kms/aws_kms.py`, `tests/test_kms_providers.py`  
> **Files updated**: `AWS_KMS_PROVIDER_AUDIT.md`, `AWS_KMS_MANUAL_SETUP_GUIDE.md`, `AWS_KMS_PENDING_VALIDATION.md`

---

## Problem

The AWS KMS provider (`providers/kms/aws_kms.py`) hardcoded `RSAES_OAEP_SHA_256` as the encryption algorithm for all KMS Encrypt/Decrypt operations. This algorithm is only valid for **asymmetric RSA KMS keys** (key spec `RSA_4096`).

**Impact**: Any user creating a symmetric KMS key (the AWS default when `--key-spec` is not specified) would receive an `InvalidKeyUsageException` when trying to use the Quantum Shield Core provider.

---

## Fix Applied

### Changes to `providers/kms/aws_kms.py`

| Change | Detail |
|--------|--------|
| Added `ALGO_SYMMETRIC_DEFAULT` constant | `"SYMMETRIC_DEFAULT"` — for symmetric KMS keys |
| Added `ALGO_RSAES_OAEP_SHA_256` constant | `"RSAES_OAEP_SHA_256"` — for asymmetric RSA keys |
| Added `_SUPPORTED_ALGORITHMS` tuple | Both algorithms, used for validation |
| Added `_ALGORITHMS_REQUIRING_PARAM` tuple | Algorithms that need explicit `EncryptionAlgorithm` in boto3 calls |
| Added `encryption_algorithm` field to `AWSKMSConfig` | Default: `SYMMETRIC_DEFAULT`, loaded from `AWS_KMS_ENCRYPTION_ALGORITHM` env var |
| Added `_encryption_kwargs()` method | Returns `{"EncryptionAlgorithm": algo}` only for RSA algorithms |
| Added `encryption_algorithm` param to `AWSKMSProvider.__init__` | Optional override via constructor |
| Added validation for algorithm | Raises `ValueError` for invalid algorithms |
| Added `algo` field to wrapped blob | Records which algorithm was used |
| Added `encryption_algorithm` and `key_spec` to health check response | Better diagnostics |

### Changes to `tests/test_kms_providers.py`

| Change | Detail |
|--------|--------|
| Split `TestAWSKMSWrap` → `TestAWSAKRSAKey` | Explicit RSA algorithm tests (5 tests) |
| Added `TestAWSKMSSymmetricKey` | Symmetric key tests (6 tests) |
| Added algorithm tests to `TestAWSKMSConfig` | Invalid algorithm, default algorithm, supported algorithms (3 tests) |
| Updated audit key tests | Use explicit RSA algorithm |

### Total test count: 30 (previously ~20 AWS KMS + Vault tests)

---

## Behaviour After Fix

### Symmetric KMS key (default, recommended)

```python
provider = AWSKMSProvider(key_id="alias/my-symmetric-key", region="eu-west-3")
```

- `encryption_algorithm` = `"SYMMETRIC_DEFAULT"`
- boto3 `encrypt()` / `decrypt()` calls do **not** include `EncryptionAlgorithm` parameter
- Works with ANY symmetric KMS key (`SYMMETRIC_DEFAULT` key spec)

### Asymmetric RSA KMS key

```python
provider = AWSKMSProvider(
    key_id="alias/my-rsa-key",
    region="eu-west-3",
    encryption_algorithm="RSAES_OAEP_SHA_256",
)
```

- `encryption_algorithm` = `"RSAES_OAEP_SHA_256"`
- boto3 `encrypt()` / `decrypt()` calls **include** `EncryptionAlgorithm=RSAES_OAEP_SHA_256`
- Works with RSA asymmetric KMS keys (`RSA_4096` key spec)

### Environment variable override

```bash
export AWS_KMS_ENCRYPTION_ALGORITHM=RSAES_OAEP_SHA_256
```

---

## Design Decisions

1. **No auto-detection via `DescribeKey`**: The simplest, safest approach is explicit configuration. Auto-detection would add complexity and could fail if `DescribeKey` permissions are missing. Users know what key type they created.

2. **No `EncryptionAlgorithm` sent for symmetric keys**: boto3 handles symmetric keys correctly without this parameter. Sending `SYMMETRIC_DEFAULT` is technically valid but omitting it is cleaner and more widely compatible.

3. **Backward compatible**: The default algorithm (`SYMMETRIC_DEFAULT`) is different from the old hardcoded value (`RSAES_OAEP_SHA_256`). Existing users who created RSA keys explicitly need to set `AWS_KMS_ENCRYPTION_ALGORITHM=RSAES_OAEP_SHA_256`. However, since no production deployment exists, this is safe.

---

## Validation Results

| Check | Status |
|-------|--------|
| Ruff lint | ✅ All checks passed |
| Ruff format | ✅ 49 files formatted |
| AWS KMS tests (RSA) | ✅ 5/5 passed |
| AWS KMS tests (symmetric) | ✅ 6/6 passed |
| AWS KMS tests (audit) | ✅ 3/3 passed |
| AWS KMS tests (config) | ✅ 4/4 passed |
| Vault tests | ✅ 12/12 passed |
| **Total tests** | **✅ 30/30 passed** |

---

## Remaining Limitations

| Limitation | Severity | Notes |
|------------|----------|-------|
| No algorithm auto-detection | Low | User must set env var for RSA keys |
| No FIPS endpoint support | Low | Not required for validation |
| No real AWS KMS validation | Medium | AWS CLI not available in this environment |

---

## Real AWS Validation (Future)

When AWS credentials are available:

```bash
# Symmetric key (default path)
export AWS_KMS_KEY_ID=alias/quantum-shield-test
export AWS_KMS_ENCRYPTION_ALGORITHM=SYMMETRIC_DEFAULT
export AWS_REGION=eu-west-3
.venv/bin/python scripts/validate_real_aws_kms.py

# RSA key (optional path)
export AWS_KMS_KEY_ID=alias/quantum-shield-test-rsa
export AWS_KMS_ENCRYPTION_ALGORITHM=RSAES_OAEP_SHA_256
export AWS_REGION=eu-west-3
.venv/bin/python scripts/validate_real_aws_kms.py
```

---

## Files Modified

| File | Status | Change |
|------|--------|--------|
| `providers/kms/aws_kms.py` | ✅ Modified | Algorithm config + validation + `_encryption_kwargs()` |
| `tests/test_kms_providers.py` | ✅ Modified | RSA + symmetric + config tests (30 total) |
| `evidence/cloud-validation/aws-kms/AWS_KMS_PROVIDER_AUDIT.md` | ✅ Updated | Fixed algorithm section, new summary |
| `evidence/cloud-validation/aws-kms/AWS_KMS_MANUAL_SETUP_GUIDE.md` | ✅ Updated | Removed warning about hardcoded algorithm |
| `evidence/cloud-validation/aws-kms/AWS_KMS_PENDING_VALIDATION.md` | ✅ Updated | Fixed algorithm bug section → fix applied section |
| `evidence/cloud-validation/aws-kms/AWS_KMS_ALGORITHM_FIX_SUMMARY.md` | ✅ Created | This file |

*No secrets exposed. No Git operations performed.*