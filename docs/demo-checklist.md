# Demo Public — Checklist de déploiement

_Use this checklist before any public demo deployment._

## Pré-requis

- [ ] Docker installé sur le serveur cible
- [ ] Domaine pointé vers le serveur (IP publique)
- [ ] Ports 80/443 ouverts

## Déploiement

```bash
docker run -d --name qshield \
  -p 8000:8000 \
  -e AUDIT_KEY="$(openssl rand -base64 32)" \
  -e API_KEY_OPERATOR="demo-operator-key" \
  -e API_KEY_AUDITOR="demo-auditor-key" \
  -e ENABLE_DOCS=true \
  ghcr.io/quantum-shield/core:latest
```

## Vérification

| Check | Command | Expected |
|-------|---------|----------|
| Health | `curl localhost:8000/health` | `{"status":"healthy"}` |
| Keygen | `curl -X POST localhost:8000/api/v1/keys/generate -H "X-API-Key: demo-operator-key"` | 201 |
| Seal | See docs/curl-examples.md | 200 |
| Unseal | See docs/curl-examples.md | 200 |
| Audit | `curl localhost:8000/api/v1/audit/logs -H "X-API-Key: demo-operator-key"` | 200 |
| Landing | Open `/` in browser | Professional B2B page |
| Demo | Open `/demo` in browser | Interactive seal/unseal |
| Swagger | `ENABLE_DOCS=true` → `/docs` | FastAPI swagger |
| Metrics | `curl localhost:8000/metrics` | Prometheus format |

## HTTPS (Caddy)

```yaml
# docker-compose.yml with Caddy reverse proxy
# See docs/live-demo-deployment.md for full config
```

## Responsive Check

- [ ] Mobile (375px width)
- [ ] Tablet (768px)
- [ ] Desktop (1280px)
- [ ] All sections readable

## Performance Check

- [ ] Landing page loads < 2s
- [ ] Demo seal/unseal < 5s
- [ ] No JS console errors
- [ ] No mixed content warnings

## Security Check

- [ ] TLS valid (no self-signed in prod)
- [ ] HSTS header present
- [ ] CSP header present
- [ ] No sensitive data in URL parameters

## Rollback Plan

```bash
docker stop qshield && docker rm qshield