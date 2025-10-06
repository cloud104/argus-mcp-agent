# MCP Server - Uso Remoto

Este documento descreve como usar o MCP Server remotamente no ambiente sandbox e a visão completa do serviço.

## Endpoint

- Base: `https://argus.sandbox.tcloud-devops.cloudtotvs.com.br/mcp/`
- Health (sem autenticação): `GET /mcp/`

## Autenticação

O MCP exige `Authorization: Bearer <token>`:

1. Obtenha um `access_token` na API:

```bash
curl -s -X POST https://argus.sandbox.tcloud-devops.cloudtotvs.com.br/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"<user>","password":"<pass>"}'
```

2. Alternativamente, quando provisionado, use `MCP_SERVICE_TOKEN` como Bearer.

## Ferramentas (HTTP)

Envie `POST` para os endpoints abaixo com JSON e Bearer token.

- Buscar logs recentes

```
POST /mcp/tools/search_logs
{
  "index": "meu_indice",
  "window": "2h"
}
```

- Contexto histórico (RAG)

```
POST /mcp/tools/retrieve_historical_context
{
  "index": "meu_indice",
  "query": "erros 500 ontem"
}
```

- Salvar resumo no RAG

```
POST /mcp/tools/save_analysis_summary
{
  "index": "meu_indice",
  "summary": "Resumo da investigação..."
}
```

- Anomalias em série temporal

```
POST /mcp/tools/detect_timeseries_anomalies
{
  "data": [ { "timestamp": "2025-10-06T10:00:00Z", "value": 1.23 } ],
  "contamination": 0.1
}
```

## Exemplo completo (curl)

```bash
TOKEN=$(curl -s -X POST https://argus.sandbox.tcloud-devops.cloudtotvs.com.br/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"<senha>"}' | jq -r .access_token)

curl -s https://argus.sandbox.tcloud-devops.cloudtotvs.com.br/mcp/

curl -s -X POST https://argus.sandbox.tcloud-devops.cloudtotvs.com.br/mcp/tools/search_logs \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"index":"logs_prod_app","window":"1h"}'
```

## Visão Geral do Servidor MCP

Servidor FastMCP que expõe ferramentas para análise de logs, RAG e detecção de anomalias.

### Arquitetura

- **Framework**: FastMCP (sobre FastAPI)
- **Fontes de Dados**:
  - Elasticsearch para logs
  - ChromaDB para armazenamento vetorial (RAG)
- **ML**: scikit-learn para detecção de anomalias

### Estrutura de Diretórios

```
mcp-server/
├── tools/              # Implementações das tools MCP
│   ├── server.py       # Servidor FastMCP principal
│   ├── auth.py         # Autenticação e validação de token
│   ├── rag_manager.py  # Integração com ChromaDB
│   └── resilience.py   # Requisições resilientes/retentativas
├── requirements.txt    # Dependências Python
├── Dockerfile          # Imagem de produção
└── Dockerfile.dev      # Imagem de desenvolvimento
```

## Executando Localmente

### Modo de Desenvolvimento

```bash
# Instalar dependências
cd mcp-server
pip install -r requirements.txt

# Executar servidor
uvicorn tools.server:app --host 0.0.0.0 --port 8002 --reload
```

### Desenvolvimento com Docker

```bash
# Build imagem de desenvolvimento
docker build -f mcp-server/Dockerfile.dev -t argus-mcp-server:dev ./mcp-server

# Subir com docker-compose
docker-compose -f docker-compose.dev.yml up mcp-server
```

## Variáveis de Ambiente

```bash
# Elasticsearch
ES_HOST=https://your-elastic-host.com
ES_USER=elastic
ES_PASSWORD=your-password
ES_TIMEOUT=30

# ChromaDB
CHROMA_MODE=embedded  # ou standalone para containers
CHROMA_HOST=argus-chromadb
CHROMA_PORT=8000
```

## Tools Disponíveis

### search_logs
Busca até 200 logs recentes no Elasticsearch dentro de uma janela de tempo.

Parâmetros:
- `index` (string): nome do índice no ES
- `window` (string): janela de tempo (ex.: "1h", "30m")

Retorno: lista de documentos com timestamp, mensagem, severidade etc.

### retrieve_historical_context
Consulta o RAG por resumos históricos semelhantes à consulta.

Parâmetros:
- `index` (string): índice ES (deriva o nome da coleção)
- `query` (string): texto de pesquisa

Retorno: lista de análises históricas com metadados

### save_analysis_summary
Persiste um resumo de análise no banco vetorial (RAG).

Parâmetros:
- `index` (string)
- `summary` (string)

Retorno: confirmação de sucesso

### detect_timeseries_anomalies
Detecção de anomalias (IsolationForest) em série temporal.

Parâmetros:
- `data` (array): pontos de série temporal
- `contamination` (float): proporção esperada de anomalias (0–1)

Retorno: registros marcados como anomalia

## Testes Rápidos

```bash
# Health do servidor
curl http://localhost:8002/

# Endpoint MCP
curl http://localhost:8002/mcp/
```

## Deploy

### Docker (produção)

```bash
# Build da imagem de produção
docker build -f mcp-server/Dockerfile -t argus-mcp-server:latest ./mcp-server

# Push para o registry
docker push southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest
```

### Kubernetes

Consulte `/k8s/dev/mcp-server-deployment.yaml` para os manifests de K8s.

## Health Checks

- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness (verifica ES, ChromaDB)
- `GET /health/startup` - Startup

## Protocolo

Este servidor implementa o [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), permitindo que agentes LLM invoquem ferramentas por interfaces padronizadas.

A API principal conecta-se a este servidor usando `langchain_mcp_adapters.client.MultiServerMCPClient`.
