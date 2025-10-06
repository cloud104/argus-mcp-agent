# Argus API

Aplicação FastAPI que expõe a API principal do Agente SRE com fluxos orquestrados em LangGraph.

## Visão Geral

A API é responsável por:
- **Autenticação**: JWT com PostgreSQL para gestão de usuários
- **Análise de Logs**: busca inicial e análise aprofundada
- **Chat**: interface conversacional com chamadas de ferramentas
- **Explicação de Log**: explicação de uma linha específica
- **Integração MCP**: comunicação com o MCP Server para executar ferramentas

## Arquitetura

- **Framework**: FastAPI
- **Orquestração LLM**: LangGraph para os fluxos do agente
- **Autenticação**: tokens JWT com refresh
- **Banco de Dados**: PostgreSQL para usuários/roles
- **Provedores LLM**: OpenAI, Google, Anthropic

## Estrutura de Diretórios

```
api/
├── app/
│   ├── agent/          # LangGraph workflows
│   ├── api/            # API route handlers
│   ├── auth/           # Authentication logic
│   └── utils/          # Utilities and resilience
├── config/             # Settings and models
├── prompts/            # LLM prompt templates
├── main.py             # FastAPI application
├── requirements.txt    # Python dependencies
├── Dockerfile          # Production image
└── Dockerfile.dev      # Development image with debugging
```

## Executando Localmente

### Modo de Desenvolvimento

```bash
# Instalar dependências
cd api
pip install -r requirements.txt

# Executar com hot-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Desenvolvimento com Docker

```bash
# Build da imagem de desenvolvimento
docker build -f api/Dockerfile.dev -t argus-api:dev ./api

# Subir com docker-compose
docker-compose -f docker-compose.dev.yml up api
```

## Variáveis de Ambiente

Principais variáveis (ver `.env.example`):

```bash
# API Keys
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...

# Database
POSTGRES_HOST=argus-postgres
POSTGRES_PORT=5432
POSTGRES_USER=argus
POSTGRES_PASSWORD=argus123
POSTGRES_DB=argus_auth

# MCP Server
MCP_SERVER_URL=http://argus-mcp-server:8002/mcp/

# Timeouts
API_TIMEOUT_INITIAL=120
API_TIMEOUT_DEEP_DIVE=120
API_TIMEOUT_CHAT=120
```

## Endpoints da API

### Autenticação
- `POST /auth/login` - Login e obtenção de tokens JWT
- `POST /auth/refresh` - Renovar token de acesso
- `GET /auth/me` - Dados do usuário atual
- `POST /auth/change-password` - Trocar a própria senha
- `POST /auth/change-email` - Trocar o próprio e-mail
- `POST /auth/users` - Criar usuário (admin)
- `PUT /auth/users/{username}/password` - Redefinir senha (admin)
- `PUT /auth/users/{username}/email` - Alterar e-mail (admin)
- `PUT /auth/users/{username}/role` - Alterar role (admin)
- `PUT /auth/users/{username}/disable|enable` - Desativar/ativar usuário (admin)

### Análises
- `POST /initial-analysis` - Busca de logs via MCP
- `POST /deep-dive` - Análise aprofundada com síntese do LLM
- `POST /explain-log-line` - Explica uma linha de log
- `POST /chat` - Chat com contexto e ferramentas

### Saúde
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness (verifica dependências)
- `GET /health/startup` - Startup (estado de inicialização)

## Workflows

### Initial Analysis
Busca logs via ferramenta `search_logs`, retorna dados brutos.

### Deep Dive
Análise com LLM, extração de entidades e relações.

### Chat
Interface conversacional com chamadas de ferramentas e injeção de contexto.

## Testes

```bash
# Executar testes
pytest -v

# Com cobertura
pytest --cov=app --cov-report=html
```

## Deploy

### Docker (produção)

```bash
# Build da imagem de produção
docker build -f api/Dockerfile -t argus-api:latest ./api

# Push para o registry
docker push southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-api:latest
```

### Kubernetes

Consulte `/k8s/dev/api-deployment.yaml` para os manifests de K8s.

## Arquivos de Configuração

- `config/settings.json` - Configurações do MCP
- `config/models.json` - Definições de modelos LLM
- `prompts/*.md` - Templates de prompts por workflow
