"""
aws_kms.py — AWS KMS provider with DEK Key Wrapping + audit key retrieval.

Implements:
  - KeyWrapper: wrap_key() / unwrap_key() via KMS Encrypt/Decrypt (RSAES_OAEP_SHA_256)
  - SecretProvider: get_audit_key() via KMS Decrypt of encrypted env blobs

Uses tenacity for async retry with exponential backoff on transient errors.

Environment Variables:
    AWS_KMS_KEY_ID           CMK ARN or alias (e.g. alias/quantum-shield-dek)
    AWS_REGION               AWS region (e.g. eu-west-1)
    AWS_ACCESS_KEY_ID        Explicit access key (optional — uses IAM role if absent)
    AWS_SECRET_ACCESS_KEY    Explicit secret key (optional)
    KMS_MAX_RETRIES          Max retry attempts (default: 3)
    KMS_RETRY_MIN            Min retry delay seconds (default: 1.0)
    KMS_RETRY_MAX            Max retry delay seconds (default: 10.0)
    AUDIT_KEY_ENCRYPTED_V1   Base64-encoded encrypted audit key blob (optional)
"""

from __future__ import annotations

import base64
import json
import logging as _logging
import os
import time
from dataclasses import dataclass
from typing import Any

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
_DEFAULT_REGION: str = "eu-west-1"
_DEFAULT_MAX_RETRIES: int = 3
_DEFAULT_RETRY_MIN: float = 1.0
_DEFAULT_RETRY_MAX: float = 10.0
_CACHE_TTL: float = 300.0  # 5 minutes


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class AWSKMSConfig:
    """Immutable configuration for AWS KMS provider."""

    key_id: str = ""
    region: str = _DEFAULT_REGION
    max_retries: int = _DEFAULT_MAX_RETRIES
    retry_min: float = _DEFAULT_RETRY_MIN
    retry_max: float = _DEFAULT_RETRY_MAX
    access_key_id: str | None = None
    secret_access_key: str | None = None

    def __post_init__(self) -> None:
        self.key_id = self.key_id or os.environ.get("AWS_KMS_KEY_ID", "")
        self.region = self.region or os.environ.get("AWS_REGION", _DEFAULT_REGION)
        if os.environ.get("KMS_MAX_RETRIES"):
            self.max_retries = int(os.environ["KMS_MAX_RETRIES"])
        if os.environ.get("KMS_RETRY_MIN"):
            self.retry_min = float(os.environ["KMS_RETRY_MIN"])
        if os.environ.get("KMS_RETRY_MAX"):
            self.retry_max = float(os.environ["KMS_RETRY_MAX"])
        self.access_key_id = self.access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_access_key = self.secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY")

    def validate(self) -> None:
        """Validate configuration, raising ValueError on failure."""
        errors: list[str] = []
        if not self.key_id:
            errors.append("AWS_KMS_KEY_ID is required (ARN or alias)")
        if not self.region:
            errors.append("AWS_REGION is required (e.g. eu-west-1)")
        if self.max_retries < 0 or self.max_retries > 10:
            errors.append("KMS_MAX_RETRIES must be between 0 and 10")
        if errors:
            raise ValueError("AWS KMS config: " + "; ".join(errors))


# ---------------------------------------------------------------------------
# Helpers — which exceptions are retryable?
# ---------------------------------------------------------------------------
def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, KeyWrapperTransientError)


# ---------------------------------------------------------------------------
# AWS KMS Client
# ---------------------------------------------------------------------------
class AWSKMSClient:
    """Low-level boto3 client with tenacity retry and error classification."""

    WRAPPING_ALGORITHM = "RSAES_OAEP_SHA_256"

    def __init__(self, config: AWSKMSConfig) -> None:
        self._config = config
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        import boto3

        kwargs: dict[str, Any] = {"region_name": self._config.region}
        if self._config.access_key_id and self._config.secret_access_key:
            kwargs["aws_access_key_id"] = self._config.access_key_id
            kwargs["aws_secret_access_key"] = self._config.secret_access_key

        self._client = boto3.Session(**kwargs).client("kms")
        return self._client

    def _classify_error(self, exc: Exception) -> KeyWrapperError:
        """Classify a boto3 exception into domain exceptions."""
        msg = str(exc)

        # Use class names since moto may not expose the same exception attributes
        exc_class = type(exc).__name__

        if exc_class == "AccessDeniedException":
            return KeyWrapperAuthError(f"AWS KMS access denied: {msg}")
        if exc_class in ("NotFoundException", "InvalidArnException"):
            return KeyWrapperError(f"AWS KMS key not found: {self._config.key_id}")
        if exc_class == "DisabledException":
            return KeyWrapperError(f"AWS KMS key disabled: {self._config.key_id}")
        if exc_class == "PendingImportException":
            return KeyWrapperError(f"AWS KMS key pending import: {self._config.key_id}")
        if exc_class in (
            "InvalidKeyUsageException",
            "InvalidCiphertextException",
            "InvalidGrantIdException",
            "InvalidGrantTokenException",
        ):
            return KeyWrapperError(f"AWS KMS key usage error: {msg}")
        if exc_class == "UnsupportedOperationException":
            return KeyWrapperError(f"AWS KMS unsupported operation: {msg}")
        if exc_class == "KMSInvalidStateException":
            return KeyWrapperTransientError(f"AWS KMS invalid state (retriable): {msg}")
        if exc_class in (
            "KMSInternalException",
            "CloudHsmClusterException",
            "CloudHsmClusterNotActiveException",
            "CloudHsmClusterInvalidConfigurationException",
            "CloudHsmClusterNotRelatedException",
        ):
            return KeyWrapperTransientError(f"AWS KMS transient: {msg}")

        return KeyWrapperTransientError(f"AWS KMS connection error: {msg}")

    # -- tenacity-retried operations --

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def encrypt(self, plaintext: bytes, key_id: str | None = None) -> bytes:
        """Wrap a DEK via KMS Encrypt."""
        client = self._get_client()
        try:
            resp = client.encrypt(
                KeyId=key_id or self._config.key_id,
                Plaintext=plaintext,
                EncryptionAlgorithm=self.WRAPPING_ALGORITHM,
            )
            return resp["CiphertextBlob"]
        except Exception as exc:
            raise self._classify_error(exc) from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def decrypt(self, ciphertext_blob: bytes) -> bytes:
        """Unwrap a DEK via KMS Decrypt."""
        client = self._get_client()
        try:
            resp = client.decrypt(
                CiphertextBlob=ciphertext_blob,
                EncryptionAlgorithm=self.WRAPPING_ALGORITHM,
            )
            return resp["Plaintext"]
        except Exception as exc:
            raise self._classify_error(exc) from exc

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_RETRIES + 1),
        wait=wait_exponential(multiplier=1, min=_DEFAULT_RETRY_MIN, max=_DEFAULT_RETRY_MAX),
        retry=retry_if_exception(_is_retryable),
        before_sleep=before_sleep_log(_logger, _logging.WARNING),
        reraise=True,
    )
    def describe_key(self) -> dict[str, Any]:
        """Get CMK metadata."""
        client = self._get_client()
        try:
            resp = client.describe_key(KeyId=self._config.key_id)
            return resp.get("KeyMetadata", {})
        except Exception as exc:
            raise self._classify_error(exc) from exc


# ---------------------------------------------------------------------------
# AWS KMS Provider (public interface)
# ---------------------------------------------------------------------------
class AWSKMSProvider(KMSProvider):
    """
    AWS KMS provider implementing both KeyWrapper and SecretProvider.

    Key Wrapping (DEK):
        Uses KMS Encrypt/Decrypt with RSAES_OAEP_SHA_256.

    Audit Key Retrieval:
        Decrypts base64-encoded encrypted blobs stored in env vars
        (AUDIT_KEY_ENCRYPTED_V1, AUDIT_KEY_ENCRYPTED_V2, ...).

    Usage:
        provider = AWSKMSProvider()
        wrapped = provider.wrap_key(dek_bytes)
        dek = provider.unwrap_key(wrapped)
        key = provider.get_audit_key("v1")
    """

    def __init__(
        self,
        key_id: str | None = None,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        max_retries: int | None = None,
        retry_min: float | None = None,
        retry_max: float | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {}
        if key_id is not None:
            kwargs["key_id"] = key_id
        if region is not None:
            kwargs["region"] = region
        if access_key_id is not None:
            kwargs["access_key_id"] = access_key_id
        if secret_access_key is not None:
            kwargs["secret_access_key"] = secret_access_key
        if max_retries is not None:
            kwargs["max_retries"] = max_retries
        if retry_min is not None:
            kwargs["retry_min"] = retry_min
        if retry_max is not None:
            kwargs["retry_max"] = retry_max

        self._config = AWSKMSConfig(**kwargs)
        self._config.validate()
        self._client: AWSKMSClient | None = None
        self._cache: dict[str, bytes | None] = {}
        self._cache_ts: dict[str, float] = {}

    def _get_client(self) -> AWSKMSClient:
        if self._client is None:
            self._client = AWSKMSClient(self._config)
        return self._client

    # ------------------------------------------------------------------
    # KeyWrapper interface (DEK wrapping / unwrapping)
    # ------------------------------------------------------------------

    def wrap_key(self, plaintext_dek: bytes) -> str:
        """
        Wrap a DEK under the configured KMS CMK.

        Args:
            plaintext_dek: 32-byte DEK from Kyber768 KEM.

        Returns:
            Base64-encoded JSON blob with metadata and ciphertext.

        Raises:
            KeyWrapperError: If wrapping fails.
            KeyWrapperAuthError: If IAM permissions are insufficient.
        """
        client = self._get_client()
        ciphertext_blob = client.encrypt(plaintext_dek)
        payload = {
            "v": 1,
            "k": base64.b64encode(ciphertext_blob).decode(),
            "region": self._config.region,
            "key_id": self._config.key_id,
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
            KeyWrapperAuthError: If IAM permissions are insufficient.
        """
        try:
            payload = json.loads(base64.b64decode(wrapped_blob))
            ciphertext_blob = base64.b64decode(payload["k"])
        except (json.JSONDecodeError, KeyError, ValueError, Exception) as exc:
            raise KeyWrapperError(f"Invalid wrapped blob format: {exc}") from exc

        client = self._get_client()
        return client.decrypt(ciphertext_blob)

    # ------------------------------------------------------------------
    # SecretProvider interface (audit key retrieval)
    # ------------------------------------------------------------------

    def _load_env_keys(self) -> dict[str, bytes]:
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

    def get_audit_key(self, version: str) -> bytes | None:
        """
        Retrieve an audit key by version.

        Tries (in order):
          1. In-memory cache
          2. Raw audit key from env (AUDIT_KEY_v1, etc.)
          3. Encrypted blob from env (AUDIT_KEY_ENCRYPTED_V1), decrypted via KMS
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

        # 2. Raw env keys
        env_keys = self._load_env_keys()
        if version in env_keys:
            key = env_keys[version]
            self._cache[version] = key
            self._cache_ts[version] = now
            return key

        # 3. Encrypted blob in env
        encrypted_env = os.environ.get(f"AUDIT_KEY_ENCRYPTED_{version.upper()}")
        if encrypted_env:
            try:
                encrypted_blob = base64.b64decode(encrypted_env)
                client = self._get_client()
                key = client.decrypt(encrypted_blob)
                self._cache[version] = key
                self._cache_ts[version] = now
                return key
            except (KeyWrapperError, KeyWrapperAuthError) as exc:
                _logger.warning("Failed to decrypt audit key %s: %s", version, exc)
                # Fall through to None

        return None

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, Any]:
        """Check CMK reachability and status."""
        client = self._get_client()
        try:
            meta = client.describe_key()
            return {
                "provider": "aws_kms",
                "key_id": self._config.key_id,
                "region": self._config.region,
                "key_state": meta.get("KeyState", "unknown"),
                "key_usage": meta.get("KeyUsage", "unknown"),
                "status": "available",
            }
        except KeyWrapperError as exc:
            return {"provider": "aws_kms", "status": "error", "error": str(exc)}
        except KeyWrapperAuthError as exc:
            return {"provider": "aws_kms", "status": "auth_error", "error": str(exc)}


__all__ = [
    "AWSKMSProvider",
    "AWSKMSConfig",
]
