"""
providers.kms — Enterprise KMS provider adapters.

LocalEnvKMS remains in security_engine for backward compatibility.
External providers are production-grade for AWS, Vault, and Azure integrations.

Providers:
    AWSKMSProvider              — AWS KMS with envelope encryption
    HashiCorpVaultKMSProvider   — HashiCorp Vault KV v2 secrets engine
    AzureKeyVaultProvider       — Azure Key Vault (stub, requires extension)

Exceptions:
    AWSKMSConnectionError, AWSKMSAuthError, AWSKMSKeyError, AWSKMSConfigurationError
    VaultKMSConnectionError, VaultKMSAuthError, VaultKMSKeyError, VaultKMSConfigurationError
"""
from providers.kms.aws_kms import AWSKMSProvider
from providers.kms.vault_kms import HashiCorpVaultKMSProvider
from providers.kms.azure_kms import AzureKeyVaultProvider

__all__ = [
    "AWSKMSProvider",
    "HashiCorpVaultKMSProvider",
    "AzureKeyVaultProvider",
]