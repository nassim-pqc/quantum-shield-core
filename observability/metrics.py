"""Prometheus custom metrics (complements prometheus-fastapi-instrumentator)."""
from prometheus_client import Counter, Histogram

CRYPTO_OPS = Counter(
    "qshield_crypto_operations_total",
    "Cryptographic operations",
    ["operation"],
)
AUDIT_WRITES = Counter(
    "qshield_audit_writes_total",
    "Audit log append operations",
)
REQUEST_LATENCY = Histogram(
    "qshield_request_duration_seconds",
    "Request latency",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)
