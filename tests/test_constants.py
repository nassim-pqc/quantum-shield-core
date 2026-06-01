"""
test_constants.py — Tests for application constants and enumerations.
"""

import pytest

from constants import (
    AES_GCM_NONCE_BYTES,
    API_KEY_HEADER_NAME,
    API_VERSION,
    CORRELATION_ID_HEADER,
    DB_MAX_OVERFLOW,
    DB_POOL_SIZE,
    DB_POOL_TIMEOUT_SECONDS,
    MAX_CONTEXT_LENGTH,
    MAX_PAYLOAD_DECODED_BYTES,
    MIN_AUDIT_KEY_BYTES,
    PQC_ALGORITHM,
    ApiRole,
    AuditAction,
    IntegrityDisplay,
    IntegrityStatus,
)


class TestApiRole:
    """Tests for ApiRole enum."""

    def test_operator_role_exists(self):
        """Verify OPERATOR role is defined."""
        assert ApiRole.OPERATOR == "operator"

    def test_auditor_role_exists(self):
        """Verify AUDITOR role is defined."""
        assert ApiRole.AUDITOR == "auditor"

    def test_api_roles_are_strings(self):
        """Verify roles are string enum members."""
        assert isinstance(ApiRole.OPERATOR, str)
        assert isinstance(ApiRole.AUDITOR, str)


class TestAuditAction:
    """Tests for AuditAction enum."""

    def test_key_generate_action_exists(self):
        """Verify KEY_GENERATE action is defined."""
        assert AuditAction.KEY_GENERATE == "KEY_GENERATE"

    def test_seal_action_exists(self):
        """Verify SEAL action is defined."""
        assert AuditAction.SEAL == "SEAL"

    def test_unseal_action_exists(self):
        """Verify UNSEAL action is defined."""
        assert AuditAction.UNSEAL == "UNSEAL"


class TestIntegrityStatus:
    """Tests for IntegrityStatus enum."""

    def test_pending_status_exists(self):
        """Verify PENDING status is defined."""
        assert IntegrityStatus.PENDING == "PENDING"

    def test_ok_status_exists(self):
        """Verify OK status is defined."""
        assert IntegrityStatus.OK == "OK"

    def test_fail_status_exists(self):
        """Verify FAIL status is defined."""
        assert IntegrityStatus.FAIL == "FAIL"


class TestIntegrityDisplay:
    """Tests for IntegrityDisplay enum."""

    def test_ok_display_value(self):
        """Verify OK display value."""
        assert IntegrityDisplay.OK == "OK"

    def test_fail_display_value(self):
        """Verify FAIL display value."""
        assert IntegrityDisplay.FAIL == "FAIL"


class TestHttpConstants:
    """Tests for HTTP/API constants."""

    def test_api_version_is_string(self):
        """Verify API_VERSION is a string."""
        assert isinstance(API_VERSION, str)
        assert len(API_VERSION) > 0

    def test_max_payload_is_positive_integer(self):
        """Verify MAX_PAYLOAD_DECODED_BYTES is a positive integer."""
        assert isinstance(MAX_PAYLOAD_DECODED_BYTES, int)
        assert MAX_PAYLOAD_DECODED_BYTES > 0

    def test_max_context_length_is_positive_integer(self):
        """Verify MAX_CONTEXT_LENGTH is a positive integer."""
        assert isinstance(MAX_CONTEXT_LENGTH, int)
        assert MAX_CONTEXT_LENGTH > 0

    def test_min_audit_key_bytes_is_positive_integer(self):
        """Verify MIN_AUDIT_KEY_BYTES is a positive integer."""
        assert isinstance(MIN_AUDIT_KEY_BYTES, int)
        assert MIN_AUDIT_KEY_BYTES > 0


class TestHeaderConstants:
    """Tests for header constants."""

    def test_correlation_id_header_is_string(self):
        """Verify CORRELATION_ID_HEADER is a string."""
        assert isinstance(CORRELATION_ID_HEADER, str)
        assert len(CORRELATION_ID_HEADER) > 0

    def test_api_key_header_name_is_string(self):
        """Verify API_KEY_HEADER_NAME is a string."""
        assert isinstance(API_KEY_HEADER_NAME, str)
        assert len(API_KEY_HEADER_NAME) > 0


class TestCryptoConstants:
    """Tests for cryptographic constants."""

    def test_pqc_algorithm_is_kyber768(self):
        """Verify PQC_ALGORITHM is Kyber768."""
        assert PQC_ALGORITHM == "Kyber768"

    def test_aes_gcm_nonce_bytes_is_12(self):
        """Verify AES_GCM_NONCE_BYTES is 12 (standard for GCM)."""
        assert AES_GCM_NONCE_BYTES == 12


class TestDatabaseConstants:
    """Tests for database pool constants."""

    def test_db_pool_size_is_positive_integer(self):
        """Verify DB_POOL_SIZE is a positive integer."""
        assert isinstance(DB_POOL_SIZE, int)
        assert DB_POOL_SIZE > 0

    def test_db_max_overflow_is_positive_integer(self):
        """Verify DB_MAX_OVERFLOW is a positive integer."""
        assert isinstance(DB_MAX_OVERFLOW, int)
        assert DB_MAX_OVERFLOW > 0

    def test_db_pool_timeout_is_positive_integer(self):
        """Verify DB_POOL_TIMEOUT_SECONDS is a positive integer."""
        assert isinstance(DB_POOL_TIMEOUT_SECONDS, int)
        assert DB_POOL_TIMEOUT_SECONDS > 0
