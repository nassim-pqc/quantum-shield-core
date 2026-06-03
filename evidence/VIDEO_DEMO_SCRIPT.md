# Quantum Shield Core — 3-Minute Video Demo Script

> **Recording tool**: QuickTime (Mac), OBS Studio, or any screen recorder
> **Duration**: ~3 minutes
> **Resolution**: 1920×1080 or higher
> **Terminal**: iTerm2 or Terminal.app with large font (16pt minimum)

---

## Pre-Recording Checklist

- [ ] Docker Desktop running
- [ ] Terminal window open, font size 16pt+
- [ ] Clean desktop (no personal files visible)
- [ ] `.env` file configured with demo keys
- [ ] Service stopped before recording (`docker compose down`)
- [ ] Browser closed or on a clean tab
- [ ] Sound check (if narrating)

---

## Script

### [0:00–0:20] Introduction

**On screen**: Terminal, project folder visible

**Narration**:
> "This is Quantum Shield Core — an enterprise post-quantum cryptographic microservice. It implements ML-KEM-768 hybrid encryption, the NIST standard for quantum-resistant cryptography. Today I'll show you a complete encryption cycle and the audit trail."

**Action**: Show the project structure briefly:
```bash
ls -la
```

---

### [0:20–0:40] The Problem

**On screen**: Terminal

**Narration**:
> "Current cryptographic systems — RSA, ECC, Diffie-Hellman — will be broken by quantum computers. NIST published FIPS 203 in 2024, defining ML-KEM as the replacement. Organizations need to migrate now, before the threat becomes real. Quantum Shield Core makes this migration accessible."

---

### [0:40–1:00] Start the Service

**On screen**: Terminal

**Actions** (type these commands):
```bash
docker compose up --build -d
```

**Narration**:
> "We're starting the service with Docker Compose. This launches the API and a PostgreSQL database for the audit trail."

Wait for the service to start (show the build output).

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

**Narration**:
> "The health check confirms the service is running with ML-KEM-768 and the database is connected."

---

### [1:00–1:20] Generate Keys

**On screen**: Terminal

**Actions**:
```bash
curl -s -X POST http://localhost:8000/api/v1/keys/generate \
  -H "X-API-Key: ${API_KEY_OPERATOR}" \
  -H "Content-Type: application/json" | python3 -m json.tool
```

**Narration**:
> "We generate a post-quantum key pair. The private key is returned once and never stored by the server — this is our stateless architecture."

**Pause** to let the viewer see the keys (base64-encoded).

---

### [1:20–1:45] Encrypt (Seal)

**On screen**: Terminal

**Actions**:
```bash
# Store keys in variables
PUB_KEY="<paste public key from previous step>"
PRIV_KEY="<paste private key from previous step>"

# Encrypt a confidential document
DATA=$(echo -n "Confidential M&A document for 2026" | base64)

curl -s -X POST http://localhost:8000/api/v1/crypto/seal \
  -H "X-API-Key: ${API_KEY_OPERATOR}" \
  -H "Content-Type: application/json" \
  -d "{
    \"public_key_b64\": \"${PUB_KEY}\",
    \"data_b64\": \"${DATA}\",
    \"context\": \"contract-2026-001\"
  }" | python3 -m json.tool
```

**Narration**:
> "We encrypt using hybrid encryption — ML-KEM-768 key encapsulation plus AES-256-GCM. The context parameter binds the ciphertext to a specific business identifier. This is Additional Authenticated Data."

---

### [1:45–2:05] Decrypt (Unseal)

**On screen**: Terminal

**Actions**:
```bash
# Store seal output in variables and decrypt
curl -s -X POST http://localhost:8000/api/v1/crypto/unseal \
  -H "X-API-Key: ${API_KEY_OPERATOR}" \
  -H "Content-Type: application/json" \
  -d "{
    \"private_key_b64\": \"${PRIV_KEY}\",
    \"ciphertext_pqc_b64\": \"<from seal output>\",
    \"nonce_b64\": \"<from seal output>\",
    \"encrypted_data_b64\": \"<from seal output>\",
    \"context\": \"contract-2026-001\"
  }" | python3 -m json.tool
```

**Narration**:
> "We decrypt using the private key. The original plaintext is recovered. Note that using a wrong context — a different business identifier — would fail with a 401 error. This is the AAD enforcement."

---

### [2:05–2:25] Audit Trail

**On screen**: Terminal

**Actions**:
```bash
# View audit logs
curl -s http://localhost:8000/api/v1/audit/logs \
  -H "X-API-Key: ${API_KEY_AUDITOR}" | python3 -m json.tool
```

**Narration**:
> "Every cryptographic operation is recorded in a tamper-evident audit trail. Each entry is signed with HMAC-SHA256. The integrity field shows whether the entry's signature is valid. This supports compliance with GDPR, NIS2, and DORA."

---

### [2:25–2:45] Metrics and Observability

**On screen**: Terminal or browser

**Actions**:
```bash
# Prometheus metrics
curl -s http://localhost:8000/metrics | grep "qshield" | head -10
```

**Narration**:
> "The service exposes Prometheus metrics for crypto operations and request latency. It also supports OpenTelemetry tracing for distributed observability."

**Optional**: Open browser to `http://localhost:8000/dashboard` if the dashboard is visually compelling.

---

### [2:45–3:00] KMS and SDKs

**On screen**: Terminal

**Actions**:
```bash
# Show the project structure for KMS providers
ls providers/kms/

# Show SDK structure
ls sdk/
ls sdk-go/
```

**Narration**:
> "The service supports enterprise KMS providers — AWS KMS, HashiCorp Vault, and Azure Key Vault — for production key management. We provide both Python and Go SDKs for easy integration. The entire project is MIT licensed, pre-commercial, and ready for POC or integration."

---

### [3:00] End

**Narration**:
> "Quantum Shield Core — post-quantum encryption, ready for the future."

**On screen**: Show the health endpoint one last time:
```bash
curl http://localhost:8000/health
```

**End recording.**

---

## Post-Recording

- Trim the video to 3 minutes
- Add title card: "Quantum Shield Core — Post-Quantum Cryptographic Microservice"
- Add end card: GitHub URL, license, contact
- Export as MP4 (H.264, 1080p)
- Optional: Add subtitles for narration

---

## Tips

- **Font size**: Use 16pt+ in terminal for readability
- **Speed**: Type slowly so commands are visible
- **Pause**: Pause 1-2 seconds after each command output
- **Narration**: Speak clearly, avoid jargon where possible
- **Background**: No music — keep it professional
- **Editing**: Cut any waiting time during Docker build