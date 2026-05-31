# Security Guide

## Secrets

| Variable | Purpose | Min length |
|----------|---------|------------|
| `AUDIT_KEY_v1` | Audit HMAC | 32 chars |
| `API_KEY_OPERATOR` | Crypto + audit write | 32 chars |
| `POSTGRES_PASSWORD` | Database | strong |

Rotate audit keys by adding `AUDIT_KEY_v2` and updating `ACTIVE_AUDIT_KEY_VERSION`. Old logs remain verifiable.

## Headers

Enforced on all responses: `X-Content-Type-Options`, `X-Frame-Options`, `CSP`, `Cache-Control: no-store`, optional HSTS.

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Default | 200/min |
| Key generate | 10/min |
| Seal | 30/min |
| Unseal | 30/min |
| Audit read | 20/min |

## Docker Hardening

- Non-root `appuser` (uid 8888)
- `cap_drop: ALL`
- `read_only: true` + tmpfs `/tmp`
- Memory limit 768M (API)
- liboqs pinned to release tag `0.12.0`

## CI Security

- `bandit` static analysis
- `pip-audit` dependency CVE scan

## Production Checklist

- [ ] TLS termination at reverse proxy  
- [ ] Restrict `ENABLE_DOCS=false`  
- [ ] Restrict CORS `ALLOWED_ORIGINS`  
- [ ] External KMS (`KMS_PROVIDER`)  
- [ ] PostgreSQL backups + encryption at rest  
- [ ] Centralized log shipping (JSON logs + correlation ID)  
