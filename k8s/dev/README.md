# Argus Agent - Kubernetes Development Environment

Deployment configuration for Argus Agent on Kubernetes (development environment).

## 📋 Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Access to Google Container Registry (`southamerica-east1-docker.pkg.dev/tcloud-devops`)

## 🔐 Secrets Configuration

**IMPORTANT**: The `secret.yaml` file contains sensitive credentials and is in `.gitignore`.

### Secrets Structure

The deployment uses 3 secrets:

1. **`gcr-json-key`**: Image Pull Secret for GCR
2. **`argus-secrets`**: Application secrets (API keys, ES credentials, JWT tokens)
3. **`postgres-secret`**: PostgreSQL database credentials

All secrets are already configured in `secret.yaml`.

## 🚀 Quick Deploy

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Apply Secrets

```bash
kubectl apply -f secret.yaml
```

### 3. Create Persistent Volume Claim

```bash
kubectl apply -f pvc.yaml
```

### 4. Deploy Infrastructure (PostgreSQL, ChromaDB)

```bash
kubectl apply -f postgres-deployment.yaml
kubectl apply -f chromadb-deployment.yaml
```

### 5. Deploy ConfigMaps

```bash
kubectl apply -f configmap.yaml
```

### 6. Deploy Application

```bash
kubectl apply -f mcp-server-deployment.yaml
kubectl apply -f app-deployment.yaml
```

### 7. Create Services

```bash
kubectl apply -f services.yaml
```

### 8. (Optional) Create Ingress

```bash
kubectl apply -f ingress.yaml
```

## ⚡ One-Command Deploy

```bash
kubectl apply -f .
```

This will apply all manifests in the correct order.

## 📊 Verify Deployment

```bash
# Check all pods
kubectl get pods -n argus-dev

# Check services
kubectl get svc -n argus-dev

# Check secrets
kubectl get secrets -n argus-dev

# Check logs
kubectl logs -f deployment/argus-app -n argus-dev
kubectl logs -f deployment/argus-mcp-server -n argus-dev
```

## 🔍 Troubleshooting

### ImagePullBackOff Error

If you see `ImagePullBackOff` errors:

```bash
# Check image pull secret
kubectl get secret gcr-json-key -n argus-dev

# Describe pod to see error details
kubectl describe pod <pod-name> -n argus-dev
```

### PostgreSQL Connection Issues

```bash
# Check PostgreSQL logs
kubectl logs -f deployment/argus-postgres -n argus-dev

# Test connection from app pod
kubectl exec -it deployment/argus-app -n argus-dev -- psql -h argus-postgres -U argus -d argus_auth
```

### Secrets Not Found

Make sure `secret.yaml` is applied:

```bash
kubectl apply -f secret.yaml
```

## 🌐 Accessing the Application

### Via Port Forward

```bash
# Forward app port
kubectl port-forward svc/argus-app 8000:8000 -n argus-dev

# Access at http://localhost:8000
```

### Via Ingress

If Ingress is configured:

```bash
# Get Ingress address
kubectl get ingress -n argus-dev
```

## 🗑️ Cleanup

```bash
# Delete all resources
kubectl delete -f .

# Or delete namespace (removes everything)
kubectl delete namespace argus-dev
```

## 📦 Components

| Component | Image | Port | Purpose |
|-----------|-------|------|---------|
| argus-app | `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:latest` | 8000 | Main application |
| argus-mcp-server | `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest` | 8002 | MCP tool server |
| argus-postgres | `postgres:16-alpine` | 5432 | Auth database |
| argus-chromadb | `chromadb/chroma:latest` | 8000 | Vector database |

## 🔒 Security Notes

- **Never commit `secret.yaml`** - It contains sensitive credentials
- Use strong passwords in production (change from defaults)
- Rotate JWT secrets regularly
- Enable RBAC and network policies
- Use TLS/SSL for Ingress in production

## 📝 Configuration Files

- `namespace.yaml` - Namespace definition
- `secret.yaml` - Secrets (NOT in git)
- `configmap.yaml` - Application configuration
- `pvc.yaml` - Persistent Volume Claims
- `postgres-deployment.yaml` - PostgreSQL deployment
- `chromadb-deployment.yaml` - ChromaDB deployment
- `mcp-server-deployment.yaml` - MCP server deployment
- `app-deployment.yaml` - Main app deployment
- `services.yaml` - Kubernetes services
- `ingress.yaml` - Ingress configuration

## 🔄 Update Deployment

After building new Docker images:

```bash
# Push images to GCR
docker push southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:latest
docker push southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest

# Restart deployments (with imagePullPolicy: Always)
kubectl rollout restart deployment/argus-app -n argus-dev
kubectl rollout restart deployment/argus-mcp-server -n argus-dev

# Watch rollout status
kubectl rollout status deployment/argus-app -n argus-dev
```

## 🏷️ Default Credentials

**Admin User:**
- Username: `admin`
- Password: `admin123` (change in production!)

**PostgreSQL:**
- User: `argus`
- Password: `argus123` (change in production!)
- Database: `argus_auth`
