#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting Quantum Shield API..."
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "${UVICORN_WORKERS:-4}" \
  --timeout-keep-alive "${UVICORN_TIMEOUT_KEEP_ALIVE:-30}"
