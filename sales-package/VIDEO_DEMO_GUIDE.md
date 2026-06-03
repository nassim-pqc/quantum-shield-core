# Quantum Shield Core — Video Demo Guide

> **Purpose**: Guide for recording a 3-minute video demo  
> **Internal use only**  
> **Date**: June 2026

---

## Overview

A 3-minute video demonstrating Quantum Shield Core. The video should be professional, clear, and honest.

**Duration**: 3 minutes maximum  
**Format**: Screen recording with voiceover  
**Language**: French (or English, depending on audience)  
**Resolution**: 1920x1080 minimum

---

## Script Structure

### 0:00 — Intro (15 seconds)

> "Bonjour, je vais vous présenter Quantum Shield Core — un microservice de chiffrement post-quantum pour les entreprises."

**Screen**: GitHub repository page

### 0:15 — Problem (20 seconds)

> "Le problème : NIST a finalisé les standards de cryptographie post-quantum en 2024. Les organisations ont besoin de chiffrement résistant aux ordinateurs quantiques, mais les solutions existantes sont soit expérimentales, soit complexes à intégrer."

**Screen**: NIST website or FIPS 203 announcement

### 0:35 — Solution (30 seconds)

> "La solution : Quantum Shield Core est une couche de chiffrement prête à intégrer, utilisant des algorithmes standardisés par NIST : ML-KEM-768 pour l'échange de clés post-quantum, et AES-256-GCM pour le chiffrement symétrique. L'architecture est stateless — aucune clé privée n'est stockée côté serveur."

**Screen**: Architecture diagram in README

### 1:05 — Features (30 seconds)

> "Le projet supporte AWS KMS, Azure Key Vault et HashiCorp Vault. Il fournit deux SDKs — Python et Go. L'observabilité est complète avec Prometheus et OpenTelemetry. La CI est verte avec 139 tests passants."

**Screen**: Feature list, KMS providers, SDK code

### 1:35 — Live Demo (60 seconds)

> "Voyons le projet en action."

**Steps**:
1. Show health check: `curl http://localhost:8000/health`
2. Generate keys: `curl -X POST .../api/v1/keys/generate`
3. Encrypt data: `curl -X POST .../api/v1/crypto/seal`
4. Decrypt data: `curl -X POST .../api/v1/crypto/unseal`
5. Show audit logs: `curl .../api/v1/audit/logs`

**Screen**: Terminal with live commands

### 2:35 — Benchmarks (15 seconds)

> "Les performances : génération de clé en 0.01 milliseconde, chiffrement d'un kilobyte en 0.20 milliseconde, vérification d'audit en 0.001 milliseconde."

**Screen**: Benchmark results table

### 2:50 — Conclusion (10 seconds)

> "Quantum Shield Core est un actif technique prêt pour l'acquisition, le partenariat ou l'intégration. Le code est disponible sous licence MIT sur GitHub. Merci."

**Screen**: GitHub repository page

---

## Recording Tips

| Tip | Detail |
|-----|--------|
| **Pace** | Speak slowly and clearly |
| **Mouse** | Move slowly, highlight key areas |
| **Terminal** | Use large font (16pt minimum) |
| **Errors** | If an error occurs, re-record the section |
| **Background** | Clean desktop, no personal files visible |
| **Audio** | Use a good microphone, no background noise |
| **Editing** | Cut unnecessary pauses, add transitions |

---

## Tools

| Tool | Purpose |
|------|---------|
| OBS Studio | Screen recording (free) |
| QuickTime | Screen recording (macOS) |
| Audacity | Audio editing (free) |
| DaVinci Resolve | Video editing (free) |

---

## Checklist Before Recording

- [ ] Service is running (`docker compose up`)
- [ ] API key is set
- [ ] Terminal font is large enough
- [ ] Desktop is clean
- [ ] Microphone is working
- [ ] Do Not Disturb is on
- [ ] Script is reviewed

---

## File Naming

```
videos/quantum-shield-demo-3min.mp4
```

---

*The video should be honest, professional, and representative of the actual project.*