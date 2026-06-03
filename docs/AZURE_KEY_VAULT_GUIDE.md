# Azure Key Vault Integration Guide

## Overview

Azure Key Vault provides enterprise-grade key management for Quantum Shield Core. The integration supports two capabilities:

1. **DEK Key Wrapping**: Uses Azure Key Vault Keys (RSA-OAEP-256) via CryptographyClient
2. **Audit Key Storage**: Uses Azure Key Vault Secrets via SecretClient

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Quantum Shield Core                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              AzureKeyVaultProvider                        │   │
│  │  ┌──────────────────┐  ┌────────────────────────────┐   │   │
│  │  │ KeyWrapper       │  │ SecretProvider             │   │   │
│  │  │ - wrap_key()     │  │ - get_audit_key()          │   │   │
│  │  │ - unwrap_key()   │  │                            │   │   │
│  │  └────────┬─────────┘  └──────────┬─────────────────┘   │   │
│  │           │                       │                       │   │
│  │           ▼                       ▼                       │   │
│  │  ┌──────────────────┐  ┌────────────────────────────┐   │   │
│  │  │ CryptographyClient│  │ SecretClient               │   │   │
│  │  │ RSA-OAEP-256      │  │ secret: audit-key-v1      │   │   │
│  │  │ key: quantum-      │  │ secret: audit-key-v2      │   │   │
│  │  │ shield-dek        │  │ (one per version)          │   │   │
│  │  └────────┬─────────┘  └──────────┬─────────────────┘   │   │
│  └───────────┼───────────────────────┼──────────────────────┘   │
│              │                       │                          │
└──────────────┼───────────────────────┼──────────────────────────┘
               │                       │
               ▼                       ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │  Azure Key Vault     │  │  Azure Key Vault     │
    │  Keys (RSA)          │  │  Secrets             │
    │  - wrapKey           │  │  - getSecret         │
    │  - unwrapKey         │  │  - setSecret         │
    └──────────────────────┘  └──────────────────────┘
```

---

## Prerequisites

### 1. Azure Subscription

```bash
# Login to Azure
az login

# Create a Key Vault (if not exists)
az keyvault create \
  --name my-quantum-shield-vault \
  --resource-group my-resource-group \
  --location westeurope \
  --sku Premium \
  --enable-rbac-authorization true
```

### 2. Create an RSA Key for DEK Wrapping

```bash
# Create RSA key for wrapping/unwrapping DEKs
az keyvault key create \
  --vault-name my-quantum-shield-vault \
  --name quantum-shield-dek \
  --kty RSA-HSM \
  --size 4096 \
  --ops wrapKey unwrapKey
```

### 3. Store Audit Keys

```bash
# Store audit key v1
az keyvault secret set \
  --vault-name my-quantum-shield-vault \
  --name quantum-shield-audit-v1 \
  --value "your-32-byte-audit-key-here-make-it-long-enough"

# Store audit key v2 (for rotation)
az keyvault secret set \
  --vault-name my-quantum-shield-vault \
  --name quantum-shield-audit-v2 \
  --value "another-32-byte-audit-key-for-rotation-purposes"
```

### 4. Configure Access

#### Option A: Managed Identity (Recommended for Azure-hosted workloads)

```bash
# Assign managed identity to your VM/App Service
az vm identity assign \
  --resource-group my-resource-group \
  --name my-vm-name

# Grant Key Vault permissions to the managed identity
az role assignment create \
  --role "Key Vault Crypto User" \
  --assignee <managed-identity-principal-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/my-quantum-shield-vault

az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee <managed-identity-principal-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/my-quantum-shield-vault
```

#### Option B: Service Principal (for non-Azure workloads)

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "quantum-shield-sp" \
  --role "Key Vault Crypto User" \
  --scopes /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/my-quantum-shield-vault

# Grant secret permissions
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee <sp-app-id> \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/my-quantum-shield-vault

# You'll get: appId, password, tenant — use as env variables below
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_KEY_VAULT_URL` | **Yes** | — | Key Vault URL (e.g. `https://myvault.vault.azure.net/`) |
| `AZURE_KEY_NAME` | No | `quantum-shield-dek` | RSA key name for DEK wrapping |
| `AZURE_SECRET_NAME` | No | `quantum-shield-audit` | Secret name prefix for audit keys |
| `AZURE_CLIENT_ID` | No* | — | Azure service principal client ID |
| `AZURE_TENANT_ID` | No* | — | Azure tenant ID |
| `AZURE_CLIENT_SECRET` | No* | — | Azure service principal client secret |
| `AZURE_MAX_RETRIES` | No | `3` | Max retry attempts for transient errors |
| `AZURE_RETRY_MIN` | No | `1.0` | Min retry delay (seconds) |
| `AZURE_RETRY_MAX` | No | `10.0` | Max retry delay (seconds) |

*Required for service principal auth. Managed Identity doesn't need these.

### Authentication Priority

`DefaultAzureCredential` tries the following in order:

1. **Environment variables** — `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`
2. **Managed Identity** — Azure VM, App Service, Azure Functions, etc.
3. **Azure CLI** — Developer credentials from `az login`
4. **Visual Studio Code** — Azure Account extension credentials

---

## Usage

### Programmatic Usage

```python
from providers.kms.azure_kms import AzureKeyVaultProvider

# Create provider (reads AZURE_KEY_VAULT_URL from env)
provider = AzureKeyVaultProvider()

# Or with explicit configuration
provider = AzureKeyVaultProvider(
    vault_url="https://myvault.vault.azure.net",
    key_name="quantum-shield-dek",
    secret_name="quantum-shield-audit",
    max_retries=5,
)

# --- Key Wrapping (DEK) ---
dek = bytes(range(32))  # 32-byte DEK from Kyber768 KEM

# Wrap DEK under Azure Key Vault RSA key
wrapped = provider.wrap_key(dek)
# Returns: base64-encoded JSON blob

# Unwrap DEK
unwrapped = provider.unwrap_key(wrapped)
# Returns: original 32-byte DEK

# --- Audit Key Retrieval ---
audit_key = provider.get_audit_key("v1")
# Returns: bytes or None

# --- Health Check ---
status = provider.health_check()
# Returns: {
#     "provider": "azure_keyvault",
#     "vault_url": "https://...",
#     "key_name": "quantum-shield-dek",
#     "key_type": "RSA-HSM",
#     "enabled": True,
#     "status": "available"
# }
```

### Docker Compose Configuration

```yaml
services:
  quantum-shield-api:
    environment:
      KMS_PROVIDER: azure
      AZURE_KEY_VAULT_URL: https://my-quantum-shield-vault.vault.azure.net/
      AZURE_KEY_NAME: quantum-shield-dek
      AZURE_SECRET_NAME: quantum-shield-audit
      # For service principal auth:
      AZURE_CLIENT_ID: ${AZURE_CLIENT_ID}
      AZURE_TENANT_ID: ${AZURE_TENANT_ID}
      AZURE_CLIENT_SECRET: ${AZURE_CLIENT_SECRET}
```

### Environment File (.env)

```bash
# .env
KMS_PROVIDER=azure
AZURE_KEY_VAULT_URL=https://my-quantum-shield-vault.vault.azure.net/
AZURE_KEY_NAME=quantum-shield-dek
AZURE_SECRET_NAME=quantum-shield-audit

# Service Principal (optional — for non-Azure deployments)
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_TENANT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
AZURE_CLIENT_SECRET=your-client-secret

# Retry configuration
AZURE_MAX_RETRIES=5
AZURE_RETRY_MIN=1.0
AZURE_RETRY_MAX=30.0
```

---

## Security Properties

### Authentication
- **DefaultAzureCredential**: Flexible auth chain (env vars → managed identity → Azure CLI)
- **Managed Identity**: No credentials in code or config files
- **Service Principal**: For non-Azure deployments with client secret

### Key Wrapping
- **RSA-OAEP-256**: Optimal Asymmetric Encryption Padding with SHA-256
- **4096-bit RSA keys**: Industry-standard key strength
- **HSM-backed keys**: FIPS 140-2/140-3 validated (Premium SKU)
- **Envelope encryption**: DEK encrypted under KMS key, never exposed to storage

### Audit Keys
- **Secret versioning**: Each version stored as separate secret
- **Access control**: Azure RBAC for secrets (Key Vault Secrets User role)
- **Audit logging**: Azure Key Vault diagnostic logs for all operations

### Error Handling
- **Retry policy**: Exponential backoff with configurable limits
- **Error classification**: Auth errors, transient errors, permanent errors
- **Local fallback**: Environment variables as fallback when vault is unreachable

---

## Testing

### Unit Tests

The Azure provider has comprehensive unit tests using `unittest.mock`:

```bash
# Run Azure KMS tests
pytest tests/test_azure_kms.py -v

# Run all KMS provider tests
pytest tests/test_kms_providers.py tests/test_azure_kms.py -v
```

### Test Coverage

| Test Area | Tests | Coverage |
|-----------|-------|----------|
| Configuration validation | 4 | URL validation, defaults |
| Key wrapping | 5 | Roundtrip, blob format, errors, auth |
| Health check | 2 | Available, auth error |
| Audit key retrieval | 6 | Cache, env, vault, missing, short, fallback |

---

## Migration from Local Env

If you're currently using `AUDIT_KEY` environment variables and want to migrate to Azure Key Vault:

1. Store your existing audit keys as secrets in Azure Key Vault
2. Set `KMS_PROVIDER=azure` and `AZURE_KEY_VAULT_URL`
3. Keep `AUDIT_KEY_v1` as fallback during migration
4. Remove env vars once migration is verified

```bash
# Migrate existing audit key to Azure
az keyvault secret set \
  --vault-name my-quantum-shield-vault \
  --name quantum-shield-audit-v1 \
  --value "$(echo $AUDIT_KEY)"

# Keep env var as fallback during transition
export AUDIT_KEY_v1="$AUDIT_KEY"
```

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `KeyWrapperAuthError` | Invalid/expired credentials | Check `DefaultAzureCredential` chain |
| `KeyWrapperError: resource not found` | Key or secret doesn't exist | Create via `az keyvault key/secret` |
| `KeyWrapperTransientError` | Network/Vault throttling | Increase retries, check network |
| `ValueError: AZURE_KEY_VAULT_URL required` | Missing env variable | Set `AZURE_KEY_VAULT_URL` |
| "Access denied" | Missing RBAC role | Assign Key Vault Crypto User + Secrets User |
| "Forbidden" (403) | Key vault firewall | Add allowlist rule for your IP/service |