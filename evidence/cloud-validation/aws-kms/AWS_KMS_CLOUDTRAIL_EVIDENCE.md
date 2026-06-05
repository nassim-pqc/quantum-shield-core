# AWS KMS CloudTrail Evidence

> **Date**: June 2026  
> **Region**: N/A  
> **Status**: NOT AVAILABLE

---

## Result: **NOT AVAILABLE**

CloudTrail evidence could not be gathered because:

1. **AWS CLI is not installed** — cannot run `aws cloudtrail lookup-events`
2. **No AWS credentials configured** — cannot authenticate to AWS
3. **No KMS key was created** — no KMS events to observe

---

## Expected Procedure

The following command should be executed after AWS CLI is configured:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=kms.amazonaws.com \
  --max-results 10
```

Expected events after running the validation:
- `Encrypt` — from `aws kms encrypt` or provider `wrap_key()`
- `Decrypt` — from `aws kms decrypt` or provider `unwrap_key()`
- `DescribeKey` — from provider `health_check()`
- `CreateKey` — if a new key was created
- `CreateAlias` — if a new alias was created

---

## Why This Is Not a Critical Failure

CloudTrail evidence is a **supplementary verification** that confirms KMS operations were logged by AWS. It is not required to validate that the Quantum Shield Core provider works with real AWS KMS.

The primary validation (Encrypt/Decrypt roundtrip through both CLI and provider) is the essential test. CloudTrail verification proves the audit trail exists but does not affect the correctness of the provider.

---

## When to Re-check

After completing manual AWS KMS validation per the setup guide:
1. Run `aws kms encrypt` / `aws kms decrypt`
2. Run the provider validation script
3. Immediately run `aws cloudtrail lookup-events`
4. Update this document with:
   - Event types observed
   - Timestamps
   - Region
   - Redacted event IDs (no sensitive data)