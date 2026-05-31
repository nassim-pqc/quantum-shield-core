# Quantum Shield — Python SDK

Official Python client for the Quantum Shield Core API.

## Installation

```bash
pip install requests  # Only external dependency
```

Or use your local copy:

```bash
cd quantum-shield-enclav
pip install -e sdk/
```

## Quick Start

```python
from sdk import QuantumShieldClient

client = QuantumShieldClient(
    base_url="http://localhost:8000",
    api_key="your-operator-key"
)

# Generate keypair
keypair = client.generate_keypair()

# Encrypt data
sealed = client.seal(
    keypair["public_key_b64"],
    b"sensitive data",
    context="my-document-id"
)

# Decrypt data
decrypted = client.unseal(
    keypair["private_key_b64"],
    sealed,
    context="my-document-id"
)
```

## Examples

| Example | Use case |
|---------|----------|
| `examples/exemple_chiffrement_fichier.py` | File encryption (PDF, DOCX) |
| `examples/exemple_audit_nis2.py` | NIS2 audit trail with verification |
| `examples/exemple_rotation_cles.py` | PQC key rotation without data loss |

Run examples:

```bash
python sdk/examples/exemple_chiffrement_fichier.py
python sdk/examples/exemple_audit_nis2.py
python sdk/examples/exemple_rotation_cles.py
```

## API Reference

### `QuantumShieldClient(base_url, api_key, timeout, verify_ssl)`

Initialize the client.

**Parameters:**
- `base_url` (str): Service URL, e.g. `http://localhost:8000`
- `api_key` (str): Operator or auditor API key
- `timeout` (int): Request timeout in seconds (default: 30)
- `verify_ssl` (bool): Verify SSL certificates (default: True)

### `client.health()` → dict

Check service health and database connectivity.

**Returns:**
```python
{
    "status": "ok",
    "algorithm": "Kyber768",
    "version": "1.0.0",
    "database": "ok"
}
```

### `client.generate_keypair()` → dict

Generate an ML-KEM-768 (Kyber768) keypair.

**Returns:**
```python
{
    "public_key_b64": "...",   # Base64 public key
    "private_key_b64": "..."   # Base64 private key (store securely!)
}
```

### `client.seal(public_key_b64, data, context)` → dict

Encrypt data using hybrid Kyber768 + AES-256-GCM.

**Parameters:**
- `public_key_b64` (str): Recipient's public key
- `data` (bytes): Data to encrypt
- `context` (str): Business identifier (AAD — binds ciphertext to ID)

**Returns:**
```python
{
    "ciphertext_pqc_b64": "...",    # Kyber768 KEM ciphertext
    "nonce_b64": "...",             # AES-GCM nonce
    "encrypted_data_b64": "..."     # Encrypted data + tag
}
```

### `client.unseal(private_key_b64, sealed, context)` → bytes

Decrypt sealed data.

**Parameters:**
- `private_key_b64` (str): Recipient's private key
- `sealed` (dict): Dict returned by `seal()`
- `context` (str): Same context used in `seal()`

**Returns:**
- bytes — decrypted data

**Raises:**
- `QuantumShieldError` (status_code=401) if context mismatches or key is invalid

### `client.seal_text(public_key_b64, text, context)` → dict

Convenience method: encrypt a string.

### `client.unseal_text(private_key_b64, sealed, context)` → str

Convenience method: decrypt to string.

### `client.seal_file(public_key_b64, file_path, context)` → dict

Convenience method: encrypt a file's contents.

### `client.unseal_to_file(private_key_b64, sealed, context, output_path)`

Convenience method: decrypt to file.

### `client.write_audit_log(action, target, user)` → dict

Write a signed entry to the audit trail.

**Parameters:**
- `action` (str): Action code (e.g., "EXPORT", "ARCHIVE", "DELETE")
- `target` (str): Target object (e.g., "report.pdf", "folder-42")
- `user` (str): User ID or role

### `client.get_audit_logs(skip, limit, action, actor)` → list

Retrieve audit entries with integrity verification.

**Parameters:**
- `skip` (int): Offset (default: 0)
- `limit` (int): Max entries (default: 50)
- `action` (str, optional): Filter by action
- `actor` (str, optional): Filter by actor

**Returns:**
List of audit log dicts with `integrity` field: `"🛡️ OK"` or `"🚨 FAIL"`

### `client.get_audit_stats()` → dict

Get audit statistics by action type.

## Error Handling

```python
from sdk import QuantumShieldClient, QuantumShieldError

client = QuantumShieldClient(...)

try:
    keypair = client.generate_keypair()
except QuantumShieldError as e:
    print(f"Error: {e.message}")
    if e.status_code == 401:
        print("Unauthorized — check API key")
    elif e.status_code == 403:
        print("Forbidden — insufficient permissions")
```

## Environment Variables

Configure via environment:

```bash
export QS_URL="http://localhost:8000"
export QS_OPERATOR_KEY="your-operator-key"
export QS_AUDITOR_KEY="your-auditor-key"
```

Then in code:

```python
import os
from sdk import QuantumShieldClient

client = QuantumShieldClient(
    base_url=os.environ.get("QS_URL", "http://localhost:8000"),
    api_key=os.environ.get("QS_OPERATOR_KEY", "demo-key")
)
```

## Thread Safety

`QuantumShieldClient` uses `requests.Session()` internally, which is thread-safe. You can safely share a client instance across threads.

## License

See LICENSE in the Quantum Shield Core repository.
