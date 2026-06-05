# Public Repo Cleanup — Audit

> Generated as part of `repo-public-cleanup` branch

## Items Identified (CTO Review Lens)

### HIGH severity — must act

| # | Item | Location | Problem | Recommendation | CTO Justification |
|---|------|----------|---------|---------------|-------------------|
| H1 | `sales-package/` | Root directory | Full buyer-facing sales material in a public repo | Move to private data room | A CTO seeing this assumes the project is for sale, not for use |
| H2 | `DOSSIER_VENTE.md` | Root (untracked) | French-language sales dossier | Move to private data room | Out of place in a technical repo |
| H3 | `FINAL_DELIVERABLE.md`, `FINAL_*` files | Root (untracked) | "Final deliverable" language — implies consulting project | Move to private data room | Makes repo look like a one-off deliverable, not a maintained project |
| H4 | `investor-kit/` | Root (untracked) | Investor-targeted material | Move to private data room | Public repo should target engineers, not investors |
| H5 | `evidence-pack/` | Root (untracked) | Duplicates `evidence/` directory content | Move to private data room | Content already exists in `evidence/`; this is a sales copy |
| H6 | `docs/INVESTOR_PACKAGE.md` | Tracked in `docs/` | Investor/valuation document in a public repo | Move to private data room | Valuation claims in public docs erode technical credibility |
| H7 | `docs/FULL_PROJECT_VALUATION.md` | Tracked in `docs/` | Explicit valuation document | Move to private data room | Same as H6 |
| H8 | `docs/FULL_COMMERCIAL_ASSESSMENT.md` | Tracked in `docs/` | Commercial assessment = sales document | Move to private data room | Belongs in data room |
| H9 | `README.md` lines 156-199 | README.md | "Enterprise Capabilities" + "Current Maturity" tables read as a sales pitch | Rewrite — shorter, more technical, less marketing | CTOs want facts, not feature brag tables |
| H10 | `README.md` links to `evidence-pack/` | README.md line 122, 134-143 | Links to a directory being removed | Fix links | Broken links = sloppy repo |
| H11 | `docs/sales/` directory | Tracked in `docs/` | Elevator pitch + objection handling = sales content | Move to private data room | Not technical documentation |

### MEDIUM severity — should act

| # | Item | Location | Problem | Recommendation | CTO Justification |
|---|------|----------|---------|---------------|-------------------|
| M1 | `evidence/PROOF_OF_USAGE_REPORT.md` | Tracked | "Proof of usage" reads more like a sales document than technical evidence | Keep but rewrite more technically | Useful content if presented as technical validation |
| M2 | `evidence/BUYER_ONE_PAGER.md` | Tracked | "Buyer" in filename = sales | Move to private data room or rename | Targets buyers, not engineers |
| M3 | `evidence/VIDEO_DEMO_SCRIPT.md` | Tracked | Video demo script = marketing material | Move to private data room | Not technical documentation |
| M4 | `evidence/SCREENSHOT_CHECKLIST.md` | Tracked | Screenshot checklist for buyer presentation | Move to private data room | Sales tooling |
| M5 | `docs/EXECUTIVE_SUMMARY.md` | Tracked | Executive summary = business document | Move to private data room or rewrite technically | Should be in data room, not public |
| M6 | `docs/FULL_TECHNICAL_DUE_DILIGENCE.md` | Tracked | Combines technical + commercial content | Keep technical parts, move commercial parts | Size (18KB) suggests overlap with other docs |
| M7 | `docs/FULL_SECURITY_AUDIT.md` | Tracked | 12KB, may overlap with other security docs | Consolidate or trim | Redundancy = AI-generated feel |
| M8 | `docs/CURRENT_STATE_REPORT.md` | Tracked | Likely overlaps with other status docs | Consolidate | Multiple status reports = generated feel |
| M9 | `docs/DEMO_USE_CASE.md` | Tracked | Demo use case = sales oriented | Keep but rewrite as technical scenario guide | Useful if framed as integration example |
| M10 | `docs/FINAL_VERIFIED_ASSESSMENT.md` | Tracked | "Final" + "Verified" = final deliverable vibe | Review and rename if kept | "Final" implies project completion, not ongoing development |

### LOW severity — nice to fix

| # | Item | Location | Problem | Recommendation | CTO Justification |
|---|------|----------|---------|---------------|-------------------|
| L1 | `docs/ENTERPRISE_QUICK_WINS_SUMMARY.md` | Tracked | "Quick wins" = consulting language | Rename or trim | Minor tone issue |
| L2 | `docs/IMPLEMENTATION_SUMMARY.md` | Tracked | May duplicate other docs | Check and consolidate if redundant | Redundancy looks AI-generated |
| L3 | `docs/ENTERPRISE_AUDIT.md` | Tracked | "Enterprise audit" — what does this add beyond other audit docs? | Check for uniqueness | Redundancy concern |
| L4 | `docs/PYPI_RELEASE_GUIDE.md` | Tracked | Useful but could be consolidated with `docs/pypi-release.md` | Consolidate | Duplicate |
| L5 | `docs/mna-review.md` | Tracked | M&A review in public docs | Move to data room | M&A content = not public |
| L6 | `README.md` badges | README.md line 3-10 | CI badge may point to private repo, test count badge is non-standard | Verify badges work | Broken badges = unmaintained look |
| L7 | Inline "enterprise-ready" phrases | README.md | "Enterprise" appears ~20 times in README | Reduce frequency | Too much enterprise = too much sales |

## Files to Remove from Git Tracking (but keep locally, backed up)

These are tracked files that need `git rm --cached`:

1. `sales-package/` (entire directory)
2. `docs/sales/` (entire directory)
3. `docs/INVESTOR_PACKAGE.md`
4. `docs/FULL_PROJECT_VALUATION.md`
5. `docs/FULL_COMMERCIAL_ASSESSMENT.md`
6. `docs/EXECUTIVE_SUMMARY.md`
7. `docs/mna-review.md`
8. `docs/FULL_TECHNICAL_DUE_DILIGENCE.md` (consider trimming)
9. `docs/FULL_SECURITY_AUDIT.md` (consider trimming)
10. `docs/CURRENT_STATE_REPORT.md` (consider trimming)
11. `docs/FINAL_VERIFIED_ASSESSMENT.md` (consider trimming/reviewing)
12. `docs/ENTERPRISE_AUDIT.md` (consider trimming)
13. `docs/IMPLEMENTATION_SUMMARY.md` (consider trimming)
14. `docs/ENTERPRISE_QUICK_WINS_SUMMARY.md` (consider trimming)
15. `evidence/BUYER_ONE_PAGER.md`
16. `evidence/VIDEO_DEMO_SCRIPT.md`
17. `evidence/SCREENSHOT_CHECKLIST.md`

## Files to Rewrite

1. `README.md` — major tone-down (Phase 4)

## Files to Create

1. `docs/PUBLIC_REPO_CLEANUP_AUDIT.md` (this file)
2. `docs/PUBLIC_DOCUMENTATION_INDEX.md` (Phase 5)
3. `docs/CODE_REVIEW_FINDINGS.md` (Phase 6)
4. `docs/PUBLIC_REPO_CLEANUP_SUMMARY.md` (Phase 10)