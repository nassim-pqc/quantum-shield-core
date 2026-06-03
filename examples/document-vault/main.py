"""
Document Vault — Real-world usage example for Quantum Shield Core.

This script demonstrates a complete document encryption workflow:
1. Generate ML-KEM-768 key pair
2. Encrypt a document using hybrid encryption (Kyber768 + AES-256-GCM)
3. Write audit log entries
4. Decrypt the document
5. Verify audit trail integrity

Prerequisites:
    - Quantum Shield Core API running (docker compose up --build)
    - API keys configured in environment or passed explicitly

Quick start:
    # Start the API
    docker compose up --build -d

    # Set environment variables
    export QSC_API_URL=http://localhost:8000
    export QSC_API_KEY=test-operator-api-key-secure-enough-32chars!!
    export QSC_AUDITOR_KEY=test-auditor-api-key-secure-enough-32chars!!!

    # Run the example
    python -m examples.document_vault.main
"""

import os
import sys
from pathlib import Path

# Ensure the project root is in the Python path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from sdk import QuantumShieldClient, QuantumShieldError  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_URL = os.environ.get("QSC_API_URL", "http://localhost:8000")
API_KEY = os.environ.get(
    "QSC_API_KEY",
    "test-operator-api-key-secure-enough-32chars!!",
)
AUDITOR_KEY = os.environ.get(
    "QSC_AUDITOR_KEY",
    "test-auditor-api-key-secure-enough-32chars!!!",
)


# ---------------------------------------------------------------------------
# Demo — Document Vault
# ---------------------------------------------------------------------------
class DocumentVaultDemo:
    """Demonstrates the document vault workflow with Quantum Shield Core."""

    def __init__(self) -> None:
        self.operator = QuantumShieldClient(
            base_url=API_URL,
            api_key=API_KEY,
            timeout=30,
        )
        self.auditor = QuantumShieldClient(
            base_url=API_URL,
            api_key=AUDITOR_KEY,
            timeout=30,
        )
        self.keypair: dict[str, str] | None = None
        self.documents: dict[str, dict] = {}

    def step_health_check(self) -> None:
        """Step 1: Check service health."""
        print("\n" + "=" * 60)
        print("STEP 1: Health Check")
        print("=" * 60)

        health = self.operator.health()
        print(f"  Status:      {health['status']}")
        print(f"  Algorithm:   {health['algorithm']}")
        print(f"  Version:     {health['version']}")
        print(f"  Database:    {health['database']}")

        assert health["status"] == "healthy", "API is not healthy"
        print("  ✓ Health check passed")

    def step_generate_keys(self) -> None:
        """Step 2: Generate ML-KEM-768 key pair."""
        print("\n" + "=" * 60)
        print("STEP 2: Generate ML-KEM-768 Key Pair")
        print("=" * 60)

        self.keypair = self.operator.generate_keypair()
        print(f"  Public key length:  {len(self.keypair['public_key_b64'])} chars (Base64)")
        print(f"  Private key length: {len(self.keypair['private_key_b64'])} chars (Base64)")
        print("  ✓ Keys generated successfully")
        print("  ⚠ Private key returned only ONCE — store it securely!")

    def step_encrypt_document(self, doc_id: str, content: bytes) -> None:
        """Step 3: Encrypt a document."""
        print(f"\n{'=' * 60}")
        print(f"STEP 3: Encrypt Document '{doc_id}'")
        print("=" * 60)

        assert self.keypair is not None, "Generate keys first"

        sealed = self.operator.seal(
            public_key_b64=self.keypair["public_key_b64"],
            data=content,
            context=doc_id,
        )

        self.documents[doc_id] = sealed

        print(f"  Document:         '{doc_id}'")
        print(f"  Original size:    {len(content)} bytes")
        print(f"  PQC ciphertext:   {len(sealed['ciphertext_pqc_b64'])} chars")
        print(f"  Encrypted data:   {len(sealed['encrypted_data_b64'])} chars")
        print(f"  AES nonce:        {len(sealed['nonce_b64'])} chars")
        print(f"  Context (AAD):    '{doc_id}'")
        print("  ✓ Document encrypted with hybrid PQC scheme")

    def step_audit_log(self, action: str, target: str, user: str) -> None:
        """Step 4: Write an audit log entry."""
        print(f"\n{'=' * 60}")
        print("STEP 4: Write Audit Log Entry")
        print("=" * 60)

        result = self.operator.write_audit_log(
            action=action,
            target=target,
            user=user,
        )
        print(f"  Action:    {action}")
        print(f"  Target:    {target}")
        print(f"  User:      {user}")
        print(f"  Entry ID:  {result['id']}")
        print(f"  Signature: {result['signature'][:20]}...")
        print("  ✓ Audit log entry written")

    def step_decrypt_document(self, doc_id: str) -> bytes:
        """Step 5: Decrypt a document."""
        print(f"\n{'=' * 60}")
        print(f"STEP 5: Decrypt Document '{doc_id}'")
        print("=" * 60)

        assert self.keypair is not None, "Generate keys first"
        assert doc_id in self.documents, f"Document '{doc_id}' not found"

        sealed = self.documents[doc_id]
        plaintext = self.operator.unseal(
            private_key_b64=self.keypair["private_key_b64"],
            sealed=sealed,
            context=doc_id,
        )

        print(f"  Decrypted size: {len(plaintext)} bytes")
        print("  ✓ Document decrypted successfully")
        return plaintext

    def step_verify_audit_trail(self) -> None:
        """Step 6: Verify audit trail integrity."""
        print(f"\n{'=' * 60}")
        print("STEP 6: Verify Audit Trail Integrity")
        print("=" * 60)

        logs = self.auditor.get_audit_logs(limit=10)
        total = len(logs)

        for i, log in enumerate(logs, 1):
            integrity_icon = "✓" if log["integrity"] == "OK" else "✗"
            print(
                f"  [{integrity_icon}] Entry {i}/{total}: "
                f"action={log['action']}, "
                f"target={log['target']}, "
                f"integrity={log['integrity']}"
            )

        all_valid = all(log["integrity"] == "OK" for log in logs)
        if all_valid:
            print("  ✓ All audit entries verified — integrity intact")
        else:
            print("  ⚠ Some entries failed integrity check!")

    def step_audit_stats(self) -> None:
        """Step 7: Get audit trail statistics."""
        print(f"\n{'=' * 60}")
        print("STEP 7: Audit Trail Statistics")
        print("=" * 60)

        stats = self.operator.get_audit_stats()
        print(f"  Total entries: {stats['total']}")
        for action, count in stats.get("by_action", {}).items():
            print(f"    {action}: {count} entries")


def main() -> None:
    """Run the Document Vault demonstration."""
    print("\n" + "#" * 60)
    print("#  QUANTUM SHIELD CORE — Document Vault Demo")
    print("#" * 60)

    demo = DocumentVaultDemo()

    try:
        # Step 1: Health check
        demo.step_health_check()

        # Step 2: Generate keys
        demo.step_generate_keys()

        # Step 3: Encrypt documents
        demo.step_encrypt_document(
            doc_id="contract-2026-001",
            content=b"This is a highly confidential contract for 2026.",
        )
        demo.step_encrypt_document(
            doc_id="report-q1-2026",
            content=b"Q1 2026 financial report - CONFIDENTIAL.",
        )

        # Step 4: Audit log
        demo.step_audit_log(
            action="DOCUMENT_UPLOAD",
            target="contract-2026-001",
            user="alice@company.com",
        )
        demo.step_audit_log(
            action="DOCUMENT_UPLOAD",
            target="report-q1-2026",
            user="alice@company.com",
        )

        # Step 5: Decrypt documents
        plaintext1 = demo.step_decrypt_document("contract-2026-001")
        print(f"  Content: {plaintext1.decode()}")

        plaintext2 = demo.step_decrypt_document("report-q1-2026")
        print(f"  Content: {plaintext2.decode()}")

        # Step 6: Verify audit trail
        demo.step_verify_audit_trail()

        # Step 7: Audit stats
        demo.step_audit_stats()

        # Summary
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("  ✓ ML-KEM-768 key generation")
        print("  ✓ Hybrid PQC encryption (Kyber768 + AES-256-GCM)")
        print("  ✓ Context binding via AAD")
        print("  ✓ HMAC-signed audit trail")
        print("  ✓ Audit integrity verification")
        print("  ✓ Stateless architecture (keys never persisted)")
        print("=" * 60)

    except QuantumShieldError as exc:
        print(f"\n  ✗ Demo failed: {exc}")
        print("\n  Make sure the Quantum Shield API is running:")
        print("    docker compose up --build")
        sys.exit(1)
    except AssertionError as exc:
        print(f"\n  ✗ Assertion failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
