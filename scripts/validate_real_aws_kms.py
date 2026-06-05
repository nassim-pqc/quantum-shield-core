#!/usr/bin/env python3
"""
validate_real_aws_kms.py — Real AWS KMS validation script.

This script tests the Quantum Shield Core AWS KMS provider against
a real AWS KMS Customer Managed Key.

Prerequisites:
    - AWS CLI configured (aws configure) or AWS env vars set
    - AWS_KMS_KEY_ID environment variable (e.g., alias/quantum-shield-test)
    - AWS_REGION environment variable (e.g., eu-west-3)

Usage:
    export AWS_KMS_KEY_ID=alias/quantum-shield-test
    export AWS_REGION=eu-west-3
    python scripts/validate_real_aws_kms.py

Security:
    - Never writes secrets to disk
    - Never prints sensitive values
    - Uses only already-configured environment credentials
"""

from __future__ import annotations

import os
import sys
from typing import Any

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# ---------------------------------------------------------------------------
# Global test state
# ---------------------------------------------------------------------------
_PASS = 0
_FAIL = 0
_RESULTS: list[dict[str, Any]] = []


def _check(name: str, passed: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if passed:
        _PASS += 1
        status = "PASS"
    else:
        _FAIL += 1
        status = "FAIL"
    _RESULTS.append({"check": name, "status": status, "detail": detail})
    print(f"  {status}: {name}" + (f" ({detail})" if detail else ""))


def main() -> int:
    print("=" * 60)
    print("AWS KMS Provider Real Validation")
    print("=" * 60)
    print()

    # ------------------------------------------------------------------
    # 1. Check environment prerequisites
    # ------------------------------------------------------------------
    print("[1/5] Environment check...")

    key_id = os.environ.get("AWS_KMS_KEY_ID", "")
    region = os.environ.get("AWS_REGION", "")

    if not key_id:
        _check("AWS_KMS_KEY_ID set", False, "Missing: export AWS_KMS_KEY_ID=alias/...")
    else:
        _check("AWS_KMS_KEY_ID set", True)

    if not region:
        _check("AWS_REGION set", False, "Missing: export AWS_REGION=eu-west-...")
    else:
        _check("AWS_REGION set", True)

    # Check boto3 availability
    try:
        import boto3  # noqa: F401

        _check("boto3 available", True)
    except ImportError:
        _check("boto3 available", False, "pip install boto3")
        print("\n❌ Cannot proceed without boto3")
        return 1

    print(f"\n  Key ID / Alias: {key_id}")
    print(f"  Region:         {region}")
    print()

    if _FAIL > 0 and not key_id:
        print("❌ Cannot proceed: AWS_KMS_KEY_ID not set")
        return 1

    # ------------------------------------------------------------------
    # 2. Import provider
    # ------------------------------------------------------------------
    print("[2/5] Provider import...")

    try:
        from providers.kms.aws_kms import AWSKMSProvider

        provider = AWSKMSProvider(max_retries=0)
        _check("AWSKMSProvider imported and initialized", True, f"key_id={key_id}")
    except Exception as exc:
        _check("AWSKMSProvider imported and initialized", False, str(exc))
        print("\n❌ Cannot proceed: provider init failed")
        return 1

    print()

    # ------------------------------------------------------------------
    # 3. Health check / DescribeKey
    # ------------------------------------------------------------------
    print("[3/5] Health check (DescribeKey)...")

    try:
        status = provider.health_check()
        key_state = status.get("key_state", "unknown")
        key_usage = status.get("key_usage", "unknown")
        is_available = status.get("status") == "available"
        _check(
            "DescribeKey / health check",
            is_available,
            f"state={key_state}, usage={key_usage}",
        )
    except Exception as exc:
        _check("DescribeKey / health check", False, str(exc))

    print()

    # ------------------------------------------------------------------
    # 4. Wrap / Unwrap (Encrypt / Decrypt)
    # ------------------------------------------------------------------
    print("[4/5] Encrypt/Decrypt roundtrip...")

    # Use a 32-byte test DEK (simulating Kyber768 shared secret)
    dek = bytes(range(32))

    try:
        wrapped = provider.wrap_key(dek)
        _check("Encrypt (wrap_key)", True, f"blob length={len(wrapped)}")
    except Exception as exc:
        _check("Encrypt (wrap_key)", False, str(exc))
        wrapped = None

    if wrapped:
        try:
            unwrapped = provider.unwrap_key(wrapped)
            _check("Decrypt (unwrap_key)", True)
        except Exception as exc:
            _check("Decrypt (unwrap_key)", False, str(exc))
            unwrapped = None

        if wrapped and unwrapped:
            roundtrip_ok = unwrapped == dek
            _check("Plaintext roundtrip", roundtrip_ok)
            if not roundtrip_ok:
                _check(
                    "Plaintext match",
                    False,
                    f"expected {dek.hex()} got {unwrapped.hex()}",
                )

    # ------------------------------------------------------------------
    # 5. Summary
    # ------------------------------------------------------------------
    print()
    print("[5/5] Summary")
    print(f"  Passed: {_PASS}")
    print(f"  Failed: {_FAIL}")
    print(f"  Region: {region}")
    print(f"  Key alias: {key_id}")

    if _FAIL == 0 and _PASS > 0:
        print("\n  Result: ✅ PASS")
        print("\n  AWS KMS provider works with a real AWS KMS customer managed key.")
        exit_code = 0
    elif _FAIL > 0:
        print(f"\n  Result: ❌ FAIL ({_FAIL} checks failed)")
        exit_code = 1
    else:
        print("\n  Result: ⚠️  No checks executed")
        exit_code = 1

    print()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
