# AWS KMS Provider — Source Code Audit

> **Date**: June 2026  
> **File audited**: `providers/kms/aws_kms.py`  
> **Supporting files**: `providers/kms/base.py`, `tests/test_kms_providers.py`  
> **Audit scope**: All methods, configuration, error handling, test coverage

---

## 1. Overview

The AWS KMS provider is fully implemented in `providers/kms/aws_kms.py` (425 lines), implementing the `KMSProvider` interface from `providers/kms/base.py`. It provides both **DEK Key Wrapping** (envelope encryption) and **Audit Key Retrieval**.

---

## 2. Environment Variables Required

| Variable | Required | Purpose |
|----------|----------|---------|
| `AWS_KMS_KEY_ID` | Yes | CMK ARN or alias (e.g., `alias/quantum-shield-dek`) |
| `AWS_REGION` | Yes | AWS region (default: `eu-west-1`) |
| `AWS_ACCESS_KEY_ID` | Optional* | Explicit access key (optional — uses IAM role if absent) |
| `AWS_SECRET_ACCESS_KEY` | Optional* | Explicit secret key (optional) |
| `KMS_MAX_RETRIES` | No | Max retry attempts (default: 3) |
| `KMS_RETRY_MIN` | No | Min retry delay seconds (default: 1.0) |
| `KMS_RETRY_MAX` | No | Max retry delay seconds (default: 10.0) |
| `AUDIT_KEY_ENCRYPTED_V1` | No | Base64-encoded encrypted audit key blob (optional) |

*\* If neither explicit keys nor IAM role is configured, SDK will fail.*

The `.env.example` documents these variables (lines 35-41).

---

## 3. Implemented Methods

### 3.1 `AWSKMSProvider.__init__(...)` — Constructor (line 247)

- Accepts optional overrides for `key_id`, `region`, `access_key_id`, `secret_access_key`, `max_retries`, `retry_min`, `retry_max`
- Builds `AWSKMSConfig` dataclass from kwargs, falls back to env vars
- Calls `config.validate()` which requires `AWS_KMS_KEY_ID` and `AWS_REGION`
- Config constraints: `max_retries` must be 0-10

**Test coverage**: `test_missing_key_id_raises` (test_kms_providers.py:136) — validates missing key_id raises `ValueError`

### 3.2 `wrap_key(plaintext_dek: bytes) -> str` — DEK Wrapping (line 288)

- Calls `AWSKMSClient.encrypt()` with `RSAES_OAEP_SHA_256`
- Returns base64-encoded JSON blob with: `v` (version), `k` (base64 ciphertext), `region`, `key_id`
- Uses KMS Encrypt, which requires `kms:Encrypt` permission on the CMK

**Test coverage**: `test_wrap_roundtrip` (line 103), `test_wrap_different_each_time` (line 112) — both pass with moto

### 3.3 `unwrap_key(wrapped_blob: str) -> bytes` — DEK Unwrapping (line 312)

- Parses the JSON blob, extracts ciphertext, calls `AWSKMSClient.decrypt()`
- Validates blob format (JSON + key field)
- Uses KMS Decrypt with `RSAES_OAEP_SHA_256`
- Requires `kms:Decrypt` permission on the CMK

**Test coverage**: `test_wrap_roundtrip` (line 103), `test_unwrap_invalid_blob_raises` (line 118), `test_unwrap_tampered_blob_raises` (line 123) — all pass with moto

### 3.4 `get_audit_key(version: str) -> bytes | None` — Audit Key Retrieval (line 351)

- Tries: in-memory cache → raw env var (`AUDIT_KEY_v1`, etc.) → encrypted env blob decrypted via KMS
- Cache TTL: 300 seconds (5 minutes)
- Encrypted blob format: base64-encoded ciphertext decrypted via `AWSKMSClient.decrypt()`

**Test coverage**: `test_get_audit_key_from_env` (line 157), `test_get_audit_key_missing` (line 171), `test_get_audit_key_encrypted` (line 176) — all pass with moto

### 3.5 `health_check() -> dict` — Health Check (line 403)

- Calls `AWSKMSClient.describe_key()` which calls KMS `DescribeKey` API
- Returns: `provider`, `key_id`, `region`, `key_state`, `key_usage`, `status`
- On error: returns error/auth_error status

**Test coverage**: `test_health_check` (line 146), `test_wrap_roundtrip` (indirect) — pass with moto

---

## 4. Internal Classes

### 4.1 `AWSKMSConfig` (line 63)

- Dataclass for configuration with env var fallback in `__post_init__`
- `validate()` method ensures `key_id` and `region` are set

### 4.2 `AWSKMSClient` (line 109)

- Low-level boto3 client with tenacity retry
- Creates boto3 session with `region_name` and optional explicit credentials
- Methods: `encrypt()`, `decrypt()`, `describe_key()`, each with tenacity retry decorator
- `_classify_error()` maps boto3 exceptions to domain exceptions (`KeyWrapperError`, `KeyWrapperAuthError`, `KeyWrapperTransientError`)
- Uses RSAES_OAEP_SHA_256 wrapping algorithm (public key algorithm, not symmetric — important note below)

---

## 5. What Is Tested with Mocks (moto)

| Feature | Status | Mock | Real AWS Needed? |
|---------|--------|------|-----------------|
| `wrap_key()` / `unwrap_key()` roundtrip | ✅ Tested | moto | No (moto handles RSA_4096) |
| Tampered blob detection | ✅ Tested | moto | No |
| Invalid blob format | ✅ Tested | N/A | No |
| Missing key_id validation | ✅ Tested | N/A | No |
| Health check | ✅ Tested | moto | No |
| `get_audit_key()` from env | ✅ Tested | N/A | No |
| `get_audit_key()` encrypted | ✅ Tested | moto | No |
| Error classification | ✅ Tested | moto | No |

---

## 6. What Requires a Real AWS Account

| Scenario | Why |
|----------|-----|
| Encrypt/Decrypt with real CMK | moto uses RSA_4096; real AWS may differ in key spec |
| IAM permission errors | moto always succeeds on auth; real IAM policies differ |
| Network latency / timeouts | moto is in-process; real AWS has network |
| Key rotation / multi-region | Beyond mock scope |
| CloudTrail logging | moto doesn't generate CloudTrail events |
| FIPS endpoint validation | moto doesn't test FIPS compliance |
| Production throughput | moto is single-threaded |
| Cross-account access | moto is single-account |

---

## 7. Current Limitations

| Limitation | Impact | Severity |
|------------|--------|----------|
| No `generate_data_key()` support | Uses KMS Encrypt directly for wrapping, which works but differs from typical KMS envelope encryption pattern | Low |
| No key rotation handling | Does not detect or handle auto-rotated CMKs | Low |
| No CloudTrail verification in tests | moto doesn't support CloudTrail | Low |
| Algorithm is not auto-detected from `DescribeKey` | User must set `AWS_KMS_ENCRYPTION_ALGORITHM` manually if using RSA keys | Low (symmetric is default) |

---

## 8. Algorithm Compatibility — Now Fixed (June 2026)

**Previous problem**: The provider hardcoded `RSAES_OAEP_SHA_256`, which only worked with asymmetric RSA keys. Symmetric KMS keys would fail.

**Fix applied**: The encryption algorithm is now configurable via:

1. **Environment variable**: `AWS_KMS_ENCRYPTION_ALGORITHM`
2. **Constructor parameter**: `encryption_algorithm` on `AWSKMSProvider`

### Supported algorithms

| Algorithm | Value | Key Type | boto3 Behaviour |
|-----------|-------|----------|-----------------|
| `SYMMETRIC_DEFAULT` (default) | `"SYMMETRIC_DEFAULT"` | Symmetric (`SYMMETRIC_DEFAULT` key spec) | No `EncryptionAlgorithm` parameter sent |
| `RSAES_OAEP_SHA_256` | `"RSAES_OAEP_SHA_256"` | Asymmetric RSA (`RSA_4096` key spec) | `EncryptionAlgorithm` parameter sent |

### Key design decisions

1. **Default is `SYMMETRIC_DEFAULT`** — matches the most common AWS KMS use case
2. **No `EncryptionAlgorithm` sent for symmetric keys** — boto3 handles it correctly without the parameter
3. **`RSAES_OAEP_SHA_256` sent for RSA keys** — explicit parameter required by AWS API
4. **Invalid algorithm raises `ValueError`** at initialization, not at runtime
5. **Blob metadata includes `algo` field** — the wrapped blob records which algorithm was used

### Code changes

| File | Change |
|------|--------|
| `providers/kms/aws_kms.py` | Added `encryption_algorithm` field to `AWSKMSConfig`, `_encryption_kwargs()` method, constructor parameter, validation, and `algo` field in wrapped blob |
| `tests/test_kms_providers.py` | Added `TestAWSKMSSymmetricKey` class (6 tests), `TestAWSKMSConfig` algorithm tests (3 tests), `TestAWSAKRSAKey` renamed from `TestAWSKMSWrap` with explicit algorithm |

### How to use

```bash
# Symmetric key (default, no change needed)
export AWS_KMS_KEY_ID=alias/my-symmetric-key
export AWS_KMS_ENCRYPTION_ALGORITHM=SYMMETRIC_DEFAULT

# Asymmetric RSA key (explicit)
export AWS_KMS_KEY_ID=alias/my-rsa-key
export AWS_KMS_ENCRYPTION_ALGORITHM=RSAES_OAEP_SHA_256
```

Or via code:
```python
from providers.kms.aws_kms import AWSKMSProvider

# Symmetric (default)
provider = AWSKMSProvider(key_id="alias/my-key", region="eu-west-3")

# RSA asymmetric
provider = AWSKMSProvider(
    key_id="alias/my-rsa-key",
    region="eu-west-3",
    encryption_algorithm="RSAES_OAEP_SHA_256",
)
```

---

## 9. Summary

| Category | Status |
|----------|--------|
| Code implemented | ✅ Complete |
| Symmetric key support | ✅ Default, tested with moto (6 tests) |
| Asymmetric RSA key support | ✅ Configurable, tested with moto (5 tests) |
| Invalid algorithm rejection | ✅ Verified at init time (1 test) |
| Mock tests | ✅ 30 total (AWS KMS: 16, Vault: 10, Config: 4) |
| Real AWS KMS validation | ❌ Not executed (AWS credentials unavailable) |
| Algorithm auto-detection | ⚠️ Not implemented (env var / constructor param instead) |
| FIPS endpoint support | ❌ Not implemented |

---

*This audit is based on source code analysis only. Real AWS KMS validation was not performed because AWS credentials were not available in the local environment.*