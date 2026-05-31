# ADR-002: Rust comme cœur cryptographique

## Statut
Accepté

## Contexte
Le projet nécessite un noyau cryptographique avec garanties de sécurité mémoire, idéal pour l'auditabilité dans un contexte régulé (NIS2, PCI-DSS).

## Décision
Implémenter le cœur cryptographique en Rust avec bindings PyO3 pour l'intégration Python.

## Justification
- Garanties de sécurité mémoire à la compilation (use-after-free, buffer overflows)
- HMAC constant-time via le crate `hmac`
- Configuration `panic = "abort"` pour éviter les comportements indéfinis
- Intégration Python native via `pyo3` sans overhead FFI
- `cargo-audit` et `cargo-deny` pour l'audit de dépendances

## Conséquences
- Le KEM (Kyber768) reste en Python via `liboqs` car pas de binding Rust direct
- La compilation Rust ajoute ~30s au pipeline CI
- Nécessite une toolchain Rust dans l'environnement de production (Docker multi-stage)

## Alternatives rejetées
- Python natif : pas de garanties sécurité mémoire
- C/C++ : gestion mémoire manuelle, trop risqué pour un audit
- Go : pas d'intégration Python native sans FFI lourd