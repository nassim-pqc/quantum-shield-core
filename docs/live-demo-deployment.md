# Live Demo Deployment Guide

This guide enables you to deploy a public Quantum Shield Core demo in under 30 minutes.

## Prerequisites

- A VPS with Docker (minimum: 1 vCPU, 1 GB RAM, 10 GB storage)
- A domain name pointing to the VPS
- 30 minutes

## Quick Deploy (Docker)

### 1. Start the service

```bash
docker run -d --name qshield \
  -p 8000:8000 \
  -e AUDIT_KEY="demo-audit-key-change-in-production-32bytes!" \
  -e API_KEY_OPERATOR="demo-operator-key-insecure-for-demo-only" \
  -e API_KEY_AUDITOR="demo-auditor-key-insecure-for-demo-only" \
  -e ENABLE_DOCS=true \
  -e LOG_LEVEL=INFO \
  quantum-shield-core:latest   # build locally: docker build -t quantum-shield-core:latest .
```

### 2. Verify

```bash
curl http://localhost:8000/health
# {"status":"healthy","algorithm":"Kyber768","version":"1.0.0","database":"ok (0 audit entries)"}
```

### 3. Test encryption

```bash
# Generate keys
curl -s -X POST http://localhost:8000/api/v1/keys/generate \
  -H "X-API-Key: demo-operator-key-insecure-for-demo-only" \
  | jq .
```

## Production Deployment with HTTPS (Caddy)

### docker-compose.yml

```yaml
version: '3.8'
services:
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    depends_on:
      - qshield

  qshield:
    image: quantum-shield-core:latest   # build locally: docker build -t quantum-shield-core:latest .
    expose:
      - "8000"
    environment:
      - AUDIT_KEY=${AUDIT_KEY}
      - API_KEY_OPERATOR=${API_KEY_OPERATOR}
      - API_KEY_AUDITOR=${API_KEY_AUDITOR}
      - ENABLE_DOCS=true
      - LOG_LEVEL=INFO
    restart: unless-stopped

volumes:
  caddy_data:
```

### Caddyfile

```
demo.quantumshieldcore.com {
    reverse_proxy qshield:8000
    header {
        Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
    }
}
```

### Environment (.env)

```bash
AUDIT_KEY="your-production-audit-key-min-32-bytes"
API_KEY_OPERATOR="your-operator-key"
API_KEY_AUDITOR="your-auditor-key"
```

### Deploy

```bash
docker compose up -d
```

## With PostgreSQL (Recommended for Production)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: qshield
      POSTGRES_USER: qshield
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U qshield"]
      interval: 5s
      timeout: 5s
      retries: 5

  qshield:
    image: quantum-shield-core:latest   # build locally: docker build -t quantum-shield-core:latest .
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql+asyncpg://qshield:${DB_PASSWORD}@postgres:5432/qshield
      - AUDIT_KEY=${AUDIT_KEY}
      - API_KEY_OPERATOR=${API_KEY_OPERATOR}
      - API_KEY_AUDITOR=${API_KEY_AUDITOR}
    ports:
      - "8000:8000"

volumes:
  pgdata:
```

## Monitoring Commands

```bash
# Check logs
docker logs qshield -f --tail 100

# Health check with timing
time curl -s http://localhost:8000/health

# Metrics
curl -s http://localhost:8000/metrics | grep -E "qshield_|python_info"

# Load test (install locust first)
pip install locust
locust -f tests/performance/load_test.py --host=http://localhost:8000 \
  --headless --users 10 --spawn-rate 1 --run-time 30s
```

## Backup

```bash
# SQLite backup
cp quantum_shield.db quantum_shield.db.backup

# PostgreSQL backup
docker exec -t postgres pg_dump -U qshield qshield > qshield_$(date +%F).sql
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `AUDIT_KEY not found` | Missing env var | Add `-e AUDIT_KEY=...` |
| `database unavailable` | PostgreSQL not ready | Wait 10s, restart container |
| Rate limit errors | Too many requests | Wait 1 minute or restart container |
| `ModuleNotFoundError` | Missing Rust build | Use pre-built Docker image |