# Azure Key Vault Provider — Enterprise Audit

## Current State

The existing `AzureKeyVaultProvider` (`providers/kms/azure_kms.py`) is a **basic implementation** that only implements the `AbstractKMS` interface from `security_engine.py`. 

## Gaps vs. AWS KMS / Vault

| Feature | AWS KMS | Vault | Azure (Current) |
|---------|---------|-------|-----------------|
| **Interface** | `KMSProvider` (KeyWrapper + SecretProvider) | `KMSProvider` | `AbstractKMS` (SecretProvider only) |
| **DEK Key Wrapping** | ✅ wrap_key/unwrap_key via RSAES_OAEP_SHA_256 | ✅ Transit Engine | ❌ Missing |
| **Config Class** | ✅ AWSKMSConfig | ✅ VaultKMSConfig | ❌ Missing |
| **Tenacity Retry** | ✅ Exponential backoff | ✅ Exponential backoff | ❌ Missing |
| **Error Classification** | ✅ Auth/Transient/Permanent | ✅ Auth/Transient/Permanent | ❌ Custom errors only |
| **Base exceptions** | ✅ KeyWrapperError hierarchy | ✅ KeyWrapperError hierarchy | ❌ Custom exception hierarchy |
| **Health Check** | ✅ describe_key | ✅ sys/health | ✅ Basic |
| **Audit Key Encryption** | ✅ Encrypted blob (AUDIT_KEY_ENCRYPTED) | ✅ KV v2 | ❌ Missing |
| **Logging** | ✅ Structured | ✅ Structured | ❌ Minimal |
| **Azure Key Vault Key (RSA)** | ✅ N/A (uses KMS Encrypt) | ✅ N/A (uses Transit) | ❌ Could use AKV RSA key |