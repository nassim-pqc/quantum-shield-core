# Quantum Shield Core — Demo Commands

> All commands are verified against the actual codebase. No invented commands.
> Commands are organized by task and include prerequisites where needed.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Docker | ≥ 24.0 | Container runtime |
| Docker Compose | ≥ 2.20 | Multi-container orchestration |
| curl | any | HTTP client |
| jq | any | JSON formatting |
| Python | 3.11+ | JSON formatting, SDK |
| Go | 1.21+ | Go SDK (optional) |

Install prerequisites on macOS:
```bash
brew install docker docker-compose curl jq python go
```

---

## 1. Install Dependencies (Development)

```bash
# Python dependencies (for development/testing)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Rust engine (optional, for constant-time HMAC/AES-GCM)
cd rust-engine
pip install maturin
maturin develop
cd ..
```

**Note**: The Rust engine is optional. If not installed, the Python fallback is used automatically.

---

## 2. Start the Backend

### Option A: Docker Compose (Recommended)

```bash
# Configure environment
cp .env.example .env
# Edit .env with your secrets:
#   POSTGRES_PASSWORD=<min 12 chars>
#   AUDIT_KEY=<min 32 chars>
#   API_KEY_OPERATOR=<min 32 chars>
#   API_KEY_AUDITOR=<min 32 chars>

# Start the service
docker compose up --build -d

# Verify it's running
curl http://localhost:8000/health
```

### Option B: Local Development

```bash
# Set environment variables
export AUDIT_KEY="your-32-byte-audit-key-here-xxxxxxxxxxxxxxxx"
export API_KEY_OPERATOR="your-operator-key-min-32-chars!"
export API_KEY_AUDITOR="your-auditor-key-min-32-chars!"
export DATABASE_URL="sqlite+aiosqlite:///./dev.db"

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. Health Check

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

Expected output:
```json
{
    "status": "healthy",
    "algorithm": "Kyber768",
    "version": "1.0.0",
    "database": "ok (N audit entries)"
}
```

---

## 4. Generate Key Pair

```bash
curl -s -X POST http://localhost:8000/api/v1/keys/generate \
  -H "X-API-Key: ${API_KEY_OPERATOR}" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: demo-$(date +%s)" \
  | python3 -m json.tool
```

**Note**: The private key is returned only once. Store it securely.

---

## 5. Encrypt Data (Seal)

First, generate a key pair and store the keys:

```bash
# Generate keys
KEYS=$(curl -s -X POST http://localhost:8000/api/v1/keys/generate \
  -H "X-API-Key: ${API_KEY_OPERATOR}" \
  -H "Content-Type: application/json")

PUB=$(echo "$KEYS" | python3 -c "import sys,json; print(json.load(sys.stdin)['public_key_b64'])")
PRIV=$(echo "$KEYS" | python3 -c "import sys,json; print(json.load(sys.stdin)['private_key_b64'])")

# Prepare plaintext (base64-encoded)
DATA=$(echo -n "Confidential document content" | base64)

# Encrypt
SEALED=$(curl -s -X POST http://localhost:8000/api/v1/crypto/seal \
  -H "X-API-Key: ${API_KEY_OPERATOR}" \
  -H "Content-Type: application/json" \
  -d "{
    \"public_key_b64\": \"${PUB}\",
    \"data_b64\": \"${DATA}\",
    \"context\": \"contract-2026-001\"
  }")

echo "$SEALED" | python3 -m json.tool
```

Expected output:
```json
{
    "ciphertext_pqc_b64": "<base64-encoded Kyber768 ciphertext>",
    "nonce_b64": "<base64-encoded 12-byte nonce>",
    "encrypted_data_b64": "<base64-encoded AES-GCM ciphertext + tag>"
}
```

---

## 6. Decrypt Data (Unseal)

```bash
# Extract values from the seal output
CPQC=$(echo "$SEALED" | python3 -c "import sys,json; print(json.load(sys.stdin)['ciphertext_pqc_b64'])")
NONCE=$(echo "$SEALED" | python3 -c "import sys,json; print(json.load(sys.stdin)['nonce_b64'])")
ENC=$(echo "$SEALED" | python3 -c "import sys,json; print(json.load(sys.stdin)['encrypted_data_b64'])")

# Decrypt
curl -s -X POST http://localhost:8000/api/v1/crypto/unseal \
  -H "X-API-Key: ${API_KEY_OPERATOR}" \
  -H "Content-Type: application/json" \
  -d "{
    \"private_key_b64\": \"${PRIV}\",
    \"ciphertext_pqc_b64\": \"${CPQC}\",
    \"nonce_b64\": \"${NONCE}\",
    \"encrypted_data_b64\": \"${ENC}\",
    \"context\": \"contract-2026-001\"
  }" | python3 -m json.tool
```

Expected output:
```json
{
    "decrypted_data_b64": "Q29uZmlkZW50aWFsIGRvY3VtZW50IGNvbnRlbnQ="
}
```

Verify the plaintext:
```bash
echo "Q29uZmlkZW50aWFsIGRvY3VtZW50IGNvbnRlbnQ=" | base64 -d
# → Confidential document content
```

---

## 7. View Audit Logs

```bash
curl -s http://localhost:8000/api/v1/audit/logs \
  -H "X-API-Key: ${API_KEY_AUDITOR}" \
  | python3 -m json.tool
```

---

## 8. View Audit Stats

```bash
curl -s http://localhost:8000/api/v1/audit/stats \
  -H "X-API-Key: ${API_KEY_AUDITOR}" \
  | python3 -m json.tool
```

---

## 9. View Prometheus Metrics

```bash
curl -s http://localhost:8000/metrics | head -30
```

Filter for quantum-shield specific metrics:
```bash
curl -s http://localhost:8000/metrics | grep "qshield\|crypto_ops\|audit_writes"
```

---

## 10. View Logs

```bash
# Docker logs
docker compose logs quantum-shield-api --tail 50

# Follow logs in real-time
docker compose logs -f quantum-shield-api
```

---

## 11. Run Python Tests

```bash
# Requires liboqs installed
AUDIT_KEY="test-audit-key-secure-enough-for-pytest-32chars!" \
API_KEY_OPERATOR="test-operator-api-key-secure-enough-32chars!!" \
API_KEY_AUDITOR="test-auditor-api-key-secure-enough-32chars!!!" \
DATABASE_URL="sqlite+aiosqlite:///./test.db" \
pytest tests/ -v --tb=short
```

---

## 12. Run Go Tests

```bash
cd sdk-go
go test ./... -v
```

---

## 13. Lint (Ruff)

```bash
ruff check .
```

---

## 14. Check Formatting (Ruff)

```bash
ruff format --check .
```

---

## 15. Go Build

```bash
cd sdk-go
go build ./...
```

---

## 16. Go Vet

```bash
cd sdk-go
go vet ./...
```

---

## 17. Full Demo Script (Automated)

```bash
# Run the complete automated demo
bash demo/demo.sh
```

Or the interactive evaluation script:
```bash
bash demo/quickstart-clean.sh
```

---

## 18. Run the Document Vault Example

```bash
# Start the API first
docker compose up --build -d

# Run the example
QSC_API_URL=http://localhost:8000 \
QSC_API_KEY=${API_KEY_OPERATOR} \
QSC_AUDITOR_KEY=${API_KEY_AUDITOR} \
python -m examples.document_vault.main
```

---

## 19. Run Benchmarks

```bash
bash scripts/benchmark.sh --md
```

---

## 20. Stop the Service

```bash
docker compose down

# Remove volumes (reset database)
docker compose down -v
```

---

## Notes

- All commands assume the service is running on `http://localhost:8000`
- API keys must be at least 32 characters
- The `AUDIT_KEY` must be at least 32 characters
- KMS provider commands (AWS, Vault, Azure) require additional configuration and enterprise license
- The Go SDK requires Go 1.21+ and the `liboqs` system library for full functionality