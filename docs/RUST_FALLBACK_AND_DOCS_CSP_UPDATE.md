# Operational Hardening — Rust Fallback Logging + Docs CSP

Two narrow operational improvements raised by the CTO audit. No crypto, no API,
no provider, no SDK changes.

## 1. Rust fallback logging

### Problem

`security_engine.py` previously swallowed Rust-engine failures silently:

```python
except Exception:
    pass  # nosec B110
```

If `quantum_shield_engine.SecurityEngine.with_audit_key(...)`,
`.generate_signed_log(...)`, or `.verify_log(...)` raised at runtime, the Python
fallback ran but no signal was emitted. An operator had no way to notice that
the Rust-accelerated path was broken.

### Fix

A module-level logger and one helper:

```python
_logger = _logging.getLogger(__name__)

def _log_rust_fallback(operation: str, exc: BaseException) -> None:
    _logger.warning(
        "rust_engine_fallback",
        extra={"operation": operation, "reason": type(exc).__name__},
    )
```

Every `except Exception` on a Rust path now calls this helper. Three sites:

| Site | `operation` value |
|---|---|
| `SecurityEngine.__init__` — Rust engine construction | `"init"` |
| `generate_signed_log` — Rust HMAC sign | `"audit_sign"` |
| `verify_log` — Rust HMAC verify | `"audit_verify"` |

### What is **not** logged

The warning contains only the operation name and the exception **class name**
(`type(exc).__name__`). No string form of the exception, no audit key, no
plaintext, no ciphertext, no signature, no shared secret. Tests assert this
explicitly (`_assert_no_payload_leak`).

## 2. Content-Security-Policy on docs routes

### Problem

The middleware unconditionally emitted `default-src 'none'`. That is the correct
default for API endpoints, but it breaks Swagger UI / ReDoc when
`ENABLE_DOCS=true` — the bundled UI needs scripts/styles from `cdn.jsdelivr.net`
and an inline bootstrap.

### Fix

A small helper picks the right policy per request:

```python
_STRICT_CSP = "default-src 'none'"
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'"
)
_DOCS_PATHS = frozenset({"/docs", "/docs/oauth2-redirect", "/redoc"})

def _csp_for_path(path: str, docs_enabled: bool = _DOCS_ENABLED) -> str:
    if docs_enabled and path in _DOCS_PATHS:
        return _DOCS_CSP
    return _STRICT_CSP
```

### Properties

- `ENABLE_DOCS` unset or `false` → strict `default-src 'none'` everywhere. No
  behaviour change vs. previous code.
- `ENABLE_DOCS=true` → only `/docs`, `/docs/oauth2-redirect`, `/redoc` get the
  relaxed policy.
- `/openapi.json` stays strict — it's JSON, no CSP relaxation needed.
- All other endpoints (`/health`, `/api/v1/*`, `/metrics`, `/`, `/dashboard`)
  keep the strict policy regardless of `ENABLE_DOCS`.
- All other security headers (HSTS, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy) are unchanged.

## Files modified

| File | Change |
|---|---|
| `security_engine.py` | `_logger`, `_log_rust_fallback()`, 3 fallback sites updated |
| `main.py` | `_STRICT_CSP`, `_DOCS_CSP`, `_DOCS_PATHS`, `_DOCS_ENABLED`, `_csp_for_path()`, middleware now uses helper |
| `tests/test_security_engine.py` | `TestRustFallbackLogging` (3 tests with payload-leak assertions) |
| `tests/test_api.py` | `TestSecurityHeaders.test_csp_strict_on_api_endpoint` + `TestCSPHelper` (6 tests) |
| `docs/RUST_FALLBACK_AND_DOCS_CSP_UPDATE.md` | This file |

## Limits

- The fix logs Rust **failures**. It does not log successful Rust execution
  (that would be noisy). Health monitoring on `rust_engine_fallback` warning
  rate is the recommended signal for "Rust path degraded".
- Swagger/ReDoc CSP includes `'unsafe-inline'` because the bundled UI uses an
  inline bootstrap. This is scoped to the docs paths only and never affects
  API endpoints.
- No crypto change. No API contract change. No provider change. No external
  audit performed.
