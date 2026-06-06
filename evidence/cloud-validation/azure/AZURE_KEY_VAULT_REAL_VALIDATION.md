# Azure Key Vault Provider — Real Validation Evidence

Azure Key Vault provider implemented and validated against a real Azure Key Vault
test environment. This is not a production customer deployment or external security
audit.

## Environment

| Parameter | Value |
|---|---|
| Vault URL | `https://qshieldkv698697.vault.azure.net/` |
| Key name | `qshield-test-key` |
| Key type | RSA (Azure Key Vault managed) |
| Algorithm | RSA-OAEP-256 (`KeyWrapAlgorithm.rsa_oaep_256`) |
| Authentication | Azure CLI credential (`DefaultAzureCredential`) |

## Validation Results (2026-06-06)

```
Health check: available
Wrap:      PASS
Unwrap:    PASS
Roundtrip: PASS
```

No errors. No warnings.

## Operations Validated

- `AzureKeyVaultProvider.health_check()` → status `available`
- `AzureKeyVaultProvider.wrap_key(32-byte DEK)` → base64-encoded JSON blob
- `AzureKeyVaultProvider.unwrap_key(blob)` → original 32-byte DEK
- Roundtrip: wrapped DEK matches original after unwrap

## Fix Applied Before This Validation

The initial validation attempt failed with:

```
Local wrap operation failed: 'str' object has no attribute 'value'
```

Root cause: `WRAPPING_ALGORITHM` was a plain `str` instead of a `KeyWrapAlgorithm`
enum. Fixed in `providers/kms/azure_kms.py` by importing and using
`KeyWrapAlgorithm.rsa_oaep_256`. See
[`docs/AZURE_KEY_VAULT_REAL_VALIDATION_FIX.md`](../../../docs/AZURE_KEY_VAULT_REAL_VALIDATION_FIX.md).

## Information Not Included

The following sensitive data is intentionally omitted:

- Azure tenant ID
- Azure subscription ID
- Azure client credentials
- Any access tokens or refresh tokens
- Private key material
