# Argus API

FastAPI application providing the main SRE Agent API with LangGraph workflows.

## Overview

The API service handles:
- **Authentication**: JWT-based user authentication with PostgreSQL
- **Log Analysis**: Initial log search and deep dive analysis
- **Chat Interface**: Conversational AI interface with tool calling
- **Log Explanation**: Single log line explanations
- **MCP Integration**: Connects to MCP server for tool execution

## Architecture

- **Framework**: FastAPI
- **LLM Orchestration**: LangGraph for agent workflows
- **Authentication**: JWT tokens with refresh support
- **Database**: PostgreSQL for user management
- **LLM Providers**: OpenAI, Google, Anthropic

## Directory Structure

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

## Running Locally

### Development Mode

```bash
# Install dependencies
cd api
pip install -r requirements.txt

# Run with hot-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Development

```bash
# Build development image
docker build -f api/Dockerfile.dev -t argus-api:dev ./api

# Run with docker-compose
docker-compose -f docker-compose.dev.yml up api
```

## Environment Variables

Key environment variables (see `.env.example`):

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

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### Analysis
- `POST /initial-analysis` - Search logs via MCP
- `POST /deep-dive` - Deep analysis with LLM synthesis
- `POST /explain-log-line` - Explain single log line
- `POST /chat` - Conversational chat with context

### Health
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe (checks dependencies)
- `GET /health/startup` - Startup probe (initialization status)

## Workflows

### Initial Analysis
Searches logs via `search_logs` tool, returns raw data.

### Deep Dive
Performs LLM-powered analysis with entity extraction and relationship mapping.

### Chat
Conversational interface with tool-calling capabilities and context injection.

## Testing

```bash
# Run tests
pytest -v

# With coverage
pytest --cov=app --cov-report=html
```

## Deployment

### Docker Production

```bash
# Build production image
docker build -f api/Dockerfile -t argus-api:latest ./api

# Push to registry
docker push southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-api:latest
```

### Kubernetes

See `/k8s/dev/api-deployment.yaml` for K8s deployment manifests.

## Configuration Files

- `config/settings.json` - MCP server configuration
- `config/models.json` - LLM model definitions
- `prompts/*.md` - Prompt templates for each workflow
