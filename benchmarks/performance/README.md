# Quantum Shield Core — Performance Benchmark Suite

## Overview

This benchmark suite measures the performance of Quantum Shield Core's cryptographic operations without requiring any external services (AWS, Azure, Vault, PostgreSQL).

## What Is Measured

| Operation | Description |
|-----------|-------------|
| Key Generation | ML-KEM-768 key pair generation via liboqs |
| Seal (1 KB, 64 KB, 1 MB, 10 MB) | Hybrid encrypt: ML-KEM-768 + AES-256-GCM |
| Unseal (1 KB, 64 KB, 1 MB, 10 MB) | Hybrid decrypt: ML-KEM-768 + AES-256-GCM |
| Audit Write | HMAC-SHA256 signed audit log generation |
| Audit Verify | HMAC-SHA256 audit log verification |
| SHA-256 Hash | Baseline hash comparison |
| HMAC-SHA256 Sign | Raw HMAC signing baseline |

## Metrics Per Operation

- Mean, median, P50, P95, P99 latency (ms)
- Min, max latency (ms)
- Standard deviation (ms)
- Operations per second
- Error count

## Quick Start

```bash
# Run benchmarks (generates JSON + Markdown)
python scripts/run_performance_benchmarks.py

# Run with more iterations
python scripts/run_performance_benchmarks.py --iterations 50

# Custom output paths
python scripts/run_performance_benchmarks.py \
  --output benchmarks/performance/results.json \
  --markdown benchmarks/performance/results.md
```

## Regression Detection

```bash
# 1. Generate baseline
python scripts/run_performance_benchmarks.py \
  --output benchmarks/performance/baseline.json

# 2. Make changes, then generate new results
python scripts/run_performance_benchmarks.py \
  --output benchmarks/performance/results.json

# 3. Compare
python scripts/compare_performance.py \
  --baseline benchmarks/performance/baseline.json \
  --current benchmarks/performance/results.json \
  --threshold 10
```

## Output Files

| File | Format | Purpose |
|------|--------|---------|
| `results.json` | JSON | Machine-readable benchmark results |
| `results.md` | Markdown | Human-readable benchmark report |
| `baseline.json` | JSON | Baseline for regression comparison |
| `*-comparison.json` | JSON | Comparison results |
| `*-comparison.md` | Markdown | Human-readable comparison report |

## Limitations

- Benchmarks measure in-process crypto performance (no HTTP/network overhead)
- Results reflect the host hardware and liboqs build configuration
- No concurrent load (single-threaded benchmarks)
- For load testing, use Locust: `locust -f tests/performance/load_test.py`
- KMS provider latency is not included (requires real providers)

## Files

| File | Description |
|------|-------------|
| `__init__.py` | Package marker |
| `baseline.example.json` | Example baseline file with reference values |
| `README.md` | This file |