# Objection Handling — Quantum Shield Core

## "Why not use liboqs directly?"

liboqs is a C library, not a service. Using it directly requires:
- Building and maintaining C bindings for your language
- Implementing your own API layer, authentication, rate limiting
- Building an audit trail from scratch
- Managing TLS, metrics, and observability
- Writing and maintaining all of this securely

Quantum Shield Core wraps liboqs into a production-grade microservice with authentication, audit, rate limiting, metrics, and deployment tooling — saving 2-4 months of development.

## "Why not develop this internally?"

Developing a production-grade cryptographic service internally costs **€80,000–€150,000** and takes **3-6 months**:
- Cryptographic implementation & security review: 4-8 weeks
- API design & authentication: 2-3 weeks
- Audit trail & compliance: 2-3 weeks
- Deployment & monitoring: 1-2 weeks
- Ongoing maintenance & CVE tracking: ongoing

Quantum Shield Core delivers the same in under 30 minutes for **€0 (self-hosted)** or subscription pricing.

## "Why ML-KEM-768 and not something else?"

- **ML-KEM-768** is the NIST standard (FIPS 203) for post-quantum key encapsulation
- Level 3 security (equivalent to AES-192) — sufficient for most use cases
- ML-KEM-512 is Level 1 (too weak for long-term confidentiality)
- ML-KEM-1024 is Level 5 (overhead: 1568 bytes public key vs 1184 for Level 3)
- 768 balances security, performance, and bandwidth

## "Why buy instead of build?"

| Factor | Build internally | Buy/Use Quantum Shield Core |
|--------|-----------------|---------------------------|
| Time to production | 3-6 months | 30 minutes |
| Development cost | €80k-€150k | Free (MIT) or subscription |
| Security audit cost | €20k-€40k | Included in development |
| Maintenance overhead | Full-time engineer | Community + optional support |
| Compliance readiness | Must build | HMAC audit trail included |

## "Is it production-ready?"

Yes. Evidence:
- 139 automated tests passing
- 3 SDKs (Python, Go, REST)
- Kubernetes Helm charts
- Prometheus metrics + OpenTelemetry tracing
- Rate limiting, RBAC, signed audit trail
- Docker container with multi-stage build

## "What about support?"

- MIT licensed — fully self-supported if desired
- Documentation: API guide, deployment guide, security guide
- ADRs document key technical decisions
- SDK examples for Python and Go
- Commercial support available (contact us)

## "How does it scale?"

- Stateless design: horizontal scaling via Kubernetes HPA
- SQLite for development, PostgreSQL for production
- Prometheus metrics for auto-scaling decisions
- Locust load tests included for benchmarking