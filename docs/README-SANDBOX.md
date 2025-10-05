# Argus Agent - Deploy no Cluster Sandbox

Este documento descreve como fazer o deploy do Argus Agent no cluster Kubernetes sandbox da TOTVS.

## 🚀 Deploy Rápido

### Opção 1: Script Automatizado (Recomendado)

```bash
# Executar script de deploy
./scripts/deploy-sandbox.sh
```

### Opção 2: Deploy Manual

```bash
# 1. Aplicar secrets
kubectl apply -f k8s/dev/secret.yaml

# 2. Deploy via Helm
cd helm/argus-agent
helm upgrade --install argus-agent . \
  --namespace argus \
  --create-namespace \
  --values values-sandbox.yaml \
  --wait \
  --timeout=10m
```

## 🧹 Limpeza

### Opção 1: Script Automatizado

```bash
# Executar script de limpeza
./scripts/cleanup-sandbox.sh
```

### Opção 2: Limpeza Manual

```bash
# 1. Remover release do Helm
helm uninstall argus-agent -n argus

# 2. Remover namespace (remove todos os recursos)
kubectl delete namespace argus
```

## 📋 Pré-requisitos

- **kubectl** configurado para o cluster sandbox
- **Helm 3.x** instalado
- Acesso ao Google Container Registry (GCR)
- Permissões para criar recursos no namespace `argus`

## 🏗️ Arquitetura

O deploy inclui os seguintes componentes:

### Aplicações
- **API** (FastAPI + LangGraph): `argus-agent-app`
- **MCP Server**: `argus-agent-mcp-server`
- **UI** (Angular + NGINX): `argus-agent-ui`

### Bancos de Dados
- **PostgreSQL**: `argus-agent-postgres` (autenticação)
- **ChromaDB**: `argus-agent-chromadb` (vetores RAG)

### Storage
- **PostgreSQL PVC**: 10Gi para dados de autenticação
- **ChromaDB PVC**: 10Gi para vetores RAG

### Rede
- **Ingress**: `sandbox.tcloud-devops.cloudtotvs.com.br`
  - `/` → UI
  - `/api/` → API
  - `/mcp/` → MCP Server

## 🔧 Configuração

### Imagens Utilizadas
- **API**: `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-api:20251004-154046`
- **MCP Server**: `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:20251004-154046`
- **UI**: `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-ui:20251004-154046`

### Secrets
- **argus-secrets**: Configurações da aplicação (LLM, Elasticsearch, JWT, etc.)
- **gcr-json-key**: Credenciais para pull de imagens do GCR

### Recursos
- **CPU**: 200m-1000m por pod
- **Memória**: 512Mi-1Gi por pod
- **Storage**: 10Gi para PostgreSQL + 10Gi para ChromaDB

## 🌐 Acesso

Após o deploy, as seguintes URLs estarão disponíveis:

- **UI Principal**: https://sandbox.tcloud-devops.cloudtotvs.com.br/
- **API**: https://sandbox.tcloud-devops.cloudtotvs.com.br/api/
- **MCP Server**: https://sandbox.tcloud-devops.cloudtotvs.com.br/mcp/

## 🔍 Monitoramento

### Verificar Status
```bash
# Status geral
kubectl get all -n argus

# Pods específicos
kubectl get pods -n argus -l app.kubernetes.io/name=argus-agent

# Recursos
kubectl top pods -n argus
```

### Logs
```bash
# Logs da API
kubectl logs -n argus deployment/argus-agent-app --tail=100

# Logs do MCP Server
kubectl logs -n argus deployment/argus-agent-mcp-server --tail=100

# Logs do PostgreSQL
kubectl logs -n argus deployment/argus-agent-postgres --tail=100

# Logs do ChromaDB
kubectl logs -n argus deployment/argus-agent-chromadb --tail=100
```

### Port Forward (para teste local)
```bash
# API
kubectl port-forward -n argus service/argus-agent-app 8000:8000

# UI
kubectl port-forward -n argus service/argus-agent-ui 8080:80

# MCP Server
kubectl port-forward -n argus service/argus-agent-mcp-server 8002:8002
```

## 🚨 Troubleshooting

### Problemas Comuns

1. **Pods em CrashLoopBackOff**
   ```bash
   # Verificar logs
   kubectl logs -n argus deployment/argus-agent-app
   
   # Verificar eventos
   kubectl get events -n argus
   ```

2. **Problemas de Conectividade**
   ```bash
   # Verificar services
   kubectl get services -n argus
   
   # Verificar ingress
   kubectl get ingress -n argus
   
   # Testar conectividade
   kubectl exec -n argus deployment/argus-agent-app -- curl http://argus-agent-postgres:5432
   ```

3. **Problemas de Storage**
   ```bash
   # Verificar PVCs
   kubectl get pvc -n argus
   
   # Verificar PVs
   kubectl get pv
   
   # Verificar storage class
   kubectl get storageclass
   ```

### Comandos Úteis

```bash
# Verificar status do Helm
helm list -n argus

# Verificar histórico do Helm
helm history argus-agent -n argus

# Rollback (se necessário)
helm rollback argus-agent 1 -n argus

# Verificar configuração
helm get values argus-agent -n argus
```

## 📊 Métricas

### Recursos Utilizados
- **CPU**: ~1.5 cores total
- **Memória**: ~2.5Gi total
- **Storage**: ~20Gi total

### Endpoints de Saúde
- **API**: `/health/ready`
- **MCP Server**: `/health/ready`
- **PostgreSQL**: `pg_isready`
- **ChromaDB**: `/api/v1/heartbeat`

## 🔄 Atualizações

### Atualizar Imagens
```bash
# Editar values-sandbox.yaml
# Alterar as tags das imagens

# Aplicar atualização
helm upgrade argus-agent . \
  --namespace argus \
  --values values-sandbox.yaml
```

### Atualizar Configurações
```bash
# Editar values-sandbox.yaml
# Aplicar mudanças
helm upgrade argus-agent . \
  --namespace argus \
  --values values-sandbox.yaml
```

## 📝 Notas Importantes

1. **Dados Persistentes**: Os dados são armazenados em volumes persistentes. A remoção do namespace apagará todos os dados.

2. **Secrets**: Os secrets contêm informações sensíveis. Nunca commite o arquivo `k8s/dev/secret.yaml`.

3. **Rede**: O ingress está configurado para usar TLS automático. Não é necessário configurar certificados manualmente.

4. **Recursos**: O deploy consome recursos significativos. Certifique-se de que o cluster tem capacidade suficiente.

5. **Backup**: Para ambientes de produção, configure backup dos volumes persistentes.

## 🆘 Suporte

Para problemas ou dúvidas:

1. Verifique os logs dos pods
2. Verifique os eventos do Kubernetes
3. Verifique a documentação do Helm chart
4. Entre em contato com a equipe de DevOps

---

**Última atualização**: 2025-01-04
**Versão**: 1.0.0
