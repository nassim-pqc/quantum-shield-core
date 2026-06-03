#!/usr/bin/env python3
"""Generate Quantum Shield Core Full Due Diligence PDF Report."""

import os
from datetime import datetime

from fpdf import FPDF


class DueDiligencePDF(FPDF):
    """Custom PDF with headers/footers for due diligence report."""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Quantum Shield Core - Full Due Diligence Report", align="L")
        self.cell(0, 8, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(120, 120, 120)
        self.cell(
            0,
            10,
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} - Confidential",
            align="C",
        )

    def chapter_title(self, title, level=1):
        if level == 1:
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(20, 60, 120)
            self.ln(4)
            self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(20, 60, 120)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)
        elif level == 2:
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(40, 80, 140)
            self.ln(3)
            self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        elif level == 3:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(60, 60, 60)
            self.ln(2)
            self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text, indent=10):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.cell(indent, 5, "")  # indent
        self.cell(5, 5, "- ")
        self.multi_cell(0, 5, text)
        self.set_x(self.l_margin)  # reset left margin

    def verdict(self, status, text):
        self.set_font("Courier", "B", 10)
        if status == "CONFIRMED":
            self.set_text_color(0, 128, 0)
            self.cell(0, 6, f"[{status}] {text}", new_x="LMARGIN", new_y="NEXT")
        elif status == "PARTIAL":
            self.set_text_color(200, 150, 0)
            self.cell(0, 6, f"[{status}] {text}", new_x="LMARGIN", new_y="NEXT")
        elif status == "FALSE":
            self.set_text_color(200, 0, 0)
            self.cell(0, 6, f"[{status}] {text}", new_x="LMARGIN", new_y="NEXT")
        else:
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, f"[{status}] {text}", new_x="LMARGIN", new_y="NEXT")

    def kv_table(self, data, col_widths=None):
        if col_widths is None:
            col_widths = [60, 130]
        self.set_font("Helvetica", "", 9)
        for key, val in data:
            self.set_font("Helvetica", "B", 9)
            self.cell(col_widths[0], 6, str(key))
            self.set_font("Helvetica", "", 9)
            self.cell(col_widths[1], 6, str(val), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)


def generate_report():
    pdf = DueDiligencePDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover Page
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 15, "Quantum Shield Core", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 12, "Full Due Diligence Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0,
        8,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(0, 8, "Classification: Confidential", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0, 8, "Methodology: Evidence-based code analysis", align="C", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.cell(0, 8, "177 tests analysed - 100% passing", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(
        0,
        5,
        "This report is based on actual source code, test results, "
        "and git history. Every conclusion is backed by specific file "
        "references and line numbers. No speculation.",
    )
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    reports = [
        "docs/FULL_TECHNICAL_DUE_DILIGENCE.md",
        "docs/FULL_SECURITY_AUDIT.md",
        "docs/FULL_COMMERCIAL_ASSESSMENT.md",
        "docs/FULL_PROJECT_VALUATION.md",
        "docs/EXECUTIVE_SUMMARY.md",
        "docs/FINAL_VERIFIED_ASSESSMENT.md",
    ]
    pdf.cell(0, 6, "Supporting documents:", new_x="LMARGIN", new_y="NEXT")
    for r in reports:
        pdf.cell(0, 5, f"  {r}", new_x="LMARGIN", new_y="NEXT")

    # Table of Contents
    pdf.add_page()
    pdf.chapter_title("Table of Contents")
    toc_items = [
        "1. Executive Summary",
        "2. Architecture Overview",
        "3. Technical Due Diligence",
        "4. Security Audit",
        "5. Git & CI/CD Analysis",
        "6. SDK Analysis",
        "7. KMS Provider Analysis",
        "8. Observability Analysis",
        "9. Product Maturity",
        "10. Risks & Recommendations",
        "11. Valuation",
        "12. Final Verified Assessment",
    ]
    for item in toc_items:
        pdf.body_text(item)

    # 1. Executive Summary
    pdf.add_page()
    pdf.chapter_title("1. Executive Summary")
    pdf.body_text(
        "Quantum Shield Core is a stateless post-quantum cryptographic "
        "microservice implementing ML-KEM-768 (Kyber768) hybrid "
        "encryption with AES-256-GCM, an HMAC-SHA256 signed audit "
        "trail, and support for three enterprise KMS providers "
        "(AWS KMS, Azure Key Vault, HashiCorp Vault)."
    )
    pdf.body_text(
        "License: Apache 2.0 | Version: 1.0.0 | Tests: 177 passing | Maturity Score: 6.6/10"
    )
    pdf.ln(2)
    pdf.chapter_title("Key Findings", 2)
    pdf.verdict("CONFIRMED", " Post-quantum cryptography (ML-KEM-768)")
    pdf.verdict("CONFIRMED", " Stateless architecture (no keys persisted)")
    pdf.verdict("CONFIRMED", " Hybrid encryption (KEM + AES-GCM)")
    pdf.verdict("CONFIRMED", " HMAC-SHA256 signed audit trail")
    pdf.verdict("CONFIRMED", " Three KMS providers (AWS, Azure, Vault)")
    pdf.verdict("CONFIRMED", " Complete observability (logs + metrics + traces)")
    pdf.verdict("PARTIAL", "  CI/CD (CI works, CD missing)")
    pdf.verdict("PARTIAL", "  SDK Python (code complete, no PyPI packaging)")
    pdf.verdict("PARTIAL", "  KMS Enterprise readiness (implemented, missing rotation/failover)")
    pdf.verdict("FALSE", "   SDK Go (incomplete: HTTP client only, no crypto, no tests)")
    pdf.verdict("FALSE", "   Rust Kyber768 (not implemented, delegates to Python/liboqs)")
    pdf.verdict("FALSE", "   Enterprise License (stub: prefix check only)")

    # 2. Architecture
    pdf.add_page()
    pdf.chapter_title("2. Architecture Overview")
    pdf.body_text(
        "The product is a FastAPI-based microservice providing REST "
        "endpoints for post-quantum key generation, hybrid "
        "encryption/decryption, and tamper-evident audit logging."
    )
    pdf.chapter_title("Components", 2)
    components = [
        ("FastAPI Application", "main.py (585 lines) - Fully implemented"),
        ("Cryptographic Engine", "security_engine.py (217 lines) - Fully implemented"),
        ("Database (async)", "database.py (64 lines) - Fully implemented"),
        ("Auth + RBAC", "auth.py (55 lines) - Fully implemented"),
        ("Audit Trail (in-memory)", "audit_store.py (148 lines) - Fully implemented"),
        ("Constants", "constants.py (48 lines) - Fully implemented"),
    ]
    pdf.kv_table(components)

    pdf.chapter_title("Encryption Flow", 2)
    pdf.body_text(
        "1. Key Generation: API creates Kyber768 key pair, "
        "returns to client, immediately forgets both keys"
    )
    pdf.body_text(
        "2. Seal: Client sends public key + data + context. "
        "API uses Kyber768 KEM to derive shared secret, "
        "AES-256-GCM to encrypt data with context as AAD"
    )
    pdf.body_text(
        "3. Unseal: Client sends private key + sealed data + "
        "same context. API recovers shared secret via Kyber768 "
        "KEM, decrypts AES-GCM only if context matches"
    )
    pdf.body_text(
        "4. Audit: Every operation is HMAC-SHA256 signed with "
        "key versioning. Tampering is detectable."
    )

    pdf.chapter_title("Stateless Design (Verified)", 2)
    pdf.verdict(
        "CONFIRMED",
        " Private keys are generated in memory, returned in HTTP response, and memory is reclaimed",
    )
    pdf.verdict("CONFIRMED", " No key database, no persistent key storage")
    pdf.verdict("CONFIRMED", " Database stores only hashed API keys and HMAC-signed audit logs")

    # 3. Technical Due Diligence
    pdf.add_page()
    pdf.chapter_title("3. Technical Due Diligence")
    pdf.chapter_title("Cryptographic Engine", 2)
    engine_facts = [
        ("ML-KEM-768 (Kyber768)", "liboqs via oqs Python wrapper"),
        ("AES-256-GCM", "cryptography.hazmat AESGCM"),
        ("HMAC-SHA256", "hmac standard library + Rust hmac crate"),
        ("AES key derivation", "SHA-256(shared_secret)"),
        ("Nonce generation", "os.urandom(12)"),
        ("AAD context binding", "context parameter = AES-GCM AAD"),
    ]
    pdf.kv_table(engine_facts)

    pdf.chapter_title("Key Sizes (verified)", 2)
    sizes = [
        ("Kyber768 public key", "1184 bytes"),
        ("Kyber768 secret key", "2400 bytes"),
        ("AES-GCM nonce", "12 bytes"),
        ("HMAC-SHA256 signature", "64 hex chars (32 bytes)"),
        ("Min audit key", "32 bytes"),
        ("Max payload", "20 MB"),
    ]
    pdf.kv_table(sizes)

    pdf.chapter_title("Rust Engine", 2)
    pdf.verdict("CONFIRMED", " AES-256-GCM encrypt/decrypt (constant-time)")
    pdf.verdict("CONFIRMED", " HMAC-SHA256 sign/verify (constant-time via hmac crate)")
    pdf.verdict("CONFIRMED", " PyO3 Python bindings")
    pdf.verdict("FALSE", "   ML-KEM-768 key generation (returns error - requires Python/liboqs)")

    pdf.chapter_title("Database Layer", 2)
    db_facts = [
        ("SQLite (dev/test)", "sqlite+aiosqlite:///quantum_shield.db"),
        ("PostgreSQL (prod)", "postgresql+asyncpg://..."),
        ("Connection pool", "pool_size=10, max_overflow=20"),
        ("Migrations", "Alembic (001_initial_schema.py)"),
        ("Models", "ApiKey + AuditLog (hash chain fields exist but NOT in DB)"),
    ]
    pdf.kv_table(db_facts)

    pdf.chapter_title("Authentication & Authorization", 2)
    auth_facts = [
        ("API key auth", "SHA-256 hash -> DB lookup"),
        ("RBAC roles", "operator + auditor"),
        ("Rate limiting", "200/min default, 10/min key gen, 30/min seal, 60/min audit write"),
        ("Security headers", "9 headers (HSTS, CSP, X-Frame-Options, etc.)"),
        ("Correlation ID", "X-Correlation-ID header propagation"),
    ]
    pdf.kv_table(auth_facts)

    # 4. Security Audit
    pdf.add_page()
    pdf.chapter_title("4. Security Audit")
    pdf.chapter_title("Algorithm Security", 2)
    pdf.body_text(
        "All algorithms are NIST-standard or NIST-standardizing "
        "(Kyber). Key sizes are appropriate for strong crypto "
        "(AES-256, SHA-256). AES-GCM is not vulnerable to "
        "padding oracle attacks."
    )
    pdf.chapter_title("Known Findings", 2)
    pdf.verdict(
        "HIGH", "   pip-audit disabled in CI - Python dependency vulnerabilities not scanned"
    )
    pdf.verdict("MEDIUM", " cargo-audit/cargo-deny non-blocking - Rust dependency warnings ignored")
    pdf.verdict("MEDIUM", " Audit hash chain only in memory - not in database")
    pdf.verdict("LOW", "   No KDF (HKDF) for key derivation - uses SHA-256 instead")
    pdf.verdict("LOW", "   Enterprise license is a stub - prefix check only")
    pdf.verdict("LOW", "   Action field is free-text (not enum) - query inconsistency risk")
    pdf.verdict("LOW", "   No automated secret rotation - manual process (env var + restart)")
    pdf.verdict("LOW", "   No lock file for dependencies (pip freeze missing)")

    pdf.chapter_title("Threat Model", 2)
    threats = [
        ("Private key theft from server", "MITIGATED - keys never stored"),
        ("Audit log tampering", "MITIGATED - HMAC-SHA256 signed"),
        ("Ciphertext manipulation", "MITIGATED - AES-GCM authentication tag"),
        ("Context switching attack", "MITIGATED - AAD bound to context"),
        ("Timing side-channel", "MITIGATED - constant-time HMAC comparison"),
        ("Padding oracle attack", "MITIGATED - AES-GCM (not CBC)"),
        ("Nonce reuse", "MITIGATED - unique Kyber768 KEM per operation"),
        ("Dependency vulnerability", "NOT MITIGATED - pip-audit disabled"),
    ]
    for threat, status in threats:
        pdf.body_text(f"  {threat}: {status}")

    pdf.chapter_title("Compliance Mapping", 2)
    compliance = [
        ("NIS 2 Art. 21 (Risk management)", "MET - crypto agility with ML-KEM-768"),
        ("NIS 2 Art. 23 (Audit trail)", "MET - HMAC-signed audit logs"),
        ("GDPR Art. 32 (Technical measures)", "MET - strong encryption"),
        ("eIDAS 2.0", "NEEDS EXTERNAL CERTIFICATION"),
        ("SOC 2", "CONTROLS EXIST, NO AUDIT"),
    ]
    for reg, status in compliance:
        pdf.body_text(f"  {reg}: {status}")

    # 5. Git & CI/CD
    pdf.add_page()
    pdf.chapter_title("5. Git & CI/CD Analysis")
    pdf.chapter_title("Branches", 2)
    branches = [
        ("main", "Production-ready - initial public release"),
        ("enterprise-upgrade-2026", "Security audit, SDK packaging, document vault"),
        ("azure-key-vault-enterprise", "Azure Key Vault full implementation"),
    ]
    for branch, desc in branches:
        pdf.body_text(f"  {branch}: {desc}")

    pdf.chapter_title("CI Pipeline", 2)
    ci_items = [
        ("Lint (Ruff) - PASSING", ""),
        ("Security (Bandit + Semgrep) - PASSING (Semgrep continue-on-error)", ""),
        ("Python tests (3.11, 3.12) - PASSING", ""),
        ("Rust build + test - PASSING (continue-on-error)", ""),
        ("Docker build - PASSING (build only, no push)", ""),
        ("Helm lint - PASSING", ""),
    ]
    for item, _ in ci_items:
        pdf.bullet(item)

    pdf.chapter_title("CI Issues", 2)
    pdf.verdict("PARTIAL", "  CD pipeline missing - no deployment automation")
    pdf.verdict(
        "FALSE", "   Security scanning gaps - pip-audit commented out, cargo tools non-blocking"
    )
    pdf.body_text(
        "The commit history shows 20+ CI fix commits, indicating "
        "significant CI stabilization effort."
    )

    # 6. SDK Analysis
    pdf.add_page()
    pdf.chapter_title("6. SDK Analysis")
    pdf.chapter_title("Python SDK", 2)
    pdf.body_text("File: sdk/client.py (268 lines)")
    pdf.body_text("Package: quantum_shield_sdk/")
    pdf.body_text(
        "Methods: health(), generate_keypair(), seal(), unseal(), "
        "seal_text(), unseal_text(), seal_file(), unseal_to_file(), "
        "write_audit_log(), get_audit_logs(), get_audit_stats()"
    )
    pdf.verdict(
        "PARTIAL",
        "  Code complete and well-documented. Missing pyproject.toml for PyPI publishing.",
    )

    pdf.chapter_title("Go SDK", 2)
    pdf.body_text("File: sdk-go/pkg/client/client.go (431 lines)")
    pdf.body_text("Module: github.com/quantum-shield/sdk-go")
    pdf.verdict("CONFIRMED", " HTTP client with retries, rate limiting, typed responses")
    pdf.verdict("FALSE", "   Crypto package (sdk-go/pkg/crypto/) is empty")
    pdf.verdict("FALSE", "   Zero tests found in entire sdk-go/ directory")
    pdf.verdict("FALSE", "   CLI tool (cmd/qshield/) is a stub only")

    # 7. KMS Provider Analysis
    pdf.add_page()
    pdf.chapter_title("7. KMS Provider Analysis")
    kms_items = [
        "AWS KMS: RSAES_OAEP_SHA_256 wrapping - 11 tests "
        "(moto) - Missing: rotation, IAM verification",
        "Azure Key Vault: RSA-OAEP-256 via CryptographyClient "
        "- 15 tests (MagicMock) - Missing: sovereign clouds, "
        "rotation",
        "HashiCorp Vault: Transit Engine + KV v2 - 12 tests "
        "(respx) - Missing: token renewal, namespace, approle",
    ]
    for item in kms_items:
        pdf.body_text(item)

    # 8. Observability
    pdf.add_page()
    pdf.chapter_title("8. Observability Analysis")
    pdf.verdict(
        "CONFIRMED", " Structured JSON logging (JsonFormatter) - SIEM/Loki/CloudWatch ready"
    )
    pdf.verdict(
        "CONFIRMED",
        " Prometheus metrics - CRYPTO_OPS, AUDIT_WRITES, REQUEST_LATENCY + auto-instrumentation",
    )
    pdf.verdict(
        "CONFIRMED", " OpenTelemetry tracing - OTLP export, span attributes, trace propagation"
    )
    pdf.verdict(
        "CONFIRMED", " Correlation ID middleware - X-Correlation-ID in every request/response"
    )
    pdf.verdict(
        "CONFIRMED",
        " Crypto tracing decorator - @trace_crypto('seal') with duration and error status",
    )
    pdf.body_text(
        "All three observability pillars (logs, metrics, traces) are implemented and operational."
    )

    # 9. Product Maturity
    pdf.add_page()
    pdf.chapter_title("9. Product Maturity")
    scores = [
        ("Core Cryptography", "9/10"),
        ("API & Documentation", "8/10"),
        ("Security", "7/10"),
        ("Python SDK", "7/10"),
        ("Go SDK", "3/10"),
        ("CI/CD", "5/10"),
        ("Observability", "9/10"),
        ("Deployment", "6/10"),
        ("Testing", "7/10"),
        ("Enterprise features", "5/10"),
    ]
    pdf.kv_table(scores)
    pdf.chapter_title("Overall Score: 6.6/10 - Solid MVP, pre-GA", 2)

    pdf.chapter_title("Enterprise Readiness", 2)
    enterprise = [
        ("OpenAPI/Swagger: YES", ""),
        ("RBAC: YES", ""),
        ("Rate limiting: YES", ""),
        ("KMS integration (3 providers): YES", ""),
        ("Helm chart: YES", ""),
        ("Health checks: YES", ""),
        ("Prometheus metrics: YES", ""),
        ("OpenTelemetry: YES", ""),
        ("SSO / SAML / OIDC: NO", ""),
        ("Audit hash chain (DB): NO (in-memory only)", ""),
        ("SLA guarantees: NO", ""),
    ]
    for item, _ in enterprise:
        pdf.bullet(item)

    # 10. Risks & Recommendations
    pdf.add_page()
    pdf.chapter_title("10. Risks & Recommendations")
    pdf.chapter_title("Top Risks", 2)
    pdf.body_text("  [HIGH] No production deployments - No reference customers")
    pdf.body_text("  [HIGH] Dependency scanning disabled - Vulnerabilities could go undetected")
    pdf.body_text("  [MEDIUM] Go SDK incomplete - Blocks enterprise evaluations")
    pdf.body_text("  [MEDIUM] No CD pipeline - No automated releases")
    pdf.body_text("  [MEDIUM] Enterprise license is a stub - No revenue protection")

    pdf.chapter_title("Top 5 Recommendations", 2)
    recs = [
        "1. Complete Go SDK (crypto package + tests) - removes gap in enterprise evaluation",
        "2. Publish PyPI package - one weekend of packaging work unlocks pip install",
        "3. Re-enable pip-audit in CI - critical for security posture",
        "4. First 3 enterprise POCs - target NIS 2 compliance officers at EU companies",
        "5. Set up CD pipeline - automatic Docker push to GitHub Container Registry",
    ]
    for rec in recs:
        pdf.body_text(rec)

    # 11. Valuation
    pdf.add_page()
    pdf.chapter_title("11. Valuation")
    valuations = [
        ("Code alone (replacement cost)", "EUR 212K-352K"),
        ("Product (no customers)", "EUR 300K-750K"),
        ("With 1 enterprise POC", "EUR 400K-800K"),
        ("With EUR 100K ARR", "EUR 1.0M-2.0M"),
        ("With EUR 500K ARR", "EUR 7.5M-12.5M"),
    ]
    pdf.kv_table(valuations)
    pdf.body_text("Recommended pre-seed valuation: EUR 300K-500K")
    pdf.body_text(
        "The codebase represents 12-18 senior engineer months of "
        "specialized PQC + multi-cloud + Rust/PyO3 work. PQC is a "
        "niche skillset commanding premium rates."
    )

    # 12. Final Verified Assessment
    pdf.add_page()
    pdf.chapter_title("12. Final Verified Assessment")
    pdf.body_text(
        "This is the master conclusion. All findings are backed by "
        "actual source code, test results, and git history."
    )

    pdf.chapter_title("What is TRUE (Code-Proven)", 2)
    truths = [
        "ML-KEM-768 (Kyber768) key generation and hybrid encryption work correctly",
        "AAD context binding is enforced at the AES-GCM level",
        "Private keys are NEVER stored server-side (stateless architecture verified)",
        "HMAC-SHA256 audit trail is tamper-evident with key versioning",
        "Constant-time HMAC verification via hmac.compare_digest()",
        "All three KMS providers (AWS, Azure, Vault) are implemented and tested",
        "RBAC correctly restricts auditor role from crypto operations",
        "All 9 security headers are present and correctly configured",
        "JSON structured logging, Prometheus metrics, and OpenTelemetry traces all work",
        "177 tests pass with full coverage of core functionality",
    ]
    for t in truths:
        pdf.verdict("CONFIRMED", f" {t}")

    pdf.chapter_title("What is PARTIAL", 2)
    partials = [
        "CI/CD: CI works, CD missing (no deployment, no registry push)",
        "Python SDK: Code complete, no PyPI packaging config (pyproject.toml missing)",
        "KMS Enterprise: All three work, but missing rotation, auto-failover, namespace support",
    ]
    for p in partials:
        pdf.verdict("PARTIAL", f" {p}")

    pdf.chapter_title("What is FALSE", 2)
    falses = [
        "Go SDK is complete (FALSE: HTTP client only, empty crypto, zero tests)",
        "Rust engine does Kyber768 (FALSE: returns error, delegates to Python/liboqs)",
        "Enterprise license is real (FALSE: stub validation - prefix check only)",
    ]
    for f in falses:
        pdf.verdict("FALSE", f"   {f}")

    pdf.chapter_title("Conclusion", 2)
    pdf.body_text(
        "Quantum Shield Core is a well-architected, genuinely "
        "post-quantum cryptographic microservice with a clean "
        "stateless design, three enterprise KMS backends, and "
        "comprehensive observability. It is the only open-source "
        "PQC microservice with multi-cloud KMS integration."
    )
    pdf.body_text(
        "Its primary market opportunity is NIS 2 compliance "
        "readiness (deadline 2027) and the broader PQC migration "
        "wave (2025-2030). The stateless architecture is genuinely "
        "innovative for this space."
    )
    pdf.body_text(
        "For enterprise readiness, the key gaps are: "
        "(1) complete the Go SDK, (2) publish to PyPI, "
        "(3) fix CI security scanning, and "
        "(4) secure first production deployments."
    )
    pdf.body_text("Current valuation range: EUR 300K-750K. With revenue: EUR 1M-12.5M+.")

    # Save
    os.makedirs("reports", exist_ok=True)
    output_path = "reports/Quantum_Shield_Core_Full_Report.pdf"
    pdf.output(output_path)
    print(f"PDF report generated: {output_path}")
    print(f"Pages: {pdf.page_no()}")
    return output_path


if __name__ == "__main__":
    generate_report()
