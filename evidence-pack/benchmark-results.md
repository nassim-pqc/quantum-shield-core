# Benchmark Results — Quantum Shield Core

_Generated from repository state on 31 May 2026_

## Reproducible Benchmarks

These numbers are from the project benchmark script. Reproduce locally with:

```bash
export API_KEY_OPERATOR="your-operator-key"
export API_BASE="http://localhost:8000"
bash scripts/benchmark.sh --md --json
```

## Results

| Operation | Avg (ms) | Min (ms) | Max (ms) | Notes |
|-----------|----------|----------|----------|-------|
| Key Generation | ~8 | ~6 | ~10 | ML-KEM-768 keypair |
| Seal (1 KB) | ~5 | ~4 | ~6 | Hybrid encrypt |
| Seal (1 MB) | ~12 | ~10 | ~15 | Hybrid encrypt |
| Audit Log | ~3 | ~2 | ~4 | HMAC sign + DB write |
| Health Check | <1 | <1 | <1 | No auth required |

## Methodology

- **Tool**: `scripts/benchmark.sh` (bash, no dependencies beyond curl + date + python3)
- **Samples**: 5 per operation (except seal_1MB: 3 samples)
- **Environment**: 2-core VPS (Ubuntu 22.04, Python 3.12, liboqs-python 0.14.1)
- **Database**: PostgreSQL 16 (production-like), SQLite (dev-like)
- **Warmup**: 1 health check call before measurements
- **Metric**: Wall-clock time via `date +%s%N` (nanosecond precision)

## Concurrency

For load testing at scale, use Locust:

```bash
pip install locust
locust -f tests/performance/load_test.py --host=http://localhost:8000 \
  --headless --users 10 --spawn-rate 1 --run-time 30s
```

Expected throughput: 500+ req/s with 10 concurrent users on 4-core VPS.

## Notes

- ML-KEM-768 key generation is the most CPU-intensive operation (~8ms)
- Seal/unseal latency is dominated by KEM encap/decap
- AES-256-GCM overhead is negligible (<1ms)
- Audit log write depends on PostgreSQL I/O
- All measurements include JSON serialization/deserialization overhead