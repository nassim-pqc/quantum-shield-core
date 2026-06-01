"""
sdk/client.py — Quantum Shield Core Python client.

Provides high-level interface for:
  - Key generation (ML-KEM-768)
  - Hybrid encryption (Seal) and decryption (Unseal)
  - Audit trail management
  - Health checks and metrics
"""

import base64
from typing import Any

import requests


class QuantumShieldError(Exception):
    """Base exception for Quantum Shield client errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class QuantumShieldClient:
    """Client for Quantum Shield Core API."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "operator-key",
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initialize Quantum Shield client.

        Parameters:
            base_url: Base URL of the Quantum Shield service
            api_key: API key for authentication (X-API-Key header)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1"
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-API-Key": api_key,
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs) -> Any:
        """Execute an HTTP request and handle errors."""
        url = f"{self.api_url}{path}"
        try:
            response = self._session.request(
                method, url, timeout=self.timeout, verify=self.verify_ssl, **kwargs
            )
        except requests.exceptions.ConnectionError as e:
            raise QuantumShieldError(
                f"Unable to reach Quantum Shield service ({self.base_url}). "
                "Verify that docker compose is running."
            ) from e
        except requests.exceptions.Timeout as e:
            raise QuantumShieldError(f"Timeout after {self.timeout}s on {url}") from e

        if not response.ok:
            detail = (
                response.json().get("detail", response.text)
                if response.content
                else response.reason
            )
            raise QuantumShieldError(
                f"API Error {response.status_code}: {detail}", status_code=response.status_code
            )
        return response.json()

    # ========================================================================
    # Health & Status
    # ========================================================================
    def health(self) -> dict:
        """
        Check service health and database connectivity.

        Returns:
            dict with status, algorithm, version, database
        """
        try:
            response = self._session.get(
                f"{self.base_url}/health", timeout=self.timeout, verify=self.verify_ssl
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise QuantumShieldError("Service unavailable") from e

    # ========================================================================
    # Key Management
    # ========================================================================
    def generate_keypair(self) -> dict[str, str]:
        """
        Generate an ML-KEM-768 (Kyber768) keypair.

        The private key is returned only once and NEVER stored server-side.
        You are responsible for secure storage.

        Returns:
            {
                "public_key_b64": str,   # Base64-encoded public key
                "private_key_b64": str   # Base64-encoded private key — KEEP SECURE
            }
        """
        return self._request("POST", "/keys/generate")

    # ========================================================================
    # Cryptography
    # ========================================================================
    def seal(
        self,
        public_key_b64: str,
        data: bytes,
        context: str,
    ) -> dict[str, str]:
        """
        Encrypt data using hybrid Kyber768 + AES-256-GCM scheme.

        The context parameter is used as Additional Authenticated Data (AAD).
        Any attempt to decrypt with a different context will fail, even with
        the correct private key. This binds the ciphertext to a business
        identifier (e.g., document ID, patient ID, contract reference).

        Parameters:
            public_key_b64: Kyber768 public key (Base64)
            data: Data to encrypt (bytes)
            context: Business identifier binding ciphertext (AAD)

        Returns:
            {
                "ciphertext_pqc_b64": str,    # Kyber768 KEM ciphertext
                "nonce_b64": str,             # AES-GCM nonce (12 bytes)
                "encrypted_data_b64": str     # Encrypted data + GCM tag
            }
        """
        return self._request(
            "POST",
            "/crypto/seal",
            json={
                "public_key_b64": public_key_b64,
                "data_b64": base64.b64encode(data).decode(),
                "context": context,
            },
        )

    def unseal(
        self,
        private_key_b64: str,
        sealed: dict[str, str],
        context: str,
    ) -> bytes:
        """
        Decrypt sealed data.

        Raises QuantumShieldError (status_code=401) if:
          - Private key does not match
          - Context differs from seal operation
          - Data has been tampered with

        Parameters:
            private_key_b64: Kyber768 private key (Base64)
            sealed: Dict returned by seal() with the 3 fields
            context: Same context used in seal operation

        Returns:
            bytes — decrypted data
        """
        result = self._request(
            "POST",
            "/crypto/unseal",
            json={
                "private_key_b64": private_key_b64,
                "ciphertext_pqc_b64": sealed["ciphertext_pqc_b64"],
                "nonce_b64": sealed["nonce_b64"],
                "encrypted_data_b64": sealed["encrypted_data_b64"],
                "context": context,
            },
        )
        return base64.b64decode(result["decrypted_data_b64"])

    def seal_text(
        self, public_key_b64: str, text: str, context: str, encoding: str = "utf-8"
    ) -> dict:
        """Convenience method: encrypt a string."""
        return self.seal(public_key_b64, text.encode(encoding), context)

    def unseal_text(
        self, private_key_b64: str, sealed: dict, context: str, encoding: str = "utf-8"
    ) -> str:
        """Convenience method: decrypt and return a string."""
        return self.unseal(private_key_b64, sealed, context).decode(encoding)

    def seal_file(self, public_key_b64: str, file_path: str, context: str) -> dict:
        """Convenience method: encrypt a file's contents."""
        with open(file_path, "rb") as f:
            return self.seal(public_key_b64, f.read(), context)

    def unseal_to_file(
        self, private_key_b64: str, sealed: dict, context: str, output_path: str
    ) -> None:
        """Convenience method: decrypt and write to a file."""
        data = self.unseal(private_key_b64, sealed, context)
        with open(output_path, "wb") as f:
            f.write(data)

    # ========================================================================
    # Audit Trail
    # ========================================================================
    def write_audit_log(self, action: str, target: str, user: str) -> dict:
        """
        Write a signed entry to the audit trail.

        Parameters:
            action: Action code (e.g., EXPORT, ARCHIVE, DELETE)
            target: Target object (e.g., report.pdf, folder-42)
            user: User ID or role

        Returns:
            dict with id, timestamp, and integrity status
        """
        return self._request(
            "POST", "/audit/log", json={"action": action, "target": target, "user": user}
        )

    def get_audit_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        action: str | None = None,
        actor: str | None = None,
    ) -> list[dict]:
        """
        Retrieve audit trail entries with integrity verification.

        Each entry contains an 'integrity' field: '🛡️ OK' or '🚨 FAIL'.

        Parameters:
            skip: Number of entries to skip
            limit: Maximum entries to return
            action: Filter by action type
            actor: Filter by actor/user

        Returns:
            List of audit log entries
        """
        params: dict = {"skip": skip, "limit": limit}
        if action:
            params["action"] = action
        if actor:
            params["actor"] = actor
        return self._request("GET", "/audit/logs", params=params)

    def get_audit_stats(self) -> dict:
        """Get audit trail statistics by action type."""
        return self._request("GET", "/audit/stats")
