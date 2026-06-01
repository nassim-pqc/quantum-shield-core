"""
test_api.py — Tests d'intégration de l'API Quantum Shield.

Couvre :
  - Health check
  - Authentification et RBAC sur tous les endpoints
  - Rate limiting (structure des headers)
  - Workflow seal → unseal bout en bout
  - Enforcement AAD (contexte altéré)
  - Piste d'audit : écriture, lecture, vérification d'intégrité
  - Validation des payloads (champs manquants, types incorrects)
  - Sécurité : messages d'erreur opaques sur unseal
"""

import base64

import pytest
import pytest_asyncio
from conftest import (
    AUDITOR_HEADERS,
    INVALID_HEADERS,
    OPERATOR_HEADERS,
    TEST_CONTEXT,
    TEST_MESSAGE,
)
from httpx import AsyncClient


# ===========================================================================
# Health Check
# ===========================================================================
class TestHealth:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client: AsyncClient):
        r = await client.get("/health")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_health_body(self, client: AsyncClient):
        r = await client.get("/health")
        body = r.json()
        assert body["status"] == "healthy"
        assert body["algorithm"] == "Kyber768"
        assert "version" in body
        assert "database" in body

    @pytest.mark.asyncio
    async def test_health_no_auth_required(self, client: AsyncClient):
        """Le health check est public — pas de clé API requise."""
        r = await client.get("/health")
        assert r.status_code == 200


# ===========================================================================
# Security Headers
# ===========================================================================
class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_hsts_header_present(self, client: AsyncClient):
        r = await client.get("/health")
        assert "strict-transport-security" in r.headers

    @pytest.mark.asyncio
    async def test_x_frame_options_deny(self, client: AsyncClient):
        r = await client.get("/health")
        assert r.headers.get("x-frame-options") == "DENY"

    @pytest.mark.asyncio
    async def test_cache_control_no_store(self, client: AsyncClient):
        r = await client.get("/health")
        assert "no-store" in r.headers.get("cache-control", "")

    @pytest.mark.asyncio
    async def test_x_content_type_options(self, client: AsyncClient):
        r = await client.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"


# ===========================================================================
# Authentication & RBAC
# ===========================================================================
class TestAuthentication:
    @pytest.mark.asyncio
    async def test_missing_api_key_returns_403(self, client: AsyncClient):
        r = await client.post("/api/v1/keys/generate")
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_403(self, client: AsyncClient):
        r = await client.post("/api/v1/keys/generate", headers=INVALID_HEADERS)
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_auditor_cannot_generate_keys(self, client: AsyncClient):
        r = await client.post("/api/v1/keys/generate", headers=AUDITOR_HEADERS)
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_auditor_cannot_seal(self, client: AsyncClient, keypair: dict):
        r = await client.post(
            "/api/v1/crypto/seal",
            headers=AUDITOR_HEADERS,
            json={
                "public_key_b64": keypair["public_key_b64"],
                "data_b64": base64.b64encode(TEST_MESSAGE).decode(),
                "context": TEST_CONTEXT,
            },
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_auditor_cannot_unseal(self, client: AsyncClient, sealed_payload: dict):
        s = sealed_payload["sealed"]
        k = sealed_payload["keypair"]
        r = await client.post(
            "/api/v1/crypto/unseal",
            headers=AUDITOR_HEADERS,
            json={
                "private_key_b64": k["private_key_b64"],
                "ciphertext_pqc_b64": s["ciphertext_pqc_b64"],
                "nonce_b64": s["nonce_b64"],
                "encrypted_data_b64": s["encrypted_data_b64"],
                "context": TEST_CONTEXT,
            },
        )
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_auditor_can_read_logs(self, client: AsyncClient):
        r = await client.get("/api/v1/audit/logs", headers=AUDITOR_HEADERS)
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_operator_can_read_logs(self, client: AsyncClient):
        r = await client.get("/api/v1/audit/logs", headers=OPERATOR_HEADERS)
        assert r.status_code == 200


# ===========================================================================
# Key Generation
# ===========================================================================
class TestKeyGeneration:
    @pytest.mark.asyncio
    async def test_generate_returns_201(self, client: AsyncClient):
        r = await client.post("/api/v1/keys/generate", headers=OPERATOR_HEADERS)
        assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_generate_returns_both_keys(self, client: AsyncClient):
        r = await client.post("/api/v1/keys/generate", headers=OPERATOR_HEADERS)
        body = r.json()
        assert "public_key_b64" in body
        assert "private_key_b64" in body

    @pytest.mark.asyncio
    async def test_generated_keys_are_valid_base64(self, client: AsyncClient):
        r = await client.post("/api/v1/keys/generate", headers=OPERATOR_HEADERS)
        body = r.json()
        base64.b64decode(body["public_key_b64"])  # Ne doit pas lever
        base64.b64decode(body["private_key_b64"])  # Ne doit pas lever

    @pytest.mark.asyncio
    async def test_two_calls_return_different_keys(self, client: AsyncClient):
        r1 = await client.post("/api/v1/keys/generate", headers=OPERATOR_HEADERS)
        r2 = await client.post("/api/v1/keys/generate", headers=OPERATOR_HEADERS)
        assert r1.json()["public_key_b64"] != r2.json()["public_key_b64"]

    @pytest.mark.asyncio
    async def test_key_generation_creates_audit_log(self, client: AsyncClient):
        await client.post("/api/v1/keys/generate", headers=OPERATOR_HEADERS)
        logs = (await client.get("/api/v1/audit/logs", headers=OPERATOR_HEADERS)).json()
        actions = [log["action"] for log in logs]
        assert "KEY_GENERATE" in actions


# ===========================================================================
# Seal (Chiffrement)
# ===========================================================================
class TestSeal:
    @pytest.mark.asyncio
    async def test_seal_returns_200(self, client: AsyncClient, keypair: dict):
        r = await client.post(
            "/api/v1/crypto/seal",
            headers=OPERATOR_HEADERS,
            json={
                "public_key_b64": keypair["public_key_b64"],
                "data_b64": base64.b64encode(TEST_MESSAGE).decode(),
                "context": TEST_CONTEXT,
            },
        )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_seal_returns_three_fields(self, client: AsyncClient, keypair: dict):
        r = await client.post(
            "/api/v1/crypto/seal",
            headers=OPERATOR_HEADERS,
            json={
                "public_key_b64": keypair["public_key_b64"],
                "data_b64": base64.b64encode(b"data").decode(),
                "context": TEST_CONTEXT,
            },
        )
        body = r.json()
        assert "ciphertext_pqc_b64" in body
        assert "nonce_b64" in body
        assert "encrypted_data_b64" in body

    @pytest.mark.asyncio
    async def test_seal_missing_context_returns_422(self, client: AsyncClient, keypair: dict):
        r = await client.post(
            "/api/v1/crypto/seal",
            headers=OPERATOR_HEADERS,
            json={
                "public_key_b64": keypair["public_key_b64"],
                "data_b64": base64.b64encode(b"data").decode(),
                # context manquant
            },
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_seal_empty_context_returns_422(self, client: AsyncClient, keypair: dict):
        r = await client.post(
            "/api/v1/crypto/seal",
            headers=OPERATOR_HEADERS,
            json={
                "public_key_b64": keypair["public_key_b64"],
                "data_b64": base64.b64encode(b"data").decode(),
                "context": "",  # context vide
            },
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_seal_creates_audit_log(self, client: AsyncClient, keypair: dict):
        await client.post(
            "/api/v1/crypto/seal",
            headers=OPERATOR_HEADERS,
            json={
                "public_key_b64": keypair["public_key_b64"],
                "data_b64": base64.b64encode(b"data").decode(),
                "context": TEST_CONTEXT,
            },
        )
        logs = (await client.get("/api/v1/audit/logs", headers=OPERATOR_HEADERS)).json()
        assert any(log["action"] == "SEAL" for log in logs)


# ===========================================================================
# Unseal (Déchiffrement)
# ===========================================================================
class TestUnseal:
    @pytest.mark.asyncio
    async def test_unseal_returns_200(self, client: AsyncClient, sealed_payload: dict):
        s = sealed_payload["sealed"]
        k = sealed_payload["keypair"]
        r = await client.post(
            "/api/v1/crypto/unseal",
            headers=OPERATOR_HEADERS,
            json={
                "private_key_b64": k["private_key_b64"],
                "ciphertext_pqc_b64": s["ciphertext_pqc_b64"],
                "nonce_b64": s["nonce_b64"],
                "encrypted_data_b64": s["encrypted_data_b64"],
                "context": TEST_CONTEXT,
            },
        )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_unseal_recovers_original_message(
        self, client: AsyncClient, sealed_payload: dict
    ):
        s = sealed_payload["sealed"]
        k = sealed_payload["keypair"]
        r = await client.post(
            "/api/v1/crypto/unseal",
            headers=OPERATOR_HEADERS,
            json={
                "private_key_b64": k["private_key_b64"],
                "ciphertext_pqc_b64": s["ciphertext_pqc_b64"],
                "nonce_b64": s["nonce_b64"],
                "encrypted_data_b64": s["encrypted_data_b64"],
                "context": TEST_CONTEXT,
            },
        )
        recovered = base64.b64decode(r.json()["decrypted_data_b64"])
        assert recovered == TEST_MESSAGE

    @pytest.mark.asyncio
    async def test_wrong_context_returns_401(self, client: AsyncClient, sealed_payload: dict):
        """AAD enforcement : contexte différent → déchiffrement rejeté."""
        s = sealed_payload["sealed"]
        k = sealed_payload["keypair"]
        r = await client.post(
            "/api/v1/crypto/unseal",
            headers=OPERATOR_HEADERS,
            json={
                "private_key_b64": k["private_key_b64"],
                "ciphertext_pqc_b64": s["ciphertext_pqc_b64"],
                "nonce_b64": s["nonce_b64"],
                "encrypted_data_b64": s["encrypted_data_b64"],
                "context": "MAUVAIS_CONTEXTE",
            },
        )
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_private_key_returns_401(self, client: AsyncClient, sealed_payload: dict):
        """Mauvaise clé privée → déchiffrement rejeté."""
        s = sealed_payload["sealed"]
        wrong_keypair = (
            await client.post("/api/v1/keys/generate", headers=OPERATOR_HEADERS)
        ).json()
        r = await client.post(
            "/api/v1/crypto/unseal",
            headers=OPERATOR_HEADERS,
            json={
                "private_key_b64": wrong_keypair["private_key_b64"],
                "ciphertext_pqc_b64": s["ciphertext_pqc_b64"],
                "nonce_b64": s["nonce_b64"],
                "encrypted_data_b64": s["encrypted_data_b64"],
                "context": TEST_CONTEXT,
            },
        )
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_error_message_is_opaque(self, client: AsyncClient, sealed_payload: dict):
        """
        Les messages d'erreur ne doivent pas révéler si c'est la clé,
        le contexte ou le tag GCM qui a échoué (protection anti-oracle).
        """
        s = sealed_payload["sealed"]
        k = sealed_payload["keypair"]
        r = await client.post(
            "/api/v1/crypto/unseal",
            headers=OPERATOR_HEADERS,
            json={
                "private_key_b64": k["private_key_b64"],
                "ciphertext_pqc_b64": s["ciphertext_pqc_b64"],
                "nonce_b64": s["nonce_b64"],
                "encrypted_data_b64": s["encrypted_data_b64"],
                "context": "WRONG",
            },
        )
        error_detail = r.json().get("detail", "")
        # Le message ne doit pas contenir de détails techniques internes
        assert "InvalidTag" not in error_detail
        assert "Traceback" not in error_detail
        assert "Exception" not in error_detail

    @pytest.mark.asyncio
    async def test_unseal_creates_audit_log(self, client: AsyncClient, sealed_payload: dict):
        s = sealed_payload["sealed"]
        k = sealed_payload["keypair"]
        await client.post(
            "/api/v1/crypto/unseal",
            headers=OPERATOR_HEADERS,
            json={
                "private_key_b64": k["private_key_b64"],
                "ciphertext_pqc_b64": s["ciphertext_pqc_b64"],
                "nonce_b64": s["nonce_b64"],
                "encrypted_data_b64": s["encrypted_data_b64"],
                "context": TEST_CONTEXT,
            },
        )
        logs = (await client.get("/api/v1/audit/logs", headers=OPERATOR_HEADERS)).json()
        assert any(log["action"] == "UNSEAL" for log in logs)


# ===========================================================================
# Audit Trail
# ===========================================================================
class TestAuditTrail:
    @pytest.mark.asyncio
    async def test_write_log_returns_201(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/audit/log",
            headers=OPERATOR_HEADERS,
            json={"action": "EXPORT", "target": "rapport.pdf", "user": "alice"},
        )
        assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_written_log_appears_in_list(self, client: AsyncClient):
        await client.post(
            "/api/v1/audit/log",
            headers=OPERATOR_HEADERS,
            json={"action": "ARCHIVE", "target": "contrat.docx", "user": "bob"},
        )
        logs = (await client.get("/api/v1/audit/logs", headers=OPERATOR_HEADERS)).json()
        targets = [log["target"] for log in logs]
        assert "contrat.docx" in targets

    @pytest.mark.asyncio
    async def test_log_integrity_is_ok_for_fresh_entry(self, client: AsyncClient):
        await client.post(
            "/api/v1/audit/log",
            headers=OPERATOR_HEADERS,
            json={"action": "SEAL", "target": "doc.pdf", "user": "operator"},
        )
        logs = (await client.get("/api/v1/audit/logs", headers=AUDITOR_HEADERS)).json()
        assert all(log["integrity"] == "OK" for log in logs)

    @pytest.mark.asyncio
    async def test_get_log_by_id_returns_200(self, client: AsyncClient):
        write_r = await client.post(
            "/api/v1/audit/log",
            headers=OPERATOR_HEADERS,
            json={"action": "TEST", "target": "file.txt", "user": "tester"},
        )
        log_id = write_r.json()["id"]
        r = await client.get(f"/api/v1/audit/logs/{log_id}", headers=AUDITOR_HEADERS)
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_get_nonexistent_log_returns_404(self, client: AsyncClient):
        r = await client.get("/api/v1/audit/logs/999999", headers=AUDITOR_HEADERS)
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_logs_pagination(self, client: AsyncClient):
        # Écrire 5 logs
        for i in range(5):
            await client.post(
                "/api/v1/audit/log",
                headers=OPERATOR_HEADERS,
                json={"action": f"ACTION_{i}", "target": f"doc_{i}.pdf", "user": "tester"},
            )
        # Récupérer seulement les 3 premiers
        r = await client.get("/api/v1/audit/logs?limit=3", headers=OPERATOR_HEADERS)
        assert len(r.json()) <= 3

    @pytest.mark.asyncio
    async def test_logs_filter_by_action(self, client: AsyncClient):
        await client.post(
            "/api/v1/audit/log",
            headers=OPERATOR_HEADERS,
            json={"action": "UNIQUE_ACTION_XYZ", "target": "f.pdf", "user": "tester"},
        )
        r = await client.get(
            "/api/v1/audit/logs?action=UNIQUE_ACTION_XYZ",
            headers=OPERATOR_HEADERS,
        )
        logs = r.json()
        assert all(log["action"] == "UNIQUE_ACTION_XYZ" for log in logs)
