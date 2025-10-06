# Guia de Deploy no Kubernetes

Este diretório contém manifests de Kubernetes e values do Helm para deploy do Argus Agent em diferentes ambientes.

## Estrutura de Diretórios

```
k8s/
├── dev/              # Ambiente de desenvolvimento
│   ├── *.yaml        # Manifests puros de K8s para dev
│   └── values.yaml   # Values do Helm para dev
├── staging/          # Ambiente de staging
│   └── values.yaml   # Values do Helm para staging
└── prod/             # Ambiente de produção
    └── values.yaml   # Values do Helm para produção
```

## Início Rápido

### Opção 1: Usando Manifests puros (Desenvolvimento)

1. **Criar namespace e secrets:**
   ```bash
   kubectl apply -f k8s/dev/namespace.yaml

   # Gerar secret a partir do .env
   make generate-k8s-secret
   # OU manualmente:
   ./scripts/generate-k8s-secret.sh argus-dev k8s/dev/secret.yaml

   # Aplicar o secret gerado
   kubectl apply -f k8s/dev/secret.yaml
   ```

   **⚠️ IMPORTANTE:** `secret.yaml` está no `.gitignore`. Nunca comite!

2. **Fazer deploy da aplicação:**
   ```bash
   kubectl apply -f k8s/dev/
   ```

3. **Checar o deploy:**
   ```bash
   kubectl get pods -n argus-dev
   kubectl get svc -n argus-dev
   ```

4. **Acessar a aplicação:**
   ```bash
   kubectl port-forward -n argus-dev svc/argus-app 8000:8000
   # Acesse http://localhost:8000
   ```

### Opção 2: Usando Helm (Recomendado)

1. **Criar secrets (se não usar secrets externos):**
   ```bash
   kubectl create namespace argus-dev

   kubectl create secret generic argus-secrets \
     --namespace=argus-dev \
     --from-literal=OPENAI_API_KEY="sk-..." \
     --from-literal=ES_HOST="https://your-es-host" \
     --from-literal=ES_USER="elastic" \
     --from-literal=ES_PASSWORD="your-password"
   ```

2. **Instalar com Helm:**
   ```bash
   # Development (usando make para criar secrets a partir do .env)
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

   # Produção
   helm install argus-prod ./helm/argus-agent \
     --namespace argus-production \
     --create-namespace \
     --values k8s/prod/values.yaml
   ```

3. **Upgrade de um deployment existente:**
   ```bash
   helm upgrade argus-dev ./helm/argus-agent \
     --namespace argus-dev \
     --values k8s/dev/values.yaml
   ```

4. **Desinstalar:**
   ```bash
   helm uninstall argus-dev --namespace argus-dev
   ```

## Usando Tilt no Desenvolvimento

Para melhor experiência com hot-reload:

1. **Instalar Tilt:**
   ```bash
   # macOS
   brew install tilt-dev/tap/tilt

   # Linux
   curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
   ```

2. **Configurar ambiente:**
   ```bash
   # Garanta que exista .env com suas credenciais
   cp .env.example .env
   # Edite o .env com seus valores
   ```

3. **Iniciar Tilt:**
   ```bash
   tilt up
   ```

   **O Tilt fará automaticamente:**
   - Carrega variáveis do `.env`
   - Gera ConfigMap e Secret a partir do `.env`
   - Faz deploy no Kubernetes
   - Configura port forwarding
   - Rebuild ao mudar o código

4. **Abrir a UI do Tilt:**
   - Pressione `space` ou acesse http://localhost:10350

**Observação:** o Tilt lê do `.env` e gera secrets dinamicamente. Não é necessário criar `secret.yaml` manualmente.

## Configuração por Ambiente

### Development (k8s/dev/values.yaml)
- Réplica única
- Service NodePort
- Segurança relaxada
- Limites de recursos pequenos
- Ingress local (argus-dev.local)

### Staging (k8s/staging/values.yaml)
- 2 réplicas com autoscaling (2-5)
- Service ClusterIP
- SSL com Let's Encrypt staging
- Limites médios
- Ingress público

### Production (k8s/prod/values.yaml)
- 3 réplicas com autoscaling (3-10)
- Service ClusterIP
- SSL com Let's Encrypt produção
- Limites altos
- Anti-affinity para alta disponibilidade
- Pod Disruption Budget

## Gestão de Secrets

**⚠️ Nunca comite secrets no git!**

### Opção 1: Secrets Manuais (Dev)
```bash
kubectl create secret generic argus-secrets \
  --namespace=argus-dev \
  --from-literal=OPENAI_API_KEY="..." \
  --from-literal=ANTHROPIC_API_KEY="..." \
  --from-literal=ES_HOST="..." \
  --from-literal=ES_USER="..." \
  --from-literal=ES_PASSWORD="..."
```

### Opção 2: External Secrets Operator (Prod)
Use o [External Secrets Operator](https://external-secrets.io/) para sincronizar de AWS Secrets Manager, Azure Key Vault ou HashiCorp Vault.

### Opção 3: Sealed Secrets
Use o [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) para criptografar secrets no git.

## Monitoramento e Troubleshooting

### Ver Logs
```bash
# Aplicação principal
kubectl logs -n argus-dev -l app=argus-app --tail=100 -f

# MCP Server
kubectl logs -n argus-dev -l app=argus-mcp-server --tail=100 -f
```

### Descrever Pods
```bash
kubectl describe pod -n argus-dev <pod-name>
```

### Executar Comandos no Pod
```bash
kubectl exec -it -n argus-dev <pod-name> -- /bin/sh
```

### Ver Uso de Recursos
```bash
kubectl top pods -n argus-dev
kubectl top nodes
```

## Configuração de Ingress

### Instalar NGINX Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### Instalar Cert-Manager (para SSL)
```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

### Ingress Local (Dev)
Adicionar em `/etc/hosts`:
```
127.0.0.1 argus-dev.local
```

## Storage

A aplicação usa um PersistentVolumeClaim para armazenar o ChromaDB:
- **Development:** 2Gi, storage class padrão
- **Staging:** 5Gi, storage class padrão
- **Production:** 20Gi, storage class fast-ssd (ajuste conforme o cluster)

Certifique-se de ter um StorageClass padrão no cluster ou especifique um em values.yaml.
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
