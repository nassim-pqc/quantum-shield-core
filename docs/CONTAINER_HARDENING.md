# Quantum Shield Core — Container Hardening Guide

> **Date**: June 2026  
> **Purpose**: Document container security posture and hardening measures  
> **Audience**: DevOps, security engineers, technical buyers

---

## 1. Overview

Quantum Shield Core provides two Dockerfiles:

| File | Purpose | Recommended For |
|------|---------|-----------------|
| `Dockerfile` | Standard multi-stage build | Development, testing |
| `Dockerfile.hardened` | Additional security hardening | Production, security-sensitive deployments |

The original `Dockerfile` is **not modified**. The hardened version is an additional option.

---

## 2. Security Features Comparison

| Feature | `Dockerfile` | `Dockerfile.hardened` |
|---------|--------------|----------------------|
| Multi-stage build | ✅ | ✅ |
| Non-root user | ✅ (appuser:8888) | ✅ (appuser:8888) |
| Minimal base image | ✅ (python:3.11-slim-bookworm) | ✅ (python:3.11-slim-bookworm) |
| No secrets in image | ✅ | ✅ |
| Health check | ✅ | ✅ |
| PYTHONDONTWRITEBYTECODE | ❌ | ✅ |
| PYTHONDEVMODE=0 | ❌ | ✅ |
| PYTHONOPTIMIZE=1 | ❌ | ✅ |
| pip cache purge | ❌ | ✅ |
| Nologin shell | ❌ | ✅ (/usr/sbin/nologin) |
| Strict directory permissions | ❌ | ✅ (755/1777) |
| curl timeout on healthcheck | ❌ | ✅ (--max-time 3) |

---

## 3. Docker Compose Hardening (Already Applied)

The existing `docker-compose.yml` already includes significant hardening:

```yaml
cap_drop:
  - ALL                    # Drop all Linux capabilities
security_opt:
  - no-new-privileges:true  # Prevent privilege escalation
read_only: true             # Read-only root filesystem
tmpfs:
  - /tmp:size=64M,mode=1777  # Writable tmpfs for temp files
mem_limit: 768m             # Memory limit
cpus: 2                     # CPU limit
logging:
  driver: json-file
  options:
    max-size: "10m"         # Log rotation
    max-file: "3"
```

---

## 4. Kubernetes Hardening Recommendations

### 4.1 Security Context

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantum-shield-api
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 8888
        runAsGroup: 8888
        fsGroup: 8888
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: quantum-shield-api
          image: quantum-shield:hardened
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          resources:
            limits:
              memory: "768Mi"
              cpu: "2"
            requests:
              memory: "256Mi"
              cpu: "0.5"
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir:
            sizeLimit: 64Mi
```

### 4.2 Network Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quantum-shield-netpol
spec:
  podSelector:
    matchLabels:
      app: quantum-shield-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - port: 8000
  egress:
    - to: []  # Allow all egress (for KMS providers)
      ports:
        - port: 443
          protocol: TCP
```

---

## 5. Read-Only Root Filesystem

The `Dockerfile.hardened` is designed to work with `read_only: true`:

- Application writes only to `/tmp/qshield` (tmpfs)
- Alembic migrations write to database, not filesystem
- No log files written to container filesystem (structured logging to stdout)

---

## 6. Capabilities Dropped

| Capability | Dropped | Reason |
|------------|---------|--------|
| `ALL` | ✅ | Drop everything not needed |
| `NET_BIND_SERVICE` | ✅ | App binds to port 8000 (non-privileged) |
| `SYS_ADMIN` | ✅ | No admin operations needed |
| `SETUID` / `SETGID` | ✅ | Non-root user, no privilege changes |

---

## 7. Image Size

| Image | Approximate Size |
|-------|-----------------|
| `python:3.11-slim-bookworm` base | ~150 MB |
| Final image (with liboqs) | ~400-500 MB |
| Final image (hardened) | ~380-480 MB |

**Note**: The hardened image may be slightly smaller due to `pip cache purge` and package cleanup.

---

## 8. Secrets Management

| Practice | Status |
|----------|--------|
| No secrets in Dockerfile | ✅ |
| No secrets in docker-compose.yml | ✅ (uses .env file) |
| .env file excluded from image | ✅ (.dockerignore) |
| .env file excluded from git | ✅ (.gitignore) |
| Secrets via environment variables | ✅ (runtime injection) |
| Secrets via Kubernetes Secrets | ✅ (recommended for production) |

---

## 9. Distroless Consideration

Google Distroless images were evaluated but **not adopted** for the following reasons:

1. **liboqs requires shared libraries** that are not available in distroless
2. **No shell access** makes debugging difficult in production
3. **Alembic migrations** require Python runtime
4. **Health check via curl** requires a shell binary

**Recommendation**: The `python:3.11-slim-bookworm` base provides the best balance of security and functionality for this project. A future evaluation of distroless with statically-linked liboqs could be considered.

---

## 10. Checklist for Production Deployment

- [ ] Use `Dockerfile.hardened` or equivalent security settings
- [ ] Enable `read_only: true` in docker-compose or Kubernetes
- [ ] Drop all Linux capabilities (`cap_drop: ALL`)
- [ ] Set `no-new-privileges: true`
- [ ] Configure memory and CPU limits
- [ ] Enable log rotation
- [ ] Use Kubernetes Secrets or external secret manager
- [ ] Enable seccomp profile (`RuntimeDefault`)
- [ ] Set `runAsNonRoot: true` in Kubernetes
- [ ] Configure network policies
- [ ] Enable Pod Disruption Budget
- [ ] Set up monitoring and alerting

---

*This guide is practical and honest. The container hardening is additional security hardening, not a guarantee of container security.*