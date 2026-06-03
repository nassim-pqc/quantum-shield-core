# Quantum Shield Core — FIPS Readiness Assessment

> **Date**: June 2026  
> **Purpose**: Honest assessment of FIPS 140-3 readiness  
> **Audience**: Enterprise security teams, compliance officers, technical buyers

---

## ⚠️ Important Disclaimer

**Quantum Shield Core is NOT FIPS certified, FIPS compliant, or FIPS validated.**

The terms used in this document are:
- **FIPS-aware** — Designed with FIPS considerations
- **FIPS-readiness** — Positioned for future FIPS validation
- **Designed with FIPS considerations** — Uses FIPS-approved algorithms where possible
- **Requires external validation before compliance claims** — Cannot make compliance claims

**No FIPS compliance claims should be made based on this document.**

---

## 1. Algorithm Alignment with FIPS

### 1.1 Algorithms Used

| Algorithm | Usage in QSC | FIPS Status | Notes |
|-----------|-------------|-------------|-------|
| ML-KEM-768 (Kyber768) | Key encapsulation | FIPS 203 (finalized 2024) | NIST PQC standard |
| AES-256-GCM | Symmetric encryption | FIPS 197 + SP 800-38D | FIPS-approved AEAD |
| SHA-256 | Key derivation, hashing | FIPS 180-4 | FIPS-approved hash |
| HMAC-SHA256 | Audit log signing | FIPS 198-1 | FIPS-approved MAC |

### 1.2 Algorithm Analysis

| Requirement | Status | Explanation |
|-------------|--------|-------------|
| FIPS-approved algorithms | ✅ | AES-256-GCM, SHA-256, HMAC-SHA256 are FIPS-approved |
| FIPS-approved key sizes | ✅ | AES-256 (256-bit key), SHA-256 (256-bit output) |
| FIPS-approved modes | ✅ | GCM is an approved mode of operation |
| FIPS-approved key derivation | ⚠️ | SHA-256 used for KDF; SP 800-108 compliant if used correctly |
| FIPS-approved random generation | ⚠️ | Uses `os.urandom()` which delegates to OS CSPRNG |

---

## 2. What Would Be Required for FIPS 140-3 Validation

### 2.1 FIPS 140-3 Levels

| Level | Description | QSC Readiness |
|-------|-------------|---------------|
| Level 1 | Basic security | Partially ready |
| Level 2 | Tamper-evident | Not ready |
| Level 3 | Tamper-resistant | Not ready |
| Level 4 | Physical security | Not ready |

### 2.2 Requirements for FIPS 140-3

| Requirement | Status | Gap |
|-------------|--------|-----|
| Cryptographic Module | ❌ | No bounded cryptographic module defined |
| Finite State Model | ❌ | No formal state model |
| Physical Security | ❌ | Software-only module |
| Operational Environment | ❌ | Not evaluated in FIPS environment |
| Key Management | ⚠️ | KMS providers exist but not FIPS-validated |
| Self-Tests | ❌ | No power-up self-tests implemented |
| Design Assurance | ❌ | No formal design documentation per FIPS |
| Mitigation of Attacks | ❌ | No formal threat analysis per FIPS |

---

## 3. Cryptographic Libraries

### 3.1 Dependencies

| Library | Version | FIPS Status | Notes |
|---------|---------|-------------|-------|
| liboqs-python | 0.14.1 | Not FIPS-validated | Open-source, not a validated module |
| liboqs | 0.14.0 | Not FIPS-validated | C library, not a validated module |
| pyca/cryptography | 42.0.7 | Uses OpenSSL | OpenSSL can be FIPS-validated (see below) |
| OpenSSL (underlying) | System | FIPS-validated builds exist | Requires FIPS-validated build |

### 3.2 OpenSSL FIPS Considerations

If using a FIPS-validated OpenSSL build:
- AES-256-GCM operations would be FIPS-compliant
- SHA-256 operations would be FIPS-compliant
- HMAC-SHA256 operations would be FIPS-compliant

**However**: The Python `cryptography` library wraps OpenSSL, and the specific build/linking configuration determines FIPS compliance.

---

## 4. What a FIPS Validation Would Require

### 4.1 Estimated Effort

| Phase | Duration | Cost Estimate |
|-------|----------|---------------|
| Module definition | 2-4 weeks | $20K-$40K |
| Implementation changes | 4-8 weeks | $40K-$80K |
| Lab testing | 8-16 weeks | $50K-$150K |
| Certification | 4-8 weeks | $20K-$50K |
| **Total** | **18-36 weeks** | **$130K-$320K** |

### 4.2 Recommended Approach

1. **Define a cryptographic module boundary** — What exactly is the "module"?
2. **Use FIPS-validated OpenSSL** — For AES-GCM and SHA-256
3. **Implement power-up self-tests** — Algorithm validation tests
4. **Document operational environment** — OS, hardware, configuration
5. **Engage a FIPS lab** — e.g., Acumen, Leidos, Gossamer
6. **Submit for CAVP + CMVP** — Cryptographic Algorithm + Module validation

---

## 5. Practical Recommendations

### 5.1 For Enterprise Buyers

| Recommendation | Priority |
|----------------|----------|
| Use FIPS-validated OpenSSL build | High |
| Implement power-up self-tests | High |
| Document cryptographic module boundary | High |
| Engage FIPS lab for assessment | Medium |
| Plan 6-12 month timeline | Medium |

### 5.2 For Integration Partners

| Recommendation | Priority |
|----------------|----------|
| Deploy on FIPS-validated OS (e.g., AWS FIPS endpoints) | High |
| Use FIPS-validated KMS (AWS KMS FIPS endpoint) | High |
| Configure TLS 1.2+ with FIPS-approved ciphers | High |
| Document FIPS configuration in deployment guide | Medium |

---

## 6. FIPS-Ready Deployment Options

### 6.1 AWS FIPS Endpoints

AWS provides FIPS endpoints for KMS:
```
https://kms-fips.us-east-1.amazonaws.com
```

### 6.2 Azure FIPS Endpoints

Azure Key Vault has FIPS-validated HSM options:
- Soft-delete + purge protection
- FIPS 140-2 Level 2 validated HSM

### 6.3 HashiCorp Vault FIPS

HashiCorp Vault Enterprise includes FIPS 140-2 compliant builds.

---

## 7. Summary

| Aspect | Status |
|--------|--------|
| Uses FIPS-approved algorithms | ✅ Yes (AES-256-GCM, SHA-256, HMAC-SHA256) |
| FIPS 140-3 certified | ❌ No |
| FIPS 140-3 compliant | ❌ No |
| FIPS-aware | ✅ Yes |
| FIPS-readiness | ⚠️ Partially — requires module definition and validation |
| Can be deployed on FIPS-validated infrastructure | ✅ Yes (with appropriate configuration) |

---

## 8. Honest Assessment

Quantum Shield Core uses **FIPS-approved algorithms** (AES-256-GCM, SHA-256, HMAC-SHA256) and can be deployed on **FIPS-validated infrastructure** (AWS FIPS endpoints, Azure FIPS HSM). However, the **cryptographic module itself is not FIPS-validated** and would require significant effort to achieve FIPS 140-3 certification.

For enterprise buyers requiring FIPS compliance:
1. Deploy on FIPS-validated infrastructure
2. Use FIPS-validated KMS providers
3. Plan for independent FIPS validation if required by regulation
4. Document the FIPS configuration for auditors

---

*This document is honest and does not make false FIPS compliance claims. FIPS validation requires external certification by an accredited laboratory.*