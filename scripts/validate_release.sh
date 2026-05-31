#!/usr/bin/env bash
# Pre-publish validation — run before tagging a GitHub release.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Checking for secrets in repo..."
if git rev-parse --is-inside-work-tree &>/dev/null; then
  if git ls-files | grep -E '^\.env$|\.env\.txt$'; then
    echo "ERROR: .env or .env.txt is tracked by git"
    exit 1
  fi
fi
for f in .env .env.txt; do
  if [[ -f "$f" ]]; then
    echo "ERROR: $f must not exist in repo (use .env.example only)"
    exit 1
  fi
done
if [[ ! -f .env.example ]]; then
  echo "ERROR: missing .env.example"
  exit 1
fi

echo "==> Checking VERSION file..."
VER="$(tr -d '[:space:]' < VERSION)"
[[ "$VER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Invalid VERSION: $VER"; exit 1; }

echo "==> Python lint (ruff)..."
python3 -m ruff check main.py security_engine.py auth.py database.py models.py audit_store.py constants.py observability providers tests 2>/dev/null || {
  echo "Install: pip install ruff"
  exit 1
}

echo "==> Docker compose build..."
docker compose build --quiet

if [[ -f .env ]]; then
  echo "==> Starting stack (local .env present)..."
  docker compose up -d
  sleep 25
  curl -sf http://127.0.0.1:8000/health | python3 -m json.tool
  curl -sf http://127.0.0.1:8000/metrics | head -5
  echo "==> Demo smoke test..."
  export API_KEY_OPERATOR="${API_KEY_OPERATOR:-operator-api-key-very-secure-32-chars-long!}"
  ./demo/demo.sh >/dev/null
  echo "Demo OK"
else
  echo "Skip runtime tests (no .env — copy .env.example to .env for full validation)"
fi

echo ""
echo "Validation complete. Tag release: git tag v$(cat VERSION) && git push origin v$(cat VERSION)"
