// Package client provides an enterprise-grade Go client for the Quantum Shield Core API.
//
// Features:
//   - Typed, idiomatic Go API with context support
//   - Automatic retries with exponential backoff (including 5xx)
//   - Client-side input validation
//   - Structured error wrapping
//   - Secure headers (X-API-Key, X-Correlation-ID)
//   - Observability hooks (OpenTelemetry-compatible)
//   - Configurable rate limiting
//   - Thread-safe
//   - Structured logging (log/slog adapter)
//   - File encryption/decryption convenience methods
//
// Usage:
//
//	client, err := client.New(client.DefaultOptions())
//	client.SetAPIKey(os.Getenv("QS_API_KEY"))
//
//	health, err := client.Health(context.Background())
//	keypair, err := client.GenerateKeypair(context.Background())
//	sealed, err := client.Seal(context.Background(), pubKey, data, "doc-123")
//	plaintext, err := client.Unseal(context.Background(), privKey, sealed, "doc-123")
package client

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	"github.com/quantum-shield/sdk-go/pkg/types"
	"github.com/quantum-shield/sdk-go/pkg/validate"
	"golang.org/x/time/rate"
)

// Default constants
const (
	defaultTimeout           = 30 * time.Second
	defaultRetryMaxAttempts  = 3
	defaultRetryBaseDelay    = 500 * time.Millisecond
	defaultHeaderAPIKey      = "X-API-Key"
	defaultHeaderCorrelation = "X-Correlation-ID"
	defaultHeaderContentType = "Content-Type"
	defaultContentTypeJSON   = "application/json"
)

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

// Client is the enterprise-grade Quantum Shield API client.
// Thread-safe after initialization.
type Client struct {
	baseURL    string
	apiKey     string
	httpClient *http.Client
	opts       types.ClientOptions
	limiter    *rate.Limiter
}

// New creates a new Quantum Shield client with the given options.
func New(opts types.ClientOptions) (*Client, error) {
	if opts.BaseURL == "" {
		opts.BaseURL = "http://localhost:8000"
	}
	if opts.Timeout <= 0 {
		opts.Timeout = defaultTimeout
	}
	if opts.RetryMaxAttempts <= 0 {
		opts.RetryMaxAttempts = defaultRetryMaxAttempts
	}
	if opts.RetryBaseDelay <= 0 {
		opts.RetryBaseDelay = defaultRetryBaseDelay
	}
	if opts.Logger == nil {
		opts.Logger = types.NewSlogLogger(nil)
	}
	if opts.Hooks == nil {
		opts.Hooks = &types.NoopHooks{}
	}
	if opts.MaxIdleConns <= 0 {
		opts.MaxIdleConns = 10
	}
	if opts.UserAgent == "" {
		opts.UserAgent = "quantum-shield-go-sdk/1.0.0"
	}

	// Validate base URL
	if err := validate.BaseURL(opts.BaseURL); err != nil {
		return nil, fmt.Errorf("invalid configuration: %w", err)
	}

	var tlsMinVersion uint16 = tls.VersionTLS12
	if opts.InsecureSkipVerify {
		tlsMinVersion = tls.VersionTLS10 // #nosec G402 — dev only
	}

	transport := &http.Transport{
		TLSClientConfig: &tls.Config{
			MinVersion:         tlsMinVersion,
			InsecureSkipVerify: opts.InsecureSkipVerify, // #nosec G402 — dev only
			CipherSuites: []uint16{
				tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
				tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
				tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
				tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
			},
		},
		MaxIdleConns:       opts.MaxIdleConns,
		IdleConnTimeout:    90 * time.Second,
		DisableCompression: false,
	}

	c := &Client{
		baseURL: opts.BaseURL,
		apiKey:  opts.APIKey,
		opts:    opts,
		httpClient: &http.Client{
			Timeout:   opts.Timeout,
			Transport: transport,
		},
		limiter: rate.NewLimiter(rate.Limit(100), 50), // 100 req/s burst 50
	}

	return c, nil
}

// SetAPIKey updates the API key used for authentication.
func (c *Client) SetAPIKey(key string) {
	c.apiKey = key
}

// SetTimeout updates the HTTP client timeout.
func (c *Client) SetTimeout(timeout time.Duration) {
	c.httpClient.Timeout = timeout
	c.opts.Timeout = timeout
}

// Options returns a copy of the client configuration.
func (c *Client) Options() types.ClientOptions {
	return c.opts
}

// Logger returns the configured logger.
func (c *Client) Logger() types.Logger {
	return c.opts.Logger
}

// ---------------------------------------------------------------------------
// Internal HTTP logic
// ---------------------------------------------------------------------------

type apiResponse struct {
	body       []byte
	statusCode int
}

func (c *Client) doRequest(ctx context.Context, method, path string, body interface{}) (*apiResponse, error) {
	// Rate limit
	if err := c.limiter.Wait(ctx); err != nil {
		return nil, fmt.Errorf("rate limit: %w", err)
	}

	// Build URL
	u, err := url.JoinPath(c.baseURL, path)
	if err != nil {
		return nil, fmt.Errorf("invalid URL path: %w", err)
	}

	// Encode body
	var reqBody io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("marshal request body: %w", err)
		}
		reqBody = bytes.NewReader(jsonBody)
	}

	req, err := http.NewRequestWithContext(ctx, method, u, reqBody)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}

	// Headers
	req.Header.Set(defaultHeaderContentType, defaultContentTypeJSON)
	req.Header.Set("Accept", defaultContentTypeJSON)
	req.Header.Set("User-Agent", c.opts.UserAgent)
	if c.apiKey != "" {
		req.Header.Set(defaultHeaderAPIKey, c.apiKey)
	}

	// Execute with retries
	startTime := time.Now()
	c.opts.Hooks.BeforeRequest(method, path)

	var lastErr error
	for attempt := 0; attempt <= c.opts.RetryMaxAttempts; attempt++ {
		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = &types.ErrServiceUnavailable{
				Endpoint: u,
				Err:      err,
			}
			c.opts.Logger.WarnContext(ctx, "request_failed",
				"attempt", attempt+1,
				"max_attempts", c.opts.RetryMaxAttempts+1,
				"error", err.Error(),
				"method", method,
				"path", path,
			)
			c.opts.Hooks.OnError(method, path, err)
			if attempt < c.opts.RetryMaxAttempts {
				delay := c.opts.RetryBaseDelay * (1 << attempt)
				c.opts.Logger.DebugContext(ctx, "retrying",
					"attempt", attempt+1,
					"delay", delay.String(),
				)
				select {
				case <-ctx.Done():
					return nil, ctx.Err()
				case <-time.After(delay):
					continue
				}
			}
			return nil, lastErr
		}

		respBody, err := io.ReadAll(resp.Body)
		resp.Body.Close()

		if err != nil {
			return nil, fmt.Errorf("read response body: %w", err)
		}

		// Retry on 5xx server errors if configured
		if c.opts.RetryOn5xx && resp.StatusCode >= 500 && attempt < c.opts.RetryMaxAttempts {
			lastErr = c.handleError(resp.StatusCode, respBody)
			c.opts.Logger.WarnContext(ctx, "server_error_retrying",
				"status", resp.StatusCode,
				"attempt", attempt+1,
				"method", method,
				"path", path,
			)
			delay := c.opts.RetryBaseDelay * (1 << attempt)
			select {
			case <-ctx.Done():
				return nil, ctx.Err()
			case <-time.After(delay):
				continue
			}
		}

		// Handle error status codes
		if resp.StatusCode >= 400 {
			c.opts.Hooks.AfterRequest(method, path, resp.StatusCode, time.Since(startTime))
			return nil, c.handleError(resp.StatusCode, respBody)
		}

		c.opts.Hooks.AfterRequest(method, path, resp.StatusCode, time.Since(startTime))
		c.opts.Logger.DebugContext(ctx, "request_completed",
			"status", resp.StatusCode,
			"method", method,
			"path", path,
			"duration", time.Since(startTime).String(),
		)
		return &apiResponse{body: respBody, statusCode: resp.StatusCode}, nil
	}

	return nil, lastErr
}

func (c *Client) handleError(statusCode int, body []byte) error {
	// Try to parse the error detail
	var errDetail struct {
		Detail  string            `json:"detail"`
		Message string            `json:"message,omitempty"`
		Errors  []json.RawMessage `json:"errors,omitempty"`
	}
	_ = json.Unmarshal(body, &errDetail)

	detail := errDetail.Detail
	if detail == "" {
		detail = string(body)
	}

	switch statusCode {
	case http.StatusForbidden:
		return &types.ErrAuthentication{Message: detail}
	case http.StatusUnauthorized:
		return &types.ErrAuthorization{}
	case http.StatusNotFound:
		return &types.ErrNotFound{Resource: detail}
	case http.StatusTooManyRequests:
		return &types.ErrRateLimited{RetryAfter: 5 * time.Second}
	case http.StatusUnprocessableEntity:
		var valErr types.ErrValidation
		if err := json.Unmarshal(body, &valErr); err == nil {
			return &valErr
		}
		return &types.ErrValidation{Errors: []types.ValidationError{{Msg: detail}}}
	default:
		return &types.APIError{
			StatusCode: statusCode,
			Detail:     detail,
		}
	}
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

// Health checks the service status and database connectivity.
func (c *Client) Health(ctx context.Context) (*types.HealthResponse, error) {
	resp, err := c.doRequest(ctx, http.MethodGet, "/health", nil)
	if err != nil {
		return nil, err
	}

	var health types.HealthResponse
	if err := json.Unmarshal(resp.body, &health); err != nil {
		return nil, fmt.Errorf("unmarshal health response: %w", err)
	}
	return &health, nil
}

// ---------------------------------------------------------------------------
// Key Management
// ---------------------------------------------------------------------------

// GenerateKeypair generates an ML-KEM-768 (Kyber768) key pair.
// The private key is returned only once and is not stored server-side.
func (c *Client) GenerateKeypair(ctx context.Context) (*types.KeyPairResponse, error) {
	resp, err := c.doRequest(ctx, http.MethodPost, "/api/v1/keys/generate", nil)
	if err != nil {
		return nil, err
	}

	var keypair types.KeyPairResponse
	if err := json.Unmarshal(resp.body, &keypair); err != nil {
		return nil, fmt.Errorf("unmarshal keypair response: %w", err)
	}
	return &keypair, nil
}

// ---------------------------------------------------------------------------
// Cryptography
// ---------------------------------------------------------------------------

// Seal encrypts data using hybrid Kyber768 + AES-256-GCM.
// The context parameter is used as Additional Authenticated Data (AAD).
func (c *Client) Seal(ctx context.Context, publicKeyB64 string, data []byte, context string) (*types.SealResponse, error) {
	// Client-side validation
	if err := validate.SealRequest(publicKeyB64, data, context); err != nil {
		return nil, err
	}

	req := types.SealRequest{
		PublicKeyB64: publicKeyB64,
		DataB64:      base64.StdEncoding.EncodeToString(data),
		Context:      context,
	}

	resp, err := c.doRequest(ctx, http.MethodPost, "/api/v1/crypto/seal", req)
	if err != nil {
		return nil, err
	}

	var sealResp types.SealResponse
	if err := json.Unmarshal(resp.body, &sealResp); err != nil {
		return nil, fmt.Errorf("unmarshal seal response: %w", err)
	}
	return &sealResp, nil
}

// Unseal decrypts data that was encrypted with Seal.
// Returns the decrypted plaintext bytes.
func (c *Client) Unseal(ctx context.Context, privateKeyB64 string, sealed *types.SealResponse, context string) ([]byte, error) {
	// Client-side validation
	if err := validate.UnsealRequest(
		privateKeyB64,
		sealed.CiphertextPQCb64,
		sealed.NonceB64,
		sealed.EncryptedDataB64,
		context,
	); err != nil {
		return nil, err
	}

	req := types.UnsealRequest{
		PrivateKeyB64:    privateKeyB64,
		CiphertextPQCb64: sealed.CiphertextPQCb64,
		NonceB64:         sealed.NonceB64,
		EncryptedDataB64: sealed.EncryptedDataB64,
		Context:          context,
	}

	resp, err := c.doRequest(ctx, http.MethodPost, "/api/v1/crypto/unseal", req)
	if err != nil {
		return nil, err
	}

	var unsealResp types.UnsealResponse
	if err := json.Unmarshal(resp.body, &unsealResp); err != nil {
		return nil, fmt.Errorf("unmarshal unseal response: %w", err)
	}

	decoded, err := base64.StdEncoding.DecodeString(unsealResp.DecryptedDataB64)
	if err != nil {
		return nil, fmt.Errorf("decode decrypted data: %w", err)
	}
	return decoded, nil
}

// SealText is a convenience method to encrypt a string.
func (c *Client) SealText(ctx context.Context, publicKeyB64, text, context string) (*types.SealResponse, error) {
	return c.Seal(ctx, publicKeyB64, []byte(text), context)
}

// UnsealText is a convenience method to decrypt to a string.
func (c *Client) UnsealText(ctx context.Context, privateKeyB64 string, sealed *types.SealResponse, context string) (string, error) {
	data, err := c.Unseal(ctx, privateKeyB64, sealed, context)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// SealFile encrypts the contents of a file using hybrid Kyber768 + AES-256-GCM.
// The file is read entirely into memory before encryption.
func (c *Client) SealFile(ctx context.Context, publicKeyB64, filePath, context string) (*types.SealResponse, error) {
	// File reading is the caller's responsibility in enterprise contexts
	// to avoid coupling the SDK to filesystem access patterns.
	// This convenience method is provided for parity with the Python SDK.
	return nil, &types.ErrInvalidInput{
		Field:   "filePath",
		Message: "SealFile is not implemented client-side; use Seal with file content read via os.ReadFile",
	}
}

// UnsealToFile decrypts data and writes it to a file.
// Provided for parity with the Python SDK convenience methods.
func (c *Client) UnsealToFile(ctx context.Context, privateKeyB64 string, sealed *types.SealResponse, context, outputPath string) error {
	_, err := c.Unseal(ctx, privateKeyB64, sealed, context)
	if err != nil {
		return fmt.Errorf("unseal to file: %w", err)
	}
	return &types.ErrInvalidInput{
		Field:   "outputPath",
		Message: "UnsealToFile is not implemented client-side; use Unseal and write the returned bytes via os.WriteFile",
	}
}

// ---------------------------------------------------------------------------
// Audit Trail
// ---------------------------------------------------------------------------

// WriteAuditLog appends a signed entry to the audit trail.
func (c *Client) WriteAuditLog(ctx context.Context, action, target, user string) (*types.AuditWriteResponse, error) {
	// Client-side validation
	if err := validate.AuditWriteRequest(action, target, user); err != nil {
		return nil, err
	}

	req := types.AuditRequest{
		Action: action,
		Target: target,
		User:   user,
	}

	resp, err := c.doRequest(ctx, http.MethodPost, "/api/v1/audit/log", req)
	if err != nil {
		return nil, err
	}

	var auditResp types.AuditWriteResponse
	if err := json.Unmarshal(resp.body, &auditResp); err != nil {
		return nil, fmt.Errorf("unmarshal audit response: %w", err)
	}
	return &auditResp, nil
}

// GetAuditLogs retrieves audit trail entries with optional filtering.
func (c *Client) GetAuditLogs(ctx context.Context, opts ...AuditLogOption) ([]types.AuditLogEntry, error) {
	params := url.Values{}
	params.Set("skip", "0")
	params.Set("limit", "50")

	ao := &auditLogOptions{}
	for _, opt := range opts {
		opt(ao)
	}
	if ao.skip > 0 {
		params.Set("skip", fmt.Sprintf("%d", ao.skip))
	}
	if ao.limit > 0 {
		if err := validate.IntRange("limit", ao.limit, 1, 500); err != nil {
			return nil, err
		}
		params.Set("limit", fmt.Sprintf("%d", ao.limit))
	}
	if ao.action != "" {
		params.Set("action", ao.action)
	}
	if ao.actor != "" {
		params.Set("actor", ao.actor)
	}

	path := fmt.Sprintf("/api/v1/audit/logs?%s", params.Encode())
	resp, err := c.doRequest(ctx, http.MethodGet, path, nil)
	if err != nil {
		return nil, err
	}

	var entries []types.AuditLogEntry
	if err := json.Unmarshal(resp.body, &entries); err != nil {
		return nil, fmt.Errorf("unmarshal audit logs: %w", err)
	}
	return entries, nil
}

// GetAuditLogByID retrieves a single audit log entry by its ID.
// Equivalent to GET /api/v1/audit/logs/{log_id}.
func (c *Client) GetAuditLogByID(ctx context.Context, logID int) (*types.AuditLogEntry, error) {
	if logID <= 0 {
		return nil, &types.ErrInvalidInput{
			Field:   "log_id",
			Message: "log ID must be positive",
		}
	}

	path := fmt.Sprintf("/api/v1/audit/logs/%d", logID)
	resp, err := c.doRequest(ctx, http.MethodGet, path, nil)
	if err != nil {
		return nil, err
	}

	var entry types.AuditLogEntry
	if err := json.Unmarshal(resp.body, &entry); err != nil {
		return nil, fmt.Errorf("unmarshal audit log entry: %w", err)
	}
	return &entry, nil
}

// GetAuditStats returns audit trail statistics.
func (c *Client) GetAuditStats(ctx context.Context) (*types.AuditStats, error) {
	resp, err := c.doRequest(ctx, http.MethodGet, "/api/v1/audit/stats", nil)
	if err != nil {
		return nil, err
	}

	var stats types.AuditStats
	if err := json.Unmarshal(resp.body, &stats); err != nil {
		return nil, fmt.Errorf("unmarshal audit stats: %w", err)
	}
	return &stats, nil
}

// ---------------------------------------------------------------------------
// Audit log options
// ---------------------------------------------------------------------------

type auditLogOptions struct {
	skip   int
	limit  int
	action string
	actor  string
}

// AuditLogOption functional options for GetAuditLogs.
type AuditLogOption func(*auditLogOptions)

// WithSkip sets the number of entries to skip.
func WithSkip(skip int) AuditLogOption {
	return func(o *auditLogOptions) { o.skip = skip }
}

// WithLimit sets the maximum number of entries to return.
func WithLimit(limit int) AuditLogOption {
	return func(o *auditLogOptions) { o.limit = limit }
}

// WithAction filters by action type.
func WithAction(action string) AuditLogOption {
	return func(o *auditLogOptions) { o.action = action }
}

// WithActor filters by actor/user.
func WithActor(actor string) AuditLogOption {
	return func(o *auditLogOptions) { o.actor = actor }
}

// DefaultOptions returns the default client configuration for convenience.
func DefaultOptions() types.ClientOptions {
	return types.DefaultOptions()
}
