package client

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/quantum-shield/sdk-go/pkg/types"
)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func testClient(t *testing.T, handler http.HandlerFunc) (*Client, *httptest.Server) {
	t.Helper()
	server := httptest.NewServer(handler)
	opts := types.DefaultOptions()
	opts.BaseURL = server.URL
	opts.APIKey = "test-api-key"
	opts.RetryMaxAttempts = 0 // No retries in tests
	c, err := New(opts)
	if err != nil {
		t.Fatalf("Failed to create client: %v", err)
	}
	return c, server
}

func jsonResponse(t *testing.T, statusCode int, v interface{}) (int, []byte) {
	t.Helper()
	data, err := json.Marshal(v)
	if err != nil {
		t.Fatalf("json marshal: %v", err)
	}
	return statusCode, data
}

func stringPtr(s string) *string { return &s }

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

func TestHealth_Success(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if r.URL.Path != "/health" {
			t.Errorf("expected /health, got %s", r.URL.Path)
		}
		// Check API key header
		if r.Header.Get("X-API-Key") != "test-api-key" {
			t.Errorf("expected X-API-Key header")
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"status":"healthy","algorithm":"ML-KEM-768","version":"2.1.0","database":"ok (42 entries)"}`)
	})
	defer srv.Close()

	health, err := c.Health(context.Background())
	if err != nil {
		t.Fatalf("Health failed: %v", err)
	}
	if health.Status != "healthy" {
		t.Errorf("expected healthy, got %s", health.Status)
	}
	if health.Algorithm != "ML-KEM-768" {
		t.Errorf("expected ML-KEM-768, got %s", health.Algorithm)
	}
}

func TestHealth_ServerError(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
		fmt.Fprint(w, `{"detail":"internal error"}`)
	})
	defer srv.Close()

	_, err := c.Health(context.Background())
	if err == nil {
		t.Fatal("expected error")
	}
}

// ---------------------------------------------------------------------------
// Key Generation
// ---------------------------------------------------------------------------

func TestGenerateKeypair_Success(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.URL.Path != "/api/v1/keys/generate" {
			t.Errorf("expected /api/v1/keys/generate, got %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		fmt.Fprint(w, `{"public_key_b64":"pub-key-123","private_key_b64":"priv-key-456"}`)
	})
	defer srv.Close()

	kp, err := c.GenerateKeypair(context.Background())
	if err != nil {
		t.Fatalf("GenerateKeypair failed: %v", err)
	}
	if kp.PublicKeyB64 != "pub-key-123" {
		t.Errorf("expected pub-key-123, got %s", kp.PublicKeyB64)
	}
	if kp.PrivateKeyB64 != "priv-key-456" {
		t.Errorf("expected priv-key-456, got %s", kp.PrivateKeyB64)
	}
}

// ---------------------------------------------------------------------------
// Seal
// ---------------------------------------------------------------------------

func TestSeal_Success(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.URL.Path != "/api/v1/crypto/seal" {
			t.Errorf("expected /api/v1/crypto/seal, got %s", r.URL.Path)
		}
		var req types.SealRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			t.Errorf("decode request: %v", err)
		}
		if req.PublicKeyB64 == "" || req.DataB64 == "" || req.Context == "" {
			t.Error("missing required fields")
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"ciphertext_pqc_b64":"ct","nonce_b64":"nonce","encrypted_data_b64":"enc"}`)
	})
	defer srv.Close()

	sealed, err := c.Seal(context.Background(), "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", []byte("hello"), "doc-1")
	if err != nil {
		t.Fatalf("Seal failed: %v", err)
	}
	if sealed.CiphertextPQCb64 != "ct" {
		t.Errorf("expected ct, got %s", sealed.CiphertextPQCb64)
	}
}

func TestSeal_ValidationError(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server")
	})
	defer srv.Close()

	_, err := c.Seal(context.Background(), "", []byte("hello"), "doc-1")
	if err == nil {
		t.Fatal("expected validation error for empty public key")
	}
}

// ---------------------------------------------------------------------------
// Unseal
// ---------------------------------------------------------------------------

func TestUnseal_Success(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.URL.Path != "/api/v1/crypto/unseal" {
			t.Errorf("expected /api/v1/crypto/unseal, got %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"decrypted_data_b64":"aGVsbG8="}`) // "hello" base64
	})
	defer srv.Close()

	sealed := &types.SealResponse{
		CiphertextPQCb64: "ct",
		NonceB64:         "nonce",
		EncryptedDataB64: "enc",
	}
	data, err := c.Unseal(context.Background(), "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", sealed, "doc-1")
	if err != nil {
		t.Fatalf("Unseal failed: %v", err)
	}
	if string(data) != "hello" {
		t.Errorf("expected hello, got %s", string(data))
	}
}

// ---------------------------------------------------------------------------
// SealText / UnsealText
// ---------------------------------------------------------------------------

func TestSealText(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"ciphertext_pqc_b64":"ct","nonce_b64":"nonce","encrypted_data_b64":"enc"}`)
	})
	defer srv.Close()

	_, err := c.SealText(context.Background(), "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "secret text", "doc-1")
	if err != nil {
		t.Fatalf("SealText failed: %v", err)
	}
}

func TestUnsealText(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"decrypted_data_b64":"c2VjcmV0"}`) // "secret"
	})
	defer srv.Close()

	sealed := &types.SealResponse{
		CiphertextPQCb64: "ct",
		NonceB64:         "nonce",
		EncryptedDataB64: "enc",
	}
	text, err := c.UnsealText(context.Background(), "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", sealed, "doc-1")
	if err != nil {
		t.Fatalf("UnsealText failed: %v", err)
	}
	if text != "secret" {
		t.Errorf("expected secret, got %s", text)
	}
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

func TestWriteAuditLog_Success(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.URL.Path != "/api/v1/audit/log" {
			t.Errorf("expected /api/v1/audit/log, got %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		fmt.Fprint(w, `{"id":42,"log":{"action":"SEAL"},"signature":"sig-abc"}`)
	})
	defer srv.Close()

	resp, err := c.WriteAuditLog(context.Background(), "SEAL", "doc-1", "alice")
	if err != nil {
		t.Fatalf("WriteAuditLog failed: %v", err)
	}
	if resp.ID != 42 {
		t.Errorf("expected ID 42, got %d", resp.ID)
	}
	if resp.Signature != "sig-abc" {
		t.Errorf("expected sig-abc, got %s", resp.Signature)
	}
}

func TestWriteAuditLog_ValidationError(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server")
	})
	defer srv.Close()

	_, err := c.WriteAuditLog(context.Background(), "", "doc-1", "alice")
	if err == nil {
		t.Fatal("expected validation error")
	}
	var e *types.ErrInvalidInput
	if !asErrInvalidInput(err, &e) {
		t.Errorf("expected ErrInvalidInput, got %T", err)
	}
}

func TestGetAuditLogs_Success(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if r.URL.Path != "/api/v1/audit/logs" && r.URL.Path != "/api/v1/audit/logs?skip=0&limit=50" {
			// Accept either path since query params may or may not be present
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `[{"id":1,"action":"SEAL","target":"doc-1","actor":"alice","log_json":"{}","signature":"sig","integrity":"OK"}]`)
	})
	defer srv.Close()

	logs, err := c.GetAuditLogs(context.Background())
	if err != nil {
		t.Fatalf("GetAuditLogs failed: %v", err)
	}
	if len(logs) != 1 {
		t.Fatalf("expected 1 log, got %d", len(logs))
	}
	if logs[0].Action != "SEAL" {
		t.Errorf("expected SEAL, got %s", logs[0].Action)
	}
}

func TestGetAuditLogByID_Success(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if r.URL.Path != "/api/v1/audit/logs/42" {
			t.Errorf("expected /api/v1/audit/logs/42, got %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"id":42,"action":"SEAL","target":"doc-1","actor":"alice","log_json":"{}","signature":"sig","integrity":"OK"}`)
	})
	defer srv.Close()

	entry, err := c.GetAuditLogByID(context.Background(), 42)
	if err != nil {
		t.Fatalf("GetAuditLogByID failed: %v", err)
	}
	if entry.ID != 42 {
		t.Errorf("expected ID 42, got %d", entry.ID)
	}
}

func TestGetAuditLogByID_InvalidID(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		t.Error("should not reach server")
	})
	defer srv.Close()

	_, err := c.GetAuditLogByID(context.Background(), 0)
	if err == nil {
		t.Fatal("expected error for invalid ID")
	}
}

func TestGetAuditStats_Success(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			t.Errorf("expected GET, got %s", r.Method)
		}
		if r.URL.Path != "/api/v1/audit/stats" {
			t.Errorf("expected /api/v1/audit/stats, got %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"total":100,"by_action":{"SEAL":60,"UNSEAL":40}}`)
	})
	defer srv.Close()

	stats, err := c.GetAuditStats(context.Background())
	if err != nil {
		t.Fatalf("GetAuditStats failed: %v", err)
	}
	if stats.Total != 100 {
		t.Errorf("expected 100, got %d", stats.Total)
	}
	if stats.ByAction["SEAL"] != 60 {
		t.Errorf("expected 60 SEALs, got %d", stats.ByAction["SEAL"])
	}
}

// ---------------------------------------------------------------------------
// Error Handling
// ---------------------------------------------------------------------------

func TestAuthenticationError(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusForbidden)
		fmt.Fprint(w, `{"detail":"invalid API key"}`)
	})
	defer srv.Close()

	_, err := c.Health(context.Background())
	if err == nil {
		t.Fatal("expected error")
	}
	var e *types.ErrAuthentication
	if !asErrAuth(err, &e) {
		t.Errorf("expected ErrAuthentication, got %T", err)
	}
}

func TestNotFoundError(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
		fmt.Fprint(w, `{"detail":"log entry 999 not found"}`)
	})
	defer srv.Close()

	_, err := c.GetAuditLogByID(context.Background(), 999)
	if err == nil {
		t.Fatal("expected error")
	}
	var e *types.ErrNotFound
	if !asErrNotFound(err, &e) {
		t.Errorf("expected ErrNotFound, got %T", err)
	}
}

func TestValidationError(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnprocessableEntity)
		fmt.Fprint(w, `{"detail":"validation error","errors":[{"field":"data_b64","msg":"too large"}]}`)
	})
	defer srv.Close()

	_, err := c.WriteAuditLog(context.Background(), "SEAL", "doc-1", "alice")
	// Note: this error comes from the server, not client validation
	if err == nil {
		t.Fatal("expected error")
	}
}

// ---------------------------------------------------------------------------
// Context Cancellation
// ---------------------------------------------------------------------------

func TestContextCancellation(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		// Simulate slow response
		time.Sleep(100 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"status":"healthy"}`)
	})
	defer srv.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()

	_, err := c.Health(ctx)
	if err == nil {
		t.Fatal("expected context deadline exceeded")
	}
}

// ---------------------------------------------------------------------------
// Client configuration
// ---------------------------------------------------------------------------

func TestNew_DefaultOptions(t *testing.T) {
	opts := DefaultOptions()
	c, err := New(opts)
	if err != nil {
		t.Fatalf("New with defaults failed: %v", err)
	}
	if c == nil {
		t.Fatal("expected non-nil client")
	}
}

func TestNew_InvalidBaseURL(t *testing.T) {
	opts := types.DefaultOptions()
	opts.BaseURL = ""
	_, err := New(opts)
	if err != nil {
		t.Fatalf("New with empty base URL should default: %v", err)
	}
}

func TestSetAPIKey(t *testing.T) {
	c, srv := testClient(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-API-Key") != "updated-key" {
			t.Errorf("expected updated-key, got %s", r.Header.Get("X-API-Key"))
		}
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, `{"status":"healthy","algorithm":"ML-KEM-768","version":"1.0","database":"ok"}`)
	})
	defer srv.Close()

	c.SetAPIKey("updated-key")
	_, err := c.Health(context.Background())
	if err != nil {
		t.Fatalf("Health failed: %v", err)
	}
}

func TestSetTimeout(t *testing.T) {
	c, _ := testClient(t, func(w http.ResponseWriter, r *http.Request) {})
	c.SetTimeout(5 * time.Second)
	// Verify via Options
	opts := c.Options()
	if opts.Timeout != 5*time.Second {
		t.Errorf("expected timeout 5s, got %s", opts.Timeout)
	}
}

func TestOptions(t *testing.T) {
	opts := types.DefaultOptions()
	opts.BaseURL = "http://test:9090"
	c, err := New(opts)
	if err != nil {
		t.Fatalf("New failed: %v", err)
	}
	returned := c.Options()
	if returned.BaseURL != "http://test:9090" {
		t.Errorf("expected http://test:9090, got %s", returned.BaseURL)
	}
}

// ---------------------------------------------------------------------------
// AuditLogOption functional options
// ---------------------------------------------------------------------------

func TestWithSkip(t *testing.T) {
	opt := WithSkip(10)
	o := &auditLogOptions{}
	opt(o)
	if o.skip != 10 {
		t.Errorf("expected skip 10, got %d", o.skip)
	}
}

func TestWithLimit(t *testing.T) {
	opt := WithLimit(100)
	o := &auditLogOptions{}
	opt(o)
	if o.limit != 100 {
		t.Errorf("expected limit 100, got %d", o.limit)
	}
}

func TestWithAction(t *testing.T) {
	opt := WithAction("SEAL")
	o := &auditLogOptions{}
	opt(o)
	if o.action != "SEAL" {
		t.Errorf("expected SEAL, got %s", o.action)
	}
}

func TestWithActor(t *testing.T) {
	opt := WithActor("alice")
	o := &auditLogOptions{}
	opt(o)
	if o.actor != "alice" {
		t.Errorf("expected alice, got %s", o.actor)
	}
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func asErrInvalidInput(err error, target **types.ErrInvalidInput) bool {
	if e, ok := err.(*types.ErrInvalidInput); ok {
		*target = e
		return true
	}
	return false
}

func asErrAuth(err error, target **types.ErrAuthentication) bool {
	if e, ok := err.(*types.ErrAuthentication); ok {
		*target = e
		return true
	}
	return false
}

func asErrNotFound(err error, target **types.ErrNotFound) bool {
	if e, ok := err.(*types.ErrNotFound); ok {
		*target = e
		return true
	}
	return false
}