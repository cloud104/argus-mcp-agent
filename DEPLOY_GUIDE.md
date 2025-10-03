# 🚀 Guia de Deploy - Argus Agent

Guia completo para deploy do Argus Agent no Kubernetes.

## 📋 Pré-requisitos

- ✅ Docker instalado e rodando
- ✅ kubectl configurado
- ✅ gcloud CLI instalado
- ✅ Acesso ao cluster Kubernetes
- ✅ Acesso ao GCR (`southamerica-east1-docker.pkg.dev/tcloud-devops`)

## ⚡ Deploy Rápido (Recomendado)

### Opção 1: Release Completa (Um único comando)

```bash
make docker-release
```

Este comando faz:
1. ✅ Login no GCR
2. ✅ Build das imagens com tags `latest` + `timestamp (YYYYMMDD-HHMMSS)`
3. ✅ Push de todas as tags para o GCR

**Resultado:**
- `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:latest`
- `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:20251003-143052`
- `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest`
- `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:20251003-143052`

### Opção 2: Deploy no Kubernetes

```bash
# Aplicar todas as configurações
kubectl apply -f k8s/dev/

# Verificar status
kubectl get pods -n argus-dev

# Ver logs
kubectl logs -f deployment/argus-app -n argus-dev
```

## 🐳 Comandos Docker Disponíveis

### Build

```bash
# Build apenas (tag latest)
make docker-build

# Build com timestamp (YYYYMMDD-HHMMSS)
make docker-build-timestamp

# Build com latest + timestamp
make docker-build-dual

# Build custom version
make docker-build VERSION=v1.2.3
```

### Push

```bash
# Push latest
make docker-push

# Push timestamp
make docker-push-timestamp

# Push latest + timestamp
make docker-push-dual
```

### Build + Push

```bash
# Build e push em um comando (latest)
make docker-build-push

# Build e push com timestamp
make docker-build-push-timestamp

# RELEASE COMPLETA (login + build + push latest + timestamp)
make docker-release
```

### Login

```bash
# Autenticar no GCR
make docker-login
```

## 📦 Workflow de Deploy Completo

### 1. Preparar Secrets

```bash
# Verificar se secret.yaml existe
ls -la k8s/dev/secret.yaml

# Se necessário, gerar JWT e MCP tokens novos
openssl rand -hex 32  # JWT_SECRET_KEY
openssl rand -hex 32  # MCP_SERVICE_TOKEN
```

### 2. Build e Push das Imagens

```bash
# Release completa (recomendado)
make docker-release

# Timestamp gerado: 20251003-143052
# Imagens criadas:
#   - argus-app:latest
#   - argus-app:20251003-143052
#   - argus-mcp-server:latest
#   - argus-mcp-server:20251003-143052
```

### 3. Deploy no Kubernetes

```bash
# Aplicar todas as configurações (ordem automática)
kubectl apply -f k8s/dev/

# OU aplicar manualmente na ordem correta:
kubectl apply -f k8s/dev/namespace.yaml
kubectl apply -f k8s/dev/secret.yaml
kubectl apply -f k8s/dev/pvc.yaml
kubectl apply -f k8s/dev/postgres-deployment.yaml
kubectl apply -f k8s/dev/chromadb-deployment.yaml
kubectl apply -f k8s/dev/configmap.yaml
kubectl apply -f k8s/dev/mcp-server-deployment.yaml
kubectl apply -f k8s/dev/app-deployment.yaml
kubectl apply -f k8s/dev/services.yaml
kubectl apply -f k8s/dev/ingress.yaml  # Opcional
```

### 4. Verificar Deployment

```bash
# Status dos pods
kubectl get pods -n argus-dev

# Status dos services
kubectl get svc -n argus-dev

# Status das secrets
kubectl get secrets -n argus-dev

# Logs do app
kubectl logs -f deployment/argus-app -n argus-dev

# Logs do MCP server
kubectl logs -f deployment/argus-mcp-server -n argus-dev

# Logs do PostgreSQL
kubectl logs -f deployment/argus-postgres -n argus-dev
```

### 5. Acessar Aplicação

```bash
# Via port-forward
kubectl port-forward -n argus-dev svc/argus-app 8000:8000

# Abrir navegador: http://localhost:8000
```

## 🔄 Update/Rollout

### Atualizar Imagens Existentes

```bash
# 1. Build e push novas versões
make docker-release

# 2. Restart dos deployments (força pull de :latest)
kubectl rollout restart deployment/argus-app -n argus-dev
kubectl rollout restart deployment/argus-mcp-server -n argus-dev

# 3. Acompanhar rollout
kubectl rollout status deployment/argus-app -n argus-dev
kubectl rollout status deployment/argus-mcp-server -n argus-dev
```

### Usar Tag Específica

```bash
# Build com versão específica
make docker-build VERSION=v1.2.3
make docker-push VERSION=v1.2.3

# Atualizar deployment para usar versão específica
kubectl set image deployment/argus-app \
  app=southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:v1.2.3 \
  -n argus-dev
```

### Rollback

```bash
# Ver histórico de rollouts
kubectl rollout history deployment/argus-app -n argus-dev

# Rollback para versão anterior
kubectl rollout undo deployment/argus-app -n argus-dev

# Rollback para revisão específica
kubectl rollout undo deployment/argus-app --to-revision=2 -n argus-dev
```

## 📊 Monitoramento

### Health Checks

```bash
# Liveness probe (processo rodando?)
curl http://localhost:8000/health/live

# Readiness probe (deps disponíveis?)
curl http://localhost:8000/health/ready

# Startup probe (inicialização completa?)
curl http://localhost:8000/health/startup
```

### Logs

```bash
# Logs em tempo real
kubectl logs -f deployment/argus-app -n argus-dev

# Logs de todos os pods de um deployment
kubectl logs -n argus-dev -l app=argus-app --tail=100 -f

# Logs de container específico em pod com múltiplos containers
kubectl logs -n argus-dev <pod-name> -c app
```

### Recursos

```bash
# Ver uso de recursos
kubectl top pods -n argus-dev

# Descrever pod (eventos, status, etc)
kubectl describe pod <pod-name> -n argus-dev
```

## 🗑️ Limpeza

```bash
# Deletar tudo exceto PVCs
kubectl delete -f k8s/dev/ --exclude=pvc.yaml

# Deletar namespace inteiro (CUIDADO: remove tudo)
kubectl delete namespace argus-dev

# Limpar Docker local
make clean-docker
```

## 🏷️ Tags e Versionamento

### Estratégias de Tag

1. **latest** - Sempre a versão mais recente (deployment contínuo)
2. **timestamp** - Identificação única por build (ex: `20251003-143052`)
3. **semver** - Versionamento semântico (ex: `v1.2.3`)
4. **commit-sha** - Hash do commit git (ex: `a1b2c3d`)

### Comandos Úteis

```bash
# Latest + timestamp (recomendado)
make docker-release

# Apenas timestamp
make docker-build-push-timestamp

# Custom version
make docker-build-push VERSION=v1.2.3

# Tag de imagem existente
make docker-tag VERSION=v1.2.3
make docker-push VERSION=v1.2.3
```

## 🔐 Secrets Management

### Arquivos de Secrets

- `k8s/dev/secret.yaml` - **NÃO COMITAR** (está no .gitignore)
- Contém:
  - `gcr-json-key` - Pull secret para GCR
  - `argus-secrets` - Credenciais da aplicação
  - `postgres-secret` - Credenciais do PostgreSQL

### Atualizar Secrets

```bash
# 1. Editar secret.yaml
vim k8s/dev/secret.yaml

# 2. Aplicar mudanças
kubectl apply -f k8s/dev/secret.yaml

# 3. Restart pods para usar novos secrets
kubectl rollout restart deployment/argus-app -n argus-dev
kubectl rollout restart deployment/argus-mcp-server -n argus-dev
```

### Gerar Novos Tokens

```bash
# JWT Secret Key
openssl rand -hex 32

# MCP Service Token
openssl rand -hex 32
```

## 🎯 Checklist de Deploy

### Antes do Deploy

- [ ] Código testado localmente com `make dev`
- [ ] Docker Compose funcionando (`docker-compose up`)
- [ ] Secrets configurados em `k8s/dev/secret.yaml`
- [ ] kubectl configurado e conectado ao cluster correto
- [ ] GCR authentication configurado (`make docker-login`)

### Durante o Deploy

- [ ] Build das imagens (`make docker-build-dual`)
- [ ] Push para GCR (`make docker-push-dual`)
- [ ] Apply dos manifestos K8s (`kubectl apply -f k8s/dev/`)
- [ ] Verificar pods healthy (`kubectl get pods -n argus-dev`)

### Após o Deploy

- [ ] Health checks passando (live, ready, startup)
- [ ] Logs sem erros críticos
- [ ] Login funcionando (admin/admin123)
- [ ] Análise de logs funcionando
- [ ] Deep dive analysis funcionando

## 📞 Troubleshooting

### ImagePullBackOff

```bash
# Verificar secret
kubectl get secret gcr-json-key -n argus-dev -o yaml

# Ver detalhes do erro
kubectl describe pod <pod-name> -n argus-dev
```

**Solução**: Verificar se `imagePullSecrets` está configurado no deployment

### CrashLoopBackOff

```bash
# Ver logs do container
kubectl logs <pod-name> -n argus-dev

# Ver eventos do pod
kubectl describe pod <pod-name> -n argus-dev
```

**Soluções comuns**:
- Verificar variáveis de ambiente
- Verificar secrets montados
- Verificar conectividade com PostgreSQL/Elasticsearch

### PostgreSQL Connection Failed

```bash
# Verificar se PostgreSQL está rodando
kubectl get pods -n argus-dev | grep postgres

# Testar conexão do pod da app
kubectl exec -it deployment/argus-app -n argus-dev -- \
  psql -h argus-postgres -U argus -d argus_auth
```

## 🔗 Links Úteis

- Registry: https://console.cloud.google.com/artifacts/docker/tcloud-devops/southamerica-east1/tcloud-devops
- Kubernetes Dashboard: (se configurado)
- Logs: (Grafana/Kibana se configurado)

## 🎓 Comandos Make Disponíveis

```bash
# Ver todos os comandos disponíveis
make help
```

**Principais:**
- `make docker-release` - Release completa (login + build + push com latest + timestamp)
- `make docker-build-dual` - Build com latest + timestamp
- `make docker-push-dual` - Push latest + timestamp
- `make k8s-dev-deploy` - Deploy no K8s dev
- `make k8s-dev-port-forward` - Port forward para 8000
- `make dev` - Rodar localmente com Docker Compose
