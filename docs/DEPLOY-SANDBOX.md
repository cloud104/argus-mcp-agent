# Guia de Deploy - Cluster Sandbox

Este guia descreve como fazer o deploy completo do Argus Agent no cluster Kubernetes sandbox.

## Pré-requisitos

1. **kubectl** configurado para o cluster sandbox
2. **Helm 3.x** instalado
3. Acesso ao Google Container Registry (GCR)
4. Namespace `argus` criado no cluster

## 1. Configuração do Contexto

```bash
# Verificar contexto atual
kubectl config current-context

# Se necessário, alterar para o contexto sandbox
kubectl config use-context sandbox
```

## 2. Criação do Namespace

```bash
# Criar namespace argus
kubectl create namespace argus

# Verificar criação
kubectl get namespace argus
```

## 3. Aplicação dos Secrets

### 3.1 Secret para GCR (Image Pull Secret)

```bash
# Aplicar o secret para pull de imagens do GCR
kubectl apply -f k8s/dev/secret.yaml
```

### 3.2 Verificar Secrets

```bash
# Listar secrets no namespace argus
kubectl get secrets -n argus

# Verificar se os secrets foram criados corretamente
kubectl describe secret argus-secrets -n argus
kubectl describe secret gcr-json-key -n argus
```

## 4. Deploy via Helm

### 4.1 Adicionar Repositório Helm (se necessário)

```bash
# Adicionar repositório estável do Helm
helm repo add stable https://charts.helm.sh/stable
helm repo update
```

### 4.2 Deploy do Chart

```bash
# Fazer deploy do chart a partir da raiz do projeto
helm upgrade --install argus-agent ./helm/argus-agent \
  --namespace argus \
  --create-namespace \
  --values helm/argus-agent/values-sandbox.yaml \
  --timeout 10m
```

**Nota:** Usamos `values-sandbox.yaml` que contém as configurações específicas para o ambiente sandbox.

### 4.3 Verificar Deploy

```bash
# Verificar status do release
helm list -n argus

# Verificar pods
kubectl get pods -n argus

# Verificar services
kubectl get services -n argus

# Verificar ingress
kubectl get ingress -n argus
```

## 5. Verificação dos Componentes

### 5.1 Verificar Deployments

```bash
# Verificar todos os deployments
kubectl get deployments -n argus

# Verificar logs de cada componente
kubectl logs -n argus deployment/argus-agent-api
kubectl logs -n argus deployment/argus-agent-mcp-server
kubectl logs -n argus deployment/argus-agent-ui
kubectl logs -n argus deployment/argus-agent-postgres
kubectl logs -n argus deployment/argus-agent-chromadb
```

### 5.2 Verificar Persistent Volumes

```bash
# Verificar PVCs
kubectl get pvc -n argus

# Verificar PVs
kubectl get pv
```

### 5.3 Verificar Ingress

```bash
# Verificar ingress
kubectl get ingress -n argus

# Verificar detalhes do ingress
kubectl describe ingress argus-agent -n argus
```

## 6. Teste de Acesso

### 6.1 URLs de Acesso

Após o deploy, as seguintes URLs estarão disponíveis:

- **UI Principal**: `https://sandbox.tcloud-devops.cloudtotvs.com.br/`
- **API**: `https://sandbox.tcloud-devops.cloudtotvs.com.br/api/`
- **MCP Server**: `https://sandbox.tcloud-devops.cloudtotvs.com.br/mcp/`

### 6.2 Teste de Conectividade

```bash
# Testar conectividade com a API
curl -k https://sandbox.tcloud-devops.cloudtotvs.com.br/api/health/ready

# Testar conectividade com o MCP Server
curl -k https://sandbox.tcloud-devops.cloudtotvs.com.br/mcp/health/ready

# Testar UI
curl -k https://sandbox.tcloud-devops.cloudtotvs.com.br/
```

## 7. Troubleshooting

### 7.1 Verificar Logs

```bash
# Logs da API
kubectl logs -n argus -l app=argus-api --tail=100 -f

# Logs do MCP Server
kubectl logs -n argus -l app=argus-mcp-server --tail=100 -f

# Logs da UI
kubectl logs -n argus -l app=argus-ui --tail=100 -f

# Logs do PostgreSQL
kubectl logs -n argus -l app=argus-postgres --tail=100 -f

# Logs do ChromaDB
kubectl logs -n argus -l app=argus-chromadb --tail=100 -f
```

### 7.2 Verificar Recursos

```bash
# Verificar uso de recursos
kubectl top pods -n argus

# Verificar eventos
kubectl get events -n argus --sort-by='.lastTimestamp'
```

### 7.3 Problemas Comuns

1. **Pods em CrashLoopBackOff**:
   - Verificar logs dos pods
   - Verificar se os secrets estão corretos
   - Verificar se as variáveis de ambiente estão definidas

2. **Problemas de Conectividade**:
   - Verificar se os services estão rodando
   - Verificar se o ingress está configurado corretamente
   - Verificar se o DNS está resolvendo corretamente

3. **Problemas de Storage**:
   - Verificar se os PVCs foram criados
   - Verificar se há storage class disponível
   - Verificar permissões de acesso

## 8. Atualização do Deploy

### 8.1 Upgrade do Chart

```bash
# Atualizar o chart
helm upgrade argus-agent ./helm/argus-agent \
  --namespace argus \
  --values helm/argus-agent/values-sandbox.yaml \
  --timeout 10m
```

### 8.2 Rollback (se necessário)

```bash
# Listar histórico de releases
helm history argus-agent -n argus

# Fazer rollback para versão anterior
helm rollback argus-agent 1 -n argus
```

## 9. Limpeza (se necessário)

### 9.1 Remover Release

```bash
# Remover release do Helm
helm uninstall argus-agent -n argus
```

### 9.2 Remover Namespace

```bash
# Remover namespace (remove todos os recursos)
kubectl delete namespace argus
```

## 10. Monitoramento

### 10.1 Verificar Status dos Pods

```bash
# Verificar status geral
kubectl get pods -n argus -o wide

# Verificar readiness e liveness
kubectl describe pods -n argus
```

### 10.2 Verificar Recursos

```bash
# Verificar uso de CPU e memória
kubectl top pods -n argus

# Verificar uso de storage
kubectl top pvc -n argus
```

## 11. Configurações Específicas do Sandbox

### 11.1 Imagens Utilizadas

- **API**: `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-api:20251004-154046`
- **MCP Server**: `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-mcp-server:20251004-154046`
- **UI**: `southamerica-east1-docker.pkg.dev/tcloud-devops/tcloud-devops/argus-ui:20251004-154046`

### 11.2 Host Base

- **Host**: `sandbox.tcloud-devops.cloudtotvs.com.br`
- **TLS**: Configurado automaticamente pelo controller nginx

### 11.3 Namespace

- **Namespace**: `argus`
- **Context**: `sandbox`

## 12. Comandos Úteis

```bash
# Verificar status completo
kubectl get all -n argus

# Verificar ingress
kubectl get ingress -n argus -o yaml

# Verificar secrets
kubectl get secrets -n argus

# Verificar configmaps
kubectl get configmaps -n argus

# Port forward para teste local
kubectl port-forward -n argus service/argus-agent-api 8000:8000
kubectl port-forward -n argus service/argus-agent-mcp-server 8002:8002
kubectl port-forward -n argus service/argus-agent-ui 8080:80
```

## 13. Próximos Passos

1. **Configurar monitoramento** com Prometheus/Grafana
2. **Configurar backup** dos volumes persistentes
3. **Configurar autoscaling** baseado em métricas
4. **Configurar alertas** para falhas de componentes
5. **Implementar CI/CD** para atualizações automáticas

---

**Nota**: Este guia assume que você tem as permissões necessárias no cluster sandbox e que os recursos de storage estão disponíveis.
