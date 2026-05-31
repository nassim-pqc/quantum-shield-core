# Quantum Shield Core — 2-Minute Demo

**Audience:** CTO, CISO, acquirer technical due diligence.

## 0:00 — Start (one command)

```bash
chmod +x demo/quickstart.sh && ./demo/quickstart.sh
```

This copies `.env.example` → `.env` (dev placeholders), builds Docker, waits for health, runs `demo.sh`.

## 0:30 — Narration map

| Time | Say | Show |
|------|-----|------|
| 0:30 | "PQC enclave with DB-backed health." | `curl -s localhost:8000/health \| jq` → `"version": "1.0.0"` |
| 0:45 | "ML-KEM-768 keypair generated per request." | `demo.sh` step 2 |
| 1:00 | "Hybrid seal: Kyber + AES-GCM, context is mandatory AAD." | Seal JSON output |
| 1:15 | "Unseal with wrong context returns opaque 401." | Repeat unseal with bad `context` |
| 1:30 | "Every operation is HMAC-signed in PostgreSQL." | `GET /api/v1/audit/logs` |
| 1:45 | "Prometheus-ready for your SOC." | `curl localhost:8000/metrics \| grep qshield` |
| 2:00 | "OpenAPI at /docs, product page at /." | Browser |

## Manual path

```bash
cp .env.example .env   # replace REPLACE_WITH_* values
docker compose up --build -d
./demo/demo.sh
```

## Swagger

http://127.0.0.1:8000/docs — see [swagger-walkthrough.md](swagger-walkthrough.md)
