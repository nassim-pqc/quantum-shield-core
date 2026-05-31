# Contributing to Quantum Shield

Thank you for evaluating or extending this asset. This repository is designed for **acquisition due diligence** and **enterprise integration** — keep changes focused and maintainable.

## Development setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Build liboqs 0.14.0 locally or use Docker (recommended).

## Workflow

1. Fork / branch from `main`
2. Make focused changes — avoid unrelated refactors
3. Run quality gates:

```bash
ruff check .
black --check .
pytest
bandit -r . -x ./tests
```

4. Open a PR with:
   - Summary of change
   - Security impact (if any)
   - Test evidence

## Conventions

- **Do not** rename root modules (`main.py`, `security_engine.py`, …)
- **Do not** break existing import paths
- Pin new dependencies in `requirements.txt`
- Document API changes in `CHANGELOG.md` and OpenAPI descriptions

## Commit messages

Use imperative mood: `Add audit filter`, `Fix pool timeout`, `Pin liboqs 0.14.0`.
