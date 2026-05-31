# cURL Examples

Set variables:

```bash
export BASE=http://127.0.0.1:8000
export KEY=operator-api-key-very-secure-32-chars-long!
```

## Health

```bash
curl -s "$BASE/health" | jq .
```

## Generate keys

```bash
curl -s -X POST "$BASE/api/v1/keys/generate" \
  -H "X-API-Key: $KEY" | jq .
```

## Seal

```bash
curl -s -X POST "$BASE/api/v1/crypto/seal" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "public_key_b64": "<PUBLIC_KEY>",
    "data_b64": "SGVsbG8gUUFudHVtIFNoaWVsZA==",
    "context": "doc-001"
  }' | jq .
```

## Unseal

```bash
curl -s -X POST "$BASE/api/v1/crypto/unseal" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "private_key_b64": "<PRIVATE_KEY>",
    "ciphertext_pqc_b64": "<CIPHERTEXT>",
    "nonce_b64": "<NONCE>",
    "encrypted_data_b64": "<DATA>",
    "context": "doc-001"
  }' | jq .
```

## Audit

```bash
curl -s -X POST "$BASE/api/v1/audit/log" \
  -H "X-API-Key: $KEY" \
  -H "Content-Type: application/json" \
  -d '{"action":"EXPORT","target":"report.pdf","user":"alice"}' | jq .

curl -s "$BASE/api/v1/audit/logs?limit=10" \
  -H "X-API-Key: $KEY" | jq .
```

## Metrics

```bash
curl -s "$BASE/metrics" | grep qshield_
```
