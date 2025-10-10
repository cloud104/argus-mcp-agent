# 🏗️ Arquitetura Futura - Diagramas e Visão

**Documento Complementar**: [MELHORIAS-SUGERIDAS.md](./MELHORIAS-SUGERIDAS.md)

---

## 📊 Arquitetura Atual vs Proposta

### Arquitetura Atual (Simples)

```mermaid
graph TB
    subgraph "Frontend"
        UI[Angular UI<br/>Port 8080]
    end

    subgraph "Backend"
        API[FastAPI + LangGraph<br/>Port 8000]
    end

    subgraph "MCP Tools"
        MCP[MCP Server<br/>Port 8002<br/>4 tools]
    end

    subgraph "Data Layer"
        ES[(Elasticsearch<br/>Logs)]
        CHROMA[(ChromaDB<br/>RAG)]
        PG[(PostgreSQL<br/>Auth)]
    end

    UI -->|HTTP| API
    API -->|MCP Protocol| MCP
    MCP --> ES
    MCP --> CHROMA
    API --> PG

    style MCP fill:#bbf,stroke:#333,stroke-width:2px
```

### Arquitetura Proposta (Multi-MCP + ML + Automação)

```mermaid
graph TB
    subgraph "Presentation Layer"
        UI[Angular UI<br/>Dashboards + Chat]
    end

    subgraph "API Layer"
        API[FastAPI + LangGraph]
        INITIAL[Initial Analysis]
        DEEP[Deep Dive]
        CHAT[Chat]
        RCA[Root Cause Analysis<br/>NEW]
        PRED[Predictive Analysis<br/>NEW]
    end

    subgraph "MCP Ecosystem"
        MCP_LOGS[MCP Logs<br/>Elasticsearch + RAG]
        MCP_METRICS[MCP Prometheus<br/>Metrics + Alerts]
        MCP_COLLAB[MCP Slack<br/>Notifications]
        MCP_TICKET[MCP Jira<br/>Issue Tracking]
        MCP_KB[MCP Knowledge<br/>Confluence Docs]
        MCP_ML[MCP ML<br/>Anomaly Detection]
    end

    subgraph "Async Workers"
        CELERY[Celery Workers]
        SCHEDULED[Scheduled Tasks]
        WEBHOOKS[Webhook Handlers]
    end

    subgraph "Data & ML"
        ES[(Elasticsearch)]
        PROM[(Prometheus)]
        CHROMA[(ChromaDB)]
        PG[(PostgreSQL)]
        REDIS[(Redis Cache)]
        MINIO[(MinIO<br/>Data Lake)]
        ML[ML Models<br/>Severity<br/>Clustering]
    end

    subgraph "Observability"
        JAEGER[Jaeger<br/>Traces]
        GRAFANA[Grafana<br/>Metrics]
    end

    UI --> API

    API --> INITIAL
    API --> DEEP
    API --> CHAT
    API --> RCA
    API --> PRED

    RCA -->|correlates| MCP_LOGS
    RCA -->|correlates| MCP_METRICS
    RCA -->|searches| MCP_KB
    RCA -->|creates| MCP_TICKET

    PRED --> MCP_ML
    PRED --> MCP_METRICS

    DEEP -->|notifies| MCP_COLLAB

    MCP_LOGS --> ES
    MCP_LOGS --> CHROMA
    MCP_METRICS --> PROM
    MCP_ML --> ML

    API --> REDIS
    API --> PG

    CELERY --> SCHEDULED
    CELERY --> WEBHOOKS
    SCHEDULED --> MCP_LOGS

    ML --> MINIO
    CHROMA --> MINIO

    API -.->|traces| JAEGER
    API -.->|metrics| GRAFANA

    style RCA fill:#f9f,stroke:#333,stroke-width:3px
    style PRED fill:#f9f,stroke:#333,stroke-width:3px
    style MCP_ML fill:#bfb,stroke:#333,stroke-width:2px
    style CELERY fill:#fbb,stroke:#333,stroke-width:2px
```

---

## 🔄 Workflows Propostos

### 1. Root Cause Analysis Workflow

```mermaid
sequenceDiagram
    participant User
    participant API
    participant MCP_Logs
    participant MCP_Metrics
    participant MCP_KB
    participant MCP_Jira
    participant LLM

    User->>API: Incident Report<br/>"500 errors in /api/users"

    Note over API: RCA Workflow Start

    API->>MCP_Logs: search_logs(index, window)
    MCP_Logs-->>API: 150 error logs

    API->>MCP_Metrics: query_metrics(service, window)
    MCP_Metrics-->>API: CPU 95%, Latency +200%

    API->>MCP_KB: search_runbooks("500 errors")
    MCP_KB-->>API: Related incidents + Solutions

    API->>LLM: Synthesize RCA<br/>(logs + metrics + history)
    LLM-->>API: Root Cause Hypothesis

    alt Critical Severity
        API->>MCP_Jira: create_issue(summary, priority)
        MCP_Jira-->>API: JIRA-1234

        API->>MCP_Slack: send_alert(channel, message)
        MCP_Slack-->>API: Message sent
    end

    API-->>User: RCA Report + Ticket ID
```

### 2. Scheduled Health Check Workflow

```mermaid
graph LR
    CRON[Cron: Daily 9AM]
    CELERY[Celery Worker]
    ANALYZE[Run Analysis]
    CHECK{Issues<br/>Found?}
    ALERT[Send Alert]
    REPORT[Generate Report]
    SAVE[Save to DB]

    CRON -->|trigger| CELERY
    CELERY --> ANALYZE
    ANALYZE --> CHECK

    CHECK -->|Yes| ALERT
    CHECK -->|No| REPORT

    ALERT --> REPORT
    REPORT --> SAVE

    style CHECK fill:#ff9,stroke:#333,stroke-width:2px
    style ALERT fill:#f99,stroke:#333,stroke-width:2px
```

### 3. Multi-Agent Collaboration Pattern

```mermaid
graph TB
    USER[User Query]
    SUPERVISOR[Supervisor Agent<br/>Router + Orchestrator]

    LOG_AGENT[Log Analyzer Agent<br/>LLM: GPT-4]
    METRIC_AGENT[Metrics Analyzer<br/>LLM: Claude]
    INC_AGENT[Incident Manager<br/>LLM: GPT-3.5]
    KB_AGENT[Knowledge Curator<br/>LLM: Claude]

    LOG_TOOLS[MCP Logs Tools]
    METRIC_TOOLS[MCP Metrics Tools]
    COLLAB_TOOLS[MCP Collab Tools]
    KB_TOOLS[MCP KB Tools]

    SYNTHESIS[Final Synthesis<br/>LLM: GPT-4]
    RESPONSE[Response to User]

    USER --> SUPERVISOR

    SUPERVISOR -->|"analyze logs"| LOG_AGENT
    SUPERVISOR -->|"check metrics"| METRIC_AGENT
    SUPERVISOR -->|"search history"| KB_AGENT

    LOG_AGENT --> LOG_TOOLS
    METRIC_AGENT --> METRIC_TOOLS
    KB_AGENT --> KB_TOOLS

    LOG_TOOLS -.->|results| LOG_AGENT
    METRIC_TOOLS -.->|results| METRIC_AGENT
    KB_TOOLS -.->|results| KB_AGENT

    LOG_AGENT --> SYNTHESIS
    METRIC_AGENT --> SYNTHESIS
    KB_AGENT --> SYNTHESIS

    SYNTHESIS --> INC_AGENT
    INC_AGENT --> COLLAB_TOOLS

    INC_AGENT --> RESPONSE
    RESPONSE --> USER

    style SUPERVISOR fill:#f9f,stroke:#333,stroke-width:3px
    style SYNTHESIS fill:#9ff,stroke:#333,stroke-width:2px
```

---

## 🧠 Machine Learning Pipeline

```mermaid
graph LR
    subgraph "Data Collection"
        ES[Elasticsearch<br/>Historical Logs]
        PROM[Prometheus<br/>Metrics]
    end

    subgraph "Feature Engineering"
        EXTRACT[Extract Features<br/>- Log patterns<br/>- Error rates<br/>- Metrics trends]
        EMBED[Generate Embeddings<br/>SentenceTransformers]
    end

    subgraph "ML Models"
        SEV[Severity Classifier<br/>RandomForest]
        CLUSTER[Log Clustering<br/>DBSCAN]
        ANOMALY[Anomaly Detector<br/>IsolationForest]
        PREDICT[Incident Predictor<br/>GradientBoosting]
    end

    subgraph "Model Serving"
        MCP_ML[MCP ML Server<br/>Inference API]
    end

    subgraph "Applications"
        RCA[Root Cause<br/>Analysis]
        AUTO[Auto-Tagging<br/>Logs]
        ALERT[Predictive<br/>Alerts]
    end

    ES --> EXTRACT
    PROM --> EXTRACT

    EXTRACT --> EMBED
    EXTRACT --> SEV
    EXTRACT --> ANOMALY
    EXTRACT --> PREDICT

    EMBED --> CLUSTER

    SEV --> MCP_ML
    CLUSTER --> MCP_ML
    ANOMALY --> MCP_ML
    PREDICT --> MCP_ML

    MCP_ML --> RCA
    MCP_ML --> AUTO
    MCP_ML --> ALERT

    style MCP_ML fill:#bfb,stroke:#333,stroke-width:2px
```

---

## 🔐 Security Architecture

```mermaid
graph TB
    subgraph "External"
        USER[User Browser]
        CICD[CI/CD Pipeline]
    end

    subgraph "Edge Layer"
        INGRESS[Nginx Ingress<br/>TLS Termination]
        WAF[Web Application Firewall]
    end

    subgraph "Auth Layer"
        JWT[JWT Validation]
        RBAC[RBAC Engine<br/>Granular Permissions]
        AUDIT[Audit Logger]
    end

    subgraph "API Layer"
        API[FastAPI]
        RATE[Rate Limiter<br/>Redis-based]
    end

    subgraph "Secrets Management"
        VAULT[HashiCorp Vault]
        SECRETS[Encrypted Secrets<br/>- DB passwords<br/>- API keys<br/>- Tokens]
    end

    subgraph "Data Layer"
        PG_ENC[(PostgreSQL<br/>Encrypted at Rest)]
        ES_AUTH[(Elasticsearch<br/>TLS + Auth)]
    end

    USER --> INGRESS
    CICD --> INGRESS

    INGRESS --> WAF
    WAF --> JWT

    JWT --> RBAC
    RBAC --> AUDIT

    AUDIT --> API
    API --> RATE

    API --> VAULT
    VAULT --> SECRETS

    API --> PG_ENC
    API --> ES_AUTH

    style JWT fill:#f99,stroke:#333,stroke-width:2px
    style RBAC fill:#f99,stroke:#333,stroke-width:2px
    style VAULT fill:#9f9,stroke:#333,stroke-width:2px
```

---

## 📊 Data Flow - Analysis Request

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Angular UI
    participant API as FastAPI
    participant C as Redis Cache
    participant MCP as MCP Servers
    participant ES as Elasticsearch
    participant LLM as LLM Provider
    participant DB as PostgreSQL

    U->>UI: Request Analysis
    UI->>API: POST /analyze/initial

    API->>C: Check cache

    alt Cache Hit
        C-->>API: Cached results
        API-->>UI: Return cached response
    else Cache Miss
        API->>MCP: search_logs(index, window)
        MCP->>ES: Query logs
        ES-->>MCP: Log results
        MCP-->>API: Formatted logs

        API->>LLM: Generate analysis
        LLM-->>API: AI response

        API->>C: Cache results
        API->>DB: Save analysis

        API-->>UI: Return response
    end

    UI-->>U: Display results

    Note over C: Cache TTL: 5 minutes
    Note over DB: Audit log created
```

---

## 🎯 Deployment Architecture

### Development Environment

```mermaid
graph TB
    subgraph "Docker Compose"
        UI[UI Container]
        API[API Container]
        MCP[MCP Container]
        PG[PostgreSQL]
        REDIS[Redis]
        CHROMA[ChromaDB]
        JAEGER[Jaeger]
    end

    DEV[Developer]

    DEV -->|http://localhost:8080| UI
    DEV -->|http://localhost:8000| API
    DEV -->|http://localhost:8002| MCP
    DEV -->|http://localhost:16686| JAEGER

    UI --> API
    API --> MCP
    API --> REDIS
    API --> PG
    MCP --> CHROMA
```

### Production Environment (Kubernetes)

```mermaid
graph TB
    subgraph "Ingress"
        NGINX[Nginx Ingress<br/>TLS + Load Balancer]
    end

    subgraph "Namespace: argus-production"
        subgraph "Deployments"
            UI[UI Pods x2<br/>HPA enabled]
            API[API Pods x3<br/>HPA enabled]
            MCP[MCP Pods x2<br/>HPA enabled]
            WORKER[Celery Workers x3]
        end

        subgraph "StatefulSets"
            PG[PostgreSQL<br/>Primary + Replica]
            REDIS[Redis Sentinel<br/>HA Setup]
        end

        subgraph "Services"
            SVC_UI[ui-service]
            SVC_API[api-service]
            SVC_MCP[mcp-service]
        end
    end

    subgraph "External Services"
        ES_EXT[(Elasticsearch<br/>Managed Service)]
        PROM_EXT[(Prometheus<br/>Managed Service)]
    end

    subgraph "Storage"
        PVC_PG[PVC: PostgreSQL]
        PVC_REDIS[PVC: Redis]
        S3[S3: MinIO/Cloud Storage<br/>Analyses + ML Models]
    end

    INTERNET[Internet]

    INTERNET --> NGINX
    NGINX --> SVC_UI
    NGINX --> SVC_API

    SVC_UI --> UI
    SVC_API --> API

    API --> SVC_MCP
    SVC_MCP --> MCP

    API --> REDIS
    API --> PG
    MCP --> ES_EXT
    MCP --> PROM_EXT

    WORKER --> REDIS

    PG --> PVC_PG
    REDIS --> PVC_REDIS

    API -.->|backup| S3
    MCP -.->|ml models| S3

    style NGINX fill:#9f9,stroke:#333,stroke-width:2px
    style API fill:#bbf,stroke:#333,stroke-width:2px
    style WORKER fill:#fbb,stroke:#333,stroke-width:2px
```

---

## 📈 Scaling Strategy

```mermaid
graph LR
    subgraph "Load Profile"
        LOW[Low Load<br/>< 100 req/min]
        MED[Medium Load<br/>100-500 req/min]
        HIGH[High Load<br/>> 500 req/min]
    end

    subgraph "Auto-Scaling"
        HPA[Horizontal Pod<br/>Autoscaler]
        METRICS[Metrics Server<br/>CPU + Memory]
    end

    subgraph "Scaling Actions"
        API_SCALE[API Pods<br/>Min: 2<br/>Max: 10]
        MCP_SCALE[MCP Pods<br/>Min: 1<br/>Max: 5]
        WORKER_SCALE[Workers<br/>Min: 2<br/>Max: 20]
    end

    subgraph "Resources"
        REDIS_SCALE[Redis Replica<br/>Read-only]
        CACHE[Cache Hit Rate<br/>Target: > 80%]
    end

    LOW --> METRICS
    MED --> METRICS
    HIGH --> METRICS

    METRICS --> HPA

    HPA --> API_SCALE
    HPA --> MCP_SCALE
    HPA --> WORKER_SCALE

    HIGH --> REDIS_SCALE
    HIGH --> CACHE

    style HIGH fill:#f99,stroke:#333,stroke-width:2px
    style HPA fill:#9f9,stroke:#333,stroke-width:2px
```

---

## 🔄 CI/CD Pipeline

```mermaid
graph LR
    subgraph "Development"
        DEV[Developer]
        GIT[Git Push]
    end

    subgraph "CI Pipeline"
        LINT[Lint<br/>flake8 + eslint]
        TEST[Unit Tests<br/>pytest + jest]
        BUILD[Build Images<br/>Docker]
        SCAN[Security Scan<br/>Trivy]
    end

    subgraph "CD Pipeline"
        PUSH[Push to Registry<br/>GCR/ACR]
        DEPLOY_DEV[Deploy to Dev<br/>Helm]
        E2E[E2E Tests<br/>Playwright]
        DEPLOY_PROD[Deploy to Prod<br/>Helm]
    end

    subgraph "Post-Deploy"
        ANALYZE[Analyze Logs<br/>via Argus!]
        MONITOR[Monitor Metrics]
        ALERT{Issues?}
        ROLLBACK[Auto Rollback]
    end

    DEV --> GIT
    GIT --> LINT
    LINT --> TEST
    TEST --> BUILD
    BUILD --> SCAN

    SCAN --> PUSH
    PUSH --> DEPLOY_DEV
    DEPLOY_DEV --> E2E

    E2E -->|pass| DEPLOY_PROD
    E2E -->|fail| ROLLBACK

    DEPLOY_PROD --> ANALYZE
    ANALYZE --> MONITOR
    MONITOR --> ALERT

    ALERT -->|Yes| ROLLBACK
    ALERT -->|No| SUCCESS[Success]

    style ANALYZE fill:#9ff,stroke:#333,stroke-width:3px
    style ROLLBACK fill:#f99,stroke:#333,stroke-width:2px
```

---

## 🎓 Referências

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LangGraph Multi-Agent Systems](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/)
- [OpenTelemetry Best Practices](https://opentelemetry.io/docs/best-practices/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [RBAC in FastAPI](https://fastapi.tiangolo.com/advanced/security/)

---

**Última atualização**: 2025-10-10
