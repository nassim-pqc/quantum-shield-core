package validate

import (
	"strings"
	"testing"

	"github.com/quantum-shield/sdk-go/pkg/types"
)

func TestAPIKey(t *testing.T) {
	tests := []struct {
		name string
		key  string
		err  bool
	}{
		{"valid key", "my-api-key-12345", false},
		{"empty key", "", true},
		{"whitespace key", "   ", true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := APIKey(tt.key)
			if (err != nil) != tt.err {
				t.Errorf("APIKey(%q) error = %v, wantErr = %v", tt.key, err, tt.err)
			}
			if err != nil {
				var e *types.ErrInvalidInput
				if !asErrInvalidInput(err, &e) {
					t.Errorf("expected ErrInvalidInput, got %T", err)
				}
			}
		})
	}
}

func TestBaseURL(t *testing.T) {
	tests := []struct {
		name string
		url  string
		err  bool
	}{
		{"valid http", "http://localhost:8000", false},
		{"valid https", "https://api.example.com", false},
		{"empty", "", true},
		{"no scheme", "localhost:8000", true},
		{"ftp scheme", "ftp://localhost", true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := BaseURL(tt.url)
			if (err != nil) != tt.err {
				t.Errorf("BaseURL(%q) error = %v, wantErr = %v", tt.url, err, tt.err)
			}
		})
	}
}

func TestPublicKey(t *testing.T) {
	tests := []struct {
		name string
		key  string
		err  bool
	}{
		{"valid long key", strings.Repeat("A", 64), false},
		{"valid extra long key", strings.Repeat("B", 128), false},
		{"empty", "", true},
		{"too short", "short", true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := PublicKey(tt.key)
			if (err != nil) != tt.err {
				t.Errorf("PublicKey(%q) error = %v, wantErr = %v", tt.key, err, tt.err)
			}
		})
	}
}

func TestPrivateKey(t *testing.T) {
	tests := []struct {
		name string
		key  string
		err  bool
	}{
		{"valid long key", strings.Repeat("A", 64), false},
		{"empty", "", true},
		{"too short", "short", true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := PrivateKey(tt.key)
			if (err != nil) != tt.err {
				t.Errorf("PrivateKey(%q) error = %v, wantErr = %v", tt.key, err, tt.err)
			}
		})
	}
}

func TestContext(t *testing.T) {
	tests := []struct {
		name string
		ctx  string
		err  bool
	}{
		{"valid", "contract-2025-001", false},
		{"empty", "", true},
		{"too long", strings.Repeat("x", MaxContextLength+1), true},
		{"exactly max", strings.Repeat("x", MaxContextLength), false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := Context(tt.ctx)
			if (err != nil) != tt.err {
				t.Errorf("Context(%q) error = %v, wantErr = %v", tt.ctx, err, tt.err)
			}
		})
	}
}

func TestData(t *testing.T) {
	tests := []struct {
		name string
		data []byte
		err  bool
	}{
		{"valid", []byte("hello"), false},
		{"empty", []byte{}, true},
		{"nil", nil, true},
		{"too large", make([]byte, MaxPayloadBytes+1), true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := Data(tt.data)
			if (err != nil) != tt.err {
				t.Errorf("Data(%d bytes) error = %v, wantErr = %v", len(tt.data), err, tt.err)
			}
		})
	}
}

func TestAuditAction(t *testing.T) {
	tests := []struct {
		name   string
		action string
		err    bool
	}{
		{"valid", "SEAL", false},
		{"empty", "", true},
		{"too long", strings.Repeat("A", MaxActionLength+1), true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := AuditAction(tt.action)
			if (err != nil) != tt.err {
				t.Errorf("AuditAction(%q) error = %v, wantErr = %v", tt.action, err, tt.err)
			}
		})
	}
}

func TestAuditTarget(t *testing.T) {
	tests := []struct {
		name   string
		target string
		err    bool
	}{
		{"valid", "doc-123", false},
		{"empty", "", true},
		{"too long", strings.Repeat("x", MaxContextLength+1), true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := AuditTarget(tt.target)
			if (err != nil) != tt.err {
				t.Errorf("AuditTarget(%q) error = %v, wantErr = %v", tt.target, err, tt.err)
			}
		})
	}
}

func TestAuditUser(t *testing.T) {
	tests := []struct {
		name string
		user string
		err  bool
	}{
		{"valid", "alice", false},
		{"empty", "", true},
		{"too long", strings.Repeat("x", MaxUserLength+1), true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := AuditUser(tt.user)
			if (err != nil) != tt.err {
				t.Errorf("AuditUser(%q) error = %v, wantErr = %v", tt.user, err, tt.err)
			}
		})
	}
}

func TestSealRequest(t *testing.T) {
	err := SealRequest(strings.Repeat("A", 64), []byte("hello"), "doc-1")
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}

	err = SealRequest("", []byte("hello"), "doc-1")
	if err == nil {
		t.Error("expected error for empty public key")
	}

	err = SealRequest(strings.Repeat("A", 64), []byte{}, "doc-1")
	if err == nil {
		t.Error("expected error for empty data")
	}

	err = SealRequest(strings.Repeat("A", 64), []byte("hello"), "")
	if err == nil {
		t.Error("expected error for empty context")
	}
}

func TestUnsealRequest(t *testing.T) {
	err := UnsealRequest(
		strings.Repeat("A", 64),
		"ct", "nonce", "enc", "doc-1",
	)
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}

	err = UnsealRequest("", "ct", "nonce", "enc", "doc-1")
	if err == nil {
		t.Error("expected error for empty private key")
	}

	err = UnsealRequest(strings.Repeat("A", 64), "", "nonce", "enc", "doc-1")
	if err == nil {
		t.Error("expected error for empty ciphertext")
	}
}

func TestAuditWriteRequest(t *testing.T) {
	err := AuditWriteRequest("SEAL", "doc-1", "alice")
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}

	err = AuditWriteRequest("", "doc-1", "alice")
	if err == nil {
		t.Error("expected error for empty action")
	}

	err = AuditWriteRequest("SEAL", "", "alice")
	if err == nil {
		t.Error("expected error for empty target")
	}

	err = AuditWriteRequest("SEAL", "doc-1", "")
	if err == nil {
		t.Error("expected error for empty user")
	}
}

func TestIntRange(t *testing.T) {
	err := IntRange("limit", 50, 1, 500)
	if err != nil {
		t.Errorf("expected no error, got %v", err)
	}

	err = IntRange("limit", 0, 1, 500)
	if err == nil {
		t.Error("expected error for out-of-range")
	}

	err = IntRange("limit", 501, 1, 500)
	if err == nil {
		t.Error("expected error for out-of-range")
	}
}

func asErrInvalidInput(err error, target **types.ErrInvalidInput) bool {
	if e, ok := err.(*types.ErrInvalidInput); ok {
		*target = e
		return true
	}
	return false
}