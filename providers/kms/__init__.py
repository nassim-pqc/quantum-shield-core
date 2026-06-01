"""
providers.kms — Enterprise KMS provider adapters.

Providers:
    AWSKMSProvider              — AWS KMS with DEK Key Wrapping + audit key retrieval
    HashiCorpVaultKMSProvider   — HashiCorp Vault Transit + KV v2 for DEK wrapping + audit keys
    AzureKeyVaultProvider       — Azure Key Vault (stub, requires extension)

Architecture:
    KMSProvider (KeyWrapper + SecretProvider) interface in base.py
"""
from providers.kms.aws_kms import AWSKMSProvider
from providers.kms.vault_kms import HashiCorpVaultKMSProvider
from providers.kms.azure_kms import AzureKeyVaultProvider
from providers.kms.base import (
    KMSProvider,
    KeyWrapper,
    SecretProvider,
    KeyWrapperError,
    KeyWrapperAuthError,
    KeyWrapperTransientError,
)

__all__ = [
    "AWSKMSProvider",
    "HashiCorpVaultKMSProvider",
    "AzureKeyVaultProvider",
    "KMSProvider",
    "KeyWrapper",
    "SecretProvider",
    "KeyWrapperError",
    "KeyWrapperAuthError",
    "KeyWrapperTransientError",
]
