#!/usr/bin/env python3
"""
Quantum Shield Core — Automated Performance Benchmark Suite

Non-destructive benchmark that measures crypto engine performance without
requiring any external services (AWS, Azure, Vault, PostgreSQL).

Measures:
  - Key generation latency (p50, p95, p99)
  - Seal/encrypt latency per payload size
  - Unseal/decrypt latency per payload size
  - Audit write latency (HMAC signing)
  - Health check latency (DB ping)
  - Throughput (MB/s)
  - Error count
  - Total test duration

Output:
  - JSON (machine-readable)
  - Markdown (human-readable, optional)

Usage:
  python scripts/run_performance_benchmarks.py
  python scripts/run_performance_benchmarks.py --iterations 50
  python scripts/run_performance_benchmarks.py --output results.json
  python scripts/run_performance_benchmarks.py --markdown results.md
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import platform
import resource
import statistics
import sys
import time
from datetime import UTC, datetime

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_engine import LocalEnvKMS, SecurityEngine

AUDIT_KEY = os.environ.get("AUDIT_KEY", "benchmark-audit-key-minimum-32-bytes-long!").encode()

PAYLOAD_SIZES = [
    (1024, "1 KB"),
    (64 * 1024, "64 KB"),
    (1024 * 1024, "1 MB"),
    (10 * 1024 * 1024, "10 MB"),
]


def _percentile(data: list[float], p: float) -> float:
    """Calculate the p-th percentile of a sorted list."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    if f == c:
        return sorted_data[f]
    return sorted_data[f] + (sorted_data[c] - sorted_data[f]) * (k - f)


def _rss_mb() -> float:
    """Get current RSS in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if sys.platform == "darwin":
        return usage.ru_maxrss / (1024 * 1024)
    return usage.ru_maxrss / 1024


def _bench_keygen(engine: SecurityEngine, iterations: int) -> dict:
    """Benchmark ML-KEM-768 key generation."""
    times: list[float] = []
    errors = 0
    for _ in range(iterations):
        try:
            t0 = time.perf_counter()
            engine.generate_keypair()
            times.append(time.perf_counter() - t0)
        except Exception:
            errors += 1
    return _build_stats(times, errors)


def _bench_seal(engine: SecurityEngine, pub_key: bytes, data: bytes, iterations: int) -> dict:
    """Benchmark hybrid seal (encrypt) operation."""
    times: list[float] = []
    errors = 0
    for _ in range(iterations):
        try:
            t0 = time.perf_counter()
            engine.encrypt_hybrid(pub_key, data, b"benchmark-context")
            times.append(time.perf_counter() - t0)
        except Exception:
            errors += 1
    return _build_stats(times, errors)


def _bench_unseal(
    engine: SecurityEngine,
    pub_key: bytes,
    priv_key: bytes,
    data: bytes,
    iterations: int,
) -> dict:
    """Benchmark hybrid unseal (decrypt) operation."""
    # Pre-seal one payload for unseal benchmark
    sealed = engine.encrypt_hybrid(pub_key, data, b"benchmark-context")
    times: list[float] = []
    errors = 0
    for _ in range(iterations):
        try:
            t0 = time.perf_counter()
            engine.decrypt_hybrid(
                priv_key,
                sealed["ciphertext_pqc"],
                sealed["nonce"],
                sealed["encrypted_data"],
                b"benchmark-context",
            )
            times.append(time.perf_counter() - t0)
        except Exception:
            errors += 1
    return _build_stats(times, errors)


def _bench_audit_write(engine: SecurityEngine, iterations: int) -> dict:
    """Benchmark HMAC-signed audit log generation."""
    times: list[float] = []
    errors = 0
    for i in range(iterations):
        try:
            t0 = time.perf_counter()
            engine.generate_signed_log("BENCHMARK", f"target-{i}", "bench-user")
            times.append(time.perf_counter() - t0)
        except Exception:
            errors += 1
    return _build_stats(times, errors)


def _bench_audit_verify(engine: SecurityEngine, iterations: int) -> dict:
    """Benchmark HMAC audit log verification."""
    # Pre-generate logs to verify
    logs = []
    for i in range(iterations):
        signed = engine.generate_signed_log("VERIFY_BENCH", f"target-{i}", "bench-user")
        logs.append((json.dumps(signed["log"], sort_keys=True), signed["signature"]))

    times: list[float] = []
    errors = 0
    for log_json, sig in logs:
        try:
            t0 = time.perf_counter()
            engine.verify_log(log_json, sig)
            times.append(time.perf_counter() - t0)
        except Exception:
            errors += 1
    return _build_stats(times, errors)


def _bench_hash(iterations: int) -> dict:
    """Benchmark SHA-256 hashing (baseline comparison)."""
    data = os.urandom(1024)
    times: list[float] = []
    errors = 0
    for _ in range(iterations):
        try:
            t0 = time.perf_counter()
            hashlib.sha256(data).digest()
            times.append(time.perf_counter() - t0)
        except Exception:
            errors += 1
    return _build_stats(times, errors)


def _bench_hmac_sign(engine: SecurityEngine, iterations: int) -> dict:
    """Benchmark raw HMAC-SHA256 signing."""
    active_key = engine.kms.get_audit_key(engine.active_key_version)
    if active_key is None:
        return _build_stats([], iterations)
    data = os.urandom(1024)
    times: list[float] = []
    errors = 0
    for _ in range(iterations):
        try:
            t0 = time.perf_counter()
            hmac.new(active_key, data, hashlib.sha256).hexdigest()
            times.append(time.perf_counter() - t0)
        except Exception:
            errors += 1
    return _build_stats(times, errors)


def _build_stats(times: list[float], errors: int) -> dict:
    """Build statistics dict from a list of timing measurements."""
    if not times:
        return {
            "iterations": errors,
            "errors": errors,
            "mean_ms": 0.0,
            "median_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
            "stdev_ms": 0.0,
            "ops_per_sec": 0.0,
        }
    ms_times = [t * 1000 for t in times]
    return {
        "iterations": len(times),
        "errors": errors,
        "mean_ms": round(statistics.mean(ms_times), 3),
        "median_ms": round(statistics.median(ms_times), 3),
        "p50_ms": round(_percentile(ms_times, 50), 3),
        "p95_ms": round(_percentile(ms_times, 95), 3),
        "p99_ms": round(_percentile(ms_times, 99), 3),
        "min_ms": round(min(ms_times), 3),
        "max_ms": round(max(ms_times), 3),
        "stdev_ms": round(statistics.stdev(ms_times), 3) if len(ms_times) > 1 else 0.0,
        "ops_per_sec": round(1.0 / statistics.mean(times), 1) if times else 0.0,
    }


def run_benchmarks(iterations: int) -> dict:
    """Run the full benchmark suite and return structured results."""
    engine = SecurityEngine(LocalEnvKMS({"v1": AUDIT_KEY}), active_key_version="v1")
    pub_key, priv_key = engine.generate_keypair()

    mem_before = _rss_mb()
    start_time = time.perf_counter()

    # Core crypto benchmarks
    keygen = _bench_keygen(engine, iterations)
    audit_write = _bench_audit_write(engine, iterations)
    audit_verify = _bench_audit_verify(engine, iterations)
    hash_bench = _bench_hash(iterations)
    hmac_bench = _bench_hmac_sign(engine, iterations)

    # Per-payload seal/unseal
    seal_results = {}
    unseal_results = {}
    for size, label in PAYLOAD_SIZES:
        data = os.urandom(size)
        seal_results[label] = _bench_seal(engine, pub_key, data, iterations)
        unseal_results[label] = _bench_unseal(engine, pub_key, priv_key, data, iterations)

    mem_after = _rss_mb()
    total_duration = time.perf_counter() - start_time

    return {
        "metadata": {
            "tool": "quantum-shield-core/run_performance_benchmarks.py",
            "timestamp": datetime.now(UTC).isoformat(),
            "host": f"{platform.system()} {platform.machine()}",
            "python_version": platform.python_version(),
            "algorithm": "ML-KEM-768 (Kyber768) + AES-256-GCM",
            "iterations": iterations,
            "payload_sizes": {label: size for size, label in PAYLOAD_SIZES},
            "total_duration_seconds": round(total_duration, 2),
            "memory_rss_mb_before": round(mem_before, 2),
            "memory_rss_mb_after": round(mem_after, 2),
            "memory_rss_mb_delta": round(max(0.0, mem_after - mem_before), 2),
        },
        "results": {
            "key_generation": keygen,
            "seal": seal_results,
            "unseal": unseal_results,
            "audit_write": audit_write,
            "audit_verify": audit_verify,
            "sha256_hash": hash_bench,
            "hmac_sha256_sign": hmac_bench,
        },
    }


def write_json(results: dict, path: str) -> None:
    """Write machine-readable JSON results."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"  JSON report: {path}")


def write_markdown(results: dict, path: str) -> None:
    """Write human-readable Markdown report."""
    meta = results["metadata"]
    res = results["results"]

    lines = [
        "# Quantum Shield Core — Performance Benchmark Report",
        "",
        f"**Generated:** {meta['timestamp']}  ",
        f"**Host:** {meta['host']} — Python {meta['python_version']}  ",
        f"**Algorithm:** {meta['algorithm']}  ",
        f"**Iterations:** {meta['iterations']}  ",
        f"**Duration:** {meta['total_duration_seconds']}s  ",
        f"**Memory RSS:** {meta['memory_rss_mb_before']}MB → "
        f"{meta['memory_rss_mb_after']}MB (Δ{meta['memory_rss_mb_delta']}MB)  ",
        "",
        "## Summary Table",
        "",
        "| Operation | Mean (ms) | P50 (ms) | P95 (ms) | P99 (ms) | Ops/sec | Errors |",
        "|-----------|-----------|----------|----------|----------|---------|--------|",
    ]

    def _row(name: str, stats: dict) -> str:
        return (
            f"| {name} | {stats['mean_ms']:.3f} | {stats['p50_ms']:.3f} | "
            f"{stats['p95_ms']:.3f} | {stats['p99_ms']:.3f} | "
            f"{stats['ops_per_sec']:.1f} | {stats['errors']} |"
        )

    lines.append(_row("Key Generation", res["key_generation"]))
    for label, stats in res["seal"].items():
        lines.append(_row(f"Seal ({label})", stats))
    for label, stats in res["unseal"].items():
        lines.append(_row(f"Unseal ({label})", stats))
    lines.append(_row("Audit Write", res["audit_write"]))
    lines.append(_row("Audit Verify", res["audit_verify"]))
    lines.append(_row("SHA-256 Hash", res["sha256_hash"]))
    lines.append(_row("HMAC-SHA256 Sign", res["hmac_sha256_sign"]))

    lines.extend(
        [
            "",
            "## Throughput (Seal Path)",
            "",
            "| Payload | Throughput (MB/s) |",
            "|---------|-------------------|",
        ]
    )
    for label, stats in res["seal"].items():
        size_bytes = meta["payload_sizes"].get(label, 0)
        if stats["mean_ms"] > 0 and size_bytes > 0:
            throughput = (size_bytes / (stats["mean_ms"] / 1000)) / (1024 * 1024)
            lines.append(f"| {label} | {throughput:.2f} |")
        else:
            lines.append(f"| {label} | N/A |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- All benchmarks run in-process (no HTTP/network overhead)",
            "- Key generation uses ML-KEM-768 via liboqs",
            "- Seal/unseal uses hybrid ML-KEM-768 + AES-256-GCM",
            "- Audit operations use HMAC-SHA256 signing",
            "- No external services required (local mode only)",
            "- Results reflect host hardware and liboqs build configuration",
            "",
            "## Raw JSON",
            "",
            "See the companion `.json` file for machine-readable results.",
            "",
        ]
    )

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Markdown report: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantum Shield Core — Automated Performance Benchmarks"
    )
    parser.add_argument(
        "--iterations", type=int, default=30, help="Iterations per benchmark (default: 30)"
    )
    parser.add_argument(
        "--output",
        default="benchmarks/performance/results.json",
        help="JSON output path",
    )
    parser.add_argument(
        "--markdown",
        default=None,
        help="Markdown output path (optional)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Quantum Shield Core — Performance Benchmark Suite")
    print("=" * 60)
    print(f"  Iterations: {args.iterations}")
    print()

    results = run_benchmarks(args.iterations)

    # Print summary
    res = results["results"]
    print("  Key Generation:")
    kg = res["key_generation"]
    print(
        f"    Mean: {kg['mean_ms']:.2f}ms  P95: {kg['p95_ms']:.2f}ms  "
        f"P99: {kg['p99_ms']:.2f}ms  Ops/s: {kg['ops_per_sec']:.1f}"
    )

    for label, stats in res["seal"].items():
        print(f"  Seal ({label}):")
        print(
            f"    Mean: {stats['mean_ms']:.2f}ms  "
            f"P95: {stats['p95_ms']:.2f}ms  "
            f"P99: {stats['p99_ms']:.2f}ms  "
            f"Ops/s: {stats['ops_per_sec']:.1f}"
        )

    for label, stats in res["unseal"].items():
        print(f"  Unseal ({label}):")
        print(
            f"    Mean: {stats['mean_ms']:.2f}ms  "
            f"P95: {stats['p95_ms']:.2f}ms  "
            f"P99: {stats['p99_ms']:.2f}ms  "
            f"Ops/s: {stats['ops_per_sec']:.1f}"
        )

    print("  Audit Write:")
    aw = res["audit_write"]
    print(
        f"    Mean: {aw['mean_ms']:.2f}ms  P95: {aw['p95_ms']:.2f}ms  "
        f"P99: {aw['p99_ms']:.2f}ms  Ops/s: {aw['ops_per_sec']:.1f}"
    )

    print("  Audit Verify:")
    av = res["audit_verify"]
    print(
        f"    Mean: {av['mean_ms']:.2f}ms  "
        f"P95: {av['p95_ms']:.2f}ms  "
        f"P99: {av['p99_ms']:.2f}ms  "
        f"Ops/s: {av['ops_per_sec']:.1f}"
    )

    total_errors = (
        kg["errors"]
        + sum(s["errors"] for s in res["seal"].values())
        + sum(s["errors"] for s in res["unseal"].values())
        + aw["errors"]
        + av["errors"]
    )
    print(f"\n  Total duration: {results['metadata']['total_duration_seconds']}s")
    print(f"  Total errors: {total_errors}")
    print(f"  Memory RSS delta: {results['metadata']['memory_rss_mb_delta']}MB")
    print()

    write_json(results, args.output)
    if args.markdown:
        write_markdown(results, args.markdown)
    else:
        # Auto-generate markdown alongside JSON
        md_path = args.output.replace(".json", ".md")
        write_markdown(results, md_path)

    print("\n  Done.")


if __name__ == "__main__":
    main()
