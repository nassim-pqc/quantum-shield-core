"""
Azure Key Vault provider (stub) — production via azure-keyvault-keys SDK.
"""
from __future__ import annotations

import os

from security_engine import AbstractKMS


class AzureKeyVaultProvider(AbstractKMS):
    """
    Azure Key Vault provider — stub prêt à câbler via azure-keyvault-keys.

    Comportement actuel : lit AUDIT_KEY_v* depuis les variables d'environnement
    (identique à LocalEnvKMS). Le stub est architecturalement correct et prêt
    pour l'intégration production.

    Pour activer Azure Key Vault réel :
      1. pip install azure-keyvault-keys azure-identity
      2. Définir AZURE_KEY_VAULT_URL et configurer DefaultAzureCredential
      3. Remplacer get_audit_key() par un appel KeyClient.unwrap_key()

    Variables d'environnement :
      AZURE_KEY_VAULT_URL   — ex: https://myvault.vault.azure.net/
      AZURE_AUDIT_KEY_NAME  — nom de la clé (défaut: quantum-shield-audit)
    """

    def __init__(
        self,
        vault_url: str | None = None,
        key_name: str | None = None,
    ) -> None:
        self.vault_url = vault_url or os.environ.get("AZURE_KEY_VAULT_URL", "")
        self.key_name = key_name or os.environ.get(
            "AZURE_AUDIT_KEY_NAME", "quantum-shield-audit"
        )
        self._local_fallback = self._load_env_keys()

    @staticmethod
    def _load_env_keys() -> dict[str, bytes]:
        keys: dict[str, bytes] = {}
        for name, value in os.environ.items():
            if name.startswith("AUDIT_KEY_"):
                version = name.split("AUDIT_KEY_", 1)[1].lower()
                if len(value) >= 32:
                    keys[version] = value.encode()
        if not keys and "AUDIT_KEY" in os.environ:
            keys["v1"] = os.environ["AUDIT_KEY"].encode()
        return keys

    def get_audit_key(self, version: str) -> bytes | None:
        return self._local_fallback.get(version)
