# MCP Server - Uso Remoto

Este documento descreve como usar o MCP Server remotamente no ambiente sandbox.

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

## Boas práticas

- Prefira janelas menores (ex.: `15m`, `1h`) para reduzir latência/custo no Elasticsearch.
- Paralelize leituras quando necessário, respeitando limites do cluster.
- Trate erros: `401` (auth), `503` (dependências indisponíveis), `429` (limites, se configurado).

# Argus MCP Server

FastMCP server exposing tools for log analysis, RAG, and anomaly detection.

## Overview

The MCP (Model Context Protocol) server provides tools that the main API agent can invoke:

- **search_logs**: Query Elasticsearch for recent logs
- **retrieve_historical_context**: Query ChromaDB RAG for historical analysis summaries
- **save_analysis_summary**: Persist analysis summaries to RAG
- **detect_timeseries_anomalies**: ML-based anomaly detection using IsolationForest

## Architecture

- **Framework**: FastMCP (built on FastAPI)
- **Data Sources**:
  - Elasticsearch for logs
  - ChromaDB for RAG vector storage
  - InfluxDB for metrics (future)
- **ML**: scikit-learn for anomaly detection

## Directory Structure

```
mcp-server/
├── tools/              # MCP tool implementations
│   ├── server.py       # Main FastMCP server
│   ├── es_client.py    # Elasticsearch client
│   ├── rag.py          # ChromaDB RAG implementation
│   └── anomaly.py      # Anomaly detection
├── requirements.txt    # Python dependencies
├── Dockerfile          # Production image
└── Dockerfile.dev      # Development image
```

## Running Locally

### Development Mode

```bash
# Install dependencies
cd mcp-server
pip install -r requirements.txt

# Run server
uvicorn tools.server:app --host 0.0.0.0 --port 8002 --reload
```

### Docker Development

```bash
# Build development image
docker build -f mcp-server/Dockerfile.dev -t argus-mcp-server:dev ./mcp-server

# Run with docker-compose
docker-compose -f docker-compose.dev.yml up mcp-server
```

## Environment Variables

```bash
# Elasticsearch
ES_HOST=https://your-elastic-host.com
ES_USER=elastic
ES_PASSWORD=your-password
ES_TIMEOUT=30

# ChromaDB
CHROMA_MODE=embedded  # or standalone for containers
CHROMA_HOST=argus-chromadb
CHROMA_PORT=8000
```

## Available Tools

### search_logs

Fetches up to 200 recent logs from Elasticsearch within a time window.

**Parameters:**
- `index` (string): Elasticsearch index name
- `window` (integer): Time window in hours (default: 1)

**Returns:**
- List of log documents with timestamps, messages, severity, etc.

### retrieve_historical_context

Queries RAG for historical analysis summaries similar to the query.

**Parameters:**
- `index` (string): Elasticsearch index name (derives collection)
- `query` (string): Search query text

**Returns:**
- List of similar historical analyses with metadata

### save_analysis_summary

Persists an analysis summary to the RAG vector database.

**Parameters:**
- `index` (string): Elasticsearch index name
- `summary` (string): Analysis summary text to store

**Returns:**
- Success confirmation with document ID

### detect_timeseries_anomalies

ML-based anomaly detection using IsolationForest.

**Parameters:**
- `data` (array): Time series data points
- `contamination` (float): Expected proportion of anomalies (0-1)

**Returns:**
- Array of boolean flags (true = anomaly)

## Testing

```bash
# Test server health
curl http://localhost:8002/

# Test MCP endpoint
curl http://localhost:8002/mcp/
```

## Deployment

### Docker Production

```bash
# Build production image
docker build -f mcp-server/Dockerfile -t argus-mcp-server:latest ./mcp-server

# Push to registry
docker push southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:latest
```

### Kubernetes

See `/k8s/dev/mcp-server-deployment.yaml` for K8s deployment manifests.

## Health Checks

- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks ES, ChromaDB)
- `GET /health/startup` - Startup probe

## Protocol

This server implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/), allowing LLM agents to invoke tools via standardized interfaces.

The main API connects to this server using `langchain_mcp_adapters.client.MultiServerMCPClient`.
