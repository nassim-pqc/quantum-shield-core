# Modèle de Menace — Quantum Shield Core

## Assets protégés

| Asset | Classification | Impact perte |
|-------|---------------|-------------|
| Clé privée Kyber768 générée | Critique | Divulgation → déchiffrement rétroactif |
| Clé HMAC d'audit (AUDIT_KEY) | Critique | Falsification de la piste d'audit |
| Données en transit (seal/unseal) | Haute | Dépend du contexte applicatif |
| Logs d'audit | Haute | Perte de traçabilité réglementaire |
| Clés API (hash SHA-256) | Moyenne | Usurpation de rôle |

## Trust Boundaries

```
[Client SDK] → TLS 1.3 → [API Gateway] → [Quantum Shield Core]
                                                ↓
                                         [PostgreSQL]
```

1. **Boundary 1**: Client → API (TLS, authentification X-API-Key)
2. **Boundary 2**: API → DB (Réseau privé, authentification PostgreSQL)
3. **Boundary 3**: Process → Env vars (AUDIT_KEY, secrets)

## Risques

### STRIDE par composant

| Composant | Spoofing | Tampering | Repudiation | Info. Disclosure | DoS | Escalation |
|-----------|----------|-----------|-------------|-----------------|-----|------------|
| API FastAPI | X-API-Key hash | Validation Pydantic | Logs HMAC | Headers sécurité | Rate limiting | RBAC |
| Security Engine | N/A | AES-GCM tag | HMAC audit | Nonce unique | N/A | N/A |
| Audit Store | N/A | Hash chain | HMAC sign | N/A | Index DB | N/A |

### Scénarios critiques

1. **Divulgation AUDIT_KEY** → Attaquant peut falsifier les logs HMAC → Perte d'intégrité de la piste d'audit
2. **Bruteforce X-API-Key** → Accès non autorisé aux endpoints → Rotation de clé
3. **Rejeu de nonce AES-GCM** → Possible fuite d'information si même clé partagée → Chaque seal génère un nouveau nonce
4. **Déni de service** → Sur-sollicitation des opérations Kyber768 (coût CPU élevé) → Rate limiting + HPA Kubernetes

## Mitigations

| Risque | Mitigation | Priorité |
|--------|-----------|----------|
| Divulgation AUDIT_KEY | Rotation des clés via ACTIVE_AUDIT_KEY_VERSION | Haute |
| Brute force API | Rate limiting + logs d'échec d'authentification | Haute |
| Fuite mémoire Rust | `panic = "abort"`, sécurité mémoire du borrow checker | Haute |
| Altération logs | HMAC-SHA256 + hash chain (prev_entry_hash) | Haute |
| Timing attacks | `hmac.compare_digest` en Python, `Hmac::verify_slice` en Rust | Haute |
| Man-in-the-middle | TLS 1.3 + HSTS + CSP restrictif | Haute |
| Rejeu de clé | Nonce unique par opération seal | Moyenne |

## Hypothèses de sécurité

1. Le réseau entre API et PostgreSQL est privé (non accessible depuis Internet)
2. Les AUDIT_KEY sont injectées via un gestionnaire de secrets (Vault, AWS Secrets Manager, etc.)
3. TLS est terminé au niveau du reverse proxy / API gateway, pas dans l'application
4. Le host est régulièrement patché (CVE OS, liboqs, OpenSSL)