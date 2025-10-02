# Argus Agent Documentation

Complete documentation for the Argus Agent project.

## Table of Contents

### Começando
- [README Principal](../README.md) - Visão geral do projeto e início rápido
- [Guia de Início Rápido](INICIO-RAPIDO.md) - Como começar em minutos
- [CLAUDE.md](../CLAUDE.md) - Guia para o assistente Claude Code
- **[Variáveis de Ambiente](ENV-VARIABLES.md)** - Guia completo de configuração do .env

### Deployment & Infrastructure
- [Deployment Guide](DEPLOYMENT.md) - Complete deployment instructions for all environments
- [Containerization Guide](README-CONTAINERIZATION.md) - Docker and Kubernetes implementation details
- [Containerization Summary](CONTAINERIZATION-SUMMARY.md) - Quick reference for containerization setup
- **[Build Local](BUILD-LOCAL.md)** - Como construir e publicar imagens localmente no GCP Artifact Registry
- [Kubernetes README](../k8s/README.md) - Kubernetes-specific documentation
- **[MCP External Access](MCP-EXTERNAL-ACCESS.md)** - Expor MCP Server externamente via Ingress

### Architecture & Design
- [Architecture](../app/docs/arquitetura.md) - System architecture and implementation details (Portuguese)
- [Use Case](../app/docs/caso-de-uso.md) - Main use case and workflows (Portuguese)

## Quick Links

### Development
```bash
# Local development (without containers)
source .venv/bin/activate
uvicorn main:app --reload  # Terminal 1
uvicorn tools.server:app --port 8002 --reload  # Terminal 2

# Docker Compose
docker-compose up

# Tilt (Kubernetes)
tilt up
```

### Deployment
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

## Documentation Structure

```
docs/
├── README.md                          # This file
├── DEPLOYMENT.md                      # Complete deployment guide
├── README-CONTAINERIZATION.md         # Containerization details
└── CONTAINERIZATION-SUMMARY.md        # Quick reference

../
├── README.md                          # Main project README
├── CLAUDE.md                          # Claude Code guide
├── k8s/README.md                      # Kubernetes guide
└── app/docs/                          # Architecture docs (Portuguese)
    ├── arquitetura.md
    └── caso-de-uso.md
```

## Contributing

When adding new documentation:
1. Place general docs in `/docs`
2. Place component-specific docs near the component
3. Update this README with links
4. Keep docs in sync with code changes

## Support

For issues or questions:
- Check existing documentation
- Review [troubleshooting sections](DEPLOYMENT.md#troubleshooting)
- Create an issue in the repository
