#!/bin/bash

set -e

MODEL_FILE="$1"
NAMESPACE="${2:-argus}"

if [ -z "$MODEL_FILE" ]; then
  echo "Uso: $0 <caminho-do-modelo.gguf> [namespace]"
  echo ""
  echo "Exemplo:"
  echo "  $0 ./qwen2.5-1.5b-instruct-q4_k_m.gguf"
  echo "  $0 ./deepseek-r1-distill-qwen-1.5b-q4_k_m.gguf argus"
  exit 1
fi

if [ ! -f "$MODEL_FILE" ]; then
  echo "Erro: Arquivo $MODEL_FILE não encontrado"
  exit 1
fi

MODEL_NAME=$(basename "$MODEL_FILE")

echo "=== Upload de Modelo GGUF para NFS ===="
echo "Modelo: $MODEL_NAME"
echo "Namespace: $NAMESPACE"
echo ""

echo "=== Criando pod helper para upload ===="
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: llama-upload-helper
  namespace: $NAMESPACE
spec:
  containers:
  - name: helper
    image: busybox:latest
    command: ["sh", "-c", "sleep 3600"]
    volumeMounts:
    - name: llama-models
      mountPath: /models
  volumes:
  - name: llama-models
    persistentVolumeClaim:
      claimName: llama-models-pvc
  restartPolicy: Never
EOF

echo "Aguardando pod ficar pronto..."
kubectl wait --for=condition=ready pod/llama-upload-helper -n $NAMESPACE --timeout=60s

echo ""
echo "=== Fazendo upload do modelo para NFS ===="
kubectl cp "$MODEL_FILE" \
  $NAMESPACE/llama-upload-helper:/models/$MODEL_NAME \
  -c helper

echo ""
echo "=== Verificando arquivo no NFS ===="
kubectl exec -n $NAMESPACE llama-upload-helper -- ls -lh /models/ | grep $MODEL_NAME

echo ""
echo "=== Limpando pod helper ===="
kubectl delete pod llama-upload-helper -n $NAMESPACE

echo ""
echo "=== Concluído! Modelo $MODEL_NAME pronto para uso ===="
