"""
Quantum Shield Core — Python SDK

Client library for the Quantum Shield Core API.
Simplifies encryption, decryption, key generation, and audit trail access.

Usage:
    from sdk import QuantumShieldClient

    client = QuantumShieldClient(
        base_url="http://localhost:8000",
        api_key="your-operator-api-key"
    )

    keypair = client.generate_keypair()
    sealed = client.seal(keypair["public_key_b64"], b"secret data", context="my-doc")
    decrypted = client.unseal(keypair["private_key_b64"], sealed, context="my-doc")
"""
from sdk.client import QuantumShieldClient, QuantumShieldError

__version__ = "1.0.0"
__all__ = ["QuantumShieldClient", "QuantumShieldError"]
