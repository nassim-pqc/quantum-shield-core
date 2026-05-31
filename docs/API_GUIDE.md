# API Guide

Base URL: `http://localhost:8000` (behind TLS in production).

## Authentication

```http
X-API-Key: <your-api-key>
X-Correlation-ID: <optional-uuid>
```

## Generate Keys

```http
POST /api/v1/keys/generate
```

Response 201: `public_key_b64`, `private_key_b64` — store the private key off-enclave.

## Seal

```http
POST /api/v1/crypto/seal
Content-Type: application/json

{
  "public_key_b64": "...",
  "data_b64": "SGVsbG8=",
  "context": "document-id-42"
}
```

## Unseal

```http
POST /api/v1/crypto/unseal

{
  "private_key_b64": "...",
  "ciphertext_pqc_b64": "...",
  "nonce_b64": "...",
  "encrypted_data_b64": "...",
  "context": "document-id-42"
}
```

## Audit

- `POST /api/v1/audit/log` — append custom event  
- `GET /api/v1/audit/logs?skip=0&limit=50` — list with live HMAC verification  
- `GET /api/v1/audit/stats` — aggregates  

OpenAPI: enable `ENABLE_DOCS=true` → `/docs`.
