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

### Build com Timestamp (Recomendado)

Para ambientes de desenvolvimento/staging, use tags com timestamp no formato `YYYYMMDD-HHMMSS`:

```bash
# Build e push com timestamp automático
make docker-build-push-timestamp

# Exemplo de tag gerada:
# southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:20250921-201146
# southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:20250921-201146
```

**Vantagens do timestamp:**
- ✅ Rastreabilidade: sabe exatamente quando a imagem foi criada
- ✅ Uniqueness: cada build gera uma tag única
- ✅ Rollback fácil: pode voltar para uma versão específica por data/hora
- ✅ Histórico: mantém histórico de todas as versões no registry

### Criar Tags Adicionais

```bash
# Criar tag a partir do latest
make docker-tag VERSION=v1.2.3

# Push da nova tag
make docker-push VERSION=v1.2.3
```

## Imagens Geradas

O build cria **duas imagens especializadas** usando Dockerfiles separados para máxima otimização:

### 1. App Principal (Dockerfile.app)
```
southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:latest
southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-app:v1.2.3
```

**Características:**
- Porta: 8000
- Comando: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Contém: `main.py`, `app/`, `prompts/`, `config/`
- **NÃO** contém: `tools/` (MCP server)
- Distroless Python 3.13
- Non-root user (uid 65532)
- **Mais enxuta**: apenas código da aplicação

### 2. MCP Server (Dockerfile.mcp)
```
southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest
southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:v1.2.3
```

**Características:**
- Porta: 8002
- Comando: `uvicorn tools.server:app --host 0.0.0.0 --port 8002`
- Contém: `tools/`, `config/`
- **NÃO** contém: `main.py`, `app/`, `prompts/` (aplicação principal)
- Distroless Python 3.13
- Non-root user (uid 65532)
- **Mais enxuta**: apenas código do MCP server

### Por que 2 imagens especializadas?

✅ **Vantagens:**
- **Menor tamanho**: Cada imagem contém apenas o código necessário
- **Segurança**: Reduz superfície de ataque (menos código = menos vulnerabilidades)
- **Performance**: Builds mais rápidos (menos arquivos para copiar)
- **Manutenção**: Mais fácil entender o que cada imagem contém
- **Deploy**: Pull mais rápido em produção

## Estrutura dos Dockerfiles

Temos **2 Dockerfiles especializados**, cada um otimizado para seu serviço:

### Dockerfile.app (Aplicação Principal)

```dockerfile
# Stage 1: builder - Instala dependências
FROM python:3.13-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ curl
RUN pip install --no-cache-dir uv
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy APENAS código da app (exclude tools/)
COPY main.py .
COPY app/ ./app/
COPY prompts/ ./prompts/
COPY config/ ./config/

# Stage 2: production - Distroless
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
WORKDIR /app
COPY --from=builder /app/main.py ./main.py
COPY --from=builder /app/app ./app
COPY --from=builder /app/prompts ./prompts
COPY --from=builder /app/config ./config
USER nonroot:nonroot
EXPOSE 8000
CMD ["/usr/local/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile.mcp (MCP Server)

```dockerfile
# Stage 1: builder - Instala dependências
FROM python:3.13-slim as builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ curl
RUN pip install --no-cache-dir uv
COPY requirements.txt .
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy APENAS código do MCP server (exclude app/, prompts/)
COPY tools/ ./tools/
COPY config/ ./config/

# Stage 2: production - Distroless
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
WORKDIR /app
COPY --from=builder /app/tools ./tools
COPY --from=builder /app/config ./config
USER nonroot:nonroot
EXPOSE 8002
CMD ["/usr/local/bin/uvicorn", "tools.server:app", "--host", "0.0.0.0", "--port", "8002"]
```

**Principais diferenças:**
- `Dockerfile.app`: Copia `main.py`, `app/`, `prompts/` (exclui `tools/`)
- `Dockerfile.mcp`: Copia `tools/` (exclui `main.py`, `app/`, `prompts/`)
- Ambos compartilham: `config/`, `requirements.txt`, mesma base distroless

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

Recomendações para diferentes ambientes:

### Development
```bash
# Usar timestamp para desenvolvimento
make docker-build-push-timestamp

# Resultado: argus-app:20250921-201146
```

### Staging
```bash
# Usar timestamp ou tag específica
make docker-build-push-timestamp

# Ou com tag manual:
make docker-build-push VERSION=staging-$(date +%Y%m%d)
```

### Production
```bash
# Usar semantic versioning (vX.Y.Z)
git tag v1.2.3
make docker-build-push VERSION=v1.2.3

# Também criar tag latest para produção
make docker-tag VERSION=v1.2.3
docker tag $(DOCKER_REGISTRY)/argus-app:v1.2.3 $(DOCKER_REGISTRY)/argus-app:latest
docker tag $(DOCKER_REGISTRY)/argus-mcp-server:v1.2.3 $(DOCKER_REGISTRY)/argus-mcp-server:latest
make docker-push VERSION=latest
```

### Resumo de Tags Recomendadas

| Ambiente | Formato Tag | Exemplo | Comando |
|----------|-------------|---------|---------|
| Dev | `YYYYMMDD-HHMMSS` | `20250921-201146` | `make docker-build-push-timestamp` |
| Staging | `YYYYMMDD-HHMMSS` | `20250921-201146` | `make docker-build-push-timestamp` |
| Prod | `vX.Y.Z` | `v1.2.3` | `make docker-build-push VERSION=v1.2.3` |
| Prod Latest | `latest` | `latest` | Manual (após validação) |

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
