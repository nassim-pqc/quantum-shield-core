# Quantum Shield Core — Checklist Before Sending

> **Purpose**: Verify everything is ready before contacting prospects  
> **Internal use only**  
> **Date**: June 2026

---

## Pre-Send Checklist

### Code Quality

- [ ] CI is green on GitHub Actions
- [ ] `ruff check .` passes
- [ ] `ruff format --check .` passes
- [ ] `go test ./...` passes (sdk-go)
- [ ] `go build ./...` succeeds
- [ ] `go vet ./...` passes
- [ ] No secrets in the repository
- [ ] No API keys in the code

### Documentation

- [ ] README.md is up to date
- [ ] Evidence pack is complete (`evidence/`)
- [ ] Performance benchmarks are recent (`benchmarks/performance/`)
- [ ] FIPS readiness doc is honest (`docs/FIPS_READINESS.md`)
- [ ] Side-channel doc is honest (`docs/SIDE_CHANNEL_READINESS.md`)
- [ ] Container hardening doc is complete (`docs/CONTAINER_HARDENING.md`)
- [ ] PDF report exists (`reports/Quantum_Shield_Core_Full_Report.pdf`)

### Sales Package

- [ ] `sales-package/README.md` is complete
- [ ] `sales-package/BUYER_SUMMARY.md` is ready
- [ ] `sales-package/TECHNICAL_OVERVIEW.md` is ready
- [ ] `sales-package/PROOF_OF_USAGE.md` is ready
- [ ] `sales-package/VALUATION_NOTE.md` is ready
- [ ] `sales-package/KNOWN_LIMITATIONS.md` is ready
- [ ] `sales-package/OUTREACH_MESSAGE.md` is ready
- [ ] `sales-package/DUE_DILIGENCE_INDEX.md` is ready
- [ ] `sales-package/SCREENSHOT_REQUIREMENTS.md` is ready
- [ ] `sales-package/VIDEO_DEMO_GUIDE.md` is ready
- [ ] `sales-package/CHECKLIST_BEFORE_SENDING.md` is complete
- [ ] `sales-package/attachments/` folder is ready

### Screenshots

- [ ] CI Actions green screenshot
- [ ] Repository main page screenshot
- [ ] README rendered screenshot
- [ ] Evidence directory screenshot
- [ ] Benchmark results screenshot
- [ ] Dockerfile.hardened screenshot
- [ ] KMS providers screenshot
- [ ] Go tests passing screenshot
- [ ] Ruff checks passing screenshot
- [ ] Document vault example screenshot
- [ ] CI history screenshot
- [ ] Benchmark execution screenshot

### Video

- [ ] Video is recorded (3 minutes max)
- [ ] Video is clear and professional
- [ ] Audio is clean (no background noise)
- [ ] Terminal font is readable
- [ ] All demo commands work
- [ ] Video is uploaded (unlisted on YouTube or similar)

### Attachments

- [ ] PDF report copied to `attachments/`
- [ ] Screenshots copied to `attachments/screenshots/`
- [ ] Video link added to `attachments/README.md`
- [ ] One-pager copied to `attachments/`
- [ ] Proof-of-usage report copied to `attachments/`
- [ ] Benchmark report copied to `attachments/`

### Prospect Preparation

- [ ] Prospect list is ready
- [ ] Personalized message is prepared
- [ ] Price range is decided
- [ ] Timeline is clear
- [ ] Follow-up plan is defined

### Final Verification

- [ ] No secrets in any document
- [ ] No internal URLs or credentials
- [ ] No exaggerated claims
- [ ] All "NOT" disclaimers are present
- [ ] Version number is current (1.0.0)
- [ ] Date is current (June 2026)
- [ ] Contact information is correct

---

## Quick Commands

```bash
# Verify code quality
ruff check . && ruff format --check .
cd sdk-go && go test ./... && go build ./... && go vet ./...

# Generate fresh benchmarks
python scripts/run_performance_benchmarks.py --iterations 30

# Verify no secrets
grep -r "password\|secret\|api_key\|token" --include="*.py" --include="*.md" .
```

---

## Red Flags to Check

| Red Flag | Action |
|----------|--------|
| Secrets in code | Remove immediately |
| Exaggerated claims | Fix before sending |
| Missing disclaimers | Add before sending |
| Broken links | Fix before sending |
| Outdated information | Update before sending |
| Missing "NOT" statements | Add before sending |

---

*Use this checklist before every prospect contact. The goal is to be honest, professional, and prepared.*