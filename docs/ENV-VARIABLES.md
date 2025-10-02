# Environment Variables Guide

This document describes all environment variables used by Argus Agent and how they're managed across different deployment methods.

## Required Environment Variables

### LLM API Keys

At least one LLM provider is required:

```bash
# OpenAI (recommended for most models)
OPENAI_API_KEY=sk-...

# Anthropic (for Claude models)
ANTHROPIC_API_KEY=sk-ant-...

# Google (for Gemini models)
GOOGLE_API_KEY=...
```

### Elasticsearch Configuration

Required for log analysis:

```bash
ES_HOST=https://your-elasticsearch-host
ES_USER=elastic
ES_PASSWORD=your-password
```

## Optional Environment Variables

### Python Environment

```bash
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### ChromaDB Configuration

When using standalone ChromaDB service:

```bash
CHROMA_HOST=chromadb  # or localhost for local dev
CHROMA_PORT=8000
```

## Environment Variable Management

### Local Development (.env file)

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```bash
   # .env
   OPENAI_API_KEY=sk-your-actual-key
   ANTHROPIC_API_KEY=sk-ant-your-actual-key
   ES_HOST=https://your-elasticsearch-host
   ES_USER=elastic
   ES_PASSWORD=your-actual-password
   ```

3. **The `.env` file is used by:**
   - Direct Python execution (`uvicorn`)
   - Docker Compose (via `env_file:` directive)
   - Tilt (generates K8s secrets dynamically)
   - Makefile commands

**⚠️ IMPORTANT:** Never commit `.env` to git! It's in `.gitignore`.

### Docker Compose

Docker Compose automatically reads from `.env`:

```yaml
# docker-compose.yml
services:
  app:
    env_file:
      - .env  # ← Automatically loads all variables
```

**Usage:**
```bash
docker-compose up  # Automatically uses .env
```

### Kubernetes with Tilt

Tilt reads `.env` and generates Kubernetes secrets dynamically:

```python
# Tiltfile
load('ext://dotenv', 'dotenv')
dotenv()  # ← Loads .env

# Then generates Secret from env vars
def create_secret():
    import os
    openai_key = os.getenv('OPENAI_API_KEY', '')
    # ... creates K8s Secret
```

**Usage:**
```bash
tilt up  # Automatically reads .env and creates secrets
```

**Benefits:**
- No manual secret.yaml creation needed
- Secrets stay in sync with .env
- No risk of committing secrets to git
- Easy to update (just edit .env and restart Tilt)

### Kubernetes with Raw Manifests

#### Method 1: Generate from .env (Recommended)

```bash
# Generate secret.yaml from .env
make generate-k8s-secret

# Or manually:
./scripts/generate-k8s-secret.sh argus-dev k8s/dev/secret.yaml

# Apply
kubectl apply -f k8s/dev/secret.yaml
```

**⚠️ WARNING:** `secret.yaml` contains sensitive data and is in `.gitignore`. Never commit it!

#### Method 2: Manual kubectl create

```bash
# Load .env and create secret
make create-k8s-secret

# Or manually:
kubectl create secret generic argus-secrets \
  --namespace=argus-dev \
  --from-literal=OPENAI_API_KEY="sk-..." \
  --from-literal=ES_HOST="https://..." \
  # ... etc
```

### Kubernetes with Helm

#### Development/Staging

Use existing secret created from .env:

```bash
# Create secret from .env
make create-k8s-secret

# Install Helm chart (uses existing secret)
helm install argus-dev ./helm/argus-agent \
  --values k8s/dev/values.yaml \
  --set secrets.existingSecret=argus-secrets
```

#### Production

**Use External Secrets Operator** (recommended):

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: argus-secrets
spec:
  secretStoreRef:
    name: aws-secrets-manager  # or azure-keyvault, etc
  target:
    name: argus-secrets
  data:
  - secretKey: OPENAI_API_KEY
    remoteRef:
      key: argus/openai-api-key
  # ... etc
```

**Or use Sealed Secrets:**

```bash
# Create sealed secret (safe to commit)
kubectl create secret generic argus-secrets \
  --dry-run=client -o yaml \
  --from-literal=OPENAI_API_KEY="sk-..." | \
  kubeseal -o yaml > sealed-secret.yaml

# Commit sealed-secret.yaml to git
git add sealed-secret.yaml
```

## Environment-Specific Configuration

### Development

```bash
# .env (local file)
OPENAI_API_KEY=sk-dev-key
ES_HOST=https://dev-elasticsearch
```

**Used by:**
- Local uvicorn
- Docker Compose
- Tilt → K8s

### Staging

```bash
# Created via External Secrets or manual kubectl
OPENAI_API_KEY=sk-staging-key
ES_HOST=https://staging-elasticsearch
```

### Production

```bash
# Managed by External Secrets Operator
# Synced from AWS Secrets Manager / Azure Key Vault / Vault
OPENAI_API_KEY=<from-secret-manager>
ES_HOST=<from-secret-manager>
```

## Security Best Practices

### ✅ DO

1. **Use `.env` for local development**
   - Easy to manage
   - Automatically ignored by git
   - Works with all tools

2. **Use Tilt for K8s development**
   - Secrets generated dynamically
   - No secret.yaml files to manage
   - No risk of committing secrets

3. **Use External Secrets Operator for production**
   - Centralized secret management
   - Automatic rotation
   - Audit logging

4. **Rotate secrets regularly**
   - Update in secret manager
   - Restart deployments

5. **Use different secrets per environment**
   - dev keys ≠ staging keys ≠ prod keys

### ❌ DON'T

1. **Never commit `.env` to git**
   - Already in `.gitignore`
   - Contains actual credentials

2. **Never commit `secret.yaml` to git**
   - Already in `.gitignore`
   - Contains base64-encoded (not encrypted!) secrets

3. **Never hardcode secrets in code**
   - Always use environment variables

4. **Never share `.env` via chat/email**
   - Use secure secret sharing tools

5. **Never use production secrets in development**
   - Always use separate keys

## Troubleshooting

### "Secret not found" in Kubernetes

```bash
# Check if secret exists
kubectl get secrets -n argus-dev

# If missing, create from .env
make create-k8s-secret

# Or with Tilt
tilt up  # Will create automatically
```

### "Environment variable not set"

```bash
# Check if .env exists
ls -la .env

# Check if variable is in .env
grep OPENAI_API_KEY .env

# Check if Docker Compose loads it
docker-compose config | grep OPENAI_API_KEY
```

### "Invalid API key" errors

```bash
# Verify .env has correct values (no quotes issues)
cat .env

# For Docker Compose, rebuild
docker-compose down
docker-compose up --build

# For Tilt, restart
tilt down
tilt up
```

## Summary: Which Method When?

| Environment | Method | Source | Why |
|------------|--------|--------|-----|
| **Local Dev** | Python | `.env` | Simplest |
| **Docker Dev** | Docker Compose | `.env` | Auto-loaded |
| **K8s Dev (Tilt)** | Tilt | `.env` | Dynamic generation |
| **K8s Dev (Manual)** | kubectl/script | `.env` → secret.yaml | One-time setup |
| **Staging** | Helm | External Secrets | Centralized |
| **Production** | Helm | External Secrets | Secure & auditable |

## Reference

### Complete .env Template

```bash
# LLM API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Elasticsearch (required)
ES_HOST=https://your-elasticsearch-host
ES_USER=elastic
ES_PASSWORD=your-password

# Python (optional, defaults provided)
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# ChromaDB (optional, for standalone mode)
CHROMA_HOST=chromadb
CHROMA_PORT=8000
```

### Quick Commands

```bash
# Setup
make setup                    # Create .env from template

# Local dev
source .venv/bin/activate
uvicorn main:app --reload

# Docker
docker-compose up             # Uses .env automatically

# Tilt (K8s)
tilt up                       # Uses .env, generates secrets

# Manual K8s
make generate-k8s-secret      # Generate secret.yaml from .env
make create-k8s-secret        # Create secret via kubectl
make create-k8s-configmap     # Create configmap
```
