# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a vulnerability

**Do not** open public GitHub issues for security vulnerabilities.

Email: `security@quantum-shield-core.io`

Include:
- Description and impact
- Steps to reproduce
- Affected version / commit
- Suggested fix (optional)

We aim to acknowledge within **48 business hours** and provide a remediation timeline for validated issues.

## Security design summary

- API keys stored as SHA-256 hashes only
- Audit logs: HMAC-SHA256 with key versioning
- Crypto: ML-KEM-768 + AES-256-GCM, mandatory AAD (`context`)
- Rate limiting via SlowAPI
- Security headers on all responses
- Docker: non-root, `cap_drop: ALL`, resource limits

## Dependency scanning

CI runs `pip-audit` and `bandit` on each push. Run locally:

```bash
pip-audit -r requirements.txt
bandit -r . -x ./tests,./.github
```
