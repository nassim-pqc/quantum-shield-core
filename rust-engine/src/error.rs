//! Enterprise error types for the Quantum Shield cryptographic engine.
//!
//! All errors are typed, auditable, and propagate cleanly to Python/PyO3.

use std::fmt;

/// Top-level error type for all cryptographic operations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CryptoError {
    /// Key generation failure (randomness source, algorithm mismatch)
    KeyGeneration(String),
    /// Encryption failure (invalid key, algorithm error)
    Encryption(String),
    /// Decryption failure (tampered data, wrong key, authentication failure)
    Decryption(String),
    /// HMAC signature generation failure
    Signing(String),
    /// HMAC signature verification failure
    Verification(String),
    /// Invalid key material (wrong length, bad format)
    InvalidKey(String),
    /// KMS provider error (transient, auth, or misconfiguration)
    KMSProvider(String),
    /// Invalid or malicious input data
    InvalidInput(String),
    /// Internal engine invariant violated
    Internal(String),
}

impl fmt::Display for CryptoError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            CryptoError::KeyGeneration(msg) => write!(f, "Key generation error: {}", msg),
            CryptoError::Encryption(msg) => write!(f, "Encryption error: {}", msg),
            CryptoError::Decryption(msg) => write!(f, "Decryption error: {}", msg),
            CryptoError::Signing(msg) => write!(f, "Signing error: {}", msg),
            CryptoError::Verification(msg) => write!(f, "Verification error: {}", msg),
            CryptoError::InvalidKey(msg) => write!(f, "Invalid key: {}", msg),
            CryptoError::KMSProvider(msg) => write!(f, "KMS provider error: {}", msg),
            CryptoError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            CryptoError::Internal(msg) => write!(f, "Internal error: {}", msg),
        }
    }
}

impl std::error::Error for CryptoError {}

impl From<CryptoError> for String {
    fn from(err: CryptoError) -> String {
        err.to_string()
    }
}

/// Result alias for cryptographic operations.
pub type CryptoResult<T> = Result<T, CryptoError>;