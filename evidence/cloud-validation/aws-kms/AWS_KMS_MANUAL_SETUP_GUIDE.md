# AWS KMS — Manual Setup Guide for Quantum Shield Core

> **Date**: June 2026  
> **Purpose**: Step-by-step guide to configure AWS CLI and KMS for real AWS validation  
> **Prerequisites**: AWS account with permissions to create KMS keys and IAM users

---

## 1. Install AWS CLI

### macOS (Homebrew)

```bash
brew install awscli
```

### macOS (Download)

Download from: https://awscli.amazonaws.com/AWSCLIV2.pkg

### Verify Installation

```bash
aws --version
# Expected: aws-cli/2.x.x ...
```

---

## 2. Configure AWS Credentials

### Option A: Interactive Setup (Recommended)

```bash
aws configure
```

You will be prompted for:
- `AWS Access Key ID` — from your IAM user
- `AWS Secret Access Key` — from your IAM user
- `Default region name` — e.g., `eu-west-3` (Paris) or `eu-west-1` (Ireland)
- `Default output format` — `json`

### Option B: Environment Variables (for CI/CD)

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=wJalrX...
export AWS_REGION=eu-west-3
```

### Option C: IAM Role (EC2/ECS)

If running on AWS infrastructure, assign an IAM role to the instance/task. The SDK will automatically retrieve temporary credentials.

### Verify Identity

```bash
aws sts get-caller-identity
```

Expected output (Account ID and ARN will differ):
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-user"
}
```

---

## 3. IAM Permissions Required

Create an IAM policy with the minimum required permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "kms:Encrypt",
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:CreateKey",
                "kms:CreateAlias",
                "kms:ListAliases",
                "cloudtrail:LookupEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

> **Note**: For production, restrict `Resource` to the specific CMK ARN.

---

## 4. Create a Test KMS Key

### 4.1 Create the Key

```bash
aws kms create-key \
  --description "Quantum Shield Core real AWS KMS validation key" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec SYMMETRIC_DEFAULT
```

Save the `KeyId` from the output.

### 4.2 Create an Alias

```bash
aws kms create-alias \
  --alias-name alias/quantum-shield-test \
  --target-key-id <KEY_ID_FROM_STEP_4.1>
```

> **Note**: The default configuration uses `SYMMETRIC_DEFAULT` algorithm, which works with symmetric keys. For asymmetric RSA keys, set `AWS_KMS_ENCRYPTION_ALGORITHM=RSAES_OAEP_SHA_256`.

Alternatively, create an **asymmetric RSA key** (only if you specifically need RSA):

```bash
aws kms create-key \
  --description "Quantum Shield Core RSA KMS validation key" \
  --key-usage ENCRYPT_DECRYPT \
  --key-spec RSA_4096
```

---

## 5. Test AWS KMS Directly via CLI

### 5.1 Encrypt

```bash
echo -n "quantum-shield-real-kms-test" > /tmp/plaintext.txt

aws kms encrypt \
  --key-id alias/quantum-shield-test \
  --plaintext fileb:///tmp/plaintext.txt \
  --output text \
  --query CiphertextBlob > /tmp/ciphertext.b64
```

> **Note**: For asymmetric RSA keys, add `--encryption-algorithm RSAES_OAEP_SHA_256`.

### 5.2 Decrypt

```bash
aws kms decrypt \
  --ciphertext-blob fileb://<(base64 --decode /tmp/ciphertext.b64) \
  --output text \
  --query Plaintext | base64 --decode
```

Expected output:
```
quantum-shield-real-kms-test
```

---

## 6. Test via Quantum Shield Core Provider

Once AWS CLI is configured:

```bash
cd quantum-shield-core

# Set environment variables
export AWS_KMS_KEY_ID=alias/quantum-shield-test
export AWS_REGION=eu-west-3
export KMS_PROVIDER=aws
export KMS_MAX_RETRIES=0

# Run the validation script
.venv/bin/python scripts/validate_real_aws_kms.py
```

If the script does not exist yet, create it (see `scripts/validate_real_aws_kms.py` in the project).

---

## 7. Check CloudTrail (Optional)

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=kms.amazonaws.com \
  --max-results 10
```

---

## 8. Cleanup (After Validation)

**Do not delete the test key automatically** — ask first. If you want to clean up:

```bash
# Delete the alias
aws kms delete-alias --alias-name alias/quantum-shield-test

# Schedule key deletion (default 7-day wait period)
aws kms schedule-key-deletion --key-id alias/quantum-shield-test --pending-window-in-days 7
```

---

## 9. Expected AWS Costs

| Service | Operation | Cost |
|---------|-----------|------|
| KMS | Customer managed key (symmetric) | $1/month per key |
| KMS | Encrypt/Decrypt (symmetric, free tier) | First 20,000 requests/month free |
| KMS | Encrypt/Decrypt (asymmetric RSA_4096) | ~$0.03 per 10,000 requests |
| CloudTrail | Management events | Free (first copy) |
| Total for validation | One-time test | < $2 |

---

## 10. Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `AccessDeniedException` | IAM permissions insufficient | Add `kms:Encrypt` and `kms:Decrypt` to IAM policy |
| `NotFoundException` | Wrong key ID or alias | Verify `aws kms list-aliases` |
| `InvalidKeyUsageException` | Algorithm mismatch with key type | Use `SYMMETRIC_DEFAULT` for symmetric keys, or `RSAES_OAEP_SHA_256` for RSA keys |
| `InvalidCiphertextException` | Wrong key or corrupted ciphertext | Re-encrypt with correct key |
| `Unable to locate credentials` | No AWS credentials configured | Run `aws configure` or set env vars |

---

*This guide was created as part of the Quantum Shield Core real AWS KMS validation package.*