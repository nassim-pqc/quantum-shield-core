# PyPI Release Guide — Quantum Shield Core

## Pré-requis

```bash
pip install build twine
```

## Étapes

### 1. Vérifier le packaging

```bash
cd sdk
python -m build
twine check dist/*
```

### 2. Métadonnées (sdk/pyproject.toml à créer)

```toml
[build-system]
requires = ["setuptools>=64", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "quantum-shield-sdk"
version = "1.0.0"
description = "Python SDK for Quantum Shield Core — post-quantum cryptography microservice"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27.0",
]

[project.urls]
Homepage = "https://github.com/quantum-shield/core"
Documentation = "https://github.com/quantum-shield/core/tree/main/sdk"
Repository = "https://github.com/quantum-shield/core"
```

### 3. Publication

```bash
# Test PyPI d'abord
twine upload --repository testpypi dist/*

# PyPI production
twine upload dist/*
```

### 4. Vérification

```bash
pip install quantum-shield-sdk --index-url https://test.pypi.org/simple/
python -c "from quantum_shield_sdk.client import QuantumShieldClient; print('OK')"
```

## Note

Rien n'est publié automatiquement. Cette guide est un pré-requis pour la publication future.