// Package client provides an enterprise-grade Go client for the Quantum Shield Core API.
//
// Features:
//   - Typed, idiomatic Go API with context support
//   - Automatic retries with exponential backoff
//   - Structured error wrapping
//   - Secure headers (X-API-Key, X-Correlation-ID)
//   - Observability hooks (OpenTelemetry-compatible)
//   - Thread-safe
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

	// Validate base URL
	_, err := url.Parse(opts.BaseURL)
	if err != nil {
		return nil, fmt.Errorf("invalid base URL %q: %w", opts.BaseURL, err)
	}

	transport := &http.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: opts.InsecureSkipVerify, // #nosec G402 — dev only
		},
		MaxIdleConns:        10,
		IdleConnTimeout:     90 * time.Second,
		DisableCompression:  false,
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
	req.Header.Set("User-Agent", "quantum-shield-go-sdk/1.0.0")
	if c.apiKey != "" {
		req.Header.Set(defaultHeaderAPIKey, c.apiKey)
	}

	// Execute with retries
	var lastErr error
	for attempt := 0; attempt <= c.opts.RetryMaxAttempts; attempt++ {
		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = &types.ErrServiceUnavailable{
				Endpoint: u,
				Err:      err,
			}
			if attempt < c.opts.RetryMaxAttempts {
				delay := c.opts.RetryBaseDelay * (1 << attempt)
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

		// Handle error status codes
		if resp.StatusCode >= 400 {
			return nil, c.handleError(resp.StatusCode, respBody)
		}

		return &apiResponse{body: respBody, statusCode: resp.StatusCode}, nil
	}

	return nil, lastErr
}

func (c *Client) handleError(statusCode int, body []byte) error {
	var apiErr types.APIError
	apiErr.StatusCode = statusCode

	// Try to parse API error response
	if err := json.Unmarshal(body, &apiErr); err != nil {
		apiErr.Detail = string(body)
	}

	switch statusCode {
	case http.StatusForbidden:
		return &types.ErrAuthentication{Message: apiErr.Detail}
	case http.StatusUnauthorized:
		return &types.ErrAuthorization{}
	case http.StatusUnprocessableEntity:
		var valErr types.ErrValidation
		if err := json.Unmarshal(body, &valErr); err == nil {
			return &valErr
		}
		return &types.ErrValidation{}
	default:
		return &apiErr
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

	return base64.StdEncoding.DecodeString(unsealResp.DecryptedDataB64)
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

// ---------------------------------------------------------------------------
// Audit Trail
// ---------------------------------------------------------------------------

// WriteAuditLog appends a signed entry to the audit trail.
func (c *Client) WriteAuditLog(ctx context.Context, action, target, user string) (*types.AuditWriteResponse, error) {
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