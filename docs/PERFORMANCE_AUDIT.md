# Quantum Shield Core — Performance Audit

> **Date**: June 2026  
> **Scope**: Inventory of existing performance tooling, gaps, and measurable capabilities  
> **Audience**: Technical buyers, engineering teams evaluating the project

---

## 1. What Already Exists

### 1.1 Crypto-Level Benchmarks (`benchmarks/run_benchmarks.py`)

| Capability | Status |
|------------|--------|
| Seal latency (avg, p95) | ✅ Measured per payload size |
| Unseal latency (avg) | ✅ Measured per payload size |
| Throughput (MB/s) | ✅ Computed from seal path |
| Operations per second (seal) | ✅ Computed |
| Memory RSS delta | ✅ Measured via `resource.getrusage` |
| Percentile calculation | ✅ p50, p95 (custom implementation) |
| JSON output | ⚠️ Raw JSON embedded in Markdown only |
| Machine-readable JSON file | ❌ Not exported separately |
| Regression comparison | ❌ No baseline comparison |
| Health check latency | ❌ Not measured |
| Audit write latency | ❌ Not measured |
| Error rate tracking | ❌ Not measured |

**Payload tiers**: 1 KB, 1 MB, 10 MB  
**Default iterations**: 20 (configurable via `--iterations`)

### 1.2 API-Level Benchmarks (`scripts/benchmark.sh`)

| Capability | Status |
|------------|--------|
| Key generation latency | ✅ 5 samples |
| Seal 1 KB latency | ✅ 5 samples |
| Seal 1 MB latency | ✅ 3 samples |
| Audit write latency | ✅ 5 samples |
| Health check latency | ✅ 5 samples |
| JSON output (`--json`) | ✅ Writes to `docs/benchmarks/results.json` |
| Markdown output (`--md`) | ✅ Writes to `docs/benchmarks/results.md` |
| Warmup call | ✅ Before measurements |
| P50/P95/P99 | ❌ Only avg/min/max |
| Error tracking | ⚠️ Warns on non-200/201 |
| Regression comparison | ❌ No baseline comparison |

**Dependencies**: curl, date, python3 (no pip packages required)

### 1.3 Load Testing (`tests/performance/load_test.py`)

| Capability | Status |
|------------|--------|
| Locust-based load test | ✅ |
| Concurrent users | ✅ Configurable |
| Multi-endpoint testing | ✅ keygen, seal, audit, health |
| Headless mode | ✅ |
| Throughput measurement | ✅ Via Locust statistics |
| Latency percentiles | ✅ Via Locust built-in stats |
| Requires running server | ⚠️ Needs live API |

### 1.4 Prometheus Metrics (Runtime)

| Metric | Type | Labels |
|--------|------|--------|
| `qshield_crypto_operations_total` | Counter | `operation` |
| `qshield_audit_writes_total` | Counter | — |
| `qshield_request_duration_seconds` | Histogram | `method`, `path` |
| FastAPI instrumentator metrics | Auto | `method`, `handler`, `status` |

### 1.5 OpenTelemetry Tracing

- W3C trace context propagation
- OTLP gRPC exporter configured
- Per-request correlation IDs via `X-Correlation-ID`

---

## 2. What Is Missing

| Gap | Impact | Priority |
|-----|--------|----------|
| Machine-readable benchmark JSON | Cannot automate regression detection | High |
| Baseline comparison script | No regression detection | High |
| Health check latency benchmark | No availability SLA measurement | Medium |
| Audit write latency benchmark | No compliance SLA measurement | Medium |
| Error rate measurement | No reliability metric | Medium |
| P99 percentile | Insufficient tail latency visibility | Medium |
| CI-integrated benchmark | No automated performance gates | Low |
| Memory profiling | Limited resource visibility | Low |
| Docker image size tracking | No container efficiency metric | Low |

---

## 3. What Can Be Measured Without External Services

All of the following can be measured locally with no AWS/Azure/Vault:

| Metric | Tool | Command |
|--------|------|---------|
| Key generation latency | `benchmarks/run_benchmarks.py` | `python benchmarks/run_benchmarks.py` |
| Seal/unseal latency | `benchmarks/run_benchmarks.py` | Same as above |
| Throughput (MB/s) | `benchmarks/run_benchmarks.py` | Same as above |
| Memory RSS | `benchmarks/run_benchmarks.py` | Same as above |
| API endpoint latency | `scripts/benchmark.sh` | `bash scripts/benchmark.sh` |
| Load testing | Locust | `locust -f tests/performance/load_test.py` |
| Runtime metrics | Prometheus | `curl localhost:8000/metrics` |

---

## 4. What Depends on Real KMS Providers

| Metric | KMS Provider | Notes |
|--------|-------------|-------|
| KMS wrap/unwrap latency | AWS KMS | Network-dependent, varies by region |
| Vault transit latency | HashiCorp Vault | Depends on Vault cluster proximity |
| Azure Key Vault latency | Azure Key Vault | Network-dependent |
| Audit key retrieval latency | Any KMS | One-time at startup, cached |

**Recommendation**: Benchmark KMS latency separately in production-like environment. Do not include in crypto-level benchmarks.

---

## 5. Methodological Limitations

| Limitation | Explanation |
|------------|-------------|
| Single-machine results | Benchmarks reflect the host hardware, not production |
| No concurrent load in crypto benchmarks | `run_benchmarks.py` is single-threaded |
| Wall-clock time only | No CPU cycle counting (unlike `perf`) |
| No cold-start measurement | First request may be slower due to JIT, caching |
| macOS vs Linux differences | `resource.getrusage` reports differently per OS |
| liboqs version sensitivity | Performance varies with liboqs build flags |
| No network overhead in crypto benchmarks | `run_benchmarks.py` measures pure crypto, not HTTP |
| API benchmark includes HTTP overhead | `benchmark.sh` measures full request lifecycle |

---

## 6. Recommended Next Steps

1. **Add machine-readable JSON export** to `benchmarks/run_benchmarks.py`
2. **Add P99 percentile** to crypto benchmarks
3. **Add health check and audit write latency** to crypto benchmarks
4. **Create baseline comparison** for regression detection
5. **Add CI benchmark job** (non-blocking, informational only)
6. **Document Docker image size** as a container efficiency metric

---

*This audit is honest and complete. It reflects the actual state of performance tooling in the repository as of June 2026.*