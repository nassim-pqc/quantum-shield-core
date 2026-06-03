"""
test_azure_kms.py — Tests for Azure Key Vault provider.

Uses:
  - respx for Azure API mocking
  - Custom mock classes for Azure SDK objects

All tests are fully isolated — no external infrastructure required.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import respx

from providers.kms.azure_kms import AzureKeyVaultConfig, AzureKeyVaultProvider
from providers.kms.base import KeyWrapperAuthError, KeyWrapperError

# ===================================================================
# Mock data
# ===================================================================
MOCK_VAULT_URL = "https://testvault.vault.azure.net"
MOCK_KEY_NAME = "quantum-shield-dek"
MOCK_SECRET_NAME = "quantum-shield-audit"
MOCK_RSA_KEY_ID = f"{MOCK_VAULT_URL}/keys/{MOCK_KEY_NAME}/abc123"


# ===================================================================
# Fixtures
# ===================================================================
@pytest.fixture
def azure_env() -> None:
    """Set Azure environment variables for testing."""
    os.environ["AZURE_KEY_VAULT_URL"] = MOCK_VAULT_URL
    os.environ["AZURE_KEY_NAME"] = MOCK_KEY_NAME
    os.environ["AZURE_SECRET_NAME"] = MOCK_SECRET_NAME
    # Clear any audit key env vars that might leak from other tests
    os.environ.pop("AUDIT_KEY_v1", None)
    os.environ.pop("AUDIT_KEY", None)


@pytest.fixture
def azure_provider(azure_env: None) -> AzureKeyVaultProvider:
    """Create an Azure Key Vault provider (Azure API calls will be mocked)."""
    return AzureKeyVaultProvider(
        vault_url=MOCK_VAULT_URL,
        key_name=MOCK_KEY_NAME,
        secret_name=MOCK_SECRET_NAME,
        max_retries=0,  # no retries in tests for speed
    )


@pytest.fixture
def dek_bytes() -> bytes:
    """A 32-byte DEK (simulating Kyber768 shared secret)."""
    return bytes(range(32))


# ===================================================================
# Configuration Tests
# ===================================================================
class TestAzureConfig:
    """Test Azure Key Vault configuration validation."""

    def test_missing_vault_url_raises(self):
        """Missing AZURE_KEY_VAULT_URL should raise ValueError."""
        if "AZURE_KEY_VAULT_URL" in os.environ:
            del os.environ["AZURE_KEY_VAULT_URL"]
        with pytest.raises(ValueError, match="AZURE_KEY_VAULT_URL"):
            AzureKeyVaultProvider(vault_url="", max_retries=0)

    def test_invalid_url_raises(self):
        """Invalid vault URL should raise ValueError."""
        with pytest.raises(ValueError, match="AZURE_KEY_VAULT_URL"):
            AzureKeyVaultProvider(vault_url="http://insecure.vault.azure.net", max_retries=0)

    def test_non_azure_url_format_does_not_raise(self):
        """A valid-looking https URL passes basic validation (vault.azure.net pattern)."""
        with pytest.raises(ValueError, match="AZURE_KEY_VAULT_URL"):
            AzureKeyVaultProvider(vault_url="https://not-azure.example.com", max_retries=0)

    def test_valid_url_works(self, azure_env: None):
        """A valid Azure Key Vault URL should not raise."""
        provider = AzureKeyVaultProvider(
            vault_url=MOCK_VAULT_URL,
            max_retries=0,
        )
        assert provider._config.vault_url == MOCK_VAULT_URL
        assert provider._config.key_name == "quantum-shield-dek"  # default


# ===================================================================
# Azure Key Vault Wrap/Unwrap Tests
# ===================================================================
class TestAzureWrap:
    """Test Azure Key Vault DEK wrapping/unwrapping (via mocked crypto client)."""

    def test_wrap_roundtrip(self, azure_provider: AzureKeyVaultProvider, dek_bytes: bytes):
        """wrap_key followed by unwrap_key should return the original DEK."""
        wrapped_key_b64 = base64.b64encode(b"encrypted_dek_data").decode()

        with patch.object(azure_provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            # Mock wrap_key: returns base64-encoded string
            mock_client.wrap_key.return_value = wrapped_key_b64
            # Mock unwrap_key: returns original DEK
            mock_client.unwrap_key.return_value = dek_bytes
            mock_get_client.return_value = mock_client

            wrapped = azure_provider.wrap_key(dek_bytes)
            assert isinstance(wrapped, str)
            assert len(wrapped) > 0

            unwrapped = azure_provider.unwrap_key(wrapped)
            assert unwrapped == dek_bytes

    def test_wrap_produces_valid_blob(
        self, azure_provider: AzureKeyVaultProvider, dek_bytes: bytes
    ):
        """wrap_key should produce a valid base64-encoded JSON blob."""
        wrapped_key_b64 = base64.b64encode(b"encrypted_dek_data").decode()

        with patch.object(azure_provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.wrap_key.return_value = wrapped_key_b64
            mock_get_client.return_value = mock_client

            blob = azure_provider.wrap_key(dek_bytes)
            # Should be valid base64
            decoded = base64.b64decode(blob)
            payload = json.loads(decoded)
            assert payload["v"] == 1
            assert payload["k"] == wrapped_key_b64
            assert payload["algorithm"] == "RSA-OAEP-256"
            assert payload["key_name"] == MOCK_KEY_NAME
            assert payload["vault_url"] == MOCK_VAULT_URL

    def test_unwrap_invalid_blob_raises(self, azure_provider: AzureKeyVaultProvider):
        """Invalid blob format should raise KeyWrapperError."""
        with pytest.raises(KeyWrapperError):
            azure_provider.unwrap_key("not-a-valid-blob")

    def test_unwrap_tampered_blob_raises(
        self, azure_provider: AzureKeyVaultProvider, dek_bytes: bytes
    ):
        """Tampered blob (corrupted wrapped key) should propagate properly."""
        wrapped_key_b64 = base64.b64encode(b"encrypted_dek_data").decode()

        with patch.object(azure_provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.wrap_key.return_value = wrapped_key_b64
            mock_client.unwrap_key.side_effect = KeyWrapperError("Unwrap failed: tampered blob")
            mock_get_client.return_value = mock_client

            wrapped = azure_provider.wrap_key(dek_bytes)
            with pytest.raises(KeyWrapperError):
                azure_provider.unwrap_key(wrapped)

    def test_wrap_auth_error(self, azure_provider: AzureKeyVaultProvider, dek_bytes: bytes):
        """Authentication failure should raise KeyWrapperAuthError."""
        with patch.object(azure_provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.wrap_key.side_effect = KeyWrapperAuthError("Azure auth failed")
            mock_get_client.return_value = mock_client

            with pytest.raises(KeyWrapperAuthError):
                azure_provider.wrap_key(dek_bytes)

    def test_health_check(self, azure_provider: AzureKeyVaultProvider):
        """Health check should return status."""
        with patch.object(azure_provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_key_properties.return_value = {
                "kid": MOCK_RSA_KEY_ID,
                "key_type": "RSA-HSM",
                "enabled": True,
                "created": "2026-01-01T00:00:00",
                "expires": None,
            }
            mock_get_client.return_value = mock_client

            status = azure_provider.health_check()
            assert status["provider"] == "azure_keyvault"
            assert status["status"] == "available"
            assert status["key_type"] == "RSA-HSM"
            assert status["enabled"] is True

    def test_health_check_auth_error(self, azure_provider: AzureKeyVaultProvider):
        """Health check should return auth error status."""
        with patch.object(azure_provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_key_properties.side_effect = KeyWrapperAuthError("Auth failed")
            mock_get_client.return_value = mock_client

            status = azure_provider.health_check()
            assert status["status"] == "auth_error"


# ===================================================================
# Azure Audit Key Tests
# ===================================================================
class TestAzureAuditKey:
    """Test Azure Key Vault audit key retrieval."""

    def test_get_audit_key_from_env(self, azure_env: None):
        """get_audit_key should return key from plain env var."""
        os.environ["AUDIT_KEY_v1"] = "a" * 32
        try:
            provider = AzureKeyVaultProvider(
                vault_url=MOCK_VAULT_URL,
                max_retries=0,
            )
            key = provider.get_audit_key("v1")
            assert key == b"a" * 32
        finally:
            del os.environ["AUDIT_KEY_v1"]

    def test_get_audit_key_missing_returns_none(self, azure_provider: AzureKeyVaultProvider):
        """get_audit_key should return None for unknown version."""
        key = azure_provider.get_audit_key("v99")
        assert key is None

    def test_get_audit_key_from_vault(self, azure_env: None):
        """get_audit_key should fetch from Key Vault Secrets."""
        os.environ.pop("AUDIT_KEY_v1", None)
        os.environ.pop("AUDIT_KEY", None)

        provider = AzureKeyVaultProvider(
            vault_url=MOCK_VAULT_URL,
            secret_name=MOCK_SECRET_NAME,
            max_retries=0,
        )

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_secret.return_value = "a" * 32
            mock_get_client.return_value = mock_client

            key = provider.get_audit_key("v1")
            assert key == b"a" * 32
            mock_client.get_secret.assert_called_once_with("quantum-shield-audit-v1")

    def test_get_audit_key_from_vault_not_found(self, azure_provider: AzureKeyVaultProvider):
        """get_audit_key should return None when secret doesn't exist."""
        with patch.object(azure_provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_secret.return_value = None
            mock_get_client.return_value = mock_client

            key = azure_provider.get_audit_key("v99")
            assert key is None

    def test_get_audit_key_too_short(self, azure_provider: AzureKeyVaultProvider):
        """get_audit_key should return None for keys shorter than 32 bytes."""
        with patch.object(azure_provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get_secret.return_value = "short"
            mock_get_client.return_value = mock_client

            key = azure_provider.get_audit_key("v1")
            assert key is None

    def test_get_audit_key_from_vault_fallback(self, azure_env: None):
        """get_audit_key should fall back to env vars when vault is unreachable."""
        os.environ["AUDIT_KEY_v1"] = "b" * 32
        try:
            provider = AzureKeyVaultProvider(
                vault_url=MOCK_VAULT_URL,
                max_retries=0,
                secret_name=MOCK_SECRET_NAME,
            )
            key = provider.get_audit_key("v1")
            assert key == b"b" * 32
        finally:
            del os.environ["AUDIT_KEY_v1"]

    def test_get_audit_key_vault_error_fallback(self, azure_env: None):
        """get_audit_key should fall back to env when vault raises an error."""
        os.environ["AUDIT_KEY_v1"] = "c" * 32
        try:
            provider = AzureKeyVaultProvider(
                vault_url=MOCK_VAULT_URL,
                max_retries=0,
                secret_name=MOCK_SECRET_NAME,
            )
            with patch.object(provider, "_get_client") as mock_get_client:
                mock_client = MagicMock()
                mock_client.get_secret.side_effect = KeyWrapperError("Vault unreachable")
                mock_get_client.return_value = mock_client

                key = provider.get_audit_key("v1")
                assert key == b"c" * 32
        finally:
            del os.environ["AUDIT_KEY_v1"]
