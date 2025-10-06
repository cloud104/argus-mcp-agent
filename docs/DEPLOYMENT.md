# Argus Agent - Guia de Deploy

Guia completo para realizar o deploy do Argus Agent em diferentes ambientes utilizando contêineres.

## Sumário

- [Setup de Desenvolvimento](#setup-de-desenvolvimento)
- [Docker Compose](#docker-compose)
- [Deploy em Kubernetes](#deploy-em-kubernetes)
- [Desenvolvimento com Tilt](#desenvolvimento-com-tilt)
- [Deploy em Produção](#deploy-em-produção)
- [Solução de Problemas](#solução-de-problemas)

## Setup de Desenvolvimento

### Pré-requisitos

- Python 3.13+
- Docker e Docker Compose
- kubectl (para deploy no Kubernetes)
- Helm 3.x (para deploy com Helm)
- Tilt (opcional, para fluxo de dev acelerado)

### Início Rápido com Docker Compose

1. **Clonar e preparar:**
   ```bash
   git clone <repository-url>
   cd argus-mcp-agent
   cp .env.example .env
   # Edite o .env com suas credenciais
   ```

2. **Build e subir:**
   ```bash
   docker-compose up --build
   ```

3. **Acesse a aplicação:**
   - App principal: http://localhost:8000
   - MCP Server: http://localhost:8002

## Docker Compose

### Desenvolvimento Padrão

```bash
# Iniciar todos os serviços
docker-compose up

# Iniciar em background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down

# Rebuild e start
docker-compose up --build
```

### Desenvolvimento com Debugging

Use `docker-compose.dev.yml` para debugging com VS Code ou PyCharm:

```bash
docker-compose -f docker-compose.dev.yml up
```

**Configuração VS Code (.vscode/launch.json):**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Remote Attach (App)",
      "type": "python",
      "request": "attach",
      "connect": { "host": "localhost", "port": 5678 },
      "pathMappings": [{ "localRoot": "${workspaceFolder}", "remoteRoot": "/app" }]
    },
    {
      "name": "Python: Remote Attach (MCP Server)",
      "type": "python",
      "request": "attach",
      "connect": { "host": "localhost", "port": 5679 },
      "pathMappings": [{ "localRoot": "${workspaceFolder}", "remoteRoot": "/app" }]
    }
  ]
}
```

## Deploy em Kubernetes

### Ambiente de Desenvolvimento

1. **Criar secrets:**
   ```bash
   kubectl create namespace argus-dev

   kubectl create secret generic argus-secrets \
     --namespace=argus-dev \
     --from-literal=OPENAI_API_KEY="sk-..." \
     --from-literal=ANTHROPIC_API_KEY="sk-ant-..." \
     --from-literal=ES_HOST="https://your-es-host" \
     --from-literal=ES_USER="elastic" \
     --from-literal=ES_PASSWORD="your-password"
   ```

2. **Deploy usando manifests puros:**
   ```bash
   kubectl apply -f k8s/dev/
   ```

   **Ou usando Helm:**
   ```bash
   helm install argus-dev ./helm/argus-agent \
     --namespace argus-dev \
     --create-namespace \
     --values k8s/dev/values.yaml
   ```

3. **Verifique o deploy:**
   ```bash
   kubectl get pods -n argus-dev
   kubectl get svc -n argus-dev
   ```

4. **Acesse a aplicação:**
   ```bash
   kubectl port-forward -n argus-dev svc/argus-app 8000:8000
   # Acesse http://localhost:8000
   ```

### Ambiente de Staging

```bash
# Build e tag das imagens
docker build -t your-registry/argus-app:staging .
docker build -f Dockerfile.dev -t your-registry/argus-mcp-server:staging .

# Push para o registry
docker push your-registry/argus-app:staging
docker push your-registry/argus-mcp-server:staging

# Deploy com Helm
helm install argus-staging ./helm/argus-agent \
  --namespace argus-staging \
  --create-namespace \
  --values k8s/staging/values.yaml \
  --set image.registry=your-registry \
  --set image.tag=staging
```

### Ambiente de Produção

```bash
# Build das imagens de produção
docker build -t your-registry/argus-app:1.0.0 .
docker build -f Dockerfile.dev -t your-registry/argus-mcp-server:1.0.0 .

# Push para o registry
docker push your-registry/argus-app:1.0.0
docker push your-registry/argus-mcp-server:1.0.0

# Deploy com Helm
helm install argus-prod ./helm/argus-agent \
  --namespace argus-production \
  --create-namespace \
  --values k8s/prod/values.yaml \
  --set image.registry=your-registry \
  --set image.tag=1.0.0
```

## Desenvolvimento com Tilt

O Tilt oferece a melhor experiência de desenvolvimento com Kubernetes:

### Setup

1. **Instalar Tilt:**
   ```bash
   # macOS
   brew install tilt-dev/tap/tilt

   # Linux
   curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
   ```

2. **Iniciar Tilt:**
   ```bash
   tilt up
   ```

3. **Abrir a UI do Tilt:**
   Pressione `space` ou acesse http://localhost:10350

### Funcionalidades

- **Live Reload:** alterações em arquivos Python são aplicadas sem rebuild
- **Web UI:** monitore serviços, logs e status de build
- **Ações Manuais:** rode testes, lint e format via botões
- **Port Forwarding:** acesse localhost:8000 e localhost:8002

### Comandos Tilt

```bash
# Iniciar Tilt
tilt up

# Modo CI (sem UI)
tilt ci

# Parar Tilt
tilt down

# Ver logs de um recurso
tilt logs argus-app
```

## Deploy em Produção

### Build de Imagens

**Build multi-stage (produção):**
```bash
docker build -t argus-agent:latest .
```

A imagem de produção:
- Usa base distroless para reduzir superfície de ataque
- Executa como usuário não-root (uid 65532)
- Sem shell/gerenciador de pacotes
- Tamanho e segurança otimizados

### Configuração de Ingress

1. **Instalar NGINX Ingress Controller:**
   ```bash
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm install ingress-nginx ingress-nginx/ingress-nginx \
     --namespace ingress-nginx \
     --create-namespace
   ```

2. **Instalar Cert-Manager:**
   ```bash
   helm repo add jetstack https://charts.jetstack.io
   helm install cert-manager jetstack/cert-manager \
     --namespace cert-manager \
     --create-namespace \
     --set installCRDs=true
   ```

3. **Configurar DNS:**
   Aponte o domínio para o IP do LoadBalancer:
   ```bash
   kubectl get svc -n ingress-nginx
   # Ex.: criar registro A: argus.example.com -> EXTERNAL-IP
   ```

4. **Habilitar Ingress no values:**
   ```yaml
   ingress:
     enabled: true
     className: "nginx"
     hosts:
       - host: argus.example.com
         paths:
           - path: /
             pathType: Prefix
     tls:
       - secretName: argus-prod-tls
         hosts:
           - argus.example.com
   ```

### Monitoramento

1. **Ver logs:**
   ```bash
   # App principal
   kubectl logs -n argus-production -l app=argus-app --tail=100 -f

   # MCP Server
   kubectl logs -n argus-production -l app=argus-mcp-server --tail=100 -f
   ```

2. **Monitorar recursos:**
   ```bash
   kubectl top pods -n argus-production
   kubectl top nodes
   ```

3. **Health checks:**
   ```bash
   kubectl get pods -n argus-production
   kubectl describe pod -n argus-production <pod-name>
   ```

### Escalonamento

**Escalonamento manual:**
```bash
kubectl scale deployment argus-app \
  --replicas=5 \
  --namespace=argus-production
```

**Auto-scaling (HPA):**
Já configurado nos values de produção. A aplicação escalará de 3 a 10 réplicas com base em CPU/memória.

### Atualizações

**Rolling update:**
```bash
helm upgrade argus-prod ./helm/argus-agent \
  --namespace argus-production \
  --values k8s/prod/values.yaml \
  --set image.tag=1.1.0
```

**Rollback:**
```bash
helm rollback argus-prod --namespace argus-production
```

## Solução de Problemas

### Problemas Comuns

**Pods não iniciam:**
```bash
kubectl describe pod -n <namespace> <pod-name>
kubectl logs -n <namespace> <pod-name>
```

**Conexão recusada ao MCP server:**
- Verifique se o pod do MCP está rodando
- Verifique resolução DNS do serviço: `kubectl exec -it <app-pod> -- nslookup argus-mcp-server`
- Cheque logs de ambos os serviços

**Problemas de storage:**
```bash
kubectl get pvc -n <namespace>
kubectl describe pvc argus-chroma-pvc -n <namespace>
```

**Problemas com secrets:**
```bash
kubectl get secrets -n <namespace>
kubectl describe secret argus-secrets -n <namespace>
```

### Debug em Contêineres

**Executar shell no pod (imagem dev):**
```bash
kubectl exec -it -n argus-dev <pod-name> -- /bin/bash
```

**Produção (distroless) com debug efêmero:**
```bash
kubectl debug -it <pod-name> \
  --image=busybox:1.28 \
  --target=<container-name>
```

### Ajustes de Performance

**Aumentar recursos:**
Edite `k8s/{env}/values.yaml`:
```yaml
app:
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"
```

**Ajustar HPA:**
```yaml
app:
  autoscaling:
    minReplicas: 5
    maxReplicas: 20
    targetCPUUtilizationPercentage: 60
```
# Argus Agent - Deployment Guide

Complete guide for deploying Argus Agent in different environments using containers.

## Table of Contents

- [Development Setup](#development-setup)
- [Docker Compose](#docker-compose)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Tilt Development](#tilt-development)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Development Setup

### Prerequisites

- Python 3.13+
- Docker and Docker Compose
- kubectl (for Kubernetes deployment)
- Helm 3.x (for Helm deployment)
- Tilt (optional, for enhanced dev workflow)

### Quick Start with Docker Compose

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd argus-mcp-agent
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Main App: http://localhost:8000
   - MCP Server: http://localhost:8002

## Docker Compose

### Standard Development

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and start
docker-compose up --build
```

### Development with Debugging

Use `docker-compose.dev.yml` for debugging with VS Code or PyCharm:

```bash
docker-compose -f docker-compose.dev.yml up
```

**VS Code Debug Configuration (.vscode/launch.json):**
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
    },
    {
      "name": "Python: Remote Attach (MCP Server)",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5679
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

## Kubernetes Deployment

### Development Environment

1. **Create secrets:**
   ```bash
   kubectl create namespace argus-dev

   kubectl create secret generic argus-secrets \
     --namespace=argus-dev \
     --from-literal=OPENAI_API_KEY="sk-..." \
     --from-literal=ANTHROPIC_API_KEY="sk-ant-..." \
     --from-literal=ES_HOST="https://your-es-host" \
     --from-literal=ES_USER="elastic" \
     --from-literal=ES_PASSWORD="your-password"
   ```

2. **Deploy using raw manifests:**
   ```bash
   kubectl apply -f k8s/dev/
   ```

   **OR using Helm:**
   ```bash
   helm install argus-dev ./helm/argus-agent \
     --namespace argus-dev \
     --create-namespace \
     --values k8s/dev/values.yaml
   ```

3. **Verify deployment:**
   ```bash
   kubectl get pods -n argus-dev
   kubectl get svc -n argus-dev
   ```

4. **Access the application:**
   ```bash
   kubectl port-forward -n argus-dev svc/argus-app 8000:8000
   # Visit http://localhost:8000
   ```

### Staging Environment

```bash
# Build and tag images
docker build -t your-registry/argus-app:staging .
docker build -f Dockerfile.dev -t your-registry/argus-mcp-server:staging .

# Push to registry
docker push your-registry/argus-app:staging
docker push your-registry/argus-mcp-server:staging

# Deploy with Helm
helm install argus-staging ./helm/argus-agent \
  --namespace argus-staging \
  --create-namespace \
  --values k8s/staging/values.yaml \
  --set image.registry=your-registry \
  --set image.tag=staging
```

### Production Environment

```bash
# Build production images
docker build -t your-registry/argus-app:1.0.0 .
docker build -f Dockerfile.dev -t your-registry/argus-mcp-server:1.0.0 .

# Push to registry
docker push your-registry/argus-app:1.0.0
docker push your-registry/argus-mcp-server:1.0.0

# Deploy with Helm
helm install argus-prod ./helm/argus-agent \
  --namespace argus-production \
  --create-namespace \
  --values k8s/prod/values.yaml \
  --set image.registry=your-registry \
  --set image.tag=1.0.0
```

## Tilt Development

Tilt provides the best development experience with Kubernetes:

### Setup

1. **Install Tilt:**
   ```bash
   # macOS
   brew install tilt-dev/tap/tilt

   # Linux
   curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
   ```

2. **Start Tilt:**
   ```bash
   tilt up
   ```

3. **Open Tilt UI:**
   Press `space` or visit http://localhost:10350

### Features

- **Live Reload:** Changes to Python files sync instantly without rebuilding
- **Web UI:** Monitor all services, logs, and build status
- **Manual Triggers:** Run tests, linting, and formatting with a button click
- **Port Forwarding:** Access services directly at localhost:8000 and localhost:8002

### Tilt Commands

```bash
# Start Tilt
tilt up

# Start in CI mode (no UI)
tilt ci

# Stop Tilt
tilt down

# View resource logs
tilt logs argus-app

# Trigger manual actions
# (Use Tilt UI buttons or tilt trigger command)
```

## Production Deployment

### Image Building

**Multi-stage production build:**
```bash
docker build -t argus-agent:latest .
```

The production image:
- Uses distroless base for minimal attack surface
- Runs as non-root user (uid 65532)
- No shell or package manager
- Optimized size and security

### Ingress Setup

1. **Install NGINX Ingress Controller:**
   ```bash
   helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
   helm install ingress-nginx ingress-nginx/ingress-nginx \
     --namespace ingress-nginx \
     --create-namespace
   ```

2. **Install Cert-Manager:**
   ```bash
   helm repo add jetstack https://charts.jetstack.io
   helm install cert-manager jetstack/cert-manager \
     --namespace cert-manager \
     --create-namespace \
     --set installCRDs=true
   ```

3. **Configure DNS:**
   Point your domain to the LoadBalancer IP:
   ```bash
   kubectl get svc -n ingress-nginx
   # Add A record: argus.example.com -> EXTERNAL-IP
   ```

4. **Enable Ingress in values:**
   ```yaml
   ingress:
     enabled: true
     className: "nginx"
     hosts:
       - host: argus.example.com
         paths:
           - path: /
             pathType: Prefix
     tls:
       - secretName: argus-prod-tls
         hosts:
           - argus.example.com
   ```

### Monitoring

1. **View logs:**
   ```bash
   # Application logs
   kubectl logs -n argus-production -l app=argus-app --tail=100 -f

   # MCP Server logs
   kubectl logs -n argus-production -l app=argus-mcp-server --tail=100 -f
   ```

2. **Resource monitoring:**
   ```bash
   kubectl top pods -n argus-production
   kubectl top nodes
   ```

3. **Health checks:**
   ```bash
   kubectl get pods -n argus-production
   kubectl describe pod -n argus-production <pod-name>
   ```

### Scaling

**Manual scaling:**
```bash
kubectl scale deployment argus-app \
  --replicas=5 \
  --namespace=argus-production
```

**Auto-scaling (HPA):**
Already configured in production values. The app will scale from 3 to 10 replicas based on CPU/memory usage.

### Updates

**Rolling update:**
```bash
helm upgrade argus-prod ./helm/argus-agent \
  --namespace argus-production \
  --values k8s/prod/values.yaml \
  --set image.tag=1.1.0
```

**Rollback:**
```bash
helm rollback argus-prod --namespace argus-production
```

## Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod -n <namespace> <pod-name>
kubectl logs -n <namespace> <pod-name>
```

**Connection refused to MCP server:**
- Check if MCP server pod is running
- Verify service DNS resolution: `kubectl exec -it <app-pod> -- nslookup argus-mcp-server`
- Check logs for both services

**Storage issues:**
```bash
kubectl get pvc -n <namespace>
kubectl describe pvc argus-chroma-pvc -n <namespace>
```

**Secret issues:**
```bash
kubectl get secrets -n <namespace>
kubectl describe secret argus-secrets -n <namespace>
```

### Debug Containers

**Execute shell in pod (dev image only):**
```bash
kubectl exec -it -n argus-dev <pod-name> -- /bin/bash
```

**For production (distroless), use ephemeral debug container:**
```bash
kubectl debug -it <pod-name> \
  --image=busybox:1.28 \
  --target=<container-name>
```

### Performance Tuning

**Increase resources:**
Edit `k8s/{env}/values.yaml`:
```yaml
app:
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"
```

**Adjust HPA:**
```yaml
app:
  autoscaling:
    minReplicas: 5
    maxReplicas: 20
    targetCPUUtilizationPercentage: 60
```

## Security Best Practices

1. **Never commit secrets to git**
2. **Use External Secrets Operator in production**
3. **Enable Network Policies**
4. **Keep base images updated**
5. **Run vulnerability scans on images**
6. **Use RBAC and least privilege**
7. **Enable audit logging**
8. **Use secure TLS configurations**

## Backup and Disaster Recovery

### Backup ChromaDB

```bash
# Create backup job
kubectl create job argus-backup \
  --from=cronjob/argus-chroma-backup \
  --namespace=argus-production

# Or manually copy
kubectl exec -n argus-production <pod-name> -- \
  tar czf /tmp/chroma-backup.tar.gz /app/chroma_db
kubectl cp argus-production/<pod-name>:/tmp/chroma-backup.tar.gz ./chroma-backup.tar.gz
```

### Restore

```bash
kubectl cp ./chroma-backup.tar.gz argus-production/<pod-name>:/tmp/
kubectl exec -n argus-production <pod-name> -- \
  tar xzf /tmp/chroma-backup.tar.gz -C /app/
```
