package types

import (
	"context"
	"testing"
	"time"
)

func TestHealthResponse_String(t *testing.T) {
	h := HealthResponse{
		Status:    "healthy",
		Algorithm: "ML-KEM-768",
		Version:   "2.1.0",
		Database:  "ok (42 audit entries)",
	}
	s := h.String()
	if s != "Quantum Shield 2.1.0 | Status: healthy | Algorithm: ML-KEM-768 | DB: ok (42 audit entries)" {
		t.Errorf("unexpected string: %s", s)
	}
}

func TestDefaultOptions(t *testing.T) {
	opts := DefaultOptions()
	if opts.BaseURL != "http://localhost:8000" {
		t.Errorf("expected default BaseURL, got %s", opts.BaseURL)
	}
	if opts.Timeout != 30*time.Second {
		t.Errorf("expected default Timeout, got %s", opts.Timeout)
	}
	if opts.RetryMaxAttempts != 3 {
		t.Errorf("expected default RetryMaxAttempts, got %d", opts.RetryMaxAttempts)
	}
	if opts.RetryBaseDelay != 500*time.Millisecond {
		t.Errorf("expected default RetryBaseDelay, got %s", opts.RetryBaseDelay)
	}
	if !opts.RetryOn5xx {
		t.Error("expected RetryOn5xx to be true by default")
	}
	if opts.InsecureSkipVerify {
		t.Error("expected InsecureSkipVerify to be false by default")
	}
	if opts.Logger == nil {
		t.Error("expected Logger to be non-nil")
	}
	if opts.Hooks == nil {
		t.Error("expected Hooks interface to be non-nil")
	}
}

func TestAPIError_Error(t *testing.T) {
	err := &APIError{StatusCode: 422, Detail: "validation failed"}
	if err.Error() != "Quantum Shield API error (422): validation failed" {
		t.Errorf("unexpected error: %s", err.Error())
	}

	err.Message = "Bad Request"
	if err.Error() != "Quantum Shield API error (422): Bad Request — validation failed" {
		t.Errorf("unexpected error with message: %s", err.Error())
	}
}

func TestErrAuthentication_Error(t *testing.T) {
	err := &ErrAuthentication{Message: "invalid API key"}
	if err.Error() != "authentication failed: invalid API key" {
		t.Errorf("unexpected error: %s", err.Error())
	}
}

func TestErrAuthorization_Error(t *testing.T) {
	err := &ErrAuthorization{Required: []string{"operator"}}
	if err.Error() != "insufficient permissions — requires: [operator]" {
		t.Errorf("unexpected error: %s", err.Error())
	}
}

func TestErrValidation_Error(t *testing.T) {
	err := &ErrValidation{Errors: []ValidationError{{Field: "data_b64", Msg: "too large"}}}
	if err.Error() != "validation error: [{Field:data_b64 Msg:too large}]" {
		t.Errorf("unexpected error: %s", err.Error())
	}
}

func TestErrServiceUnavailable_Error(t *testing.T) {
	err := &ErrServiceUnavailable{Endpoint: "http://localhost:8000", Err: context.DeadlineExceeded}
	if err.Error() != "service unavailable at http://localhost:8000: context deadline exceeded" {
		t.Errorf("unexpected error: %s", err.Error())
	}
	if err.Unwrap() != context.DeadlineExceeded {
		t.Error("Unwrap should return the wrapped error")
	}
}

func TestErrNotFound_Error(t *testing.T) {
	err := &ErrNotFound{Resource: "log entry 42"}
	if err.Error() != "resource not found: log entry 42" {
		t.Errorf("unexpected error: %s", err.Error())
	}
}

func TestErrRateLimited_Error(t *testing.T) {
	err := &ErrRateLimited{RetryAfter: 5 * time.Second}
	if err.Error() != "rate limited — retry after 5s" {
		t.Errorf("unexpected error: %s", err.Error())
	}
}

func TestErrInvalidInput_Error(t *testing.T) {
	err := &ErrInvalidInput{Field: "api_key", Message: "must not be empty"}
	if err.Error() != "invalid input: api_key — must not be empty" {
		t.Errorf("unexpected error: %s", err.Error())
	}
}

func TestKeyPairResponse(t *testing.T) {
	kp := KeyPairResponse{PublicKeyB64: "pub", PrivateKeyB64: "priv"}
	if kp.PublicKeyB64 != "pub" || kp.PrivateKeyB64 != "priv" {
		t.Error("KeyPairResponse fields not set correctly")
	}
}

func TestSealResponse(t *testing.T) {
	s := SealResponse{
		CiphertextPQCb64: "ct",
		NonceB64:         "nonce",
		EncryptedDataB64: "enc",
	}
	if s.CiphertextPQCb64 != "ct" || s.NonceB64 != "nonce" || s.EncryptedDataB64 != "enc" {
		t.Error("SealResponse fields not set correctly")
	}
}

func TestAuditLogEntry(t *testing.T) {
	e := AuditLogEntry{
		ID: 1, Action: "SEAL", Target: "doc-123", Actor: "go-sdk",
		Integrity: "OK",
	}
	if e.ID != 1 || e.Action != "SEAL" || e.Integrity != "OK" {
		t.Error("AuditLogEntry fields not set correctly")
	}
}

func TestAuditStats(t *testing.T) {
	s := AuditStats{Total: 100, ByAction: map[string]int{"SEAL": 60, "UNSEAL": 40}}
	if s.Total != 100 || s.ByAction["SEAL"] != 60 {
		t.Error("AuditStats fields not set correctly")
	}
}

func TestAuditLog_ToJSON(t *testing.T) {
	l := &AuditLog{
		Timestamp:  time.Date(2026, 3, 6, 12, 0, 0, 0, time.UTC),
		Action:     "TEST",
		Target:     "doc-1",
		User:       "tester",
		KeyVersion: "v1",
	}
	data, err := l.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}
	if len(data) == 0 {
		t.Fatal("expected non-empty JSON")
	}
}

func TestNewSlogLogger(t *testing.T) {
	l := NewSlogLogger(nil)
	if l == nil {
		t.Fatal("expected non-nil logger")
	}
	// Should not panic
	l.DebugContext(nil, "test")
	l.InfoContext(nil, "test")
	l.WarnContext(nil, "test")
	l.ErrorContext(nil, "test")
}

func TestNoopHooks(t *testing.T) {
	h := NoopHooks{}
	// Should not panic
	h.BeforeRequest("GET", "/health")
	h.AfterRequest("GET", "/health", 200, time.Second)
	h.OnError("GET", "/health", nil)
}
