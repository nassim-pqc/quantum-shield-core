// Package types provides shared types for the Quantum Shield Go SDK.
//
// Enterprise-grade type definitions with JSON serialization support
// for all Quantum Shield API operations.
package types

import (
	"encoding/json"
	"fmt"
	"time"
)

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

// HealthResponse represents the service health status.
type HealthResponse struct {
	Status    string `json:"status"`
	Algorithm string `json:"algorithm"`
	Version   string `json:"version"`
	Database  string `json:"database"`
}

// String returns a human-readable representation of the health status.
func (h HealthResponse) String() string {
	return fmt.Sprintf("Quantum Shield %s | Status: %s | Algorithm: %s | DB: %s",
		h.Version, h.Status, h.Algorithm, h.Database)
}

// ---------------------------------------------------------------------------
// Key Management
// ---------------------------------------------------------------------------

// KeyPairResponse represents a generated ML-KEM-768 key pair.
type KeyPairResponse struct {
	PublicKeyB64  string `json:"public_key_b64"`
	PrivateKeyB64 string `json:"private_key_b64"`
}

// ---------------------------------------------------------------------------
// Cryptography
// ---------------------------------------------------------------------------

// SealRequest is the payload for encrypting data (seal operation).
type SealRequest struct {
	PublicKeyB64 string `json:"public_key_b64"`
	DataB64      string `json:"data_b64"`
	Context      string `json:"context"`
}

// SealResponse represents the result of a seal operation.
type SealResponse struct {
	CiphertextPQCb64 string `json:"ciphertext_pqc_b64"`
	NonceB64         string `json:"nonce_b64"`
	EncryptedDataB64 string `json:"encrypted_data_b64"`
}

// UnsealRequest is the payload for decrypting data (unseal operation).
type UnsealRequest struct {
	PrivateKeyB64    string `json:"private_key_b64"`
	CiphertextPQCb64 string `json:"ciphertext_pqc_b64"`
	NonceB64         string `json:"nonce_b64"`
	EncryptedDataB64 string `json:"encrypted_data_b64"`
	Context          string `json:"context"`
}

// UnsealResponse represents the result of an unseal operation.
type UnsealResponse struct {
	DecryptedDataB64 string `json:"decrypted_data_b64"`
}

// ---------------------------------------------------------------------------
// Audit Trail
// ---------------------------------------------------------------------------

// AuditRequest is the payload for writing an audit log entry.
type AuditRequest struct {
	Action string `json:"action"`
	Target string `json:"target"`
	User   string `json:"user"`
}

// AuditLogEntry represents a single audit log entry with integrity verification.
type AuditLogEntry struct {
	ID         int    `json:"id"`
	Action     string `json:"action"`
	Target     string `json:"target"`
	Actor      string `json:"actor"`
	LogJSON    string `json:"log_json"`
	Signature  string `json:"signature"`
	Integrity  string `json:"integrity"`
}

// AuditWriteResponse represents the response after writing an audit log.
type AuditWriteResponse struct {
	ID        int                    `json:"id"`
	Log       map[string]interface{} `json:"log"`
	Signature string                 `json:"signature"`
}

// AuditStats represents audit trail statistics.
type AuditStats struct {
	Total    int            `json:"total"`
	ByAction map[string]int `json:"by_action"`
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

// APIError represents an error returned by the Quantum Shield API.
type APIError struct {
	StatusCode int    `json:"-"`
	Detail     string `json:"detail"`
	Message    string `json:"message,omitempty"`
}

func (e *APIError) Error() string {
	if e.Message != "" {
		return fmt.Sprintf("Quantum Shield API error (%d): %s — %s", e.StatusCode, e.Message, e.Detail)
	}
	return fmt.Sprintf("Quantum Shield API error (%d): %s", e.StatusCode, e.Detail)
}

// ---------------------------------------------------------------------------
// SDK Error Types
// ---------------------------------------------------------------------------

// ErrAuthentication indicates an authentication failure.
type ErrAuthentication struct {
	Message string
}

func (e *ErrAuthentication) Error() string {
	return fmt.Sprintf("authentication failed: %s", e.Message)
}

// ErrAuthorization indicates insufficient permissions.
type ErrAuthorization struct {
	Required []string
}

func (e *ErrAuthorization) Error() string {
	return fmt.Sprintf("insufficient permissions — requires: %v", e.Required)
}

// ErrValidation indicates a request validation error.
type ErrValidation struct {
	Errors []ValidationError `json:"errors,omitempty"`
}

type ValidationError struct {
	Field string `json:"field,omitempty"`
	Msg   string `json:"msg,omitempty"`
}

func (e *ErrValidation) Error() string {
	return fmt.Sprintf("validation error: %+v", e.Errors)
}

// ErrServiceUnavailable indicates the service is not reachable.
type ErrServiceUnavailable struct {
	Endpoint string
	Err      error
}

func (e *ErrServiceUnavailable) Error() string {
	return fmt.Sprintf("service unavailable at %s: %v", e.Endpoint, e.Err)
}

func (e *ErrServiceUnavailable) Unwrap() error {
	return e.Err
}

// ---------------------------------------------------------------------------
// Options
// ---------------------------------------------------------------------------

// ClientOptions configures the Quantum Shield client behaviour.
type ClientOptions struct {
	// BaseURL is the Quantum Shield service URL.
	BaseURL string

	// APIKey is the authentication key (X-API-Key header).
	APIKey string

	// Timeout is the HTTP client timeout duration.
	Timeout time.Duration

	// RetryMaxAttempts is the maximum number of retry attempts.
	RetryMaxAttempts int

	// RetryBaseDelay is the base delay between retries (exponential backoff).
	RetryBaseDelay time.Duration

	// InsecureSkipVerify skips TLS certificate verification (dev only).
	InsecureSkipVerify bool
}

// DefaultOptions returns sensible enterprise defaults.
func DefaultOptions() ClientOptions {
	return ClientOptions{
		BaseURL:          "http://localhost:8000",
		APIKey:           "",
		Timeout:          30 * time.Second,
		RetryMaxAttempts: 3,
		RetryBaseDelay:   500 * time.Millisecond,
		InsecureSkipVerify: false,
	}
}

// ---------------------------------------------------------------------------
// Audit Log (structured)
// ---------------------------------------------------------------------------

// AuditLog represents a structured audit log entry for local use.
type AuditLog struct {
	Timestamp  time.Time `json:"timestamp"`
	Action     string    `json:"action"`
	Target     string    `json:"target"`
	User       string    `json:"user"`
	KeyVersion string    `json:"key_version"`
}

// ToJSON serializes the audit log to JSON bytes.
func (l *AuditLog) ToJSON() ([]byte, error) {
	return json.Marshal(l)
}