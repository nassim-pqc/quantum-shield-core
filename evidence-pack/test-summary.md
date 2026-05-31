# Test Summary — Quantum Shield Core

_Generated from repository state on 31 May 2026_

## Results

**139 tests — 139 passed, 0 failed, 0 skipped**

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_api.py` | 37 | Integration: health, auth, seal, unseal, audit |
| `tests/test_security.py` | 21 | Security: auth bypass, validation, tamper, rate limit |
| `tests/test_audit_store.py` | 21 | Unit: store, read, verify audit logs |
| `tests/test_auth.py` | 11 | Unit: RBAC, key validation, inactive keys |
| `tests/test_security_engine.py` | 24 | Unit: Kyber768, AES-GCM, HMAC, edge cases |
| `tests/test_constants.py` | 17 | Unit: enums, constants, config |
| `tests/test_database.py` | 4 | Integration: connection, table creation |

## Test Categories

- **Integration tests** (API): 37 + 21 = 58
- **Unit tests** (crypto engine): 24
- **Unit tests** (audit store): 21
- **Unit tests** (auth): 11
- **Unit tests** (config): 17 + 4 = 21

## Key Validations

| Feature | Verified By |
|---------|-------------|
| Health check | `TestHealth` (3 tests) |
| RBAC enforcement | `TestAuthentication` (8 tests) |
| Key generation | `TestKeyGeneration` + `TestKeyGeneration` (10 tests) |
| Seal operation | `TestSeal` + `TestEncryptHybrid` (11 tests) |
| Unseal roundtrip | `TestUnseal` + `TestDecryptHybrid` (14 tests) |
| AAD enforcement | Wrong context → 401 (2 tests) |
| Tamper detection | Wrong key, wrong context, flipped bits (6 tests) |
| HMAC audit | Sign, verify, tamper, cross-key (12 tests) |
| Error opacity | No internal details in unseal errors (1 test) |
| Payload validation | Empty, too large, missing fields (6 tests) |
| Pagination | Limit, skip, filter (3 tests) |

## Environment

- SQLite in-memory for tests (reproducible, no external DB required)
- Test audit key: `test-audit-key-secure-enough-for-pytest-32chars!`
- CI enforces tests on every pull request

_All tests pass. Run `pytest tests/ -v` locally to reproduce._