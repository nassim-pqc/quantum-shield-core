# ADR-003: AES-256-GCM comme chiffrement symétrique

## Statut
Accepté

## Contexte
Le KEM Kyber768 génère une clé partagée. Cette clé doit être utilisée pour le chiffrement symétrique des données avec authentification.

## Décision
Utiliser AES-256-GCM (AEAD) avec nonce de 12 octets et AAD (Additional Authenticated Data) lié au contexte applicatif.

## Justification
- AES-256-GCM est un standard NIST, largement audité
- AEAD garantit confidentialité + intégrité + authenticité
- Le tag GCM (16 octets) permet la détection de toute altération
- L'AAD lie le chiffrement à un contexte métier (ex: ID contrat)
- La clé AES est dérivée via SHA-256 du shared_secret Kyber768

## Conséquences
- Taille du ciphertext = plaintext + 16 octets (tag GCM)
- Nonce de 12 octets généré via `os.urandom()` à chaque opération
- La validation AAD est critique : contexte différent = refus de déchiffrement

## Alternatives rejetées
- AES-128-GCM : niveau de sécurité insuffisant pour usage PQC
- ChaCha20-Poly1305 : excellent mais AES-GCM bénéficie d'accélération matérielle AES-NI
- XChaCha20-Poly1305 : nonce plus grand mais non standard dans l'écosystème audité