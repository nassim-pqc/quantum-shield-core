"""
Exemple 2 — Piste d'audit NIS2 avec vérification d'intégrité

Cas d'usage NIS2 Art. 21 : traçabilité des opérations sur les données
sensibles avec preuve d'intégrité cryptographique.
"""

import os

from sdk import QuantumShieldClient

client = QuantumShieldClient(
    base_url=os.environ.get("QS_URL", "http://localhost:8000"),
    api_key=os.environ.get("QS_OPERATOR_KEY", "demo-operator-key-for-evaluation-2026!!"),
)

print("=== Quantum Shield — NIS2 Audit Trail ===\n")

# Simulate workflow operations
operations = [
    ("EXPORT", "rapport-financier-Q2.pdf", "alice.martin"),
    ("SEAL", "contrat-fournisseur-42.docx", "bob.dupont"),
    ("ARCHIVE", "dossier-patient-RH-001", "systeme-automatise"),
    ("ACCESS", "donnees-personnelles-batch", "charlie.leblanc"),
]

print("[1] Logging operations to audit trail...")
for action, target, user in operations:
    result = client.write_audit_log(action=action, target=target, user=user)
    print(f"  ✔ #{result['id']:3d} | {action:10s} | {target}")

# Read and verify integrity
print("\n[2] Verifying audit trail integrity...")
logs = client.get_audit_logs(limit=20)
for log in logs:
    status = log.get("integrity", "🛡️ OK")
    print(f"  {status} | #{log['id']:3d} | {log['action']:12s} | {log['target']}")

all_ok = all(log.get("integrity", "🛡️ OK") == "🛡️ OK" for log in logs)
print(f"\n  {'✔ All entries are intact.' if all_ok else '✘ ALERT: Corrupted entries detected!'}")

# Statistics
print("\n[3] Audit trail statistics...")
stats = client.get_audit_stats()
print(f"  Total entries: {stats.get('total', 0)}")
for action, count in stats.get("by_action", {}).items():
    print(f"  {action:15s} : {count} operation(s)")

print("\n✔ NIS2 audit example completed.\n")
