# HKDF-SHA256 Key Derivation Update

## Problem

`security_engine.py` previously derived the AES-256-GCM data key from the
Kyber768 KEM shared secret with a single SHA-256 hash:

```python
aes_key = hashlib.sha256(shared_secret).digest()
```

A KEM output is a uniformly distributed shared secret, not formal "input keying
material" in the NIST SP 800-56C sense. A plain SHA-256 compression provides
no domain separation, no salt-mixing, and no NIST-recommended extract-then-expand
structure. It is a known red flag in applied-crypto review.

## Fix

The derivation now uses **HKDF-SHA256** (RFC 5869), via the
`cryptography.hazmat.primitives.kdf.hkdf` module already in the dependency set:

```python
def _derive_aes_key(shared_secret: bytes, context: bytes = b"") -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"quantum-shield-core:aes-256-gcm:v1:" + context,
    ).derive(shared_secret)
```

The HKDF `info` parameter binds:
- a versioned domain-separation prefix (`v1`), so the suffix can be bumped to
  intentionally invalidate older blobs in the future;
- the caller's `context`, which is also passed to AES-GCM as AAD — the same
  context-binding now happens both at key-derivation time **and** at AEAD
  authentication time (defense in depth).

## Files Modified

| File | Change |
|---|---|
| `security_engine.py` | Added `_derive_aes_key()`; replaced both SHA-256 sites in `encrypt_hybrid` / `decrypt_hybrid`. |
| `tests/test_security_engine.py` | Added `TestHKDFKeyDerivation` (7 tests: length, determinism, context separation, secret separation, anti-regression vs SHA-256, end-to-end roundtrip, wrong-context failure). |
| `docs/HKDF_KEY_DERIVATION_UPDATE.md` | This file. |

## Rust AES Path Note

The Rust engine (`rust-engine/src/lib.rs`) still derives via `Sha256::digest(shared_secret)`
internally. To prevent any cross-path incompatibility (a blob sealed under one
derivation could not be unsealed under another), the Python code no longer calls
`self._rust_engine.encrypt_aes_gcm` / `decrypt_aes_gcm` — Python HKDF is now the
single canonical path for AES-GCM seal/unseal.

The Rust HMAC path (`generate_signed_log`, `verify_log`) is unchanged: HMAC takes
its key directly, has no derivation ambiguity, and stays Rust-accelerated.

The Rust crate itself was not modified.

## Backward Compatibility

**This is a breaking change for previously sealed payloads.** Any ciphertext
produced by an older version of `security_engine.py` cannot be unsealed by this
version, because the AES key derivation is different.

This is acceptable for a pre-production project with no stored production blobs.
For any deployment that needs migration, the previous derivation can be added
back as a fallback path under a feature flag — out of scope here.

## Tests Executed

```
ruff check .             → All checks passed
ruff format --check .    → 49 files OK
pytest tests/            → 194 passed (187 prior + 7 new HKDF tests)
go test ./...            → OK (sdk-go: client, config, types, validate)
go build ./...           → OK
go vet ./...             → OK
```

## Limits

- This is an **applied-crypto improvement**, not the result of an independent
  cryptographic audit. The project still recommends a formal external review
  before any production claim.
- HKDF salt is `None` (uses HKDF's all-zero default). Adding an explicit salt
  derived from the KEM ciphertext could be a future hardening step, but would
  again break existing blobs and add little practical security here.
- No FIPS validation claim is made or implied by this change.
