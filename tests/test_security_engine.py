"""
test_security_engine.py — Tests unitaires du moteur cryptographique.

Couvre :
  - Génération de paires de clés Kyber768
  - Chiffrement hybride (seal) et déchiffrement (unseal)
  - Résistance aux altérations (tamper detection via AES-GCM tag)
  - Résistance aux mauvaises clés privées
  - Enforcement du contexte AAD
  - Génération et vérification des logs HMAC-SHA256
  - Détection de falsification des logs
  - Robustesse sur les cas limites (payload vide, payload large)
"""

import hashlib
import hmac
import json
import os

import pytest

from security_engine import SecurityEngine

# ---------------------------------------------------------------------------
# Fixture moteur
# ---------------------------------------------------------------------------
AUDIT_KEY = b"test-audit-key-minimum-32-bytes-ok!"


@pytest.fixture
def engine() -> SecurityEngine:
    return SecurityEngine(audit_key=AUDIT_KEY)


# ---------------------------------------------------------------------------
# Génération de clés
# ---------------------------------------------------------------------------
class TestKeyGeneration:
    def test_generates_non_empty_keys(self, engine: SecurityEngine):
        pub, priv = engine.generate_keypair()
        assert len(pub) > 0
        assert len(priv) > 0

    def test_public_and_private_keys_are_different(self, engine: SecurityEngine):
        pub, priv = engine.generate_keypair()
        assert pub != priv

    def test_two_calls_generate_different_keys(self, engine: SecurityEngine):
        pub1, priv1 = engine.generate_keypair()
        pub2, priv2 = engine.generate_keypair()
        assert pub1 != pub2
        assert priv1 != priv2

    def test_public_key_is_kyber768_length(self, engine: SecurityEngine):
        # Kyber768 public key = 1184 bytes
        pub, _ = engine.generate_keypair()
        assert len(pub) == 1184

    def test_secret_key_is_kyber768_length(self, engine: SecurityEngine):
        # Kyber768 secret key = 2400 bytes
        _, priv = engine.generate_keypair()
        assert len(priv) == 2400


# ---------------------------------------------------------------------------
# Chiffrement hybride — Seal
# ---------------------------------------------------------------------------
class TestEncryptHybrid:
    def test_seal_returns_three_components(self, engine: SecurityEngine):
        pub, _ = engine.generate_keypair()
        result = engine.encrypt_hybrid(pub, b"data", b"ctx")
        assert "ciphertext_pqc" in result
        assert "nonce" in result
        assert "encrypted_data" in result

    def test_nonce_is_12_bytes(self, engine: SecurityEngine):
        pub, _ = engine.generate_keypair()
        result = engine.encrypt_hybrid(pub, b"data", b"ctx")
        assert len(result["nonce"]) == 12

    def test_nonce_is_random_each_call(self, engine: SecurityEngine):
        pub, _ = engine.generate_keypair()
        r1 = engine.encrypt_hybrid(pub, b"data", b"ctx")
        r2 = engine.encrypt_hybrid(pub, b"data", b"ctx")
        assert r1["nonce"] != r2["nonce"]

    def test_ciphertext_differs_from_plaintext(self, engine: SecurityEngine):
        pub, _ = engine.generate_keypair()
        plaintext = b"mon document confidentiel"
        result = engine.encrypt_hybrid(pub, plaintext, b"ctx")
        assert plaintext not in result["encrypted_data"]

    def test_seal_empty_payload(self, engine: SecurityEngine):
        pub, _ = engine.generate_keypair()
        result = engine.encrypt_hybrid(pub, b"", b"ctx")
        assert result["encrypted_data"] is not None

    def test_seal_large_payload(self, engine: SecurityEngine):
        pub, _ = engine.generate_keypair()
        large_data = os.urandom(1 * 1024 * 1024)  # 1 MB
        result = engine.encrypt_hybrid(pub, large_data, b"ctx")
        assert len(result["encrypted_data"]) > len(large_data)  # ciphertext + GCM tag


# ---------------------------------------------------------------------------
# Déchiffrement hybride — Unseal
# ---------------------------------------------------------------------------
class TestDecryptHybrid:
    def test_roundtrip_recovers_original_plaintext(self, engine: SecurityEngine):
        pub, priv = engine.generate_keypair()
        plaintext = b"M&A contract payload - CONFIDENTIAL"
        ctx = b"dossier-ma-2025"

        sealed = engine.encrypt_hybrid(pub, plaintext, ctx)
        recovered = engine.decrypt_hybrid(
            priv,
            sealed["ciphertext_pqc"],
            sealed["nonce"],
            sealed["encrypted_data"],
            ctx,
        )
        assert recovered == plaintext

    def test_roundtrip_with_empty_payload(self, engine: SecurityEngine):
        pub, priv = engine.generate_keypair()
        sealed = engine.encrypt_hybrid(pub, b"", b"ctx")
        recovered = engine.decrypt_hybrid(
            priv, sealed["ciphertext_pqc"], sealed["nonce"], sealed["encrypted_data"], b"ctx"
        )
        assert recovered == b""

    def test_wrong_private_key_raises(self, engine: SecurityEngine):
        pub, _ = engine.generate_keypair()
        _, wrong_priv = engine.generate_keypair()  # Different key pair

        sealed = engine.encrypt_hybrid(pub, b"data", b"ctx")

        with pytest.raises(Exception):
            engine.decrypt_hybrid(
                wrong_priv,
                sealed["ciphertext_pqc"],
                sealed["nonce"],
                sealed["encrypted_data"],
                b"ctx",
            )

    def test_wrong_context_raises(self, engine: SecurityEngine):
        """AAD enforcement : le contexte doit correspondre exactement."""
        pub, priv = engine.generate_keypair()
        sealed = engine.encrypt_hybrid(pub, b"data", b"bon-contexte")

        with pytest.raises(Exception):
            engine.decrypt_hybrid(
                priv,
                sealed["ciphertext_pqc"],
                sealed["nonce"],
                sealed["encrypted_data"],
                b"mauvais-contexte",  # ← contexte altéré
            )

    def test_tampered_ciphertext_raises(self, engine: SecurityEngine):
        """AES-GCM authentication tag doit détecter toute altération."""
        pub, priv = engine.generate_keypair()
        sealed = engine.encrypt_hybrid(pub, b"data", b"ctx")

        # Flip un bit dans le ciphertext chiffré
        tampered = bytearray(sealed["encrypted_data"])
        tampered[0] ^= 0xFF
        sealed["encrypted_data"] = bytes(tampered)

        with pytest.raises(Exception):
            engine.decrypt_hybrid(
                priv,
                sealed["ciphertext_pqc"],
                sealed["nonce"],
                sealed["encrypted_data"],
                b"ctx",
            )

    def test_tampered_nonce_raises(self, engine: SecurityEngine):
        pub, priv = engine.generate_keypair()
        sealed = engine.encrypt_hybrid(pub, b"data", b"ctx")

        tampered_nonce = bytes([b ^ 0xFF for b in sealed["nonce"]])

        with pytest.raises(Exception):
            engine.decrypt_hybrid(
                priv,
                sealed["ciphertext_pqc"],
                tampered_nonce,
                sealed["encrypted_data"],
                b"ctx",
            )


# ---------------------------------------------------------------------------
# Audit Trail — Génération et vérification HMAC
# ---------------------------------------------------------------------------
class TestAuditTrail:
    def test_signed_log_has_required_fields(self, engine: SecurityEngine):
        result = engine.generate_signed_log("SEAL", "doc.pdf", "operator")
        assert "log" in result
        assert "signature" in result
        log = result["log"]
        assert "timestamp" in log
        assert log["action"] == "SEAL"
        assert log["target"] == "doc.pdf"
        assert log["user"] == "operator"

    def test_signature_is_64_char_hex(self, engine: SecurityEngine):
        result = engine.generate_signed_log("SEAL", "doc.pdf", "operator")
        assert len(result["signature"]) == 64
        int(result["signature"], 16)  # Doit être un hex valide

    def test_verify_log_returns_true_for_valid_entry(self, engine: SecurityEngine):
        result = engine.generate_signed_log("UNSEAL", "doc.pdf", "operator")
        log_json = json.dumps(result["log"], sort_keys=True)
        assert engine.verify_log(log_json, result["signature"]) is True

    def test_verify_log_returns_false_for_tampered_content(self, engine: SecurityEngine):
        result = engine.generate_signed_log("SEAL", "doc.pdf", "operator")
        tampered_log = result["log"].copy()
        tampered_log["action"] = "UNSEAL"  # Falsification de l'action
        tampered_json = json.dumps(tampered_log, sort_keys=True)
        assert engine.verify_log(tampered_json, result["signature"]) is False

    def test_verify_log_returns_false_for_wrong_signature(self, engine: SecurityEngine):
        result = engine.generate_signed_log("SEAL", "doc.pdf", "operator")
        log_json = json.dumps(result["log"], sort_keys=True)
        assert engine.verify_log(log_json, "a" * 64) is False

    def test_different_audit_keys_produce_different_signatures(self):
        engine1 = SecurityEngine(audit_key=b"first-audit-key-minimum-32-bytes-aa!")
        engine2 = SecurityEngine(audit_key=b"second-audit-key-minimum-32-bytes-b!")

        r1 = engine1.generate_signed_log("SEAL", "doc.pdf", "operator")
        r2 = engine2.generate_signed_log("SEAL", "doc.pdf", "operator")

        # Même contenu logique, clés HMAC différentes → signatures différentes
        assert r1["signature"] != r2["signature"]

    def test_verify_log_returns_false_for_cross_key_signature(self):
        """Une signature produite avec la clé A ne doit pas valider avec la clé B."""
        engine_a = SecurityEngine(audit_key=b"audit-key-a-minimum-32-bytes-aaaa!")
        engine_b = SecurityEngine(audit_key=b"audit-key-b-minimum-32-bytes-bbbb!")

        result = engine_a.generate_signed_log("SEAL", "doc.pdf", "operator")
        log_json = json.dumps(result["log"], sort_keys=True)

        assert engine_b.verify_log(log_json, result["signature"]) is False

    def test_verify_log_handles_exception_gracefully(self, engine: SecurityEngine):
        """verify_log ne doit jamais lever d'exception — retourne False sur entrée invalide."""
        assert engine.verify_log("not-valid-json{{{", "invalidsig") is False
        assert engine.verify_log("", "") is False


# ---------------------------------------------------------------------------
# Initialisation du moteur
# ---------------------------------------------------------------------------
class TestEngineInit:
    def test_rejects_short_audit_key(self):
        with pytest.raises(ValueError, match="32 bytes"):
            SecurityEngine(audit_key=b"tooshort")

    def test_accepts_exactly_32_byte_key(self):
        engine = SecurityEngine(audit_key=b"exactly-32-bytes-audit-key-here!")
        assert engine is not None

    def test_pqc_alg_attribute_is_kyber768(self):
        engine = SecurityEngine(audit_key=AUDIT_KEY)
        assert engine.pqc_alg == "Kyber768"


# ---------------------------------------------------------------------------
# HKDF-SHA256 key derivation (replaces previous direct SHA-256(shared_secret))
# ---------------------------------------------------------------------------
class TestHKDFKeyDerivation:
    """Properties of the HKDF-SHA256 AES key derivation."""

    def test_derivation_returns_32_bytes(self):
        from security_engine import _derive_aes_key

        key = _derive_aes_key(b"x" * 32, context=b"ctx")
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_same_secret_and_context_yields_same_key(self):
        from security_engine import _derive_aes_key

        secret = os.urandom(32)
        assert _derive_aes_key(secret, b"same-ctx") == _derive_aes_key(secret, b"same-ctx")

    def test_different_context_yields_different_key(self):
        from security_engine import _derive_aes_key

        secret = os.urandom(32)
        assert _derive_aes_key(secret, b"ctx-A") != _derive_aes_key(secret, b"ctx-B")

    def test_different_secret_yields_different_key(self):
        from security_engine import _derive_aes_key

        ctx = b"shared-context"
        assert _derive_aes_key(os.urandom(32), ctx) != _derive_aes_key(os.urandom(32), ctx)

    def test_derivation_is_not_plain_sha256(self):
        """Guard against regression to SHA-256(shared_secret) direct."""
        from security_engine import _derive_aes_key

        secret = b"\x00" * 32
        assert _derive_aes_key(secret, b"context") != hashlib.sha256(secret).digest()

    def test_seal_unseal_roundtrip_uses_hkdf(self, engine: SecurityEngine):
        """End-to-end check: HKDF-based seal/unseal still roundtrips cleanly."""
        pub, priv = engine.generate_keypair()
        plaintext = b"Quantum Shield Core HKDF roundtrip"
        context = b"hkdf-roundtrip-context"

        sealed = engine.encrypt_hybrid(pub, plaintext, context)
        recovered = engine.decrypt_hybrid(
            priv,
            sealed["ciphertext_pqc"],
            sealed["nonce"],
            sealed["encrypted_data"],
            context,
        )
        assert recovered == plaintext

    def test_wrong_context_still_fails_under_hkdf(self, engine: SecurityEngine):
        """Defense-in-depth: context mismatch fails at AES-GCM AAD AND at HKDF."""
        pub, priv = engine.generate_keypair()
        sealed = engine.encrypt_hybrid(pub, b"payload", b"correct-context")

        with pytest.raises(Exception):
            engine.decrypt_hybrid(
                priv,
                sealed["ciphertext_pqc"],
                sealed["nonce"],
                sealed["encrypted_data"],
                b"wrong-context",
            )
