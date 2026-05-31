# Architecture — Quantum Shield Core

## System Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        SDK_PY[Python SDK]
        SDK_GO[Go SDK]
        CLI[cURL / HTTPie]
    end

    subgraph "Ingress"
        GW[API Gateway / Reverse Proxy]
        TLS[TLS 1.3 Termination]
    end

    subgraph "Quantum Shield Core"
        API[FastAPI]
        SE[Security Engine]
        AUTH[Auth & RBAC]
        AUDIT[Audit Store]
        OBS[Observability]
    end

    subgraph "External Integrations"
        KMS_AWS[AWS KMS]
        KMS_VAULT[HashiCorp Vault]
        KMS_AZURE[Azure Key Vault]
    end

    subgraph "Data Stores"
        PG[(PostgreSQL)]
    end

    SDK_PY --> GW
    SDK_GO --> GW
    CLI --> GW
    GW --> TLS
    TLS --> API

    API --> AUTH
    API --> SE
    API --> AUDIT
    API --> OBS

    SE --> KMS_AWS
    SE --> KMS_VAULT
    SE --> KMS_AZURE

    AUDIT --> PG
    AUTH --> PG
```

## Data Flow: Seal Operation

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Engine
    participant KMS
    participant Audit

    Client->>API: POST /api/v1/crypto/seal
    API->>Auth: Validate X-API-Key
    Auth-->>API: role=operator
    API->>Engine: encrypt_hybrid(pub_key, data, context)
    Engine->>Engine: Kyber768 KEM encap_secret()
    Engine->>Engine: SHA-256 derive AES key
    Engine->>Engine: AES-256-GCM encrypt(nonce, data, context)
    Engine-->>API: {ciphertext_pqc, nonce, encrypted_data}
    API->>Engine: generate_signed_log("SEAL", context, role)
    Engine->>KMS: get_audit_key(v1)
    KMS-->>Engine: audit_key
    Engine-->>API: {log, signature, key_version}
    API->>Audit: store_log(log, signature)
    Audit-->>API: entry_id
    API-->>Client: {ciphertext_pqc_b64, nonce_b64, encrypted_data_b64}
```

## Data Flow: Unseal Operation

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant Engine
    participant Audit

    Client->>API: POST /api/v1/crypto/unseal
    API->>Auth: Validate X-API-Key
    Auth-->>API: role=operator
    API->>Engine: decrypt_hybrid(priv_key, cpqc, nonce, enc_data, context)
    Engine->>Engine: Kyber768 KEM decap_secret()
    Engine->>Engine: SHA-256 derive AES key
    Engine->>Engine: AES-256-GCM decrypt(nonce, encrypted_data, context)
    Engine-->>API: plaintext
    API->>Engine: generate_signed_log("UNSEAL", context, role)
    Engine-->>API: {log, signature}
    API->>Audit: store_log(log, signature)
    Audit-->>API: entry_id
    API-->>Client: {decrypted_data_b64}
```

## Cryptographic Flow

```mermaid
graph LR
    subgraph "Encryption (Seal)"
        A1[Plaintext] --> B1[Kyber768 Encapsulation]
        C1[Public Key] --> B1
        B1 --> D1[Shared Secret]
        B1 --> E1[Ciphertext PQC]
        D1 --> F1[SHA-256 KDF]
        F1 --> G1[AES-256-GCM]
        A1 --> G1
        H1[Context/AAD] --> G1
        I1[Nonce urandom] --> G1
        G1 --> J1[Encrypted Data]
        J1 --> K1[Output: Ciphertext + Nonce + Encrypted Data]
        E1 --> K1
    end
```

## Component Stack

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| API | FastAPI (Python 3.12+) | HTTP endpoints, validation, routing |
| Auth | SQLAlchemy + SHA-256 | API key hashing, RBAC enforcement |
| Crypto (KEM) | liboqs-python (Python) | ML-KEM-768 key generation and KEM |
| Crypto (AEAD) | pyca/cryptography (Python) | AES-256-GCM with AAD |
| Crypto (Rust) | PyO3 (Rust) | HMAC-SHA256 audit, AES-GCM operations |
| Audit | PostgreSQL + SQLAlchemy | Append-only log persistence |
| Logging | structlog / JSON | Structured JSON for SIEM |
| Metrics | Prometheus | `/metrics`, crypto ops counters |
| Tracing | OpenTelemetry | W3C trace context, OTLP export |
| Rate Limiting | slowapi | Per-IP rate limiting |
| Container | Docker + K8s | Deployment, scaling, health checks |

## KMS Integration Points

```mermaid
graph TB
    subgraph "KMS Abstraction"
        I[AbstractKMS]
        L[LocalEnvKMS]
        A[AWSKMSProvider]
        V[HashiCorpVaultKMSProvider]
        Z[AzureKeyVaultProvider]
    end

    I --> L
    I --> A
    I --> V
    I --> Z
    
    L -->|Fallback| ENV[Environment Variables]
    A -->|Planned| AWS[AWS KMS]
    V -->|Planned| VAULT[Vault Transit]
    Z -->|Planned| AZURE[Azure Key Vault]
```

## Resource Requirements

| Environment | CPU | RAM | Storage | Notes |
|-------------|-----|-----|---------|-------|
| Development | 1 vCPU | 512 MB | 100 MB | SQLite, no KMS |
| Production | 2 vCPU | 2 GB | 10 GB + DB | PostgreSQL, KMS |
| High-availability | 4 vCPU | 4 GB | 50 GB + DB | 3 replicas, HPA |