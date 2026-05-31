#!/usr/bin/env bash
# Capture live API/Docker outputs and render documentation PNGs.
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${ROOT}/docs/images/captures"
mkdir -p "$OUT_DIR"

echo "Capturing from ${BASE_URL} -> ${OUT_DIR}"

curl -sf "${BASE_URL}/health" | python3 -m json.tool > "${OUT_DIR}/health.json"
curl -sf "${BASE_URL}/metrics" | grep -E '^qshield_|^http_request' | head -40 > "${OUT_DIR}/metrics.txt" || true
curl -sf "${BASE_URL}/openapi.json" -o "${OUT_DIR}/openapi.json"

if [[ -n "${API_KEY_OPERATOR:-}" ]]; then
  curl -sf -X POST "${BASE_URL}/api/v1/keys/generate" \
    -H "X-API-Key: ${API_KEY_OPERATOR}" \
    -H "X-Correlation-ID: doc-capture-$(date +%s)" \
    | python3 -m json.tool > "${OUT_DIR}/keygen-redacted.json"
  python3 -c "
import json
p='${OUT_DIR}/keygen-redacted.json'
d=json.load(open(p))
for k in list(d):
    if 'b64' in k and d[k]:
        d[k]=d[k][:20]+'...[REDACTED]'
json.dump(d, open(p,'w'), indent=2)
"
  curl -sf -X POST "${BASE_URL}/api/v1/audit/log" \
    -H "X-API-Key: ${API_KEY_OPERATOR}" \
    -H "Content-Type: application/json" \
    -d '{"action":"DOC_CAPTURE","target":"release-screenshot","user":"operator"}' \
    | python3 -m json.tool > "${OUT_DIR}/audit-write.json" || true

  curl -sf "${BASE_URL}/api/v1/audit/logs?limit=3" \
    -H "X-API-Key: ${API_KEY_OPERATOR}" \
    | python3 -m json.tool > "${OUT_DIR}/audit-logs.json" || true
fi

docker ps --filter name=qshield --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' > "${OUT_DIR}/docker-ps.txt" 2>/dev/null || true
docker compose -f "${ROOT}/docker-compose.yml" logs --tail=12 quantum-shield-api 2>/dev/null \
  | sed 's/\x1b\[[0-9;]*m//g' > "${OUT_DIR}/docker-startup.log" || true

python3 "${ROOT}/scripts/generate_doc_screenshots.py"
echo "Done. Screenshots: ${ROOT}/docs/images/screenshot-*.png"
