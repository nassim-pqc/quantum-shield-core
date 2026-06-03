# Quantum Shield Core — Performance Benchmark Report

**Generated:** 2026-06-03T20:58:08.744539+00:00  
**Host:** Darwin arm64 — Python 3.12.8  
**Algorithm:** ML-KEM-768 (Kyber768) + AES-256-GCM  
**Iterations:** 10  
**Duration:** 0.13s  
**Memory RSS:** 68.59MB → 128.33MB (Δ59.73MB)  

## Summary Table

| Operation | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Ops/sec | Errors |
|-----------|-----------|----------|----------|----------|---------|--------|
| Key Generation | 0.015 | 0.013 | 0.021 | 0.024 | 66870.8 | 0 |
| Seal (1 KB) | 0.205 | 0.046 | 0.920 | 1.465 | 4880.4 | 0 |
| Seal (64 KB) | 0.053 | 0.051 | 0.071 | 0.075 | 18805.8 | 0 |
| Seal (1 MB) | 0.366 | 0.250 | 0.743 | 0.829 | 2728.7 | 0 |
| Seal (10 MB) | 3.864 | 3.326 | 6.618 | 8.172 | 258.8 | 0 |
| Unseal (1 KB) | 0.030 | 0.027 | 0.043 | 0.048 | 32944.4 | 0 |
| Unseal (64 KB) | 0.051 | 0.046 | 0.073 | 0.075 | 19784.0 | 0 |
| Unseal (1 MB) | 0.382 | 0.383 | 0.510 | 0.538 | 2619.5 | 0 |
| Unseal (10 MB) | 3.212 | 3.002 | 3.776 | 3.851 | 311.4 | 0 |
| Audit Write | 0.055 | 0.010 | 0.253 | 0.404 | 18330.4 | 0 |
| Audit Verify | 0.004 | 0.003 | 0.009 | 0.011 | 244905.9 | 0 |
| SHA-256 Hash | 0.001 | 0.001 | 0.002 | 0.002 | 1004420.0 | 0 |
| HMAC-SHA256 Sign | 0.002 | 0.002 | 0.003 | 0.003 | 481023.6 | 0 |

## Throughput (Seal Path)

| Payload | Throughput (MB/s) |
|---------|-------------------|
| 1 KB | 4.76 |
| 64 KB | 1179.25 |
| 1 MB | 2732.24 |
| 10 MB | 2587.99 |

## Notes

- All benchmarks run in-process (no HTTP/network overhead)
- Key generation uses ML-KEM-768 via liboqs
- Seal/unseal uses hybrid ML-KEM-768 + AES-256-GCM
- Audit operations use HMAC-SHA256 signing
- No external services required (local mode only)
- Results reflect host hardware and liboqs build configuration

## Raw JSON

See the companion `.json` file for machine-readable results.
