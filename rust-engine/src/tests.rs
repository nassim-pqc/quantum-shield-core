//! Unit tests for the Quantum Shield Rust cryptographic engine.
//!
//! Covers: AES-GCM encryption/decryption, HMAC audit trail,
//! key validation, error handling, and edge cases.

#[cfg(test)]
mod tests {
    use crate::error::CryptoError;
    use crate::SecurityEngine;

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------
    const VALID_KEY: &[u8] = b"test-audit-key-minimum-32-bytes-ok!";

    fn engine() -> SecurityEngine {
        SecurityEngine::with_audit_key(VALID_KEY).expect("Engine init should succeed")
    }

    // -----------------------------------------------------------------------
    // Engine initialization
    // -----------------------------------------------------------------------
    #[test]
    fn test_engine_init_with_valid_key() {
        let engine = SecurityEngine::with_audit_key(VALID_KEY);
        assert!(engine.is_ok());
    }

    #[test]
    fn test_engine_rejects_short_key() {
        let result = SecurityEngine::with_audit_key(b"tooshort");
        assert!(result.is_err());
        if let Err(CryptoError::InvalidKey(msg)) = result {
            assert!(msg.contains("32 bytes"));
        } else {
            panic!("Expected InvalidKey error");
        }
    }

    #[test]
    fn test_engine_accepts_exactly_32_bytes() {
        let engine = SecurityEngine::with_audit_key(b"exactly-32-bytes-audit-key-here!");
        assert!(engine.is_ok());
    }

    #[test]
    fn test_pqc_algorithm_is_kyber768() {
        let engine = engine();
        assert_eq!(engine.pqc_algorithm(), "Kyber768");
    }

    #[test]
    fn test_active_key_version_defaults_to_v1() {
        let engine = engine();
        assert_eq!(engine.active_key_version(), "v1");
    }

    // -----------------------------------------------------------------------
    // AES-GCM encryption/decryption
    // -----------------------------------------------------------------------
    #[test]
    fn test_aes_gcm_roundtrip() {
        let engine = engine();
        let shared_secret = b"this-is-a-32-byte-shared-secret-key!!";
        let plaintext = b"Hello, Quantum Shield!";
        let aad = b"doc-123";

        let (nonce, ciphertext) = engine
            .encrypt_aes_gcm(shared_secret, plaintext, aad)
            .expect("Encryption should succeed");

        assert_eq!(nonce.len(), 12, "Nonce must be 12 bytes");

        let decrypted = engine
            .decrypt_aes_gcm(shared_secret, &nonce, &ciphertext, aad)
            .expect("Decryption should succeed");

        assert_eq!(decrypted, plaintext, "Decrypted text must match original");
    }

    #[test]
    fn test_aes_gcm_roundtrip_empty_plaintext() {
        let engine = engine();
        let shared_secret = b"this-is-a-32-byte-shared-secret-key!!";
        let aad = b"ctx";

        let (nonce, ciphertext) = engine
            .encrypt_aes_gcm(shared_secret, b"", aad)
            .expect("Empty plaintext encryption should succeed");

        let decrypted = engine
            .decrypt_aes_gcm(shared_secret, &nonce, &ciphertext, aad)
            .expect("Empty plaintext decryption should succeed");

        assert_eq!(decrypted, b"");
    }

    #[test]
    fn test_aes_gcm_large_payload() {
        let engine = engine();
        let shared_secret = b"this-is-a-32-byte-shared-secret-key!!";
        let large_data = vec![0xABu8; 1_000_000]; // 1 MB

        let (nonce, ciphertext) = engine
            .encrypt_aes_gcm(shared_secret, &large_data, b"ctx")
            .expect("Large payload encryption should succeed");

        let decrypted = engine
            .decrypt_aes_gcm(shared_secret, &nonce, &ciphertext, b"ctx")
            .expect("Large payload decryption should succeed");

        assert_eq!(decrypted, large_data);
    }

    #[test]
    fn test_aes_gcm_wrong_context_fails() {
        let engine = engine();
        let shared_secret = b"this-is-a-32-byte-shared-secret-key!!";

        let (nonce, ciphertext) = engine
            .encrypt_aes_gcm(shared_secret, b"secret", b"correct-context")
            .expect("Encryption should succeed");

        let result = engine.decrypt_aes_gcm(
            shared_secret,
            &nonce,
            &ciphertext,
            b"wrong-context", // Different context — should fail
        );

        assert!(result.is_err(), "Decryption with wrong context should fail");
    }

    #[test]
    fn test_aes_gcm_wrong_key_fails() {
        let engine = engine();
        let correct_key = b"this-is-a-32-byte-shared-secret-key!!";
        let wrong_key = b"this-is-a-different-32-byte-key-here!!";

        let (nonce, ciphertext) = engine
            .encrypt_aes_gcm(correct_key, b"secret", b"ctx")
            .expect("Encryption should succeed");

        let result = engine.decrypt_aes_gcm(wrong_key, &nonce, &ciphertext, b"ctx");
        assert!(result.is_err(), "Decryption with wrong key should fail");
    }

    #[test]
    fn test_aes_gcm_tampered_ciphertext_fails() {
        let engine = engine();
        let key = b"this-is-a-32-byte-shared-secret-key!!";

        let (nonce, mut ciphertext) = engine
            .encrypt_aes_gcm(key, b"secret", b"ctx")
            .expect("Encryption should succeed");

        // Flip one byte in ciphertext
        ciphertext[0] ^= 0xFF;

        let result = engine.decrypt_aes_gcm(key, &nonce, &ciphertext, b"ctx");
        assert!(
            result.is_err(),
            "Decryption of tampered ciphertext should fail"
        );
    }

    #[test]
    fn test_aes_gcm_tampered_nonce_fails() {
        let engine = engine();
        let key = b"this-is-a-32-byte-shared-secret-key!!";

        let (nonce, ciphertext) = engine
            .encrypt_aes_gcm(key, b"secret", b"ctx")
            .expect("Encryption should succeed");

        // Flip all bits in nonce
        let tampered_nonce: Vec<u8> = nonce.iter().map(|b| b ^ 0xFF).collect();

        let result = engine.decrypt_aes_gcm(key, &tampered_nonce, &ciphertext, b"ctx");
        assert!(
            result.is_err(),
            "Decryption with tampered nonce should fail"
        );
    }

    #[test]
    fn test_aes_gcm_short_shared_secret_fails() {
        let engine = engine();
        let short_secret = b"too-short";

        let result = engine.encrypt_aes_gcm(short_secret, b"data", b"ctx");
        assert!(
            result.is_err(),
            "Encryption with short shared secret should fail"
        );
    }

    #[test]
    fn test_aes_gcm_invalid_nonce_size_fails() {
        let engine = engine();
        let key = b"this-is-a-32-byte-shared-secret-key!!";
        let short_nonce = b"short";

        let result = engine.decrypt_aes_gcm(key, short_nonce, b"ciphertext", b"ctx");
        assert!(
            result.is_err(),
            "Decryption with wrong nonce size should fail"
        );
    }

    // -----------------------------------------------------------------------
    // HMAC Audit Trail
    // -----------------------------------------------------------------------
    #[test]
    fn test_generate_signed_log_returns_required_fields() {
        let engine = engine();
        let (log_json, signature, key_ver) = engine
            .generate_signed_log("SEAL", "doc.pdf", "operator")
            .expect("Signing should succeed");

        assert!(!log_json.is_empty());
        assert!(!signature.is_empty());
        assert_eq!(key_ver, "v1");

        // Verify signature is hex (64 chars)
        assert_eq!(signature.len(), 64, "HMAC-SHA256 should be 64 hex chars");
        assert!(signature.chars().all(|c| c.is_ascii_hexdigit()));
    }

    #[test]
    fn test_verify_log_returns_true_for_valid_entry() {
        let engine = engine();
        let (log_json, signature, _) = engine
            .generate_signed_log("UNSEAL", "doc.pdf", "operator")
            .expect("Signing should succeed");

        assert!(engine.verify_log(&log_json, &signature));
    }

    #[test]
    fn test_verify_log_returns_false_for_tampered_content() {
        let engine = engine();
        let (mut log_json, signature, _) = engine
            .generate_signed_log("SEAL", "doc.pdf", "operator")
            .expect("Signing should succeed");

        // Tamper: change SEAL to UNSEAL in JSON
        log_json = log_json.replace("SEAL", "UNSEAL");

        assert!(!engine.verify_log(&log_json, &signature));
    }

    #[test]
    fn test_verify_log_returns_false_for_wrong_signature() {
        let engine = engine();
        let (log_json, _, _) = engine
            .generate_signed_log("SEAL", "doc.pdf", "operator")
            .expect("Signing should succeed");

        assert!(!engine.verify_log(&log_json, "a".repeat(64).as_str()));
    }

    #[test]
    fn test_different_keys_produce_different_signatures() {
        let engine1 = SecurityEngine::with_audit_key(b"first-audit-key-minimum-32-bytes-aa!")
            .expect("Engine1 init");
        let engine2 = SecurityEngine::with_audit_key(b"second-audit-key-minimum-32-bytes-b!")
            .expect("Engine2 init");

        let (log1, sig1, _) = engine1
            .generate_signed_log("SEAL", "doc.pdf", "operator")
            .expect("Engine1 sign");
        let (_, sig2, _) = engine2
            .generate_signed_log("SEAL", "doc.pdf", "operator")
            .expect("Engine2 sign");

        // Same logical content, different keys — signatures must differ
        assert_ne!(sig1, sig2, "Different keys must produce different signatures");
    }

    #[test]
    fn test_verify_log_returns_false_for_cross_key_signature() {
        let engine_a = SecurityEngine::with_audit_key(b"audit-key-a-minimum-32-bytes-aaaa!")
            .expect("Engine A init");
        let engine_b = SecurityEngine::with_audit_key(b"audit-key-b-minimum-32-bytes-bbbb!")
            .expect("Engine B init");

        let (log_json, signature, _) = engine_a
            .generate_signed_log("SEAL", "doc.pdf", "operator")
            .expect("Engine A sign");

        assert!(!engine_b.verify_log(&log_json, &signature));
    }

    #[test]
    fn test_verify_log_handles_invalid_input_gracefully() {
        let engine = engine();
        // Must never panic
        assert!(!engine.verify_log("not-valid-json{{{", "invalidsig"));
        assert!(!engine.verify_log("", ""));
        assert!(!engine.verify_log("{}", "a".repeat(64).as_str()));
    }

    #[test]
    fn test_verify_log_handles_missing_key_version() {
        let engine = engine();
        let log_no_version = r#"{"action":"SEAL","target":"doc","user":"admin"}"#;
        // Should not panic; key_version defaults to "v1" which exists
        let result = engine.verify_log(log_no_version, "a".repeat(64).as_str());
        assert!(!result, "Should return false but not panic");
    }

    // -----------------------------------------------------------------------
    // Key rotation
    // -----------------------------------------------------------------------
    #[test]
    fn test_set_active_key_version() {
        let mut engine = engine();
        assert_eq!(engine.active_key_version(), "v1");

        // Can't set to non-existent version
        let result = engine.set_active_key_version("v99");
        assert!(result.is_err());
    }

    #[test]
    fn test_log_uses_active_key_version() {
        let engine = engine();
        let (_, _, key_ver) = engine
            .generate_signed_log("SEAL", "target", "user")
            .expect("Signing should succeed");
        assert_eq!(key_ver, "v1");
    }
}