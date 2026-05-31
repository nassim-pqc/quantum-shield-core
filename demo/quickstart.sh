#!/usr/bin/env bash
# Quantum Shield Core — 60-second quickstart
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
  echo "IMPORTANT: Edit .env and replace all REPLACE_WITH_* values before production use."
  sed -i.bak \
    -e 's/REPLACE_WITH_STRONG_POSTGRES_PASSWORD/dev-postgres-password-minimum-32-chars-long!/' \
    -e 's/REPLACE_WITH_AUDIT_HMAC_KEY_VERSION_1_MIN_32_CHARS/dev-audit-hmac-key-minimum-32-chars-long!!/' \
    -e 's/REPLACE_WITH_OPERATOR_API_KEY_MIN_32_CHARS/operator-api-key-very-secure-32-chars-long!/' \
    -e 's/REPLACE_WITH_AUDITOR_API_KEY_MIN_32_CHARS/auditor-api-key-very-secure-32-chars-long!!/' \
    .env 2>/dev/null || sed -i '' \
    -e 's/REPLACE_WITH_STRONG_POSTGRES_PASSWORD/dev-postgres-password-minimum-32-chars-long!/' \
    -e 's/REPLACE_WITH_AUDIT_HMAC_KEY_VERSION_1_MIN_32_CHARS/dev-audit-hmac-key-minimum-32-chars-long!!/' \
    -e 's/REPLACE_WITH_OPERATOR_API_KEY_MIN_32_CHARS/operator-api-key-very-secure-32-chars-long!/' \
    -e 's/REPLACE_WITH_AUDITOR_API_KEY_MIN_32_CHARS/auditor-api-key-very-secure-32-chars-long!!/' \
    .env
  rm -f .env.bak
fi

echo "Building and starting Quantum Shield Core..."
docker compose up --build -d

echo "Waiting for health..."
for i in $(seq 1 40); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

curl -s http://127.0.0.1:8000/health | python3 -m json.tool

export API_KEY_OPERATOR="${API_KEY_OPERATOR:-operator-api-key-very-secure-32-chars-long!}"
echo ""
echo "Running full demo..."
"${ROOT}/demo/demo.sh"

echo ""
echo "Quickstart complete."
echo "  Landing:  http://127.0.0.1:8000/"
echo "  Docs:     http://127.0.0.1:8000/docs"
echo "  Metrics:  http://127.0.0.1:8000/metrics"
