# ◈ Quantum Shield Core — Proof of Usage

> **Version**: 1.0.0 | **License**: MIT | **Status**: Pre-commercial / Technical Asset

---

## What is Quantum Shield Core?

Quantum Shield Core is an **enterprise post-quantum cryptographic microservice** implementing hybrid encryption based on **ML-KEM-768** (Kyber768) and **AES-256-GCM**. It is designed to help organizations prepare their systems for the post-quantum era — the moment when quantum computers will be capable of breaking today's standard cryptographic algorithms.

The project provides:

- A **production-ready API** (FastAPI + Rust core engine) for post-quantum key generation, encryption, and decryption
- A **stateless architecture** where no user private key is ever stored server-side
- An **HMAC-signed, append-only audit trail** with key rotation support
- **Pluggable KMS providers** (AWS KMS, HashiCorp Vault, Azure Key Vault)
- Two **client SDKs** (Python and Go)
- **Full observability** (Prometheus metrics, OpenTelemetry tracing, structured JSON logs)

---

## Why is this project useful?

The global cryptographic infrastructure is facing a fundamental transition. NIST finalized the first post-quantum cryptography standards in 2024 (FIPS 203 — ML-KEM). Organizations that handle sensitive data — healthcare, defense, finance, legal, government — need to migrate to quantum-resistant algorithms before current encryption becomes vulnerable.

Quantum Shield Core provides a **ready-to-integrate, modular cryptographic layer** that:

- Uses **NIST-standardized algorithms** (ML-KEM-768, FIPS 203)
- Maintains **backward compatibility** via hybrid encryption (PQ + classical)
- Enforces **zero-knowledge key management** (stateless server)
- Provides a **complete audit trail** for compliance (GDPR, NIS2, DORA, HIPAA)

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Layer | FastAPI (Python 3.12) | HTTP endpoints, validation, OpenAPI |
| Crypto Core | Rust (PyO3 bindings) | Constant-time HMAC-SHA256, AES-GCM |
| KEM | liboqs-python (ML-KEM-768) | Post-quantum key encapsulation |
| AEAD | pyca/cryptography (AES-256-GCM) | Symmetric authenticated encryption |
| Auth | SHA-256 hashed API keys + RBAC | Authentication and authorization |
| Audit | PostgreSQL (async) | Append-only signed log storage |
| Metrics | Prometheus | Crypto operations, request latency |
| Tracing | OpenTelemetry | W3C trace context, OTLP export |
| Rate Limiting | SlowAPI | Per-IP rate limiting |
| KMS | AWS KMS, Vault, Azure Key Vault | Enterprise key management |
| SDK Python | requests-based typed client | Python integration |
| SDK Go | idiomatic Go client | Go integration |
| Deployment | Docker, Helm, docker-compose | Container orchestration |

---

## How Post-Quantum Encryption Works

Quantum Shield Core uses a **hybrid encryption scheme** combining two layers:

### 1. ML-KEM-768 (Kyber768) — Key Encapsulation

ML-KEM-768 is a NIST-standardized post-quantum algorithm (FIPS 203). It generates a public/secret key pair. When encrypting, the sender uses the recipient's public key to produce a **ciphertext** and a **shared secret**. Only the holder of the secret key can recover the shared secret from the ciphertext. This is resistant to both classical and quantum attacks.

### 2. AES-256-GCM — Authenticated Encryption

The shared secret from ML-KEM is hashed (SHA-256) to derive a symmetric key, which is then used with AES-256-GCM to encrypt the actual data. AES-GCM provides:
- **Confidentiality**: data is encrypted
- **Integrity**: any tampering is detected (GCM tag)
- **Authenticity**: Additional Authenticated Data (AAD) binds the ciphertext to a business context

### The Hybrid Approach

This dual-layer approach ensures that even if one algorithm is compromised, the other provides security. This is the recommended migration strategy by NIST, ETSI, and ANSSI.

---

## Stateless Architecture

The server operates in **stateless mode** regarding cryptographic keys:

1. The client generates a key pair via the API
2. The **private key is returned once** and immediately discarded by the server
3. No private key is ever written to disk, logs, or database
4. The server cannot decrypt data it has encrypted

**Security benefits:**
- Server compromise does not expose user keys
- No key recovery risk from database breaches
- Reduces attack surface significantly

**Compliance benefits:**
- Supports data minimization (GDPR Art. 5)
- Enables zero-knowledge encryption architectures
- Reduces liability for key custody

**What this does NOT guarantee:**
- The client must still secure their private key (hardware security module, secure enclave, etc.)
- The server still needs an audit key (stored in environment/KMS) for signing audit logs
- This is not a complete end-to-end encrypted communication system

---

## KMS Providers

Quantum Shield Core supports pluggable Key Management Service providers:

### Local Environment (Default)
- Audit keys stored in environment variables (`AUDIT_KEY`)
- Suitable for development and testing
- No external dependencies

### AWS KMS
- DEK wrapping via KMS Encrypt/Decrypt (RSAES_OAEP_SHA_256)
- Audit key retrieval from encrypted environment blobs
- Exponential backoff retry with tenacity
- Configurable via `AWS_KMS_KEY_ID`, `AWS_REGION`, etc.

### HashiCorp Vault
- DEK wrapping via Transit Engine (`/v1/transit/encrypt/:key`)
- Audit key retrieval via KV v2 secrets engine
- SSL verification and configurable timeouts
- Configurable via `VAULT_ADDR`, `VAULT_TOKEN`, etc.

### Azure Key Vault
- DEK wrapping via Azure Key Vault keys
- Audit key retrieval via Azure Key Vault secrets
- Azure Identity authentication
- Configurable via `AZURE_VAULT_URL`, etc.

All KMS providers implement the `KMSProvider` interface combining `KeyWrapper` (DEK wrapping) and `SecretProvider` (audit key retrieval).

---

## Python SDK Usage

```python
from sdk import QuantumShieldClient

# Initialize client
client = QuantumShieldClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",
)

# Health check
health = client.health()
print(f"Status: {health['status']}")

# Generate ML-KEM-768 key pair
keypair = client.generate_keypair()
pub_key = keypair["public_key_b64"]
priv_key = keypair["private_key_b64"]  # Store securely — returned only once

# Encrypt (Seal)
sealed = client.seal(
    public_key_b64=pub_key,
    data=b"Confidential document content",
    context="document-2026-001",  # AAD — binds ciphertext to context
)

# Decrypt (Unseal)
plaintext = client.unseal(
    private_key_b64=priv_key,
    sealed=sealed,
    context="document-2026-001",
)
# plaintext == b"Confidential document content"

# Audit trail
client.write_audit_log(action="EXPORT", target="report.pdf", user="alice")
logs = client.get_audit_logs(action="EXPORT")
```

---

## Go SDK Usage

```go
import (
    "context"
    "fmt"
    "github.com/quantum-shield/sdk-go/pkg/client"
    "github.com/quantum-shield/sdk-go/pkg/types"
)

func main() {
    c, err := client.New(client.DefaultOptions())
    if err != nil {
        panic(err)
    }
    c.SetAPIKey(os.Getenv("QS_API_KEY"))

    ctx := context.Background()

    // Health check
    health, _ := c.Health(ctx)
    fmt.Printf("Status: %s\n", health.Status)

    // Generate key pair
    keypair, _ := c.GenerateKeypair(ctx)

    // Seal (encrypt)
    sealed, _ := c.Seal(ctx, keypair.PublicKeyB64, []byte("Confidential data"), "doc-123")

    // Unseal (decrypt)
    plaintext, _ := c.Unseal(ctx, keypair.PrivateKeyB64, sealed, "doc-123")
    fmt.Printf("Decrypted: %s\n", string(plaintext))

    // Audit trail
    c.WriteAuditLog(ctx, "EXPORT", "report.pdf", "alice")
}
```

---

## Running a Local Demo

```bash
# 1. Clone the repository
git clone https://github.com/nassim-pqc/quantum-shield-core.git
cd quantum-shield-core

# 2. Copy environment template
cp .env.example .env
# Edit .env with your secrets (min 32 chars for AUDIT_KEY and API keys)

# 3. Start with Docker Compose
docker compose up --build -d

# 4. Verify health
curl http://localhost:8000/health

# 5. Run the full demo script
bash demo/quickstart-clean.sh
```

For detailed commands, see [DEMO_COMMANDS.md](DEMO_COMMANDS.md).

---

## Verifying CI is Green

The project uses GitHub Actions for continuous integration:

- **Lint**: Ruff check + Ruff format
- **Security**: Bandit SAST + Semgrep
- **Tests**: Python 3.11 & 3.12 (139 tests)
- **Rust**: Build + tests (PyO3 engine)
- **Docker**: Multi-stage build verification
- **Helm**: Chart lint

To verify locally:

```bash
# Lint
ruff check .
ruff format --check .

# Tests (requires liboqs installed)
AUDIT_KEY="test-audit-key-secure-enough-for-pytest-32chars!" \
pytest tests/ -v
```

---

## Verifying Go Tests

```bash
cd sdk-go
go test ./... -v
go build ./...
go vet ./...
```

---

## Verifying Python Tests

```bash
AUDIT_KEY="test-audit-key-secure-enough-for-pytest-32chars!" \
pytest tests/ -v --tb=short
```

---

## Project Maturity

| Aspect | Status |
|--------|--------|
| Core encryption engine | Working, tested |
| API endpoints | Complete, documented |
| Audit trail | Working, HMAC-signed |
| KMS providers (local) | Working |
| KMS providers (AWS/Vault/Azure) | Implemented, enterprise-licensed |
| Python SDK | Complete, tested |
| Go SDK | Complete, tested |
| Docker deployment | Working |
| CI/CD | GitHub Actions configured |
| Observability | Prometheus + OpenTelemetry |
| Documentation | Comprehensive |
| External crypto audit | **Not yet performed** |
| Revenue | **None yet** |
| Production customers | **None yet** |

---

## Honesty Statement

This is a **pre-commercial technical asset**. It has:

- Working code with 139 passing tests
- Comprehensive documentation
- CI/CD pipeline
- Two client SDKs
- Enterprise KMS integrations

It does **not yet** have:

- Independent cryptographic audit
- Revenue or paying customers
- Production deployment history
- SOC 2 or ISO 27001 certification
- Bug bounty program

The project is ready for **POC, integration, acquisition, or further development**.

---

## Additional Documentation

- [VIDEO_DEMO_SCRIPT.md](VIDEO_DEMO_SCRIPT.md) — 3-minute video script
- [DEMO_COMMANDS.md](DEMO_COMMANDS.md) — Exact demo commands
- [SCREENSHOT_CHECKLIST.md](SCREENSHOT_CHECKLIST.md) — Recommended screenshots
- [STATELESS_EXPLANATION.md](STATELESS_EXPLANATION.md) — Stateless mode explained
- [BUYER_ONE_PAGER.md](BUYER_ONE_PAGER.md) — Buyer summary document
- [PROOF_OF_USAGE_REPORT.md](PROOF_OF_USAGE_REPORT.md) — Full proof of usage report
- [CREATION_SUMMARY.md](CREATION_SUMMARY.md) — Creation summary