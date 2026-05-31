# Simplified Threat Model

## Assets

- Audit HMAC keys (`AUDIT_KEY_v*`)
- API keys (operator / auditor)
- Kyber private keys (client-side; not stored by enclave)
- Audit log integrity

## Trust Boundaries

| Zone | Trust |
|------|-------|
| Client | Holds PQC private keys |
| Enclave API | Stateless crypto + audit signing |
| PostgreSQL | Persistent audit + API key hashes |
| KMS (future) | Root of trust for audit keys |

## Threats & Mitigations

| Threat | Mitigation |
|--------|------------|
| Stolen API key | SHA-256 storage; rotation; RBAC least privilege |
| Audit log tampering | HMAC per entry; verify on read; `entry_hash` chain prep |
| Payload flooding | 20 MB limit; rate limits (SlowAPI) |
| Downgrade / weak crypto | Fixed Kyber768 + AES-256-GCM |
| Container escape | Non-root user, cap_drop ALL, resource limits |
| Secret in image | Explicit COPY list; `.dockerignore`; env-only secrets |
| SQL injection | SQLAlchemy ORM parameterization |
| Error oracle (unseal) | Opaque 401 message |

## Out of Scope (current release)

- HSM-backed PQC key storage (keys returned to client)
- Full hash-chain verification UI
- mTLS (deploy at ingress)
