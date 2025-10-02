# Build e Publicação Local de Imagens

Este guia explica como construir e publicar as imagens Docker do Argus Agent localmente para o Google Artifact Registry.

## Pré-requisitos

1. **Docker** instalado e rodando
2. **Google Cloud SDK (gcloud)** instalado
3. **Autenticação GCP** configurada
4. **Permissões** para push no Artifact Registry

## Configuração Inicial

### 1. Autenticar no GCP

```bash
# Login no GCP
gcloud auth login

# Configurar projeto
gcloud config set project tcloud-devops
```

### 2. Configurar Docker para Artifact Registry

```bash
# Configurar autenticação (uma vez)
make docker-login

# Ou manualmente:
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
```

## Build e Publicação

### Workflow Completo

```bash
# 1. Build das imagens de produção
make docker-build

# 2. Push para o registry
make docker-push

# Ou fazer tudo de uma vez:
make docker-build-push
```

### Build com Versão Específica

```bash
# Build com tag customizada
make docker-build VERSION=v1.2.3

# Push da versão específica
make docker-push VERSION=v1.2.3

# Ou tudo junto:
make docker-build-push VERSION=v1.2.3
```

### Criar Tags Adicionais

```bash
# Criar tag a partir do latest
make docker-tag VERSION=v1.2.3

# Push da nova tag
make docker-push VERSION=v1.2.3
```

## Imagens Geradas

O build cria **duas imagens** a partir do mesmo Dockerfile usando multi-stage build:

### 1. App Principal
```
southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:latest
southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:v1.2.3
```

**Características:**
- Porta: 8000
- Comando: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Distroless Python 3.13
- Non-root user (uid 65532)

### 2. MCP Server
```
southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest
southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:v1.2.3
```

**Características:**
- Porta: 8002
- Comando: `uvicorn tools.server:app --host 0.0.0.0 --port 8002`
- Distroless Python 3.13
- Non-root user (uid 65532)

## Estrutura do Dockerfile

O `Dockerfile` usa multi-stage build com 4 estágios:

```dockerfile
# Stage 1: builder - Instala dependências e compila
FROM python:3.13-slim as builder

# Stage 2: base - Imagem base com distroless
FROM gcr.io/distroless/python3-debian12 as base

# Stage 3: app - Aplicação principal
FROM base as app
EXPOSE 8000
CMD ["/usr/local/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage 4: mcp-server - MCP Server
FROM base as mcp-server
EXPOSE 8002
CMD ["/usr/local/bin/uvicorn", "tools.server:app", "--host", "0.0.0.0", "--port", "8002"]
```

## Uso das Imagens

### Docker Compose (Produção)

O `docker-compose.yml` já está configurado para usar as imagens do registry:

```yaml
services:
  app:
    image: southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:latest

  mcp-server:
    image: southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest
```

Uso:
```bash
# Pull e rodar
docker-compose pull
docker-compose up
```

### Kubernetes / Helm

As imagens são configuradas nos values files:

```yaml
# k8s/prod/values.yaml
image:
  registry: southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops
  tag: "1.0.0"

app:
  image:
    tag: "1.0.0"

mcpServer:
  image:
    tag: "1.0.0"
```

Deploy:
```bash
# Development
make helm-install-dev

# Production com versão específica
make helm-install-prod VERSION=v1.2.3
```

## Desenvolvimento Local

Para desenvolvimento, use as imagens de desenvolvimento (com debugging tools):

```bash
# Build imagens de dev
make docker-build-dev

# Rodar com docker-compose.dev.yml
make dev-debug
```

## Comandos Úteis

### Ver Imagens Locais
```bash
docker images | grep argus
```

### Inspecionar Imagem
```bash
docker inspect southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:latest
```

### Rodar Imagem Manualmente
```bash
# App
docker run -p 8000:8000 \
  --env-file .env \
  southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:latest

# MCP Server
docker run -p 8002:8002 \
  --env-file .env \
  southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest
```

### Limpar Imagens Antigas
```bash
# Remover imagens não usadas
docker image prune -a

# Remover tudo (cuidado!)
make clean-docker
```

## Troubleshooting

### Erro: "denied: Permission denied"
```bash
# Re-autenticar
gcloud auth login
make docker-login
```

### Erro: "manifest unknown"
```bash
# Verificar se a imagem existe no registry
gcloud artifacts docker images list \
  southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops
```

### Erro: "no space left on device"
```bash
# Limpar Docker
docker system prune -a --volumes
```

### Build Lento
```bash
# Usar BuildKit para builds mais rápidos
export DOCKER_BUILDKIT=1
make docker-build
```

## Boas Práticas

1. ✅ **Sempre use tags específicas em produção** (não use `latest`)
2. ✅ **Teste a imagem localmente antes do push**
3. ✅ **Use versioning semântico** (v1.2.3)
4. ✅ **Faça push apenas de código revisado**
5. ✅ **Documente mudanças no CHANGELOG**
6. ⚠️ **Não exponha credenciais nas imagens**

## Estratégia de Versionamento

Recomendações:

```bash
# Development (branch feature)
make docker-build-push VERSION=dev-$(git rev-parse --short HEAD)

# Staging (branch develop)
make docker-build-push VERSION=staging

# Production (tag git)
git tag v1.2.3
make docker-build-push VERSION=v1.2.3
```

## CI/CD Futuro

No futuro, usaremos **Google Cloud Build** para automatizar o processo:

```yaml
# cloudbuild.yaml (exemplo futuro)
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '--target', 'app', '-t', 'gcr.io/$PROJECT_ID/argus-app:$TAG_NAME', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '--target', 'mcp-server', '-t', 'gcr.io/$PROJECT_ID/argus-mcp-server:$TAG_NAME', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/argus-app:$TAG_NAME']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/argus-mcp-server:$TAG_NAME']
```

Por enquanto, **todo build e push é feito localmente** usando o Makefile.

## Referências

- [Google Artifact Registry Docs](https://cloud.google.com/artifact-registry/docs)
- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Distroless Base Images](https://github.com/GoogleContainerTools/distroless)
