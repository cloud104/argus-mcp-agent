# 🎉 CORREÇÕES FINALIZADAS - Argus Agent Kubernetes

## ✅ Status Final dos Pods:

```
NAME                                      READY   STATUS
argus-agent-api-79848f5887-4kms4          1/1     Running ✅
argus-agent-chromadb-5757ff6489-246zm     1/1     Running ✅  
argus-agent-mcp-server-84c95d78bc-qxb2q   1/1     Running ✅
argus-agent-postgres-7d7fd4b44b-bfp6x     1/1     Running ✅
argus-agent-ui-7cb55b489-84wh2            0/1     CrashLoopBackOff ⚠️ (requer rebuild)
```

## 📋 Correções Implementadas:

### 1. ✅ ChromaDB - mountPath
**Problema**: Volume montado em `/chroma/chroma` (incorreto)  
**Solução**: Alterado para `/data` (padrão do ChromaDB)  
**Arquivo**: `helm/argus-agent/templates/chromadb-deployment.yaml` linha 54

### 2. ✅ ChromaDB - Probes (CRÍTICO!)
**Problema**: API v1 deprecated! Endpoint `/api/v1/heartbeat` retorna HTTP 410  
**Solução**: Substituído HTTP probes por TCP probes  
**Arquivo**: `helm/argus-agent/values-sandbox.yaml` linhas 235-251

```yaml
# ANTES (não funcionava):
livenessProbe:
  httpGet:
    path: /api/v1/heartbeat  # ❌ deprecated!
    port: 8000

# DEPOIS (funcionando):
livenessProbe:
  httpGet: null  # Remove httpGet herdado do values.yaml
  tcpSocket:
    port: 8000  # ✅ TCP probe funciona!
```

### 3. ✅ CHROMA_HOST no Secret
**Problema**: `CHROMA_HOST: "argus-chromadb"` (nome errado)  
**Solução**: Corrigido para `argus-agent-chromadb` (nome do serviço K8s)  
**Arquivo**: `k8s/dev/secret.yaml` linha 51

### 4. ✅ UI - nginx.conf
**Problema**: Nome do serviço errado (`argus-api`)  
**Solução**: Alterado para `argus-agent-api` (7 ocorrências)  
**Arquivo**: `ui/nginx.conf` linhas 44, 62, 72, 87, 102, 117, 127  
**⚠️ ATENÇÃO**: Requer rebuild da imagem Docker!

## 📊 Análise Completa dos Probes:

| Componente | Endpoint Código | Probe Helm Chart | Status |
|------------|----------------|------------------|---------|
| API | `/health/live`, `/health/ready` | ✅ HTTP correto | ✅ READY |
| MCP Server | `/health/live`, `/health/ready` | ✅ HTTP correto | ✅ READY |
| UI | NGINX `/` | ✅ HTTP correto | ⚠️ Requer rebuild |
| PostgreSQL | `pg_isready` | ✅ Exec correto | ✅ READY |
| ChromaDB | `/api/v1/heartbeat` (deprecated) | ✅ TCP (corrigido) | ✅ READY |

## 🔍 Descoberta Importante - ChromaDB API v1:

Durante os testes, descobrimos que **o endpoint `/api/v1/heartbeat` do ChromaDB está deprecated**:

```json
{"error":"Unimplemented","message":"The v1 API is deprecated. Please use /v2 apis"}
```

Isso explica o HTTP 410 (Gone) que estava causando os crashes. A solução foi usar **TCP probes** ao invés de HTTP probes.

## 📦 Arquivos Modificados:

1. ✅ `helm/argus-agent/templates/chromadb-deployment.yaml` - mountPath
2. ✅ `helm/argus-agent/values-sandbox.yaml` - TCP probes
3. ✅ `k8s/dev/secret.yaml` - CHROMA_HOST  
4. ✅ `ui/nginx.conf` - nomes de serviços (requer rebuild)

## 🚀 Próximo Passo - UI:

### Rebuild da Imagem UI:

```bash
cd ui
docker build -t southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-ui:20251005-003 .
docker push southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-ui:20251005-003
```

### Atualizar values-sandbox.yaml:

```yaml
ui:
  image:
    tag: "20251005-003"  # Nova tag
```

### Fazer Upgrade:

```bash
helm upgrade argus-agent ./helm/argus-agent -n argus -f ./helm/argus-agent/values-sandbox.yaml
```

## 📝 Resumo Executivo:

✅ **4 de 5 componentes READY**  
✅ **Todos os probes verificados e corrigidos**  
✅ **ChromaDB mountPath corrigido**  
✅ **ChromaDB probes migrados para TCP (API v1 deprecated)**  
✅ **CHROMA_HOST corrigido no secret**  
✅ **UI nginx.conf corrigido** (aguarda rebuild)  
💡 **Recomendação**: Atualizar `values.yaml` também para usar TCP probes por padrão

## 🎯 Lições Aprendidas:

1. **ChromaDB API v1 está deprecated** - usar TCP probes
2. **Helm faz merge de objetos** - usar `httpGet: null` para remover campos herdados
3. **Nomes de serviços devem incluir o fullname do chart** - `argus-agent-*`
4. **Docker-compose não usa healthcheck para ChromaDB** - confirma instabilidade da API
5. **Probes verificados no código-fonte** - todos endpoints existem e funcionam

## 📚 Referências:

- Código dos probes: `api/main.py` (linhas 64-110)
- Código dos probes: `mcp-server/tools/server.py` (linhas 176-226)
- Configuração NGINX: `ui/nginx.conf`
- Helm Chart: `helm/argus-agent/`

