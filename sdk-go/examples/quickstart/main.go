// Example: Quickstart — demonstrates the complete Quantum Shield Go SDK workflow.
package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/quantum-shield/sdk-go/pkg/client"
	"github.com/quantum-shield/sdk-go/pkg/types"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Initialize client
	opts := types.DefaultOptions()
	opts.BaseURL = getEnv("QS_URL", "http://localhost:8000")
	opts.APIKey = getEnv("QS_API_KEY", "operator-key")
	opts.Timeout = 10 * time.Second

	c, err := client.New(opts)
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}

	// 1. Health check
	health, err := c.Health(ctx)
	if err != nil {
		log.Fatalf("Health check failed: %v", err)
	}
	fmt.Printf("✅ Health: %s (v%s, %s)\n", health.Status, health.Version, health.Algorithm)

	// 2. Generate keypair
	keypair, err := c.GenerateKeypair(ctx)
	if err != nil {
		log.Fatalf("Key generation failed: %v", err)
	}
	fmt.Printf("🔑 Keypair generated (pub: %d chars)\n", len(keypair.PublicKeyB64))

	// 3. Seal (encrypt)
	plaintext := []byte("Sensitive document: M&A contract 2025-001")
	context := "contract-2025-001"

	sealed, err := c.Seal(ctx, keypair.PublicKeyB64, plaintext, context)
	if err != nil {
		log.Fatalf("Seal failed: %v", err)
	}
	fmt.Printf("🔒 Sealed: ciphertext=%d bytes, nonce=%d bytes\n",
		len(sealed.CiphertextPQCb64), len(sealed.NonceB64))

	// 4. Unseal (decrypt)
	decrypted, err := c.Unseal(ctx, keypair.PrivateKeyB64, sealed, context)
	if err != nil {
		log.Fatalf("Unseal failed: %v", err)
	}
	fmt.Printf("🔓 Unsealed: %s\n", string(decrypted))

	// 5. Audit trail
	auditEntry, err := c.WriteAuditLog(ctx, "SEAL", context, "go-sdk-demo")
	if err != nil {
		log.Fatalf("Audit write failed: %v", err)
	}
	fmt.Printf("📝 Audit written: ID=%d, Signature=%s…\n",
		auditEntry.ID, auditEntry.Signature[:16])

	// 6. Read audit logs
	logs, err := c.GetAuditLogs(ctx, client.WithLimit(5))
	if err != nil {
		log.Fatalf("Audit read failed: %v", err)
	}
	fmt.Printf("📋 Last %d audit entries:\n", len(logs))
	for _, entry := range logs {
		fmt.Printf("   [%d] %s — %s — integrity: %s\n",
			entry.ID, entry.Action, entry.Target, entry.Integrity)
	}

	fmt.Println("\n✅ Quickstart complete — Quantum Shield Go SDK is operational!")
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}