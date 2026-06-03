// Example: Audit trail workflow — demonstrates audit log write, query, and verification.
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
	apiKey := getEnv("QS_API_KEY", "operator-key")
	baseURL := getEnv("QS_URL", "http://localhost:8000")

	opts := types.DefaultOptions()
	opts.BaseURL = baseURL
	opts.APIKey = apiKey
	opts.Timeout = 15 * time.Second

	c, err := client.New(opts)
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// 1. Health check
	health, err := c.Health(ctx)
	if err != nil {
		log.Fatalf("Service unreachable: %v", err)
	}
	fmt.Printf("✅ Service: %s\n", health.Status)

	// 2. Write audit log entries
	fmt.Println("\n--- Writing Audit Logs ---")
	entries := []struct{ action, target, user string }{
		{"LOGIN", "system", "alice"},
		{"EXPORT", "report-2025-Q1.pdf", "alice"},
		{"SEAL", "contract-42", "bob"},
		{"UNSEAL", "contract-42", "bob"},
		{"DELETE", "temp-file-99", "alice"},
	}

	for _, e := range entries {
		resp, err := c.WriteAuditLog(ctx, e.action, e.target, e.user)
		if err != nil {
			log.Printf("⚠️  WriteAuditLog(%s, %s, %s) failed: %v", e.action, e.target, e.user, err)
			continue
		}
		fmt.Printf("📝 [%d] %s | %s | %s — sig: %s…\n",
			resp.ID, e.action, e.target, e.user, resp.Signature[:12])
	}

	// 3. Query audit logs with filtering
	fmt.Println("\n--- Query: Last 10 entries by alice ---")
	logs, err := c.GetAuditLogs(ctx,
		client.WithLimit(10),
		client.WithActor("alice"),
	)
	if err != nil {
		log.Fatalf("GetAuditLogs failed: %v", err)
	}
	for _, entry := range logs {
		fmt.Printf("   [%d] %-8s %-20s integrity: %s\n",
			entry.ID, entry.Action, entry.Target, entry.Integrity)
	}

	// 4. Get audit statistics
	fmt.Println("\n--- Audit Statistics ---")
	stats, err := c.GetAuditStats(ctx)
	if err != nil {
		log.Fatalf("GetAuditStats failed: %v", err)
	}
	fmt.Printf("   Total entries: %d\n", stats.Total)
	for action, count := range stats.ByAction {
		fmt.Printf("   %s: %d\n", action, count)
	}

	fmt.Println("\n✅ Audit trail example complete!")
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}