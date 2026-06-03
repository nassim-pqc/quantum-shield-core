# Quantum Shield SDK — PyPI Release Guide

## Overview

This guide covers packaging and publishing the Python SDK (`sdk/` module) to PyPI as `quantum-shield-sdk`.

The SDK is the primary consumption path for Python developers integrating with Quantum Shield Core.

---

## Prerequisites

```bash
# Install build tools
pip install build twine

# Create PyPI account
# https://pypi.org/account/register/

# Create Test PyPI account (optional but recommended)
# https://test.pypi.org/account/register/
```

---

## Project Structure

The SDK is a lightweight wrapper around the `sdk/` module:

```
quantum-shield-core/
├── sdk/                          # Existing module (untouched)
│   ├── __init__.py
│   ├── client.py
│   ├── README.md
│   └── examples/
├── quantum_shield_sdk/           # PyPI wrapper package (NEW)
│   ├── __init__.py               # Re-exports from sdk
│   └── pyproject.toml            # Build configuration
```

The wrapper re-exports all public API:

```python
# quantum_shield_sdk/__init__.py
from sdk import QuantumShieldClient, QuantumShieldError  # noqa: F401
from sdk import __version__  # noqa: F401
```

**Note**: The `sdk/` module must be in the Python path when the wrapper is used (e.g., installed alongside the SDK or the full project).

---

## Building for PyPI

```bash
# 1. Navigate to the wrapper directory
cd quantum_shield_sdk/

# 2. Build source distribution and wheel
python -m build

# 3. Check distribution files
ls dist/
# Output: quantum-shield-sdk-1.0.0.tar.gz  quantum_shield_sdk-1.0.0-py3-none-any.whl

# 4. Verify with twine
twine check dist/*
```

---

## Publishing to Test PyPI

```bash
# Upload to test PyPI
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Install from test PyPI
pip install --index-url https://test.pypi.org/simple/ quantum-shield-sdk
```

## Publishing to Production PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# You'll be prompted for:
#   - Username: __token__
#   - Password: <your PyPI API token>
```

---

## Version Management

### Update version number

Edit `sdk/__init__.py`:
```python
__version__ = "1.0.1"  # Update this
```

Then update `quantum_shield_sdk/pyproject.toml`:
```toml
version = "1.0.1"
```

### Semantic Versioning

| Version | When |
|---------|------|
| MAJOR.x.x | Breaking API changes |
| x.MINOR.x | New features, backward compatible |
| x.x.PATCH | Bug fixes, backward compatible |

---

## Usage After Installation

```python
# After: pip install quantum-shield-sdk
from quantum_shield_sdk import QuantumShieldClient

client = QuantumShieldClient(
    base_url="http://localhost:8000",
    api_key="your-operator-api-key"
)

# Generate keys
keys = client.generate_keypair()

# Encrypt data
sealed = client.seal(
    public_key_b64=keys["public_key_b64"],
    data=b"Secret document content",
    context="document-123"
)

# Decrypt data
plaintext = client.unseal(
    private_key_b64=keys["private_key_b64"],
    sealed=sealed,
    context="document-123"
)

# Audit trail
logs = client.get_audit_logs()
stats = client.get_audit_stats()
```

---

## Automated Publishing (GitHub Actions)

Add to `.github/workflows/pypi.yml`:

```yaml
name: PyPI Release

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build twine
      - run: python -m build quantum_shield_sdk/
      - run: twine upload quantum_shield_sdk/dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```

---

## Pre-release Checklist

- [ ] Tests pass: `pytest tests/ -v`
- [ ] SDK client tested against running API
- [ ] Version numbers synced (`sdk/__init__.py` and `pyproject.toml`)
- [ ] README.md updated with latest examples
- [ ] `twine check` passes
- [ ] Test PyPI publish succeeds
- [ ] Test install from PyPI works
- [ ] All examples in `sdk/examples/` run correctly

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'sdk'` | Install quantum-shield-core or add project root to PYTHONPATH |
| `twine check` fails | Ensure description is valid RST/Markdown |
| PyPI rejects version | Version must be unique; increment before re-publishing |
| Token authentication fails | Generate new token at PyPI → Account Settings → API Tokens |