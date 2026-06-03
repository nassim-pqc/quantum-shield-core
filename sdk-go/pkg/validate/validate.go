// Package validate provides input validation helpers for the Quantum Shield Go SDK.
//
// All validation is performed client-side before sending API requests, ensuring
// that invalid data is caught early without consuming network resources.
package validate

import (
	"fmt"
	"strings"

	"github.com/quantum-shield/sdk-go/pkg/types"
)

const (
	// MaxContextLength is the maximum allowed length for context/identifier fields.
	MaxContextLength = 128

	// MaxActionLength is the maximum allowed length for audit action strings.
	MaxActionLength = 64

	// MaxUserLength is the maximum allowed length for user identifier strings.
	MaxUserLength = 64

	// MinKeyLength is the minimum length for a valid Base64-encoded Kyber768 key.
	MinKeyLength = 64

	// MaxPayloadBytes is the maximum decoded payload size (10MB).
	MaxPayloadBytes = 10 * 1024 * 1024
)

// APIKey validates an API key string.
func APIKey(key string) error {
	if strings.TrimSpace(key) == "" {
		return &types.ErrInvalidInput{
			Field:   "api_key",
			Message: "API key must not be empty",
		}
	}
	return nil
}

// BaseURL validates a base URL string.
func BaseURL(url string) error {
	if strings.TrimSpace(url) == "" {
		return &types.ErrInvalidInput{
			Field:   "base_url",
			Message: "base URL must not be empty",
		}
	}
	if !strings.HasPrefix(url, "http://") && !strings.HasPrefix(url, "https://") {
		return &types.ErrInvalidInput{
			Field:   "base_url",
			Message: "base URL must start with http:// or https://",
		}
	}
	return nil
}

// PublicKey validates a Base64-encoded Kyber768 public key.
func PublicKey(key string) error {
	if strings.TrimSpace(key) == "" {
		return &types.ErrInvalidInput{
			Field:   "public_key",
			Message: "public key must not be empty",
		}
	}
	if len(key) < MinKeyLength {
		return &types.ErrInvalidInput{
			Field:   "public_key",
			Message: fmt.Sprintf("public key too short (got %d chars, expected >= %d)", len(key), MinKeyLength),
		}
	}
	return nil
}

// PrivateKey validates a Base64-encoded Kyber768 private key.
func PrivateKey(key string) error {
	if strings.TrimSpace(key) == "" {
		return &types.ErrInvalidInput{
			Field:   "private_key",
			Message: "private key must not be empty",
		}
	}
	if len(key) < MinKeyLength {
		return &types.ErrInvalidInput{
			Field:   "private_key",
			Message: fmt.Sprintf("private key too short (got %d chars, expected >= %d)", len(key), MinKeyLength),
		}
	}
	return nil
}

// Context validates a context/AAD string.
func Context(ctx string) error {
	if strings.TrimSpace(ctx) == "" {
		return &types.ErrInvalidInput{
			Field:   "context",
			Message: "context must not be empty",
		}
	}
	if len(ctx) > MaxContextLength {
		return &types.ErrInvalidInput{
			Field:   "context",
			Message: fmt.Sprintf("context too long (got %d chars, max %d)", len(ctx), MaxContextLength),
		}
	}
	return nil
}

// Data validates plaintext data size.
func Data(data []byte) error {
	if len(data) == 0 {
		return &types.ErrInvalidInput{
			Field:   "data",
			Message: "data must not be empty",
		}
	}
	if len(data) > MaxPayloadBytes {
		return &types.ErrInvalidInput{
			Field:   "data",
			Message: fmt.Sprintf("data too large (got %d bytes, max %d)", len(data), MaxPayloadBytes),
		}
	}
	return nil
}

// AuditAction validates an audit action string.
func AuditAction(action string) error {
	if strings.TrimSpace(action) == "" {
		return &types.ErrInvalidInput{
			Field:   "action",
			Message: "audit action must not be empty",
		}
	}
	if len(action) > MaxActionLength {
		return &types.ErrInvalidInput{
			Field:   "action",
			Message: fmt.Sprintf("audit action too long (got %d chars, max %d)", len(action), MaxActionLength),
		}
	}
	return nil
}

// AuditTarget validates an audit target string.
func AuditTarget(target string) error {
	if strings.TrimSpace(target) == "" {
		return &types.ErrInvalidInput{
			Field:   "target",
			Message: "audit target must not be empty",
		}
	}
	if len(target) > MaxContextLength {
		return &types.ErrInvalidInput{
			Field:   "target",
			Message: fmt.Sprintf("audit target too long (got %d chars, max %d)", len(target), MaxContextLength),
		}
	}
	return nil
}

// AuditUser validates an audit user string.
func AuditUser(user string) error {
	if strings.TrimSpace(user) == "" {
		return &types.ErrInvalidInput{
			Field:   "user",
			Message: "audit user must not be empty",
		}
	}
	if len(user) > MaxUserLength {
		return &types.ErrInvalidInput{
			Field:   "user",
			Message: fmt.Sprintf("audit user too long (got %d chars, max %d)", len(user), MaxUserLength),
		}
	}
	return nil
}

// SealRequest validates all fields in a seal operation.
func SealRequest(publicKeyB64 string, data []byte, context string) error {
	if err := PublicKey(publicKeyB64); err != nil {
		return err
	}
	if err := Data(data); err != nil {
		return err
	}
	if err := Context(context); err != nil {
		return err
	}
	return nil
}

// UnsealRequest validates all fields in an unseal operation.
func UnsealRequest(privateKeyB64, ciphertextPQCb64, nonceB64, encryptedDataB64, context string) error {
	if err := PrivateKey(privateKeyB64); err != nil {
		return err
	}
	if strings.TrimSpace(ciphertextPQCb64) == "" {
		return &types.ErrInvalidInput{
			Field:   "ciphertext_pqc_b64",
			Message: "ciphertext must not be empty",
		}
	}
	if strings.TrimSpace(nonceB64) == "" {
		return &types.ErrInvalidInput{
			Field:   "nonce_b64",
			Message: "nonce must not be empty",
		}
	}
	if strings.TrimSpace(encryptedDataB64) == "" {
		return &types.ErrInvalidInput{
			Field:   "encrypted_data_b64",
			Message: "encrypted data must not be empty",
		}
	}
	if err := Context(context); err != nil {
		return err
	}
	return nil
}

// AuditWriteRequest validates all fields in an audit write operation.
func AuditWriteRequest(action, target, user string) error {
	if err := AuditAction(action); err != nil {
		return err
	}
	if err := AuditTarget(target); err != nil {
		return err
	}
	if err := AuditUser(user); err != nil {
		return err
	}
	return nil
}

// IntRange validates that an integer is within the given range [min, max].
func IntRange(field string, value, min, max int) error {
	if value < min || value > max {
		return &types.ErrInvalidInput{
			Field:   field,
			Message: fmt.Sprintf("must be between %d and %d (got %d)", min, max, value),
		}
	}
	return nil
}