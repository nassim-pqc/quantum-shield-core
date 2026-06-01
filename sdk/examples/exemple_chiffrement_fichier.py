"""
Exemple 1 — Chiffrement d'un fichier (PDF, DOCX, etc.)

Cas d'usage NIS2 : chiffrement de documents RH, juridiques, ou financiers
avant stockage dans un GED ou un système d'archivage.

Prérequis :
    pip install requests
    docker compose up (from project root)
"""

import os
import tempfile
from pathlib import Path

from sdk import QuantumShieldClient

# Configuration
client = QuantumShieldClient(
    base_url=os.environ.get("QS_URL", "http://localhost:8000"),
    api_key=os.environ.get("QS_OPERATOR_KEY", "demo-operator-key-for-evaluation-2026!!"),
)

print("=== Quantum Shield — File Encryption ===\n")

# 1. Service health check
health = client.health()
print(f"✔ Service operational | Algorithm: {health['algorithm']}")

# 2. Generate keypair
print("\n[1] Generating PQC keypair...")
keypair = client.generate_keypair()
print(f"  Public key  : {keypair['public_key_b64'][:40]}...")
print("  ⚠️  Private key must be stored securely (HSM, vault, KMS)")

# 3. Create a test file simulating confidential document
with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
    f.write(b"CONFIDENTIAL REPORT\n")
    f.write(b"===================\n")
    f.write(b"Target: Company XYZ\n")
    f.write(b"Estimated value: 45M EUR\n")
    f.write(b"Date: 2026-Q2\n")
    source_path = f.name

encrypted_path = source_path + ".enc"
decrypted_path = source_path + ".dec"

context = f"document-rh-{Path(source_path).stem}"

# 4. Encrypt file
print("\n[2] Encrypting file...")
print(f"  Source      : {source_path}")
print(f"  Context AAD : {context}")
sealed = client.seal_file(keypair["public_key_b64"], source_path, context)
import json

with open(encrypted_path, "w") as f:
    json.dump(sealed, f)
print(f"  Encrypted → {encrypted_path}")
print("  ✔ File encrypted (Kyber768 KEM + AES-256-GCM)")

# 5. Decrypt file
print("\n[3] Decrypting...")
with open(encrypted_path) as f:
    sealed_loaded = json.load(f)
client.unseal_to_file(keypair["private_key_b64"], sealed_loaded, context, decrypted_path)
print(f"  Decrypted → {decrypted_path}")

# 6. Verify integrity
original = Path(source_path).read_bytes()
recovered = Path(decrypted_path).read_bytes()
assert original == recovered, "ERROR: Data does not match!"
print("  ✔ Integrity verified — byte-by-byte identical")

# Cleanup
os.unlink(source_path)
os.unlink(encrypted_path)
os.unlink(decrypted_path)

print("\n✔ Example completed successfully.\n")
