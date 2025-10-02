# Kubernetes Deployment Guide

This directory contains Kubernetes manifests and Helm values for deploying Argus Agent in different environments.

## Directory Structure

```
k8s/
├── dev/              # Development environment
│   ├── *.yaml        # Raw K8s manifests for dev
│   └── values.yaml   # Helm values for dev
├── staging/          # Staging environment
│   └── values.yaml   # Helm values for staging
└── prod/             # Production environment
    └── values.yaml   # Helm values for production
```

## Quick Start

### Option 1: Using Raw Kubernetes Manifests (Development)

1. **Create the namespace and secrets:**
   ```bash
   kubectl apply -f k8s/dev/namespace.yaml

   # Generate secret from .env file
   make generate-k8s-secret
   # OR manually:
   ./scripts/generate-k8s-secret.sh argus-dev k8s/dev/secret.yaml

   # Apply the generated secret
   kubectl apply -f k8s/dev/secret.yaml
   ```

   **⚠️ IMPORTANT:** `secret.yaml` is in `.gitignore`. Never commit it!

2. **Deploy the application:**
   ```bash
   kubectl apply -f k8s/dev/
   ```

3. **Check the deployment:**
   ```bash
   kubectl get pods -n argus-dev
   kubectl get svc -n argus-dev
   ```

4. **Access the application:**
   ```bash
   kubectl port-forward -n argus-dev svc/argus-app 8000:8000
   # Visit http://localhost:8000
   ```

### Option 2: Using Helm (Recommended)

1. **Create secrets (if not using external secrets manager):**
   ```bash
   kubectl create namespace argus-dev

   kubectl create secret generic argus-secrets \
     --namespace=argus-dev \
     --from-literal=OPENAI_API_KEY="sk-..." \
     --from-literal=ES_HOST="https://your-es-host" \
     --from-literal=ES_USER="elastic" \
     --from-literal=ES_PASSWORD="your-password"
   ```

2. **Install with Helm:**
   ```bash
   # Development (using make to create secrets from .env)
   make create-k8s-secret
   make create-k8s-configmap

   helm install argus-dev ./helm/argus-agent \
     --namespace argus-dev \
     --create-namespace \
     --values k8s/dev/values.yaml

   # Staging
   helm install argus-staging ./helm/argus-agent \
     --namespace argus-staging \
     --create-namespace \
     --values k8s/staging/values.yaml

   # Production
   helm install argus-prod ./helm/argus-agent \
     --namespace argus-production \
     --create-namespace \
     --values k8s/prod/values.yaml
   ```

3. **Upgrade an existing deployment:**
   ```bash
   helm upgrade argus-dev ./helm/argus-agent \
     --namespace argus-dev \
     --values k8s/dev/values.yaml
   ```

4. **Uninstall:**
   ```bash
   helm uninstall argus-dev --namespace argus-dev
   ```

## Using Tilt for Development

For a better development experience with hot-reload:

1. **Install Tilt:**
   ```bash
   # macOS
   brew install tilt-dev/tap/tilt

   # Linux
   curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
   ```

2. **Configure environment:**
   ```bash
   # Make sure .env file exists with your credentials
   cp .env.example .env
   # Edit .env with your values
   ```

3. **Start Tilt:**
   ```bash
   tilt up
   ```

   **Tilt will automatically:**
   - Load environment variables from `.env`
   - Generate ConfigMap and Secret from `.env`
   - Deploy to Kubernetes
   - Setup port forwarding
   - Rebuild on code changes

4. **Open Tilt UI:**
   - Press `space` or visit http://localhost:10350

**Note:** Tilt reads from `.env` and generates K8s secrets dynamically. You don't need to manually create `secret.yaml`.

## Environment-Specific Configuration

### Development (k8s/dev/values.yaml)
- Single replica
- NodePort service
- Relaxed security settings
- Small resource limits
- Local ingress (argus-dev.local)

### Staging (k8s/staging/values.yaml)
- 2 replicas with autoscaling (2-5)
- ClusterIP service
- SSL with Let's Encrypt staging
- Medium resource limits
- Public ingress

### Production (k8s/prod/values.yaml)
- 3 replicas with autoscaling (3-10)
- ClusterIP service
- SSL with Let's Encrypt production
- High resource limits
- Pod anti-affinity for HA
- Pod disruption budget

## Secrets Management

**⚠️ Never commit secrets to git!**

### Option 1: Manual Secrets (Development)
```bash
kubectl create secret generic argus-secrets \
  --namespace=argus-dev \
  --from-literal=OPENAI_API_KEY="..." \
  --from-literal=ANTHROPIC_API_KEY="..." \
  --from-literal=ES_HOST="..." \
  --from-literal=ES_USER="..." \
  --from-literal=ES_PASSWORD="..."
```

### Option 2: External Secrets Operator (Production)
Use [External Secrets Operator](https://external-secrets.io/) to sync from AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault.

### Option 3: Sealed Secrets
Use [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) to encrypt secrets in git.

## Monitoring and Troubleshooting

### View Logs
```bash
# Main application
kubectl logs -n argus-dev -l app=argus-app --tail=100 -f

# MCP Server
kubectl logs -n argus-dev -l app=argus-mcp-server --tail=100 -f
```

### Describe Pods
```bash
kubectl describe pod -n argus-dev <pod-name>
```

### Execute Commands in Pod
```bash
kubectl exec -it -n argus-dev <pod-name> -- /bin/sh
```

### Check Resource Usage
```bash
kubectl top pods -n argus-dev
kubectl top nodes
```

## Ingress Setup

### Install NGINX Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### Install Cert-Manager (for SSL)
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

### Local Development Ingress
Add to `/etc/hosts`:
```
127.0.0.1 argus-dev.local
```

## Storage

The application uses a PersistentVolumeClaim for ChromaDB storage:
- **Development:** 2Gi, standard storage class
- **Staging:** 5Gi, standard storage class
- **Production:** 20Gi, fast-ssd storage class (customize based on your cluster)

Make sure your cluster has a default StorageClass or specify one in values.yaml.
