# FULL PROJECT VALUATION — Quantum Shield Core
**Date:** 2026-03-06  
**Methodology:** Evidence-based code valuation + market comparables

---

## 1. CODE VALUATION (Code Alone)

### 1.1 Source Code Metrics

| Component | Files | Lines of Code | Estimated Effort |
|---|---|---|---|
| Python API (main.py, etc.) | 8 core files | ~1,500 | 3-4 months |
| KMS Providers | 4 files | ~1,585 | 2-3 months |
| Rust Engine | 4 files | ~450 | 1-2 months |
| Python SDK | 2 files | ~285 | 2-3 weeks |
| Go SDK | 4 files | ~500 | 1-2 months |
| Tests | 9 files | ~1,800 | 2-3 months |
| CI/CD & Deploy | 6 files | ~300 | 2-3 weeks |
| Documentation | 25+ files | ~5,000 | 2-3 months |
| Frontend/Examples | 5 files | ~600 | 2-3 weeks |
| **Total** | **~60+ files** | **~12,000** | **12-18 engineer-months** |

### 1.2 Development Cost (replacement cost)

| Cost Type | Low Estimate | High Estimate | Notes |
|---|---|---|---|
| Engineering (senior) | €180K | €270K | 12 months × €15K-22.5K/mo |
| Security audit | €15K | €40K | External PQC audit required |
| liboqs integration | €20K | €40K | C library build + integration |
| Multi-cloud KMS | €30K | €60K | AWS + Azure + Vault expertise |
| Rust + PyO3 | €20K | €30K | Niche expertise premium |
| **Code Replacement Value** | **€265K** | **€440K** | |

### 1.3 IP Valuation Factors

| Factor | Adjustment | Reason |
|---|---|---|
| PQC expertise (Kyber768) | +20% | Specialized, high-demand skill |
| Multi-cloud KMS drivers | +15% | Reusable across industries |
| Open-source license | -20% | No exclusivity |
| No FIPS certification | -15% | Limited regulated market |
| Stub enterprise license | -10% | No revenue protection |
| **Adjusted Code Value** | **€212K** | **— €352K** |

**Verdict (Code Alone):**
- **Conservative:** €212,000
- **Optimistic:** €352,000

---

## 2. PRODUCT VALUATION (Without Customers)

### 2.1 Asset-Based Valuation

| Asset | Value | Basis |
|---|---|---|
| Code repository (60+ source files) | €212K-352K | Replacement cost |
| Documentation (25+ docs) | €25K-50K | Technical writing cost |
| CI/CD + Helm charts | €10K-25K | DevOps engineering |
| Test suite (177 passing tests) | €30K-60K | Test engineering |
| Brand + Repository | €20K-50K | GitHub presence, Apache 2.0 license |
| **Total Asset Value** | **€297K-537K** | |

### 2.2 Cost-to-Duplicate (without customers)

| Item | Cost | Period |
|---|---|---|
| Rebuild from scratch | €265K-440K | 12-18 months |
| Security + compliance prep | €30K-60K | 3-6 months |
| Go SDK completion | €15K-30K | 1-2 months |
| PyPI packaging | €5K-10K | 2-3 weeks |
| Production hardening | €40K-80K | 3-6 months |
| **Total** | **€355K-620K** | |

### 2.3 Value to Strategic Buyer

| Buyer Type | Strategic Value | Rationale |
|---|---|---|
| **Crypto agility vendor** | €500K-1M | Skip 12-18 months of R&D |
| **Security consulting firm** | €300K-500K | NIS 2 compliance tool for clients |
| **HSM manufacturer** | €200K-400K | Add PQC to existing product |
| **SIEM/observability vendor** | €150K-300K | Add PQC audit pipeline |

**Verdict (Product, No Customers):**
- **Conservative:** €300,000
- **Fair Market:** €450,000
- **Strategic:** €750,000

---

## 3. VALUATION WITH POC

### 3.1 POC Scenarios

| Scenario | Value Uplift | Justification |
|---|---|---|
| Single POC (1 enterprise client) | +€100K-200K | Demonstrated value, de-risked |
| 2-3 POCs in parallel | +€300K-600K | Validation across verticals |
| First paid POC | +€100K-150K | Revenue validation |

### 3.2 Adjusted Valuation with POC

| Scenario | Value Range |
|---|---|
| 1 POC (enterprise pilot) | €400K-650K |
| 2-3 POCs (multi-vertical) | €600K-1.05M |
| First paid customer | €500K-750K |

---

## 4. VALUATION WITH REVENUE

### 4.1 Revenue Model (Projected)

| Revenue Stream | ARR per Customer | Target Customers | Total ARR |
|---|---|---|---|
| Self-hosted Enterprise License | €12K-48K/yr | 10-50 | €120K-2.4M |
| Managed SaaS (monthly) | €1K-5K/mo | 20-100 | €240K-6M |
| Support + Consulting | €50K-150K/yr | 5-20 | €250K-3M |
| White-label/OEM | €30K-120K/yr | 2-10 | €60K-1.2M |

### 4.2 SaaS Multiples

| ARR | Multiple | Valuation |
|---|---|---|
| €100K (Seed) | 10-15x | €1M-1.5M |
| €500K (Series A) | 15-25x | €7.5M-12.5M |
| €1M (Growth) | 20-30x | €20M-30M |
| €5M (Scale) | 25-50x | €125M-250M |

### 4.3 Comparison to Crypto Security Startups

| Company | ARR at Exit | Valuation | Multiple |
|---|---|---|---|
| **Web3 security avg** (2022-2024) | €1M-5M | €10M-100M | 10-20x |
| **Crypto infra avg** | €500K-2M | €5M-40M | 10-20x |
| **Quantum safe companies** | (pre-revenue) | €2M-10M | N/A (speculative) |

---

## 5. FINAL VALUATION RANGES

| Scenario | Conservative | Fair Value | Optimistic |
|---|---|---|---|
| **Code Only** | €212K | €280K | €352K |
| **Product (no customers)** | €300K | €450K | €750K |
| **With 1 enterprise POC** | €400K | €550K | €800K |
| **With €100K ARR** | €1.0M | €1.5M | €2.0M |
| **With €500K ARR** | €7.5M | €10M | €12.5M |
| **With €1M+ ARR** | €20M | €25M | €30M |

### 5.1 Valuation Justification

**Current state (code + docs):**
- The codebase represents 12-18 senior engineer months of specialized work
- PQC + multi-cloud + Rust/PyO3 is a niche skillset commanding premium rates
- The code is well-structured and tested (177 passing tests)
- Open-source license limits enterprise valuation but enables community adoption

**With POC:**
- First enterprise POC de-risks the technology
- Validates the NIS 2 compliance use case (the primary market driver)
- Opens negotiation with strategic acquirers

**With Revenue:**
- SaaS multiples for cyber security are 10-30x ARR
- PQC is expected to be a growth market (NIS 2 deadline 2027, PQC migration 2025-2030)
- First-mover advantage in open-source PQC microservices

---

## 6. RISK ADJUSTMENT FACTORS

| Factor | Adjustment | Reason |
|---|---|---|
| No production deployments | -20% | De-risking required |
| Go SDK incomplete | -5% | Minor gap |
| No FIPS certification | -10% | Regulated market limitation |
| pip-audit disabled | -5% | Process gap |
| Open-source | -15% | No exclusivity |
| PQC market nascent | -10% | Timing risk |
| Strong competition (AWS/Azure) | -15% | Platform risk |
| **Total discount** | **-50% to -80%** | Currently pre-revenue |

---

## 7. RECOMMENDATION

### For Current Fundraising:
- **Pre-seed valuation:** €300K-€500K
- **Use of funds:** complete Go SDK, PyPI packaging, first 3 enterprise POCs

### For Strategic Sale:
- **Target valuation:** €750K-€1.5M
- **Buyer profile:** Security platform seeking PQC capability

### For organic growth:
- **Target first revenue:** within 6 months (NIS 2 compliance consulting + license)
- **Path to €100K ARR:** 5-10 enterprise licenses at €12K-€20K/yr