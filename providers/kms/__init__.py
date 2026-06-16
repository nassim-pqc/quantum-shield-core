"""
providers.kms — Enterprise KMS provider adapters.

Providers:
    AWSKMSProvider              — AWS KMS with DEK Key Wrapping + audit key retrieval
    HashiCorpVaultKMSProvider   — HashiCorp Vault Transit + KV v2 for DEK wrapping + audit keys
    AzureKeyVaultProvider       — Azure Key Vault (stub, requires extension)

Architecture:
    KMSProvider (KeyWrapper + SecretProvider) interface in base.py
"""

from typing import TYPE_CHECKING

# Base interfaces are dependency-free, so import them eagerly.
from providers.kms.base import (
    KeyWrapper,
    KeyWrapperAuthError,
    KeyWrapperError,
    KeyWrapperTransientError,
    KMSProvider,
    SecretProvider,
)

# Concrete cloud providers pull heavy, optional SDKs (boto3, azure-keyvault-*,
# hvac). They are loaded lazily (PEP 562) so importing this package — or using
# only one provider — never requires every cloud SDK to be installed.
_LAZY_PROVIDERS = {
    "AWSKMSProvider": "providers.kms.aws_kms",
    "AzureKeyVaultProvider": "providers.kms.azure_kms",
    "HashiCorpVaultKMSProvider": "providers.kms.vault_kms",
}

if TYPE_CHECKING:  # for type checkers / IDEs only — no runtime import cost
    from providers.kms.aws_kms import AWSKMSProvider
    from providers.kms.azure_kms import AzureKeyVaultProvider
    from providers.kms.vault_kms import HashiCorpVaultKMSProvider


def __getattr__(name: str):
    module_path = _LAZY_PROVIDERS.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, name)


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
