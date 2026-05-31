# Quantum Shield Core — Benchmark Results

**Generated:** 2026-05-28 (Docker `qshield_enclave`, liboqs 0.14.0 + liboqs-python 0.14.1)  
**Host:** Linux aarch64/x86_64 container — Python 3.11.15  
**Algorithm:** ML-KEM-768 (Kyber768) + AES-256-GCM  
**Product version:** 1.0.0  
**Iterations per payload:** 15  

## Summary Table

| Payload | Seal avg (ms) | Seal p95 (ms) | Unseal avg (ms) | Throughput (MB/s) | Ops/sec (seal) | RSS peak (MB) |
|---------|---------------|---------------|-----------------|-------------------|----------------|---------------|
| 1 KB    | 0.09          | 0.28          | 0.03            | 11.39             | 11111          | 31.7          |
| 1 MB    | 0.46          | 0.70          | 0.54            | 2185.14           | 2174           | 36.6          |
| 10 MB   | 3.57          | 6.14          | 3.55            | 2800.28           | 280            | 82.6          |

## Interpretation

- **1 KB**: Kyber encapsulation dominates; sub-millisecond seal on reference hardware.
- **1 MB / 10 MB**: AES-GCM bulk path; throughput figures are high because CPU-bound crypto completes in sub-10 ms on this host — use as **relative** comparison between releases, not absolute SLA.
- **Memory**: RSS peak scales with payload (10 MB → ~83 MB) — within the 768 MB container limit.

Re-run inside Docker:

```bash
docker compose exec quantum-shield-api \
  python benchmarks/run_benchmarks.py --iterations 20 --output /tmp/BENCHMARK_RESULTS.md
```

## Raw JSON

```json
{
  "1 KB": {
    "payload_bytes": 1024,
    "iterations": 15,
    "seal_ms_avg": 0.09,
    "seal_ms_p95": 0.28,
    "unseal_ms_avg": 0.03,
    "throughput_mbps": 11.39,
    "ops_per_sec_seal": 11111.11,
    "memory_rss_mb_peak": 31.7
  },
  "1 MB": {
    "payload_bytes": 1048576,
    "iterations": 15,
    "seal_ms_avg": 0.46,
    "seal_ms_p95": 0.7,
    "unseal_ms_avg": 0.54,
    "throughput_mbps": 2185.14,
    "ops_per_sec_seal": 2173.91,
    "memory_rss_mb_peak": 36.6
  },
  "10 MB": {
    "payload_bytes": 10485760,
    "iterations": 15,
    "seal_ms_avg": 3.57,
    "seal_ms_p95": 6.14,
    "unseal_ms_avg": 3.55,
    "throughput_mbps": 2800.28,
    "ops_per_sec_seal": 280.11,
    "memory_rss_mb_peak": 82.6
  }
}
```
