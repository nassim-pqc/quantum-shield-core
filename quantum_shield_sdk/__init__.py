"""
Quantum Shield Core SDK — PyPI package wrapper.

This package re-exports everything from the `sdk` module for PyPI distribution.

Usage:
    pip install quantum-shield-sdk

    from quantum_shield_sdk import QuantumShieldClient

    client = QuantumShieldClient(base_url="http://localhost:8000", api_key="<your-key>")
"""

from sdk import (  # noqa: F401
    QuantumShieldClient,
    QuantumShieldError,
    __version__,  # noqa: F401
)

__all__ = ["QuantumShieldClient", "QuantumShieldError"]
