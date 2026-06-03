# Quantum Shield Core — Attachments

> **Purpose**: Files to include in the ZIP sent to prospects  
> **Date**: June 2026

---

## How to Use This Folder

1. Copy the required files into this folder
2. Create a ZIP from this folder
3. Send the ZIP with your outreach message

---

## Required Files

| File | Source | Status |
|------|--------|--------|
| `quantum-shield-full-report.pdf` | `reports/Quantum_Shield_Core_Full_Report.pdf` | ⚠️ Copy manually |
| `buyer-one-pager.md` | `evidence/BUYER_ONE_PAGER.md` | ⚠️ Copy manually |
| `proof-of-usage.md` | `evidence/PROOF_OF_USAGE_REPORT.md` | ⚠️ Copy manually |
| `benchmark-report.md` | `docs/PERFORMANCE_BENCHMARK_REPORT.md` | ⚠️ Copy manually |
| `technical-overview.md` | `sales-package/TECHNICAL_OVERVIEW.md` | ✅ Already in sales-package |
| `known-limitations.md` | `sales-package/KNOWN_LIMITATIONS.md` | ✅ Already in sales-package |

---

## Optional Files

| File | Source | When to Include |
|------|--------|-----------------|
| Screenshots (ZIP) | `screenshots/` | When available |
| Video link | YouTube/Vimeo | When recorded |
| Container hardening | `docs/CONTAINER_HARDENING.md` | For DevOps buyers |
| FIPS readiness | `docs/FIPS_READINESS.md` | For compliance buyers |
| Side-channel readiness | `docs/SIDE_CHANNEL_READINESS.md` | For security buyers |

---

## How to Copy

```bash
# Copy PDF report
cp reports/Quantum_Shield_Core_Full_Report.pdf sales-package/attachments/

# Copy one-pager
cp evidence/BUYER_ONE_PAGER.md sales-package/attachments/buyer-one-pager.md

# Copy proof of usage
cp evidence/PROOF_OF_USAGE_REPORT.md sales-package/attachments/proof-of-usage.md

# Copy benchmark report
cp docs/PERFORMANCE_BENCHMARK_REPORT.md sales-package/attachments/benchmark-report.md
```

---

## How to Create ZIP

```bash
cd sales-package
zip -r quantum-shield-sales-package.zip attachments/
```

---

## What NOT to Include

| Item | Reason |
|------|--------|
| Source code | Send GitHub link instead |
| Secrets or API keys | Never include secrets |
| `.env` files | Never include environment files |
| Database files | Never include `.db` or `.sqlite` |
| Large binary files | Keep ZIP under 10MB |

---

## File Naming

Use clear, professional naming:
- `quantum-shield-full-report.pdf`
- `buyer-one-pager.md`
- `proof-of-usage.md`
- `benchmark-report.md`
- `technical-overview.md`

---

*Keep this folder clean and professional. The ZIP is often the first impression.*