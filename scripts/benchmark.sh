#!/usr/bin/env bash
# Quantum Shield Core — Reproducible Benchmark Suite
#
# Usage:
#   export API_KEY_OPERATOR="your-operator-key"
#   export API_BASE="http://localhost:8000"
#   bash scripts/benchmark.sh [--json] [--md]
#
# Outputs:
#   docs/benchmarks/results.json  (if --json)
#   docs/benchmarks/results.md    (if --md)
#   stdout summary table

set -euo pipefail

API_KEY="${API_KEY_OPERATOR:-test-operator-key-change-me}"
API_BASE="${API_BASE:-http://localhost:8000}"
HEADERS=(-H "X-API-Key: ${API_KEY}" -H "Content-Type: application/json")

RESULTS_DIR="docs/benchmarks"
mkdir -p "$RESULTS_DIR"

RESULT_FILE="$RESULTS_DIR/results.json"
MD_FILE="$RESULTS_DIR/results.md"

OUTPUT_JSON=false
OUTPUT_MD=false

for arg in "$@"; do
    case "$arg" in
        --json) OUTPUT_JSON=true ;;
        --md)   OUTPUT_MD=true ;;
    esac
done

# --- Helper: timed request ---
bench() {
    local label="$1" method="$2" path="$3"
    shift 3

    local start total_ms
    start=$(date +%s%N)
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" \
        "${HEADERS[@]}" "$@" "$API_BASE$path")
    local end
    end=$(date +%s%N)
    total_ms=$(( (end - start) / 1000000 ))

    echo "$label" "$total_ms" "$http_code"
}

# --- Warmup ---
echo "Warming up..."
curl -sf -o /dev/null "${HEADERS[@]}" "$API_BASE/health" 2>/dev/null || true

# --- Benchmarks ---
echo "Running benchmarks..."

declare -a results

# Key generation (5 samples)
echo "  keygen..."
for i in 1 2 3 4 5; do
    results+=("$(bench "keygen" POST "/api/v1/keys/generate")")
    sleep 0.2
done

# Seal 1KB (5 samples)
echo "  seal_1kb..."
PAYLOAD_1KB=$(python3 -c "import base64; print(base64.b64encode(b'x'*1024).decode())")
PUB_KEY=$(curl -sf -X POST "${HEADERS[@]}" "$API_BASE/api/v1/keys/generate" | python3 -c "import sys,json; print(json.load(sys.stdin)['public_key_b64'])")

for i in 1 2 3 4 5; do
    results+=("$(bench "seal_1kb" POST "/api/v1/crypto/seal" \
        -d "{\"public_key_b64\":\"$PUB_KEY\",\"data_b64\":\"$PAYLOAD_1KB\",\"context\":\"bench-$i\"}")")
    sleep 0.2
done

# Seal 1MB (3 samples)
echo "  seal_1mb..."
PAYLOAD_1MB=$(python3 -c "import base64; print(base64.b64encode(b'x'*(1024*1024)).decode())")
for i in 1 2 3; do
    results+=("$(bench "seal_1mb" POST "/api/v1/crypto/seal" \
        -d "{\"public_key_b64\":\"$PUB_KEY\",\"data_b64\":\"$PAYLOAD_1MB\",\"context\":\"bench-large-$i\"}")")
    sleep 0.5
done

# Audit write (5 samples)
echo "  audit..."
for i in 1 2 3 4 5; do
    results+=("$(bench "audit" POST "/api/v1/audit/log" \
        -d "{\"action\":\"BENCHMARK\",\"target\":\"bench-$i\",\"user\":\"benchmark\"}")")
    sleep 0.2
done

# Health (5 samples)
echo "  health..."
for i in 1 2 3 4 5; do
    results+=("$(bench "health" GET "/health")")
    sleep 0.05
done

# --- Parse & Aggregate ---
declare -A sums counts mins maxs
for r in "${results[@]}"; do
    read -r label ms code <<< "$r"
    if [ "$code" != "200" ] && [ "$code" != "201" ]; then
        echo "WARNING: $label returned HTTP $code (expected 200/201), skipping"
        continue
    fi
    sums[$label]=$(( sums[$label] + ms ))
    counts[$label]=$(( counts[$label] + 1 ))
    if [ -z "${mins[$label]}" ] || [ "$ms" -lt "${mins[$label]}" ]; then
        mins[$label]=$ms
    fi
    if [ -z "${maxs[$label]}" ] || [ "$ms" -gt "${maxs[$label]}" ]; then
        maxs[$label]=$ms
    fi
done

# --- Output ---
echo ""
echo "========================================="
echo "  Quantum Shield Core — Benchmarks"
echo "========================================="
echo ""

output_json="["
output_md="| Operation | Samples | Avg (ms) | Min (ms) | Max (ms) |\n|-----------|---------|----------|----------|----------|\n"
first=true

for label in keygen seal_1kb seal_1mb audit health; do
    count=${counts[$label]:-0}
    if [ "$count" -eq 0 ]; then
        echo "  [SKIP] $label: no valid samples"
        continue
    fi
    avg=$(( sums[$label] / count ))
    min=${mins[$label]}
    max=${maxs[$label]}

    printf "  %-12s  samples=%d  avg=%dms  min=%dms  max=%dms\n" \
        "$label" "$count" "$avg" "$min" "$max"

    output_md+="| $label | $count | $avg | $min | $max |\n"

    entry="{\"operation\":\"$label\",\"samples\":$count,\"avg_ms\":$avg,\"min_ms\":$min,\"max_ms\":$max}"
    if $first; then
        output_json+="$entry"
        first=false
    else
        output_json+=",$entry"
    fi
done
output_json+="]"

echo ""
echo "========================================="

if $OUTPUT_JSON; then
    echo "$output_json" > "$RESULT_FILE"
    echo "JSON results saved to $RESULT_FILE"
fi

if $OUTPUT_MD; then
    {
        echo "# Benchmark Results"
        echo ""
        echo "Date: $(date -u '+%Y-%m-%d %H:%M UTC')"
        echo "API: $API_BASE"
        echo ""
        echo -e "$output_md"
    } > "$MD_FILE"
    echo "Markdown results saved to $MD_FILE"
fi