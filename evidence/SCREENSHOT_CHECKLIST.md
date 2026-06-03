# Quantum Shield Core — Screenshot Checklist

> Recommended screenshots for the proof of usage package.
> Each screenshot should be saved in `docs/images/captures/` or attached to the sales deck.

---

## 1. GitHub Actions — CI Green

**What to capture**: The GitHub Actions workflow runs page showing all jobs passing (green checkmarks).

**How to capture**:
1. Go to https://github.com/nassim-pqc/quantum-shield-core/actions
2. Click on a recent successful workflow run
3. Screenshot the full page showing all jobs green

**Why it's useful**: Proves the project has automated CI, all tests pass, and code quality is enforced.

**How to use in sales**: Include in technical due diligence section as evidence of engineering maturity.

---

## 2. Pull Request Merged

**What to capture**: A merged pull request showing code review, CI checks passing, and merge commit.

**How to capture**:
1. Go to https://github.com/nassim-pqc/quantum-shield-core/pulls?q=is%3Apr+is%3Amerged
2. Click on a representative merged PR
3. Screenshot the PR page showing review, CI status, and merge

**Why it's useful**: Shows collaborative development process and code review practices.

**How to use in sales**: Demonstrates engineering discipline and team practices.

---

## 3. Project Directory Structure

**What to capture**: The top-level directory tree showing organized project structure.

**How to capture**:
```bash
tree -L 2 -I '__pycache__|node_modules|.git|.venv' | head -80
```
Or screenshot from VS Code file explorer.

**Why it's useful**: Shows clean, organized codebase with clear separation of concerns.

**How to use in sales**: Proves professional code organization and maintainability.

---

## 4. OpenAPI / Swagger Documentation

**What to capture**: The Swagger UI showing all API endpoints with descriptions.

**How to capture**:
1. Start the service with `ENABLE_DOCS=true`
2. Open http://localhost:8000/docs in browser
3. Screenshot the full Swagger UI page

**Why it's useful**: Shows a complete, documented API ready for integration.

**How to use in sales**: Demonstrates API completeness and developer experience.

---

## 5. Health Endpoint Response

**What to capture**: Terminal showing the `/health` endpoint response.

**How to capture**:
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```
Screenshot the terminal output.

**Why it's useful**: Proves the service is operational and healthy.

**How to use in sales**: Quick proof that the system works.

---

## 6. Encryption Cycle (Seal + Unseal)

**What to capture**: Terminal showing the full encryption and decryption cycle.

**How to capture**:
1. Run `bash demo/demo.sh`
2. Screenshot the Seal and Unseal outputs

**Why it's useful**: Core functionality proof — the system encrypts and decrypts correctly.

**How to use in sales**: Primary technical demonstration.

---

## 7. Audit Trail

**What to capture**: Terminal showing audit log entries with HMAC signatures and integrity verification.

**How to capture**:
```bash
curl -s http://localhost:8000/api/v1/audit/logs \
  -H "X-API-Key: ${API_KEY_AUDITOR}" | python3 -m json.tool
```
Screenshot the output.

**Why it's useful**: Proves compliance-ready audit trail with tamper-evident signatures.

**How to use in sales**: Key differentiator for regulated industries.

---

## 8. Python Tests Passing

**What to capture**: Terminal showing pytest output with all tests passing.

**How to capture**:
```bash
AUDIT_KEY="test-audit-key-secure-enough-for-pytest-32chars!" \
pytest tests/ -v --tb=short 2>&1 | tail -30
```
Screenshot the terminal output.

**Why it's useful**: Proves code quality and test coverage.

**How to use in sales**: Evidence of engineering rigor.

---

## 9. Go Tests Passing

**What to capture**: Terminal showing Go test output with all tests passing.

**How to capture**:
```bash
cd sdk-go && go test ./... -v 2>&1 | tail -30
```
Screenshot the terminal output.

**Why it's useful**: Proves the Go SDK is tested and functional.

**How to use in sales**: Shows multi-language SDK support.

---

## 10. Go Build Success

**What to capture**: Terminal showing `go build ./...` completing without errors.

**How to capture**:
```bash
cd sdk-go && go build ./...
echo "Exit code: $?"
```
Screenshot the terminal output.

**Why it's useful**: Proves the Go SDK compiles cleanly.

**How to use in sales**: Technical verification for Go integration.

---

## 11. Go Vet Success

**What to capture**: Terminal showing `go vet ./...` completing without issues.

**How to capture**:
```bash
cd sdk-go && go vet ./...
echo "Exit code: $?"
```
Screenshot the terminal output.

**Why it's useful**: Shows Go code quality and static analysis.

**How to use in sales**: Additional Go quality assurance evidence.

---

## 12. Prometheus Metrics

**What to capture**: Terminal or browser showing Prometheus metrics endpoint.

**How to capture**:
```bash
curl -s http://localhost:8000/metrics | grep -E "^(qshield|crypto_ops|audit)" | head -20
```
Or open http://localhost:8000/metrics in browser and screenshot.

**Why it's useful**: Proves observability and monitoring capabilities.

**How to use in sales**: Shows production-readiness features.

---

## 13. KMS Provider Code

**What to capture**: VS Code or terminal showing the KMS provider implementations.

**How to capture**:
```bash
ls -la providers/kms/
```
Screenshot the file listing showing aws_kms.py, azure_kms.py, vault_kms.py, base.py.

**Why it's useful**: Proves enterprise KMS integration support.

**How to use in sales**: Shows enterprise readiness and cloud provider support.

---

## 14. Document Vault Example

**What to capture**: Terminal showing the Document Vault example running successfully.

**How to capture**:
```bash
python -m examples.document_vault.main
```
Screenshot the terminal output showing all steps completing.

**Why it's useful**: Real-world use case demonstration.

**How to use in sales**: Shows practical application beyond raw API calls.

---

## 15. README Overview

**What to capture**: Browser showing the GitHub repository README page.

**How to capture**:
1. Go to https://github.com/nassim-pqc/quantum-shield-core
2. Screenshot the top of the README with badges and description

**Why it's useful**: First impression of the project for visitors.

**How to use in sales**: Project identity and branding.

---

## 16. Docker Deployment

**What to capture**: Terminal showing Docker containers running.

**How to capture**:
```bash
docker compose ps
```
Screenshot the output showing both containers healthy.

**Why it's useful**: Proves Docker deployment works.

**How to use in sales**: Deployment readiness evidence.

---

## 17. Ruff Lint Clean

**What to capture**: Terminal showing `ruff check .` with no errors.

**How to capture**:
```bash
ruff check . 2>&1 | tail -5
```
Screenshot the terminal output.

**Why it's useful**: Shows code quality and lint compliance.

**How to use in sales**: Engineering standards evidence.

---

## 18. Ruff Format Check

**What to capture**: Terminal showing `ruff format --check .` with no issues.

**How to capture**:
```bash
ruff format --check . 2>&1 | tail -5
```
Screenshot the terminal output.

**Why it's useful**: Shows consistent code formatting.

**How to use in sales**: Engineering standards evidence.

---

## Capture Tips

- Use **full-screen captures** (not partial windows)
- Use **dark terminal theme** for readability
- Add **annotations** to highlight key output lines
- Save as **PNG** (not JPEG) for text clarity
- Use consistent **font size** (14pt minimum) across all captures
- Include **timestamps** in terminal output when possible
- Keep captures **clean** — no personal files or browser tabs visible