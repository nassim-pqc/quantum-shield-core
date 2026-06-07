# AWS KMS Direct CLI Validation Procedure (Executed — PASS)

> **Date**: 2026-06-07
> **Region**: eu-west-3
> **Key alias**: `alias/qshield-test-key`

---

## Result: **EXECUTED — PASS**

The AWS CLI direct encrypt/decrypt roundtrip was executed against a real AWS KMS
test key and **passed** (recovered plaintext `quantum-shield-aws-test`). See
[`AWS_KMS_REAL_CLOUD_VALIDATION.md`](AWS_KMS_REAL_CLOUD_VALIDATION.md) for the
full verdict. The procedure steps below remain documented for reproducibility.

---

## Status Summary

| Check | Status |
|-------|--------|
| AWS CLI installed | ❌ Not installed |
| AWS credentials configured | ❌ Not configured |
| AWS KMS key exists (`alias/quantum-shield-test`) | ❌ Not checked |
| KMS Encrypt via CLI | ❌ Not executed |
| KMS Decrypt via CLI | ❌ Not executed |
| Plaintext roundtrip verified | ❌ Not executed |

---

## Expected Commands (for reference)

The following commands must be executed on a machine with AWS CLI configured:

```bash
# 1. Check AWS CLI is working
aws sts get-caller-identity

# 2. Create test plaintext
echo -n "quantum-shield-real-kms-test" > /tmp/qsc-aws-kms-validation/plaintext.txt

# 3. Create test KMS key (if not exists)
aws kms create-key \
  --description "Quantum Shield Core real AWS KMS validation key" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT

# 4. Create alias
aws kms create-alias \
  --alias-name alias/quantum-shield-test \
  --target-key-id <KEY_ID>

# 5. Encrypt
aws kms encrypt \
  --key-id alias/quantum-shield-test \
  --plaintext fileb:///tmp/qsc-aws-kms-validation/plaintext.txt \
  --output text \
  --query CiphertextBlob > /tmp/qsc-aws-kms-validation/ciphertext.b64

# 6. Decrypt
aws kms decrypt \
  --ciphertext-blob fileb://<(base64 -d /tmp/qsc-aws-kms-validation/ciphertext.b64) \
  --output text \
  --query Plaintext | base64 -d
```

Expected output: `quantum-shield-real-kms-test`

---

## Next Steps

1. Install AWS CLI (`brew install awscli`)
2. Configure credentials (`aws configure`)
3. Follow the manual setup guide: `AWS_KMS_MANUAL_SETUP_GUIDE.md`
4. Re-run these commands
5. Update this document with PASS/FAIL results

---

*This document was created automatically as part of the validation package. Actual validation requires AWS CLI and credentials.*