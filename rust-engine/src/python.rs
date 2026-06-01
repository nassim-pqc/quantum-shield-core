//! PyO3 Python bindings for the Quantum Shield cryptographic engine.
//!
//! This module exposes the Rust SecurityEngine to Python, enabling
//! memory-safe cryptographic operations from the existing FastAPI codebase.
//!
//! # Usage (Python)
//!
//! ```python
//! from quantum_shield_engine import SecurityEngine
//!
//! engine = SecurityEngine.with_audit_key(b"a" * 32)
//! assert engine.pqc_algorithm() == "Kyber768"
//!
//! # AES-GCM operations (KEM handled by Python liboqs)
//! shared_secret = bytes(32)  # from Kyber768 decapsulation
//! nonce, ciphertext = engine.encrypt_aes_gcm(shared_secret, b"Hello", b"ctx")
//! plaintext = engine.decrypt_aes_gcm(shared_secret, nonce, ciphertext, b"ctx")
//!
//! # Signed audit trail
//! log_json, signature, key_ver = engine.generate_signed_log("SEAL", "doc.pdf", "admin")
//! assert engine.verify_log(log_json, signature)
//! ```

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use crate::error::CryptoError;
use crate::SecurityEngine as RustSecurityEngine;
use crate::LocalKMS;
use std::collections::HashMap;

// ---------------------------------------------------------------------------
// Python exception wrapper
// ---------------------------------------------------------------------------

/// Convert a Rust CryptoError to a Python ValueError with descriptive message.
fn py_err(err: CryptoError) -> PyErr {
    PyValueError::new_err(err.to_string())
}

// ---------------------------------------------------------------------------
// Python SecurityEngine class
// ---------------------------------------------------------------------------

/// Core cryptographic engine for Quantum Shield.
///
/// Memory-safe Rust implementation with HMAC-SHA256 audit trail and AES-256-GCM.
///
/// Args:
///     audit_key: Optional bytes — raw audit key (min 32 bytes).
///                If provided, creates a local KMS provider.
///
/// Raises:
///     ValueError: If the audit key is too short or KMS initialization fails.
#[pyclass(name = "SecurityEngine", module = "quantum_shield_engine")]
pub struct PySecurityEngine {
    inner: RustSecurityEngine,
}

#[pymethods]
impl PySecurityEngine {
    /// Create a new SecurityEngine with a local audit key.
    ///
    /// This is the simplest initialization for development/testing.
    /// For production, use `from_kms_provider()` with a configured KMS.
    #[staticmethod]
    fn with_audit_key(audit_key: &[u8]) -> PyResult<Self> {
        RustSecurityEngine::with_audit_key(audit_key)
            .map(|inner| PySecurityEngine { inner })
            .map_err(py_err)
    }

    /// Create a new SecurityEngine from environment keys (AUDIT_KEY_v1, etc.).
    ///
    /// Loads keys from environment variables following the same convention
    /// as the Python SecurityEngine.
    #[staticmethod]
    fn from_env() -> PyResult<Self> {
        let mut keys: HashMap<String, Vec<u8>> = HashMap::new();
        for (name, value) in std::env::vars() {
            if name.starts_with("AUDIT_KEY_") {
                let version = name.strip_prefix("AUDIT_KEY_")
                    .unwrap_or("")
                    .to_lowercase();
                if value.len() >= 32 {
                    keys.insert(version, value.into_bytes());
                }
            }
        }
        // Also check AUDIT_KEY (without version suffix)
        if keys.is_empty() {
            if let Ok(val) = std::env::var("AUDIT_KEY") {
                if val.len() >= 32 {
                    keys.insert("v1".to_string(), val.into_bytes());
                }
            }
        }
        let active_version = std::env::var("ACTIVE_AUDIT_KEY_VERSION")
            .unwrap_or_else(|_| "v1".to_string());

        let kms = LocalKMS::new(keys);
        RustSecurityEngine::new(Box::new(kms), Some(&active_version))
            .map(|inner| PySecurityEngine { inner })
            .map_err(py_err)
    }

    /// Get the PQC algorithm name.
    fn pqc_algorithm(&self) -> &str {
        self.inner.pqc_algorithm()
    }

    /// Get the active audit key version.
    fn active_key_version(&self) -> &str {
        self.inner.active_key_version()
    }

    /// Encrypt data using AES-256-GCM.
    ///
    /// Args:
    ///     shared_secret: bytes — 32-byte shared secret from Kyber768 KEM
    ///     plaintext: bytes — data to encrypt
    ///     aad: bytes — Additional Authenticated Data (context)
    ///
    /// Returns:
    ///     Tuple of (nonce: bytes, ciphertext: bytes)
    ///
    /// Raises:
    ///     ValueError: If shared_secret is too short or encryption fails.
    #[pyo3(signature = (shared_secret, plaintext, aad = None))]
    fn encrypt_aes_gcm(
        &self,
        py: Python,
        shared_secret: &[u8],
        plaintext: &[u8],
        aad: Option<&[u8]>,
    ) -> PyResult<(PyObject, PyObject)> {
        let aad = aad.unwrap_or(b"");
        let (nonce, ciphertext) = self.inner
            .encrypt_aes_gcm(shared_secret, plaintext, aad)
            .map_err(py_err)?;

        Ok((
            PyBytes::new(py, &nonce).into(),
            PyBytes::new(py, &ciphertext).into(),
        ))
    }

    /// Decrypt data using AES-256-GCM.
    ///
    /// Args:
    ///     shared_secret: bytes — 32-byte shared secret from Kyber768 KEM decapsulation
    ///     nonce: bytes — 12-byte nonce from encryption
    ///     ciphertext: bytes — encrypted data with GCM tag
    ///     aad: bytes — Additional Authenticated Data (must match encryption)
    ///
    /// Returns:
    ///     bytes — decrypted plaintext
    ///
    /// Raises:
    ///     ValueError: If authentication fails (tampered data, wrong key, or context mismatch)
    #[pyo3(signature = (shared_secret, nonce, ciphertext, aad = None))]
    fn decrypt_aes_gcm(
        &self,
        py: Python,
        shared_secret: &[u8],
        nonce: &[u8],
        ciphertext: &[u8],
        aad: Option<&[u8]>,
    ) -> PyResult<PyObject> {
        let aad = aad.unwrap_or(b"");
        let plaintext = self.inner
            .decrypt_aes_gcm(shared_secret, nonce, ciphertext, aad)
            .map_err(py_err)?;

        Ok(PyBytes::new(py, &plaintext).into())
    }

    /// Generate a signed audit log entry (HMAC-SHA256).
    ///
    /// Args:
    ///     action: str — action code (e.g., "SEAL")
    ///     target: str — target object identifier
    ///     user: str — user or role
    ///
    /// Returns:
    ///     Tuple of (log_json: str, signature_hex: str, key_version: str)
    ///
    /// Raises:
    ///     ValueError: If signing fails (missing key, etc.)
    fn generate_signed_log(
        &self,
        action: &str,
        target: &str,
        user: &str,
    ) -> PyResult<(String, String, String)> {
        self.inner
            .generate_signed_log(action, target, user)
            .map_err(py_err)
    }

    /// Verify an HMAC-SHA256 signature for a log entry.
    ///
    /// Supports key rotation: reads key_version from the log JSON.
    ///
    /// Args:
    ///     log_json: str — JSON string of the log entry
    ///     signature: str — HMAC-SHA256 hex signature
    ///
    /// Returns:
    ///     bool — True if signature is valid, False otherwise
    fn verify_log(&self, log_json: &str, signature: &str) -> bool {
        self.inner.verify_log(log_json, signature)
    }

    /// Set a new active audit key version (for key rotation).
    ///
    /// Args:
    ///     version: str — key version (e.g., "v2")
    ///
    /// Raises:
    ///     ValueError: If the new version is not found in KMS
    fn set_active_key_version(&mut self, version: &str) -> PyResult<()> {
        self.inner.set_active_key_version(version).map_err(py_err)
    }

    /// String representation.
    fn __repr__(&self) -> String {
        format!(
            "SecurityEngine(pqc={}, audit_key_version={})",
            self.inner.pqc_algorithm(),
            self.inner.active_key_version()
        )
    }
}

// ---------------------------------------------------------------------------
// Module definition
// ---------------------------------------------------------------------------

/// Quantum Shield Engine — Core cryptographic module.
///
/// Memory-safe, auditable, post-quantum cryptography for Python.
#[pymodule]
#[pyo3(name = "quantum_shield_engine")]
fn quantum_shield_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PySecurityEngine>()?;
    m.add("__version__", "1.0.0")?;
    m.add("PQC_ALGORITHM", crate::PQC_ALGORITHM)?;
    m.add("AES_GCM_NONCE_BYTES", crate::AES_GCM_NONCE_BYTES)?;
    m.add("MIN_AUDIT_KEY_BYTES", crate::MIN_AUDIT_KEY_BYTES)?;
    Ok(())
}