# AWS KMS — Real Cloud Validation

> **Verdict: PASS.** The AWS KMS provider was validated against a **real AWS KMS
> test key** using both the AWS CLI (direct encrypt/decrypt) and the Quantum
> Shield `AWSKMSProvider` wrap/unwrap roundtrip.

> **Date**: 2026-06-07
> **Environment**: real AWS KMS test account (development/test only)
> **Region**: eu-west-3
> **Key reference**: `alias/qshield-test-key`
> **Key type**: SYMMETRIC_DEFAULT
> **Key usage**: ENCRYPT_DECRYPT

---

## Verdict

| Validation | Status | Detail |
|------------|--------|--------|
| AWS CLI direct encrypt/decrypt | ✅ PASS | Roundtrip recovered `quantum-shield-aws-test` |
| Quantum Shield `AWSKMSProvider.health_check()` | ✅ PASS | `status: available`, `key_state: Enabled` |
| Quantum Shield `AWSKMSProvider` wrap/unwrap | ✅ PASS | 32-byte DEK wrapped + unwrapped |
| Roundtrip (unwrapped == original DEK) | ✅ PASS | — |
| CloudTrail evidence | ⚠️ NOT COLLECTED | Procedure documented, not executed |

---

## What was validated

### 1. AWS CLI direct encrypt/decrypt

```
aws kms encrypt --key-id alias/qshield-test-key --plaintext fileb://plaintext.txt ...
aws kms decrypt --ciphertext-blob fileb://ciphertext.bin ...
→ decrypted: quantum-shield-aws-test
```

Ciphertext blob length: 236 Base64 chars. Plaintext recovered exactly.

### 2. Quantum Shield `AWSKMSProvider`

```python
provider = AWSKMSProvider(key_id="alias/qshield-test-key", region="eu-west-3")
health = provider.health_check()
# → {provider: aws_kms, region: eu-west-3, encryption_algorithm: SYMMETRIC_DEFAULT,
#    key_state: Enabled, key_usage: ENCRYPT_DECRYPT, key_spec: SYMMETRIC_DEFAULT,
#    status: available}

dek = secrets.token_bytes(32)
wrapped = provider.wrap_key(dek)        # str, length 472
unwrapped = provider.unwrap_key(wrapped)
assert unwrapped == dek                 # PASS
```

Result:

```
Health check: available
Wrapped blob type: str
Wrapped blob length: 472
Unwrap: PASS
Roundtrip: PASS
```

---

## Notes

- The provider's `AWS_REGION` environment variable is shadowed by the
  `AWSKMSConfig.region` default (`eu-west-1`). The validation therefore passes
  the region explicitly via the constructor (`region="eu-west-3"`), which is the
  documented primary API. See "Limitations" below.
- Credentials were provided through a local AWS CLI profile
  (`qshield-aws-test`) via the standard boto3 credential chain. No access keys
  are embedded in code or configuration.

---

## Limitations

This validates AWS KMS integration against a real AWS test environment.
This is not a production customer deployment.
This is not an external security audit.
This is not FIPS certification.
This does not prove production readiness.

CloudTrail-based evidence was not collected; see
[`AWS_KMS_CLOUDTRAIL_PROCEDURE.md`](AWS_KMS_CLOUDTRAIL_PROCEDURE.md) for the
procedure if independent log evidence is required.

## Information intentionally omitted

- AWS account ID
- Full key ARN / full key ID
- Access key ID / secret access key / session token
- Full ciphertext / wrapped blob contents
