"""
vault_kms.py — Production-grade HashiCorp Vault KMS provider.

Integrates with Vault KV v2 secrets engine for audit key storage/rotation.
Full enterprise features: auth token, retry logic, timeout, async support,
connection pooling, health checks, and strict validation.

Environment Variables:
    VAULT_ADDR              Vault server URL (e.g. https://vault:8200)
    VAULT_TOKEN             Vault authentication token (short-lived preferred)
    VAULT_KV_PATH           KV v2 path (default: quantum-shield/audit-keys)
    VAULT_KV_MOUNT          KV v2 mount point (default: secret)
    VAULT_TIMEOUT           HTTP client timeout seconds (default: 10)
    VAULT_MAX_RETRIES       Max retry attempts (default: 3)
    VAULT_RETRY_DELAY       Base delay seconds (default: 1.0)
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

import httpx

from security_engine import AbstractKMS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_TIMEOUT: float = 10.0
_DEFAULT_MAX_RETRIES: int = 3
_DEFAULT_RETRY_DELAY: float = 1.0
_MAX_KEY_SIZE: int = 64
_MAX_PATH_DEPTH: int = 10

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class VaultKMSConnectionError(Exception):
    """Raised when Vault server is unreachable."""

class VaultKMSAuthError(Exception):
    """Raised on authentication failure (bad token, expired, or insufficient perms)."""

class VaultKMSKeyError(Exception):
    """Raised when key operation fails (missing key, bad format, etc.)."""

class VaultKMSConfigurationError(Exception):
    """Raised on invalid configuration or environment."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class VaultKMSConfig:
    """Immutable configuration for HashiCorp Vault provider."""

    addr: str = ""
    token: str = ""
    kv_path: str = "quantum-shield/audit-keys"
    mount_point: str = "secret"
    timeout: float = _DEFAULT_TIMEOUT
    max_retries: int = _DEFAULT_MAX_RETRIES
    retry_delay: float = _DEFAULT_RETRY_DELAY
    verify_ssl: bool = True
    _validated: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self.addr = self.addr or os.environ.get("VAULT_ADDR", "")
        self.token = self.token or os.environ.get("VAULT_TOKEN", "")
        self.kv_path = self.kv_path or os.environ.get(
            "VAULT_KV_PATH", "quantum-shield/audit-keys"
        )
        self.mount_point = self.mount_point or os.environ.get(
            "VAULT_KV_MOUNT", "secret"
        )
        timeout_env = os.environ.get("VAULT_TIMEOUT")
        if timeout_env is not None:
            self.timeout = float(timeout_env)
        max_retries_env = os.environ.get("VAULT_MAX_RETRIES")
        if max_retries_env is not None:
            self.max_retries = int(max_retries_env)
        retry_delay_env = os.environ.get("VAULT_RETRY_DELAY")
        if retry_delay_env is not None:
            self.retry_delay = float(retry_delay_env)
        verify_env = os.environ.get("VAULT_VERIFY_SSL", "true")
        self.verify_ssl = verify_env.lower() in ("true", "1", "yes")

    def validate(self) -> None:
        """Validate configuration, raising VaultKMSConfigurationError on failure."""
        errors: list[str] = []

        # Validate address
        if not self.addr:
            errors.append("VAULT_ADDR is required (e.g. https://vault:8200)")
        else:
            addr_pattern = re.compile(
                r"^https?://[a-zA-Z0-9._-]+(:\d{1,5})?(/.*)?$"
            )
            if not addr_pattern.match(self.addr):
                errors.append(f"VAULT_ADDR '{self.addr}' is not a valid URL")

        # Validate token
        if not self.token:
            errors.append("VAULT_TOKEN is required")
        elif len(self.token) < 8:
            errors.append("VAULT_TOKEN appears too short (min 8 chars)")

        # Validate path
        path_parts = self.kv_path.split("/")
        if len(path_parts) > _MAX_PATH_DEPTH:
            errors.append(f"VAULT_KV_PATH depth exceeds {_MAX_PATH_DEPTH} segments")

        # Validate numeric parameters
        if self.timeout <= 0:
            errors.append("VAULT_TIMEOUT must be positive")
        if self.max_retries < 0 or self.max_retries > 10:
            errors.append("VAULT_MAX_RETRIES must be between 0 and 10")
        if self.retry_delay <= 0:
            errors.append("VAULT_RETRY_DELAY must be positive")

        if errors:
            raise VaultKMSConfigurationError(
                "Vault KMS configuration validation failed: " + "; ".join(errors)
            )
        self._validated = True


# ---------------------------------------------------------------------------
# Vault KV v2 Client (production-grade)
# ---------------------------------------------------------------------------
class VaultKVClient:
    """
    Low-level HTTP client for HashiCorp Vault KV v2 secrets engine.

    Thread-safe when using separate instances. Supports retries with
    exponential backoff, connection pooling via httpx.AsyncClient.
    """

    def __init__(self, config: VaultKMSConfig) -> None:
        self._config = config
        self._client: httpx.AsyncClient | None = None
        self._headers: dict[str, str] = {
            "X-Vault-Token": config.token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._kv_path = f"/v1/{config.mount_point}/data/{config.kv_path}"

    async def __aenter__(self) -> VaultKVClient:
        await self._ensure_client()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._config.addr.rstrip("/"),
                headers=self._headers,
                timeout=httpx.Timeout(self._config.timeout),
                verify=self._config.verify_ssl,
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                    keepalive_expiry=30.0,
                ),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an HTTP request with retry logic."""
        client = await self._ensure_client()
        last_exc: Exception | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                response = await client.request(method, path, json=json_data)

                # Handle 403 — bad token
                if response.status_code == 403:
                    raise VaultKMSAuthError(
                        "Vault authentication failed (403 Forbidden). "
                        "Check VAULT_TOKEN and token permissions."
                    )

                # Handle 404 — path not found
                if response.status_code == 404:
                    raise VaultKMSKeyError(
                        f"Vault path not found: {path}. "
                        "Ensure the KV v2 engine is enabled and path is correct."
                    )

                response.raise_for_status()

                data: dict[str, Any] = response.json()
                # Handle Vault wrapping response
                if "data" in data and isinstance(data["data"], dict):
                    if "data" in data["data"]:  # KV v2 nested response
                        return data["data"]["data"]
                    return data["data"]
                return data

            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_exc = VaultKMSConnectionError(
                    f"Vault connection failed (attempt {attempt + 1}/"
                    f"{self._config.max_retries + 1}): {exc}"
                )
                if attempt < self._config.max_retries:
                    delay = self._config.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                continue

            except (VaultKMSAuthError, VaultKMSKeyError):
                raise

            except httpx.HTTPStatusError as exc:
                raise VaultKMSConnectionError(
                    f"Vault HTTP {exc.response.status_code}: {exc.response.text}"
                ) from exc

            except Exception as exc:
                raise VaultKMSConnectionError(
                    f"Unexpected Vault client error: {exc}"
                ) from exc

        raise VaultKMSConnectionError(
            f"Vault request failed after {self._config.max_retries + 1} attempts. "
            f"Last error: {last_exc}"
        ) from last_exc

    async def get_secret(self, key: str) -> str | None:
        """
        Retrieve a secret from KV v2 by key name.

        Args:
            key: Secret key name (e.g. "v1", "v2")

        Returns:
            Secret value as string, or None if key does not exist.
        """
        try:
            result = await self._request("GET", f"{self._kv_path}")
            if isinstance(result, dict) and key in result:
                value = result[key]
                if value is None:
                    return None
                return str(value)
            # Check nested structure
            for k, v in result.items():
                if k == key:
                    return str(v) if v is not None else None
            return None
        except VaultKMSKeyError:
            return None

    async def list_secrets(self) -> dict[str, Any]:
        """List all secrets at the configured path."""
        try:
            result = await self._request("GET", f"{self._kv_path}")
            return result if isinstance(result, dict) else {}
        except VaultKMSKeyError:
            return {}

    async def health(self) -> dict[str, Any]:
        """Check Vault server health (sys/health endpoint)."""
        return await self._request("GET", "/v1/sys/health")


# ---------------------------------------------------------------------------
# HashiCorp Vault KMS Provider (Enterprise)
# ---------------------------------------------------------------------------
class HashiCorpVaultKMSProvider(AbstractKMS):
    """
    Production-grade HashiCorp Vault KMS provider.

    Integrates with KV v2 secrets engine for secure audit key storage.
    Supports key versioning, rotation, retry logic, async operations,
    connection pooling, and comprehensive error handling.

    Usage:
        provider = HashiCorpVaultKMSProvider()
        # Or with explicit config:
        provider = HashiCorpVaultKMSProvider(
            addr="https://vault:8200",
            token="hvs.xxx..."
        )
        key = provider.get_audit_key("v1")

    Environment:
        VAULT_ADDR, VAULT_TOKEN, VAULT_KV_PATH, VAULT_KV_MOUNT,
        VAULT_TIMEOUT, VAULT_MAX_RETRIES, VAULT_RETRY_DELAY
    """

    def __init__(
        self,
        addr: str | None = None,
        token: str | None = None,
        kv_path: str | None = None,
        mount_point: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        verify_ssl: bool | None = None,
        env_fallback: bool = True,
    ) -> None:
        """
        Initialize Vault KMS provider.

        Args:
            addr: Vault server URL. Defaults to VAULT_ADDR env var.
            token: Vault auth token. Defaults to VAULT_TOKEN env var.
            kv_path: KV v2 secrets path. Defaults to VAULT_KV_PATH env var.
            mount_point: KV v2 mount point. Defaults to "secret".
            timeout: HTTP client timeout in seconds.
            max_retries: Maximum retry attempts for transient failures.
            retry_delay: Base retry delay in seconds (exponential backoff).
            verify_ssl: Whether to verify Vault TLS certificate.
            env_fallback: If True, falls back to environment variables when
                         explicit parameters are not provided.
        """
        # Build config from explicit params + env fallback
        config_kwargs: dict[str, Any] = {}
        if addr is not None:
            config_kwargs["addr"] = addr
        if token is not None:
            config_kwargs["token"] = token
        if kv_path is not None:
            config_kwargs["kv_path"] = kv_path
        if mount_point is not None:
            config_kwargs["mount_point"] = mount_point
        if timeout is not None:
            config_kwargs["timeout"] = timeout
        if max_retries is not None:
            config_kwargs["max_retries"] = max_retries
        if retry_delay is not None:
            config_kwargs["retry_delay"] = retry_delay
        if verify_ssl is not None:
            config_kwargs["verify_ssl"] = verify_ssl

        self._config = VaultKMSConfig(**config_kwargs)

        # Validate config (will raise VaultKMSConfigurationError if invalid)
        self._config.validate()

        self._client: VaultKVClient | None = None
        self._cache: dict[str, bytes | None] = {}
        self._cache_ttl: float = 300.0  # 5 minutes
        self._cache_timestamps: dict[str, float] = {}

        # Local env fallback for development/testing
        self._local_fallback = self._load_env_keys()

    @staticmethod
    def _load_env_keys() -> dict[str, bytes]:
        """Load keys from environment as fallback."""
        keys: dict[str, bytes] = {}
        for name, value in os.environ.items():
            if name.startswith("AUDIT_KEY_"):
                version = name.split("AUDIT_KEY_", 1)[1].lower()
                if len(value) >= 32:
                    keys[version] = value.encode()
        if not keys and "AUDIT_KEY" in os.environ:
            keys["v1"] = os.environ["AUDIT_KEY"].encode()
        return keys

    async def _get_client(self) -> VaultKVClient:
        """Get or create Vault KV client (lazy initialization)."""
        if self._client is None:
            self._client = VaultKVClient(self._config)
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client connection pool."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    def get_audit_key(self, version: str) -> bytes | None:
        """
        Retrieve an audit key from Vault KV v2 by version.

        Args:
            version: Key version identifier (e.g. "v1", "v2", "current")

        Returns:
            Key as bytes, or None if the key is not found.

        Raises:
            VaultKMSConnectionError: If Vault is unreachable after retries.
            VaultKMSAuthError: If token is invalid or expired.
        """
        # Check local cache first (in-memory, per-process)
        now = time.time()
        if version in self._cache:
            ts = self._cache_timestamps.get(version, 0)
            if now - ts < self._cache_ttl:
                return self._cache[version]

        # Check local env fallback (for dev/test environments)
        if version in self._local_fallback:
            key = self._local_fallback[version]
            self._cache[version] = key
            self._cache_timestamps[version] = now
            return key

        # Fetch from Vault KV v2 (synchronous wrapper around async call)
        try:
            key = asyncio.run(self._get_audit_key_async(version))
            self._cache[version] = key
            self._cache_timestamps[version] = now
            return key
        except (VaultKMSConnectionError, VaultKMSAuthError) as exc:
            # Fallback to local env keys on connection failure
            if self._local_fallback:
                key = self._local_fallback.get(version)
                if key is not None:
                    self._cache[version] = key
                    self._cache_timestamps[version] = now
                    return key
            raise

    async def _get_audit_key_async(self, version: str) -> bytes | None:
        """Async implementation of get_audit_key."""
        client = await self._get_client()
        value = await client.get_secret(version)

        if value is None:
            return None

        value = value.strip()

        # Validate key length
        if len(value) < 32:
            raise VaultKMSKeyError(
                f"Audit key '{version}' from Vault is too short "
                f"({len(value)} bytes, minimum 32). Check key configuration."
            )

        if len(value) > _MAX_KEY_SIZE:
            raise VaultKMSKeyError(
                f"Audit key '{version}' from Vault exceeds maximum size "
                f"({len(value)} > {_MAX_KEY_SIZE})."
            )

        return value.encode("utf-8")

    async def rotate_key(
        self,
        version: str,
        key_value: str,
    ) -> None:
        """
        Rotate an audit key by writing a new version to Vault KV v2.

        Args:
            version: Key version identifier (e.g. "v2", "v3")
            key_value: New key value (minimum 32 characters)

        Raises:
            ValueError: If key_value is too short.
            VaultKMSConnectionError: If Vault is unreachable.
        """
        if len(key_value) < 32:
            raise ValueError(
                f"New key must be at least 32 bytes (got {len(key_value)})"
            )

        client = await self._get_client()

        # KV v2 expects data under a "data" key
        payload: dict[str, Any] = {
            "data": {
                version: key_value,
            },
            "options": {
                "max_versions": 10,
            },
        }

        # Use raw request for write operations
        path = f"/v1/{self._config.mount_point}/data/{self._config.kv_path}"
        await client._request("POST", path, json_data=payload)

        # Invalidate cache for this version
        self._cache.pop(version, None)
        self._cache_timestamps.pop(version, None)

    async def list_key_versions(self) -> list[str]:
        """List all available key versions from Vault."""
        client = await self._get_client()
        secrets = await client.list_secrets()
        return [k for k in secrets.keys() if isinstance(k, str) and k.startswith("v")]

    async def health_check(self) -> dict[str, Any]:
        """
        Perform a health check against the Vault server.

        Returns:
            dict with health status information.

        Raises:
            VaultKMSConnectionError: If Vault is unreachable.
        """
        client = await self._get_client()
        try:
            health = await client.health()
            return {
                "provider": "vault",
                "addr": self._config.addr,
                "kv_path": f"{self._config.mount_point}/{self._config.kv_path}",
                "initialized": health.get("initialized", False),
                "sealed": health.get("sealed", True),
                "cluster_name": health.get("cluster_name", "unknown"),
                "version": health.get("version", "unknown"),
            }
        except VaultKMSConnectionError as exc:
            return {
                "provider": "vault",
                "addr": self._config.addr,
                "status": "unreachable",
                "error": str(exc),
            }


# ---------------------------------------------------------------------------
# Legacy compatibility alias
# ---------------------------------------------------------------------------
HashiCorpVaultProvider = HashiCorpVaultKMSProvider

__all__ = [
    "HashiCorpVaultKMSProvider",
    "HashiCorpVaultProvider",
    "VaultKMSConfig",
    "VaultKMSConnectionError",
    "VaultKMSAuthError",
    "VaultKMSKeyError",
    "VaultKMSConfigurationError",
]