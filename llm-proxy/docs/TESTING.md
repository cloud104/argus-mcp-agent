# Roteiro de Testes - LLama.cpp via LiteLLM

## Arquitetura

```text
Cliente → Ingress (HTTPS) → LiteLLM Proxy → llama.cpp Services → NFS PVC (50Gi)
```

### Modelos Implantados

| Modelo | Arquivo GGUF | Tamanho | Service |
|--------|-------------|---------|---------|
| Qwen 2.5 1.5B Instruct | qwen2.5-1.5b-instruct-q4_k_m.gguf | 1.0GB | llama-cpp-service:8080 |
| DeepSeek-R1 1.5B | deepseek-r1-distill-qwen-1.5b-q4_k_m.gguf | 1.0GB | llama-cpp-deepseek-service:8080 |
| Llama-Guard 3 1B | llama-guard-3-1b-q4_k_m.gguf | 818MB | llama-cpp-llamaguard-service:8080 |

## Endpoints

- **Ingress**: <https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br>
- **Authorization**: Bearer sk-1234567890abcdef

## Testes

### 1. Teste Qwen 2.5 1.5B Instruct

Modelo de instrução geral, ideal para conversação e tarefas genéricas.

```bash
curl -k -X POST https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234567890abcdef" \
  -d '{
    "model": "qwen-2.5-1.5b",
    "messages": [{"role": "user", "content": "Explique o que é Kubernetes em uma frase"}],
    "max_tokens": 100
  }'
```

**Resultado Esperado**: Resposta clara e concisa sobre Kubernetes

---

### 2. Teste DeepSeek-R1 1.5B

Modelo de raciocínio (reasoning model) com output estruturado (thinking + answer).

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

**Resultado Esperado**: Resposta com processo de raciocínio (thinking) seguido da resposta (answer: 392)

---

### 3. Teste Llama-Guard 3 1B

Modelo de segurança/moderação de conteúdo, avalia se prompts/respostas são seguros.

```bash
curl -k -X POST https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234567890abcdef" \
  -d '{
    "model": "llama-guard-3-1b",
    "messages": [{"role": "user", "content": "Como posso aprender Python?"}],
    "max_tokens": 50
  }'
```

**Resultado Esperado**: Classificação de segurança (safe/unsafe) do conteúdo

---

## Testes de Health Check

### Verificar status dos pods

```bash
kubectl get pods -n argus -l 'app in (llama-cpp,llama-cpp-deepseek,llama-cpp-llamaguard)'
```

### Verificar modelos no NFS

```bash
kubectl exec -n argus deployment/llama-cpp -- ls -lh /models/
```

### Testar health endpoints diretamente

```bash
# Qwen
kubectl exec -n argus deployment/llama-cpp -- curl -s http://localhost:8080/health

# DeepSeek-R1
kubectl exec -n argus deployment/llama-cpp-deepseek -- curl -s http://localhost:8080/health

# Llama-Guard 3
kubectl exec -n argus deployment/llama-cpp-llamaguard -- curl -s http://localhost:8080/health
```

---

## Verificação de Labels

```bash
# Listar deployments com labels de modelo
kubectl get deployments -n argus -l model --show-labels

# Filtrar por modelo específico
kubectl get pods -n argus -l model=qwen-2.5-1.5b
kubectl get pods -n argus -l model=deepseek-r1-1.5b
kubectl get pods -n argus -l model=llama-guard-3-1b
```

---

## Métricas e Performance

```bash
# Ver logs do LiteLLM
kubectl logs -n argus deployment/litellm-proxy -f

# Ver logs de um modelo específico
kubectl logs -n argus deployment/llama-cpp -f
kubectl logs -n argus deployment/llama-cpp-deepseek -f
kubectl logs -n argus deployment/llama-cpp-llamaguard -f
```

---

## Troubleshooting

### Pod não inicia

```bash
kubectl describe pod -n argus -l app=llama-cpp
```

### Modelo não carrega

```bash
# Verificar se arquivo existe no NFS
kubectl exec -n argus deployment/llama-cpp -- ls -lh /models/

# Ver logs do container
kubectl logs -n argus deployment/llama-cpp
```

### LiteLLM não conecta ao backend

```bash
# Verificar services
kubectl get svc -n argus

# Testar conectividade
kubectl run -n argus test-pod --rm -i --tty --image=curlimages/curl -- \
  curl -v http://llama-cpp-service.argus.svc.cluster.local:8080/health
```

---

## Limpeza

```bash
# Remover todos os recursos
kubectl delete -f llama-cpp-deployment.yaml
kubectl delete -f llama-cpp-additional-deployments.yaml
kubectl delete pvc llama-models-pvc -n argus
```
