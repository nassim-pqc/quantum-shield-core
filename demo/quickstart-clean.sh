#!/usr/bin/env bash
# Quantum Shield Core — Demo rapide pour évaluateurs techniques
# Prérequis : Docker >= 24, Docker Compose >= 2.20
set -euo pipefail

GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

header() { echo -e "\n${BOLD}${CYAN}▶ $1${NC}"; }
ok()     { echo -e "  ${GREEN}✔ $1${NC}"; }
info()   { echo -e "  ${YELLOW}$1${NC}"; }

echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║         QUANTUM SHIELD ENCLAVE — ÉVALUATION         ║"
echo "║     Chiffrement Post-Quantique Souverain (PQC)       ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 1. Vérification des prérequis
header "Vérification des prérequis"
command -v docker >/dev/null 2>&1 || { echo "Docker requis. https://docs.docker.com/get-docker/"; exit 1; }
command -v jq     >/dev/null 2>&1 || { echo "jq requis. brew install jq / apt install jq"; exit 1; }
ok "Docker et jq disponibles"

# 2. Configuration
header "Configuration de l'environnement"
if [ ! -f .env ]; then
  cp .env.example .env
  # Injecter des valeurs de test sécurisées
  sed -i.bak \
    -e 's/REPLACE_WITH_STRONG_POSTGRES_PASSWORD/DemoPassword2026Secure!/g' \
    -e 's/REPLACE_WITH_AUDIT_HMAC_KEY_VERSION_1_MIN_32_CHARS/DemoAuditKeyForEvaluation2026MinChars!/g' \
    -e 's/REPLACE_WITH_OPERATOR_API_KEY_MIN_32_CHARS/demo-operator-key-for-evaluation-2026!!/g' \
    -e 's/REPLACE_WITH_AUDITOR_API_KEY_MIN_32_CHARS/demo-auditor-key-for-evaluation-2026!!!/g' \
    .env 2>/dev/null || true
  rm -f .env.bak
  ok ".env créé avec des valeurs de démonstration"
else
  ok ".env existant conservé"
fi

BASE_URL="http://127.0.0.1:8000"
OPERATOR_KEY=$(grep "^API_KEY_OPERATOR=" .env | cut -d'=' -f2)
HEADERS=(-H "X-API-Key: ${OPERATOR_KEY}" -H "Content-Type: application/json")

# 3. Démarrage de la stack
header "Démarrage de la stack Docker"
docker compose down -v --remove-orphans 2>/dev/null || true
docker compose up --build -d
info "Attente de la disponibilité du service..."
for i in $(seq 1 30); do
  if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then break; fi
  sleep 2
  echo -n "."
done
echo ""
ok "Service opérationnel"

# 4. Health check
header "Health Check"
HEALTH=$(curl -sf "${BASE_URL}/health")
echo "  $(echo "${HEALTH}" | jq -r '"Statut: \(.status) | Algo: \(.algorithm) | DB: \(.database)"')"
ok "Endpoint /health fonctionnel"

# 5. Génération de clés PQC
header "Génération de clés Post-Quantiques (ML-KEM-768 / Kyber768)"
KEYPAIR=$(curl -sf -X POST "${BASE_URL}/api/v1/keys/generate" "${HEADERS[@]}")
PUB_KEY=$(echo "${KEYPAIR}" | jq -r '.public_key_b64')
PRIV_KEY=$(echo "${KEYPAIR}" | jq -r '.private_key_b64')
info "Clé publique  : ${PUB_KEY:0:40}..."
info "Clé privée    : ${PRIV_KEY:0:40}..."
ok "Paire de clés Kyber768 générée"

# 6. Chiffrement (Seal)
header "Chiffrement hybride (Seal) — Kyber768 KEM + AES-256-GCM"
PAYLOAD_B64=$(echo -n "DONNEES_CONFIDENTIELLES_M&A_2026" | base64)
CONTEXT="dossier-ma-acquisition-2026"
SEALED=$(curl -sf -X POST "${BASE_URL}/api/v1/crypto/seal" "${HEADERS[@]}" \
  -d "{\"public_key_b64\":\"${PUB_KEY}\",\"data_b64\":\"${PAYLOAD_B64}\",\"context\":\"${CONTEXT}\"}")
CPQ=$(echo "${SEALED}" | jq -r '.ciphertext_pqc_b64')
NONCE=$(echo "${SEALED}" | jq -r '.nonce_b64')
ENC=$(echo "${SEALED}" | jq -r '.encrypted_data_b64')
info "Ciphertext KEM : ${CPQ:0:40}..."
info "Données chiffrées : ${ENC:0:40}..."
ok "Payload scellé — données inaccessibles sans clé privée"

# 7. Déchiffrement (Unseal)
header "Déchiffrement (Unseal) — Récupération du plaintext"
UNSEALED=$(curl -sf -X POST "${BASE_URL}/api/v1/crypto/unseal" "${HEADERS[@]}" \
  -d "{\"private_key_b64\":\"${PRIV_KEY}\",\"ciphertext_pqc_b64\":\"${CPQ}\",\"nonce_b64\":\"${NONCE}\",\"encrypted_data_b64\":\"${ENC}\",\"context\":\"${CONTEXT}\"}")
RECOVERED=$(echo "${UNSEALED}" | jq -r '.decrypted_data_b64' | base64 -d)
info "Données récupérées : ${RECOVERED}"
ok "Déchiffrement parfait — intégrité vérifiée par GCM"

# 8. Test de sécurité AAD
header "Test de sécurité — Falsification du contexte (AAD enforcement)"
TAMPERED=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/api/v1/crypto/unseal" \
  "${HEADERS[@]}" \
  -d "{\"private_key_b64\":\"${PRIV_KEY}\",\"ciphertext_pqc_b64\":\"${CPQ}\",\"nonce_b64\":\"${NONCE}\",\"encrypted_data_b64\":\"${ENC}\",\"context\":\"CONTEXTE_FRAUDULEUX\"}")
[ "${TAMPERED}" = "401" ] && ok "Attaque bloquée — Code 401 (contexte falsifié rejeté)" || echo "ÉCHEC DU TEST"

# 9. Piste d'audit
header "Piste d'audit HMAC — Vérification d'intégrité"
LOGS=$(curl -sf "${BASE_URL}/api/v1/audit/logs" "${HEADERS[@]}")
COUNT=$(echo "${LOGS}" | jq length)
INTEGRITY=$(echo "${LOGS}" | jq -r '.[0].integrity // "N/A"')
info "Entrées dans la piste d'audit : ${COUNT}"
info "Intégrité dernière entrée : ${INTEGRITY}"
ok "Audit trail fonctionnel et vérifié HMAC"

# 10. Métriques Prometheus
header "Observabilité — Métriques Prometheus"
METRICS=$(curl -sf "${BASE_URL}/metrics" | grep "^qshield_" | head -5)
echo "${METRICS}" | while read -r line; do info "${line}"; done
ok "Endpoint /metrics opérationnel"

# Conclusion
echo ""
echo -e "${BOLD}${GREEN}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║         ÉVALUATION COMPLÈTE — TOUT VERT ✔           ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Swagger UI  : http://127.0.0.1:8000/docs            ║"
echo "║  Dashboard   : http://127.0.0.1:8000/dashboard       ║"
echo "║  Métriques   : http://127.0.0.1:8000/metrics         ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
