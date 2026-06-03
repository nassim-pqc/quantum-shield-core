// Example: Encryption workflow — demonstrates seal and unseal operations in detail.
package main

import (
	"context"
	"encoding/base64"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/quantum-shield/sdk-go/pkg/client"
	"github.com/quantum-shield/sdk-go/pkg/config"
)

func main() {
	// Load configuration from environment
	cfg := config.Load()
	cfg.APIKey = getEnv("QS_API_KEY", "operator-key")

	opts := cfg.ClientOptions()
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
	fmt.Printf("✅ Service: %s (v%s)\n", health.Status, health.Version)

	// 2. Generate ML-KEM-768 key pair
	keypair, err := c.GenerateKeypair(ctx)
	if err != nil {
		log.Fatalf("Key generation failed: %v", err)
	}
	fmt.Printf("🔑 Public key:  %d chars\n", len(keypair.PublicKeyB64))
	fmt.Printf("🔑 Private key: %d chars (store securely!)\n", len(keypair.PrivateKeyB64))

	// 3. Encrypt data (Seal)
	plaintext := []byte("Confidential: Quantum-resistant encryption in action.")
	contextID := "demo-encryption-001"

	sealed, err := c.Seal(ctx, keypair.PublicKeyB64, plaintext, contextID)
	if err != nil {
		log.Fatalf("Seal failed: %v", err)
	}
	fmt.Printf("🔒 Ciphertext (PQC): %d chars\n", len(sealed.CiphertextPQCb64))
	fmt.Printf("🔒 Nonce:            %d chars\n", len(sealed.NonceB64))
	fmt.Printf("🔒 Encrypted data:   %d chars\n", len(sealed.EncryptedDataB64))

	// 4. Decrypt data (Unseal)
	decrypted, err := c.Unseal(ctx, keypair.PrivateKeyB64, sealed, contextID)
	if err != nil {
		log.Fatalf("Unseal failed: %v", err)
	}
	fmt.Printf("🔓 Decrypted: %s\n", string(decrypted))

	// 5. Demonstrate tamper detection (wrong context)
	_, err = c.Unseal(ctx, keypair.PrivateKeyB64, sealed, "wrong-context")
	if err != nil {
		fmt.Printf("🛡️  Tamper detected (wrong context): %v\n", err)
	} else {
		log.Fatal("ERROR: Should have detected tamper!")
	}

	// 6. Base64 round-trip verification
	fmt.Println("\n--- Base64 Round-Trip Test ---")
	dataB64 := base64.StdEncoding.EncodeToString(decrypted)
	fmt.Printf("📦 Base64: %s\n", dataB64)
	decoded, _ := base64.StdEncoding.DecodeString(dataB64)
	fmt.Printf("📦 Decoded: %s\n", string(decoded))

	fmt.Println("\n✅ Encryption example complete!")
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}