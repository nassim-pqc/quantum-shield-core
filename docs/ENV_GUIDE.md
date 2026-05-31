# Environment Guide

Copy `.env.example` to `.env` and replace every `REPLACE_WITH_*` placeholder.

## Required

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `AUDIT_KEY_v1` | Audit signing key (≥32 chars) |
| `API_KEY_OPERATOR` | Operator API key (≥32 chars) |

## Recommended

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY_AUDITOR` | — | Read-heavy audit role |
| `ACTIVE_AUDIT_KEY_VERSION` | `v1` | Active HMAC key version |
| `KMS_PROVIDER` | `local` | `local`, `aws`, `vault`, `azure` |
| `ENABLE_DOCS` | `false` | OpenAPI `/docs` |
| `DATABASE_URL` | set by compose | Async SQLAlchemy URL |
| `UVICORN_WORKERS` | `4` | Worker processes |
| `LOG_LEVEL` | `INFO` | JSON log level |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | Enable tracing |

## PostgreSQL URL Format

```
postgresql+asyncpg://USER:PASSWORD@HOST:5432/DBNAME
```

## SQLite (local dev only)

```
DATABASE_URL=sqlite+aiosqlite:///./quantum_shield.db
```
