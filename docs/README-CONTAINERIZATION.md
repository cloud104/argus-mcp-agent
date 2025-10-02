# Containerization Guide - Argus Agent

This document explains the containerization setup created for Argus Agent.

## What Was Created

### Docker Files

1. **Dockerfile** - Production image
   - Multi-stage build with Python 3.13
   - Final stage uses distroless base (minimal attack surface)
   - Runs as non-root user (uid 65532)
   - Optimized for production

2. **Dockerfile.dev** - Development image
   - Based on Python 3.13-slim
   - Includes debugging tools (debugpy, ipdb)
   - Includes development tools (pytest, black, ruff, mypy)
   - Supports hot-reload

3. **docker-compose.yml** - Standard development setup
   - Two services: app and mcp-server
   - Volume mounts for live code changes
   - Health checks
   - Network isolation

4. **docker-compose.dev.yml** - Development with debugging
   - Same as docker-compose.yml but with debugpy enabled
   - Waits for debugger to attach before starting
   - Separate debug ports (5678 for app, 5679 for mcp-server)

5. **.dockerignore** - Optimizes build context
   - Excludes unnecessary files from Docker builds
   - Reduces image size and build time

### Kubernetes Manifests

#### k8s/dev/ - Development Environment
- `namespace.yaml` - argus-dev namespace
- `configmap.yaml` - Environment variables and config files
- `secret.yaml.example` - Template for secrets (DO NOT COMMIT actual secrets!)
- `mcp-server-deployment.yaml` - MCP server deployment
- `app-deployment.yaml` - Main app deployment
- `services.yaml` - ClusterIP services for both apps
- `pvc.yaml` - PersistentVolumeClaim for ChromaDB storage
- `values.yaml` - Helm values override for development

#### k8s/staging/ - Staging Environment
- `values.yaml` - Helm values for staging (2-5 replicas, autoscaling, SSL)

#### k8s/prod/ - Production Environment
- `values.yaml` - Helm values for production (3-10 replicas, HA, pod anti-affinity)

### Helm Chart

Located in `helm/argus-agent/`:

**Structure:**
```
helm/argus-agent/
├── Chart.yaml                    # Chart metadata
├── values.yaml                   # Default values
├── .helmignore                   # Files to exclude from chart
└── templates/
    ├── _helpers.tpl              # Template helpers
    ├── NOTES.txt                 # Post-install notes
    ├── namespace.yaml            # Namespace creation
    ├── serviceaccount.yaml       # Service account
    ├── configmap.yaml            # ConfigMaps
    ├── secret.yaml               # Secrets (if enabled)
    ├── pvc.yaml                  # Persistent storage
    ├── mcp-server-deployment.yaml # MCP server
    ├── app-deployment.yaml       # Main application
    ├── services.yaml             # Services
    ├── ingress.yaml              # Ingress (with SSL support)
    └── hpa.yaml                  # Horizontal Pod Autoscaler
```

**Features:**
- Multi-environment support (dev, staging, prod)
- Configurable resources, replicas, and autoscaling
- Ingress with SSL/TLS (cert-manager integration)
- Health checks (liveness, readiness)
- Security contexts
- Pod anti-affinity for HA
- ConfigMap/Secret management

### Tilt Development Workflow

**Tiltfile** - Provides hot-reload development in Kubernetes:
- Live sync of Python files (no rebuild needed)
- Automatic restarts on config changes
- Port forwarding (8000, 8002, debug ports)
- Manual triggers for tests, linting, formatting
- Web UI at http://localhost:10350

### CI/CD

**.github/workflows/docker-build.yml** - GitHub Actions workflow:
- Builds and pushes images on push to main/develop
- Creates tags for releases
- Scans images for vulnerabilities (Trivy)
- Uploads security results to GitHub

### Documentation

1. **DEPLOYMENT.md** - Complete deployment guide
   - Docker Compose usage
   - Kubernetes deployment steps
   - Tilt workflow
   - Production best practices
   - Troubleshooting

2. **k8s/README.md** - Kubernetes-specific guide
   - Quick start instructions
   - Environment-specific configs
   - Secrets management
   - Monitoring and troubleshooting

3. **CLAUDE.md** - Updated with containerization section
   - Docker commands
   - Kubernetes deployment
   - Tilt workflow
   - Image architecture
   - Secrets management

4. **Makefile** - Common commands
   - Development shortcuts
   - Docker build/push
   - Kubernetes deployment
   - Helm operations
   - Testing and linting

## Quick Start

### Using Docker Compose (Easiest)

```bash
# Standard development
docker-compose up

# With debugging
docker-compose -f docker-compose.dev.yml up
```

### Using Tilt (Best for K8s development)

```bash
tilt up
# Press space to open UI
```

### Using Kubernetes + Helm

```bash
# Create secrets
make create-k8s-secret

# Install
make helm-install-dev

# Access
kubectl port-forward -n argus-dev svc/argus-app 8000:8000
```

### Using Makefile

```bash
# See all available commands
make help

# Common commands
make dev              # Start docker-compose
make dev-debug        # Start with debugging
make helm-install-dev # Install with Helm
make tilt-up         # Start Tilt
make test            # Run tests
```

## Environment Comparison

| Feature | Development | Staging | Production |
|---------|------------|---------|------------|
| Replicas | 1 | 2-5 (HPA) | 3-10 (HPA) |
| Service Type | NodePort | ClusterIP | ClusterIP |
| Ingress | Local (argus-dev.local) | Yes (SSL staging) | Yes (SSL prod) |
| Resources | Low (128Mi-512Mi) | Medium (256Mi-1Gi) | High (512Mi-2Gi) |
| Security | Relaxed | Strict | Very Strict |
| Storage | 2Gi | 5Gi | 20Gi |
| Anti-affinity | No | No | Yes |
| PDB | No | No | Yes |

## Security Features

1. **Production Image:**
   - Distroless base (no shell, minimal packages)
   - Non-root user (uid 65532)
   - Multi-stage build (smaller surface)

2. **Kubernetes:**
   - Security contexts enforced
   - Secrets never in code
   - Network policies (can be added)
   - RBAC configured

3. **Best Practices:**
   - Health checks
   - Resource limits
   - Vulnerability scanning (Trivy)
   - Pod anti-affinity (prod)
   - Pod disruption budgets (prod)

## Next Steps

1. **Setup Container Registry:**
   - Create account on Docker Hub or private registry
   - Update `DOCKER_USERNAME` in Makefile
   - Add credentials to CI/CD secrets

2. **Configure Ingress:**
   - Install NGINX Ingress Controller
   - Install cert-manager for SSL
   - Configure DNS records

3. **External Secrets:**
   - Install External Secrets Operator
   - Configure secrets in AWS/Azure/Vault
   - Update Helm values to use external secrets

4. **Monitoring:**
   - Add Prometheus metrics
   - Configure Grafana dashboards
   - Set up alerting

5. **Backup:**
   - Create CronJob for ChromaDB backups
   - Configure backup storage

## Debugging

### VS Code

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Remote Attach (App)",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "/app"
        }
      ]
    }
  ]
}
```

Then:
1. Start with `docker-compose -f docker-compose.dev.yml up`
2. Attach debugger in VS Code (F5)
3. Set breakpoints and debug

## Common Issues

**Issue: Secrets not found**
- Solution: Create secrets with `make create-k8s-secret` or manually

**Issue: Images not pulling**
- Solution: Check registry credentials, image names, and network

**Issue: PVC not binding**
- Solution: Check storage class exists: `kubectl get storageclass`

**Issue: Services can't communicate**
- Solution: Check service names match DNS (argus-mcp-server:8002)

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [Tilt Documentation](https://docs.tilt.dev/)
- [External Secrets Operator](https://external-secrets.io/)
