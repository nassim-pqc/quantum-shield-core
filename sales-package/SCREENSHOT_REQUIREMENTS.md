# Quantum Shield Core — Screenshot Requirements

> **Purpose**: List of required screenshots for the sales package  
> **Internal use only**  
> **Date**: June 2026

---

## Required Screenshots

### 1. GitHub Actions (CI Green)

**What**: GitHub Actions workflow showing all jobs passing  
**Where**: `https://github.com/nassim-pqc/quantum-shield-core/actions`  
**Filename**: `screenshots/ci-actions-green.png`  
**Notes**: Show all jobs (lint, security, test, build) in green

### 2. Repository Main Page

**What**: GitHub repository main page with README visible  
**Where**: `https://github.com/nassim-pqc/quantum-shield-core`  
**Filename**: `screenshots/repo-main-page.png`  
**Notes**: Show stars, language breakdown, recent commits

### 3. README

**What**: README.md rendered on GitHub  
**Where**: `https://github.com/nassim-pqc/quantum-shield-core`  
**Filename**: `screenshots/readme-rendered.png`  
**Notes**: Show architecture diagram, features, benchmarks table

### 4. Evidence Directory

**What**: `evidence/` directory listing  
**Where**: `https://github.com/nassim-pqc/quantum-shield-core/tree/main/evidence`  
**Filename**: `screenshots/evidence-directory.png`  
**Notes**: Show all evidence files

### 5. Benchmark Results

**What**: `benchmarks/performance/results.md` rendered  
**Where**: Local file or GitHub  
**Filename**: `screenshots/benchmark-results.png`  
**Notes**: Show summary table with latency numbers

### 6. Dockerfile.hardened

**What**: `Dockerfile.hardened` content  
**Where**: `https://github.com/nassim-pqc/quantum-shield-core/blob/main/Dockerfile.hardened`  
**Filename**: `screenshots/dockerfile-hardened.png`  
**Notes**: Show multi-stage build, non-root user

### 7. KMS Providers

**What**: `providers/kms/` directory listing  
**Where**: `https://github.com/nassim-pqc/quantum-shield-core/tree/main/providers/kms`  
**Filename**: `screenshots/kms-providers.png`  
**Notes**: Show AWS, Azure, Vault provider files

### 8. Go SDK Tests

**What**: Go test output showing all tests passing  
**Where**: Terminal output  
**Filename**: `screenshots/go-tests-passing.png`  
**Notes**: Run `cd sdk-go && go test ./... -v` and capture

### 9. Ruff Checks

**What**: Ruff check and format output  
**Where**: Terminal output  
**Filename**: `screenshots/ruff-checks-passing.png`  
**Notes**: Run `ruff check . && ruff format --check .` and capture

### 10. Document Vault Example

**What**: `examples/document-vault/main.py`  
**Where**: `https://github.com/nassim-pqc/quantum-shield-core/blob/main/examples/document-vault/main.py`  
**Filename**: `screenshots/document-vault-example.png`  
**Notes**: Show the example integration code

### 11. CI History

**What**: GitHub Actions workflow history  
**Where**: `https://github.com/nassim-pqc/quantum-shield-core/actions`  
**Filename**: `screenshots/ci-history.png`  
**Notes**: Show multiple successful runs

### 12. Performance Benchmark

**What**: Benchmark execution output  
**Where**: Terminal output  
**Filename**: `screenshots/benchmark-execution.png`  
**Notes**: Run `python scripts/run_performance_benchmarks.py --iterations 10` and capture

---

## Naming Convention

All screenshots should follow this pattern:
```
screenshots/[descriptive-name].png
```

Examples:
- `screenshots/ci-actions-green.png`
- `screenshots/repo-main-page.png`
- `screenshots/benchmark-results.png`

---

## Storage

Store all screenshots in:
```
screenshots/
```

At the repository root. This directory should be:
- Created before taking screenshots
- Added to `.gitignore` if not committed
- Or committed if you want them in the repo

---

## Quality Requirements

| Requirement | Value |
|-------------|-------|
| Format | PNG |
| Resolution | At least 1920x1080 |
| Clarity | Text must be readable |
| Cropping | Show relevant content, not entire screen |
| Annotations | Optional, but helpful |

---

## Before Taking Screenshots

1. Ensure CI is green (check GitHub Actions)
2. Run benchmarks to generate fresh results
3. Run Go tests to verify they pass
4. Run Ruff checks to verify they pass
5. Clean up terminal output (no secrets, no errors)

---

*All screenshots should be honest and representative of the actual project state.*