# Quantum Shield — Official Go SDK

Enterprise-grade Go client for the Quantum Shield Core API.

## Features

- **Full API coverage**: Health, key generation, seal/unseal, audit trail (all endpoints)
- **Missing endpoint added**: `GET /api/v1/audit/logs/{log_id}` via `GetAuditLogByID()`
- **Client-side validation**: All inputs validated before API calls
- **Enterprise error types**: `ErrAuthentication`, `ErrAuthorization`, `ErrValidation`, `ErrNotFound`, `ErrRateLimited`, `ErrServiceUnavailable`, `ErrInvalidInput`
- **Exponential backoff**: Configurable retries with jitter, including 5xx server errors
- **Rate limiting**: Client-side rate limiter prevents API throttling
- **Observability hooks**: OpenTelemetry-compatible hooks interface
- **Structured logging**: `log/slog` adapter via `types.SlogLogger`
- **Configuration management**: Environment-based config via `pkg/config`
- **Context-aware**: All operations accept `context.Context` for cancellation/deadlines
- **Thread-safe**: Single client instance safe for concurrent use

## Installation

```bash
go get github.com/quantum-shield/sdk-go
```

## Quick Start

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
    cfg.APIKey = "your-operator-key"

    c, err := client.New(cfg.ClientOptions())
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()

    // Health check
    health, _ := c.Health(ctx)
    fmt.Printf("Status: %s\n", health.Status)

    // Generate keypair
    keypair, _ := c.GenerateKeypair(ctx)

    // Encrypt
    sealed, _ := c.Seal(ctx, keypair.PublicKeyB64, []byte("sensitive data"), "doc-123")

    // Decrypt
    decrypted, _ := c.Unseal(ctx, keypair.PrivateKeyB64, sealed, "doc-123")
    fmt.Printf("Decrypted: %s\n", string(decrypted))
}
```

## API Reference

### Client

```go
c, err := client.New(opts)
c.SetAPIKey("new-key")                  // Rotate API key at runtime
c.SetTimeout(30 * time.Second)          // Adjust timeout
```

### Operations

| Method | Description |
|--------|-------------|
| `Health(ctx)` | Service health + DB status |
| `GenerateKeypair(ctx)` | ML-KEM-768 key pair |
| `Seal(ctx, pubKey, data, context)` | Hybrid encrypt |
| `Unseal(ctx, privKey, sealed, context)` | Hybrid decrypt |
| `SealText(ctx, pubKey, text, context)` | Encrypt string |
| `UnsealText(ctx, privKey, sealed, context)` | Decrypt to string |
| `WriteAuditLog(ctx, action, target, user)` | Append audit entry |
| `GetAuditLogs(ctx, opts...)` | List audit entries |
| `GetAuditLogByID(ctx, logID)` | Get single audit entry |
| `GetAuditStats(ctx)` | Audit statistics |

### Error Handling

```go
switch e := err.(type) {
case *types.ErrAuthentication:
    fmt.Printf("Auth failed: %s\n", e.Message)
case *types.ErrAuthorization:
    fmt.Printf("Insufficient permissions\n")
case *types.ErrValidation:
    fmt.Printf("Validation error: %+v\n", e.Errors)
case *types.ErrNotFound:
    fmt.Printf("Not found: %s\n", e.Resource)
case *types.ErrRateLimited:
    fmt.Printf("Rate limited, retry after %s\n", e.RetryAfter)
case *types.ErrServiceUnavailable:
    fmt.Printf("Service down: %v\n", e.Err)
case *types.ErrInvalidInput:
    fmt.Printf("Invalid input: %s — %s\n", e.Field, e.Message)
}
```

## Examples

```bash
# Quickstart (full workflow)
cd examples/quickstart
QS_API_KEY="your-key" go run main.go

# Encryption deep-dive
cd examples/encryption
QS_API_KEY="your-key" go run main.go

# Audit trail management
cd examples/audit-trail
QS_API_KEY="your-key" go run main.go
```

## Environment

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

## Package Structure

```
sdk-go/
├── go.mod                  # Module: github.com/quantum-shield/sdk-go (Go 1.22)
├── README.md               # This file
├── examples/
│   ├── quickstart/         # Complete workflow example
│   ├── encryption/         # Encryption deep-dive
│   └── audit-trail/        # Audit trail management
└── pkg/
    ├── client/             # HTTP client with retries, rate limiting, validation
    ├── config/             # Environment-based configuration
    ├── types/              # Type definitions, error types, logger interfaces
    └── validate/           # Client-side input validation
```

## License

See LICENSE in the Quantum Shield Core repository.