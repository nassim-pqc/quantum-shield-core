#!/usr/bin/env python3
"""
Quantum Shield Core — Performance Regression Comparison

Compares current benchmark results against a baseline file.
Reports improvement, regression, and percentage variation for each metric.

Usage:
  python scripts/compare_performance.py
  python scripts/compare_performance.py --baseline benchmarks/performance/baseline.json
  python scripts/compare_performance.py --current benchmarks/performance/results.json
  python scripts/compare_performance.py --threshold 15
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_json(path: str) -> dict:
    """Load a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _compare_stat(baseline_val: float, current_val: float, threshold: float) -> dict:
    """Compare a single stat."""
    if baseline_val == 0:
        return {
            "baseline": baseline_val,
            "current": current_val,
            "delta_pct": 0.0,
            "status": "baseline_zero",
        }

    delta_pct = ((current_val - baseline_val) / baseline_val) * 100

    if delta_pct < -threshold:
        status = "improved"
    elif delta_pct > threshold:
        status = "regressed"
    else:
        status = "stable"

    return {
        "baseline": round(baseline_val, 3),
        "current": round(current_val, 3),
        "delta_pct": round(delta_pct, 2),
        "status": status,
    }


def _compare_operation(baseline_op: dict, current_op: dict, threshold: float) -> dict:
    """Compare all stats for a single operation."""
    stats_to_compare = [
        "mean_ms",
        "p50_ms",
        "p95_ms",
        "p99_ms",
        "min_ms",
        "max_ms",
        "ops_per_sec",
    ]
    result = {}
    for stat in stats_to_compare:
        b_val = baseline_op.get(stat, 0)
        c_val = current_op.get(stat, 0)
        result[stat] = _compare_stat(b_val, c_val, threshold)
    return result


def compare_results(baseline: dict, current: dict, threshold: float) -> dict:
    """Compare full benchmark results and return structured comparison."""
    comparisons = {}
    b_results = baseline.get("results", {})
    c_results = current.get("results", {})

    # Compare top-level operations
    ops = [
        "key_generation",
        "audit_write",
        "audit_verify",
        "sha256_hash",
        "hmac_sha256_sign",
    ]
    for op_name in ops:
        if op_name in b_results and op_name in c_results:
            comparisons[op_name] = _compare_operation(
                b_results[op_name], c_results[op_name], threshold
            )

    # Compare seal and unseal per payload
    for group in ["seal", "unseal"]:
        if group in b_results and group in c_results:
            comparisons[group] = {}
            for payload_label in b_results[group]:
                if payload_label in c_results[group]:
                    comparisons[group][payload_label] = _compare_operation(
                        b_results[group][payload_label],
                        c_results[group][payload_label],
                        threshold,
                    )

    # Overall verdict
    has_regressed = False
    has_improved = False
    for _op_name, op_data in comparisons.items():
        if isinstance(op_data, dict) and "mean_ms" in op_data:
            if op_data["mean_ms"]["status"] == "regressed":
                has_regressed = True
            elif op_data["mean_ms"]["status"] == "improved":
                has_improved = True
        elif isinstance(op_data, dict):
            for _label, label_data in op_data.items():
                if isinstance(label_data, dict) and "mean_ms" in label_data:
                    if label_data["mean_ms"]["status"] == "regressed":
                        has_regressed = True
                    elif label_data["mean_ms"]["status"] == "improved":
                        has_improved = True

    if has_regressed:
        verdict = "REGRESSION_DETECTED"
    elif has_improved:
        verdict = "IMPROVED"
    else:
        verdict = "STABLE"

    return {
        "metadata": {
            "baseline_timestamp": baseline.get("metadata", {}).get("timestamp", "unknown"),
            "current_timestamp": current.get("metadata", {}).get("timestamp", "unknown"),
            "threshold_pct": threshold,
            "verdict": verdict,
        },
        "comparisons": comparisons,
    }


def _format_status_emoji(status: str) -> str:
    """Return an emoji for a comparison status."""
    return {
        "improved": "✅",
        "regressed": "🔴",
        "stable": "⚪",
        "baseline_zero": "❓",
    }.get(status, "?")


def write_comparison_markdown(comparison: dict, path: str) -> None:
    """Write human-readable comparison report."""
    meta = comparison["metadata"]
    comps = comparison["comparisons"]

    lines = [
        "# Quantum Shield Core — Performance Regression Report",
        "",
        f"**Baseline:** {meta['baseline_timestamp']}  ",
        f"**Current:** {meta['current_timestamp']}  ",
        f"**Threshold:** ±{meta['threshold_pct']}%  ",
        f"**Verdict:** {meta['verdict']}  ",
        "",
        "## Summary",
        "",
        "| Operation | Metric | Baseline | Current | Δ% | Status |",
        "|-----------|--------|----------|---------|-----|--------|",
    ]

    def _add_rows(op_name: str, op_data: dict, prefix: str = "") -> None:
        for stat_name in ["mean_ms", "p95_ms", "p99_ms", "ops_per_sec"]:
            if stat_name in op_data:
                s = op_data[stat_name]
                emoji = _format_status_emoji(s["status"])
                if prefix:
                    display_name = f"{prefix}/{op_name}"
                else:
                    display_name = op_name
                lines.append(
                    f"| {display_name} | {stat_name} | "
                    f"{s['baseline']} | {s['current']} | "
                    f"{s['delta_pct']:+.1f}% | {emoji} {s['status']} |"
                )

    for _op_name, op_data in comps.items():
        if isinstance(op_data, dict) and "mean_ms" in op_data:
            _add_rows(_op_name, op_data)
        elif isinstance(op_data, dict):
            for _label, _label_data in op_data.items():
                if isinstance(_label_data, dict):
                    _add_rows(_label, _label_data, prefix=_op_name)

    lines.extend(
        [
            "",
            "## Legend",
            "",
            "- ✅ **improved**: metric decreased by more than threshold",
            "- 🔴 **regressed**: metric increased by more than threshold",
            "- ⚪ **stable**: metric variation within threshold",
            "- ❓ **baseline_zero**: baseline value was zero",
            "",
            "## Notes",
            "",
            "- For latency metrics (mean, p95, p99), lower is better",
            "- For throughput metrics (ops/sec), higher is better",
            "- This comparison is non-destructive and informational only",
            "",
        ]
    )

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Comparison report: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Quantum Shield Core — Performance Regression Comparison"
    )
    parser.add_argument(
        "--baseline",
        default="benchmarks/performance/baseline.json",
        help="Path to baseline JSON file",
    )
    parser.add_argument(
        "--current",
        default="benchmarks/performance/results.json",
        help="Path to current results JSON file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Regression threshold in percentage (default: 10%%)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for comparison JSON (optional)",
    )
    parser.add_argument(
        "--markdown",
        default=None,
        help="Output path for comparison Markdown (optional)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Quantum Shield Core — Performance Regression Comparison")
    print("=" * 60)
    print()

    # Load files
    if not os.path.exists(args.baseline):
        print(f"  ERROR: Baseline file not found: {args.baseline}")
        print("  Run the benchmark first to generate a baseline:")
        print("    python scripts/run_performance_benchmarks.py")
        print(f"    cp benchmarks/performance/results.json {args.baseline}")
        sys.exit(1)

    if not os.path.exists(args.current):
        print(f"  ERROR: Current results file not found: {args.current}")
        print("  Run the benchmark first:")
        print("    python scripts/run_performance_benchmarks.py")
        sys.exit(1)

    baseline = _load_json(args.baseline)
    current = _load_json(args.current)

    comparison = compare_results(baseline, current, args.threshold)

    # Print summary
    verdict = comparison["metadata"]["verdict"]
    print(f"  Baseline: {comparison['metadata']['baseline_timestamp']}")
    print(f"  Current:  {comparison['metadata']['current_timestamp']}")
    print(f"  Threshold: ±{args.threshold}%")
    print(f"  Verdict:  {verdict}")
    print()

    # Print per-operation summary
    comps = comparison["comparisons"]
    for _op_name, op_data in comps.items():
        if isinstance(op_data, dict) and "mean_ms" in op_data:
            s = op_data["mean_ms"]
            emoji = _format_status_emoji(s["status"])
            print(
                f"  {emoji} {_op_name}: "
                f"{s['baseline']}ms → {s['current']}ms "
                f"({s['delta_pct']:+.1f}%)"
            )
        elif isinstance(op_data, dict):
            for _label, label_data in op_data.items():
                if isinstance(label_data, dict) and "mean_ms" in label_data:
                    s = label_data["mean_ms"]
                    emoji = _format_status_emoji(s["status"])
                    print(
                        f"  {emoji} {_op_name}/{_label}: "
                        f"{s['baseline']}ms → {s['current']}ms "
                        f"({s['delta_pct']:+.1f}%)"
                    )

    print()

    # Write output files
    json_path = args.output or args.current.replace(".json", "-comparison.json")
    write_comparison_markdown(
        comparison,
        args.markdown or json_path.replace(".json", ".md"),
    )

    # Write JSON
    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)
    print(f"  Comparison JSON: {json_path}")

    print("\n  Done.")


if __name__ == "__main__":
    main()
