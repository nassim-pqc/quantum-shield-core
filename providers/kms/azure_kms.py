"""
azure_kms.py — Azure Key Vault provider with DEK Key Wrapping + audit key retrieval.

Implements:
  - KeyWrapper: wrap_key() / unwrap_key() via Azure Key Vault Keys (RSA-OAEP-256)
  - SecretProvider: get_audit_key() via Azure Key Vault Secrets

Uses tenacity for async retry with exponential backoff on transient errors.

Authentication (tried in order via DefaultAzureCredential):
  1. Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
  2. Managed Identity (Azure VM, App Service, etc.)
  3. Azure CLI credential (development)
  4. Visual Studio Code / Visual Studio credential

Environment Variables:
    AZURE_KEY_VAULT_URL          Key Vault URL (e.g. https://myvault.vault.azure.net/)
    AZURE_KEY_NAME               Key name for DEK wrapping (default: quantum-shield-dek)
    AZURE_SECRET_NAME            Secret name prefix for audit keys (default: quantum-shield-audit)
    AZURE_CLIENT_ID              Azure client ID (optional — uses DefaultAzureCredential)
    AZURE_TENANT_ID              Azure tenant ID (optional)
    AZURE_CLIENT_SECRET          Azure client secret (optional)
    AZURE_MAX_RETRIES            Max retry attempts (default: 3)
    AZURE_RETRY_MIN              Min retry delay seconds (default: 1.0)
    AZURE_RETRY_MAX              Max retry delay seconds (default: 10.0)
    AUDIT_KEY_ENCRYPTED_V1       Base64-encoded encrypted audit key blob (optional — for migration)
"""

from __future__ import annotations

import base64
import json
import logging as _logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any

from azure.core.exceptions import (
    AzureError,
    ClientAuthenticationError,
    HttpResponseError,
    ResourceNotFoundError,
    ServiceRequestError,
)
from azure.identity import DefaultAzureCredential
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from providers.kms.base import (
    KeyWrapperAuthError,
    KeyWrapperError,
    KeyWrapperTransientError,
    KMSProvider,
)

_logger = _logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_MAX_RETRIES: int = 3
_DEFAULT_RETRY_MIN: float = 1.0
_DEFAULT_RETRY_MAX: float = 10.0
_CACHE_TTL: float = 300.0  # 5 minutes
_RSA_KEY_OPS: list[str] = ["wrapKey", "unwrapKey"]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class AzureKeyVaultConfig:
    """Immutable configuration for Azure Key Vault provider."""

    vault_url: str = ""
    key_name: str = "quantum-shield-dek"
    secret_name: str = "quantum-shield-audit"
    max_retries: int = _DEFAULT_MAX_RETRIES
    retry_min: float = _DEFAULT_RETRY_MIN
    retry_max: float = _DEFAULT_RETRY_MAX

    def __post_init__(self) -> None:
        self.vault_url = self.vault_url or os.environ.get("AZURE_KEY_VAULT_URL", "")
        self.key_name = self.key_name or os.environ.get("AZURE_KEY_NAME", "quantum-shield-dek")
        self.secret_name = self.secret_name or os.environ.get(
            "AZURE_SECRET_NAME", "quantum-shield-audit"
        )
        if os.environ.get("AZURE_MAX_RETRIES"):
            self.max_retries = int(os.environ["AZURE_MAX_RETRIES"])
        if os.environ.get("AZURE_RETRY_MIN"):
            self.retry_min = float(os.environ["AZURE_RETRY_MIN"])
        if os.environ.get("AZURE_RETRY_MAX"):
            self.retry_max = float(os.environ["AZURE_RETRY_MAX"])

    def validate(self) -> None:
        """Validate configuration, raising ValueError on failure."""
        errors: list[str] = []
        if not self.vault_url:
            errors.append("AZURE_KEY_VAULT_URL is required (e.g. https://myvault.vault.azure.net/)")
        elif not re.match(
            r"^https://[a-zA-Z0-9][a-zA-Z0-9.-]+\.vault\.azure\.net/?$", self.vault_url
        ):
            errors.append(
                f"AZURE_KEY_VAULT_URL '{self.vault_url}' is not a valid Azure Key Vault URL"
            )
        if not self.key_name:
            errors.append("AZURE_KEY_NAME is required")
        if not self.secret_name:
            errors.append("AZURE_SECRET_NAME is required")
        if self.max_retries < 0 or self.max_retries > 10:
            errors.append("AZURE_MAX_RETRIES must be between 0 and 10")
        if self.retry_min <= 0:
            errors.append("AZURE_RETRY_MIN must be positive")
        if errors:
            raise ValueError("Azure Key Vault config: " + "; ".join(errors))


# ---------------------------------------------------------------------------
# Helpers — which exceptions are retryable?
# ---------------------------------------------------------------------------
def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, KeyWrapperTransientError)


# ---------------------------------------------------------------------------
# Azure Key Vault Client
# ---------------------------------------------------------------------------
class AzureKeyVaultClient:
    """Low-level Azure Key Vault client with tenacity retry and error classification.

    Provides access to:
      - Key Vault Keys API: wrap/unwrap DEK (RSA-OAEP-256)
      - Key Vault Secrets API: get/set audit keys
      - Key Vault Keys API: get key metadata for health checks
    """

    WRAPPING_ALGORITHM = "RSA-OAEP-256"

    def __init__(self, config: AzureKeyVaultConfig) -> None:
        self._config = config
        self._credential: DefaultAzureCredential | None = None
        self._key_client: Any = None
        self._secret_client: Any = None
        self._crypto_client: Any = None

    def _get_credential(self) -> DefaultAzureCredential:
        """Get or create the Azure credential (lazy initialization)."""
        if self._credential is not None:
            return self._credential
        self._credential = DefaultAzureCredential(
            exclude_visual_studio_code_credential=False,
            exclude_interactive_browser_credential=True,
            logging_enable=False,
        )
        return self._credential

    def _get_key_client(self) -> Any:
        """Get or create the Key Vault Keys client (lazy initialization)."""
        if self._key_client is not None:
            return self._key_client
        from azure.keyvault.keys import KeyClient

        credential = self._get_credential()
        self._key_client = KeyClient(
            vault_url=self._config.vault_url,
            credential=credential,
        )
        return self._key_client

    def _get_secret_client(self) -> Any:
        """Get or create the Key Vault Secrets client (lazy initialization)."""
        if self._secret_client is not None:
            return self._secret_client
        from azure.keyvault.secrets import SecretClient

        credential = self._get_credential()
        self._secret_client = SecretClient(
            vault_url=self._config.vault_url,
            credential=credential,
        )
        return self._secret_client

    def _get_crypto_client(self) -> Any:
        """Get or create the Cryptography client (lazy initialization)."""
        if self._crypto_client is not None:
            return self._crypto_client
        from azure.keyvault.keys.crypto import CryptographyClient

        key_client = self._get_key_client()
        key = key_client.get_key(self._config.key_name)
        self._crypto_client = CryptographyClient(key, credential=self._get_credential())
        return self._crypto_client

    def _classify_error(self, exc: Exception, context: str = "") -> KeyWrapperError:
        """Classify an Azure SDK exception into domain exceptions."""
        msg = f"{context}: {exc}" if context else str(exc)

        if isinstance(exc, ClientAuthenticationError):
            return KeyWrapperAuthError(f"Azure authentication failed: {msg}")
        if isinstance(exc, ResourceNotFoundError):
            return KeyWrapperError(f"Azure resource not found: {msg}")
        if isinstance(exc, ServiceRequestError):
            return KeyWrapperTransientError(f"Azure connection error (retriable): {msg}")
        if isinstance(exc, HttpResponseError):
            status_code: int = (
                exc.status_code
                if hasattr(exc, "status_code") and exc.status_code is not None
                else 0
            )
            if status_code == 403:
                return KeyWrapperAuthError(f"Azure access denied (403): {msg}")
            if status_code == 404:
                return KeyWrapperError(f"Azure resource not found (404): {msg}")
            if status_code == 429 or status_code >= 500:
                return KeyWrapperTransientError(
                    f"Azure transient HTTP {status_code} (retriable): {msg}"
                )
            if status_code == 409:
                return KeyWrapperTransientError(f"Azure conflict (409, retriable): {msg}")
            return KeyWrapperError(f"Azure HTTP {status_code}: {msg}")
        if isinstance(exc, AzureError):
            return KeyWrapperTransientError(f"Azure transient error (retriable): {msg}")

        return KeyWrapperTransientError(f"Unexpected Azure error (retriable): {msg}")

    # -- tenacity-retried operations --

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def wrap_key(self, plaintext_dek: bytes) -> str:
        """Wrap a DEK using Azure Key Vault RSA key (RSA-OAEP-256).

        Returns the wrapped key as a base64-encoded string.
        """
        crypto_client = self._get_crypto_client()
        try:
            result = crypto_client.wrap_key(
                algorithm=self.WRAPPING_ALGORITHM,
                key=plaintext_dek,
            )
            return base64.b64encode(result.encrypted_key).decode()
        except Exception as exc:
            raise self._classify_error(exc, "wrap_key") from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def unwrap_key(self, wrapped_key_b64: str) -> bytes:
        """Unwrap a DEK using Azure Key Vault RSA key (RSA-OAEP-256).

        Args:
            wrapped_key_b64: Base64-encoded wrapped key from wrap_key().

        Returns:
            The original plaintext DEK.
        """
        crypto_client = self._get_crypto_client()
        try:
            wrapped_bytes = base64.b64decode(wrapped_key_b64)
            result = crypto_client.unwrap_key(
                algorithm=self.WRAPPING_ALGORITHM,
                encrypted_key=wrapped_bytes,
            )
            return result.key
        except Exception as exc:
            raise self._classify_error(exc, "unwrap_key") from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def get_secret(self, secret_name: str) -> str | None:
        """Get a secret from Azure Key Vault.

        Returns:
            The secret value as string, or None if not found.
        """
        secret_client = self._get_secret_client()
        try:
            secret = secret_client.get_secret(secret_name)
            return secret.value
        except ResourceNotFoundError:
            return None
        except Exception as exc:
            raise self._classify_error(exc, f"get_secret({secret_name})") from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def set_secret(self, secret_name: str, value: str) -> None:
        """Set a secret in Azure Key Vault."""
        secret_client = self._get_secret_client()
        try:
            secret_client.set_secret(secret_name, value)
        except Exception as exc:
            raise self._classify_error(exc, f"set_secret({secret_name})") from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def _get_rsa_key_for_testing(self) -> Any:
        """Get a reference to the RSA key for use in testing.

        Only used in test environments where we need to mock at the key level.
        """
        from azure.keyvault.keys import KeyClient

        credential = self._get_credential()
        client = KeyClient(vault_url=self._config.vault_url, credential=credential)
        return client.get_key(self._config.key_name)

    def get_key_properties(self) -> dict[str, Any]:
        """Get RSA key metadata for health checking."""
        key_client = self._get_key_client()
        try:
            key = key_client.get_key(self._config.key_name)
            _enabled = None
            _created = None
            _expires = None
            if hasattr(key, "properties"):
                if hasattr(key.properties, "enabled"):
                    _enabled = key.properties.enabled
                if hasattr(key.properties, "created_on") and key.properties.created_on:
                    _created = key.properties.created_on.isoformat()
                if hasattr(key.properties, "expires_on") and key.properties.expires_on:
                    _expires = key.properties.expires_on.isoformat()
            return {
                "kid": key.id,
                "key_type": key.key_type,
                "enabled": _enabled,
                "created": _created,
                "expires": _expires,
            }
        except Exception as exc:
            raise self._classify_error(exc, "get_key_properties") from exc


# ---------------------------------------------------------------------------
# Azure Key Vault Provider (public interface)
# ---------------------------------------------------------------------------
class AzureKeyVaultProvider(KMSProvider):
    """
    Azure Key Vault provider implementing both KeyWrapper and SecretProvider.

    Key Wrapping (DEK):
        Uses Azure Key Vault Keys (RSA-OAEP-256) via the CryptographyClient.
        Requires a pre-created RSA key in the vault (e.g., 'quantum-shield-dek').

    Audit Key Retrieval:
        Uses Azure Key Vault Secrets via the SecretClient.
        Secrets are stored with a naming pattern: '{secret_name}-{version}'
        (e.g., 'quantum-shield-audit-v1', 'quantum-shield-audit-v2').

    Environment Fallback:
        Falls back to AUDIT_KEY_vX environment variables if Key Vault is unreachable
        or the secret doesn't exist (useful for development/testing).

    Usage:
        provider = AzureKeyVaultProvider()
        wrapped = provider.wrap_key(dek_bytes)
        dek = provider.unwrap_key(wrapped)
        key = provider.get_audit_key("v1")
    """

    def __init__(
        self,
        vault_url: str | None = None,
        key_name: str | None = None,
        secret_name: str | None = None,
        max_retries: int | None = None,
        retry_min: float | None = None,
        retry_max: float | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {}
        if vault_url is not None:
            kwargs["vault_url"] = vault_url
        if key_name is not None:
            kwargs["key_name"] = key_name
        if secret_name is not None:
            kwargs["secret_name"] = secret_name
        if max_retries is not None:
            kwargs["max_retries"] = max_retries
        if retry_min is not None:
            kwargs["retry_min"] = retry_min
        if retry_max is not None:
            kwargs["retry_max"] = retry_max

        self._config = AzureKeyVaultConfig(**kwargs)
        self._config.validate()
        self._client: AzureKeyVaultClient | None = None
        self._cache: dict[str, bytes | None] = {}
        self._cache_ts: dict[str, float] = {}
        self._local_fallback = self._load_env_keys()

    @staticmethod
    def _load_env_keys() -> dict[str, bytes]:
        """Load raw audit keys from env vars as fallback."""
        keys: dict[str, bytes] = {}
        for name, value in os.environ.items():
            if name.startswith("AUDIT_KEY_") and not name.startswith("AUDIT_KEY_ENCRYPTED_"):
                version = name.split("AUDIT_KEY_", 1)[1].lower()
                if len(value) >= 32:
                    keys[version] = value.encode()
        if not keys and "AUDIT_KEY" in os.environ:
            keys["v1"] = os.environ["AUDIT_KEY"].encode()
        return keys

    def _get_client(self) -> AzureKeyVaultClient:
        if self._client is None:
            self._client = AzureKeyVaultClient(self._config)
        return self._client

    # ------------------------------------------------------------------
    # KeyWrapper interface (DEK wrapping / unwrapping)
    # ------------------------------------------------------------------

    def wrap_key(self, plaintext_dek: bytes) -> str:
        """
        Wrap a DEK using Azure Key Vault RSA key (RSA-OAEP-256).

        Args:
            plaintext_dek: 32-byte DEK from Kyber768 KEM.

        Returns:
            Base64-encoded JSON blob with metadata and wrapped key.

        Raises:
            KeyWrapperError: If wrapping fails.
            KeyWrapperAuthError: If Azure credentials are insufficient.
        """
        client = self._get_client()
        wrapped_b64 = client.wrap_key(plaintext_dek)
        payload = {
            "v": 1,
            "k": wrapped_b64,
            "algorithm": AzureKeyVaultClient.WRAPPING_ALGORITHM,
            "key_name": self._config.key_name,
            "vault_url": self._config.vault_url,
        }
        return base64.b64encode(json.dumps(payload, sort_keys=True).encode()).decode()

    def unwrap_key(self, wrapped_blob: str) -> bytes:
        """
        Unwrap a previously wrapped DEK.

        Args:
            wrapped_blob: The blob string returned by wrap_key().

        Returns:
            The original 32-byte DEK.

        Raises:
            KeyWrapperError: If unwrapping fails (wrong key, tampered blob).
            KeyWrapperAuthError: If Azure credentials are insufficient.
        """
        try:
            payload = json.loads(base64.b64decode(wrapped_blob))
            wrapped_key_b64: str = payload["k"]
        except (json.JSONDecodeError, KeyError, ValueError, Exception) as exc:
            raise KeyWrapperError(f"Invalid wrapped blob format: {exc}") from exc

        client = self._get_client()
        return client.unwrap_key(wrapped_key_b64)

    # ------------------------------------------------------------------
    # SecretProvider interface (audit key retrieval)
    # ------------------------------------------------------------------

    def get_audit_key(self, version: str) -> bytes | None:
        """
        Retrieve an audit key by version.

        Tries (in order):
          1. In-memory cache
          2. Local env fallback (AUDIT_KEY_v1, etc.)
          3. Azure Key Vault Secrets (quantum-shield-audit-v1, etc.)
          4. None

        Args:
            version: Key version (e.g. "v1", "v2").

        Returns:
            Key as bytes, or None if not found.
        """
        now = time.time()

        # 1. Cache
        if version in self._cache:
            ts = self._cache_ts.get(version, 0)
            if now - ts < _CACHE_TTL:
                return self._cache[version]

        # 2. Local env fallback
        if version in self._local_fallback:
            key = self._local_fallback[version]
            self._cache[version] = key
            self._cache_ts[version] = now
            return key

        # 3. Azure Key Vault Secrets
        try:
            client = self._get_client()
            secret_name = f"{self._config.secret_name}-{version}"
            secret_value = client.get_secret(secret_name)
            if secret_value is None:
                return None
            key = secret_value.encode("utf-8") if isinstance(secret_value, str) else secret_value
            if len(key) < 32:
                _logger.warning(
                    "Audit key %s from Azure Key Vault is too short (%d bytes)",
                    version,
                    len(key),
                )
                return None
            self._cache[version] = key
            self._cache_ts[version] = now
            return key
        except (KeyWrapperError, KeyWrapperAuthError) as exc:
            _logger.warning("Failed to retrieve audit key %s from Azure: %s", version, exc)
            # On failure, try local fallback
            if version in self._local_fallback:
                key = self._local_fallback[version]
                self._cache[version] = key
                self._cache_ts[version] = now
                return key
            return None

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """Check Azure Key Vault reachability and key status."""
        client = self._get_client()
        try:
            props = client.get_key_properties()
            return {
                "provider": "azure_keyvault",
                "vault_url": self._config.vault_url,
                "key_name": self._config.key_name,
                "key_type": props.get("key_type", "unknown"),
                "enabled": props.get("enabled"),
                "status": "available",
            }
        except KeyWrapperAuthError as exc:
            return {
                "provider": "azure_keyvault",
                "vault_url": self._config.vault_url,
                "status": "auth_error",
                "error": str(exc),
            }
        except KeyWrapperError as exc:
            return {
                "provider": "azure_keyvault",
                "vault_url": self._config.vault_url,
                "status": "error",
                "error": str(exc),
            }


__all__ = [
    "AzureKeyVaultProvider",
    "AzureKeyVaultConfig",
]
