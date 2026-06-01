"""
Azure Key Vault provider — production-grade key management.

Integrates with Azure Key Vault Secrets for secure audit key storage.
Supports authentication via DefaultAzureCredential (env, managed identity, etc).

Environment Variables:
    AZURE_KEY_VAULT_URL      Vault URL (e.g. https://myvault.vault.azure.net/)
    AZURE_AUDIT_KEY_NAME     Secret name for audit key (default: quantum-shield-audit)
    AZURE_TENANT_ID          Azure tenant ID (optional — uses DefaultAzureCredential)
"""
from __future__ import annotations

import os
import time
from typing import Any

from security_engine import AbstractKMS


class AzureKeyVaultConnectionError(Exception):
    """Raised when Azure Key Vault is unreachable."""


class AzureKeyVaultAuthError(Exception):
    """Raised on authentication failure with Azure Key Vault."""


class AzureKeyVaultKeyError(Exception):
    """Raised when a key operation fails (missing key, access denied, etc.)."""


class AzureKeyVaultConfigurationError(Exception):
    """Raised on invalid configuration or missing required environment variables."""


class AzureKeyVaultProvider(AbstractKMS):
    """
    Production-grade Azure Key Vault provider for audit key management.

    Integrates with Azure Key Vault Secrets for secure key storage and rotation.
    Supports DefaultAzureCredential for flexible authentication (env vars, managed
    identity, service principal, etc).

    Usage:
        provider = AzureKeyVaultProvider()
        key = provider.get_audit_key("v1")

    Environment:
        AZURE_KEY_VAULT_URL: Vault URL (required, e.g. https://myvault.vault.azure.net/)
        AZURE_AUDIT_KEY_NAME: Secret name (optional, default: quantum-shield-audit)
    """

    def __init__(
        self,
        vault_url: str | None = None,
        key_name: str | None = None,
    ) -> None:
        """
        Initialize Azure Key Vault provider.

        Args:
            vault_url: Azure Key Vault URL. Defaults to AZURE_KEY_VAULT_URL env var.
            key_name: Secret name for audit key. Defaults to quantum-shield-audit.

        Raises:
            AzureKeyVaultConfigurationError: If vault_url is missing or invalid.
        """
        self.vault_url = vault_url or os.environ.get("AZURE_KEY_VAULT_URL", "")
        self.key_name = key_name or os.environ.get(
            "AZURE_AUDIT_KEY_NAME", "quantum-shield-audit"
        )

        if not self.vault_url:
            raise AzureKeyVaultConfigurationError(
                "AZURE_KEY_VAULT_URL is required (e.g. https://myvault.vault.azure.net/)"
            )

        if not self.vault_url.startswith("https://"):
            raise AzureKeyVaultConfigurationError(
                f"AZURE_KEY_VAULT_URL must use https (got '{self.vault_url}')"
            )

        self._client: Any = None
        self._cache: dict[str, bytes | None] = {}
        self._cache_ttl: float = 300.0  # 5 minutes
        self._cache_timestamps: dict[str, float] = {}

        # Local env fallback for dev/test
        self._local_fallback = self._load_env_keys()

    @staticmethod
    def _load_env_keys() -> dict[str, bytes]:
        """Load keys from environment variables as fallback."""
        keys: dict[str, bytes] = {}
        for name, value in os.environ.items():
            if name.startswith("AUDIT_KEY_"):
                version = name.split("AUDIT_KEY_", 1)[1].lower()
                if len(value) >= 32:
                    keys[version] = value.encode()
        if not keys and "AUDIT_KEY" in os.environ:
            keys["v1"] = os.environ["AUDIT_KEY"].encode()
        return keys

    def _get_client(self) -> Any:
        """Get or create Azure Key Vault client (lazy initialization)."""
        if self._client is not None:
            return self._client

        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential

            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=self.vault_url, credential=credential)
            return self._client
        except ImportError as exc:
            raise AzureKeyVaultConnectionError(
                "Azure SDK not installed: pip install azure-keyvault-secrets azure-identity"
            ) from exc

    def get_audit_key(self, version: str) -> bytes | None:
        """
        Retrieve an audit key from Azure Key Vault.

        Args:
            version: Key version identifier (e.g. "v1", "v2"). For Azure,
                    this corresponds to secret versions.

        Returns:
            Key as bytes, or None if not found.

        Raises:
            AzureKeyVaultConnectionError: If Key Vault is unreachable.
            AzureKeyVaultAuthError: If authentication fails.
        """
        now = time.time()

        # Check cache
        if version in self._cache:
            ts = self._cache_timestamps.get(version, 0)
            if now - ts < self._cache_ttl:
                return self._cache[version]

        # Check local env fallback first (for dev/test)
        if version in self._local_fallback:
            key = self._local_fallback[version]
            self._cache[version] = key
            self._cache_timestamps[version] = now
            return key

        # Try to fetch from Azure Key Vault
        try:
            client = self._get_client()

            # For Azure, we use secret name + version pattern
            # e.g., audit-key-v1 or audit-key-v2
            secret_name = f"{self.key_name}-{version}"

            try:
                secret = client.get_secret(secret_name)
                key = secret.value.encode("utf-8") if isinstance(secret.value, str) else secret.value
                self._cache[version] = key
                self._cache_timestamps[version] = now
                return key
            except Exception as exc:
                if "not found" in str(exc).lower() or "404" in str(exc):
                    return None
                raise AzureKeyVaultConnectionError(
                    f"Failed to retrieve secret '{secret_name}': {exc}"
                ) from exc

        except AzureKeyVaultConnectionError:
            # On connection failure, try local fallback
            if version in self._local_fallback:
                key = self._local_fallback[version]
                self._cache[version] = key
                self._cache_timestamps[version] = now
                return key
            raise
        except Exception as exc:
            if "Unauthorized" in str(exc) or "403" in str(exc):
                raise AzureKeyVaultAuthError(
                    f"Azure Key Vault authentication failed: {exc}. "
                    "Check DefaultAzureCredential configuration."
                ) from exc
            raise AzureKeyVaultConnectionError(
                f"Unexpected Azure Key Vault error: {exc}"
            ) from exc

    def store_audit_key(self, version: str, key_value: bytes) -> None:
        """
        Store an audit key in Azure Key Vault.

        Args:
            version: Key version identifier.
            key_value: Raw key bytes (must be >= 32 bytes).

        Raises:
            ValueError: If key is too short.
            AzureKeyVaultConnectionError: If Key Vault is unreachable.
        """
        if len(key_value) < 32:
            raise ValueError(
                f"Key must be at least 32 bytes (got {len(key_value)})"
            )

        try:
            client = self._get_client()
            secret_name = f"{self.key_name}-{version}"
            key_str = key_value.decode("utf-8") if isinstance(key_value, bytes) else key_value

            client.set_secret(secret_name, key_str)

            # Invalidate cache
            self._cache.pop(version, None)
            self._cache_timestamps.pop(version, None)

        except Exception as exc:
            if "Unauthorized" in str(exc) or "403" in str(exc):
                raise AzureKeyVaultAuthError(
                    f"Azure Key Vault authentication failed: {exc}"
                ) from exc
            raise AzureKeyVaultConnectionError(
                f"Failed to store secret: {exc}"
            ) from exc

    def health_check(self) -> dict[str, Any]:
        """
        Perform a health check against Azure Key Vault.

        Returns:
            dict with health status information.
        """
        try:
            client = self._get_client()
            client.get_secret(f"{self.key_name}-v1")
            return {
                "provider": "azure_keyvault",
                "vault_url": self.vault_url,
                "key_name": self.key_name,
                "status": "available",
            }
        except Exception as exc:
            return {
                "provider": "azure_keyvault",
                "vault_url": self.vault_url,
                "key_name": self.key_name,
                "status": "unavailable",
                "error": str(exc),
            }


__all__ = [
    "AzureKeyVaultProvider",
    "AzureKeyVaultConnectionError",
    "AzureKeyVaultAuthError",
    "AzureKeyVaultKeyError",
    "AzureKeyVaultConfigurationError",
]

