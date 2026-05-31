# QUANTUM SHIELD
## Dossier Technique & Commercial — Usage Confidentiel

**Solution souveraine de chiffrement post-quantique pour données d'entreprise**
Version 4.0 · Document préparé pour présentation à acheteur qualifié

---

## Résumé Exécutif

Les ordinateurs quantiques rendront obsolètes d'ici 2030–2035 la quasi-totalité des systèmes de chiffrement déployés aujourd'hui. La stratégie d'attaque dite « *harvest now, decrypt later* » est déjà en cours : des acteurs étatiques collectent aujourd'hui des données chiffrées pour les déchiffrer demain.

**Quantum Shield** est une réponse opérationnelle à cette menace. C'est un microservice souverain et clé en main qui expose par API REST un moteur de chiffrement hybride post-quantique — le seul standard recommandé simultanément par le NIST (FIPS 203, août 2024), l'ANSSI et l'ENISA pour la transition cryptographique.

**L'acheteur acquiert :**
- Un moteur cryptographique production-ready, testé et documenté
- Une architecture souveraine 100% on-premise, zéro dépendance cloud
- Une piste d'audit inviolable conforme NIS2 / ISO 27001
- La première brique d'une offre PQC à forte valeur ajoutée

---

## 1. Contexte Marché

### Le problème est réglementaire autant que technique

| Réglementation | Exigence | Échéance |
|---|---|---|
| **NIS2** (directive UE) | Mesures cryptographiques état de l'art pour OIV et OSE | En vigueur — transposition FR 2024 |
| **NIST FIPS 203** | Migration vers ML-KEM (Kyber) pour systèmes fédéraux US | Standard publié août 2024 |
| **ANSSI PQC Roadmap** | Recommande l'hybridation PQC dès maintenant | Guidance publiée 2024 |
| **NSM-10 (USA)** | Inventaire et migration des systèmes cryptographiques | 2025–2030 |
| **Directive eIDAS 2** | Signatures électroniques résistantes aux attaques quantiques | 2026 |

Le marché adressable PQC est estimé à **17 milliards USD d'ici 2030** (MarketsandMarkets, 2024), avec une croissance de 34% par an. Les premiers entrants sont ceux qui se positionnent maintenant.

### Le timing est optimal

- Les standards NIST sont finalisés → pas de risque de changer de technologie
- Les grands éditeurs (Microsoft, IBM, AWS) proposent du PQC en cloud seulement
- Le marché souverain / on-premise n'a pas encore d'acteur dominant en France
- Les appels d'offres sectoriels (défense, santé, finance) vont commencer à exiger du PQC en 2025–2026

---

## 2. Architecture Technique

### Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────┐
│  Applications métier (ERP, GED, messagerie, SIEM...)         │
│  ──────────────── REST API (JSON / Base64) ─────────────────  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Quantum Shield Core (Docker / on-premise)          │  │
│  │                                                        │  │
│  │  Authentification  │  RBAC   │  Rate Limiting          │  │
│  │  (X-API-Key)       │  Rôles  │  (slowapi)              │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐  │  │
│  │  │  SecurityEngine                                  │  │  │
│  │  │  Kyber768 KEM (ML-KEM, NIST FIPS 203)           │  │  │
│  │  │  + AES-256-GCM (chiffrement symétrique)         │  │  │
│  │  │  + HMAC-SHA256  (audit trail signé)             │  │  │
│  │  └──────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  Base de données audit  │  Dashboard visuel            │  │
│  │  (SQLite / PostgreSQL)  │  (interface temps réel)      │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Stack technologique

| Composant | Technologie | Justification |
|---|---|---|
| **KEM post-quantique** | Kyber768 via liboqs (Open Quantum Safe) | Standard NIST FIPS 203 · bibliothèque de référence du NIST |
| **Chiffrement symétrique** | AES-256-GCM | Niveau militaire · authenticated encryption |
| **Framework API** | FastAPI (Python 3.11) | Async natif · validation Pydantic · performances élevées |
| **Audit trail** | HMAC-SHA256 + SQLAlchemy async | Signatures vérifiables · PostgreSQL-ready |
| **Déploiement** | Docker multi-stage | Image minimale · utilisateur non-root · healthcheck intégré |
| **Base de données** | SQLite (défaut) / PostgreSQL | Zéro config en entrée · migration une ligne d'env |

---

## 3. Fonctionnalités Détaillées

### 3.1 Chiffrement Hybride Post-Quantique

Le schéma hybride est la seule approche recommandée par l'ensemble des agences nationales de cybersécurité (NIST, ANSSI, BSI, NCSC) pour la période de transition :

```
Kyber768.Encap(clé_publique)  →  secret_partagé (32 octets)
AES-256-GCM.Encrypt(secret_partagé, donnée, contexte_AAD)  →  données_chiffrées
```

**Pourquoi hybride ?** Si une vulnérabilité était découverte dans Kyber768, AES-256-GCM protège toujours. Si un ordinateur quantique casse AES, Kyber protège. Les deux doivent être compromis simultanément — probabilité nulle dans les horizons prévisibles.

### 3.2 Contexte AAD (Additional Authenticated Data)

Chaque donnée chiffrée est cryptographiquement liée à un identifiant de contexte (numéro de dossier, identifiant document, département). Toute tentative de réutiliser un chiffré dans un contexte différent échoue immédiatement. Empêche les attaques par rejeu et la confusion de données entre projets/clients.

### 3.3 Piste d'Audit Inviolable

```
Chaque opération → log JSON canonique → HMAC-SHA256(AUDIT_KEY)
→ stockage en base → vérification à chaque lecture
→ "🛡️ OK" si intact / "🚨 FAIL" si falsifié
```

Conforme aux exigences de NIS2 Art. 21, ISO 27001 A.12.4, HDS (Hébergement Données de Santé).

### 3.4 Contrôle d'Accès par Rôles (RBAC)

| Rôle | Droits |
|---|---|
| **Operator** | Générer des clés, chiffrer, déchiffrer, écrire des logs |
| **Auditor** | Lire et vérifier la piste d'audit uniquement |

Architecture extensible : ajout d'un rôle `admin` ou `readonly` sans modifier la logique métier.

### 3.5 Sécurité Infrastructure

- Validation fail-secure au démarrage (refuse de démarrer si secrets faibles ou absents)
- Rate limiting par endpoint et par IP (protection anti-brute force)
- HTTP Security Headers (HSTS, X-Frame-Options, CSP, Cache-Control)
- Erreurs opaques côté client (protection anti-oracle)
- Comparaison de clés en temps constant (protection anti-timing)
- Image Docker non-root (UID 8888, principe du moindre privilège)

---

## 4. Différenciateurs Concurrentiels

| Critère | Quantum Shield | Concurrents cloud (AWS KMS PQC, Azure) | Bibliothèques open-source (liboqs brut) |
|---|---|---|---|
| **Souveraineté** | ✅ 100% on-premise | ❌ Données en cloud étranger | ⚠️ Pas de service, intégration à faire |
| **Déploiement** | ✅ Docker en 5 min | ❌ Compte cloud requis | ❌ Dev from scratch |
| **API prête** | ✅ REST documentée | ✅ Oui | ❌ Non |
| **Audit NIS2** | ✅ Intégré et signé | ⚠️ Partiel | ❌ Non |
| **RBAC** | ✅ Opérateur / Auditeur | ✅ IAM complexe | ❌ Non |
| **Standard NIST** | ✅ FIPS 203 (ML-KEM) | ✅ | ✅ |
| **Coût** | ✅ Licence unique | ❌ Pay-per-use illimité | ✅ Gratuit mais coût intégration |
| **Support FR / ANSSI** | ✅ Architecture compatible CSPN | ❌ | ❌ |

---

## 5. Cas d'Usage Cibles

### Secteur Juridique & M&A
Chiffrement des dossiers de fusion-acquisition, actes notariés, procédures judiciaires. Garantie de confidentialité à long terme même si les algorithmes classiques sont compromis dans 10 ans.

### Santé & HDS
Dossiers patients, données génomiques, essais cliniques. Conformité HDS exige chiffrement fort et piste d'audit — Quantum Shield répond aux deux en une seule brique.

### Industrie & Défense
Propriété intellectuelle (brevets, plans, formulations), données de contrats sensibles. La souveraineté on-premise est non-négociable dans ces secteurs.

### Fintech & Assurance
Données clients, modèles de scoring, historiques de transactions. La réglementation DORA (Digital Operational Resilience Act) renforce les exigences cryptographiques à partir de 2025.

### Intégration dans des produits tiers (OEM)
La conception API-first permet à n'importe quel éditeur d'intégrer le moteur PQC en quelques heures sans toucher à la cryptographie.

---

## 6. Modèles de Valorisation

### Option A — Cession d'IP complète (recommandée)
Transfert du code source, de la documentation et des droits de propriété intellectuelle.

**Fourchette : 80 000 – 150 000 €**

Inclus : code source complet (11 fichiers), suite de tests (couverture >80%), documentation technique, dossier d'architecture, accompagnement technique de 30 jours.

### Option B — Licence on-premise par déploiement
L'acheteur intègre et revend sous sa marque.

**8 000 – 20 000 €/an par déploiement client**

Adapté aux intégrateurs et ESN.

### Option C — Licence OEM / white-label
Intégration du moteur dans un produit existant de l'acheteur.

**Redevance 5–15% du CA généré** ou **forfait annuel 15 000 – 40 000 €**

---

## 7. Livrables Inclus dans la Cession

| Livrable | Statut |
|---|---|
| Code source complet (11 fichiers Python + Docker) | ✅ Inclus |
| Suite de tests pytest (unitaires + intégration) | ✅ Inclus |
| Dashboard d'audit visuel (HTML, zéro dépendance) | ✅ Inclus |
| Documentation technique complète (README) | ✅ Inclus |
| Dossier d'architecture de sécurité | ✅ Ce document |
| Template de déploiement (.env.example) | ✅ Inclus |
| Accompagnement technique (30 jours) | ✅ Négociable |
| Formation équipe technique acheteur (1 jour) | ✅ Négociable |

---

## 8. Conformité Réglementaire

| Référentiel | Couverture par Quantum Shield |
|---|---|
| **NIST FIPS 203** (ML-KEM) | ✅ Kyber768 = ML-KEM-768 |
| **NIS2 Art. 21** | ✅ Chiffrement + piste d'audit signée |
| **ISO 27001 A.10** | ✅ Chiffrement des données |
| **ISO 27001 A.12.4** | ✅ Journaux d'audit avec intégrité |
| **HDS** | ✅ Architecture compatible |
| **RGPD Art. 32** | ✅ Mesures techniques appropriées |
| **DORA** | ✅ Résilience cryptographique |
| **ANSSI PQC** | ✅ Architecture hybride recommandée |

**Prochaine étape recommandée pour l'acheteur :** Qualification CSPN (ANSSI) — ouvre le marché des marchés publics et OIV. Délai estimé : 6–12 mois post-acquisition. Coût : 15 000–40 000 €.

---

## 9. Due Diligence Technique — Points Clés

**Ce que l'acheteur trouvera dans le code :**
- Validation fail-secure dès le démarrage (aucun lancement possible sans secrets valides)
- Comparaison des clés API en temps constant (`hmac.compare_digest`)
- Sérialisation JSON canonique (`sort_keys=True`) pour la stabilité des HMAC
- Assignation ctypes par slice pour la compatibilité liboqs-python
- Messages d'erreur opaques côté client (protection anti-oracle)
- Tests couvrant les cas limites, les attaques par falsification et les mauvaises clés

**Ce que l'acheteur devra ajouter s'il veut scaler :**
- KMS intégré (gestion du cycle de vie des clés) : ~4 semaines
- Multi-tenant avec isolation par organisation : ~3 semaines
- PostgreSQL en cluster HA : ~1 semaine (changement de variable d'env + infra)

---

## 10. Contact & Conditions

Ce dossier est confidentiel et destiné exclusivement au destinataire identifié. Toute reproduction ou diffusion est interdite sans accord écrit.

**Disponibilité :** Démonstration technique disponible sur demande (live ou enregistrée).
**Délai de réponse :** 48h ouvrées.
**NDA :** Accord de confidentialité disponible avant tout échange de code source.

---

*Quantum Shield — Architecture souveraine · Standard NIST · Production-ready*
*Document version 4.0 — Mai 2025*
