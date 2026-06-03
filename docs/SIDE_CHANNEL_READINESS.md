# Quantum Shield Core — Side-Channel Readiness Assessment

> **Date**: June 2026  
> **Purpose**: Honest assessment of side-channel attack resistance  
> **Audience**: Security engineers, cryptographers, technical buyers

---

## ⚠️ Important Disclaimer

**Quantum Shield Core is NOT side-channel proof, side-channel resistant, or formally verified.**

The terms used in this document are:
- **Side-channel-aware** — Awareness of side-channel risks
- **Uses hardened primitives where delegated to crypto libraries** — Relies on library implementations
- **Requires independent audit for high-assurance environments** — Cannot guarantee resistance

**No side-channel resistance claims should be made based on this document.**

---

## 1. Side-Channel Attack Categories

| Attack Type | Description | QSC Relevance |
|-------------|-------------|---------------|
| **Timing attacks** | Measure time variations to infer secrets | Medium — HMAC comparison is constant-time |
| **Power analysis** | Measure power consumption during crypto operations | Low — Software implementation |
| **Electromagnetic emanation** | Measure EM radiation during operations | Low — Software implementation |
| **Cache attacks** | Exploit CPU cache behavior | Medium — Possible on shared hardware |
| **Branch prediction** | Exploit branch predictor behavior | Low — Limited branching in crypto path |
| **Memory access patterns** | Exploit memory allocation patterns | Medium — Possible with ML-KEM operations |

---

## 2. Existing Protections

### 2.1 Constant-Time Comparison

| Location | Protection | Status |
|----------|------------|--------|
| `security_engine.py` line 215 | `hmac.compare_digest()` | ✅ Constant-time comparison |
| `auth.py` line 30 | SHA-256 hash comparison | ⚠️ Database lookup (not constant-time in DB) |

**Analysis**: The HMAC signature verification uses `hmac.compare_digest()`, which is a constant-time comparison function provided by Python's standard library. This prevents timing attacks on signature verification.

### 2.2 Cryptographic Library Delegation

| Operation | Library | Side-Channel Protection |
|-----------|---------|------------------------|
| AES-256-GCM encryption | pyca/cryptography (OpenSSL) | ✅ Delegated to OpenSSL (hardware-accelerated AES-NI) |
| AES-256-GCM decryption | pyca/cryptography (OpenSSL) | ✅ Delegated to OpenSSL |
| SHA-256 hashing | Python hashlib / OpenSSL | ✅ Delegated to OpenSSL |
| HMAC-SHA256 | Python hmac / Rust engine | ⚠️ Python hmac is not constant-time; Rust engine is |
| ML-KEM-768 operations | liboqs | ⚠️ Depends on liboqs implementation |

### 2.3 Rust Engine (When Available)

| Operation | Rust Engine | Constant-Time |
|-----------|-------------|---------------|
| HMAC-SHA256 signing | `quantum_shield_engine` | ✅ When Rust engine is loaded |
| HMAC verification | `quantum_shield_engine` | ✅ When Rust engine is loaded |
| AES-GCM encrypt | `quantum_shield_engine` | ✅ When Rust engine is loaded |
| AES-GCM decrypt | `quantum_shield_engine` | ✅ When Rust engine is loaded |

**Note**: The Rust engine is optional. When not available, Python fallbacks are used.

---

## 3. Known Vulnerabilities

### 3.1 Python HMAC Fallback

**Location**: `security_engine.py` lines 190, 214  
**Issue**: When the Rust engine is not available, `hmac.new()` is used for signing, and `hmac.compare_digest()` is used for verification. While `hmac.compare_digest()` is constant-time, the HMAC computation itself may not be constant-time in the Python fallback.

**Impact**: Low — Timing differences are likely too small to exploit in practice, but theoretically possible.

**Mitigation**: Use the Rust engine (which provides constant-time HMAC) or implement a constant-time HMAC in Python.

### 3.2 Database Key Hash Comparison

**Location**: `auth.py` line 30-33  
**Issue**: API key verification queries the database by SHA-256 hash. The database comparison may not be constant-time.

**Impact**: Low — The hash is sent to the database, not compared locally. Database-level timing attacks are difficult to exploit.

**Mitigation**: Use a constant-time comparison after retrieving the hash from the database.

### 3.3 ML-KEM Operations via liboqs

**Location**: `security_engine.py` lines 93-96, 106-107, 139-140  
**Issue**: ML-KEM operations are delegated to liboqs. The side-channel resistance depends on the liboqs implementation.

**Impact**: Medium — liboqs is actively developed and includes side-channel mitigations, but formal verification is not complete.

**Mitigation**: Use a FIPS-validated or formally verified ML-KEM implementation when available.

### 3.4 Error Messages

**Location**: `main.py` lines 431-435, 466-470  
**Issue**: Error messages are generic ("Seal operation failed", "Unseal failed"). This is good — no internal details are leaked.

**Impact**: None — Error messages do not leak sensitive information.

---

## 4. Areas Requiring External Audit

| Area | Risk Level | Priority |
|------|------------|----------|
| ML-KEM-768 implementation (liboqs) | Medium | High |
| AES-GCM implementation (OpenSSL) | Low | Medium |
| HMAC implementation (Python fallback) | Low | Medium |
| Key derivation (SHA-256) | Low | Low |
| Overall system integration | Medium | High |

**Recommendation**: Engage a cryptographic security firm for a side-channel audit before production deployment in high-assurance environments.

---

## 5. Recommendations

### 5.1 Immediate Actions

| Action | Priority | Effort |
|--------|----------|--------|
| Enable Rust engine for constant-time operations | High | Low |
| Review liboqs side-channel mitigations | Medium | Low |
| Document side-channel risks for auditors | Medium | Low |

### 5.2 Medium-Term Actions

| Action | Priority | Effort |
|--------|----------|--------|
| Implement constant-time HMAC in Python fallback | Medium | Medium |
| Conduct side-channel timing analysis | High | High |
| Engage external cryptographic audit | High | High |

### 5.3 Long-Term Actions

| Action | Priority | Effort |
|--------|----------|--------|
| Formally verify critical crypto paths | Low | Very High |
| Implement side-channel countermeasures in liboqs bindings | Medium | High |
| Achieve FIPS 140-3 validation (includes side-channel testing) | Medium | Very High |

---

## 6. Honest Assessment

| Aspect | Status |
|--------|--------|
| Side-channel-aware | ✅ Yes — awareness of risks documented |
| Constant-time HMAC verification | ✅ Yes — uses `hmac.compare_digest()` |
| Constant-time HMAC signing | ⚠️ Depends on Rust engine |
| Constant-time AES-GCM | ✅ Yes — delegated to OpenSSL (hardware AES-NI) |
| Side-channel proof | ❌ No — not formally verified |
| Formally verified | ❌ No — no formal verification |
| Independent side-channel audit | ❌ No — not yet performed |

---

## 7. What This Means for Enterprise Buyers

### For Standard Enterprise Use
- The existing protections are **adequate for most enterprise use cases**
- Side-channel attacks require physical access or shared hardware
- Cloud environments (AWS, Azure) provide hardware isolation

### For High-Assurance Environments
- **Independent side-channel audit is recommended**
- Consider using the Rust engine for constant-time operations
- Deploy on dedicated hardware if side-channel resistance is critical

### For Regulated Industries
- Document the side-channel risk assessment
- Include side-channel considerations in security audits
- Plan for independent cryptographic audit

---

## 8. Conclusion

Quantum Shield Core provides **basic side-channel awareness** through constant-time comparison (`hmac.compare_digest`) and delegation to hardened crypto libraries (OpenSSL, liboqs). However, it is **not formally verified** for side-channel resistance and **requires independent audit** for high-assurance environments.

The project takes a **pragmatic approach**: delegate to well-tested libraries where possible, document risks honestly, and recommend external audit for critical deployments.

---

*This document is honest and does not make false side-channel resistance claims. Side-channel resistance requires formal verification and independent audit.*