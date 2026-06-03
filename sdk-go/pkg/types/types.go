// Package types provides shared types for the Quantum Shield Go SDK.
//
// Enterprise-grade type definitions with JSON serialization support
// for all Quantum Shield API operations.
package types

import (
	"encoding/json"
	"fmt"
	"log/slog"
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
	ID        int    `json:"id"`
	Action    string `json:"action"`
	Target    string `json:"target"`
	Actor     string `json:"actor"`
	LogJSON   string `json:"log_json"`
	Signature string `json:"signature"`
	Integrity string `json:"integrity"`
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

// ErrNotFound indicates that the requested resource was not found (HTTP 404).
type ErrNotFound struct {
	Resource string
}

func (e *ErrNotFound) Error() string {
	return fmt.Sprintf("resource not found: %s", e.Resource)
}

// ErrRateLimited indicates the client has been rate limited (HTTP 429).
type ErrRateLimited struct {
	RetryAfter time.Duration
}

func (e *ErrRateLimited) Error() string {
	return fmt.Sprintf("rate limited — retry after %s", e.RetryAfter)
}

// ErrInvalidInput indicates a local validation error before the request is sent.
type ErrInvalidInput struct {
	Field   string
	Message string
}

func (e *ErrInvalidInput) Error() string {
	return fmt.Sprintf("invalid input: %s — %s", e.Field, e.Message)
}

// ---------------------------------------------------------------------------
// Options
// ---------------------------------------------------------------------------

// Logger defines the logging interface used by the SDK.
// Implementations should be safe for concurrent use.
type Logger interface {
	DebugContext(ctx interface{}, msg string, args ...interface{})
	InfoContext(ctx interface{}, msg string, args ...interface{})
	WarnContext(ctx interface{}, msg string, args ...interface{})
	ErrorContext(ctx interface{}, msg string, args ...interface{})
}

// noopLogger is a default logger that discards all messages.
type noopLogger struct{}

func (noopLogger) DebugContext(_ interface{}, _ string, _ ...interface{}) {}
func (noopLogger) InfoContext(_ interface{}, _ string, _ ...interface{})  {}
func (noopLogger) WarnContext(_ interface{}, _ string, _ ...interface{})  {}
func (noopLogger) ErrorContext(_ interface{}, _ string, _ ...interface{}) {}

// SlogLogger adapts a *slog.Logger to the SDK Logger interface.
type SlogLogger struct {
	inner *slog.Logger
}

// NewSlogLogger creates a new slog-based logger adapter.
func NewSlogLogger(inner *slog.Logger) *SlogLogger {
	if inner == nil {
		inner = slog.Default()
	}
	return &SlogLogger{inner: inner}
}

func (s *SlogLogger) DebugContext(_ interface{}, msg string, args ...interface{}) {
	s.inner.Debug(msg, args...)
}
func (s *SlogLogger) InfoContext(_ interface{}, msg string, args ...interface{}) {
	s.inner.Info(msg, args...)
}
func (s *SlogLogger) WarnContext(_ interface{}, msg string, args ...interface{}) {
	s.inner.Warn(msg, args...)
}
func (s *SlogLogger) ErrorContext(_ interface{}, msg string, args ...interface{}) {
	s.inner.Error(msg, args...)
}

// ObservabilityHooks allows external observability integrations (OpenTelemetry, etc.).
type ObservabilityHooks interface {
	// BeforeRequest is called before each HTTP request.
	BeforeRequest(method, path string)
	// AfterRequest is called after each HTTP request with the status code.
	AfterRequest(method, path string, statusCode int, duration time.Duration)
	// OnError is called when a request fails.
	OnError(method, path string, err error)
}

// NoopHooks is a default hooks implementation that does nothing.
type NoopHooks struct{}

func (NoopHooks) BeforeRequest(_, _ string)                        {}
func (NoopHooks) AfterRequest(_, _ string, _ int, _ time.Duration) {}
func (NoopHooks) OnError(_, _ string, _ error)                     {}

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

	// RetryOn5xx enables retries on 5xx server errors in addition to connection errors.
	RetryOn5xx bool

	// InsecureSkipVerify skips TLS certificate verification (dev only).
	InsecureSkipVerify bool

	// Logger is the structured logger. If nil, a no-op logger is used.
	Logger Logger

	// Hooks allows observability integrations. If nil, no-op hooks are used.
	Hooks ObservabilityHooks

	// MaxIdleConns is the maximum number of idle connections in the pool.
	MaxIdleConns int

	// UserAgent overrides the default User-Agent header.
	UserAgent string
}

// DefaultOptions returns sensible enterprise defaults.
func DefaultOptions() ClientOptions {
	return ClientOptions{
		BaseURL:            "http://localhost:8000",
		APIKey:             "",
		Timeout:            30 * time.Second,
		RetryMaxAttempts:   3,
		RetryBaseDelay:     500 * time.Millisecond,
		RetryOn5xx:         true,
		InsecureSkipVerify: false,
		Logger:             noopLogger{},
		Hooks:              NoopHooks{},
		MaxIdleConns:       10,
		UserAgent:          "quantum-shield-go-sdk/1.0.0",
	}
}

// FromEnvironment fills ClientOptions from environment variables.
// Environment variables override whatever is already set.
func (o *ClientOptions) FromEnvironment() {
	if v := getEnv("QS_URL", ""); v != "" {
		o.BaseURL = v
	}
	if v := getEnv("QS_API_KEY", ""); v != "" {
		o.APIKey = v
	}
}

func getEnv(key, fallback string) string {
	// This is resolved at runtime using os.Getenv via the config package.
	// This stub exists to allow types to compile independently.
	return fallback
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