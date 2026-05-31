# ADR-004: Architecture microservice

## Statut
Accepté

## Contexte
Le service cryptographique doit être déployable, scalable et isolable des autres composants de l'infrastructure.

## Décision
Architecture microservice REST exposant une API FastAPI, conteneurisé via Docker, orchestré via Kubernetes.

## Justification
- Séparation des responsabilités : le service cryptographique peut être audité indépendamment
- Scalabilité horizontale : les opérations cryptographiques sont sans état (stateless)
- Isolation réseau : le service peut être placé derrière un API gateway avec politiques réseau restrictives
- Observabilité native : Prometheus, OpenTelemetry, logs JSON structurés
- Côté client : SDK Python et Go pour l'intégration applicative

## Conséquences
- Le service ne stocke pas de clés privées (stateless par conception)
- La base de données PostgreSQL est requise uniquement pour la piste d'audit
- Le rate limiting par IP est nécessaire pour la protection anti-DoS

## Alternatives rejetées
- Bibliothèque Python seule : pas de séparation des responsabilités, difficile à auditer isolément
- Architecture monolithique : pas de scaling indépendant du composant crypto
- gRPC : plus performant mais courbe d'apprentissage plus élevée et écosystème moins mature pour l'audit