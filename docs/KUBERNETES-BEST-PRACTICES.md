# 🎯 Kubernetes Best Practices - Argus Agent

## 📦 ConfigMap vs Hardcoded na Imagem

### ❌ Abordagem Anterior (Hardcoded):

```dockerfile
# ui/Dockerfile
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf  # ❌ Hardcoded
COPY dist/ /usr/share/nginx/html
```

**Problemas:**
- ❌ Requer rebuild da imagem para qualquer mudança
- ❌ Nome do serviço hardcoded (`argus-api` vs `argus-agent-api`)
- ❌ Impossível ter configs diferentes por ambiente
- ❌ Não segue 12-factor app principles

### ✅ Abordagem Recomendada (ConfigMap):

```yaml
# helm/argus-agent/templates/ui-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: argus-agent-ui-nginx
data:
  nginx.conf: |
    # Configuração usa templates Helm
    proxy_pass http://{{ include "argus-agent.fullname" . }}-api:{{ .Values.api.service.port }}/api/;
```

```yaml
# helm/argus-agent/templates/ui-deployment.yaml
volumeMounts:
- name: nginx-config
  mountPath: /etc/nginx/nginx.conf
  subPath: nginx.conf
volumes:
- name: nginx-config
  configMap:
    name: argus-agent-ui-nginx
```

**Vantagens:**
- ✅ **Sem rebuild**: Mudanças aplicadas com `kubectl apply` ou `helm upgrade`
- ✅ **Flexível**: Diferentes configs por ambiente (dev, staging, prod)
- ✅ **Nomes dinâmicos**: Usa templates Helm para nomes de serviços
- ✅ **Versionado**: ConfigMap versionado no Git
- ✅ **Rollback fácil**: `helm rollback`
- ✅ **12-factor compliant**: Configuração separada do código

## 🔄 Workflow de Mudanças:

### Antes (Hardcoded):
```bash
1. Editar ui/nginx.conf
2. docker build -t argus-ui:new-tag .
3. docker push argus-ui:new-tag
4. Atualizar values.yaml com new-tag
5. helm upgrade argus-agent ...
⏱️ Tempo: ~5-10 minutos (build + push)
```

### Agora (ConfigMap):
```bash
1. Editar helm/argus-agent/templates/ui-configmap.yaml
2. helm upgrade argus-agent ...
⏱️ Tempo: ~10 segundos
```

## 🌍 Configs por Ambiente:

### values-dev.yaml:
```yaml
ui:
  nginxConfig:
    apiServiceName: "argus-agent-api"
    apiPort: 8000
```

### values-prod.yaml:
```yaml
ui:
  nginxConfig:
    apiServiceName: "argus-api-prod"
    apiPort: 80
    enableCaching: true
    customHeaders:
      - "X-Custom-Header: production"
```

## 📊 Comparação Completa:

| Aspecto | Hardcoded na Imagem | ConfigMap (K8s) | Template com envsubst |
|---------|--------------------|-----------------|-----------------------|
| **Rebuild necessário** | ❌ Sim | ✅ Não | ⚠️ Só se mudar entrypoint |
| **Tempo de mudança** | 5-10 min | 10 seg | 10 seg |
| **Configs por ambiente** | ❌ Não | ✅ Sim | ✅ Sim |
| **Funciona fora do K8s** | ✅ Sim | ❌ Não | ✅ Sim |
| **Complexidade** | ✅ Baixa | ⚠️ Média | ⚠️ Média-Alta |
| **Melhor prática K8s** | ❌ Não | ✅ **SIM** | ⚠️ Depende |
| **Versionamento** | Imagem | Git (Helm) | Git (Helm) |
| **Rollback** | Tag anterior | `helm rollback` | `helm rollback` |

## 🎯 Recomendação:

### Use **ConfigMap** quando:
- ✅ Deploy no Kubernetes
- ✅ Múltiplos ambientes
- ✅ Configurações podem mudar
- ✅ Nomes de serviços são dinâmicos

### Use **Hardcoded** quando:
- ✅ Docker Compose local
- ✅ Ambiente único e estável
- ✅ Config nunca muda
- ✅ Simplicidade é prioridade

### Use **envsubst Template** quando:
- ✅ Muitas variáveis dinâmicas
- ✅ Precisa funcionar em K8s e Docker
- ✅ Configuração complexa por ambiente

## 💡 Outras Best Practices Aplicadas:

### 1. **Secrets no Kubernetes Secret (não ConfigMap)**
```yaml
# ❌ NÃO FAÇA ISSO:
apiVersion: v1
kind: ConfigMap
data:
  DATABASE_PASSWORD: "secret123"  # ❌ Visível para todos!

# ✅ FAÇA ISSO:
apiVersion: v1
kind: Secret
type: Opaque
stringData:
  DATABASE_PASSWORD: "secret123"  # ✅ Base64 encoded, RBAC protegido
```

### 2. **Probes Corretos**
```yaml
# ✅ API/MCP Server: HTTP probes com endpoints específicos
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000

# ✅ ChromaDB: TCP probes (API v1 deprecated)
livenessProbe:
  tcpSocket:
    port: 8000

# ✅ PostgreSQL: Exec probe com comando nativo
livenessProbe:
  exec:
    command: ["pg_isready", "-U", "argus"]
```

### 3. **Resource Limits**
```yaml
resources:
  requests:  # O que o pod PRECISA
    memory: "256Mi"
    cpu: "100m"
  limits:  # O que o pod PODE usar no máximo
    memory: "512Mi"
    cpu: "500m"
```

### 4. **Security Context**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  readOnlyRootFilesystem: true  # Quando possível
```

## 📚 Referências:

- [Kubernetes ConfigMap Best Practices](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [12-Factor App - Config](https://12factor.net/config)
- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)

## 🔄 Migração Implementada:

```bash
# 1. Criado ConfigMap com nginx.conf
✅ helm/argus-agent/templates/ui-configmap.yaml

# 2. Atualizado Deployment para montar ConfigMap
✅ helm/argus-agent/templates/ui-deployment.yaml

# 3. Imagem UI agora pode ser genérica
✅ Qualquer tag funcionará, config vem do ConfigMap

# 4. Upgrade sem rebuild:
helm upgrade argus-agent ./helm/argus-agent -n argus -f values-sandbox.yaml
```

## 🎉 Resultado:

**Antes**: Mudança no nginx.conf = rebuild imagem (~10 min)  
**Agora**: Mudança no nginx.conf = helm upgrade (~10 seg)  

**Flexibilidade**: Mesma imagem funciona em dev, staging e prod! 🚀

