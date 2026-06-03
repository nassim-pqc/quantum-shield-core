# Quantum Shield Core — Performance Regression Guide

> **Purpose**: How to detect and manage performance regressions  
> **Audience**: Developers, CI/CD maintainers, technical leads

---

## Overview

Quantum Shield Core includes a performance regression detection system that compares current benchmark results against a saved baseline. This guide explains how to use it.

---

## 1. Workflow

### Step 1: Generate a Baseline

Run the benchmark suite and save the results as a baseline:

```bash
python scripts/run_performance_benchmarks.py \
  --iterations 30 \
  --output benchmarks/performance/baseline.json
```

### Step 2: Make Changes

Implement your code changes (crypto, API, etc.).

### Step 3: Run Benchmarks Again

```bash
python scripts/run_performance_benchmarks.py \
  --iterations 30 \
  --output benchmarks/performance/results.json
```

### Step 4: Compare

```bash
python scripts/compare_performance.py \
  --baseline benchmarks/performance/baseline.json \
  --current benchmarks/performance/results.json \
  --threshold 10
```

### Step 5: Review Results

The comparison script outputs:
- **JSON**: `benchmarks/performance/results-comparison.json`
- **Markdown**: `benchmarks/performance/results-comparison.md`

---

## 2. Threshold Configuration

The `--threshold` parameter (default: 10%) determines when a metric is considered regressed:

| Threshold | Sensitivity | Use Case |
|-----------|-------------|----------|
| 5% | High | Strict production environments |
| 10% | Medium | General development (default) |
| 15% | Low | Noisy environments, hardware variation |
| 20% | Very Low | CI on shared runners |

**Recommendation**: Use 10% for local development, 15-20% for CI on shared runners.

---

## 3. Verdicts

| Verdict | Meaning |
|---------|---------|
| `STABLE` | All metrics are within the threshold |
| `IMPROVED` | At least one metric improved beyond threshold, no regressions |
| `REGRESSION_DETECTED` | At least one metric regressed beyond threshold |

---

## 4. CI Integration (Optional)

The regression comparison can be added to CI as a **non-blocking informational job**:

```yaml
# .github/workflows/benchmark.yml (example — not active by default)
name: Performance Benchmarks
on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run benchmarks
        run: python scripts/run_performance_benchmarks.py --iterations 20
      - name: Compare with baseline
        run: |
          if [ -f benchmarks/performance/baseline.json ]; then
            python scripts/compare_performance.py \
              --baseline benchmarks/performance/baseline.json \
              --current benchmarks/performance/results.json \
              --threshold 15
          fi
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: benchmarks/performance/
```

**Important**: This job should NOT be a blocking gate. Performance varies between CI runners, and false positives would make the pipeline fragile.

---

## 5. Best Practices

| Practice | Reason |
|----------|--------|
| Generate baseline on same hardware | Hardware variation affects results |
| Use consistent iteration count | More iterations = more stable results |
| Run benchmarks when idle | Background processes affect timing |
| Commit baseline to repo | Enables cross-machine comparison |
| Review regressions manually | Some regressions are expected (e.g., new features) |
| Update baseline after confirmed changes | Baseline should reflect current state |

---

## 6. What Causes False Positives

| Cause | Mitigation |
|-------|------------|
| Background CPU usage | Run benchmarks when system is idle |
| Different hardware | Generate baseline on target hardware |
| Different liboqs build | Record liboqs version in baseline metadata |
| Python GC timing | Run multiple iterations to average |
| Thermal throttling | Run on consistent thermal state |

---

## 7. Files Reference

| File | Purpose |
|------|---------|
| `scripts/run_performance_benchmarks.py` | Run benchmarks |
| `scripts/compare_performance.py` | Compare results against baseline |
| `benchmarks/performance/baseline.json` | Saved baseline (git-tracked) |
| `benchmarks/performance/results.json` | Latest benchmark results |
| `benchmarks/performance/results-comparison.json` | Comparison results (JSON) |
| `benchmarks/performance/results-comparison.md` | Comparison results (Markdown) |
| `benchmarks/performance/baseline.example.json` | Example baseline with reference values |

---

*This guide is practical and honest. The regression system is informational, not a blocking gate.*