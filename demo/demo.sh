#!/usr/bin/env bash
# Quantum Shield Core — Full API demo sequence
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OPERATOR_KEY="${API_KEY_OPERATOR:-operator-api-key-very-secure-32-chars-long!}"
AUDITOR_KEY="${API_KEY_AUDITOR:-auditor-api-key-very-secure-32-chars-long!!}"
HDR=(-H "X-API-Key: ${OPERATOR_KEY}" -H "Content-Type: application/json")
CID="demo-$(date +%s)"

echo "=== Quantum Shield Core Demo ==="
echo "Base URL: ${BASE_URL}"
echo ""

echo "1. Health"
curl -sS "${BASE_URL}/health" | python3 -m json.tool
echo ""

echo "2. Generate key pair"
KEYS=$(curl -sS -X POST "${BASE_URL}/api/v1/keys/generate" "${HDR[@]}" -H "X-Correlation-ID: ${CID}")
echo "${KEYS}" | python3 -m json.tool
PUB=$(echo "${KEYS}" | python3 -c "import sys,json; print(json.load(sys.stdin)['public_key_b64'])")
PRIV=$(echo "${KEYS}" | python3 -c "import sys,json; print(json.load(sys.stdin)['private_key_b64'])")
echo ""

DATA_B64=$(python3 -c "import base64; print(base64.b64encode(b'Confidential NIS2 document payload').decode())")
CONTEXT="demo-contract-2026-001"

echo "3. Seal"
SEALED=$(curl -sS -X POST "${BASE_URL}/api/v1/crypto/seal" "${HDR[@]}" \
  -d "{\"public_key_b64\":\"${PUB}\",\"data_b64\":\"${DATA_B64}\",\"context\":\"${CONTEXT}\"}")
echo "${SEALED}" | python3 -m json.tool
CPQC=$(echo "${SEALED}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ciphertext_pqc_b64'])")
NONCE=$(echo "${SEALED}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['nonce_b64'])")
ENC=$(echo "${SEALED}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['encrypted_data_b64'])")
echo ""

echo "4. Unseal"
curl -sS -X POST "${BASE_URL}/api/v1/crypto/unseal" "${HDR[@]}" \
  -d "{\"private_key_b64\":\"${PRIV}\",\"ciphertext_pqc_b64\":\"${CPQC}\",\"nonce_b64\":\"${NONCE}\",\"encrypted_data_b64\":\"${ENC}\",\"context\":\"${CONTEXT}\"}" \
  | python3 -m json.tool
echo ""

echo "5. Write audit log"
curl -sS -X POST "${BASE_URL}/api/v1/audit/log" "${HDR[@]}" \
  -d '{"action":"DEMO","target":"demo.sh","user":"operator"}' | python3 -m json.tool
echo ""

echo "6. List audit logs (auditor)"
curl -sS "${BASE_URL}/api/v1/audit/logs?limit=5" \
  -H "X-API-Key: ${AUDITOR_KEY}" | python3 -m json.tool
echo ""

echo "7. Prometheus metrics (sample)"
curl -sS "${BASE_URL}/metrics" | head -20
echo ""
echo "=== Demo complete ==="
