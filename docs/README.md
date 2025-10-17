# 📖 Documentação do Argus Agent

Documentação completa do projeto Argus Agent - um assistente SRE com IA para análise de logs TOTVS Protheus.

## 🎯 Visão Geral

O Argus Agent é uma plataforma completa de análise de logs composta por:
- **API FastAPI** com orquestração LangGraph
- **MCP Server** para ferramentas e RAG
- **UI Angular 18** com design system TOTVS
- **Infraestrutura** com PostgreSQL, ChromaDB e Elasticsearch

## 📑 Índice da Documentação

### 🚀 Começando
- [README Principal](../README.md) - Visão geral do projeto e setup rápido
- [Guia de Início Rápido](INICIO-RAPIDO.md) - Como começar em minutos
- **[Variáveis de Ambiente](ENV-VARIABLES.md)** - Guia completo de configuração do .env

### 🎯 Planejamento & Evolução
- **[Melhorias Sugeridas](MELHORIAS-SUGERIDAS.md)** - Roadmap de evolução e próximos passos
- **[Arquitetura Futura](ARQUITETURA-FUTURA.md)** - Diagramas e visão de arquitetura proposta

### 🏗️ Componentes
- [API Documentation](../api/README.md) - FastAPI + LangGraph (porta 8000)
- [MCP Server Documentation](../mcp-server/README.md) - FastMCP Server (porta 8002)
- [UI Documentation](../ui/README.md) - Angular 18 + NGINX (porta 8080)

### 🐳 Deploy & Infraestrutura
- [Guia de Deploy](DEPLOYMENT.md) - Instruções completas para todos os ambientes
- [Guia de Containerização](README-CONTAINERIZATION.md) - Detalhes de Docker e Kubernetes
- [Resumo de Containerização](CONTAINERIZATION-SUMMARY.md) - Referência rápida
- **[Build Local (GCP)](BUILD-LOCAL.md)** - Como construir e publicar imagens localmente
- [Kubernetes README](../k8s/README.md) - Documentação específica de Kubernetes
- [Deploy Sandbox](DEPLOY-SANDBOX.md) - Ambiente de sandbox/desenvolvimento

### 🌐 Integração & API
- **[Acesso Externo ao MCP](MCP-EXTERNAL-ACCESS.md)** - Expor MCP Server via Ingress
- [Sandbox README](README-SANDBOX.md) - Uso do ambiente sandbox

### ✅ Testes & Validação
- [Resultados de Testes](TESTING-RESULTS.md) - Resultados de testes de integração
- [Testes de Autenticação](AUTH_TESTING.md) - Validação do sistema de autenticação

### 📋 Referências & Resumos
- [Resumo Final](FINAL-SUMMARY.md) - Resumo do projeto
- [Guia de Deploy Completo](DEPLOY_GUIDE.md) - Guia detalhado de deploy
- [Correções de Probes](PROBES-CORRECTIONS.md) - Ajustes em health checks
- [Kubernetes Best Practices](KUBERNETES-BEST-PRACTICES.md) - Boas práticas K8s

## 🎮 Atalhos Rápidos

### Desenvolvimento Local

```bash
# Setup inicial
make setup
cp .env.example .env
# Editar .env com suas credenciais

# Docker Compose (recomendado)
make dev                    # ou: docker-compose up

# Desenvolvimento sem containers
# Terminal 1 - API
cd api && uvicorn main:app --port 8000 --reload

# Terminal 2 - MCP Server
cd mcp-server && uvicorn tools.server:app --port 8002 --reload

# Terminal 3 - UI
cd ui && npm start

# Kubernetes local com Tilt
make tilt-up               # ou: tilt up
```

### Deploy em Ambientes

```bash
# Development (K8s)
make helm-install-dev

# Ou manualmente:
helm install argus-dev ./helm/argus-agent \
  --namespace argus-dev \
  --create-namespace \
  --values k8s/dev/values.yaml

# Production
helm install argus-prod ./helm/argus-agent \
  --namespace argus-production \
  --create-namespace \
  --values k8s/prod/values.yaml
```

### Build & Push

```bash
# Build local e push para GCP
make docker-login
make docker-release        # Build + push (latest + timestamp)

# Ou por componente
make docker-build          # Build api, mcp-server, ui
make docker-push           # Push para registry
```

## 📂 Estrutura de Documentação

```
argus-mcp-agent/
├── README.md                          # README principal do projeto
├── docs/                              # 📚 Documentação completa
│   ├── README.md                      # Este arquivo (índice)
│   ├── INICIO-RAPIDO.md              # Guia de início rápido
│   ├── ENV-VARIABLES.md              # Variáveis de ambiente
│   ├── MELHORIAS-SUGERIDAS.md        # Roadmap de evolução e melhorias
│   ├── ARQUITETURA-FUTURA.md         # Diagramas Mermaid da arquitetura
│   ├── DEPLOYMENT.md                  # Guia de deploy
│   ├── DEPLOY-SANDBOX.md             # Deploy sandbox
│   ├── BUILD-LOCAL.md                # Build local (GCP)
│   ├── README-CONTAINERIZATION.md    # Containerização
│   ├── CONTAINERIZATION-SUMMARY.md   # Resumo containerização
│   ├── MCP-EXTERNAL-ACCESS.md        # Acesso externo MCP
│   ├── README-SANDBOX.md             # Sandbox
│   ├── TESTING-RESULTS.md            # Resultados de testes
│   ├── AUTH_TESTING.md               # Testes de autenticação
│   ├── FINAL-SUMMARY.md              # Resumo final
│   ├── DEPLOY_GUIDE.md               # Guia de deploy detalhado
│   ├── PROBES-CORRECTIONS.md         # Correções de probes
│   └── KUBERNETES-BEST-PRACTICES.md  # Best practices K8s
│
├── api/
│   └── README.md                      # Documentação da API
├── mcp-server/
│   └── README.md                      # Documentação do MCP Server
├── ui/
│   └── README.md                      # Documentação da UI
└── k8s/
    └── README.md                      # Documentação Kubernetes
```

## 🤝 Contribuição

Ao adicionar ou atualizar documentação:

1. **Documentos gerais**: Coloque em `/docs`
2. **Documentos específicos**: Coloque próximo ao componente (ex: `api/README.md`)
3. **Atualize os índices**: Sempre atualize este README e o principal
4. **Sincronize com código**: Mantenha a documentação atualizada com mudanças
5. **Use markdown**: Siga o padrão de formatação existente
6. **Adicione emojis**: Para melhor navegação visual (opcional)

## 📞 Suporte

Para dúvidas ou problemas:

1. 📚 **Consulte a documentação**: Verifique os documentos relevantes acima
2. 🔍 **Troubleshooting**: Consulte [DEPLOYMENT.md](DEPLOYMENT.md) para soluções comuns
3. 💬 **Issues**: Abra um issue no repositório com detalhes
4. 🛠️ **Logs**: Use `make dev-logs` ou `kubectl logs` para diagnóstico

## 🔗 Links Úteis

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) - Protocolo usado pelo MCP Server
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Framework de orquestração
- [FastAPI](https://fastapi.tiangolo.com/) - Framework da API
- [Angular 18](https://angular.dev/) - Framework da UI
- [Helm](https://helm.sh/) - Gerenciamento de pacotes K8s
