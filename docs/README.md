# Documentação do Argus Agent

Documentação completa do projeto Argus Agent.

## Sumário

### Começando
- [README Principal](../README.md) - Visão geral do projeto e início rápido
- [Guia de Início Rápido](INICIO-RAPIDO.md) - Como começar em minutos
- [CLAUDE.md](../CLAUDE.md) - Guia para o assistente Claude Code
- **[Variáveis de Ambiente](ENV-VARIABLES.md)** - Guia completo de configuração do .env

### Deploy & Infraestrutura
- [Guia de Deploy](DEPLOYMENT.md) - Instruções completas para todos os ambientes
- [Guia de Containerização](README-CONTAINERIZATION.md) - Detalhes de Docker e Kubernetes
- [Resumo de Containerização](CONTAINERIZATION-SUMMARY.md) - Referência rápida
- **[Build Local](BUILD-LOCAL.md)** - Como construir e publicar imagens localmente (GCP Artifact Registry)
- [Kubernetes README](../k8s/README.md) - Documentação específica de Kubernetes
- **[Acesso Externo ao MCP](MCP-EXTERNAL-ACCESS.md)** - Expor MCP Server via Ingress

### Arquitetura & Design
- [Arquitetura](../app/docs/arquitetura.md) - Arquitetura do sistema e detalhes de implementação
- [Caso de Uso](../app/docs/caso-de-uso.md) - Caso de uso principal e fluxos

## Atalhos Rápidos

### Desenvolvimento
```bash
# Desenvolvimento local (sem containers)
source .venv/bin/activate
uvicorn main:app --reload  # Terminal 1
uvicorn tools.server:app --port 8002 --reload  # Terminal 2

# Docker Compose
docker-compose up

# Tilt (Kubernetes)
tilt up
```

### Deploy
```bash
# Development
helm install argus-dev ./helm/argus-agent \
  --namespace argus-dev \
  --values k8s/dev/values.yaml

# Production
helm install argus-prod ./helm/argus-agent \
  --namespace argus-production \
  --values k8s/prod/values.yaml
```

## Estrutura de Documentação

```
docs/
├── README.md                          # Este arquivo
├── DEPLOYMENT.md                      # Guia completo de deploy
├── README-CONTAINERIZATION.md         # Detalhes de containerização
└── CONTAINERIZATION-SUMMARY.md        # Referência rápida

../
├── README.md                          # README principal do projeto
├── CLAUDE.md                          # Guia do Claude Code
├── k8s/README.md                      # Guia de Kubernetes
└── app/docs/                          # Documentos de arquitetura
    ├── arquitetura.md
    └── caso-de-uso.md
```

## Contribuição

Ao adicionar novas documentações:
1. Coloque documentos gerais em `/docs`
2. Coloque docs específicas próximas ao componente
3. Atualize este README com os links
4. Mantenha os docs sincronizados com as mudanças no código

## Suporte

Para dúvidas ou problemas:
- Consulte a documentação existente
- Revise as [seções de troubleshooting](DEPLOYMENT.md#solução-de-problemas)
- Abra um issue no repositório
