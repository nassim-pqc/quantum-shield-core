# Docker Guide

## Build & Run

```bash
cp .env.example .env
docker compose up --build
```

Services:

- **postgres** — PostgreSQL 16, healthcheck `pg_isready`
- **quantum-shield-api** — runs migrations then uvicorn

## Volumes

- `qshield_pgdata` — PostgreSQL data (replace SQLite volume from earlier versions)

## Healthchecks

- Postgres: `pg_isready`
- API: `GET /health` (includes DB ping)

## Resource Limits

| Service | CPU | Memory |
|---------|-----|--------|
| API | 2 | 768M |
| Postgres | — | 256M |

## Troubleshooting

```bash
docker compose logs -f quantum-shield-api
docker compose exec quantum-shield-api alembic current
```

If migrations fail, verify `DATABASE_URL` and Postgres credentials in `.env`.
