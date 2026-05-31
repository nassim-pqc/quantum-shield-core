# Swagger Walkthrough

1. Set `ENABLE_DOCS=true` in `.env` and restart: `docker compose up -d`
2. Open http://127.0.0.1:8000/docs
3. Click **Authorize** — not required for trying public `/health`; for crypto endpoints use header `X-API-Key`
4. Expand **Cryptography** → `POST /api/v1/crypto/seal` → **Try it out**
5. Use values from `./demo.sh` output (`public_key_b64`, `data_b64`, `context`)
6. Execute **Unseal** with returned ciphertext fields and the matching `private_key_b64`
7. Under **Audit Trail**, call `GET /api/v1/audit/logs` with auditor or operator key

OpenAPI JSON: http://127.0.0.1:8000/openapi.json
