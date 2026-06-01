"""
base.py — Abstract interfaces for KMS providers.

Two distinct capabilities:
  - KeyWrapper: wrap/unwrap a DEK (Data Encryption Key from Kyber768 KEM)
  - SecretProvider: get/rotate/store audit keys (for HMAC audit trail)

Both AWSKMSProvider and HashiCorpVaultKMSProvider implement both interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class KeyWrapper(ABC):
    """Interface for DEK Key Wrapping (envelope encryption)."""

    @abstractmethod
    def wrap_key(self, plaintext_dek: bytes) -> str:
        """
        Wrap a Data Encryption Key under a KMS master key.

        Args:
            plaintext_dek: The DEK to wrap (32 bytes for AES-256).

        Returns:
            Serialized wrapped blob (base64-encoded JSON with metadata).
        """
        ...

    @abstractmethod
    def unwrap_key(self, wrapped_blob: str) -> bytes:
        """
        Unwrap a previously wrapped DEK.

        Args:
            wrapped_blob: The wrapped blob string from wrap_key().

        Returns:
            The original plaintext DEK.

        Raises:
            KeyWrapperError: If unwrapping fails (wrong key, tampered blob).
        """
        ...

    @abstractmethod
    def health_check(self) -> dict[str, Any]: ...


class SecretProvider(ABC):
    """Interface for audit key storage and retrieval."""

    @abstractmethod
    def get_audit_key(self, version: str) -> bytes | None:
        """
        Retrieve an audit key by version.

        Args:
            version: Key version (e.g. "v1", "v2").

        Returns:
            Key as bytes, or None if not found.
        """
        ...


class KMSProvider(KeyWrapper, SecretProvider):
    """
    Combined interface: a KMS provider can both wrap DEKs and serve audit keys.
    """

    pass


class KeyWrapperError(Exception):
    """Raised when key wrapping/unwrapping fails."""


class KeyWrapperAuthError(KeyWrapperError):
    """Raised on authentication/authorization failure."""


class KeyWrapperTransientError(KeyWrapperError):
    """Raised on transient failures (automatically retried)."""


__all__ = [
    "KeyWrapper",
    "SecretProvider",
    "KMSProvider",
    "KeyWrapperError",
    "KeyWrapperAuthError",
    "KeyWrapperTransientError",
]
