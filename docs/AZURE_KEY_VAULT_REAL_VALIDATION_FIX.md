# Azure Key Vault Provider — Real Validation Bug Fix

## Problem

During real Azure Key Vault cloud validation, `wrap_key()` failed with:

```
Local wrap operation failed: 'str' object has no attribute 'value'
```

`health_check()`, `unwrap_key()`, and the roundtrip test passed, but `wrap_key()` raised
an `AttributeError` that was caught and re-raised as a `KeyWrapperTransientError`.

## Root Cause

`AzureKeyVaultClient.WRAPPING_ALGORITHM` was defined as a plain string:

```python
# Before (wrong)
WRAPPING_ALGORITHM = "RSA-OAEP-256"
```

The Azure SDK's `CryptographyClient.wrap_key()` and `.unwrap_key()` expect a
`KeyWrapAlgorithm` enum object, not a string. Internally the SDK calls `.value` on
the parameter to extract the algorithm string for the HTTP request body. Passing a
plain `str` caused `AttributeError: 'str' object has no attribute 'value'`.

Note: `unwrap_key()` was also passing the same string but happened to work because
the SDK code path hit a different branch (or the error was silently swallowed during
the test sequence). The `wrap_key()` branch was the first to fail visibly.

## Fix Applied

**File:** `providers/kms/azure_kms.py`

### 1. Import `KeyWrapAlgorithm` at module level

```python
from azure.keyvault.keys.crypto import KeyWrapAlgorithm
```

### 2. Change the class constant to use the enum

```python
# After (correct)
# Enum used for Azure SDK calls; .value == "RSA-OAEP-256" for JSON payloads
WRAPPING_ALGORITHM = KeyWrapAlgorithm.rsa_oaep_256
```

`KeyWrapAlgorithm.rsa_oaep_256.value == "RSA-OAEP-256"` — identical to the
previous string, so existing blobs remain readable.

### 3. Use `.value` in the JSON payload

The `AzureKeyVaultProvider.wrap_key()` method embeds the algorithm in the
persisted blob. Changed from:

```python
"algorithm": AzureKeyVaultClient.WRAPPING_ALGORITHM,        # was the enum object
```

to:

```python
"algorithm": AzureKeyVaultClient.WRAPPING_ALGORITHM.value,  # string "RSA-OAEP-256"
```

This keeps the payload JSON-serializable and backward-compatible.

## Files Modified

| File | Change |
|---|---|
| `providers/kms/azure_kms.py` | Import `KeyWrapAlgorithm`; change constant to enum; use `.value` in JSON payload |

## Tests Executed

| Suite | Result |
|---|---|
| `pytest tests/test_azure_kms.py` | 18/18 PASS |
| `pytest tests/test_kms_providers.py` | 30/30 PASS |
| `pytest tests/test_api.py` | 37/37 PASS |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 49 files formatted correctly |

## Real Azure Validation Result

Executed against `https://qshieldkv698697.vault.azure.net/`, key `qshield-test-key` (RSA):

```
Health check: available
Wrap:      PASS
Unwrap:    PASS
Roundtrip: PASS
```

No `'str' object has no attribute 'value'` error. No warnings.

Azure Key Vault provider implemented and validated against a real Azure Key Vault
test environment. This is not a production customer deployment or external security
audit.

## Payload Compatibility

Blobs produced before this fix used a string constant `"RSA-OAEP-256"` in the `algorithm`
field. Blobs produced after this fix use `KeyWrapAlgorithm.rsa_oaep_256.value` which
evaluates to the identical string `"RSA-OAEP-256"`. No migration required.

## Remaining Limits

- No production deployment or third-party security audit has been performed.
- The test vault and key used for validation are a development environment.
- Go SDK tests were not executed (no Go installation detected in this session).
