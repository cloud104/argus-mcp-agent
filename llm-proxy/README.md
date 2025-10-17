# LLM Proxy - Local LLM Deployment

Módulo para deployment de LLMs locais usando llama.cpp atrás do LiteLLM Proxy no Kubernetes.

## Arquitetura

```text
Cliente → Ingress (HTTPS) → LiteLLM Proxy → llama.cpp Services → NFS PVC (50Gi)
```

### Componentes

**LiteLLM Proxy**
- Proxy unificado para múltiplos LLMs
- API compatível com OpenAI
- Roteamento inteligente de requisições
- Endpoint: `https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br`

**llama.cpp**
- Runtime eficiente para modelos GGUF
- Baixo uso de memória com quantização Q4_K_M
- Execução em CPU (4 threads por modelo)
- API compatível com OpenAI `/v1/chat/completions`

**Storage**
- PVC NFS 50Gi (ReadWriteMany)
- StorageClass: `nfs-persistence`
- Modelos compartilhados entre todos os pods

## Modelos Disponíveis

| Modelo | Tamanho | Uso Recomendado | Service |
|--------|---------|----------------|---------|
| **Qwen 2.5 1.5B Instruct** | 1.0GB | Conversação geral, instruções | llama-cpp-service:8080 |
| **DeepSeek-R1 1.5B** | 1.0GB | Raciocínio, matemática, análise | llama-cpp-deepseek-service:8080 |
| **Llama-Guard 3 1B** | 818MB | Moderação de conteúdo, segurança | llama-cpp-llamaguard-service:8080 |

## Estrutura de Arquivos

```text
llm-proxy/
├── README.md                 # Este arquivo
├── k8s/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── litellm/
│   │   │   ├── namespace.yaml
│   │   │   ├── configmap.yaml
│   │   │   ├── secret.yaml
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   └── kustomization.yaml
│   │   └── llama-cpp/
│   │       ├── pvc.yaml
│   │       ├── qwen-deployment.yaml
│   │       ├── deepseek-deployment.yaml
│   │       ├── llamaguard-deployment.yaml
│   │       ├── services.yaml
│   │       └── kustomization.yaml
│   └── jobs/
│       └── model-download-jobs.yaml (referência)
├── scripts/
│   └── upload-model.sh       # Script para upload de modelos
└── docs/
    └── TESTING.md            # Roteiro de testes
```

## Quick Start

### 1. Deploy Completo

```bash
# Deploy usando kustomize
kubectl apply -k llm-proxy/k8s/base

# Ou deploy direto dos manifests
kubectl apply -f llm-proxy/k8s/base/litellm/
kubectl apply -f llm-proxy/k8s/base/llama-cpp/
```

### 2. Upload de Modelos

```bash
# Download dos modelos (fazer localmente)
curl -L -o qwen2.5-1.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf

curl -L -o deepseek-r1-distill-qwen-1.5b-q4_k_m.gguf \
  https://huggingface.co/unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf

curl -L -o llama-guard-3-1b-q4_k_m.gguf \
  https://huggingface.co/QuantFactory/Llama-Guard-3-1B-GGUF/resolve/main/Llama-Guard-3-1B.Q4_K_M.gguf

# Upload para o cluster
./llm-proxy/scripts/upload-model.sh qwen2.5-1.5b-instruct-q4_k_m.gguf
./llm-proxy/scripts/upload-model.sh deepseek-r1-distill-qwen-1.5b-q4_k_m.gguf
./llm-proxy/scripts/upload-model.sh llama-guard-3-1b-q4_k_m.gguf
```

### 3. Verificar Deployment

```bash
# Verificar pods
kubectl get pods -n argus -l 'app in (llama-cpp,llama-cpp-deepseek,llama-cpp-llamaguard)'

# Verificar services
kubectl get svc -n argus | grep llama

# Verificar modelos no NFS
kubectl exec -n argus deployment/llama-cpp -- ls -lh /models/
```

## Uso da API

### Endpoint

```bash
https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions
```

### Autenticação

```bash
Authorization: Bearer sk-1234567890abcdef
```

### Exemplos

**Qwen 2.5 (Conversação)**
```bash
curl -k -X POST https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234567890abcdef" \
  -d '{
    "model": "qwen-2.5-1.5b",
    "messages": [{"role": "user", "content": "Explique Kubernetes"}],
    "max_tokens": 100
  }'
```

**DeepSeek-R1 (Raciocínio)**
```bash
curl -k -X POST https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234567890abcdef" \
  -d '{
    "model": "deepseek-r1-1.5b",
    "messages": [{"role": "user", "content": "Calcule: 15 * 23 + 47"}],
    "max_tokens": 150
  }'
```

**Llama-Guard 3 (Moderação)**
```bash
curl -k -X POST https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234567890abcdef" \
  -d '{
    "model": "llama-guard-3-1b",
    "messages": [{"role": "user", "content": "Como aprender Python?"}],
    "max_tokens": 50
  }'
```

## Configuração

### Adicionar Novo Modelo

1. **Criar Deployment**

Copie um deployment existente e ajuste:
- `metadata.name`
- `metadata.labels.model`
- `spec.template.spec.containers[0].args[5]` (caminho do modelo)
- `spec.template.spec.containers[0].resources`

2. **Criar Service**

Adicione um novo service em `services.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: llama-cpp-novomodelo-service
  namespace: argus
spec:
  selector:
    app: llama-cpp-novomodelo
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
  type: ClusterIP
```

3. **Atualizar LiteLLM ConfigMap**

Adicione em `litellm/configmap.yaml`:
```yaml
- model_name: novo-modelo
  litellm_params:
    model: openai/novo-modelo
    api_base: http://llama-cpp-novomodelo-service.argus.svc.cluster.local:8080/v1
```

4. **Deploy**
```bash
kubectl apply -f llm-proxy/k8s/base/llama-cpp/novomodelo-deployment.yaml
kubectl apply -f llm-proxy/k8s/base/llama-cpp/services.yaml
kubectl apply -f llm-proxy/k8s/base/litellm/configmap.yaml
kubectl rollout restart deployment/litellm-proxy -n argus
```

### Atualizar Secret do LiteLLM

```bash
kubectl edit secret litellm-secret -n argus
```

## Performance

- **Qwen 2.5**: ~9.7 tokens/s (CPU, 4 threads)
- **DeepSeek-R1**: ~6.8 tokens/s (CPU, 4 threads)
- **Llama-Guard 3**: ~10 tokens/s (CPU, 4 threads)

## Recursos

### Por Pod

| Componente | CPU Request | CPU Limit | Memory Request | Memory Limit |
|------------|-------------|-----------|----------------|--------------|
| LiteLLM | 250m | 1000m | 512Mi | 2Gi |
| Qwen | 1000m | 2000m | 4Gi | 6Gi |
| DeepSeek-R1 | 1000m | 2000m | 4Gi | 6Gi |
| Llama-Guard | 500m | 2000m | 2Gi | 4Gi |

### Total
- **CPU**: ~3.75 cores (request) / ~8 cores (limit)
- **Memory**: ~11.5Gi (request) / ~18Gi (limit)
- **Storage**: 50Gi NFS (RWX)

## Troubleshooting

### Pod não inicia

```bash
kubectl describe pod -n argus <pod-name>
kubectl logs -n argus <pod-name>
```

### Modelo não encontrado

```bash
# Verificar se o arquivo existe no NFS
kubectl exec -n argus deployment/llama-cpp -- ls -lh /models/

# Re-upload do modelo
./llm-proxy/scripts/upload-model.sh <modelo.gguf>
```

### LiteLLM não conecta ao backend

```bash
# Testar conectividade direta
kubectl run test-pod -n argus --rm -i --tty --image=curlimages/curl -- \
  curl -v http://llama-cpp-service.argus.svc.cluster.local:8080/health

# Verificar logs do LiteLLM
kubectl logs -n argus deployment/litellm-proxy -f
```

## Limpeza

```bash
# Remover deployments
kubectl delete -k llm-proxy/k8s/base

# Remover PVC (apaga os modelos!)
kubectl delete pvc llama-models-pvc -n argus
```

## Referências

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [llama.cpp Server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md)
- [GGUF Model Format](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
- [Roteiro de Testes](./docs/TESTING.md)
