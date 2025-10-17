.PHONY: help deploy deploy-litellm deploy-llama status logs clean test upload-model

NAMESPACE ?= argus

help:
	@echo "LLM Proxy - Makefile"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make deploy              - Deploy completo (LiteLLM + llama.cpp)"
	@echo "  make deploy-litellm      - Deploy apenas LiteLLM"
	@echo "  make deploy-llama        - Deploy apenas llama.cpp"
	@echo "  make status              - Verificar status dos pods"
	@echo "  make logs                - Ver logs do LiteLLM"
	@echo "  make logs-qwen           - Ver logs do Qwen"
	@echo "  make logs-deepseek       - Ver logs do DeepSeek-R1"
	@echo "  make logs-llamaguard     - Ver logs do Llama-Guard"
	@echo "  make test                - Testar os 3 modelos"
	@echo "  make clean               - Remover todos os recursos"
	@echo "  make upload-model        - Upload de modelo (MODEL=path/to/model.gguf)"
	@echo ""

deploy:
	@echo "=== Deploying LLM Proxy ==="
	kubectl apply -k k8s/base/
	@echo ""
	@echo "Aguardando pods ficarem prontos..."
	kubectl wait --for=condition=ready pod -l app=litellm-proxy -n $(NAMESPACE) --timeout=120s || true
	kubectl wait --for=condition=ready pod -l app=llama-cpp -n $(NAMESPACE) --timeout=120s || true
	kubectl wait --for=condition=ready pod -l app=llama-cpp-deepseek -n $(NAMESPACE) --timeout=120s || true
	kubectl wait --for=condition=ready pod -l app=llama-cpp-llamaguard -n $(NAMESPACE) --timeout=120s || true
	@echo ""
	@$(MAKE) status

deploy-litellm:
	@echo "=== Deploying LiteLLM ==="
	kubectl apply -k k8s/base/litellm/
	kubectl wait --for=condition=ready pod -l app=litellm-proxy -n $(NAMESPACE) --timeout=120s

deploy-llama:
	@echo "=== Deploying llama.cpp ==="
	kubectl apply -k k8s/base/llama-cpp/
	kubectl wait --for=condition=ready pod -l 'app in (llama-cpp,llama-cpp-deepseek,llama-cpp-llamaguard)' -n $(NAMESPACE) --timeout=120s

status:
	@echo "=== Status dos Pods ==="
	kubectl get pods -n $(NAMESPACE) -l 'app in (litellm-proxy,llama-cpp,llama-cpp-deepseek,llama-cpp-llamaguard)' -o wide
	@echo ""
	@echo "=== Status dos Services ==="
	kubectl get svc -n $(NAMESPACE) | grep -E '(litellm|llama)'
	@echo ""
	@echo "=== Modelos no NFS ==="
	kubectl exec -n $(NAMESPACE) deployment/llama-cpp -- ls -lh /models/ 2>/dev/null || echo "Aguardando pod llama-cpp ficar pronto..."

logs:
	kubectl logs -n $(NAMESPACE) deployment/litellm-proxy -f

logs-qwen:
	kubectl logs -n $(NAMESPACE) deployment/llama-cpp -f

logs-deepseek:
	kubectl logs -n $(NAMESPACE) deployment/llama-cpp-deepseek -f

logs-llamaguard:
	kubectl logs -n $(NAMESPACE) deployment/llama-cpp-llamaguard -f

test:
	@echo "=== Testando Qwen 2.5 1.5B ==="
	@curl -k -s -X POST https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions \
	  -H "Content-Type: application/json" \
	  -H "Authorization: Bearer sk-1234567890abcdef" \
	  -d '{"model": "qwen-2.5-1.5b", "messages": [{"role": "user", "content": "Diga olá"}], "max_tokens": 50}' \
	  | jq -r '.choices[0].message.content' || echo "Falha no teste"
	@echo ""
	@echo "=== Testando DeepSeek-R1 1.5B ==="
	@curl -k -s -X POST https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions \
	  -H "Content-Type: application/json" \
	  -H "Authorization: Bearer sk-1234567890abcdef" \
	  -d '{"model": "deepseek-r1-1.5b", "messages": [{"role": "user", "content": "2+2=?"}], "max_tokens": 50}' \
	  | jq -r '.choices[0].message.content' || echo "Falha no teste"
	@echo ""
	@echo "=== Testando Llama-Guard 3 1B ==="
	@curl -k -s -X POST https://litellm.sandbox.tcloud-devops.cloudtotvs.com.br/chat/completions \
	  -H "Content-Type: application/json" \
	  -H "Authorization: Bearer sk-1234567890abcdef" \
	  -d '{"model": "llama-guard-3-1b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 20}' \
	  | jq -r '.choices[0].message.content' || echo "Falha no teste"

upload-model:
ifndef MODEL
	@echo "Erro: especifique MODEL=path/to/model.gguf"
	@exit 1
endif
	./scripts/upload-model.sh $(MODEL) $(NAMESPACE)

clean:
	@echo "=== Removendo recursos ==="
	kubectl delete -k k8s/base/ || true
	@echo ""
	@echo "Para remover o PVC (apaga os modelos!):"
	@echo "  kubectl delete pvc llama-models-pvc -n $(NAMESPACE)"
