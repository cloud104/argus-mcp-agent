#!/bin/bash
# Generate Kubernetes secret from .env file
# Usage: ./scripts/generate-k8s-secret.sh [namespace] [output-file]

set -e

NAMESPACE=${1:-argus-dev}
OUTPUT_FILE=${2:-k8s/dev/secret.yaml}

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Load .env file
set -a
source .env
set +a

# Generate secret.yaml
cat > "$OUTPUT_FILE" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: argus-secrets
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  OPENAI_API_KEY: "${OPENAI_API_KEY:-}"
  GOOGLE_API_KEY: "${GOOGLE_API_KEY:-}"
  ANTHROPIC_API_KEY: "${ANTHROPIC_API_KEY:-}"
  ES_HOST: "${ES_HOST:-}"
  ES_USER: "${ES_USER:-}"
  ES_PASSWORD: "${ES_PASSWORD:-}"
EOF

echo "✅ Secret generated at: $OUTPUT_FILE"
echo "⚠️  WARNING: This file contains sensitive data. Do NOT commit it to git!"
echo ""
echo "To apply:"
echo "  kubectl apply -f $OUTPUT_FILE"
