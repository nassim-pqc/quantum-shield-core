# Observability

| Signal | Implementation |
|--------|----------------|
| Logs | JSON stdout (`LOG_LEVEL`) |
| Correlation | `X-Correlation-ID` header |
| Metrics | `/metrics` (Instrumentator + custom counters) |
| Traces | OpenTelemetry OTLP (optional) |

## Custom Prometheus metrics

- `qshield_crypto_operations_total{operation}`
- `qshield_audit_writes_total`
- `qshield_request_duration_seconds{method,path}`

## Enable tracing

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
export OTEL_SERVICE_NAME=quantum-shield-core
```

See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the full observability flow.
