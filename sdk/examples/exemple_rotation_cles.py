"""
Exemple 3 — Rotation de clés et re-chiffrement

Cas d'usage enterprise : rotation périodique des clés PQC sans perte
de données, conformément aux politiques de sécurité NIS2 / ISO 27001.
"""

import os

from sdk import QuantumShieldClient

client = QuantumShieldClient(
    base_url=os.environ.get("QS_URL", "http://localhost:8000"),
    api_key=os.environ.get("QS_OPERATOR_KEY", "demo-operator-key-for-evaluation-2026!!"),
)

print("=== Quantum Shield — Key Rotation ===\n")

# Sensitive data to protect
secret_data = b"FORMULATION_BREVET_CONFIDENTIELLE_REF_2026_XYZ"
context = "brevet-formulation-2026-xyz"

# 1. Encrypt with current keys (generation N)
print("[1] Encrypting with generation N keys...")
keys_gen_n = client.generate_keypair()
sealed_gen_n = client.seal(keys_gen_n["public_key_b64"], secret_data, context)
print("  ✔ Data encrypted with generation N key")
print(f"  Public key N : {keys_gen_n['public_key_b64'][:40]}...")

# 2. Generate new keypair (rotation to generation N+1)
print("\n[2] Rotating to generation N+1...")
keys_gen_n1 = client.generate_keypair()
print(f"  Public key N+1 : {keys_gen_n1['public_key_b64'][:40]}...")

# 3. Re-encrypt: unseal N, seal N+1
print("\n[3] Re-encryption (unseal N → seal N+1)...")
plaintext_recovered = client.unseal(keys_gen_n["private_key_b64"], sealed_gen_n, context)
assert plaintext_recovered == secret_data, "Error during re-encryption"
sealed_gen_n1 = client.seal(keys_gen_n1["public_key_b64"], plaintext_recovered, context)
print("  ✔ Data re-encrypted with generation N+1 key")

# 4. Final verification
final_data = client.unseal(keys_gen_n1["private_key_b64"], sealed_gen_n1, context)
assert final_data == secret_data, "Final verification failed"
print("\n  ✔ Data integrity verified after rotation")
print("  ✔ Old key (N) can be safely revoked")

# 5. Log the rotation to audit trail
client.write_audit_log(action="KEY_ROTATION", target=context, user="responsable-securite")
print("\n  ✔ Rotation logged to NIS2 audit trail")
print("\n✔ Key rotation completed.\n")
