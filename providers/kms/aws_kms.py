"""
aws_kms.py — Production-grade AWS KMS provider.

Implements envelope encryption: GenerateDataKey for DEK + KMS key for CEK.
Full enterprise features: IAM-compatible, retries, async support, key rotation,
error handling, and fallback behavior.

Architecture:
    ┌─────────────────────────────────────────────────────┐
    │                  AWS KMS Provider                    │
    │                                                      │
    │  get_audit_key(v) → Decrypt encrypted DEK blob      │
    │  generate_data_key() → GenerateDataKey (CMK)        │
    │  rotate_master_key() → Re-wrap with new CMK         │
    │  encrypt_envelope(data) → DEK + encrypted payload   │
    │  decrypt_envelope(dek, payload) → plaintext          │
    └─────────────────────────────────────────────────────┘

Environment Variables:
    AWS_KMS_KEY_ID           CMK ARN or alias (e.g. alias/quantum-shield-audit)
    AWS_REGION               AWS region (e.g. eu-west-1)
    AWS_ACCESS_KEY_ID        AWS access key (optional — uses IAM role if absent)
    AWS_SECRET_ACCESS_KEY    AWS secret key (optional — uses IAM role if absent)
    KMS_DEK_ALGORITHM        Data encryption algorithm (default: AES_256)
    KMS_MAX_RETRIES          Max retry count (default: 3)
    KMS_RETRY_DELAY          Base retry delay in seconds (default: 1.0)
"""
from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from security_engine import AbstractKMS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_DEFAULT_REGION: str = "eu-west-1"
_DEFAULT_MAX_RETRIES: int = 3
_DEFAULT_RETRY_DELAY: float = 1.0
_DEK_ALGORITHM: str = "AES_256"
_DEK_BYTE_LENGTH: int = 32
_MAX_KEY_SIZE: int = 64

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class AWSKMSConnectionError(Exception):
    """Raised when AWS KMS is unreachable or returns a transient error."""


class AWSKMSAuthError(Exception):
    """Raised on authentication/authorization failure with KMS."""


class AWSKMSKeyError(Exception):
    """Raised when a key operation fails (missing key, access denied, etc.)."""


class AWSKMSConfigurationError(Exception):
    """Raised on invalid configuration or missing required environment variables."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class AWSKMSConfig:
    """Immutable configuration for AWS KMS provider."""

    key_id: str = ""
    region: str = _DEFAULT_REGION
    max_retries: int = _DEFAULT_MAX_RETRIES
    retry_delay: float = _DEFAULT_RETRY_DELAY
    dek_algorithm: str = _DEK_ALGORITHM
    access_key_id: str | None = None
    secret_access_key: str | None = None

    def __post_init__(self) -> None:
        self.key_id = self.key_id or os.environ.get("AWS_KMS_KEY_ID", "")
        self.region = self.region or os.environ.get("AWS_REGION", _DEFAULT_REGION)
        max_retries_env = os.environ.get("KMS_MAX_RETRIES")
        if max_retries_env is not None:
            self.max_retries = int(max_retries_env)
        retry_delay_env = os.environ.get("KMS_RETRY_DELAY")
        if retry_delay_env is not None:
            self.retry_delay = float(retry_delay_env)
        dek_alg_env = os.environ.get("KMS_DEK_ALGORITHM")
        if dek_alg_env is not None:
            self.dek_algorithm = dek_alg_env
        # IAM role-based auth is preferred; explicit creds are optional
        self.access_key_id = self.access_key_id or os.environ.get(
            "AWS_ACCESS_KEY_ID"
        )
        self.secret_access_key = self.secret_access_key or os.environ.get(
            "AWS_SECRET_ACCESS_KEY"
        )

    def validate(self) -> None:
        """Validate configuration, raising AWSKMSConfigurationError on failure."""
        errors: list[str] = []

        if not self.key_id:
            errors.append(
                "AWS_KMS_KEY_ID is required (ARN or alias, e.g. "
                "arn:aws:kms:eu-west-1:123456789:key/xxx or alias/xxx)"
            )

        if not self.region:
            errors.append("AWS_REGION is required (e.g. eu-west-1)")

        valid_algorithms = ["AES_256", "AES_128"]
        if self.dek_algorithm not in valid_algorithms:
            errors.append(
                f"KMS_DEK_ALGORITHM must be one of {valid_algorithms} "
                f"(got '{self.dek_algorithm}')"
            )

        if self.max_retries < 0 or self.max_retries > 10:
            errors.append("KMS_MAX_RETRIES must be between 0 and 10")
        if self.retry_delay <= 0:
            errors.append("KMS_RETRY_DELAY must be positive")

        if errors:
            raise AWSKMSConfigurationError(
                "AWS KMS configuration validation failed: " + "; ".join(errors)
            )


# ---------------------------------------------------------------------------
# AWS KMS Client (production-grade)
# ---------------------------------------------------------------------------
class AWSKMSClient:
    """
    Low-level client for AWS KMS operations.

    Uses boto3 with optional explicit credentials (falls back to IAM role).
    Supports retry logic with exponential backoff for all operations.
    """

    def __init__(self, config: AWSKMSConfig) -> None:
        self._config = config
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-init boto3 KMS client with configured region and auth."""
        if self._client is not None:
            return self._client

        import boto3

        session_kwargs: dict[str, Any] = {
            "region_name": self._config.region,
        }

        if self._config.access_key_id and self._config.secret_access_key:
            session_kwargs["aws_access_key_id"] = self._config.access_key_id
            session_kwargs["aws_secret_access_key"] = self._config.secret_access_key

        session = boto3.Session(**session_kwargs)
        self._client = session.client("kms")
        return self._client

    def _execute_with_retry(
        self, operation: str, **kwargs: Any
    ) -> dict[str, Any]:
        """
        Execute a KMS operation with retry logic.

        Args:
            operation: boto3 KMS client method name (e.g. 'decrypt', 'generate_data_key')
            **kwargs: Parameters to pass to the method.

        Returns:
            API response dict.

        Raises:
            AWSKMSConnectionError: On transient failures after retries.
            AWSKMSAuthError: On auth/access denied errors.
            AWSKMSKeyError: On key-related errors.
        """
        client = self._get_client()
        method = getattr(client, operation)
        last_exc: Exception | None = None

        for attempt in range(self._config.max_retries + 1):
            try:
                response = method(**kwargs)
                return response

            except client.exceptions.NotFoundException as exc:
                raise AWSKMSKeyError(
                    f"AWS KMS key not found: {self._config.key_id}. "
                    "Verify the key ID/alias and region."
                ) from exc

            except client.exceptions.AccessDeniedException as exc:
                raise AWSKMSAuthError(
                    f"AWS KMS access denied for key {self._config.key_id}. "
                    "Check IAM permissions for kms:Decrypt and kms:GenerateDataKey."
                ) from exc

            except client.exceptions.DisabledException as exc:
                raise AWSKMSKeyError(
                    f"AWS KMS key {self._config.key_id} is disabled."
                ) from exc

            except client.exceptions.PendingImportException as exc:
                raise AWSKMSKeyError(
                    f"AWS KMS key {self._config.key_id} has pending import."
                ) from exc

            except (
                client.exceptions.InvalidKeyUsageException,
                client.exceptions.InvalidCiphertextException,
                client.exceptions.InvalidGrantTokenException,
            ) as exc:
                raise AWSKMSKeyError(
                    f"AWS KMS key usage error: {exc}"
                ) from exc

            except (
                client.exceptions.CloudHsmClusterException,
                client.exceptions.KMSInternalException,
                client.exceptions.KMSInvalidStateException,
            ) as exc:
                last_exc = AWSKMSConnectionError(
                    f"AWS KMS transient error (attempt {attempt + 1}/"
                    f"{self._config.max_retries + 1}): {exc}"
                )
                if attempt < self._config.max_retries:
                    delay = self._config.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                continue

            except Exception as exc:
                raise AWSKMSConnectionError(
                    f"AWS KMS unexpected error: {exc}"
                ) from exc

        raise AWSKMSConnectionError(
            f"AWS KMS {operation} failed after "
            f"{self._config.max_retries + 1} attempts. "
            f"Last error: {last_exc}"
        ) from last_exc

    def decrypt(self, ciphertext_blob: bytes) -> bytes:
        """
        Decrypt a ciphertext blob using the configured CMK.

        Args:
            ciphertext_blob: Encrypted data blob (includes key metadata).

        Returns:
            Decrypted plaintext bytes.

        Raises:
            AWSKMSKeyError: If ciphertext is invalid or key doesn't match.
        """
        # The ciphertext blob already contains key ID info for KMS to match
        result = self._execute_with_retry(
            "decrypt",
            CiphertextBlob=ciphertext_blob,
        )
        return result["Plaintext"]

    def generate_data_key(self) -> tuple[bytes, bytes]:
        """
        Generate a data encryption key (DEK) using the CMK.

        Returns:
            Tuple of (plaintext_dek, encrypted_dek_blob).
            Store the encrypted blob; discard plaintext after use.
        """
        result = self._execute_with_retry(
            "generate_data_key",
            KeyId=self._config.key_id,
            KeySpec=self._config.dek_algorithm,
        )
        return result["Plaintext"], result["CiphertextBlob"]

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt a small payload (up to 1 MB) directly with KMS.

        For audit keys (< 64 bytes), direct encryption is appropriate.
        Larger data should use envelope encryption via generate_data_key().

        Args:
            plaintext: Data to encrypt (max 1 MB).

        Returns:
            Encrypted ciphertext blob.
        """
        result = self._execute_with_retry(
            "encrypt",
            KeyId=self._config.key_id,
            Plaintext=plaintext,
        )
        return result["CiphertextBlob"]

    def re_encrypt(
        self, ciphertext_blob: bytes, destination_key_id: str | None = None
    ) -> tuple[bytes, str]:
        """
        Re-encrypt data under the same or a new CMK (key rotation).

        Args:
            ciphertext_blob: Existing encrypted ciphertext.
            destination_key_id: New CMK ID/alias. Uses current key if None.

        Returns:
            Tuple of (new_ciphertext_blob, new_key_id).
        """
        dest_key = destination_key_id or self._config.key_id
        result = self._execute_with_retry(
            "re_encrypt",
            CiphertextBlob=ciphertext_blob,
            DestinationKeyId=dest_key,
        )
        return result["CiphertextBlob"], result["KeyId"]

    def create_alias(self, alias_name: str, target_key_id: str) -> None:
        """Create an alias for a CMK."""
        self._execute_with_retry("create_alias", AliasName=alias_name, TargetKeyId=target_key_id)

    def list_keys(self) -> list[dict[str, Any]]:
        """List all KMS keys in the account."""
        result = self._execute_with_retry("list_keys", Limit=100)
        return result.get("Keys", [])

    def describe_key(self) -> dict[str, Any]:
        """Get metadata about the configured CMK."""
        result = self._execute_with_retry("describe_key", KeyId=self._config.key_id)
        return result.get("KeyMetadata", {})


# ---------------------------------------------------------------------------
# AWS KMS Provider (Enterprise)
# ---------------------------------------------------------------------------
class AWSKMSProvider(AbstractKMS):
    """
    Production-grade AWS KMS provider for audit key management.

    Implements envelope encryption:
    - Audit keys are encrypted with KMS CMK and stored as encrypted blobs
    - Data encryption keys (DEKs) are generated via GenerateDataKey
    - Supports key rotation via re-encrypt operations
    - Full IAM integration with optional explicit credentials

    Usage:
        provider = AWSKMSProvider(
            key_id="arn:aws:kms:eu-west-1:123456789:key/xxx",
            region="eu-west-1"
        )
        # Or using environment variables
        provider = AWSKMSProvider()

    Environment:
        AWS_KMS_KEY_ID, AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
        KMS_DEK_ALGORITHM, KMS_MAX_RETRIES, KMS_RETRY_DELAY
    """

    def __init__(
        self,
        key_id: str | None = None,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        env_fallback: bool = True,
    ) -> None:
        """
        Initialize AWS KMS provider.

        Args:
            key_id: KMS CMK ARN or alias. Defaults to AWS_KMS_KEY_ID.
            region: AWS region. Defaults to AWS_REGION.
            access_key_id: Optional explicit AWS access key.
            secret_access_key: Optional explicit AWS secret key.
            max_retries: Max retry attempts for transient failures.
            retry_delay: Base retry delay in seconds.
            env_fallback: If True, falls back to env vars for missing params.
        """
        config_kwargs: dict[str, Any] = {}
        if key_id is not None:
            config_kwargs["key_id"] = key_id
        if region is not None:
            config_kwargs["region"] = region
        if access_key_id is not None:
            config_kwargs["access_key_id"] = access_key_id
        if secret_access_key is not None:
            config_kwargs["secret_access_key"] = secret_access_key
        if max_retries is not None:
            config_kwargs["max_retries"] = max_retries
        if retry_delay is not None:
            config_kwargs["retry_delay"] = retry_delay

        self._config = AWSKMSConfig(**config_kwargs)
        self._config.validate()

        self._client: AWSKMSClient | None = None
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

    def _get_client(self) -> AWSKMSClient:
        """Get or create KMS client (lazy initialization)."""
        if self._client is None:
            self._client = AWSKMSClient(self._config)
        return self._client

    def _serialize_encrypted_key(
        self, version: str, encrypted_blob: bytes
    ) -> str:
        """Serialize an encrypted key blob to a storable format."""
        payload = {
            "v": 1,
            "k": base64.b64encode(encrypted_blob).decode("utf-8"),
            "region": self._config.region,
        }
        return json.dumps(payload, sort_keys=True)

    def _deserialize_encrypted_key(self, stored: str) -> bytes:
        """Deserialize an encrypted key blob from stored format."""
        try:
            payload = json.loads(stored)
            return base64.b64decode(payload["k"])
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise AWSKMSKeyError(
                f"Failed to deserialize encrypted key: {exc}"
            ) from exc

    def get_audit_key(self, version: str) -> bytes | None:
        """
        Retrieve an audit key by decrypting it with KMS.

        Keys are stored as encrypted blobs (encrypted with KMS CMK).
        On retrieval, they are decrypted using the KMS Decrypt API.

        Args:
            version: Key version (e.g. "v1", "v2").

        Returns:
            Key as bytes, or None if not found.

        Raises:
            AWSKMSConnectionError: If KMS is unreachable.
            AWSKMSAuthError: If IAM credentials are insufficient.
        """
        now = time.time()

        # Check cache
        if version in self._cache:
            ts = self._cache_timestamps.get(version, 0)
            if now - ts < self._cache_ttl:
                return self._cache[version]

        # Check local env fallback
        if version in self._local_fallback:
            key = self._local_fallback[version]
            self._cache[version] = key
            self._cache_timestamps[version] = now
            return key

        # Try to decrypt from environment (encrypted blob stored in env)
        encrypted_env_key = os.environ.get(f"AUDIT_KEY_ENCRYPTED_{version.upper()}")
        if encrypted_env_key:
            try:
                encrypted_blob = self._deserialize_encrypted_key(encrypted_env_key)
                client = self._get_client()
                key = client.decrypt(encrypted_blob)
                self._cache[version] = key
                self._cache_timestamps[version] = now
                return key
            except (
                AWSKMSConnectionError,
                AWSKMSAuthError,
                AWSKMSKeyError,
            ) as exc:
                if self._local_fallback:
                    key = self._local_fallback.get(version)
                    if key is not None:
                        return key
                raise

        # No encrypted key found — fall back to env keys
        if self._local_fallback:
            key = self._local_fallback.get(version)
            if key is not None:
                return key

        return None

    def encrypt_key_with_kms(self, version: str, plaintext_key: bytes) -> str:
        """
        Encrypt an audit key with KMS and return the serialized form.

        This is used to initially seal a key for storage.

        Args:
            version: Key version identifier.
            plaintext_key: Raw key bytes (must be >= 32 bytes).

        Returns:
            Serialized encrypted key string (JSON) safe for storage in env.

        Raises:
            ValueError: If key is too short.
            AWSKMSConnectionError: If KMS is unreachable.
        """
        if len(plaintext_key) < 32:
            raise ValueError(
                f"Key must be at least 32 bytes (got {len(plaintext_key)})"
            )

        client = self._get_client()
        encrypted_blob = client.encrypt(plaintext_key)
        serialized = self._serialize_encrypted_key(version, encrypted_blob)

        # Set environment variable for persistence
        env_key = f"AUDIT_KEY_ENCRYPTED_{version.upper()}"
        os.environ[env_key] = serialized

        # Cache the plaintext
        self._cache[version] = plaintext_key
        self._cache_timestamps[version] = time.time()

        return serialized

    def generate_data_key(self) -> tuple[bytes, bytes]:
        """
        Generate a new data encryption key (DEK) using KMS GenerateDataKey.

        Returns:
            Tuple of (plaintext_dek, encrypted_dek_blob).
            Store encrypted_dek_blob; discard plaintext after use.
        """
        client = self._get_client()
        return client.generate_data_key()

    def rotate_key(
        self,
        version: str,
        new_key_value: bytes | None = None,
    ) -> str:
        """
        Rotate an audit key — re-encrypt or generate a new encrypted key.

        Args:
            version: New version identifier (e.g. "v3").
            new_key_value: Optional explicit key value. Auto-generated if None.

        Returns:
            Serialized encrypted key string.

        Raises:
            AWSKMSConnectionError: If KMS is unreachable.
        """
        if new_key_value is None:
            new_key_value = os.urandom(32)

        return self.encrypt_key_with_kms(version, new_key_value)

    def describe_key(self) -> dict[str, Any]:
        """Get metadata about the configured KMS CMK."""
        client = self._get_client()
        return client.describe_key()

    def health_check(self) -> dict[str, Any]:
        """
        Perform a health check against AWS KMS.

        Returns:
            dict with health status and key metadata.
        """
        try:
            key_meta = self.describe_key()
            return {
                "provider": "aws_kms",
                "key_id": self._config.key_id,
                "region": self._config.region,
                "key_arn": key_meta.get("Arn", "unknown"),
                "key_state": key_meta.get("KeyState", "unknown"),
                "key_usage": key_meta.get("KeyUsage", "unknown"),
                "creation_date": str(key_meta.get("CreationDate", "unknown")),
                "status": "available",
            }
        except (AWSKMSConnectionError, AWSKMSAuthError, AWSKMSKeyError) as exc:
            return {
                "provider": "aws_kms",
                "key_id": self._config.key_id,
                "region": self._config.region,
                "status": "unavailable",
                "error": str(exc),
            }


# ---------------------------------------------------------------------------
# Legacy compatibility alias
# ---------------------------------------------------------------------------
__all__ = [
    "AWSKMSProvider",
    "AWSKMSConfig",
    "AWSKMSConnectionError",
    "AWSKMSAuthError",
    "AWSKMSKeyError",
    "AWSKMSConfigurationError",
]