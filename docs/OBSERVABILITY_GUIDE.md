# Quantum Shield Core — Observability Guide

## Overview

Quantum Shield Core provides comprehensive observability through three pillars:

1. **Metrics** (Prometheus) — real-time monitoring of cryptographic operations
2. **Tracing** (OpenTelemetry) — distributed request tracing
3. **Logging** (Structured JSON) — SIEM-compatible audit and application logs

---

## 1. Prometheus Metrics

### Endpoint

Metrics are exposed at `/metrics` (port 8000) via `prometheus-fastapi-instrumentator`.

```bash
curl http://localhost:8000/metrics
```

### Custom Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `qshield_crypto_operations_total` | Counter | `operation` | Cryptographic operations by type |
| `qshield_audit_writes_total` | Counter | — | Audit log append operations |
| `qshield_request_duration_seconds` | Histogram | `method`, `path` | Request latency distribution |

### Operation Labels

The `qshield_crypto_operations_total` metric tracks:

| Label | Operation |
|-------|-----------|
| `key_generate` | ML-KEM-768 key pair generation |
| `seal` | Hybrid encryption |
| `unseal` | Hybrid decryption |

### Automatic FastAPI Metrics

The `prometheus-fastapi-instrumentator` automatically provides:

- `http_request_duration_seconds` — request latency by method/path/status
- `http_request_total` — total request count
- `http_request_size_bytes` — request size distribution
- `http_response_size_bytes` — response size distribution

### Example Prometheus Queries

```promql
# Crypto operations per second
rate(qshield_crypto_operations_total[5m])

# Audit write rate
rate(qshield_audit_writes_total[5m])

# P95 latency by endpoint
histogram_quantile(0.95, rate(qshield_request_duration_seconds_bucket[5m]))

# Error rate by endpoint
rate(http_request_duration_seconds_count{status=~"5.."}[5m])
```

### Grafana Dashboard

Recommended panels:

1. **Crypto Operations Rate** — line chart of `rate(qshield_crypto_operations_total[5m])` by `operation`
2. **Audit Write Rate** — single stat of `rate(qshield_audit_writes_total[5m])`
3. **Request Latency** — heatmap of `qshield_request_duration_seconds_bucket`
4. **P95 Latency by Endpoint** — bar chart of histogram_quantile
5. **Error Rate** — gauge of error percentage
6. **Health Status** — text panel showing current health

---

## 2. Structured Logging

### Format

All logs are emitted as JSON objects for SIEM ingestion (Loki, CloudWatch, ELK):

```json
{
  "timestamp": "2026-03-06 16:30:00,123",
  "level": "INFO",
  "logger": "quantum_shield",
  "message": "request_completed",
  "correlation_id": "abc-123-def",
  "method": "POST",
  "path": "/api/v1/crypto/seal",
  "duration_ms": 45.23
}
```

### Log Levels

| Level | When |
|-------|------|
| DEBUG | Detailed debugging (SQL queries via `SQL_ECHO=true`) |
| INFO | Normal operations (startup, shutdown, requests) |
| WARNING | Minor issues (unseal failures, rate limit warnings) |
| ERROR | Operation failures (crypto errors, DB connection issues) |
| CRITICAL | Startup failures (missing audit key) |

### Configuration

```bash
# Set log level
export LOG_LEVEL=INFO

# Enable SQL query logging (development only)
export SQL_ECHO=true
```

### Correlation IDs

Every request receives a `X-Correlation-ID` header:

- If the client provides one → it is propagated
- If not → a UUID is generated

This appears in both response headers and structured logs for end-to-end tracing.

---

## 3. OpenTelemetry Tracing

### Configuration

Tracing is enabled by setting the OTLP endpoint:

```bash
# Required: OTLP gRPC endpoint
export OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317

# Optional configuration
export OTEL_SERVICE_NAME=quantum-shield-core
export OTEL_EXPORTER_INSECURE=true  # default: true
```

When no endpoint is configured, tracing calls are no-ops (no performance impact).

### Automatic Instrumentation

The following are automatically instrumented:

- All HTTP requests (method, path, status, duration)
- Framework internals (via `opentelemetry-instrumentation-fastapi`)

### Custom Spans

Cryptographic operations are instrumented with custom spans:

| Span Name | Attributes | Description |
|-----------|------------|-------------|
| `crypto.seal` | `crypto.operation`, `crypto.algorithm`, `crypto.duration_ms` | Hybrid encryption |
| `crypto.unseal` | `crypto.operation`, `crypto.algorithm`, `crypto.duration_ms` | Hybrid decryption |
| `crypto.audit_sign` | `crypto.operation`, `crypto.algorithm`, `crypto.duration_ms` | Audit log signing |

### Distributed Tracing Flow

```
Client App                   Quantum Shield                Jaeger/Tempo
    │                             │                            │
    │── POST /crypto/seal ───────▶│                            │
    │   X-Correlation-ID: abc     │                            │
    │                             │── crypto.seal span ───────▶│
    │                             │── audit_sign span ────────▶│
    │◀─────────── 200 OK ────────│                            │
    │                             │                            │
    │── Query traces by           │                            │
    │   X-Correlation-ID=abc ─────┼───────────────────────────▶│
```

### Backend Options

| Backend | Endpoint | Notes |
|---------|----------|-------|
| Jaeger | `http://jaeger:4317` | gRPC, recommended for dev |
| Grafana Tempo | `http://tempo:4317` | gRPC, production-ready |
| Datadog | `http://localhost:4317` | Via OTLP ingest |
| SigNoz | `http://signoz:4317` | Open-source alternative |

---

## 4. Integration with Docker Compose

### Adding Prometheus

```yaml
# docker-compose.observability.yml
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "4317:4317"   # OTLP gRPC
      - "16686:16686"  # UI
```

### Prometheus Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'quantum-shield'
    scrape_interval: 10s
    static_configs:
      - targets: ['quantum-shield-api:8000']
```

---

## 5. Health Check Endpoint

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "algorithm": "Kyber768",
  "version": "1.0.0",
  "database": "ok (42 audit entries)"
}
```

Status values:
- `healthy` — API, database, and KMS are operational
- `degraded` — Database unavailable (API still functional but audit logs limited)

---

## 6. Monitoring Checklist

### Production Setup

- [ ] Prometheus scraping `/metrics` every 10s
- [ ] Grafana dashboard with crypto operation charts
- [ ] Alerts for:
  - Error rate > 1% over 5 minutes
  - Crypto operation rate drops to 0 (service may be down)
  - P95 latency > 2 seconds
  - Health check returns "degraded"
- [ ] Structured logs shipped to SIEM (Loki / CloudWatch / ELK)
- [ ] OpenTelemetry traces exported (Jaeger / Tempo)
- [ ] Correlation IDs in all logs for request tracing

### Development Setup

```bash
# Quick monitoring setup for development:
# Prometheus metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health

# Structured logging (JSON)
curl -s http://localhost:8000/health | jq .
```

---

## 7. Load Testing

A Locust-based load test is available:

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/performance/load_test.py \
  --host http://localhost:8000 \
  --headless -u 10 -r 2 --run-time 1m
```

Metrics to watch during load tests:
- `qshield_crypto_operations_total` rate
- `qshield_request_duration_seconds` P95
- Error rate and types
- Request throughput