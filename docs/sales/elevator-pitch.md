# Elevator Pitch — Quantum Shield Core

_"Post-quantum cryptography as a microservice. Production-ready in 30 minutes."_

Quantum Shield Core is a stateless cryptographic microservice that provides **ML-KEM-768** (NIST FIPS 203) key encapsulation and **AES-256-GCM** hybrid encryption through a simple REST API.

**Why it matters**: By 2030, quantum computers will break RSA and ECC. Organizations migrating to post-quantum cryptography need a drop-in replacement — not a multi-year rearchitecture.

**What it does**: 
- Generate post-quantum key pairs (ML-KEM-768 / Kyber768)
- Hybrid encrypt (seal) data with Kyber768 + AES-256-GCM
- Hybrid decrypt (unseal) data with matching keys
- Maintain a tamper-evident, HMAC-signed audit trail

**What makes it credible**:
- NIST-standard algorithms (FIPS 203, SP 800-38D)
- Memory-safe Rust core with constant-time cryptography
- 139 passing tests, 3 SDKs (Python, Go, REST)
- Append-only signed audit trail for compliance
- Stateless architecture — no private keys stored server-side

**Who needs it**: Organizations handling sensitive data that must remain confidential beyond 2030 — defense, finance, healthcare, critical infrastructure.

**Deploy**: One Docker command. Use it today.