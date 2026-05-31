# Benchmark Methodology

## Run

```bash
# Inside dev environment with liboqs built (or Docker exec)
python benchmarks/run_benchmarks.py --iterations 30
```

Output: `benchmarks/BENCHMARK_RESULTS.md` (auto-generated with tables and JSON).

## What is measured

| Metric | Description |
|--------|-------------|
| Seal avg / p95 | Kyber encapsulation + AES-GCM encrypt |
| Unseal avg | Decapsulation + AES-GCM decrypt |
| Throughput | MB/s based on seal path |
| RSS memory | Process max RSS delta per payload tier |

## Payload tiers

- **1 KB** — API/token-style payloads
- **1 MB** — typical document
- **10 MB** — stress (below 20 MB API limit)

## Reproducibility

Record host CPU model, `liboqs` version, and Python version from the generated report header when publishing results for Acquire.com or technical datasheets.

See [BENCHMARK_RESULTS.md](./BENCHMARK_RESULTS.md) after running the script.
