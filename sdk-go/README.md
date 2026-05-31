# Quantum Shield — Official Go SDK

Enterprise-grade Go client for the [Quantum Shield Core](https://github.com/quantum-shield/core) API.

## Features

- **Type-safe**: Fully typed Go API with comprehensive documentation
- **Context-aware**: All operations accept `context.Context` for cancellation/deadlines
- **Automatic retries**: Exponential backoff with configurable max attempts
- **Rate limiting**: Client-side rate limiter to prevent API throttling
- **Error wrapping**: Structured error types for auth, validation, and network failures
- **Observability-ready**: Compatible with OpenTelemetry and structured logging
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
    "github.com/quantum-shield/sdk-go/pkg/types"
)

func main() {
    opts := types.DefaultOptions()
    opts.APIKey = "your-operator-key"
    opts.BaseURL = "http://localhost:8000"

    c, err := client.New(opts)
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
| `WriteAuditLog(ctx, action, target, user)` | Append audit entry |
| `GetAuditLogs(ctx, opts...)` | List audit entries |
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
case *types.ErrServiceUnavailable:
    fmt.Printf("Service down: %v\n", e.Err)
}
```

## Examples

Run the quickstart example:

```bash
cd examples/quickstart
QS_API_KEY="your-key" go run main.go
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `QS_URL` | `http://localhost:8000` | Quantum Shield service URL |
| `QS_API_KEY` | — | API key for authentication |

## License

See LICENSE in the Quantum Shield Core repository.