"""
security_engine.py — Core cryptographic engine for Quantum Shield.

ML-KEM-768 (Kyber768) hybrid encryption + HMAC-SHA256 signed audit trail.
KMS abstraction supports local env keys and enterprise provider stubs.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging as _logging
import os
from datetime import UTC, datetime
from typing import Any

import oqs
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from constants import AES_GCM_NONCE_BYTES, MIN_AUDIT_KEY_BYTES, PQC_ALGORITHM
from observability.tracing import trace_crypto

# Try to import Rust engine for constant-time HMAC and AES-GCM
_RUST_ENGINE_AVAILABLE = False
try:
    import quantum_shield_engine

    _RUST_ENGINE_AVAILABLE = True
except ImportError:
    pass

_logger = _logging.getLogger(__name__)
_logger.info("rust_engine_status", extra={"loaded": _RUST_ENGINE_AVAILABLE})


def _log_rust_fallback(operation: str, exc: BaseException) -> None:
    """Warn that a Rust-engine code path fell back to the Python implementation.

    Only the operation name and the exception type are logged — never any
    plaintext, ciphertext, shared secret, audit key or other sensitive payload.
    """
    _logger.warning(
        "rust_engine_fallback",
        extra={"operation": operation, "reason": type(exc).__name__},
    )


# ---------------------------------------------------------------------------
# Key derivation
# ---------------------------------------------------------------------------
# HKDF info string: domain-separates this AES-256-GCM usage from any other use
# of the same KEM shared secret. Bumping this suffix invalidates older blobs.
_HKDF_INFO_PREFIX: bytes = b"quantum-shield-core:aes-256-gcm:v1:"


def _derive_aes_key(shared_secret: bytes, context: bytes = b"") -> bytes:
    """Derive a 32-byte AES-256 key from a KEM shared secret via HKDF-SHA256.

    Replaces a previous ``SHA-256(shared_secret)`` direct derivation, bringing the
    KDF closer to NIST SP 800-56C / RFC 5869 guidance. The caller's ``context``
    is bound into HKDF's ``info`` parameter for domain separation; the same
    context is also passed to AES-GCM as AAD by callers.

    This is an applied-crypto improvement; the engine has **not** undergone an
    independent cryptographic audit.
    """
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=_HKDF_INFO_PREFIX + context,
    ).derive(shared_secret)


# --- KMS Abstraction ---
class AbstractKMS:
    """Interface for AWS KMS / HashiCorp Vault / Azure Key Vault integrations."""

    def get_audit_key(self, version: str) -> bytes | None:
        raise NotImplementedError


class LocalEnvKMS(AbstractKMS):
    """Fallback KMS using environment variables."""

    def __init__(self, keys_dict: dict[str, bytes]) -> None:
        self._keys = keys_dict

    def get_audit_key(self, version: str) -> bytes | None:
        return self._keys.get(version)


class SecurityEngine:
    PQC_ALG: str = PQC_ALGORITHM

    def __init__(
        self,
        kms_provider: AbstractKMS | None = None,
        active_key_version: str = "v1",
        *,
        audit_key: bytes | None = None,
    ) -> None:
        if audit_key is not None:
            if len(audit_key) < MIN_AUDIT_KEY_BYTES:
                raise ValueError(f"Audit key must be at least {MIN_AUDIT_KEY_BYTES} bytes.")
            kms_provider = LocalEnvKMS({"v1": audit_key})
            active_key_version = "v1"

        if kms_provider is None:
            raise ValueError("kms_provider or audit_key is required.")

        self.kms = kms_provider
        self.active_key_version = active_key_version
        self.pqc_alg = self.PQC_ALG

        if not self.kms.get_audit_key(self.active_key_version):
            raise ValueError(f"Active audit key '{active_key_version}' not found in KMS.")

        # Optional Rust acceleration for the HMAC audit path.
        #
        # Deliberately gated to the single-key `audit_key=` construction path.
        # The Rust engine holds exactly one key and emits a fixed
        # ``key_version="v1"``; it has no view of the KMS key catalogue. Enabling
        # it for the KMS-backed path would therefore (a) break verification of
        # rotated keys, and (b) mislabel signatures whenever the active version
        # is not ``v1``. The KMS path keeps the pure-Python signer/verifier,
        # which is rotation-aware and already uses a constant-time comparison.
        self._rust_engine = None
        if _RUST_ENGINE_AVAILABLE and audit_key is not None:
            try:
                self._rust_engine = quantum_shield_engine.SecurityEngine.with_audit_key(audit_key)
            except Exception as exc:  # nosec B110 — fallback to Python is intentional
                _log_rust_fallback("init", exc)

    # ------------------------------------------------------------------
    # Post-quantum key encapsulation (ML-KEM-768 / Kyber768)
    # ------------------------------------------------------------------
    def generate_keypair(self) -> tuple[bytes, bytes]:
        """Generate a Kyber768 key pair (public, secret)."""
        with oqs.KeyEncapsulation(self.pqc_alg) as kem:
            public_key = kem.generate_keypair()
            secret_key = kem.export_secret_key()
        return public_key, secret_key

    @trace_crypto("seal")
    def encrypt_hybrid(
        self,
        public_key: bytes,
        plaintext: bytes,
        context: bytes,
    ) -> dict[str, bytes]:
        """Hybrid encrypt: Kyber768 KEM + AES-256-GCM with AAD=context."""
        with oqs.KeyEncapsulation(self.pqc_alg) as kem:
            ciphertext_pqc, shared_secret = kem.encap_secret(public_key)

        # AES-256-GCM via Python HKDF-SHA256 derivation (single canonical path).
        # The Rust engine's `encrypt_aes_gcm` is intentionally not used here
        # because it derives via SHA-256(shared_secret) — keeping a single
        # derivation path guarantees that any seal/unseal pair stays consistent.
        aes_key = _derive_aes_key(shared_secret, context)
        nonce = os.urandom(AES_GCM_NONCE_BYTES)
        encrypted_data = AESGCM(aes_key).encrypt(nonce, plaintext, context)

        return {
            "ciphertext_pqc": ciphertext_pqc,
            "nonce": nonce,
            "encrypted_data": encrypted_data,
        }

    @trace_crypto("unseal")
    def decrypt_hybrid(
        self,
        private_key: bytes,
        ciphertext_pqc: bytes,
        nonce: bytes,
        encrypted_data: bytes,
        context: bytes,
    ) -> bytes:
        """Reverse of encrypt_hybrid; raises on auth failure or wrong key."""
        with oqs.KeyEncapsulation(self.pqc_alg, secret_key=private_key) as kem:
            shared_secret = kem.decap_secret(ciphertext_pqc)

        # Mirrors encrypt_hybrid: single Python HKDF-SHA256 derivation path.
        aes_key = _derive_aes_key(shared_secret, context)
        return AESGCM(aes_key).decrypt(nonce, encrypted_data, context)

    # ------------------------------------------------------------------
    # Signed audit trail (HMAC-SHA256, key versioning)
    # ------------------------------------------------------------------
    @trace_crypto("audit_sign")
    def generate_signed_log(self, action: str, target: str, user: str) -> dict[str, Any]:
        """Produce a tamper-evident audit log with key versioning.

        Returns a dict with keys: log (dict), signature (str), key_version (str).
        The log dict is serialized with sorted keys for deterministic JSON.
        """
        log_data: dict[str, Any] = {
            "action": action,
            "key_version": self.active_key_version,
            "target": target,
            "timestamp": datetime.now(UTC).isoformat(),
            "user": user,
        }

        log_bytes = json.dumps(log_data, sort_keys=True).encode("utf-8")

        if self._rust_engine is not None:
            try:
                log_json_str, signature, key_version = self._rust_engine.generate_signed_log(
                    action, target, user
                )
                return {
                    "log": json.loads(log_json_str),
                    "signature": signature,
                    "key_version": key_version,
                }
            except Exception as exc:  # nosec B110 — fallback to Python is intentional
                _log_rust_fallback("audit_sign", exc)

        active_key = self.kms.get_audit_key(self.active_key_version)
        if active_key is None:
            raise ValueError(f"Active audit key '{self.active_key_version}' not found in KMS.")
        signature = hmac.new(active_key, log_bytes, hashlib.sha256).hexdigest()

        return {
            "log": log_data,
            "signature": signature,
            "key_version": self.active_key_version,
        }

    def verify_log(self, log_json_str: str, signature: str) -> bool:
        """Verify HMAC signature, supporting key rotation."""
        if self._rust_engine is not None:
            try:
                return self._rust_engine.verify_log(log_json_str, signature)
            except Exception as exc:  # nosec B110 — fallback to Python is intentional
                _log_rust_fallback("audit_verify", exc)

        try:
            log_data = json.loads(log_json_str)
            key_version = log_data.get("key_version", "v1")
            audit_key = self.kms.get_audit_key(key_version)
            if not audit_key:
                return False

            log_bytes = log_json_str.encode("utf-8")
            expected = hmac.new(audit_key, log_bytes, hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception:
            return False
