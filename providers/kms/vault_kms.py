"""
vault_kms.py — HashiCorp Vault provider with DEK Key Wrapping + audit key retrieval.

Implements:
  - KeyWrapper: wrap_key() / unwrap_key() via Vault Transit Engine
    (/v1/transit/encrypt/:key_name, /v1/transit/decrypt/:key_name)
  - SecretProvider: get_audit_key() via KV v2 secrets engine

Uses tenacity for async retry with exponential backoff on transient errors.

Environment Variables:
    VAULT_ADDR               Vault server URL (e.g. https://vault:8200)
    VAULT_TOKEN              Vault authentication token
    VAULT_TRANSIT_KEY        Transit Engine key name (default: quantum-shield-dek)
    VAULT_KV_PATH            KV v2 path for audit keys (default: quantum-shield/audit-keys)
    VAULT_KV_MOUNT           KV v2 mount point (default: secret)
    VAULT_TIMEOUT            HTTP client timeout seconds (default: 10)
    VAULT_MAX_RETRIES        Max retry attempts (default: 3)
    VAULT_RETRY_MIN          Min retry delay seconds (default: 1.0)
    VAULT_RETRY_MAX          Max retry delay seconds (default: 10.0)
    VAULT_VERIFY_SSL         TLS verification (default: true)
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

import httpx
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
_DEFAULT_TIMEOUT: float = 10.0
_DEFAULT_MAX_RETRIES: int = 3
_DEFAULT_RETRY_MIN: float = 1.0
_DEFAULT_RETRY_MAX: float = 10.0
_CACHE_TTL: float = 300.0  # 5 minutes
_MAX_PATH_DEPTH: int = 10


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class VaultKMSConfig:
    """Immutable configuration for Vault KMS provider."""

    addr: str = ""
    token: str = ""
    transit_key: str = "quantum-shield-dek"
    kv_path: str = "quantum-shield/audit-keys"
    mount_point: str = "secret"
    timeout: float = _DEFAULT_TIMEOUT
    max_retries: int = _DEFAULT_MAX_RETRIES
    retry_min: float = _DEFAULT_RETRY_MIN
    retry_max: float = _DEFAULT_RETRY_MAX
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        self.addr = self.addr or os.environ.get("VAULT_ADDR", "")
        self.token = self.token or os.environ.get("VAULT_TOKEN", "")
        self.transit_key = self.transit_key or os.environ.get(
            "VAULT_TRANSIT_KEY", "quantum-shield-dek"
        )
        self.kv_path = self.kv_path or os.environ.get("VAULT_KV_PATH", "quantum-shield/audit-keys")
        self.mount_point = self.mount_point or os.environ.get("VAULT_KV_MOUNT", "secret")
        if os.environ.get("VAULT_TIMEOUT"):
            self.timeout = float(os.environ["VAULT_TIMEOUT"])
        if os.environ.get("VAULT_MAX_RETRIES"):
            self.max_retries = int(os.environ["VAULT_MAX_RETRIES"])
        if os.environ.get("VAULT_RETRY_MIN"):
            self.retry_min = float(os.environ["VAULT_RETRY_MIN"])
        if os.environ.get("VAULT_RETRY_MAX"):
            self.retry_max = float(os.environ["VAULT_RETRY_MAX"])
        verify_env = os.environ.get("VAULT_VERIFY_SSL", "true")
        self.verify_ssl = verify_env.lower() in ("true", "1", "yes")

    def validate(self) -> None:
        """Validate configuration, raising ValueError on failure."""
        errors: list[str] = []
        if not self.addr:
            errors.append("VAULT_ADDR is required (e.g. https://vault:8200)")
        elif not re.match(r"^https?://[a-zA-Z0-9._-]+(:\d{1,5})?(/.*)?$", self.addr):
            errors.append(f"VAULT_ADDR '{self.addr}' is not a valid URL")
        if not self.token:
            errors.append("VAULT_TOKEN is required")
        elif len(self.token) < 8:
            errors.append("VAULT_TOKEN appears too short (min 8 chars)")
        path_parts = self.kv_path.split("/")
        if len(path_parts) > _MAX_PATH_DEPTH:
            errors.append(f"VAULT_KV_PATH depth exceeds {_MAX_PATH_DEPTH} segments")
        if self.timeout <= 0:
            errors.append("VAULT_TIMEOUT must be positive")
        if self.max_retries < 0 or self.max_retries > 10:
            errors.append("VAULT_MAX_RETRIES must be between 0 and 10")
        if self.retry_min <= 0:
            errors.append("VAULT_RETRY_MIN must be positive")
        if errors:
            raise ValueError("Vault KMS config: " + "; ".join(errors))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, KeyWrapperTransientError)


# ---------------------------------------------------------------------------
# Vault Client
# ---------------------------------------------------------------------------
class VaultClient:
    """
    HTTP client for HashiCorp Vault (Transit Engine + KV v2).

    Thread-safe when using separate instances. Uses tenacity for retry.
    """

    def __init__(self, config: VaultKMSConfig) -> None:
        self._config = config
        self._client: httpx.Client | None = None
        self._headers: dict[str, str] = {
            "X-Vault-Token": config.token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._config.addr.rstrip("/"),
                headers=self._headers,
                timeout=httpx.Timeout(self._config.timeout),
                verify=self._config.verify_ssl,
            )
        return self._client

    def _classify_error(self, exc: Exception, context: str = "") -> KeyWrapperError:
        msg = f"{context}: {exc}" if context else str(exc)
        if isinstance(exc, httpx.HTTPStatusError):
            if exc.response.status_code == 403:
                return KeyWrapperAuthError(f"Vault auth failed (403): {msg}")
            if exc.response.status_code == 404:
                return KeyWrapperError(f"Vault path not found: {msg}")
            if exc.response.status_code in (429, 500, 502, 503, 504):
                return KeyWrapperTransientError(
                    f"Vault transient HTTP {exc.response.status_code}: {msg}"
                )
            return KeyWrapperError(f"Vault HTTP {exc.response.status_code}: {msg}")
        if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
            return KeyWrapperTransientError(f"Vault connection error: {msg}")
        return KeyWrapperTransientError(f"Unexpected Vault error: {msg}")

    # -- tenacity-retried operations --

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def transit_encrypt(self, key_name: str, plaintext_b64: str) -> str:
        """Encrypt plaintext using Vault Transit Engine."""
        client = self._get_client()
        try:
            resp = client.post(
                f"/v1/transit/encrypt/{key_name}",
                json={"plaintext": plaintext_b64},
            )
            resp.raise_for_status()
            return resp.json()["data"]["ciphertext"]
        except Exception as exc:
            raise self._classify_error(exc, "transit_encrypt") from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def transit_decrypt(self, key_name: str, ciphertext: str) -> str:
        """Decrypt ciphertext using Vault Transit Engine."""
        client = self._get_client()
        try:
            resp = client.post(
                f"/v1/transit/decrypt/{key_name}",
                json={"ciphertext": ciphertext},
            )
            resp.raise_for_status()
            return resp.json()["data"]["plaintext"]
        except Exception as exc:
            raise self._classify_error(exc, "transit_decrypt") from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def kv_get(self, path: str) -> dict[str, Any]:
        """Read a secret from KV v2."""
        client = self._get_client()
        try:
            resp = client.get(f"/v1/{path}")
            if resp.status_code == 404:
                return {}
            resp.raise_for_status()
            data = resp.json()
            # KV v2 wraps data under data.data
            if "data" in data and isinstance(data["data"], dict):
                inner = data["data"]
                if "data" in inner:
                    return inner["data"]
                return inner
            return data
        except Exception as exc:
            raise self._classify_error(exc, "kv_get") from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def health(self) -> dict[str, Any]:
        """Check Vault server health."""
        client = self._get_client()
        try:
            resp = client.get("/v1/sys/health")
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            raise self._classify_error(exc, "health") from exc


# ---------------------------------------------------------------------------
# HashiCorp Vault KMS Provider
# ---------------------------------------------------------------------------
class HashiCorpVaultKMSProvider(KMSProvider):
    """
    HashiCorp Vault provider implementing both KeyWrapper and SecretProvider.

    Key Wrapping (DEK):
        Uses Vault Transit Engine (/v1/transit/encrypt/:key, /v1/transit/decrypt/:key).

    Audit Key Retrieval:
        Uses KV v2 secrets engine (GET /v1/:mount/data/:path).

    Usage:
        provider = HashiCorpVaultKMSProvider()
        wrapped = provider.wrap_key(dek_bytes)
        dek = provider.unwrap_key(wrapped)
        key = provider.get_audit_key("v1")
    """

    def __init__(
        self,
        addr: str | None = None,
        token: str | None = None,
        transit_key: str | None = None,
        kv_path: str | None = None,
        mount_point: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_min: float | None = None,
        retry_max: float | None = None,
        verify_ssl: bool | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {}
        if addr is not None:
            kwargs["addr"] = addr
        if token is not None:
            kwargs["token"] = token
        if transit_key is not None:
            kwargs["transit_key"] = transit_key
        if kv_path is not None:
            kwargs["kv_path"] = kv_path
        if mount_point is not None:
            kwargs["mount_point"] = mount_point
        if timeout is not None:
            kwargs["timeout"] = timeout
        if max_retries is not None:
            kwargs["max_retries"] = max_retries
        if retry_min is not None:
            kwargs["retry_min"] = retry_min
        if retry_max is not None:
            kwargs["retry_max"] = retry_max
        if verify_ssl is not None:
            kwargs["verify_ssl"] = verify_ssl

        self._config = VaultKMSConfig(**kwargs)
        self._config.validate()
        self._client: VaultClient | None = None
        self._cache: dict[str, bytes | None] = {}
        self._cache_ts: dict[str, float] = {}
        self._local_fallback = self._load_env_keys()

    @staticmethod
    def _load_env_keys() -> dict[str, bytes]:
        """Load raw audit keys from env vars as fallback."""
        keys: dict[str, bytes] = {}
        for name, value in os.environ.items():
            if name.startswith("AUDIT_KEY_"):
                version = name.split("AUDIT_KEY_", 1)[1].lower()
                if len(value) >= 32:
                    keys[version] = value.encode()
        if not keys and "AUDIT_KEY" in os.environ:
            keys["v1"] = os.environ["AUDIT_KEY"].encode()
        return keys

    def _get_client(self) -> VaultClient:
        if self._client is None:
            self._client = VaultClient(self._config)
        return self._client

    # ------------------------------------------------------------------
    # KeyWrapper interface (DEK wrapping via Transit Engine)
    # ------------------------------------------------------------------

    def wrap_key(self, plaintext_dek: bytes) -> str:
        """
        Wrap a DEK using Vault Transit Engine.

        Args:
            plaintext_dek: 32-byte DEK from Kyber768 KEM.

        Returns:
            Base64-encoded JSON blob with ciphertext and metadata.

        Raises:
            KeyWrapperError: If wrapping fails.
            KeyWrapperAuthError: If Vault token is invalid.
        """
        client = self._get_client()
        plaintext_b64 = base64.b64encode(plaintext_dek).decode()
        ciphertext = client.transit_encrypt(self._config.transit_key, plaintext_b64)
        payload = {
            "v": 1,
            "c": ciphertext,
            "transit_key": self._config.transit_key,
            "addr": self._config.addr,
        }
        return base64.b64encode(json.dumps(payload, sort_keys=True).encode()).decode()

    def unwrap_key(self, wrapped_blob: str) -> bytes:
        """
        Unwrap a previously wrapped DEK using Vault Transit Engine.

        Args:
            wrapped_blob: The blob string returned by wrap_key().

        Returns:
            The original 32-byte DEK.

        Raises:
            KeyWrapperError: If unwrapping fails.
            KeyWrapperAuthError: If Vault token is invalid.
        """
        try:
            payload = json.loads(base64.b64decode(wrapped_blob))
            ciphertext: str = payload["c"]
        except (json.JSONDecodeError, KeyError, ValueError, Exception) as exc:
            raise KeyWrapperError(f"Invalid wrapped blob format: {exc}") from exc

        client = self._get_client()
        plaintext_b64 = client.transit_decrypt(self._config.transit_key, ciphertext)
        return base64.b64decode(plaintext_b64)

    # ------------------------------------------------------------------
    # SecretProvider interface (audit key via KV v2)
    # ------------------------------------------------------------------

    def get_audit_key(self, version: str) -> bytes | None:
        """
        Retrieve an audit key from Vault KV v2 by version.

        Tries (in order):
          1. In-memory cache
          2. Local env fallback
          3. Vault KV v2 (GET /v1/:mount/data/:path)
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

        # 3. Vault KV v2
        try:
            client = self._get_client()
            kv_path = f"{self._config.mount_point}/data/{self._config.kv_path}"
            secrets = client.kv_get(kv_path)
            raw = secrets.get(version)
            if raw is None:
                return None
            key = raw.encode() if isinstance(raw, str) else raw
            if len(key) < 32:
                _logger.warning(
                    "Audit key %s from Vault is too short (%d bytes)", version, len(key)
                )
                return None
            self._cache[version] = key
            self._cache_ts[version] = now
            return key
        except KeyWrapperError:
            return None

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """Check Vault server health."""
        client = self._get_client()
        try:
            health = client.health()
            return {
                "provider": "vault",
                "addr": self._config.addr,
                "transit_key": self._config.transit_key,
                "initialized": health.get("initialized", False),
                "sealed": health.get("sealed", True),
                "version": health.get("version", "unknown"),
                "status": "available",
            }
        except KeyWrapperError as exc:
            return {"provider": "vault", "status": "error", "error": str(exc)}
        except KeyWrapperAuthError as exc:
            return {"provider": "vault", "status": "auth_error", "error": str(exc)}


__all__ = [
    "HashiCorpVaultKMSProvider",
    "VaultKMSConfig",
]
