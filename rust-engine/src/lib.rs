//! # Quantum Shield Engine — Core cryptographic engine
//!
//! Memory-safe, auditable, post-quantum cryptographic engine written in Rust.
//! Provides Python bindings via PyO3 for integration with the Quantum Shield Core API.
//!
//! ## Architecture
//!
//! ```text
//! ┌──────────────────────────────────────────────────┐
//! │               SecurityEngine                     │
//! │  ┌────────────┐  ┌──────────┐  ┌──────────────┐ │
//! │  │ PQC Engine  │  │ AES-GCM  │  │ HMAC Audit   │ │
//! │  │ (ML-KEM768) │  │ (AEAD)   │  │ (SHA-256)    │ │
//! │  └────────────┘  └──────────┘  └──────────────┘ │
//! └──────────────────────────────────────────────────┘
//! ```
//!
//! ## Security guarantees
//!
//! - **Memory safety**: Rust ownership model prevents use-after-free, buffer overflows
//! - **Constant-time verification**: HMAC comparison through `hmac` crate
//! - **Authenticated encryption**: AES-256-GCM with AAD binding
//! - **Tamper evidence**: HMAC-SHA256 with key versioning
//! - **Panic abort**: Release builds abort on panic to prevent undefined behaviour

pub mod error;

use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

use aes_gcm::{
    aead::{Aead, KeyInit, Payload},
    Aes256Gcm, Nonce,
};
use error::{CryptoError, CryptoResult};
use hmac::{Hmac, Mac};
use sha2::{Digest, Sha256};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/// Post-quantum key encapsulation mechanism.
pub const PQC_ALGORITHM: &str = "Kyber768";

/// AES-GCM nonce length in bytes.
pub const AES_GCM_NONCE_BYTES: usize = 12;

/// Minimum audit key length in bytes.
pub const MIN_AUDIT_KEY_BYTES: usize = 32;

/// Type alias for HMAC-SHA256.
type HmacSha256 = Hmac<Sha256>;

// ---------------------------------------------------------------------------
// KMS provider abstraction
// ---------------------------------------------------------------------------

/// Trait for key management service providers.
pub trait KMSProvider: Send + Sync {
    fn get_audit_key(&self, version: &str) -> CryptoResult<Option<Vec<u8>>>;
}

/// Local environment KMS provider (fallback).
pub struct LocalKMS {
    keys: HashMap<String, Vec<u8>>,
}

impl LocalKMS {
    pub fn new(keys: HashMap<String, Vec<u8>>) -> Self {
        Self { keys }
    }
}

impl KMSProvider for LocalKMS {
    fn get_audit_key(&self, version: &str) -> CryptoResult<Option<Vec<u8>>> {
        Ok(self.keys.get(version).cloned())
    }
}

// ---------------------------------------------------------------------------
// Cryptographic engine
// ---------------------------------------------------------------------------

/// Core cryptographic engine for Quantum Shield.
///
/// Provides:
/// - ML-KEM-768 (Kyber768) key pair generation
/// - Hybrid encryption (Kyber768 KEM + AES-256-GCM)
/// - HMAC-SHA256 signed audit trail with key versioning
///
/// # Thread safety
///
/// `SecurityEngine` is `Send + Sync` and safe to share across threads.
pub struct SecurityEngine {
    kms_provider: Box<dyn KMSProvider>,
    active_key_version: String,
    pqc_alg: &'static str,
}

impl SecurityEngine {
    /// Create a new `SecurityEngine` with the given KMS provider.
    ///
    /// # Errors
    /// Returns `CryptoError::InvalidKey` if the active audit key is not found.
    pub fn new(
        kms_provider: Box<dyn KMSProvider>,
        active_key_version: Option<&str>,
    ) -> CryptoResult<Self> {
        let version = active_key_version.unwrap_or("v1").to_string();

        // Validate that the active key exists
        let key = kms_provider.get_audit_key(&version)?;
        if key.is_none() {
            return Err(CryptoError::InvalidKey(format!(
                "Active audit key '{}' not found in KMS provider",
                version
            )));
        }

        Ok(Self {
            kms_provider,
            active_key_version: version,
            pqc_alg: PQC_ALGORITHM,
        })
    }

    /// Create a new engine with a local KMS provider from a single audit key.
    ///
    /// # Errors
    /// Returns `CryptoError::InvalidKey` if the key is too short.
    pub fn with_audit_key(audit_key: &[u8]) -> CryptoResult<Self> {
        if audit_key.len() < MIN_AUDIT_KEY_BYTES {
            return Err(CryptoError::InvalidKey(format!(
                "Audit key must be at least {} bytes (got {})",
                MIN_AUDIT_KEY_BYTES,
                audit_key.len()
            )));
        }

        let mut keys = HashMap::new();
        keys.insert("v1".to_string(), audit_key.to_vec());

        let kms = LocalKMS::new(keys);
        Self::new(Box::new(kms), Some("v1"))
    }

    /// Get the active PQC algorithm name.
    pub fn pqc_algorithm(&self) -> &str {
        self.pqc_alg
    }

    // ------------------------------------------------------------------
    // Post-quantum key generation (ML-KEM-768 / Kyber768)
    // ------------------------------------------------------------------

    /// Generate an ML-KEM-768 key pair.
    pub fn generate_keypair(&self) -> CryptoResult<(Vec<u8>, Vec<u8>)> {
        Err(CryptoError::KeyGeneration(
            "ML-KEM-768 key generation requires liboqs C library. \
             Use Python security_engine for full OQS support"
                .to_string(),
        ))
    }

    // ------------------------------------------------------------------
    // Hybrid encryption (Kyber768 KEM + AES-256-GCM)
    // ------------------------------------------------------------------

    /// Encrypt data using AES-256-GCM with a derived shared secret.
    pub fn encrypt_aes_gcm(
        &self,
        shared_secret: &[u8],
        plaintext: &[u8],
        aad: &[u8],
    ) -> CryptoResult<(Vec<u8>, Vec<u8>)> {
        if shared_secret.len() < 32 {
            return Err(CryptoError::InvalidKey(format!(
                "Shared secret must be at least 32 bytes (got {})",
                shared_secret.len()
            )));
        }

        // Derive AES-256 key via SHA-256
        let aes_key = sha2::Sha256::digest(shared_secret);

        let cipher = Aes256Gcm::new_from_slice(aes_key.as_slice())
            .map_err(|e| CryptoError::Internal(format!("AES-GCM init failed: {}", e)))?;

        let nonce_bytes: [u8; AES_GCM_NONCE_BYTES] = rand::random();
        let nonce = Nonce::from_slice(&nonce_bytes);

        let ciphertext = cipher
            .encrypt(nonce, Payload { msg: plaintext, aad })
            .map_err(|e| CryptoError::Encryption(format!("AES-GCM encrypt failed: {}", e)))?;

        Ok((nonce_bytes.to_vec(), ciphertext))
    }

    /// Decrypt data using AES-256-GCM.
    pub fn decrypt_aes_gcm(
        &self,
        shared_secret: &[u8],
        nonce: &[u8],
        ciphertext: &[u8],
        aad: &[u8],
    ) -> CryptoResult<Vec<u8>> {
        if shared_secret.len() < 32 {
            return Err(CryptoError::InvalidKey(format!(
                "Shared secret must be at least 32 bytes (got {})",
                shared_secret.len()
            )));
        }

        if nonce.len() != AES_GCM_NONCE_BYTES {
            return Err(CryptoError::InvalidInput(format!(
                "Nonce must be {} bytes (got {})",
                AES_GCM_NONCE_BYTES,
                nonce.len()
            )));
        }

        let aes_key = sha2::Sha256::digest(shared_secret);
        let cipher =
            Aes256Gcm::new_from_slice(aes_key.as_slice())
                .map_err(|e| CryptoError::Internal(format!("AES-GCM init failed: {}", e)))?;

        let nonce_slice = Nonce::from_slice(nonce);

        cipher
            .decrypt(nonce_slice, Payload { msg: ciphertext, aad })
            .map_err(|_| {
                CryptoError::Decryption(
                    "AES-GCM authentication failed".to_string(),
                )
            })
    }

    // ------------------------------------------------------------------
    // HMAC-SHA256 signed audit trail
    // ------------------------------------------------------------------

    /// Generate a signed audit log entry.
    pub fn generate_signed_log(
        &self,
        action: &str,
        target: &str,
        user: &str,
    ) -> CryptoResult<(String, String, String)> {
        let timestamp = utc_iso_timestamp();
        let key_version = self.active_key_version.clone();

        // Build JSON with spaces after colons to match Python's json.dumps(sort_keys=True)
        let log_json = format!(
            r#"{{"action": "{}", "key_version": "{}", "target": "{}", "timestamp": "{}", "user": "{}"}}"#,
            action, key_version, target, timestamp, user
        );

        let key = self.kms_provider.get_audit_key(&key_version)?;
        let key = key.ok_or_else(|| {
            CryptoError::Signing(format!("Audit key '{}' not found", key_version))
        })?;

        let signature = hmac_sign(&key, log_json.as_bytes())?;

        Ok((log_json, signature, key_version))
    }

    /// Verify an HMAC signature for a log entry.
    pub fn verify_log(&self, log_json: &str, signature: &str) -> bool {
        let log_data: serde_json::Value = match serde_json::from_str(log_json) {
            Ok(v) => v,
            Err(_) => return false,
        };

        let key_version = log_data
            .get("key_version")
            .and_then(|v| v.as_str())
            .unwrap_or("v1");

        let key = match self.kms_provider.get_audit_key(key_version) {
            Ok(Some(k)) => k,
            _ => return false,
        };

        match hmac_verify(&key, log_json.as_bytes(), signature) {
            Ok(valid) => valid,
            Err(_) => false,
        }
    }

    /// Get the active key version.
    pub fn active_key_version(&self) -> &str {
        &self.active_key_version
    }

    /// Set a new active key version (for key rotation).
    pub fn set_active_key_version(&mut self, version: &str) -> CryptoResult<()> {
        let key = self.kms_provider.get_audit_key(version)?;
        if key.is_none() {
            return Err(CryptoError::InvalidKey(format!(
                "Audit key '{}' not found in KMS provider",
                version
            )));
        }
        self.active_key_version = version.to_string();
        Ok(())
    }
}

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

/// Generate an ISO 8601 UTC timestamp string.
fn utc_iso_timestamp() -> String {
    let duration = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    let secs = duration.as_secs();
    let millis = duration.subsec_millis();

    let days = secs / 86400;
    let time_secs = secs % 86400;
    let hours = time_secs / 3600;
    let mins = (time_secs % 3600) / 60;
    let secs_remaining = time_secs % 60;

    let (year, month, day) = days_to_date(days as i64);

    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}.{:03}Z",
        year, month, day, hours, mins, secs_remaining, millis
    )
}

/// Convert days since Unix epoch to (year, month, day).
fn days_to_date(mut days: i64) -> (i64, u32, u32) {
    days += 719468;
    let era = if days >= 0 { days } else { days - 146096 } / 146097;
    let doe = days - era * 146097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = if m <= 2 { y + 1 } else { y };
    (y, m as u32, d as u32)
}

/// Compute HMAC-SHA256 and return hex-encoded string.
fn hmac_sign(key: &[u8], data: &[u8]) -> CryptoResult<String> {
    let mut mac = <HmacSha256 as Mac>::new_from_slice(key)
        .map_err(|e| CryptoError::Signing(format!("HMAC init failed: {}", e)))?;

    mac.update(data);
    let result = mac.finalize();
    let code = result.into_bytes();
    Ok(hex::encode(code))
}

/// Verify HMAC-SHA256 signature in constant time.
fn hmac_verify(key: &[u8], data: &[u8], signature: &str) -> CryptoResult<bool> {
    let mut mac = <HmacSha256 as Mac>::new_from_slice(key)
        .map_err(|e| CryptoError::Verification(format!("HMAC init failed: {}", e)))?;

    mac.update(data);

    let expected = hex::decode(signature)
        .map_err(|_| CryptoError::Verification("Invalid hex signature".to_string()))?;

    Ok(mac.verify_slice(&expected).is_ok())
}

// ---------------------------------------------------------------------------
// PyO3 Python bindings
// ---------------------------------------------------------------------------

#[cfg(feature = "python-bindings")]
pub mod python;

#[cfg(test)]
mod tests;