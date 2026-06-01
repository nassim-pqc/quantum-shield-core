"""
test_kms_providers.py — Tests for KMS providers (AWS KMS + HashiCorp Vault).

Uses:
  - moto for AWS KMS mocking
  - respx for Vault HTTP API mocking

All tests are fully isolated — no external infrastructure required.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any
from unittest.mock import ANY

import pytest
import respx
from moto import mock_aws

from providers.kms.aws_kms import AWSKMSProvider
from providers.kms.base import KeyWrapperAuthError, KeyWrapperError
from providers.kms.vault_kms import HashiCorpVaultKMSProvider

# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture
def aws_credentials() -> None:
    """Set fake AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"


@pytest.fixture
def aws_kms_client(aws_credentials: None) -> Any:
    """Create a mock AWS KMS client and return the underlying moto backend."""
    with mock_aws():
        import boto3

        client = boto3.Session(region_name="eu-west-1").client("kms", region_name="eu-west-1")
        # Create a CMK for testing
        key = client.create_key(
            Policy="test",
            Description="Test key",
            KeyUsage="ENCRYPT_DECRYPT",
            KeySpec="RSA_4096",
        )
        key_id = key["KeyMetadata"]["KeyId"]
        os.environ["AWS_KMS_KEY_ID"] = key_id
        yield client


@pytest.fixture
def aws_provider(aws_kms_client: Any) -> AWSKMSProvider:
    """Create an AWS KMS provider connected to the mock."""
    return AWSKMSProvider(
        key_id=os.environ["AWS_KMS_KEY_ID"],
        region="eu-west-1",
        max_retries=0,  # no retries in tests for speed
    )


@pytest.fixture
def vault_env() -> None:
    """Set Vault environment variables for testing."""
    os.environ["VAULT_ADDR"] = "http://localhost:8200"
    os.environ["VAULT_TOKEN"] = "hvs.test-token-12345678"


@pytest.fixture
def vault_provider(vault_env: None) -> HashiCorpVaultKMSProvider:
    """Create a Vault provider (HTTP requests will be mocked via respx)."""
    return HashiCorpVaultKMSProvider(
        addr="http://localhost:8200",
        token="hvs.test-token-12345678",
        transit_key="quantum-shield-dek",
        max_retries=0,
    )


@pytest.fixture
def dek_bytes() -> bytes:
    """A 32-byte DEK (simulating Kyber768 shared secret)."""
    return bytes(range(32))


# ===================================================================
# AWS KMS Tests
# ===================================================================


class TestAWSKMSWrap:
    """Test AWS KMS DEK wrapping/unwrapping."""

    def test_wrap_roundtrip(self, aws_provider: AWSKMSProvider, dek_bytes: bytes):
        """wrap_key followed by unwrap_key should return the original DEK."""
        wrapped = aws_provider.wrap_key(dek_bytes)
        assert isinstance(wrapped, str)
        assert len(wrapped) > 0

        unwrapped = aws_provider.unwrap_key(wrapped)
        assert unwrapped == dek_bytes

    def test_wrap_different_each_time(self, aws_provider: AWSKMSProvider, dek_bytes: bytes):
        """Same DEK should produce different wrapped blobs (random padding)."""
        w1 = aws_provider.wrap_key(dek_bytes)
        w2 = aws_provider.wrap_key(dek_bytes)
        assert w1 != w2

    def test_unwrap_invalid_blob_raises(self, aws_provider: AWSKMSProvider):
        """Invalid blob format should raise KeyWrapperError."""
        with pytest.raises(KeyWrapperError):
            aws_provider.unwrap_key("not-a-valid-blob")

    def test_unwrap_tampered_blob_raises(self, aws_provider: AWSKMSProvider, dek_bytes: bytes):
        """Tampered blob (corrupted ciphertext) should raise KeyWrapperError."""
        wrapped = aws_provider.wrap_key(dek_bytes)
        payload = json.loads(base64.b64decode(wrapped))
        # Flip bits in the ciphertext
        corrupted_ciphertext = bytearray(base64.b64decode(payload["k"]))
        corrupted_ciphertext[0] ^= 0xFF
        payload["k"] = base64.b64encode(bytes(corrupted_ciphertext)).decode()
        tampered = base64.b64encode(json.dumps(payload, sort_keys=True).encode()).decode()

        with pytest.raises(KeyWrapperError):
            aws_provider.unwrap_key(tampered)

    def test_missing_key_id_raises(self):
        """Provider without key_id should raise ValueError on init."""
        old_key = os.environ.pop("AWS_KMS_KEY_ID", None)
        try:
            with pytest.raises(ValueError, match="AWS_KMS_KEY_ID"):
                AWSKMSProvider(key_id="", region="eu-west-1", max_retries=0)
        finally:
            if old_key:
                os.environ["AWS_KMS_KEY_ID"] = old_key

    def test_health_check(self, aws_provider: AWSKMSProvider):
        """Health check should return available status with mock."""
        status = aws_provider.health_check()
        assert status["provider"] == "aws_kms"
        assert status["status"] == "available"
        assert "key_id" in status


class TestAWSKMSAuditKey:
    """Test AWS KMS audit key retrieval."""

    def test_get_audit_key_from_env(self, aws_kms_client: Any, dek_bytes: bytes):
        """get_audit_key should return key from plain env var."""
        os.environ["AUDIT_KEY_v1"] = "a" * 32
        try:
            provider = AWSKMSProvider(
                key_id=os.environ["AWS_KMS_KEY_ID"],
                region="eu-west-1",
                max_retries=0,
            )
            key = provider.get_audit_key("v1")
            assert key == b"a" * 32
        finally:
            del os.environ["AUDIT_KEY_v1"]

    def test_get_audit_key_missing_returns_none(self, aws_provider: AWSKMSProvider):
        """get_audit_key should return None for unknown version."""
        key = aws_provider.get_audit_key("v99")
        assert key is None

    def test_get_audit_key_encrypted(self, aws_kms_client: Any, aws_provider: AWSKMSProvider):
        """get_audit_key should decrypt an encrypted blob from env."""
        # Encrypt a key via the real (mocked) KMS
        plaintext = b"x" * 32
        encrypted = aws_kms_client.encrypt(
            KeyId=os.environ["AWS_KMS_KEY_ID"],
            Plaintext=plaintext,
            EncryptionAlgorithm="RSAES_OAEP_SHA_256",
        )["CiphertextBlob"]
        os.environ["AUDIT_KEY_ENCRYPTED_V2"] = base64.b64encode(encrypted).decode()
        try:
            key = aws_provider.get_audit_key("v2")
            assert key == plaintext
        finally:
            del os.environ["AUDIT_KEY_ENCRYPTED_V2"]


# ===================================================================
# Vault Transit Engine Tests (via respx)
# ===================================================================


class TestVaultWrap:
    """Test Vault Transit Engine DEK wrapping/unwrapping."""

    def test_wrap_roundtrip(self, vault_provider: HashiCorpVaultKMSProvider, dek_bytes: bytes):
        """wrap_key then unwrap_key should return the original DEK."""
        plaintext_b64 = base64.b64encode(dek_bytes).decode()
        vault_ciphertext = "vault:v1:abc123def456"

        with respx.mock:
            # Mock transit/encrypt
            respx.post("http://localhost:8200/v1/transit/encrypt/quantum-shield-dek").respond(
                200, json={"data": {"ciphertext": vault_ciphertext}}
            )
            # Mock transit/decrypt
            respx.post("http://localhost:8200/v1/transit/decrypt/quantum-shield-dek").respond(
                200, json={"data": {"plaintext": plaintext_b64}}
            )

            wrapped = vault_provider.wrap_key(dek_bytes)
            assert isinstance(wrapped, str)

            unwrapped = vault_provider.unwrap_key(wrapped)
            assert unwrapped == dek_bytes

    def test_wrap_vault_auth_error(
        self, vault_provider: HashiCorpVaultKMSProvider, dek_bytes: bytes
    ):
        """Vault 403 should raise KeyWrapperAuthError."""
        with respx.mock:
            respx.post("http://localhost:8200/v1/transit/encrypt/quantum-shield-dek").respond(403)

            with pytest.raises(KeyWrapperAuthError):
                vault_provider.wrap_key(dek_bytes)

    def test_unwrap_invalid_blob_raises(self, vault_provider: HashiCorpVaultKMSProvider):
        """Invalid blob should raise KeyWrapperError."""
        with pytest.raises(KeyWrapperError):
            vault_provider.unwrap_key("not-valid")

    def test_wrap_vault_connection_error(
        self, vault_provider: HashiCorpVaultKMSProvider, dek_bytes: bytes
    ):
        """Connection refused should eventually raise KeyWrapperError after retries."""
        import httpx

        with respx.mock:
            route = respx.post("http://localhost:8200/v1/transit/encrypt/quantum-shield-dek")
            route.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(KeyWrapperError):
                vault_provider.wrap_key(dek_bytes)

    def test_health_check(self, vault_provider: HashiCorpVaultKMSProvider):
        """Health check should return status from Vault sys/health."""
        with respx.mock:
            respx.get("http://localhost:8200/v1/sys/health").respond(
                200, json={"initialized": True, "sealed": False, "version": "1.15.0"}
            )

            status = vault_provider.health_check()
            assert status["provider"] == "vault"
            assert status["initialized"] is True
            assert status["sealed"] is False

    def test_health_check_unreachable(self, vault_provider: HashiCorpVaultKMSProvider):
        """Health check should return error status when Vault is down."""
        import httpx

        with respx.mock:
            route = respx.get("http://localhost:8200/v1/sys/health")
            route.side_effect = httpx.ConnectError("Connection refused")

            status = vault_provider.health_check()
            assert status["status"] == "error"


class TestVaultAuditKey:
    """Test Vault KV v2 audit key retrieval."""

    def test_get_audit_key_from_vault(self, vault_env: None):
        """get_audit_key should fetch from KV v2 and return the key."""
        # Pop any leaking audit keys from test_security_engine
        os.environ.pop("AUDIT_KEY_v1", None)
        os.environ.pop("AUDIT_KEY", None)
        provider = HashiCorpVaultKMSProvider(
            addr="http://localhost:8200",
            token="hvs.test-token-12345678",
            transit_key="quantum-shield-dek",
            max_retries=0,
        )
        with respx.mock:
            respx.get("http://localhost:8200/v1/secret/data/quantum-shield/audit-keys").respond(
                200, json={"data": {"data": {"v1": "a" * 32}}}
            )
            key = provider.get_audit_key("v1")
            assert key == b"a" * 32

    def test_get_audit_key_missing(self, vault_provider: HashiCorpVaultKMSProvider):
        """get_audit_key should return None for missing version."""
        with respx.mock:
            respx.get("http://localhost:8200/v1/secret/data/quantum-shield/audit-keys").respond(
                200, json={"data": {"data": {"v1": "a" * 32}}}
            )

            key = vault_provider.get_audit_key("v99")
            assert key is None

    def test_get_audit_key_from_env_fallback(self, vault_env: None):
        """get_audit_key should fall back to env vars when Vault is down."""
        os.environ["AUDIT_KEY_v1"] = "b" * 32
        try:
            provider = HashiCorpVaultKMSProvider(
                addr="http://localhost:8200",
                token="hvs.test-token-12345678",
                max_retries=0,
            )
            key = provider.get_audit_key("v1")
            assert key == b"b" * 32
        finally:
            del os.environ["AUDIT_KEY_v1"]


class TestVaultConfig:
    """Test Vault configuration validation."""

    def test_missing_addr_raises(self):
        """Missing VAULT_ADDR should raise ValueError."""
        if "VAULT_ADDR" in os.environ:
            del os.environ["VAULT_ADDR"]
        with pytest.raises(ValueError, match="VAULT_ADDR"):
            HashiCorpVaultKMSProvider(addr="", token="hvs.valid-token-12345678")

    def test_invalid_url_raises(self):
        """Invalid VAULT_ADDR URL should raise ValueError."""
        with pytest.raises(ValueError, match="VAULT_ADDR"):
            HashiCorpVaultKMSProvider(
                addr="not-a-url",
                token="hvs.valid-token-12345678",
            )
