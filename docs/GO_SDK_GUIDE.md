# Quantum Shield Go SDK — Enterprise Guide

## Overview

The Quantum Shield Go SDK (`sdk-go/`) provides an enterprise-grade Go client for the Quantum Shield Core API. It enables Go applications to leverage post-quantum cryptography (ML-KEM-768 + AES-256-GCM) with a typed, idiomatic Go interface.

---

## Installation

```bash
go get github.com/quantum-shield/sdk-go
```

**Requirements:**
- Go 1.22 or later
- Access to a running Quantum Shield Core instance

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QS_URL` | `http://localhost:8000` | Quantum Shield service URL |
| `QS_API_KEY` | — | API key for authentication |
| `QS_TIMEOUT` | `30s` | HTTP client timeout |
| `QS_RETRY_MAX_ATTEMPTS` | `3` | Max retry attempts |
| `QS_RETRY_BASE_DELAY` | `500ms` | Base delay for exponential backoff |
| `QS_RETRY_ON_5XX` | `true` | Retry on server errors (5xx) |
| `QS_INSECURE_SKIP_VERIFY` | `false` | Skip TLS verification (dev only) |
| `QS_LOG_LEVEL` | `info` | Log level (debug, info, warn, error) |
| `QS_LOG_FORMAT` | `text` | Log format (text, json) |

### Using the Config Package

```go
import (
    "github.com/quantum-shield/sdk-go/pkg/client"
    "github.com/quantum-shield/sdk-go/pkg/config"
)

// Load from environment variables
cfg := config.Load()
opts := cfg.ClientOptions()

// Or set values directly
cfg.APIKey = "your-operator-key"
opts = cfg.ClientOptions()

c, err := client.New(opts)
```

### Programmatic Configuration

```go
import (
    "github.com/quantum-shield/sdk-go/pkg/client"
    "github.com/quantum-shield/sdk-go/pkg/types"
)

opts := types.DefaultOptions()
opts.BaseURL = "https://api.quantum-shield.io:8443"
opts.APIKey = "your-operator-key"
opts.Timeout = 15 * time.Second
opts.RetryMaxAttempts = 5
opts.RetryBaseDelay = 1 * time.Second

c, err := client.New(opts)
```

---

## Authentication

Authentication is handled via the `X-API-Key` header. The API key is set during client creation or updated at runtime:

```go
// Set during construction
opts.APIKey = "your-key"

// Or update at runtime
c.SetAPIKey("new-key")
```

The backend uses SHA-256 hashed API keys with RBAC roles (`operator`, `auditor`).

---

## API Reference

### Client Creation

```go
func New(opts types.ClientOptions) (*Client, error)
func DefaultOptions() types.ClientOptions
```

### Health

```go
func (c *Client) Health(ctx context.Context) (*types.HealthResponse, error)
```

Returns service status, algorithm, version, and database health.

### Key Management

```go
func (c *Client) GenerateKeypair(ctx context.Context) (*types.KeyPairResponse, error)
```

Generates an ML-KEM-768 (Kyber768) key pair. The private key is returned only once.

### Encryption (Seal/Unseal)

```go
func (c *Client) Seal(ctx context.Context, pubKey string, data []byte, context string) (*types.SealResponse, error)
func (c *Client) Unseal(ctx context.Context, privKey string, sealed *types.SealResponse, context string) ([]byte, error)
func (c *Client) SealText(ctx context.Context, pubKey, text, context string) (*types.SealResponse, error)
func (c *Client) UnsealText(ctx context.Context, privKey string, sealed *types.SealResponse, context string) (string, error)
```

The `context` parameter is used as Additional Authenticated Data (AAD). Decryption with a different context will fail.

### Audit Trail

```go
func (c *Client) WriteAuditLog(ctx context.Context, action, target, user string) (*types.AuditWriteResponse, error)
func (c *Client) GetAuditLogs(ctx context.Context, opts ...AuditLogOption) ([]types.AuditLogEntry, error)
func (c *Client) GetAuditLogByID(ctx context.Context, logID int) (*types.AuditLogEntry, error)
func (c *Client) GetAuditStats(ctx context.Context) (*types.AuditStats, error)
```

Audit log filtering options:

```go
client.WithSkip(10)     // Skip first N entries
client.WithLimit(100)   // Limit results (max 500)
client.WithAction("SEAL") // Filter by action type
client.WithActor("alice") // Filter by actor
```

### Runtime Configuration

```go
func (c *Client) SetAPIKey(key string)
func (c *Client) SetTimeout(timeout time.Duration)
func (c *Client) Options() types.ClientOptions
func (c *Client) Logger() types.Logger
```

---

## Error Handling

All errors are typed and can be checked with Go's type assertion:

```go
switch e := err.(type) {
case *types.ErrAuthentication:
    // Invalid API key (403)
case *types.ErrAuthorization:
    // Insufficient permissions (401)
case *types.ErrValidation:
    // Request validation error (422)
case *types.ErrNotFound:
    // Resource not found (404)
case *types.ErrRateLimited:
    // Rate limited (429)
case *types.ErrServiceUnavailable:
    // Network error or service down
case *types.ErrInvalidInput:
    // Client-side validation error
case *types.APIError:
    // Generic API error
}
```

---

## Structured Logging

The SDK supports structured logging via `log/slog`:

```go
import (
    "log/slog"
    "github.com/quantum-shield/sdk-go/pkg/types"
)

// Use default logger
opts.Logger = types.NewSlogLogger(nil)

// Use custom logger
opts.Logger = types.NewSlogLogger(slog.New(slog.NewJSONHandler(os.Stdout, nil)))
```

---

## Observability Hooks

Integrate OpenTelemetry or custom instrumentation:

```go
type MyHooks struct{}

func (h MyHooks) BeforeRequest(method, path string) {
    // Start span
}
func (h MyHooks) AfterRequest(method, path string, statusCode int, duration time.Duration) {
    // Record metrics
}
func (h MyHooks) OnError(method, path string, err error) {
    // Record error
}

opts.Hooks = &MyHooks{}
```

---

## Validation

The SDK performs client-side validation before every API call:

- Public/private key length checks
- Data size limits (10MB max)
- Context/AAD length validation (128 chars max)
- Audit action length validation (64 chars max)
- Audit user length validation (64 chars max)
- Base URL format validation

Validation errors are returned as `*types.ErrInvalidInput` before any network request is made.

---

## Complete Example

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "github.com/quantum-shield/sdk-go/pkg/client"
    "github.com/quantum-shield/sdk-go/pkg/config"
)

func main() {
    cfg := config.Load()
    cfg.APIKey = "operator-key"

    c, err := client.New(cfg.ClientOptions())
    if err != nil {
        log.Fatal(err)
    }

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    // Health check
    health, _ := c.Health(ctx)
    fmt.Printf("Status: %s\n", health.Status)

    // Generate keypair
    kp, _ := c.GenerateKeypair(ctx)

    // Encrypt
    sealed, _ := c.Seal(ctx, kp.PublicKeyB64, []byte("sensitive data"), "doc-123")

    // Decrypt
    data, _ := c.Unseal(ctx, kp.PrivateKeyB64, sealed, "doc-123")
    fmt.Printf("Decrypted: %s\n", string(data))

    // Audit
    c.WriteAuditLog(ctx, "SEAL", "doc-123", "go-sdk")
    logs, _ := c.GetAuditLogs(ctx, client.WithLimit(5))
    fmt.Printf("Audit entries: %d\n", len(logs))
}
```

---

## Best Practices

1. **Reuse the client**: Create a single `Client` instance — it's thread-safe and maintains a connection pool.
2. **Set timeouts**: Always use `context.WithTimeout` to prevent goroutine leaks.
3. **Secure private keys**: Private keys from `GenerateKeypair` are returned only once. Store them securely.
4. **Use meaningful context**: The `context` parameter binds ciphertext to business identifiers — never reuse across different documents.
5. **Monitor retries**: Configure `RetryMaxAttempts` and `RetryBaseDelay` based on your latency requirements.
6. **Enable structured logging**: Use `SlogLogger` to integrate with your observability pipeline.
7. **Validate inputs early**: Client-side validation catches common errors before network calls.

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `ErrAuthentication` | Wrong API key | Check `QS_API_KEY` or `opts.APIKey` |
| `ErrServiceUnavailable` | Service not running | Verify `QS_URL` and `docker compose ps` |
| `ErrValidation` | Invalid input | Check field constraints (length, size) |
| `ErrNotFound` | Resource doesn't exist | Verify log ID or endpoint path |
| `ErrRateLimited` | Too many requests | Reduce request rate or increase limits |
| Context deadline exceeded | Timeout too short | Increase `QS_TIMEOUT` or context timeout |
| TLS errors | Certificate validation | Set `QS_INSECURE_SKIP_VERIFY=true` (dev only) |

---

## Package Structure

```
sdk-go/
├── go.mod                  # Module definition
├── README.md               # Quick start
├── examples/
│   ├── quickstart/         # Complete workflow example
│   ├── encryption/         # Encryption deep-dive
│   └── audit-trail/        # Audit trail management
└── pkg/
    ├── client/             # HTTP client with retries, rate limiting
    ├── config/             # Environment-based configuration
    ├── types/              # Type definitions, errors, interfaces
    └── validate/           # Client-side input validation
```

---

## Package Index

- `pkg/client` — Main client with all API operations
- `pkg/config` — Environment variable configuration loader
- `pkg/types` — Type definitions, error types, logger interface
- `pkg/validate` — Input validation helpers