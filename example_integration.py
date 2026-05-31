"""
Quantum Shield — Script de Démo Client Interactif
==================================================
Démonstration pas-à-pas du protocole cryptographique Post-Quantique.
A lancer dans un terminal après avoir exécuté : docker compose up --build
"""
import base64
import os
import sys
import time
import requests

# Codes couleur ANSI pour un rendu terminal professionnel
C_GREEN = "\033[92m"
C_CYAN = "\033[96m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

def print_step(step_num, title):
    print(f"\n{C_BOLD}{C_CYAN}[ÉTAPE {step_num}] {title}...{C_RESET}")
    time.sleep(0.6)

def print_success(message):
    print(f"  {C_GREEN}✔ {message}{C_RESET}")

def print_info(label, value):
    print(f"  {C_BOLD}{label}:{C_RESET} {value[:60]}...")

# Configuration
API_URL = os.environ.get("QS_API_URL", "http://localhost:8000/api/v1")
OPERATOR_KEY = os.environ.get("QS_OPERATOR_KEY", "test-operator-api-key-secure-enough-32chars!!")

# Header de l'application
print(f"{C_BOLD}{C_YELLOW}" + "="*65)
print("     ⚡ QUANTUM SHIELD — ADAPTER VOTRE INFRASTRUCTURE AU PQC ⚡  ")
print("="*65 + f"{C_RESET}")
print(f"Connexion au microservice d'enclave : {C_BOLD}{API_URL}{C_RESET}\n")

if not OPERATOR_KEY:
    print(f"{C_RED}❌ Erreur : La variable QS_OPERATOR_KEY n'est pas définie.{C_RESET}")
    sys.exit(1)

# Initialisation de la session HTTP
SESSION = requests.Session()
SESSION.headers.update({"X-API-Key": OPERATOR_KEY, "Content-Type": "application/json"})

try:
    # ------------------------------------------------------------------
    # ÉTAPE 1 : Vérification de la santé du service
    # ------------------------------------------------------------------
    print_step(1, "Vérification de l'état de l'enclave (Health Check)")
    health_resp = SESSION.get(f"{API_URL.replace('/api/v1', '')}/health", timeout=5)
    health_resp.raise_for_status()
    health_data = health_resp.json()
    print_success("Service opérationnel et sain.")
    print_info("Algorithme actif", health_data.get("algorithm", "Inconnu"))
    print_info("Backend DB local", health_data.get("database", "Inconnu"))

    # ------------------------------------------------------------------
    # ÉTAPE 2 : Génération de la paire de clés Kyber768 (ML-KEM)
    # ------------------------------------------------------------------
    print_step(2, "Génération d'une paire de clés Post-Quantique (Kyber768)")
    key_resp = SESSION.post(f"{API_URL}/keys/generate", timeout=5)
    key_resp.raise_for_status()
    keypair = key_resp.json()
    print_success("Paire de clés asymétriques générée avec succès.")
    print_info("Clé Publique (Base64)", keypair["public_key_b64"])
    print_info("Clé Privée (Base64)", keypair["private_key_b64"])

    # ------------------------------------------------------------------
    # ÉTAPE 3 : Chiffrement / Scellement de la donnée (Seal)
    # ------------------------------------------------------------------
    print_step(3, "Chiffrement d'une donnée critique corporative (Seal)")
    document_secret = b"DONNEES_FINANCIERES_CONFIDENTIELLES_2026"
    context_metier = "PROJET_M&A_QUANTUM"
    
    print(f"  {C_BOLD}Donnée brute : {C_RESET}{document_secret.decode()}")
    print(f"  {C_BOLD}Contexte lié (AAD) : {C_RESET}{context_metier}")
    
    seal_payload = {
        "public_key_b64": keypair["public_key_b64"],
        "data_b64": base64.b64encode(document_secret).decode(),
        "context": context_metier
    }
    
    seal_resp = SESSION.post(f"{API_URL}/crypto/seal", json=seal_payload, timeout=5)
    seal_resp.raise_for_status()
    sealed_data = seal_resp.json()
    print_success("Payload scellé cryptographiquement.")
    print_info("Ciphertext PQC (KEM)", sealed_data["ciphertext_pqc_b64"])
    print_info("Données chiffrées (AES-GCM)", sealed_data["encrypted_data_b64"])

    # ----------------──────────────────────────────────────────────────
    # ÉTAPE 4 : Déchiffrement / Ouverture (Unseal)
    # ------------------------------------------------------------------
    print_step(4, "Déchiffrement via l'Enclave Post-Quantique (Unseal)")
    unseal_payload = {
        "private_key_b64": keypair["private_key_b64"],
        "ciphertext_pqc_b64": sealed_data["ciphertext_pqc_b64"],
        "nonce_b64": sealed_data["nonce_b64"],
        "encrypted_data_b64": sealed_data["encrypted_data_b64"],
        "context": context_metier
    }
    
    unseal_resp = SESSION.post(f"{API_URL}/crypto/unseal", json=unseal_payload, timeout=5)
    unseal_resp.raise_for_status()
    unsealed_data = unseal_resp.json()
    
    plaintext_recupere = base64.b64decode(unsealed_data["decrypted_data_b64"])
    print_success("Déchiffrement réussi sans altération.")
    print(f"  {C_GREEN}{C_BOLD}▶ Donnée restaurée : {plaintext_recupere.decode()}{C_RESET}")

    # ------------------------------------------------------------------
    # ÉTAPE 5 : Simulation d'une attaque par falsification (Sécurité Défensive)
    # ------------------------------------------------------------------
    print_step(5, "Simulation d'attaque : Altération du contexte métier (AAD)")
    print(f"  {C_YELLOW}Action : Tentative de rejeu du payload avec un contexte modifié...{C_RESET}")
    
    tampered_payload = {**unseal_payload, "context": "CONTEXTE_FRAUDULEUX_REJEU"}
    
    attack_resp = SESSION.post(f"{API_URL}/crypto/unseal", json=tampered_payload, timeout=5)
    
    if attack_resp.status_code == 401:
        print_success("L'attaque a échoué. L'enclave a bloqué le déchiffrement (Code 401).")
        print(f"  {C_GREEN}Message du serveur : {attack_resp.json()['detail']}{C_RESET}")
    else:
        print(f"  {C_RED}❌ Échec de la protection : Le serveur a répondu {attack_resp.status_code}{C_RESET}")

    # ------------------------------------------------------------------
    # ÉPILOQUE : Conclusion
    # ------------------------------------------------------------------
    print(f"\n{C_BOLD}{C_GREEN}" + "="*65)
    print(" 🎉 TOUT EST VERT — LE PROTOCOLE QUANTUM SHIELD EST VERIFIE !")
    print("="*65 + f"{C_RESET}\n")

except requests.exceptions.ConnectionError:
    print(f"\n{C_RED}❌ Erreur de connexion : Impossible de joindre l'API Quantum Shield.{C_RESET}")
    print("   Assurez-vous d'avoir lancé l'infrastructure avec : docker compose up")
except Exception as e:
    print(f"\n{C_RED}❌ Une erreur inattendue est survenue durant la démo : {e}{C_RESET}")