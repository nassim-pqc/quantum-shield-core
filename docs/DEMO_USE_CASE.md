# Document Vault — Real-World Use Case Demo

## Overview

The **Document Vault** example demonstrates a complete document encryption workflow using Quantum Shield Core. It showcases how to integrate post-quantum cryptography into a real-world document management system.

---

## Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Document Vault Workflow                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Health Check      → Verify API availability                     │
│  2. Generate Keys     → ML-KEM-768 key pair                         │
│  3. Encrypt Document  → Hybrid PQC encryption (Kyber768 + AES-GCM)  │
│  4. Audit Log         → HMAC-signed audit entry                     │
│  5. Decrypt Document  → Reverse hybrid decryption                   │
│  6. Verify Audit      → Integrity check on all entries              │
│  7. Audit Stats       → Summary of all operations                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

```bash
# 1. Start Quantum Shield Core
docker compose up --build -d

# 2. Verify API is running
curl http://localhost:8000/health
# {"status":"healthy","algorithm":"Kyber768","version":"1.0.0","database":"ok (0 audit entries)"}

# 3. Set environment variables
export QSC_API_URL=http://localhost:8000
export QSC_API_KEY=test-operator-api-key-secure-enough-32chars!!
export QSC_AUDITOR_KEY=test-auditor-api-key-secure-enough-32chars!!!
```

### Run the Demo

```bash
# From the project root
python -m examples.document_vault.main
```

---

## Expected Output

```
############################################################
#  QUANTUM SHIELD CORE — Document Vault Demo
############################################################

============================================================
STEP 1: Health Check
============================================================
  Status:      healthy
  Algorithm:   Kyber768
  Version:     1.0.0
  Database:    ok (0 audit entries)
  ✓ Health check passed

============================================================
STEP 2: Generate ML-KEM-768 Key Pair
============================================================
  Public key length:  1184 chars (Base64)
  Private key length: 2400 chars (Base64)
  ✓ Keys generated successfully
  ⚠ Private key returned only ONCE — store it securely!

============================================================
STEP 3: Encrypt Document 'contract-2026-001'
============================================================
  Document:         'contract-2026-001'
  Original size:    52 bytes
  PQC ciphertext:   2176 chars
  Encrypted data:   92 chars
  AES nonce:        16 chars
  Context (AAD):    'contract-2026-001'
  ✓ Document encrypted with hybrid PQC scheme

============================================================
STEP 4: Write Audit Log Entry
============================================================
  Action:    DOCUMENT_UPLOAD
  Target:    contract-2026-001
  User:      alice@company.com
  Entry ID:  3
  Signature: a1b2c3d4e5f6...
  ✓ Audit log entry written

============================================================
STEP 5: Decrypt Document 'contract-2026-001'
============================================================
  Decrypted size: 52 bytes
  ✓ Document decrypted successfully
  Content: This is a highly confidential contract for 2026.

============================================================
STEP 6: Verify Audit Trail Integrity
============================================================
  [✓] Entry 1/4: action=DOCUMENT_UPLOAD, target=report-q1-2026, integrity=OK
  [✓] Entry 2/4: action=DOCUMENT_UPLOAD, target=contract-2026-001, integrity=OK
  [✓] Entry 3/4: action=SEAL, target=contract-2026-001, integrity=OK
  [✓] Entry 4/4: action=KEY_GENERATE, target=keypair, integrity=OK
  ✓ All audit entries verified — integrity intact

============================================================
STEP 7: Audit Trail Statistics
============================================================
  Total entries: 4
    DOCUMENT_UPLOAD: 2 entries
    KEY_GENERATE: 1 entries
    SEAL: 1 entries

============================================================
DEMO COMPLETED SUCCESSFULLY
============================================================
```

---

## Security Properties Demonstrated

### 1. Post-Quantum Key Generation
- ML-KEM-768 (NIST-selected, formerly Kyber768)
- 768-bit security level
- Resistant to Shor's algorithm

### 2. Hybrid Encryption
- Kyber768 KEM for key exchange
- AES-256-GCM for data encryption
- Context binding via AAD (Additional Authenticated Data)
- Forward secrecy: ephemeral shared secrets

### 3. Stateless Architecture
- Private keys returned once, never stored server-side
- No key material in database, cache, logs, or audit trail

### 4. Tamper-Evident Audit Trail
- HMAC-SHA256 signed entries
- Key versioning for rotation
- Integrity verification on every read
- Anti-tampering: any modification detected immediately

### 5. Authentication & Authorization
- API key authentication (SHA-256 hashed)
- RBAC: operator can encrypt/decrypt, auditor can only read logs

---

## Use Case Scenarios

### Healthcare (GDPR Compliant)
```
Patient records encrypted with PQC
→ Stored in vault
→ Access logged in audit trail
→ Decrypted only by authorized practitioners
```

### Legal (Confidential Documents)
```
Contracts encrypted per-client key
→ Tamper-evident audit of all access
→ Context binding prevents cross-document confusion
→ Stateless: no key escrow risk
```

### Finance (Regulatory Compliance)
```
Transaction data encrypted with PQC
→ NIS2/DORA compliant audit trail
→ Key separation: encryption vs. audit keys
→ Future-proof against quantum attacks
```

### Defense (Classified Documents)
```
Documents encrypted with ML-KEM-768
→ Multiple key domains per classification level
→ Full audit trail with integrity verification
→ Quantum-resistant for long-term security
```

---

## Code Walkthrough

The demo (`examples/document-vault/main.py`) demonstrates each step:

```python
# 1. Initialize clients
operator = QuantumShieldClient(base_url="http://localhost:8000", api_key=API_KEY)
auditor = QuantumShieldClient(base_url="http://localhost:8000", api_key=AUDITOR_KEY)

# 2. Check health
health = operator.health()

# 3. Generate PQC keys
keypair = operator.generate_keypair()

# 4. Encrypt document (context = document ID = AAD)
sealed = operator.seal(
    public_key_b64=keypair["public_key_b64"],
    data=b"Document content",
    context="document-id-001",
)

# 5. Write audit log
operator.write_audit_log(
    action="DOCUMENT_UPLOAD",
    target="document-id-001",
    user="alice@company.com",
)

# 6. Decrypt document
plaintext = operator.unseal(
    private_key_b64=keypair["private_key_b64"],
    sealed=sealed,
    context="document-id-001",
)

# 7. Verify audit trail
logs = auditor.get_audit_logs(limit=10)
# Each log has an 'integrity' field: "OK" or "FAIL"
```

---

## Integration Points

| System | Integration Method |
|--------|-------------------|
| Document Management | Via SDK (Python/Go) |
| Identity Provider | API keys seeded from Identity Provider |
| SIEM / Logging | JSON structured logs ingested by SIEM |
| Monitoring | Prometheus metrics + OpenTelemetry tracing |
| Key Management | AWS KMS / HashiCorp Vault / Local |
| Audit Compliance | HMAC-signed trail with integrity verification |

---

## Additional Examples

The SDK includes more examples:

```bash
# File encryption example
python -m sdk.examples.exemple_chiffrement_fichier

# Key rotation example
python -m sdk.examples.exemple_rotation_cles

# NIS2 compliance example
python -m sdk.examples.exemple_audit_nis2