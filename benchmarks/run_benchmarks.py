#!/usr/bin/env python3
"""
Quantum Shield Core — Crypto & resource benchmarks.

Measures latency, throughput, CPU time, and memory delta per payload size.
Writes results to benchmarks/BENCHMARK_RESULTS.md.

Usage:
  python benchmarks/run_benchmarks.py
  python benchmarks/run_benchmarks.py --iterations 30 --output benchmarks/BENCHMARK_RESULTS.md
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import sys
import time
from datetime import UTC, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_engine import LocalEnvKMS, SecurityEngine

AUDIT_KEY = os.environ.get("AUDIT_KEY", "benchmark-audit-key-minimum-32-bytes-long!").encode()

PAYLOAD_SIZES = [
    (1024, "1 KB"),
    (1024 * 1024, "1 MB"),
    (10 * 1024 * 1024, "10 MB"),
]


def _percentile(data: list[float], p: float) -> float:
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
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # macOS reports bytes; Linux reports kilobytes
    if sys.platform == "darwin":
        return usage.ru_maxrss / (1024 * 1024)
    return usage.ru_maxrss / 1024


def bench_engine(iterations: int) -> dict:
    engine = SecurityEngine(LocalEnvKMS({"v1": AUDIT_KEY}), active_key_version="v1")
    pub, priv = engine.generate_keypair()
    results: dict = {}

    for size, label in PAYLOAD_SIZES:
        data = os.urandom(size)
        seal_times: list[float] = []
        unseal_times: list[float] = []
        mem_before = _rss_mb()

        for _ in range(iterations):
            t0 = time.perf_counter()
            sealed = engine.encrypt_hybrid(pub, data, b"benchmark-context")
            seal_times.append(time.perf_counter() - t0)

            t1 = time.perf_counter()
            engine.decrypt_hybrid(
                priv,
                sealed["ciphertext_pqc"],
                sealed["nonce"],
                sealed["encrypted_data"],
                b"benchmark-context",
            )
            unseal_times.append(time.perf_counter() - t1)

        mem_after = _rss_mb()
        seal_avg = statistics.mean(seal_times)
        results[label] = {
            "payload_bytes": size,
            "iterations": iterations,
            "seal_ms_avg": seal_avg * 1000,
            "seal_ms_p95": _percentile([t * 1000 for t in seal_times], 95),
            "unseal_ms_avg": statistics.mean(unseal_times) * 1000,
            "throughput_mbps": (size / seal_avg) / (1024 * 1024) if seal_avg > 0 else 0,
            "ops_per_sec_seal": 1.0 / seal_avg if seal_avg > 0 else 0,
            "memory_rss_mb_delta": max(0.0, mem_after - mem_before),
            "memory_rss_mb_peak": mem_after,
        }

    return results


def write_report(results: dict, output_path: str, iterations: int) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Quantum Shield Core — Benchmark Results",
        "",
        f"**Generated:** {ts}  ",
        f"**Host:** {platform.system()} {platform.machine()} — Python {platform.python_version()}  ",
        "**Algorithm:** ML-KEM-768 (Kyber768) + AES-256-GCM  ",
        f"**Iterations per payload:** {iterations}  ",
        "",
        "## Summary Table",
        "",
        "| Payload | Seal avg (ms) | Seal p95 (ms) | Unseal avg (ms) | Throughput (MB/s) | Ops/sec (seal) | RSS Δ (MB) |",
        "|---------|---------------|---------------|-----------------|-------------------|----------------|------------|",
    ]
    for label, m in results.items():
        lines.append(
            f"| {label} | {m['seal_ms_avg']:.2f} | {m['seal_ms_p95']:.2f} | "
            f"{m['unseal_ms_avg']:.2f} | {m['throughput_mbps']:.2f} | "
            f"{m['ops_per_sec_seal']:.1f} | {m['memory_rss_mb_delta']:.2f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- **1 KB**: dominated by Kyber encapsulation overhead; suitable for token/session wrapping.",
            "- **1 MB**: throughput reflects AES-GCM bulk path; typical document encryption.",
            "- **10 MB**: stress test for RAM limits (API enforces 20 MB max per request).",
            "",
            "Re-run after hardware or liboqs build changes:",
            "",
            "```bash",
            "python benchmarks/run_benchmarks.py --iterations 30",
            "```",
            "",
            "## Raw JSON",
            "",
            "```json",
            json.dumps(results, indent=2),
            "```",
            "",
        ]
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_chart(results: dict, output_dir: str) -> None:
    """Generate matplotlib visualization of benchmark results."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("⊙ matplotlib not available — skipping chart generation")
        print("  Install: pip install matplotlib\n")
        return

    labels = list(results.keys())
    seal_avgs = [results[l]["seal_ms_avg"] for l in labels]
    seal_p95s = [results[l]["seal_ms_p95"] for l in labels]
    unseal_avgs = [results[l]["unseal_ms_avg"] for l in labels]
    throughput = [results[l]["throughput_mbps"] for l in labels]

    x = range(len(labels))
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Quantum Shield — Cryptographic Performance (ML-KEM-768 + AES-256-GCM)",
        fontsize=14,
        fontweight="bold",
    )

    # Seal latency
    ax1.bar([i - 0.2 for i in x], seal_avgs, 0.35, label="Mean", color="#2563eb", alpha=0.85)
    ax1.bar([i + 0.15 for i in x], seal_p95s, 0.35, label="P95", color="#93c5fd", alpha=0.85)
    ax1.set_title("Seal (Encryption) Latency", fontweight="bold")
    ax1.set_ylabel("Time (ms)")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(labels)
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    # Unseal latency
    ax2.bar(x, unseal_avgs, 0.6, color="#16a34a", alpha=0.85)
    ax2.set_title("Unseal (Decryption) Latency", fontweight="bold")
    ax2.set_ylabel("Time (ms)")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(labels)
    ax2.grid(axis="y", alpha=0.3)

    # Throughput
    ax3.bar(x, throughput, 0.6, color="#dc2626", alpha=0.85)
    ax3.set_title("Encryption Throughput", fontweight="bold")
    ax3.set_ylabel("MB/s")
    ax3.set_xticks(list(x))
    ax3.set_xticklabels(labels)
    ax3.grid(axis="y", alpha=0.3)

    # Operations per second (seal)
    ops_per_sec = [1000 / m["seal_ms_avg"] if m["seal_ms_avg"] > 0 else 0 for m in results.values()]
    ax4.bar(x, ops_per_sec, 0.6, color="#9333ea", alpha=0.85)
    ax4.set_title("Seal Operations per Second", fontweight="bold")
    ax4.set_ylabel("Ops/sec")
    ax4.set_xticks(list(x))
    ax4.set_xticklabels(labels)
    ax4.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    chart_path = os.path.join(output_dir, "benchmark_chart.png")
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(chart_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✔ Chart generated: {chart_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Quantum Shield benchmarks")
    parser.add_argument("--iterations", type=int, default=20)
    _default_out = os.path.join(os.path.dirname(__file__), "BENCHMARK_RESULTS.md")
    if not os.access(os.path.dirname(_default_out) or ".", os.W_OK):
        _default_out = "/tmp/BENCHMARK_RESULTS.md"
    parser.add_argument("--output", default=_default_out)
    args = parser.parse_args()

    print("Quantum Shield Core — Benchmark Suite")
    print(f"Iterations: {args.iterations}\n")

    results = bench_engine(args.iterations)
    for label, m in results.items():
        print(f"[{label}]")
        print(f"  Seal:   {m['seal_ms_avg']:.2f} ms (p95 {m['seal_ms_p95']:.2f} ms)")
        print(f"  Unseal: {m['unseal_ms_avg']:.2f} ms")
        print(f"  Throughput: {m['throughput_mbps']:.2f} MB/s")
        print(f"  Memory RSS peak: {m['memory_rss_mb_peak']:.1f} MB\n")

    write_report(results, args.output, args.iterations)
    print(f"✔ Report written to {args.output}")

    output_dir = os.path.dirname(args.output) or "."
    write_chart(results, output_dir)


if __name__ == "__main__":
    main()
