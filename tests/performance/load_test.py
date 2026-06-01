"""
tests/performance/load_test.py — Load test for Quantum Shield Core.

Usage:
    pip install locust
    locust -f tests/performance/load_test.py --host=http://localhost:8000

Or in headless mode:
    locust -f tests/performance/load_test.py --host=http://localhost:8000 \\
           --headless --users 10 --spawn-rate 1 --run-time 30s
"""

import base64
import os

from locust import HttpUser, between, task


class QuantumShieldUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.api_key = os.environ.get("LOCUST_API_KEY", "test-operator-key-change-me")
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        # Generate a key pair once for seal/unseal tasks
        with self.client.post(
            "/api/v1/keys/generate", headers=self.headers, catch_response=True
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                self.public_key_b64 = data["public_key_b64"]
                self.private_key_b64 = data["private_key_b64"]
            else:
                self.public_key_b64 = None
                self.private_key_b64 = None

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def generate_keypair(self):
        self.client.post("/api/v1/keys/generate", headers=self.headers)

    @task(5)
    def seal_1kb(self):
        if not self.public_key_b64:
            return
        payload = base64.b64encode(b"x" * 1024).decode()
        self.client.post(
            "/api/v1/crypto/seal",
            headers=self.headers,
            json={
                "public_key_b64": self.public_key_b64,
                "data_b64": payload,
                "context": "load-test-doc-001",
            },
        )

    @task(5)
    def seal_1mb(self):
        if not self.public_key_b64:
            return
        payload = base64.b64encode(b"x" * (1024 * 1024)).decode()
        self.client.post(
            "/api/v1/crypto/seal",
            headers=self.headers,
            json={
                "public_key_b64": self.public_key_b64,
                "data_b64": payload,
                "context": "load-test-large-doc-001",
            },
        )

    @task(2)
    def write_audit_log(self):
        self.client.post(
            "/api/v1/audit/log",
            headers=self.headers,
            json={
                "action": "LOAD_TEST",
                "target": "load-test-target",
                "user": "locust",
            },
        )

    @task(1)
    def read_audit_logs(self):
        self.client.get("/api/v1/audit/logs", headers=self.headers)
