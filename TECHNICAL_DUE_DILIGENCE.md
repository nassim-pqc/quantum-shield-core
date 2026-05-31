# Technical Due Diligence — Quantum Shield Core

**Version:** 1.0.0  
**Date:** May 2026  
**Recipient:** Qualified buyer — confidential document

---

## 1. What You Are Acquiring

### Included in the Transfer

| Deliverable | Detail | Status |
|-------------|--------|--------|
| Complete source code | Python 3.11, FastAPI, SQLAlchemy async | ✅ Production-ready |
| Cryptographic engine | ML-KEM-768 + AES-256-GCM + HMAC audit | ✅ Tested |
| Test suite | Unit + integration, ~75%+ coverage | ✅ Included |
| Python SDK client | With 3 integration examples | ✅ Included |
| Docker deployment | docker-compose.yml + Dockerfile multi-stage | ✅ Production-ready |
| Technical documentation | README, Architecture, Threat Model, ENV guide | ✅ Complete |
| Security documentation | Security Guide, SECURITY.md | ✅ Complete |
| CI/CD pipelines | GitHub Actions (tests, lint, security, release) | ✅ Configured |
| Audit dashboard | HTML UI with no external dependencies | ✅ Functional |
| Performance benchmarks | Scripts + charts + results | ✅ Included |
| Sales collateral | Business positioning + pricing guidance | ✅ Included |

### NOT Included (for acquirer to develop)

| Capability | Effort | Priority |
|-----------|--------|----------|
| Real AWS/Vault/Azure KMS | 3–5 days senior dev | Recommended |
| Multi-tenant with DB isolation | 2–3 weeks senior dev | Use-case dependent |
| Kubernetes Helm charts | 3–5 days devops | If K8s deployment |
| External penetration test | 15–40k€, 4–8 weeks | For enterprise buyers |
| CSPN ANSSI qualification | 15–40k€, 6–12 months | For public sector/OIV |
| Additional language SDKs | 1–2 weeks per language | Per roadmap |

---

## 2. Technical Architecture

### Technology Stack

```
FastAPI 0.111 + Python 3.11
SQLAlchemy 2.0 async + PostgreSQL 16 / SQLite
liboqs-python 0.14.1 (ML-KEM-768 / Kyber768)
cryptography 42.0.7 (AES-256-GCM)
Prometheus + OpenTelemetry + JSON structured logs
Docker multi-stage + docker-compose
Alembic (auto-migration on startup)
```

### API Endpoints

| Method | Endpoint | Role | Purpose |
|--------|----------|------|---------|
| GET | `/health` | Public | Service & DB health |
| GET | `/metrics` | Public | Prometheus metrics |
| POST | `/api/v1/keys/generate` | operator | Generate Kyber768 keypair |
| POST | `/api/v1/crypto/seal` | operator | Hybrid encrypt |
| POST | `/api/v1/crypto/unseal` | operator | Hybrid decrypt |
| POST | `/api/v1/audit/log` | operator, auditor | Write audit entry |
| GET | `/api/v1/audit/logs` | operator, auditor | Read audit entries |
| GET | `/api/v1/audit/stats` | operator, auditor | Audit statistics |

### Cryptographic Scheme

**Seal (encryption):**
```
Kyber768.Encap(pub_key) → ciphertext_pqc + shared_secret
SHA-256(shared_secret) → aes_key (32 bytes)
AESGCM.encrypt(aes_key, nonce, plaintext, context_AAD) → encrypted_data
```

**Unseal (decryption):**
```
Kyber768.Decap(priv_key, ciphertext_pqc) → shared_secret
SHA-256(shared_secret) → aes_key
AESGCM.decrypt(aes_key, nonce, encrypted_data, context_AAD) → plaintext
```

---

## 3. Security

### What Is Implemented

- **Authentication:** X-API-Key → SHA-256 hash → DB lookup → RBAC role
- **Timing resistance:** `hmac.compare_digest()` for key comparison
- **Oracle resistance:** Generic 401 error messages on unseal failure
- **HTTP security headers:** HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- **Rate limiting:** SlowAPI per IP and per endpoint
- **Fail-secure:** Refuses startup if AUDIT_KEY missing or too short
- **Container hardening:** Non-root user (UID 8888), cap_drop: ALL, read-only rootfs

### NOT Certified

- No external penetration test report
- No CSPN qualification (required for public sector in France)
- No SOC2/ISO 27001 (organizational process, outside this scope)

---

## 4. Dependencies & Licenses

| Dependency | Version | License |
|------------|---------|---------|
| FastAPI | 0.111.0 | MIT |
| SQLAlchemy | 2.0.31 | MIT |
| liboqs-python | 0.14.1 | MIT (Open Quantum Safe) |
| cryptography | 42.0.7 | Apache 2.0 / BSD |
| uvicorn | 0.30.1 | BSD |
| pydantic | 2.7.4 | MIT |
| alembic | 1.13.2 | MIT |
| slowapi | 0.1.9 | MIT |
| prometheus-client | 0.20.0 | Apache 2.0 |
| opentelemetry | 1.25.0 | Apache 2.0 |

**No proprietary or GPL/AGPL dependencies.** Acquirer can distribute and modify freely after transfer.

---

## 5. Testing & Quality

- **Coverage:** Report via `pytest --cov` (see `coverage_html/` after run)
- **Unit tests:** Cryptographic engine, audit store, RBAC authentication
- **Integration tests:** Full API workflow via httpx AsyncClient
- **Linting:** Ruff + Black (config in `ruff.toml`)
- **Security scanning:** Bandit + pip-audit in CI
- **CI/CD:** 5 GitHub Actions workflows (test, lint, security, docker, release)

---

## 6. Post-Acquisition Work Estimate

For an integrator or ESN commercializing this component:

**Phase 1 — Immediate production (2–4 weeks)**
- Wire real KMS (AWS or Vault): 3–5 days
- Customer network/infra adaptation: 1–2 days
- Team technical training: 1 day (SDK + docs provided)

**Phase 2 — Industrialization (1–3 months)**
- Multi-tenant isolation if needed: 2–3 weeks
- External penetration test: 4–8 weeks (book external firm)
- Integration into acquirer's product catalog

**Phase 3 — Advanced market positioning (6–12 months)**
- CSPN ANSSI qualification (for public sector/OIV market)
- Java or Go SDKs (if enterprise customers demand)

---

## 7. Quick Start for Technical Evaluation

```bash
git clone <repo>
cd quantum-shield-enclav
bash demo/quickstart-clean.sh
# → Launches stack, runs full workflow, displays results
```

After startup:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **Dashboard:** http://127.0.0.1:8000/dashboard
- **Metrics:** http://127.0.0.1:8000/metrics

---

## 8. File Structure

```
quantum-shield-enclav/
├── main.py                    # FastAPI app entry point
├── security_engine.py         # ML-KEM-768 + AES-GCM + HMAC
├── auth.py                    # RBAC authentication
├── audit_store.py             # Append-only audit persistence
├── database.py                # SQLAlchemy async setup
├── models.py                  # SQLAlchemy ORM models
├── constants.py               # Application constants
├── providers/kms/             # KMS abstraction (AWS/Vault/Azure stubs)
├── tests/                     # Unit + integration tests
├── benchmarks/                # Performance benchmarks
├── demo/                      # Demo scripts (quickstart, curl examples)
├── sdk/                       # Python client library
├── docs/                      # Technical documentation
├── observability/             # Logging, metrics, tracing
├── landing/                   # HTML landing page
├── docker-compose.yml         # Local dev stack
├── Dockerfile                 # Multi-stage production image
├── requirements.txt           # Python dependencies
├── .github/workflows/         # CI/CD pipelines
└── README.md                  # Project overview
```

---

## 9. FAQ

**Q: Can I use this in production immediately?**  
A: Yes, with two caveats:
1. Wire a real KMS (AWS/Vault/Azure) instead of the local env-var stub (~3–5 days)
2. Conduct your own security assessment or hire a penetration testing firm

**Q: What happens to private keys?**  
A: The enclave never stores client private keys. Clients receive private keys once and are responsible for secure storage (HSM, vault, KMS, or your application's secure key store).

**Q: Does it support multi-tenancy?**  
A: Structurally yes (the code separates by context/AAD and audit entries). Database-level isolation (separate tenants, separate audit logs) is not implemented; it's 2–3 weeks of development.

**Q: What if I want to use Azure / Vault / AWS KMS?**  
A: Providers are scaffolded in `providers/kms/`. Activate one by:
1. `pip install` the cloud SDK (boto3, hvac, azure-keyvault-keys)
2. Set environment variables (AWS_REGION, VAULT_ADDR, AZURE_KEY_VAULT_URL)
3. Replace the `get_audit_key()` stub with cloud calls

**Q: Is there a roadmap?**  
A: Roadmap is at the acquirer's discretion. Common asks:
- Multi-tenant isolation
- Additional language SDKs
- Kubernetes operators
- CSPN qualification (France)

---

*Document is confidential. Do not distribute without written permission from the transferor.*
